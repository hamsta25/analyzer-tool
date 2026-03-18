# analyzer-tool

A standalone, general-purpose local content analyzer. Extracts text from PDFs (digital, handwritten, scanned), transcribes videos offline, and searches the web as a fallback — outputting clean markdown files to `out/`.

---

## What it does

| Module | Input | Output |
|---|---|---|
| `pdf_analyzer.py` | PDF files (digital or scanned/handwritten) | Markdown with extracted text, OCR where needed |
| `video_transcriber.py` | Video/audio files (mp4, mkv, wav, …) | Markdown transcript with timestamps |
| `web_search.py` | Search query string | Markdown with top-N DuckDuckGo results |
| `analyzer.py` | Any combination via unified CLI | All of the above + index |

All output goes to `out/` which is gitignored — manage it per-project or per-course.

---

## Installation

```bash
pip install -r requirements.txt
```

### External dependencies

#### ffmpeg (required for video transcription)

| Platform | Command |
|---|---|
| Windows (winget) | `winget install Gyan.FFmpeg` |
| Windows (choco) | `choco install ffmpeg` |
| Ubuntu/Debian | `sudo apt install ffmpeg` |
| macOS | `brew install ffmpeg` |

#### Tesseract OCR (required for handwritten/scanned PDFs)

| Platform | Command |
|---|---|
| Windows | Download installer: https://github.com/UB-Mannheim/tesseract/wiki |
| Ubuntu/Debian | `sudo apt install tesseract-ocr` |
| macOS | `brew install tesseract` |

After installing Tesseract on Windows, add it to your `PATH` (e.g. `C:\Program Files\Tesseract-OCR`).

### Automated setup

```powershell
# Windows
.\setup.ps1

# Linux/macOS
bash setup.sh
```

---

## Usage

### Unified CLI (`analyzer.py`)

```bash
# Extract text from a PDF
python src/analyzer.py pdf path/to/file.pdf

# Force OCR on all pages (e.g. fully handwritten notebook)
python src/analyzer.py pdf path/to/file.pdf --ocr-all

# Process an entire directory of PDFs
python src/analyzer.py pdf path/to/dir/

# Transcribe a video (downloads 'base' model on first run, then fully offline)
python src/analyzer.py video path/to/lecture.mkv

# Use a larger Whisper model for better accuracy
python src/analyzer.py video path/to/lecture.mkv --model small

# Web search fallback
python src/analyzer.py search "RISC-V pipeline hazards"

# Process all PDFs + videos in a directory and generate an index
python src/analyzer.py all path/to/course-materials/ --output out/
```

### Individual modules

```bash
# PDF extraction
python src/pdf_analyzer.py path/to/file.pdf [--ocr-all] [--output out/]
python src/pdf_analyzer.py path/to/dir/ [--output out/]

# Video transcription
python src/video_transcriber.py path/to/video.mkv [--model base] [--output out/]

# Web search (prints to stdout by default)
python src/web_search.py "search query" [--n 5] [--output out/]
```

---

## Whisper model sizes

| Model | Size | Speed | Accuracy |
|---|---|---|---|
| tiny | ~75 MB | fastest | lowest |
| base | ~145 MB | fast | good |
| small | ~460 MB | moderate | better |
| medium | ~1.5 GB | slow | high |
| large | ~3 GB | slowest | best |

Models are downloaded once and cached locally (`~/.cache/whisper/`).

---

## Project structure

```
analyzer-tool/
  src/
    analyzer.py          ← unified CLI
    pdf_analyzer.py      ← PDF text extraction + OCR
    video_transcriber.py ← Whisper offline transcription
    web_search.py        ← DuckDuckGo search fallback
  out/                   ← output folder (gitignored, manage per-project)
  requirements.txt
  setup.ps1              ← Windows setup
  setup.sh               ← Linux/macOS setup
```

> **Note:** The `out/` folder is gitignored. Copy or symlink it per course/project as needed.
