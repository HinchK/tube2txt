import pytest
from tube2txt import get_video_id, format_vtt_timestamp, fetch_transcript_api

def test_get_video_id():
    # Standard watch URL
    assert get_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    # Shortened URL
    assert get_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    # Embed URL
    assert get_video_id("https://www.youtube.com/embed/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    # Shorts URL
    assert get_video_id("https://www.youtube.com/shorts/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    # Just the ID
    assert get_video_id("dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    # URL with extra parameters
    assert get_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ&feature=shared") == "dQw4w9WgXcQ"
    # Invalid or non-matching
    assert get_video_id("https://google.com") is None
    assert get_video_id("short") is None

def test_format_vtt_timestamp():
    # Zero
    assert format_vtt_timestamp(0) == "00:00:00.000"
    # Only seconds
    assert format_vtt_timestamp(45.5) == "00:00:45.500"
    # Minutes and seconds
    assert format_vtt_timestamp(125.25) == "00:02:05.250"
    # Hours, minutes, and seconds
    assert format_vtt_timestamp(3661.123) == "01:01:01.123"
    # Large value
    assert format_vtt_timestamp(36000.999) == "10:00:00.999"
    # Rounding/Formatting check
    assert format_vtt_timestamp(1.1234) == "00:00:01.123"

def test_fetch_transcript_api_real():
    """Integration test for the real YouTube Transcript API."""
    video_id = "v26QZtUONDI"
    segments = fetch_transcript_api(video_id)
    assert segments is not None
    assert len(segments) > 0
    assert "text" in segments[0]
    assert "start" in segments[0]
