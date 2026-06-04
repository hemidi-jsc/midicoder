#!/bin/bash
# ============================================================
# Midicoder CE - Install Script (Linux/macOS)
# ============================================================
# Downloads the pre-built binary and installs to ~/.midicoder
#
# Usage:
#   curl -sSL https://midicoder.com/install.sh | bash
#
# Options:
#   --force   : Overwrite existing installation
#   --version : Specify version (default: latest)
# ============================================================

set -e

MIDICODER_VERSION="${MIDICODER_VERSION:-1.0.0}"
FORCE="${FORCE:-false}"
MIDICODER_HOME="$HOME/.midicoder"
BIN_PATH="$MIDICODER_HOME/bin"
GITHUB_BASE="https://github.com/hemidi-jsc/midicoder/releases/download"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info()    { echo -e "${CYAN}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $1"; }

echo ""
echo -e "${CYAN}=========================================${NC}"
echo -e "${CYAN}  Midicoder CE Installer v${MIDICODER_VERSION}${NC}"
echo -e "${CYAN}=========================================${NC}"
echo ""

# Detect OS
OS=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)

case "$ARCH" in
    x86_64|amd64)  ARCH="x86_64" ;;
    aarch64|arm64) ARCH="arm64"  ;;
    *) log_error "Unsupported architecture: $ARCH"; exit 1 ;;
esac

log_info "Detected: ${OS} (${ARCH})"

# Determine package name
case "$OS" in
    Linux*)  PACKAGE="midicoder-linux-${ARCH}-bin.tar.gz" ;;
    Darwin*) PACKAGE="midicoder-macos-${ARCH}-bin.tar.gz" ;;
    *)       log_error "Unsupported OS: $OS"; exit 1 ;;
esac

DOWNLOAD_URL="${GITHUB_BASE}/v${MIDICODER_VERSION}/${PACKAGE}"

# Check existing installation
if [ -d "$BIN_PATH" ] && [ "$FORCE" != "true" ]; then
    log_warn "Midicoder already installed at $MIDICODER_HOME"
    echo -n "Overwrite? (y/N) "
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "Cancelled."
        exit 0
    fi
    # Backup
    BACKUP="${MIDICODER_HOME}.backup-$(date +%Y%m%d-%H%M%S)"
    mv "$MIDICODER_HOME" "$BACKUP"
    log_info "Backed up to $BACKUP"
fi

# Download
log_info "Downloading from: $DOWNLOAD_URL"
TEMP_FILE=$(mktemp)

if command -v curl &> /dev/null; then
    curl -sfL "$DOWNLOAD_URL" -o "$TEMP_FILE"
elif command -v wget &> /dev/null; then
    wget -q -O "$TEMP_FILE" "$DOWNLOAD_URL"
else
    log_error "curl or wget required"
    exit 1
fi

# Install
mkdir -p "$BIN_PATH"
tar -xzf "$TEMP_FILE" -C "$BIN_PATH" --strip-components=1
rm -f "$TEMP_FILE"

chmod +x "$BIN_PATH/midicoder"

# Add to PATH
EXPORT_LINE='export PATH="$HOME/.midicoder/bin:$PATH"'
SHELL_RC="$HOME/.bashrc"

if [ -f "$HOME/.zshrc" ]; then
    SHELL_RC="$HOME/.zshrc"
fi

if ! grep -q "midicoder" "$SHELL_RC" 2>/dev/null; then
    echo "" >> "$SHELL_RC"
    echo "# Midicoder" >> "$SHELL_RC"
    echo "$EXPORT_LINE" >> "$SHELL_RC"
    log_info "Added to $SHELL_RC"
fi

export PATH="$BIN_PATH:$PATH"

# Verify
if "$BIN_PATH/midicoder" --version &>/dev/null; then
    log_success "Midicoder installed successfully!"
else
    log_warn "Installation complete but verification failed"
fi

echo ""
echo "To use midicoder:"
echo "  1. Restart your terminal, or run: source $SHELL_RC"
echo "  2. Run: midicoder"
echo ""
echo "Uninstall: rm -rf $MIDICODER_HOME"
echo ""
