"""Dynamic TOTP QRCode generation and scan validation service (FR-04, FR-11, SPR-04)."""
import base64
import io
import time
from datetime import datetime
from typing import Optional, Tuple
import pyotp
import qrcode
from models.attendance_session import AttendanceSession
from repositories.attendance_repo import AttendanceRepository
from services.log_service import LogService

TOTP_INTERVAL_SECONDS = 30
EXPIRED_CODE_ERROR = "Invalid or expired attendance code. Please scan the current QR code on the screen."


class QRCode:
    """Matches Week 8 UML QRCode class (generateCode and validateScan)."""

    def __init__(self, secret: Optional[str] = None, interval: int = TOTP_INTERVAL_SECONDS):
        self.secret = secret or pyotp.random_base32()
        self.interval = interval
        self.totp = pyotp.TOTP(self.secret, interval=self.interval)

    def generateCode(self, for_time: Optional[datetime] = None) -> str:
        if for_time is not None:
            return self.totp.at(for_time)
        return self.totp.now()

    def seconds_remaining(self) -> int:
        return self.interval - (int(time.time()) % self.interval)

    def validateScan(self, submitted_code: str, for_time: Optional[datetime] = None) -> bool:
        if not submitted_code:
            return False
        cleaned = submitted_code.strip()
        if ":" in cleaned:
            cleaned = cleaned.split(":")[-1].strip()
        if not cleaned.isdigit() or len(cleaned) != 6:
            return False
        if for_time is not None:
            return bool(self.totp.verify(cleaned, for_time=for_time, valid_window=0))
        return bool(self.totp.verify(cleaned, valid_window=0))


class QRService:
    def __init__(
        self,
        attendance_repo: Optional[AttendanceRepository] = None,
        log_service: Optional[LogService] = None,
    ):
        self.attendance_repo = attendance_repo or AttendanceRepository()
        self.log_service = log_service or LogService()

    def create_secret(self) -> str:
        return pyotp.random_base32()

    def generate_session_qr(self, session_row: dict) -> dict:
        qr_obj = QRCode(secret=session_row["totp_secret"])
        code = qr_obj.generateCode()
        payload = f"NSU:{session_row['id']}:{code}"

        img = qrcode.make(payload)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        b64_img = base64.b64encode(buf.getvalue()).decode("ascii")

        return {
            "session_id": session_row["id"],
            "code": code,
            "payload": payload,
            "seconds_remaining": qr_obj.seconds_remaining(),
            "qr_data_uri": f"data:image/png;base64,{b64_img}",
        }

    def validateScan(
        self,
        submitted_code: str,
        student_email: Optional[str] = None,
        ip_address: Optional[str] = None,
        now: Optional[datetime] = None,
    ) -> Tuple[Optional[dict], str]:
        """
        Validates a scanned QR payload or 6-digit backup code against active sessions.
        Also enforces automatic session closing if the scheduled class end time has passed (BUG-03 fix).
        """
        if not submitted_code or not submitted_code.strip():
            self.log_service.log_event(
                "EXPIRED_QR_SCAN",
                "Blank QR or attendance code submitted.",
                email=student_email,
                ip_address=ip_address,
            )
            return None, EXPIRED_CODE_ERROR

        cleaned = submitted_code.strip()
        target_session_id = None
        if cleaned.upper().startswith("NSU:"):
            parts = cleaned.split(":")
            if len(parts) == 3 and parts[1].isdigit():
                target_session_id = int(parts[1])
                cleaned = parts[2].strip()

        sessions = self.attendance_repo.get_active_sessions()
        current_dt = now or datetime.now()

        for row in sessions:
            if target_session_id is not None and row["id"] != target_session_id:
                continue

            model = AttendanceSession(
                id=row["id"],
                course_id=row["course_id"],
                session_date=row["session_date"],
                start_time=row["start_time"],
                end_time=row["end_time"],
                totp_secret=row["totp_secret"],
                is_active=bool(row["is_active"]),
            )

            if model.is_expired(now=current_dt):
                self.attendance_repo.close_session(row["id"])
                continue

            qr_obj = QRCode(secret=row["totp_secret"])
            if qr_obj.validateScan(cleaned, for_time=current_dt):
                return row, ""

        self.log_service.log_event(
            "EXPIRED_QR_SCAN",
            f"Invalid or expired attendance code attempted: {submitted_code[:24]}",
            email=student_email,
            ip_address=ip_address,
        )
        return None, EXPIRED_CODE_ERROR
