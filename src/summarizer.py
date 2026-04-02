"""
summarizer.py -- Build quality-checked summaries from text, PDF, and media inputs.

This module performs a pre-summary validation flow:
1. Basic text sanity and spelling checks
2. Claim extraction and optional web-backed fact-check hints
3. Extractive summary generation focused on semantic continuity
4. Post-summary coherence scoring

Usage:
    python src/summarizer.py input-file-or-url [--output out/] [--max-sentences 8]
"""

import argparse
import re
import statistics
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from url_resolver import DownloadedFile, is_url
from web_search import search

VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".m4a", ".mp3", ".wav", ".flac"}
TEXT_EXTENSIONS = {".md", ".txt", ".rst", ".log"}

STOPWORDS = {
    "the", "and", "for", "that", "this", "with", "from", "have", "has", "are", "was", "were", "will",
    "can", "you", "your", "about", "into", "over", "then", "than", "also", "they", "them", "their",
    "una", "uno", "dei", "delle", "della", "dello", "con", "per", "che", "come", "sono", "alla", "allo",
    "dopo", "prima", "nelle", "negli", "dati", "testo", "file", "from", "into", "using",
}


def _read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _strip_markdown(text: str) -> str:
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"`[^`]+`", " ", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


def _split_sentences(text: str) -> list[str]:
    chunks = re.split(r"(?<=[.!?])\s+", text)
    return [c.strip() for c in chunks if c and c.strip()]


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ']+", text.lower())


def _content_tokens(text: str) -> list[str]:
    return [t for t in _tokenize(text) if len(t) > 2 and t not in STOPWORDS]


def _sentence_score(sentence: str, freq: Counter[str]) -> float:
    tokens = _content_tokens(sentence)
    if not tokens:
        return 0.0
    return sum(freq[t] for t in tokens) / len(tokens)


def _extractive_summary(text: str, max_sentences: int) -> str:
    sentences = _split_sentences(text)
    if not sentences:
        return ""
    if len(sentences) <= max_sentences:
        return " ".join(sentences)

    freq = Counter(_content_tokens(text))
    ranked: list[tuple[int, float]] = []
    for i, sentence in enumerate(sentences):
        score = _sentence_score(sentence, freq)
        if i == 0:
            score += 0.05
        ranked.append((i, score))

    selected = sorted(ranked, key=lambda p: p[1], reverse=True)[:max_sentences]
    indices = sorted(idx for idx, _ in selected)
    return " ".join(sentences[i] for i in indices)


def _coherence_score(original: str, summary: str) -> float:
    a = set(_content_tokens(original))
    b = set(_content_tokens(summary))
    if not a or not b:
        return 0.0
    return round(len(a.intersection(b)) / len(a.union(b)), 3)


def _logical_checks(text: str) -> dict[str, Any]:
    sentences = _split_sentences(text)
    if not sentences:
        return {
            "sentence_count": 0,
            "avg_sentence_words": 0.0,
            "duplicate_sentence_ratio": 0.0,
            "status": "warn",
            "notes": ["No sentence detected in input text."],
        }

    sentence_lengths = [len(_content_tokens(s)) for s in sentences]
    avg_len = statistics.mean(sentence_lengths) if sentence_lengths else 0.0
    unique = len(set(s.lower() for s in sentences))
    duplicate_ratio = 0.0 if not sentences else round(1 - (unique / len(sentences)), 3)

    notes: list[str] = []
    status = "ok"
    if avg_len < 5:
        status = "warn"
        notes.append("Average sentence content is very short; summary quality may be unstable.")
    if duplicate_ratio > 0.2:
        status = "warn"
        notes.append("High duplicate sentence ratio detected in source text.")

    return {
        "sentence_count": len(sentences),
        "avg_sentence_words": round(avg_len, 2),
        "duplicate_sentence_ratio": duplicate_ratio,
        "status": status,
        "notes": notes,
    }


def _spelling_checks(text: str, max_items: int = 20) -> dict[str, Any]:
    try:
        from spellchecker import SpellChecker
    except Exception:
        return {
            "enabled": False,
            "error_count": 0,
            "suggestions": [],
            "note": "pyspellchecker not installed; spelling check skipped.",
        }

    words = [w for w in re.findall(r"\b[A-Za-zÀ-ÖØ-öø-ÿ']{4,}\b", text) if w.isalpha()]
    spell = SpellChecker()
    unknown = sorted(spell.unknown([w.lower() for w in words]))
    suggestions = []
    for w in unknown[:max_items]:
        cand = spell.correction(w)
        suggestions.append({"word": w, "suggestion": cand or "(none)"})

    return {
        "enabled": True,
        "error_count": len(unknown),
        "suggestions": suggestions,
        "note": "",
    }


