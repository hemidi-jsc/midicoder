from __future__ import annotations

import re
from typing import Iterable


GROUP_ID_PATTERN = re.compile(r"midicoder:(?:begin|end)\s*(.*)$", re.IGNORECASE)
REAL_SEAM_CONFIDENCE = 0.98
EXEMPLAR_GROUP_PENALTY = 0.95
SYMBOL_BASE_CONFIDENCE = 0.5
SYMBOL_SOURCE_PENALTY = 0.75
ENTRYPOINT_CONFIDENCE = 0.4


def _extract_module_from_path(file_path: str) -> tuple[str, bool]:
    normalized = file_path.replace("\\", "/").strip("/")
    parts = [part for part in normalized.split("/") if part]

    for anchor in ("src", "domain", "modules", "app"):
        if anchor in parts:
            idx = parts.index(anchor)
            # Treat anchor/<module>/... as module. If anchor is directly
            # followed by a file (no further path segments), fall back.
            if idx + 2 < len(parts):
                return parts[idx + 1], False

    filename = parts[-1] if parts else ""
    stem = filename.rsplit(".", 1)[0]
    lowered = stem.lower()
    for suffix in (".controller", ".service", "-controller", "-service", "_controller"):
        if lowered.endswith(suffix):
            stem = stem[: -len(suffix)]
            break

    if stem and stem.lower() not in {"index", "main"}:
        return stem, True

    return "default", True


def _infer_kind_from_path(file_path: str) -> str:
    lowered = file_path.replace("\\", "/").lower()
    filename = lowered.split("/")[-1]

    if "controller" in filename:
        return "controller"
    if "service" in filename:
        return "service"
    if "model" in filename or "entity" in filename:
        return "model"
    if "route" in filename or "/routes/" in lowered:
        return "route"
    return "service"


def _coerce_line(value: object) -> int | None:
    try:
        line = int(value)
    except (TypeError, ValueError):
        return None
    return line if line > 0 else None


def _coerce_float(value: object, fallback: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _clamp(value: float) -> float:
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return round(value, 2)


def _module_fallback_penalty(file_path: object) -> float:
    module, fallback = _extract_module_from_path(str(file_path or ""))
    if not module:
        return 0.85
    return 0.85 if fallback else 1.0


def _strip_internal_fields(seams: Iterable[dict]) -> list[dict]:
    cleaned: list[dict] = []
    for seam in seams:
        if not isinstance(seam, dict):
            continue
        cleaned.append({k: v for k, v in seam.items() if not str(k).startswith("_")})
    return cleaned


def _has_parent_symbol(record: dict) -> bool:
    # Only treat non-top-level scopes as "parent".
    # Top-level symbols are typically marked as "module" (Python)
    # or "export"/"module" (JS/TS); those should NOT be filtered out.
    top_level_scopes = {"", "module", "export", None}

    for key in ("parent", "container", "enclosing"):
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return True
        if value:
            return True

    scope = record.get("scope")
    if isinstance(scope, str):
        return scope.strip() not in top_level_scopes
    return bool(scope)


def _is_exemplar_source(item: dict) -> int:
    source = str(item.get("_source", "")).lower()
    return 1 if source == "exemplar" else 0
