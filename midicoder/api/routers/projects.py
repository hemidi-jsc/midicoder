"""
Projects router — multi-project management via SQLite projects.db.
"""

import hashlib
from pathlib import Path

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from midicoder.api.i18n import i18n
from midicoder.api.models import ApiResponse

router = APIRouter(prefix="/projects", tags=["Projects"])


def _set_config_project_path(path: str) -> None:
    """Update ConfigManager to load project YAML from the given path."""
    try:
        from midicoder.pipeline.config import get_config
        cfg = get_config()
        cfg.set_project_path(path)
    except Exception:
        pass


def _reset_config_project_path() -> None:
    try:
        from midicoder.pipeline.config import get_config
        cfg = get_config()
        cfg.set_project_path(None)
    except Exception:
        pass


class ProjectCreateRequest(BaseModel):
    name: str = Field(..., description="Tên project")
    path: str = Field(..., description="Đường dẫn tuyệt đối đến folder project")
    stack: str = Field(default="", description="Tech stack (tùy chọn)")


class ProjectUpdateRequest(BaseModel):
    name: str = Field(default=None, description="Tên mới")


# ============================================================================
# GET /projects — list tất cả projects
# ============================================================================

@router.get("/", response_model=ApiResponse)
async def list_projects(request: Request):
    """Lấy danh sách tất cả projects và project đang active."""
    language = i18n.get_language_from_request(request)
    try:
        from midicoder.storage.projects import ProjectsManager
        mgr = ProjectsManager()
        mgr.init()

        projects = mgr.list_all()
        active = mgr.get_active()

        return ApiResponse(
            success=True,
            data={
                "projects": projects,
                "active": active,
            },
            language=language,
        )
    except Exception as e:
        return ApiResponse(success=False, data=None, message=str(e), language=language)


# ============================================================================
# POST /projects — tạo project mới + init workspace
# ============================================================================

@router.post("/", response_model=ApiResponse)
async def create_project(request_data: ProjectCreateRequest, request: Request):
    """
    Tạo project mới:
    1. Tạo workspace structure + SQLite databases (trực tiếp, không qua CLI)
    2. Ghi vào projects registry (SQLite)
    3. Đánh dấu active
    """
    language = i18n.get_language_from_request(request)
    try:
        from datetime import datetime, timezone

        import yaml

        from midicoder.pipeline.config import get_config
        from midicoder.storage.projects import ProjectsManager
        from midicoder.storage.sqlite import (
            SCHEMA_ARTIFACTS,
            SCHEMA_ACTIVITY,
            SCHEMA_BRIEFS,
            SCHEMA_CONTEXT,
            SCHEMA_PROVENANCE,
            init_database,
        )

        path = Path(request_data.path).resolve()
        path_str = str(path)

        # Tạo project_id từ path
        project_id = hashlib.md5(path_str.encode()).hexdigest()[:12]

        # Kiểm tra đã tồn tại chưa
        mgr = ProjectsManager()
        mgr.init()
        existing = mgr.get_by_path(path_str)
        if existing:
            # Đánh dấu active
            mgr.activate(existing["project_id"])
            _set_config_project_path(path_str)
            return ApiResponse(
                success=True,
                data={"project": existing, "created": False, "already_exists": True},
                message="Project đã tồn tại, đã đánh dấu active",
                language=language,
            )

        # Kiểm tra workspace đã tồn tại — nếu có .midicoder/config/midicoder.yml → import
        workspace_dir = path / ".midicoder"
        if workspace_dir.exists():
            existing_config = workspace_dir / "config" / "midicoder.yml"
            if existing_config.exists():
                # Project Midicoder có sẵn — import thay vì reject
                import yaml as _yaml
                try:
                    cfg_data = _yaml.safe_load(existing_config.read_text()) or {}
                except Exception:
                    cfg_data = {}
                if "midicoder_version" not in cfg_data:
                    return ApiResponse(
                        success=False,
                        data=None,
                        message=f"Folder {workspace_dir} không phải project Midicoder (thiếu midicoder_version trong config).",
                        language=language,
                    )
                # Import: register + activate
                mgr.activate(existing["project_id"]) if existing else None
                project = mgr.create(
                    project_id=project_id,
                    name=request_data.name,
                    path=path_str,
                    set_active=True,
                )
                _set_config_project_path(path_str)
                return ApiResponse(
                    success=True,
                    data={"project": project, "created": False, "imported": True},
                    message=f"Đã import project '{request_data.name}' từ disk",
                    language=language,
                )
            else:
                # Folder tồn tại nhưng không phải Midicoder project
                return ApiResponse(
                    success=False,
                    data=None,
                    message=f"Folder {workspace_dir} tồn tại nhưng không phải project Midicoder.",
                    language=language,
                )

        # 1. Tạo cấu trúc thư mục
        for sub in ("config", "data", "versions", "runtime", "cache"):
            (workspace_dir / sub).mkdir(parents=True, exist_ok=True)

        # 2. Khởi tạo SQLite databases
        data_dir = workspace_dir / "data"
        init_database(data_dir / "briefs.db", SCHEMA_BRIEFS)
        init_database(data_dir / "artifacts.db", SCHEMA_ARTIFACTS + SCHEMA_ACTIVITY)
        init_database(data_dir / "provenance.db", SCHEMA_PROVENANCE)
        init_database(data_dir / "context.db", SCHEMA_CONTEXT)

        # 3. Tạo project config file (không set active_version - sẽ set khi tạo version đầu tiên)
        config_file = workspace_dir / "config" / "midicoder.yml"
        config_data = {
            "midicoder_version": "1.0.0",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "max_versions": 5,
            "capabilities": {"enabled": []},
        }
        config_file.write_text(
            yaml.dump(config_data, default_flow_style=False, allow_unicode=True),
            encoding="utf-8",
        )

        # 4. Save vào projects registry + activate + set config path
        project = mgr.create(
            project_id=project_id,
            name=request_data.name,
            path=path_str,
            set_active=True,
        )
        _set_config_project_path(path_str)

        return ApiResponse(
            success=True,
            data={"project": project, "created": True},
            message=f"Project '{request_data.name}' đã được tạo thành công",
            language=language,
        )
    except Exception as e:
        return ApiResponse(success=False, data=None, message=str(e), language=language)


