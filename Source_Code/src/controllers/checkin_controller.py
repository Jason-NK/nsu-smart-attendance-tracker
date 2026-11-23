"""Student Check-In and Attendance History Controller (FR-05, FR-06, FR-07, FR-09, SPR-03)."""
from datetime import datetime
from flask import Blueprint, render_template, request, session
from controllers.security_filter import role_required
from models.attendance_record import AttendanceRecord
from repositories.attendance_repo import AttendanceRepository
from services.auth_service import validate_student_id
from services.log_service import LogService
from services.qr_service import QRService

checkin_bp = Blueprint("checkin", __name__)


@checkin_bp.route("/student_scanner", methods=["GET", "POST"])
@role_required("student")
def student_scanner():
    error = None
    confirmation = None
    default_student_id = session.get("student_id") or ""

    if request.method == "POST":
        entered_student_id = request.form.get("student_id", "").strip()
        entered_code = request.form.get("attendance_code", "").strip()

        valid_sid, sid_err = validate_student_id(entered_student_id)
        if not valid_sid:
            error = sid_err
        elif default_student_id and entered_student_id != default_student_id:
            LogService().log_event(
                "PRIVACY_VIOLATION",
                f"Student {session.get('email')} tried checking in with mismatched Student ID {entered_student_id}",
                email=session.get("email"),
                ip_address=request.remote_addr,
            )
            error = "Student ID does not match your logged-in NSU student account."
        else:
            attendance_repo = AttendanceRepository()
            qr_service = QRService(attendance_repo=attendance_repo)
            matched_session, qr_err = qr_service.validateScan(
                entered_code,
                student_email=session.get("email"),
                ip_address=request.remote_addr,
            )
            if qr_err or not matched_session:
                error = qr_err
            elif attendance_repo.has_checked_in(matched_session["id"], session["user_id"]):
                confirmation = {
                    "student_name": session.get("full_name"),
                    "student_id": entered_student_id,
                    "course_code": matched_session["course_code"],
                    "course_name": matched_session["course_name"],
                    "session_date": matched_session["session_date"],
                    "check_in_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "status": "Present (Already Checked In)",
                }
            else:
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                record = AttendanceRecord(
                    id=None,
                    session_id=matched_session["id"],
                    course_id=matched_session["course_id"],
                    user_id=session["user_id"],
                    student_id=entered_student_id,
                    student_name=session.get("full_name"),
                    check_in_time=now_str,
                    status="Present",
                )
                record.save_record(attendance_repo)
                confirmation = {
                    "student_name": record.student_name,
                    "student_id": record.student_id,
                    "course_code": matched_session["course_code"],
                    "course_name": matched_session["course_name"],
                    "session_date": matched_session["session_date"],
                    "check_in_time": record.check_in_time,
                    "status": record.status,
                }

    return render_template(
        "student_scanner.html",
        full_name=session.get("full_name"),
        student_id=default_student_id,
        error=error,
        confirmation=confirmation,
    )


@checkin_bp.route("/student_history")
@role_required("student")
def student_history():
    requested_sid = request.args.get("student_id")
    own_sid = session.get("student_id")

    if requested_sid and own_sid and requested_sid.strip() != own_sid:
        LogService().log_event(
            "PRIVACY_VIOLATION",
            f"Student {session.get('email')} attempted to view history for student_id={requested_sid}",
            email=session.get("email"),
            ip_address=request.remote_addr,
        )
        return (
            render_template(
                "error.html",
                title="Access Denied",
                message="Access Denied. Students can only view their own attendance history.",
            ),
            403,
        )

    records = AttendanceRepository().get_records_for_student(session["user_id"])
    return render_template(
        "student_history.html",
        full_name=session.get("full_name"),
        student_id=own_sid,
        records=records,
    )
