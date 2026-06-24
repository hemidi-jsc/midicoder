"""
Router cho các commands về contract
"""

import json
from pathlib import Path
from fastapi import APIRouter, Query, Request
from starlette.responses import StreamingResponse

from midicoder.api.pipeline_bridge import pipeline_bridge
from midicoder.api.i18n import i18n
from midicoder.api.models import ApiResponse


def _get_project_artifacts_mgr():
    """Resolve project-level ArtifactsManager."""
    from midicoder.storage.sqlite import ArtifactsManager, get_project_db_path, get_active_project_cwd
    cwd = get_active_project_cwd()
    if cwd:
        db_path = get_project_db_path(cwd, "artifacts.db")
        mgr = ArtifactsManager(db_path=db_path)
        mgr.init()
        return mgr
    # Fallback to global
    mgr = ArtifactsManager()
    mgr.init()
    return mgr

router = APIRouter(prefix="/contract", tags=["Contract"])


def _sse(data: str | dict, event: str = None) -> str:
    """Format SSE message — always JSON-encode data."""
    payload = json.dumps(data, ensure_ascii=False) if isinstance(data, dict) else json.dumps(str(data), ensure_ascii=False)
    line = f"data: {payload}"
    if event:
        line = f"event: {event}\n{line}"
    return f"{line}\n\n"


@router.get("/gen-category-stream")
async def generate_contract_category_stream(request: Request, category: str = Query(...), force: bool = Query(False)):
    """SSE streaming endpoint cho gen 1 category riêng — compatible với llm-progress component."""
    language = i18n.get_language_from_request(request)

    async def error_gen(message: str):
        yield _sse(message, "error")

    try:
        stream = await pipeline_bridge.contract_category_gen_stream(category=category, force=force)
    except Exception as e:
        return StreamingResponse(error_gen(str(e)), media_type="text/event-stream")

    async def event_generator():
        try:
            async for item in stream:
                if await request.is_disconnected():
                    return
                yield _sse(item["data"], item["event"])
        except Exception as e:
            yield _sse(str(e), "error")

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/freeze", response_model=ApiResponse)
async def freeze_contract(request: Request):
    """Freeze tất cả contract artifacts — lock như source of truth."""
    language = i18n.get_language_from_request(request)

    result = await pipeline_bridge.contract_freeze()

    if result["success"]:
        return ApiResponse(
            success=True,
            data=result.get("_data", {}),
            message=i18n.translate("contract.freeze_success", language),
            language=language,
        )

    return ApiResponse(
        success=False,
        data=None,
        message=result.get("stderr", result.get("error", "Unknown error")),
        language=language,
    )


# ============================================================================
# GET endpoints — đọc từ SQLite ArtifactsManager (lazy import)
# ============================================================================

@router.get("/artifacts", response_model=ApiResponse)
async def get_contract_artifacts(request: Request, category: str = Query(...)):
    """Check existence + get metadata for a contract category artifact."""
    language = i18n.get_language_from_request(request)
    try:
        mgr = _get_project_artifacts_mgr()
        artifact = mgr.get(f"contract_{category}")
        if artifact is None:
            return ApiResponse(success=True, data={"exists": False}, language=language)
        return ApiResponse(success=True, data={
            "exists": True,
            "artifact_id": artifact.get("artifact_id"),
            "status": artifact.get("status"),
            "content_length": len(artifact.get("content", "")),
            "updated_at": artifact.get("updated_at"),
        }, language=language)
    except Exception as e:
        return ApiResponse(success=False, data=None, message=str(e), language=language)


@router.get("/artifacts/{category}", response_model=ApiResponse)
async def get_contract_artifact_content(request: Request, category: str):
    """Get raw YAML content for a contract category artifact."""
    language = i18n.get_language_from_request(request)
    try:
        mgr = _get_project_artifacts_mgr()
        artifact = mgr.get(f"contract_{category}")
        if artifact is None:
            return ApiResponse(success=True, data={"exists": False, "content": ""}, language=language)
        return ApiResponse(success=True, data={
            "exists": True,
            "artifact_id": artifact.get("artifact_id"),
            "status": artifact.get("status"),
            "content": artifact.get("content", ""),
            "updated_at": artifact.get("updated_at"),
        }, language=language)
    except Exception as e:
        return ApiResponse(success=False, data=None, message=str(e), language=language)


@router.get("/manifest", response_model=ApiResponse)
async def get_contract_manifest_endpoint(version: str = Query(None), request: Request = None):
    """Lấy contract manifest từ SQLite ArtifactsManager."""
    language = i18n.get_language_from_request(request)
    try:
        mgr = _get_project_artifacts_mgr()
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