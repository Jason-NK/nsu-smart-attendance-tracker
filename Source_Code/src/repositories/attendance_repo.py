"""Repository for attendance sessions and attendance records."""
from typing import List, Optional
from models.attendance_record import AttendanceRecord
from repositories.db import get_connection


class AttendanceRepository:
    def create_session(
        self,
        course_id: int,
        session_date: str,
        start_time: str,
        end_time: str,
        totp_secret: str,
    ) -> int:
        conn = get_connection()
        try:
            cur = conn.execute(
                """
                INSERT INTO attendance_sessions (course_id, session_date, start_time, end_time, totp_secret, is_active)
                VALUES (?, ?, ?, ?, ?, 1)
                """,
                (course_id, session_date, start_time, end_time, totp_secret),
            )
            conn.commit()
            return cur.lastrowid
        finally:
            conn.close()

    def get_session_by_id(self, session_id: int) -> Optional[dict]:
        conn = get_connection()
        try:
            row = conn.execute(
                """
                SELECT s.*, c.course_code, c.course_name, c.professor_id
                FROM attendance_sessions s
                JOIN courses c ON c.id = s.course_id
                WHERE s.id = ?
                """,
                (session_id,),
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_active_sessions(self) -> List[dict]:
        conn = get_connection()
        try:
            rows = conn.execute(
                """
                SELECT s.*, c.course_code, c.course_name, c.professor_id
                FROM attendance_sessions s
                JOIN courses c ON c.id = s.course_id
                WHERE s.is_active = 1
                ORDER BY s.id DESC
                """
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_sessions_for_professor(self, professor_id: int) -> List[dict]:
        conn = get_connection()
        try:
            rows = conn.execute(
                """
                SELECT s.*, c.course_code, c.course_name
                FROM attendance_sessions s
                JOIN courses c ON c.id = s.course_id
                WHERE c.professor_id = ?
                ORDER BY s.id DESC
                """,
                (professor_id,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def close_session(self, session_id: int) -> None:
        conn = get_connection()
        try:
            conn.execute(
                "UPDATE attendance_sessions SET is_active = 0 WHERE id = ?",
                (session_id,),
            )
            conn.commit()
        finally:
            conn.close()

    def has_checked_in(self, session_id: int, user_id: int) -> bool:
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT id FROM attendance_records WHERE session_id = ? AND user_id = ?",
                (session_id, user_id),
            ).fetchone()
            return row is not None
        finally:
            conn.close()

    def save_record(self, record: AttendanceRecord) -> int:
        conn = get_connection()
        try:
            cur = conn.execute(
                """
                INSERT INTO attendance_records
                    (session_id, course_id, user_id, student_id, student_name, check_in_time, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.session_id,
                    record.course_id,
                    record.user_id,
                    record.student_id,
                    record.student_name,
                    record.check_in_time,
                    record.status,
                ),
            )
            conn.commit()
            return cur.lastrowid
        finally:
            conn.close()

    def get_records_for_course(self, course_id: int) -> List[dict]:
        conn = get_connection()
        try:
            rows = conn.execute(
                """
                SELECT ar.id, ar.student_name, ar.student_id, c.course_code, c.course_name,
                       s.session_date, ar.check_in_time, ar.status
                FROM attendance_records ar
                JOIN courses c ON c.id = ar.course_id
                JOIN attendance_sessions s ON s.id = ar.session_id
                WHERE ar.course_id = ?
                ORDER BY ar.check_in_time DESC
                """,
                (course_id,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_records_for_student(self, user_id: int) -> List[dict]:
        conn = get_connection()
        try:
            rows = conn.execute(
                """
                SELECT ar.id, c.course_code, c.course_name, s.session_date, ar.check_in_time, ar.status
                FROM attendance_records ar
                JOIN courses c ON c.id = ar.course_id
                JOIN attendance_sessions s ON s.id = ar.session_id
                WHERE ar.user_id = ?
                ORDER BY s.session_date DESC, ar.check_in_time DESC
                """,
                (user_id,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()
