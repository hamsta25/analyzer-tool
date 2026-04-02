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
python -m pip install -r requirements.txt
```

On Windows, if you use a virtual environment, prefer:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
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

#### OCRmyPDF (optional, improves scanned note preprocessing)

| Platform | Command |
|---|---|
| Windows | `py -3 -m pip install ocrmypdf` |
| Ubuntu/Debian | `sudo apt install ocrmypdf` |
| macOS | `brew install ocrmypdf` |

---

## Verifying and configuring PATH

After installing **ffmpeg** or **Tesseract**, ensure they're in your system PATH so the tools can find them.

### Verify installation

```bash
# Verify ffmpeg
ffmpeg -version

# Verify Tesseract
tesseract --version
```

If either command returns "not found," add them to PATH:

### Windows (PowerShell / Command Prompt)

**ffmpeg** — common installation paths:
- `C:\Program Files\ffmpeg\bin` (if installed via installer)
- `C:\tools\ffmpeg\bin` (if used Chocolatey without admin)

To add to PATH persistently:
1. Press `Win+X` → Select "System"
2. Click "Advanced system settings" → "Environment Variables"
3. Under "User variables" or "System variables," select `Path` → **Edit**
4. Click **New** and paste the ffmpeg install path
5. Click **OK** and restart your terminal
6. Verify: `ffmpeg -version`

**Tesseract** — typical path: `C:\Program Files\Tesseract-OCR`
```

Add persistently (as Administrator in PowerShell):
```powershell
[Environment]::SetEnvironmentVariable("PATH", $env:PATH + ";C:\Program Files\Tesseract-OCR", "User")
# Restart PowerShell to apply
```

### macOS / Linux

If `brew install` or `apt install` was used, both tools should already be in PATH. Verify:
```bash
which ffmpeg && which tesseract
```

If not found despite installation:
```bash
# Find installation path

# Add to shell profile (~/.zshrc, ~/.bashrc, or ~/.bash_profile)
export PATH="/usr/local/bin:$PATH"
source ~/.zshrc  # reload
```

---

### Automated setup

```powershell
# Windows
.\setup.ps1

# Linux/macOS
bash setup.sh
```

---

## Troubleshooting

### "Python not found" or "pip not found"

Windows users with MSYS2, Git Bash, or Cygwin installed may encounter conflicts if those tools are in PATH before Python.org Python.

#### Diagnose the issue

```powershell
# Check which Python is resolved first
where python
py -0p  # Shows all Python installations and active one
```

⚠️ **If you see `C:\msys64\ucrt64\bin\python.exe` or `C:\...\Git\usr\bin\python.exe` (MSYS2 or Git Bash Python)**:
- This Python lacks pip and doesn't have installed packages
- Even after installing via `py -3 -m pip install`, bare `python` won't find them
- The solution is **Preferred (below) or adjust PATH order**

If you see bare `python` resolve to MSYS2 but want to keep it as default:

#### Solutions

**Preferred (Windows Python launcher)**:
```powershell
py -3 -m pip install -r requirements.txt
py -3 src/analyzer.py --help
```

**If you're inside a venv, always use interpreter-scoped pip**:
```powershell
python -m pip install -r requirements.txt
```

**Activation quick reference**:
```powershell
.\.venv\Scripts\Activate.ps1

# CMD
.\.venv\Scripts\activate.bat

# Git Bash
source .venv/Scripts/activate
```

**Alternative (ensure Python.org Python is first in PATH)**:
1. Install Python from https://www.python.org/downloads/
2. Open "Environment Variables" (`Win+X` → System → Advanced → Environment Variables)
3. Move the Python.org path (e.g., `C:\Users\...\AppData\Local\Programs\Python\Python314`) **before** any MSYS2/Git Bash paths
4. Restart PowerShell and re-run `.\setup.ps1`

**If still stuck**:
- Run `.\setup.ps1` which validates pip availability and prints diagnostics
- Run `.\scripts\env-doctor.ps1` to detect python/pip mismatch and venv issues in your current shell
- Run `.\scripts\python-env-remediate.ps1` for a safe PATH reordering dry-run (use `-Apply` to commit)
- Review the error message for additional guidance
- On Linux/macOS, check: `which -a python3 python` and `python3 -m pip --version`

**Recommended Windows recovery sequence**:
```powershell
# 1) Diagnose
.\scripts\env-doctor.ps1

# 2) Simulate remediation
.\scripts\python-env-remediate.ps1

# 3) Apply remediation only if plan is correct
.\scripts\python-env-remediate.ps1 -Apply
# 4) Open a new terminal and verify
where python
py -0p
python -m pip --version
```

