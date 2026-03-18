"""
generate_examples.py -- Generate test assets for the example-usage folder.

Generates:
  - test-image.png  : a simple synthetic image with text "Hello OCR test 123"
  - test-video.mp4  : a tiny 5-second silent blue video (320x240, libx264)

Run from the repo root:
    python example-usage/generate_examples.py
"""

import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent


def generate_image() -> None:
    out = HERE / "test-image.png"
    try:
        from PIL import Image, ImageDraw, ImageFont

        img = Image.new("RGB", (400, 100), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arial.ttf", 36)
        except Exception:
            font = ImageFont.load_default()
        draw.text((20, 25), "Hello OCR test 123", fill=(0, 0, 0), font=font)
        img.save(out)
        print(f"[OK] Generated {out}")
    except ImportError:
        sys.exit("Pillow is required to generate the test image. Run: pip install Pillow")


def generate_video() -> None:
    out = HERE / "test-video.mp4"
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        # Try known WinGet/Chocolatey paths
        candidates = [
            r"C:\Users\Maria\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe",
            r"C:\ProgramData\chocolatey\bin\ffmpeg.exe",
            r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
        ]
        for c in candidates:
            if Path(c).is_file():
                ffmpeg = c
                break
    if ffmpeg is None:
        sys.exit("ffmpeg not found. Install with: winget install Gyan.FFmpeg")

    cmd = [
        ffmpeg, "-y",
        "-f", "lavfi", "-i", "color=c=blue:size=320x240:rate=1",
        "-f", "lavfi", "-i", "anullsrc",
        "-t", "5",
        "-c:v", "libx264",
        "-c:a", "aac",
        str(out),
    ]
    subprocess.run(cmd, check=True)
    print(f"[OK] Generated {out}")


if __name__ == "__main__":
    generate_image()
    generate_video()
