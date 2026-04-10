# Build Executables Midicoder

Hướng dẫn này giải thích cách build standalone Midicoder executables cho Windows, macOS và Linux sử dụng Docker.

## Tổng Quan

Midicoder executables được build bằng **PyInstaller**, bundle:

- Python runtime
- Midicoder source code
- Tất cả dependencies

Kết quả là một **single standalone executable** (~50-100MB) chạy được mà không cần cài đặt Python.

## Phương Pháp Build

### Option 1: Docker Build (Khuyến Nghị)

Docker đảm bảo môi trường build nhất quán trên mọi platform.

#### Yêu Cầu

- Docker đã cài đặt và chạy
- Ít nhất 2GB disk space trống

#### Build cho Linux

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

#### Build với Tùy Chọn Tùy Chỉnh

```bash
# Chỉ định Python version
./build-with-docker.sh --python-version 3.11

# Dùng Docker image tag cụ thể
./build-with-docker.sh --tag midicoder-builder:linux-3.11

# Không dùng Docker cache
./build-with-docker.sh --no-cache

# Push Docker image lên registry sau build
./build-with-docker.sh --push
```

#### Docker Build Thủ Công

```bash
# Build Docker image
docker build -f scripts/Dockerfile.build \
  --build-arg PYTHON_VERSION=3.11 \
  -t midicoder-builder:linux .

# Chạy build trong container
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

Build trực tiếp trên máy của bạn nếu đã có Python 3.11.

#### Yêu Cầu

- Python 3.11 đã cài đặt (cho `tree_sitter_languages` compatibility)
- Build tools đã cài đặt

#### Cài Dependencies

```bash
cd scripts
pip install -r requirements.txt
```

#### Build

```bash
# Linux
./build-linux.sh

# macOS
./build-macos.sh  # nếu có
```

---

### Option 3: Windows Build

#### Yêu Cầu

- Python 3.11 đã cài đặt
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

## Dockerfile.build Giải Thích

### Python Version Lock

```dockerfile
ARG PYTHON_VERSION=3.11
FROM python:${PYTHON_VERSION}-slim-bookworm AS builder
```

**Tại sao Python 3.11?**

- `tree_sitter_languages` có pre-built wheels cho Python 3.11
- Python 3.13+ cần build từ source (unreliable trên Windows)
- 3.11 stable và được test kỹ

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

Cần thiết cho việc compile native dependencies.

### PyInstaller Hook

```dockerfile
COPY scripts/hooks/hook-midicoder.py /build/hook-midicoder.py
```

Custom hook đảm bảo tất cả Midicoder modules được include:

```python
hiddenimports = [
    'midicoder.cli',
    'midicoder.commands.init',
    'midicoder.commands.brief',
    'midicoder.commands.contract',
    # ... tất cả command modules
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

Mỗi release package chứa một **single executable**:

```
midicoder-linux-bin.tar.gz
└── midicoder  # Self-contained executable
```

Installer (`install.sh` hoặc `install.ps1`) download package này và extract vào `~/.midicoder/bin/`.

---

## Verify Build

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

**Nguyên nhân:** Python 3.13+ không có pre-built wheels.

**Giải pháp:** Dùng Python 3.11 trong Docker build.

### Build Chậm

**Nguyên nhân:** Build đầu tiên download và compile dependencies.

**Giải pháp:** Dùng Docker cache hoặc chỉ build `--no-cache` khi cần.

### Executable Quá Lớn

**Nguyên nhân:** PyInstaller include tất cả dependencies.

**Dự kiến:** 50-100MB là normal cho Python executables.

### Missing Hidden Imports

**Triệu chứng:** `ModuleNotFoundError` tại runtime.

**Giải pháp:** Thêm missing modules vào `scripts/hooks/hook-midicoder.py`.

---

## CI/CD Integration

### GitHub Actions Ví Dụ

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

            - name: Build với Docker
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
| Linux    | 5-10 phút   | 2-3 phút     |
| Windows  | 10-15 phút  | 3-5 phút     |
| macOS    | 8-12 phút   | 2-4 phút     |

### Executable Size

| Platform | Size   |
| -------- | ------ |
| Linux    | ~80MB  |
| Windows  | ~100MB |
| macOS    | ~85MB  |

### Runtime Performance

- **Startup time:** ~500ms (cold start)
- **Command execution:** Tương tự native Python
- **Memory usage:** ~100MB baseline

---

## Best Practices

1. **Luôn dùng Docker cho production builds** - Đảm bảo consistency
2. **Lock Python version** - Dùng 3.11 cho compatibility
3. **Verify checksums** - Luôn generate và verify SHA256
4. **Test executables** - Chạy trên clean systems trước release
5. **Sign executables** - Dùng code signing cho Windows/macOS

---

## Bước Tiếp Theo

Sau khi build:

1. **Test local:** Chạy executables trên clean systems
2. **Create release:** Upload lên GitHub Releases
3. **Update installers:** Chỉ đến new release URL
4. **Thông báo users:** Announce new version

---

**Xem thêm:**

- [Dockerfile.build](../../scripts/Dockerfile.build) - Docker build configuration
- [build-with-docker.sh](../../scripts/build-with-docker.sh) - Build orchestration script
