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


def test_extract_images_calls_ffmpeg_in_parallel():
    """extract_images should call ffmpeg for each segment in parallel."""
    from tube2txt import extract_images

    segments = [
        {"start": "00:00:01.000", "text": "hello"},
        {"start": "00:00:05.000", "text": "world"},
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        video_path = os.path.join(tmpdir, "video.webm")
        open(video_path, "w").close()
        images_dir = os.path.join(tmpdir, "images")

        call_count = 0
        def mock_run(cmd, **kwargs):
            nonlocal call_count
            call_count += 1
            # Create the output image file
            for i, arg in enumerate(cmd):
                if arg.endswith(".jpg"):
                    open(arg, "w").close()
                    break
            return MagicMock(returncode=0)

        with patch("subprocess.run", side_effect=mock_run):
            extract_images(video_path, segments, images_dir, parallel=2)
            assert call_count == 2
            assert os.path.exists(images_dir)


def test_process_video_calls_on_progress():
    """process_video should call on_progress at each step when provided."""
    from tube2txt import process_video

    progress_calls = []
    def on_progress(type_, step, message):
        progress_calls.append((type_, step, message))

    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = os.path.join(tmpdir, "test-slug")
        db_path = os.path.join(tmpdir, "test.db")

        # Create a fake VTT so parsing works
        os.makedirs(project_path, exist_ok=True)
        vtt_path = os.path.join(project_path, "video.en.vtt")
        with open(vtt_path, "w") as f:
            f.write("WEBVTT\n\n00:00:01.000 --> 00:00:03.000\nHello world\n")

        video_path = os.path.join(project_path, "video.webm")
        open(video_path, "w").close()

        with patch("tube2txt.download_video", return_value=(video_path, vtt_path)):
            with patch("tube2txt.extract_images"):
                with patch("tube2txt.GeminiClient") as mock_gc:
                    process_video(
                        url="https://youtube.com/watch?v=test",
                        slug="test-slug",
                        mode="outline",
                        ai_flag=False,
                        db_path=db_path,
                        project_path=project_path,
                        on_progress=on_progress,
                    )

        steps = [c[1] for c in progress_calls]
        assert "download" in steps
        assert "parse" in steps
        assert "html" in steps
        assert "index" in steps
        assert "images" in steps

        # Verify complete message sent
        types = [c[0] for c in progress_calls]
        assert "complete" in types


def test_process_video_works_without_callback():
    """process_video should work with on_progress=None (CLI mode)."""
    from tube2txt import process_video

    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = os.path.join(tmpdir, "test-slug")
        db_path = os.path.join(tmpdir, "test.db")

        os.makedirs(project_path, exist_ok=True)
        vtt_path = os.path.join(project_path, "video.en.vtt")
        with open(vtt_path, "w") as f:
            f.write("WEBVTT\n\n00:00:01.000 --> 00:00:03.000\nHello world\n")

        video_path = os.path.join(project_path, "video.webm")
        open(video_path, "w").close()

        with patch("tube2txt.download_video", return_value=(video_path, vtt_path)):
            with patch("tube2txt.extract_images"):
                result = process_video(
                    url="https://youtube.com/watch?v=test",
                    slug="test-slug",
                    mode="outline",
                    ai_flag=False,
                    db_path=db_path,
                    project_path=project_path,
                )
        assert result == project_path
