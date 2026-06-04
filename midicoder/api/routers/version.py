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
    """Tạo version mới — reuse CLI `midicoder version create <name> [--from parent]`."""
    language = i18n.get_language_from_request(request)

    body = await request.json()
    version = body.get("version", "")
    from_version = body.get("from_version")

    if not version:
        return ApiResponse(
            success=False,
            data=None,
            message="Cần cung cấp 'version' trong request body",
            language=language,
        )

    args = {"_positional": version}
    if from_version:
        args["from"] = from_version

    result = await pipeline_bridge.execute_command("version", "create", args)

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

    result = await pipeline_bridge.execute_command("version", "use", {"_positional": version})

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


@router.get("/list", response_model=ApiResponse)
async def list_versions(request: Request = None):
    """List versions — reuse CLI `midicoder version list`."""
    language = i18n.get_language_from_request(request)

    result = await pipeline_bridge.execute_command("version", "list")

    if result["success"]:
        return ApiResponse(
            success=True,
            data={"raw_output": result.get("stdout", "")},
            language=language,
        )

    return ApiResponse(
        success=False,
        data=None,
        message=result.get("stderr", "List versions thất bại"),
        language=language,
    )


@router.post("/delete", response_model=ApiResponse)
async def delete_version(
    version: str = Query(..., description="Version để xóa"),
    force: bool = Query(False, description="Force delete active version"),
    request: Request = None,
):
    """Delete version — reuse CLI `midicoder version delete <name> [--force]`."""
    language = i18n.get_language_from_request(request)

    args = {"_positional": version, "force": force}
    result = await pipeline_bridge.execute_command("version", "delete", args)

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
