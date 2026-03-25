# Gridland TUI Integration — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers-extended-cc:subagent-driven-development (if subagents available) or superpowers-extended-cc:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the AlpineJS Hub dashboard with a Gridland TUI backed by a headless FastAPI API with WebSocket support for real-time video processing.

**Architecture:** Gridland (Bun/React/OpenTUI) frontend communicates with FastAPI backend over REST + WebSocket. The existing monolithic `__init__.py` gets a new `process_video()` function extracted from `main()`, adding Python-native yt-dlp download and ffmpeg image extraction. Single Docker container via multi-stage build.

**Tech Stack:** Python 3.9+, FastAPI, WebSockets, Bun, Gridland/OpenTUI, React, TypeScript

**Spec:** `docs/superpowers/specs/2026-03-25-gridland-tui-integration-design.md`

---

## File Map

### Modified Files
| File | Responsibility | Changes |
|------|---------------|---------|
| `src/tube2txt/__init__.py` | Domain classes + CLI | Extract `process_video()`, add `download_video()`, `extract_images()`, keep `main()` as thin CLI |
| `src/tube2txt/hub.py` | FastAPI API server | Strip HTML, add `/api/videos/{slug}`, `/api/videos/{slug}/images/{filename}`, `WS /ws/process`, CORS |
| `pyproject.toml` | Package config | Add `websockets` dep |
| `Dockerfile` | Container build | Multi-stage Bun + Python |
| `docker-compose.yml` | Container orchestration | Update for new Dockerfile |

### New Files
| File | Responsibility |
|------|---------------|
| `tests/test_process_video.py` | Tests for `process_video()`, `download_video()`, `extract_images()` |
| `tests/test_api.py` | Tests for REST + WebSocket endpoints |
| `tui/package.json` | Gridland project config |
| `tui/tsconfig.json` | TypeScript config |
| `tui/src/index.tsx` | App entry, screen router, navigation |
| `tui/src/hooks/useWebSocket.ts` | WebSocket connection + message state |
| `tui/src/hooks/useVideos.ts` | REST data fetching for videos |
| `tui/src/hooks/useSearch.ts` | Debounced FTS5 search |
| `tui/src/screens/ProcessScreen.tsx` | URL input, mode toggle, terminal log |
| `tui/src/screens/DashboardScreen.tsx` | Video list with keyboard nav |
| `tui/src/screens/VideoDetailScreen.tsx` | Transcript + AI content tabs |
| `tui/src/screens/SearchScreen.tsx` | Search input + results |
| `tui/src/components/TerminalLog.tsx` | Scrollable log viewer |
| `tui/src/components/VideoCard.tsx` | Video card for dashboard |
| `tui/src/components/SearchResult.tsx` | Search result row |

---

## Task 0: Extract `download_video()` into `__init__.py`

**Files:**
- Modify: `src/tube2txt/__init__.py`
- Create: `tests/test_process_video.py`

Currently `main()` expects `--vtt` to be passed by an external bash script. We need a Python function that calls yt-dlp to download video + subtitles.

- [ ] **Step 0.1: Write the failing test**

Create `tests/test_process_video.py`:

```python
import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock

def test_download_video_calls_ytdlp():
    """download_video should call yt-dlp and return (video_file, vtt_file)."""
    from tube2txt import download_video

    with tempfile.TemporaryDirectory() as tmpdir:
        mock_result = MagicMock()
        mock_result.returncode = 0

        # Simulate yt-dlp creating files
        def side_effect(*args, **kwargs):
            open(os.path.join(tmpdir, "video.webm"), "w").close()
            open(os.path.join(tmpdir, "video.en.vtt"), "w").close()
            return mock_result

        with patch("subprocess.run", side_effect=side_effect):
            video, vtt = download_video("https://youtube.com/watch?v=test", tmpdir)
            assert video is not None
            assert vtt is not None
            assert vtt.endswith(".vtt")


def test_download_video_returns_none_on_failure():
    """download_video should return (None, None) if yt-dlp fails."""
    from tube2txt import download_video

    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("subprocess.run", side_effect=Exception("yt-dlp not found")):
            video, vtt = download_video("https://youtube.com/watch?v=test", tmpdir)
            assert video is None
            assert vtt is None
```

- [ ] **Step 0.2: Run test to verify it fails**

Run: `cd /Users/hinchk/code/apps/TubedToText && python -m pytest tests/test_process_video.py::test_download_video_calls_ytdlp -v`
Expected: FAIL with `ImportError: cannot import name 'download_video'`

- [ ] **Step 0.3: Implement `download_video()`**

Add to `src/tube2txt/__init__.py` (before `main()`):

```python
import glob as glob_module
import shutil
import concurrent.futures

def download_video(url, output_dir):
    """Download video and subtitles using yt-dlp. Returns (video_file, vtt_file) or (None, None)."""
    os.makedirs(output_dir, exist_ok=True)
    cmd = [
        "yt-dlp", "--no-warnings",
        "--write-auto-subs", "--write-subs",
        "-o", os.path.join(output_dir, "video.%(ext)s"),
        url
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except Exception as e:
        print(f"Error downloading: {e}")
        return None, None

    # Find downloaded files
    video_files = glob_module.glob(os.path.join(output_dir, "video.*"))
    video_files = [f for f in video_files if not f.endswith(".vtt")]
    vtt_files = glob_module.glob(os.path.join(output_dir, "video.*.vtt"))

    video = video_files[0] if video_files else None
    vtt = vtt_files[0] if vtt_files else None
    return video, vtt
```

- [ ] **Step 0.4: Run tests to verify they pass**

Run: `cd /Users/hinchk/code/apps/TubedToText && python -m pytest tests/test_process_video.py -v`
Expected: 2 PASSED

- [ ] **Step 0.5: Commit**

