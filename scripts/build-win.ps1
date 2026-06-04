# =============================================================================
# Midicoder Windows Build Script
# =============================================================================
# Full release build: Angular → midicoder/frontend/ → PyInstaller binary
#
# Runtime bundled:
#   - Python 3.12.x (locked from .venv)
#   - FastAPI + uvicorn + all Python dependencies
#   - tree_sitter + tree_sitter_languages (native .pyd)
#   - midicoder/ package + Angular SPA dist
#   - Datasette (SQLite web viewer)
#   - SQLite (Python stdlib)
#
# NOT bundled:
#   - Node.js (build time only)
#
# Prerequisites:
#   - Python 3.12.x in .venv
#   - Node.js (for Angular build)
#   - All dependencies in .venv (uv pip install -e ".[dev]")
#
# Usage:
#   .\scripts\build-win.ps1
# =============================================================================

$ErrorActionPreference = "Stop"

$repoRoot = (Get-Item $PSScriptRoot).Parent.FullName
$outputDir = Join-Path $repoRoot "dist\windows"

Write-Host "[BUILD] Midicoder Release Builder (Windows)" -ForegroundColor Green

Set-Location $repoRoot

# ============================================================================
# Lock: Python runtime from .venv (Python 3.12.x)
# ============================================================================
$pythonExe = Join-Path $repoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    Write-Host "[FAIL] .venv not found. Run: uv venv && uv pip install -e ." -ForegroundColor Red
    exit 1
}
$pyVer = & $pythonExe --version
Write-Host "[BUILD] Using Python: $pyVer" -ForegroundColor Green

# Verify version is 3.12
if ($pyVer -notmatch "3\.12") {
    Write-Host "[FAIL] Python 3.12.x required, got: $pyVer" -ForegroundColor Red
    exit 1
}

# ============================================================================
# Lock: Node.js (build time only, not bundled)
# ============================================================================
$nodeVer = node --version 2>$null
if (-not $nodeVer) {
    Write-Host "[FAIL] Node.js required for Angular build" -ForegroundColor Red
    exit 1
}
Write-Host "[BUILD] Using Node.js: $nodeVer (build time only)" -ForegroundColor Green

# Step 1: Build Angular
Write-Host "[BUILD] Building Angular frontend..." -ForegroundColor Green
Set-Location "$repoRoot\webgui"
try {
    npx ng build --configuration=production
} catch {
    Write-Host "[FAIL] Angular build failed" -ForegroundColor Red
    exit 1
}
Set-Location $repoRoot

# Step 2: Copy dist to midicoder/frontend/
Write-Host "[BUILD] Copying Angular dist to midicoder/frontend/" -ForegroundColor Green

$srcDist = Join-Path $repoRoot "webgui\dist\webgui\browser"
if (-not (Test-Path $srcDist)) {
    $srcDist = Join-Path $repoRoot "webgui\dist\browser"
}
if (-not (Test-Path $srcDist)) {
    Write-Host "[FAIL] Angular dist not found" -ForegroundColor Red
    exit 1
}

$destFrontend = Join-Path $repoRoot "midicoder\frontend"
if (Test-Path $destFrontend) { Remove-Item -Recurse -Force $destFrontend }
New-Item -ItemType Directory -Path $destFrontend -Force | Out-Null
Copy-Item -Path "$srcDist\*" -Destination $destFrontend -Recurse -Force
Set-Content "$destFrontend\__init__.py" ""

# Step 3: Check PyInstaller in .venv
& $pythonExe -c "import PyInstaller" 2>$null
if (-not $?) {
    Write-Host "[FAIL] PyInstaller not in .venv. Run: uv pip install pyinstaller" -ForegroundColor Red
    exit 1
}

# Step 4: Clean old build artifacts (avoids PyInstaller y/N prompt)
$buildDir = Join-Path $repoRoot "build\midicoder"
$pyDistDir = Join-Path $outputDir "midicoder"
if (Test-Path $buildDir) { Remove-Item -Recurse -Force $buildDir }
if (Test-Path $pyDistDir) { Remove-Item -Recurse -Force $pyDistDir }

New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
Write-Host "[BUILD] Building with PyInstaller (using .venv Python 3.12)..." -ForegroundColor Green
& $pythonExe -m PyInstaller `
    --clean `
    "$repoRoot\midicoder.spec" `
    --distpath="$outputDir"

# Step 5: Verify & package
$collectDir = Join-Path $outputDir "midicoder"
$exePath = Join-Path $collectDir "midicoder.exe"
if (Test-Path $exePath) {
    Write-Host "[BUILD] Build successful!" -ForegroundColor Green
    Get-Item $exePath | Select-Object Name, @{N='Size(MB)';E={[math]::Round($_.Length/1MB,1)}}, LastWriteTime

    $zipPath = Join-Path $outputDir "midicoder-windows-bin.zip"
    Compress-Archive -Path $collectDir -DestinationPath $zipPath -Force
    Write-Host "[BUILD] Package: midicoder-windows-bin.zip ($([math]::Round((Get-Item $zipPath).Length/1MB,1)) MB)" -ForegroundColor Green
} else {
    Write-Host "[FAIL] Build failed - executable not found at $exePath" -ForegroundColor Red
    Write-Host "[DEBUG] Available in dist:" -ForegroundColor Yellow
    Get-ChildItem -Path $outputDir -Recurse -File | Select-Object FullName, @{N='Size(KB)';E={[math]::Round($_.Length/1KB,1)}}
    exit 1
}

# Cleanup
if (Test-Path $destFrontend) {
    Remove-Item -Recurse -Force $destFrontend
    Write-Host "[BUILD] Cleaned up midicoder/frontend/" -ForegroundColor Green
}
