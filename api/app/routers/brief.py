"""
Router cho các commands về brief
"""

from pathlib import Path
from pydantic import BaseModel, Field

from fastapi import APIRouter, Query, Request

from app.artifact import get_brief_master, get_brief_raw, get_brief_working
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


def _write_brief_file(version: str, content: str) -> bool:
    """
    Write brief content to version directory.
    CLI commands đọc từ .midicoder/versions/{version}/brief.md
    """
    try:
        from app.config import get_project_cwd
        project_cwd = Path(get_project_cwd())
        brief_dir = project_cwd / ".midicoder" / "versions" / version
        brief_dir.mkdir(parents=True, exist_ok=True)
        brief_file = brief_dir / "brief.md"
        brief_file.write_text(content, encoding="utf-8")
        return True
    except Exception as e:
        print(f"Error writing brief file: {e}")
        return False


@router.post("/analyze", response_model=ApiResponse)
async def analyze_brief(request_data: BriefAnalyzeRequest = None, request: Request = None):
    """
    Phân tích brief

    Args:
        request_data: Request chứa brief_content và version
        request: Request object để lấy ngôn ngữ

    Returns:
        ApiResponse: Kết quả phân tích brief
    """
    if request_data is None:
        request_data = BriefAnalyzeRequest(brief_content="")

    language = i18n.get_language_from_request(request)

    # Write brief content to file trước khi analyze
    if request_data.brief_content.strip():
        _write_brief_file(request_data.version, request_data.brief_content)

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
    """
    Lưu brief

    Args:
        request_data: Request chứa name, tags, version, brief_content
        request: Request object để lấy ngôn ngữ

    Returns:
        ApiResponse: Kết quả lưu brief
    """
    if request_data is None:
        request_data = BriefSaveRequest(name="default")

    language = i18n.get_language_from_request(request)

    # Write brief to file nếu có content
    if request_data.brief_content.strip():
        _write_brief_file(request_data.version, request_data.brief_content)

    return ApiResponse(
        success=True,
        data={"saved_path": f".midicoder/versions/{request_data.version}/briefs/{request_data.name}.md"},
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


# ============================================================================
# GET endpoints — đọc artifact files từ disk
# ============================================================================

@router.get("/master", response_model=ApiResponse)
async def get_master_brief(version: str = Query(None), request: Request = None):
    """
    Lấy master brief markdown từ disk.
    Reads .midicoder/versions/{version}/briefs/master-brief.md
    """
    language = i18n.get_language_from_request(request)
    content = get_brief_master(version)
    if content is None:
        return ApiResponse(success=False, data=None, message="Master brief not found", language=language)
    return ApiResponse(success=True, data={"content": content}, language=language)


@router.get("/working", response_model=ApiResponse)
async def get_working_brief(version: str = Query(None), request: Request = None):
    """
    Lấy working brief markdown từ disk.
    Reads .midicoder/versions/{version}/briefs/working-brief.md
    """
    language = i18n.get_language_from_request(request)
    content = get_brief_working(version)
    if content is None:
        return ApiResponse(success=False, data=None, message="Working brief not found", language=language)
    return ApiResponse(success=True, data={"content": content}, language=language)


@router.get("/raw", response_model=ApiResponse)
async def get_raw_brief(version: str = Query(None), request: Request = None):
    """
    Lấy brief.md gốc từ disk (file CLI đọc).
    Reads .midicoder/versions/{version}/brief.md
    """
    language = i18n.get_language_from_request(request)
    content = get_brief_raw(version)
    if content is None:
        return ApiResponse(success=False, data=None, message="Brief not found", language=language)
    return ApiResponse(success=True, data={"content": content}, language=language)