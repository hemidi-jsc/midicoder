"""
Midicoder Launcher — System Tray App.

Windowed mode: no console window, system tray icon, graceful shutdown via menu.
Bundled with PyInstaller as windowed=True.

Features:
  - No console window (windowed binary)
  - System tray icon with status menu
  - Log file at ~/.midicoder/logs/midicoder-YYYYMMDD.log
  - Windows toast notification when ready
  - Graceful shutdown via tray menu "Exit"

User flow:
    double-click midicoder.exe
    [no console, tray icon appears]
    [notification: "Midicoder ready"]
    [browser opens automatically]
    right-click tray icon → Exit
"""

from __future__ import annotations

import io
import logging
import os
import re
import signal
import socket
import subprocess
import sys
import threading
import time
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Brand color
BRAND_COLOR = "#e90089"

# App version
from midicoder import __version__ as APP_VERSION

# Server ports
BACKEND_PORT = 6868
FRONTEND_PORT = 7272
SQLITE_VIEWER_PORT = 8080

# Logger for log file
logger = logging.getLogger("midicoder.launcher")


# =============================================================================
# Log redirect — all print() goes to log file + in-memory buffer
# =============================================================================

_log_file: Optional[io.TextIOWrapper] = None
_log_buffer: List[str] = []
_MAX_LOG_LINES = 500


class _LogWriter(io.TextIOBase):
    """Redirect stdout/stderr to log file + in-memory buffer."""

    def write(self, msg: str) -> int:
        if _log_file and not _log_file.closed:
            try:
                _log_file.write(msg)
                _log_file.flush()
            except Exception:
                pass
        _log_buffer.append(msg)
        if len(_log_buffer) > _MAX_LOG_LINES:
            del _log_buffer[:100]
        return len(msg)

    def flush(self) -> None:
        if _log_file and not _log_file.closed:
            try:
                _log_file.flush()
            except Exception:
                pass


def _init_logging() -> Path:
    """Set up log file and redirect stdout/stderr."""
    global _log_file
    log_dir = Path.home() / ".midicoder" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d")
    log_path = log_dir / f"midicoder-{date_str}.log"

    _log_file = open(log_path, "a", encoding="utf-8")
    sys.stdout = _LogWriter()  # type: ignore
    sys.stderr = _LogWriter()  # type: ignore

    # Also set up Python logging
    handler = logging.FileHandler(str(log_path), encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    return log_path


def _log(msg: str) -> None:
    """Write to log file."""
    prefix = f"[{datetime.now().strftime('%H:%M:%S')}] "
    if _log_file and not _log_file.closed:
        try:
            _log_file.write(prefix + msg + "\n")
            _log_file.flush()
        except Exception:
            pass
    logger.info(msg)


def get_log_file() -> Optional[Path]:
    """Get the current log file path."""
    if _log_file:
        return Path(_log_file.name)
    return None


# =============================================================================
# Server infrastructure
# =============================================================================


class ServerHandle:
    """Handle cho một server chạy trong thread."""

    def __init__(self, name: str, port: int):
        self.name = name
        self.port = port
        self.thread: Optional[threading.Thread] = None
        self.started = False

    def start(self) -> bool:
        raise NotImplementedError

    def stop(self) -> None:
        raise NotImplementedError


class ThreadServer(ServerHandle):
    """Server chạy trong thread — dùng cho bundled mode."""

    def __init__(self, name: str, port: int, run_func, stop_func=None):
        super().__init__(name, port)
        self._run_func = run_func
        self._stop_func = stop_func

    def start(self) -> bool:
        if not _check_port_available(self.port):
            _log(f"Port {self.port} đang bị chiếm — không thể start {self.name}")
            return False
        self.thread = threading.Thread(target=self._wrapped_run, daemon=True)
        self.thread.start()
        if _wait_for_port(self.port, timeout=90):
            self.started = True
            _log(f"{self.name} started — http://localhost:{self.port}")
            return True
        else:
            _log(f"{self.name} start timeout sau 90s")
            return False

    def _wrapped_run(self):
        try:
            self._run_func()
        except Exception as e:
            _log(f"{self.name} crashed: {e}")

    def stop(self) -> None:
        if self._stop_func:
            try:
                self._stop_func()
            except Exception:
                pass
        _log(f"{self.name} stopped")


# =============================================================================
# Port / utility helpers
# =============================================================================


def _check_port_available(port: int) -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            return s.connect_ex(("127.0.0.1", port)) != 0
    except socket.error:
        return False


def _wait_for_port(port: int, timeout: int = 30) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.5)
                if s.connect_ex(("127.0.0.1", port)) == 0:
                    return True
        except socket.error:
            pass
        time.sleep(0.5)
    return False