```bash
git add tests/test_process_video.py src/tube2txt/__init__.py
git commit -m "feat: add download_video() Python function wrapping yt-dlp"
```

---

## Task 1: Add `extract_images()` to `__init__.py`

**Files:**
- Modify: `src/tube2txt/__init__.py`
- Modify: `tests/test_process_video.py`

The current code prints `TIMESTAMP:` lines for bash. We need Python-native parallel image extraction via ffmpeg.

- [ ] **Step 1.1: Write the failing test**

Append to `tests/test_process_video.py`:

```python
def test_extract_images_calls_ffmpeg_in_parallel():
    """extract_images should call ffmpeg for each segment in parallel."""
    from tube2txt import extract_images

    segments = [
        {"start": "00:00:01.000", "text": "hello"},
        {"start": "00:00:05.000", "text": "world"},
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        video_path = os.path.join(tmpdir, "video.webm")
        open(video_path, "w").close()
        images_dir = os.path.join(tmpdir, "images")

        call_count = 0
        def mock_run(cmd, **kwargs):
            nonlocal call_count
            call_count += 1
            # Create the output image file
            output_path = cmd[cmd.index("-frames:v") - 3]  # ffmpeg -ss TS -nostdin -i VID -frames:v ...
            # Actually the output path is the positional arg after the input flags
            for i, arg in enumerate(cmd):
                if arg.endswith(".jpg"):
                    open(arg, "w").close()
                    break
            return MagicMock(returncode=0)

        with patch("subprocess.run", side_effect=mock_run):
            extract_images(video_path, segments, images_dir, parallel=2)
            assert call_count == 2
            assert os.path.exists(images_dir)
```

- [ ] **Step 1.2: Run test to verify it fails**

Run: `cd /Users/hinchk/code/apps/TubedToText && python -m pytest tests/test_process_video.py::test_extract_images_calls_ffmpeg_in_parallel -v`
Expected: FAIL with `ImportError: cannot import name 'extract_images'`

- [ ] **Step 1.3: Implement `extract_images()`**

Add to `src/tube2txt/__init__.py` (after `download_video()`):

```python
def _extract_single_image(video_path, ts, output_path):
    """Extract a single frame using ffmpeg."""
    cmd = [
        "ffmpeg", "-ss", ts, "-nostdin", "-i", video_path,
        "-frames:v", "1", "-q:v", "2", "-vf", "scale=1024:-1",
        output_path, "-loglevel", "error", "-y"
    ]
    try:
        subprocess.run(cmd, check=True)
        return True
    except Exception:
        return False


def extract_images(video_path, segments, images_dir, parallel=4):
    """Extract screenshot images for each segment in parallel using ffmpeg."""
    os.makedirs(images_dir, exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=parallel) as executor:
        futures = []
        for seg in segments:
            ts = seg["start"]
            ts_filename = ts.replace(":", "-").replace(".", "-")
            img_path = os.path.join(images_dir, f"{ts_filename}.jpg")
            if not os.path.exists(img_path):
                futures.append(executor.submit(_extract_single_image, video_path, ts, img_path))
        concurrent.futures.wait(futures)
```

- [ ] **Step 1.4: Run tests to verify they pass**

Run: `cd /Users/hinchk/code/apps/TubedToText && python -m pytest tests/test_process_video.py -v`
Expected: 3 PASSED

- [ ] **Step 1.5: Commit**

```bash
git add src/tube2txt/__init__.py tests/test_process_video.py
git commit -m "feat: add extract_images() with parallel ffmpeg execution"
```

---

## Task 2: Extract `process_video()` from `main()`

**Files:**
- Modify: `src/tube2txt/__init__.py`
- Modify: `tests/test_process_video.py`

Extract all processing logic from `main()` into a reusable `process_video()` function with an optional `on_progress` callback.

- [ ] **Step 2.1: Write the failing test**

Append to `tests/test_process_video.py`:

```python
def test_process_video_calls_on_progress():
    """process_video should call on_progress at each step when provided."""
    from tube2txt import process_video

    progress_calls = []
    def on_progress(type_, step, message):
        progress_calls.append((type_, step, message))

    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = os.path.join(tmpdir, "test-slug")
        db_path = os.path.join(tmpdir, "test.db")

        # Create a fake VTT so parsing works
        os.makedirs(project_path, exist_ok=True)
        vtt_path = os.path.join(project_path, "video.en.vtt")
        with open(vtt_path, "w") as f:
            f.write("WEBVTT\n\n00:00:01.000 --> 00:00:03.000\nHello world\n")

        video_path = os.path.join(project_path, "video.webm")
        open(video_path, "w").close()

        with patch("tube2txt.download_video", return_value=(video_path, vtt_path)):
            with patch("tube2txt.extract_images"):
                with patch("tube2txt.GeminiClient") as mock_gc:
                    process_video(
                        url="https://youtube.com/watch?v=test",
                        slug="test-slug",
                        mode="outline",
                        ai_flag=False,
                        db_path=db_path,
                        project_path=project_path,
                        on_progress=on_progress,
                    )

        steps = [c[1] for c in progress_calls]
        assert "download" in steps
        assert "parse" in steps
        assert "html" in steps
        assert "index" in steps
        assert "images" in steps

        # Verify complete message sent
        types = [c[0] for c in progress_calls]
        assert "complete" in types


def test_process_video_works_without_callback():
    """process_video should work with on_progress=None (CLI mode)."""
    from tube2txt import process_video

    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = os.path.join(tmpdir, "test-slug")
        db_path = os.path.join(tmpdir, "test.db")

        os.makedirs(project_path, exist_ok=True)
        vtt_path = os.path.join(project_path, "video.en.vtt")
        with open(vtt_path, "w") as f:
            f.write("WEBVTT\n\n00:00:01.000 --> 00:00:03.000\nHello world\n")

        video_path = os.path.join(project_path, "video.webm")
        open(video_path, "w").close()

        with patch("tube2txt.download_video", return_value=(video_path, vtt_path)):
            with patch("tube2txt.extract_images"):
                result = process_video(
                    url="https://youtube.com/watch?v=test",
                    slug="test-slug",
                    mode="outline",
                    ai_flag=False,
                    db_path=db_path,
                    project_path=project_path,
                )
        assert result == project_path
```

