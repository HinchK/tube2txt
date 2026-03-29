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
from tube2txt import process_video, Database, get_parser

CWD = os.getcwd()
DB_PATH = os.environ.get("TUBE2TXT_DB", os.path.join(CWD, "tube2txt.db"))
PROJECTS_DIR = os.path.join(CWD, "projects")
TUI_DIST_DIR = os.environ.get("TUBE2TXT_TUI_DIR")

app = FastAPI(title="Tube2Txt API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    print(f"--- Tube2Txt Hub Starting ---")
    print(f"CWD: {CWD}")
    print(f"Database Path: {DB_PATH}")
    print(f"Projects Dir: {PROJECTS_DIR}")
    
    # Ensure database is initialized
    try:
        Database(DB_PATH)
        print("✓ Database initialized")
    except Exception as e:
        print(f"× Database initialization failed: {e}")
        # We don't exit here to allow healthcheck to still run
    
    # Ensure projects dir exists
    if not os.path.exists(PROJECTS_DIR):
        os.makedirs(PROJECTS_DIR, exist_ok=True)
        print(f"✓ Created projects directory at {PROJECTS_DIR}")


@app.get("/healthcheck")
async def healthcheck():
    return {"status": "ok", "db": DB_PATH}


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Serve projects directory
if os.path.exists(PROJECTS_DIR):
    app.mount("/projects", StaticFiles(directory=PROJECTS_DIR), name="projects")


@app.get("/api/videos")
async def get_videos():
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT slug, url, title, processed_at FROM videos ORDER BY processed_at DESC")
        videos = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return videos
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/api/videos/{slug}")
async def get_video_detail(slug: str):
    try:
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
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/api/videos/{slug}/images/{filename}")
async def get_video_image(slug: str, filename: str):
    img_path = os.path.join(PROJECTS_DIR, slug, "images", filename)
    if not os.path.exists(img_path):
        return JSONResponse(status_code=404, content={"error": "Image not found"})
    return FileResponse(img_path)


@app.get("/api/search")
async def search(q: str = Query(...)):
    try:
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
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


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
                # Handle both 'command' string and structured fields
                command = data.get("command")
                
                url = data.get("url")
                slug = data.get("slug", "default")
                mode = data.get("mode", "outline")
                ai_flag = data.get("ai", True)
                parallel = data.get("parallel", 4)
                db_path = DB_PATH # Use the default hub DB path

                if not command and not url:
                    raise ValueError("No command or URL provided")

                if command:
                    # Parse the command safely
                    parsed_args = shlex.split(command)
                    
                    # If they included "tube2txt" at the start, remove it
                    if parsed_args and parsed_args[0] == "tube2txt":
                        parsed_args = parsed_args[1:]
                    
                    # Use the project's own parser
                    parser = get_parser()
                    args, unknown = parser.parse_known_args(parsed_args)
                    
                    # Resolve URL and slug exactly like main()
                    url = args.url or url
                    slug = args.slug_or_url or slug
                    mode = getattr(args, "mode", mode)
                    ai_flag = getattr(args, "ai", ai_flag)
                    parallel = getattr(args, "parallel", parallel)
                    db_path = getattr(args, "db", DB_PATH)

                # Final URL/slug resolution logic matches CLI
                if not url:
                    if slug and (slug.startswith("http") or len(slug) == 11):
                        url = slug
                        slug = "default"
                    else:
                        raise ValueError("Missing URL")

                project_path = os.path.join(PROJECTS_DIR, slug)

                def on_progress(type_, step, message):
                    asyncio.run_coroutine_threadsafe(
                        websocket.send_json({"type": type_, "step": step, "message": message}),
                        loop,
                    )

                await loop.run_in_executor(
                    None,
                    lambda: process_video(
                        url=url,
                        slug=slug,
                        mode=mode,
                        ai_flag=ai_flag,
                        db_path=db_path,
                        project_path=project_path,
                        parallel=parallel,
                        on_progress=on_progress,
                    ),
                )
            except Exception as e:
                await websocket.send_json({"type": "error", "message": str(e)})
            finally:
                _job_running = False
                _job_lock.release()

    except WebSocketDisconnect:
        pass


# TUI Asset Detection & Mounting
tui_dist = TUI_DIST_DIR
if not tui_dist:
    paths_to_check = [
        os.path.join(CWD, "static"),
        os.path.join(CWD, "tui", "dist"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "tui", "dist")
    ]
    for p in paths_to_check:
        if os.path.exists(p):
            tui_dist = p
            break

if tui_dist and os.path.exists(tui_dist):
    print(f"✓ Found TUI assets at: {tui_dist}")
    
    # Handle SPA fallback and static files
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str = ""):
        # If it's an API or WS route, but we got here, it's a 404 for the API
        if full_path.startswith("api/") or full_path.startswith("ws/"):
            return JSONResponse(status_code=404, content={"error": "Not found"})

        # Check if it's a file that exists in the dist directory
        file_path = os.path.join(tui_dist, full_path)
        if full_path and os.path.isfile(file_path):
            return FileResponse(file_path)

        # Fallback to index.html for SPA (client-side routing)
        index_path = os.path.join(tui_dist, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        
        return JSONResponse(status_code=404, content={"error": "index.html not found"})
else:
    print("! Warning: TUI dist directory not found. Serving API only.")


def start_hub():
    """Entry point for the hub command."""
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting Tube2Txt Hub at http://0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    start_hub()


if __name__ == "__main__":
    start_hub()
