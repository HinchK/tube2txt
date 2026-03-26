# Changelog

All notable changes to Tube2Txt are documented here.

---

## [3.2.1] — 2026-03-26

### Added
- **Project Obsidian Pulse** — a classy, subtle integration in the web showcase footer.
- **Improved Footer Layout** — responsive and centered with project codename, timestamp, and repository link.
- **GitHub Repository Link** — direct link to `github.com/hinchk/tube2txt` with consistent iconography.

---

## [3.2.0] — 2026-03-25

### Added
- **Gridland Web Showcase** — a standalone React component (`src/components/Tube2TxtShowcase.tsx`) for demonstrating the tool's TUI aesthetic on the web.
- **Terminal Simulation** — interactive CLI typing flow with progress bars and CRT visual effects (scanlines, flicker, glow).
- **TUI Feature Grid** — terminal-style box-drawing components for showcasing AI Voice, Smart Clips, and Global Search.

---

## [3.1.0] — 2026-03-25

### Added
- **Gridland TUI dashboard** (`tui/`) — a full terminal UI built with Bun, OpenTUI, and React 19
  - `ProcessScreen` — submit a YouTube URL and watch live processing logs
  - `DashboardScreen` — browse all processed videos with `VideoCard` components
  - `VideoDetailScreen` — view transcript segments and AI-generated markdown files
  - `SearchScreen` — FTS5 full-text search with `SearchResult` components
- **WebSocket endpoint** `WS /ws/process` — streams real-time processing progress events (`type`, `step`, `message`) to connected clients
- **React hooks** — `useWebSocket`, `useVideos`, `useSearch` for TUI data management
- **`GET /api/videos/{slug}`** endpoint — returns video detail with transcript segments and all AI markdown files read from disk
- **`GET /api/videos/{slug}/images/{filename}`** endpoint — serves project images via the API
- **CORS middleware** on the FastAPI app to support TUI-to-API communication
- **Multi-stage Dockerfile** — stage 1 builds the TUI with Bun; stage 2 is the Python runtime; built TUI assets are served from `tui-dist/` at `/`
- **Integration test** for WebSocket process + REST fetch flow (`tests/`)
- `process_video()` now accepts an `on_progress(type_, step, message)` callback; `None` falls back to stdout printing for the CLI

### Changed
- Hub (`hub.py`) no longer serves an HTML dashboard page — it is now a pure headless JSON + WebSocket API
- `process_video()` extracted from `main()` into a standalone function to support programmatic use by the WebSocket handler
- `download_video()` and `extract_images()` are now discrete importable functions
- TUI built assets served at `/` by `tube2txt-hub` when `tui-dist/` is present (falls back to `tui/dist` in development)

### Fixed
- `tui/.gitignore` added to exclude `node_modules/` from version control
- CLI breaking changes noted in plan review addressed

---

## [3.0.1] — 2026-03-24

### Added
- `src/tube2txt/` package structure with `setuptools` — project is now installable via `pip` / `pipx` / `uv`
- Entry points: `tube2txt`, `tube2txt-hub`, `tube2txt-index`
- **AI voice by Strunk & White** — AI prompts now instruct Gemini to write in the style of *The Elements of Style* (concise, vigorous, active voice)
- **Vibrant terminal output** — AI-generated markdown printed in cyan for immediate review
- **Artifact summary** — list of all generated file paths printed on completion
- `TUBE2TXT_DB` environment variable for customizing the SQLite database path

### Changed
- Gemini model updated to current generation
- Path management centralized across all modules
- Clip parsing enhanced for more robust timestamp extraction

---

## [3.0.0] — 2026-03-24

### Added
- **Tube2Txt Hub** — local FastAPI web dashboard to browse video library
- **Global FTS5 search** — search any word or phrase across all processed video transcripts
- **SQLite database** (`tube2txt.db`) for centralized metadata and transcript storage
- **Smart Clips**
  - AI-driven clip extraction: Gemini identifies the most interesting moments
  - Manual clip extraction by timestamp range
- **`tube2txt-index`** command for migrating or re-indexing legacy projects

---

## [2.0.0] — 2026-03-23

### Added
- Docker support via `docker-compose`
- Diverse AI content modes: `outline`, `notes`, `recipe`, `technical`
- Interactive CLI prompts
- Parallel screenshot extraction via `xargs -P` / `ThreadPoolExecutor`
- Playlist URL support

---

## [1.0.0] — 2026-03-23

### Added
- Initial open-source release
- Windows support — see [WINDOWS-INSTALL.md](WINDOWS-INSTALL.md)
- `CONTRIBUTING.md` and standard open-source scaffolding
- Basic YouTube-to-HTML transcript conversion with ffmpeg screenshot extraction
- AI outline generation via Gemini
