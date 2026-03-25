import os
import json
import sqlite3
import tempfile
import pytest
from unittest.mock import patch


# We need to set env vars BEFORE importing hub
@pytest.fixture
def test_env(tmp_path):
    """Set up a test environment with a seeded DB."""
    db_path = str(tmp_path / "test.db")
    projects_dir = str(tmp_path / "projects")
    os.makedirs(projects_dir)

    # Create a test project
    project_path = os.path.join(projects_dir, "test-video")
    os.makedirs(os.path.join(project_path, "images"))
    with open(os.path.join(project_path, "TUBE2TXT-OUTLINE.md"), "w") as f:
        f.write("## Outline\n\nTest outline content")
    with open(os.path.join(project_path, "TUBE2TXT-NOTES.md"), "w") as f:
        f.write("## Notes\n\nTest notes content")

    # Seed the DB
    conn = sqlite3.connect(db_path)
    conn.execute("""CREATE TABLE IF NOT EXISTS videos (
        id INTEGER PRIMARY KEY AUTOINCREMENT, slug TEXT UNIQUE,
        url TEXT, title TEXT, processed_at DATETIME)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS segments (
        id INTEGER PRIMARY KEY AUTOINCREMENT, video_id INTEGER,
        start_ts TEXT, seconds INTEGER, text TEXT, thumbnail_path TEXT)""")
    conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS segments_search USING fts5(segment_id, text)")
    conn.execute("INSERT INTO videos (slug, url, title, processed_at) VALUES (?, ?, ?, ?)",
                 ("test-video", "https://youtube.com/watch?v=test", "Test Video", "2026-03-25"))
    conn.execute("INSERT INTO segments (video_id, start_ts, seconds, text, thumbnail_path) VALUES (?, ?, ?, ?, ?)",
                 (1, "00:00:01.000", 1, "Hello world", "images/00-00-01-000.jpg"))
    conn.execute("INSERT INTO segments_search (segment_id, text) VALUES (?, ?)", (1, "Hello world"))
    conn.commit()
    conn.close()

    return {"db_path": db_path, "projects_dir": projects_dir}


@pytest.fixture
def client(test_env):
    """Create a FastAPI TestClient with test env."""
    with patch.dict(os.environ, {"TUBE2TXT_DB": test_env["db_path"]}):
        # Re-import to pick up env vars
        import importlib
        import tube2txt.hub as hub_module
        hub_module.DB_PATH = test_env["db_path"]
        hub_module.PROJECTS_DIR = test_env["projects_dir"]

        from fastapi.testclient import TestClient
        return TestClient(hub_module.app)


def test_get_videos(client):
    response = client.get("/api/videos")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["slug"] == "test-video"


def test_get_video_detail(client):
    response = client.get("/api/videos/test-video")
    assert response.status_code == 200
    data = response.json()
    assert data["slug"] == "test-video"
    assert len(data["segments"]) == 1
    assert data["segments"][0]["start_ts"] == "00:00:01.000"
    assert len(data["ai_files"]) == 2
    names = [f["name"] for f in data["ai_files"]]
    assert "OUTLINE" in names
    assert "NOTES" in names


def test_get_video_detail_not_found(client):
    response = client.get("/api/videos/nonexistent")
    assert response.status_code == 404


def test_search(client):
    response = client.get("/api/search?q=Hello")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["slug"] == "test-video"


def test_websocket_process_sends_progress(client, test_env):
    """WebSocket should stream progress messages during processing."""
    with patch("tube2txt.hub.process_video") as mock_pv:
        def fake_process(url, slug, mode, ai_flag, db_path, project_path, on_progress, parallel=4):
            on_progress("status", "download", "Downloading...")
            on_progress("status", "parse", "Parsing...")
            on_progress("complete", "done", "Finished")
            return project_path

        mock_pv.side_effect = fake_process

        with client.websocket_connect("/ws/process") as ws:
            ws.send_json({"action": "start", "slug": "ws-test", "url": "https://youtube.com/watch?v=test", "ai": False, "mode": "outline"})

            msgs = []
            while True:
                data = ws.receive_json()
                msgs.append(data)
                if data.get("type") in ("complete", "error"):
                    break

            types = [m["type"] for m in msgs]
            assert "status" in types
            assert "complete" in types
