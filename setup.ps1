# Setup script for analyzer-tool (Windows PowerShell)
# Run from repo root: .\setup.ps1

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "=== analyzer-tool setup ===" -ForegroundColor Cyan

# 1. Python check
Write-Host "`n[1/4] Checking Python..." -ForegroundColor Yellow
try {
    $pyVersion = python --version 2>&1
    Write-Host "  Found: $pyVersion" -ForegroundColor Green
} catch {
    Write-Error "Python not found. Install from https://www.python.org/downloads/"
}

# 2. Install Python dependencies
Write-Host "`n[2/4] Installing Python dependencies..." -ForegroundColor Yellow
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Write-Host "  Python deps installed." -ForegroundColor Green

# 3. Check ffmpeg
Write-Host "`n[3/4] Checking ffmpeg..." -ForegroundColor Yellow
if (Get-Command ffmpeg -ErrorAction SilentlyContinue) {
    $ffVer = ffmpeg -version 2>&1 | Select-Object -First 1
    Write-Host "  Found: $ffVer" -ForegroundColor Green
} else {
    Write-Host "  ffmpeg NOT found." -ForegroundColor Red
    Write-Host "  Install via winget:  winget install Gyan.FFmpeg"
    Write-Host "  Install via choco:   choco install ffmpeg"
    Write-Host "  Then restart your terminal and re-run this script."
}

# 4. Check Tesseract
Write-Host "`n[4/4] Checking Tesseract OCR..." -ForegroundColor Yellow
if (Get-Command tesseract -ErrorAction SilentlyContinue) {
    $tessVer = tesseract --version 2>&1 | Select-Object -First 1
    Write-Host "  Found: $tessVer" -ForegroundColor Green
} else {
    Write-Host "  Tesseract NOT found (needed for handwritten/scanned PDF OCR)." -ForegroundColor Yellow
    Write-Host "  Install from: https://github.com/UB-Mannheim/tesseract/wiki"
    Write-Host "  After install, ensure tesseract.exe is in your PATH."
}

Write-Host "`n=== Setup complete ===" -ForegroundColor Cyan
Write-Host "Try: python src/analyzer.py --help"
