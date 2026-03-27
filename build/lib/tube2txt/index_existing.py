import os
import sqlite3
import re
from tube2txt import Database, VTTParser

# For pip-installed packages, the database and projects dir should be relative to CWD
# unless specified via environment variables.
CWD = os.getcwd()

def migrate():
    db_path = os.environ.get("TUBE2TXT_DB", os.path.join(CWD, "tube2txt.db"))
    db = Database(db_path)
    projects_dir = os.path.join(CWD, "projects")
    
    if not os.path.exists(projects_dir):
        print(f"No projects directory found at {projects_dir}")
        return

    for slug in os.listdir(projects_dir):
        proj_path = os.path.join(projects_dir, slug)
        if not os.path.isdir(proj_path):
            continue
            
        print(f"Migrating {slug}...")
        
        # Try to find VTT and index.html to reconstruct data
        vtt_file = None
        for f in os.listdir(proj_path):
            if f.endswith(".vtt"):
                vtt_file = os.path.join(proj_path, f)
                break
        
        if not vtt_file:
            print(f"  Skipping {slug}: No VTT file found.")
            continue
            
        # Re-parse VTT
        parser = VTTParser(vtt_file)
        segments = parser.parse()
        
        # Re-index
        # We might not have the original URL, so we'll use a placeholder or try to find it in index.html
        url = "https://www.youtube.com/" 
        index_html = os.path.join(proj_path, "index.html")
        if os.path.exists(index_html):
            with open(index_html, 'r') as f:
                content = f.read()
                match = re.search(r'Source: <a href="([^"]+)"', content)
                if match:
                    url = match.group(1)
        
        db.index_video(slug, url, segments)
        print(f"  Successfully migrated {slug}")

if __name__ == "__main__":
    migrate()
