# ============================================================
# Midicoder Windows Uninstall Script
# ============================================================
# This script uninstalls Midicoder from the system
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File uninstall.ps1
#
# Options:
#   -Sandbox    : Uninstall from ./sandbox/.midicoder instead of %USERPROFILE%
#   -KeepConfig : Keep the ~/.midicoder directory (only removes from PATH)
# ============================================================

param(
    [switch]$Sandbox,
    [switch]$KeepConfig
)

# ============================================================
# Configuration
# ============================================================

if ($Sandbox) {
    $MIDICODER_HOME = Join-Path $PSScriptRoot "..\..\sandbox\.midicoder"
    $MIDICODER_HOME = (Resolve-Path $MIDICODER_HOME).Path
    $IS_SANDBOX = $true
} else {
    $MIDICODER_HOME = "$env:USERPROFILE\.midicoder"
    $IS_SANDBOX = $false
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
# Uninstallation Functions
# ============================================================

function Show-Header {
    Write-Cyan "========================================="
    Write-Cyan "  Midicoder Uninstaller"
    Write-Cyan "========================================="
    Write-Host ""
    
    if ($IS_SANDBOX) {
        Write-Yellow "[SANDBOX MODE] Uninstalling from: $MIDICODER_HOME"
        Write-Host ""
    }
    
    Write-Host "Installation directory: $MIDICODER_HOME"
    Write-Host ""
}

function Test-InstallationExists {
    if (-not (Test-Path $MIDICODER_HOME)) {
        Write-Yellow "Midicoder is not installed at $MIDICODER_HOME"
        Write-Host ""
        Write-Host "Nothing to uninstall."
        exit 0
    }
    
    if (-not (Test-Path $BIN_PATH)) {
        Write-Yellow "Midicoder bin directory not found at $BIN_PATH"
        Write-Host ""
        Write-Host "Nothing to uninstall."
        exit 0
    }
    
    Write-Host "Found Midicoder installation."
}

function Remove-FromPath {
    $binPath = $BIN_PATH
    
    if ($IS_SANDBOX) {
        Write-Yellow "[SANDBOX] Not modifying system PATH (sandbox mode)"
        return
    }
    
    Write-Host "Removing from PATH..."
    
    # Get current PATH (User level)
    $currentPath = [Environment]::GetEnvironmentVariable("PATH", "User")
    
    # Remove midicoder from PATH
    $pathEntries = $currentPath.Split(';') | Where-Object { $_ -and $_ -ne $binPath }
    $newPath = $pathEntries -join ';'
    
    [Environment]::SetEnvironmentVariable("PATH", $newPath, "User")
    
    # Update current session
    $env:PATH = $newPath
    
    Write-Green "Removed from PATH (user level)."
}

function Remove-InstallationDirectory {
    if ($KeepConfig) {
        Write-Yellow "Keeping configuration directory (-KeepConfig specified)"
        return
    }
    
    Write-Host "Removing installation directory..."
    
    try {
        Remove-Item -Path $MIDICODER_HOME -Recurse -Force
        Write-Green "Installation directory removed."
    }
    catch {
        Write-Red "Error removing directory: $_"
        Write-Yellow "Please try deleting manually: $MIDICODER_HOME"
    }
}

function Remove-BackupDirectories {
    Write-Host "Checking for backup directories..."
    
    $sandboxPath = Join-Path $PSScriptRoot "..\..\sandbox"
    $homeParent = Split-Path $MIDICODER_HOME -Parent
    
    $searchPaths = @($sandboxPath, $homeParent)
    $pattern = "*.backup-*"
    
    foreach ($searchPath in $searchPaths) {
        if (Test-Path $searchPath) {
            $backups = Get-ChildItem -Path $searchPath -Filter $pattern -Directory -ErrorAction SilentlyContinue
            if ($backups) {
                Write-Host "Found $($backups.Count) backup directory/directories"
                
                if (-not $KeepConfig) {
                    foreach ($backup in $backups) {
                        try {
                            Remove-Item -Path $backup.FullName -Recurse -Force
                            Write-Green "Removed backup: $($backup.Name)"
                        }
                        catch {
                            Write-Yellow "Could not remove backup: $($backup.Name)"
                        }
                    }
                }
            }
        }
    }
}

function Print-Completion {
    Write-Host ""
    Write-Green "========================================="
    Write-Green "  Uninstallation Complete!"
    Write-Green "========================================="
    Write-Host ""
    
    if ($KeepConfig) {
        Write-Yellow "Configuration directory preserved at: $MIDICODER_HOME"
        Write-Host ""
        Write-Host "To remove it manually:"
        Write-Host "  rmdir /s /q `$MIDICODER_HOME"
        Write-Host ""
    }
    
    Write-Host "Note: You may need to restart your terminal"
    Write-Host "      for PATH changes to take effect."
    Write-Host ""
}

# ============================================================
# Main
# ============================================================

function Main {
    Show-Header
    Test-InstallationExists
    Remove-FromPath
    Remove-InstallationDirectory
    Remove-BackupDirectories
    Print-Completion
}

# Run
Main