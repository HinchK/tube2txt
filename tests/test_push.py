import pytest
import os
import sqlite3
from tube2txt.cloud import push

# Ensure a temporary DB with no entries for a given slug
@pytest.fixture
def empty_db(tmp_path):
    db_path = tmp_path / "empty.db"
    # Create minimal schema matching expected tables
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE videos (
            id INTEGER PRIMARY KEY,
            slug TEXT UNIQUE,
            title TEXT,
            url TEXT,
            processed_at TEXT,
            remote_url TEXT,
            is_archived INTEGER,
            last_synced_at TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE segments (
            id INTEGER PRIMARY KEY,
            video_id INTEGER,
            start_ts TEXT,
            seconds REAL,
            text TEXT
        )
    """)
    conn.commit()
    conn.close()
    return str(db_path)

def test_push_missing_slug_raises(empty_db, monkeypatch):
    # Ensure remote config file does not exist to bypass config prompt
    def mock_exists(path):
        return False
    monkeypatch.setattr(os.path, "exists", mock_exists)

    with pytest.raises(ValueError) as exc:
        push("nonexistent", db_path=empty_db, projects_dir=".")
    assert "not found in local DB" in str(exc.value)
