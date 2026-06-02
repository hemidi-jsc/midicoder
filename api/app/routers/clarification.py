"""
Router cho clarification Q&A sessions.

Reuse logic từ midicoder.pipeline.commands.brief:
- _generate_clarification_question() — LLM generate question
- _save_clarification() — lưu Q&A vào SQLite
- _convert_to_master_brief() — convert working→master
"""

import uuid
from pathlib import Path

from pydantic import BaseModel, Field
from fastapi import Query, Request

from app.i18n import i18n
from app.models import ApiResponse

# Lazy import CLI functions — tránh import CLI khi app startup
_generate_clarification_question = None
_save_clarification = None
_convert_to_master_brief = None


def _get_cli_functions():
    """Lazy import CLI functions từ brief.py"""
    global _generate_clarification_question, _save_clarification, _convert_to_master_brief
    if _generate_clarification_question is None:
        from midicoder.pipeline.commands.brief import (
            _generate_clarification_question as _gcq,
            _save_clarification as _sc,
            _convert_to_master_brief as _cmb,
        )
        _generate_clarification_question = _gcq
        _save_clarification = _sc
        _convert_to_master_brief = _cmb


def _get_project_db_path(db_name: str) -> Path:
    """Lấy explicit path đến database file của project."""
    from app.config import get_project_cwd
    project_cwd = Path(get_project_cwd())
    return project_cwd / ".midicoder" / "data" / db_name


def _get_session_store():
    """In-memory session store cho clarification sessions.

    Format: {session_id: {brief_id, analysis_data, qa_history, round, domain}}
    """
    if not hasattr(_get_session_store, "_store"):
        _get_session_store._store = {}
    return _get_session_store._store


from fastapi import APIRouter

router = APIRouter(prefix="/clarification", tags=["Clarification"])


class ClarificationStartRequest(BaseModel):
    version: str = Field(default="v1.0.0", description="Version name")
    non_interactive: bool = Field(default=False, description="Skip if no brief found")


class ClarificationAnswersRequest(BaseModel):
    session_id: str = Field(..., description="Session ID từ /start")
    answers: list[dict] = Field(
        ...,
        description="List of {question_id, values[], notes?}",
    )


@router.post("/start", response_model=ApiResponse)
async def start_clarification(
    request_data: ClarificationStartRequest = None,
    request: Request = None,
):
    """
    Bắt đầu clarification session.

    Process:
    1. Tìm working-brief có analysis artifact
    2. Load analysis JSON từ artifacts
    3. Gọi _generate_clarification_question() để lấy câu hỏi đầu tiên
    4. Tạo session + trả về câu hỏi

    Request body: {"version": "v1.0.0"}
    """
    if request_data is None:
        request_data = ClarificationStartRequest()

    language = i18n.get_language_from_request(request)
    version = request_data.version or "v1.0.0"

    _get_cli_functions()

    from midicoder.storage.sqlite import BriefsManager, ArtifactsManager
    from midicoder.pipeline.llm import load_llm_config

    briefs_manager = BriefsManager(db_path=_get_project_db_path("briefs.db"))
    briefs_manager.init()

    artifacts_manager = ArtifactsManager(db_path=_get_project_db_path("artifacts.db"))
    artifacts_manager.init()

    # Bước 1: Tìm working-brief có analysis artifact
    active_brief = None
    for brief in briefs_manager.list(version=version):
        if brief.get("type") == "working":
            bid = brief.get("brief_id")
            for art in artifacts_manager.list(artifact_type="analysis", brief_id=bid):
                active_brief = brief
                break
        if active_brief:
            break

    if not active_brief:
        return ApiResponse(
            success=False,
            data=None,
            message="Không tìm thấy working brief đã analyze. Cần chạy brief analyze trước.",
            language=language,
        )

    # Bước 2: Load analysis JSON từ artifacts
    try:
        analysis_record = artifacts_manager.get(artifact_id=f"analysis-{active_brief.get('brief_id')}")
        if not analysis_record or not analysis_record.get("content"):
            return ApiResponse(
                success=False,
                data=None,
                message="Không tìm thấy analysis artifact. Cần chạy brief analyze trước.",
                language=language,
            )

        import json
        analysis_data = json.loads(analysis_record.get("content", "{}"))
    except Exception as e:
        return ApiResponse(
            success=False,
            data=None,
            message=f"Lỗi load analysis: {str(e)}",
            language=language,
        )

    # Bước 3: Load LLM config + generate câu hỏi đầu tiên
    try:
        llm_config = load_llm_config()
    except Exception as e:
        return ApiResponse(
            success=False,
            data=None,
            message=f"Lỗi load LLM config: {str(e)}",
            language=language,
        )

    domain = active_brief.get("domain", "generic")
    qa_history = []

    # Generate câu hỏi đầu tiên (reuse CLI function)
    needs_more, question_text = _generate_clarification_question(
        analysis_data=analysis_data,
        qa_history=qa_history,
        llm_config=llm_config,
        domain=domain,
    )

    if not needs_more:
        # Đã đủ rõ, tự động convert → master
        _convert_to_master_brief(briefs_manager, active_brief.get("brief_id"))

        return ApiResponse(
            success=True,
            data={
                "status": "ready",
                "clarification_id": None,
                "message": "Brief đã đủ rõ, không cần clarify thêm",
            },
            message="Brief đã đủ rõ",
            language=language,
        )

    # Bước 4: Tạo session
    session_id = f"clarify-{uuid.uuid4().hex[:8]}"
    store = _get_session_store()
    store[session_id] = {
        "brief_id": active_brief.get("brief_id"),
        "version": version,
        "domain": domain,
        "analysis_data": analysis_data,
        "qa_history": qa_history,
        "round": 1,
        "max_rounds": 10,
    }

    # Build question object cho frontend
    question_obj = {
        "id": f"q-{session_id}-1",
        "source_text": question_text[:200],
        "ambiguity_type": "general",
        "question": question_text,
        "required": True,
        "type": "text",
    }

    return ApiResponse(
        success=True,
        data={
            "clarification_id": session_id,
            "status": "questions_ready",
            "round": 1,
            "questions": [question_obj],
        },
        message="Clarification session bắt đầu",
        language=language,
    )


