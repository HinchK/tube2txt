import os
import re
import sys
import json
import argparse
import sqlite3
import subprocess
from datetime import datetime
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
from google import genai
from google.genai import types

class Database:
    def __init__(self, db_path="tube2txt.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS videos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    slug TEXT UNIQUE,
                    url TEXT,
                    title TEXT,
                    processed_at DATETIME
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS segments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id INTEGER,
                    start_ts TEXT,
                    seconds INTEGER,
                    text TEXT,
                    thumbnail_path TEXT,
                    FOREIGN KEY (video_id) REFERENCES videos (id)
                )
            """)
            # FTS for global search
            cursor.execute("CREATE VIRTUAL TABLE IF NOT EXISTS segments_search USING fts5(segment_id, text)")
            conn.commit()

    def index_video(self, slug, url, segments):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO videos (slug, url, title, processed_at) VALUES (?, ?, ?, ?)",
                         (slug, url, slug, datetime.now().isoformat()))
            video_id = cursor.lastrowid
            
            # Clear old segments if any
            cursor.execute("DELETE FROM segments WHERE video_id = ?", (video_id,))
            
            for seg in segments:
                ts_filename = seg['start'].replace(':', '-').replace('.', '-')
                thumbnail_path = f"images/{ts_filename}.jpg"
                cursor.execute("INSERT INTO segments (video_id, start_ts, seconds, text, thumbnail_path) VALUES (?, ?, ?, ?, ?)",
                             (video_id, seg['start'], seg['seconds'], seg['text'], thumbnail_path))
                segment_id = cursor.lastrowid
                cursor.execute("INSERT INTO segments_search (segment_id, text) VALUES (?, ?)", (segment_id, seg['text']))
            conn.commit()

class ClippingEngine:
    @staticmethod
    def extract_clip(video_file, start_ts, end_ts, output_path):
        """Extract a clip using ffmpeg stream copy (lossless and fast)."""
        cmd = [
            "ffmpeg", "-ss", start_ts, "-to", end_ts,
            "-i", video_file, "-c", "copy", "-map", "0",
            output_path, "-loglevel", "error", "-y"
        ]
        try:
            subprocess.run(cmd, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error extracting clip: {e}")
            return False

class GeminiClient:
    def __init__(self, api_key):
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required.")
        self.client = genai.Client(api_key=api_key)

    def generate_content(self, segments, mode='outline'):
        full_transcript = "\n".join([f"[{s['start']}] {s['text']}" for s in segments])
        
        prompts = {
            'outline': "Provide a clear, high-level markdown outline of the content. Include timestamps in brackets [HH:MM:SS] for each section.",
            'notes': "Create detailed study notes from this transcript. Include key takeaways, definitions of any complex terms, and a summary for each major section. Use timestamps in brackets [HH:MM:SS].",
            'recipe': "Extract any recipes, ingredients, and cooking steps from this transcript. Format them clearly in markdown with timestamps [HH:MM:SS].",
            'technical': "Provide a technical deep-dive or documentation based on this transcript. Focus on implementation details, code concepts, and architectural points. Use timestamps in brackets [HH:MM:SS].",
            'clips': """Identify the 3 most interesting, viral, or high-value 30-60 second segments from this video. 
            For each, provide:
            1. A catchy title.
            2. Start and End timestamps (format: HH:MM:SS-HH:MM:SS).
            3. A brief reason why it's a great clip.
            Return ONLY the data in this format:
            CLIP:[Title]|[HH:MM:SS-HH:MM:SS]|[Reason]
            """
        }
        
        system_prompt = prompts.get(mode, prompts['outline'])
        prompt = f"""
I have a transcript of a YouTube video. {system_prompt}

Transcript:
{full_transcript}
"""
        response = self.client.models.generate_content(
            model='models/gemini-2.0-flash',
            contents=prompt
        )
        return response.text

class VTTParser:
    def __init__(self, file_path):
        self.file_path = file_path
        self.segments = []

    def parse(self):
        with open(self.file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Simple VTT parsing logic
        lines = content.strip().split('\n')
        current_start = None
        current_text = []
        in_header = True

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if in_header:
                if '-->' in line:
                    in_header = False
                else:
                    continue

            match = re.search(r'(\d\d:\d\d:\d\d\.\d\d\d) --> (\d\d:\d\d:\d\d\.\d\d\d)', line)
            if match:
                if current_start and current_text:
                    self.segments.append({
                        'start': current_start,
                        'text': ' '.join(current_text),
                        'seconds': self.to_seconds(current_start)
                    })
                current_start = match.group(1)
                current_text = []
            else:
                # Basic cleaning of VTT tags like <c>
                line = re.sub(r'<[^>]+>', '', line)
                if line and not line.isdigit():
                    current_text.append(line)

        # Add last segment
        if current_start and current_text:
            self.segments.append({
                'start': current_start,
                'text': ' '.join(current_text),
                'seconds': self.to_seconds(current_start)
            })

        # Deduplicate consecutive identical text segments (common in auto-subs)
        deduped = []
        last_text = None
        for seg in self.segments:
            if seg['text'] != last_text:
                deduped.append(seg)
                last_text = seg['text']
        self.segments = deduped
        return self.segments

    def to_seconds(self, timestamp):
        parts = timestamp.split(':')
        h, m, s = float(parts[0]), float(parts[1]), float(parts[2])
        return int(h * 3600 + m * 60 + s)

class HTMLGenerator:
    def __init__(self, segments, video_url, slug):
        self.segments = segments
        self.video_url = video_url
        self.slug = slug

    def generate(self, output_file):
        html_content = f"""<html>
