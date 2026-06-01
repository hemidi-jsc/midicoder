"""
Router cho các commands về code
"""

from fastapi import APIRouter, Query, Request

from app.artifact import (
    get_generated_code_files,
    get_generated_file_content,
    get_plan_lowering,
)
from app.cli_wrapper import cli_wrapper
from app.i18n import i18n
from app.models import ApiResponse, CodeGenRequest, CodeApplyRequest

router = APIRouter(prefix="/code", tags=["Code"])


@router.post("/build", response_model=ApiResponse)
async def build_code_plan(request: Request):
    """
    Build code plan từ IR
    
    Args:
        request: Request object để lấy ngôn ngữ
    
    Returns:
        ApiResponse: Kết quả build code plan
    """
    language = i18n.get_language_from_request(request)
    
    # Gọi CLI wrapper để build code plan
    result = await cli_wrapper.code_build()
    
    if result["success"]:
        return ApiResponse(
            success=True,
            data={
                "built": True,
                "plan_path": ".midicoder/versions/<version>/plan/lowering.json",
            },
            message=i18n.translate("code.build_success", language),
            language=language,
        )
    
    return ApiResponse(
        success=False,
        data=None,
        message=result.get("stderr", "Unknown error"),
        language=language,
    )


@router.post("/plan", response_model=ApiResponse)
async def plan_code(request: Request):
    """
    Plan code (alias của build)
    
    Args:
        request: Request object để lấy ngôn ngữ
    
    Returns:
        ApiResponse: Kết quả plan code
    """
    language = i18n.get_language_from_request(request)
    
    # Gọi CLI wrapper để plan code
    result = await cli_wrapper.code_plan()
    
    if result["success"]:
        return ApiResponse(
            success=True,
            data={
                "planned": True,
                "plan_path": ".midicoder/versions/<version>/plan/lowering.json",
            },
            message=i18n.translate("code.build_success", language),
            language=language,
        )
    
    return ApiResponse(
        success=False,
        data=None,
        message=result.get("stderr", "Unknown error"),
        language=language,
    )


@router.post("/gen", response_model=ApiResponse)
async def generate_code(request_data: CodeGenRequest = None, request: Request = None):
    """
    Generate code từ plan
    
    Args:
        request_data: Tham số generate code
        request: Request object để lấy ngôn ngữ
    
    Returns:
        ApiResponse: Kết quả generate code
    """
    if request_data is None:
        request_data = CodeGenRequest()
    
    language = i18n.get_language_from_request(request) if request else "vi"
    
    # Gọi CLI wrapper để generate code
    result = await cli_wrapper.code_gen(runtime=request_data.runtime)
    
    if result["success"]:
        return ApiResponse(
            success=True,
            data={
                "generated": True,
                "generated_path": ".midicoder/versions/<version>/code/generated",
                "report_path": ".midicoder/versions/<version>/code/report.json",
            },
            message=i18n.translate("code.gen_success", language),
            language=language,
        )
    
    return ApiResponse(
        success=False,
        data=None,
        message=result.get("stderr", "Unknown error"),
        language=language,
    )


@router.post("/apply", response_model=ApiResponse)
async def apply_code(request_data: CodeApplyRequest = None, request: Request = None):
    """
    Apply code vào working directory
    
    Args:
        request_data: Tham số apply code
        request: Request object để lấy ngôn ngữ
    
    Returns:
        ApiResponse: Kết quả apply code
    """
    if request_data is None:
        request_data = CodeApplyRequest()
    
    language = i18n.get_language_from_request(request) if request else "vi"

    # Gọi CLI wrapper để apply code
    result = await cli_wrapper.code_apply(
        force=request_data.force,
        dry_run=request_data.dry_run,
        no_reindex=request_data.no_reindex,
        patches_subdir=request_data.patches_subdir,
    )

    if result["success"]:
        return ApiResponse(
            success=True,
            data={
                "applied": True,
                "status_path": ".midicoder/versions/<version>/code/applied/status.json",
            },
            message=i18n.translate("code.apply_success", language),
            language=language,
        )

    return ApiResponse(
        success=False,
        data=None,
        message=result.get("stderr", "Unknown error"),
        language=language,
    )


# ============================================================================
# GET endpoints — đọc artifact files từ disk
# ============================================================================

@router.get("/files", response_model=ApiResponse)
async def list_code_files(version: str = Query(None), request: Request = None):
    """
    List generated code files.
    Reads .midicoder/versions/{version}/code/generated/
    """
    language = i18n.get_language_from_request(request)
    files = get_generated_code_files(version)
    return ApiResponse(success=True, data={"files": files, "count": len(files)}, language=language)


@router.get("/file/{file_path:path}", response_model=ApiResponse)
async def get_code_file(file_path: str, version: str = Query(None), request: Request = None):
    """
    Lấy nội dung file code đã generate.
    Reads .midicoder/versions/{version}/code/generated/{file_path}
    """
    language = i18n.get_language_from_request(request)
    content = get_generated_file_content(version, file_path)
    if content is None:
        return ApiResponse(success=False, data=None, message=f"File not found: {file_path}", language=language)
    return ApiResponse(success=True, data={"path": file_path, "content": content}, language=language)


@router.get("/plan", response_model=ApiResponse)
async def get_code_plan(version: str = Query(None), request: Request = None):
    """
    Lấy lowering plan JSON.
    Reads .midicoder/versions/{version}/plan/lowering.json
    """
    language = i18n.get_language_from_request(request)
    data = get_plan_lowering(version)
    if data is None:
        return ApiResponse(success=False, data=None, message="Code plan not found", language=language)
    return ApiResponse(success=True, data=data, language=language)