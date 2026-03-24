#!/bin/bash

# tube2txt.sh - Hybrid Bash/Python Youtube to Webpage converter with AI Outlines

set -euo pipefail

# Configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHON_SCRIPT="$SCRIPT_DIR/tube2txt.py"
STYLES_CSS="$SCRIPT_DIR/styles.css"
HUB_SCRIPT="$SCRIPT_DIR/hub.py"
PROJECTS_DIR="$SCRIPT_DIR/projects"
TUBE2TXT_DB="${TUBE2TXT_DB:-$SCRIPT_DIR/tube2txt.db}"

# Load environment variables if .env exists
if [[ -f "$SCRIPT_DIR/.env" ]]; then
    # Filter out comments and empty lines, then export
    export $(grep -v '^#' "$SCRIPT_DIR/.env" | grep -v '^\s*$' | xargs)
fi

# Usage
usage() {
    echo "Tube2Txt v3 - Local Hub & Smart Clips"
    echo ""
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  <project-name> <url>   Process a video or playlist"
    echo "  hub                    Start the Local Hub dashboard"
    echo "  clip <slug> <ts-range> Extract a manual clip (e.g. clip my-video 00:01:00-00:02:00)"
    echo ""
    echo "Options:"
    echo "  --ai             Generate markdown content using Gemini"
    echo "  --mode <mode>    AI mode: outline (default), notes, recipe, technical, clips"
    echo "  --parallel <N>   Number of parallel ffmpeg processes (default: 4)"
    echo "  --help           Show this help message"
    exit 1
}

# Hub command
if [[ "${1:-}" == "hub" ]]; then
    echo "Starting Tube2Txt Hub at http://localhost:8000"
    python3 "$HUB_SCRIPT"
    exit 0
fi

# Clip command
if [[ "${1:-}" == "clip" ]]; then
    SLUG=$2
    RANGE=$3
    VIDEO_FILE=$(ls "$PROJECTS_DIR/$SLUG"/video.* | head -n 1)
    if [[ ! -f "$VIDEO_FILE" ]]; then
        echo "Error: Video file not found for slug $SLUG"
        exit 1
    fi
    echo "Extracting clip $RANGE for $SLUG..."
    cd "$PROJECTS_DIR/$SLUG"
    python3 "$PYTHON_SCRIPT" --clip "$RANGE" --video-file "$(basename "$VIDEO_FILE")"
    exit 0
fi

# Check arguments
if [[ "$#" -lt 1 || "$1" == "--help" ]]; then
    usage
fi

SLUG=$1
URL=$2
AI_FLAG=""
MODE="outline"
PARALLEL=4

# Check GEMINI_API_KEY if --ai is used
check_api_key() {
    if [[ -z "${GEMINI_API_KEY:-}" ]]; then
        if [[ -f "$SCRIPT_DIR/.env" ]]; then
            export $(grep -v '^#' "$SCRIPT_DIR/.env" | xargs)
        fi
    fi
    if [[ -z "${GEMINI_API_KEY:-}" ]]; then
        echo "Error: GEMINI_API_KEY is not set. AI features require an API key."
        exit 1
    fi
}

# Shift arguments to check for flags
shift 2 || true # In case only 1 argument was provided
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --ai) AI_FLAG="--ai"; check_api_key ;;
        --mode) MODE="$2"; shift ;;
        --parallel) PARALLEL="$2"; shift ;;
        --help) usage ;;
        *) echo "Unknown parameter: $1"; usage ;;
    esac
    shift
done

# Check dependencies
for cmd in yt-dlp ffmpeg python3; do
    if ! command -v $cmd &> /dev/null; then
        echo "Error: $cmd is not installed."
        exit 1
    fi
done

# Ensure projects directory exists
mkdir -p "$PROJECTS_DIR"

