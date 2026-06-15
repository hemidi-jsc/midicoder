"""
Artifact Stats Command — thu thập thông tin chi tiết của các artifacts
thuộc version active hiện tại.

Trả về dict có cấu trúc:
{
    "pipeline": {"brief": "none"|"done", ...},
    "briefs": { ... },
    "contracts": { ... },
    "ir": { ... },
    "code": { ... },
}
"""

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, Optional

from midicoder.storage.projects import ProjectsManager
from midicoder.storage.sqlite import get_connection


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_project_root() -> Path:
    """Lấy root của project đang active."""
    try:
        from midicoder.pipeline.config import get_config
        cfg = get_config()
        if cfg._project_path:
            return Path(cfg._project_path)
    except Exception:
        pass

    mgr = ProjectsManager()
    mgr.init()
    active = mgr.get_active()
    if active:
        return Path(active["path"])

    return Path.cwd()


def _get_active_version() -> Optional[str]:
    """Lấy tên version đang active (strip 'v' prefix nếu có)."""
    try:
        mgr = ProjectsManager()
        mgr.init()
        project_id = _get_project_id()
        v = mgr.version_get_active(project_id)
        if v:
            return v.get("version_name", "")
    except Exception:
        pass
    return None


def _get_project_id() -> str:
    import hashlib
    root = _get_project_root()
    return hashlib.md5(str(root.resolve()).encode()).hexdigest()[:12]


def _get_version_metadata() -> Dict[str, Any]:
    """Đọc metadata.yml của version active."""
    vname = _get_active_version()
    if not vname:
        return {"pipeline": {"brief": "none", "contract": "none", "ir": "none", "code": "none"}}
    # Load metadata.yml
    data_dir = _get_project_root() / ".midicoder" / "versions"
    meta_file = data_dir / vname / "metadata.yml"
    if meta_file.exists():
        import yaml
        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            pass
    return {"pipeline": {"brief": "none", "contract": "none", "ir": "none", "code": "none"}}


# ---------------------------------------------------------------------------
# Per-category stat collectors
# ---------------------------------------------------------------------------

def _collect_brief_stats(version: str) -> Dict[str, Any]:
    """Collect brief statistics from briefs.db."""
    data_dir = _get_project_root() / ".midicoder" / "data"
    briefs_db = data_dir / "briefs.db"

    result: Dict[str, Any] = {
        "count": 0,
        "status": "draft",
        "title": "",
        "word_count": 0,
        "clarification_count": 0,
        "change_count": 0,
        "updated_at": "",
        "types": {},
    }

    if not briefs_db.exists():
        return result

    try:
        with sqlite3.connect(str(briefs_db), timeout=30) as conn:
            conn.row_factory = sqlite3.Row

            # Total briefs for this version
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM briefs WHERE version = ?", (version,)
            ).fetchone()
            count = row["cnt"] if row else 0
            result["count"] = count

            if count == 0:
                return result

            # Get the main brief (latest by id)
            brief = conn.execute(
                "SELECT * FROM briefs WHERE version = ? ORDER BY id DESC LIMIT 1",
                (version,),
            ).fetchone()

            if brief:
                b = dict(brief)
                result["status"] = b.get("status", "draft")
                result["title"] = b.get("title", "") or ""
                content = b.get("content", "") or ""
                result["word_count"] = len(content.split()) if content else 0
                result["updated_at"] = b.get("updated_at", b.get("created_at", ""))

                # Clarification count for this brief
                clar_count = conn.execute(
                    "SELECT COUNT(*) as cnt FROM clarifications WHERE brief_id = ?",
                    (b.get("brief_id"),),
                ).fetchone()["cnt"]
                result["clarification_count"] = clar_count

                # Change history count
                lineage_count = conn.execute(
                    "SELECT COUNT(*) as cnt FROM brief_revisions WHERE brief_id = ?",
                    (b.get("brief_id"),),
                ).fetchone()["cnt"]
                result["change_count"] = lineage_count

            # Count by type
            rows = conn.execute(
                "SELECT type, COUNT(*) as cnt FROM briefs WHERE version = ? GROUP BY type",
                (version,),
            ).fetchall()
            for r in rows:
                result["types"][r["type"]] = r["cnt"]

    except Exception:
        pass

    return result


def _collect_contract_stats(version: str) -> Dict[str, Any]:
    """Collect contract statistics from artifacts.db."""
    data_dir = _get_project_root() / ".midicoder" / "data"
    artifacts_db = data_dir / "artifacts.db"

    result: Dict[str, Any] = {
        "count": 0,
        "categories": {},
        "total_entities": 0,
        "total_commands": 0,
        "total_queries": 0,
        "total_events": 0,
    }

    if not artifacts_db.exists():
        return result

    try:
        with sqlite3.connect(str(artifacts_db), timeout=30) as conn:
            conn.row_factory = sqlite3.Row

            # List all contract artifacts for this version
            contracts = conn.execute(
                "SELECT * FROM artifacts WHERE type = 'contract' AND version = ?",
                (version,),
            ).fetchall()

            result["count"] = len(contracts)

            for c in contracts:
                cd = dict(c)
                artifact_id = cd.get("artifact_id", "")
                # Extract category from artifact_id (e.g., "contract_entities" → "entities")
                category = artifact_id.replace("contract_", "") if artifact_id.startswith("contract_") else artifact_id
                result["categories"][category] = {
                    "status": cd.get("status", "pending"),
                    "updated_at": cd.get("updated_at", ""),
                }

                # Parse content YAML to count items
                content = cd.get("content", "") or ""
                if content:
                    try:
                        import yaml
                        data = yaml.safe_load(content)
                        if isinstance(data, list):
                            if category == "entities":
                                result["total_entities"] += len(data)
                            elif category == "commands":
                                result["total_commands"] += len(data)
                            elif category == "queries":
                                result["total_queries"] += len(data)
                            elif category == "events":
                                result["total_events"] += len(data)
                    except Exception:
                        pass

    except Exception:
        pass

    return result


