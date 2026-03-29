---
name: gen-test
description: Generate pytest tests for tube2txt following the established patterns in tests/test_api.py and tests/test_process_video.py. Pass the function or endpoint to test as the argument.
---

Generate a pytest test for `$ARGUMENTS` following the patterns in `tests/test_api.py` and `tests/test_process_video.py`.

## Established Patterns to Follow

**For API/hub tests** (add to `tests/test_api.py`):
- Use the `client` fixture which patches `TUBE2TXT_DB` and `PROJECTS_DIR` via `patch.dict(os.environ, ...)`
- For WebSocket tests, use `client.websocket_connect("/ws/process")` and collect messages until `type in ("complete", "error")`
- Seed test data in the `test_env` fixture's SQLite DB, never use production paths

**For pipeline unit tests** (add to `tests/test_process_video.py`):
- Mock external calls (`yt-dlp`, `ffmpeg`, `GeminiClient`) with `unittest.mock.patch`
- Test `on_progress` callback invocations to verify the pipeline emits correct step names

## Steps

1. Read the relevant source file to understand the function/endpoint signature
2. Identify the minimal fixture setup needed
3. Write the test function with a clear docstring describing what it asserts
4. Ensure the test is isolated — no real network calls, no real file I/O unless using `tmp_path`
5. Run `.venv/bin/pytest tests/ -x -q` to confirm the new test passes

Place the test in the appropriate existing file rather than creating a new one.