# Function to process a single video
process_video() {
    local VIDEO_URL=$1
    local VIDEO_SLUG=$2
    
    echo "----------------------------------------------------"
    echo "Processing video: $VIDEO_SLUG ($VIDEO_URL)"
    echo "----------------------------------------------------"
    
    mkdir -p "$PROJECTS_DIR/$VIDEO_SLUG/images"
    
    local ABS_STYLES_CSS=$(realpath "$STYLES_CSS")
    local ABS_PYTHON_SCRIPT=$(realpath "$PYTHON_SCRIPT")

    pushd "$PROJECTS_DIR/$VIDEO_SLUG" > /dev/null

    echo "Downloading video and subtitles..."
    local VIDEO_FILE=$(yt-dlp --no-warnings --write-auto-subs --write-subs --no-simulate --print filename -o "video.%(ext)s" "$VIDEO_URL" | head -n 1)

    if [[ ! -f "$VIDEO_FILE" ]]; then
        VIDEO_FILE=$(ls video.* | head -n 1 2>/dev/null) || true
    fi

    if [[ -z "$VIDEO_FILE" || ! -f "$VIDEO_FILE" ]]; then
        echo "Error: Could not download video for $VIDEO_SLUG."
        popd > /dev/null
        return
    fi

    local VTT_FILE=$(ls video.en.vtt 2>/dev/null | head -n 1)
    if [[ -z "$VTT_FILE" ]]; then
        VTT_FILE=$(ls video.*.vtt 2>/dev/null | head -n 1)
    fi
    if [[ -z "$VTT_FILE" ]]; then
        VTT_FILE=$(ls *.vtt 2>/dev/null | head -n 1)
    fi

    if [[ -z "$VTT_FILE" ]]; then
        echo "Error: Could not find VTT subtitle file for $VIDEO_SLUG."
        popd > /dev/null
        return
    fi

    cp "$ABS_STYLES_CSS" .

    echo "Generating HTML and processing transcript..."
    local MODE_UPPER=$(echo "$MODE" | tr '[:lower:]' '[:upper:]')
    local OUTLINE_FILE="TUBE2TXT-${MODE_UPPER}.md"
    
    # Run Python logic and capture output
    local PY_OUTPUT=$(python3 "$ABS_PYTHON_SCRIPT" \
        --vtt "$VTT_FILE" \
        --url "$VIDEO_URL" \
        --slug "$VIDEO_SLUG" \
        --output-html "index.html" \
        --output-outline "$OUTLINE_FILE" \
        --mode "$MODE" \
        --db "$TUBE2TXT_DB" \
        $AI_FLAG)

    # Extract images in parallel
    echo "Extracting images in parallel ($PARALLEL processes)..."
    local TS_FILE=$(mktemp)
    echo "$PY_OUTPUT" | grep "^TIMESTAMP:" | sed 's/TIMESTAMP://' > "$TS_FILE"
    
    export VIDEO_FILE
    cat "$TS_FILE" | xargs -I {} -P "$PARALLEL" bash -c '
        TS="$1"
        TS_FILENAME=${TS//:/-}
        TS_FILENAME=${TS_FILENAME//./-}
        if [[ ! -f "images/$TS_FILENAME.jpg" ]]; then
            ffmpeg -ss "$TS" -nostdin -i "$VIDEO_FILE" -frames:v 1 -q:v 2 -vf scale=1024:-1 "images/$TS_FILENAME.jpg" -loglevel error
        fi
    ' -- {}
    rm "$TS_FILE"

    # AI Clipping Logic
    if [[ "$MODE" == "clips" && "$AI_FLAG" == "--ai" ]]; then
        echo "Extracting AI-recommended clips..."
        echo "$PY_OUTPUT" | grep "^CLIP:" | while read -r line; do
            local RANGE=$(echo "$line" | cut -d'|' -f2)
            echo "Extracting AI clip: $RANGE"
            python3 "$ABS_PYTHON_SCRIPT" --clip "$RANGE" --video-file "$VIDEO_FILE"
        done
    fi

    echo "Finished: $VIDEO_SLUG"
    popd > /dev/null
}

if ! command -v realpath &> /dev/null; then
    realpath() {
        [[ $1 = /* ]] && echo "$1" || echo "$PWD/${1#./}"
    }
fi

# Main logic
if [[ "$URL" == *"playlist?list="* ]] || [[ "$URL" == *"&list="* ]]; then
    echo "Playlist detected: $URL"
    PLAYLIST_NAME="$SLUG"
    mkdir -p "$PROJECTS_DIR/$PLAYLIST_NAME"
    pushd "$PROJECTS_DIR/$PLAYLIST_NAME" > /dev/null
    
    echo "Fetching video list..."
    yt-dlp --quiet --flat-playlist --print "%(id)s" --print "%(title)s" "$URL" > playlist_data.txt
    
    while IFS= read -r ID && IFS= read -r TITLE; do
        CLEAN_TITLE=$(echo "$TITLE" | sed 's/[^a-zA-Z0-9]/_/g' | cut -c1-50)
        process_video "https://www.youtube.com/watch?v=$ID" "$CLEAN_TITLE"
    done < playlist_data.txt
    
    rm playlist_data.txt
    echo "Playlist processing complete!"
    popd > /dev/null
else
    if [[ ! "$URL" =~ ^http ]] && [[ ${#URL} -eq 11 ]]; then
        echo "Detected video ID: $URL. Using full YouTube URL."
        URL="https://www.youtube.com/watch?v=$URL"
    fi
    process_video "$URL" "$SLUG"
fi

echo "All tasks complete!"
