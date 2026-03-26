import os
import re
import sys
import argparse
import glob
import shutil
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
    video_file, vtt_file, metadata = Downloader.get_video_and_subs(url, project_path)
    
    if not video_file or not vtt_file:
        print(f"Error: Could not download video or subtitles for {slug}.")
        return None

    # Parse & Generate HTML
    print("Generating HTML and processing transcript...")
    vtt_path = os.path.join(project_path, vtt_file)
    parser = VTTParser(vtt_path)
    segments = parser.parse()
    
    # Use real title if available for HTML
    display_title = metadata.get("title", slug)
    html_gen = HTMLGenerator(segments, url, display_title)
    html_gen.generate(os.path.join(project_path, "index.html"))
    
    # DB Indexing
    db = Database(db_path)
    db.index_video(slug, url, segments, metadata=metadata)
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

def download_video(url, output_dir):
    """Download video and subtitles using yt-dlp. Returns (video_file, vtt_file) or (None, None)."""
    os.makedirs(output_dir, exist_ok=True)
    cmd = [
        "yt-dlp", "--no-warnings",
        "--write-auto-subs", "--write-subs",
        "-o", os.path.join(output_dir, "video.%(ext)s"),
        url
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except Exception as e:
        print(f"Error downloading: {e}")
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
    video_file, vtt_file = download_video(url, project_path)
    if not video_file or not vtt_file:
        _notify(on_progress, "error", "download", f"Failed to download video or subtitles for {slug}")
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


def main():
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
