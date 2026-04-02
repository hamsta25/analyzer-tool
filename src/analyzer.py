"""
analyzer.py — Unified CLI entry point for the analyzer-tool.

Usage:
    python src/analyzer.py pdf   path/to/file.pdf [--ocr-all] [--output out/]
    python src/analyzer.py video path/to/video.mkv [--model base] [--output out/]
    python src/analyzer.py search "query" [--n 5] [--output out/]
    python src/analyzer.py all   path/to/dir/ [--model base] [--output out/]

The `all` mode scans a directory for PDFs and video files, processes them all,
and generates a summary index in out/index.md.
"""

import argparse
import sys
from pathlib import Path

VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".m4a", ".mp3", ".wav", ".flac"}


def cmd_pdf(args: argparse.Namespace) -> None:
    from pdf_analyzer import process_path
    from url_resolver import is_url, DownloadedFile

    if is_url(args.input):
        print(f"[URL] Downloading PDF: {args.input}")
        with DownloadedFile(args.input) as tmp_path:
            process_path(
                tmp_path,
                Path(args.output),
                args.ocr_all,
                ocr_engine=args.ocr_engine,
                ocr_lang=args.ocr_lang,
                tesseract_psm=args.tesseract_psm,
            )
    else:
        process_path(
            Path(args.input),
            Path(args.output),
            args.ocr_all,
            ocr_engine=args.ocr_engine,
            ocr_lang=args.ocr_lang,
            tesseract_psm=args.tesseract_psm,
        )


def cmd_video(args: argparse.Namespace) -> None:
    from video_transcriber import transcribe
    from url_resolver import is_url, DownloadedFile

    if is_url(args.input):
        print(f"[URL] Downloading video: {args.input}")
        with DownloadedFile(args.input) as tmp_path:
            transcribe(tmp_path, args.model, Path(args.output))
    else:
        transcribe(Path(args.input), args.model, Path(args.output))


def cmd_search(args: argparse.Namespace) -> None:
    from web_search import search, results_to_markdown
    import re

    results = search(args.query, args.n)
    markdown = results_to_markdown(args.query, results)

    if args.output:
        out_dir = Path(args.output)
        out_dir.mkdir(parents=True, exist_ok=True)
        slug = re.sub(r"[^\w]+", "_", args.query)[:50]
        out_file = out_dir / f"search_{slug}.md"
        out_file.write_text(markdown, encoding="utf-8")
        print(f"->→ {out_file}")
    else:
        print(markdown)


def cmd_all(args: argparse.Namespace) -> None:
    from pdf_analyzer import process_path
    from video_transcriber import transcribe

    base = Path(args.input)
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    processed: list[str] = []

    # PDFs
    pdfs = list(base.rglob("*.pdf"))
    for pdf in pdfs:
        print(f"->[PDF] {pdf}")
        process_path(
            pdf,
            out_dir,
            ocr_all=False,
            ocr_engine="auto",
            ocr_lang="eng",
            tesseract_psm=6,
        )
        processed.append(f"- PDF: `{pdf.name}` → `{pdf.stem}.md`")

    # Videos
    videos = [f for f in base.rglob("*") if f.suffix.lower() in VIDEO_EXTENSIONS]
    for vid in videos:
        print(f"->[VIDEO] {vid}")
        transcribe(vid, args.model, out_dir)
        processed.append(f"- Video: `{vid.name}` → `{vid.stem}_transcript.md`")

    # Summary index
    index_lines = [
        "# Analyzer Output Index\n",
        f"_Source directory: `{base}`_\n",
        "\n## Processed Files\n",
    ] + processed

    index_file = out_dir / "index.md"
    index_file.write_text("\n".join(index_lines), encoding="utf-8")
    print(f"->\n→ Index written to {index_file}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyzer-tool: PDF extraction, video transcription, web search."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # pdf
    p_pdf = sub.add_parser("pdf", help="Extract text from a PDF file or directory")
    p_pdf.add_argument("input", help="PDF file or directory")
    p_pdf.add_argument("--ocr-all", action="store_true", help="Force OCR on all pages")
    p_pdf.add_argument(
        "--ocr-engine",
        choices=["auto", "tesseract", "ocrmypdf"],
        default="auto",
        help="OCR engine strategy (default: auto)",
    )
    p_pdf.add_argument(
        "--ocr-lang",
        default="eng",
        help="Tesseract language(s), e.g. eng or ita+eng",
    )
    p_pdf.add_argument(
        "--tesseract-psm",
        type=int,
        default=6,
        help="Tesseract page segmentation mode (default: 6)",
    )
    p_pdf.add_argument("--output", default="out", help="Output directory (default: out/)")

    # video
    p_vid = sub.add_parser("video", help="Transcribe a video or audio file")
    p_vid.add_argument("input", help="Video or audio file path")
    p_vid.add_argument("--model", default="base",
                       choices=["tiny", "base", "small", "medium", "large"])
    p_vid.add_argument("--output", default="out", help="Output directory (default: out/)")

    # search
    p_srch = sub.add_parser("search", help="DuckDuckGo web search")
    p_srch.add_argument("query", help="Search query")
    p_srch.add_argument("--n", type=int, default=5, help="Number of results (default: 5)")
    p_srch.add_argument("--output", default=None, help="Output directory (stdout if omitted)")

    # all
    p_all = sub.add_parser("all", help="Process all PDFs and videos in a directory")
    p_all.add_argument("input", help="Source directory")
    p_all.add_argument("--model", default="base",
                       choices=["tiny", "base", "small", "medium", "large"])
    p_all.add_argument("--output", default="out", help="Output directory (default: out/)")

    args = parser.parse_args()
    dispatch = {"pdf": cmd_pdf, "video": cmd_video, "search": cmd_search, "all": cmd_all}
    dispatch[args.command](args)


if __name__ == "__main__":
    # Allow running from repo root: python src/analyzer.py …
    sys.path.insert(0, str(Path(__file__).parent))
    main()
