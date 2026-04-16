# ============================================================
# Midicoder Windows Install Script
# ============================================================
# This script installs Midicoder CLI to %USERPROFILE%\.midicoder
#
# Prerequisites:
#   - PowerShell 5.0 or higher
#   - Internet connection (to download the binary)
#
# Usage:
#   powershell -ExecutionPolicy Bypass -c "irm https://midicoder.com/install.ps1 | iex"
#
# Options:
#   -Force      : Overwrite existing installation without prompt
#   -Sandbox    : Install to ./sandbox/.midicoder instead of %USERPROFILE%
# ============================================================

param(
    [switch]$Force,
    [switch]$Sandbox
)

# ============================================================
# Configuration
# ============================================================

$MIDICODER_VERSION = "1.0.0"
$MIDICODER_REPO = "hemidi-jsc/midicoder"
$GITHUB_RELEASE_URL = "https://github.com/$MIDICODER_REPO/releases/download/v$MIDICODER_VERSION"
$DOWNLOAD_URL = "$GITHUB_RELEASE_URL/midicoder-windows-bin.zip"

# Determine installation path
if ($Sandbox) {
    # Get absolute path to sandbox/.midicoder
    $scriptDir = (Get-Item $PSScriptRoot).FullName
    $repoRoot = (Get-Item "$scriptDir\..\..").FullName
    $MIDICODER_HOME = Join-Path $repoRoot "sandbox\.midicoder"
    $IS_SANDBOX = $true
    
    # For sandbox mode, use local test package if available
    $LOCAL_PACKAGE = Join-Path $repoRoot "sandbox\midicoder-windows-bin.zip"
    if (Test-Path $LOCAL_PACKAGE) {
        $DOWNLOAD_URL = $LOCAL_PACKAGE
        $USE_LOCAL_PACKAGE = $true
    }
} else {
    $MIDICODER_HOME = "$env:USERPROFILE\.midicoder"
    $IS_SANDBOX = $false
    $USE_LOCAL_PACKAGE = $false
}

$BIN_PATH = Join-Path $MIDICODER_HOME "bin"

# ============================================================
# Helper Functions
# ============================================================

function Write-Green { param($Message) Write-Host $Message -ForegroundColor Green }
function Write-Red { param($Message) Write-Host $Message -ForegroundColor Red }
function Write-Yellow { param($Message) Write-Host $Message -ForegroundColor Yellow }
function Write-Cyan { param($Message) Write-Host $Message -ForegroundColor Cyan }

# ============================================================
# Installation Functions
# ============================================================

function Show-Header {
    Write-Cyan "========================================="
    Write-Cyan "  Midicoder Installer v$MIDICODER_VERSION"
    Write-Cyan "========================================="
    Write-Host ""
    
    if ($IS_SANDBOX) {
        Write-Yellow "[SANDBOX MODE] Installing to: $MIDICODER_HOME"
        Write-Host ""
    }
}

function Test-ExistingInstallation {
    if (Test-Path $BIN_PATH) {
        Write-Yellow "Midicoder is already installed at $MIDICODER_HOME"
        
        if (-not $Force) {
            $response = Read-Host "Do you want to overwrite? (y/N)"
            if ($response -ne "y" -and $response -ne "Y") {
                Write-Host "Installation cancelled."
                exit 0
            }
        }
        
        # Backup old installation
        $backupPath = "$MIDICODER_HOME.backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
        Write-Host "Backing up existing installation to $backupPath..."
        Copy-Item -Path $MIDICODER_HOME -Destination $backupPath -Recurse -Force
        Remove-Item -Path $MIDICODER_HOME -Recurse -Force
    }
}

function Download-Binary {
    Write-Host "Downloading Midicoder v$MIDICODER_VERSION..."
    
    $downloadFile = "midicoder-windows-bin.zip"
    $downloadPath = Join-Path $env:TEMP $downloadFile
    
    try {
        $progressPreference = 'SilentlyContinue'
        Invoke-WebRequest -Uri $DOWNLOAD_URL -OutFile $downloadPath -UseBasicParsing
        $progressPreference = 'Continue'
        Write-Green "Download complete."
    }
    catch {
        Write-Red "Error downloading: $_"
        Write-Red ""
        Write-Red "Please check your internet connection and try again."
        Write-Red "Or download manually from: $DOWNLOAD_URL"
        exit 1
    }
    
    return $downloadPath
}

