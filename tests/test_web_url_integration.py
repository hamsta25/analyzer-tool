"""
tests/test_web_url_integration.py -- Integration tests that require real network access.

These tests make live HTTP/yt-dlp calls. They are marked with @pytest.mark.integration
and are excluded from the default (offline) CI run.

Run them explicitly:
    pytest tests/test_web_url_integration.py -v -m integration

Environment requirements:
    - pip install yt-dlp
    - Internet access to the selected URL host

Default acceptance URL (short public sample):
    https://samplelib.com/lib/preview/mp4/sample-5s.mp4

You can override with:
    ANALYZER_TEST_VIDEO_URL="https://..."

Acceptance is executed against TEST_VIDEO_URL (env-overridable).
"""

import os
import sys
from pathlib import Path

import pytest

# Make src/ importable
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

TEST_VIDEO_URL = os.getenv(
    "ANALYZER_TEST_VIDEO_URL",
    "https://samplelib.com/lib/preview/mp4/sample-5s.mp4",
)

# ---------------------------------------------------------------------------
# Marks
# ---------------------------------------------------------------------------

integration = pytest.mark.integration


# ---------------------------------------------------------------------------
# url_resolver integration
# ---------------------------------------------------------------------------


@integration
def test_web_video_download_produces_file():
    """
    DownloadedFile must download the selected test video URL to a temp path.
    The file must be non-empty and removed after the context exits.
    """
    from url_resolver import DownloadedFile

    captured_path = None

    with DownloadedFile(TEST_VIDEO_URL) as path:
        captured_path = path
        assert path.exists(), f"Downloaded file does not exist: {path}"
        size = path.stat().st_size
        assert size > 0, f"Downloaded file is empty: {path}"
        print(f"\n[integration] Downloaded {size / 1024:.1f} KB to {path}")

    # Temp directory must be cleaned up after context exit
    assert not captured_path.exists(), "Temp file was not removed after context exit"


# ---------------------------------------------------------------------------
# Full pipeline integration: url -> transcribe -> markdown
# ---------------------------------------------------------------------------


@integration
def test_web_video_transcription_produces_markdown(tmp_path):
    """
    End-to-end: download test video URL and transcribe with Whisper.
    The output markdown file must exist and contain a non-empty ## Transcript section.
    """
    from url_resolver import DownloadedFile

    try:
        from video_transcriber import transcribe
    except ImportError:
        pytest.skip("openai-whisper not installed")

    out_dir = tmp_path / "out"
    out_dir.mkdir()

    with DownloadedFile(TEST_VIDEO_URL) as video_path:
        transcribe(video_path, model_name="base", output_dir=out_dir)

    # Find the generated markdown file
    md_files = list(out_dir.glob("*_transcript.md"))
    assert md_files, f"No transcript markdown file found in {out_dir}"

    md_file = md_files[0]
    content = md_file.read_text(encoding="utf-8")

    assert "## Transcript" in content, "Markdown missing ## Transcript section"
    # The transcript body should have some non-whitespace text
    transcript_body = content.split("## Transcript", 1)[1]
    assert transcript_body.strip(), "Transcript section is empty"

    print(f"\n[integration] Transcript written to {md_file}")
    print(f"[integration] Transcript excerpt:\n{transcript_body[:300]}")


# ---------------------------------------------------------------------------
# CLI integration: analyzer.py video <url>
# ---------------------------------------------------------------------------


@integration
def test_analyzer_cli_video_url(tmp_path):
    """
    Run ``python src/analyzer.py video <url> --output <tmp>`` as a subprocess.
    The process must exit with code 0 and produce a *_transcript.md file.
    """
    import subprocess

    repo_root = Path(__file__).parent.parent
    analyzer = repo_root / "src" / "analyzer.py"
    out_dir = tmp_path / "cli_out"

    result = subprocess.run(
        [sys.executable, str(analyzer), "video", TEST_VIDEO_URL,
         "--output", str(out_dir)],
        capture_output=True,
        text=True,
        cwd=str(repo_root / "src"),
    )

    print("\n[integration] stdout:\n", result.stdout[-2000:])
    if result.returncode != 0:
        print("[integration] stderr:\n", result.stderr[-2000:])

    assert result.returncode == 0, (
        f"analyzer.py exited with code {result.returncode}\n"
        f"stderr: {result.stderr[-1000:]}"
    )

    md_files = list(out_dir.glob("*_transcript.md"))
    assert md_files, f"No transcript markdown file produced in {out_dir}"

    content = md_files[0].read_text(encoding="utf-8")
    assert "## Transcript" in content
    print(f"[integration] CLI test passed. Output: {md_files[0]}")