---

## Usage

### Unified CLI (`analyzer.py`)

```bash
# Extract text from a PDF
python src/analyzer.py pdf path/to/file.pdf

# Force OCR on all pages (e.g. fully handwritten notebook)
python src/analyzer.py pdf path/to/file.pdf --ocr-all

# Handwritten notes in Italian/English with better structure handling
python src/analyzer.py pdf path/to/file.pdf --ocr-all --ocr-engine auto --ocr-lang ita+eng --tesseract-psm 6

# Force OCRmyPDF preprocessing if installed (better for skew/noise/rotation)
python src/analyzer.py pdf path/to/file.pdf --ocr-engine ocrmypdf --ocr-lang ita+eng

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

### Web URLs as input (Google Drive, direct links)

The `video` and `pdf` subcommands accept HTTP/HTTPS URLs directly — no manual download needed.

```bash
# Transcribe a video shared on Google Drive
python src/analyzer.py video "https://drive.google.com/file/d/1i6ZqijtHN82T9Ig5NDCN9SgHDNRctvpo/view?usp=sharing"

# Transcribe a YouTube video (or any yt-dlp-supported platform)
python src/analyzer.py video "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Download and extract text from a PDF hosted online
python src/analyzer.py pdf "https://example.com/report.pdf"

# Use a larger model when transcribing from a URL
python src/analyzer.py video "https://drive.google.com/..." --model small --output out/
```

**Supported URL types:**

| Type | Example | Backend |
|---|---|---|
| Google Drive shared file | `drive.google.com/file/d/.../view` | `yt-dlp` |
| YouTube and most video platforms | `youtube.com/watch?v=...` | `yt-dlp` |
| Direct video link | `example.com/video.mp4` | `requests` |
| Direct PDF link | `example.com/report.pdf` | `requests` |

**Requirements for URL input:**
- `yt-dlp` is installed (included in `requirements.txt`): `pip install yt-dlp`
- Internet access at runtime
- For Google Drive: the file must be publicly shared ("Anyone with the link can view")
- ffmpeg is still required for video transcription (see above)

The tool downloads the file to a local temp directory, processes it, then cleans up automatically.

---

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

### OCR strategy notes (handwritten/scanned pages)

- `--ocr-engine auto` (recommended): tries OCRmyPDF preprocessing when available, then applies Tesseract OCR on sparse pages.
- `--ocr-engine tesseract`: direct OCR only, faster setup but weaker on skew/noisy scans.
- `--ocr-engine ocrmypdf`: forces OCRmyPDF preprocessing first (best for scanned lecture notes), then extraction.

For pages with drawings/diagrams, the tool now exports page snapshots under `out/assets/<pdf-name>/` and embeds them in markdown so context is not lost when plain text OCR misses structure.

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
    url_resolver.py      ← HTTP/HTTPS URL download (Google Drive, yt-dlp, direct)
  tests/
    test_url_resolver.py        ← unit tests (offline, mocked)
    test_web_url_integration.py ← integration tests (real network, opt-in)
  out/                   ← output folder (gitignored, manage per-project)
  requirements.txt
  pytest.ini
  setup.ps1              ← Windows setup
  setup.sh               ← Linux/macOS setup
```

> **Note:** The `out/` folder is gitignored. Copy or symlink it per course/project as needed.


---

## Tesseract & FFmpeg Quick-Install (Troubleshooting)

### Tesseract OCR

Tesseract must be installed separately  it is **not** a Python package:

```powershell
# Windows
winget install UB-Mannheim.TesseractOCR
```

```bash
# Ubuntu/Debian
sudo apt install tesseract-ocr

# macOS
brew install tesseract
```

> **Note:** `pytesseract` is **not used** in this tool. Tesseract is called directly via
> `subprocess` to avoid ABI incompatibilities between `pandas` (a `pytesseract` dependency)
> and NumPy 2.x. No `pip install pytesseract` is needed.

### FFmpeg

FFmpeg must be installed separately:

```powershell
# Windows
winget install Gyan.FFmpeg
```

```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg
```

The tool automatically searches common WinGet/Chocolatey install paths if `ffmpeg` is not on
your system `PATH`.

### Whisper model downloads

Whisper models are downloaded automatically on first use from OpenAI's servers (~75 MB for
`tiny`, up to ~3 GB for `large`). They are cached at `~/.cache/whisper/`. An internet
connection is required only on the first run for each model size.