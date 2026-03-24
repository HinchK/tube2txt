#!/bin/bash

# tube2txt.sh - Hybrid Bash/Python Youtube to Webpage converter with AI Outline

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
    echo "  --ai       Generate a markdown outline using Gemini (requires GEMINI_API_KEY)"
    echo "  --help     Show this help message"
    echo ""
    echo "Example:"
    echo "  $0 my-project \"https://www.youtube.com/watch?v=dQw4w9WgXcQ\" --ai"
    exit 1
}

# Check arguments
if [[ "$#" -lt 1 || "$1" == "--help" ]]; then
    usage
fi

SLUG=$1
URL=$2
AI_FLAG=""

# Shift arguments to check for flags
shift 2 || true # In case only 1 argument was provided
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --ai) AI_FLAG="--ai" ;;
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

# Create project directory
mkdir -p "$SLUG/images"
cd "$SLUG"

echo "Downloading video and subtitles for: $SLUG"
# Download video and subtitles
# --write-auto-subs --write-subs handles both manual and auto captions
# --print filename helps us know what we got
# We use --no-warnings to keep stdout clean
VIDEO_FILE=$(yt-dlp --no-warnings --write-auto-subs --write-subs --no-simulate --print filename -o "video.%(ext)s" "$URL" | head -n 1)

if [[ ! -f "$VIDEO_FILE" ]]; then
    # Fallback if --print filename didn't give us the exact file
    VIDEO_FILE=$(ls video.* | head -n 1)
fi

# Find the VTT file (prefer English)
VTT_FILE=$(ls video.en.vtt 2>/dev/null | head -n 1)
if [[ -z "$VTT_FILE" ]]; then
    VTT_FILE=$(ls video.*.vtt 2>/dev/null | head -n 1)
fi
if [[ -z "$VTT_FILE" ]]; then
    VTT_FILE=$(ls *.vtt 2>/dev/null | head -n 1)
fi

if [[ -z "$VTT_FILE" ]]; then
    echo "Error: Could not find VTT subtitle file."
    exit 1
fi

echo "Using video: $VIDEO_FILE"
echo "Using subtitles: $VTT_FILE"

# Copy styles
cp "$STYLES_CSS" .

# Call Python script for parsing and HTML generation
echo "Generating HTML and processing transcript..."
TIMESTAMPS=$(python3 "$PYTHON_SCRIPT" \
    --vtt "$VTT_FILE" \
    --url "$URL" \
    --slug "$SLUG" \
    --output-html "index.html" \
    --output-outline "TUBE2TXT-OUTLINE.md" \
    $AI_FLAG)

# Extract images
echo "Extracting images (this may take a while)..."
while IFS= read -r line; do
    if [[ $line == TIMESTAMP:* ]]; then
        TS=${line#TIMESTAMP:}
        TS_FILENAME=${TS//:/-}
        TS_FILENAME=${TS_FILENAME//./-}
        
        # Only extract if it doesn't exist
        if [[ ! -f "images/$TS_FILENAME.jpg" ]]; then
            ffmpeg -ss "$TS" -nostdin -i "$VIDEO_FILE" -frames:v 1 -q:v 2 -vf scale=1024:-1 "images/$TS_FILENAME.jpg" -loglevel error
        fi
    fi
done <<< "$TIMESTAMPS"

echo "Done! Project created in directory: $SLUG"
echo "Open $SLUG/index.html to view the transcript."
if [[ "$AI_FLAG" == "--ai" ]]; then
    echo "AI Outline generated in $SLUG/TUBE2TXT-OUTLINE.md"
fi
