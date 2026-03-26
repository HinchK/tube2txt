# AI Assistant Guide for Tube2Txt

## Project Context

**Name:** Tube2Txt
**Purpose:** Convert YouTube videos into structured web pages with transcripts, screenshots, and AI-assisted markdown analysis. Includes a Gridland TUI dashboard and headless FastAPI API with WebSocket support.
**Tech Stack:** Python 3.9+, FastAPI, WebSockets, SQLite/FTS5, Bun, Gridland/OpenTUI, React, TypeScript

## Architecture

### Python Backend (`src/tube2txt/`)
- `__init__.py` — Import facade + CLI functions: `download_video()`, `extract_images()`, `process_video()`, `main()`
- `db.py` — `Database` (SQLite/FTS5)
- `ai.py` — `GeminiClient` (Gemini API)
- `clipping.py` — `ClippingEngine`
- `downloader.py` — `Downloader` (yt-dlp wrapper)
- `parsers.py` — `VTTParser`
- `generator.py` — `HTMLGenerator`
- `hub.py` — FastAPI headless JSON API: REST endpoints + WebSocket `/ws/process` for real-time processing
- `index_existing.py` — Migration script for legacy projects

### Gridland TUI (`tui/`)
- `src/index.tsx` — App entry, screen router with navigation bar
- `src/hooks/` — `useWebSocket.ts`, `useVideos.ts`, `useSearch.ts`
- `src/screens/` — ProcessScreen, DashboardScreen, VideoDetailScreen, SearchScreen
- `src/components/` — TerminalLog, VideoCard, SearchResult

### Key Files
- `pyproject.toml` — Python package config, entry points: `tube2txt`, `tube2txt-hub`, `tube2txt-index`
- `Dockerfile` — Multi-stage: Bun (TUI build) + Python (runtime)
- `styles.css` — CSS for generated HTML pages
- `projects/` — Output directory (gitignored)
- `tube2txt.db` — SQLite database

## API Endpoints

- `GET /api/videos` — List all videos
- `GET /api/videos/{slug}` — Video detail with segments + AI files
- `GET /api/videos/{slug}/images/{filename}` — Serve images
- `GET /api/search?q=` — FTS5 search across all transcripts
- `WS /ws/process` — Real-time video processing (send `{action: "start", slug, url, ai, mode}`)

## Commands

```bash
# Install/update Python deps (system pip is PEP 668 blocked, use uv)
uv pip install -e "."
uv pip install pytest httpx  # test deps

# Python CLI
tube2txt my-video "https://youtube.com/watch?v=..." --ai --mode notes

# Start API server
tube2txt-hub

# TUI development
cd tui && bun install && bun run dev

# Build TUI
cd tui && bun run build

# Run tests
venv/bin/pytest tests/ -v

# Docker
docker compose up hub
docker compose run tube2txt tube2txt my-video "URL" --ai
```

## Conventions

1. All output goes to `projects/<slug>/` directory
2. Image extraction uses parallel ffmpeg via ThreadPoolExecutor
3. `process_video()` accepts optional `on_progress` callback — None = print (CLI), function = WebSocket streaming
4. TUI uses lowercase JSX intrinsics (`<box>`, `<text>`, `<input>`, `<select>`, `<scrollbox>`) per OpenTUI API
5. Environment: `GEMINI_API_KEY` in `.env`, `TUBE2TXT_DB` for custom DB path

## Gotchas

- After editing any file in `src/tube2txt/`, run `uv pip install -e "."` before tests — changes won't be visible otherwise
- OpenTUI components are lowercase JSX intrinsics, NOT PascalCase (`<box>` not `<Box>`, `<text>` not `<Text>`)
- Gridland renderer: `const renderer = await createCliRenderer(); createRoot(renderer).render(<App />)` — not a bare `render()` call
- Bun build requires `--target bun` because OpenTUI uses `bun:ffi` internally
- `select` component takes `options: [{label, value}]` and `onChange: (index) => void`, not `items`/`value` props
- The `bun.lock` file should be committed but `node_modules/` is gitignored via `tui/.gitignore`
