# Windows Installation Guide for Tube2Txt

This guide outlines how to set up and run Tube2Txt on a Microsoft Windows environment.

## Prerequisites

To run this tool on Windows, you will need the following components installed and added to your system's PATH.

### 1. Install Python 3
1. Download the latest Python installer from [python.org](https://www.python.org/downloads/windows/).
2. **CRITICAL:** During installation, ensure you check the box that says **"Add Python to PATH"**.
3. After installation, open PowerShell and verify:
   ```powershell
   python --version
   pip --version
   ```

### 2. Install FFmpeg
1. Download a "release build" from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) (e.g., `ffmpeg-release-essentials.7z`).
2. Extract the folder to a permanent location (e.g., `C:\ffmpeg`).
3. Add the `bin` folder (e.g., `C:\ffmpeg\bin`) to your System Environment Variables (PATH).
4. Verify in PowerShell:
   ```powershell
   ffmpeg -version
   ```

### 3. Install yt-dlp
1. Download `yt-dlp.exe` from the [latest release](https://github.com/yt-dlp/yt-dlp/releases).
2. Move it to a folder in your PATH (or the same folder as FFmpeg).
3. Verify in PowerShell:
   ```powershell
   yt-dlp --version
   ```

### 4. Install Git Bash (Recommended)
Since `tube2txt.sh` is a shell script, the easiest way to run it on Windows is using **Git Bash**, which comes with [Git for Windows](https://gitforwindows.org/).

Alternatively, you can use **WSL (Windows Subsystem for Linux)**.

## Project Setup

1. Open Git Bash and navigate to where you want the project:
   ```bash
   cd /c/users/yourname/projects
   git clone <your-repo-url>
   cd TubedToText
   ```
2. Install Python dependencies:
   ```bash
   pip install google-genai python-dotenv
   ```
3. (Optional) Set up your API key:
   ```bash
   cp .env.example .env
   # Edit .env with Notepad and add your key
   ```

## Running the tool

In Git Bash:
```bash
./tube2txt.sh my-project "video-id-or-url" --ai --mode notes --parallel 4
```

---

## Troubleshooting
- **Command Not Found**: Ensure you restarted your terminal after adding items to the PATH.
- **Permission Denied**: Try running Git Bash as an Administrator or ensure the script is executable: `chmod +x tube2txt.sh`.