function Verify-Download {
    param($DownloadPath)
    
    Write-Host "Verifying download..."
    
    if (-not (Test-Path $DownloadPath)) {
        Write-Red "Error: Downloaded file not found"
        exit 1
    }
    
    $fileSize = (Get-Item $DownloadPath).Length
    # For sandbox mode, accept smaller test packages
    $minSize = if ($USE_LOCAL_PACKAGE) { 100 } else { 1000000 }
    if ($fileSize -lt $minSize) {
        Write-Red "Error: Downloaded file size ($fileSize bytes) seems too small"
        exit 1
    }
    
    if ($USE_LOCAL_PACKAGE) {
        Write-Green "Using local test package ($fileSize bytes)"
    } else {
        Write-Green "Download verified ($([math]::Round($fileSize / 1MB, 2)) MB)"
    }
}

function Install-Binary {
    param($DownloadPath)
    
    Write-Host "Installing Midicoder..."
    
    # Create directory structure
    New-Item -ItemType Directory -Path $BIN_PATH -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $MIDICODER_HOME "cache") -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $MIDICODER_HOME "logs") -Force | Out-Null
    
    # Extract binary
    try {
        Expand-Archive -Path $DownloadPath -DestinationPath $BIN_PATH -Force
        Write-Green "Binary extracted."
    }
    catch {
        Write-Red "Error extracting archive: $_"
        exit 1
    }
    
    # Clean up download
    if (Test-Path $DownloadPath) {
        Remove-Item -Path $DownloadPath -Force
    }
}

function Add-ToPath {
    $binPath = $BIN_PATH
    
    if ($IS_SANDBOX) {
        # For sandbox mode, only add to current session
        $env:PATH = "$binPath;" + $env:PATH
        Write-Yellow "[SANDBOX] Added to current session PATH only."
        return
    }
    
    # Get current PATH (User level)
    $currentPath = [Environment]::GetEnvironmentVariable("PATH", "User")
    
    # Check if already in PATH
    if ($currentPath -like "*$binPath*") {
        Write-Yellow "Already in PATH."
        # Also add to current session
        $env:PATH = "$binPath;" + $env:PATH
        return
    }
    
    # Add to PATH (User level - doesn't require admin)
    $newPath = "$binPath;$currentPath"
    [Environment]::SetEnvironmentVariable("PATH", $newPath, "User")
    
    # Update current session
    $env:PATH = $newPath
    
    Write-Green "Added to PATH (user level)."
}

function Verify-Installation {
    Write-Host "Verifying installation..."
    
    $midicoderPath = Join-Path $BIN_PATH "midicoder.exe"
    
    if (-not (Test-Path $midicoderPath)) {
        Write-Red "Error: midicoder.exe not found at $midicoderPath"
        exit 1
    }
    
    try {
        $versionOutput = & $midicoderPath --version 2>&1
        if ($versionOutput -and $versionOutput -notlike "*error*" -and $versionOutput -notlike "*Error*") {
            Write-Green "Midicoder installed successfully!"
            Write-Green "  $versionOutput"
            return $true
        } else {
            Write-Yellow "Installation complete but verification failed"
            Write-Yellow "  Output: $versionOutput"
            return $false
        }
    }
    catch {
        Write-Yellow "Installation complete but verification failed: $_"
        return $false
    }
}

function Print-Usage {
    Write-Host ""
    Write-Green "========================================="
    Write-Green "  Installation Complete!"
    Write-Green "========================================="
    Write-Host ""
    
    if ($IS_SANDBOX) {
        Write-Host "To use midicoder in sandbox mode:"
        Write-Host "  1. Add to PATH (current session):"
        Write-Host "     $env:PATH = '$BIN_PATH';$env:PATH"
        Write-Host ""
        Write-Host "  2. Or run directly:"
        Write-Host "     $BIN_PATH\midicoder.exe --version"
        Write-Host ""
    }
    else {
        Write-Host "To use midicoder:"
        Write-Host "  1. Open a new PowerShell/Command Prompt window"
        Write-Host "     (or run: $env:PATH = [Environment]::GetEnvironmentVariable('PATH','User') + $env:PATH)"
        Write-Host ""
        Write-Host "  2. Try running:"
        Write-Host "     midicoder --version"
        Write-Host "     midicoder --help"
        Write-Host "     midicoder init"
        Write-Host ""
    }
    
    Write-Host "Installation directory: $MIDICODER_HOME"
    Write-Host "Documentation: https://midicoder.com/docs"
    Write-Host ""
    
    Write-Host "To uninstall:"
    Write-Host "  powershell -ExecutionPolicy Bypass -File $MIDICODER_HOME\..\uninstall\uninstall.ps1"
    Write-Host ""
}

# ============================================================
# Main
# ============================================================

function Main {
    Show-Header
    Test-ExistingInstallation
    $downloadPath = Download-Binary
    Verify-Download -DownloadPath $downloadPath
    Install-Binary -DownloadPath $downloadPath
    Add-ToPath
    $verified = Verify-Installation
    Print-Usage
    
    if (-not $verified) {
        Write-Yellow ""
        Write-Yellow "Note: If midicoder command is not found, please restart your terminal."
    }
}

# Run
Main