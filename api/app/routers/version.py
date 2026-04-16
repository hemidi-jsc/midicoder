"""
Router cho các commands về version
"""

from fastapi import APIRouter, Request

from app.cli_wrapper import cli_wrapper
from app.i18n import i18n
from app.models import ApiResponse, VersionCreateRequest

router = APIRouter(prefix="/version", tags=["Version"])


@router.post("/create", response_model=ApiResponse)
async def create_version(request_data: VersionCreateRequest, request: Request):
    """
    Tạo phiên bản mới
    
    Args:
        request_data: Tên phiên bản cần tạo
        request: Request object để lấy ngôn ngữ
    
    Returns:
        ApiResponse: Kết quả tạo phiên bản
    """
    language = i18n.get_language_from_request(request)
    
    # Gọi CLI wrapper để create version
    result = await cli_wrapper.version_create(request_data.version)
    
    if result["success"]:
        return ApiResponse(
            success=True,
            data={
                "version": request_data.version,
                "created": True,
            },
            message=i18n.translate("version.create_success", language),
            language=language,
        )
    
    return ApiResponse(
        success=False,
        data=None,
        message=result.get("stderr", "Unknown error"),
        language=language,
    )