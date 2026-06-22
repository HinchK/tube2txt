# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Context

**Name:** Tube2Txt  
**Version:** 3.2.0  
**Purpose:** Convert YouTube videos into structured web pages with transcripts, screenshots, and AI-assisted markdown analysis. Exposes a Gridland TUI dashboard, a headless FastAPI hub with WebSocket support, and a remote Next.js gallery backed by Supabase.  
**Tech Stack:** Python 3.9+, FastAPI, WebSockets, SQLite/FTS5, Bun, Gridland/OpenTUI, React 19, TypeScript, Next.js, Supabase, Tailwind CSS

## Repository Layout

```
tube2txt/
├── src/tube2txt/           # Python backend (4 core files)
│   ├── __init__.py         # Domain classes, pipeline, CLI
│   ├── hub.py              # FastAPI server + WebSocket endpoint
│   ├── cloud.py            # Supabase sync (push/config/share)
│   └── index_existing.py   # Legacy migration script
├── tui/                    # Gridland TUI + browser SPA
│   └── src/
│       ├── index.tsx       # CLI entry (Bun runtime)
│       ├── web.tsx         # Browser entry (SPA)
│       ├── App.tsx         # 4-screen router
│       ├── screens/        # ProcessScreen, DashboardScreen, SearchScreen, VideoDetailScreen
│       ├── components/     # TerminalLog, VideoCard, SearchResult, Tube2TxtShowcase
│       └── hooks/          # useWebSocket, useVideos, useSearch
├── remote/                 # Next.js web gallery (Vercel/Supabase)
│   └── src/
│       ├── app/v/[slug]/   # Dynamic public video pages
│       └── components/     # DataStream, IntelligenceBrief
├── tests/                  # 4 pytest test modules
├── scripts/                # 6 shell automation scripts
├── docs/superpowers/       # Planning & design specs
├── design-system/          # Brand/aesthetic documentation
├── pyproject.toml          # Python package config
├── Dockerfile              # Multi-stage: Bun → Python
└── docker-compose.yml
```

## Python Backend

### Domain Classes (`src/tube2txt/__init__.py`)

| Class | Responsibility |
|---|---|
| `Database` | SQLite init, video/segment indexing, schema migration for `remote_url`, `is_archived`, `last_synced_at` |
| `GeminiClient` | Gemini 2.5 Flash AI generation; `generate_content(segments, mode)` + `determine_best_mode(outline)` |
| `VTTParser` | VTT file parsing with deduplication of consecutive identical segments |
| `HTMLGenerator` | Builds `index.html` with embedded transcript, thumbnail fallback, and YouTube timestamp links |
| `ClippingEngine` | ffmpeg stream-copy clip extraction |

### Database Schema (SQLite)

```sql
videos     -- id, slug, url, title, processed_at, remote_url, is_archived, last_synced_at
segments   -- id, video_id, start_ts, seconds, text, thumbnail_path
segments_search (FTS5 virtual) -- segment_id, text
```

Schema migrations for `remote_url`, `is_archived`, `last_synced_at` run automatically via `ALTER TABLE ... ADD COLUMN` (silently no-ops if column already exists).

### Processing Pipeline (`process_video()`)

The pipeline runs in this exact order; steps 1 and 3 represent the **transcript-first strategy** added in v3.x:

1. **Transcript API** — `fetch_transcript_api(video_id)` via `youtube-transcript-api`; gracefully handles `IpBlocked`, `TranscriptsDisabled`, `NoTranscriptFound`
2. **Download** — `download_video(url, output_dir)` — yt-dlp with 3-pass fallback: full → subtitle-only → minimal
3. **VTT Fallback** — `VTTParser.parse()` only if step 1 yielded no segments and a VTT file was downloaded
4. **HTML** — `HTMLGenerator.generate()` writes `index.html` + copies `styles.css`
5. **Index** — `Database.index_video()` inserts video + segments into SQLite FTS5
6. **AI** — `GeminiClient.generate_content()` (if `ai_flag=True` and `GEMINI_API_KEY` set); always generates OUTLINE first, then auto-detects best secondary mode via `determine_best_mode()`; appends CLIPS if `mode="clips"`
7. **Images** — `extract_images()` via parallel ffmpeg (default 4 workers), skipped if no video file

