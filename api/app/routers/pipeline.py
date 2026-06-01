"""
Router cho pipeline status
Scan .midicoder/versions/ để xác định progress của từng phase
"""

import json
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, Request

from app.i18n import i18n
from app.models import ApiResponse

router = APIRouter(prefix="/pipeline", tags=["Pipeline"])


def _get_active_version() -> str | None:
    """Lấy active version từ .midicoder/config/"""
    config_dir = Path(".midicoder") / "config"
    active_file = config_dir / "active_version.txt"
    if active_file.exists():
        return active_file.read_text().strip()
    # Fallback: lấy version đầu tiên
    versions_dir = Path(".midicoder") / "versions"
    if versions_dir.exists():
        versions = list(versions_dir.iterdir())
        if versions:
            return versions[0].name
    return None


def _check_file_exists(version_dir: Path, *paths: str) -> bool:
    """Check nếu file tồn tại trong version directory"""
    return (version_dir / "/".join(paths)).exists()


def _detect_phase_status(version_dir: Path, phase_files: list[tuple[str, str]]) -> str:
    """
    Detect status của một phase dựa trên existence của artifact files.
    
    Args:
        version_dir: Path đến version directory
        phase_files: List của (display_name, relative_path)
        
    Returns:
        'complete' nếu có file, 'pending' nếu không
    """
    for _, rel_path in phase_files:
        if _check_file_exists(version_dir, *rel_path.split("/")):
            return "complete"
    return "pending"


def _get_pipeline_progress(version_dir: Path) -> Dict[str, Any]:
    """
    Build pipeline progress từ disk artifacts.
    
    Returns:
        Dict với status của từng phase
    """
    progress = {
        "init": "complete" if version_dir.exists() else "pending",
        "brief": _detect_phase_status(version_dir, [
            ("master_brief", "briefs/master-brief.md"),
            ("working_brief", "briefs/working-brief.md"),
        ]),
        "contract": _detect_phase_status(version_dir, [
            ("ir", "contracts/ir.json"),
            ("manifest", "contracts/manifest.json"),
        ]),
        "ir": _detect_phase_status(version_dir, [
            ("mir", "ir/mir.json"),
            ("symbol_table", "ir/symbol-table.json"),
        ]),
        "code": "pending",
        "preview": "pending",
    }

    # Code phase có nhiều sub-steps
    code_steps = []
    if _check_file_exists(version_dir, "plan", "lowering.json"):
        code_steps.append("plan_complete")
    if _check_file_exists(version_dir, "code", "generated") and (version_dir / "code" / "generated").is_dir():
        code_steps.append("gen_complete")
    if _check_file_exists(version_dir, "code", "applied", "status.json"):
        code_steps.append("apply_complete")
        progress["code"] = "complete"
    elif code_steps:
        progress["code"] = "in_progress"
        progress["code_step"] = code_steps[-1]

    return progress


@router.get("/status", response_model=ApiResponse)
async def get_pipeline_status(request: Request):
    """
    Lấy trạng thái hiện tại của pipeline.
    
    Scan các artifact files trong .midicoder/versions/{active_version}/
    để xác định phase nào đã hoàn thành.
    
    Returns:
        ApiResponse: Pipeline progress
    """
    language = i18n.get_language_from_request(request)

    version = _get_active_version()
    versions_dir = Path(".midicoder") / "versions"
    version_dir = versions_dir / version if version else Path("")

    progress = _get_pipeline_progress(version_dir)

    # Get project name từ config
    project_name = "midicoder-project"
    config_file = Path(".midicoder") / "config" / "midicoder.yml"
    if config_file.exists():
        try:
            content = config_file.read_text()
            for line in content.split("\n"):
                if line.startswith("project_name:"):
                    project_name = line.split(":", 1)[1].strip().strip('"').strip("'")
                    break
        except Exception:
            pass

    return ApiResponse(
        success=True,
        data={
            "project_name": project_name,
            "active_version": version,
            "pipeline_progress": progress,
            "versions_dir_exists": versions_dir.exists(),
            "version_dir": str(version_dir),
        },
        message=i18n.translate("common.success", language),
        language=language,
    )


@router.get("/versions", response_model=ApiResponse)
async def list_versions(request: Request):
    """
    List tất cả versions có sẵn.
    
    Returns:
        ApiResponse: Danh sách versions
    """
    language = i18n.get_language_from_request(request)

    versions_dir = Path(".midicoder") / "versions"
    versions = []

    if versions_dir.exists():
        for v in versions_dir.iterdir():
            if v.is_dir():
                versions.append({
                    "name": v.name,
                    "path": str(v),
                    "has_brief": (v / "briefs" / "master-brief.md").exists(),
                    "has_contract": (v / "contracts" / "ir.json").exists(),
                    "has_ir": (v / "ir" / "mir.json").exists(),
                    "has_code": (v / "code" / "generated").exists(),
                })

    return ApiResponse(
        success=True,
        data={"versions": versions, "active": _get_active_version()},
        message=i18n.translate("common.success", language),
        language=language,
    )
