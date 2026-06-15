"""
Router cho brief — thin wrapper, tất cả logic delegate qua pipeline_bridge.

Kiến trúc:
- Router chỉ: parse request → resolve language → gọi pipeline_bridge → wrap ApiResponse
- Không có business logic, không init Manager trực tiếp
- Pipeline commands nằm ở: midicoder/pipeline/commands/brief.py
"""

import json
from typing import Optional

from pydantic import BaseModel, Field
from fastapi import APIRouter, Query, Request
from starlette.responses import StreamingResponse

from midicoder.api.i18n import i18n
from midicoder.api.models import ApiResponse
from midicoder.api.pipeline_bridge import pipeline_bridge
from midicoder.api.config import get_project_cwd

router = APIRouter(prefix="/brief", tags=["Brief"])


# ============================================================================
# Request models
# ============================================================================

class BriefAnalyzeRequest(BaseModel):
    version: str = Field(default="v1.0.0", description="Version name")


class BriefSaveRequest(BaseModel):
    version: str = Field(default="v1.0.0", description="Version name")
    brief_content: str = Field(default="", description="Nội dung brief")


# ============================================================================
# Helpers
# ============================================================================

def _resolve_project_cwd() -> Optional[str]:
    """Lấy project_cwd, return None nếu không có active project."""
    return get_project_cwd()


def _sse(data: str | dict, event: str = None) -> str:
    """Format SSE message — always JSON-encode data."""
    payload = json.dumps(data, ensure_ascii=False) if isinstance(data, dict) else json.dumps(str(data), ensure_ascii=False)
    line = f"data: {payload}"
    if event:
        line = f"event: {event}\n{line}"
    return f"{line}\n\n"


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/analyze", response_model=ApiResponse)
async def analyze_brief(request_data: BriefAnalyzeRequest = None, request: Request = None):
    """Phân tích brief — delegate vào pipeline."""
    if request_data is None:
        request_data = BriefAnalyzeRequest()

    language = i18n.get_language_from_request(request)
    project_cwd = _resolve_project_cwd()
    if not project_cwd:
        return ApiResponse(success=False, data=None, message=i18n.t("brief.noActiveProject", language), language=language)

    result = await pipeline_bridge.execute_command(
        "brief", "analyze",
        project_cwd=project_cwd,
        version=request_data.version,
        language=language,
    )

    data = result.get("_data", {})
    if data.get("success"):
        return ApiResponse(
            success=True,
            data=data.get("data"),
            message=i18n.t("brief.analyze_success", language),
            language=language,
        )

    error = data.get("error", "")
    if error == "not_found":
        message = i18n.t("brief.notFound", language)
    elif error.startswith("blocked_status:"):
        status = error.split(":", 1)[1]
        message = i18n.t("brief.analyze_blocked", language, status=status)
    elif error == "empty_content":
        message = i18n.t("brief.emptyContent", language)
    elif error.startswith("llm_failed:"):
        message = f"LLM analysis failed: {error.split(':', 1)[1]}"
    else:
        message = result.get("stderr", i18n.t("brief.analyze_failed", language))

    return ApiResponse(success=False, data=None, message=message, language=language)


@router.get("/analyze-stream")
async def analyze_brief_stream_sse(request: Request, version: str = "v1.0.0"):
    """SSE endpoint cho brief analysis — delegate vào pipeline stream generator."""
    project_cwd = _resolve_project_cwd()

    async def error_gen(message: str):
        yield _sse(message, "error")

    if not project_cwd:
        return StreamingResponse(error_gen(i18n.t("brief.noActiveProject")), media_type="text/event-stream")

    language = i18n.get_language_from_request(request)

    try:
        stream = await pipeline_bridge.brief_analyze_stream(project_cwd, version, language)
    except ValueError as e:
        err = e.args[0] if e.args else {}
        if isinstance(err, dict):
            code = err.get("code", "unknown")
        else:
            code = str(err)
        if code == "not_found":
            return StreamingResponse(error_gen(i18n.t("brief.notFound")), media_type="text/event-stream")
        elif code.startswith("blocked_status:"):
            return StreamingResponse(error_gen(f"Brief status='{code.split(':', 1)[1]}', chỉ phân tích khi status=draft"), media_type="text/event-stream")
        elif code == "empty_content":
            return StreamingResponse(error_gen(i18n.t("brief.emptyContent")), media_type="text/event-stream")
        else:
            return StreamingResponse(error_gen(str(err)), media_type="text/event-stream")

    async def event_generator():
        try:
            async for item in stream:
                if await request.is_disconnected():
                    return
                yield _sse(item["data"], item["event"])
        except Exception as e:
            yield _sse(str(e), "error")

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/save", response_model=ApiResponse)
async def save_brief(request_data: BriefSaveRequest = None, request: Request = None):
    """Upsert brief cho version — delegate vào pipeline."""
    if request_data is None:
        request_data = BriefSaveRequest()

    language = i18n.get_language_from_request(request)
    project_cwd = _resolve_project_cwd()
    if not project_cwd:
        return ApiResponse(success=False, data=None, message=i18n.t("brief.noActiveProject", language), language=language)

    if not request_data.brief_content.strip():
        return ApiResponse(success=True, data={"saved": True}, message="OK", language=language)

    result = await pipeline_bridge.execute_command(
        "brief", "save",
        project_cwd=project_cwd,
        version=request_data.version,
        brief_content=request_data.brief_content,
        change_description="Auto-save",
    )

    if not result["success"]:
        stderr = result.get("stderr", "")
        if "đóng băng" in stderr or "freezed" in stderr.lower():
            return ApiResponse(success=False, data=None, message=i18n.t("brief.freezedBlocked", language), language=language)
        return ApiResponse(success=False, data=None, message=i18n.t("brief.saveFailed", language), language=language)

    data = result.get("_data", {})
    brief_id = data.get("brief_id")
    updated = data.get("updated", False)

    if brief_id:
        return ApiResponse(
            success=True,
            data={"saved": True, "brief_id": brief_id, "updated": updated},
            message=i18n.t("brief.updated" if updated else "brief.saved", language),
            language=language,
        )

    return ApiResponse(success=False, data=None, message=i18n.t("brief.saveFailed", language), language=language)


