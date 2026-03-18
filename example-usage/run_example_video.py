"""
run_example_video.py -- Transcribe test-video.mp4 with Whisper tiny model.

Run from the repo root:
    python example-usage/run_example_video.py

Requires:
  - test-video.mp4 (generate with: python example-usage/generate_examples.py)
  - FFmpeg (winget install Gyan.FFmpeg)
  - openai-whisper (pip install openai-whisper)
  - The tiny model (~75 MB) is downloaded automatically on first run.
"""

import sys
from pathlib import Path

HERE = Path(__file__).parent
VIDEO = HERE / "test-video.mp4"

# Add src/ to path so we can import the transcriber directly
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def main() -> None:
    if not VIDEO.exists():
        sys.exit(
            f"test-video.mp4 not found at {VIDEO}\n"
            "Run first: python example-usage/generate_examples.py"
        )

    from video_transcriber import transcribe

    out_dir = HERE / "out"
    print(f"Transcribing: {VIDEO}")
    print("Model: tiny  (downloads ~75 MB on first run)")
    print("-" * 40)
    transcribe(VIDEO, model_name="tiny", output_dir=out_dir)
    transcript_file = out_dir / (VIDEO.stem + "_transcript.md")
    if transcript_file.exists():
        print("-" * 40)
        print(transcript_file.read_text(encoding="utf-8"))
        print("[OK] Transcription complete.")
    else:
        print("[WARN] Transcript file not found -- check FFmpeg/Whisper installation.")


if __name__ == "__main__":
    main()