Signature:
```python
process_video(url, slug, mode="outline", ai_flag=True, db_path="tube2txt.db",
              project_path=None, on_progress=None, parallel=4) -> str | None
```

Progress callback: `on_progress(type_: str, step: str, message: str) -> None`. Pass `None` for CLI print, or a function for WebSocket streaming.

### AI Modes & Personas

| Mode | Output file | Notes |
|---|---|---|
| `outline` | `TUBE2TXT-OUTLINE.md` | Always generated first; used for auto mode detection |
| `notes` | `TUBE2TXT-NOTES.md` | Written in the voice of **Prot from K-PAX** (K. Spacey) — earnest, detached alien observer |
| `recipe` | `TUBE2TXT-RECIPE.md` | Ingredients, steps, timestamps |
| `technical` | `TUBE2TXT-TECHNICAL.md` | Code/architecture deep-dive |
| `clips` | `TUBE2TXT-CLIPS.md` | Top 3 viral 30-60s segments with `CLIP:[title]|[ts-ts]|[reason]` format |

Auto-detection: after generating an outline, `determine_best_mode()` uses Gemini to classify into `recipe`, `technical`, or `notes`.

### CLI (`main()` / `get_parser()`)

Git-style verb commands with aliases:

| Command | Aliases | Description |
|---|---|---|
| `add` | `url`, `process` | Process a YouTube URL |
| `ls` | `list` | List all local projects |
| `rm` | `delete` | Remove a project (interactive picker if no slug given) |
| `archive` | — | Mark a project as archived |
| `push` | `sync` | Sync project to Supabase remote |
| `share` | — | Print shareable gallery URL |
| `config` | `setup` | Interactive Supabase + Gemini setup wizard |
| `remote` | — | Print remote gallery status URL |

Behavior notes:
- Running `tube2txt` with no args enters **interactive mode** (`cmd_interactive`)
- Passing a bare URL as first arg auto-inserts the `add` command (legacy compat)
- `GEMINI_API_KEY` presence **auto-enables** AI even without `--ai` flag
- `--mode` only accepts `outline|notes|technical|recipe` (not `clips` directly; clips are added when outline mode selects it or when `mode="clips"` is passed to `process_video()` directly)

### Cloud Integration (`src/tube2txt/cloud.py`)

- `config()` — Interactive wizard that writes `remote/.env.local` (Supabase URL, anon key, service role key, site URL, SKIP_LOGIN) and `.env` (Gemini key)
- `push(slug)` — Upserts to Supabase `videos` table (`on_conflict=slug`), bundles all AI markdown files + transcript into a single JSON metadata record (`on_conflict=vid_id`)
- `get_remote_url(slug)` — Returns `{NEXT_PUBLIC_SITE_URL}/v/{slug}` from `remote/.env.local`

Metadata bundle keys: `outline`, `notes`, `clips`, `recipe`, `technical`, `transcript`

## Hub / FastAPI Server (`src/tube2txt/hub.py`)

### REST Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/healthcheck` | Returns `{status, db}` |
| `GET` | `/api/videos` | All videos ordered by `processed_at DESC` |
| `GET` | `/api/videos/{slug}` | Video detail with `segments[]` + `ai_files[]` |
| `GET` | `/api/videos/{slug}/images/{filename}` | Serve project images |
| `GET` | `/api/search?q=` | FTS5 full-text search (limit 20) |
| `WS` | `/ws/process` | Real-time processing stream |

### WebSocket Protocol (`/ws/process`)

Send:
```json
{ "action": "start", "url": "...", "slug": "...", "mode": "outline", "ai": true, "parallel": 4 }
```
Or send a raw CLI string:
```json
{ "action": "start", "command": "tube2txt add my-slug https://... --ai" }
```

