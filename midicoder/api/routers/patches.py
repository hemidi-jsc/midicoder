"""
Router cho patch files
"""

from fastapi import APIRouter, Query, Request

from midicoder.api.artifact import get_patch_content, list_patches
from midicoder.api.i18n import i18n
from midicoder.api.models import ApiResponse

router = APIRouter(prefix="/patches", tags=["Patches"])


@router.get("/", response_model=ApiResponse)
async def list_patch_files(version: str = Query(None), request: Request = None):
    """
    List patch files in version directory.
    Reads .midicoder/versions/{version}/patches/
    """
    language = i18n.get_language_from_request(request)
    files = list_patches(version)
    return ApiResponse(success=True, data={"files": files, "count": len(files)}, language=language)


@router.get("/{patch_name:path}", response_model=ApiResponse)
async def get_patch(patch_name: str, version: str = Query(None), request: Request = None):
    """
    Lấy nội dung một patch file.
    Reads .midicoder/versions/{version}/patches/{patch_name}
    """
    language = i18n.get_language_from_request(request)
    content = get_patch_content(version, patch_name)
    if content is None:
        return ApiResponse(success=False, data=None, message=f"Patch not found: {patch_name}", language=language)
    return ApiResponse(success=True, data={"name": patch_name, "content": content}, language=language)
