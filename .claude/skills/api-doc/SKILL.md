---
name: api-doc
description: Generate or update API documentation for the Tube2Txt FastAPI hub. Produces a markdown reference covering all REST endpoints and the WebSocket protocol.
---

Generate complete API documentation for `src/tube2txt/hub.py`. Output a markdown doc covering:

## REST Endpoints

Document each route in this format:
```
### GET /api/videos
Returns all videos ordered by date DESC.

**Response**: `[{slug, url, title, processed_at}]`
```

Routes to document:
- `GET /healthcheck`
- `GET /api/videos`
- `GET /api/videos/{slug}` — include the `segments` and `ai_files` fields in the response shape
- `GET /api/videos/{slug}/images/{filename}`
- `GET /api/search?q=` — note the FTS5 MATCH behavior and 20-result limit

## WebSocket Protocol

Document `/ws/process`:

**Send** (to start a job):
```json
{"action": "start", "slug": "my-video", "url": "https://...", "ai": true, "mode": "outline", "parallel": 4}
```
Or send a raw command string: `{"action": "start", "command": "tube2txt my-video https://... --ai"}`

**Receive** (progress stream):
```json
{"type": "status|error|complete", "step": "download|parse|generate|index|ai|images", "message": "..."}
```

**Constraints**: Only one job runs at a time (lock-protected). A second `start` while a job is running returns `{"type": "error", "message": "A job is already in progress"}`.

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `TUBE2TXT_DB` | `./tube2txt.db` | SQLite database path |
| `TUBE2TXT_TUI_DIR` | auto-detected | Override TUI dist directory |
| `PORT` | `8000` | uvicorn bind port |

Write the output to `API.md` in the project root.
