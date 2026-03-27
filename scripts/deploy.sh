#!/usr/bin/env bash
# deploy.sh — Build Docker image and deploy Tube2Txt
#
# Targets:
#   local    Build image + start via docker-compose (default)
#   railway  Push to Railway via `railway up`
#   docker   Build + push to a registry (requires --image)
#
# Options:
#   --target TARGET     Deployment target: local|railway|docker (default: local)
#   --image IMAGE       Full image name for docker push (e.g. ghcr.io/user/tube2txt:latest)
#   --no-cache          Pass --no-cache to docker build
#   --dry-run           Print commands without executing them
#
# Examples:
#   ./scripts/deploy.sh
#   ./scripts/deploy.sh --target railway
#   ./scripts/deploy.sh --target docker --image ghcr.io/youruser/tube2txt:latest
#   ./scripts/deploy.sh --no-cache --dry-run

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

TARGET="local"
IMAGE=""
NO_CACHE=false
DRY_RUN=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)   TARGET="$2"; shift 2 ;;
    --image)    IMAGE="$2"; shift 2 ;;
    --no-cache) NO_CACHE=true; shift ;;
    --dry-run)  DRY_RUN=true; shift ;;
    -h|--help)
      sed -n '2,17p' "$0" | sed 's/^# //'
      exit 0 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

run() {
  if $DRY_RUN; then
    echo "[DRY RUN] $*"
  else
    echo "+ $*"
    "$@"
  fi
}

cd "$ROOT"

echo "=== Tube2Txt Deploy ==="
echo "Target  : $TARGET"
$DRY_RUN && echo "Mode    : DRY RUN"
echo ""

case "$TARGET" in
  # ── Local (docker-compose) ────────────────────────────────────────────────
  local)
    BUILD_ARGS=()
    $NO_CACHE && BUILD_ARGS+=("--no-cache")

    echo "── Building Docker image ────────────────────────────────"
    run docker compose build "${BUILD_ARGS[@]}" hub

    echo ""
    echo "── Starting hub service ─────────────────────────────────"
    run docker compose up -d hub

    echo ""
    echo "Hub running at http://localhost:8000"
    echo "Logs: docker compose logs -f hub"
    ;;

  # ── Railway ───────────────────────────────────────────────────────────────
  railway)
    if ! command -v railway &>/dev/null; then
      echo "ERROR: Railway CLI not found. Install: npm i -g @railway/cli"
      exit 1
    fi
    echo "── Deploying to Railway ─────────────────────────────────"
    run railway up
    ;;

  # ── Docker registry ───────────────────────────────────────────────────────
  docker)
    if [[ -z "$IMAGE" ]]; then
      echo "ERROR: --image is required for --target docker"
      echo "  Example: --image ghcr.io/youruser/tube2txt:latest"
      exit 1
    fi

    BUILD_ARGS=("--tag" "$IMAGE")
    $NO_CACHE && BUILD_ARGS+=("--no-cache")

    echo "── Building image: $IMAGE ───────────────────────────────"
    run docker build "${BUILD_ARGS[@]}" .

    echo ""
    echo "── Pushing to registry ──────────────────────────────────"
    run docker push "$IMAGE"

    echo ""
    echo "Image available: $IMAGE"
    ;;

  *)
    echo "Unknown target: $TARGET (choose: local|railway|docker)"
    exit 1
    ;;
esac

echo ""
echo "=== Deploy complete ==="
