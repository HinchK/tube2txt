# Tube2Txt Forge v3.2

> **Inspiration:** This project is a modern rewrite of the original [Youtube2Webpage](https://github.com/obra/Youtube2Webpage) script.

Tube2Txt is a "Local-First" video intelligence forge. It processes YouTube videos into structured Markdown archives locally on your machine and pushes them to your remote Supabase gallery.

## Features

- **Standardized CLI**: Git-style verbs (`add`, `ls`, `push`, `config`, `rm`, `share`) for an intuitive developer experience.
- **Progressive Disclosure**: Interactive prompts guide you through missing arguments, including a full **Interactive Forge** mode.
- **Gridland Web Hub**: Polished terminal-aesthetic UI to process videos and browse your library locally.
- **Supabase Remote Gallery**: Sync your local forge to a hosted web gallery with authentication and shared browsing.
- **AI Analysis**: Gemini-powered summaries (outline, notes, recipe, technical, clips).
- **Smart Clips**: AI-driven or manual extraction of highlights.

## Installation & Setup

Tube2Txt requires **Python 3.9+**, **Node/Bun**, and **ffmpeg**.

1.  **Clone and Setup**:
    ```bash
    git clone https://github.com/youruser/tube2txt.git
    cd tube2txt
    ./scripts/setup.sh
    ```

2.  **Configuration**:
    Run the interactive setup to configure your Supabase remote and Gemini API key:
    ```bash
    uv run tube2txt config
    ```

## Usage

### 1. Process Video (`add`)
Adds a YouTube video to your local forge.
```bash
# Basic process
uv run tube2txt add "https://www.youtube.com/watch?v=..." --ai

# Legacy shortcut still works
uv run tube2txt "URL"
```

### 2. List Archives (`ls`)
Lists all locally processed videos and their sync status.
```bash
uv run tube2txt ls
```

### 3. Push to Remote (`push`)
Uploads local metadata and transcripts to your remote Supabase gallery.
```bash
uv run tube2txt push [SLUG]
```

### 4. Management (`rm`, `archive`, `share`)
- `rm [SLUG]`: Permanently removes a local project.
- `archive [SLUG]`: Marks a project as archived locally.
- `share [SLUG]`: Displays the remote URL for a synced video.

### 5. Launch the Hub (Local Web Dashboard)
```bash
uv run tube2txt-hub
```
*Access at http://0.0.0.0:8000.*

## Maintenance Scripts

-   `./scripts/setup.sh`: Full environment initialization.
-   `./scripts/build.sh`: Rebuild TUI and reinstall Python package.
-   `./scripts/test.sh`: Run the full test suite.
-   `./scripts/purge-projects.sh`: Clear all generated video data.

## Architecture

- **`src/tube2txt/`**: Python backend (FastAPI, yt-dlp, ffmpeg, Gemini, Supabase).
- **`tui/`**: React/TypeScript local dashboard built with Tailwind.
- **`remote/`**: Next.js/Supabase web gallery for cloud hosting.
- **`projects/`**: Generated local output (HTML, transcripts, images).
- **`tube2txt.db`**: Central SQLite intelligence database.

## License

MIT
