#!/usr/bin/env bash
# Setup script for analyzer-tool (Linux/macOS)
# Run from repo root: bash setup.sh

set -e
echo "=== analyzer-tool setup ==="

# 1. Robust Python interpreter resolution
echo ""
echo "[1/4] Resolving Python interpreter..."

PY=""
for candidate in python3 python; do
    if command -v "$candidate" &>/dev/null; then
        # Check if it's MSYS2/MinGW python (reject it)
        prefix=$("$candidate" -c "import sys; print(sys.prefix)" 2>/dev/null || echo "")
        if [[ "$prefix" =~ msys|mingw|cygwin ]]; then
            echo "  [Skip] $candidate at $(command -v "$candidate") (MSYS2/MinGW detected)"
            continue
        fi
        
        # Check if pip is available
        if "$candidate" -m pip --version &>/dev/null; then
            PY="$candidate"
            echo "  Found: $("$candidate" --version) from $(command -v "$candidate")"
            break
        else
            echo "  [Skip] $candidate (pip not found)"
            continue
        fi
    fi
done

if [ -z "$PY" ]; then
    echo "ERROR: No suitable Python found. Solutions:" >&2
    echo "  1. Install Python 3: python3 or python" >&2
    echo "  2. On Ubuntu/Debian: sudo apt install python3-pip" >&2
    echo "  3. On macOS: brew install python3" >&2
    echo "  4. Check PATH: which -a python3 python" >&2
    exit 1
fi

# 2. Validate pip availability before attempting install
echo ""
echo "[Validation] Checking pip in $PY..."
pip_version=$("$PY" -m pip --version 2>&1)
if [ $? -ne 0 ]; then
    echo "ERROR: pip not found in $PY" >&2
    echo "Diagnostic: $pip_version" >&2
    echo "Solutions:" >&2
    echo "  1. Upgrade pip: $PY -m pip install --upgrade pip" >&2
    echo "  2. Use ensurepip: $PY -m ensurepip --upgrade" >&2
    echo "  3. Check for MSYS2 conflicts: which -a python3 python" >&2
    exit 1
fi
echo "  Found: $pip_version"

# 3. Install Python dependencies
echo ""
echo "[2/4] Installing Python dependencies..."
$PY -m pip install --upgrade pip
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to upgrade pip. See output above." >&2
    exit 1
fi

$PY -m pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies from requirements.txt. See output above." >&2
    exit 1
fi
echo "  Python deps installed successfully."

# 4. Check ffmpeg
echo ""
echo "[3/4] Checking ffmpeg..."
if command -v ffmpeg &>/dev/null; then
    echo "  Found: $(ffmpeg -version 2>&1 | head -1)"
else
    echo "  ffmpeg NOT found."
    echo "  Ubuntu/Debian: sudo apt install ffmpeg"
    echo "  macOS:         brew install ffmpeg"
    echo "  See README.md › 'Verifying and configuring PATH' for manual PATH setup."
fi

# 5. Check Tesseract
echo ""
echo "[4/4] Checking Tesseract OCR..."
if command -v tesseract &>/dev/null; then
    echo "  Found: $(tesseract --version 2>&1 | head -1)"
else
    echo "  Tesseract NOT found (needed for handwritten/scanned PDF OCR)."
    echo "  Ubuntu/Debian: sudo apt install tesseract-ocr"
    echo "  macOS:         brew install tesseract"
    echo "  See README.md › 'Verifying and configuring PATH' for manual PATH setup."
fi

echo ""
echo "=== Setup complete ==="
echo "Try: $PY src/analyzer.py --help"