def _extract_claims(text: str, max_claims: int) -> list[str]:
    claims = []
    for sentence in _split_sentences(text):
        if re.search(r"\d|%|million|billion|founded|published|reported|according", sentence, flags=re.IGNORECASE):
            claims.append(sentence)
        if len(claims) >= max_claims:
            break
    return claims


def _claim_supported(claim: str, result: dict[str, Any]) -> bool:
    haystack = (result.get("title", "") + " " + result.get("body", "")).lower()
    tokens = [t for t in _content_tokens(claim) if len(t) > 4][:6]
    if not tokens:
        return False
    hits = sum(1 for t in tokens if t in haystack)
    return hits >= 2


def _fact_check(claims: list[str], per_claim_results: int) -> dict[str, Any]:
    checked = []
    for claim in claims:
        query = " ".join(claim.split()[:12])
        try:
            results = search(query, n=per_claim_results)
            supported = any(_claim_supported(claim, r) for r in results)
            checked.append(
                {
                    "claim": claim,
                    "status": "supported-hint" if supported else "not-confirmed",
                    "refs": [r.get("href", "") for r in results[:2]],
                }
            )
        except Exception as exc:
            checked.append(
                {
                    "claim": claim,
                    "status": "not-checked",
                    "refs": [],
                    "error": str(exc),
                }
            )

    return {
        "claims": checked,
        "supported": sum(1 for c in checked if c["status"] == "supported-hint"),
        "not_confirmed": sum(1 for c in checked if c["status"] == "not-confirmed"),
        "not_checked": sum(1 for c in checked if c["status"] == "not-checked"),
    }


def _load_source_text(
    source_path: Path,
    output_dir: Path,
    model: str,
    ocr_all: bool,
    ocr_engine: str,
    ocr_lang: str,
    tesseract_psm: int,
) -> tuple[str, str]:
    suffix = source_path.suffix.lower()

    if suffix in TEXT_EXTENSIONS:
        return _strip_markdown(_read_text_file(source_path)), source_path.name

    if suffix == ".pdf":
        from pdf_analyzer import analyze_pdf

        md = analyze_pdf(
            source_path,
            output_dir=output_dir,
            ocr_all=ocr_all,
            ocr_engine=ocr_engine,
            ocr_lang=ocr_lang,
            tesseract_psm=tesseract_psm,
        )
        return _strip_markdown(md), source_path.name

    if suffix in VIDEO_EXTENSIONS:
        from video_transcriber import transcribe

        transcribe(source_path, model_name=model, output_dir=output_dir)
        transcript = output_dir / f"{source_path.stem}_transcript.md"
        if not transcript.exists():
            sys.exit(f"Expected transcript not found: {transcript}")
        return _strip_markdown(_read_text_file(transcript)), source_path.name

    sys.exit(
        f"Unsupported input type: {source_path.suffix}. "
        "Use .md/.txt/.pdf or media files (mp4/mkv/mp3/wav...)."
    )


def summarize_input(
    input_value: str,
    output_dir: Path,
    max_sentences: int,
    model: str,
    ocr_all: bool,
    ocr_engine: str,
    ocr_lang: str,
    tesseract_psm: int,
    fact_check: bool,
    fact_check_results: int,
    max_claims: int,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)

    if is_url(input_value):
        with DownloadedFile(input_value) as local_path:
            text, source_label = _load_source_text(
                local_path,
                output_dir,
                model,
                ocr_all,
                ocr_engine,
                ocr_lang,
                tesseract_psm,
            )
            slug = "url_input"
            return _write_summary_report(
                text,
                source_label=f"{input_value} ({source_label})",
                output_dir=output_dir,
                output_slug=slug,
                max_sentences=max_sentences,
                fact_check=fact_check,
                fact_check_results=fact_check_results,
                max_claims=max_claims,
            )

    local = Path(input_value)
    if not local.exists():
        sys.exit(f"Input not found: {local}")

    text, source_label = _load_source_text(
        local,
        output_dir,
        model,
        ocr_all,
        ocr_engine,
        ocr_lang,
        tesseract_psm,
    )
    return _write_summary_report(
        text,
        source_label=source_label,
        output_dir=output_dir,
        output_slug=local.stem,
        max_sentences=max_sentences,
        fact_check=fact_check,
        fact_check_results=fact_check_results,
        max_claims=max_claims,
    )


