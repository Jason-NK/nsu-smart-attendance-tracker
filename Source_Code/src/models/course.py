"""Course model matching Week 8 UML class design."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Course:
    id: Optional[int]
    course_code: str
    course_name: str
    professor_id: int

    def add_session(self, attendance_repo, session_date: str, start_time: str, end_time: str, totp_secret: str):
        return attendance_repo.create_session(
            course_id=self.id,
            session_date=session_date,
            start_time=start_time,
            end_time=end_time,
            totp_secret=totp_secret,
        )
