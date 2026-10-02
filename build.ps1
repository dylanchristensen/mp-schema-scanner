# Build a standalone Windows binary for the MP Schema Gap Scanner
# (Implicit Assumption Graph build).
#
# Usage (from PowerShell):
#     .\build.ps1
#
# Produces dist\mp-scanner-iag.exe. Does NOT delete other exes already
# in dist\ (e.g. a previously-working mp-scanner.exe is left untouched).
# Dependencies are installed into the active Python environment if missing.

$ErrorActionPreference = "Stop"

Write-Host "[1/3] Installing build dependencies..."
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt
python -m pip install --quiet pyinstaller waitress

Write-Host "[2/3] Cleaning previous build cache (build\ only; dist\ preserved)..."
if (Test-Path build) { Remove-Item -Recurse -Force build }
# Remove only our own previous output, so other exes in dist\ survive.
if (Test-Path "dist\mp-scanner-iag.exe") { Remove-Item -Force "dist\mp-scanner-iag.exe" }

Write-Host "[3/3] Building with PyInstaller..."
python -m PyInstaller --noconfirm mp-scanner.spec

$exe = Join-Path (Get-Location) "dist\mp-scanner-iag.exe"
if (Test-Path $exe) {
    $size = [math]::Round((Get-Item $exe).Length / 1MB, 1)
    Write-Host ""
    Write-Host "Build complete:"
    Write-Host "  $exe  ($size MB)"
    Write-Host ""
    Write-Host "Run it by double-clicking, or:"
    Write-Host "  .\dist\mp-scanner-iag.exe"
} else {
    Write-Error "Build failed: dist\mp-scanner-iag.exe not produced."
    exit 1
}
