"""
Router cho các commands về index
"""

from fastapi import APIRouter, Request

from app.cli_wrapper import cli_wrapper
from app.i18n import i18n
from app.models import ApiResponse, IndexReindexRequest

router = APIRouter(prefix="/index", tags=["Index"])


@router.post("/", response_model=ApiResponse)
async def build_index(request: Request):
    """
    Build index từ codebase
    
    Args:
        request: Request object để lấy ngôn ngữ
    
    Returns:
        ApiResponse: Kết quả build index
    """
    language = i18n.get_language_from_request(request)
    
    # Gọi CLI wrapper để build index
    result = await cli_wrapper.index_build()
    
    if result["success"]:
        return ApiResponse(
            success=True,
            data={"indexed": True},
            message=i18n.translate("common.success", language),
            language=language,
        )
    
    return ApiResponse(
        success=False,
        data=None,
        message=result.get("stderr", "Unknown error"),
        language=language,
    )


@router.post("/reindex", response_model=ApiResponse)
async def reindex(request_data: IndexReindexRequest = None, request: Request = None):
    """
    Reindex các file đã thay đổi
    
    Args:
        request_data: Danh sách file paths đã thay đổi
        request: Request object để lấy ngôn ngữ
    
    Returns:
        ApiResponse: Kết quả reindex
    """
    if request_data is None:
        request_data = IndexReindexRequest()
    
    language = i18n.get_language_from_request(request) if request else "vi"
    
    # Gọi CLI wrapper để reindex
    result = await cli_wrapper.index_reindex(request_data.paths if request_data.paths else None)
    
    if result["success"]:
        return ApiResponse(
            success=True,
            data={"indexed": True, "files_count": len(request_data.paths) if request_data.paths else 0},
            message=i18n.translate("common.success", language),
            language=language,
        )
    
    return ApiResponse(
        success=False,
        data=None,
        message=result.get("stderr", "Unknown error"),
        language=language,
    )