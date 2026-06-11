"""
Router cho pipeline status
Đọc trực tiếp từ SQLite với explicit project path (không dùng Path.cwd())
"""

import sqlite3
from pathlib import Path

from fastapi import APIRouter, Request

from midicoder.api.i18n import i18n
from midicoder.api.models import ApiResponse

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
            content = active_file.read_text().strip()
            if content:
                return content
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
    for vdir in sorted(versions_dir.iterdir(), key=lambda d: d.name):
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


def _get_pipeline_progress_from_sqlite(db_path: Path) -> dict:
    """Đọc pipeline progress trực tiếp từ SQLite artifacts table."""
    if not db_path.exists():
        return {}
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT artifact_id, status FROM artifacts ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()

        progress = {}
        for row in rows:
            aid = row["artifact_id"] or ""
            status = row["status"] or "pending"
            if aid.startswith("brief_"):
                progress["brief"] = {"status": status}
            elif aid.startswith("analysis-brief"):
                progress["brief"] = {"status": "generated"}
            elif aid.startswith("contract_"):
                progress["contract"] = {"status": status}
            elif aid.startswith("mir_"):
                progress["mir"] = {"status": status}
            elif aid.startswith("plan_"):
                progress["code"] = {"status": status}
            elif aid.startswith("code_"):
                progress["code"] = {"status": "generated"}
        return progress
    except Exception:
        return {}


def _get_artifacts_summary_from_sqlite(db_path: Path) -> dict:
    """Đọc artifacts summary trực tiếp từ SQLite."""
    if not db_path.exists():
        return {"briefs": 0, "contracts": 0, "mir": 0, "plans": 0, "code": 0}
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT artifact_id, COUNT(*) as cnt FROM artifacts GROUP BY artifact_id")
        rows = cursor.fetchall()
        conn.close()

        summary = {"briefs": 0, "contracts": 0, "mir": 0, "plans": 0, "code": 0}
        for row in rows:
            aid = row[0] or ""
            cnt = row[1] or 0
            if aid.startswith("brief_"):
                summary["briefs"] += cnt
            elif aid.startswith("contract_"):
                summary["contracts"] += cnt
            elif aid.startswith("mir_"):
                summary["mir"] += cnt
            elif aid.startswith("plan_"):
                summary["plans"] += cnt
            elif aid.startswith("code_"):
                summary["code"] += cnt
        return summary
    except Exception:
        return {"briefs": 0, "contracts": 0, "mir": 0, "plans": 0, "code": 0}


def _get_last_activity_from_sqlite(db_path: Path) -> str | None:
    """Đọc last activity từ SQLite artifacts table."""
    if not db_path.exists():
        return None
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT updated_at FROM artifacts ORDER BY updated_at DESC LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None
    except Exception:
        return None


@router.get("/status", response_model=ApiResponse)
async def get_pipeline_status(request: Request):
    """
    Lấy trạng thái hiện tại của pipeline.
    
    Đọc trực tiếp từ SQLite với explicit project path (không dùng CLI Path.cwd()).
    """
    language = i18n.get_language_from_request(request)

    try:
        from midicoder.pipeline.config import get_config
        from midicoder.storage.projects import ProjectsManager, DB_PROJECTS
        from midicoder.api.config import get_project_cwd

        # Lấy project path active
        project_cwd = get_project_cwd()
        data_dir = Path(project_cwd) / ".midicoder" / "data"
        artifacts_db = data_dir / "artifacts.db"

        # Đọc progress trực tiếp từ SQLite (không qua CLI)
        progress = _get_pipeline_progress_from_sqlite(artifacts_db)
        artifacts = _get_artifacts_summary_from_sqlite(artifacts_db)
        last_activity = _get_last_activity_from_sqlite(artifacts_db)

        # Versions & active version — đọc từ project path (không phải Path.cwd())
        versions = _get_versions_for_project(project_cwd)
        active_version = _get_active_version_for_project(project_cwd)

        # Đánh dấu version active + lọc status archived
        from midicoder.api.config import get_version_status
        for v in versions:
            vname = v["version"]
            v["active"] = vname == active_version
            status = get_version_status(vname) or "draft"
            v["status"] = status
            v["is_archived"] = status == "archived"

        # Nếu active version bị archived → block pipeline progress
        active_status = get_version_status(active_version) if active_version else None
        if active_status == "archived":
            return ApiResponse(
                success=False,
                data=None,
                message=f"Version '{active_version}' đã bị archived và không thể truy cập nữa. Hãy switch sang version đang active.",
                language=language,
            )

        # Project name từ ProjectsManager (multi-project registry)
        projects_mgr = ProjectsManager(db_path=DB_PROJECTS)
        projects_mgr.init()
        active_project = projects_mgr.get_active()
        if active_project:
            project_name = active_project.get("name", "")
        else:
            project_name = ""

        # Map midicoder stages to frontend phases
        frontend_progress = {
            "init": "complete" if active_version else "pending",
            "brief": _map_progress_stage(progress.get("brief", {})),
            "contract": _map_progress_stage(progress.get("contract", {})),
            "ir": _map_progress_stage(progress.get("mir", {})),
            "code": _map_progress_stage(progress.get("code", {})),
            "preview": "pending",
        }

        workspace_initialized = (Path(project_cwd) / ".midicoder").exists()

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
                "workspace_initialized": workspace_initialized,
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
        from midicoder.api.config import get_project_cwd

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
