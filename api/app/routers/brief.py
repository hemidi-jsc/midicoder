"""
Router cho brief — 1 version = 1 brief duy nhất, status là progress.

Kiến trúc:
- Mỗi version có đúng 1 brief (type=working)
- Status progression: draft → clarified → frozen → archived
- Mỗi lần thay đổi content → log vào brief_lineage table
- Tất cả DB paths dùng explicit project path từ get_project_cwd()
"""

import hashlib
import json
import re
import uuid
from pathlib import Path

from pydantic import BaseModel, Field

from fastapi import APIRouter, Query, Request

from app.i18n import i18n
from app.models import ApiResponse

router = APIRouter(prefix="/brief", tags=["Brief"])


class BriefAnalyzeRequest(BaseModel):
    brief_content: str = Field(..., description="Nội dung brief")
    version: str = Field(default="v1.0.0", description="Version name")


class BriefSaveRequest(BaseModel):
    version: str = Field(default="v1.0.0", description="Version name")
    brief_content: str = Field(default="", description="Nội dung brief")


def _get_project_db_path(db_name: str) -> Path:
    """Lấy explicit path đến database file của project."""
    from app.config import get_project_cwd
    project_cwd = Path(get_project_cwd())
    return project_cwd / ".midicoder" / "data" / db_name


def _get_working_brief(mgr, version: str):
    """Lấy brief duy nhất cho version này."""
    for b in mgr.list(version=version):
        if b.get("type") == "working":
            return b
    return None


def _log_lineage(mgr, brief_id: str, version: str, change_type: str, change_description: str):
    """Log thay đổi vào brief_lineage table."""
    try:
        with mgr._get_connection() as conn:
            conn.execute(
                "INSERT INTO brief_lineage (brief_id, parent_brief_id, version, change_type, change_description) VALUES (?, ?, ?, ?, ?)",
                (brief_id, brief_id, version, change_type, change_description),
            )
    except Exception:
        pass


def _upsert_brief(mgr, version: str, content: str, title: str = None, change_description: str = "Auto-save"):
    """Upsert brief: update nếu tồn tại (log lineage), tạo mới nếu chưa có."""
    existing = _get_working_brief(mgr, version)
    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

    if existing:
        brief_id = existing.get("brief_id")
        old_hash = existing.get("hash", "")
        if old_hash != content_hash:
            _log_lineage(mgr, brief_id, version, "content_update", f"Content updated: {change_description}")
        with mgr._get_connection() as conn:
            conn.execute(
                "UPDATE briefs SET content = ?, hash = ?, title = ?, updated_at = datetime('now') WHERE brief_id = ?",
                (content, content_hash, title or existing.get("title", ""), brief_id),
            )
        return brief_id, True
    else:
        brief_id = f"brief-{uuid.uuid4().hex[:8]}"
        try:
            mgr.create(
                brief_id=brief_id,
                version=version,
                content=content,
                title=title or content.split("\n")[0].strip()[:100],
                brief_type="working",
            )
            _log_lineage(mgr, brief_id, version, "created", "Brief created")
            return brief_id, False
        except Exception:
            return None, False


