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
- `tui/src/components/Tube2TxtShowcase.tsx` — Standalone Gridland-aesthetic web showcase component
- `projects/` — Output directory (gitignored)
- `tube2txt.db` — SQLite database for video index and FTS5 search

## API Endpoints

- `GET /api/videos` — List all processed videos
- `GET /api/videos/{slug}` — Video detail with segments and AI files
- `GET /api/videos/{slug}/images/{filename}` — Serve thumbnail images
- `GET /api/search?q=` — Full-text search across all transcripts
- `WS /ws/process` — WebSocket for real-time video processing

## Strict Rules & Conventions

1. **Output Directory:** All generated content goes to `projects/<slug>/`.
2. **Hub Restarts:** After making any changes to `src/tube2txt/hub.py` or the TUI, the `tube2txt-hub` process MUST be killed and restarted to reflect changes.
3. **Web TUI:** The TUI code (`tui/src/`) must use standard HTML tags (div, span, button) and Tailwind CSS for browser compatibility, even though it follows a terminal aesthetic.
4. **Unified Input:** The "Command or URL" field in the Hub should be treated as a direct bridge to the CLI parameters.
5. **Testing:** Always use `./scripts/test.sh` to ensure the correct Python environment.

## Common Commands

```bash
# Full environment setup (Python + TUI)
./scripts/setup.sh

# Start the Intelligence Hub (Web Dashboard)
uv run tube2txt-hub

# Process a video via CLI
uv run tube2txt "URL" --ai

# Run tests
./scripts/test.sh
```
