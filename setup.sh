#!/usr/bin/env bash
# Setup script for analyzer-tool (Linux/macOS)
# Run from repo root: bash setup.sh

set -e

echo "=== analyzer-tool setup ==="

# 1. Python check
echo ""
echo "[1/4] Checking Python..."
if command -v python3 &>/dev/null; then
    echo "  Found: $(python3 --version)"
    PY=python3
elif command -v python &>/dev/null; then
    echo "  Found: $(python --version)"
    PY=python
else
    echo "  ERROR: Python not found. Install python3 first."
    exit 1
fi

# 2. Install Python dependencies
echo ""
echo "[2/4] Installing Python dependencies..."
$PY -m pip install --upgrade pip
$PY -m pip install -r requirements.txt
echo "  Python deps installed."

# 3. Check ffmpeg
echo ""
echo "[3/4] Checking ffmpeg..."
if command -v ffmpeg &>/dev/null; then
    echo "  Found: $(ffmpeg -version 2>&1 | head -1)"
else
    echo "  ffmpeg NOT found."
    echo "  Ubuntu/Debian: sudo apt install ffmpeg"
    echo "  macOS:         brew install ffmpeg"
fi

# 4. Check Tesseract
echo ""
echo "[4/4] Checking Tesseract OCR..."
if command -v tesseract &>/dev/null; then
    echo "  Found: $(tesseract --version 2>&1 | head -1)"
else
    echo "  Tesseract NOT found (needed for handwritten/scanned PDF OCR)."
    echo "  Ubuntu/Debian: sudo apt install tesseract-ocr"
    echo "  macOS:         brew install tesseract"
fi

echo ""
echo "=== Setup complete ==="
echo "Try: $PY src/analyzer.py --help"
