# AI Assistant Guide for Tube2Txt v3

This file serves as the system rules, context, and orientation guide for any AI (like Gemini, Claude, or ChatGPT) assisting with this repository. Whenever you begin a new session, refer to this document.

## Project Context

**Name:** Tube2Txt v3
**Purpose:** A CLI tool to convert YouTube videos and playlists into structured web pages with transcripts and screenshots, with AI-assisted markdown analysis powered by Gemini. Includes a local hub dashboard and smart clip extraction.
**Tech Stack:** Python 3.9+, `yt-dlp`, `ffmpeg`, `google-genai` API, FastAPI + uvicorn (hub), SQLite with FTS5 (search).

**Background:** This is a rewrite of a legacy script (`Youtube2Webpage`). The main goal is fast performance, clean architecture, zero-bloat dependencies (no massive frontend frameworks like React/Vue, just plain HTML/Vanilla CSS for generated pages), and seamless AI content extraction.

## Core Files & Architecture

The project is structured as a Python package under `src/tube2txt/`:

- `src/tube2txt/__init__.py`: The main CLI entry point.
  - Parses arguments via `argparse` (slug, URL, `--ai`, `--mode`, `--clip`, `--parallel`, etc.).
  - Orchestrates the full pipeline: download -> parse -> generate HTML -> AI content -> image extraction.
  - Loads `.env` for `GEMINI_API_KEY` via `python-dotenv`.
  - Detects if the URL is a single video or a playlist.
  - Uses `concurrent.futures.ThreadPoolExecutor` for parallel screenshot extraction.
  - Supports `--mode clips` for AI-recommended clip extraction.
- `src/tube2txt/downloader.py`: `Downloader` class wrapping `yt-dlp`.
  - Downloads video, subtitles, and extracts metadata (title, description, thumbnail).
- `src/tube2txt/parsers.py`: `VTTParser` for WebVTT subtitle files.
- `src/tube2txt/ai.py`: `GeminiClient` using `google-genai`.
  - Generates specialized markdown: `outline`, `notes`, `recipe`, `technical`, or `clips`.
  - Auto-determines the best secondary mode from the outline.
- `src/tube2txt/generator.py`: `HTMLGenerator` for building `index.html` from transcript segments.
- `src/tube2txt/db.py`: `Database` class for SQLite with FTS5 indexing and search.
- `src/tube2txt/hub.py`: FastAPI-powered local dashboard.
  - Serves a single-page app with AlpineJS for browsing all processed videos.
  - Full-text search across all transcript segments via FTS5.
  - Serves static files from `projects/`.
- `src/tube2txt/clipping.py`: `ClippingEngine` for extracting video clips via `ffmpeg` stream copy.
- `src/tube2txt/index_existing.py`: Migration script to re-index legacy projects into the SQLite DB.
- `styles.css`: The Vanilla CSS file copied into every project.
- `projects/`: An ignored directory where all generated video projects are deposited.
- `tube2txt.db`: SQLite database for the hub's search and video index.

**Entry points** (defined in `pyproject.toml`):
- `tube2txt` -> `tube2txt:main`
- `tube2txt-hub` -> `tube2txt.hub:start_hub`
- `tube2txt-index` -> `tube2txt.index_existing:migrate`

## Strict Rules & Conventions

1. **Output Directory:** ALL downloaded videos, generated HTML, extracted images, and markdown files MUST go into the `projects/` directory (e.g., `projects/my-project/`). The `.gitignore` explicitly ignores `projects/`.
2. **Performance Constraints:**
   - Operations should be as fast as possible. Python scripts should be extremely optimized.
   - Do NOT serialize image extraction; always utilize parallelization (`concurrent.futures.ThreadPoolExecutor`).
3. **Vanilla Web Tech:** The generated webpage `index.html` uses raw HTML/CSS. If introducing Javascript, use plain Vanilla JS. **Do not** introduce complex frameworks like React or Tailwind unless explicitly instructed. The hub (`hub.py`) is an exception — it uses Tailwind via CDN and AlpineJS for the dashboard UI.
4. **Environment Variables:** The primary API key required is `GEMINI_API_KEY`. The `.env` file in the project root is auto-loaded by `python-dotenv`. If modifications are made requiring third-party tools, handle missing API keys gracefully (using fallbacks or clear error messages).
5. **Robust Error Handling:** Do not allow the script to fail silently. Ensure all `yt-dlp` and `ffmpeg` outputs/errors are suppressed when successful, but clearly printed and halted if something goes wrong.

## Common Agent Commands

Install the package in development mode first:

```bash
pip install -e .
```

Then test the script (ensure your API key is in `.env`):

```bash
tube2txt test-video "https://www.youtube.com/watch?v=YOUR_VIDEO_ID" --ai --mode notes
```

Check inside `projects/test-video/` to verify results.

Other commands:

```bash
# Start the local hub dashboard
tube2txt-hub

# Extract a manual clip from an existing project
tube2txt my-video --clip 00:01:00-00:02:00 --video-file projects/my-video/video.mp4

# Re-index existing projects into the SQLite DB
tube2txt-index

# Run tests
python -m pytest tests/ -x -q
```
