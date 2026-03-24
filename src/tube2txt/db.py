import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_path="tube2txt.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS videos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    slug TEXT UNIQUE,
                    url TEXT,
                    title TEXT,
                    processed_at DATETIME
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS segments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id INTEGER,
                    start_ts TEXT,
                    seconds INTEGER,
                    text TEXT,
                    thumbnail_path TEXT,
                    FOREIGN KEY (video_id) REFERENCES videos (id)
                )
            """)
            # FTS for global search
            cursor.execute("CREATE VIRTUAL TABLE IF NOT EXISTS segments_search USING fts5(segment_id, text)")
            conn.commit()

    def index_video(self, slug, url, segments):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO videos (slug, url, title, processed_at) VALUES (?, ?, ?, ?)",
                         (slug, url, slug, datetime.now().isoformat()))
            video_id = cursor.lastrowid
            
            # Clear old segments if any
            cursor.execute("DELETE FROM segments WHERE video_id = ?", (video_id,))
            
            for seg in segments:
                ts_filename = seg['start'].replace(':', '-').replace('.', '-')
                thumbnail_path = f"images/{ts_filename}.jpg"
                cursor.execute("INSERT INTO segments (video_id, start_ts, seconds, text, thumbnail_path) VALUES (?, ?, ?, ?, ?)",
                             (video_id, seg['start'], seg['seconds'], seg['text'], thumbnail_path))
                segment_id = cursor.lastrowid
                cursor.execute("INSERT INTO segments_search (segment_id, text) VALUES (?, ?)", (segment_id, seg['text']))
            conn.commit()
