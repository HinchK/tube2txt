import os
import sys
import re
import json
import sqlite3
import shlex
import asyncio
import threading
import subprocess
import uvicorn
from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from tube2txt import process_video, Database

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

# Ensure schema exists before serving any requests
Database(DB_PATH)


@app.get("/healthcheck")
async def healthcheck():
    return {"status": "ok"}


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


_job_lock = threading.Lock()
_job_running = False


@app.websocket("/ws/process")
async def ws_process(websocket: WebSocket):
    global _job_running
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("action") != "start":
                continue

            if not _job_lock.acquire(blocking=False):
                await websocket.send_json({"type": "error", "message": "A job is already in progress"})
                continue

            _job_running = True
            loop = asyncio.get_event_loop()

            try:
                command = data.get("command")
                if not command:
                    raise ValueError("No command provided")

                # Parse the command safely
                parsed_args = shlex.split(command)
                
                # If they included "tube2txt" at the start, replace it with module execution
                if parsed_args and parsed_args[0] == "tube2txt":
                    parsed_args = [sys.executable, "-m", "tube2txt"] + parsed_args[1:]
                elif parsed_args and parsed_args[0] != sys.executable:
                    parsed_args = [sys.executable, "-m", "tube2txt"] + parsed_args

                def run_cmd():
                    # Run as a subprocess, capture stdout/stderr
                    process = subprocess.Popen(
                        parsed_args,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1
                    )
                    
                    for line in process.stdout:
                        line = line.strip()
                        if not line:
                            continue
                        # Send line to websocket
                        asyncio.run_coroutine_threadsafe(
                            websocket.send_json({"type": "status", "message": line}),
                            loop,
                        )
                        
                    process.wait()
                    if process.returncode == 0:
                        asyncio.run_coroutine_threadsafe(
                            websocket.send_json({"type": "complete", "message": "Job finished successfully."}),
                            loop,
                        )
                    else:
                        asyncio.run_coroutine_threadsafe(
                            websocket.send_json({"type": "error", "message": f"Process exited with code {process.returncode}"}),
                            loop,
                        )

                await loop.run_in_executor(None, run_cmd)
            except Exception as e:
                await websocket.send_json({"type": "error", "message": str(e)})
            finally:
                _job_running = False
                _job_lock.release()

    except WebSocketDisconnect:
        pass


def start_hub():
    """Entry point for the hub command."""
    # Serve built TUI assets at root (if available)
    # Search order: /app/static (Docker), ./static (local), ./tui/dist (dev fallback)
    tui_dist = os.path.join(CWD, "static")
    if not os.path.exists(tui_dist):
        tui_dist = os.path.join(CWD, "tui", "dist")

    if os.path.exists(tui_dist):
        print(f"Serving TUI from: {tui_dist}")

        # Handle SPA fallback and static files
        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str = ""):
            # If it's an API or WS route, but we got here, it's a 404 for the API
            if full_path.startswith("api/") or full_path.startswith("ws/"):
                return JSONResponse(status_code=404, content={"error": "Not found"})

            # Root path
            if not full_path or full_path == "":
                return FileResponse(os.path.join(tui_dist, "index.html"))

            # Check if it's a file that exists in the dist directory
            file_path = os.path.join(tui_dist, full_path)
            if os.path.isfile(file_path):
                return FileResponse(file_path)

            # Fallback to index.html for SPA (client-side routing)
            return FileResponse(os.path.join(tui_dist, "index.html"))
    else:
        print("Warning: TUI dist directory not found. Serving API only.")

    # Ensure database is initialized
    print(f"Initializing database at {DB_PATH}")
    Database(DB_PATH)

    port = int(os.environ.get("PORT", 8000))
    print(f"Starting Tube2Txt API at http://0.0.0.0:{port}")
    print(f"Database: {DB_PATH}")
    print(f"Projects: {PROJECTS_DIR}")
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    start_hub()
