"""
Brief Commands Implementation.

Tất cả business logic của brief nằm ở đây — API router chỉ delegate qua pipeline_bridge.

Lệnh quản lý briefs:
- brief analyze:    Phân tích brief bằng LLM (sync), lưu kết quả vào artifact
- brief analyze-stream: Phân tích brief bằng LLM (streaming cho SSE)
- brief save:       Upsert brief content (tạo mới hoặc cập nhật)
- brief get:        Lấy brief + clarifications + persisted analysis
- brief clarifications: Lấy danh sách Q&A clarifications
- brief revisions:  Lấy lịch sử revisions
- brief revision-diff: Lấy unified diff của revision N so với N-1
- brief freeze:     Đóng brief (status → freezed), version (draft → inbuild)
"""

import difflib
import hashlib
import json
import uuid
from pathlib import Path
from typing import AsyncIterator, Dict, Any, Optional, List

from midicoder.storage.sqlite import (
    BriefsManager,
    ArtifactsManager,
    get_connection,
)
from midicoder.storage.activity import log
from midicoder.pipeline.config import get_config
from midicoder.pipeline.analyze import (
    BriefAnalysis,
    analyze_brief_with_llm_sync,
    analyze_brief_with_llm_stream,
    StreamChunk,
)


# ============================================================================
# Internal helpers
# ============================================================================

def _get_project_db_path(project_cwd: str, db_name: str) -> Path:
    """Lấy explicit path đến database file của project."""
    return Path(project_cwd) / ".midicoder" / "data" / db_name


def _get_active_project_domain() -> str:
    """Lấy domain từ projects.db cho project đang active. Fallback 'default'."""
    try:
        from midicoder.storage.projects import ProjectsManager, DB_PROJECTS
        mgr = ProjectsManager(db_path=DB_PROJECTS)
        mgr.init()
        active = mgr.get_active()
        if active:
            return mgr.get_domain(active["project_id"])
    except Exception:
        pass
    return "default"


def _find_brief(mgr: BriefsManager, version: str) -> Optional[Dict[str, Any]]:
    """Lấy brief duy nhất cho version này."""
    for b in mgr.list(version=version):
        return b
    return None


def _add_revision(
    mgr: BriefsManager,
    brief_id: str,
    version: str,
    event: str,
    diff_summary: str,
    content: str = None,
) -> None:
    """Thêm revision vào brief_revisions table."""
    try:
        mgr.add_revision(brief_id, version, event, diff_summary, content)
    except Exception:
        pass


def _normalize_timestamp(ts: str) -> str:
    """Append 'Z' cho timestamp SQLite để frontend parse đúng UTC."""
    if ts and isinstance(ts, str) and not ts.endswith("Z") and "+" not in ts:
        return ts + "Z"
    return ts


# ============================================================================
# Schema normalization — align LLM output to frontend template expectations
# ============================================================================

def _normalize_entity(e: dict) -> dict:
    """Normalize entity: ensure name, type, description exist for frontend table."""
    return {
        "name": e.get("name", ""),
        "type": e.get("type") or "aggregate",
        "description": e.get("description") or "",
        "fields": e.get("fields") or e.get("attributes", []),
    }


def _normalize_command(c: dict) -> dict:
    """Normalize command: ensure name, target, description exist."""
    return {
        "name": c.get("name", ""),
        "target": c.get("target") or "",
        "description": c.get("description") or "",
        "input": c.get("input", []),
    }


def _normalize_query(q: dict) -> dict:
    """Normalize query: ensure name, entity, filter exist."""
    return {
        "name": q.get("name", ""),
        "entity": q.get("entity") or "",
        "filter": q.get("filter") or "",
        "input": q.get("input", []),
    }


def _normalize_event(ev: dict) -> dict:
    """Normalize event: ensure name, source, description exist."""
    return {
        "name": ev.get("name", ""),
        "source": ev.get("source") or "",
        "description": ev.get("description") or "",
        "fields": ev.get("fields") or ev.get("payload", []),
    }


def _normalize_ui_component(uc: dict) -> dict:
    """Normalize ui_component: ensure name, type, description exist.

    Old schema: {entity_id, component_type} — no name/type/description
    New schema: {name, type, description, entity_id}
    """
    component_type = uc.get("type") or uc.get("component_type") or "data_table"
    entity_id = uc.get("entity_id") or ""

    # If no name provided (old schema), derive from entity_id + component_type
    name = uc.get("name") or ""
    if not name and entity_id:
        type_label = {
            "form_field": "Form",
            "data_table": "Danh sách",
            "card_list": "Danh sách thẻ",
            "dialog": "Động thoại",
            "form_builder": "Form builder",
            "sidebar": "Sidebar",
            "header": "Header",
            "modal": "Modal",
            "notification": "Thông báo",
            "chart": "Biểu đồ",
        }.get(component_type, component_type)
        name = f"{type_label} {entity_id}"

    description = uc.get("description") or ""
    if not description and entity_id:
        type_desc = {
            "form_field": f"Form nhập liệu cho {entity_id}",
            "data_table": f"Bảng hiển thị danh sách {entity_id}",
            "card_list": f"Danh sách thẻ hiển thị {entity_id}",
            "dialog": f"Động thoại xác nhận cho {entity_id}",
        }.get(component_type, f"Component cho {entity_id}")
        description = type_desc

    return {
        "name": name,
        "type": component_type,
        "description": description,
        "entity_id": entity_id,
    }


