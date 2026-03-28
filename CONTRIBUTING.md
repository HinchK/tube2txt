# Contributing to Tube2Txt

## Development Setup

```bash
git clone <repo-url>
cd PATIENCE-HAMMER-BOOBS

# Python backend
uv pip install -e "."
uv pip install pytest httpx

# Gridland TUI (optional)
cd tui && bun install
```

## Project Structure

```
src/tube2txt/        ← Python package (core, hub, indexer)
tui/src/             ← Gridland TUI (Bun + OpenTUI + React)
tests/               ← pytest integration tests
```

## Key Conventions

- **Python deps**: The system pip is PEP 668 blocked — always use `uv pip`.
- **After editing `src/tube2txt/__init__.py`**: Run `uv pip install -e "."` before running tests so new exports are visible.
- **TUI components**: Use lowercase JSX intrinsics (`<box>`, `<text>`, `<input>`, `<select>`, `<scrollbox>`) per the OpenTUI API — never PascalCase.
- **TUI build target**: `bun build --target bun` is required because OpenTUI uses `bun:ffi` internally.
- **`select` component**: Takes `options: [{label, value}]` and `onChange: (index) => void` — not `items`/`value` props.
- **Gridland renderer**: `const renderer = await createCliRenderer(); createRoot(renderer).render(<App />)` — not a bare `render()` call.

## Running Tests

```bash
.venv/bin/pytest tests/ -v
```

## Submitting Changes

1. Fork the repository and create a feature branch.
2. Make changes following the conventions above.
3. Run the test suite and confirm it passes.
4. Open a pull request with a clear description of what changed and why.

## Reporting Issues

Open a GitHub issue with steps to reproduce, expected behavior, and actual behavior.

## Code of Conduct

Be respectful and professional in all interactions.
