"""Midicoder entry point — WebGUI Launcher only.

Khi chạy `midicoder`, terminal sẽ:
- Hiển thị ASCII logo
- Start backend (FastAPI :6868)
- Start frontend (Angular :7272)
- Start SQLite viewer (Datasette :8080)
- Mở browser tabs
- Aggregate logs về terminal
- Graceful shutdown khi Ctrl+C

Terminal chỉ dùng để hiển thị status/logs — không phải CLI interactive.
"""

from __future__ import annotations

from midicoder.launcher import run

if __name__ == "__main__":
    raise SystemExit(run())
