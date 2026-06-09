"""
Router cho Version — reuse pipeline qua pipeline_bridge.
"""

from fastapi import APIRouter, Query, Request

from midicoder.api.pipeline_bridge import pipeline_bridge
from midicoder.api.i18n import i18n
from midicoder.api.models import ApiResponse

router = APIRouter(prefix="/version", tags=["Version"])


@router.post("/create", response_model=ApiResponse)
async def create_version(request: Request = None):
    """Tao version moi — reuse CLI `midicoder version create <name>`.
    Note: --from not used (all other versions get archived on create, making --from meaningless)."""
    language = i18n.get_language_from_request(request)

    body = await request.json()
    version = body.get("version", "")

    if not version:
        return ApiResponse(
            success=False,
            data=None,
            message="Cần cung cấp 'version' trong request body",
            language=language,
        )

    result = await pipeline_bridge.execute_command("version", "create", **{"_positional": version})

    if result["success"]:
        return ApiResponse(
            success=True,
            data={"version": version, "created": True},
            message=f"Version '{version}' đã được tạo",
            language=language,
        )

    return ApiResponse(
        success=False,
        data=None,
        message=result.get("stderr", "Tạo version thất bại"),
        language=language,
    )


@router.post("/use", response_model=ApiResponse)
async def use_version(request: Request = None):
    """Switch version — reuse CLI `midicoder version use <name>`. Không có --from."""
    language = i18n.get_language_from_request(request)

    body = await request.json()
    version = body.get("version", "")

    if not version:
        return ApiResponse(
            success=False,
            data=None,
            message="Cần cung cấp 'version' trong request body",
            language=language,
        )

    args = {"_positional": version}
    result = await pipeline_bridge.execute_command("version", "use", **args)

    if result["success"]:
        return ApiResponse(
            success=True,
            data={"version": version, "active": True},
            message=f"Đã switch sang {version}",
            language=language,
        )

    return ApiResponse(
        success=False,
        data=None,
        message=result.get("stderr", "Switch version thất bại"),
        language=language,
    )


@router.post("/check-create", response_model=ApiResponse)
async def check_create_version(request: Request = None):
    """Kiểm tra impact trước khi tạo version mới.

    Trả về:
    - will_archive: danh sách versions sẽ bị archived (active=1)
    - will_delete: danh sách versions sẽ bị auto-cleanup (vượt max_versions)
    - max_versions: giới hạn số versions
    - current_count: số version hiện tại
    """
    language = i18n.get_language_from_request(request)

    body = await request.json()
    new_version = body.get("version", "")

    # Validate version name format (semver)
    if not new_version:
        return ApiResponse(
            success=False,
            data=None,
            message="Cần cung cấp tên version",
            language=language,
        )

    # Normalize prefix
    if not new_version.startswith("v"):
        new_version = "v" + new_version

    # Validate semver format
    import re
    SEMVER = re.compile(r'^v\d+\.\d+\.\d+(-[a-zA-Z0-9.]+)?$')
    if not SEMVER.match(new_version):
        return ApiResponse(
            success=False,
            data=None,
            message=f"Tên '{new_version}' không đúng định dạng SemVer. Ví dụ: v1.0.0, v2.1.0, v1.0.0-beta",
            language=language,
        )

    try:
        from midicoder.pipeline.commands.version import _get_project_id, get_max_versions
        from midicoder.storage.projects import ProjectsManager
        from pathlib import Path

        mgr = ProjectsManager()
        mgr.init()
        active_project = mgr.get_active()
        if not active_project:
            return ApiResponse(
                success=True,
                data={"will_archive": [], "will_delete": [], "max_versions": 5, "current_count": 0},
                language=language,
            )

        project_id = active_project["project_id"]
        max_versions = get_max_versions()

        # Check version already exists
        existing = mgr.version_get(project_id, new_version)
        if existing:
            return ApiResponse(
                success=False,
                data=None,
                message=f"Version '{new_version}' đã tồn tại",
                language=language,
            )

        # Lấy tất cả versions từ SQLite
        versions = mgr.version_list(project_id)
        current_count = len(versions)

        # Check semver phải lớn hơn tất cả version hiện có
        def parse_semver(ver: str):
            """Parse v1.2.3 or v1.2.3-beta → (1, 2, 3)"""
            m = re.match(r'^v(\d+)\.(\d+)\.(\d+)', ver)
            if m:
                return (int(m.group(1)), int(m.group(2)), int(m.group(3)))
            return (0, 0, 0)

        new_ver_tuple = parse_semver(new_version)
        max_existing = max((parse_semver(v.get("version_name", "")) for v in versions), default=(0, 0, 0))
        if new_ver_tuple <= max_existing:
            max_ver_name = max(v.get("version_name", "") for v in versions if parse_semver(v.get("version_name", "")) == max_existing)
            return ApiResponse(
                success=False,
                data=None,
                message=f"Version '{new_version}' phải lớn hơn version cao nhất hiện có ('{max_ver_name}')",
                language=language,
            )

        # Versions sẽ bị archived: chỉ những version có status='inbuild'
        # (selected pointer active=1 là khác — version đang chọn bị deselect, không bị archive)
        will_archive = []
        for v in versions:
            if v.get("status") == "inbuild":
                will_archive.append({
                    "version": v.get("version_name", ""),
                    "status": v.get("status", "draft"),
                })

        # Versions sẽ bị auto-delete nếu vượt max_versions
        # Sau khi tạo version mới, count sẽ là current_count + 1
        will_delete = []
        if current_count + 1 > max_versions:
            to_delete_count = current_count + 1 - max_versions

            # Sort theo priority: archived (order=0) → draft (1) → active (2, skip)
            def sort_key(vv):
                status = vv.get("status", "draft")
                created = vv.get("created_at", "")
                status_order = {"archived": 0, "draft": 1, "inbuild": 2}.get(status, 3)
                return (status_order, created)

            sorted_versions = sorted(versions, key=sort_key)

            deleted = 0
            for v in sorted_versions:
                if deleted >= to_delete_count:
                    break
                # Không bao giờ xóa active version
                if v.get("active") == 1:
                    continue
                will_delete.append({
                    "version": v.get("version_name", ""),
                    "status": v.get("status", "draft"),
                    "created_at": v.get("created_at", ""),
                })
                deleted += 1

        return ApiResponse(
            success=True,
            data={
                "will_archive": will_archive,
                "will_delete": will_delete,
                "max_versions": max_versions,
                "current_count": current_count,
            },
            language=language,
        )
    except Exception as e:
        return ApiResponse(success=False, data=None, message=str(e), language=language)


