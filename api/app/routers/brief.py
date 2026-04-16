"""
Router cho các commands về brief
"""

from fastapi import APIRouter, Request

from app.cli_wrapper import cli_wrapper
from app.i18n import i18n
from app.models import ApiResponse

router = APIRouter(prefix="/brief", tags=["Brief"])


@router.post("/analyze", response_model=ApiResponse)
async def analyze_brief(request: Request):
    """
    Phân tích brief
    
    Args:
        request: Request object để lấy ngôn ngữ
    
    Returns:
        ApiResponse: Kết quả phân tích brief
    """
    language = i18n.get_language_from_request(request)
    
    # Gọi CLI wrapper để analyze brief
    result = await cli_wrapper.brief_analyze()
    
    if result["success"]:
        # Parse stdout_data nếu có
        data = result.get("stdout_data") or {}
        return ApiResponse(
            success=True,
            data=data,
            message=i18n.translate("brief.analyze_success", language),
            language=language,
        )
    
    return ApiResponse(
        success=False,
        data=None,
        message=result.get("stderr", "Unknown error"),
        language=language,
    )


@router.post("/rewrite", response_model=ApiResponse)
async def rewrite_brief(request: Request):
    """
    Viết lại brief
    
    Args:
        request: Request object để lấy ngôn ngữ
    
    Returns:
        ApiResponse: Kết quả viết lại brief
    """
    language = i18n.get_language_from_request(request)
    
    # Gọi CLI wrapper để rewrite brief
    result = await cli_wrapper.brief_rewrite()
    
    if result["success"]:
        return ApiResponse(
            success=True,
            data={"rewritten": True},
            message=i18n.translate("brief.rewrite_success", language),
            language=language,
        )
    
    return ApiResponse(
        success=False,
        data=None,
        message=result.get("stderr", "Unknown error"),
        language=language,
    )