"""Repository for security_logs table (SPR-09)."""
from typing import List, Optional
from repositories.db import get_connection


class LogRepository:
    def add_log(self, event_type: str, details: str, email: Optional[str] = None, ip_address: Optional[str] = None) -> int:
        conn = get_connection()
        try:
            cur = conn.execute(
                "INSERT INTO security_logs (event_type, email, details, ip_address) VALUES (?, ?, ?, ?)",
                (event_type, email, details, ip_address),
            )
            conn.commit()
            return cur.lastrowid
        finally:
            conn.close()

    def get_recent_logs(self, limit: int = 50) -> List[dict]:
        conn = get_connection()
        try:
            rows = conn.execute(
                "SELECT * FROM security_logs ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()