@router.post("/analyze", response_model=ApiResponse)
async def analyze_brief(request_data: BriefAnalyzeRequest = None, request: Request = None):
    """Phân tích brief — upsert SQLite + gọi LLM trực tiếp."""
    if request_data is None:
        request_data = BriefAnalyzeRequest(brief_content="")

    language = i18n.get_language_from_request(request)
    version = request_data.version or "v1.0.0"

    if not request_data.brief_content.strip():
        return ApiResponse(success=False, data=None, message="Brief content không được để trống", language=language)

    from midicoder.storage.sqlite import BriefsManager, ArtifactsManager

    briefs_manager = BriefsManager(db_path=_get_project_db_path("briefs.db"))
    briefs_manager.init()

    brief_id, _ = _upsert_brief(briefs_manager, version, request_data.brief_content)
    if not brief_id:
        return ApiResponse(success=False, data=None, message="Không thể lưu brief vào SQLite", language=language)

    from midicoder.pipeline.llm import load_llm_config, call_llm
    from midicoder.pipeline.domain import detect_domain, get_domain_prompt, normalize_domain

    try:
        llm_config = load_llm_config()
    except Exception as e:
        return ApiResponse(success=False, data=None, message=f"Lỗi load LLM config: {str(e)}", language=language)

    domain = normalize_domain(detect_domain(request_data.brief_content, llm_config))
    try:
        system_prompt = get_domain_prompt(domain)
    except Exception:
        system_prompt = get_domain_prompt("generic")

    try:
        response = call_llm(
            config=llm_config,
            system=system_prompt,
            messages=[{"role": "user", "content": request_data.brief_content}],
        )

        content = response.content.strip()
        content = re.sub(r'<thinking>.*?</thinking>', '', content, flags=re.DOTALL).strip()

        json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', content, re.DOTALL)
        if json_match:
            content = json_match.group(1).strip()
        if not content.startswith('{'):
            brace_start = content.find('{')
            if brace_start >= 0:
                brace_end = content.rfind('}')
                if brace_end >= brace_start:
                    content = content[brace_start:brace_end + 1]

        json_data = json.loads(content)
    except Exception as e:
        return ApiResponse(success=False, data=None, message=f"LLM analysis failed: {str(e)}", language=language)

    # Lưu analysis artifact — dùng explicit project DB path
    artifacts_manager = ArtifactsManager(db_path=_get_project_db_path("artifacts.db"))
    artifacts_manager.init()

    entities = json_data.get("entities", [])
    commands = json_data.get("commands", [])
    queries = json_data.get("queries", [])
    events = json_data.get("events", [])
    ui_components = json_data.get("ui_components", [])
    confidence = json_data.get("confidence", 0.5)
    summary = json_data.get("summary", "")

    artifacts_manager.create(
        artifact_id=f"analysis-{brief_id}",
        artifact_type="analysis",
        name="Brief Analysis",
        version=version,
        brief_id=brief_id,
        content=json.dumps(json_data, indent=2, ensure_ascii=False),
        metadata={
            "domain": domain,
            "confidence": confidence,
            "tokens_used": response.usage.get("total_tokens", 0),
            "entity_count": len(entities),
            "command_count": len(commands),
            "query_count": len(queries),
            "event_count": len(events),
            "ui_component_count": len(ui_components),
        },
    )

    ambiguities = json_data.get("ambiguities", [])
    needs_clarification = bool(ambiguities) or confidence < 0.8

    return ApiResponse(
        success=True,
        data={
            "status": "needs_clarification" if needs_clarification else "ready_for_contract",
            "analysis": {
                "intent": {
                    "domain": json_data.get("domain", domain),
                    "type": json_data.get("type", "api"),
                    "scale": json_data.get("scale", "medium"),
                },
                "ambiguities": ambiguities,
                "summary": summary,
            },
            "metadata": {
                "domain": domain,
                "confidence": confidence,
                "entities": len(entities),
                "commands": len(commands),
                "queries": len(queries),
                "events": len(events),
                "ui_components": len(ui_components),
                "brief_id": brief_id,
            },
        },
        message="Phân tích brief thành công",
        language=language,
    )


@router.post("/save", response_model=ApiResponse)
async def save_brief(request_data: BriefSaveRequest = None, request: Request = None):
    """Upsert brief cho version — 1 version = 1 brief duy nhất."""
    if request_data is None:
        request_data = BriefSaveRequest()

    language = i18n.get_language_from_request(request)

    if request_data.brief_content.strip():
        from midicoder.storage.sqlite import BriefsManager
        mgr = BriefsManager(db_path=_get_project_db_path("briefs.db"))
        mgr.init()

        brief_id, updated = _upsert_brief(mgr, request_data.version, request_data.brief_content, change_description="Auto-save")
        if brief_id:
            return ApiResponse(
                success=True,
                data={"saved": True, "brief_id": brief_id, "updated": updated},
                message="Brief updated" if updated else "Brief saved",
                language=language,
            )
        return ApiResponse(success=False, data=None, message="Failed to save brief", language=language)

    return ApiResponse(success=True, data={"saved": True}, message="OK", language=language)


@router.post("/rewrite", response_model=ApiResponse)
async def rewrite_brief(request_data: BriefAnalyzeRequest = None, request: Request = None):
    """Viết lại brief bằng LLM — upsert content mới + log lineage."""
    if request_data is None:
        request_data = BriefAnalyzeRequest(brief_content="")

    language = i18n.get_language_from_request(request)
    version = request_data.version or "v1.0.0"

    from midicoder.storage.sqlite import BriefsManager
    mgr = BriefsManager(db_path=_get_project_db_path("briefs.db"))
    mgr.init()

    existing = _get_working_brief(mgr, version)
    if not existing:
        return ApiResponse(success=False, data=None, message="Không tìm thấy brief để rewrite", language=language)

    brief_content = request_data.brief_content or existing.get("content", "")
    if not brief_content.strip():
        return ApiResponse(success=False, data=None, message="Brief content không được để trống", language=language)

    from midicoder.pipeline.llm import load_llm_config, call_llm

    try:
        llm_config = load_llm_config()
    except Exception as e:
        return ApiResponse(success=False, data=None, message=f"Lỗi load LLM config: {str(e)}", language=language)

    rewrite_prompt = (
        "Bạn là technical writer chuyên nghiệp. Cải thiện brief dưới đây để rõ ràng, cụ thể hơn.\n\n"
        f"## Brief gốc:\n{brief_content}"
    )

    try:
        response = call_llm(
            config=llm_config,
            system="Cải thiện brief để rõ ràng, cụ thể hơn.",
            messages=[{"role": "user", "content": rewrite_prompt}],
        )
        improved_content = response.content.strip()
        brief_id, _ = _upsert_brief(mgr, version, improved_content, existing.get("title", ""), change_description="LLM rewrite")

        return ApiResponse(
            success=True,
            data={"brief_id": brief_id, "content": improved_content, "tokens_used": response.usage.get("total_tokens", 0)},
            message="Rewrite brief thành công",
            language=language,
        )
    except Exception as e:
        return ApiResponse(success=False, data=None, message=f"LLM rewrite failed: {str(e)}", language=language)


