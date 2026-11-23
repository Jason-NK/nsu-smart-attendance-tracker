"""AttendanceSession model tracking class session lifecycle and automatic expiration."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class AttendanceSession:
    id: Optional[int]
    course_id: int
    session_date: str   # YYYY-MM-DD
    start_time: str     # HH:MM
    end_time: str       # HH:MM
    totp_secret: str
    is_active: bool = True

    def start_session(self) -> None:
        self.is_active = True

    def end_session(self) -> None:
        self.is_active = False

    def is_expired(self, now: Optional[datetime] = None) -> bool:
        """Returns True if the session was manually closed or past its scheduled end time."""
        if not self.is_active:
            return True
        current_time = now or datetime.now()
        try:
            end_dt = datetime.strptime(f"{self.session_date} {self.end_time}", "%Y-%m-%d %H:%M")
            return current_time > end_dt
        except ValueError:
            return False
