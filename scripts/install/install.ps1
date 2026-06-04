# ============================================================
# Midicoder CE - Install Script (Windows PowerShell)
# ============================================================
# Downloads the pre-built binary and installs to %USERPROFILE%\.midicoder
#
# Usage:
#   powershell -c "irm https://midicoder.com/install.ps1 | iex"
#
# Options:
#   -Force    : Overwrite existing installation
#   -Version  : Specify version (default: latest)
# ============================================================

param(
    [switch]$Force,
    [string]$Version = "1.0.0"
)

$ErrorActionPreference = "Stop"

$midicoderHome = "$env:USERPROFILE\.midicoder"
$binPath = Join-Path $midicoderHome "bin"
$githubBase = "https://github.com/hemidi-jsc/midicoder/releases/download"
$packageName = "midicoder-windows-bin.zip"
$downloadUrl = "$githubBase/v$Version/$packageName"

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  Midicoder CE Installer v$Version" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Check existing
if (Test-Path $binPath) -and (-not $Force) {
    Write-Host "[WARN] Midicoder already installed at $midicoderHome" -ForegroundColor Yellow
    $resp = Read-Host "Overwrite? (y/N)"
    if ($resp -ne "y" -and $resp -ne "Y") { exit 0 }
    $backup = "$midicoderHome.backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    Move-Item $midicoderHome $backup -Force
    Write-Host "[INFO] Backed up to $backup" -ForegroundColor Cyan
}

# Download
Write-Host "[INFO] Downloading from: $downloadUrl" -ForegroundColor Cyan
$tempFile = [System.IO.Path]::GetTempPath() + "midicoder-install.zip"

try {
    $progressPreference = 'SilentlyContinue'
    Invoke-WebRequest -Uri $downloadUrl -OutFile $tempFile -UseBasicParsing
    $progressPreference = 'Continue'
} catch {
    Write-Host "[ERROR] Download failed: $_" -ForegroundColor Red
    exit 1
}

# Install — ZIP contains midicoder/ folder (COLLECT mode), extract into bin/
New-Item -ItemType Directory -Path $binPath -Force | Out-Null

# Expand to temp first, then move contents into binPath (strip the midicoder/ wrapper)
$tempDir = Join-Path ([System.IO.Path]::GetTempPath()) "midicoder-install-$$"
New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
Expand-Archive -Path $tempFile -DestinationPath $tempDir -Force
Remove-Item $tempFile -Force

# Move contents: midicoder/midicoder.exe → bin/midicoder.exe
$extractedDir = Join-Path $tempDir "midicoder"
if (Test-Path $extractedDir) {
    Get-ChildItem $extractedDir -Recurse -File | ForEach-Object {
        $relPath = $_.FullName.Substring($extractedDir.Length + 1)
        $dest = Join-Path $binPath $relPath
        $destDir = Split-Path $dest -Parent
        if (-not (Test-Path $destDir)) { New-Item -ItemType Directory -Path $destDir -Force | Out-Null }
        Copy-Item $_.FullName $dest -Force
    }
    Get-ChildItem $extractedDir -Directory -Recurse | ForEach-Object {
        $relPath = $_.FullName.Substring($extractedDir.Length + 1)
        $destDir = Join-Path $binPath $relPath
        if (-not (Test-Path $destDir)) { New-Item -ItemType Directory -Path $destDir -Force | Out-Null }
    }
} else {
    # Fallback: flat ZIP (single-file mode)
    Copy-Item "$tempDir\*" $binPath -Recurse -Force
}
Remove-Item $tempDir -Recurse -Force

# Verify exe
$exePath = Join-Path $binPath "midicoder.exe"
if (-not (Test-Path $exePath)) {
    Write-Host "[WARN] Installation complete but .exe not found" -ForegroundColor Yellow
    exit 1
}

# Create .cmd wrapper so 'midicoder' works in CMD too
$cmdWrapper = Join-Path $binPath "midicoder.cmd"
@"
@echo off
"%~dp0midicoder.exe" %*
"@ | Set-Content $cmdWrapper -Encoding ASCII

# Add to PATH (user level)
$currentPath = [Environment]::GetEnvironmentVariable("PATH", "User")
if ($currentPath -notlike "*$binPath*") {
    $newPath = "$binPath;$currentPath"
    [Environment]::SetEnvironmentVariable("PATH", $newPath, "User")
    $env:PATH = "$binPath;$env:PATH"
    Write-Host "[INFO] Added to PATH (user level)" -ForegroundColor Cyan
} else {
    $env:PATH = "$binPath;$env:PATH"
}

# Create Start Menu shortcut
try {
    $startMenu = [Environment]::GetFolderPath("StartMenu")
    $startMenuDir = Join-Path $startMenu "Programs\Midicoder"
    New-Item -ItemType Directory -Path $startMenuDir -Force | Out-Null

    $wsShell = New-Object -ComObject WScript.Shell
    $shortcut = $wsShell.CreateShortcut("$startMenuDir\Midicoder.lnk")
    $shortcut.TargetPath = $exePath
    $shortcut.IconLocation = "$exePath,0"
    $shortcut.WorkingDirectory = $binPath
    $shortcut.Description = "Midicoder CE - Contract Coding Platform"
    $shortcut.Save()

    # Uninstall shortcut in Start Menu
    $uninstallScript = Join-Path $repoRoot "..\scripts\uninstall\uninstall.ps1"
    $uninstallShortcut = $wsShell.CreateShortcut("$startMenuDir\Uninstall Midicoder.lnk")
    $uninstallShortcut.TargetPath = "powershell.exe"
    $uninstallShortcut.Arguments = "-ExecutionPolicy Bypass -File `"$PSScriptRoot\..\uninstall\uninstall.ps1`""
    $uninstallShortcut.WorkingDirectory = $PSScriptRoot
    $uninstallShortcut.Description = "Uninstall Midicoder"
    $uninstallShortcut.Save()

    Write-Host "[INFO] Start Menu shortcuts created" -ForegroundColor Cyan
} catch {
    Write-Host "[WARN] Could not create Start Menu shortcuts: $_" -ForegroundColor Yellow
}

# Create Desktop shortcut
try {
    $desktop = [Environment]::GetFolderPath("Desktop")
    $wsShell = New-Object -ComObject WScript.Shell
    $shortcut = $wsShell.CreateShortcut("$desktop\Midicoder.lnk")
    $shortcut.TargetPath = $exePath
    $shortcut.IconLocation = "$exePath,0"
    $shortcut.WorkingDirectory = $binPath
    $shortcut.Description = "Midicoder CE - Contract Coding Platform"
    $shortcut.Save()
    Write-Host "[INFO] Desktop shortcut created" -ForegroundColor Cyan
} catch {
    Write-Host "[WARN] Could not create Desktop shortcut: $_" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "To use midicoder:"
Write-Host "  1. Open a new terminal"
Write-Host "  2. Run: midicoder"
Write-Host ""
Write-Host "Uninstall: Remove-Item -Recurse -Force $midicoderHome"
Write-Host ""
