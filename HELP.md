# Tube2Txt Forge - CLI Help Guide

Tube2Txt is a "Local-First" video intelligence forge. It processes YouTube videos into structured Markdown archives locally on your machine and pushes them to your remote Supabase gallery.

---

## 🛠 Command Standard (Git-Style)

Tube2Txt uses industry-standard verbs. If you omit a required argument (like a URL or a Project Slug), the tool will guide you through an interactive selection or prompt.

### 1. Process Video (`add`)
Adds a YouTube video to your local forge.
```bash
uv run tube2txt add "https://www.youtube.com/watch?v=..."
```
- **Progressive Disclosure**: Running `tube2txt add` without a URL will launch the **Interactive Forge**.
- **Legacy Support**: `uv run tube2txt "URL"` still works as a shortcut.

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
- **Progressive Disclosure**: If `SLUG` is omitted, you will be presented with a numbered list of unsynced local projects to choose from.

### 4. Configuration (`config`)
Sets up your Supabase Project URL, API Keys, and Gemini credentials.
```bash
uv run tube2txt config
```

### 5. Management (`rm`, `archive`, `share`)
- `rm [SLUG]`: Permanently removes a local project and its directory.
- `archive [SLUG]`: Marks a project as archived in the local database.
- `share [SLUG]`: Displays the remote URL for a synced video.

---

## 🔐 Authentication

Tube2Txt uses two levels of security:

### 1. Forge Sync (CLI)
When you run `tube2txt config`, you are asked for a **Service Role Key**. This allows your local CLI to push data directly to your Supabase tables while bypassing Row Level Security (RLS). **Keep this key private.**

### 2. Web Gallery (Frontend)
When you access the remote site, you must sign in with a standard user account.
- **First Time**: Use the **"Create Account"** button on the login page.
- **Tip**: In your Supabase Dashboard under `Auth > Providers`, disable "Confirm Email" if you want to log in immediately without checking your inbox.

---

## 🔧 Troubleshooting

- **"zsh: no matches found"**: This happens when a URL contains special characters like `?`. **Always put URLs in quotes**.
- **Database Error**: If you see "Slug not found," ensure you are running the command in the same directory where your `tube2txt.db` is located.
- **Missing AI Analysis**: Ensure `GEMINI_API_KEY` is set in your environment or configured via `tube2txt config`.
