---
name: add-ai-mode
description: Add a new AI processing mode to the tube2txt pipeline. Handles all required touch-points across CLI args, GeminiClient prompts, and hub WebSocket parsing.
---

Add a new AI processing mode named `$ARGUMENTS` to the tube2txt pipeline. Touch these locations in order:

1. **`src/tube2txt/__init__.py`** — Add `$ARGUMENTS` to the `--mode` argparse `choices` list (search for `choices=["outline"`).

2. **`src/tube2txt/__init__.py`** — Add a prompt branch for `$ARGUMENTS` in `GeminiClient.generate_content()`. Follow the existing pattern: a descriptive system prompt tailored to the mode's purpose.

3. **`src/tube2txt/hub.py`** — Add `$ARGUMENTS` to the valid modes list in the WebSocket command handler (search for `"outline"` in the hub file).

4. **`CLAUDE.md`** — Update the `--mode` example line under "Python CLI" to include `$ARGUMENTS` in the pipe-delimited list.

After making changes, run: `.venv/bin/pytest tests/ -x -q` to confirm nothing broke.