def _normalize_value_object(vo: dict) -> dict:
    """Normalize value_object: ensure name, description, fields exist."""
    return {
        "name": vo.get("name", ""),
        "description": vo.get("description") or "",
        "fields": vo.get("fields", []),
        "methods": vo.get("methods", []),
    }


def _normalize_guard(g: dict) -> dict:
    """Normalize guard: ensure name, target, type, description exist."""
    return {
        "name": g.get("name", ""),
        "target": g.get("target") or "",
        "type": g.get("type") or "business_rule",
        "description": g.get("description") or "",
    }


def _normalize_workflow(w: dict) -> dict:
    """Normalize workflow: ensure name, description, trigger, steps exist."""
    return {
        "name": w.get("name", ""),
        "description": w.get("description") or "",
        "trigger": w.get("trigger") or w.get("triggers", []),
        "steps": w.get("steps", []),
    }


def _normalize_aggregate(a: dict) -> dict:
    """Normalize aggregate: ensure name, description, root_entity, member_entities exist."""
    return {
        "name": a.get("name", ""),
        "description": a.get("description") or "",
        "root_entity": a.get("root_entity") or a.get("root") or "",
        "member_entities": a.get("member_entities") or a.get("members", []),
    }


def _normalize_role(r: dict) -> dict:
    """Normalize role: ensure name, description, permissions exist."""
    return {
        "name": r.get("name", ""),
        "description": r.get("description") or "",
        "permissions": r.get("permissions", []),
    }


def _normalize_permission(p: dict) -> dict:
    """Normalize permission: ensure name, description, resource, action exist."""
    return {
        "name": p.get("name", ""),
        "description": p.get("description") or "",
        "resource": p.get("resource") or "",
        "action": p.get("action") or "",
    }


def _normalize_state_machine(sm: dict) -> dict:
    """Normalize state_machine: ensure name, entity, states, transitions exist."""
    return {
        "name": sm.get("name", ""),
        "entity": sm.get("entity") or "",
        "states": sm.get("states", []),
        "transitions": sm.get("transitions", []),
    }


def _normalize_ambiguity(amb: dict) -> dict:
    """Normalize ambiguity: ensure summary, question, recommend exist.

    Supports legacy format (description, type, source_text) for backward compat.
    """
    # New format: summary, question, recommend
    if "summary" in amb:
        return {
            "summary": amb.get("summary", ""),
            "question": amb.get("question", ""),
            "recommend": amb.get("recommend", ""),
        }
    # Legacy format: description, type, source_text — convert to new format
    return {
        "summary": amb.get("description", "") or amb.get("source_text", ""),
        "question": f"Vui lòng làm rõ: {amb.get('description', '')}",
        "recommend": "",
    }


ALL_MODULE_TYPES = [
    "entities", "commands", "queries", "events", "ui_components",
    "value_objects", "guards", "workflows", "aggregates",
    "roles", "permissions", "state_machines",
]

NORMALIZE_FN = {
    "entities": _normalize_entity,
    "commands": _normalize_command,
    "queries": _normalize_query,
    "events": _normalize_event,
    "ui_components": _normalize_ui_component,
    "value_objects": _normalize_value_object,
    "guards": _normalize_guard,
    "workflows": _normalize_workflow,
    "aggregates": _normalize_aggregate,
    "roles": _normalize_role,
    "permissions": _normalize_permission,
    "state_machines": _normalize_state_machine,
}


def _extract_module_array(json_data: dict, key: str) -> list:
    """Extract a module array from root level or from a nested 'metadata' dict."""
    val = json_data.get(key)
    if isinstance(val, list):
        return val
    meta = json_data.get("metadata")
    if isinstance(meta, dict):
        mv = meta.get(key)
        if isinstance(mv, list):
            return mv
    return []


def _normalize_analysis_json(json_data: dict) -> dict:
    """Normalize LLM output to match frontend table columns and contract gen expectations.

    Handles both old schema (from cached artifacts) and new schema.
    Normalizes all 12 module types.

    Extracts arrays from root level OR nested 'metadata' dict — LLMs often
    nest module arrays in a metadata wrapper.
    """
    result = dict(json_data)

    for key in ALL_MODULE_TYPES:
        arr = _extract_module_array(result, key)
        if arr:
            fn = NORMALIZE_FN[key]
            result[key] = [fn(item) for item in arr]

    # Normalize ambiguities (not a module type, but needs same treatment)
    raw_amb = result.get("ambiguities", [])
    if not isinstance(raw_amb, list):
        raw_amb = []
    meta = result.get("metadata")
    if isinstance(meta, dict) and not raw_amb:
        raw_amb = meta.get("ambiguities", [])
        if not isinstance(raw_amb, list):
            raw_amb = []
    if raw_amb:
        result["ambiguities"] = [_normalize_ambiguity(a) for a in raw_amb]

    return result


