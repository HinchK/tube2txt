import os
import json
import sqlite3
from datetime import datetime

try:
    import requests
except ImportError:
    requests = None

def setup_remote():
    """Interactive prompt to set up remote deployment configuration."""
    print("Setting up remote deployment for MyTubeScripts...")
    
    env_path = os.path.join("remote", ".env.local")
    
    url = input("Enter your Supabase Project URL: ").strip()
    key = input("Enter your Supabase Anon Key: ").strip()
    
    if url and key:
        os.makedirs("remote", exist_ok=True)
        with open(env_path, "w") as f:
            f.write(f"NEXT_PUBLIC_SUPABASE_URL={url}\n")
            f.write(f"NEXT_PUBLIC_SUPABASE_ANON_KEY={key}\n")
        print(f"✅ Saved to {env_path}")
        print("\nNext steps:")
        print("1. Go to your Supabase dashboard and create two tables:")
        print("   - 'videos' (id, slug, title, date)")
        print("   - 'metadata' (id, video_slug, type, content)")
        print("2. Deploy your 'remote' folder to Vercel or Netlify.")
        print("   cd remote && npx vercel")
    else:
        print("Setup aborted.")

def sync_project(slug, db_path="tube2txt.db", projects_dir="projects"):
    """Sync a local project to the Supabase remote."""
    if not requests:
        print("Error: The 'requests' module is required for remote sync.")
        print("Run: pip install requests")
        return

    env_path = os.path.join("remote", ".env.local")
    if not os.path.exists(env_path):
        print("Error: Remote not configured. Run 'tube2txt setup' first.")
        return

    url = None
    key = None
    with open(env_path, "r") as f:
        for line in f:
            if line.startswith("NEXT_PUBLIC_SUPABASE_URL="):
                url = line.strip().split("=", 1)[1]
            elif line.startswith("NEXT_PUBLIC_SUPABASE_ANON_KEY="):
                key = line.strip().split("=", 1)[1]

    if not url or not key:
        print("Error: Missing credentials in remote/.env.local")
        return

    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates"
    }

    # Fetch local DB data
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT title, url FROM videos WHERE slug = ?", (slug,))
        row = cursor.fetchone()
        if not row:
            print(f"Error: Slug '{slug}' not found in local DB.")
            return
        title, video_url = row

        cursor.execute("SELECT start_ts, seconds, text FROM segments WHERE video_id = (SELECT id FROM videos WHERE slug = ?)", (slug,))
        segments = [{"start": r[0], "seconds": r[1], "text": r[2]} for r in cursor.fetchall()]

    # Push to 'videos' table
    video_payload = {
        "slug": slug,
        "title": title,
        "date": datetime.now().isoformat()
    }
    
    resp = requests.post(f"{url}/rest/v1/videos", headers=headers, json=video_payload)
    if resp.status_code >= 400:
        print(f"Failed to sync video record: {resp.text}")
        return

    # Push metadata (outline, etc)
    project_path = os.path.join(projects_dir, slug)
    for md_file in ["TUBE2TXT-OUTLINE.md", "TUBE2TXT-NOTES.md", "TUBE2TXT-CLIPS.md", "TUBE2TXT-RECIPE.md", "TUBE2TXT-TECHNICAL.md"]:
        fpath = os.path.join(project_path, md_file)
        if os.path.exists(fpath):
            with open(fpath, "r") as f:
                content = f.read()
            mtype = md_file.split("-")[1].split(".")[0].lower()
            meta_payload = {
                "video_slug": slug,
                "type": mtype,
                "content": content
            }
            requests.post(f"{url}/rest/v1/metadata", headers=headers, json=meta_payload)

    # Sync segments as 'transcript' metadata type (JSON stringified)
    if segments:
        requests.post(f"{url}/rest/v1/metadata", headers=headers, json={
            "video_slug": slug,
            "type": "transcript",
            "content": json.dumps(segments)
        })

    # Update local DB last_synced_at
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
