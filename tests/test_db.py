import os
import sqlite3
from tube2txt.db import Database

def test_database_init():
    db_path = "tests/test.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    
    try:
        db = Database(db_path)
        assert os.path.exists(db_path)
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            assert "videos" in tables
            assert "segments" in tables
            assert "segments_search" in tables
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)

def test_index_video():
    db_path = "tests/test_index.db"
    if os.path.exists(db_path):
        os.remove(db_path)
        
    try:
        db = Database(db_path)
        segments = [
            {"start": "00:00:01.000", "seconds": 1, "text": "Hello"},
            {"start": "00:00:05.000", "seconds": 5, "text": "World"}
        ]
        db.index_video("test-slug", "http://example.com", segments)
        
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM videos WHERE slug='test-slug'")
            video = cursor.fetchone()
            assert video is not None
            assert video["url"] == "http://example.com"
            
            cursor.execute("SELECT * FROM segments WHERE video_id=?", (video["id"],))
            rows = cursor.fetchall()
            assert len(rows) == 2
            assert rows[0]["text"] == "Hello"
            assert rows[1]["text"] == "World"
            
            # Test FTS
            cursor.execute("SELECT * FROM segments_search WHERE text MATCH 'Hello'")
            fts_row = cursor.fetchone()
            assert fts_row is not None
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)
