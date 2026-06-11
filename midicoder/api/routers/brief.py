"""
Router cho brief — 1 version = 1 brief duy nhất, 2 status: draft / freezed.

Kiến trúc:
- Mỗi version có đúng 1 brief
- Status: draft (có thể chỉnh sửa) → freezed (readonly, không thể chỉnh sửa)
- Status chỉ đổi khi user bấm nút freeze trên WebGUI (delegate qua pipeline_bridge)
- Không có auto-transition status
- Mỗi lần thay đổi content → log vào brief_revisions table
- Tất cả DB paths dùng explicit project path từ get_project_cwd()
"""

import hashlib
import json
import uuid
from pathlib import Path

from pydantic import BaseModel, Field

from fastapi import APIRouter, Query, Request

from midicoder.api.i18n import i18n
from midicoder.api.models import ApiResponse
from midicoder.api.pipeline_bridge import pipeline_bridge
from midicoder.api.config import get_project_cwd

router = APIRouter(prefix="/brief", tags=["Brief"])


class BriefAnalyzeRequest(BaseModel):
    brief_content: str = Field(..., description="Nội dung brief")
    version: str = Field(default="v1.0.0", description="Version name")


class BriefSaveRequest(BaseModel):
    version: str = Field(default="v1.0.0", description="Version name")
    brief_content: str = Field(default="", description="Nội dung brief")


def _get_project_db_path(db_name: str) -> Path | None:
    """Lấy explicit path đến database file của project. Returns None nếu không có project."""
    from midicoder.api.config import get_project_cwd
    project_cwd = get_project_cwd()
    if not project_cwd:
        return None
    return Path(project_cwd) / ".midicoder" / "data" / db_name


def _get_brief(mgr, version: str):
    """Lấy brief duy nhất cho version này."""
    for b in mgr.list(version=version):
        return b
    return None


def _add_revision(mgr, brief_id: str, version: str, event: str, diff_summary: str, content: str = None):
    """Thêm revision vào brief_revisions table."""
    try:
        mgr.add_revision(brief_id, version, event, diff_summary, content)
    except Exception:
        pass


def _upsert_brief(mgr, version: str, content: str, title: str = None, change_description: str = "Auto-save"):
    """Upsert brief: update nếu tồn tại (log revision), tạo mới nếu chưa có.

    Raises ValueError nếu brief đã freezed.
    """
    existing = _get_brief(mgr, version)
    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

    if existing:
        brief_id = existing.get("brief_id")
        if existing.get("status") == "freezed":
            raise ValueError("Brief đã được đóng băng, không thể chỉnh sửa")
        old_hash = existing.get("content_hash", "")
        if old_hash != content_hash:
            pass  # revision is logged below
        with mgr._get_connection() as conn:
            conn.execute(
                "UPDATE briefs SET content = ?, content_hash = ?, title = ?, updated_at = datetime('now') WHERE brief_id = ?",
                (content, content_hash, title or existing.get("title", ""), brief_id),
            )
        _add_revision(mgr, brief_id, version, "content_updated", change_description, content)
        return brief_id, True
    else:
        brief_id = f"brief-{uuid.uuid4().hex[:8]}"
        try:
            mgr.create(
                brief_id=brief_id,
                version=version,
                content=content,
                title=title or content.split("\n")[0].strip()[:100],
            )
            _add_revision(mgr, brief_id, version, "created", "Brief created", content)
            return brief_id, False
        except Exception:
            return None, False


