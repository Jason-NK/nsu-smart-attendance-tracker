"""Attendance Session & Reporting Controller for Professors and Admins (FR-02, FR-03, FR-04, FR-08, FR-10)."""
from datetime import date, datetime
from flask import Blueprint, Response, jsonify, redirect, render_template, request, session, url_for
from controllers.security_filter import role_required
from models.attendance_session import AttendanceSession
from repositories.attendance_repo import AttendanceRepository
from repositories.course_repo import CourseRepository
from services.auth_service import validate_course_code
from services.log_service import LogService
from services.qr_service import QRService
from services.report_service import ReportService

session_bp = Blueprint("sessions", __name__)


def _parse_session_date(raw_date: str):
    """Supports YYYY-MM-DD (HTML date input) and MM/DD/YYYY."""
    raw = (raw_date or "").strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
        try:
            parsed = datetime.strptime(raw, fmt).date()
            return parsed
        except ValueError:
            continue
    return None


@session_bp.route("/professor_dashboard")
@role_required("professor")
def professor_dashboard():
    prof_id = session["user_id"]
    course_repo = CourseRepository()
    attendance_repo = AttendanceRepository()
    qr_service = QRService(attendance_repo=attendance_repo)

    courses = course_repo.get_by_professor(prof_id)
    all_sessions = attendance_repo.get_sessions_for_professor(prof_id)

    active_session = None
    qr_bundle = None
    now = datetime.now()
    for s in all_sessions:
        if s["is_active"]:
            model = AttendanceSession(
                id=s["id"],
                course_id=s["course_id"],
                session_date=s["session_date"],
                start_time=s["start_time"],
                end_time=s["end_time"],
                totp_secret=s["totp_secret"],
                is_active=True,
            )
            if model.is_expired(now=now):
                attendance_repo.close_session(s["id"])
                s["is_active"] = 0
            elif active_session is None:
                active_session = s
                qr_bundle = qr_service.generate_session_qr(s)

    selected_course_id = request.args.get("course_id", type=int)
    if not selected_course_id and courses:
        selected_course_id = courses[0]["id"]

    records = []
    selected_course = None
    if selected_course_id:
        selected_course = course_repo.get_by_id(selected_course_id)
        if selected_course and selected_course["professor_id"] == prof_id:
            records = attendance_repo.get_records_for_course(selected_course_id)

    return render_template(
        "professor_dashboard.html",
        full_name=session.get("full_name"),
        courses=courses,
        selected_course=selected_course,
        records=records,
        active_session=active_session,
        qr_bundle=qr_bundle,
        today_str=date.today().strftime("%Y-%m-%d"),
        error=request.args.get("error"),
        success=request.args.get("success"),
    )


@session_bp.route("/courses/create", methods=["POST"])
@role_required("professor")
def create_course():
    course_code = request.form.get("course_code", "").strip().upper()
    course_name = request.form.get("course_name", "").strip()

    valid_code, err = validate_course_code(course_code)
    if not valid_code:
        return redirect(url_for("sessions.professor_dashboard", error=err))
    if not course_name:
        return redirect(url_for("sessions.professor_dashboard", error="Course name is required."))

    course_repo = CourseRepository()
    if course_repo.get_by_code(course_code):
        return redirect(url_for("sessions.professor_dashboard", error=f"Course {course_code} already exists."))

    course_id = course_repo.create_course(course_code, course_name, session["user_id"])
    return redirect(
        url_for(
            "sessions.professor_dashboard",
            course_id=course_id,
            success=f"Course {course_code} created successfully.",
        )
    )


@session_bp.route("/courses/<int:course_id>/upload_roster", methods=["POST"])
@role_required("professor")
def upload_roster(course_id: int):
    course_repo = CourseRepository()
    course = course_repo.get_by_id(course_id)
    if not course or course["professor_id"] != session["user_id"]:
        return render_template("error.html", title="Access Denied", message="Access Denied."), 403

    uploaded = request.files.get("roster_file")
    if not uploaded or not uploaded.filename:
        return redirect(
            url_for("sessions.professor_dashboard", course_id=course_id, error="Only CSV files under 2 MB are allowed for class rosters.")
        )

    file_bytes = uploaded.read()
    ok, msg, _ = ReportService().validate_and_import_roster(course_id, uploaded.filename, file_bytes)
    if not ok:
        return redirect(url_for("sessions.professor_dashboard", course_id=course_id, error=msg))
    return redirect(url_for("sessions.professor_dashboard", course_id=course_id, success=msg))


