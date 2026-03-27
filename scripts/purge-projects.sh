#!/usr/bin/env bash
# purge-projects.sh — Trim the projects/ directory
#
# Modes:
#   --keep-last N   Delete oldest projects, keeping the N most recently modified (default: 10)
#   --older-than N  Delete projects not modified in the last N days
#   --videos-only   Delete only video files (.webm, .mp4, .mkv) inside each project (keep transcripts/images)
#   --dry-run       Print what would be deleted without deleting anything
#
# Examples:
#   ./scripts/purge-projects.sh --keep-last 10
#   ./scripts/purge-projects.sh --older-than 30 --dry-run
#   ./scripts/purge-projects.sh --videos-only
#   ./scripts/purge-projects.sh --keep-last 5 --videos-only

set -euo pipefail

PROJECTS_DIR="$(cd "$(dirname "$0")/.." && pwd)/projects"
KEEP_LAST=""
OLDER_THAN=""
VIDEOS_ONLY=false
DRY_RUN=false

# ── Argument parsing ────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --keep-last)   KEEP_LAST="$2"; shift 2 ;;
    --older-than)  OLDER_THAN="$2"; shift 2 ;;
    --videos-only) VIDEOS_ONLY=true; shift ;;
    --dry-run)     DRY_RUN=true; shift ;;
    -h|--help)
      sed -n '2,14p' "$0" | sed 's/^# //'
      exit 0 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

if [[ -z "$KEEP_LAST" && -z "$OLDER_THAN" && "$VIDEOS_ONLY" == false ]]; then
  echo "Usage: $0 [--keep-last N] [--older-than DAYS] [--videos-only] [--dry-run]"
  exit 1
fi

[[ -d "$PROJECTS_DIR" ]] || { echo "Projects directory not found: $PROJECTS_DIR"; exit 1; }

DRY_PREFIX=""
$DRY_RUN && DRY_PREFIX="[DRY RUN] "

echo "${DRY_PREFIX}Projects directory: $PROJECTS_DIR"

freed=0

# ── Helper: human-readable bytes ───────────────────────────────────────────
human_bytes() {
  local bytes=$1
  if   (( bytes >= 1073741824 )); then printf "%.1f GB" "$(echo "scale=1; $bytes/1073741824" | bc)"
  elif (( bytes >= 1048576 ));    then printf "%.1f MB" "$(echo "scale=1; $bytes/1048576" | bc)"
  elif (( bytes >= 1024 ));       then printf "%.1f KB" "$(echo "scale=1; $bytes/1024" | bc)"
  else printf "%d B" "$bytes"; fi
}

# ── Mode: --videos-only ─────────────────────────────────────────────────────
if $VIDEOS_ONLY; then
  echo "${DRY_PREFIX}Removing video files (.webm/.mp4/.mkv/.vtt) from all projects..."
  while IFS= read -r -d '' f; do
    size=$(stat -f%z "$f" 2>/dev/null || stat -c%s "$f" 2>/dev/null || echo 0)
    echo "${DRY_PREFIX}  DELETE $(basename "$(dirname "$f")")/$(basename "$f")  ($(human_bytes "$size"))"
    $DRY_RUN || { rm -f "$f"; freed=$((freed + size)); }
    $DRY_RUN && freed=$((freed + size))
  done < <(find "$PROJECTS_DIR" -maxdepth 2 \( -name "*.webm" -o -name "*.mp4" -o -name "*.mkv" -o -name "*.vtt" \) -print0)
fi

# ── Mode: --older-than DAYS ─────────────────────────────────────────────────
if [[ -n "$OLDER_THAN" ]]; then
  echo "${DRY_PREFIX}Removing projects not modified in the last ${OLDER_THAN} days..."
  while IFS= read -r -d '' dir; do
    slug=$(basename "$dir")
    size=$(du -sk "$dir" 2>/dev/null | awk '{print $1 * 1024}')
    echo "${DRY_PREFIX}  DELETE $slug  ($(human_bytes "$size"))"
    $DRY_RUN || { rm -rf "$dir"; freed=$((freed + size)); }
    $DRY_RUN && freed=$((freed + size))
  done < <(find "$PROJECTS_DIR" -mindepth 1 -maxdepth 1 -type d -not -newer "$PROJECTS_DIR" -mtime +"$OLDER_THAN" -print0)
fi

# ── Mode: --keep-last N ──────────────────────────────────────────────────────
if [[ -n "$KEEP_LAST" ]]; then
  echo "${DRY_PREFIX}Keeping last $KEEP_LAST projects by modification time..."
  # List all project dirs sorted newest→oldest, skip first $KEEP_LAST
  mapfile -d '' all_dirs < <(find "$PROJECTS_DIR" -mindepth 1 -maxdepth 1 -type d -print0 \
    | xargs -0 ls -dt 2>/dev/null | tr '\n' '\0')

  # Rebuild null-delimited via ls -dt
  to_delete=()
  i=0
  while IFS= read -r dir; do
    i=$((i + 1))
    (( i > KEEP_LAST )) && to_delete+=("$dir")
  done < <(find "$PROJECTS_DIR" -mindepth 1 -maxdepth 1 -type d -print0 \
            | xargs -0 ls -dt 2>/dev/null)

  if [[ ${#to_delete[@]} -eq 0 ]]; then
    echo "  Nothing to delete (${i} projects ≤ keep-last ${KEEP_LAST})."
  else
    for dir in "${to_delete[@]}"; do
      slug=$(basename "$dir")
      size=$(du -sk "$dir" 2>/dev/null | awk '{print $1 * 1024}')
      echo "${DRY_PREFIX}  DELETE $slug  ($(human_bytes "$size"))"
      $DRY_RUN || { rm -rf "$dir"; freed=$((freed + size)); }
      $DRY_RUN && freed=$((freed + size))
    done
  fi
fi

echo ""
if $DRY_RUN; then
  echo "Dry run complete. Would free: $(human_bytes "$freed")"
else
  echo "Done. Freed: $(human_bytes "$freed")"
fi
