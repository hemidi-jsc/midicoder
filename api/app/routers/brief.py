"""
Router cho các commands về brief
"""

from pydantic import BaseModel, Field

from fastapi import APIRouter, Query, Request

from app.cli_wrapper import cli_wrapper
from app.i18n import i18n
from app.models import ApiResponse

router = APIRouter(prefix="/brief", tags=["Brief"])


class BriefAnalyzeRequest(BaseModel):
    brief_content: str = Field(..., description="Nội dung brief")
    version: str = Field(default="v1.0.0", description="Version name")


class BriefSaveRequest(BaseModel):
    name: str = Field(..., description="Tên brief")
    tags: list[str] = Field(default=[], description="Tags")
    version: str = Field(default="v1.0.0", description="Version name")
    brief_content: str = Field(default="", description="Nội dung brief (optional)")


@router.post("/analyze", response_model=ApiResponse)
async def analyze_brief(request_data: BriefAnalyzeRequest = None, request: Request = None):
    """Phân tích brief"""
    if request_data is None:
        request_data = BriefAnalyzeRequest(brief_content="")

    language = i18n.get_language_from_request(request)

    # Lưu brief vào SQLite trước khi analyze
    if request_data.brief_content.strip():
        from midicoder.storage.sqlite import BriefsManager
        mgr = BriefsManager()
        mgr.init()
        try:
            mgr.create(
                brief_id=request_data.version,
                version=request_data.version,
                content=request_data.brief_content,
                title=f"Working brief {request_data.version}",
                brief_type="working",
            )
        except Exception:
            pass  # Brief có thể đã tồn tại (UNIQUE constraint)

    # Gọi CLI wrapper để analyze brief
    result = await cli_wrapper.brief_analyze()

    if result["success"]:
        data = result.get("stdout_data") or {}
        return ApiResponse(
            success=True,
            data=data,
            message=i18n.translate("brief.analyze_success", language),
            language=language,
        )

    return ApiResponse(
        success=False,
        data=None,
        message=result.get("stderr", result.get("stdout", "Unknown error")),
        language=language,
    )


@router.post("/save", response_model=ApiResponse)
async def save_brief(request_data: BriefSaveRequest = None, request: Request = None):
    """Lưu brief vào SQLite BriefsManager"""
    if request_data is None:
        request_data = BriefSaveRequest(name="default")

    language = i18n.get_language_from_request(request)

    # Lưu brief vào SQLite nếu có content
    if request_data.brief_content.strip():
        from midicoder.storage.sqlite import BriefsManager
        mgr = BriefsManager()
        mgr.init()
        try:
            brief_record = mgr.create(
                brief_id=request_data.name,
                version=request_data.version,
                content=request_data.brief_content,
                title=request_data.name,
                brief_type="working",
            )
            return ApiResponse(
                success=True,
                data={"saved": True, "brief_id": request_data.name, "id": brief_record.get("id")},
                message="Brief saved successfully",
                language=language,
            )
        except Exception as e:
            return ApiResponse(
                success=False,
                data=None,
                message=f"Failed to save brief: {str(e)}",
                language=language,
            )

    return ApiResponse(
        success=True,
        data={"saved": True, "brief_id": request_data.name},
        message="Brief saved successfully",
        language=language,
    )


@router.post("/rewrite", response_model=ApiResponse)
async def rewrite_brief(request: Request):
    """
    Viết lại brief
    
    Args:
        request: Request object để lấy ngôn ngữ
    
    Returns:
        ApiResponse: Kết quả viết lại brief
    """
    language = i18n.get_language_from_request(request)
    
    # Gọi CLI wrapper để rewrite brief
    result = await cli_wrapper.brief_rewrite()
    
    if result["success"]:
        return ApiResponse(
            success=True,
            data={"rewritten": True},
            message=i18n.translate("brief.rewrite_success", language),
            language=language,
        )
    
    return ApiResponse(
        success=False,
        data=None,
        message=result.get("stderr", "Unknown error"),
        language=language,
    )


@router.get("/master", response_model=ApiResponse)
async def get_master_brief(version: str = Query(None), request: Request = None):
    """Lấy master brief markdown từ SQLite BriefsManager."""
    language = i18n.get_language_from_request(request)
    try:
        from midicoder.storage.sqlite import BriefsManager
        mgr = BriefsManager()
        mgr.init()
        briefs = mgr.list(version=version)
        for brief in briefs:
            if brief.get("type") == "master":
                content = brief.get("content")
                if content:
                    return ApiResponse(success=True, data={"content": content}, language=language)
        # Fallback: lấy brief mới nhất
        if briefs:
            content = briefs[0].get("content")
            if content:
                return ApiResponse(success=True, data={"content": content}, language=language)
        return ApiResponse(success=False, data=None, message="Master brief not found", language=language)
    except Exception as e:
        return ApiResponse(success=False, data=None, message=str(e), language=language)


@router.get("/working", response_model=ApiResponse)
async def get_working_brief(version: str = Query(None), request: Request = None):
    """Lấy working brief markdown từ SQLite BriefsManager."""
    language = i18n.get_language_from_request(request)
    try:
        from midicoder.storage.sqlite import BriefsManager
        mgr = BriefsManager()
        mgr.init()
        briefs = mgr.list(version=version)
        for brief in briefs:
            if brief.get("type") == "working":
                content = brief.get("content")
                if content:
                    return ApiResponse(success=True, data={"content": content}, language=language)
        # Fallback: lấy brief mới nhất
        if briefs:
            content = briefs[0].get("content")
            if content:
                return ApiResponse(success=True, data={"content": content}, language=language)
        return ApiResponse(success=False, data=None, message="Working brief not found", language=language)
    except Exception as e:
        return ApiResponse(success=False, data=None, message=str(e), language=language)


@router.get("/raw", response_model=ApiResponse)
async def get_raw_brief(version: str = Query(None), request: Request = None):
    """Lấy brief mới nhất từ SQLite BriefsManager (bất kể type)."""
    language = i18n.get_language_from_request(request)
    try:
        from midicoder.storage.sqlite import BriefsManager
        mgr = BriefsManager()
        mgr.init()
        briefs = mgr.list(version=version)
        if not briefs:
            return ApiResponse(success=False, data=None, message="Brief not found", language=language)
        return ApiResponse(success=True, data={"content": briefs[0].get("content", "")}, language=language)
    except Exception as e:
        return ApiResponse(success=False, data=None, message=str(e), language=language)