"""Security logging service recording failed logins, expired QR scans, and access blocks."""
from typing import List, Optional
from repositories.log_repo import LogRepository


class LogService:
    def __init__(self, log_repo: Optional[LogRepository] = None):
        self.log_repo = log_repo or LogRepository()

    def log_event(
        self,
        event_type: str,
        details: str,
        email: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> int:
        return self.log_repo.add_log(
            event_type=event_type,
            details=details,
            email=email,
            ip_address=ip_address,
        )

    def get_recent_logs(self, limit: int = 50) -> List[dict]:
        return self.log_repo.get_recent_logs(limit=limit)
