from __future__ import annotations

from dataclasses import dataclass

from .deterministic import base_file_content


@dataclass(frozen=True)
class MergeResult:
    content: str
    status: str
    detail: str = ""


def _canonical(text: str) -> str:
    return "\n".join(
        line.rstrip() for line in text.replace("\r\n", "\n").strip().split("\n")
    )


def _region_bounds(content: str, ir_ref: str) -> tuple[int, int] | None:
    start_marker = f"# region {ir_ref}"
    end_marker = f"# endregion {ir_ref}"
    start = content.find(start_marker)
    if start < 0:
        return None
    end = content.find(end_marker, start)
    if end < 0:
        return None
    end = end + len(end_marker)
    if end < len(content) and content[end : end + 1] == "\n":
        end += 1
    return start, end


def merge_content(
    *,
    runtime_path: str,
    existing: str | None,
    block: str,
    ir_ref: str,
    mode: str,
) -> MergeResult:
    current = existing if existing is not None else base_file_content(runtime_path)
    if not current.endswith("\n"):
        current += "\n"
    if not block.endswith("\n"):
        block += "\n"

    if mode == "create":
        if existing is None:
            return MergeResult(content=current + block, status="created")
        bounds = _region_bounds(current, ir_ref)
        if bounds is not None:
            start, end = bounds
            return MergeResult(
                content=current[:start] + block + current[end:], status="updated"
            )
        if _canonical(existing) == _canonical(current + block):
            return MergeResult(content=existing, status="noop")
        # Recover from legacy/non-region output by replacing with canonical baseline + block.
        return MergeResult(
            content=current + block, status="updated", detail="MERGE_CREATE_RECOVERED"
        )

    bounds = _region_bounds(current, ir_ref)
    if mode in {"append", "patch"}:
        if bounds is None:
            if not current.endswith("\n\n"):
                current += "\n"
            return MergeResult(content=current + block, status="updated")
        start, end = bounds
        merged = current[:start] + block + current[end:]
        return MergeResult(content=merged, status="updated")

    return MergeResult(
        content=current, status="error", detail=f"Unknown merge mode: {mode}"
    )
