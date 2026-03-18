# Setup script for analyzer-tool (Windows PowerShell)
# Run from repo root: .\setup.ps1

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "=== analyzer-tool setup ===" -ForegroundColor Cyan

# 1. Robust Python interpreter resolution
Write-Host "`n[1/4] Resolving Python interpreter..." -ForegroundColor Yellow

$Python = $null
$candidates = @("py.exe", "python3.exe", "python.exe")

foreach ($candidate in $candidates) {
    try {
        $fullPath = (Get-Command $candidate -ErrorAction Stop).Source
        $version = & $fullPath --version 2>&1
        
        # Reject MSYS2/MinGW python if pip missing
        if ($candidate -eq "python.exe" -or $candidate -eq "python3.exe") {
            $hasPip = & $fullPath -m pip --version 2>$null
            if ($LASTEXITCODE -ne 0) {
                Write-Host "  [Skip] $candidate at $fullPath (pip not found)" -ForegroundColor Yellow
                continue
            }
        }
        
        $Python = $fullPath
        Write-Host "  Found: $version at $Python" -ForegroundColor Green
        break
    } catch {
        # Continue to next candidate
    }
}

if (-not $Python) {
    Write-Error @"
Python not found or pip unavailable. Solutions:
  1. Install Python.org Python: https://www.python.org/downloads/
  2. Check installed versions: where python ; py -0p
  3. Ensure Python.org Python comes before MSYS2/Git Bash in PATH
  4. As last resort: py -3 -m pip install -r requirements.txt (manual fallback)
"@
    exit 1
}

# 2. Validate pip availability before attempting install
Write-Host "`n[Validation] Checking pip in resolved Python..." -ForegroundColor Yellow
$pipVersion = & $Python -m pip --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error @"
pip not found in $Python. Error: $pipVersion

Solutions:
  1. Ensure you installed Python from https://www.python.org/ (not MSYS2)
  2. Run: $Python -m ensurepip --upgrade
  3. Check PATH conflicts: where python ; py -0p
  4. If MSYS2 detected, uninstall: pacman -R python
"@
    exit 1
}
Write-Host "  Found: $pipVersion" -ForegroundColor Green

# 3. Install Python dependencies
Write-Host "`n[2/4] Installing Python dependencies..." -ForegroundColor Yellow
& $Python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to upgrade pip. See output above."
    exit 1
}

& $Python -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to install dependencies from requirements.txt. See output above."
    exit 1
}
Write-Host "  Python deps installed successfully." -ForegroundColor Green

# 4. Check ffmpeg
Write-Host "`n[3/4] Checking ffmpeg..." -ForegroundColor Yellow
if (Get-Command ffmpeg -ErrorAction SilentlyContinue) {
    $ffVer = ffmpeg -version 2>&1 | Select-Object -First 1
    Write-Host "  Found: $ffVer" -ForegroundColor Green
} else {
    Write-Host "  ffmpeg NOT found." -ForegroundColor Red
    Write-Host "  Install via winget:  winget install Gyan.FFmpeg"
    Write-Host "  Install via choco:   choco install ffmpeg"
    Write-Host "  Then restart your terminal and re-run this script."
    Write-Host "  See README.md › 'Verifying and configuring PATH' for manual PATH setup."
}

# 5. Check Tesseract
Write-Host "`n[4/4] Checking Tesseract OCR..." -ForegroundColor Yellow
if (Get-Command tesseract -ErrorAction SilentlyContinue) {
    $tessVer = tesseract --version 2>&1 | Select-Object -First 1
    Write-Host "  Found: $tessVer" -ForegroundColor Green
} else {
    Write-Host "  Tesseract NOT found (needed for handwritten/scanned PDF OCR)." -ForegroundColor Yellow
    Write-Host "  Install from: https://github.com/UB-Mannheim/tesseract/wiki"
    Write-Host "  After install, ensure tesseract.exe is in your PATH."
    Write-Host "  See README.md › 'Verifying and configuring PATH' for manual PATH setup."
}

Write-Host "`n=== Setup complete ===" -ForegroundColor Cyan
Write-Host "Try: & '$Python' src/analyzer.py --help"
