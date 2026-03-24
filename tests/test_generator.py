import os
from tube2txt.generator import HTMLGenerator

def test_html_generator():
    segments = [
        {"start": "00:00:01.000", "seconds": 1, "text": "Hello"},
        {"start": "00:00:05.000", "seconds": 5, "text": "World"}
    ]
    output_path = "tests/test.html"
    if os.path.exists(output_path):
        os.remove(output_path)
        
    try:
        gen = HTMLGenerator(segments, "http://example.com", "test-slug")
        gen.generate(output_path)
        
        assert os.path.exists(output_path)
        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()
            assert "<h1>Youtube transcript: test-slug</h1>" in content
            assert 'href="http://example.com" target="_blank">http://example.com</a>' in content
            assert "Hello" in content
            assert "World" in content
            assert 'id="00:00:01.000"' in content
            assert 'href="http://example.com&t=1"' in content
    finally:
        if os.path.exists(output_path):
            os.remove(output_path)
