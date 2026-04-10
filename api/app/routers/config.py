"""
Router cho các commands về config
"""

from fastapi import APIRouter, Request

from app.cli_wrapper import cli_wrapper
from app.i18n import i18n
from app.models import ApiResponse, ConfigSetRequest

router = APIRouter(prefix="/config", tags=["Config"])


@router.get("/list", response_model=ApiResponse)
async def list_config(request: Request):
    """
    Liệt kê tất cả cấu hình
    
    Args:
        request: Request object để lấy ngôn ngữ
    
    Returns:
        ApiResponse: Danh sách cấu hình
    """
    language = i18n.get_language_from_request(request)
    
    # Gọi CLI wrapper để lấy config
    result = await cli_wrapper.config_list()
    
    if result["success"]:
        # Parse stdout để lấy config dict
        try:
            config_data = result.get("stdout_data") or {}
            return ApiResponse(
                success=True,
                data=config_data,
                message=i18n.translate("config.list_success", language),
                language=language,
            )
        except Exception as e:
            return ApiResponse(
                success=False,
                data=None,
                message=str(e),
                language=language,
            )
    
    return ApiResponse(
        success=False,
        data=None,
        message=result.get("stderr", "Unknown error"),
        language=language,
    )


@router.get("/get/{key}", response_model=ApiResponse)
async def get_config(key: str, request: Request):
    """
    Lấy giá trị của một key config
    
    Args:
        key: Key của config
        request: Request object để lấy ngôn ngữ
    
    Returns:
        ApiResponse: Giá trị config
    """
    language = i18n.get_language_from_request(request)
    
    # Gọi CLI wrapper để lấy config
    result = await cli_wrapper.config_get(key)
    
    if result["success"]:
        # Parse stdout để lấy giá trị
        stdout = result.get("stdout", "").strip()
        return ApiResponse(
            success=True,
            data={"key": key, "value": stdout},
            message=i18n.translate("config.get_success", language),
            language=language,
        )
    
    return ApiResponse(
        success=False,
        data=None,
        message=result.get("stderr", "Unknown error"),
        language=language,
    )


@router.post("/set", response_model=ApiResponse)
async def set_config(config: ConfigSetRequest, request: Request):
    """
    Đặt giá trị cho một key config
    
    Args:
        config: Request chứa key và value
        request: Request object để lấy ngôn ngữ
    
    Returns:
        ApiResponse: Kết quả đặt config
    """
    language = i18n.get_language_from_request(request)
    
    # Gọi CLI wrapper để set config
    result = await cli_wrapper.config_set(config.key, config.value)
    
    if result["success"]:
        return ApiResponse(
            success=True,
            data={"key": config.key, "value": config.value},
            message=i18n.translate("config.set_success", language),
            language=language,
        )
    
    return ApiResponse(
        success=False,
        data=None,
        message=result.get("stderr", "Unknown error"),
        language=language,
    )


@router.post("/validate", response_model=ApiResponse)
async def validate_config(request: Request):
    """
    Validate cấu hình hiện tại
    
    Args:
        request: Request object để lấy ngôn ngữ
    
    Returns:
        ApiResponse: Kết quả validate
    """
    language = i18n.get_language_from_request(request)
    
    # Gọi CLI wrapper để validate config
    result = await cli_wrapper.config_validate()
    
    if result["success"]:
        return ApiResponse(
            success=True,
            data=None,
            message=i18n.translate("config.validate_success", language),
            language=language,
        )
    
    return ApiResponse(
        success=False,
        data=None,
        message=result.get("stderr", "Unknown error"),
        language=language,
    )


@router.post("/reset", response_model=ApiResponse)
async def reset_config(request: Request):
    """
    Reset cấu hình về mặc định
    
    Args:
        request: Request object để lấy ngôn ngữ
    
    Returns:
        ApiResponse: Kết quả reset
    """
    language = i18n.get_language_from_request(request)
    
    # Gọi CLI wrapper để reset config
    result = await cli_wrapper.config_reset()
    
    if result["success"]:
        return ApiResponse(
            success=True,
            data=None,
            message=i18n.translate("config.reset_success", language),
            language=language,
        )
    
    return ApiResponse(
        success=False,
        data=None,
        message=result.get("stderr", "Unknown error"),
        language=language,
    )