"""
Project Management Commands — logic nằm trong pipeline, API chỉ reuse qua pipeline_bridge.

Trách nhiệm:
- init_workspace: tạo thư mục + SQLite DB + config YAML
- project_create: register vào projects.db
- project_activate: chuyển active project
- project_delete: xóa khỏi registry
- project_list: list tất cả projects
- project_get_active: lấy project đang active
- get_techstacks, get_prompt_domains: metadata helper

Tất cả thao tác ghi vào SQLite (projects.db) ĐỀU đồng bộ với file system.
"""

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM
from midicoder.storage.projects import ProjectsManager
from midicoder.storage.sqlite import (
    SCHEMA_ARTIFACTS,
    SCHEMA_ACTIVITY,
    SCHEMA_BRIEFS,
    SCHEMA_CONTEXT,
    SCHEMA_PROVENANCE,
    get_connection,
    init_database,
)
from midicoder.storage.activity import log as _log_activity


# ============================================================================
# Workspace initialization
# ============================================================================


def init_workspace(
    project_path: str,
    tech_stack: dict,
    prompt_domain: str,
    max_versions: int = 5,
) -> Dict[str, Any]:
    """
    Khởi tạo workspace structure cho project mới.

    Tạo:
    - .midicoder/{config,data,versions,runtime,cache}/
    - SQLite databases (briefs.db, artifacts.db, provenance.db, context.db)
    - .midicoder/config/midicoder.yml

    Args:
        project_path: Đường dẫn tuyệt đối đến folder project
        tech_stack: {infrastructure, backend, frontend, ui_framework}
        prompt_domain: Domain prompt engineering
        max_versions: Giới hạn số versions (mặc định 5)

    Returns:
        dict với keys: workspace_dir, config_file, project_id
    """
    path = Path(project_path).resolve()
    workspace_dir = path / ".midicoder"

    # 1. Tạo cấu trúc thư mục
    for sub in ("config", "data", "versions", "runtime", "cache"):
        (workspace_dir / sub).mkdir(parents=True, exist_ok=True)
    _log_activity("project.workspace_created", resource_id=str(path),
                  details={"workspace": str(workspace_dir.relative_to(path))})

    # 2. Khởi tạo SQLite databases
    data_dir = workspace_dir / "data"
    init_database(data_dir / "briefs.db", SCHEMA_BRIEFS)
    init_database(data_dir / "artifacts.db", SCHEMA_ARTIFACTS + SCHEMA_ACTIVITY)
    init_database(data_dir / "provenance.db", SCHEMA_PROVENANCE)
    init_database(data_dir / "context.db", SCHEMA_CONTEXT)
    _log_activity("project.db_initialized", resource_id=str(path),
                  details={"databases": ["briefs.db", "artifacts.db", "provenance.db", "context.db"]})

    # 3. Tạo project config YAML
    config_file = workspace_dir / "config" / "midicoder.yml"
    config_data = {
        "midicoder_version": "1.0.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "max_versions": max_versions,
        "tech_stack": tech_stack,
        "prompt_domain": prompt_domain,
        "capabilities": {"enabled": []},
    }
    config_file.write_text(
        yaml.dump(config_data, default_flow_style=False, allow_unicode=True),
        encoding="utf-8",
    )
    _log_activity("project.config_created", resource_id=str(path),
                  details={"config_file": str(config_file.relative_to(path))})

    project_id = hashlib.md5(str(path).encode()).hexdigest()[:12]

    return {
        "workspace_dir": str(workspace_dir),
        "config_file": str(config_file),
        "project_id": project_id,
    }


# ============================================================================
# Project CRUD — SQLite projects.db + ConfigManager sync
# ============================================================================


def _ensure_manager() -> ProjectsManager:
    mgr = ProjectsManager()
    mgr.init()
    return mgr


def _set_config_project_path(path: Optional[str]) -> None:
    """Update ConfigManager._project_path để load YAML đúng project."""
    try:
        from midicoder.pipeline.config import get_config
        cfg = get_config()
        cfg.set_project_path(path)
    except Exception:
        pass


