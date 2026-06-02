"""
Router cho Version — tạo phiên bản mới.

Đọc/viết trực tiếp vào project path (không qua CLI subprocess).
"""

import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app.i18n import i18n
from app.models import ApiResponse, VersionCreateRequest

router = APIRouter(prefix="/version", tags=["Version"])


SEMVER_PATTERN = re.compile(
    r'^v?\d+\.\d+\.\d+(-[a-zA-Z0-9]+(\.[a-zA-Z0-9]+)*)?(\+[a-zA-Z0-9]+(\.[a-zA-Z0-9]+)*)?$'
)


class VersionCreateRequest(BaseModel):
    version: str = Field(..., description="Tên version (SemVer)")
    from_version: str | None = Field(default=None, description="Copy từ version này (tùy chọn)")


def _normalize_version(name: str) -> str:
    """Ensure version name starts with 'v'."""
    if not name.startswith('v'):
        return 'v' + name
    return name


def _validate_version(name: str) -> bool:
    return bool(SEMVER_PATTERN.match(name))


def _get_project_workspace(project_cwd: str) -> Path:
    return Path(project_cwd) / ".midicoder"


def _create_version_direct(project_cwd: str, name: str, from_version: str | None = None) -> dict:
    """
    Tạo version mới trực tiếp trên disk (không qua CLI subprocess).
    
    Reuse logic từ midicoder.pipeline.commands.version.create_version() nhưng
    dùng explicit project path thay vì Path.cwd().
    """
    name = _normalize_version(name)
    
    if not _validate_version(name):
        raise ValueError(f"Version name không hợp lệ: {name}. Dùng SemVer (v1.0.0, v1.0.1-alpha)")

    workspace = _get_project_workspace(project_cwd)
    versions_dir = workspace / "versions"
    versions_dir.mkdir(parents=True, exist_ok=True)
    version_dir = versions_dir / name

    if version_dir.exists():
        raise ValueError(f"Version '{name}' đã tồn tại")

    # Create version directory
    version_dir.mkdir(parents=True, exist_ok=True)

    # Copy from parent version if specified
    if from_version:
        from_version = _normalize_version(from_version)
        parent_dir = versions_dir / from_version
        if not parent_dir.exists():
            raise ValueError(f"Version nguồn '{from_version}' không tồn tại")
        
        parent_src = parent_dir / "src"
        if parent_src.exists():
            target_src = version_dir / "src"
            shutil.copytree(parent_src, target_src)

    # Create version metadata.yml
    metadata = {
        "version": name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "parent_version": from_version,
        "status": "active",
        "archived": False,
        "description": "",
    }
    
    metadata_file = version_dir / "metadata.yml"
    import yaml
    with open(metadata_file, "w", encoding="utf-8") as f:
        yaml.dump(metadata, f, default_flow_style=False, allow_unicode=True)

    # Set as active version
    config_dir = workspace / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    
    # Update active_version.txt
    active_file = config_dir / "active_version.txt"
    active_file.write_text(name, encoding="utf-8")
    
    # Update midicoder.yml
    config_file = config_dir / "midicoder.yml"
    if config_file.exists():
        with open(config_file, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        cfg["active_version"] = name
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(cfg, f, default_flow_style=False, allow_unicode=True)

    return {
        "version": name,
        "created": True,
        "parent_version": from_version,
    }


@router.post("/create", response_model=ApiResponse)
async def create_version(request_data: VersionCreateRequest, request: Request):
    """
    Tạo phiên bản mới.
    
    Tạo directory .midicoder/versions/{name}/ với metadata.yml,
    set active_version.txt, và update midicoder.yml.
    """
    language = i18n.get_language_from_request(request)
    try:
        from app.config import get_project_cwd

        project_cwd = get_project_cwd()
        result = _create_version_direct(
            project_cwd,
            request_data.version,
            request_data.from_version,
        )

        return ApiResponse(
            success=True,
            data=result,
            message=f"Version '{result['version']}' đã được tạo thành công",
            language=language,
        )
    except ValueError as e:
        return ApiResponse(
            success=False,
            data=None,
            message=str(e),
            language=language,
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            data=None,
            message=f"Tạo version thất bại: {str(e)}",
            language=language,
        )
