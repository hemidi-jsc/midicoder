"""
Router cho activity log
Dùng shared module storage.activity cho cả read.
"""

from fastapi import APIRouter, Query, Request
from typing import Optional

from midicoder.api.i18n import i18n
from midicoder.api.models import ApiResponse
from midicoder.storage import activity

router = APIRouter(prefix="/activity", tags=["Activity"])


@router.get("/recent", response_model=ApiResponse)
async def get_recent_activity(
    request: Request,
    days: int = Query(3, ge=1),
    version: Optional[str] = Query(None),
):
    """Lấy hoạt động gần đây (mặc định 3 ngày), có thể filter theo version."""
    language = i18n.get_language_from_request(request)
    activities = activity.query_recent(days=days, version=version)
    return ApiResponse(
        success=True,
        data={"activities": activities, "count": len(activities)},
        language=language,
    )


@router.get("/all", response_model=ApiResponse)
async def get_all_activity(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    version: Optional[str] = Query(None),
):
    """Lấy tất cả hoạt động với phân trang, có thể filter theo version."""
    language = i18n.get_language_from_request(request)
    result = activity.query_all(page=page, per_page=per_page, version=version)
    return ApiResponse(
        success=True,
        data=result,
        language=language,
    )
