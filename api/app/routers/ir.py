"""
Router cho các commands về IR (MIR)
"""

from fastapi import APIRouter, Query, Request

from app.artifact import (
    get_ir_dependency_graph,
    get_ir_entity_relationship,
    get_ir_mir,
    get_ir_symbol_table,
)
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
# GET endpoints — đọc artifact files từ disk
# ============================================================================

@router.get("/mir", response_model=ApiResponse)
async def get_mir(version: str = Query(None), request: Request = None):
    """
    Lấy MIR JSON từ disk.
    Reads .midicoder/versions/{version}/ir/mir.json
    """
    language = i18n.get_language_from_request(request)
    data = get_ir_mir(version)
    if data is None:
        return ApiResponse(success=False, data=None, message="MIR not found", language=language)
    return ApiResponse(success=True, data=data, language=language)


@router.get("/symbol-table", response_model=ApiResponse)
async def get_symbol_table(version: str = Query(None), request: Request = None):
    """
    Lấy symbol table JSON từ disk.
    Reads .midicoder/versions/{version}/ir/symbol-table.json
    """
    language = i18n.get_language_from_request(request)
    data = get_ir_symbol_table(version)
    if data is None:
        return ApiResponse(success=False, data=None, message="Symbol table not found", language=language)
    return ApiResponse(success=True, data=data, language=language)


@router.get("/dependency-graph", response_model=ApiResponse)
async def get_dependency_graph(version: str = Query(None), request: Request = None):
    """
    Lấy dependency graph JSON từ disk.
    Reads .midicoder/versions/{version}/ir/dependency-graph.json
    """
    language = i18n.get_language_from_request(request)
    data = get_ir_dependency_graph(version)
    if data is None:
        return ApiResponse(success=False, data=None, message="Dependency graph not found", language=language)
    return ApiResponse(success=True, data=data, language=language)


@router.get("/entity-relationship", response_model=ApiResponse)
async def get_entity_relationship(version: str = Query(None), request: Request = None):
    """
    Lấy entity-relationship GraphML từ disk.
    Reads .midicoder/versions/{version}/ir/entity-relationship.graphml
    """
    language = i18n.get_language_from_request(request)
    content = get_ir_entity_relationship(version)
    if content is None:
        return ApiResponse(success=False, data=None, message="Entity relationship graph not found", language=language)
    return ApiResponse(success=True, data={"content": content}, language=language)