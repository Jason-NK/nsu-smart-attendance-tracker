"""Tests for TC-05, NT-04, ST-04, and BUG-03 (Dynamic TOTP QR Validation & Auto-Timeout)."""
from datetime import datetime, timedelta
from repositories.attendance_repo import AttendanceRepository
from repositories.log_repo import LogRepository
from services.qr_service import QRCode, QRService


def test_tc05_valid_active_totp_code_passes(client):
    repo = AttendanceRepository()
    qr_service = QRService(attendance_repo=repo)
    secret = qr_service.create_secret()
    today = datetime.now().strftime("%Y-%m-%d")

    repo.create_session(course_id=1, session_date=today, start_time="00:01", end_time="23:59", totp_secret=secret)
    live_code = QRCode(secret=secret).generateCode()

    matched, err = qr_service.validateScan(live_code, student_email="jkennedy@spartans.nsu.edu")
    assert err == ""
    assert matched is not None
    assert matched["course_id"] == 1


def test_nt04_and_st04_expired_qr_code_rejected_and_logged(client):
    repo = AttendanceRepository()
    qr_service = QRService(attendance_repo=repo)
    secret = qr_service.create_secret()
    today = datetime.now().strftime("%Y-%m-%d")

    repo.create_session(course_id=1, session_date=today, start_time="00:01", end_time="23:59", totp_secret=secret)
    old_code = QRCode(secret=secret).generateCode(for_time=datetime.now() - timedelta(seconds=60))

    matched, err = qr_service.validateScan(old_code, student_email="jkennedy@spartans.nsu.edu")
    assert matched is None
    assert "Invalid or expired attendance code." in err

    logs = LogRepository().get_recent_logs()
    assert any(log["event_type"] == "EXPIRED_QR_SCAN" for log in logs)


def test_bug03_session_auto_closes_after_end_time(client):
    repo = AttendanceRepository()
    qr_service = QRService(attendance_repo=repo)
    secret = qr_service.create_secret()
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    sid = repo.create_session(course_id=1, session_date=yesterday, start_time="08:00", end_time="09:00", totp_secret=secret)
    live_code = QRCode(secret=secret).generateCode()

    matched, err = qr_service.validateScan(live_code, student_email="jkennedy@spartans.nsu.edu")
    assert matched is None
    assert "Invalid or expired attendance code." in err
    assert repo.get_session_by_id(sid)["is_active"] == 0
