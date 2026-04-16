#!/bin/bash
# ============================================================
# Midicoder Linux/macOS Install Script
# ============================================================
# This script installs Midicoder CLI to ~/.midicoder
#
# Prerequisites:
#   - curl or wget
#   - tar
#
# Usage:
#   curl -o- https://midicoder.com/install.sh | bash
#   wget -qO- https://midicoder.com/install.sh | bash
#
# Options:
#   --force         Overwrite existing installation without prompt
#   --sandbox       Install to ./sandbox/.midicoder instead of ~/.midicoder
#   --version X.X.X Specify version to install (default: 1.0.0)
# ============================================================

set -e

# ============================================================
# Configuration
# ============================================================

MIDICODER_VERSION="${MIDICODER_VERSION:-1.0.0}"
MIDICODER_REPO="hemidi-jsc/midicoder"
GITHUB_RELEASE_URL="https://github.com/${MIDICODER_REPO}/releases/download/v${MIDICODER_VERSION}"

# Parse arguments
FORCE=false
SANDBOX=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --force)
            FORCE=true
            shift
            ;;
        --sandbox)
            SANDBOX=true
            shift
            ;;
        --version)
            MIDICODER_VERSION="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--force] [--sandbox] [--version X.X.X]"
            exit 1
            ;;
    esac
done

# Determine installation path
if [ "$SANDBOX" = true ]; then
    # Get the directory where this script is located, then go to sandbox
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
# OS Detection
# ============================================================

detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        ARCH=$(uname -m)
        if [ "$ARCH" = "arm64" ]; then
            OS="macos-arm64"
        else
            OS="macos"
        fi
        log_info "Detected OS: macOS ($ARCH)"
    elif [[ -f /etc/debian_version ]]; then
        OS="linux"
        ARCH=$(uname -m)
        log_info "Detected OS: Debian/Ubuntu Linux ($ARCH)"
    elif [[ -f /etc/redhat-release ]]; then
        OS="linux"
        ARCH=$(uname -m)
        log_info "Detected OS: RedHat/CentOS Linux ($ARCH)"
    elif [[ -f /etc/arch-release ]]; then
        OS="linux"
        ARCH=$(uname -m)
        log_info "Detected OS: Arch Linux ($ARCH)"
    else
        OS="linux"
        ARCH=$(uname -m)
        log_warning "Detected OS: Generic Unix/Linux ($ARCH)"
    fi
}

# ============================================================
# Installation Functions
# ============================================================

show_header() {
    echo -e "${CYAN}=========================================${NC}"
    echo -e "${CYAN}  Midicoder Installer v${MIDICODER_VERSION}${NC}"
    echo -e "${CYAN}=========================================${NC}"
    echo ""
    
    if [ "$IS_SANDBOX" = true ]; then
        log_warning "[SANDBOX MODE] Installing to: $MIDICODER_HOME"
        echo ""
    fi
}

check_existing_installation() {
    if [ -d "$BIN_PATH" ]; then
        log_warning "Midicoder is already installed at $MIDICODER_HOME"
        
        if [ "$FORCE" != true ]; then
            echo -n "Do you want to overwrite? (y/N) "
            read -r response
            if [[ ! "$response" =~ ^[Yy]$ ]]; then
                echo "Installation cancelled."
                exit 0
            fi
        fi
        
        # Backup old installation
        BACKUP_PATH="${MIDICODER_HOME}.backup-$(date +%Y%m%d-%H%M%S)"
        log_info "Backing up existing installation to $BACKUP_PATH..."
        cp -r "$MIDICODER_HOME" "$BACKUP_PATH"
        rm -rf "$MIDICODER_HOME"
        log_success "Backup created."
    fi
}

download_binary() {
    log_info "Downloading Midicoder v${MIDICODER_VERSION}..."
    
    DOWNLOAD_FILE="midicoder-${OS}-bin.tar.gz"
    DOWNLOAD_URL="${GITHUB_RELEASE_URL}/${DOWNLOAD_FILE}"
    
    # Check for curl or wget
    if command -v curl &> /dev/null; then
        curl -sfL "$DOWNLOAD_URL" -o "$DOWNLOAD_FILE"
        log_success "Download complete (curl)."
    elif command -v wget &> /dev/null; then
        wget -q -O "$DOWNLOAD_FILE" "$DOWNLOAD_URL"
        log_success "Download complete (wget)."
    else
        log_error "curl or wget is required to download the binary"
        log_error "Please install curl or wget and try again"
        log_error "Or download manually from: $DOWNLOAD_URL"
        exit 1
    fi
    
    # Verify download
    if [ ! -f "$DOWNLOAD_FILE" ]; then
        log_error "Downloaded file not found"
        exit 1
    fi
    
    FILE_SIZE=$(stat -f%z "$DOWNLOAD_FILE" 2>/dev/null || stat -c%s "$DOWNLOAD_FILE" 2>/dev/null)
    if [ "$FILE_SIZE" -lt 1000000 ]; then
        log_error "Downloaded file size ($FILE_SIZE bytes) seems too small"
        rm -f "$DOWNLOAD_FILE"
        exit 1
    fi
    
    log_success "Download verified ($FILE_SIZE bytes)"
    
    echo "$DOWNLOAD_FILE"
}

