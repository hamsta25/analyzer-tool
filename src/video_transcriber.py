"""
video_transcriber.py — Transcribe video/audio files using OpenAI Whisper (fully offline).

Usage:
    python src/video_transcriber.py path/to/video.mkv [--model base] [--output out/]
"""

import argparse
import shutil
import sys
from pathlib import Path


def _check_ffmpeg() -> None:
    if shutil.which("ffmpeg") is None:
        sys.exit(
            "ffmpeg not found. Install it before transcribing:\n"
            "  Windows (winget): winget install Gyan.FFmpeg\n"
            "  Windows (choco):  choco install ffmpeg\n"
            "  Linux:            sudo apt install ffmpeg\n"
            "  macOS:            brew install ffmpeg\n"
        )


def transcribe(input_path: Path, model_name: str, output_dir: Path) -> None:
    """Transcribe a single audio/video file and write markdown output."""
    _check_ffmpeg()

    try:
        import whisper
    except ImportError:
        sys.exit("openai-whisper not found. Run: pip install openai-whisper")

    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading Whisper model '{model_name}' (downloads on first use)…")
    model = whisper.load_model(model_name)

    print(f"Transcribing: {input_path}")
    result = model.transcribe(str(input_path), verbose=True)

    lines = [
        f"# Transcription: {input_path.name}\n",
        f"_Model: {model_name}_\n",
        "\n## Transcript\n",
        result["text"].strip(),
        "\n\n## Segments\n",
    ]
    for seg in result.get("segments", []):
        start = _fmt_time(seg["start"])
        end = _fmt_time(seg["end"])
        lines.append(f"- `[{start} → {end}]` {seg['text'].strip()}")

    out_file = output_dir / (input_path.stem + "_transcript.md")
    out_file.write_text("\n".join(lines), encoding="utf-8")
    print(f"  → {out_file}")


def _fmt_time(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Transcribe video/audio with Whisper.")
    parser.add_argument("input", help="Video or audio file path")
    parser.add_argument(
        "--model",
        default="base",
        choices=["tiny", "base", "small", "medium", "large"],
        help="Whisper model size (default: base)",
    )
    parser.add_argument("--output", default="out", help="Output directory (default: out/)")
    args = parser.parse_args()

    transcribe(Path(args.input), args.model, Path(args.output))


if __name__ == "__main__":
    main()
