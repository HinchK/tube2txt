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
Source: <a href="{{self.video_url}}" target="_blank">{{self.video_url}}</a>
<ul>
"""
        for seg in self.segments:
            ts_filename = seg['start'].replace(':', '-').replace('.', '-')
            html_content += f"""<li>
    <div class="grab"><img src="images/{{ts_filename}}.jpg" /></div>
    <div class="subtitle">
        <span id="{{seg['start']}}">{{seg['text']}}</span>
        <a href="{{self.video_url}}&t={{seg['seconds']}}" target="_blank" class="videolink">#</a>
    </div>
</li>
"""
        html_content += """
</ul>
</body>
</html>"""
        # Note: Using .format style for the f-string was tricky with nested braces, 
        # let's use standard replacement for the template part.
        
        # Actually, let's just use a clean string substitution or a simple f-string correctly.
        # The previous version had nested braces from the HTML/CSS which is why it was tricky.
        
        # Rewriting to be safer:
        header = f"""<html>
<head>
 <link rel="stylesheet" type="text/css" href="styles.css" />
 </head>
<body>
<h1>Youtube transcript: {self.slug}</h1>
Source: <a href="{self.video_url}" target="_blank">{self.video_url}</a>
<ul>
"""
        body = ""
        for seg in self.segments:
            ts_filename = seg['start'].replace(':', '-').replace('.', '-')
            body += f"""<li>
    <div class="grab"><img src="images/{ts_filename}.jpg" /></div>
    <div class="subtitle">
        <span id="{seg['start']}">{seg['text']}</span>
        <a href="{self.video_url}&t={seg['seconds']}" target="_blank" class="videolink">#</a>
    </div>
</li>
"""
        footer = """
</ul>
</body>
</html>"""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(header + body + footer)
