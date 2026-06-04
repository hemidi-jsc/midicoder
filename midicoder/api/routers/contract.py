"""
Router cho các commands về contract
"""

from fastapi import APIRouter, Query, Request

from midicoder.api.pipeline_bridge import pipeline_bridge
from midicoder.api.i18n import i18n
from midicoder.api.models import ApiResponse

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
    result = await pipeline_bridge.contract_gen()
    
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
    result = await pipeline_bridge.contract_gen_resume()
    
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
    result = await pipeline_bridge.contract_check()
    
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
    result = await pipeline_bridge.contract_feedback()

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
# GET endpoints — đọc từ SQLite ArtifactsManager (lazy import)
# ============================================================================

@router.get("/ir", response_model=ApiResponse)
async def get_contract_ir_endpoint(version: str = Query(None), request: Request = None):
    """Lấy contract IR từ SQLite ArtifactsManager."""
    language = i18n.get_language_from_request(request)
    try:
        from midicoder.storage.sqlite import ArtifactsManager
        mgr = ArtifactsManager()
        mgr.init()
        artifacts = mgr.list_by_type("contract")
        if not artifacts:
            return ApiResponse(success=False, data=None, message="No contracts found", language=language)
        # Build IR dict: category → parsed content
        ir = {}
        for art in artifacts:
            aid = art.get("artifact_id", "")
            if aid.startswith("contract_"):
                category = aid.replace("contract_", "", 1)
                content = art.get("content", "")
                try:
                    import json
                    ir[category] = json.loads(content)
                except (json.JSONDecodeError, TypeError):
                    ir[category] = content
        return ApiResponse(success=True, data=ir, language=language)
    except Exception as e:
        return ApiResponse(success=False, data=None, message=str(e), language=language)


@router.get("/manifest", response_model=ApiResponse)
async def get_contract_manifest_endpoint(version: str = Query(None), request: Request = None):
    """Lấy contract manifest từ SQLite ArtifactsManager."""
    language = i18n.get_language_from_request(request)
    try:
        from midicoder.storage.sqlite import ArtifactsManager
        mgr = ArtifactsManager()
        mgr.init()
        artifacts = mgr.list_by_type("contract")
        if not artifacts:
            return ApiResponse(success=False, data=None, message="Manifest not found", language=language)
        categories = {}
        for art in artifacts:
            aid = art.get("artifact_id", "")
            if aid.startswith("contract_"):
                category = aid.replace("contract_", "", 1)
                categories[category] = {
                    "name": art.get("name", aid),
                    "status": art.get("status", "pending"),
                    "updated_at": art.get("updated_at"),
                }
        return ApiResponse(success=True, data={"total": len(artifacts), "categories": categories}, language=language)
    except Exception as e:
        return ApiResponse(success=False, data=None, message=str(e), language=language)


@router.get("/entities", response_model=ApiResponse)
async def get_contract_entities(version: str = Query(None), request: Request = None):
    """Lấy entities YAML từ SQLite ArtifactsManager."""
    language = i18n.get_language_from_request(request)
    try:
        from midicoder.storage.sqlite import ArtifactsManager
        mgr = ArtifactsManager()
        mgr.init()
        artifact = mgr.get("contract_entities")
        if artifact is None:
            return ApiResponse(success=False, data=None, message="Entities YAML not found", language=language)
        return ApiResponse(success=True, data={"content": artifact.get("content", "")}, language=language)
    except Exception as e:
        return ApiResponse(success=False, data=None, message=str(e), language=language)


@router.get("/contracts", response_model=ApiResponse)
async def get_contract_contracts(version: str = Query(None), request: Request = None):
    """Lấy contracts YAML từ SQLite ArtifactsManager."""
    language = i18n.get_language_from_request(request)
    try:
        from midicoder.storage.sqlite import ArtifactsManager
        mgr = ArtifactsManager()
        mgr.init()
        artifact = mgr.get("contract_commands")
        if artifact is None:
            return ApiResponse(success=False, data=None, message="Contracts YAML not found", language=language)
        return ApiResponse(success=True, data={"content": artifact.get("content", "")}, language=language)
    except Exception as e:
        return ApiResponse(success=False, data=None, message=str(e), language=language)