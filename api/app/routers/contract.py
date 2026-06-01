"""
Router cho các commands về contract
"""

from fastapi import APIRouter, Query, Request

from app.artifact import (
    get_contracts_contracts_yaml,
    get_contracts_entities_yaml,
    get_contracts_ir,
    get_contracts_manifest,
)
from app.cli_wrapper import cli_wrapper
from app.i18n import i18n
from app.models import ApiResponse

router = APIRouter(prefix="/contract", tags=["Contract"])


@router.post("/gen", response_model=ApiResponse)
async def generate_contract(request: Request):
    """
    Generate DSL contract từ brief
    
    Args:
        request: Request object để lấy ngôn ngữ
    
    Returns:
        ApiResponse: Kết quả generate contract
    """
    language = i18n.get_language_from_request(request)
    
    # Gọi CLI wrapper để generate contract
    result = await cli_wrapper.contract_gen()
    
    if result["success"]:
        return ApiResponse(
            success=True,
            data={"generated": True},
            message=i18n.translate("contract.gen_success", language),
            language=language,
        )
    
    return ApiResponse(
        success=False,
        data=None,
        message=result.get("stderr", "Unknown error"),
        language=language,
    )


@router.post("/gen/resume", response_model=ApiResponse)
async def resume_contract_gen(request: Request):
    """
    Tiếp tục generate contract (resume)
    
    Args:
        request: Request object để lấy ngôn ngữ
    
    Returns:
        ApiResponse: Kết quả resume contract generation
    """
    language = i18n.get_language_from_request(request)
    
    # Gọi CLI wrapper để resume contract gen
    result = await cli_wrapper.contract_gen_resume()
    
    if result["success"]:
        return ApiResponse(
            success=True,
            data={"resumed": True},
            message=i18n.translate("contract.gen_success", language),
            language=language,
        )
    
    return ApiResponse(
        success=False,
        data=None,
        message=result.get("stderr", "Unknown error"),
        language=language,
    )


@router.post("/check", response_model=ApiResponse)
async def check_contract(request: Request):
    """
    Kiểm tra contract
    
    Args:
        request: Request object để lấy ngôn ngữ
    
    Returns:
        ApiResponse: Kết quả kiểm tra contract
    """
    language = i18n.get_language_from_request(request)
    
    # Gọi CLI wrapper để check contract
    result = await cli_wrapper.contract_check()
    
    if result["success"]:
        return ApiResponse(
            success=True,
            data={"valid": True},
            message=i18n.translate("contract.check_success", language),
            language=language,
        )
    
    return ApiResponse(
        success=False,
        data=None,
        message=result.get("stderr", "Unknown error"),
        language=language,
    )


@router.post("/feedback", response_model=ApiResponse)
async def contract_feedback(request: Request):
    """
    Feedback cho contract

    Args:
        request: Request object để lấy ngôn ngữ

    Returns:
        ApiResponse: Kết quả feedback
    """
    language = i18n.get_language_from_request(request)

    # Gọi CLI wrapper để contract feedback
    result = await cli_wrapper.contract_feedback()

    if result["success"]:
        return ApiResponse(
            success=True,
            data={"processed": True},
            message=i18n.translate("common.success", language),
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

@router.get("/ir", response_model=ApiResponse)
async def get_contract_ir(version: str = Query(None), request: Request = None):
    """
    Lấy contract IR JSON từ disk.

    Reads .midicoder/versions/{version}/contracts/ir.json
    """
    language = i18n.get_language_from_request(request)
    data = get_contracts_ir(version)
    if data is None:
        return ApiResponse(
            success=False,
            data=None,
            message=i18n.translate("contract.ir_not_found", language) or "IR contract not found",
            language=language,
        )
    return ApiResponse(success=True, data=data, language=language)


@router.get("/manifest", response_model=ApiResponse)
async def get_contract_manifest(version: str = Query(None), request: Request = None):
    """
    Lấy contract manifest JSON từ disk.
    """
    language = i18n.get_language_from_request(request)
    data = get_contracts_manifest(version)
    if data is None:
        return ApiResponse(
            success=False,
            data=None,
            message="Manifest not found",
            language=language,
        )
    return ApiResponse(success=True, data=data, language=language)


@router.get("/entities", response_model=ApiResponse)
async def get_contract_entities(version: str = Query(None), request: Request = None):
    """
    Lấy entities.yaml từ disk.
    """
    language = i18n.get_language_from_request(request)
    content = get_contracts_entities_yaml(version)
    if content is None:
        return ApiResponse(
            success=False,
            data=None,
            message="Entities YAML not found",
            language=language,
        )
    return ApiResponse(success=True, data={"content": content}, language=language)


@router.get("/contracts", response_model=ApiResponse)
async def get_contract_contracts(version: str = Query(None), request: Request = None):
    """
    Lấy contracts.yaml từ disk.
    """
    language = i18n.get_language_from_request(request)
    content = get_contracts_contracts_yaml(version)
    if content is None:
        return ApiResponse(
            success=False,
            data=None,
            message="Contracts YAML not found",
            language=language,
        )
    return ApiResponse(success=True, data={"content": content}, language=language)