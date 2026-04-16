# Building Midicoder Executables

This guide explains how to build standalone Midicoder executables for Windows, macOS, and Linux using Docker.

## Overview

Midicoder executables are built using **PyInstaller**, which bundles:

- Python runtime
- Midicoder source code
- All dependencies

The result is a **single standalone executable** (~50-100MB) that runs without requiring Python installation.

## Build Methods

### Option 1: Docker Build (Recommended)

Docker ensures a consistent build environment across all platforms.

#### Prerequisites

- Docker installed and running
- At least 2GB free disk space

#### Build for Linux

```bash
cd scripts
./build-with-docker.sh --python-version 3.11
```

Output:

```
dist/linux/midicoder                    # Executable
dist/linux/midicoder.sha256            # Checksum
dist/linux/midicoder-linux-bin.tar.gz  # Release package
dist/linux/midicoder-linux-bin.tar.gz.sha256
```

#### Build with Custom Options

```bash
# Specify Python version
./build-with-docker.sh --python-version 3.11

# Use specific Docker image tag
./build-with-docker.sh --tag midicoder-builder:linux-3.11

# Don't use Docker cache
./build-with-docker.sh --no-cache

# Push Docker image to registry after build
./build-with-docker.sh --push
```

#### Manual Docker Build

```bash
# Build Docker image
docker build -f scripts/Dockerfile.build \
  --build-arg PYTHON_VERSION=3.11 \
  -t midicoder-builder:linux .

# Run build in container
docker run --rm \
  -v $(pwd):/build:ro \
  -v $(pwd)/dist/linux:/output \
  midicoder-builder:linux \
  /bin/bash -c '
    cd /tmp/build
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
```

---

### Option 2: Direct Build (Linux/macOS)

Build directly on your machine if you have Python 3.11 installed.

#### Prerequisites

- Python 3.11 installed (for `tree_sitter_languages` compatibility)
- Build tools installed

#### Install Dependencies

```bash
cd scripts
pip install -r requirements.txt
```

#### Build

```bash
# Linux
./build-linux.sh

# macOS
./build-macos.sh  # if exists
```

---

### Option 3: Windows Build

#### Prerequisites

- Python 3.11 installed
- PowerShell 5.0+

#### Build

```powershell
cd scripts
.\build-windows.bat
```

Output:

```
dist/windows/midicoder.exe
```

---

## Dockerfile.build Explained

### Python Version Lock

```dockerfile
ARG PYTHON_VERSION=3.11
FROM python:${PYTHON_VERSION}-slim-bookworm AS builder
```

**Why Python 3.11?**

- `tree_sitter_languages` has pre-built wheels for Python 3.11
- Python 3.13+ requires building from source (unreliable on Windows)
- 3.11 is stable and well-tested

### Build Dependencies

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    pkg-config \
    git \
    wget \
    curl
```

These are required for compiling native dependencies.

### PyInstaller Hook

```dockerfile
COPY scripts/hooks/hook-midicoder.py /build/hook-midicoder.py
```

Custom hook ensures all Midicoder modules are included:

```python
hiddenimports = [
    'midicoder.cli',
    'midicoder.commands.init',
    'midicoder.commands.brief',
    'midicoder.commands.contract',
    # ... all command modules
]
```

---

## Build Output Structure

### Linux/macOS

```
dist/linux/
├── midicoder                          # Executable (~80MB)
├── midicoder.sha256                   # Checksum
├── midicoder-linux-bin.tar.gz         # Release package
└── midicoder-linux-bin.tar.gz.sha256  # Package checksum
```

### Windows

```
dist/windows/
├── midicoder.exe                      # Executable (~100MB)
├── midicoder.exe.sha256               # Checksum
└── midicoder-windows-bin.zip          # Release package
```

---

## Release Package Contents

Each release package contains a **single executable**:

```
midicoder-linux-bin.tar.gz
└── midicoder  # Self-contained executable
```

The installer (`install.sh` or `install.ps1`) downloads this package and extracts it to `~/.midicoder/bin/`.

---

## Verifying Build

### Check Executable

```bash
# Linux/macOS
./dist/linux/midicoder --version

# Windows
dist\windows\midicoder.exe --version
```

Expected output:

```
midicoder 1.0.0
```

### Verify Checksum

```bash
cd dist/linux
sha256sum -c midicoder.sha256
```

### Test Full Functionality

```bash
./dist/linux/midicoder --help
./dist/linux/midicoder init --help
./dist/linux/midicoder contract --help
```

---

## Troubleshooting

### `tree_sitter_languages` Import Error

**Cause:** Python 3.13+ doesn't have pre-built wheels.

**Solution:** Use Python 3.11 in Docker build.

### Build Takes Too Long

**Cause:** First build downloads and compiles dependencies.

**Solution:** Use Docker cache or build with `--no-cache` only when needed.

### Executable is Too Large

**Cause:** PyInstaller includes all dependencies.

**Expected:** 50-100MB is normal for Python executables.

### Missing Hidden Imports

**Symptom:** `ModuleNotFoundError` at runtime.

**Solution:** Add missing modules to `scripts/hooks/hook-midicoder.py`.

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Build Executables

on:
    push:
        tags:
            - "v*"

jobs:
    build-linux:
        runs-on: ubuntu-latest
        steps:
            - uses: actions/checkout@v4

            - name: Build with Docker
              run: |
                  ./scripts/build-with-docker.sh --python-version 3.11

            - name: Upload artifacts
              uses: actions/upload-artifact@v4
              with:
                  name: midicoder-linux
                  path: dist/linux/
```

---

## Performance Considerations

### Build Time

| Platform | First Build | Cached Build |
| -------- | ----------- | ------------ |
| Linux    | 5-10 min    | 2-3 min      |
| Windows  | 10-15 min   | 3-5 min      |
| macOS    | 8-12 min    | 2-4 min      |

### Executable Size

| Platform | Size   |
| -------- | ------ |
| Linux    | ~80MB  |
| Windows  | ~100MB |
| macOS    | ~85MB  |

### Runtime Performance

- **Startup time:** ~500ms (cold start)
- **Command execution:** Same as native Python
- **Memory usage:** ~100MB baseline

---

## Best Practices

1. **Always use Docker for production builds** - Ensures consistency
2. **Lock Python version** - Use 3.11 for compatibility
3. **Verify checksums** - Always generate and verify SHA256
4. **Test executables** - Run on clean systems before release
5. **Sign executables** - Use code signing for Windows/macOS

---

## Next Steps

After building:

1. **Test locally:** Run executables on clean systems
2. **Create release:** Upload to GitHub Releases
3. **Update installers:** Point to new release URL
4. **Notify users:** Announce new version

---

**See also:**

- [Dockerfile.build](../../scripts/Dockerfile.build) - Docker build configuration
- [build-with-docker.sh](../../scripts/build-with-docker.sh) - Build orchestration script