- [ ] **Step 2.2: Run test to verify it fails**

Run: `cd /Users/hinchk/code/apps/TubedToText && python -m pytest tests/test_process_video.py::test_process_video_calls_on_progress -v`
Expected: FAIL with `ImportError: cannot import name 'process_video'`

- [ ] **Step 2.3: Implement `process_video()`**

Add to `src/tube2txt/__init__.py` (after `extract_images()`):

```python
def _notify(on_progress, type_, step, message):
    """Send progress notification via callback or print."""
    if on_progress:
        on_progress(type_, step, message)
    else:
        print(message)


def process_video(url, slug, mode="outline", ai_flag=True, db_path="tube2txt.db",
                  project_path=None, on_progress=None, parallel=4):
    """
    Full video processing pipeline. Returns project_path on success, None on failure.

    on_progress: optional callback (type: str, step: str, message: str) -> None
    """
    if project_path is None:
        project_path = os.path.join("projects", slug)
    os.makedirs(os.path.join(project_path, "images"), exist_ok=True)

    # 1. Download
    _notify(on_progress, "status", "download", "Downloading video and subtitles...")
    video_file, vtt_file = download_video(url, project_path)
    if not video_file or not vtt_file:
        _notify(on_progress, "error", "download", f"Failed to download video or subtitles for {slug}")
        return None

    # 2. Parse VTT
    _notify(on_progress, "status", "parse", "Parsing subtitles...")
    parser = VTTParser(vtt_file)
    segments = parser.parse()

    # 3. Generate HTML
    _notify(on_progress, "status", "html", "Generating HTML...")
    html_gen = HTMLGenerator(segments, url, slug)
    html_gen.generate(os.path.join(project_path, "index.html"))

    # Copy styles.css
    pkg_dir = os.path.dirname(os.path.abspath(__file__))
    styles_src = os.path.join(pkg_dir, "styles.css")
    if not os.path.exists(styles_src):
        styles_src = os.path.join(os.path.dirname(os.path.dirname(pkg_dir)), "styles.css")
    if os.path.exists(styles_src):
        shutil.copy(styles_src, os.path.join(project_path, "styles.css"))

    # 4. DB indexing
    _notify(on_progress, "status", "index", f"Indexing video in database...")
    db = Database(db_path)
    db.index_video(slug, url, segments)

    # 5. AI content
    api_key = os.environ.get("GEMINI_API_KEY")
    if ai_flag and not api_key:
        _notify(on_progress, "status", "ai", "Skipping AI -- GEMINI_API_KEY not set")
    elif ai_flag and api_key:
        client = GeminiClient(api_key)

        _notify(on_progress, "status", "ai", "Generating outline...")
        outline = client.generate_content(segments, mode="outline")
        outline_path = os.path.join(project_path, "TUBE2TXT-OUTLINE.md")
        with open(outline_path, "w", encoding="utf-8") as f:
            f.write(outline)
        _notify(on_progress, "ai_output", "ai", outline)

        best_mode = client.determine_best_mode(outline)
        _notify(on_progress, "status", "ai", f"Generating {best_mode} content...")
        additional = client.generate_content(segments, mode=best_mode)
        add_path = os.path.join(project_path, f"TUBE2TXT-{best_mode.upper()}.md")
        with open(add_path, "w", encoding="utf-8") as f:
            f.write(additional)
        _notify(on_progress, "ai_output", "ai", additional)

        if mode == "clips":
            _notify(on_progress, "status", "ai", "Generating clips...")
            clips = client.generate_content(segments, mode="clips")
            clips_path = os.path.join(project_path, "TUBE2TXT-CLIPS.md")
            with open(clips_path, "w", encoding="utf-8") as f:
                f.write(clips)
            _notify(on_progress, "ai_output", "ai", clips)

    # 6. Extract images
    _notify(on_progress, "status", "images", "Extracting images...")
    extract_images(video_file, segments, os.path.join(project_path, "images"), parallel=parallel)

    _notify(on_progress, "complete", "done", f"Finished processing {slug}")
    return project_path
```

- [ ] **Step 2.4: Refactor `main()` to use `process_video()`**

Replace the processing logic in `main()` (lines 299-370) with:

```python
def main():
    parser = argparse.ArgumentParser(description="Tube2Txt Python Logic")
    parser.add_argument("slug_or_url", nargs="?", help="Project slug or YouTube URL")
    parser.add_argument("url", nargs="?", help="YouTube video URL (if slug provided)")
    parser.add_argument("--vtt", help="Path to existing VTT file (skips download)")
    parser.add_argument("--ai", action="store_true", help="Run AI generation")
    parser.add_argument("--mode", default="outline", help="Requested AI mode")
    parser.add_argument("--parallel", type=int, default=4, help="Parallel image extraction")
    parser.add_argument("--db", default="tube2txt.db", help="Path to SQLite DB")
    parser.add_argument("--projects-dir", default="projects", help="Directory for output")
    parser.add_argument("--clip", help="Manual clip: START-END")
    parser.add_argument("--video-file", help="Video file for manual clipping")

    args = parser.parse_args()

    # Manual Clipping
    if args.clip and args.video_file:
        clip_match = re.match(r'^(\d{2}:\d{2}:\d{2}(?:\.\d+)?)-(\d{2}:\d{2}:\d{2}(?:\.\d+)?)$', args.clip)
        if not clip_match:
            print(f"Error: Invalid clip range format '{args.clip}'. Expected HH:MM:SS-HH:MM:SS")
            sys.exit(1)
        start, end = clip_match.group(1), clip_match.group(2)
        output_name = f"clip_{start.replace(':','-')}_{end.replace(':','-')}.mp4"
        os.makedirs("clips", exist_ok=True)
        if ClippingEngine.extract_clip(args.video_file, start, end, os.path.join("clips", output_name)):
            print(f"CLIP_SAVED:clips/{output_name}")
        sys.exit(0)

    # Resolve URL and slug
    url = args.url
    slug = args.slug_or_url
    if not url:
        if slug and (slug.startswith("http") or len(slug) == 11):
            url = slug
            slug = "default"
        else:
            print("Error: Missing URL.")
            sys.exit(1)

    project_path = os.path.join(args.projects_dir, slug)
    result = process_video(
        url=url,
        slug=slug,
        mode=args.mode,
        ai_flag=args.ai,
        db_path=args.db,
        project_path=project_path,
        parallel=args.parallel,
    )

    if result:
        print(f"\nProject: {os.path.abspath(result)}")
```

