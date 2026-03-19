"""
pdf_analyzer.py -- Extract text from PDFs (digital + OCR for handwritten/scanned pages).

Usage:
    python src/pdf_analyzer.py path/to/file.pdf [--ocr-all] [--output out/] [--ocr-engine auto]
    python src/pdf_analyzer.py path/to/dir/ [--ocr-all] [--output out/] [--ocr-engine auto]
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

KNOWN_OCRMYPDF_PATHS = [
    r"C:\Program Files\OCRmyPDF\ocrmypdf.exe",
    r"C:\Program Files (x86)\OCRmyPDF\ocrmypdf.exe",
    "/usr/bin/ocrmypdf",
    "/usr/local/bin/ocrmypdf",
]

SPARSE_THRESHOLD = 80  # characters per page below which OCR is attempted
VISUAL_HINT_THRESHOLD = 1  # minimum count of drawings/images to treat page as visual-heavy


def _find_binary(name: str, known_paths: list[str]) -> Optional[str]:
    """Resolve an executable from PATH or known install locations."""
    found = shutil.which(name)
    if found:
        return found
    for p in known_paths:
        if Path(p).is_file():
            return p
    return None


def _find_tesseract() -> Optional[str]:
    """Return path to tesseract executable, or None if not found."""
    return _find_binary("tesseract", KNOWN_TESSERACT_PATHS)


def _find_ocrmypdf() -> Optional[str]:
    """Return path to ocrmypdf executable, or None if not found."""
    return _find_binary("ocrmypdf", KNOWN_OCRMYPDF_PATHS)


def _tesseract_ocr_image(img_path: Path, tesseract_cmd: str, ocr_lang: str, psm: int) -> str:
    """Run tesseract on an image file and return the extracted text."""
    with tempfile.NamedTemporaryFile(suffix='', delete=False) as tf:
        out_stem = tf.name
    try:
        cmd = [
            tesseract_cmd,
            str(img_path),
            out_stem,
            'txt',
            '--oem',
            '1',
            '--psm',
            str(psm),
        ]
        if ocr_lang:
            cmd.extend(['-l', ocr_lang])

        subprocess.run(
            cmd,
            check=True, capture_output=True, timeout=120
        )
        out_file = Path(out_stem + '.txt')
        text = out_file.read_text(encoding='utf-8', errors='replace').strip()
        out_file.unlink(missing_ok=True)
        return text
    except Exception as e:
        return f"[OCR failed: {e}]"


def _preprocess_with_ocrmypdf(pdf_path: Path, ocrmypdf_cmd: str) -> tuple[Optional[Path], str]:
    """Preprocess a PDF with OCRmyPDF and return a temporary searchable PDF path."""
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tf:
        out_pdf = Path(tf.name)

    cmd = [
        ocrmypdf_cmd,
        '--skip-text',
        '--rotate-pages',
        '--deskew',
        '--clean-final',
        '--optimize',
        '0',
        str(pdf_path),
        str(out_pdf),
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=900)
        return out_pdf, "_[OCRmyPDF preprocessing enabled]_"
    except Exception as e:
        out_pdf.unlink(missing_ok=True)
        return None, f"_[OCRmyPDF preprocessing failed: {e}]_"


def _page_visual_stats(page: "fitz.Page") -> tuple[int, int, bool]:
    """Return simple visual complexity statistics for a page."""
    image_count = len(page.get_images(full=True))
    drawing_count = len(page.get_drawings())
    has_visuals = (image_count + drawing_count) >= VISUAL_HINT_THRESHOLD
    return image_count, drawing_count, has_visuals


def _save_page_snapshot(page: "fitz.Page", assets_dir: Path, page_index: int) -> Path:
    """Render and save a page image snapshot to preserve diagrams in markdown output."""
    assets_dir.mkdir(parents=True, exist_ok=True)
    out = assets_dir / f"page_{page_index:03d}.png"
    mat = fitz.Matrix(2, 2)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    out.write_bytes(pix.tobytes("png"))
    return out


def _ocr_page(page: "fitz.Page", tesseract_cmd: str, ocr_lang: str, psm: int) -> str:
    """Render a page to image and run Tesseract OCR via subprocess."""
    mat = fitz.Matrix(2, 2)  # 2x zoom for better OCR quality
    pix = page.get_pixmap(matrix=mat)

    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tf:
        img_path = Path(tf.name)

    try:
        img_path.write_bytes(pix.tobytes("png"))
        return _tesseract_ocr_image(img_path, tesseract_cmd, ocr_lang=ocr_lang, psm=psm)
    finally:
        img_path.unlink(missing_ok=True)


def analyze_pdf(
    path: Path,
    output_dir: Path,
    ocr_all: bool = False,
    ocr_engine: str = "auto",
    ocr_lang: str = "eng",
    tesseract_psm: int = 6,
) -> str:
    """Return extracted markdown text from a PDF file."""
    lines = [f"# {path.name}\n"]

    preprocessed_pdf: Optional[Path] = None
    source_pdf = path

    if ocr_engine in {"auto", "ocrmypdf"}:
        ocrmypdf_cmd = _find_ocrmypdf()
        if ocrmypdf_cmd:
            preprocessed_pdf, note = _preprocess_with_ocrmypdf(path, ocrmypdf_cmd)
            lines.append(note)
            if preprocessed_pdf is not None:
                source_pdf = preprocessed_pdf
        elif ocr_engine == "ocrmypdf":
            lines.append("_[OCRmyPDF not found, falling back to Tesseract]_\n")

    doc = fitz.open(str(source_pdf))
    tesseract_cmd = _find_tesseract()
    assets_dir = output_dir / "assets" / path.stem

    try:
        for i, page in enumerate(doc, start=1):
            text = page.get_text().strip()
            use_ocr = ocr_all or len(text) < SPARSE_THRESHOLD
            image_count, drawing_count, has_visuals = _page_visual_stats(page)

            lines.append(f"\n## Page {i}\n")

            if has_visuals:
                lines.append(
                    f"_[visuals detected: images={image_count}, drawings={drawing_count}]_\n"
                )
                snapshot_path = _save_page_snapshot(page, assets_dir, i)
                rel = snapshot_path.relative_to(output_dir).as_posix()
                lines.append(f"![Page {i} visual snapshot]({rel})\n")

            if use_ocr and not ocr_all:
                lines.append(f"_[sparse page -- {len(text)} chars -- attempting OCR]_\n")

            if use_ocr:
                if tesseract_cmd is None:
                    lines.append(
                        "[OCR unavailable] Tesseract not found. Install it:\n"
                        "  Windows: winget install UB-Mannheim.TesseractOCR\n"
                        "  Linux:   sudo apt install tesseract-ocr\n"
                        "  macOS:   brew install tesseract\n"
                    )
                else:
                    lines.append(_ocr_page(page, tesseract_cmd, ocr_lang=ocr_lang, psm=tesseract_psm))
            else:
                lines.append(text)
    finally:
        doc.close()
        if preprocessed_pdf is not None:
            preprocessed_pdf.unlink(missing_ok=True)

    return "\n".join(lines)


def process_path(
    input_path: Path,
    output_dir: Path,
    ocr_all: bool,
    ocr_engine: str = "auto",
    ocr_lang: str = "eng",
    tesseract_psm: int = 6,
) -> None:
    """Process a single PDF or a directory of PDFs."""
    output_dir.mkdir(parents=True, exist_ok=True)

    pdfs = list(input_path.rglob("*.pdf")) if input_path.is_dir() else [input_path]
    if not pdfs:
        print(f"No PDF files found in {input_path}")
        return

    for pdf in pdfs:
        print(f"Processing: {pdf}")
        content = analyze_pdf(
            pdf,
            output_dir=output_dir,
            ocr_all=ocr_all,
            ocr_engine=ocr_engine,
            ocr_lang=ocr_lang,
            tesseract_psm=tesseract_psm,
        )
        out_file = output_dir / (pdf.stem + ".md")
        out_file.write_text(content, encoding="utf-8")
        print(f"  -> {out_file}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract text from PDF files.")
    parser.add_argument("input", help="PDF file or directory")
    parser.add_argument("--ocr-all", action="store_true", help="Force OCR on all pages")
    parser.add_argument(
        "--ocr-engine",
        choices=["auto", "tesseract", "ocrmypdf"],
        default="auto",
        help="OCR engine strategy (default: auto).",
    )
    parser.add_argument(
        "--ocr-lang",
        default="eng",
        help="Tesseract language(s), e.g. eng or ita+eng (default: eng).",
    )
    parser.add_argument(
        "--tesseract-psm",
        type=int,
        default=6,
        help="Tesseract page segmentation mode (default: 6).",
    )
    parser.add_argument("--output", default="out", help="Output directory (default: out/)")
    args = parser.parse_args()

    process_path(
        Path(args.input),
        Path(args.output),
        args.ocr_all,
        ocr_engine=args.ocr_engine,
        ocr_lang=args.ocr_lang,
        tesseract_psm=args.tesseract_psm,
    )


if __name__ == "__main__":
    main()
