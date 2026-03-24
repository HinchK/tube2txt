# Youtube2Webpage Rewrite: Tube2Txt

## Objective
Rewrite the [Youtube2Webpage](https://github.com/obra/Youtube2Webpage) tool (originally in Perl/Electron) into a hybrid Python and Bash tool with an added AI-assisted feature to generate a markdown outline using Gemini.

## Background & Motivation
The original tool converts YouTube videos into web pages with transcripts and screenshots. The user wants a modern, easily maintainable rewrite in Python/Bash with AI-powered content summarization (outline).

## Scope & Impact
- **In-Scope**:
    - Hybrid tool (Bash for orchestration, Python for logic/AI).
    - Downloads YouTube video and subtitles using `yt-dlp`.
    - Parses VTT subtitles.
    - Extracts screenshots at transcript timestamps using `ffmpeg`.
    - Generates an `index.html` with transcript and images.
    - Generates `TUBE2TXT-OUTLINE.md` using Google's Gemini API.
- **Out-of-Scope**:
    - Electron GUI (this is a CLI-first tool).
    - Support for providers other than YouTube (at least for the initial version).

## Proposed Solution

### 1. Bash Orchestrator (`tube2txt.sh`)
- Handles CLI arguments (`slug` and `URL`).
- Manages directory creation and file organization.
- Invokes `yt-dlp` for downloads.
- Calls `ffmpeg` for batch image extraction (or delegates to Python).
- Orchestrates calls to the Python script for parsing, HTML generation, and AI.

### 2. Python Logic (`tube2txt.py`)
- **VTT Parsing**: A robust parser for `.vtt` files that handles timestamps and captions.
- **HTML Generation**: Creates `index.html` using a template or simple string formatting.
- **Gemini Integration**: Uses the `google-generativeai` library to send the full transcript to Gemini and receive a structured markdown outline.
- **API Key Management**: Reads `GEMINI_API_KEY` from an environment variable or `.env` file.

### 3. File Structure
The output for a project named `my-video` will look like:
```
my-video/
├── images/
│   ├── 00-00-01-123.jpg
│   └── ...
├── video.webm
├── video.en.vtt
├── index.html
├── styles.css
└── TUBE2TXT-OUTLINE.md
```

## Alternatives Considered
- **Pure Python**: Easier to distribute but might be slower for orchestration tasks that Bash excels at (like calling multiple CLI tools).
- **Pure Bash**: Parsing VTT files and interacting with Gemini API in Bash is complex and error-prone.
- **Other AI Providers**: The user specifically requested Gemini.

## Implementation Plan

### Phase 1: Core Logic (Python)
- Implement `VTTParser` class.
- Implement `HTMLGenerator` class.
- Implement `GeminiClient` for outline generation.

### Phase 2: Orchestration (Bash)
- Implement `tube2txt.sh` to handle inputs and call `yt-dlp`.
- Integrate Python scripts into the flow.
- Add image extraction logic (using `ffmpeg`).

### Phase 3: AI Integration
- Set up Gemini API call with a prompt designed to generate a clear, high-level outline from the transcript.

### Phase 4: Styling & Cleanup
- Ensure `styles.css` is correctly applied.
- Add help/usage documentation.

## Verification
- Test with a short YouTube video (e.g., a 1-minute clip).
- Verify `index.html` renders correctly with images.
- Verify `TUBE2TXT-OUTLINE.md` contains a coherent outline.
- Check for error handling (missing API keys, invalid URLs, etc.).

## Migration & Rollback
- Since this is a rewrite in a new directory, no migration of existing data is needed.
- Rollback involves deleting the generated project folders.
