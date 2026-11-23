"""Tests for TC-02..TC-08, NT-01, NT-03, NT-05, NT-06, ST-02, ST-03, and 20-min timeout."""
import io
import time
from datetime import date
from repositories.attendance_repo import AttendanceRepository
from services.qr_service import QRCode


def _login(client, email, password):
    return client.post("/login", data={"email": email, "password": password}, follow_redirects=False)


def test_tc02_and_nt05_professor_creates_course_and_validates_code(client):
    _login(client, "dnwosu@nsu.edu", "Professor123")

    bad = client.post("/courses/create", data={"course_code": "CSC@38000", "course_name": "Bad"}, follow_redirects=True)
    assert b"Enter a valid course code" in bad.data

    good = client.post("/courses/create", data={"course_code": "CSC-410", "course_name": "Cloud Security"}, follow_redirects=True)
    assert good.status_code == 200
    assert b"CSC-410" in good.data


def test_tc03_tc04_tc06_tc07_tc08_full_workflow_and_csv_export(client):
    _login(client, "dnwosu@nsu.edu", "Professor123")
    today = date.today().strftime("%Y-%m-%d")
    start_resp = client.post(
        "/sessions/start",
        data={"course_id": "1", "session_date": today, "start_time": "00:01", "end_time": "23:59"},
        follow_redirects=True,
    )
    assert start_resp.status_code == 200
    assert b"Live Attendance Session" in start_resp.data

    active = AttendanceRepository().get_active_sessions()[0]
    live_code = QRCode(secret=active["totp_secret"]).generateCode()

    _login(client, "jkennedy@spartans.nsu.edu", "Spartan123")
    checkin_resp = client.post(
        "/student_scanner",
        data={"student_id": "1234567", "attendance_code": live_code},
        follow_redirects=True,
    )
    assert b"Check-In Confirmed!" in checkin_resp.data

    hist_resp = client.get("/student_history")
    assert hist_resp.status_code == 200
    assert b"CSC-380" in hist_resp.data

    _login(client, "dnwosu@nsu.edu", "Professor123")
    dash = client.get("/professor_dashboard?course_id=1")
    assert b"Jason Kennedy" in dash.data

    csv_resp = client.get("/courses/1/export_csv")
    assert csv_resp.status_code == 200
    assert "text/csv" in csv_resp.content_type
    assert b"Student Name,Student ID,Course Code,Session Date,Check-In Time,Status" in csv_resp.data
    assert b"Jason Kennedy,1234567,CSC-380" in csv_resp.data


def test_nt01_invalid_student_id_blocked(client):
    _login(client, "jkennedy@spartans.nsu.edu", "Spartan123")
    resp = client.post("/student_scanner", data={"student_id": "ABC1234", "attendance_code": "123456"})
    assert b"Student ID is required and must be a 7-digit number." in resp.data


def test_nt03_past_session_date_rejected(client):
    _login(client, "dnwosu@nsu.edu", "Professor123")
    resp = client.post(
        "/sessions/start",
        data={"course_id": "1", "session_date": "01/15/2025", "start_time": "10:00", "end_time": "11:00"},
        follow_redirects=True,
    )
    assert b"Please pick a valid session date that is today or in the future." in resp.data


def test_nt06_invalid_roster_upload_rejected(client):
    _login(client, "dnwosu@nsu.edu", "Professor123")
    bad_ext = client.post(
        "/courses/1/upload_roster",
        data={"roster_file": (io.BytesIO(b"alert(1)"), "script.js")},
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert b"Only CSV files under 2 MB are allowed for class rosters." in bad_ext.data

    oversized = client.post(
        "/courses/1/upload_roster",
        data={"roster_file": (io.BytesIO(b"a" * (2 * 1024 * 1024 + 50)), "huge.csv")},
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert b"Only CSV files under 2 MB are allowed for class rosters." in oversized.data


def test_st02_student_blocked_from_professor_routes(client):
    _login(client, "jkennedy@spartans.nsu.edu", "Spartan123")
    for route in ("/professor_dashboard", "/courses/1/export_csv"):
        resp = client.get(route)
        assert resp.status_code == 403
        assert b"Access Denied" in resp.data


def test_st03_student_cannot_snoop_other_student_history(client):
    _login(client, "jkennedy@spartans.nsu.edu", "Spartan123")
    resp = client.get("/student_history?student_id=7654321")
    assert resp.status_code == 403
    assert b"Access Denied" in resp.data


def test_spr06_20_minute_idle_timeout(client):
    _login(client, "jkennedy@spartans.nsu.edu", "Spartan123")
    with client.session_transaction() as sess:
        sess["last_activity"] = time.time() - (21 * 60)
    resp = client.get("/student_scanner", follow_redirects=False)
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]