install_binary() {
    local DOWNLOAD_FILE="$1"
    
    log_info "Installing Midicoder..."
    
    # Create directory structure
    mkdir -p "$BIN_PATH"
    mkdir -p "$MIDICODER_HOME/cache"
    mkdir -p "$MIDICODER_HOME/logs"
    
    # Extract binary
    if tar -tzf "$DOWNLOAD_FILE" &> /dev/null; then
        # Archive contains midicoder file directly
        tar -xzf "$DOWNLOAD_FILE" -C "$BIN_PATH" --strip-components=1 2>/dev/null || \
        tar -xzf "$DOWNLOAD_FILE" -C "$BIN_PATH" 2>/dev/null || \
        tar -xzf "$DOWNLOAD_FILE" -C "$MIDICODER_HOME" 2>/dev/null || true
        
        # Check if binary is in bin or root
        if [ -f "$BIN_PATH/midicoder" ]; then
            chmod +x "$BIN_PATH/midicoder"
        elif [ -f "$MIDICODER_HOME/midicoder" ]; then
            mv "$MIDICODER_HOME/midicoder" "$BIN_PATH/midicoder"
            chmod +x "$BIN_PATH/midicoder"
        else
            log_error "Could not find midicoder binary in archive"
            exit 1
        fi
    else
        log_error "Failed to extract archive"
        exit 1
    fi
    
    log_success "Binary installed."
    
    # Clean up download
    rm -f "$DOWNLOAD_FILE"
}

setup_path() {
    if [ "$IS_SANDBOX" = true ]; then
        # For sandbox mode, only add to current session
        export PATH="$BIN_PATH:$PATH"
        log_warning "[SANDBOX] Added to current session PATH only."
        echo ""
        echo "To use midicoder, run:"
        echo "  export PATH=\"$BIN_PATH:\$PATH\""
        echo ""
        return
    fi
    
    # Add to shell profile
    EXPORT_LINE='export MIDICODER_HOME="$HOME/.midicoder"'
    PATH_LINE='export PATH="$MIDICODER_HOME/bin:$PATH"'
    
    # Check common shell config files
    for CONFIG_FILE in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.profile" "$HOME/.bash_profile"; do
        if [ -f "$CONFIG_FILE" ]; then
            if ! grep -q "MIDICODER_HOME" "$CONFIG_FILE" 2>/dev/null; then
                echo "" >> "$CONFIG_FILE"
                echo "# Midicoder installation" >> "$CONFIG_FILE"
                echo "$EXPORT_LINE" >> "$CONFIG_FILE"
                echo "$PATH_LINE" >> "$CONFIG_FILE"
                log_info "Added to $CONFIG_FILE"
            fi
        fi
    done
    
    # Add to current session
    export MIDICODER_HOME="$HOME/.midicoder"
    export PATH="$BIN_PATH:$PATH"
    
    log_success "PATH configured."
}

verify_installation() {
    log_info "Verifying installation..."
    
    if [ ! -x "$BIN_PATH/midicoder" ]; then
        log_error "midicoder binary not found or not executable at $BIN_PATH/midicoder"
        exit 1
    fi
    
    VERSION_OUTPUT=$("$BIN_PATH/midicoder" --version 2>/dev/null || echo "")
    
    if [ -n "$VERSION_OUTPUT" ] && [[ ! "$VERSION_OUTPUT" =~ error ]] && [[ ! "$VERSION_OUTPUT" =~ Error ]]; then
        log_success "✓ Midicoder installed successfully!"
        echo "  $VERSION_OUTPUT"
        return 0
    else
        log_warning "⚠ Installation complete but verification failed"
        log_warning "  Output: $VERSION_OUTPUT"
        return 1
    fi
}

print_usage() {
    echo ""
    echo -e "${GREEN}=========================================${NC}"
    echo -e "${GREEN}  Installation Complete!${NC}"
    echo -e "${GREEN}=========================================${NC}"
    echo ""
    
    if [ "$IS_SANDBOX" = true ]; then
        echo "To use midicoder in sandbox mode:"
        echo "  1. The PATH has been updated for this session"
        echo ""
        echo "  2. Try running:"
        echo "     midicoder --version"
        echo "     midicoder --help"
        echo ""
    else
        echo "To use midicoder:"
        echo "  1. Restart your terminal, OR run:"
        echo "     source $HOME/.bashrc   # for bash"
        echo "     source $HOME/.zshrc    # for zsh"
        echo ""
        echo "  2. Try running:"
        echo "     midicoder --version"
        echo "     midicoder --help"
        echo "     midicoder init"
        echo ""
    fi
    
    echo "Installation directory: $MIDICODER_HOME"
    echo "Documentation: https://midicoder.com/docs"
    echo ""
    echo "To uninstall:"
    echo "  bash $MIDICODER_HOME/../uninstall/uninstall.sh"
    echo ""
}

# ============================================================
# Main
# ============================================================

main() {
    show_header
    detect_os
    check_existing_installation
    DOWNLOAD_FILE=$(download_binary)
    install_binary "$DOWNLOAD_FILE"
    setup_path
    verify_installation || true
    print_usage
}

# Run
main "$@"