import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from summarizer import (  # noqa: E402
    _coherence_score,
    _extract_claims,
    _extractive_summary,
    _logical_checks,
    _split_sentences,
    _strip_markdown,
    _write_summary_report,
    summarize_input,
)


def test_strip_markdown_removes_links_and_code():
    raw = "# Title\nText with [link](https://example.com) and `code`."
    plain = _strip_markdown(raw)
    assert "https://example.com" not in plain
    assert "code" not in plain
    assert "Text with link" in plain


def test_split_sentences_detects_three_sentences():
    text = "First sentence. Second sentence? Third sentence!"
    chunks = _split_sentences(text)
    assert len(chunks) == 3


def test_extractive_summary_respects_budget():
    text = (
        "Python is widely used in data and automation. "
        "Summary quality depends on coherent source text. "
        "Quality checks should run before output generation. "
        "Fact checking improves trust in extracted claims."
    )
    summary = _extractive_summary(text, max_sentences=2)
    assert len(_split_sentences(summary)) <= 2


def test_coherence_score_in_range():
    score = _coherence_score(
        "This is a source text about machine learning and embedded systems.",
        "A summary about embedded systems and machine learning.",
    )
    assert 0.0 <= score <= 1.0


def test_logical_checks_warn_on_tiny_sentences():
    result = _logical_checks("A. B. C.")
    assert result["status"] == "warn"
    assert result["sentence_count"] == 3


def test_extract_claims_picks_numeric_sentences():
    text = "The project started in 2022. We have momentum. Growth reached 45%."
    claims = _extract_claims(text, max_claims=5)
    assert len(claims) == 2
    assert "2022" in claims[0]


def test_write_summary_report_creates_file(tmp_path):
    text = (
        "Analyzer-tool extracts text from PDFs and videos. "
        "This project was started in 2026 and has 3 modules. "
        "The architecture uses reusable CLI commands."
    )
    out = _write_summary_report(
        text=text,
        source_label="sample.txt",
        output_dir=tmp_path,
        output_slug="sample",
        max_sentences=3,
        fact_check=False,
        fact_check_results=2,
        max_claims=3,
    )
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert "## Summary" in content
    assert "## Pre-Summary Quality Checks" in content


def test_summarize_input_txt_file(tmp_path):
    src = tmp_path / "note.txt"
    src.write_text(
        "This is a practical note about embedded systems. "
        "It includes 2 checkpoints and one release target.",
        encoding="utf-8",
    )
    out_dir = tmp_path / "out"
    out_file = summarize_input(
        input_value=str(src),
        output_dir=out_dir,
        max_sentences=4,
        model="base",
        ocr_all=False,
        ocr_engine="auto",
        ocr_lang="eng",
        tesseract_psm=6,
        fact_check=False,
        fact_check_results=2,
        max_claims=3,
    )
    assert out_file.exists()
    assert out_file.name.endswith("_summary.md")