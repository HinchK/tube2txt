# Tube2Txt v2

Tube2Txt converts YouTube videos and playlists into structured web pages with transcripts and screenshots, with AI-assisted analysis powered by Gemini.

This is a high-performance rewrite of [Youtube2Webpage](https://github.com/obra/Youtube2Webpage) using Python and Bash.

## New in v2.0
- **Parallel Processing**: Screenshot extraction is now up to 4x faster using parallel `ffmpeg` processes.
- **Playlist Support**: Pass a playlist URL to process all videos in the series automatically.
- **AI Modes**: Specialized prompts for `outline` (default), `notes`, `recipe`, and `technical`.
- **Interactive Mode**: Prompts for missing information if not provided via CLI.
- **Docker Support**: Run with zero local dependencies (except Docker).
- **PyPI Ready**: Installable via `pip`.

## Installation

### Method 1: Local (macOS/Linux)
1. **Install System Dependencies**:
   - `yt-dlp`
   - `ffmpeg`
   - `python3`
   - `pip3 install google-genai python-dotenv --break-system-packages`

2. **Make Executable**:
   ```bash
   chmod +x tube2txt.sh
   ```

### Method 2: Docker (Easiest)
Ensure you have Docker and Docker Compose installed.
```bash
export GEMINI_API_KEY="your-key"
docker-compose run tube2txt project-name "url" --ai
```

### Method 3: Windows
Please see the **[WINDOWS-INSTALL.md](WINDOWS-INSTALL.md)** guide.

## Usage

```bash
./tube2txt.sh project-name "https://www.youtube.com/watch?v=..." [options]
```

### Options
- `--ai`: Generate AI content using Gemini (requires `GEMINI_API_KEY`).
- `--mode <mode>`: AI mode: `outline` (default), `notes`, `recipe`, `technical`.
- `--parallel <N>`: Number of parallel `ffmpeg` processes (default: 4).
- `--help`: Show usage information.

### Environment Variables
- `GEMINI_API_KEY`: Your Google Gemini API key.
  - Set in shell: `export GEMINI_API_KEY=...`
  - Or use a `.env` file (see `.env.example`).

## Features
- **Transcript Generation**: Downloads video and subtitles using `yt-dlp`.
- **Screenshot Extraction**: Uses `ffmpeg` to capture images at each segment.
- **Webpage Creation**: Generates a clean `index.html` with transcript and images.
- **AI Content**: Generates specialized markdown files using Gemini.

## Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License
MIT License. See [LICENSE](LICENSE) for details.