Receive events:
```json
{ "type": "status|complete|error|ai_output", "step": "download|api|...", "message": "..." }
```

Single-job protection: `_job_lock = threading.Lock()` prevents concurrent jobs.

### SPA / Static Serving

Hub detects TUI assets in order: `TUBE2TXT_TUI_DIR` env → `./static/` → `./tui/dist/` → adjacent `tui/dist/`. Unknown paths fall back to `index.html` for SPA routing. API/WS paths return 404 if no handler matches.

### Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `TUBE2TXT_DB` | `tube2txt.db` (cwd) | SQLite database path |
| `TUBE2TXT_TUI_DIR` | auto-detected | Override TUI dist dir |
| `PORT` | `8000` | Server port (Railway-aware) |
| `GEMINI_API_KEY` | — | Required for AI features |

## Gridland TUI (`tui/`)

### Screens

| Screen | File | Description |
|---|---|---|
| Process | `ProcessScreen.tsx` | URL input, command entry, live terminal log |
| Dashboard | `DashboardScreen.tsx` | VideoCard grid, library browser |
| Search | `SearchScreen.tsx` | FTS5 search, highlighted SearchResult components |
| Detail | `VideoDetailScreen.tsx` | Tabbed: TRANSCRIPT + AI markdown files, segment viewer with images |

### Components

- `TerminalLog.tsx` — Colored message log (`error`/`status`/`complete`)
- `VideoCard.tsx` — Thumbnail, title, slug, date with selection state
- `SearchResult.tsx` — Text match with query highlighting
- `Tube2TxtShowcase.tsx` — Landing page with CRT scanlines, flicker effects, terminal simulation, feature grid

### Hooks

- `useWebSocket.ts` — Auto-reconnect with exponential backoff (up to 30s)
- `useVideos.ts` — `GET /api/videos` + `GET /api/videos/{slug}`
- `useSearch.ts` — Debounced `GET /api/search?q=` (300ms)

### Build Targets

| Command | Target | Output | Runtime |
|---|---|---|---|
| `bun run build` | `--target bun` | `tui/dist/` | Bun (CLI TUI) |
| `bun run build-web` | `--target browser` | `tui/dist/` | Browser (SPA) |
| `bun run dev` | — | stdout | Bun (live dev) |

## Remote Gallery (`remote/`)

Next.js app deployed to Vercel, reads from Supabase:

- `app/v/[slug]/page.tsx` — Public video page (server-rendered)
- `DataStream.tsx` — Collapsible transcript segment browser; hash-based deep linking `#t-{seconds}`
- `IntelligenceBrief.tsx` — Markdown renderer with `[HH:MM:SS]` → `#t-{seconds}` timestamp link extraction

Configure with `remote/.env.local`:
```
NEXT_PUBLIC_SUPABASE_URL=...
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...
NEXT_PUBLIC_SITE_URL=https://your-project.vercel.app
SKIP_LOGIN=false
```

## Commands

### Local Development

```bash
cd tui && bun install && bun run build && cd ..
uv venv && source .venv/bin/activate
uv pip install -e "."
```

### Python CLI

```bash
# Process a video (AI auto-enabled if GEMINI_API_KEY is set)
tube2txt add my-video "https://youtube.com/watch?v=..."

# Explicit AI with mode
tube2txt my-video "https://youtube.com/watch?v=..." --ai --mode notes

# Manual clip extraction
tube2txt my-video --clip 00:01:30-00:02:00 --video-file projects/my-video/video.mp4

# Project management
tube2txt ls
tube2txt rm my-video
tube2txt archive my-video
tube2txt push my-video
tube2txt share my-video
tube2txt config          # Set up Supabase + Gemini
tube2txt remote          # Print gallery URL
```

### Hub Server

```bash
tube2txt-hub             # Starts at http://0.0.0.0:8000
PORT=9000 tube2txt-hub   # Custom port
```

