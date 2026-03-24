#!/bin/bash

# tube2txt.sh - Hybrid Bash/Python Youtube to Webpage converter with AI Outlines

set -euo pipefail

# Configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHON_SCRIPT="$SCRIPT_DIR/tube2txt.py"
STYLES_CSS="$SCRIPT_DIR/styles.css"

# Usage
usage() {
    echo "Tube2Txt - Convert Youtube videos to structured web pages with AI outlines."
    echo ""
    echo "Usage: $0 project-name \"video-url\" [options]"
    echo ""
    echo "Options:"
    echo "  --ai             Generate markdown content using Gemini (requires GEMINI_API_KEY)"
    echo "  --mode <mode>    AI mode: outline (default), notes, recipe, technical"
    echo "  --parallel <N>   Number of parallel ffmpeg processes (default: 4)"
    echo "  --help           Show this help message"
    echo ""
    echo "Example:"
    echo "  $0 my-project \"https://www.youtube.com/watch?v=dQw4w9WgXcQ\" --ai --mode notes"
    exit 1
}

# Check arguments
if [[ "$#" -lt 1 || "$1" == "--help" ]]; then
    usage
fi

SLUG=$1
URL=$2
AI_FLAG=""
MODE="outline"
PARALLEL=4

# Shift arguments to check for flags
shift 2 || true # In case only 1 argument was provided
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --ai) AI_FLAG="--ai" ;;
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

# Function to process a single video
process_video() {
    local VIDEO_URL=$1
    local VIDEO_SLUG=$2
    
    echo "----------------------------------------------------"
    echo "Processing video: $VIDEO_SLUG ($VIDEO_URL)"
    echo "----------------------------------------------------"
    
    # Create project directory
    mkdir -p "$VIDEO_SLUG/images"
    
    # We need absolute path for STYLES_CSS and PYTHON_SCRIPT since we'll cd
    local ABS_STYLES_CSS=$(realpath "$STYLES_CSS")
    local ABS_PYTHON_SCRIPT=$(realpath "$PYTHON_SCRIPT")

    pushd "$VIDEO_SLUG" > /dev/null

    echo "Downloading video and subtitles..."
    # We use --no-warnings to keep stdout clean
    local VIDEO_FILE=$(yt-dlp --no-warnings --write-auto-subs --write-subs --no-simulate --print filename -o "video.%(ext)s" "$VIDEO_URL" | head -n 1)

    if [[ ! -f "$VIDEO_FILE" ]]; then
        # Fallback if --print filename didn't give us the exact file
        VIDEO_FILE=$(ls video.* | head -n 1 2>/dev/null) || true
    fi

    if [[ -z "$VIDEO_FILE" || ! -f "$VIDEO_FILE" ]]; then
        echo "Error: Could not download video for $VIDEO_SLUG."
        popd > /dev/null
        return
    fi

    # Find the VTT file (prefer English)
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

    # Copy styles
    cp "$ABS_STYLES_CSS" .

    # Call Python script for parsing and HTML generation
    echo "Generating HTML and processing transcript..."
    local MODE_UPPER=$(echo "$MODE" | tr '[:lower:]' '[:upper:]')
    local OUTLINE_FILE="TUBE2TXT-${MODE_UPPER}.md"
    local TIMESTAMPS=$(python3 "$ABS_PYTHON_SCRIPT" \
        --vtt "$VTT_FILE" \
        --url "$VIDEO_URL" \
        --slug "$VIDEO_SLUG" \
        --output-html "index.html" \
        --output-outline "$OUTLINE_FILE" \
        --mode "$MODE" \
        $AI_FLAG)

    # Extract images in parallel
    echo "Extracting images in parallel ($PARALLEL processes)..."
    # Use a temporary file for timestamps to avoid command line length limits
    local TS_FILE=$(mktemp)
    echo "$TIMESTAMPS" | grep "^TIMESTAMP:" | sed 's/TIMESTAMP://' > "$TS_FILE"
    
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

    echo "Finished: $VIDEO_SLUG"
    popd > /dev/null
}

# Ensure realpath is available (common on Linux, might need brew install coreutils on Mac)
if ! command -v realpath &> /dev/null; then
    realpath() {
        [[ $1 = /* ]] && echo "$1" || echo "$PWD/${1#./}"
    }
fi

# Main logic
if [[ "$URL" == *"playlist?list="* ]] || [[ "$URL" == *"&list="* ]]; then
    echo "Playlist detected: $URL"
    PLAYLIST_NAME="$SLUG"
    mkdir -p "$PLAYLIST_NAME"
    pushd "$PLAYLIST_NAME" > /dev/null
    
    echo "Fetching video list..."
    # Get all video URLs and titles
    # Use --flat-playlist to avoid downloading metadata for all videos at once
    
    # Temporarily store playlist data
    yt-dlp --quiet --flat-playlist --print "%(id)s" --print "%(title)s" "$URL" > playlist_data.txt
    
    while IFS= read -r ID && IFS= read -r TITLE; do
        # Sanitize title for directory name
        CLEAN_TITLE=$(echo "$TITLE" | sed 's/[^a-zA-Z0-9]/_/g' | cut -c1-50)
        process_video "https://www.youtube.com/watch?v=$ID" "$CLEAN_TITLE"
    done < playlist_data.txt
    
    rm playlist_data.txt
    echo "Playlist processing complete!"
    popd > /dev/null
else
    # Single video
    # If URL is just an 11-char ID, turn it into a full URL
    if [[ ! "$URL" =~ ^http ]] && [[ ${#URL} -eq 11 ]]; then
        echo "Detected video ID: $URL. Using full YouTube URL."
        URL="https://www.youtube.com/watch?v=$URL"
    fi
    process_video "$URL" "$SLUG"
fi

echo "All tasks complete!"
