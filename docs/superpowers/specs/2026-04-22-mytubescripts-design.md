# MyTubeScripts: Local Forge & Remote Gallery Architecture

## 1. Context and Goals

The current Tube2Txt application acts as an integrated system: downloading, processing, and hosting an interactive TUI from a single machine. While effective, hosting video processing tools and the resulting media files online can lead to copyright or security issues.

The goal of this architectural pivot is to cleanly separate the "heavy processing" from the "sharing and viewing" experience. 

We will create **MyTubeScripts**:
*   **The Local Forge (Tube2Txt):** A robust local CLI application that does the heavy lifting (yt-dlp, ffmpeg, Gemini API) on the user's machine.
*   **The Remote Gallery (MyTubeScripts):** A lightweight, serverless web application (hosted on Vercel) that displays the processed transcripts, AI analysis, and screenshots for public sharing and browsing.
*   **The Cloud Bridge (Supabase):** The synchronization layer connecting the two.

## 2. Architecture & Data Flow

The system relies on a unidirectional data push from local to remote:

1.  **Local Processing:** `tube2txt process <url>` runs locally, utilizing ffmpeg and yt-dlp, storing results in local SQLite (`tube2txt.db`) and the `projects/` directory.
2.  **Cloud Sync:** The user triggers a sync (e.g., `tube2txt sync <slug>`). The Python backend pushes the metadata, text segments, and AI markdown to Supabase PostgreSQL, and uploads screenshots to a Supabase Storage bucket.
3.  **Remote Viewing:** The Vercel-hosted React app fetches data from Supabase using read-only API keys to render the public gallery and provide global search functionality.

## 3. Component 1: CLI Refactor & Local Management

The local CLI will be upgraded to a modern sub-command structure to improve library management.

### Supported Commands
*   `tube2txt process [url]` (or just `tube2txt [url]`): Core processing engine.
*   `tube2txt list`: View local video library.
*   `tube2txt remote`: List videos that have been synced to the remote gallery.
*   `tube2txt sync [slug]`: Push local project data to Supabase. (Syncs all pending if no slug provided).
*   `tube2txt share [slug]`: Generates and copies the public MyTubeScripts URL for a synced video.
*   `tube2txt delete [slug]`: Remove local project (with prompt to optionally remove remote data).
*   `tube2txt archive [slug]`: Compress project to `.zip` and drop raw video to save space.
*   `tube2txt setup`: Interactive CLI wizard to configure `.env` (API keys for Gemini, Supabase URL, and Supabase Service Key).
*   `tube2txt help`: Detailed CLI documentation.

### State Tracking
The local `tube2txt.db` `videos` table will be updated to include sync tracking:
*   `remote_url`: (TEXT) URL on the public gallery.
*   `is_archived`: (BOOLEAN) Local archive status.
*   `last_synced_at`: (TIMESTAMP) Tracks when the project was last pushed.

## 4. Component 2: Supabase Cloud Layer

Supabase will act as the serverless backend.

*   **Database (PostgreSQL):**
    *   `videos` table: Metadata (slug, title, url, processed_at).
    *   `segments` table: Transcript lines with timestamps (includes FTS index for global search).
    *   `ai_content` table: Stores the generated markdown (e.g., outline, recipe, notes).
*   **Storage:** A public bucket named `projects` to host screenshot files.
*   **Security:** 
    *   The Local Forge uses the `SERVICE_ROLE_KEY` to insert/update records.
    *   The Remote Gallery uses the `ANON_KEY` (with Row Level Security enabling public read access) to query data securely without exposing write privileges.

## 5. Component 3: MyTubeScripts Remote Gallery

A new directory (`remote/`) will be added to the repository containing the source code for the public-facing gallery.

*   **Tech Stack:** Next.js (or Vite/React), configured for zero-config Vercel deployment.
*   **Design:** Reuses the established "Gridland" aesthetic and React components from the current TUI for a consistent brand experience.
*   **Key Views:**
    *   **Library Dashboard:** Browse all synced scripts with thumbnail cards.
    *   **Video Detail:** View transcript, AI analysis, and scrub through screenshots.
    *   **Global Search:** Full-text search querying the Supabase database.
*   **Deployment:** The user simply connects the `remote/` folder to Vercel and supplies the Supabase URL and Anon Key. No backend maintenance required.
