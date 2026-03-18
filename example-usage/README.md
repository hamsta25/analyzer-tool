# example-usage

This folder contains example scripts and assets to verify the analyzer-tool is working correctly.

## Prerequisites

Make sure you have run from the repo root:

```bash
pip install -r requirements.txt
```

And installed the external tools:
- **Tesseract OCR**: `winget install UB-Mannheim.TesseractOCR` (Windows) or `sudo apt install tesseract-ocr` (Linux)
- **FFmpeg**: `winget install Gyan.FFmpeg` (Windows) or `sudo apt install ffmpeg` (Linux)

## Step 1: Generate test assets

Run this **once** to create `test-image.png` and `test-video.mp4`:

```bash
python example-usage/generate_examples.py
```

This requires Pillow (for the image) and FFmpeg (for the video). Both are generated locally and are not committed to git.

## Step 2: Run OCR example

```bash
python example-usage/run_example_ocr.py
```

Expected output: extracted text from `test-image.png` printed to stdout, containing "Hello OCR test 123".

## Step 3: Run video transcription example

```bash
python example-usage/run_example_video.py
```

Expected output: a short transcript of the silent test video using the `tiny` Whisper model. The model (~75 MB) is downloaded automatically on first run.

## Files

| File | Purpose |
|---|---|
| `generate_examples.py` | Generates `test-image.png` and `test-video.mp4` |
| `run_example_ocr.py` | Runs OCR on `test-image.png` via pdf_analyzer subprocess path |
| `run_example_video.py` | Transcribes `test-video.mp4` with Whisper tiny model |
| `test-image.png` | Generated test image (not in git, run generate_examples.py) |
| `test-video.mp4` | Generated test video (not in git, run generate_examples.py) |