VALID_APP_TYPES = {"web_app", "mobile_app", "api_service", "desktop_app", "cli_tool", "microservice", "saas_platform"}
VALID_SCALES = {"small", "medium", "large"}


def _compute_app_type(json_data: dict) -> str:
    """Infer application type from extracted modules."""
    has_ui = bool(json_data.get("ui_components"))
    has_workflows = bool(json_data.get("workflows"))
    has_state_machines = bool(json_data.get("state_machines"))
    has_roles = bool(json_data.get("roles"))
    entity_count = len(json_data.get("entities", []))

    if has_ui and has_roles and entity_count > 10:
        return "saas_platform"
    elif has_ui and entity_count > 5:
        return "web_app"
    elif has_workflows and has_state_machines:
        return "saas_platform"
    elif entity_count <= 5 and not has_ui:
        return "api_service"
    else:
        return "web_app"


def _compute_scale(json_data: dict) -> str:
    """Infer project scale from total entity count."""
    total = len(json_data.get("entities", []))
    if total <= 5:
        return "small"
    elif total <= 15:
        return "medium"
    else:
        return "large"


def _compute_status(json_data: dict, confidence: float) -> str:
    """Compute analysis status from ambiguities and confidence."""
    ambiguities = json_data.get("ambiguities", [])
    if ambiguities:
        return "needs_clarification"
    elif confidence >= 0.8:
        return "ready_for_contract"
    else:
        return "needs_clarification"


def _extract_root_field(json_data: dict, key: str, default: str = "") -> str:
    """Extract a field from root level or from a nested 'metadata' dict."""
    val = json_data.get(key, default)
    if val:
        return val
    meta = json_data.get("metadata")
    if isinstance(meta, dict):
        return meta.get(key, default)
    return default


def _build_analysis_response(json_data: dict, analysis: BriefAnalysis, brief_id: str) -> dict:
    """Build unified analysis response format cho frontend.

    Extracts fields from multiple locations in json_data since LLMs may nest
    metadata in a 'metadata' dict or spread it at root level.
    """
    # Normalize first — handles old/new schema mismatch
    json_data = _normalize_analysis_json(json_data)

    # Extract all 12 module arrays from root OR nested metadata
    entities = _extract_module_array(json_data, "entities")
    commands = _extract_module_array(json_data, "commands")
    queries = _extract_module_array(json_data, "queries")
    events = _extract_module_array(json_data, "events")
    ui_components = _extract_module_array(json_data, "ui_components")
    value_objects = _extract_module_array(json_data, "value_objects")
    guards = _extract_module_array(json_data, "guards")
    workflows = _extract_module_array(json_data, "workflows")
    aggregates = _extract_module_array(json_data, "aggregates")
    roles = _extract_module_array(json_data, "roles")
    permissions = _extract_module_array(json_data, "permissions")
    state_machines = _extract_module_array(json_data, "state_machines")
    confidence = analysis.confidence

    # Extract from root OR nested metadata dict — LLMs often nest these
    llm_type = _extract_root_field(json_data, "type")
    llm_scale = _extract_root_field(json_data, "scale")
    llm_domain = _extract_root_field(json_data, "domain") or analysis.domain
    llm_summary = _extract_root_field(json_data, "summary") or analysis.text_summary or ""

    # Validate LLM values — fall back to computed if invalid
    app_type = llm_type if llm_type in VALID_APP_TYPES else _compute_app_type(json_data)
    app_scale = llm_scale if llm_scale in VALID_SCALES else _compute_scale(json_data)

    summary = llm_summary
    ambiguities = json_data.get("ambiguities", [])

    # Ensure ambiguities is a proper list — LLMs may return dict or None
    if not isinstance(ambiguities, list):
        ambiguities = []

    # Compute status dynamically
    status = _compute_status(json_data, confidence)

    return {
        "status": status,
        "analysis": {
            "intent": {
                "domain": llm_domain,
                "type": app_type,
                "scale": app_scale,
            },
            "domain": llm_domain,
            "type": app_type,
            "scale": app_scale,
            "ambiguities": ambiguities,
            "summary": summary,
            "entities": entities,
            "commands": commands,
            "queries": queries,
            "events": events,
            "ui_components": ui_components,
            "value_objects": value_objects,
            "guards": guards,
            "workflows": workflows,
            "aggregates": aggregates,
            "roles": roles,
            "permissions": permissions,
            "state_machines": state_machines,
        },
        "metadata": {
            "domain": llm_domain,
            "confidence": confidence,
            "entities": len(entities),
            "commands": len(commands),
            "queries": len(queries),
            "events": len(events),
            "ui_components": len(ui_components),
            "value_objects": len(value_objects),
            "guards": len(guards),
            "workflows": len(workflows),
            "aggregates": len(aggregates),
            "roles": len(roles),
            "permissions": len(permissions),
            "state_machines": len(state_machines),
            "brief_id": brief_id,
        },
    }


