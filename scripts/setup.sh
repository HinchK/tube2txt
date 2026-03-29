#!/usr/bin/env bash
# setup.sh — Initialize the Tube2Txt environment (Python + TUI)
#
# Usage:
#   ./scripts/setup.sh
#
# Requirements:
#   - Python 3.9+
#   - uv (recommended) or pip
#   - bun (required for TUI build)

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TUI_DIR="$ROOT/tui"

echo "=== Tube2Txt Setup ==="
echo ""

# ── Check Requirements ──────────────────────────────────────────────────────
echo "── Checking Requirements ────────────────────────────────"

if ! command -v bun &>/dev/null; then
  echo "ERROR: 'bun' not found. Please install Bun (https://bun.sh) to build the TUI."
  exit 1
fi

if ! command -v python3 &>/dev/null; then
  echo "ERROR: 'python3' not found."
  exit 1
fi

echo "✓ Requirements met"
echo ""

# ── Python Environment ──────────────────────────────────────────────────────
echo "── Python Environment ───────────────────────────────────"
cd "$ROOT"

if command -v uv &>/dev/null; then
  echo "Using 'uv' for environment management..."
  if [[ ! -d .venv ]]; then
    uv venv
  fi
  source .venv/bin/activate
  echo "Installing dependencies..."
  uv pip install -e ".[dev]"
else
  echo "Using 'pip' for environment management..."
  if [[ ! -d .venv ]]; then
    python3 -m venv .venv
  fi
  source .venv/bin/activate
  echo "Installing dependencies..."
  pip install -e ".[dev]"
fi

echo "✓ Python environment ready"
echo ""

# ── TUI Build ───────────────────────────────────────────────────────────────
echo "── TUI Build ────────────────────────────────────────────"
cd "$TUI_DIR"

echo "Installing TUI dependencies..."
bun install

echo "Building production web bundle..."
bun run build-web

echo "✓ TUI build complete"
echo ""

# ── Finish ──────────────────────────────────────────────────────────────────
echo "=== Setup complete! ==="
echo ""
echo "To start the Tube2Txt Hub:"
echo "  uv run tube2txt-hub"
echo ""
echo "To process a video via CLI:"
echo "  uv run tube2txt my-video \"URL\" --ai"
echo ""
echo "To run tests:"
echo "  ./scripts/test.sh"
echo ""
echo "Don't forget to set your GEMINI_API_KEY in a .env file!"
