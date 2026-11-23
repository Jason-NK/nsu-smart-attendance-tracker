"""Helper script to initialize and seed attendance.db using Python's built-in sqlite3."""
import sqlite3
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = ROOT_DIR / "attendance.db"
SCHEMA_PATH = ROOT_DIR / "database" / "schema.sql"
SEED_PATH = ROOT_DIR / "database" / "seed_data.sql"


def init_db(db_path: Path = DB_PATH) -> None:
    conn = sqlite3.connect(str(db_path))
    try:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            conn.executescript(f.read())
        with open(SEED_PATH, "r", encoding="utf-8") as f:
            conn.executescript(f.read())
        conn.commit()
        print(f"Database initialized and seeded at: {db_path}")
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
