import os
import re
import sys
import json
import argparse
import sqlite3
import subprocess
import glob as glob_module
import shutil
import concurrent.futures
from datetime import datetime
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
from google import genai
from google.genai import types

# Constants for terminal coloring
CLI_COLOR_CYAN = "\033[36m"
CLI_COLOR_RESET = "\033[0m"

class Database:
    def __init__(self, db_path="tube2txt.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        # Robustness check: Ensure db_path isn't a directory
        if os.path.isdir(self.db_path):
            raise RuntimeError(
                f"Cannot initialize database: '{self.db_path}' is a directory. "
                "Please delete the directory or choose a different database path."
            )

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
            'outline': (
                "Provide a clear, high-level markdown outline of the content. "
                "Include timestamps in brackets [HH:MM:SS] for each section. "
                "Adhere to 'The Elements of Style' (1918): omit needless words, "
                "be specific, concrete, and definite."
            ),
            'notes': (
                "Create detailed study notes from this transcript. "
                "Adhere strictly to the principles of 'The Elements of Style' (1918): "
                "Be clear, concise, and use the active voice. Omit needless words. "
                "Include key takeaways, definitions of complex terms, and a summary for each major section. "
                "Use timestamps in brackets [HH:MM:SS]."
            ),
            'recipe': (
                "Extract recipes, ingredients, and cooking steps from this transcript. "
                "Follow 'The Elements of Style' (1918): use the active voice for instructions, "
                "be specific and definite, and omit needless words. "
                "Format them clearly in markdown with timestamps [HH:MM:SS]."
            ),
            'technical': (
                "Provide a technical deep-dive or documentation based on this transcript. "
                "Adhere to 'The Elements of Style' (1918): use definite, specific, concrete language. "
                "Omit needless words. Focus on implementation details, code concepts, and architectural points. "
                "Use timestamps in brackets [HH:MM:SS]."
            ),
            'clips': (
                "Identify the 3 most interesting, viral, or high-value 30-60 second segments from this video. "
                "In your descriptions, follow 'The Elements of Style' (1918): "
                "use active voice, be specific, and omit needless words. "
                "For each, provide:\n"
                "1. A catchy title.\n"
                "2. Start and End timestamps (format: HH:MM:SS-HH:MM:SS).\n"
                "3. A brief reason why it's a great clip.\n"
                "Return ONLY the data in this format:\n"
                "CLIP:[Title]|[HH:MM:SS-HH:MM:SS]|[Reason]\n"
                "After the CLIP: lines, you may provide a brief markdown summary of why these clips represent the essence of the video, "
                "maintaining a concise, vigorous style."
            )
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

def download_video(url, output_dir, on_progress=None):
    """Download video and subtitles using yt-dlp. Returns (video_file, vtt_file) or (None, None)."""
    os.makedirs(output_dir, exist_ok=True)
    cmd = [
        "yt-dlp", "--no-warnings",
        "--write-auto-subs", "--write-subs",
        "-o", os.path.join(output_dir, "video.%(ext)s")
    ]

    # Add cookies if available
    cookies_path = os.environ.get("YT_DLP_COOKIES")
    if not cookies_path:
        # Check standard locations
        possible_paths = [
            os.path.join(os.getcwd(), "cookies.txt"),
            os.path.join(os.getcwd(), "projects", "cookies.txt"),
            os.path.join(os.getcwd(), "src", "cookies.txt")
        ]
        for p in possible_paths:
            if os.path.exists(p):
                cookies_path = p
                break

cmd.extend(["--cookies-from-browser chrome -cookies cookies.txt"])

    # if cookies_path and os.path.exists(cookies_path):
    #     _notify(on_progress, "status", "download", f"Using cookies from: {cookies_path}")
    #     cmd.extend(["--cookies-from-browser chrome -cookies", cookies_path])

    cmd.append(url)
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if result.stdout:
            for line in result.stdout.splitlines():
                if line.strip():
                    _notify(on_progress, "status", "download", f"yt-dlp: {line}")
    except subprocess.CalledProcessError as e:
        error_msg = f"yt-dlp failed (code {e.returncode})"
        if e.stderr:
            error_msg += f": {e.stderr.strip()}"
        elif e.stdout:
            error_msg += f": {e.stdout.strip()}"
        _notify(on_progress, "error", "download", f"Error downloading: {error_msg}")
        return None, None
    except Exception as e:
        _notify(on_progress, "error", "download", f"Unexpected error during download: {e}")
        return None, None

    # Find downloaded files
    video_files = glob_module.glob(os.path.join(output_dir, "video.*"))
    video_files = [f for f in video_files if not f.endswith(".vtt")]
    vtt_files = glob_module.glob(os.path.join(output_dir, "video.*.vtt"))

    video = video_files[0] if video_files else None
    vtt = vtt_files[0] if vtt_files else None
    return video, vtt


def _extract_single_image(video_path, ts, output_path):
    """Extract a single frame using ffmpeg."""
    cmd = [
        "ffmpeg", "-ss", ts, "-nostdin", "-i", video_path,
        "-frames:v", "1", "-q:v", "2", "-vf", "scale=1024:-1",
        "-strict", "-2",
        output_path, "-loglevel", "error", "-y"
    ]
    try:
        subprocess.run(cmd, check=True)
        return True
    except Exception:
        return False


def extract_images(video_path, segments, images_dir, parallel=4):
    """Extract screenshot images for each segment in parallel using ffmpeg."""
    os.makedirs(images_dir, exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=parallel) as executor:
        futures = []
        for seg in segments:
            ts = seg["start"]
            ts_filename = ts.replace(":", "-").replace(".", "-")
            img_path = os.path.join(images_dir, f"{ts_filename}.jpg")
            if not os.path.exists(img_path):
                futures.append(executor.submit(_extract_single_image, video_path, ts, img_path))
        concurrent.futures.wait(futures)


def _notify(on_progress, type_, step, message):
    """Send progress notification via callback or print."""
    if on_progress:
        on_progress(type_, step, message)
    else:
        print(message)


def process_video(url, slug, mode="outline", ai_flag=True, db_path="tube2txt.db",
                  project_path=None, on_progress=None, parallel=4):
    """
    Full video processing pipeline. Returns project_path on success, None on failure.

    on_progress: optional callback (type: str, step: str, message: str) -> None
    """
    if project_path is None:
        project_path = os.path.join("projects", slug)
    os.makedirs(os.path.join(project_path, "images"), exist_ok=True)

    # 1. Download
    _notify(on_progress, "status", "download", "Downloading video and subtitles...")
    video_file, vtt_file = download_video(url, project_path, on_progress=on_progress)
    if not video_file or not vtt_file:
        return None

    # 2. Parse VTT
    _notify(on_progress, "status", "parse", "Parsing subtitles...")
    parser = VTTParser(vtt_file)
    segments = parser.parse()

    # 3. Generate HTML
    _notify(on_progress, "status", "html", "Generating HTML...")
    html_gen = HTMLGenerator(segments, url, slug)
    html_gen.generate(os.path.join(project_path, "index.html"))

    # Copy styles.css
    pkg_dir = os.path.dirname(os.path.abspath(__file__))
    styles_src = os.path.join(pkg_dir, "styles.css")
    if not os.path.exists(styles_src):
        styles_src = os.path.join(os.path.dirname(os.path.dirname(pkg_dir)), "styles.css")
    if os.path.exists(styles_src):
        shutil.copy(styles_src, os.path.join(project_path, "styles.css"))

    # 4. DB indexing
    _notify(on_progress, "status", "index", f"Indexing video in database...")
    db = Database(db_path)
    db.index_video(slug, url, segments)

    # 5. AI content
    api_key = os.environ.get("GEMINI_API_KEY")
    if ai_flag and not api_key:
        _notify(on_progress, "status", "ai", "Skipping AI -- GEMINI_API_KEY not set")
    elif ai_flag and api_key:
        client = GeminiClient(api_key)

        _notify(on_progress, "status", "ai", "Generating outline...")
        outline = client.generate_content(segments, mode="outline")
        outline_path = os.path.join(project_path, "TUBE2TXT-OUTLINE.md")
        with open(outline_path, "w", encoding="utf-8") as f:
            f.write(outline)
        _notify(on_progress, "ai_output", "ai", outline)

        best_mode = client.determine_best_mode(outline)
        _notify(on_progress, "status", "ai", f"Generating {best_mode} content...")
        additional = client.generate_content(segments, mode=best_mode)
        add_path = os.path.join(project_path, f"TUBE2TXT-{best_mode.upper()}.md")
        with open(add_path, "w", encoding="utf-8") as f:
            f.write(additional)
        _notify(on_progress, "ai_output", "ai", additional)

        if mode == "clips":
            _notify(on_progress, "status", "ai", "Generating clips...")
            clips = client.generate_content(segments, mode="clips")
            clips_path = os.path.join(project_path, "TUBE2TXT-CLIPS.md")
            with open(clips_path, "w", encoding="utf-8") as f:
                f.write(clips)
            _notify(on_progress, "ai_output", "ai", clips)

    # 6. Extract images
    _notify(on_progress, "status", "images", "Extracting images...")
    extract_images(video_file, segments, os.path.join(project_path, "images"), parallel=parallel)

    _notify(on_progress, "complete", "done", f"Finished processing {slug}")
    return project_path


def get_parser():
    parser = argparse.ArgumentParser(description="Tube2Txt Python Logic")
    parser.add_argument("slug_or_url", nargs="?", help="Project slug or YouTube URL")
    parser.add_argument("url", nargs="?", help="YouTube video URL (if slug provided)")
    parser.add_argument("--vtt", help="Path to existing VTT file (skips download)")
    parser.add_argument("--ai", action="store_true", help="Run AI generation")
    parser.add_argument("--mode", default="outline", help="Requested AI mode")
    parser.add_argument("--parallel", type=int, default=4, help="Parallel image extraction")
    parser.add_argument("--db", default="tube2txt.db", help="Path to SQLite DB")
    parser.add_argument("--projects-dir", default="projects", help="Directory for output")
    parser.add_argument("--clip", help="Manual clip: START-END")
    parser.add_argument("--video-file", help="Video file for manual clipping")
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()

    # Manual Clipping
    if args.clip and args.video_file:
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

    # Resolve URL and slug
    url = args.url
    slug = args.slug_or_url
    if not url:
        if slug and (slug.startswith("http") or len(slug) == 11):
            url = slug
            slug = "default"
        else:
            print("Error: Missing URL.")
            sys.exit(1)

    project_path = os.path.join(args.projects_dir, slug)
    result = process_video(
        url=url,
        slug=slug,
        mode=args.mode,
        ai_flag=args.ai,
        db_path=args.db,
        project_path=project_path,
        parallel=args.parallel,
    )

    if result:
        print(f"\nProject: {os.path.abspath(result)}")

if __name__ == "__main__":
    main()
