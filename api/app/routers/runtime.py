"""
Router cho các commands về runtime
"""

from fastapi import APIRouter, Request

from app.cli_wrapper import cli_wrapper
from app.i18n import i18n
from app.models import ApiResponse, RuntimeTestRequest, RuntimeFixRequest

router = APIRouter(prefix="/runtime", tags=["Runtime"])


@router.post("/test", response_model=ApiResponse)
async def test_runtime(request_data: RuntimeTestRequest = None, request: Request = None):
    """
    Test runtime của generated code
    
    Args:
        request_data: Tham số test runtime
        request: Request object để lấy ngôn ngữ
    
    Returns:
        ApiResponse: Kết quả test runtime
    """
    if request_data is None:
        request_data = RuntimeTestRequest()
    
    language = i18n.get_language_from_request(request) if request else "vi"
    
    # Gọi CLI wrapper để test runtime
    result = await cli_wrapper.runtime_test(
        timeout=request_data.timeout,
        port=request_data.port,
        verbose=request_data.verbose,
    )
    
    if result["success"]:
        return ApiResponse(
            success=True,
            data={
                "passed": True,
                "logs": result.get("stdout", ""),
            },
            message=i18n.translate("runtime.test_success", language),
            language=language,
        )
    
    return ApiResponse(
        success=False,
        data={
            "passed": False,
            "logs": result.get("stderr", ""),
        },
        message=result.get("stderr", i18n.translate("runtime.test_failed", language)),
        language=language,
    )


@router.post("/fix", response_model=ApiResponse)
async def fix_runtime(request_data: RuntimeFixRequest = None, request: Request = None):
    """
    Fix runtime errors sử dụng LLM
    
    Args:
        request_data: Tham số fix runtime
        request: Request object để lấy ngôn ngữ
    
    Returns:
        ApiResponse: Kết quả fix runtime
    """
    if request_data is None:
        request_data = RuntimeFixRequest()
    
    language = i18n.get_language_from_request(request) if request else "vi"
    
    # Gọi CLI wrapper để fix runtime
    result = await cli_wrapper.runtime_fix(
        log_timestamp=request_data.log_timestamp,
        dry_run=request_data.dry_run,
        auto_apply=request_data.auto_apply,
        auto_fix_loop=request_data.auto_fix_loop,
        test_timeout=request_data.test_timeout,
        test_port=request_data.test_port,
    )
    
    if result["success"]:
        return ApiResponse(
            success=True,
            data={
                "fixed": True,
                "applied": request_data.auto_apply,
            },
            message=i18n.translate("runtime.fix_success", language),
            language=language,
        )
    
    return ApiResponse(
        success=False,
        data=None,
        message=result.get("stderr", "Unknown error"),
        language=language,
    )