"""Core User, Student, and Professor models matching Week 8 UML class design."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    id: Optional[int]
    username: str
    full_name: str
    email: str
    password_hash: str
    role: str

    def login(self) -> dict:
        return {
            "user_id": self.id,
            "username": self.username,
            "full_name": self.full_name,
            "email": self.email,
            "role": self.role,
        }

    def logout(self) -> bool:
        return True


@dataclass
class Student(User):
    student_id: str = ""
    major: str = ""

    def scan_code(self, code: str) -> str:
        return code.strip()

    def view_history(self, attendance_repo):
        return attendance_repo.get_records_for_student(self.id)


@dataclass
class Professor(User):
    employee_id: str = ""
    department: str = ""

    def create_course(self, course_repo, course_code: str, course_name: str):
        return course_repo.create_course(course_code, course_name, self.id)

    def request_report(self, report_service, course_id: int):
        return report_service.generate_csv_report(course_id)
