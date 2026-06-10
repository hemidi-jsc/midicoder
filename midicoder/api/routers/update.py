"""
Router cho Update — kiểm tra & nâng cấp phiên bản.

Tất cả logic delegate vào update_checker module.
"""

import threading
from fastapi import APIRouter, Request

from midicoder.api.i18n import i18n
from midicoder.api.models import ApiResponse
from midicoder.update_checker import get_checker

router = APIRouter(prefix="/update", tags=["Update"])


@router.get("/status", response_model=ApiResponse)
async def get_update_status(request: Request):
    """Lấy trạng thái update từ cache (không gọi network)."""
    language = i18n.get_language_from_request(request)
    checker = get_checker()
    data = checker.get_cached()

    return ApiResponse(
        success=True,
        data=data,
        message=i18n.translate("common.success", language),
        language=language,
    )


@router.post("/check-now", response_model=ApiResponse)
async def check_update_now(request: Request):
    """Force check GitHub API ngay lập tức."""
    language = i18n.get_language_from_request(request)
    checker = get_checker()

    # Chạy trong thread để không block event loop
    def _do_check():
        return checker.check()

    result = await _run_async(_do_check)

    status_msg = (
        f"Có phiên bản mới: {result.get('latest_version')}"
        if result.get("has_update")
        else "Đã có phiên bản mới nhất"
    )

    return ApiResponse(
        success=True,
        data=result,
        message=status_msg,
        language=language,
    )


@router.post("/upgrade", response_model=ApiResponse)
async def upgrade_to_latest(request: Request):
    """Download & upgrade phiên bản mới — app sẽ tự restart."""
    language = i18n.get_language_from_request(request)
    checker = get_checker()

    cache = checker.get_cached()
    if not cache.get("has_update"):
        return ApiResponse(
            success=False,
            data=None,
            message="Không có phiên bản mới để nâng cấp",
            language=language,
        )

    # Upgrade chạy blocking (shutdown + exit) — nên phải trong thread riêng
    def _do_upgrade():
        checker.upgrade()

    thread = threading.Thread(target=_do_upgrade, daemon=True, name="upgrade-thread")
    thread.start()

    # Trả response ngay cho frontend biết đang upgrade
    return ApiResponse(
        success=True,
        data={"upgrading": True, "target_version": cache.get("latest_version")},
        message="Đang nâng cấp... Ứng dụng sẽ tự khởi động lại",
        language=language,
    )


async def _run_async(fn) -> dict:
    """Chạy blocking function trong thread pool (FastAPI đã có sẵn run_in_threadpool)."""
    from fastapi.concurrency import run_in_threadpool
    return await run_in_threadpool(fn)
