import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock

def test_download_video_calls_ytdlp():
    """download_video should call yt-dlp and return (video_file, vtt_file)."""
    from tube2txt import download_video

    with tempfile.TemporaryDirectory() as tmpdir:
        mock_result = MagicMock()
        mock_result.returncode = 0

        # Simulate yt-dlp creating files
        def side_effect(*args, **kwargs):
            open(os.path.join(tmpdir, "video.webm"), "w").close()
            open(os.path.join(tmpdir, "video.en.vtt"), "w").close()
            return mock_result

        with patch("subprocess.run", side_effect=side_effect):
            video, vtt = download_video("https://youtube.com/watch?v=test", tmpdir)
            assert video is not None
            assert vtt is not None
            assert vtt.endswith(".vtt")


def test_download_video_returns_none_on_failure():
    """download_video should return (None, None) if yt-dlp fails."""
    from tube2txt import download_video

    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("subprocess.run", side_effect=Exception("yt-dlp not found")):
            video, vtt = download_video("https://youtube.com/watch?v=test", tmpdir)
            assert video is None
            assert vtt is None
