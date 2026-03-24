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
            model='gemini-2.5-flash',
            contents=prompt
        )
        return response.text

    def determine_best_mode(self, outline):
        prompt = f"""
Based on the following video outline, determine which of these three modes is most appropriate for a deep-dive:
1. 'recipe' (if it's a cooking video or contains a recipe)
2. 'technical' (if it's about coding, engineering, or complex systems)
3. 'notes' (if it's an educational talk, lecture, or general information)

Outline:
{outline}

Return ONLY the word: 'recipe', 'technical', or 'notes'.
"""
        response = self.client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        mode = response.text.strip().lower()
        if 'recipe' in mode: return 'recipe'
        if 'technical' in mode: return 'technical'
        return 'notes'

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
    parser.add_argument("--mode", default="outline", help="Requested AI mode")
    parser.add_argument("--ai", action="store_true", help="Run AI generation")
    parser.add_argument("--db", default="tube2txt.db", help="Path to SQLite DB")
    parser.add_argument("--clip", help="Extract a clip: START-END (HH:MM:SS-HH:MM:SS)")
    parser.add_argument("--video-file", help="Path to video file for clipping")
    
    args = parser.parse_args()

    # Manual Clipping
    if args.clip and args.video_file:
        # Parse timestamps: "HH:MM:SS-HH:MM:SS" or "HH:MM:SS.mmm-HH:MM:SS.mmm"
        clip_match = re.match(r'^(\d{2}:\d{2}:\d{2}(?:\.\d+)?)-(\d{2}:\d{2}:\d{2}(?:\.\d+)?)$', args.clip)
        if not clip_match:
            print(f"Error: Invalid clip range format '{args.clip}'. Expected HH:MM:SS-HH:MM:SS")
            sys.exit(1)
        start, end = clip_match.group(1), clip_match.group(2)
        output_name = f"clip_{start.replace(':','-')}_{end.replace(':','-')}.mp4"
        os.makedirs("clips", exist_ok=True)
        if ClippingEngine.extract_clip(args.video_file, start, end, os.path.join("clips", output_name)):
            print(f"CLIP_SAVED:clips/{output_name}")
        sys.exit(0)

    if not args.url or not args.slug:
        print("Error: Missing required arguments (URL and Slug).")
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

        api_key = os.environ.get("GEMINI_API_KEY")
        if args.ai and not api_key:
            print("Warning: GEMINI_API_KEY not found. Skipping AI generation.")
        
        if api_key:
            client = GeminiClient(api_key)
            
            # 1. Always generate the outline
            print("\n--- GENERATING OUTLINE ---")
            outline = client.generate_content(segments, mode='outline')
            outline_path = f"TUBE2TXT-OUTLINE.md"
            with open(outline_path, 'w', encoding='utf-8') as f:
                f.write(outline)
            print(outline)
            print(f"\nAI Outline saved at {outline_path}")

            # 2. Determine best additional mode and generate it
            best_mode = client.determine_best_mode(outline)
            print(f"\n--- GENERATING ADDITIONAL CONTENT ({best_mode.upper()}) ---")
            additional_content = client.generate_content(segments, mode=best_mode)
            additional_path = f"TUBE2TXT-{best_mode.upper()}.md"
            with open(additional_path, 'w', encoding='utf-8') as f:
                f.write(additional_content)
            print(additional_content)
            print(f"\nAI {best_mode.capitalize()} saved at {additional_path}")

            # 3. Special case for Clips if explicitly requested
            if args.mode == 'clips':
                print("\n--- GENERATING CLIPS ---")
                clips_content = client.generate_content(segments, mode='clips')
                clips_path = "TUBE2TXT-CLIPS.md"
                with open(clips_path, 'w', encoding='utf-8') as f:
                    f.write(clips_content)
                print(clips_content)
                for line in clips_content.split('\n'):
                    if line.startswith('CLIP:'):
                        print(line)

        # Output timestamps for Bash to use for image extraction
        for seg in segments:
            print(f"TIMESTAMP:{seg['start']}")

if __name__ == "__main__":
    main()
