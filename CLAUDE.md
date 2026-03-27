# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Context

**Name:** Tube2Txt
**Purpose:** Convert YouTube videos into structured web pages with transcripts, screenshots, and AI-assisted markdown analysis. Includes a Gridland TUI dashboard and headless FastAPI API with WebSocket support.
**Tech Stack:** Python 3.9+, FastAPI, WebSockets, SQLite/FTS5, Bun, Gridland/OpenTUI, React, TypeScript

## Architecture

### Python Backend (`src/tube2txt/`)

- `__init__.py` — Domain classes (Database, ClippingEngine, GeminiClient, VTTParser, HTMLGenerator) + `download_video()`, `extract_images()`, `process_video()`, `main()` CLI
- `hub.py` — FastAPI headless JSON API: REST endpoints + WebSocket `/ws/process` for real-time processing
- `index_existing.py` — Migration script for legacy projects

### Processing Pipeline

`process_video()` orchestrates the full pipeline in order:
1. `download_video()` — yt-dlp downloads video + auto-subs (VTT) to `projects/<slug>/`
2. `VTTParser.parse()` — Parses/deduplicates subtitle segments
3. `HTMLGenerator.generate()` — Builds `index.html` with embedded transcript + YouTube timestamp links
4. `Database.index_video()` — Indexes segments into SQLite FTS5 table
5. `GeminiClient.generate_content()` — AI analysis (if `--ai`), writes `TUBE2TXT-<MODE>.md`
6. `extract_images()` — Parallel ffmpeg screenshots via ThreadPoolExecutor (4 workers default)

The `on_progress` callback signature is `(type_, step, message) -> None`. Pass `None` for CLI print behavior, or a function for WebSocket streaming in `hub.py`.

### Gridland TUI (`tui/`)

- `src/index.tsx` — App entry, 4-screen router (Process, Dashboard, Search, Detail) with nav bar
- `src/hooks/` — `useWebSocket.ts` (auto-reconnect with exponential backoff), `useVideos.ts`, `useSearch.ts`
- `src/screens/` — ProcessScreen, DashboardScreen, VideoDetailScreen, SearchScreen
- `src/components/` — TerminalLog, VideoCard, SearchResult
- `web.tsx` — Separate entry point for browser build (`bun run build-web`)

### Key Files

- `pyproject.toml` — Python package config, entry points: `tube2txt`, `tube2txt-hub`, `tube2txt-index`
- `Dockerfile` — Multi-stage: Bun (TUI build) → Python runtime; TUI assets copied to `./static/`
- `styles.css` — CSS for generated HTML pages
- `projects/` — Output directory (gitignored)
- `tube2txt.db` — SQLite database (created on first `hub.py` startup)

## API Endpoints

- `GET /api/videos` — List all videos (ordered by date DESC)
- `GET /api/videos/{slug}` — Video detail with segments + AI markdown files
- `GET /api/videos/{slug}/images/{filename}` — Serve project images
- `GET /api/search?q=` — FTS5 full-text search (limit 20 results)
- `WS /ws/process` — Real-time video processing; send `{action: "start", slug, url, ai, mode}`; only one job runs at a time (lock-protected)

Hub serves built TUI as SPA from `./static/` → `./tui/dist/` fallback; unknown paths return `index.html`.

## Commands

### Local Development

```bash
cd tui && bun install && bun run build && cd ..
uv venv && source .venv/bin/activate
uv pip install -e "."
```

### Python CLI

```bash
tube2txt my-video "https://youtube.com/watch?v=..." --ai
tube2txt my-video "https://youtube.com/watch?v=..." --ai --mode notes  # outline|notes|recipe|technical|clips
tube2txt my-video --clip 00:01:30-00:02:00 --video-file projects/my-video/video.mp4
```

### Start API server (serves TUI if built)

```bash
tube2txt-hub
```

### Re-index legacy projects

```bash
tube2txt-index
```

### Tests

```bash
pytest tests/ -v
pytest tests/test_api.py -v        # API + WebSocket tests
pytest tests/test_process_video.py -v  # Pipeline unit tests
```

### TUI development

```bash
cd tui && bun run dev              # Run TUI directly (Bun runtime)
cd tui && bun run build-web        # Browser build for hub SPA
```

### Docker

```bash
docker compose up hub
```

## Conventions

1. All output goes to `projects/<slug>/` directory
2. Image filenames use `HH-MM-SS-mmm.jpg` format (colons/dots replaced with dashes)
3. AI output files are named `TUBE2TXT-<MODE>.md` (e.g., `TUBE2TXT-OUTLINE.md`)
4. `process_video()` accepts optional `on_progress` callback — `None` = print (CLI), function = WebSocket streaming
5. TUI uses lowercase JSX intrinsics (`<box>`, `<text>`, `<input>`, `<select>`, `<scrollbox>`) per OpenTUI API
6. Environment: `GEMINI_API_KEY` in `.env`, `TUBE2TXT_DB` for custom DB path

## Gotchas

- If `uv` commands fail with TOML errors, check `uv.lock` for corruption (e.g. `aversion` instead of `version`).
- After editing `src/tube2txt/__init__.py`, run `uv pip install -e "."` to refresh entry points.
- `tube2txt-hub` automatically handles the `PORT` env var for Railway/cloud deployments.
- OpenTUI components are lowercase JSX intrinsics, NOT PascalCase (`<box>` not `<Box>`)
- Gridland renderer: `const renderer = await createCliRenderer(); createRoot(renderer).render(<App />)` — not a bare `render()` call
- Bun build requires `--target bun` because OpenTUI uses `bun:ffi` internally
- `select` component takes `options: [{label, value}]` and `onChange: (index) => void`, not `items`/`value` props
- The `bun.lock` file should be committed but `node_modules/` is gitignored via `tui/.gitignore`
