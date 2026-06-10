"""
Update checker — kiểm tra phiên bản mới từ GitHub Releases.

Background thread check mỗi 3 giờ, cache kết quả vào settings.db.
Frontend đọc từ /api/update/status (không gọi network).

Dùng stdlib urllib — không cần dependency mới.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import threading
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Callable

from midicoder import __version__

# GitHub API — không cần auth cho public repo
GITHUB_RELEASES_API = (
    "https://api.github.com/repos/hemidi-jsc/midicoder/releases/latest"
)
GITHUB_RAW_RELEASES = (
    "https://github.com/hemidi-jsc/midicoder/releases"
)

# Interval 3 giờ
CHECK_INTERVAL = 3 * 3600

# User-Agent để tránh bị GitHub rate-limit (IP-based, 60 req/hour cho unauthenticated)
_USER_AGENT = f"Midicoder-CE/{__version__}"


# ============================================================================
# Version comparison
# ============================================================================


def _parse_version(v: str) -> tuple[int, ...]:
    """Parse '1.0.0' → (1, 0, 0), ignore 'v' prefix and pre-release suffix."""
    v = v.lstrip("v").strip()
    # Strip pre-release/build metadata: '1.0.0-beta.1+build123' → '1.0.0'
    for sep in ("-", "+"):
        idx = v.find(sep)
        if idx >= 0:
            v = v[:idx]
    parts = []
    for p in v.split("."):
        try:
            parts.append(int(p))
        except ValueError:
            break
    return tuple(parts) if parts else (0,)


def _is_newer(latest: str, current: str) -> bool:
    return _parse_version(latest) > _parse_version(current)


# ============================================================================
# HTTP helpers (stdlib only)
# ============================================================================


def _http_get(url: str, timeout: int = 15) -> dict:
    """GET request with urllib — returns parsed JSON dict."""
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _download_file(url: str, dest: str, timeout: int = 300) -> str:
    """Download file from URL to dest path with timeout support.

    Uses urlopen + manual write instead of urlretrieve (which lacks timeout).
    """
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        block_size = 8192
        with open(dest, "wb") as f:
            while True:
                chunk = resp.read(block_size)
                if not chunk:
                    break
                f.write(chunk)
    return dest


# ============================================================================
# Upgrade helpers — OS-specific
# ============================================================================


def _get_install_dir() -> Path:
    """Get ~/.midicoder/bin — nơi binary được install."""
    return Path.home() / ".midicoder" / "bin"


def _get_asset_name_for_os() -> str:
    """Return the expected GitHub release asset name for current OS."""
    if sys.platform == "win32":
        return "midicoder-windows-bin.zip"
    elif sys.platform == "linux":
        arch = os.uname().machine
        if arch in ("x86_64", "amd64"):
            return "midicoder-linux-x86_64-bin.tar.gz"
        elif arch in ("aarch64", "arm64"):
            return "midicoder-linux-arm64-bin.tar.gz"
        else:
            return f"midicoder-linux-{arch}-bin.tar.gz"
    elif sys.platform == "darwin":
        arch = os.uname().machine
        return f"midicoder-macos-{arch}-bin.tar.gz"
    else:
        return ""


def _run_windows_upgrade(zip_path: str, install_dir: str, exe_path: str) -> None:
    """Create & launch PowerShell helper for Windows upgrade (new process).

    Process cũ đang lock file nên phải dùng process riêng để overwrite.
    """
    ps_script = f"""\
$ErrorActionPreference = "Stop"
$TempExtract = "$env:TEMP\\midicoder-upgrade-$$"
$OldDir = "{install_dir}.old"

# Backup current installation
if (Test-Path "{install_dir}") {{
    Rename-Item "{install_dir}" $OldDir -Force
}}