def _init_databases() -> None:
    """Initialize global SQLite databases on first launch.

    Creates ~/.midicoder/data/{projects.db, settings.db} with schemas.
    """
    try:
        from midicoder.storage.projects import ProjectsManager
        from midicoder.storage.settings import SettingsManager

        # Init projects.db
        projects_mgr = ProjectsManager()
        projects_mgr.init()
        _log("Initialized projects.db")

        # Init settings.db (includes legacy migration)
        settings_mgr = SettingsManager()
        settings_mgr.init()
        _log("Initialized settings.db")
    except Exception as e:
        _log(f"Database initialization error (non-fatal): {e}")


def _kill_process_on_port(port: int) -> bool:
    """Kill any process listening on the given port (Windows).

    Returns True if a process was found and killed, False otherwise.
    """
    if sys.platform != "win32":
        return False
    try:
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True, text=True, timeout=5
        )
        pattern = re.compile(
            rf"^\s+TCP\s+127\.0\.0\.1:{port}\s+\S+\s+LISTENING\s+(\d+)",
            re.MULTILINE,
        )
        m = pattern.search(result.stdout)
        if m:
            pid = m.group(1)
            subprocess.run(
                ["taskkill", "/F", "/PID", pid],
                capture_output=True, timeout=5
            )
            _log(f"Killed PID {pid} on port {port}")
            return True
    except Exception as e:
        _log(f"_kill_process_on_port({port}) error: {e}")
    return False


def _ensure_ports_free() -> None:
    """Kill processes occupying our required ports before starting servers."""
    for port in (BACKEND_PORT, FRONTEND_PORT, SQLITE_VIEWER_PORT):
        _kill_process_on_port(port)


def _get_project_root() -> Path:
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


def _get_bundle_path() -> Optional[Path]:
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return None


# =============================================================================
# Server start functions
# =============================================================================


def _start_backend() -> Optional[ServerHandle]:
    """Start backend FastAPI server in a thread."""
    try:
        import uvicorn
    except ImportError:
        _log("uvicorn không thể import — backend sẽ không khởi động")
        return None

    config = uvicorn.Config(
        "midicoder.api.main:server",
        host="0.0.0.0",
        port=BACKEND_PORT,
        log_level="warning",
        loop="asyncio",
    )
    server = uvicorn.Server(config)

    def run_server():
        server.run()

    def stop_server():
        server.should_exit = True

    return ThreadServer("Backend", BACKEND_PORT, run_func=run_server, stop_func=stop_server)


def _find_frontend_dist() -> Optional[Path]:
    """Find Angular dist directory."""
    bundle = _get_bundle_path()
    if bundle:
        bundled_dist = bundle / "midicoder" / "frontend"
        if (bundled_dist / "index.html").is_file():
            return bundled_dist

    import importlib
    try:
        frontend_pkg = importlib.import_module("midicoder.frontend")
        pkg_path = Path(frontend_pkg.__file__).parent
        if (pkg_path / "index.html").is_file():
            return pkg_path
    except ImportError:
        pass

    project_root = _get_project_root()
    for candidate in [
        project_root / "webgui" / "dist" / "webgui" / "browser",
        project_root / "webgui" / "dist" / "browser",
    ]:
        if (candidate / "index.html").is_file():
            return candidate
    return None


