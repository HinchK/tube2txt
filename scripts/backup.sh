#!/usr/bin/env bash
# backup.sh — Archive the database and optionally project files
#
# Creates a timestamped .tar.gz in ./backups/
#
# Options:
#   --db-only        Back up only tube2txt.db (fast, default)
#   --with-projects  Include the full projects/ directory
#   --with-media     Include projects/ AND video/media files (large)
#   --dest DIR       Output directory (default: ./backups)
#   --dry-run        Show what would be archived without writing
#
# Examples:
#   ./scripts/backup.sh
#   ./scripts/backup.sh --with-projects
#   ./scripts/backup.sh --with-projects --dest /mnt/nas/tube2txt-backups

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DB_PATH="$ROOT/tube2txt.db"
PROJECTS_DIR="$ROOT/projects"
DEST="$ROOT/backups"
MODE="db-only"
DRY_RUN=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --db-only)        MODE="db-only"; shift ;;
    --with-projects)  MODE="with-projects"; shift ;;
    --with-media)     MODE="with-media"; shift ;;
    --dest)           DEST="$2"; shift 2 ;;
    --dry-run)        DRY_RUN=true; shift ;;
    -h|--help)
      sed -n '2,16p' "$0" | sed 's/^# //'
      exit 0 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

TIMESTAMP=$(date +"%Y%m%d-%H%M%S")
ARCHIVE_NAME="tube2txt-backup-${TIMESTAMP}.tar.gz"
ARCHIVE_PATH="$DEST/$ARCHIVE_NAME"

echo "=== Tube2Txt Backup ==="
echo "Mode    : $MODE"
echo "Output  : $ARCHIVE_PATH"
echo ""

$DRY_RUN || mkdir -p "$DEST"

# Build tar arguments
TAR_ARGS=()
EXCLUDE_ARGS=()

case "$MODE" in
  db-only)
    [[ -f "$DB_PATH" ]] || { echo "ERROR: Database not found at $DB_PATH"; exit 1; }
    TAR_SOURCES=("tube2txt.db")
    ;;
  with-projects)
    # Exclude video/media files — keep transcripts, images, markdown
    EXCLUDE_ARGS=(
      "--exclude=projects/*.webm"
      "--exclude=projects/*.mp4"
      "--exclude=projects/*.mkv"
    )
    TAR_SOURCES=("tube2txt.db" "projects")
    ;;
  with-media)
    TAR_SOURCES=("tube2txt.db" "projects")
    ;;
esac

if $DRY_RUN; then
  echo "[DRY RUN] Would create: $ARCHIVE_PATH"
  echo "[DRY RUN] Contents:"
  for src in "${TAR_SOURCES[@]}"; do
    full="$ROOT/$src"
    if [[ -f "$full" ]]; then
      size=$(stat -f%z "$full" 2>/dev/null || stat -c%s "$full" 2>/dev/null || echo 0)
      echo "  $src  ($((size / 1024)) KB)"
    elif [[ -d "$full" ]]; then
      size=$(du -sh "$full" 2>/dev/null | awk '{print $1}')
      echo "  $src/  ($size)"
    fi
  done
  exit 0
fi

cd "$ROOT"
tar -czf "$ARCHIVE_PATH" "${EXCLUDE_ARGS[@]}" "${TAR_SOURCES[@]}"

ARCHIVE_SIZE=$(du -sh "$ARCHIVE_PATH" | awk '{print $1}')
echo "Backup created: $ARCHIVE_PATH  ($ARCHIVE_SIZE)"

# Prune old backups — keep last 10
echo ""
echo "Pruning old backups (keeping last 10)..."
mapfile -t old_backups < <(ls -t "$DEST"/tube2txt-backup-*.tar.gz 2>/dev/null | tail -n +11)
if [[ ${#old_backups[@]} -gt 0 ]]; then
  for f in "${old_backups[@]}"; do
    echo "  Removing old backup: $(basename "$f")"
    rm -f "$f"
  done
else
  echo "  Nothing to prune."
fi