@router.post("/freeze", response_model=ApiResponse)
async def freeze_brief(version: str = Query(None), request: Request = None):
    """Đóng brief — status clarified → frozen."""
    language = i18n.get_language_from_request(request)

    if not version:
        body = await request.json()
        version = body.get("version", "v1.0.0")

    from midicoder.storage.sqlite import BriefsManager
    mgr = BriefsManager(db_path=_get_project_db_path("briefs.db"))
    mgr.init()

    target = _get_working_brief(mgr, version)
    if not target:
        return ApiResponse(success=False, data=None, message="Không tìm thấy brief", language=language)

    if target.get("status") not in ("clarified", "draft"):
        return ApiResponse(success=False, data=None, message=f"Brief ở status {target.get('status')}, không thể freeze", language=language)

    brief_id = target.get("brief_id")
    mgr.update_status(brief_id, "frozen")
    _log_lineage(mgr, brief_id, version, "frozen", "Brief frozen")

    return ApiResponse(success=True, data={"brief_id": brief_id, "status": "frozen"}, message="Brief đã được đóng", language=language)


@router.get("/get", response_model=ApiResponse)
async def get_brief(version: str = Query(None), request: Request = None):
    """Lấy brief duy nhất cho version (content + status + clarifications + analysis artifact)."""
    language = i18n.get_language_from_request(request)
    try:
        from midicoder.storage.sqlite import BriefsManager, ArtifactsManager
        mgr = BriefsManager(db_path=_get_project_db_path("briefs.db"))
        mgr.init()

        brief = _get_working_brief(mgr, version)
        if not brief:
            return ApiResponse(success=False, data=None, message="Brief not found", language=language)

        brief_id = brief.get("brief_id")
        clarifications = mgr.get_clarifications(brief_id)

        # Load analysis artifact nếu có (explicit project DB path)
        analysis_data = None
        try:
            artifacts_mgr = ArtifactsManager(db_path=_get_project_db_path("artifacts.db"))
            artifacts_mgr.init()
            for art in artifacts_mgr.list(artifact_type="analysis", brief_id=brief_id):
                try:
                    content = json.loads(art.get("content") or "{}")
                    # metadata trong SQLite là JSON string — phải parse
                    metadata = {}
                    raw_metadata = art.get("metadata")
                    if raw_metadata:
                        if isinstance(raw_metadata, str):
                            metadata = json.loads(raw_metadata)
                        elif isinstance(raw_metadata, dict):
                            metadata = raw_metadata
                    
                    analysis_data = {
                        "status": "ready_for_contract" if metadata.get("confidence", 0) >= 0.8 else "needs_clarification",
                        "analysis": {
                            "intent": content.get("intent", {}),
                            "ambiguities": content.get("ambiguities", []),
                            "summary": content.get("summary", ""),
                        },
                        "metadata": metadata,
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
                "type": brief.get("type", "working"),
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

        brief = _get_working_brief(mgr, version)
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


@router.get("/lineage", response_model=ApiResponse)
async def get_brief_lineage(version: str = Query(None), request: Request = None):
    """Lấy lịch sử thay đổi của brief (từ brief_lineage table)."""
    language = i18n.get_language_from_request(request)
    try:
        from midicoder.storage.sqlite import BriefsManager
        mgr = BriefsManager(db_path=_get_project_db_path("briefs.db"))
        mgr.init()

        brief = _get_working_brief(mgr, version)
        if not brief:
            return ApiResponse(success=True, data={"lineage": [], "count": 0}, language=language)

        brief_id = brief.get("brief_id")
        with mgr._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM brief_lineage WHERE brief_id = ? ORDER BY created_at", (brief_id,))
            lineage = [dict(row) for row in cursor.fetchall()]

        return ApiResponse(success=True, data={"lineage": lineage, "count": len(lineage)}, language=language)
    except Exception as e:
        return ApiResponse(success=False, data=None, message=str(e), language=language)
