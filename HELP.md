# MyTubeScripts Forge - CLI Help Guide

Welcome to the **Tube2Txt** command-line tool. This tool acts as the "Forge" for your personal video archive, allowing you to process YouTube videos locally and sync them to a remote gallery.

---

## 🚀 Quick Start

If you run `tube2txt` without any arguments, it will enter **Interactive Mode** and walk you through the process:

```bash
uv run tube2txt
```

---

## 🛠 Command Reference

### 1. Process a Video (`url` or `process`)
Decodes a YouTube video, extracts transcripts, and generates AI analysis.

**Usage:**
```bash
uv run tube2txt <URL> [SLUG]
# OR
uv run tube2txt url <URL> [SLUG]
```

**Options:**
- `--ai`: Force-run AI generation (automatic if `GEMINI_API_KEY` is set).
- `--mode [outline|notes|technical|recipe]`: Choose the deep-dive analysis type.
- `--parallel N`: Use N threads for image extraction (default: 4).

> [!TIP]
> Always quote your YouTube URLs to avoid shell issues: `uv run tube2txt "https://..."`

### 2. List Archives (`list`)
Shows all locally processed videos and their sync status.

```bash
uv run tube2txt list
```

### 3. Sync to Remote (`sync`)
Pushes local metadata and transcripts to your Supabase-backed remote gallery.

```bash
uv run tube2txt sync <SLUG>
```

### 4. Remote Management (`setup`, `remote`, `share`)
- `setup`: Configure your Supabase/Remote environment.
- `remote`: Check the status and URL of your live gallery.
- `share <SLUG>`: Generate a direct link to a video on your remote site.

### 5. Maintenance (`archive`, `delete`)
- `archive <SLUG>`: Marks a project as archived in the DB.
- `delete <SLUG>`: Permanently removes the project folder and DB entry.

---

## 💾 Database Setup

Before you can sync, you must set up your Supabase database:
1. Open your Supabase Project Dashboard.
2. Go to the **SQL Editor**.
3. Copy and run the contents of [supabase_schema.sql](file:///Users/hinchk/jkh/TUBE2TXT/tube2txt-repo/supabase_schema.sql).
4. This will create the `videos` and `metadata` tables and set up public read access.

---

## 🔐 Authentication

Tube2Txt uses two levels of security:

### 1. Forge Sync (CLI)
When you run `tube2txt setup`, you are asked for a **Service Role Key**. This allows your local CLI to push data directly to your Supabase tables while bypassing Row Level Security (RLS). **Keep this key private.**

### 2. Web Gallery (Frontend)
When you access the remote site, you must sign in with a standard user account.
- **First Time**: Use the **"Create Account"** button on the login page.
- **Tip**: In your Supabase Dashboard under `Auth > Providers`, disable "Confirm Email" if you want to log in immediately without checking your inbox.

---

## 🔧 Troubleshooting

- **"zsh: no matches found"**: This happens when a URL contains special characters like `?`. **Always put URLs in quotes**.
- **Supabase Sync fails**: Run `tube2txt setup` to ensure your credentials are correct in `remote/.env.local`.
- **Images missing**: Ensure `ffmpeg` is installed on your system.

---

## 🌐 Architecture Note
**No video files are ever uploaded to the server.** The Forge (your local machine) handles the heavy lifting. The Remote Gallery only stores metadata, transcripts, and sparse image links to ensure privacy and low hosting costs.