def _save_analysis_artifact(
    artifacts_manager: ArtifactsManager,
    artifact_id: str,
    json_data: dict,
    version: str,
    brief_id: str,
    domain: str,
    confidence: float,
    tokens_used: int,
    latency_ms: int,
) -> None:
    """Lưu analysis result vào artifacts (upsert idempotent)."""
    # Extract counts from root OR nested metadata — use same logic as _build_analysis_response
    entities = _extract_module_array(json_data, "entities")
    commands = _extract_module_array(json_data, "commands")
    queries = _extract_module_array(json_data, "queries")
    events = _extract_module_array(json_data, "events")
    ui_components = _extract_module_array(json_data, "ui_components")
    value_objects = _extract_module_array(json_data, "value_objects")
    guards = _extract_module_array(json_data, "guards")
    workflows = _extract_module_array(json_data, "workflows")
    aggregates = _extract_module_array(json_data, "aggregates")
    roles = _extract_module_array(json_data, "roles")
    permissions = _extract_module_array(json_data, "permissions")
    state_machines = _extract_module_array(json_data, "state_machines")

    content_json = json.dumps(json_data, indent=2, ensure_ascii=False)
    artifact_metadata = {
        "domain": domain,
        "confidence": confidence,
        "tokens_used": tokens_used,
        "latency_ms": latency_ms,
        "entity_count": len(entities),
        "command_count": len(commands),
        "query_count": len(queries),
        "event_count": len(events),
        "ui_component_count": len(ui_components),
        "value_object_count": len(value_objects),
        "guard_count": len(guards),
        "workflow_count": len(workflows),
        "aggregate_count": len(aggregates),
        "role_count": len(roles),
        "permission_count": len(permissions),
        "state_machine_count": len(state_machines),
    }

    existing = artifacts_manager.get(artifact_id)
    if existing:
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

    log("artifact.saved", resource_type="artifact", resource_id=artifact_id, details={"artifact_type": "analysis"})


# ============================================================================
# Public pipeline functions — callable từ pipeline_bridge
# ============================================================================


def save_brief(project_cwd: str, version: str, brief_content: str, change_description: str = "Auto-save") -> dict:
    """
    Upsert brief cho version. Tạo mới nếu chưa có, cập nhật + log revision nếu đã tồn tại.

    Args:
        project_cwd: Absolute path đến project root
        version: Version name (vd: "v1.0.0")
        brief_content: Nội dung brief
        change_description: Mô tả thay đổi

    Returns:
        {"brief_id": str, "updated": bool}

    Raises:
        ValueError: Nếu brief đã freezed
    """
    briefs_db = _get_project_db_path(project_cwd, "briefs.db")
    mgr = BriefsManager(db_path=briefs_db)
    mgr.init()

    existing = _find_brief(mgr, version)
    content_hash = hashlib.sha256(brief_content.encode("utf-8")).hexdigest()

    if existing:
        brief_id = existing.get("brief_id")
        if existing.get("status") == "freezed":
            raise ValueError("Brief đã được đóng băng, không thể chỉnh sửa")

        old_hash = existing.get("content_hash", "")
        with mgr._get_connection() as conn:
            conn.execute(
                "UPDATE briefs SET content = ?, content_hash = ?, title = ?, updated_at = datetime('now') WHERE brief_id = ?",
                (brief_content, content_hash, existing.get("title", ""), brief_id),
            )
        _add_revision(mgr, brief_id, version, "content_updated", change_description, brief_content)
        log("brief.updated", resource_type="brief", resource_id=brief_id)
        return {"brief_id": brief_id, "updated": True}
    else:
        brief_id = f"brief-{uuid.uuid4().hex[:8]}"
        title = brief_content.split("\n")[0].strip()[:100] or ""
        try:
            mgr.create(
                brief_id=brief_id,
                version=version,
                content=brief_content,
                title=title or "Untitled",
            )
            _add_revision(mgr, brief_id, version, "created", "Brief created", brief_content)
            log("brief.created", resource_type="brief", resource_id=brief_id)
            return {"brief_id": brief_id, "updated": False}
        except Exception:
            return {"brief_id": None, "updated": False}


def analyze_brief_for_api(project_cwd: str, version: str, language: str = "vi") -> dict:
    """
    Phân tích brief bằng LLM (sync) — dùng cho POST /brief/analyze.

    Args:
        project_cwd: Absolute path đến project root
        version: Version name
        language: Mã ngôn ngữ (vi, en) — inject vào prompt template

    Returns:
        {"success": bool, "data": dict or None, "error": str or None}
    """
    briefs_db = _get_project_db_path(project_cwd, "briefs.db")
    briefs_manager = BriefsManager(db_path=briefs_db)
    briefs_manager.init()

    brief = _find_brief(briefs_manager, version)
    if not brief:
        return {"success": False, "data": None, "error": "not_found"}

    brief_id = brief.get("brief_id")
    brief_status = brief.get("status", "draft")
    brief_content = brief.get("content", "")

    if brief_status != "draft":
        return {"success": False, "data": None, "error": f"blocked_status:{brief_status}"}

    if not brief_content.strip():
        return {"success": False, "data": None, "error": "empty_content"}

    domain = _get_active_project_domain()

    try:
        analysis = analyze_brief_with_llm_sync(
            brief_content=brief_content,
            domain=domain,
            brief_id=brief_id,
            language=language,
        )
    except Exception as e:
        return {"success": False, "data": None, "error": f"llm_failed:{str(e)}"}

    # Save artifact
    artifacts_db = _get_project_db_path(project_cwd, "artifacts.db")
    artifacts_manager = ArtifactsManager(db_path=artifacts_db)
    artifacts_manager.init()
    _save_analysis_artifact(
        artifacts_manager,
        f"analysis-{brief_id}",
        analysis.json_data,
        version,
        brief_id,
        analysis.domain,
        analysis.confidence,
        analysis.tokens_used,
        analysis.latency_ms,
    )

    response_data = _build_analysis_response(analysis.json_data, analysis, brief_id)

    return {"success": True, "data": response_data, "error": None}


