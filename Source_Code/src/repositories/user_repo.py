"""Repository for user queries using parameterized SQL (prevents SQL injection)."""
from typing import Optional
from repositories.db import get_connection


class UserRepository:
    def find_by_email(self, email: str) -> Optional[dict]:
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM users WHERE LOWER(email) = LOWER(?)",
                (email.strip(),),
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def find_by_id(self, user_id: int) -> Optional[dict]:
        conn = get_connection()
        try:
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def find_by_student_id(self, student_id: str) -> Optional[dict]:
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM users WHERE student_id = ?",
                (student_id.strip(),),
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def create_user(
        self,
        username: str,
        full_name: str,
        email: str,
        password_hash: str,
        role: str,
        student_id: Optional[str] = None,
        major: Optional[str] = None,
        employee_id: Optional[str] = None,
        department: Optional[str] = None,
    ) -> int:
        conn = get_connection()
        try:
            cur = conn.execute(
                """
                INSERT INTO users (username, full_name, email, password_hash, role, student_id, major, employee_id, department)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (username, full_name, email, password_hash, role, student_id, major, employee_id, department),
            )
            conn.commit()
            return cur.lastrowid
        finally:
            conn.close()
