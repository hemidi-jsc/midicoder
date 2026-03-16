"""Simple structured logging helpers for IR build output."""

from __future__ import annotations

from typing import Any


def safe_print(text: str) -> None:
    try:
        print(text)
    except UnicodeEncodeError:
        safe = text.encode("ascii", "backslashreplace").decode("ascii")
        print(safe)


def log(
    stage: str,
    status: str,
    message: str | None = None,
    **fields: Any,
) -> None:
    stage_label = f"IR:{stage.upper()}"
    status_label = status.upper()
    parts = [f"[{stage_label:<10}]", f"{status_label:<5}"]
    if message:
        parts.append(message)
    if fields:
        kv = " ".join(f"{key}={value}" for key, value in fields.items())
        parts.append(f"| {kv}")
    safe_print(" ".join(parts))


def header(title: str, width: int = 60) -> None:
    safe_print(title)
    safe_print("-" * width)