async def analyze_brief_stream_for_api(project_cwd: str, version: str, language: str = "vi") -> AsyncIterator[Dict[str, Any]]:
    """
    Async generator cho SSE streaming — dùng cho GET /brief/analyze-stream.

    Yields dict with keys: "event" (str) and "data" (str|dict).

    Args:
        project_cwd: Absolute path đến project root
        version: Version name
        language: Mã ngôn ngữ (vi, en) — inject vào prompt template

    Raises:
        ValueError: {"code": "not_found" | "blocked_status:{status}" | "empty_content"}
    """
    briefs_db = _get_project_db_path(project_cwd, "briefs.db")
    briefs_manager = BriefsManager(db_path=briefs_db)
    briefs_manager.init()

    brief = _find_brief(briefs_manager, version)
    if not brief:
        raise ValueError({"code": "not_found"})

    brief_id = brief.get("brief_id")
    brief_status = brief.get("status", "draft")
    brief_content = brief.get("content", "")

    if brief_status != "draft":
        raise ValueError({"code": f"blocked_status:{brief_status}"})

    if not brief_content.strip():
        raise ValueError({"code": "empty_content"})

    domain = _get_active_project_domain()

    # Yield started event
    yield {
        "event": "started",
        "data": {
            "brief_id": brief_id,
            "version": version,
            "brief_length": len(brief_content),
        },
    }

    # Stream LLM analysis
    json_data = None
    analysis_domain = domain
    analysis_confidence = 0.5
    analysis_tokens = 0
    analysis_latency = 0

    try:
        async for chunk in analyze_brief_with_llm_stream(
            brief_content=brief_content,
            domain=domain,
            brief_id=brief_id,
            language=language,
        ):
            data = chunk.data if isinstance(chunk.data, dict) else str(chunk.data)
            if chunk.accumulated:
                data = {"data": data, "accumulated": chunk.accumulated}
            yield {"event": chunk.type, "data": data}

            if chunk.type == "complete" and isinstance(chunk.data, dict):
                json_data = chunk.data.get("json_data")
                analysis_domain = chunk.data.get("domain", domain)
                analysis_confidence = chunk.data.get("confidence", 0.5)
                analysis_tokens = chunk.data.get("tokens_used", 0)
                analysis_latency = chunk.data.get("latency_ms", 0)

    except Exception as e:
        yield {"event": "error", "data": str(e)}
        return

    # Save artifact + yield final_result
    if json_data:
        artifacts_db = _get_project_db_path(project_cwd, "artifacts.db")
        artifacts_manager = ArtifactsManager(db_path=artifacts_db)
        artifacts_manager.init()
        _save_analysis_artifact(
            artifacts_manager,
            f"analysis-{brief_id}",
            json_data,
            version,
            brief_id,
            analysis_domain,
            analysis_confidence,
            analysis_tokens,
            analysis_latency,
        )

        yield {
            "event": "final_result",
            "data": _build_analysis_response(json_data, BriefAnalysis(
                json_data=json_data,
                text_summary=json_data.get("summary", ""),
                domain=analysis_domain,
                confidence=analysis_confidence,
                tokens_used=analysis_tokens,
                latency_ms=analysis_latency,
            ), brief_id),
        }


