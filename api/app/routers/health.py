"""
Router cho health check và thông tin hệ thống
"""

from datetime import datetime
from fastapi import APIRouter, Request

from app.config import settings, get_project_cwd, get_global_config_path
from app.i18n import i18n
from app.models import ApiResponse, HealthResponse, LanguagesResponse

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/", response_model=HealthResponse)
async def health_check():
    """
    Kiểm tra trạng thái health của API
    
    Returns:
        HealthResponse: Trạng thái health
    """
    return HealthResponse(
        status="healthy",
        version=settings.api_version,
        timestamp=datetime.utcnow(),
    )


@router.get("/ready", response_model=HealthResponse)
async def ready_check():
    """
    Kiểm tra API đã sẵn sàng chưa
    
    Returns:
        HealthResponse: Trạng thái ready
    """
    return HealthResponse(
        status="ready",
        version=settings.api_version,
        timestamp=datetime.utcnow(),
    )


@router.get("/info", response_model=ApiResponse)
async def get_info(request: Request):
    """
    Lấy thông tin API
    
    Args:
        request: Request object để lấy ngôn ngữ
    
    Returns:
        ApiResponse: Thông tin API
    """
    language = i18n.get_language_from_request(request)
    
    return ApiResponse(
        success=True,
        data={
            "app_name": settings.app_name,
            "api_version": settings.api_version,
            "host": settings.host,
            "port": settings.port,
            "default_language": settings.default_language,
            "supported_languages": settings.supported_languages,
        },
        message=i18n.translate("common.success", language),
        language=language,
    )


@router.get("/languages", response_model=LanguagesResponse)
async def get_languages(request: Request):
    """
    Lấy danh sách ngôn ngữ được hỗ trợ
    
    Returns:
        LanguagesResponse: Danh sách ngôn ngữ
    """
    return LanguagesResponse(
        languages=i18n.get_all_languages(),
        default=settings.default_language,
    )


@router.get("/status", response_model=ApiResponse)
async def get_status(request: Request):
    """
    Lấy trạng thái hệ thống và CWD hiện tại
    
    Returns:
        ApiResponse: Thông tin status và CWD
    """
    language = i18n.get_language_from_request(request)
    
    cwd = get_project_cwd()
    config_path = get_global_config_path()
    
    return ApiResponse(
        success=True,
        data={
            "cwd": cwd,
            "global_config_path": str(config_path),
            "global_config_exists": config_path.exists(),
            "api_ready": True,
        },
        message=i18n.translate("common.success", language),
        language=language,
    )