def _enrich_with_git_info(project: Dict[str, Any]) -> Dict[str, Any]:
    """Thêm repo_url từ git remote vào project dict."""
    from midicoder.pipeline.commands.git_helper import get_repo_url
    path = project.get("path", "")
    if path:
        project["repo_url"] = get_repo_url(path)
    else:
        project["repo_url"] = None
    return project


def _enrich_with_tech_stack(project: Dict[str, Any]) -> Dict[str, Any]:
    """Đọc tech_stack + prompt_domain từ midicoder.yml vào project dict."""
    path = project.get("path", "")
    if not path:
        project["tech_stack"] = None
        project["prompt_domain"] = None
        return project
    config_file = Path(path) / ".midicoder" / "config" / "midicoder.yml"
    if config_file.exists():
        try:
            cfg_data = yaml.safe_load(config_file.read_text(encoding="utf-8")) or {}
            project["tech_stack"] = cfg_data.get("tech_stack", {})
            project["prompt_domain"] = cfg_data.get("prompt_domain", "")
        except Exception:
            project["tech_stack"] = {}
            project["prompt_domain"] = ""
    else:
        project["tech_stack"] = {}
        project["prompt_domain"] = ""
    return project


def project_list() -> Dict[str, Any]:
    """List tất cả projects và project đang active."""
    mgr = _ensure_manager()
    projects = [_enrich_with_git_info(_enrich_with_tech_stack(dict(p))) for p in mgr.list_all()]
    active = mgr.get_active()
    if active:
        active = _enrich_with_git_info(_enrich_with_tech_stack(active))

    return {
        "projects": projects,
        "active": active,
    }


def project_get_active() -> Optional[Dict[str, Any]]:
    """Lấy project đang active (bao gồm tech_stack từ midicoder.yml)."""
    mgr = _ensure_manager()
    project = mgr.get_active()
    if project:
        project = _enrich_with_git_info(project)
        project = _enrich_with_tech_stack(project)
    return project


def project_create(
    name: str,
    path: str,
    tech_stack: dict,
    prompt_domain: str,
) -> Dict[str, Any]:
    """
    Tạo project mới: init workspace + register SQLite + activate + set ConfigManager.

    Flow:
    1. Kiểm tra đã tồn tại (theo path) → nếu có thì activate/import
    2. Init workspace structure + DB + YAML config
    3. Register vào projects.db
    4. Activate + set ConfigManager._project_path

    Returns:
        dict: {project, created, message}
    """
    path_resolved = str(Path(path).resolve())
    project_id = hashlib.md5(path_resolved.encode()).hexdigest()[:12]

    mgr = _ensure_manager()

    # Kiểm tra đã tồn tại theo path
    existing = mgr.get_by_path(path_resolved)
    if existing:
        mgr.activate(existing["project_id"])
        _set_config_project_path(path_resolved)
        _log_activity("project.activated", resource_id=existing["project_id"],
                      details={"name": existing["name"], "reason": "already_exists"})
        return {
            "project": existing,
            "created": False,
            "already_exists": True,
        }

    # Kiểm tra workspace đã tồn tại — import nếu là Midicoder project
    workspace_dir = Path(path_resolved) / ".midicoder"
    if workspace_dir.exists():
        existing_config = workspace_dir / "config" / "midicoder.yml"
        if existing_config.exists():
            try:
                cfg_data = yaml.safe_load(existing_config.read_text()) or {}
            except Exception:
                cfg_data = {}
            if "midicoder_version" in cfg_data:
                # Import existing Midicoder project
                if existing:
                    mgr.activate(existing["project_id"])
                else:
                    # Register mới
                    result = init_workspace(path_resolved, tech_stack, prompt_domain)
                    mgr.create(
                        project_id=project_id,
                        name=name,
                        path=path_resolved,
                        set_active=True,
                    )
                _set_config_project_path(path_resolved)
                _log_activity("project.imported", resource_id=project_id,
                              details={"name": name, "path": path_resolved})
                return {
                    "project": mgr.get(project_id) or existing,
                    "created": False,
                    "imported": True,
                }
            else:
                EM.raise_error(
                    ErrorCode.CONFIG_READ_FAILED,
                    message=f"Folder {workspace_dir} không phải project Midicoder (thiếu midicoder_version trong config).",
                    path=str(workspace_dir),
                )
        else:
            EM.raise_error(
                ErrorCode.CONFIG_READ_FAILED,
                message=f"Folder {workspace_dir} tồn tại nhưng không phải project Midicoder.",
                path=str(workspace_dir),
            )

    # Tạo project mới hoàn toàn
    _log_activity("project.creating", resource_id=project_id,
                  details={"name": name, "path": path_resolved})

    # 1. Init workspace
    init_workspace(path_resolved, tech_stack, prompt_domain)

    # 2. Register + activate
    project = mgr.create(
        project_id=project_id,
        name=name,
        path=path_resolved,
        set_active=True,
    )

    # 3. Set ConfigManager
    _set_config_project_path(path_resolved)

    _log_activity("project.created", resource_id=project_id,
                  details={"name": name, "path": path_resolved})

    return {
        "project": project,
        "created": True,
    }