def get_brief_for_api(project_cwd: str, version: str) -> dict:
    """
    Lấy brief + clarifications + persisted analysis — dùng cho GET /brief/get.

    Args:
        project_cwd: Absolute path đến project root
        version: Version name

    Returns:
        {"success": bool, "data": dict or None, "error": str or None}
    """
    try:
        briefs_db = _get_project_db_path(project_cwd, "briefs.db")
        mgr = BriefsManager(db_path=briefs_db)
        mgr.init()

        brief = _find_brief(mgr, version)
        if not brief:
            return {"success": False, "data": None, "error": "not_found"}

        brief_id = brief.get("brief_id")
        clarifications = mgr.get_clarifications(brief_id)

        # Load persisted analysis from artifacts
        analysis_data = None
        try:
            artifacts_db = _get_project_db_path(project_cwd, "artifacts.db")
            artifacts_mgr = ArtifactsManager(db_path=artifacts_db)
            artifacts_mgr.init()
            for art in artifacts_mgr.list(artifact_type="analysis", brief_id=brief_id):
                try:
                    content = json.loads(art.get("content") or "{}")

                    # Normalize schema — handles old cached artifacts
                    content = _normalize_analysis_json(content)

                    metadata_raw = {}
                    raw_metadata = art.get("metadata")
                    if raw_metadata:
                        if isinstance(raw_metadata, str):
                            metadata_raw = json.loads(raw_metadata)
                        elif isinstance(raw_metadata, dict):
                            metadata_raw = raw_metadata

                    intent = content.get("intent") or {
                        "domain": content.get("domain", ""),
                        "type": content.get("type"),
                        "scale": content.get("scale"),
                    }

                    # Extract from root OR nested metadata dict — LLMs often nest these
                    persisted_type_raw = intent.get("type") or _extract_root_field(content, "type")
                    persisted_scale_raw = intent.get("scale") or _extract_root_field(content, "scale")
                    persisted_domain = intent.get("domain") or _extract_root_field(content, "domain")

                    # Validate — fall back to computed if invalid
                    persisted_type = persisted_type_raw if persisted_type_raw in VALID_APP_TYPES else _compute_app_type(content)
                    persisted_scale = persisted_scale_raw if persisted_scale_raw in VALID_SCALES else _compute_scale(content)
                    persisted_confidence = metadata_raw.get("confidence", 0.5)

                    # Ensure ambiguities is a list and normalize format (old → new)
                    persisted_ambiguities = content.get("ambiguities", [])
                    if not isinstance(persisted_ambiguities, list):
                        persisted_ambiguities = []
                    persisted_ambiguities = [_normalize_ambiguity(a) for a in persisted_ambiguities]

                    persisted_status = _compute_status(content, persisted_confidence)

                    # Compute counts from actual arrays — metadata_raw may be stale (old artifact)
                    persisted_entities = _extract_module_array(content, "entities")
                    persisted_commands = _extract_module_array(content, "commands")
                    persisted_queries = _extract_module_array(content, "queries")
                    persisted_events = _extract_module_array(content, "events")
                    persisted_ui = _extract_module_array(content, "ui_components")
                    persisted_vo = _extract_module_array(content, "value_objects")
                    persisted_guards = _extract_module_array(content, "guards")
                    persisted_workflows = _extract_module_array(content, "workflows")
                    persisted_aggregates = _extract_module_array(content, "aggregates")
                    persisted_roles = _extract_module_array(content, "roles")
                    persisted_permissions = _extract_module_array(content, "permissions")
                    persisted_sm = _extract_module_array(content, "state_machines")

                    normalized_metadata = {
                        "domain": persisted_domain or metadata_raw.get("domain", ""),
                        "confidence": persisted_confidence,
                        "entities": len(persisted_entities),
                        "commands": len(persisted_commands),
                        "queries": len(persisted_queries),
                        "events": len(persisted_events),
                        "ui_components": len(persisted_ui),
                        "value_objects": len(persisted_vo),
                        "guards": len(persisted_guards),
                        "workflows": len(persisted_workflows),
                        "aggregates": len(persisted_aggregates),
                        "roles": len(persisted_roles),
                        "permissions": len(persisted_permissions),
                        "state_machines": len(persisted_sm),
                        "brief_id": brief_id,
                    }

                    analysis_data = {
                        "status": persisted_status,
                        "analysis": {
                            "intent": {
                                "domain": persisted_domain,
                                "type": persisted_type,
                                "scale": persisted_scale,
                            },
                            "domain": persisted_domain,
                            "type": persisted_type,
                            "scale": persisted_scale,
                            "ambiguities": persisted_ambiguities,
                            "summary": _extract_root_field(content, "summary"),
                            "entities": persisted_entities,
                            "commands": persisted_commands,
                            "queries": persisted_queries,
                            "events": persisted_events,
                            "ui_components": persisted_ui,
                            "value_objects": persisted_vo,
                            "guards": persisted_guards,
                            "workflows": persisted_workflows,
                            "aggregates": persisted_aggregates,
                            "roles": persisted_roles,
                            "permissions": persisted_permissions,
                            "state_machines": persisted_sm,
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

        return {
            "success": True,
            "data": {
                "brief_id": brief_id,
                "version": brief.get("version"),
                "status": brief.get("status", "draft"),
                "title": brief.get("title", ""),
                "content": brief.get("content", ""),
                "clarifications": clarifications,
                "analysis": analysis_data,
                "created_at": _normalize_timestamp(brief.get("created_at", "")),
                "updated_at": _normalize_timestamp(brief.get("updated_at", "")),
            },
            "error": None,
        }
    except Exception as e:
        return {"success": False, "data": None, "error": str(e)}


def get_clarifications_for_api(project_cwd: str, version: str) -> dict:
    """
    Lấy clarifications cho brief của version.

    Args:
        project_cwd: Absolute path đến project root
        version: Version name

    Returns:
        {"success": bool, "data": {"clarifications": list, "count": int}, "error": str or None}
    """
    try:
        briefs_db = _get_project_db_path(project_cwd, "briefs.db")
        mgr = BriefsManager(db_path=briefs_db)
        mgr.init()

        brief = _find_brief(mgr, version)
        if not brief:
            return {"success": True, "data": {"clarifications": [], "count": 0}, "error": None}

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
                "created_at": _normalize_timestamp(c.get("created_at", "")),
            })
        cl_list.sort(key=lambda x: x.get("round", 0))

        return {"success": True, "data": {"clarifications": cl_list, "count": len(cl_list)}, "error": None}
    except Exception as e:
        return {"success": False, "data": None, "error": str(e)}


