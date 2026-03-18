"""
pdf_analyzer.py -- Extract text from PDFs (digital + OCR for handwritten/scanned pages).

Usage:
    python src/pdf_analyzer.py path/to/file.pdf [--ocr-all] [--output out/]
    python src/pdf_analyzer.py path/to/dir/ [--ocr-all] [--output out/]
"""

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

try:
    import fitz  # PyMuPDF
except ImportError:
    sys.exit("PyMuPDF not found. Run: pip install PyMuPDF>=1.24")

KNOWN_TESSERACT_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    "/usr/bin/tesseract",
    "/usr/local/bin/tesseract",
]

SPARSE_THRESHOLD = 80  # characters per page below which OCR is attempted


def _find_tesseract() -> Optional[str]:
    """Return path to tesseract executable, or None if not found."""
    found = shutil.which("tesseract")
    if found:
        return found
    for p in KNOWN_TESSERACT_PATHS:
        if Path(p).is_file():
            return p
    return None


def _tesseract_ocr_image(img_path: Path, tesseract_cmd: str) -> str:
    """Run tesseract on an image file and return the extracted text."""
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


def _ocr_page(page: "fitz.Page") -> str:
    """Render a page to image and run Tesseract OCR via subprocess."""
    tesseract_cmd = _find_tesseract()
    if tesseract_cmd is None:
        return (
            "[OCR unavailable] Tesseract not found. Install it:\n"
            "  Windows: winget install UB-Mannheim.TesseractOCR\n"
            "  Linux:   sudo apt install tesseract-ocr\n"
            "  macOS:   brew install tesseract\n"
        )

    mat = fitz.Matrix(2, 2)  # 2x zoom for better OCR quality
    pix = page.get_pixmap(matrix=mat)

    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tf:
        img_path = Path(tf.name)

    try:
        img_path.write_bytes(pix.tobytes("png"))
        return _tesseract_ocr_image(img_path, tesseract_cmd)
    finally:
        img_path.unlink(missing_ok=True)


def analyze_pdf(path: Path, ocr_all: bool = False) -> str:
    """Return extracted markdown text from a PDF file."""
    doc = fitz.open(str(path))
    lines = [f"# {path.name}\n"]

    for i, page in enumerate(doc, start=1):
        text = page.get_text().strip()
        use_ocr = ocr_all or len(text) < SPARSE_THRESHOLD

        lines.append(f"\n## Page {i}\n")
        if use_ocr and not ocr_all:
            lines.append(f"_[sparse page -- {len(text)} chars -- attempting OCR]_\n")

        if use_ocr:
            lines.append(_ocr_page(page))
        else:
            lines.append(text)

    doc.close()
    return "\n".join(lines)


def process_path(input_path: Path, output_dir: Path, ocr_all: bool) -> None:
    """Process a single PDF or a directory of PDFs."""
    output_dir.mkdir(parents=True, exist_ok=True)

    pdfs = list(input_path.rglob("*.pdf")) if input_path.is_dir() else [input_path]
    if not pdfs:
        print(f"No PDF files found in {input_path}")
        return

    for pdf in pdfs:
        print(f"Processing: {pdf}")
        content = analyze_pdf(pdf, ocr_all=ocr_all)
        out_file = output_dir / (pdf.stem + ".md")
        out_file.write_text(content, encoding="utf-8")
        print(f"  -> {out_file}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract text from PDF files.")
    parser.add_argument("input", help="PDF file or directory")
    parser.add_argument("--ocr-all", action="store_true", help="Force OCR on all pages")
    parser.add_argument("--output", default="out", help="Output directory (default: out/)")
    args = parser.parse_args()

    process_path(Path(args.input), Path(args.output), args.ocr_all)


if __name__ == "__main__":
    main()
