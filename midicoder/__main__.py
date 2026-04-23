"""Module entry point for python -m midicoder."""

from __future__ import annotations

# Import từ pipeline module (new CLI)
from midicoder.pipeline.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
