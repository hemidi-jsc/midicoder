"""
Router cho pipeline status
Dùng midicoder.pipeline.commands.util để đọc progress từ SQLite ArtifactsManager
"""

from pathlib import Path

from fastapi import APIRouter, Request

from app.i18n import i18n
from app.models import ApiResponse

router = APIRouter(prefix="/pipeline", tags=["Pipeline"])


def _map_progress_stage(stage_data: dict) -> str:
    """Map status từ midicoder pipeline progress sang frontend phase status"""
    status = stage_data.get("status", "not_started")
    if status in ("analyzed", "generated", "validated", "applied", "complete"):
        return "complete"
    elif status == "pending":
        return "in_progress"
    return "pending"


def _get_active_version_for_project(project_cwd: str) -> str | None:
    """Đọc active version từ project path cụ thể (không dùng Path.cwd())."""
    try:
        active_file = Path(project_cwd) / ".midicoder" / "config" / "active_version.txt"
        if active_file.exists():
            return active_file.read_text().strip()
        # Fallback: đọc từ YAML config
        import yaml
        config_file = Path(project_cwd) / ".midicoder" / "config" / "midicoder.yml"
        if config_file.exists():
            with open(config_file, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
            return cfg.get("active_version")
    except Exception:
        pass
    return None


def _get_versions_for_project(project_cwd: str) -> list[dict]:
    """List versions từ project path cụ thể (không dùng Path.cwd())."""
    versions_dir = Path(project_cwd) / ".midicoder" / "versions"
    if not versions_dir.exists():
        return []
    versions = []
    import yaml
    for vdir in versions_dir.iterdir():
        if vdir.is_dir():
            metadata = vdir / "metadata.yml"
            if metadata.exists():
                try:
                    with open(metadata, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f) or {}
                    versions.append({
                        "version": vdir.name,
                        "active": False,
                        "archived": data.get("archived", False),
                    })
                except Exception:
                    versions.append({"version": vdir.name, "active": False, "archived": False})
            else:
                versions.append({"version": vdir.name, "active": False, "archived": False})
    return versions


@router.get("/status", response_model=ApiResponse)
async def get_pipeline_status(request: Request):
    """
    Lấy trạng thái hiện tại của pipeline.

    Đọc từ midicoder.pipeline.commands.util.get_pipeline_progress()
    → ArtifactsManager (SQLite) → artifacts table
    """
    import os

    language = i18n.get_language_from_request(request)

    try:
        from midicoder.pipeline.config import get_config
        from midicoder.storage.projects import ProjectsManager
        from app.config import get_project_cwd

        # Lấy project path active
        project_cwd = get_project_cwd()

        # CLI functions dùng Path.cwd() — phải chdir đến project path trước
        original_cwd = os.getcwd()
        try:
            if project_cwd:
                os.chdir(project_cwd)

            from midicoder.pipeline.commands.util import (
                get_pipeline_progress,
                get_artifacts_summary,
                get_last_activity,
            )
            progress = get_pipeline_progress()
            artifacts = get_artifacts_summary()
            last_activity = get_last_activity()
        finally:
            os.chdir(original_cwd)

        # Versions & active version — đọc từ project path (không phải Path.cwd())
        versions = _get_versions_for_project(project_cwd)
        active_version = _get_active_version_for_project(project_cwd)

        # Đánh dấu version active
        for v in versions:
            if v["version"] == active_version:
                v["active"] = True

        # Project name từ ProjectsManager (multi-project registry)
        projects_mgr = ProjectsManager()
        projects_mgr.init()
        active_project = projects_mgr.get_active()
        if active_project:
            project_name = active_project.get("name", "")
        else:
            # Fallback: global config
            cfg = get_config()
            global_conf = cfg.load_global_config()
            project_name = global_conf.get("project", {}).get("name", "")

        # Map midicoder stages to frontend phases
        frontend_progress = {
            "init": "complete" if active_version else "pending",
            "brief": _map_progress_stage(progress.get("brief", {})),
            "contract": _map_progress_stage(progress.get("contract", {})),
            "ir": _map_progress_stage(progress.get("mir", {})),
            "code": _map_progress_stage(progress.get("code", {})),
            "preview": "pending",
        }

        return ApiResponse(
            success=True,
            data={
                "project_name": project_name or "midicoder-project",
                "project": active_project,
                "active_version": active_version,
                "pipeline_progress": frontend_progress,
                "artifacts": artifacts,
                "last_activity": last_activity,
                "versions": versions,
                "workspace_initialized": (Path(project_cwd) / ".midicoder").exists(),
            },
            message=i18n.translate("common.success", language),
            language=language,
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            data={"pipeline_progress": {
                "init": "pending", "brief": "pending",
                "contract": "pending", "ir": "pending",
                "code": "pending", "preview": "pending",
            }},
            message=f"Failed to load pipeline status: {str(e)}",
            language=language,
        )


@router.get("/versions", response_model=ApiResponse)
async def list_versions(request: Request):
    """
    List tất cả versions có sẵn.

    Đọc từ project path active (không phải Path.cwd()).
    """
    language = i18n.get_language_from_request(request)

    try:
        from app.config import get_project_cwd

        project_cwd = get_project_cwd()
        versions = _get_versions_for_project(project_cwd)
        active = _get_active_version_for_project(project_cwd)

        return ApiResponse(
            success=True,
            data={"versions": versions, "active": active},
            message=i18n.translate("common.success", language),
            language=language,
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            data={"versions": [], "active": None},
            message=f"Failed to list versions: {str(e)}",
            language=language,
        )
