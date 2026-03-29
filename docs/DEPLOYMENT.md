# Deployment Guide for Tube2Txt

Tube2Txt is a "local-first" application that relies on `ffmpeg`, `yt-dlp`, and a persistent SQLite database. This guide covers how to deploy it across different platforms.

## Summary Table

| Platform | Difficulty | Recommended? | Notes |
| :--- | :--- | :--- | :--- |
| **Railway** | Easy | **Yes** | Best for quick, managed full-stack deployment. |
| **VPS** | Medium | **Yes** | Best for long-term self-hosting and full control. |
| **Vercel / Netlify** | Hard | No | Not suited for background processing or local DBs. |

---

## 1. Railway (Recommended)

Railway is the easiest way to get Tube2Txt online. It uses the existing `Dockerfile`.

1.  **Connect Repo**: Point Railway to your GitHub repository.
2.  **Variables**: Add `GEMINI_API_KEY` to your project variables.
3.  **Persistence (CRITICAL)**: By default, Railway disks are ephemeral. To keep your videos:
    -   Go to **Settings** -> **Volumes**.
    -   Create a Volume and mount it to `/app/projects`.
    -   Tube2Txt will now save all HTML and images to this persistent disk.
4.  **Networking**: Railway will automatically detect the `PORT` variable and map it to your public URL.

## 2. VPS (DigitalOcean, Linode, Hetzner)

A VPS is ideal for Tube2Txt because video processing can be CPU intensive.

### Option A: Docker (Easiest)
1.  Install Docker and Docker Compose on your VPS.
2.  Clone the repo and create your `.env` file.
3.  Run: `docker compose up -d`
4.  The Hub will be available at `http://<vps-ip>:8000`.

### Option B: Bare Metal (Systemd)
1.  Install system dependencies: `sudo apt install ffmpeg python3-pip bun`.
2.  Run `./scripts/setup.sh`.
3.  Create a systemd service to keep the hub running:
    ```ini
    [Unit]
    Description=Tube2Txt Hub
    After=network.target

    [Service]
    User=youruser
    WorkingDirectory=/path/to/tube2txt
    ExecStart=/path/to/tube2txt/.venv/bin/python -m tube2txt.hub
    Restart=always
    Environment=GEMINI_API_KEY=your_key_here

    [Install]
    WantedBy=multi-user.target
    ```

## 3. Vercel / Netlify (Frontend Only)

These platforms are designed for **static content** and **short-lived functions**. They cannot run Tube2Txt's backend because:
-   No system-level `ffmpeg` access.
-   No persistent file system for SQLite or images.
-   Serverless functions timeout before a video can finish downloading.

**If you must use them:**
-   Build the TUI separately: `cd tui && bun run build-web`.
-   Deploy the `tui/dist` folder as a static site.
-   **Note**: You will still need a separate VPS or Railway instance to host the API and update the TUI configuration to point to that API's URL.

## Security Warning

The Tube2Txt Hub currently **has no authentication**. If you deploy it to a public URL (especially on a VPS), anyone who finds the link can process videos and browse your library. 

**Recommendation:** If deploying publicly, use a tool like **Cloudflare Zero Trust** or an **Nginx Auth Proxy** to put a login in front of the site.