# Extract ZIP — strip midicoder/ wrapper dir
Expand-Archive -Path "{zip_path}" -DestinationPath $TempExtract -Force
$ExtractedDir = Join-Path $TempExtract "midicoder"
if (Test-Path $ExtractedDir) {{
    # Ensure target dir exists
    New-Item -ItemType Directory -Path "{install_dir}" -Force | Out-Null
    Get-ChildItem $ExtractedDir -Recurse -File | ForEach-{{
        $rel = $_.FullName.Substring($ExtractedDir.Length + 1)
        $dst = Join-Path "{install_dir}" $rel
        $dstDir = Split-Path $dst -Parent
        if (-not (Test-Path $dstDir)) {{ New-Item -ItemType Directory $dstDir -Force | Out-Null }}
        Copy-Item $_.FullName $dst -Force
    }}
    Get-ChildItem $ExtractedDir -Directory -Recurse | ForEach-{{
        $rel = $_.FullName.Substring($ExtractedDir.Length + 1)
        $dstDir = Join-Path "{install_dir}" $rel
        if (-not (Test-Path $dstDir)) {{ New-Item -ItemType Directory $dstDir -Force | Out-Null }}
    }}
}}

# Cleanup
Remove-Item $TempExtract -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "{zip_path}" -Force -ErrorAction SilentlyContinue
Remove-Item $OldDir -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "$ScriptPath" -Force -ErrorAction SilentlyContinue

# Relaunch
Start-Process "{exe_path}"
"""
    script_path = os.path.join(tempfile.gettempdir(), f"midicoder-upgrade-{os.getpid()}.ps1")
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(ps_script)

    # Start PowerShell as new process — detached, doesn't wait
    creation_flags = 0
    if sys.platform == "win32":
        creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    subprocess.Popen(
        ["powershell", "-ExecutionPolicy", "Bypass", "-File", script_path],
        creationflags=creation_flags,
    )


def _run_linux_upgrade(tar_path: str, install_dir: str, exe_path: str) -> None:
    """Create & launch bash helper for Linux upgrade (new process)."""
    bash_script = f"""\
#!/bin/bash
set -e
TEMP_EXTRACT="$HOME/.midicoder-upgrade-$$"
OLD_DIR="{install_dir}.old"

# Backup
if [ -d "{install_dir}" ]; then
    mv "{install_dir}" "$OLD_DIR"
fi

mkdir -p "{install_dir}"
mkdir -p "$TEMP_EXTRACT"
tar -xzf "{tar_path}" -C "$TEMP_EXTRACT" --strip-components=1
chmod +x "$TEMP_EXTRACT/midicoder"

# Move new into place
cp -r "$TEMP_EXTRACT/"* "{install_dir}/"

# Cleanup
rm -rf "$TEMP_EXTRACT"
rm -f "{tar_path}"
rm -rf "$OLD_DIR"
SCRIPT_FILE="$(readlink -f "$0" 2>/dev/null || echo "$0")"
rm -f "$SCRIPT_FILE"

