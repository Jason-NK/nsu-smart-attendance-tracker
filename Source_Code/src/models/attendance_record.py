"""AttendanceRecord model representing a validated student check-in."""
from dataclasses import dataclass
from typing import Optional

ALLOWED_STATUSES = ("Present", "Late", "Excused")


@dataclass
class AttendanceRecord:
    id: Optional[int]
    session_id: int
    course_id: int
    user_id: int
    student_id: str
    student_name: str
    check_in_time: str
    status: str = "Present"

    def save_record(self, attendance_repo) -> int:
        if self.status not in ALLOWED_STATUSES:
            raise ValueError("Please select a valid attendance status from the list.")
        return attendance_repo.save_record(self)
