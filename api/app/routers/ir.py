"""
Router cho các commands về IR (MIR)
"""

from fastapi import APIRouter, Query, Request

from app.cli_wrapper import cli_wrapper
from app.i18n import i18n
from app.models import ApiResponse, IRBuildRequest

router = APIRouter(prefix="/ir", tags=["IR"])


@router.post("/build", response_model=ApiResponse)
async def build_ir(request_data: IRBuildRequest = None, request: Request = None):
    """
    Build IR (MIR) từ contracts

    Args:
        request_data: Tham số build IR
        request: Request object để lấy ngôn ngữ

    Returns:
        ApiResponse: Kết quả build IR
    """
    if request_data is None:
        request_data = IRBuildRequest()

    language = i18n.get_language_from_request(request) if request else "vi"

    # Gọi CLI wrapper để build IR
    result = await cli_wrapper.ir_build(skip_diagrams=request_data.skip_diagrams)

    if result["success"]:
        return ApiResponse(
            success=True,
            data={
                "built": True,
                "mir_path": ".midicoder/versions/<version>/ir/mir.json",
                "symbol_table_path": ".midicoder/versions/<version>/ir/symbol-table.json",
            },
            message=i18n.translate("ir.build_success", language),
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

@router.get("/mir", response_model=ApiResponse)
async def get_mir(version: str = Query(None), request: Request = None):
    """Lấy MIR JSON từ SQLite ArtifactsManager."""
    language = i18n.get_language_from_request(request)
    try:
        import json
        from midicoder.storage.sqlite import ArtifactsManager
        mgr = ArtifactsManager()
        mgr.init()
        artifacts = mgr.list_by_type("mir")
        if not artifacts:
            return ApiResponse(success=False, data=None, message="MIR not found", language=language)
        content = artifacts[0].get("content", "")
        try:
            data = json.loads(content)
        except (json.JSONDecodeError, TypeError):
            data = {"raw": content}
        return ApiResponse(success=True, data=data, language=language)
    except Exception as e:
        return ApiResponse(success=False, data=None, message=str(e), language=language)


@router.get("/symbol-table", response_model=ApiResponse)
async def get_symbol_table_endpoint(version: str = Query(None), request: Request = None):
    """Lấy symbol table từ metadata của MIR artifact."""
    language = i18n.get_language_from_request(request)
    try:
        import json
        from midicoder.storage.sqlite import ArtifactsManager
        mgr = ArtifactsManager()
        mgr.init()
        artifacts = mgr.list_by_type("mir")
        if not artifacts:
            return ApiResponse(success=False, data=None, message="Symbol table not found", language=language)
        metadata = artifacts[0].get("metadata", {})
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except json.JSONDecodeError:
                metadata = {}
        if isinstance(metadata, dict):
            data = metadata.get("symbol_table") or metadata
        else:
            data = None
        if data is None:
            return ApiResponse(success=False, data=None, message="Symbol table not found", language=language)
        return ApiResponse(success=True, data=data, language=language)
    except Exception as e:
        return ApiResponse(success=False, data=None, message=str(e), language=language)


@router.get("/dependency-graph", response_model=ApiResponse)
async def get_dependency_graph_endpoint(version: str = Query(None), request: Request = None):
    """Lấy dependency graph từ MIR artifact."""
    language = i18n.get_language_from_request(request)
    try:
        import json
        from midicoder.storage.sqlite import ArtifactsManager
        mgr = ArtifactsManager()
        mgr.init()
        artifacts = mgr.list_by_type("mir")
        if not artifacts:
            return ApiResponse(success=False, data=None, message="Dependency graph not found", language=language)
        content = artifacts[0].get("content", "")
        try:
            mir_data = json.loads(content)
        except (json.JSONDecodeError, TypeError):
            return ApiResponse(success=False, data=None, message="Dependency graph not found", language=language)
        data = {
            "operations": mir_data.get("operations", []),
            "data_flows": mir_data.get("data_flows", []),
            "effect_flows": mir_data.get("effect_flows", []),
        }
        return ApiResponse(success=True, data=data, language=language)
    except Exception as e:
        return ApiResponse(success=False, data=None, message=str(e), language=language)


@router.get("/entity-relationship", response_model=ApiResponse)
async def get_entity_relationship_endpoint(version: str = Query(None), request: Request = None):
    """Lấy entity-relationship graph từ MIR metadata."""
    language = i18n.get_language_from_request(request)
    try:
        import json
        from midicoder.storage.sqlite import ArtifactsManager
        mgr = ArtifactsManager()
        mgr.init()
        artifacts = mgr.list_by_type("mir")
        if not artifacts:
            return ApiResponse(success=False, data=None, message="Entity relationship graph not found", language=language)
        metadata = artifacts[0].get("metadata", {})
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except json.JSONDecodeError:
                metadata = {}
        if isinstance(metadata, dict):
            content = metadata.get("entity_relationship_graph")
        else:
            content = None
        if content is None:
            return ApiResponse(success=False, data=None, message="Entity relationship graph not found", language=language)
        return ApiResponse(success=True, data={"content": content}, language=language)
    except Exception as e:
        return ApiResponse(success=False, data=None, message=str(e), language=language)