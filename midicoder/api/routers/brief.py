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
import uuid
from pathlib import Path

from pydantic import BaseModel, Field

from fastapi import APIRouter, Query, Request

from midicoder.api.i18n import i18n
from midicoder.api.models import ApiResponse

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


def _get_working_brief(mgr, version: str):
    """Lấy brief duy nhất cho version này."""
    for b in mgr.list(version=version):
        if b.get("type") == "working":
            return b
    return None


def _log_lineage(mgr, brief_id: str, version: str, change_type: str, change_description: str, old_hash: str = None, new_hash: str = None):
    """Log thay đổi vào brief_lineage table."""
    try:
        with mgr._get_connection() as conn:
            # Kiểm tra schema có columns hash không (backward compat với DB cũ)
            cursor = conn.execute("PRAGMA table_info(brief_lineage)")
            columns = [row["name"] for row in cursor.fetchall()]
            if "old_content_hash" in columns:
                conn.execute(
                    "INSERT INTO brief_lineage (brief_id, parent_brief_id, version, change_type, change_description, old_content_hash, new_content_hash) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (brief_id, brief_id, version, change_type, change_description, old_hash, new_hash),
                )
            else:
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
            _log_lineage(mgr, brief_id, version, "content_update", f"Content updated: {change_description}", old_hash=old_hash, new_hash=content_hash)
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
            _log_lineage(mgr, brief_id, version, "created", "Brief created", old_hash=None, new_hash=content_hash)
            return brief_id, False
        except Exception:
            return None, False


@router.post("/analyze", response_model=ApiResponse)
async def analyze_brief(request_data: BriefAnalyzeRequest = None, request: Request = None):
    """Phân tích brief — upsert SQLite + reuse _analyze_with_llm() từ CLI pipeline."""
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

    # Reuse 100% CLI pipeline function — import từ pure module
    from midicoder.pipeline.analyze import analyze_brief_with_llm

    try:
        analysis = analyze_brief_with_llm(
            brief_content=request_data.brief_content,
            domain=None,
            brief_id=brief_id,
        )
    except Exception as e:
        return ApiResponse(success=False, data=None, message=f"LLM analysis failed: {str(e)}", language=language)

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

    # Upsert: update nếu artifact đã tồn tại, tạo mới nếu chưa
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

    # Cập nhật status brief sau analyze
    if confidence >= 0.8 and len(ambiguities) == 0:
        # Đủ rõ, không có ambiguity → clarified
        try:
            briefs_manager.update_status(brief_id, "clarified")
        except Exception:
            pass
    else:
        # Có ambiguity hoặc confidence thấp → analyzed (chờ clarify)
        try:
            briefs_manager.update_status(brief_id, "analyzed")
        except Exception:
            pass

    # Luôn trả về "needs_clarification" sau khi analyze
    # User có thể skip clarify nếu brief đã đủ rõ (clarify done=True ngay lập tức)
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


@router.post("/freeze", response_model=ApiResponse)
async def freeze_brief(version: str = Query(None), request: Request = None):
    """Đóng brief — status clarified/draft → frozen."""
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

    if target.get("status") == "frozen":
        return ApiResponse(success=False, data=None, message="Brief đã được đóng rồi", language=language)

    brief_id = target.get("brief_id")
    brief_hash = target.get("hash", "")
    mgr.update_status(brief_id, "frozen")
    _log_lineage(mgr, brief_id, version, "frozen", "Brief frozen", old_hash=brief_hash, new_hash=brief_hash)

    # Chuyển status version từ draft → active (brief đã được đóng)
    try:
        from midicoder.storage.projects import ProjectsManager
        pm = ProjectsManager()
        pm.init()
        active_project = pm.get_active()
        if active_project:
            pm.version_update_status(active_project["project_id"], version, "inbuild")

        # Cập nhật metadata.yml
        from midicoder.api.config import _get_project_root
        from pathlib import Path
        import yaml
        meta_file = Path(_get_project_root()) / ".midicoder" / "versions" / version / "metadata.yml"
        if meta_file.exists():
            with open(meta_file, "r", encoding="utf-8") as f:
                meta = yaml.safe_load(f) or {}
            meta["status"] = "inbuild"
            with open(meta_file, "w", encoding="utf-8") as f:
                yaml.dump(meta, f, default_flow_style=False, allow_unicode=True)
    except Exception:
        pass

    return ApiResponse(success=True, data={"brief_id": brief_id, "status": "frozen"}, message="Brief đã được đóng", language=language)


@router.post("/set-status", response_model=ApiResponse)
async def set_brief_status(request: Request):
    """Set status của brief (draft → analyzed → clarified → frozen).

    Request body: {"version": "v1.0.0", "status": "clarified"}
    """
    language = i18n.get_language_from_request(request)
    body = await request.json()
    version = body.get("version", "v1.0.0")
    new_status = body.get("status", "clarified")

    from midicoder.storage.sqlite import BriefsManager
    mgr = BriefsManager(db_path=_get_project_db_path("briefs.db"))
    mgr.init()

    target = _get_working_brief(mgr, version)
    if not target:
        return ApiResponse(success=False, data=None, message="Không tìm thấy brief", language=language)

    brief_id = target.get("brief_id")
    brief_hash = target.get("hash", "")
    mgr.update_status(brief_id, new_status)
    _log_lineage(mgr, brief_id, version, "status_change", f"Status changed to {new_status}", old_hash=brief_hash, new_hash=brief_hash)

    # Nếu brief được frozen → chuyển status version sang active
    if new_status == "frozen":
        try:
            from midicoder.storage.projects import ProjectsManager
            pm = ProjectsManager()
            pm.init()
            active_project = pm.get_active()
            if active_project:
                pm.version_update_status(active_project["project_id"], version, "inbuild")

            # Cập nhật metadata.yml
            from midicoder.api.config import _get_project_root
            from pathlib import Path
            import yaml
            meta_file = Path(_get_project_root()) / ".midicoder" / "versions" / version / "metadata.yml"
            if meta_file.exists():
                with open(meta_file, "r", encoding="utf-8") as f:
                    meta = yaml.safe_load(f) or {}
                meta["status"] = "inbuild"
                with open(meta_file, "w", encoding="utf-8") as f:
                    yaml.dump(meta, f, default_flow_style=False, allow_unicode=True)
        except Exception:
            pass

    return ApiResponse(success=True, data={"brief_id": brief_id, "status": new_status}, message=f"Brief status: {new_status}", language=language)


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
                    metadata_raw = {}
                    raw_metadata = art.get("metadata")
                    if raw_metadata:
                        if isinstance(raw_metadata, str):
                            metadata_raw = json.loads(raw_metadata)
                        elif isinstance(raw_metadata, dict):
                            metadata_raw = raw_metadata

                    # LLM trả domain/type/scale ở gốc JSON — không phải trong intent object
                    intent = content.get("intent") or {
                        "domain": content.get("domain", ""),
                        "type": content.get("type", "api"),
                        "scale": content.get("scale", "medium"),
                    }

                    # Normalize metadata keys: artifact DB lưu entity_count, command_count...
                    # nhưng frontend template đọc metadata.entities, metadata.commands...
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