@router.post("/analyze", response_model=ApiResponse)
async def analyze_brief(request_data: BriefAnalyzeRequest = None, request: Request = None):
    """Phân tích brief — upsert SQLite + LLM analysis. KHÔNG đổi status tự động."""
    if request_data is None:
        request_data = BriefAnalyzeRequest(brief_content="")

    language = i18n.get_language_from_request(request)
    version = request_data.version or "v1.0.0"

    if not request_data.brief_content.strip():
        return ApiResponse(success=False, data=None, message=i18n.t("brief.emptyContent", language), language=language)

    from midicoder.storage.sqlite import BriefsManager, ArtifactsManager

    briefs_manager = BriefsManager(db_path=_get_project_db_path("briefs.db"))
    briefs_manager.init()

    try:
        brief_id, _ = _upsert_brief(briefs_manager, version, request_data.brief_content)
    except ValueError as e:
        return ApiResponse(success=False, data=None, message=str(e), language=language)

    if not brief_id:
        return ApiResponse(success=False, data=None, message=i18n.t("brief.saveFailed", language), language=language)

    from midicoder.pipeline.analyze import analyze_brief_with_llm

    try:
        analysis = analyze_brief_with_llm(
            brief_content=request_data.brief_content,
            domain=None,
            brief_id=brief_id,
        )
    except Exception as e:
        return ApiResponse(success=False, data=None, message=f"LLM analysis failed: {str(e)}", language=language)

    _add_revision(briefs_manager, brief_id, version, "analyzed", "LLM analysis completed", request_data.brief_content)

    json_data = analysis.json_data
    entities = json_data.get("entities", [])
    commands = json_data.get("commands", [])
    queries = json_data.get("queries", [])
    events = json_data.get("events", [])
    ui_components = json_data.get("ui_components", [])
    confidence = analysis.confidence
    summary = json_data.get("summary", "")

    artifact_id = f"analysis-{brief_id}"
    artifacts_manager = ArtifactsManager(db_path=_get_project_db_path("artifacts.db"))
    artifacts_manager.init()

    content_json = json.dumps(json_data, indent=2, ensure_ascii=False)
    artifact_metadata = {
        "domain": analysis.domain,
        "confidence": confidence,
        "tokens_used": analysis.tokens_used,
        "latency_ms": analysis.latency_ms,
        "entity_count": len(entities),
        "command_count": len(commands),
        "query_count": len(queries),
        "event_count": len(events),
        "ui_component_count": len(ui_components),
    }

    existing_artifact = artifacts_manager.get(artifact_id)
    if existing_artifact:
        artifacts_manager.update_content(artifact_id, content_json)
    else:
        artifacts_manager.create(
            artifact_id=artifact_id,
            artifact_type="analysis",
            name="Brief Analysis",
            version=version,
            brief_id=brief_id,
            content=content_json,
            metadata=artifact_metadata,
        )

    ambiguities = json_data.get("ambiguities", [])

    return ApiResponse(
        success=True,
        data={
            "status": "needs_clarification",
            "analysis": {
                "intent": {
                    "domain": json_data.get("domain", analysis.domain),
                    "type": json_data.get("type", "api"),
                    "scale": json_data.get("scale", "medium"),
                },
                "ambiguities": ambiguities,
                "summary": summary,
            },
            "metadata": {
                "domain": analysis.domain,
                "confidence": confidence,
                "entities": len(entities),
                "commands": len(commands),
                "queries": len(queries),
                "events": len(events),
                "ui_components": len(ui_components),
                "brief_id": brief_id,
            },
        },
        message=i18n.t("brief.analyzeSuccess", language),
        language=language,
    )


@router.post("/save", response_model=ApiResponse)
async def save_brief(request_data: BriefSaveRequest = None, request: Request = None):
    """Upsert brief cho version. Block nếu brief đã freezed."""
    if request_data is None:
        request_data = BriefSaveRequest()

    language = i18n.get_language_from_request(request)

    if request_data.brief_content.strip():
        from midicoder.storage.sqlite import BriefsManager
        mgr = BriefsManager(db_path=_get_project_db_path("briefs.db"))
        mgr.init()

        try:
            brief_id, updated = _upsert_brief(mgr, request_data.version, request_data.brief_content, change_description="Auto-save")
        except ValueError as e:
            return ApiResponse(success=False, data=None, message=str(e), language=language)

        if brief_id:
            return ApiResponse(
                success=True,
                data={"saved": True, "brief_id": brief_id, "updated": updated},
                message=i18n.t("brief.updated" if updated else "brief.saved", language),
                language=language,
            )
        return ApiResponse(success=False, data=None, message=i18n.t("brief.saveFailed", language), language=language)

    return ApiResponse(success=True, data={"saved": True}, message="OK", language=language)


