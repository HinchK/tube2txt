#!/bin/bash

# tube2txt.sh - Hybrid Bash/Python Youtube to Webpage converter with AI Outlines

set -eo pipefail

# Configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHON_SCRIPT="uv run tube2txt"
STYLES_CSS="$SCRIPT_DIR/styles.css"
HUB_CMD="uv run tube2txt-hub"
PROJECTS_DIR="$SCRIPT_DIR/projects"
TUBE2TXT_DB="${TUBE2TXT_DB:-$SCRIPT_DIR/tube2txt.db}"
VERBOSE=0
ARTIFACTS_FILE=$(mktemp)

# Load environment variables if .env exists
if [[ -f "$SCRIPT_DIR/.env" ]]; then
    export $(grep -v '^#' "$SCRIPT_DIR/.env" | grep -v '^\s*$' | xargs)
fi

# Cookie detection for yt-dlp
COOKIES_ARG=""

if [[ -n "${YT_DLP_COOKIES:-}" && -f "$YT_DLP_COOKIES" ]]; then
   COOKIES_ARG="--verbose --cookies $YT_DLP_COOKIES"
elif [[ -f "$SCRIPT_DIR/cookies.txt" ]]; then
   COOKIES_ARG="--verbose --cookies $SCRIPT_DIR/cookies.txt"
elif [[ -f "$PROJECTS_DIR/cookies.txt" ]]; then
   COOKIES_ARG="--verbose --cookies $PROJECTS_DIR/cookies.txt"
elif [[ -f "$SCRIPT_DIR/src/cookies.txt" ]]; then
   COOKIES_ARG="--verbose --cookies $SCRIPT_DIR/src/cookies.txt"
fi

# Verbose output helper
v_echo() {
    if [[ "$VERBOSE" -eq 1 ]]; then
        echo "[VERBOSE] $1"
    fi
}

# Usage
usage() {
    echo "Tube2Txt v3 - Local Hub & Smart Clips"
    echo ""
    echo "Usage: $0 [slug] <url> [options]"
    echo "       $0 <url> [options] (slug defaults to 'default')"
    echo ""
    echo "Commands:"
    echo "  hub                    Start the Local Hub dashboard"
    echo "  clip <slug> <ts-range> Extract a manual clip (e.g. clip my-video 00:01:00-00:02:00)"
    echo ""
    echo "Options:"
    echo "  -v, --verbose    Output all steps for troubleshooting"
    echo "  --ai             Generate markdown content using Gemini (auto if API key exists)"
    echo "  --mode <mode>    AI mode: outline (default), notes, recipe, technical, clips"
    echo "  --parallel <N>   Number of parallel ffmpeg processes (default: 4)"
    echo "  --help           Show this help message"
    exit 1
}

# Hub command
if [[ "${1:-}" == "hub" ]]; then
    echo "Starting Tube2Txt Hub at http://localhost:8000"
    $HUB_CMD
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
    $PYTHON_SCRIPT add --clip "$RANGE" --video-file "$(basename "$VIDEO_FILE")"
    exit 0
fi

# Initialize variables
SLUG=""
URL=""
AI_FLAG=""
MODE="outline"
PARALLEL=4

# Check for verbose flag early
for arg in "$@"; do
    if [[ "$arg" == "-v" || "$arg" == "--verbose" ]]; then
        VERBOSE=1
        set -x
    fi
done

# Progressive disclosure if no parameters
if [[ "$#" -eq 0 ]]; then
    echo "--- Tube2Txt Interactive Setup ---"
    read -p "Enter YouTube URL: " URL
    if [[ -z "$URL" ]]; then echo "URL is required."; exit 1; fi

    read -p "Enter project title (default: default): " SLUG
    SLUG=${SLUG:-default}

    if [[ -n "${GEMINI_API_KEY:-}" ]]; then
        read -p "Perform AI outline creation? (Y/n): " AI_CHOICE
        if [[ "$AI_CHOICE" != "n" ]]; then AI_FLAG="--ai"; fi
    fi
