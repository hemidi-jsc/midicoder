#!/bin/bash
# ============================================================
# Midicoder Linux/macOS Uninstall Script
# ============================================================
# This script uninstalls Midicoder from the system
#
# Usage:
#   bash uninstall.sh
#
# Options:
#   --sandbox     Uninstall from ./sandbox/.midicoder instead of ~/.midicoder
#   --keep-config Keep the ~/.midicoder directory (only removes from PATH)
# ============================================================

set -e

# ============================================================
# Configuration
# ============================================================

SANDBOX=false
KEEP_CONFIG=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --sandbox)
            SANDBOX=true
            shift
            ;;
        --keep-config)
            KEEP_CONFIG=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--sandbox] [--keep-config]"
            exit 1
            ;;
    esac
done

# Determine installation path
if [ "$SANDBOX" = true ]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    MIDICODER_HOME="$(cd "$SCRIPT_DIR/../.." && pwd)/sandbox/.midicoder"
    IS_SANDBOX=true
else
    MIDICODER_HOME="$HOME/.midicoder"
    IS_SANDBOX=false
fi

BIN_PATH="$MIDICODER_HOME/bin"

# ============================================================
# Colors
# ============================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ============================================================
# Helper Functions
# ============================================================

log_info() {
    echo -e "${CYAN}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ============================================================
# Uninstallation Functions
# ============================================================

show_header() {
    echo -e "${CYAN}=========================================${NC}"
    echo -e "${CYAN}  Midicoder Uninstaller${NC}"
    echo -e "${CYAN}=========================================${NC}"
    echo ""
    
    if [ "$IS_SANDBOX" = true ]; then
        log_warning "[SANDBOX MODE] Uninstalling from: $MIDICODER_HOME"
        echo ""
    fi
    
    echo "Installation directory: $MIDICODER_HOME"
    echo ""
}

test_installation_exists() {
    if [ ! -d "$MIDICODER_HOME" ]; then
        log_warning "Midicoder is not installed at $MIDICODER_HOME"
        echo ""
        echo "Nothing to uninstall."
        exit 0
    fi
    
    if [ ! -d "$BIN_PATH" ]; then
        log_warning "Midicoder bin directory not found at $BIN_PATH"
        echo ""
        echo "Nothing to uninstall."
        exit 0
    fi
    
    log_info "Found Midicoder installation."
}

remove_from_path() {
    if [ "$IS_SANDBOX" = true ]; then
        log_warning "[SANDBOX] Not modifying system PATH (sandbox mode)"
        return
    fi
    
    log_info "Removing from PATH..."
    
    # Remove from common shell config files
    for CONFIG_FILE in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.profile" "$HOME/.bash_profile"; do
        if [ -f "$CONFIG_FILE" ]; then
            if grep -q "MIDICODER_HOME" "$CONFIG_FILE" 2>/dev/null; then
                # Remove midicoder-related lines
                sed -i '/MIDICODER_HOME/d' "$CONFIG_FILE" 2>/dev/null || \
                sed -i.bak '/MIDICODER_HOME/d' "$CONFIG_FILE" 2>/dev/null || true
                sed -i '/Midicoder installation/d' "$CONFIG_FILE" 2>/dev/null || \
                sed -i.bak '/Midicoder installation/d' "$CONFIG_FILE" 2>/dev/null || true
                log_info "Removed from $CONFIG_FILE"
            fi
        fi
    done
    
    log_success "Removed from shell configs."
}

remove_installation_directory() {
    if [ "$KEEP_CONFIG" = true ]; then
        log_warning "Keeping configuration directory (--keep-config specified)"
        return
    fi
    
    log_info "Removing installation directory..."
    
    rm -rf "$MIDICODER_HOME"
    log_success "Installation directory removed."
}

remove_backup_directories() {
    log_info "Checking for backup directories..."
    
    # Check sandbox and home parent directories
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
    SANDBOX_PATH="$REPO_ROOT/sandbox"
    
    SEARCH_PATHS=("$SANDBOX_PATH" "$(dirname "$MIDICODER_HOME")")
    PATTERN="*.backup-*"
    
    for SEARCH_PATH in "${SEARCH_PATHS[@]}"; do
        if [ -d "$SEARCH_PATH" ]; then
            BACKUPS=("$SEARCH_PATH"/.midicoder.backup-*)
            if [ -e "${BACKUPS[0]}" ]; then
                log_info "Found ${#BACKUPS[@]} backup directory/directories"
                
                if [ "$KEEP_CONFIG" != true ]; then
                    for BACKUP in "${BACKUPS[@]}"; do
                        if [ -d "$BACKUP" ]; then
                            rm -rf "$BACKUP"
                            log_success "Removed backup: $(basename "$BACKUP")"
                        fi
                    done
                fi
            fi
        fi
    done
}

print_completion() {
    echo ""
    echo -e "${GREEN}=========================================${NC}"
    echo -e "${GREEN}  Uninstallation Complete!${NC}"
    echo -e "${GREEN}=========================================${NC}"
    echo ""
    
    if [ "$KEEP_CONFIG" = true ]; then
        log_warning "Configuration directory preserved at: $MIDICODER_HOME"
        echo ""
        echo "To remove it manually:"
        echo "  rm -rf $MIDICODER_HOME"
        echo ""
    fi
    
    echo "Note: You may need to restart your terminal"
    echo "      for PATH changes to take effect."
    echo ""
}

# ============================================================
# Main
# ============================================================

main() {
    show_header
    test_installation_exists
    remove_from_path
    remove_installation_directory
    remove_backup_directories
    print_completion
}

# Run
main "$@"