def get_revisions_for_api(project_cwd: str, version: str) -> dict:
    """
    Lấy lịch sử revisions của brief.

    Args:
        project_cwd: Absolute path đến project root
        version: Version name

    Returns:
        {"success": bool, "data": {"revisions": list, "count": int}, "error": str or None}
    """
    try:
        briefs_db = _get_project_db_path(project_cwd, "briefs.db")
        mgr = BriefsManager(db_path=briefs_db)
        mgr.init()

        brief = _find_brief(mgr, version)
        if not brief:
            return {"success": True, "data": {"revisions": [], "count": 0}, "error": None}

        brief_id = brief.get("brief_id")
        revisions = mgr.get_revisions(brief_id)

        for rev in revisions:
            ts = rev.get("created_at", "")
            rev["created_at"] = _normalize_timestamp(ts)

        return {"success": True, "data": {"revisions": revisions, "count": len(revisions)}, "error": None}
    except Exception as e:
        return {"success": False, "data": None, "error": str(e)}


def get_revision_diff_for_api(project_cwd: str, version: str, revision_number: int) -> dict:
    """
    Lấy unified diff của revision N so với revision N-1.

    Args:
        project_cwd: Absolute path đến project root
        version: Version name
        revision_number: Số revision (1-based)

    Returns:
        {"success": bool, "data": dict, "error": str or None}
    """
    try:
        briefs_db = _get_project_db_path(project_cwd, "briefs.db")
        mgr = BriefsManager(db_path=briefs_db)
        mgr.init()

        brief = _find_brief(mgr, version)
        if not brief:
            return {
                "success": True,
                "data": {"diff_text": "", "stats": {"added": 0, "removed": 0}},
                "error": None,
            }

        brief_id = brief.get("brief_id")
        revisions = mgr.get_revisions(brief_id)

        current_rev = None
        prev_rev = None
        for rev in revisions:
            if rev["revision_number"] == revision_number:
                current_rev = rev
                break

        if not current_rev:
            return {"success": False, "data": None, "error": "revision_not_found"}

        for rev in revisions:
            if rev["revision_number"] == revision_number - 1:
                prev_rev = rev
                break

        current_content = current_rev.get("content_snapshot") or ""
        prev_content = prev_rev.get("content_snapshot") or "" if prev_rev else ""

        current_lines = current_content.splitlines(keepends=True)
        prev_lines = prev_content.splitlines(keepends=True)

        diff = list(difflib.unified_diff(
            prev_lines, current_lines,
            fromfile=f"v{revision_number - 1}",
            tofile=f"v{revision_number}",
            lineterm="",
        ))
        diff_text = "\n".join(diff) if diff else ""

        added = sum(1 for line in diff if line.startswith("+") and not line.startswith("+++"))
        removed = sum(1 for line in diff if line.startswith("-") and not line.startswith("---"))

        return {
            "success": True,
            "data": {
                "revision_number": revision_number,
                "event": current_rev.get("event"),
                "diff_summary": current_rev.get("diff_summary"),
                "diff_text": diff_text,
                "stats": {"added": added, "removed": removed, "total": added + removed},
                "has_diff": added > 0 or removed > 0,
            },
            "error": None,
        }
    except Exception as e:
        return {"success": False, "data": None, "error": str(e)}


# ============================================================================
# CLI commands (giữ nguyên cho backward compatibility)
# ============================================================================

def _analyze_with_llm(
    brief_content: str,
    domain: Optional[str],
    brief_id: str,
) -> BriefAnalysis:
    """CLI wrapper cho analyze_brief_with_llm_sync — thêm activity log output."""
    effective_domain = domain if domain else "default"
    log("brief.analyzing", resource_type="brief", resource_id=brief_id, details={"domain": effective_domain})
    try:
        analysis = analyze_brief_with_llm_sync(
            brief_content=brief_content,
            domain=effective_domain,
            brief_id=brief_id,
        )
    except Exception as e:
        log("llm.failed", resource_type="brief", resource_id=brief_id, details={"error": str(e)}, status="error")
        raise

    log("brief.analyzed", resource_type="brief", resource_id=brief_id, details={
        "domain": analysis.domain,
        "tokens_used": analysis.tokens_used,
        "latency_ms": analysis.latency_ms,
        "confidence": analysis.confidence,
    })
    log("brief.json_parsed", resource_type="brief", resource_id=brief_id)

    return analysis


