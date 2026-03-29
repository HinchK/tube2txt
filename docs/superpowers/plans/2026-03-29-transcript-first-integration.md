# Transcript-First Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Pivot Tube2Txt to a "transcript-first" architecture using `youtube-transcript-api` to bypass `yt-dlp` bot detection.

**Architecture:** Prioritize transcript extraction via API. Treat video download and image extraction as optional enhancements. Standardize the segment data structure to be source-agnostic.

**Tech Stack:** Python, `youtube-transcript-api`, `yt-dlp`, FastAPI, React.

---

### Task 1: Update Dependencies

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add `youtube-transcript-api` to dependencies**

```toml
# pyproject.toml
dependencies = [
    "google-genai",
    "python-dotenv",
    "fastapi",
    "uvicorn",
    "yt-dlp",
    "websockets",
    "youtube-transcript-api",
]
```

- [ ] **Step 2: Run dependency sync**

Run: `uv sync` (or `pip install youtube-transcript-api`)

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml
git commit -m "chore: add youtube-transcript-api dependency"
```

---

### Task 2: Implement Transcript Extraction Logic

**Files:**
- Modify: `src/tube2txt/__init__.py`
- Test: `tests/test_transcript.py` (New)

- [ ] **Step 1: Add Video ID extraction and Transcript Fetching**

Add these to `src/tube2txt/__init__.py`:

```python
def get_video_id(url):
    """Extract video ID from various YouTube URL formats."""
    regex = r'(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})'
    match = re.search(regex, url)
    return match.group(1) if match else None

def fetch_transcript_api(video_id, languages=['en', 'de']):
    """Fetch transcript using youtube-transcript-api."""
    from youtube_transcript_api import YouTubeTranscriptApi
    try:
        return YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
    except Exception as e:
        print(f"Transcript API error: {e}")
        return None

def format_vtt_timestamp(seconds):
    """Convert seconds to HH:MM:SS.mmm format."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02}:{m:02}:{s:06.3f}"
```

- [ ] **Step 2: Add unit tests for extraction**

```python
# tests/test_transcript.py
from tube2txt import get_video_id, format_vtt_timestamp

def test_get_video_id():
    assert get_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert get_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"

def test_format_vtt_timestamp():
    assert format_vtt_timestamp(3661.5) == "01:01:01.500"
```

- [ ] **Step 3: Commit**

```bash
git add src/tube2txt/__init__.py tests/test_transcript.py
git commit -m "feat: implement transcript api extraction and timestamp formatting"
```

---

### Task 3: Refactor `process_video` Pipeline

**Files:**
- Modify: `src/tube2txt/__init__.py`

- [ ] **Step 1: Update `process_video` to prioritize API transcript**

```python
def process_video(url, slug, ...):
    # ... setup ...
    
    # 1. Extract Video ID and Fetch Transcript
    video_id = get_video_id(url)
    transcript_data = fetch_transcript_api(video_id) if video_id else None
    
    segments = []
    if transcript_data:
        _notify(on_progress, "status", "parse", "Using transcript from API...")
        for entry in transcript_data:
            segments.append({
                'start': format_vtt_timestamp(entry['start']),
                'text': entry['text'],
                'seconds': int(entry['start'])
            })
    
    # 2. Download (Optional Video)
    _notify(on_progress, "status", "download", "Attempting video download (optional)...")
    video_file, vtt_file = download_video(url, project_path, on_progress=on_progress)
    
    # Fallback to VTT if API failed
    if not segments and vtt_file:
        _notify(on_progress, "status", "parse", "Parsing VTT fallback...")
        parser = VTTParser(vtt_file)
        segments = parser.parse()
        
    if not segments:
        _notify(on_progress, "error", "transcript", "Failed to retrieve transcript from any source.")
        return None

    # ... Indexing, AI generation ...

    # 6. Extract images (ONLY if video_file exists)
    if video_file and os.path.exists(video_file):
        _notify(on_progress, "status", "images", "Extracting images...")
        extract_images(video_file, segments, os.path.join(project_path, "images"), parallel=parallel)
    else:
        _notify(on_progress, "status", "images", "Skipping images (video download failed or skipped)")
```

- [ ] **Step 2: Commit**

```bash
git add src/tube2txt/__init__.py
git commit -m "refactor: update process_video pipeline to be transcript-first"
```

---

### Task 4: UI Resilience for Missing Images

**Files:**
- Modify: `src/tube2txt/__init__.py` (HTMLGenerator)
- Modify: `tui/src/components/VideoCard.tsx`
- Modify: `tui/src/screens/VideoDetailScreen.tsx`

- [ ] **Step 1: Update `HTMLGenerator` image fallback**

```python
# In HTMLGenerator.generate
html_content += f"""<li>
    <div class="grab">
        <img src="images/{ts_filename}.jpg" onerror="this.style.display='none'; this.parentElement.innerHTML='<div class=\'no-img\'>No Preview</div>';" />
    </div>
    ...
"""
```

- [ ] **Step 2: Add TUI placeholder logic**

In `tui/src/components/VideoCard.tsx`, check if the thumbnail path exists/is valid. If not, show a stylized placeholder.

- [ ] **Step 3: Commit**

```bash
git add src/tube2txt/__init__.py tui/src/
git commit -m "feat: add image placeholders for missing video frames"
```

---

### Task 5: Final Validation

- [ ] **Step 1: Test with a video that requires login**
- [ ] **Step 2: Verify AI output generates from API transcript**
- [ ] **Step 3: Verify Hub/TUI reflects "No Preview" status correctly**