# Relaunch (background)
nohup "{exe_path}" > /dev/null 2>&1 &
"""
    script_path = os.path.join(tempfile.gettempdir(), f"midicoder-upgrade-${os.getpid()}.sh")
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(bash_script)
    os.chmod(script_path, 0o755)

    subprocess.Popen(["bash", script_path])


# ============================================================================
# Global callbacks (set by launcher)
# ============================================================================

_shutdown_servers: Optional[Callable[[], None]] = None
_tray_icon_stop: Optional[Callable[[], None]] = None


def set_shutdown_callbacks(
    shutdown_fn: Callable[[], None],
    tray_stop_fn: Optional[Callable[[], None]] = None,
) -> None:
    """Call from launcher after servers are ready, before tray runs."""
    global _shutdown_servers, _tray_icon_stop
    _shutdown_servers = shutdown_fn
    _tray_icon_stop = tray_stop_fn


# ============================================================================
# UpdateChecker
# ============================================================================


class UpdateChecker:
    """Check GitHub releases, cache result, schedule periodic checks."""

    def __init__(self) -> None:
        self.current_version = __version__
        self._cache: dict = {}
        self._lock = threading.Lock()
        self._timer: Optional[threading.Timer] = None
        self._running = False

    # ----- Core: check GitHub API -----

    def check(self) -> dict:
        """Fetch latest release from GitHub API. Returns status dict."""
        try:
            data = _http_get(GITHUB_RELEASES_API, timeout=10)
        except Exception as e:
            with self._lock:
                self._cache = {
                    "current_version": self.current_version,
                    "has_update": False,
                    "latest_version": self.current_version,
                    "download_url": GITHUB_RAW_RELEASES,
                    "release_notes": "",
                    "checked_at": datetime.now(timezone.utc).isoformat(),
                    "assets": {},
                    "error": f"Network error: {e}",
                }
            return self._cache

        tag = data.get("tag_name", "").lstrip("v").strip()
        html_url = data.get("html_url", GITHUB_RAW_RELEASES)
        body = data.get("body", "")
        assets = {a["name"]: a["browser_download_url"] for a in data.get("assets", [])}

        with self._lock:
            self._cache = {
                "current_version": self.current_version,
                "has_update": _is_newer(tag, self.current_version),
                "latest_version": tag or self.current_version,
                "download_url": html_url,
                "release_notes": body,
                "checked_at": datetime.now(timezone.utc).isoformat(),
                "assets": assets,
            }
        return self._cache

    # ----- Cache access -----

    def get_cached(self) -> dict:
        """Return the last check result (no network call)."""
        with self._lock:
            if not self._cache:
                return {
                    "current_version": self.current_version,
                    "has_update": False,
                    "latest_version": self.current_version,
                    "download_url": GITHUB_RAW_RELEASES,
                    "release_notes": "",
                    "checked_at": "",
                    "assets": {},
                }
            return dict(self._cache)

    # ----- Scheduler -----

    def start(self) -> None:
        """Start background scheduler: check now + every 3 hours."""
        self._running = True
        t = threading.Thread(target=self.check, daemon=True, name="update-check-initial")
        t.start()
        self._schedule_next()

    def _schedule_next(self) -> None:
        if not self._running:
            return
        self._timer = threading.Timer(CHECK_INTERVAL, self._scheduled_check)
        self._timer.daemon = True
        self._timer.start()

    def _scheduled_check(self) -> None:
        self.check()
        self._schedule_next()

    def stop(self) -> None:
        self._running = False
        if self._timer:
            self._timer.cancel()

    # ----- Upgrade: download → shutdown → helper → exit -----

    def upgrade(self) -> None:
        """Download new version, shutdown servers, spawn helper, exit.

        This runs in a thread from the FastAPI endpoint. After downloading,
        it stops everything and spawns a new OS process to replace the binary
        and relaunch. Then os._exit() kills this process.
        """
        cache = self.get_cached()
        if not cache.get("has_update"):
            raise RuntimeError("Không có phiên bản mới để nâng cấp")

        asset_name = _get_asset_name_for_os()
        assets = cache.get("assets", {})
        if asset_name not in assets:
            raise RuntimeError(
                f"Không tìm thấy asset cho OS hiện tại: {asset_name}"
            )

        download_url = assets[asset_name]
        install_dir = _get_install_dir()

        # Determine exe path
        if sys.platform == "win32":
            exe_path = str(install_dir / "midicoder.exe")
        else:
            exe_path = str(install_dir / "midicoder")

        # 1. Download to temp
        temp_dest = os.path.join(
            tempfile.gettempdir(),
            f"midicoder-{cache['latest_version']}-{asset_name}",
        )
        _download_file(download_url, temp_dest)

        # 2. Shutdown servers
        if _shutdown_servers:
            try:
                _shutdown_servers()
            except Exception:
                pass
        import time
        time.sleep(1)

        # 3. Stop tray icon
        if _tray_icon_stop:
            try:
                _tray_icon_stop()
            except Exception:
                pass

        # 4. Spawn OS-specific helper process
        if sys.platform == "win32":
            _run_windows_upgrade(temp_dest, str(install_dir), exe_path)
        else:
            _run_linux_upgrade(temp_dest, str(install_dir), exe_path)

        # 5. Kill current process
        os._exit(0)


# ============================================================================
# Singleton — dùng toàn cục
# ============================================================================

_checker = UpdateChecker()


def get_checker() -> UpdateChecker:
    """Get the global UpdateChecker instance."""
    return _checker
