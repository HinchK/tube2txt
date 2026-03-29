---
name: release-notes
description: Generate release notes for a new tube2txt version from git history. Pass the previous version tag as the argument (e.g., /release-notes v3.0.0).
disable-model-invocation: true
---

Generate release notes for the next tube2txt release, comparing against `$ARGUMENTS` (or `HEAD~20` if no tag given).

## Steps

1. Get the current version from `pyproject.toml`:
```bash
grep '^version' pyproject.toml
```

2. Get commits since the last tag:
```bash
git log $ARGUMENTS..HEAD --oneline --no-merges
```

3. Get a full diff summary:
```bash
git diff $ARGUMENTS --stat
```

4. Categorize commits into sections:
   - **New Features** — new AI modes, new endpoints, new CLI flags
   - **Improvements** — pipeline changes, performance, UX
   - **Bug Fixes** — any fix commits
   - **Breaking Changes** — API shape changes, renamed flags, removed endpoints

5. Output release notes in this format:
```markdown
## tube2txt v<VERSION> — <date>

### New Features
- ...

### Improvements
- ...

### Bug Fixes
- ...

### Breaking Changes
- ...

### Upgrade Notes
Any migration steps (e.g., re-run `tube2txt-index` if DB schema changed).
```

Write to `CHANGELOG.md` (append at top, preserve existing entries).
