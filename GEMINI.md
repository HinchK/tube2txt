# AI Assistant Guide for Tube2Txt

This file serves as the system rules, context, and orientation guide for any AI (like Gemini, Claude, or ChatGPT) assisting with this repository.

## Project Context

**Name:** Tube2Txt
**Purpose:** A CLI tool and TUI dashboard to convert YouTube videos into structured web pages with transcripts, screenshots, and AI-assisted markdown analysis powered by Gemini. Includes a headless FastAPI API with WebSocket support and a Gridland TUI frontend.
**Tech Stack:** Python 3.9+, FastAPI, WebSockets, `yt-dlp`, `ffmpeg`, `google-genai` API, SQLite/FTS5, Bun, Gridland/OpenTUI, React, TypeScript.

## Core Files & Architecture

### Python Backend (`src/tube2txt/`)
- `__init__.py`: All domain classes (Database, ClippingEngine, GeminiClient, VTTParser, HTMLGenerator) plus key functions:
  - `download_video(url, output_dir)` — Downloads video + subtitles via yt-dlp
  - `extract_images(video_path, segments, images_dir)` — Parallel ffmpeg frame extraction
  - `process_video(url, slug, ...)` — Full pipeline with optional `on_progress` callback
  - `main()` — CLI entry point
- `hub.py`: FastAPI headless JSON API with REST endpoints and WebSocket `/ws/process` for real-time processing. CORS enabled. Serves TUI assets at root when built.
- `index_existing.py`: Migration script to re-index legacy projects into SQLite DB.

### Gridland TUI (`tui/`)
- `src/index.tsx` — App entry with screen navigation (Process, Dashboard, Search, Detail)
- `src/hooks/` — `useWebSocket.ts`, `useVideos.ts`, `useSearch.ts`
- `src/screens/` — ProcessScreen, DashboardScreen, VideoDetailScreen, SearchScreen
- `src/components/` — TerminalLog, VideoCard, SearchResult
- Uses lowercase JSX intrinsics (`<box>`, `<text>`, `<input>`, `<select>`, `<scrollbox>`) per OpenTUI API

### Other Files
- `pyproject.toml` — Package config with entry points: `tube2txt`, `tube2txt-hub`, `tube2txt-index`
- `Dockerfile` — Multi-stage build: Bun (TUI) + Python (runtime)
- `docker-compose.yml` — Hub and CLI services
- `styles.css` — CSS for generated HTML pages
- `src/components/Tube2TxtShowcase.tsx` — Standalone Gridland-aesthetic web showcase component
- `projects/` — Output directory (gitignored)
- `tube2txt.db` — SQLite database for video index and FTS5 search

## API Endpoints

- `GET /api/videos` — List all processed videos
- `GET /api/videos/{slug}` — Video detail with segments and AI files
- `GET /api/videos/{slug}/images/{filename}` — Serve thumbnail images
- `GET /api/search?q=` — Full-text search across all transcripts
- `WS /ws/process` — WebSocket for real-time video processing

## Strict Rules & Conventions

1. **Output Directory:** All generated content goes to `projects/<slug>/`. The `.gitignore` ignores `projects/`.
2. **Performance:** Image extraction uses parallel ffmpeg via `concurrent.futures.ThreadPoolExecutor`.
3. **Progress Callback:** `process_video()` accepts `on_progress(type, step, message)`. When None, it prints (CLI mode). When provided, it streams to WebSocket.
4. **Environment Variables:** `GEMINI_API_KEY` in `.env` (auto-loaded). `TUBE2TXT_DB` for custom DB path.
5. **Error Handling:** Don't fail silently. Print clear errors and return None/False on failure.

## Common Commands

```bash
# Process a video via CLI
tube2txt my-video "https://www.youtube.com/watch?v=VIDEO_ID" --ai --mode notes

# Start the API server (serves TUI if built)
tube2txt-hub

# TUI development
cd tui && bun install && bun run dev

# Build TUI for production
cd tui && bun run build

# Run tests
.venv/bin/pytest tests/ -v

# Docker
docker compose up hub
docker compose run tube2txt tube2txt my-video "URL" --ai
```
