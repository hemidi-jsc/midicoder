"""
MCP-C: Pack Tools.

Cung cấp 2 MCP tools:
- list_packs: Trả về danh sách tất cả packs với metadata
- get_pack: Trả về thông tin chi tiết cho một pack cụ thể

Source: midicoder.contracts.registry (CP_ID_TO_INTERNAL) + pack.yml files
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from midicoder.contracts.registry import CP_ID_TO_INTERNAL
from midicoder.errors import MidicoderErrorManager as EM, ErrorCode

logger = logging.getLogger(__name__)

# Đường dẫn đến packs directory
PACKS_DIR = Path(__file__).resolve().parent.parent.parent / "packs"


def _load_pack_yml(pack_internal_id: str) -> Dict[str, Any]:
    """
    Load pack.yml từ directory của pack.

    Args:
        pack_internal_id: Tên folder (vd: "cp01_domain_model")

    Returns:
        Dictionary từ pack.yml, hoặc {} nếu file không tồn tại
    """
    pack_yml = PACKS_DIR / pack_internal_id / "pack.yml"
    if not pack_yml.exists():
        return {}

    try:
        with open(pack_yml, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        # pack.yml wrap trong "pack:" key
        if "pack" in data and isinstance(data["pack"], dict):
            return data["pack"]
        return data
    except yaml.YAMLError as e:
        logger.warning(
            f"Không thể parse pack.yml cho {pack_internal_id}: {e}"
        )
        return {}


def _count_templates(pack_internal_id: str) -> int:
    """Đếm số template files trong pack."""
    templates_dir = PACKS_DIR / pack_internal_id
    if not templates_dir.exists():
        return 0
    return len(list(templates_dir.rglob("*.jinja2")))


def _get_pack_emitter_key(pack_internal_id: str) -> Optional[str]:
    """
    Lấy emitter key từ pack_internal_id.

    Args:
        pack_internal_id: Tên folder (vd: "cp01_domain_model")

    Returns:
        Emitter key (vd: "cp01.entity") hoặc None
    """
    # Extract CP number từ internal_id
    parts = pack_internal_id.split("_")
    if parts:
        return parts[0]  # e.g. "cp01"
    return None


# ============================================================================
# MCP Tool: list_packs
# ============================================================================


def list_packs() -> Dict[str, Any]:
    """
    Trả về danh sách tất cả packs với metadata cơ bản.

    Source: midicoder.contracts.registry.CP_ID_TO_INTERNAL + pack.yml files

    Returns:
        Dictionary với:
        - packs: list của pack info (id, internal_id, name, status, category, description)
        - total: tổng số packs
        - statuses: breakdown theo status (stable, experimental, deprecated)
    """
    packs: List[Dict[str, Any]] = []
    status_counts: Dict[str, int] = {}

    for pack_id, internal_id in sorted(CP_ID_TO_INTERNAL.items()):
        yml_data = _load_pack_yml(internal_id)

        status = yml_data.get("status", "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1

        pack_info: Dict[str, Any] = {
            "id": pack_id,
            "internal_id": internal_id,
            "name": yml_data.get("name", internal_id.replace("_", " ").title()),
            "version": yml_data.get("version", "0.0.0"),
            "status": status,
            "category": yml_data.get("category", "unknown"),
            "description": yml_data.get("description", ""),
            "definitions_count": len(yml_data.get("definitions", [])),
            "recipes_count": len(yml_data.get("recipes", [])),
            "obligations_count": len(yml_data.get("obligations", [])),
            "depends_on": yml_data.get("depends_on", []),
            "template_count": _count_templates(internal_id),
        }
        packs.append(pack_info)

    return {
        "packs": packs,
        "total": len(packs),
        "statuses": status_counts,
    }


# ============================================================================
# MCP Tool: get_pack
# ============================================================================


def get_pack(pack_id: str) -> Dict[str, Any]:
    """
    Trả về thông tin chi tiết cho một pack cụ thể.

    Args:
        pack_id: Pack ID (vd: "CP01", "CP02")

    Returns:
        Dictionary với đầy đủ thông tin pack:
        - id, internal_id, name, version, status, category
        - capabilities: list của capability definitions
        - definitions: list của DSL definitions
        - recipes: list của recipe definitions
        - obligations: list của obligation definitions
        - file_contributions: infrastructure, per_entity, per_command, per_query, ...
        - depends_on: danh sách dependency
        - error_codes: error code prefix và range

    Raises:
        MidicoderError: Nếu pack_id không tồn tại
    """
    # Normalize pack_id
    pack_id = pack_id.strip().upper()

    if pack_id not in CP_ID_TO_INTERNAL:
        available = ", ".join(sorted(CP_ID_TO_INTERNAL.keys()))
        EM.raise_error(
            ErrorCode.INVALID_INPUT,
            pack_id=pack_id,
            available_packs=available,
            detail=f"Pack '{pack_id}' không tồn tại. Packs: {available}",
        )

    internal_id = CP_ID_TO_INTERNAL[pack_id]
    yml_data = _load_pack_yml(internal_id)

    # Build file_contributions summary
    fc = yml_data.get("file_contributions", {})
    file_contributions: Dict[str, Any] = {
        "infrastructure": {
            "count": len(fc.get("infrastructure", [])),
            "files": [
                f.get("path", "") for f in fc.get("infrastructure", [])
            ],
        },
        "per_entity": {
            "count": len(fc.get("per_entity", [])),
            "patterns": [
                f.get("path_pattern", "") for f in fc.get("per_entity", [])
            ],
        },
        "per_command": {
            "count": len(fc.get("per_command", [])),
            "patterns": [
                f.get("path_pattern", "") for f in fc.get("per_command", [])
            ],
        },
        "per_query": {
            "count": len(fc.get("per_query", [])),
            "patterns": [
                f.get("path_pattern", "") for f in fc.get("per_query", [])
            ],
        },
        "per_ui_component": {
            "count": len(fc.get("per_ui_component", [])),
            "patterns": [
                f.get("path_pattern", "") for f in fc.get("per_ui_component", [])
            ],
        },
        "per_widget": {
            "count": len(fc.get("per_widget", [])),
            "patterns": [
                f.get("path_pattern", "") for f in fc.get("per_widget", [])
            ],
        },
        "per_vo": {
            "count": len(fc.get("per_vo", [])),
            "patterns": [
                f.get("path_pattern", "") for f in fc.get("per_vo", [])
            ],
        },
    }

    # Extract emitters info từ file contributions
    emitters: Dict[str, List[str]] = {}
    for category in fc.values():
        if isinstance(category, list):
            for entry in category:
                emitter = entry.get("pack_emitter")
                if emitter:
                    if emitter not in emitters:
                        emitters[emitter] = []
                    path = entry.get("path", entry.get("path_pattern", ""))
                    emitters[emitter].append(path)

    result: Dict[str, Any] = {
        "id": pack_id,
        "internal_id": internal_id,
        "name": yml_data.get("name", internal_id.replace("_", " ").title()),
        "version": yml_data.get("version", "0.0.0"),
        "status": yml_data.get("status", "unknown"),
        "category": yml_data.get("category", "unknown"),
        "description": yml_data.get("description", ""),
        "depends_on": yml_data.get("depends_on", []),
        "capabilities": yml_data.get("capabilities", []),
        "capabilities_provided": yml_data.get("capabilities_provided", []),
        "definitions": yml_data.get("definitions", []),
        "recipes": yml_data.get("recipes", []),
        "obligations": yml_data.get("obligations", []),
        "file_contributions": file_contributions,
        "emitters": emitters,
        "error_codes": yml_data.get("error_codes", {}),
        "template_count": _count_templates(internal_id),
    }

    return result
