# Tube2Txt

Tube2Txt is a tool to convert YouTube videos into structured web pages with transcripts and screenshots, with an optional AI-assisted markdown outline feature powered by Gemini.

This is a rewrite of [Youtube2Webpage](https://github.com/obra/Youtube2Webpage) in Python and Bash.

## Features
- **Transcript Generation**: Downloads video and subtitles using `yt-dlp`.
- **Screenshot Extraction**: Uses `ffmpeg` to capture images at each transcript segment.
- **Webpage Creation**: Generates a clean `index.html` with transcript and images.
- **AI Outline**: Generates a high-level markdown outline (`TUBE2TXT-OUTLINE.md`) using Google's Gemini API.

## Installation Pipeline

Tube2Txt requires a few system dependencies. Here is how to install them:

**1. Install Python 3.9+**
- Mac (using Homebrew): `brew install python`

**2. Install ffmpeg**
- Mac (using Homebrew): `brew install ffmpeg`

**3. Install yt-dlp**
- Mac (using Homebrew): `brew install yt-dlp`

**4. Install Python dependencies**
```bash
pip3 install google-genai
```

**5. Clone the Repository**
```bash
git clone https://github.com/HinchK/tube2txt.git
cd tube2txt
chmod +x tube2txt.sh
```

## Obtaining the Gemini API Key

To use the `--ai` flag and automatically generate markdown outlines using Gemini, you will need an API Key from Google AI Studio.

1. Go to [Google AI Studio](https://aistudio.google.com/).
2. Sign in with your Google account.
3. On the left sidebar, click **Get API key**.
4. Click **Create API key** and select a project (or create a new one).
5. Copy the generated API key.
6. Export the key as an environment variable in your terminal:
   ```bash
   export GEMINI_API_KEY="your-api-key-here"
   ```
   *Tip: Add `export GEMINI_API_KEY="your-api-key-here"` to your `~/.zshrc` or `~/.bash_profile` so it loads on every session automatically.*

### Using a .env file (Recommended)

Alternatively, you can create a `.env` file in the project directory based on the provided template:

```bash
cp .env.example .env
# edit .env and replace 'your_gemini_api_key_here' with your real key
```

If you use a `.env` file, you should also install `python-dotenv`:
```bash
pip3 install python-dotenv --break-system-packages
```

## Usage

```bash
./tube2txt.sh project-name "https://www.youtube.com/watch?v=..." [--ai]
```

### Options
- `--ai`: Generate an AI outline. Requires the `GEMINI_API_KEY` environment variable to be set.
- `--help`: Show usage information.

### Example

```bash
export GEMINI_API_KEY="AIzaSy...xyz"
./tube2txt.sh my-video "https://www.youtube.com/watch?v=jNQXAC9IVRw" --ai
```

The output will be saved in the `my-video/` directory:
- `index.html`: The generated web page with transcript and extracted screenshots.
- `images/`: Directory containing screenshots of the video.
- `TUBE2TXT-OUTLINE.md`: The AI-generated video outline (if `--ai` was provided).
- `styles.css`: Copied stylesheet.
- `video.*`: Downloaded video and subtitle files.
