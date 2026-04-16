#!/bin/bash
# =============================================================================
# Midicoder Linux Build Script
# =============================================================================
# This script builds the Midicoder executable for Linux using PyInstaller.
# Can be run directly on Linux host or inside Docker container.
#
# Prerequisites:
#   - Python 3.11 installed (for tree_sitter_languages compatibility)
#   - Dependencies installed via: pip install -r requirements.txt
#
# Usage:
#   # Direct on host
#   ./scripts/build-linux.sh
#   
#   # Inside Docker
#   docker run --rm midicoder-builder:linux
# =============================================================================

set -e

# =============================================================================
# Configuration
# =============================================================================

PYTHON_CMD="${PYTHON_CMD:-python3}"
BUILD_DIR="${BUILD_DIR:-/build}"
OUTPUT_DIR="${OUTPUT_DIR:-/output}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# =============================================================================
# Main Build Process
# =============================================================================

echo "========================================="
echo "  Midicoder Linux Builder"
echo "========================================="
echo ""

# Change to build directory
cd "$BUILD_DIR"

# Check Python version
log_info "Checking Python version..."
PYTHON_VERSION=$($PYTHON_CMD --version)
echo "  $PYTHON_VERSION"

# Check if dependencies are installed
log_info "Checking dependencies..."
if ! $PYTHON_CMD -c "import pyinstaller" 2>/dev/null; then
    log_error "PyInstaller not installed. Run: pip install -r requirements.txt"
    exit 1
fi

# Create output directory
log_info "Creating output directory: $OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

# Build with PyInstaller
log_info "Building Midicoder executable..."
log_info "This may take a few minutes..."
echo ""

$PYTHON_CMD -m PyInstaller \
    --clean \
    --onefile \
    --name midicoder \
    --console \
    --add-data "midicoder:midicoder" \
    --hidden-import=midicoder.cli \
    --hidden-import=midicoder.__main__ \
    --hidden-import=midicoder.commands \
    --hidden-import=midicoder.commands.init \
    --hidden-import=midicoder.commands.brief \
    --hidden-import=midicoder.commands.contract \
    --hidden-import=midicoder.commands.ir \
    --hidden-import=midicoder.commands.code \
    --hidden-import=midicoder.commands.version \
    --hidden-import=midicoder.commands.config \
    --hidden-import=midicoder.commands.index \
    --hidden-import=midicoder.commands.runtime \
    --hidden-import=typer \
    --hidden-import=pydantic \
    --hidden-import=ruamel.yaml \
    --hidden-import=rich \
    --hidden-import=questionary \
    --hidden-import=tree_sitter \
    --hidden-import=tree_sitter_languages \
    --additional-hooks-dir=scripts/hooks \
    --distpath="$OUTPUT_DIR" \
    midicoder/__main__.py

# Check if build succeeded
if [ -f "$OUTPUT_DIR/midicoder" ]; then
    log_info "Build successful!"
    echo ""
    echo "Output: $OUTPUT_DIR/midicoder"
    ls -lh "$OUTPUT_DIR/midicoder"
    
    # Make executable
    chmod +x "$OUTPUT_DIR/midicoder"
    
    # Generate checksum
    log_info "Generating SHA256 checksum..."
    sha256sum "$OUTPUT_DIR/midicoder" > "$OUTPUT_DIR/midicoder.sha256"
    cat "$OUTPUT_DIR/midicoder.sha256"
    
    # Create tar.gz package
    log_info "Creating release package..."
    cd "$OUTPUT_DIR"
    tar -czf midicoder-linux-bin.tar.gz midicoder
    sha256sum midicoder-linux-bin.tar.gz > midicoder-linux-bin.tar.gz.sha256
    
    echo ""
    echo "========================================="
    echo "  Build Complete!"
    echo "========================================="
    echo ""
    echo "Release packages:"
    echo "  - $OUTPUT_DIR/midicoder (executable)"
    echo "  - $OUTPUT_DIR/midicoder-linux-bin.tar.gz (release package)"
    echo ""
else
    log_error "Build failed - executable not found"
    exit 1
fi