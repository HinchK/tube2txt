import os
from tube2txt.parsers import VTTParser

def test_vtt_parser():
    vtt_content = """WEBVTT

00:00:01.000 --> 00:00:03.000
Hello world

00:00:03.500 --> 00:00:06.000
This is a <c>test</c>
of the parser
"""
    vtt_path = "tests/test_temp.vtt"
    with open(vtt_path, "w", encoding="utf-8") as f:
        f.write(vtt_content)
    
    try:
        parser = VTTParser(vtt_path)
        segments = parser.parse()
        
        assert len(segments) == 2
        assert segments[0]["start"] == "00:00:01.000"
        assert segments[0]["text"] == "Hello world"
        assert segments[0]["seconds"] == 1
        
        assert segments[1]["start"] == "00:00:03.500"
        assert segments[1]["text"] == "This is a test of the parser"
        assert segments[1]["seconds"] == 3
    finally:
        if os.path.exists(vtt_path):
            os.remove(vtt_path)

def test_to_seconds():
    parser = VTTParser("dummy")
    assert parser.to_seconds("00:00:01.000") == 1
    assert parser.to_seconds("00:01:00.000") == 60
    assert parser.to_seconds("01:00:00.000") == 3600
    assert parser.to_seconds("01:01:01.500") == 3661
