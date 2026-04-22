import os
import json
import sqlite3
from datetime import datetime

try:
    import requests
except ImportError:
    requests = None

CLI_COLOR_CYAN = "\033[96m"
CLI_COLOR_RESET = "\033[0m"

def config():
    """Interactive prompt to set up remote deployment configuration."""
    if not requests:
        print(f"{CLI_COLOR_CYAN}Error: The 'requests' module is required for remote features.{CLI_COLOR_RESET}")
        print("Run: pip install requests")
        return

    print(f"{CLI_COLOR_CYAN}--- Tube2Txt Remote Setup ---{CLI_COLOR_RESET}")
    print("This connects your local Forge to your Supabase backend.\n")
    
    env_path = os.path.join("remote", ".env.local")
    
    url = input("1. Supabase Project URL: ").strip()
    anon_key = input("2. Supabase Anon Key (for the web gallery): ").strip()
    service_key = input("3. Supabase Service Role Key (for the CLI to push data): ").strip()
    
    if url and anon_key and service_key:
        os.makedirs("remote", exist_ok=True)
        with open(env_path, "w") as f:
            f.write(f"NEXT_PUBLIC_SUPABASE_URL={url}\n")
            f.write(f"NEXT_PUBLIC_SUPABASE_ANON_KEY={anon_key}\n")
            f.write(f"SUPABASE_SERVICE_ROLE_KEY={service_key}\n")
        
        print(f"\n✅ Configuration saved to {env_path}")
        print("\nNext steps:")
        print(f"1. Run the SQL schema in your Supabase Editor: {CLI_COLOR_CYAN}supabase_schema.sql{CLI_COLOR_RESET}")
        print("2. In Supabase > Authentication > Providers, you can disable 'Confirm Email' for quick local testing.")
        print("3. Deploy your 'remote' folder or run it locally with 'npm run dev'.")
    else:
        print("Setup aborted. Missing required keys.")

def push(slug, db_path="tube2txt.db", projects_dir="projects"):
    """Sync a local project to the Supabase remote."""
    if not requests:
        raise ImportError("The 'requests' module is required for remote sync. Install with pip install requests")

    # Verify slug exists in local DB first
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT title, url FROM videos WHERE slug = ?", (slug,))
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Error: Slug '{slug}' not found in local DB.")
        title, video_url = row
        cursor.execute("SELECT start_ts, seconds, text FROM segments WHERE video_id = (SELECT id FROM videos WHERE slug = ?)", (slug,))
        segments = [{"start": r[0], "seconds": r[1], "text": r[2]} for r in cursor.fetchall()]

    # Load remote configuration
    env_path = os.path.join("remote", ".env.local")
    if not os.path.exists(env_path):
        raise FileNotFoundError("Remote gallery not configured. Run 'tube2txt config' first.")

    url = None
    key = None
    with open(env_path, "r") as f:
        for line in f:
            if line.startswith("NEXT_PUBLIC_SUPABASE_URL="):
                url = line.strip().split("=", 1)[1]
            elif line.startswith("SUPABASE_SERVICE_ROLE_KEY="):
                key = line.strip().split("=", 1)[1]
            elif line.startswith("NEXT_PUBLIC_SUPABASE_ANON_KEY=") and not key:
                key = line.strip().split("=", 1)[1]

    if not url or not key:
        raise ValueError("Error: Missing credentials in remote/.env.local")

    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates"
    }

    # Push video metadata
    video_payload = {"slug": slug, "title": title, "date": datetime.now().isoformat()}
    resp = requests.post(f"{url}/rest/v1/videos", headers=headers, json=video_payload)
    if resp.status_code >= 400:
        raise RuntimeError(f"Failed to sync video record: {resp.text}")

    # Retrieve video ID for metadata linking
    resp = requests.get(f"{url}/rest/v1/videos?slug=eq.{slug}&select=id", headers=headers)
    if resp.status_code >= 400 or not resp.json():
        raise RuntimeError(f"Failed to fetch video ID for metadata sync: {resp.text}")
    vid_id = resp.json()[0]['id']

    # Bundle additional metadata files
    project_path = os.path.join(projects_dir, slug)
    metadata_bundle = {}
    for md_file in ["TUBE2TXT-OUTLINE.md", "TUBE2TXT-NOTES.md", "TUBE2TXT-CLIPS.md", "TUBE2TXT-RECIPE.md", "TUBE2TXT-TECHNICAL.md"]:
        fpath = os.path.join(project_path, md_file)
        if os.path.exists(fpath):
            with open(fpath, "r") as f:
                content = f.read()
            mtype = md_file.split("-")[1].split(".")[0].lower()
            metadata_bundle[mtype] = content
    if segments:
        metadata_bundle["transcript"] = segments

    meta_payload = {"video_slug": slug, "type": "bundle", "content": json.dumps(metadata_bundle), "vid_id": vid_id}
    resp = requests.post(f"{url}/rest/v1/metadata", headers=headers, json=meta_payload)
    if resp.status_code >= 400:
        raise RuntimeError(f"Failed to sync metadata: {resp.text}")

    # Update local DB sync timestamp
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE videos SET last_synced_at = ? WHERE slug = ?", (datetime.now().isoformat(), slug))
        conn.commit()
    print(f"✅ Successfully synced '{slug}' to remote.")


def get_remote_url(slug=None):
    # This is a stub for generating the live URL
    base = "https://your-deployment-url.vercel.app"
    if slug:
        return f"{base}/v/{slug}"
    return base
