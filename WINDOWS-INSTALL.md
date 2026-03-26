# Windows Installation Guide

This guide covers running Tube2Txt on Windows. The recommended path is **WSL** or **Git Bash**. Native PowerShell is supported for dependency installation.

## Prerequisites

### 1. Python 3.9+

1. Download from [python.org](https://www.python.org/downloads/windows/).
2. During installation, check **"Add Python to PATH"**.
3. Verify:
   ```powershell
   python --version
   pip --version
   ```

### 2. FFmpeg

1. Download a release build from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) (e.g. `ffmpeg-release-essentials.7z`).
2. Extract to a permanent location (e.g. `C:\ffmpeg`).
3. Add `C:\ffmpeg\bin` to your System PATH.
4. Verify:
   ```powershell
   ffmpeg -version
   ```

### 3. yt-dlp

1. Download `yt-dlp.exe` from the [latest release](https://github.com/yt-dlp/yt-dlp/releases).
2. Place it in a folder already on your PATH (e.g. `C:\ffmpeg\bin`).
3. Verify:
   ```powershell
   yt-dlp --version
   ```

### 4. Bun (for TUI development only)

If you want to run or build the Gridland TUI:

1. Install from [bun.sh](https://bun.sh/) — run the PowerShell installer or `winget install Oven-sh.Bun`.
2. Verify:
   ```powershell
   bun --version
   ```

### 5. Git Bash or WSL (Recommended)

The CLI tools work on native Windows, but Git Bash or WSL give you a Unix shell for a smoother experience.

- **Git Bash**: Install with [Git for Windows](https://gitforwindows.org/).
- **WSL**: Run `wsl --install` in PowerShell (requires Windows 10 1903+ or Windows 11).

## Project Setup

### Option A: Git Bash / WSL

```bash
cd /c/users/yourname/projects   # Git Bash path style
git clone <your-repo-url>
cd TubedToText

# Install Python deps (use uv if available, otherwise pip)
pip install -e "."

# Copy and fill in your Gemini API key
cp .env.example .env
notepad .env
```

### Option B: PowerShell / Command Prompt

```powershell
cd C:\Users\yourname\projects
git clone <your-repo-url>
cd TubedToText

pip install -e "."

copy .env.example .env
notepad .env
```

## Running

```bash
# Process a video
tube2txt my-project "https://www.youtube.com/watch?v=..." --ai --mode notes

# Start the API server + TUI dashboard
tube2txt-hub
# Open http://localhost:8000 in your browser
```

## TUI (Optional)

```bash
cd tui
bun install
bun run dev        # development
bun run build      # production build (output: tui/dist/)
```

## Troubleshooting

| Problem | Fix |
|---|---|
| `command not found` | Restart terminal after adding items to PATH |
| `Permission denied` on script | Run Git Bash as Administrator, or `chmod +x tube2txt.sh` |
| `ModuleNotFoundError` | Run `pip install -e "."` from the project root |
| Bun not found in WSL | Install Bun inside WSL separately: `curl -fsSL https://bun.sh/install \| bash` |
