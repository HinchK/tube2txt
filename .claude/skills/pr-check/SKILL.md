---
name: pr-check
description: Run a pre-merge checklist for the current branch against main. Verifies tests, conventions, and deployment readiness before creating a PR.
disable-model-invocation: true
---

Run the following checklist before creating a PR from the current branch:

## 1. Tests
```bash
.venv/bin/pytest tests/ -v
```
All tests must pass. If any fail, stop and fix before continuing.

## 2. TUI Build
```bash
cd tui && bun run build-web && cd ..
```
Confirm `tui/dist/index.html` exists after build.

## 3. Convention Checks
- [ ] New AI modes added to all 3 locations: argparse choices, `GeminiClient.generate_content()`, hub WebSocket validation
- [ ] Any new `on_progress` calls use the correct signature: `(type_, step, message)`
- [ ] Image filenames use `HH-MM-SS-mmm.jpg` format (dashes, not colons)
- [ ] AI output files named `TUBE2TXT-<MODE>.md` (uppercase mode)
- [ ] No new secrets or API keys hardcoded (check with `git diff main | grep -iE 'api_key|secret|password'`)

## 4. Docker Sanity
```bash
docker compose build hub --no-cache 2>&1 | tail -5
```
Confirm the build completes without error.

## 5. Git Summary
```bash
git log main..HEAD --oneline
git diff main --stat
```
Review what's changing. Summarize for the PR description.

## Output
Report results for each step. If all pass, output a draft PR title and one-paragraph description ready to paste into `gh pr create`.