### Re-index Legacy Projects

```bash
tube2txt-index
```

### Tests

```bash
pytest tests/ -v
pytest tests/test_api.py -v             # API + WebSocket integration tests
pytest tests/test_process_video.py -v  # Pipeline unit tests
pytest tests/test_cli.py -v            # Argument alias tests
pytest tests/test_transcript.py -v     # get_video_id, format_vtt_timestamp, fetch_transcript_api
```

### TUI Development

```bash
cd tui && bun run dev          # Run TUI in Bun runtime
cd tui && bun run build-web    # Build browser SPA for hub
```

### Docker

```bash
docker compose up hub
```

### Automation Scripts

```bash
scripts/setup.sh         # Full env init (Python venv + Bun)
scripts/build.sh         # Rebuild TUI + reinstall Python package
scripts/test.sh          # Run pytest suite
scripts/purge-projects.sh  # Clear all generated video data
scripts/deploy.sh        # Docker/Railway deployment
scripts/backup.sh        # DB + projects backup
```

## Conventions

1. All output goes to `projects/<slug>/` directory
2. Image filenames use `HH-MM-SS-mmm.jpg` format (colons/dots replaced with dashes)
3. AI output files are named `TUBE2TXT-<MODE>.md` (uppercase mode, e.g., `TUBE2TXT-OUTLINE.md`)
4. `process_video()` accepts optional `on_progress` callback — `None` = print (CLI), function = WebSocket streaming
5. TUI uses lowercase JSX intrinsics (`<box>`, `<text>`, `<input>`, `<select>`, `<scrollbox>`) per OpenTUI API
6. Environment: `GEMINI_API_KEY` in `.env`, `TUBE2TXT_DB` for custom DB path
7. AI notes mode uses the **K-PAX voice** (Prot persona) — maintain this when editing the `notes` prompt in `GeminiClient`
8. The `push` command bundles all AI files + transcript into a single Supabase `metadata` record keyed by `vid_id`
9. Interactive pickers (`_select_project`) show at most 15 projects; fall back to all if `unsynced_only` yields none
10. `normalize_command()` maps CLI aliases to canonical names before dispatch in `main()`

## Gotchas

- If `uv` commands fail with TOML errors, check `uv.lock` for corruption (e.g., `aversion` instead of `version`).
- After editing `src/tube2txt/__init__.py`, run `uv pip install -e "."` to refresh entry points.
- `tube2txt-hub` automatically handles the `PORT` env var for Railway/cloud deployments.
- OpenTUI components are lowercase JSX intrinsics, NOT PascalCase (`<box>` not `<Box>`).
- Gridland renderer: `const renderer = await createCliRenderer(); createRoot(renderer).render(<App />)` — not a bare `render()` call.
- Bun build requires `--target bun` because OpenTUI uses `bun:ffi` internally.
- `select` component takes `options: [{label, value}]` and `onChange: (index) => void`, not `items`/`value` props.
- The `bun.lock` file should be committed but `node_modules/` is gitignored via `tui/.gitignore`.
- `hub.py` mounts `/projects` as a static files route only if the directory exists at startup — create it first or `Database` init creates it.
- `GeminiClient.generate_content()` always writes OUTLINE first; the secondary mode is auto-detected by `determine_best_mode()`, not taken from `args.mode` directly.
- `GEMINI_API_KEY` presence in the environment auto-enables AI in `cmd_add()` even without `--ai` flag — this is intentional behavior.
- Database migrations (`ALTER TABLE ADD COLUMN`) silently swallow `sqlite3.OperationalError` — safe to run against existing DBs.
- ffmpeg MJPEG encoder quirks: `_extract_single_image` uses `-strict -2` to handle older ffmpeg encoder constraints (see CHANGELOG v3.2.1).
- `remote/.env.local` is separate from root `.env` — Supabase keys go in `remote/`, Gemini key goes in root `.env`.
