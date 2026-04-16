"""
Router cho các commands về IR (MIR)
"""

from fastapi import APIRouter, Request

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