<head>
 <link rel="stylesheet" type="text/css" href="styles.css" />
 </head>
<body>
<h1>Youtube transcript: {self.slug}</h1>
Source: <a href="{self.video_url}" target="_blank">{self.video_url}</a>
<ul>
"""
        for seg in self.segments:
            ts_filename = seg['start'].replace(':', '-').replace('.', '-')
            html_content += f"""<li>
    <div class="grab"><img src="images/{ts_filename}.jpg" /></div>
    <div class="subtitle">
        <span id="{seg['start']}">{seg['text']}</span>
        <a href="{self.video_url}&t={seg['seconds']}" target="_blank" class="videolink">#</a>
    </div>
</li>
"""
        html_content += """
</ul>
</body>
</html>"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

def main():
    parser = argparse.ArgumentParser(description="Tube2Txt Python Logic")
    parser.add_argument("--vtt", help="Path to VTT file")
    parser.add_argument("--url", help="YouTube video URL")
    parser.add_argument("--slug", help="Project slug")
    parser.add_argument("--output-html", help="Path to output HTML")
    parser.add_argument("--output-outline", help="Path to output markdown content")
    parser.add_argument("--mode", default="outline", choices=["outline", "notes", "recipe", "technical", "clips"], help="AI mode")
    parser.add_argument("--ai", action="store_true", help="Run AI generation")
    parser.add_argument("--db", default="tube2txt.db", help="Path to SQLite DB")
    parser.add_argument("--clip", help="Extract a clip: START-END (HH:MM:SS-HH:MM:SS)")
    parser.add_argument("--video-file", help="Path to video file for clipping")
    
    args = parser.parse_args()

    # Manual Clipping
    if args.clip and args.video_file:
        start, end = args.clip.split('-')
        output_name = f"clip_{start.replace(':','-')}_{end.replace(':','-')}.mp4"
        os.makedirs("clips", exist_ok=True)
        if ClippingEngine.extract_clip(args.video_file, start, end, os.path.join("clips", output_name)):
            print(f"CLIP_SAVED:clips/{output_name}")
        sys.exit(0)

    # Interactive prompts if arguments are missing and we're in a terminal
    if sys.stdin.isatty():
        if not args.url:
            args.url = input("Enter YouTube URL or Video ID: ").strip()
        if not args.slug:
            # Generate a default slug from URL if possible
            if args.url:
                if '=' in args.url:
                    default_slug = args.url.split('=')[-1]
                else:
                    default_slug = args.url.split('/')[-1]
                args.slug = input(f"Enter project name (default '{default_slug}'): ").strip() or default_slug
            else:
                args.slug = input("Enter project name: ").strip()
        
        if not args.output_html:
            args.output_html = "index.html"
        if not args.output_outline:
            args.output_outline = f"TUBE2TXT-{args.mode.upper()}.md"

    if not args.url or not args.slug:
        print("Error: Missing required arguments (URL and Slug). Use --help for usage.")
        sys.exit(1)

    if args.vtt:
        vtt_parser = VTTParser(args.vtt)
        segments = vtt_parser.parse()

        html_gen = HTMLGenerator(segments, args.url, args.slug)
        html_gen.generate(args.output_html)

        # DB Indexing
        db = Database(args.db)
        db.index_video(args.slug, args.url, segments)
        print(f"Video indexed in DB: {args.db}")

        if args.ai:
            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                print("Warning: GEMINI_API_KEY not found. Skipping AI generation.")
            else:
                client = GeminiClient(api_key)
                content = client.generate_content(segments, args.mode)
                with open(args.output_outline, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"AI {args.mode.capitalize()} generated at {args.output_outline}")
                
                # If mode is clips, output CLIP: headers for Bash to parse
                if args.mode == 'clips':
                    for line in content.split('\n'):
                        if line.startswith('CLIP:'):
                            print(line)

        # Output timestamps for Bash to use for image extraction
        for seg in segments:
            print(f"TIMESTAMP:{seg['start']}")

if __name__ == "__main__":
    main()
