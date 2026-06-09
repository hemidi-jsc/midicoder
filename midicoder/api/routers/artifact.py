"""
Artifact Stats Router — thống kê chi tiết các artifacts của version active.

Delegate tất cả logic vào pipeline/commands/artifact_stats.py qua pipeline_bridge.
"""

from fastapi import APIRouter, Request

from midicoder.api.i18n import i18n
from midicoder.api.models import ApiResponse
from midicoder.api.pipeline_bridge import pipeline_bridge

router = APIRouter(prefix="/artifacts", tags=["Artifacts"])


@router.get("/stats", response_model=ApiResponse)
async def get_artifact_stats(request: Request = None):
    """Lấy thông tin chi tiết của tất cả artifacts cho version active."""
    language = i18n.get_language_from_request(request)

    result = await pipeline_bridge.execute_command("artifact", "stats")

    if result["success"]:
        data = result.get("_data", {})
        return ApiResponse(
            success=True,
            data=data,
            message="Lấy thông tin artifacts thành công",
            language=language,
        )
    else:
        return ApiResponse(
            success=False,
            data=None,
            message=result.get("stderr", "Lỗi khi lấy thông tin artifacts"),
            language=language,
        )