def _start_frontend() -> Optional[ServerHandle]:
    """Start frontend SPA server in a thread."""
    dist_dir = _find_frontend_dist()
    if dist_dir is None:
        _log("Không thể tìm Angular dist")
        return None

    try:
        from midicoder import spa_serve
    except ImportError:
        _log("spa_serve module không tìm thấy")
        return None

    spa_thread = None

    def run_spa():
        nonlocal spa_thread
        spa_thread = spa_serve.start(
            port=FRONTEND_PORT, host="0.0.0.0", dist_dir=str(dist_dir), daemon=True
        )
        if spa_thread is not None:
            spa_thread.join()

    return ThreadServer("Frontend", FRONTEND_PORT, run_func=run_spa, stop_func=lambda: None)


def _start_sqlite_viewer() -> Optional[ServerHandle]:
    """Start Datasette SQLite viewer in a thread.

    Shows ALL databases:
    - Global: ~/.midicoder/data/{projects.db, settings.db}
    - Per-project: <project_path>/.midicoder/data/*.db (for each registered project)
    """
    try:
        from datasette.app import Datasette
    except ImportError:
        _log("Datasette không thể import")
        return None

    db_files = []

    # 1. Global DBs
    global_data = Path.home() / ".midicoder" / "data"
    if global_data.exists():
        db_files.extend([str(f) for f in global_data.glob("*.db")])

    # 2. Per-project DBs from registered projects
    try:
        from midicoder.storage.projects import ProjectsManager
        mgr = ProjectsManager()
        mgr.init()
        for proj in mgr.list_all():
            proj_data = Path(proj["path"]) / ".midicoder" / "data"
            if proj_data.exists():
                db_files.extend([str(f) for f in proj_data.glob("*.db")])
    except Exception as e:
        _log(f"Could not list project DBs: {e}")

    if not db_files:
        _log("Không tìm thấy file .db để hiển thị")
        return None

    # Deduplicate by absolute path
    db_files = list(set(Path(p).resolve() for p in db_files))
    db_files = [str(p) for p in db_files]

    ds_app = Datasette(files=db_files, cors=True)

    import uvicorn
    config = uvicorn.Config(
        ds_app.app,
        host="0.0.0.0",
        port=SQLITE_VIEWER_PORT,
        log_level="warning",
        loop="asyncio",
        factory=True,
    )
    server = uvicorn.Server(config)

    def run_ds():
        server.run()

    def stop_ds():
        server.should_exit = True

    return ThreadServer("SQLite Viewer", SQLITE_VIEWER_PORT, run_func=run_ds, stop_func=stop_ds)


# =============================================================================
# Tray icon — load from bundled logo.png (fallback: inline 'M')
# =============================================================================