else
    # Parse arguments
    while [[ "$#" -gt 0 ]]; do
        case $1 in
            -v|--verbose) VERBOSE=1 ;;
            --ai) AI_FLAG="--ai" ;;
            --mode) MODE="$2"; shift ;;
            --parallel) PARALLEL="$2"; shift ;;
            --help) usage ;;
            -*) echo "Unknown parameter: $1"; usage ;;
            *)
                if [[ -z "$URL" ]]; then
                    if [[ -z "$SLUG" && "$#" -ge 2 && ! "$2" =~ ^- ]]; then
                        SLUG=$1
                        URL=$2
                        shift
                    else
                        URL=$1
                        SLUG=${SLUG:-default}
                    fi
                fi
                ;;
        esac
        shift
    done
fi

if [[ -z "$URL" ]]; then
    usage
fi

# Auto-enable AI if API key is present
if [[ -n "${GEMINI_API_KEY:-}" ]]; then
    AI_FLAG="--ai"
fi

# Check dependencies
for cmd in yt-dlp ffmpeg python3 uv; do
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

    v_echo "Running Python worker: $PYTHON_SCRIPT"
    # Run Python logic
    $PYTHON_SCRIPT add "$VIDEO_URL" "$VIDEO_SLUG" \
        --mode "$MODE" \
        --db "$TUBE2TXT_DB" \
        --parallel "$PARALLEL" \
        $AI_FLAG

    # Log artifacts
    {
        local PROJ_PATH="$PROJECTS_DIR/$VIDEO_SLUG"
        echo "[$VIDEO_SLUG Artifacts]"
        echo "  - Index Page:  $PROJ_PATH/index.html"
        echo "  - Stylesheet:  $PROJ_PATH/styles.css"
        if [[ -f "$PROJ_PATH/TUBE2TXT-OUTLINE.md" ]]; then
            echo "  - AI Outline:  $PROJ_PATH/TUBE2TXT-OUTLINE.md"
        fi
        echo ""
    } >> "$ARTIFACTS_FILE"

    echo "Finished: $VIDEO_SLUG"
}

if ! command -v realpath &> /dev/null; then
    realpath() {
        [[ $1 = /* ]] && echo "$1" || echo "$PWD/${1#./}"
    }
fi

# Main logic
if [[ "$URL" == *"playlist?list="* ]] || [[ "$URL" == *"&list="* ]]; then
    v_echo "Playlist detected: $URL"
    PLAYLIST_NAME="$SLUG"
    mkdir -p "$PROJECTS_DIR/$PLAYLIST_NAME"
    
    # We use yt-dlp to get the list, then call our python CLI for each
    echo "Fetching video list..."
    yt-dlp $COOKIES_ARG --flat-playlist --print "%(id)s" --print "%(title)s" "$URL" > playlist_data.txt

    while IFS= read -r ID && IFS= read -r TITLE; do
        CLEAN_TITLE=$(echo "$TITLE" | sed 's/[^a-zA-Z0-9]/_/g' | cut -c1-50)
        process_video "https://www.youtube.com/watch?v=$ID" "$CLEAN_TITLE"
    done < playlist_data.txt

    rm playlist_data.txt
    echo "Playlist processing complete!"
else
    if [[ ! "$URL" =~ ^http ]] && [[ ${#URL} -eq 11 ]]; then
        v_echo "Detected video ID: $URL. Using full YouTube URL."
        URL="https://www.youtube.com/watch?v=$URL"
    fi
    process_video "$URL" "$SLUG"
fi

echo "All tasks complete!"

if [[ -f "$ARTIFACTS_FILE" ]]; then
    echo ""
    echo "--- GENERATED ARTIFACTS ---"
    cat "$ARTIFACTS_FILE"
    rm "$ARTIFACTS_FILE"
fi
