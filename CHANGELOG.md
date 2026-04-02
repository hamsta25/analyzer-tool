# CHANGELOG

All notable changes to this project will be documented in this file.
Format: [Semantic Versioning](https://semver.org/) — `MAJOR.MINOR.PATCH`.

---

## [Unreleased] — ocr-dev branch

### Added — M6 Web URL Input (2026-04-02)

- **`src/url_resolver.py`** — new module for resolving and downloading media/documents from HTTP/HTTPS URLs:
  - Detects Google Drive shared file links (`drive.google.com/file/d/...`)
  - Routes Google Drive and platform URLs through `yt-dlp` for download
  - Routes direct-extension links (`.mp4`, `.pdf`, etc.) through `requests`
  - `DownloadedFile` context manager: downloads to temp directory, cleans up automatically
  - `is_url(value)` public helper for URL detection in CLI
- **`src/analyzer.py`** — `video` and `pdf` subcommands now accept HTTP/HTTPS URLs as input:
  - `python src/analyzer.py video https://drive.google.com/file/d/.../view` works end-to-end
  - Temp file is always cleaned up after transcription/extraction completes
- **`requirements.txt`** — added `yt-dlp>=2024.1.1` dependency
- **`tests/test_url_resolver.py`** — 21 unit tests (all offline, mocked) for `url_resolver`
- **`tests/test_web_url_integration.py`** — integration tests for real network access (marked `@pytest.mark.integration`, excluded from default CI run)
- **`pytest.ini`** — test configuration; integration tests excluded from default run
- **`.github/ROADMAP.md`** — added P3 epic (Web URL Input) with M6 milestone and DoD

### Changed

- `analyzer.py` `cmd_video` and `cmd_pdf` now check `is_url()` before treating input as a filesystem path
- `tests/test_web_url_integration.py` now uses `ANALYZER_TEST_VIDEO_URL` (default short public sample URL) to avoid hardcoding long/private links
- `requirements.txt` now pins `requests>=2.33.0` following local `pip-audit` vulnerability findings

### Added — M7 Intelligent Summary (2026-04-02)

- **`src/summarizer.py`** — new quality-checked summarization pipeline:
  - Supports `.md`, `.txt`, `.pdf`, media files, and URL inputs
  - Runs pre-summary checks for spelling, logical quality, and claim extraction
  - Performs optional web-backed fact-check hints via DuckDuckGo search
  - Produces `*_summary.md` reports with quality metrics and references
- **`src/analyzer.py`** — new `summarize` subcommand in unified CLI
- **`tests/test_summarizer.py`** — unit tests for summary extraction and quality checks
- **`tests/test_summarize_cli.py`** — CLI regression test for summarize command
- **`requirements.txt`** — added `pyspellchecker>=0.8.1` for spelling validation

---

## [0.1.0] — 2026-03-19

### Added (initial implementation)

- `src/pdf_analyzer.py` — PDF text extraction with OCR fallback (Tesseract / OCRmyPDF)
- `src/video_transcriber.py` — offline video/audio transcription via OpenAI Whisper
- `src/web_search.py` — DuckDuckGo web search, results to markdown
- `src/analyzer.py` — unified CLI (`pdf`, `video`, `search`, `all` subcommands)
- `setup.ps1` / `setup.sh` — environment setup scripts with Python/pip validation
- `scripts/env-doctor.ps1` — Python environment diagnostics
- `scripts/python-env-remediate.ps1` — automatic PATH remediation for MSYS2 conflicts
- `example-usage/` — example scripts for OCR, video transcription
- `.github/ROADMAP.md` — program increment plan (P0-P2 epics, risk register)
- `.github/AGENTS.md` — agent operating model and guardrails
- `.github/agents/program-manager.agent.md` — PM agent definition
- `.github/skills/` — pm-status, pm-release, pm-ocr-audit skill files
- `.github/workflows/ci.yml` and `security.yml` — CI/CD and security workflow stubs
