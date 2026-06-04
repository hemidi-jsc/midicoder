"""
Static SPA server for Angular distribution.

Serves pre-built Angular dist with:
- SPA fallback (any non-file route → index.html)
- Correct MIME types (JS, CSS, HTML, JSON, images)
- Cache-Control headers (max-age=300 for dev)
- Directory listing disabled
- Lightweight, no dependencies beyond stdlib

Usage from launcher:
    from midicoder import spa_serve
    spa_serve.start(port=7272, dist_dir="/path/to/webgui/dist/webgui/browser")

Usage standalone:
    python -m midicoder.spi_serve --port 7272 --dist /path/to/dist

Angular dist detection order:
    webgui/dist/webgui/browser/  (Angular 17+ default)
    webgui/dist/browser/          (legacy)
"""

from __future__ import annotations

import argparse
import html
import http.server
import logging
import mimetypes
import os
import socketserver
import sys
import threading
from pathlib import Path
from typing import Optional

logger = logging.getLogger("midicoder.spa_serve")

# Register MIME types upfront
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("text/javascript", ".mjs")
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("application/json", ".json")
mimetypes.add_type("image/svg+xml", ".svg")
mimetypes.add_type("image/webp", ".webp")
mimetypes.add_type("font/woff", ".woff")
mimetypes.add_type("font/woff2", ".woff2")
mimetypes.add_type("text/html", ".html")


class SPAHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler for Angular SPA with fallback to index.html."""

    # Disable server header leakage
    server_version = "Midicoder-SPA/1.0"
    sys_version = ""

    # Directory to serve from (set at class level)
    _spa_root: str = ""

    def __init__(self, *args, directory: str = "", **kwargs):
        root = directory or self._spa_root
        super().__init__(*args, directory=root, **kwargs)

    def do_GET(self):
        # Strip query string for file lookup
        path = self.path.split("?")[0].lstrip("/")

        # Resolve target file
        target = os.path.join(self.directory, path)
        target = os.path.normpath(target)

        # Security: prevent path traversal
        root = os.path.normpath(self.directory)
        if not target.startswith(root):
            self.send_error(403, "Access denied")
            return

        if os.path.isfile(target):
            super().do_GET()
        else:
            # SPA fallback: serve index.html for Angular router
            self.path = "/index.html"
            super().do_GET()

    def end_headers(self):
        # Cache-Control: short cache for dev, browser can revalidate
        self.send_header("Cache-Control", "no-cache, must-revalidate")
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()

    def log_message(self, format, *args):
        # Suppress default stderr logging — launcher handles log aggregation
        pass


def find_angular_dist(project_root: Path) -> Optional[Path]:
    """Find Angular dist directory from project root.

    Checks in order:
      1. webgui/dist/<project_name>/browser/  (Angular 17+ ng build output)
      2. webgui/dist/browser/                  (legacy output)
      3. dist/browser/                         (flat structure)
    """
    candidates = [
        project_root / "webgui" / "dist" / "webgui" / "browser",
        project_root / "webgui" / "dist" / "browser",
        project_root / "dist" / "browser",
    ]
    for c in candidates:
        if (c / "index.html").is_file():
            return c

    # Fallback: check if webgui/dist/webgui has index.html directly
    fallback = project_root / "webgui" / "dist" / "webgui"
    if (fallback / "index.html").is_file():
        return fallback

    return None


def start(
    port: int = 7272,
    host: str = "0.0.0.0",
    dist_dir: Optional[str] = None,
    project_root: Optional[str] = None,
    daemon: bool = True,
) -> Optional[threading.Thread]:
    """Start SPA server in a background thread.

    Args:
        port: HTTP port (default 7272)
        host: Bind address (default 0.0.0.0)
        dist_dir: Explicit path to Angular dist/browser
        project_root: Project root (auto-detect dist if dist_dir not given)
        daemon: Run as daemon thread (exits with main process)

    Returns:
        Thread if started, None if failed.
    """
    # Resolve dist directory
    if dist_dir:
        d = Path(dist_dir)
    elif project_root:
        d = find_angular_dist(Path(project_root))
    else:
        d = find_angular_dist(Path.cwd())

    if d is None or not (d / "index.html").is_file():
        logger.error("Angular dist not found. dist_dir=%s, project_root=%s", dist_dir, project_root)
        return None

    # Set class-level root
    SPAHandler._spa_root = str(d)

    # Allow address reuse
    socketserver.TCPServer.allow_reuse_address = True

    try:
        server = socketserver.TCPServer((host, port), SPAHandler)
    except OSError as e:
        logger.error("Failed to bind to %s:%d — %s", host, port, e)
        return None

    def _run():
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()

    t = threading.Thread(target=_run, daemon=daemon)
    t.start()
    logger.info("SPA server started on http://%s:%d (dist: %s)", host, port, d)
    return t


def main():
    """CLI entry point: python -m midicoder.spa_serve"""
    parser = argparse.ArgumentParser(description="Serve Angular SPA")
    parser.add_argument("--port", type=int, default=7272)
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--dist", help="Path to Angular dist/browser")
    parser.add_argument("--project-root", help="Project root (auto-detect dist)")
    args = parser.parse_args()

    t = start(port=args.port, host=args.host, dist_dir=args.dist, project_root=args.project_root, daemon=False)
    if t is None:
        print("Failed to start SPA server", file=sys.stderr)
        sys.exit(1)

    print(f"SPA server running on http://{args.host}:{args.port}")
    try:
        t.join()
    except KeyboardInterrupt:
        print("\nShutting down...")


if __name__ == "__main__":
    main()
