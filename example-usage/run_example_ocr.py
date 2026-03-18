"""
run_example_ocr.py -- Run Tesseract OCR on test-image.png and print the result.

Run from the repo root:
    python example-usage/run_example_ocr.py

Requires:
  - test-image.png (generate with: python example-usage/generate_examples.py)
  - Tesseract OCR installed (winget install UB-Mannheim.TesseractOCR)
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).parent
IMG = HERE / "test-image.png"

KNOWN_TESSERACT_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    "/usr/bin/tesseract",
    "/usr/local/bin/tesseract",
]


def find_tesseract():
    found = shutil.which("tesseract")
    if found:
        return found
    for p in KNOWN_TESSERACT_PATHS:
        if Path(p).is_file():
            return p
    return None


def run_ocr(img_path: Path, tesseract_cmd: str) -> str:
    with tempfile.NamedTemporaryFile(suffix='', delete=False) as tf:
        out_stem = tf.name
    try:
        subprocess.run(
            [tesseract_cmd, str(img_path), out_stem, 'txt'],
            check=True, capture_output=True, timeout=120
        )
        out_file = Path(out_stem + '.txt')
        text = out_file.read_text(encoding='utf-8', errors='replace').strip()
        out_file.unlink(missing_ok=True)
        return text
    except Exception as e:
        return f"[OCR failed: {e}]"


def main() -> None:
    if not IMG.exists():
        sys.exit(
            f"test-image.png not found at {IMG}\n"
            "Run first: python example-usage/generate_examples.py"
        )

    tesseract = find_tesseract()
    if tesseract is None:
        sys.exit(
            "Tesseract not found. Install it:\n"
            "  Windows: winget install UB-Mannheim.TesseractOCR\n"
            "  Linux:   sudo apt install tesseract-ocr\n"
            "  macOS:   brew install tesseract"
        )

    print(f"Using Tesseract: {tesseract}")
    print(f"Running OCR on: {IMG}")
    print("-" * 40)
    text = run_ocr(IMG, tesseract)
    print(text)
    print("-" * 40)
    if "Hello" in text or "OCR" in text or "123" in text:
        print("[OK] OCR is working correctly.")
    else:
        print("[WARN] Expected text not found -- check Tesseract installation.")


if __name__ == "__main__":
    main()