def _collect_ir_stats(version: str) -> Dict[str, Any]:
    """Collect IR/MIR statistics from artifacts.db."""
    data_dir = _get_project_root() / ".midicoder" / "data"
    artifacts_db = data_dir / "artifacts.db"

    result: Dict[str, Any] = {
        "operations": 0,
        "data_flows": 0,
        "effect_flows": 0,
        "boundaries": 0,
        "entities": 0,
    }

    if not artifacts_db.exists():
        return result

    try:
        with sqlite3.connect(str(artifacts_db), timeout=30) as conn:
            conn.row_factory = sqlite3.Row

            mir = conn.execute(
                "SELECT * FROM artifacts WHERE type = 'mir' AND version = ? ORDER BY id DESC LIMIT 1",
                (version,),
            ).fetchone()

            if mir:
                md = dict(mir)
                # Parse metadata JSON
                metadata_raw = md.get("metadata", "") or ""
                if metadata_raw:
                    try:
                        meta = json.loads(metadata_raw)
                        result["operations"] = meta.get("operation_count", 0)
                        result["data_flows"] = meta.get("data_flow_count", 0)
                        result["effect_flows"] = meta.get("effect_flow_count", 0)
                        result["boundaries"] = meta.get("boundary_count", 0)
                        # Entity count from nested metadata
                        nested = meta.get("metadata", {})
                        if isinstance(nested, dict):
                            result["entities"] = len(nested.get("entities", []))
                    except (json.JSONDecodeError, TypeError):
                        pass

                # Fallback: parse full content JSON
                if not any(result.values()):
                    content = md.get("content", "") or ""
                    if content:
                        try:
                            mir_data = json.loads(content)
                            result["operations"] = len(mir_data.get("operations", []))
                            result["data_flows"] = len(mir_data.get("data_flows", []))
                            result["effect_flows"] = len(mir_data.get("effect_flows", []))
                            result["boundaries"] = len(mir_data.get("boundaries", []))
                            meta_inner = mir_data.get("metadata", {})
                            if isinstance(meta_inner, dict):
                                result["entities"] = len(meta_inner.get("entities", []))
                        except (json.JSONDecodeError, TypeError):
                            pass

    except Exception:
        pass

    return result


def _collect_code_stats(version: str) -> Dict[str, Any]:
    """Collect code generation statistics from artifacts.db + disk scan."""
    data_dir = _get_project_root() / ".midicoder" / "data"
    artifacts_db = data_dir / "artifacts.db"

    result: Dict[str, Any] = {
        "total_files": 0,
        "total_lines": 0,
        "total_size": 0,
        "file_types": {},
    }

    # 1. Try plan metadata first
    if artifacts_db.exists():
        try:
            with sqlite3.connect(str(artifacts_db), timeout=30) as conn:
                conn.row_factory = sqlite3.Row
                plan = conn.execute(
                    "SELECT * FROM artifacts WHERE type = 'plan' AND version = ? ORDER BY id DESC LIMIT 1",
                    (version,),
                ).fetchone()
                if plan:
                    p = dict(plan)
                    meta_raw = p.get("metadata", "") or ""
                    if meta_raw:
                        try:
                            pmeta = json.loads(meta_raw)
                            result["total_files"] = (
                                pmeta.get("backend_files_count", 0)
                                + pmeta.get("frontend_files_count", 0)
                                + pmeta.get("infra_files_count", 0)
                            )
                        except (json.JSONDecodeError, TypeError):
                            pass
        except Exception:
            pass

    # 2. Scan disk for generated code
    version_dir = _get_project_root() / ".midicoder" / "versions" / version
    src_dir = version_dir / "src"
    code_dir = version_dir / "code" / "generated"

    for scan_dir in [src_dir, code_dir]:
        if scan_dir.exists():
            for fpath in scan_dir.rglob("*"):
                if fpath.is_file() and not fpath.name.startswith("."):
                    result["total_files"] += 1
                    try:
                        size = fpath.stat().st_size
                        result["total_size"] += size
                        text = fpath.read_text(encoding="utf-8", errors="ignore")
                        result["total_lines"] += text.count("\n") + (1 if text and not text.endswith("\n") else 0)
                    except Exception:
                        pass

                    # Count by extension
                    ext = fpath.suffix.lstrip(".") or "no_ext"
                    result["file_types"][ext] = result["file_types"].get(ext, 0) + 1

    return result


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def get_artifact_stats() -> Dict[str, Any]:
    """Thu thập toàn bộ stats của artifacts cho version active.

    Returns:
        Dict với keys: pipeline, briefs, contracts, ir, code
    """
    version = _get_active_version()
    if not version:
        return {
            "pipeline": {"brief": "none", "contract": "none", "ir": "none", "code": "none"},
            "briefs": {},
            "contracts": {},
            "ir": {},
            "code": {},
        }

    meta = _get_version_metadata()
    pipeline = meta.get("pipeline", {"brief": "none", "contract": "none", "ir": "none", "code": "none"})

    return {
        "pipeline": pipeline,
        "briefs": _collect_brief_stats(version),
        "contracts": _collect_contract_stats(version),
        "ir": _collect_ir_stats(version),
        "code": _collect_code_stats(version),
    }
