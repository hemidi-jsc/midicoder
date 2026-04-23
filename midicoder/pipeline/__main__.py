"""Module entry point for python -m midicoder.pipeline."""

from __future__ import annotations

from midicoder.pipeline.cli import main

if __name__ == "__main__":
    raise SystemExit(main())