import os
import re
import sys
import json
import argparse
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
from google import genai
from google.genai import types

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

class GeminiClient:
    def __init__(self, api_key):
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required.")
        self.client = genai.Client(api_key=api_key)

    def generate_outline(self, segments):
        full_transcript = "\n".join([f"[{s['start']}] {s['text']}" for s in segments])
        prompt = f"""
I have a transcript of a YouTube video. Please provide a clear, high-level markdown outline of the content.
Include timestamps in brackets [HH:MM:SS] for each section. Use the timestamps from the transcript provided.

Transcript:
{full_transcript}
"""
        response = self.client.models.generate_content(
            model='gemini-3-flash-preview',
            contents=prompt
        )
        return response.text

def main():
    parser = argparse.ArgumentParser(description="Tube2Txt Python Logic")
    parser.add_argument("--vtt", required=True, help="Path to VTT file")
    parser.add_argument("--url", required=True, help="YouTube video URL")
    parser.add_argument("--slug", required=True, help="Project slug")
    parser.add_argument("--output-html", required=True, help="Path to output HTML")
    parser.add_argument("--output-outline", required=True, help="Path to output markdown outline")
    parser.add_argument("--ai", action="store_true", help="Run AI outline generation")
    
    args = parser.parse_args()

    vtt_parser = VTTParser(args.vtt)
    segments = vtt_parser.parse()

    html_gen = HTMLGenerator(segments, args.url, args.slug)
    html_gen.generate(args.output_html)

    if args.ai:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("Warning: GEMINI_API_KEY not found. Skipping outline generation.")
        else:
            client = GeminiClient(api_key)
            outline = client.generate_outline(segments)
            with open(args.output_outline, 'w', encoding='utf-8') as f:
                f.write(outline)
            print(f"Outline generated at {args.output_outline}")

    # Output timestamps for Bash to use for image extraction
    for seg in segments:
        print(f"TIMESTAMP:{seg['start']}")

if __name__ == "__main__":
    main()
