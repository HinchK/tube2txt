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

    def generate_content(self, segments, mode='outline'):
        full_transcript = "\n".join([f"[{s['start']}] {s['text']}" for s in segments])
        
        prompts = {
            'outline': "Provide a clear, high-level markdown outline of the content. Include timestamps in brackets [HH:MM:SS] for each section.",
            'notes': "Create detailed study notes from this transcript. Include key takeaways, definitions of any complex terms, and a summary for each major section. Use timestamps in brackets [HH:MM:SS].",
            'recipe': "Extract any recipes, ingredients, and cooking steps from this transcript. Format them clearly in markdown with timestamps [HH:MM:SS].",
            'technical': "Provide a technical deep-dive or documentation based on this transcript. Focus on implementation details, code concepts, and architectural points. Use timestamps in brackets [HH:MM:SS]."
        }
        
        system_prompt = prompts.get(mode, prompts['outline'])
        prompt = f"""
I have a transcript of a YouTube video. {system_prompt}

Transcript:
{full_transcript}
"""
        response = self.client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt
        )
        return response.text

def main():
    parser = argparse.ArgumentParser(description="Tube2Txt Python Logic")
    parser.add_argument("--vtt", help="Path to VTT file")
    parser.add_argument("--url", help="YouTube video URL")
    parser.add_argument("--slug", help="Project slug")
    parser.add_argument("--output-html", help="Path to output HTML")
    parser.add_argument("--output-outline", help="Path to output markdown content")
    parser.add_argument("--mode", default="outline", choices=["outline", "notes", "recipe", "technical"], help="AI mode")
    parser.add_argument("--ai", action="store_true", help="Run AI generation")
    
    args = parser.parse_args()

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

    # Note: VTT file will be handled by Bash script, but if we're running standalone
    # we might need to wait for it or ensure it exists.
    if args.vtt:
        vtt_parser = VTTParser(args.vtt)
        segments = vtt_parser.parse()

        html_gen = HTMLGenerator(segments, args.url, args.slug)
        html_gen.generate(args.output_html)

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

        # Output timestamps for Bash to use for image extraction
        for seg in segments:
            print(f"TIMESTAMP:{seg['start']}")

if __name__ == "__main__":
    main()