# ============================================================================
# POST /projects/:id/activate — chuyển project active
# ============================================================================

@router.post("/{project_id}/activate", response_model=ApiResponse)
async def activate_project(project_id: str, request: Request):
    """Đánh dấu project là active."""
    language = i18n.get_language_from_request(request)
    try:
        from midicoder.storage.projects import ProjectsManager
        mgr = ProjectsManager()
        mgr.init()

        project = mgr.get(project_id)
        if not project:
            return ApiResponse(
                success=False,
                data=None,
                message=f"Project '{project_id}' không tồn tại",
                language=language,
            )

        mgr.activate(project_id)
        _set_config_project_path(project["path"])

        return ApiResponse(
            success=True,
            data={"project": mgr.get(project_id)},
            message=f"Đã chuyển sang project '{project['name']}'",
            language=language,
        )
    except Exception as e:
        return ApiResponse(success=False, data=None, message=str(e), language=language)


# ============================================================================
# DELETE /projects/:id — xóa project khỏi registry
# ============================================================================

@router.delete("/{project_id}", response_model=ApiResponse)
async def delete_project(project_id: str, request: Request):
    """Xóa project khỏi registry (không xóa thư mục trên disk)."""
    language = i18n.get_language_from_request(request)
    try:
        from midicoder.storage.projects import ProjectsManager
        mgr = ProjectsManager()
        mgr.init()

        project = mgr.get(project_id)
        if not project:
            return ApiResponse(
                success=False,
                data=None,
                message=f"Project '{project_id}' không tồn tại",
                language=language,
            )

        # Không cho xóa project đang active nếu có nhiều projects
        if project.get("active"):
            all_projects = mgr.list_all()
            if len(all_projects) > 1:
                return ApiResponse(
                    success=False,
                    data=None,
                    message="Không thể xóa project đang active. Hãy chuyển sang project khác trước.",
                    language=language,
                )

        name = project.get("name", project_id)
        mgr.delete(project_id)

        return ApiResponse(
            success=True,
            data=None,
            message=f"Đã xóa project '{name}' khỏi registry",
            language=language,
        )
    except Exception as e:
        return ApiResponse(success=False, data=None, message=str(e), language=language)


# ============================================================================
# GET /projects/active — lấy project đang active
# ============================================================================

@router.get("/active", response_model=ApiResponse)
async def get_active_project(request: Request):
    """Lấy project đang active."""
    language = i18n.get_language_from_request(request)
    try:
        from midicoder.storage.projects import ProjectsManager
        mgr = ProjectsManager()
        mgr.init()

        active = mgr.get_active()
        return ApiResponse(
            success=True,
            data={"project": active},
            language=language,
        )
    except Exception as e:
        return ApiResponse(success=False, data=None, message=str(e), language=language)
