#!/usr/bin/env bash
# test.sh — Run the Tube2Txt test suite
#
# Options:
#   --api          Run only API/WebSocket tests (test_api.py)
#   --pipeline     Run only pipeline unit tests (test_process_video.py)
#   --verbose, -v  Pass -v to pytest
#   --failfast, -x Stop on first failure
#   --coverage     Run with coverage report
#   --clean        Remove __pycache__ and .pytest_cache before running
#
# Examples:
#   ./scripts/test.sh
#   ./scripts/test.sh --api -v
#   ./scripts/test.sh --coverage

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TESTS_DIR="$ROOT/tests"

SUITE=""
VERBOSE=false
FAILFAST=false
COVERAGE=false
CLEAN=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --api)         SUITE="test_api.py"; shift ;;
    --pipeline)    SUITE="test_process_video.py"; shift ;;
    -v|--verbose)  VERBOSE=true; shift ;;
    -x|--failfast) FAILFAST=true; shift ;;
    --coverage)    COVERAGE=true; shift ;;
    --clean)       CLEAN=true; shift ;;
    -h|--help)
      sed -n '2,16p' "$0" | sed 's/^# //'
      exit 0 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

cd "$ROOT"

# Activate venv
if [[ -f .venv/bin/activate ]]; then
  source .venv/bin/activate
elif [[ -f venv/bin/activate ]]; then
  source venv/bin/activate
fi

# ── Clean ────────────────────────────────────────────────────────────────────
if $CLEAN; then
  echo "Cleaning caches..."
  find "$ROOT" -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
  rm -rf "$ROOT/.pytest_cache"
  echo "Done."
fi

# ── Build pytest command ─────────────────────────────────────────────────────
PYTEST_ARGS=()

if [[ -n "$SUITE" ]]; then
  PYTEST_ARGS+=("$TESTS_DIR/$SUITE")
else
  PYTEST_ARGS+=("$TESTS_DIR/")
fi

$VERBOSE  && PYTEST_ARGS+=("-v")
$FAILFAST && PYTEST_ARGS+=("-x")

if $COVERAGE; then
  if ! command -v coverage &>/dev/null && ! python -m coverage --version &>/dev/null 2>&1; then
    echo "Installing coverage..."
    pip install coverage --quiet
  fi
  echo "=== Running tests with coverage ==="
  python -m coverage run -m pytest "${PYTEST_ARGS[@]}"
  echo ""
  python -m coverage report -m --include="src/tube2txt/*"
else
  echo "=== Running tests ==="
  python -m pytest "${PYTEST_ARGS[@]}"
fi
