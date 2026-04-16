#!/bin/bash
# =============================================================================
# Midicoder Docker Build Orchestration Script
# =============================================================================
# This script orchestrates the Docker-based build process for Midicoder.
# It builds the Docker image and runs the build inside the container.
#
# Usage:
#   ./scripts/build-with-docker.sh [options]
#
# Options:
#   --python-version X.X   Python version to use (default: 3.11)
#   --tag TAG              Docker image tag (default: midicoder-builder:linux)
#   --no-cache             Don't use Docker cache
#   --push                 Push image to registry after build
# =============================================================================

set -e

# =============================================================================
# Default Configuration
# =============================================================================

PYTHON_VERSION="${PYTHON_VERSION:-3.11}"
DOCKER_TAG="${DOCKER_TAG:-midicoder-builder:linux}"
NO_CACHE=false
PUSH=false
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOCKERFILE="$REPO_ROOT/scripts/Dockerfile.build"
OUTPUT_DIR="$REPO_ROOT/dist/linux"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# =============================================================================
# Parse Arguments
# =============================================================================

while [[ $# -gt 0 ]]; do
    case $1 in
        --python-version)
            PYTHON_VERSION="$2"
            shift 2
            ;;
        --tag)
            DOCKER_TAG="$2"
            shift 2
            ;;
        --no-cache)
            NO_CACHE=true
            shift
            ;;
        --push)
            PUSH=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--python-version X.X] [--tag TAG] [--no-cache] [--push]"
            exit 1
            ;;
    esac
done

# =============================================================================
# Check Docker
# =============================================================================

if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed or not in PATH"
    exit 1
fi

log_info "Docker version: $(docker --version)"

# =============================================================================
# Create Output Directory
# =============================================================================

mkdir -p "$OUTPUT_DIR"
log_info "Output directory: $OUTPUT_DIR"

# =============================================================================
# Build Docker Image
# =============================================================================

DOCKER_BUILD_ARGS=(
    -f "$DOCKERFILE"
    -t "$DOCKER_TAG"
    --build-arg PYTHON_VERSION="$PYTHON_VERSION"
)

if [ "$NO_CACHE" = true ]; then
    DOCKER_BUILD_ARGS+=("--no-cache")
fi

log_info "Building Docker image: $DOCKER_TAG"
log_info "Python version: $PYTHON_VERSION"
echo ""

docker build "${DOCKER_BUILD_ARGS[@]}" "$REPO_ROOT"

# =============================================================================
# Run Build in Container
# =============================================================================

log_info "Running build in container..."
echo ""

docker run --rm \
    -v "$REPO_ROOT":"/build:ro" \
    -v "$OUTPUT_DIR":"/output" \
    "$DOCKER_TAG" \
    /bin/bash -c '
        cd /build
        # Copy source files to container
        cp -r midicoder /tmp/build/midicoder 2>/dev/null || true
        cp pyproject.toml /tmp/build/ 2>/dev/null || true
        cp -r scripts /tmp/build/scripts 2>/dev/null || true
        cd /tmp/build
        
        # Run PyInstaller
        python -m PyInstaller \
            --clean \
            --onefile \
            --name midicoder \
            --console \
            --add-data "midicoder:midicoder" \
            --hidden-import=midicoder.cli \
            --hidden-import=midicoder.__main__ \
            --hidden-import=midicoder.commands \
            --additional-hooks-dir=scripts/hooks \
            --distpath=/output \
            midicoder/__main__.py
    '

# =============================================================================
# Post-Process Output
# =============================================================================

if [ -f "$OUTPUT_DIR/midicoder" ]; then
    log_info "Build successful!"
    
    # Make executable
    chmod +x "$OUTPUT_DIR/midicoder"
    
    # Generate checksum
    log_info "Generating checksums..."
    cd "$OUTPUT_DIR"
    sha256sum midicoder > midicoder.sha256
    
    # Create release package
    tar -czf midicoder-linux-bin.tar.gz midicoder
    sha256sum midicoder-linux-bin.tar.gz > midicoder-linux-bin.tar.gz.sha256
    
    echo ""
    echo "========================================="
    echo "  Build Complete!"
    echo "========================================="
    echo ""
    echo "Output files:"
    ls -lh "$OUTPUT_DIR"
    echo ""
    echo "Checksums:"
    cat "$OUTPUT_DIR/midicoder.sha256"
    cat "$OUTPUT_DIR/midicoder-linux-bin.tar.gz.sha256"
    echo ""
else
    log_error "Build failed - executable not found in $OUTPUT_DIR"
    exit 1
fi

# =============================================================================
# Push to Registry (if requested)
# =============================================================================

if [ "$PUSH" = true ]; then
    log_info "Pushing Docker image to registry..."
    docker push "$DOCKER_TAG"
fi