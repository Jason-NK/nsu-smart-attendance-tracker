"""Repository for courses and CSV class roster enrollments."""
from typing import List, Optional
from repositories.db import get_connection


class CourseRepository:
    def create_course(self, course_code: str, course_name: str, professor_id: int) -> int:
        conn = get_connection()
        try:
            cur = conn.execute(
                "INSERT INTO courses (course_code, course_name, professor_id) VALUES (?, ?, ?)",
                (course_code.strip().upper(), course_name.strip(), professor_id),
            )
            conn.commit()
            return cur.lastrowid
        finally:
            conn.close()

    def get_by_professor(self, professor_id: int) -> List[dict]:
        conn = get_connection()
        try:
            rows = conn.execute(
                """
                SELECT c.*,
                       (SELECT COUNT(*) FROM enrollments e WHERE e.course_id = c.id) AS student_count
                FROM courses c
                WHERE c.professor_id = ?
                ORDER BY c.course_code ASC
                """,
                (professor_id,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_by_id(self, course_id: int) -> Optional[dict]:
        conn = get_connection()
        try:
            row = conn.execute("SELECT * FROM courses WHERE id = ?", (course_id,)).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_by_code(self, course_code: str) -> Optional[dict]:
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM courses WHERE UPPER(course_code) = UPPER(?)",
                (course_code.strip(),),
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def enroll_student(self, course_id: int, student_id: str, student_name: str, student_email: str) -> None:
        conn = get_connection()
        try:
            conn.execute(
                """
                INSERT OR IGNORE INTO enrollments (course_id, student_id, student_name, student_email)
                VALUES (?, ?, ?, ?)
                """,
                (course_id, student_id.strip(), student_name.strip(), student_email.strip()),
            )
            conn.commit()
        finally:
            conn.close()

    def get_enrolled_students(self, course_id: int) -> List[dict]:
        conn = get_connection()
        try:
            rows = conn.execute(
                "SELECT * FROM enrollments WHERE course_id = ? ORDER BY student_name ASC",
                (course_id,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()