def _make_icon():
    """Load logo.png from bundle for tray icon.

    Priority: bundled midicoder/logo.png → repo webgui/public/logo.png → inline fallback.
    Returns a PIL Image for pystray.
    """
    from PIL import Image

    logo_path = None

    # 1. Bundled logo
    bundle = _get_bundle_path()
    if bundle:
        p = bundle / "midicoder" / "logo.png"
        if p.is_file():
            logo_path = str(p)

    # 2. Dev mode: repo logo
    if not logo_path:
        repo = _get_project_root()
        for candidate in [
            repo / "webgui" / "public" / "logo.png",
            repo / "midicoder" / "logo.png",
        ]:
            if candidate.is_file():
                logo_path = str(candidate)
                break

    if logo_path:
        img = Image.open(logo_path).convert("RGBA")
        img = img.resize((32, 32), Image.LANCZOS)
    else:
        # Inline fallback: magenta M on dark background
        # 32x32 is the Windows tray icon sweet spot — scales down to 16x16 without blur
        img = Image.new("RGBA", (32, 32), (15, 15, 23, 255))
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle([1, 1, 31, 31], radius=6, fill=(30, 30, 46, 255))
        bbox = draw.textbbox((0, 0), "M", anchor="lt")
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        draw.text(((32 - tw) // 2, (32 - th) // 2), "M", fill=(233, 0, 137, 255))

    return img


# =============================================================================
# Windows toast notification
# =============================================================================


def _show_toast(title: str, message: str) -> None:
    """Show Windows toast notification (best-effort, no crash if unavailable)."""
    if sys.platform != "win32":
        return
    try:
        import win10toast
        toaster = win10toast.ToastNotifier()
        toaster.show_toast(title, message, duration=5)
    except ImportError:
        _log("Toast notification skipped (win10toast not available)")


# =============================================================================
# Global state for tray
# =============================================================================

_servers: List[ServerHandle] = []
_shutdown_event = threading.Event()
_tray_icon: Optional["Icon"] = None  # pystray Icon reference


def _shutdown_servers() -> None:
    """Stop all servers gracefully."""
    _log("Đang dừng servers...")
    for s in reversed(_servers):
        s.stop()
    # Give threads a moment to clean up
    for s in _servers:
        if s.thread and s.thread.is_alive():
            s.thread.join(timeout=3)
    _log("Tất cả servers đã dừng.")


def _stop_tray_icon() -> None:
    """Stop the tray icon (called by upgrade flow)."""
    global _tray_icon
    if _tray_icon:
        try:
            _tray_icon.stop()
        except Exception:
            pass


# =============================================================================
# Main launcher — tray icon based
# =============================================================================


def run() -> int:
    """
    Main entry point.

    In windowed mode: shows system tray icon, no console.
    In dev mode (console): same but logs to terminal too.
    """
    is_windowed = hasattr(sys, "frozen") and (sys.stdout is None
                                               or not getattr(sys.stdout, "isatty", lambda: True)()
                                               or type(sys.stdout).__name__ == "DevNull")

    # 1. Init logging
    log_path = _init_logging()
    _log("=" * 60)
    _log(f"Midicoder CE v{APP_VERSION} — Contract Coding Platform")
    _log(f"Log file: {log_path}")
    _log(f"Windowed mode: {is_windowed}")

    # 1b. Initialize global SQLite databases
    _init_databases()

    # 1c. Start update checker scheduler (background, non-blocking)
    try:
        from midicoder.update_checker import set_shutdown_callbacks
        set_shutdown_callbacks(_shutdown_servers, _stop_tray_icon)
    except Exception as e:
        _log(f"Update checker init error (non-fatal): {e}")

    # 1c. Ensure ports are free before starting
    _ensure_ports_free()
    time.sleep(0.5)  # brief pause for OS to release ports

    # 2. Start servers
    _log("Đang start backend...")
    backend = _start_backend()
    if backend and backend.start():
        _servers.append(backend)
    else:
        _log("Backend không thể start — dừng khởi động")
        if is_windowed:
            import ctypes
            ctypes.windll.user32.MessageBoxW(
                0, "Backend không thể khởi động. Kiểm tra log tại ~/.midicoder/logs/", "Midicoder Error", 0x10
            )
        return 1

    _log("Đang start frontend...")
    frontend = _start_frontend()
    if frontend and frontend.start():
        _servers.append(frontend)
    else:
        _log("Frontend không start được")

    _log("Đang start SQLite viewer...")
    sqlite_viewer = _start_sqlite_viewer()
    if sqlite_viewer and sqlite_viewer.start():
        _servers.append(sqlite_viewer)
    else:
        _log("SQLite viewer không khả dụng")

    # 3. Open browser
    time.sleep(1)
    try:
        webbrowser.open(f"http://localhost:{FRONTEND_PORT}")
        webbrowser.open(f"http://localhost:{SQLITE_VIEWER_PORT}", new=2)
    except Exception as e:
        _log(f"Browser open error: {e}")

    # 4. Summary
    _log(f"Backend:      http://localhost:{BACKEND_PORT}")
    has_frontend = any(s.name == "Frontend" for s in _servers)
    _log(f"Frontend:     http://localhost:{FRONTEND_PORT}" if has_frontend else "Frontend:     [x]")
    has_sqlite = any(s.name == "SQLite Viewer" for s in _servers)
    _log(f"SQLite Viewer: http://localhost:{SQLITE_VIEWER_PORT}" if has_sqlite else "SQLite Viewer: [x]")

    # 5. Toast notification
    _show_toast(f"Midicoder v{APP_VERSION}", "All servers ready — http://localhost:7272")
    _log("All servers ready")

    # 5b. Start update checker background scheduler
    try:
        from midicoder.update_checker import get_checker
        get_checker().start()
        _log("Update checker started")
    except Exception as e:
        _log(f"Update checker start error (non-fatal): {e}")

    # 6. Start system tray icon
    if is_windowed:
        try:
            _log("Starting system tray icon...")
            _run_tray()
        except Exception as e:
            _log(f"Tray icon failed: {e} — blocking with MessageBox exit")
            import ctypes
            ctypes.windll.user32.MessageBoxW(
                0, "Midicoder is running. Open Task Manager to stop.", "Midicoder", 0x40
            )
            while True:
                time.sleep(1)
    else:
        # Dev mode: wait for Ctrl+C
        _log("Press Ctrl+C to stop all servers...")
        signal.signal(signal.SIGINT, lambda s, f: (_shutdown_servers(), sys.exit(0)))
        try:
            while not _shutdown_event.is_set():
                _shutdown_event.wait(1)
        except KeyboardInterrupt:
            _shutdown_servers()

    return 0


def _run_tray() -> None:
    """Run the system tray icon (blocks until Exit selected)."""
    try:
        from pystray import Icon, MenuItem
    except ImportError:
        _log("pystray not available — running without tray icon")
        import ctypes
        ctypes.windll.user32.MessageBoxW(
            0, "Running without tray. Close this message and press Ctrl+C in a terminal to stop.", "Midicoder", 0x40
        )
        while True:
            time.sleep(1)

    def _on_exit(icon, item):
        _shutdown_servers()
        icon.stop()
        sys.exit(0)

    def _open_logs(icon, item):
        lf = get_log_file()
        if lf and lf.exists():
            os.startfile(str(lf))
        else:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, "Log file not found yet.", "Midicoder", 0x40)

    # Build menu — pystray 0.19.x: MenuItem(text, action, enabled=...)
    # Separators: MenuItem(None, None)
    # Status items: disabled (action=noop, enabled=False)
    tray_menu = (
        MenuItem(f"🟢 Backend :{BACKEND_PORT}", lambda i, m: None, enabled=False),
        MenuItem(f"🟢 Frontend :{FRONTEND_PORT}", lambda i, m: None, enabled=False),
        MenuItem(f"🟢 SQLite Viewer :{SQLITE_VIEWER_PORT}", lambda i, m: None, enabled=False),
        MenuItem(None, None),
        MenuItem("🌐 Open Frontend", lambda i, m: webbrowser.open(f"http://localhost:{FRONTEND_PORT}")),
        MenuItem("📊 Open API Docs", lambda i, m: webbrowser.open(f"http://localhost:{BACKEND_PORT}/docs")),
        MenuItem("💾 Open SQLite Viewer", lambda i, m: webbrowser.open(f"http://localhost:{SQLITE_VIEWER_PORT}")),
        MenuItem("📋 View Logs", _open_logs),
        MenuItem(None, None),
        MenuItem("❌ Exit", _on_exit),
    )

    icon_img = _make_icon()
    global _tray_icon
    _tray_icon = Icon("midicoder", icon_img, "Midicoder", menu=tray_menu)

    # Run — this blocks until stop() is called
    _tray_icon.run()


# Keep backward compatibility for __main__.py
def main():
    """Entry point for `python -m midicoder`."""
    raise SystemExit(run())


if __name__ == "__main__":
    main()
