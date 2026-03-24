# Tube2Txt v3

Tube2Txt is a central intelligence platform that converts YouTube videos and playlists into structured web pages with transcripts, screenshots, and AI-assisted analysis.

## New in v3.0
- **Tube2Txt Hub**: A local web dashboard to browse your video library.
- **Global Search**: Search for any word or phrase across **all** your processed videos.
- **Smart Clips**: 
  - **Manual Clips**: Extract specific video segments with a simple command.
  - **AI-Driven Clips**: Gemini identifies the most interesting moments and extracts them automatically.
- **SQLite Database**: Centralized storage for metadata and searchable transcripts.

## Installation

### Method 1: Local (macOS/Linux)
1. **Install System Dependencies**:
   - `yt-dlp`, `ffmpeg`, `python3`
   - `pip3 install google-genai python-dotenv fastapi uvicorn --break-system-packages`

2. **Make Executable**:
   ```bash
   chmod +x tube2txt.sh
   ```

### Method 2: Docker
```bash
docker-compose up --build
# Then in another terminal:
docker-compose run tube2txt <project-name> <url> --ai
```

## Usage

### 1. Process a Video
```bash
./tube2txt.sh my-project "https://www.youtube.com/watch?v=..." --ai
```

### 2. Launch the Hub
```bash
./tube2txt.sh hub
# Open http://localhost:8000 in your browser
```

### 3. Smart Clips
- **AI Clipping**:
  ```bash
  ./tube2txt.sh my-project "url" --ai --mode clips
  ```
- **Manual Clipping**:
  ```bash
  ./tube2txt.sh clip my-project 00:01:00-00:02:30
  ```

### Options
- `--ai`: Generate AI content.
- `--mode <mode>`: AI mode: `outline` (default), `notes`, `recipe`, `technical`, `clips`.
- `--parallel <N>`: Number of parallel `ffmpeg` processes (default: 4).

## Features
- **Parallel Processing**: Screenshot extraction is up to 10x faster.
- **Playlist Support**: Pass a playlist URL to process everything at once.
- **Windows Support**: See [WINDOWS-INSTALL.md](WINDOWS-INSTALL.md).
