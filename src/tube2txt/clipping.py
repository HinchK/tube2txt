import subprocess

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
