import os
import re
import sys
import argparse
import glob
import shutil
import concurrent.futures
from .db import Database
from .clipping import ClippingEngine
from .ai import GeminiClient
from .parsers import VTTParser
from .generator import HTMLGenerator
from .downloader import Downloader

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Constants for terminal coloring
CLI_COLOR_CYAN = "\033[36m"
CLI_COLOR_RESET = "\033[0m"

def extract_single_image(video_path, ts, output_path):
    """Extract a single image frame using ffmpeg."""
    cmd = [
        "ffmpeg", "-ss", ts, "-nostdin", "-i", video_path, 
        "-frames:v", "1", "-q:v", "2", "-vf", "scale=1024:-1", 
        output_path, "-loglevel", "error", "-y"
    ]
    try:
        subprocess.run(cmd, check=True)
        return True
    except Exception as e:
        print(f"Error extracting image at {ts}: {e}")
        return False

def process_video_logic(url, slug, mode, ai_flag, db_path, parallel, projects_dir, styles_css_path):
    print(f"----------------------------------------------------")
    print(f"Processing video: {slug} ({url})")
    print(f"----------------------------------------------------")
    
    project_path = os.path.join(projects_dir, slug)
    os.makedirs(os.path.join(project_path, "images"), exist_ok=True)
    
    # Copy styles.css
    if os.path.exists(styles_css_path):
        shutil.copy(styles_css_path, os.path.join(project_path, "styles.css"))
    
    # Download
    print("Downloading video and subtitles...")
    video_file, vtt_file = Downloader.get_video_and_subs(url, project_path)
    
    if not video_file or not vtt_file:
        print(f"Error: Could not download video or subtitles for {slug}.")
        return None

    # Parse & Generate HTML
    print("Generating HTML and processing transcript...")
    vtt_path = os.path.join(project_path, vtt_file)
    parser = VTTParser(vtt_path)
    segments = parser.parse()
    
    html_gen = HTMLGenerator(segments, url, slug)
    html_gen.generate(os.path.join(project_path, "index.html"))
    
    # DB Indexing
    db = Database(db_path)
    db.index_video(slug, url, segments)
    print(f"Video indexed in DB: {db_path}")
    
    # AI Content
    api_key = os.environ.get("GEMINI_API_KEY")
    if ai_flag and not api_key:
        print("Warning: GEMINI_API_KEY not found. Skipping AI generation.")
        api_key = None

    if api_key:
        client = GeminiClient(api_key)
        
        # 1. Outline
        print("\n--- GENERATING OUTLINE ---")
        outline = client.generate_content(segments, mode='outline')
        with open(os.path.join(project_path, "TUBE2TXT-OUTLINE.md"), 'w', encoding='utf-8') as f:
            f.write(outline)
        for line in outline.split('\n'):
            print(f"{CLI_COLOR_CYAN}{line}{CLI_COLOR_RESET}")

        # 2. Best mode
        best_mode = client.determine_best_mode(outline)
        print(f"\n--- GENERATING ADDITIONAL CONTENT ({best_mode.upper()}) ---")
        additional = client.generate_content(segments, mode=best_mode)
        with open(os.path.join(project_path, f"TUBE2TXT-{best_mode.upper()}.md"), 'w', encoding='utf-8') as f:
            f.write(additional)
        for line in additional.split('\n'):
            if line.startswith('CLIP:'):
                print(f"{CLI_COLOR_CYAN}[CLIP] {line[5:]}{CLI_COLOR_RESET}")
            else:
                print(f"{CLI_COLOR_CYAN}{line}{CLI_COLOR_RESET}")

        # 3. Explicit clips
        if mode == 'clips':
            print("\n--- GENERATING CLIPS ---")
            clips_content = client.generate_content(segments, mode='clips')
            with open(os.path.join(project_path, "TUBE2TXT-CLIPS.md"), 'w', encoding='utf-8') as f:
                f.write(clips_content)
            
            clip_ranges = []
            for line in clips_content.split('\n'):
                if line.startswith('CLIP:'):
                    print(f"{CLI_COLOR_CYAN}[CLIP] {line[5:]}{CLI_COLOR_RESET}")
                    clip_ranges.append(line.split('|')[1])
                else:
                    print(f"{CLI_COLOR_CYAN}{line}{CLI_COLOR_RESET}")
            
            # Extract AI clips
            if clip_ranges:
                print("Extracting AI-recommended clips...")
                for r in clip_ranges:
                    start, end = r.split('-')
                    out_name = f"clip_{start.replace(':','-')}_{end.replace(':','-')}.mp4"
                    os.makedirs(os.path.join(project_path, "clips"), exist_ok=True)
                    ClippingEngine.extract_clip(
                        os.path.join(project_path, video_file), 
                        start, end, 
                        os.path.join(project_path, "clips", out_name)
                    )

    # Extract images in parallel
    print(f"Extracting images in parallel ({parallel} processes)...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=parallel) as executor:
        futures = []
        for seg in segments:
            ts = seg['start']
            ts_filename = ts.replace(':', '-').replace('.', '-')
            img_path = os.path.join(project_path, "images", f"{ts_filename}.jpg")
            if not os.path.exists(img_path):
                futures.append(executor.submit(
                    extract_single_image, 
                    os.path.join(project_path, video_file), 
                    ts, img_path
                ))
        concurrent.futures.wait(futures)
    
    print(f"Finished: {slug}")
    return project_path

def main():
    parser = argparse.ArgumentParser(description="Tube2Txt CLI")
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
    
    args = parser.parse_args()

    # Manual Clipping
    if args.clip and args.video_file:
        clip_match = re.match(r'^(\d{2}:\d{2}:\d{2}(?:\.\d+)?)-(\d{2}:\d{2}:\d{2}(?:\.\d+)?)$', args.clip)
        if not clip_match:
            print(f"Error: Invalid format {args.clip}")
            sys.exit(1)
        start, end = clip_match.group(1), clip_match.group(2)
        output_name = f"clip_{start.replace(':','-')}_{end.replace(':','-')}.mp4"
        os.makedirs("clips", exist_ok=True)
        if ClippingEngine.extract_clip(args.video_file, start, end, os.path.join("clips", output_name)):
            print(f"CLIP_SAVED:clips/{output_name}")
        sys.exit(0)

    # Normal processing
    url = args.url
    slug = args.slug_or_url
    
    if not url:
        # If only one positional arg, it might be the URL
        if slug and (slug.startswith("http") or len(slug) == 11):
            url = slug
            slug = "default"
        else:
            print("Error: Missing URL.")
            sys.exit(1)

    # Identify styles.css location (it's in the same dir as the script normally)
    pkg_dir = os.path.dirname(os.path.abspath(__file__))
    # styles.css might be in the root of the repo if running from source, 
    # or installed with the package.
    styles_css = os.path.join(pkg_dir, "styles.css")
    if not os.path.exists(styles_css):
        # Fallback to root dir if running from src/tube2txt
        styles_css = os.path.join(os.path.dirname(os.path.dirname(pkg_dir)), "styles.css")

    # Playlist detection
    if "playlist?list=" in url or "&list=" in url:
        print(f"Playlist detected: {url}")
        playlist_videos = Downloader.get_playlist_videos(url)
        artifact_paths = []
        for vid_id, vid_title in playlist_videos:
            clean_title = re.sub(r'[^a-zA-Z0-9]', '_', vid_title)[:50]
            v_url = f"https://www.youtube.com/watch?v={vid_id}"
            path = process_video_logic(v_url, clean_title, args.mode, args.ai, args.db, args.parallel, args.projects_dir, styles_css)
            if path: artifact_paths.append(path)
    else:
        path = process_video_logic(url, slug, args.mode, args.ai, args.db, args.parallel, args.projects_dir, styles_css)
        artifact_paths = [path] if path else []

    if artifact_paths:
        print("\n--- GENERATED ARTIFACTS ---")
        for p in artifact_paths:
            print(f"Project: {os.path.abspath(p)}")
            for f in glob.glob(os.path.join(p, "*")):
                if os.path.isfile(f):
                    print(f"  - {os.path.abspath(f)}")
            if os.path.exists(os.path.join(p, "images")):
                print(f"  - {os.path.abspath(os.path.join(p, 'images'))}/")
            if os.path.exists(os.path.join(p, "clips")):
                print(f"  - {os.path.abspath(os.path.join(p, 'clips'))}/")

if __name__ == "__main__":
    main()
