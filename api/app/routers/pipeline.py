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


@router.get("/status", response_model=ApiResponse)
async def get_pipeline_status(request: Request):
    """
    Lấy trạng thái hiện tại của pipeline.

    Đọc từ midicoder.pipeline.commands.util.get_pipeline_progress()
    → ArtifactsManager (SQLite) → artifacts table
    """
    language = i18n.get_language_from_request(request)

    try:
        from midicoder.pipeline.commands.util import (
            get_pipeline_progress,
            get_artifacts_summary,
            get_last_activity,
            get_versions_list,
        )
        from midicoder.pipeline.commands.version import get_active_version
        from midicoder.pipeline.config import get_config
        from midicoder.storage.projects import ProjectsManager

        # Progress từ SQLite ArtifactsManager
        progress = get_pipeline_progress()
        artifacts = get_artifacts_summary()
        last_activity = get_last_activity()
        versions = get_versions_list()

        # Active version
        active_version = get_active_version()

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
                "active_version": active_version,  # None nếu chưa có version nào
                "pipeline_progress": frontend_progress,
                "artifacts": artifacts,
                "last_activity": last_activity,
                "versions": versions,
                "workspace_initialized": Path(".midicoder").exists(),
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

    Dùng midicoder pipeline để lấy versions list.
    """
    language = i18n.get_language_from_request(request)

    try:
        from midicoder.pipeline.commands.util import get_versions_list
        from midicoder.pipeline.commands.version import get_active_version

        versions = get_versions_list()
        active = get_active_version()

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