def _execute_analyze(domain: Optional[str] = None, force: bool = False) -> None:
    """Thực thi phân tích brief — CLI path."""
    log("brief.analyze_started", resource_type="brief", details={"domain": domain})

    config = get_config()
    active_version = config.get("active_version")

    if not active_version:
        log("config.missing_active_version", resource_type="brief", status="error", details={"error": "Không tìm thấy active_version"})
        raise SystemExit(1)

    versions_dir = Path(".midicoder/versions") / active_version
    brief_file = versions_dir / "brief.md"

    if not brief_file.exists():
        log("brief.file_not_found", resource_type="brief", status="error", details={"path": str(brief_file)})
        raise SystemExit(1)

    content = brief_file.read_text(encoding="utf-8")
    log("brief.file_read", resource_type="brief", details={"path": str(brief_file), "version": active_version, "size": len(content)})

    briefs_manager = BriefsManager()
    briefs_manager.init()

    existing = None
    for brief in briefs_manager.list():
        if brief.get("source_file") == str(brief_file.absolute()):
            existing = brief
            break

    if existing:
        if force:
            log("brief.overriding_existing", resource_type="brief", resource_id=existing.get("brief_id"), details={"reason": "--force"})
        else:
            log("brief.skipped_existing", resource_type="brief", resource_id=existing.get("brief_id"), details={"reason": "already exists, use --force"})
            return

    brief_id = f"brief-{uuid.uuid4().hex[:8]}"
    version = "v1.0.0"
    title = content.split("\n")[0].replace("#", "").strip() or brief_file.stem

    record = briefs_manager.create(
        brief_id=brief_id,
        version=version,
        content=content,
        title=title,
    )

    briefs_manager.add_revision(brief_id, version, "created", "Brief created", content)
    log("brief.created", resource_type="brief", resource_id=brief_id, details={"status": record["status"]})

    log("llm.analysis_started", resource_type="brief", resource_id=brief_id)

    try:
        analysis = _analyze_with_llm(
            brief_content=content,
            domain=domain,
            brief_id=brief_id,
        )

        briefs_manager.add_revision(brief_id, version, "analyzed", "LLM analysis completed", content)

        artifacts_manager = ArtifactsManager()
        artifacts_manager.init()
        artifacts_manager.create(
            artifact_id=f"analysis-{brief_id}",
            artifact_type="analysis",
            name="Brief Analysis",
            version=version,
            brief_id=brief_id,
            content=json.dumps(analysis.json_data, indent=2, ensure_ascii=False),
            metadata={
                "domain": analysis.domain,
                "confidence": analysis.confidence,
                "tokens_used": analysis.tokens_used,
                "latency_ms": analysis.latency_ms,
                "summary": analysis.text_summary,
            },
        )

        log("artifact.saved", resource_type="artifact", resource_id=f"analysis-{brief_id}", details={"artifact_type": "analysis"})
        log("brief.analysis_summary", resource_type="brief", resource_id=brief_id, details={"summary": analysis.text_summary})

    except Exception as e:
        log("llm.analysis_failed", resource_type="brief", resource_id=brief_id, details={"error": str(e)}, status="error")
        raise SystemExit(1)

    log("brief.analyze_completed", resource_type="brief", resource_id=brief_id)


def freeze_brief(version: str, project_cwd: str) -> dict:
    """
    Đóng brief: brief status → freezed, version status draft → inbuild.

    Ghi đồng bộ vào:
    - briefs.db: brief status → freezed
    - projects.db: version status → inbuild
    - .midicoder/versions/{v}/metadata.yml: status → inbuild

    Args:
        version: Version name (vd: "v1.0.0")
        project_cwd: Absolute path đến project root

    Returns:
        dict: {brief_id, status} nếu thành công

    Raises:
        ValueError: Nếu không tìm thấy brief hoặc brief đã freezed
    """
    briefs_db = Path(project_cwd) / ".midicoder" / "data" / "briefs.db"

    briefs_manager = BriefsManager(db_path=briefs_db)
    briefs_manager.init()

    target = None
    for b in briefs_manager.list(version=version):
        target = b
        break

    if not target:
        raise ValueError("Không tìm thấy brief")

    if target.get("status") == "freezed":
        raise ValueError("Brief đã được đóng băng rồi")

    brief_id = target.get("brief_id")

    # 1. Update brief status in briefs.db
    briefs_manager.update_status(brief_id, "freezed")
    log("brief.freezed", resource_type="brief", resource_id=brief_id, details={"brief_id": brief_id})

    # 2. Record revision lineage
    try:
        briefs_manager.add_revision(brief_id, version, "freezed", "Brief freezed, version → inbuild", "")
    except Exception:
        pass

    # 3. Update version status in projects.db (SQLite)
    try:
        from midicoder.storage.projects import ProjectsManager
        pm = ProjectsManager()
        pm.init()
        active_project = pm.get_active()
        if active_project:
            pm.version_update_status(active_project["project_id"], version, "inbuild")
            log("version.status_changed", resource_type="version", resource_id=version, details={"from": "draft", "to": "inbuild", "source": "sqlite"})
    except Exception:
        pass

    # 4. Update metadata.yml (filesystem) — SQLite là nguồn sự thật, sync ra file
    try:
        import yaml as _yaml
        meta_file = Path(project_cwd) / ".midicoder" / "versions" / version / "metadata.yml"
        if meta_file.exists():
            with open(meta_file, "r", encoding="utf-8") as f:
                meta = _yaml.safe_load(f) or {}
            meta["status"] = "inbuild"
            with open(meta_file, "w", encoding="utf-8") as f:
                _yaml.dump(meta, f, default_flow_style=False, allow_unicode=True)
            log("version.status_synced", resource_type="version", resource_id=version, details={"source": "metadata.yml"})
    except Exception:
        pass

    log("brief.freeze_completed", resource_type="brief", resource_id=brief_id, details={"version": version})

    return {"brief_id": brief_id, "status": "freezed"}
