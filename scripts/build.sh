#!/usr/bin/env bash
# build.sh — Build the full Tube2Txt stack (TUI web bundle + Python package)
#
# Options:
#   --tui-only     Only build the TUI (skips Python reinstall)
#   --python-only  Only reinstall the Python package (skips TUI build)
#   --no-install   Build TUI but skip `uv pip install -e .` (useful if already installed)
#   --watch        After build, start the hub server
#
# Examples:
#   ./scripts/build.sh
#   ./scripts/build.sh --tui-only
#   ./scripts/build.sh --watch

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TUI_DIR="$ROOT/tui"

BUILD_TUI=true
BUILD_PYTHON=true
WATCH=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --tui-only)    BUILD_PYTHON=false; shift ;;
    --python-only) BUILD_TUI=false; shift ;;
    --no-install)  BUILD_PYTHON=false; shift ;;
    --watch)       WATCH=true; shift ;;
    -h|--help)
      sed -n '2,18p' "$0" | sed 's/^# //'
      exit 0 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

echo "=== Tube2Txt Build ==="
echo ""

# ── TUI ─────────────────────────────────────────────────────────────────────
if $BUILD_TUI; then
  echo "── TUI (browser build) ──────────────────────────────────"
  cd "$TUI_DIR"

  if [[ ! -d node_modules ]]; then
    echo "Installing TUI dependencies..."
    bun install --frozen-lockfile
  fi

  echo "Building web bundle..."
  bun run build-web

  echo "✓ TUI built → tui/dist/"
  echo ""
fi

# ── Python ───────────────────────────────────────────────────────────────────
if $BUILD_PYTHON; then
  echo "── Python package ───────────────────────────────────────"
  cd "$ROOT"

  # Detect uv or fall back to pip
  if command -v uv &>/dev/null; then
    echo "Installing with uv..."
    uv pip install -e ".[dev]"
  else
    if [[ -f .venv/bin/activate ]]; then
      source .venv/bin/activate
    fi
    echo "Installing with pip..."
    pip install -e ".[dev]" --quiet
  fi

  echo "✓ Python package installed"
  echo ""
fi

echo "=== Build complete ==="

if $WATCH; then
  echo ""
  echo "Starting hub server..."
  cd "$ROOT"
  if command -v uv &>/dev/null; then
    uv run tube2txt-hub
  else
    [[ -f .venv/bin/activate ]] && source .venv/bin/activate
    tube2txt-hub
  fi
fi
