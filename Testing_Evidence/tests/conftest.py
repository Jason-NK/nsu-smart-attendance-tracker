"""Pytest fixtures setting up an isolated temporary SQLite database for every test."""
import sys
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from app import create_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    test_db = tmp_path / "test_attendance.db"
    monkeypatch.setenv("ATTENDANCE_DB_PATH", str(test_db))
    app = create_app({"TESTING": True, "SECRET_KEY": "test-secret-key"})
    with app.test_client() as test_client:
        yield test_client
