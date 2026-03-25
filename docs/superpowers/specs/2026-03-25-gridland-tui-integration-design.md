# Gridland TUI Integration -- Design Spec

**Date**: 2026-03-25
**Status**: Approved
**Scope**: Replace the FastAPI Hub with a Gridland TUI that handles video processing, dashboard browsing, video detail viewing, and full-text search.

## Summary

Integrate tube2txt with Gridland to provide a browser-based TUI that replaces the existing AlpineJS Hub dashboard. The Gridland frontend communicates with a refactored FastAPI backend over REST (data queries) and WebSocket (real-time processing). Deployed as a single Docker container.

## Current Codebase State

The project has three Python source files:

- **`src/tube2txt/__init__.py`** -- Monolithic file containing ALL domain classes (Database, ClippingEngine, GeminiClient, VTTParser, HTMLGenerator) and the `main()` CLI entry point. There is no separate `process_video` function -- all processing logic is inline in `main()`. Importantly, `main()` does NOT do image extraction in Python; it prints `TIMESTAMP:` lines to stdout for an external bash script (`tube2txt.sh`, no longer present) to extract images via ffmpeg. Image extraction in Python is new work required by this spec.
- **`src/tube2txt/hub.py`** -- FastAPI Hub with HTML dashboard, `/api/videos` and `/api/search` endpoints, and `start_hub()` entry point.
- **`src/tube2txt/index_existing.py`** -- Migration script.

**Database schema:**
- `videos` table: `id, slug, url, title, processed_at` (no `description` or `thumbnail_url` columns)
- `segments` table: `id, video_id, start_ts, seconds, text, thumbnail_path` (no `end` field)
- `segments_search` FTS5 virtual table: `segment_id, text`

## Architecture

### System Boundaries

```
+-------------------------+     REST + WS     +-------------------------+
|   GRIDLAND TUI (Bun)    | <--------------> |  FASTAPI BACKEND (Py)   |
|                         |                   |                         |
|  Screens:               |                   |  REST:                  |
|    ProcessScreen        |   GET /api/*      |    /api/videos          |
|    DashboardScreen      | <--------------   |    /api/videos/{slug}   |
|    VideoDetailScreen    |                   |    /api/search?q=       |
|    SearchScreen         |   WS /ws/process  |                         |
|                         | <--------------> |  WebSocket:             |
|  Hooks:                 |                   |    /ws/process          |
|    useWebSocket()       |                   |                         |
|    useVideos()          |                   |  Domain (in __init__.py)|
|    useSearch()          |                   |    Database, VTTParser  |
+-------------------------+                   |    GeminiClient,        |
                                              |    HTMLGenerator,       |
                                              |    ClippingEngine       |
                                              +----------+--------------+
                                                         |
                                              +----------+--------------+
                                              |  tube2txt.db | projects/ |
                                              +-------------------------+
```

### Key Decisions

- **Gridland replaces the Hub entirely** -- no parallel UI to maintain
- **Clean API with domain objects** -- API returns structured data, TUI decides presentation
- **WebSocket for processing** -- bidirectional, real-time progress streaming
- **Single Docker container** -- multi-stage build with Bun (build) + Python (runtime)
- **CLI preserved** -- `tube2txt` CLI works independently, no Gridland dependency

## API Design

### REST Endpoints

| Endpoint | Method | Returns |
|---|---|---|
| `/api/videos` | GET | `[{slug, url, title, processed_at}]` |
| `/api/videos/{slug}` | GET | `{slug, url, title, segments: [{start_ts, seconds, text}], ai_files: [{name, content}]}` |
| `/api/search?q=` | GET | `[{slug, title, start_ts, text, thumbnail_path}]` |
| `/api/videos/{slug}/images/{filename}` | GET | Binary image file |

**Notes on the `/api/videos/{slug}` endpoint:**
- `segments` come from the `segments` DB table (fields: `start_ts`, `seconds`, `text`)
- `ai_files` is a list of `{name, content}` objects read by globbing `TUBE2TXT-*.md` files in `projects/{slug}/`. Example: `[{name: "OUTLINE", content: "## Introduction..."}, {name: "NOTES", content: "..."}]`. The `name` field is the uppercase suffix extracted from the filename (e.g., `TUBE2TXT-OUTLINE.md` -> `"OUTLINE"`).
- If no AI content files exist, `ai_files` is an empty array `[]`