@router.post("/freeze", response_model=ApiResponse)
async def freeze_brief_ep(version: str = Query(None), request: Request = None):
    """Đóng băng brief — delegate vào pipeline."""
    language = i18n.get_language_from_request(request)

    if not version:
        body = await request.json()
        version = body.get("version", "v1.0.0")

    project_cwd = _resolve_project_cwd()
    if not project_cwd:
        return ApiResponse(success=False, data=None, message=i18n.t("brief.noActiveProject", language), language=language)

    result = await pipeline_bridge.execute_command(
        "brief", "freeze",
        version=version,
        project_cwd=project_cwd,
    )

    if result["success"]:
        data = result.get("_data", {})
        return ApiResponse(
            success=True,
            data={"brief_id": data.get("brief_id"), "status": "freezed"},
            message=i18n.t("brief.freezedMsg", language),
            language=language,
        )

    return ApiResponse(
        success=False,
        data=None,
        message=result.get("stderr", i18n.t("brief.freezeError", language)),
        language=language,
    )


@router.get("/get", response_model=ApiResponse)
async def get_brief(version: str = Query(None), request: Request = None):
    """Lấy brief duy nhất cho version — delegate vào pipeline."""
    language = i18n.get_language_from_request(request)
    project_cwd = _resolve_project_cwd()
    if not project_cwd:
        return ApiResponse(success=False, data=None, message=i18n.t("brief.noActiveProject", language), language=language)

    result = await pipeline_bridge.execute_command(
        "brief", "get",
        project_cwd=project_cwd,
        version=version or "v1.0.0",
    )

    data = result.get("_data", {})
    if data.get("success"):
        return ApiResponse(
            success=True,
            data=data.get("data"),
            language=language,
        )

    return ApiResponse(
        success=False,
        data=None,
        message=data.get("error") or result.get("stderr", "Brief not found"),
        language=language,
    )


@router.get("/clarifications", response_model=ApiResponse)
async def get_clarifications(version: str = Query(None), request: Request = None):
    """Lấy clarifications cho brief — delegate vào pipeline."""
    language = i18n.get_language_from_request(request)
    project_cwd = _resolve_project_cwd()
    if not project_cwd:
        return ApiResponse(success=False, data=None, message=i18n.t("brief.noActiveProject", language), language=language)

    result = await pipeline_bridge.execute_command(
        "brief", "clarifications",
        project_cwd=project_cwd,
        version=version or "v1.0.0",
    )

    data = result.get("_data", {})
    if data.get("success"):
        return ApiResponse(
            success=True,
            data=data.get("data"),
            language=language,
        )

    return ApiResponse(
        success=False,
        data=None,
        message=data.get("error") or result.get("stderr", ""),
        language=language,
    )


@router.get("/revisions", response_model=ApiResponse)
async def get_brief_revisions(version: str = Query(None), request: Request = None):
    """Lấy lịch sử revision của brief — delegate vào pipeline."""
    language = i18n.get_language_from_request(request)
    project_cwd = _resolve_project_cwd()
    if not project_cwd:
        return ApiResponse(success=False, data=None, message=i18n.t("brief.noActiveProject", language), language=language)

    result = await pipeline_bridge.execute_command(
        "brief", "revisions",
        project_cwd=project_cwd,
        version=version or "v1.0.0",
    )

    data = result.get("_data", {})
    if data.get("success"):
        return ApiResponse(
            success=True,
            data=data.get("data"),
            language=language,
        )

    return ApiResponse(
        success=False,
        data=None,
        message=data.get("error") or result.get("stderr", ""),
        language=language,
    )


@router.get("/revisions/{revision_number}/diff", response_model=ApiResponse)
async def get_revision_diff(
    revision_number: int,
    version: str = Query(None),
    request: Request = None,
):
    """Lấy unified diff của revision N so với N-1 — delegate vào pipeline."""
    language = i18n.get_language_from_request(request)
    project_cwd = _resolve_project_cwd()
    if not project_cwd:
        return ApiResponse(success=False, data=None, message=i18n.t("brief.noActiveProject", language), language=language)

    result = await pipeline_bridge.execute_command(
        "brief", "revision-diff",
        project_cwd=project_cwd,
        version=version or "v1.0.0",
        revision_number=revision_number,
    )

    data = result.get("_data", {})
    if data.get("success"):
        return ApiResponse(
            success=True,
            data=data.get("data"),
            language=language,
        )

    error = data.get("error", "")
    if error == "revision_not_found":
        message = i18n.t("brief.revisionNotFound", language)
    else:
        message = error or result.get("stderr", "")

    return ApiResponse(
        success=False,
        data=None,
        message=message,
        language=language,
    )
