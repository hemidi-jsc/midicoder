"""
Router cho Version — tất cả logic qua pipeline_bridge.
"""

from fastapi import APIRouter, Query, Request

from midicoder.api.pipeline_bridge import pipeline_bridge
from midicoder.api.i18n import i18n
from midicoder.api.models import ApiResponse

router = APIRouter(prefix="/version", tags=["Version"])


@router.post("/create", response_model=ApiResponse)
async def create_version(request: Request = None):
    """Tạo version mới — reuse pipeline."""
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
    """Switch version — reuse pipeline."""
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
    """Kiểm tra impact trước khi tạo version mới — delegate vào pipeline."""
    language = i18n.get_language_from_request(request)

    body = await request.json()
    new_version = body.get("version", "")

    if not new_version:
        return ApiResponse(
            success=False,
            data=None,
            message="Cần cung cấp tên version",
            language=language,
        )

    result = await pipeline_bridge.execute_command(
        "version", "check-create", _positional=new_version
    )

    if result["success"]:
        data = result.get("_data", {})
        error = data.get("error")
        if error:
            return ApiResponse(
                success=False,
                data=None,
                message=error,
                language=language,
            )
        return ApiResponse(
            success=True,
            data={
                "will_archive": data.get("will_archive", []),
                "will_delete": data.get("will_delete", []),
                "max_versions": data.get("max_versions", 5),
                "current_count": data.get("current_count", 0),
                "parent_version": data.get("parent_version"),
            },
            language=language,
        )

    return ApiResponse(
        success=False,
        data=None,
        message=result.get("stderr", "Không thể kiểm tra"),
        language=language,
    )


@router.get("/list", response_model=ApiResponse)
async def list_versions(request: Request = None):
    """Lấy danh sách versions — delegate vào pipeline."""
    language = i18n.get_language_from_request(request)

    result = await pipeline_bridge.execute_command("version", "list-json")

    if result["success"]:
        data = result.get("_data", {})
        return ApiResponse(
            success=True,
            data={
                "versions": data.get("versions", []),
                "active_version": data.get("active_version"),
            },
            language=language,
        )

    return ApiResponse(
        success=False,
        data=None,
        message=result.get("stderr", "Không thể lấy danh sách versions"),
        language=language,
    )


@router.post("/delete", response_model=ApiResponse)
async def delete_version(
    version: str = Query(..., description="Version để xóa"),
    force: bool = Query(False, description="Force delete active version"),
    request: Request = None,
):
    """Delete version — reuse pipeline."""
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
