---
name: project-conventions
description: Tube2Txt project conventions loaded as background context for Claude. Covers naming rules, pipeline patterns, TUI component API, and common gotchas.
user-invocable: false
---

## Tube2Txt Project Conventions

Always apply these when writing or editing code in this repo:

### Output & File Naming
- All project output goes to `projects/<slug>/`
- Image filenames: `HH-MM-SS-mmm.jpg` (colons and dots replaced with dashes)
- AI output files: `TUBE2TXT-<MODE>.md` where MODE is uppercase (e.g., `TUBE2TXT-OUTLINE.md`)

### Pipeline
- `process_video()` is the single orchestration entry point — don't call sub-steps directly from outside
- `on_progress` callback signature is always `(type_: str, step: str, message: str) -> None`
- Pass `None` for `on_progress` in CLI contexts; pass a function in WebSocket/hub contexts
- Pipeline steps in order: download → parse → generate_html → index → ai → extract_images

### AI Modes
- Valid modes: `outline`, `notes`, `recipe`, `technical`, `clips`
- Adding a new mode requires changes in 3 places: argparse choices, `GeminiClient.generate_content()`, hub WebSocket validation
- Mode names are lowercase in code, uppercase in filenames

### TUI (OpenTUI / Gridland)
- JSX intrinsics are lowercase: `<box>`, `<text>`, `<input>`, `<select>`, `<scrollbox>` — never PascalCase
- Renderer init: `const renderer = await createCliRenderer(); createRoot(renderer).render(<App />)`
- `select` takes `options: [{label, value}]` and `onChange: (index) => void` — not `items`/`value`
- Build target must be `--target bun` (OpenTUI uses `bun:ffi`)

### Testing
- Hub tests patch `TUBE2TXT_DB` and `PROJECTS_DIR` via `patch.dict(os.environ, ...)` + module re-import
- Never use real network or file I/O in unit tests — use `tmp_path` and mocks
- WebSocket tests collect messages until `type in ("complete", "error")`

### Environment
- `GEMINI_API_KEY` in `.env` — never hardcode or log
- `TUBE2TXT_DB` overrides DB path; `PORT` controls uvicorn port
- After editing `__init__.py`, run `uv pip install -e "."` to refresh entry points

### Common Gotchas
- `uv.lock` corruption shows as `aversion` instead of `version` in TOML — regenerate if build fails
- `tube2txt-hub` handles `PORT` env var automatically for Railway deployments
- `bun.lock` should be committed; `node_modules/` is gitignored via `tui/.gitignore`
