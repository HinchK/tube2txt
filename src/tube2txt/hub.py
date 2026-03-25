import os
import re
import sqlite3
import uvicorn
from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional

CWD = os.getcwd()
DB_PATH = os.environ.get("TUBE2TXT_DB", os.path.join(CWD, "tube2txt.db"))
PROJECTS_DIR = os.path.join(CWD, "projects")

app = FastAPI(title="Tube2Txt API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Serve projects directory
if os.path.exists(PROJECTS_DIR):
    app.mount("/projects", StaticFiles(directory=PROJECTS_DIR), name="projects")


@app.get("/api/videos")
async def get_videos():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT slug, url, title, processed_at FROM videos ORDER BY processed_at DESC")
    videos = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return videos


@app.get("/api/videos/{slug}")
async def get_video_detail(slug: str):
    conn = get_db()
    cursor = conn.cursor()

    # Get video
    cursor.execute("SELECT slug, url, title, processed_at FROM videos WHERE slug = ?", (slug,))
    video = cursor.fetchone()
    if not video:
        conn.close()
        return JSONResponse(status_code=404, content={"error": "Video not found"})

    video = dict(video)

    # Get segments
    cursor.execute(
        "SELECT start_ts, seconds, text FROM segments WHERE video_id = (SELECT id FROM videos WHERE slug = ?) ORDER BY seconds",
        (slug,),
    )
    video["segments"] = [dict(row) for row in cursor.fetchall()]
    conn.close()

    # Read AI files from disk
    project_dir = os.path.join(PROJECTS_DIR, slug)
    ai_files = []
    if os.path.exists(project_dir):
        import glob
        for md_path in sorted(glob.glob(os.path.join(project_dir, "TUBE2TXT-*.md"))):
            name = re.search(r"TUBE2TXT-(.+)\.md$", os.path.basename(md_path))
            if name:
                with open(md_path, "r", encoding="utf-8") as f:
                    ai_files.append({"name": name.group(1), "content": f.read()})
    video["ai_files"] = ai_files

    return video


@app.get("/api/videos/{slug}/images/{filename}")
async def get_video_image(slug: str, filename: str):
    img_path = os.path.join(PROJECTS_DIR, slug, "images", filename)
    if not os.path.exists(img_path):
        return JSONResponse(status_code=404, content={"error": "Image not found"})
    return FileResponse(img_path)


@app.get("/api/search")
async def search(q: str = Query(...)):
    conn = get_db()
    cursor = conn.cursor()
    query = """
        SELECT s.start_ts, s.seconds, s.text, s.thumbnail_path, v.slug, v.title
        FROM segments s
        JOIN videos v ON s.video_id = v.id
        WHERE s.id IN (
            SELECT segment_id FROM segments_search WHERE segments_search MATCH ?
        )
        LIMIT 20
    """
    cursor.execute(query, (q,))
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def start_hub():
    """Entry point for the hub command."""
    # Serve built TUI assets at root (if available)
    tui_dist = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "tui-dist")
    if not os.path.exists(tui_dist):
        # Fallback for development: check CWD
        tui_dist = os.path.join(CWD, "tui", "dist")
    if os.path.exists(tui_dist):
        app.mount("/", StaticFiles(directory=tui_dist, html=True), name="tui")

    print(f"Starting Tube2Txt API at http://localhost:8000")
    print(f"Database: {DB_PATH}")
    print(f"Projects: {PROJECTS_DIR}")
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    start_hub()