**Notes on search:**
- Uses the existing FTS5 query pattern from `hub.py`
- No server-side highlighting in v1 -- the TUI does client-side highlighting using the search query
- Returns raw segment data matching the existing `/api/search` response shape

### WebSocket Protocol

**Endpoint**: `WS /ws/process`

**Client -> Server:**
```json
{"action": "start", "slug": "my-video", "url": "https://...", "ai": true, "mode": "notes"}
```

**Server -> Client (progress stream):**
```json
{"type": "status", "step": "download", "message": "Downloading video..."}
{"type": "status", "step": "parse", "message": "Parsing subtitles..."}
{"type": "status", "step": "ai", "message": "Generating outline..."}
{"type": "ai_output", "step": "ai", "content": "## Introduction [00:00:15]\n..."}
{"type": "status", "step": "images", "message": "Extracting images..."}
{"type": "complete", "slug": "my-video"}
{"type": "error", "message": "yt-dlp failed: ..."}
```

**Note on ai_output:** The current `GeminiClient.generate_content` returns the full response at once (not streamed from Gemini). The `ai_output` message is sent as a single batch after generation completes, not line-by-line. Gemini streaming is out of scope for v1.

## TUI Screens

### Navigation

Tab-based navigation bar always visible at top: `[1] Process  [2] Dashboard  [3] Search`. WebSocket connection status indicator in top-right corner.

### Process Screen

- Input fields: YouTube URL, project slug
- AI mode selector: toggle between outline/notes/recipe/technical/clips
- Start Processing button (disabled while a job is running)
- Scrollable terminal log showing real-time WebSocket progress messages

### Dashboard Screen

- Vertical list of processed videos as cards
- Each card shows: slug, title, processed date
- Keyboard navigation: arrow keys to select, Enter to view detail, `o` to open static HTML in system browser
- Empty state: "No videos yet. Press [1] to process your first video."

### Video Detail Screen

- Reached from Dashboard or Search
- Video metadata header (title, slug, URL, date)
- Tabbed content: Transcript (timestamped segments in ScrollBox), plus one tab per AI file (Outline, Notes, etc. -- dynamically generated from `ai_files` array)
- `o` opens generated `index.html` in system browser
- `Esc` returns to Dashboard

### Search Screen

- Input field with 300ms debounced FTS5 search
- Results show: video slug, timestamp, snippet text (client-side highlight of query match)
- Enter on a result navigates to VideoDetail scrolled to that timestamp
- Empty state: "No results."

## State Management

Three React hooks:

### `useWebSocket(url)`
- Connects to `ws://localhost:8000/ws/process` on mount
- Exposes `send(message)` for dispatching commands
- Maintains `messages[]` array for terminal log
- Tracks `connectionStatus` (connected/disconnected/reconnecting)
- Auto-reconnects with exponential backoff

### `useVideos()`
- Fetches `GET /api/videos` on mount and after job completion
- Fetches `GET /api/videos/{slug}` for detail view
- Returns `{videos, selectedVideo, loading, error, refetch}`

### `useSearch(query)`
- Debounces input (300ms), calls `GET /api/search?q=`
- Returns `{results, loading, error}`

## Changes to Existing Code

### Modified Files

**`src/tube2txt/__init__.py`** -- Moderate refactor
- Extract a `process_video(url, slug, mode, ai_flag, db_path, project_path, on_progress=None)` function from the inline processing logic currently inside `main()`. This function encapsulates: yt-dlp download, VTT parsing, HTML generation, DB indexing, AI content generation, and image extraction.
- **New: Python image extraction.** The current `main()` prints `TIMESTAMP:` lines for an external bash script to extract images. Since `tube2txt.sh` no longer exists, `process_video()` must implement image extraction directly in Python using `subprocess` to call `ffmpeg` and `concurrent.futures.ThreadPoolExecutor` for parallelism. This is new code (~20 lines, modeled on the pattern that existed in the `main` branch).
- **New: yt-dlp download in Python.** The current `main()` expects `--vtt` to be passed (the bash script handled download). `process_video()` must call yt-dlp via `subprocess` to download video + subtitles. This can reuse patterns from the bash script.
- The `main()` function becomes a thin CLI wrapper that parses args and calls `process_video()`.
- `on_progress` is an optional callback `(type: str, step: str, message: str) -> None`. When present, progress is sent via the callback. When absent, `print()` is used (CLI behavior preserved).
- All domain classes (Database, GeminiClient, VTTParser, HTMLGenerator, ClippingEngine) remain in this file, unchanged.