@router.post("/freeze", response_model=ApiResponse)
async def freeze_brief_ep(version: str = Query(None), request: Request = None):
    """Đóng băng brief — delegate vào pipeline (status → freezed, version → inbuild)."""
    language = i18n.get_language_from_request(request)

    if not version:
        body = await request.json()
        version = body.get("version", "v1.0.0")

    project_cwd = get_project_cwd()
    if not project_cwd:
        return ApiResponse(success=False, data=None, message=i18n.t("brief.noActiveProject", language), language=language)

    result = await pipeline_bridge.execute_command(
        "brief", "freeze", version=version, project_cwd=project_cwd
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
    """Lấy brief duy nhất cho version (content + status + clarifications + analysis artifact)."""
    language = i18n.get_language_from_request(request)
    try:
        from midicoder.storage.sqlite import BriefsManager, ArtifactsManager
        mgr = BriefsManager(db_path=_get_project_db_path("briefs.db"))
        mgr.init()

        brief = _get_brief(mgr, version)
        if not brief:
            return ApiResponse(success=False, data=None, message="Brief not found", language=language)

        brief_id = brief.get("brief_id")
        clarifications = mgr.get_clarifications(brief_id)

        analysis_data = None
        try:
            artifacts_mgr = ArtifactsManager(db_path=_get_project_db_path("artifacts.db"))
            artifacts_mgr.init()
            for art in artifacts_mgr.list(artifact_type="analysis", brief_id=brief_id):
                try:
                    content = json.loads(art.get("content") or "{}")
                    metadata_raw = {}
                    raw_metadata = art.get("metadata")
                    if raw_metadata:
                        if isinstance(raw_metadata, str):
                            metadata_raw = json.loads(raw_metadata)
                        elif isinstance(raw_metadata, dict):
                            metadata_raw = raw_metadata

                    intent = content.get("intent") or {
                        "domain": content.get("domain", ""),
                        "type": content.get("type", "api"),
                        "scale": content.get("scale", "medium"),
                    }

                    normalized_metadata = {
                        "domain": metadata_raw.get("domain", intent.get("domain", "")),
                        "confidence": metadata_raw.get("confidence", 0.5),
                        "entities": metadata_raw.get("entity_count", metadata_raw.get("entities", 0)),
                        "commands": metadata_raw.get("command_count", metadata_raw.get("commands", 0)),
                        "queries": metadata_raw.get("query_count", metadata_raw.get("queries", 0)),
                        "events": metadata_raw.get("event_count", metadata_raw.get("events", 0)),
                        "ui_components": metadata_raw.get("ui_component_count", metadata_raw.get("ui_components", 0)),
                        "brief_id": brief_id,
                    }

                    analysis_data = {
                        "status": "ready_for_contract" if normalized_metadata.get("confidence", 0) >= 0.8 else "needs_clarification",
                        "analysis": {
                            "intent": intent,
                            "ambiguities": content.get("ambiguities", []),
                            "summary": content.get("summary", ""),
                            "entities": content.get("entities", []),
                            "commands": content.get("commands", []),
                            "queries": content.get("queries", []),
                            "events": content.get("events", []),
                            "ui_components": content.get("ui_components", []),
                        },
                        "metadata": normalized_metadata,
                    }
                    if content.get("ambiguities"):
                        analysis_data["status"] = "needs_clarification"
                except Exception:
                    pass
                break
        except Exception:
            pass

        return ApiResponse(
            success=True,
            data={
                "brief_id": brief_id,
                "version": brief.get("version"),
                "status": brief.get("status", "draft"),
                "title": brief.get("title", ""),
                "content": brief.get("content", ""),
                "clarifications": clarifications,
                "analysis": analysis_data,
                "created_at": brief.get("created_at", ""),
                "updated_at": brief.get("updated_at", ""),
            },
            language=language,
        )
    except Exception as e:
        return ApiResponse(success=False, data=None, message=str(e), language=language)


@router.get("/clarifications", response_model=ApiResponse)
async def get_clarifications(version: str = Query(None), request: Request = None):
    """Lấy clarifications cho brief của version."""
    language = i18n.get_language_from_request(request)
    try:
        from midicoder.storage.sqlite import BriefsManager
        mgr = BriefsManager(db_path=_get_project_db_path("briefs.db"))
        mgr.init()

        brief = _get_brief(mgr, version)
        if not brief:
            return ApiResponse(success=True, data={"clarifications": [], "count": 0}, language=language)

        clarifications = mgr.get_clarifications(brief.get("brief_id"))
        cl_list = []
        for c in clarifications:
            cl_list.append({
                "id": c.get("id"),
                "brief_id": brief.get("brief_id"),
                "round": c.get("round"),
                "question": c.get("question", ""),
                "answer": c.get("answer", ""),
                "is_memo": bool(c.get("is_memo")),
                "created_at": c.get("created_at", ""),
            })
        cl_list.sort(key=lambda x: x.get("round", 0))
        return ApiResponse(success=True, data={"clarifications": cl_list, "count": len(cl_list)}, language=language)
    except Exception as e:
        return ApiResponse(success=False, data=None, message=str(e), language=language)


@router.get("/revisions", response_model=ApiResponse)
async def get_brief_revisions(version: str = Query(None), request: Request = None):
    """Lấy lịch sử revision của brief (từ brief_revisions table)."""
    language = i18n.get_language_from_request(request)
    try:
        from midicoder.storage.sqlite import BriefsManager
        mgr = BriefsManager(db_path=_get_project_db_path("briefs.db"))
        mgr.init()

        brief = _get_brief(mgr, version)
        if not brief:
            return ApiResponse(success=True, data={"revisions": [], "count": 0}, language=language)

        brief_id = brief.get("brief_id")
        revisions = mgr.get_revisions(brief_id)

        # Append 'Z' để frontend parse đúng UTC (giống activity.py)
        for rev in revisions:
            ts = rev.get("created_at", "")
            if ts and isinstance(ts, str) and not ts.endswith("Z") and "+" not in ts:
                rev["created_at"] = ts + "Z"

        return ApiResponse(success=True, data={"revisions": revisions, "count": len(revisions)}, language=language)
    except Exception as e:
        return ApiResponse(success=False, data=None, message=str(e), language=language)


@router.get("/revisions/{revision_number}/diff", response_model=ApiResponse)
async def get_revision_diff(
    revision_number: int,
    version: str = Query(None),
    request: Request = None,
):
    """Lấy unified diff của revision N so với revision N-1.

    Returns:
        - added_lines, removed_lines: list of strings with line numbers
        - diff_text: unified diff format string
        - stats: {added, removed, total}
    """
    import difflib

    language = i18n.get_language_from_request(request)
    try:
        from midicoder.storage.sqlite import BriefsManager
        mgr = BriefsManager(db_path=_get_project_db_path("briefs.db"))
        mgr.init()

        brief = _get_brief(mgr, version)
        if not brief:
            return ApiResponse(success=True, data={"diff_text": "", "stats": {"added": 0, "removed": 0}}, language=language)

        brief_id = brief.get("brief_id")

        # Get current revision
        revisions = mgr.get_revisions(brief_id)
        current_rev = None
        prev_rev = None
        for rev in revisions:
            if rev["revision_number"] == revision_number:
                current_rev = rev
                break

        if not current_rev:
            return ApiResponse(success=False, data=None, message="Revision not found", language=language)

        # Find previous revision
        for rev in revisions:
            if rev["revision_number"] == revision_number - 1:
                prev_rev = rev
                break

        current_content = current_rev.get("content_snapshot") or ""
        prev_content = ""
        if prev_rev:
            prev_content = prev_rev.get("content_snapshot") or ""

        # Compute unified diff
        current_lines = current_content.splitlines(keepends=True)
        prev_lines = prev_content.splitlines(keepends=True)

        diff = list(difflib.unified_diff(prev_lines, current_lines, fromfile=f"v{revision_number - 1}", tofile=f"v{revision_number}", lineterm=""))
        diff_text = "\n".join(diff) if diff else ""

        # Count added/removed
        added = sum(1 for line in diff if line.startswith("+") and not line.startswith("+++"))
        removed = sum(1 for line in diff if line.startswith("-") and not line.startswith("---"))

        return ApiResponse(
            success=True,
            data={
                "revision_number": revision_number,
                "event": current_rev.get("event"),
                "diff_summary": current_rev.get("diff_summary"),
                "diff_text": diff_text,
                "stats": {"added": added, "removed": removed, "total": added + removed},
                "has_diff": added > 0 or removed > 0,
            },
            language=language,
        )
    except Exception as e:
        return ApiResponse(success=False, data=None, message=str(e), language=language)
