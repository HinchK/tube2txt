[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/deploy?repo=https://github.com/HinchK/tube2txt)

# Tube2Txt v3.1

> **Inspiration:** This project is a modern rewrite of the original [Youtube2Webpage](https://github.com/obra/Youtube2Webpage) script.

Tube2Txt converts YouTube videos into structured web pages with transcripts, screenshots, and AI-assisted analysis. It ships with a **Gridland TUI dashboard** and a headless **FastAPI + WebSocket API**.

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/deploy?repo=https://github.com/HinchK/tube2txt)

**Post-Deployment Setup:**

1. Provide your `GEMINI_API_KEY` when prompted by Railway (get one free at [Google AI Studio](https://aistudio.google.com/)).
2. Once the service is live, open the generated Railway URL to access the hub.
3. To process your first video via the Railway CLI:
   ```bash
   railway run tube2txt my-video-slug "https://youtube.com/watch?v=..." --ai
   ```

## Features

- **Gridland TUI**: Terminal dashboard built with Bun + OpenTUI + React — process videos, browse your library, and search transcripts, all from the terminal.
- **WebSocket Processing**: Real-time progress streaming via `/ws/process` — the TUI connects here to show live logs.
- **REST API**: Full JSON API for video listing, detail, image serving, and FTS5 search.
- **AI Analysis**: Gemini-powered outlines, notes, recipes, technical summaries, and smart clip extraction.
- **AI Voice by Strunk & White**: AI-generated content follows _The Elements of Style_ (1918) for concise, active writing.
- **FTS5 Global Search**: Search any word or phrase across all processed videos.
- **Smart Clips**: Manual or AI-driven video segment extraction.
- **Parallel Screenshot Extraction**: Up to 10x faster via `ThreadPoolExecutor` + ffmpeg.
- **SQLite Database**: Centralized metadata and searchable transcript storage.
- **Docker Support**: Multi-stage Dockerfile with Bun TUI build and Python runtime.

## Architecture

```
src/tube2txt/
  ├─ __init__.py        ← Core: Database, ClippingEngine, GeminiClient,
  │                       VTTParser, HTMLGenerator; download_video(),
  │                       extract_images(), process_video(), main() CLI
  ├─ hub.py             ← FastAPI API: REST endpoints + WebSocket /ws/process
  └─ index_existing.py  ← Migration script for legacy projects

tui/
  ├─ src/index.tsx      ← App entry, screen router, navigation bar
  ├─ src/hooks/         ← useWebSocket.ts, useVideos.ts, useSearch.ts
  ├─ src/screens/       ← ProcessScreen, DashboardScreen, VideoDetailScreen, SearchScreen
  └─ src/components/    ← TerminalLog, VideoCard, SearchResult

pyproject.toml          ← Package config, entry points
Dockerfile              ← Multi-stage: Bun (TUI) + Python (runtime)
styles.css              ← CSS for generated HTML pages
projects/               ← Output directory (gitignored)
tube2txt.db             ← SQLite database (gitignored)
```

## Web Showcase (Gridland Aesthetic)

We've included a standalone React component that provides a "Gridland" inspired terminal experience for showcasing `tube2txt` on the web.

### Features

- **CRT Effect**: Authentic scanlines, flicker, and glow.
- **Simulated CLI**: Interactive typing demo showing the `--ai` pipeline.
- **TUI Grid**: Terminal-style feature showcase using box-drawing aesthetics.

Integration
Copy `tui/src/components/Tube2TxtShowcase.tsx` into your React/Next.js project. It requires **Tailwind CSS**.

```tsx
import Tube2TxtShowcase from "./components/Tube2TxtShowcase";
```

export default function Page() {
return <Tube2TxtShowcase />;
}

````

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/videos` | List all videos (ordered by date) |
| `GET` | `/api/videos/{slug}` | Video detail with segments and AI files |
| `GET` | `/api/videos/{slug}/images/{filename}` | Serve project images |
| `GET` | `/api/search?q=` | FTS5 full-text search across all transcripts |
| `WS` | `/ws/process` | Real-time video processing with progress events |

### WebSocket Protocol (`/ws/process`)

Send a JSON message to start processing:

```json
{
  "action": "start",
  "slug": "my-video",
  "url": "https://youtube.com/watch?v=...",
  "ai": true,
  "mode": "outline"
}
````

The server streams back `{"type": "...", "step": "...", "message": "..."}` events.

## Installation

### Method 1: uv (Recommended)

```bash
# Install Python deps into a virtual env
uv pip install -e "."

# Test deps
uv pip install pytest httpx
```

### Method 2: pip/pipx

```bash
# For global CLI access
pipx install .

# Or inside a venv
pip install .
```

After installation, three commands are available:

| Command          | Description                                                  |
| ---------------- | ------------------------------------------------------------ |
| `tube2txt`       | Main Python worker (VTT parsing, AI generation, DB indexing) |
| `tube2txt-hub`   | Starts the API server + serves the TUI dashboard             |
| `tube2txt-index` | Migrates or re-indexes existing projects                     |

### Method 3: Docker

```bash
docker compose up hub
# In another terminal:
docker compose run tube2txt tube2txt my-video "https://youtube.com/watch?v=..." --ai
```

## Usage

### Process a Video

```bash
tube2txt my-video "https://www.youtube.com/watch?v=..." --ai --mode notes
```

Output goes to `projects/my-video/`:

| File                  | Description                                  |
| --------------------- | -------------------------------------------- |
| `index.html`          | Transcript page with timestamped screenshots |
| `images/`             | Extracted video frames                       |
| `TUBE2TXT-OUTLINE.md` | AI outline (when `--ai` is used)             |
| `TUBE2TXT-NOTES.md`   | AI notes (when `--mode notes`)               |

### Launch the Hub + TUI

```bash
tube2txt-hub
# Open http://localhost:8000 in a browser, or the Gridland TUI connects automatically
```

### TUI Development

```bash
cd tui && bun install && bun run dev
```

### Build TUI for Production

```bash
cd tui && bun run build
# Output goes to tui/dist/, served at / by tube2txt-hub
```

### Smart Clips

```bash
# AI picks the best moments
tube2txt my-video "url" --ai --mode clips

# Manual clip extraction
tube2txt my-video "url" --clip 00:01:00-00:02:30
```

### Re-index Existing Projects

```bash
tube2txt-index
# Or: python3 -m tube2txt.index_existing
```

## Options

| Flag             | Description                                                           |
| ---------------- | --------------------------------------------------------------------- |
| `--ai`           | Generate AI content via Gemini                                        |
| `--mode <mode>`  | AI mode: `outline` (default), `notes`, `recipe`, `technical`, `clips` |
| `--parallel <N>` | Parallel ffmpeg processes for screenshot extraction (default: 4)      |

## Environment Variables

| Variable         | Description                                 | Default              |
| ---------------- | ------------------------------------------- | -------------------- |
| `GEMINI_API_KEY` | Google Gemini API key (required for `--ai`) | —                    |
| `TUBE2TXT_DB`    | Path to the SQLite database file            | `tube2txt.db` in CWD |
| `PORT`           | Port the hub server listens on              | `8000`               |

## Running Tests

```bash
.venv/bin/pytest tests/ -v
```

## Windows

See [WINDOWS-INSTALL.md](WINDOWS-INSTALL.md).

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

## License

MIT