**`src/tube2txt/hub.py`** -- Major refactor
- Strip the HTML rendering (the `read_root()` endpoint returning the AlpineJS dashboard)
- Keep: FastAPI app, `get_db()` helper, static file mounting, existing `/api/videos` and `/api/search` endpoints
- Add: `/api/videos/{slug}` detail endpoint (reads DB + `TUBE2TXT-*.md` files from disk)
- Add: `/api/videos/{slug}/images/{filename}` endpoint
- Add: `WS /ws/process` WebSocket endpoint that calls `process_video()` with a WebSocket-backed `on_progress` callback
- Add: CORS middleware (Gridland dev server runs on a different port)
- `start_hub` entry point serves API + built TUI assets

**`pyproject.toml`** -- Add `websockets` dependency

**`Dockerfile`** -- Rewrite as multi-stage build
- Stage 1: `oven/bun` builds Gridland app
- Stage 2: `python:3.11-slim` runs FastAPI, serves built TUI assets

### Untouched Files
- `src/tube2txt/index_existing.py` -- no changes

### New Files

```
tui/
  package.json
  tsconfig.json
  src/
    index.tsx               # App entry, screen router
    hooks/
      useWebSocket.ts
      useVideos.ts
      useSearch.ts
    screens/
      ProcessScreen.tsx
      DashboardScreen.tsx
      VideoDetailScreen.tsx
      SearchScreen.tsx
    components/
      TerminalLog.tsx
      VideoCard.tsx
      SearchResult.tsx
```

## Error Handling

### WebSocket
- **Connection lost mid-processing**: Backend job continues. TUI re-fetches on reconnect.
- **Multiple simultaneous jobs**: Rejected with error message. Start button disabled during active job.
- **Invalid URL / yt-dlp failure**: Error sent via WebSocket, displayed in terminal log.

### API
- **Video not found**: 404, TUI shows message and navigates to Dashboard.
- **Empty search**: Returns empty array, TUI shows "No results."
- **Missing GEMINI_API_KEY**: Processing continues without AI. Progress stream notes the skip.

### TUI
- **Long titles**: Truncated with ellipsis in cards, full in detail view.
- **Large transcripts**: OpenTUI ScrollBox handles natively.
- **Empty dashboard**: Shows guidance message.

## Out of Scope (v1)

- Job queue / concurrent processing
- Authentication
- Video deletion from TUI
- Playlist batch processing in TUI (CLI handles it)
- Gemini streaming (AI content returned as batch)
- Server-side search highlighting (done client-side)

## Testing Strategy

### Backend (pytest)
- API endpoint tests with seeded test SQLite DB via FastAPI `TestClient`
- WebSocket test: connect, send job, assert progress message sequence (mock yt-dlp and GeminiClient calls)
- Progress callback test: call `process_video()` with mock `on_progress`, verify call sequence
- Existing tests unchanged

### Frontend (Bun test)
- Hook tests with mocked fetch/WebSocket
- Screen rendering tests with mock data
- Lower priority than backend tests for v1

### Integration
- End-to-end: start FastAPI, WebSocket client sends process command, mock download step using `tests/sample.vtt`, verify progress stream and final REST response

## Entry Points

All three existing entry points preserved:
- `tube2txt` -- CLI, works independently (no Gridland dependency)
- `tube2txt-hub` -- Now serves API + Gridland TUI (replaces AlpineJS dashboard)
- `tube2txt-index` -- Unchanged

## Gridland Dependency

- **Runtime**: Bun (required by Gridland/OpenTUI)
- **Setup**: `bun create gridland` to scaffold, then install from ShadCN registry
- **Key packages**: `@gridland/*`, `@opentui/react`
- **Reference**: https://www.gridland.io/, https://opentui.com/
- **Port**: Gridland dev server on configurable port; production build served by FastAPI on port 8000