@session_bp.route("/sessions/start", methods=["POST"])
@role_required("professor")
def start_session():
    course_id = request.form.get("course_id", type=int)
    raw_date = request.form.get("session_date", "").strip()
    start_time = request.form.get("start_time", "").strip()
    end_time = request.form.get("end_time", "").strip() or "23:59"

    course_repo = CourseRepository()
    course = course_repo.get_by_id(course_id) if course_id else None
    if not course or course["professor_id"] != session["user_id"]:
        return redirect(url_for("sessions.professor_dashboard", error="Please select a valid course."))

    parsed_date = _parse_session_date(raw_date)
    if not parsed_date or parsed_date < date.today():
        return redirect(
            url_for(
                "sessions.professor_dashboard",
                course_id=course_id,
                error="Please pick a valid session date that is today or in the future.",
            )
        )

    try:
        st = datetime.strptime(start_time, "%H:%M").time()
        et = datetime.strptime(end_time, "%H:%M").time()
        if st >= et:
            raise ValueError("Start time must be before end time")
    except ValueError:
        return redirect(
            url_for(
                "sessions.professor_dashboard",
                course_id=course_id,
                error="Enter a valid start time before the class end time.",
            )
        )

    attendance_repo = AttendanceRepository()
    qr_service = QRService(attendance_repo=attendance_repo)
    secret = qr_service.create_secret()
    attendance_repo.create_session(
        course_id=course_id,
        session_date=parsed_date.strftime("%Y-%m-%d"),
        start_time=start_time,
        end_time=end_time,
        totp_secret=secret,
    )
    return redirect(
        url_for(
            "sessions.professor_dashboard",
            course_id=course_id,
            success=f"Live attendance session started for {course['course_code']}.",
        )
    )


@session_bp.route("/sessions/<int:session_id>/end", methods=["POST"])
@role_required("professor")
def end_session(session_id: int):
    attendance_repo = AttendanceRepository()
    sess = attendance_repo.get_session_by_id(session_id)
    if not sess or sess["professor_id"] != session["user_id"]:
        return render_template("error.html", title="Access Denied", message="Access Denied."), 403

    attendance_repo.close_session(session_id)
    return redirect(
        url_for(
            "sessions.professor_dashboard",
            course_id=sess["course_id"],
            success="Attendance session closed.",
        )
    )


@session_bp.route("/sessions/<int:session_id>/qr_refresh")
@role_required("professor")
def qr_refresh(session_id: int):
    attendance_repo = AttendanceRepository()
    sess = attendance_repo.get_session_by_id(session_id)
    if not sess or sess["professor_id"] != session["user_id"]:
        return jsonify({"error": "Access Denied"}), 403

    model = AttendanceSession(
        id=sess["id"],
        course_id=sess["course_id"],
        session_date=sess["session_date"],
        start_time=sess["start_time"],
        end_time=sess["end_time"],
        totp_secret=sess["totp_secret"],
        is_active=bool(sess["is_active"]),
    )
    if model.is_expired():
        attendance_repo.close_session(session_id)
        return jsonify({"expired": True}), 200

    qr_bundle = QRService(attendance_repo=attendance_repo).generate_session_qr(sess)
    return jsonify(qr_bundle)


@session_bp.route("/courses/<int:course_id>/export_csv")
@role_required("professor")
def export_csv(course_id: int):
    course_repo = CourseRepository()
    course = course_repo.get_by_id(course_id)
    if not course or course["professor_id"] != session["user_id"]:
        return render_template("error.html", title="Access Denied", message="Access Denied."), 403

    filename, csv_content = ReportService().generate_csv_report(course_id)
    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@session_bp.route("/admin_logs")
@role_required("admin")
def admin_logs():
    logs = LogService().get_recent_logs(limit=100)
    return render_template(
        "error.html",
        title="IT Support Security Logs",
        message=f"Showing {len(logs)} most recent security events.",
        logs=logs,
    )