def project_activate(project_id: str) -> Dict[str, Any]:
    """Chuyển active project + update ConfigManager."""
    mgr = _ensure_manager()

    project = mgr.get(project_id)
    if not project:
        EM.raise_error(
            ErrorCode.VERSION_NOT_FOUND,
            message=f"Project '{project_id}' không tồn tại",
            version=project_id,
        )

    mgr.activate(project_id)
    _set_config_project_path(project["path"])
    _log_activity("project.switched", resource_id=project_id,
                  details={"name": project["name"]})

    return {"project": mgr.get(project_id)}


def project_delete(project_id: str) -> Dict[str, Any]:
    """Xóa project khỏi registry (không xóa folder)."""
    mgr = _ensure_manager()

    project = mgr.get(project_id)
    if not project:
        EM.raise_error(
            ErrorCode.VERSION_NOT_FOUND,
            message=f"Project '{project_id}' không tồn tại",
            version=project_id,
        )

    # Không cho xóa project active nếu có nhiều projects
    if project.get("active"):
        all_projects = mgr.list_all()
        if len(all_projects) > 1:
            EM.raise_error(
                ErrorCode.VERSION_DELETE_ACTIVE,
                message="Không thể xóa project đang active. Hãy chuyển sang project khác trước.",
                version=project_id,
            )

    name = project.get("name", project_id)
    mgr.delete(project_id)
    _log_activity("project.deleted", resource_id=project_id,
                  details={"name": name})

    return {"name": name}


# ============================================================================
# Tech stack + prompt domain metadata
# ============================================================================


def get_techstacks() -> Dict[str, Any]:
    """Lấy danh sách tech stack hỗ trợ từ contracts/registry."""
    from midicoder.contracts.registry import (
        BACKEND_STACKS,
        FRONTEND_STACKS,
        INFRA_STACK,
    )
    from midicoder.packs.models import PresetType

    STACK_LABELS = {
        "fastapi": "FastAPI (Python)",
        "nestjs": "NestJS (TypeScript)",
        "angular": "Angular",
        "react": "React",
        "infrastructure": "Infrastructure (Docker/K8s)",
    }

    return {
        "infrastructure": [{"value": INFRA_STACK, "label": STACK_LABELS.get(INFRA_STACK, INFRA_STACK)}],
        "backend": [{"value": s, "label": STACK_LABELS.get(s, s)} for s in sorted(BACKEND_STACKS)],
        "frontend": [{"value": s, "label": STACK_LABELS.get(s, s)} for s in sorted(FRONTEND_STACKS)],
        "ui_framework": [{"value": p.value, "label": p.value.capitalize()} for p in PresetType],
    }


def get_prompt_domains() -> List[Dict[str, str]]:
    """Scan pipeline/prompts/ cho domain subdirs."""
    prompts_dir = Path(__file__).parent.parent / "prompts"
    domains = [{"value": "default", "label": "Default"}]
    if prompts_dir.is_dir():
        for entry in sorted(prompts_dir.iterdir()):
            if entry.is_dir() and not entry.name.startswith("__"):
                domains.append({"value": entry.name, "label": entry.name.replace("_", " ").title()})
    return domains
