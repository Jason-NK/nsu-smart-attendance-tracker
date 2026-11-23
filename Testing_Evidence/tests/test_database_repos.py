"""Tests for database schema, seed accounts, and persistence (NFR-04)."""
from repositories.attendance_repo import AttendanceRepository
from repositories.course_repo import CourseRepository
from repositories.user_repo import UserRepository


def test_seeded_users_and_course_exist(client):
    user_repo = UserRepository()
    student = user_repo.find_by_email("jkennedy@spartans.nsu.edu")
    prof = user_repo.find_by_email("dnwosu@nsu.edu")
    assert student is not None and student["role"] == "student"
    assert prof is not None and prof["role"] == "professor"

    course = CourseRepository().get_by_code("CSC-380")
    assert course is not None
    assert course["course_name"] == "Software Engineering"


def test_records_persist_in_sqlite(client):
    records = AttendanceRepository().get_records_for_course(1)
    assert len(records) >= 2
    assert any(r["student_id"] == "1234567" for r in records)
