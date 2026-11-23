"""CSV Attendance Report Export and Roster Upload Validation Service (FR-10, SPR-08)."""
import csv
import io
from typing import Optional, Tuple
from repositories.attendance_repo import AttendanceRepository
from repositories.course_repo import CourseRepository

MAX_ROSTER_BYTES = 2 * 1024 * 1024  # 2 MB
ROSTER_UPLOAD_ERROR = "Only CSV files under 2 MB are allowed for class rosters."


class ReportService:
    def __init__(
        self,
        attendance_repo: Optional[AttendanceRepository] = None,
        course_repo: Optional[CourseRepository] = None,
    ):
        self.attendance_repo = attendance_repo or AttendanceRepository()
        self.course_repo = course_repo or CourseRepository()

    def generate_csv_report(self, course_id: int) -> Tuple[str, str]:
        course = self.course_repo.get_by_id(course_id)
        records = self.attendance_repo.get_records_for_course(course_id)
        course_code = course["course_code"] if course else f"COURSE-{course_id}"

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Student Name", "Student ID", "Course Code", "Session Date", "Check-In Time", "Status"])

        for rec in records:
            writer.writerow([
                rec["student_name"],
                rec["student_id"],
                rec["course_code"],
                rec["session_date"],
                rec["check_in_time"],
                rec["status"],
            ])

        filename = f"{course_code}_attendance_report.csv"
        return filename, output.getvalue()

    def validate_and_import_roster(self, course_id: int, filename: str, file_bytes: bytes) -> Tuple[bool, str, int]:
        if not filename or not filename.lower().endswith(".csv"):
            return False, ROSTER_UPLOAD_ERROR, 0

        if len(file_bytes) == 0 or len(file_bytes) > MAX_ROSTER_BYTES:
            return False, ROSTER_UPLOAD_ERROR, 0

        try:
            text = file_bytes.decode("utf-8-sig")
        except UnicodeDecodeError:
            return False, ROSTER_UPLOAD_ERROR, 0

        reader = csv.DictReader(io.StringIO(text))
        required_cols = {"student_id", "student_name", "student_email"}
        if not reader.fieldnames or not required_cols.issubset({c.strip().lower() for c in reader.fieldnames}):
            return False, "CSV roster must include student_id, student_name, and student_email columns.", 0

        added = 0
        for row in reader:
            norm = {k.strip().lower(): (v or "").strip() for k, v in row.items() if k}
            sid = norm.get("student_id", "")
            sname = norm.get("student_name", "")
            semail = norm.get("student_email", "")
            if sid.isdigit() and len(sid) == 7 and sname and semail:
                self.course_repo.enroll_student(course_id, sid, sname, semail)
                added += 1

        return True, f"Roster imported successfully ({added} students processed).", added