@router.get("/list", response_model=ApiResponse)
async def list_versions(request: Request = None):
    """Lấy danh sách tất cả versions của project đang active — trả về JSON structured data."""
    language = i18n.get_language_from_request(request)

    try:
        from midicoder.pipeline.commands.version import _get_project_id, _get_project_root, get_versions_dir, get_active_version
        from midicoder.storage.projects import ProjectsManager
        from pathlib import Path

        # Lấy active project
        mgr = ProjectsManager()
        mgr.init()
        active_project = mgr.get_active()
        if not active_project:
            return ApiResponse(
                success=True,
                data={"versions": [], "active_version": None},
                language=language,
            )

        project_id = active_project["project_id"]

        # Lấy versions từ SQLite
        versions = []
        for v in mgr.version_list(project_id):
            vname = v.get("version_name", "")
            version_info = {
                "version": vname,
                "status": v.get("status", "draft"),
                "active": bool(v.get("active")),
                "parent_version": v.get("parent_version"),
                "created_at": v.get("created_at", ""),
            }

            # Load thêm metadata từ file system nếu có (chỉ field phụ, KHÔNG override status từ SQLite)
            try:
                project_root = Path(active_project["path"])
                versions_dir = project_root / ".midicoder" / "versions"
                mf = versions_dir / vname / "metadata.yml"
                if mf.exists():
                    import yaml
                    with open(mf, "r", encoding="utf-8") as f:
                        file_meta = yaml.safe_load(f) or {}
                        # Chỉ merge field phụ, bảo vệ status từ SQLite
                        for key in ("artifacts", "pipeline", "description", "parent_version", "created_at"):
                            if key in file_meta:
                                version_info[key] = file_meta[key]
            except Exception:
                pass

            versions.append(version_info)

        # Lấy active version
        active_version = mgr.version_get_active(project_id)
        active_version_name = active_version.get("version_name") if active_version else None

        return ApiResponse(
            success=True,
            data={"versions": versions, "active_version": active_version_name},
            language=language,
        )
    except Exception as e:
        return ApiResponse(success=False, data=None, message=str(e), language=language)


@router.post("/delete", response_model=ApiResponse)
async def delete_version(
    version: str = Query(..., description="Version để xóa"),
    force: bool = Query(False, description="Force delete active version"),
    request: Request = None,
):
    """Delete version — reuse CLI `midicoder version delete <name> [--force]`."""
    language = i18n.get_language_from_request(request)

    args = {"_positional": version, "force": force}
    result = await pipeline_bridge.execute_command("version", "delete", **args)

    if result["success"]:
        return ApiResponse(
            success=True,
            data={"version": version, "deleted": True},
            message=f"Đã xóa version {version}",
            language=language,
        )

    return ApiResponse(
        success=False,
        data=None,
        message=result.get("stderr", "Xóa version thất bại"),
        language=language,
    )