@router.post("/answers", response_model=ApiResponse)
async def submit_clarification_answers(
    request_data: ClarificationAnswersRequest = None,
    request: Request = None,
):
    """
    Gửi câu trả lời clarification.

    Process:
    1. Load session từ store
    2. Lưu Q&A vào SQLite (_save_clarification)
    3. Generate câu hỏi tiếp theo (_generate_clarification_question)
    4. Nếu LLM nói done → convert → master-brief

    Request body: {"session_id": "...", "answers": [{"question_id": "...", "values": ["..."], "notes": "..."}]}
    """
    if request_data is None:
        return ApiResponse(
            success=False,
            data=None,
            message="Request body cần session_id và answers",
            language="vi",
        )

    language = i18n.get_language_from_request(request)
    session_id = request_data.session_id
    answers = request_data.answers

    _get_cli_functions()

    store = _get_session_store()
    session = store.get(session_id)

    if not session:
        return ApiResponse(
            success=False,
            data=None,
            message="Session không tồn tại hoặc đã hết hạn. Cần start clarification lại.",
            language=language,
        )

    from midicoder.storage.sqlite import BriefsManager
    from midicoder.pipeline.llm import load_llm_config

    briefs_manager = BriefsManager(db_path=_get_project_db_path("briefs.db"))
    briefs_manager.init()

    brief_id = session["brief_id"]
    qa_history = session["qa_history"]
    round_num = session["round"]

    # Extract answer text từ frontend answers format
    for ans in answers:
        values = ans.get("values", [])
        notes = ans.get("notes", "")
        answer_text = "; ".join(values) if values else notes

        if not answer_text.strip():
            continue

        # Lưu Q&A vào SQLite (reuse CLI function)
        _save_clarification(
            briefs_manager=briefs_manager,
            brief_id=brief_id,
            round_num=round_num,
            question=ans.get("question_id", f"Question {round_num}"),
            answer=answer_text,
        )

        qa_history.append({
            "question": ans.get("question_id", f"Question {round_num}"),
            "answer": answer_text,
        })

    # Generate câu hỏi tiếp theo
    llm_config = load_llm_config()
    needs_more, next_question = _generate_clarification_question(
        analysis_data=session["analysis_data"],
        qa_history=qa_history,
        llm_config=llm_config,
        domain=session["domain"],
    )

    session["qa_history"] = qa_history
    session["round"] = round_num + 1

    if not needs_more:
        # Đã đủ rõ → convert → master-brief + update status
        _convert_to_master_brief(briefs_manager, brief_id)
        briefs_manager.update_status(brief_id, "clarified")

        # Cleanup session
        del store[session_id]

        return ApiResponse(
            success=True,
            data={
                "status": "ready",
                "message": f"Clarification hoàn tất sau {round_num} rounds",
                "total_rounds": round_num,
            },
            message="Clarification hoàn tất, brief đã chuyển sang master",
            language=language,
        )

    # Còn câu hỏi tiếp theo
    question_obj = {
        "id": f"q-{session_id}-{round_num + 1}",
        "source_text": next_question[:200],
        "ambiguity_type": "general",
        "question": next_question,
        "required": True,
        "type": "text",
    }

    return ApiResponse(
        success=True,
        data={
            "status": "more_questions",
            "clarification_id": session_id,
            "round": round_num + 1,
            "questions": [question_obj],
        },
        message="Câu trả lời đã được lưu, còn câu hỏi tiếp theo",
        language=language,
    )


@router.get("/status/{session_id}", response_model=ApiResponse)
async def get_clarification_status(
    session_id: str,
    request: Request = None,
):
    """
    Lấy trạng thái clarification session.

    GET /clarification/status/{session_id}
    """
    language = i18n.get_language_from_request(request)
    store = _get_session_store()
    session = store.get(session_id)

    if not session:
        # Kiểm tra xem brief đã chuyển sang master chưa (session đã clean)
        from midicoder.storage.sqlite import BriefsManager
        mgr = BriefsManager(db_path=_get_project_db_path("briefs.db"))
        mgr.init()
        for b in mgr.list():
            if b.get("brief_id") == session_id:
                return ApiResponse(
                    success=True,
                    data={
                        "status": "completed",
                        "brief_status": b.get("status"),
                    },
                    language=language,
                )

        return ApiResponse(
            success=False,
            data=None,
            message="Session không tồn tại",
            language=language,
        )

    return ApiResponse(
        success=True,
        data={
            "status": "in_progress",
            "clarification_id": session_id,
            "round": session["round"],
            "total_answers": len(session["qa_history"]),
            "brief_id": session["brief_id"],
        },
        language=language,
    )
