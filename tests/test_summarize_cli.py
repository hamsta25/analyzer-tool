import subprocess
import sys
from pathlib import Path


def test_analyzer_cli_summarize_txt(tmp_path):
    repo_root = Path(__file__).parent.parent
    analyzer = repo_root / "src" / "analyzer.py"
    src_file = tmp_path / "input.txt"
    out_dir = tmp_path / "out"

    src_file.write_text(
        "This is a short project note. It contains 3 milestones and one risk. "
        "The goal is to validate summary generation.",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(analyzer),
            "summarize",
            str(src_file),
            "--output",
            str(out_dir),
            "--no-fact-check",
        ],
        capture_output=True,
        text=True,
        cwd=str(repo_root / "src"),
    )

    assert result.returncode == 0, f"stderr: {result.stderr}"
    summaries = list(out_dir.glob("*_summary.md"))
    assert summaries, "No summary markdown generated"

    content = summaries[0].read_text(encoding="utf-8")
    assert "## Summary" in content
    assert "## Pre-Summary Quality Checks" in content