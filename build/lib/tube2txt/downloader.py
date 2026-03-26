import subprocess
import os
import glob

class Downloader:
    @staticmethod
    def get_video_and_subs(url, output_dir):
        """Use yt-dlp to download video and subtitles, and fetch metadata."""
        # Ensure output dir exists
        os.makedirs(output_dir, exist_ok=True)
        
        # We'll run yt-dlp inside the output directory
        # Using --print to get metadata fields in a structured way
        cmd = [
            "yt-dlp",
            "--no-warnings",
            "--write-auto-subs",
            "--write-subs",
            "--no-simulate",
            "--print", "filename",
            "--print", "title",
            "--print", "description",
            "--print", "thumbnail",
            "-o", "video.%(ext)s",
            url
        ]
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True, cwd=output_dir)
            lines = result.stdout.strip().split('\n')
            
            video_file = lines[0] if len(lines) > 0 else None
            metadata = {
                "title": lines[1] if len(lines) > 1 else "Unknown Title",
                "description": lines[2] if len(lines) > 2 else "",
                "thumbnail_url": lines[3] if len(lines) > 3 else ""
            }
            
            # If yt-dlp didn't print the filename as expected, try to find it
            if not video_file or not os.path.exists(os.path.join(output_dir, video_file)):
                files = glob.glob(os.path.join(output_dir, "video.*"))
                if files:
                    video_file = os.path.basename(files[0])
            
            if not video_file:
                return None, None, metadata
            
            # Find VTT file
            vtt_file = None
            vtt_patterns = [
                "video.en.vtt",
                "video.*.vtt",
                "*.vtt"
            ]
            for pattern in vtt_patterns:
                files = glob.glob(os.path.join(output_dir, pattern))
                if files:
                    vtt_file = os.path.basename(files[0])
                    break
            
            return video_file, vtt_file, metadata
        except subprocess.CalledProcessError as e:
            print(f"Error downloading video: {e}")
            return None, None, {}

    @staticmethod
    def get_playlist_videos(url):
        """Get list of (id, title) from a playlist."""
        cmd = [
            "yt-dlp",
            "--quiet",
            "--flat-playlist",
            "--print", "%(id)s",
            "--print", "%(title)s",
            url
        ]
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            output = result.stdout.strip().split('\n')
            videos = []
            for i in range(0, len(output), 2):
                if i + 1 < len(output):
                    videos.append((output[i], output[i+1]))
            return videos
        except subprocess.CalledProcessError as e:
            print(f"Error fetching playlist: {e}")
            return []
