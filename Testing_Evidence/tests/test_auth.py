"""Tests for TC-01, NT-02, ST-01, ST-05 (Login, NSU Email Validation, SQLi, bcrypt)."""
from repositories.log_repo import LogRepository
from repositories.user_repo import UserRepository


def test_tc01_valid_student_login(client):
    resp = client.post(
        "/login",
        data={"email": "jkennedy@spartans.nsu.edu", "password": "Spartan123"},
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert "/student_scanner" in resp.headers["Location"]


def test_nt02_reject_non_nsu_email(client):
    resp = client.post(
        "/login",
        data={"email": "student123@gmail.com", "password": "Spartan123"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"Enter a valid NSU email address." in resp.data


def test_st01_unauthenticated_page_access_redirects(client):
    for protected in ("/student_scanner", "/student_history", "/professor_dashboard"):
        resp = client.get(protected, follow_redirects=False)
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]


def test_st05_sql_injection_blocked_and_passwords_hashed(client):
    resp = client.post(
        "/login",
        data={"email": "' OR 1=1 --", "password": "anything"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"Enter a valid NSU email address." in resp.data

    user = UserRepository().find_by_email("jkennedy@spartans.nsu.edu")
    assert user is not None
    assert user["password_hash"].startswith("$2b$")
    assert user["password_hash"] != "Spartan123"

    logs = LogRepository().get_recent_logs()
    assert any(log["event_type"] == "FAILED_LOGIN" for log in logs)