def _write_summary_report(
    text: str,
    source_label: str,
    output_dir: Path,
    output_slug: str,
    max_sentences: int,
    fact_check: bool,
    fact_check_results: int,
    max_claims: int,
) -> Path:
    logical = _logical_checks(text)
    spelling = _spelling_checks(text)
    claims = _extract_claims(text, max_claims=max_claims)
    claim_report = _fact_check(claims, per_claim_results=fact_check_results) if fact_check else {
        "claims": [],
        "supported": 0,
        "not_confirmed": 0,
        "not_checked": 0,
    }

    summary = _extractive_summary(text, max_sentences=max_sentences)
    coherence = _coherence_score(text, summary)

    report_lines = [
        f"# Summary Report: {source_label}\n",
        f"_Generated: {datetime.now(UTC).isoformat()}_\n",
        "\n## Summary\n",
        summary or "[No summary could be generated from the provided input.]",
        "\n\n## Pre-Summary Quality Checks\n",
        f"- Logical status: **{logical['status']}**",
        f"- Sentence count: {logical['sentence_count']}",
        f"- Average content words per sentence: {logical['avg_sentence_words']}",
        f"- Duplicate sentence ratio: {logical['duplicate_sentence_ratio']}",
        f"- Spelling check enabled: {spelling['enabled']}",
        f"- Potential spelling issues: {spelling['error_count']}",
        f"- Coherence score (source vs summary): {coherence}",
    ]

    if logical["notes"]:
        report_lines.append("\n### Logical Notes\n")
        report_lines.extend([f"- {n}" for n in logical["notes"]])

    if spelling["note"]:
        report_lines.append(f"\n- {spelling['note']}")

    if spelling["suggestions"]:
        report_lines.append("\n### Spelling Suggestions (sample)\n")
        for item in spelling["suggestions"][:10]:
            report_lines.append(f"- {item['word']} -> {item['suggestion']}")

    report_lines.append("\n## Fact-Check Hints\n")
    if not fact_check:
        report_lines.append("- Fact-check disabled by flag.")
    else:
        report_lines.append(f"- Claims reviewed: {len(claim_report['claims'])}")
        report_lines.append(f"- Supported hints: {claim_report['supported']}")
        report_lines.append(f"- Not confirmed: {claim_report['not_confirmed']}")
        report_lines.append(f"- Not checked: {claim_report['not_checked']}")
        if claim_report["claims"]:
            report_lines.append("\n### Claim Details\n")
            for c in claim_report["claims"]:
                report_lines.append(f"- Status: **{c['status']}**")
                report_lines.append(f"  Claim: {c['claim']}")
                if c.get("refs"):
                    for ref in c["refs"]:
                        report_lines.append(f"  Ref: {ref}")
                if c.get("error"):
                    report_lines.append(f"  Error: {c['error']}")

    safe_slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", output_slug)[:80] or "summary"
    out_file = output_dir / f"{safe_slug}_summary.md"
    out_file.write_text("\n".join(report_lines), encoding="utf-8")
    return out_file


def main() -> None:
    parser = argparse.ArgumentParser(description="Create quality-checked summaries.")
    parser.add_argument("input", help="Input file path or URL")
    parser.add_argument("--output", default="out", help="Output directory (default: out/)")
    parser.add_argument("--max-sentences", type=int, default=8, help="Summary sentence budget")
    parser.add_argument("--model", default="base", choices=["tiny", "base", "small", "medium", "large"])

    parser.add_argument("--ocr-all", action="store_true", help="Force OCR when input is PDF")
    parser.add_argument(
        "--ocr-engine",
        choices=["auto", "tesseract", "ocrmypdf"],
        default="auto",
        help="OCR engine strategy for PDF inputs",
    )
    parser.add_argument("--ocr-lang", default="eng", help="Tesseract language(s), e.g. eng or ita+eng")
    parser.add_argument("--tesseract-psm", type=int, default=6, help="Tesseract page segmentation mode")

    parser.add_argument("--no-fact-check", action="store_true", help="Disable web-backed claim checks")
    parser.add_argument("--fact-check-results", type=int, default=3, help="DuckDuckGo results per claim")
    parser.add_argument("--max-claims", type=int, default=5, help="Maximum claims to review")

    args = parser.parse_args()
    out = summarize_input(
        input_value=args.input,
        output_dir=Path(args.output),
        max_sentences=max(1, args.max_sentences),
        model=args.model,
        ocr_all=args.ocr_all,
        ocr_engine=args.ocr_engine,
        ocr_lang=args.ocr_lang,
        tesseract_psm=args.tesseract_psm,
        fact_check=not args.no_fact_check,
        fact_check_results=max(1, args.fact_check_results),
        max_claims=max(1, args.max_claims),
    )
    print(f"Summary written: {out}")


if __name__ == "__main__":
    main()