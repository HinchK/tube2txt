# Design Spec: Transcript-First Integration

## 1. Overview
Pivot Tube2Txt to a "transcript-first" architecture using `youtube-transcript-api`. This ensures that even if `yt-dlp` fails due to authentication or bot detection, the core intelligence (AI analysis, searchable index, TUI dashboard) remains functional.

## 2. Architecture
The system will prioritize transcript extraction as a standalone, resilient operation. Video download and image extraction will be treated as optional, non-blocking enhancements.

### Components
- **`TranscriptExtractor`**: A new utility (or logic within `process_video`) that uses `youtube-transcript-api` to fetch captions by Video ID.
- **`VTTParser` (Legacy)**: Maintained for local VTT files but bypassed when using the API.
- **`process_video`**: Refactored to handle "partial success" (Transcript YES, Video NO).
- **`HTMLGenerator` & TUI Components**: Updated to handle missing segment images gracefully.

## 3. Data Flow
1. **Extraction**: Resolve YouTube URL to Video ID. Attempt `youtube-transcript-api`.
2. **Fallback/Optional**: Attempt `yt-dlp` for the video file (`video.*`). 
    - If successful: Proceed to `extract_images`.
    - If failed: Log the warning but do not halt the pipeline.
3. **AI Generation**: Use the fetched transcript for all Gemini operations (Outline, Notes, etc.).
4. **Storage**: Index the segments in SQLite. If images are missing, `thumbnail_path` will be `null` or point to a placeholder.
5. **Rendering**:
    - HTML: Show a placeholder image or a generic YouTube thumbnail.
    - TUI: Display a "No Preview" icon or label for segments without extracted frames.

## 4. Error Handling
- **`youtube-transcript-api` Failures**: If both the API and `yt-dlp` fail to get transcripts, then the process fails.
- **Video Download Failures**: Explicitly caught and treated as a "warning" state rather than a "failure" state.
- **Dependency Management**: Add `youtube-transcript-api` to `pyproject.toml`.

## 5. Testing Strategy
- **Mocking**: Mock `youtube-transcript-api` responses for unit tests.
- **Regression**: Ensure existing CLI commands (manual VTT, manual clipping) still work.
- **Integration**: Verify the "Partial Success" state in the TUI (Dashboard showing a video with no images).
- **Bot Detection Simulation**: Test with a URL known to trigger bot detection to confirm transcript-only recovery.

## 6. UI/UX Considerations (TUI)
- The "Processing" screen should clearly distinguish between "Transcript Fetched" and "Video Downloaded".
- The Video Detail screen should not crash or show "broken image" icons when screenshots are missing.
