#!/bin/bash
# =============================================================================
# Midicoder Linux Build Script
# =============================================================================
# Full release build: Angular → midicoder/frontend/ → PyInstaller binary
#
# Runtime bundled:
#   - Python 3.12.x (exact version from .venv)
#   - FastAPI + uvicorn + all Python dependencies
#   - tree_sitter + tree_sitter_languages (native .so included, UPX excluded)
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
#   ./scripts/build-linux.sh
# =============================================================================

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT_DIR="${REPO_ROOT}/dist/linux"

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

log()  { echo -e "${GREEN}[BUILD]${NC} $1"; }
fail() { echo -e "${RED}[FAIL]${NC} $1"; exit 1; }

cd "$REPO_ROOT"

log "Midicoder Release Builder (Linux)"

# ============================================================================
# Lock: Python from .venv (3.12.x)
# ============================================================================
PYTHON_EXE="$REPO_ROOT/.venv/bin/python"
if [ ! -f "$PYTHON_EXE" ]; then
    fail ".venv not found. Run: uv venv && uv pip install -e ."
fi

PY_VER=$("$PYTHON_EXE" --version)
log "Using Python: $PY_VER"

if [[ ! "$PY_VER" =~ 3\.12 ]]; then
    fail "Python 3.12.x required, got: $PY_VER"
fi

# ============================================================================
# Lock: Node.js (build time only, not bundled)
# ============================================================================
NODE_VER=$(node --version 2>/dev/null) || true
if [ -z "$NODE_VER" ]; then
    fail "Node.js required for Angular build"
fi
log "Using Node.js: $NODE_VER (build time only)"

# Step 1: Build Angular
log "Building Angular frontend..."
cd "$REPO_ROOT/webgui"
npx ng build --configuration=production || fail "Angular build failed"
cd "$REPO_ROOT"

# Step 2: Copy dist to midicoder/frontend/
log "Copying Angular dist to midicoder/frontend/"
rm -rf midicoder/frontend
mkdir -p midicoder/frontend
if [ -d "webgui/dist/webgui/browser" ]; then
    cp -r webgui/dist/webgui/browser/* midicoder/frontend/
elif [ -d "webgui/dist/browser" ]; then
    cp -r webgui/dist/browser/* midicoder/frontend/
else
    fail "Angular dist not found"
fi
touch midicoder/frontend/__init__.py

# Step 3: Check PyInstaller in .venv
"$PYTHON_EXE" -c "import PyInstaller" 2>/dev/null || fail "PyInstaller not in .venv. Run: uv pip install pyinstaller"

# Step 4: Clean old build artifacts (avoids PyInstaller y/N prompt)
rm -rf "$REPO_ROOT/build/midicoder"
rm -rf "$OUTPUT_DIR/midicoder"

mkdir -p "$OUTPUT_DIR"
log "Building with PyInstaller (using .venv Python 3.12)..."
"$PYTHON_EXE" -m PyInstaller \
    --clean \
    "$REPO_ROOT/midicoder.spec" \
    --distpath="$OUTPUT_DIR"

# Step 5: Verify & package
if [ -f "$OUTPUT_DIR/midicoder/midicoder" ]; then
    chmod +x "$OUTPUT_DIR/midicoder/midicoder"
    log "Build successful!"
    ls -lh "$OUTPUT_DIR/midicoder/midicoder"

    cd "$OUTPUT_DIR"
    sha256sum midicoder/midicoder > midicoder.sha256
    tar -czf midicoder-linux-bin.tar.gz midicoder
    sha256sum midicoder-linux-bin.tar.gz > midicoder-linux-bin.tar.gz.sha256
    log "Package: midicoder-linux-bin.tar.gz"
else
    fail "Build failed - executable not found"
fi

# Cleanup: remove frontend/ (build artifact)
rm -rf midicoder/frontend
log "Cleaned up midicoder/frontend/"