- [ ] **Step 2.5: Run all tests**

Run: `cd /Users/hinchk/code/apps/TubedToText && python -m pytest tests/test_process_video.py -v`
Expected: 5 PASSED

- [ ] **Step 2.6: Commit**

```bash
git add src/tube2txt/__init__.py tests/test_process_video.py
git commit -m "feat: extract process_video() from main() with on_progress callback"
```

---

## Task 3: Refactor `hub.py` — Strip HTML, add REST endpoints

**Files:**
- Modify: `src/tube2txt/hub.py`
- Create: `tests/test_api.py`

Strip the AlpineJS dashboard, keep existing `/api/videos` and `/api/search`, add `/api/videos/{slug}` detail endpoint and CORS.

- [ ] **Step 3.1: Write the failing test**

Create `tests/test_api.py`:

```python
import os
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
```

- [ ] **Step 3.2: Run tests to verify they fail**

Run: `cd /Users/hinchk/code/apps/TubedToText && python -m pytest tests/test_api.py::test_get_video_detail -v`
Expected: FAIL (endpoint doesn't exist yet)

- [ ] **Step 3.3: Refactor `hub.py`**

Rewrite `src/tube2txt/hub.py`:

```python
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
    print(f"Starting Tube2Txt API at http://localhost:8000")
    print(f"Database: {DB_PATH}")
    print(f"Projects: {PROJECTS_DIR}")
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    start_hub()
```

- [ ] **Step 3.4: Run tests to verify they pass**

Run: `cd /Users/hinchk/code/apps/TubedToText && python -m pytest tests/test_api.py -v`
Expected: 4 PASSED

- [ ] **Step 3.5: Commit**

```bash
git add src/tube2txt/hub.py tests/test_api.py
git commit -m "refactor: strip Hub HTML, add /api/videos/{slug} detail endpoint and CORS"
```

---

## Task 4: Add WebSocket `/ws/process` endpoint

**Files:**
- Modify: `src/tube2txt/hub.py`
- Modify: `tests/test_api.py`
- Modify: `pyproject.toml`

- [ ] **Step 4.1: Add `websockets` dependency**

In `pyproject.toml`, add `"websockets"` to the dependencies list:

```toml
dependencies = [
    "google-genai",
    "python-dotenv",
    "fastapi",
    "uvicorn",
    "yt-dlp",
    "websockets",
]
```

Run: `cd /Users/hinchk/code/apps/TubedToText && pip install -e .`

- [ ] **Step 4.2: Write the failing test**

Append to `tests/test_api.py`:

```python
import json

def test_websocket_process_sends_progress(client, test_env):
    """WebSocket should stream progress messages during processing."""
    from unittest.mock import AsyncMock

    with patch("tube2txt.hub.process_video") as mock_pv:
        # Simulate process_video calling on_progress
        def fake_process(url, slug, mode, ai_flag, db_path, project_path, on_progress, parallel):
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


def test_websocket_rejects_concurrent_jobs(client, test_env):
    """WebSocket should reject a second job while one is running."""
    import threading
    import time

    with patch("tube2txt.hub.process_video") as mock_pv:
        def slow_process(**kwargs):
            time.sleep(1)
            kwargs["on_progress"]("complete", "done", "Done")
            return "projects/test"

        mock_pv.side_effect = lambda **kwargs: slow_process(**kwargs)

        with client.websocket_connect("/ws/process") as ws:
            ws.send_json({"action": "start", "slug": "job1", "url": "https://youtube.com/watch?v=1", "ai": False, "mode": "outline"})
            # Try to start second job immediately
            ws.send_json({"action": "start", "slug": "job2", "url": "https://youtube.com/watch?v=2", "ai": False, "mode": "outline"})

            msgs = []
            while True:
                data = ws.receive_json()
                msgs.append(data)
                if data.get("type") == "complete":
                    break

            error_msgs = [m for m in msgs if m.get("type") == "error"]
            assert len(error_msgs) >= 1
            assert "already" in error_msgs[0]["message"].lower()
```

- [ ] **Step 4.3: Run tests to verify they fail**

Run: `cd /Users/hinchk/code/apps/TubedToText && python -m pytest tests/test_api.py::test_websocket_process_sends_progress -v`
Expected: FAIL (endpoint doesn't exist)

- [ ] **Step 4.4: Implement WebSocket endpoint**

Add to `src/tube2txt/hub.py` (before `start_hub()`):

```python
import json
import asyncio
import threading
from tube2txt import process_video

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
                slug = data["slug"]
                url = data["url"]
                ai_flag = data.get("ai", False)
                mode = data.get("mode", "outline")
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
                        db_path=DB_PATH,
                        project_path=project_path,
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
```

- [ ] **Step 4.5: Run tests to verify they pass**

Run: `cd /Users/hinchk/code/apps/TubedToText && python -m pytest tests/test_api.py -v`
Expected: 6 PASSED

- [ ] **Step 4.6: Commit**

```bash
git add src/tube2txt/hub.py tests/test_api.py pyproject.toml
git commit -m "feat: add WebSocket /ws/process endpoint with progress streaming"
```

---

## Task 5: Scaffold Gridland TUI project

**Files:**
- Create: `tui/package.json`
- Create: `tui/tsconfig.json`
- Create: `tui/src/index.tsx`

- [ ] **Step 5.1: Initialize Gridland project**

```bash
cd /Users/hinchk/code/apps/TubedToText
mkdir -p tui/src/hooks tui/src/screens tui/src/components
```

- [ ] **Step 5.2: Create `tui/package.json`**

```json
{
  "name": "tube2txt-tui",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "bun run src/index.tsx",
    "build": "bun build src/index.tsx --outdir dist"
  },
  "dependencies": {
    "@gridland/core": "latest",
    "@opentui/react": "latest",
    "react": "^19.0.0"
  },
  "devDependencies": {
    "@types/react": "^19.0.0",
    "typescript": "^5.0.0"
  }
}
```

- [ ] **Step 5.3: Create `tui/tsconfig.json`**

```json
{
  "compilerOptions": {
    "target": "ESNext",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "strict": true,
    "esModuleInterop": true,
    "outDir": "dist",
    "rootDir": "src"
  },
  "include": ["src"]
}
```

- [ ] **Step 5.4: Create `tui/src/index.tsx` — App entry with navigation**

```tsx
import React, { useState } from "react";
import { Box, Text } from "@opentui/react";
import { render } from "@gridland/core";
import { ProcessScreen } from "./screens/ProcessScreen";
import { DashboardScreen } from "./screens/DashboardScreen";
import { SearchScreen } from "./screens/SearchScreen";
import { VideoDetailScreen } from "./screens/VideoDetailScreen";

type Screen = "process" | "dashboard" | "search" | "detail";

function App() {
  const [screen, setScreen] = useState<Screen>("process");
  const [selectedSlug, setSelectedSlug] = useState<string | null>(null);
  const [wsStatus, setWsStatus] = useState("disconnected");

  const navigateToDetail = (slug: string) => {
    setSelectedSlug(slug);
    setScreen("detail");
  };

  return (
    <Box flexDirection="column" width="100%">
      {/* Navigation bar */}
      <Box paddingX={1} borderStyle="single" borderBottom>
        <Text bold color="cyan">tube2txt</Text>
        <Text>  </Text>
        <Text inverse={screen === "process"} onClick={() => setScreen("process")}> [1] Process </Text>
        <Text inverse={screen === "dashboard"} onClick={() => setScreen("dashboard")}> [2] Dashboard </Text>
        <Text inverse={screen === "search"} onClick={() => setScreen("search")}> [3] Search </Text>
        <Box flexGrow={1} />
        <Text dimColor>ws: {wsStatus}</Text>
      </Box>

      {/* Screen content */}
      <Box flexGrow={1} padding={1}>
        {screen === "process" && <ProcessScreen onWsStatusChange={setWsStatus} />}
        {screen === "dashboard" && <DashboardScreen onSelectVideo={navigateToDetail} />}
        {screen === "search" && <SearchScreen onSelectResult={navigateToDetail} />}
        {screen === "detail" && selectedSlug && (
          <VideoDetailScreen slug={selectedSlug} onBack={() => setScreen("dashboard")} />
        )}
      </Box>
    </Box>
  );
}

render(<App />);
```

- [ ] **Step 5.5: Install dependencies**

```bash
cd /Users/hinchk/code/apps/TubedToText/tui && bun install
```

- [ ] **Step 5.6: Commit**

```bash
cd /Users/hinchk/code/apps/TubedToText
git add tui/package.json tui/tsconfig.json tui/src/index.tsx tui/bun.lockb
git commit -m "feat: scaffold Gridland TUI project with navigation shell"
```

---

## Task 6: Implement TUI hooks

**Files:**
- Create: `tui/src/hooks/useWebSocket.ts`
- Create: `tui/src/hooks/useVideos.ts`
- Create: `tui/src/hooks/useSearch.ts`

- [ ] **Step 6.1: Create `useWebSocket.ts`**

```typescript
import { useState, useEffect, useCallback, useRef } from "react";

interface WsMessage {
  type: string;
  step?: string;
  message?: string;
  content?: string;
}

interface UseWebSocketReturn {
  send: (data: Record<string, unknown>) => void;
  messages: WsMessage[];
  status: "connected" | "disconnected" | "reconnecting";
  clearMessages: () => void;
}

export function useWebSocket(url: string): UseWebSocketReturn {
  const [messages, setMessages] = useState<WsMessage[]>([]);
  const [status, setStatus] = useState<UseWebSocketReturn["status"]>("disconnected");
  const wsRef = useRef<WebSocket | null>(null);
  const retryRef = useRef(0);

  const connect = useCallback(() => {
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setStatus("connected");
      retryRef.current = 0;
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data) as WsMessage;
      setMessages((prev) => [...prev, data]);
    };

    ws.onclose = () => {
      setStatus("reconnecting");
      const delay = Math.min(1000 * 2 ** retryRef.current, 30000);
      retryRef.current++;
      setTimeout(connect, delay);
    };

    ws.onerror = () => ws.close();
  }, [url]);

  useEffect(() => {
    connect();
    return () => wsRef.current?.close();
  }, [connect]);

  const send = useCallback((data: Record<string, unknown>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  }, []);

  const clearMessages = useCallback(() => setMessages([]), []);

  return { send, messages, status, clearMessages };
}
```

- [ ] **Step 6.2: Create `useVideos.ts`**

```typescript
import { useState, useEffect, useCallback } from "react";

const API_BASE = "http://localhost:8000";

interface Video {
  slug: string;
  url: string;
  title: string;
  processed_at: string;
}

interface VideoDetail extends Video {
  segments: Array<{ start_ts: string; seconds: number; text: string }>;
  ai_files: Array<{ name: string; content: string }>;
}

interface UseVideosReturn {
  videos: Video[];
  selectedVideo: VideoDetail | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
  fetchDetail: (slug: string) => Promise<void>;
}

export function useVideos(): UseVideosReturn {
  const [videos, setVideos] = useState<Video[]>([]);
  const [selectedVideo, setSelectedVideo] = useState<VideoDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchVideos = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/videos`);
      setVideos(await res.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to fetch videos");
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchDetail = useCallback(async (slug: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/videos/${slug}`);
      if (!res.ok) throw new Error("Video not found");
      setSelectedVideo(await res.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to fetch video");
      setSelectedVideo(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchVideos();
  }, [fetchVideos]);

  return { videos, selectedVideo, loading, error, refetch: fetchVideos, fetchDetail };
}
```

- [ ] **Step 6.3: Create `useSearch.ts`**

```typescript
import { useState, useEffect, useRef } from "react";

const API_BASE = "http://localhost:8000";

interface SearchResult {
  slug: string;
  title: string;
  start_ts: string;
  seconds: number;
  text: string;
  thumbnail_path: string;
}

interface UseSearchReturn {
  results: SearchResult[];
  loading: boolean;
  error: string | null;
}

export function useSearch(query: string): UseSearchReturn {
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout>>();

  useEffect(() => {
    if (timerRef.current) clearTimeout(timerRef.current);

    if (query.length < 2) {
      setResults([]);
      return;
    }

    timerRef.current = setTimeout(async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(`${API_BASE}/api/search?q=${encodeURIComponent(query)}`);
        setResults(await res.json());
      } catch (e) {
        setError(e instanceof Error ? e.message : "Search failed");
      } finally {
        setLoading(false);
      }
    }, 300);

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [query]);

  return { results, loading, error };
}
```

- [ ] **Step 6.4: Commit**

```bash
cd /Users/hinchk/code/apps/TubedToText
git add tui/src/hooks/
git commit -m "feat: add useWebSocket, useVideos, useSearch hooks"
```

---

## Task 7: Implement TUI screens

**Files:**
- Create: `tui/src/screens/ProcessScreen.tsx`
- Create: `tui/src/screens/DashboardScreen.tsx`
- Create: `tui/src/screens/VideoDetailScreen.tsx`
- Create: `tui/src/screens/SearchScreen.tsx`
- Create: `tui/src/components/TerminalLog.tsx`
- Create: `tui/src/components/VideoCard.tsx`
- Create: `tui/src/components/SearchResult.tsx`

This is the largest task. Each screen is implemented as a focused React component using OpenTUI primitives.

- [ ] **Step 7.1: Create `TerminalLog.tsx`**

```tsx
import React from "react";
import { Box, Text, ScrollBox } from "@opentui/react";

interface Message {
  type: string;
  step?: string;
  message?: string;
}

export function TerminalLog({ messages }: { messages: Message[] }) {
  return (
    <ScrollBox flexGrow={1} borderStyle="single">
      {messages.map((msg, i) => {
        const prefix = msg.type === "error" ? "!" : ">";
        const color = msg.type === "error" ? "red" : msg.type === "complete" ? "green" : "cyan";
        return (
          <Text key={i} color={color}>
            {prefix} {msg.message || ""}
          </Text>
        );
      })}
      {messages.length === 0 && <Text dimColor>Waiting for job...</Text>}
    </ScrollBox>
  );
}
```

- [ ] **Step 7.2: Create `VideoCard.tsx`**

```tsx
import React from "react";
import { Box, Text } from "@opentui/react";

interface Props {
  slug: string;
  title: string;
  processedAt: string;
  selected: boolean;
  onSelect: () => void;
}

export function VideoCard({ slug, title, processedAt, selected, onSelect }: Props) {
  return (
    <Box
      borderStyle="single"
      borderColor={selected ? "cyan" : undefined}
      paddingX={1}
      onClick={onSelect}
    >
      <Box flexDirection="column" flexGrow={1}>
        <Text bold>{title}</Text>
        <Text dimColor>{slug} | {processedAt}</Text>
      </Box>
    </Box>
  );
}
```

- [ ] **Step 7.3: Create `SearchResult.tsx`**

```tsx
import React from "react";
import { Box, Text } from "@opentui/react";

interface Props {
  slug: string;
  startTs: string;
  text: string;
  query: string;
  selected: boolean;
  onSelect: () => void;
}

export function SearchResult({ slug, startTs, text, query, selected, onSelect }: Props) {
  return (
    <Box
      borderStyle="single"
      borderColor={selected ? "cyan" : undefined}
      paddingX={1}
      onClick={onSelect}
    >
      <Box flexDirection="column">
        <Text>
          <Text bold>{slug}</Text> <Text color="cyan">[{startTs}]</Text>
        </Text>
        <Text>{text}</Text>
      </Box>
    </Box>
  );
}
```

- [ ] **Step 7.4: Create `ProcessScreen.tsx`**

```tsx
import React, { useState } from "react";
import { Box, Text, Input, Select } from "@opentui/react";
import { useWebSocket } from "../hooks/useWebSocket";
import { TerminalLog } from "../components/TerminalLog";

const MODES = ["outline", "notes", "recipe", "technical", "clips"];
const WS_URL = "ws://localhost:8000/ws/process";

interface Props {
  onWsStatusChange: (status: string) => void;
}

export function ProcessScreen({ onWsStatusChange }: Props) {
  const [url, setUrl] = useState("");
  const [slug, setSlug] = useState("");
  const [mode, setMode] = useState("outline");
  const [isRunning, setIsRunning] = useState(false);
  const { send, messages, status, clearMessages } = useWebSocket(WS_URL);

  React.useEffect(() => onWsStatusChange(status), [status, onWsStatusChange]);

  // Detect job completion
  React.useEffect(() => {
    const last = messages[messages.length - 1];
    if (last?.type === "complete" || last?.type === "error") {
      setIsRunning(false);
    }
  }, [messages]);

  const startJob = () => {
    if (!url || !slug || isRunning) return;
    clearMessages();
    setIsRunning(true);
    send({ action: "start", slug, url, ai: true, mode });
  };

  return (
    <Box flexDirection="column" flexGrow={1}>
      <Box flexDirection="column" gap={1}>
        <Box>
          <Text>URL:  </Text>
          <Input value={url} onChange={setUrl} placeholder="https://youtube.com/watch?v=..." />
        </Box>
        <Box>
          <Text>Slug: </Text>
          <Input value={slug} onChange={setSlug} placeholder="my-video" />
        </Box>
        <Box>
          <Text>Mode: </Text>
          <Select items={MODES} value={mode} onChange={setMode} />
        </Box>
        <Box>
          <Text
            bold
            color={isRunning ? "gray" : "green"}
            onClick={isRunning ? undefined : startJob}
          >
            {isRunning ? "[ Processing... ]" : "[ Start Processing ]"}
          </Text>
        </Box>
      </Box>
      <Box marginTop={1} flexGrow={1}>
        <TerminalLog messages={messages} />
      </Box>
    </Box>
  );
}
```

- [ ] **Step 7.5: Create `DashboardScreen.tsx`**

```tsx
import React, { useState } from "react";
import { Box, Text } from "@opentui/react";
import { useVideos } from "../hooks/useVideos";
import { VideoCard } from "../components/VideoCard";

interface Props {
  onSelectVideo: (slug: string) => void;
}

export function DashboardScreen({ onSelectVideo }: Props) {
  const { videos, loading, error } = useVideos();
  const [selectedIdx, setSelectedIdx] = useState(0);

  if (loading) return <Text>Loading...</Text>;
  if (error) return <Text color="red">{error}</Text>;
  if (videos.length === 0) {
    return <Text dimColor>No videos yet. Press [1] to process your first video.</Text>;
  }

  return (
    <Box flexDirection="column">
      <Text dimColor>{videos.length} video{videos.length !== 1 ? "s" : ""} processed</Text>
      <Box flexDirection="column" marginTop={1}>
        {videos.map((v, i) => (
          <VideoCard
            key={v.slug}
            slug={v.slug}
            title={v.title}
            processedAt={v.processed_at}
            selected={i === selectedIdx}
            onSelect={() => onSelectVideo(v.slug)}
          />
        ))}
      </Box>
      <Text dimColor marginTop={1}>Click to view detail | o: open in browser</Text>
    </Box>
  );
}
```

- [ ] **Step 7.6: Create `VideoDetailScreen.tsx`**

```tsx
import React, { useState, useEffect } from "react";
import { Box, Text, ScrollBox } from "@opentui/react";
import { useVideos } from "../hooks/useVideos";

interface Props {
  slug: string;
  onBack: () => void;
}

export function VideoDetailScreen({ slug, onBack }: Props) {
  const { selectedVideo, loading, error, fetchDetail } = useVideos();
  const [activeTab, setActiveTab] = useState(0);

  useEffect(() => {
    fetchDetail(slug);
  }, [slug, fetchDetail]);

  if (loading) return <Text>Loading...</Text>;
  if (error) return <Text color="red">{error}</Text>;
  if (!selectedVideo) return <Text>Not found</Text>;

  const tabs = [
    { name: "Transcript", content: null },
    ...selectedVideo.ai_files.map((f) => ({ name: f.name, content: f.content })),
  ];

  return (
    <Box flexDirection="column" flexGrow={1}>
      {/* Header */}
      <Box flexDirection="column" marginBottom={1}>
        <Text bold>{selectedVideo.title}</Text>
        <Text dimColor>{selectedVideo.slug} | {selectedVideo.url} | {selectedVideo.processed_at}</Text>
      </Box>

      {/* Tabs */}
      <Box marginBottom={1}>
        {tabs.map((tab, i) => (
          <Text
            key={tab.name}
            inverse={i === activeTab}
            onClick={() => setActiveTab(i)}
          >
            {` ${tab.name} `}
          </Text>
        ))}
      </Box>

      {/* Content */}
      <ScrollBox flexGrow={1} borderStyle="single">
        {activeTab === 0
          ? selectedVideo.segments.map((seg, i) => (
              <Text key={i}>
                <Text color="cyan">[{seg.start_ts}]</Text> {seg.text}
              </Text>
            ))
          : <Text>{tabs[activeTab]?.content}</Text>
        }
      </ScrollBox>

      <Text dimColor marginTop={1}>Tab: switch | o: open in browser | Esc: back</Text>
    </Box>
  );
}
```

- [ ] **Step 7.7: Create `SearchScreen.tsx`**

```tsx
import React, { useState } from "react";
import { Box, Text, Input } from "@opentui/react";
import { useSearch } from "../hooks/useSearch";
import { SearchResult } from "../components/SearchResult";

interface Props {
  onSelectResult: (slug: string) => void;
}

export function SearchScreen({ onSelectResult }: Props) {
  const [query, setQuery] = useState("");
  const { results, loading, error } = useSearch(query);
  const [selectedIdx, setSelectedIdx] = useState(0);

  return (
    <Box flexDirection="column" flexGrow={1}>
      <Box>
        <Text>Search: </Text>
        <Input value={query} onChange={setQuery} placeholder="Search transcripts..." />
      </Box>

      {loading && <Text dimColor marginTop={1}>Searching...</Text>}
      {error && <Text color="red" marginTop={1}>{error}</Text>}

      {!loading && results.length === 0 && query.length >= 2 && (
        <Text dimColor marginTop={1}>No results.</Text>
      )}

      <Box flexDirection="column" marginTop={1}>
        {results.map((r, i) => (
          <SearchResult
            key={`${r.slug}-${r.start_ts}`}
            slug={r.slug}
            startTs={r.start_ts}
            text={r.text}
            query={query}
            selected={i === selectedIdx}
            onSelect={() => onSelectResult(r.slug)}
          />
        ))}
      </Box>
    </Box>
  );
}
```

- [ ] **Step 7.8: Verify TUI builds**

```bash
cd /Users/hinchk/code/apps/TubedToText/tui && bun run build
```
Expected: Build succeeds, output in `tui/dist/`

- [ ] **Step 7.9: Commit**

```bash
cd /Users/hinchk/code/apps/TubedToText
git add tui/src/
git commit -m "feat: implement all TUI screens and components"
```

---

## Task 8: Update Dockerfile for multi-stage build

**Files:**
- Modify: `Dockerfile`
- Modify: `docker-compose.yml`

- [ ] **Step 8.1: Rewrite `Dockerfile`**

```dockerfile
# Stage 1: Build Gridland TUI
FROM oven/bun:1 AS tui-builder
WORKDIR /tui
COPY tui/package.json tui/bun.lockb ./
RUN bun install --frozen-lockfile
COPY tui/ .
RUN bun run build

# Stage 2: Python runtime
FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

RUN curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp && \
    chmod a+rx /usr/local/bin/yt-dlp

WORKDIR /app

COPY src/ ./src/
COPY pyproject.toml .
COPY README.md .
COPY styles.css .

RUN pip install --no-cache-dir .

# Copy built TUI assets
COPY --from=tui-builder /tui/dist ./tui-dist/

RUN mkdir -p /app/projects

EXPOSE 8000

CMD ["tube2txt-hub"]
```

- [ ] **Step 8.2: Update `docker-compose.yml`**

Read current file, ensure it references the new Dockerfile correctly. Remove any references to `tube2txt.sh`.

- [ ] **Step 8.3: Verify Docker build**

```bash
cd /Users/hinchk/code/apps/TubedToText && docker build -t tube2txt .
```
Expected: Build succeeds

- [ ] **Step 8.4: Commit**

```bash
git add Dockerfile docker-compose.yml
git commit -m "feat: multi-stage Dockerfile with Bun TUI build + Python runtime"
```

---

## Task 9: Integration test — end-to-end WebSocket flow

**Files:**
- Modify: `tests/test_api.py`

- [ ] **Step 9.1: Write integration test**

Append to `tests/test_api.py`:

```python
def test_integration_process_and_fetch(test_env):
    """Full flow: process via WebSocket, then fetch via REST."""
    with patch.dict(os.environ, {"TUBE2TXT_DB": test_env["db_path"]}):
        import tube2txt.hub as hub_module
        hub_module.DB_PATH = test_env["db_path"]
        hub_module.PROJECTS_DIR = test_env["projects_dir"]

        from fastapi.testclient import TestClient
        test_client = TestClient(hub_module.app)

        with patch("tube2txt.hub.process_video") as mock_pv:
            slug = "integration-test"

            def fake_process(**kwargs):
                # Simulate creating project artifacts
                project_path = kwargs["project_path"]
                os.makedirs(project_path, exist_ok=True)
                with open(os.path.join(project_path, "TUBE2TXT-OUTLINE.md"), "w") as f:
                    f.write("# Test Outline")

                # Seed DB
                conn = sqlite3.connect(test_env["db_path"])
                conn.execute("INSERT OR REPLACE INTO videos (slug, url, title, processed_at) VALUES (?, ?, ?, ?)",
                             (slug, "https://test.com", "Integration Test", "2026-03-25"))
                conn.commit()
                conn.close()

                cb = kwargs["on_progress"]
                cb("status", "download", "Downloading...")
                cb("complete", "done", "Done")
                return project_path

            mock_pv.side_effect = fake_process

            # 1. Process via WebSocket
            with test_client.websocket_connect("/ws/process") as ws:
                ws.send_json({"action": "start", "slug": slug, "url": "https://test.com", "ai": False, "mode": "outline"})
                msgs = []
                while True:
                    data = ws.receive_json()
                    msgs.append(data)
                    if data["type"] in ("complete", "error"):
                        break
                assert msgs[-1]["type"] == "complete"

            # 2. Fetch via REST
            res = test_client.get(f"/api/videos/{slug}")
            assert res.status_code == 200
            data = res.json()
            assert data["slug"] == slug
            assert len(data["ai_files"]) == 1
            assert data["ai_files"][0]["name"] == "OUTLINE"
```

- [ ] **Step 9.2: Run all tests**

Run: `cd /Users/hinchk/code/apps/TubedToText && python -m pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 9.3: Commit**

```bash
git add tests/test_api.py
git commit -m "test: add integration test for WebSocket process + REST fetch flow"
```

---

## Task 10: Update CLAUDE.md and clean up

**Files:**
- Modify: `CLAUDE.md`
- Modify: `GEMINI.md`

- [ ] **Step 10.1: Update CLAUDE.md**

Add the `tui/` directory to the architecture section. Update commands to mention `bun install` and `bun run dev` for the TUI. Note the WebSocket endpoint.

- [ ] **Step 10.2: Update GEMINI.md**

Mirror the same updates for consistency.

- [ ] **Step 10.3: Final commit**

```bash
git add CLAUDE.md GEMINI.md
git commit -m "docs: update project docs for Gridland TUI integration"
```
