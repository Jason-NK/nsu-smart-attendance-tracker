"""SQLite database connection helper using safe relative paths."""
import os
import sqlite3
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_DB_PATH = ROOT_DIR / "attendance.db"
SCHEMA_PATH = ROOT_DIR / "database" / "schema.sql"
SEED_PATH = ROOT_DIR / "database" / "seed_data.sql"


def get_db_path() -> Path:
    custom = os.environ.get("ATTENDANCE_DB_PATH")
    if custom:
        return Path(custom)
    return DEFAULT_DB_PATH


def get_connection() -> sqlite3.Connection:
    db_path = get_db_path()
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def ensure_database_initialized(seed: bool = True) -> None:
    """Creates tables (and optionally loads seed data) if attendance.db does not exist yet."""
    db_path = get_db_path()
    first_time = not db_path.exists() or db_path.stat().st_size == 0
    conn = get_connection()
    try:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            conn.executescript(f.read())
        if first_time and seed and SEED_PATH.exists():
            with open(SEED_PATH, "r", encoding="utf-8") as f:
                conn.executescript(f.read())
        conn.commit()
    finally:
        conn.close()
