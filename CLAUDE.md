# Tube2Txt v3

CLI tool that converts YouTube videos/playlists into structured web pages with transcripts, screenshots, and AI-generated markdown analysis. Includes a local hub dashboard and smart clip extraction.

## Commands

```bash
# Process a video (install with pip install -e . first)
tube2txt my-video "https://www.youtube.com/watch?v=VIDEO_ID" --ai --mode notes

# Start the hub dashboard (FastAPI + uvicorn on port 8000)
tube2txt-hub

# Re-index legacy projects into SQLite
tube2txt-index

# Manual clip extraction
tube2txt my-video --clip 00:01:00-00:02:00 --video-file projects/my-video/video.mp4

# Run tests
python -m pytest tests/ -x -q

# Docker
docker-compose up --build
```

## Architecture

```
src/tube2txt/
  __init__.py     # CLI entry point (main), orchestration, parallel image extraction
  downloader.py   # yt-dlp wrapper: downloads video + subtitles, extracts metadata
  parsers.py      # VTT subtitle parser
  ai.py           # GeminiClient: generates outline/notes/recipe/technical/clips via google-genai
  generator.py    # HTMLGenerator: builds index.html from transcript segments
  db.py           # Database: SQLite with FTS5 for video indexing and search
  hub.py          # FastAPI app: dashboard UI (Tailwind CDN + AlpineJS), search, static serving
  clipping.py     # ClippingEngine: ffmpeg stream-copy clip extraction
  index_existing.py  # Migration script for legacy projects
```

Entry points (pyproject.toml):
- `tube2txt` -> `tube2txt:main`
- `tube2txt-hub` -> `tube2txt.hub:start_hub`
- `tube2txt-index` -> `tube2txt.index_existing:migrate`

## Conventions

- **Output directory**: ALL artifacts go into `projects/<slug>/` (gitignored). Never output elsewhere.
- **Vanilla web**: Generated pages use raw HTML/CSS only. No frameworks. Hub is the exception (Tailwind CDN + AlpineJS).
- **Performance**: Image extraction uses `concurrent.futures.ThreadPoolExecutor`. Never serialize.
- **Error handling**: Fail loudly on `yt-dlp`/`ffmpeg` errors. Suppress output on success.
- **AI modes**: outline, notes, recipe, technical, clips. AI auto-determines best secondary mode from outline.

## Environment

- `GEMINI_API_KEY` (required for `--ai`): loaded via `python-dotenv` from `.env`
- `TUBE2TXT_DB` (optional): custom SQLite path, defaults to `tube2txt.db` in CWD
- System deps: `yt-dlp`, `ffmpeg`, Python 3.9+

## Gotchas

- `styles.css` lives at repo root, gets copied into each project dir. The `__init__.py` has a two-step fallback to find it (package dir, then repo root).
- Hub reads `PROJECTS_DIR` and `DB_PATH` relative to CWD, not the package location.
- VTT parser expects WebVTT format with timestamp lines like `00:00:01.000 --> 00:00:05.000`.
- The `--ai` flag requires `GEMINI_API_KEY` but degrades gracefully (skips AI generation with a warning).
