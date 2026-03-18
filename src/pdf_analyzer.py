"""
pdf_analyzer.py — Extract text from PDFs (digital + OCR for handwritten/scanned pages).

Usage:
    python src/pdf_analyzer.py path/to/file.pdf [--ocr-all] [--output out/]
    python src/pdf_analyzer.py path/to/dir/ [--ocr-all] [--output out/]
"""

import argparse
import re
import sys
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    sys.exit("PyMuPDF not found. Run: pip install PyMuPDF>=1.24")

try:
    import pytesseract
    from PIL import Image
    import io
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

SPARSE_THRESHOLD = 80  # characters per page below which OCR is attempted


def _ocr_page(page: "fitz.Page") -> str:
    """Render a page to image and run Tesseract OCR on it."""
    if not TESSERACT_AVAILABLE:
        return (
            "[OCR unavailable] Install pytesseract + Pillow and Tesseract engine:\n"
            "  Windows: https://github.com/UB-Mannheim/tesseract/wiki\n"
            "  Linux:   sudo apt install tesseract-ocr\n"
            "  Then:    pip install pytesseract pillow\n"
        )
    mat = fitz.Matrix(2, 2)  # 2x zoom for better OCR quality
    pix = page.get_pixmap(matrix=mat)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    return pytesseract.image_to_string(img)


def analyze_pdf(path: Path, ocr_all: bool = False) -> str:
    """Return extracted markdown text from a PDF file."""
    doc = fitz.open(str(path))
    lines = [f"# {path.name}\n"]

    for i, page in enumerate(doc, start=1):
        text = page.get_text().strip()
        use_ocr = ocr_all or len(text) < SPARSE_THRESHOLD

        lines.append(f"\n## Page {i}\n")
        if use_ocr and not ocr_all:
            lines.append(f"_[sparse page — {len(text)} chars — attempting OCR]_\n")

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
        print(f"  → {out_file}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract text from PDF files.")
    parser.add_argument("input", help="PDF file or directory")
    parser.add_argument("--ocr-all", action="store_true", help="Force OCR on all pages")
    parser.add_argument("--output", default="out", help="Output directory (default: out/)")
    args = parser.parse_args()

    process_path(Path(args.input), Path(args.output), args.ocr_all)


if __name__ == "__main__":
    main()
