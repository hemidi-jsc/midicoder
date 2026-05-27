"""
MCP-E: SQLite Tools.

Cung cấp 3 MCP tools:
- get_active_brief: Lấy active brief từ SQLite database
- get_clarifications: Lấy clarifications cho một brief
- list_artifacts: List tất cả artifacts (contracts, generated files) cho brief

Source: midicoder.storage.sqlite (BriefsManager, ArtifactsManager)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from midicoder.errors import MidicoderErrorManager as EM, ErrorCode

logger = logging.getLogger(__name__)


def _get_briefs_manager():
    """Lấy BriefsManager instance."""
    from midicoder.storage.sqlite import BriefsManager, DB_BRIEFS

    return BriefsManager(DB_BRIEFS)


def _get_artifacts_manager():
    """Lấy ArtifactsManager instance."""
    from midicoder.storage.sqlite import ArtifactsManager, DB_ARTIFACTS

    return ArtifactsManager(DB_ARTIFACTS)


# ============================================================================
# MCP Tool: get_active_brief
# ============================================================================


def get_active_brief() -> Dict[str, Any]:
    """
    Lấy active brief hiện tại từ SQLite database.

    Logic:
    1. Kiểm tra .midicoder/active_brief file (nếu có)
    2. Fallback: lấy brief mới nhất từ database
    3. Fallback: lấy brief đầu tiên

    Returns:
        Dictionary với:
        - found: True nếu tìm thấy active brief
        - brief: full brief record (brief_id, version, title, content, status, ...)
        - brief_id: ID của brief
        - fallback_used: True nếu dùng fallback method

    Raises:
        MidicoderError: Nếu không thể kết nối database
    """
    # 1. Kiểm tra active_brief file
    active_brief_file = Path(".midicoder/active_brief")
    fallback_used = False

    if active_brief_file.exists():
        try:
            brief_id = active_brief_file.read_text().strip()
            mgr = _get_briefs_manager()
            brief = mgr.get(brief_id)
            if brief:
                return {
                    "found": True,
                    "brief": brief,
                    "brief_id": brief_id,
                    "fallback_used": False,
                }
        except Exception as e:
            logger.warning(f"Không thể đọc active_brief file: {e}")

    # 2. Fallback: lấy brief mới nhất từ database
    fallback_used = True
    try:
        mgr = _get_briefs_manager()
        briefs = mgr.list()

        if briefs:
            latest = briefs[0]
            return {
                "found": True,
                "brief": latest,
                "brief_id": latest.get("brief_id"),
                "fallback_used": True,
                "total_briefs": len(briefs),
            }
    except Exception as e:
        logger.warning(f"Không thể query database cho briefs: {e}")

    # 3. Không tìm thấy brief nào
    return {
        "found": False,
        "brief": None,
        "brief_id": None,
        "fallback_used": True,
        "message": "Không tìm thấy brief nào trong database",
    }


# ============================================================================
# MCP Tool: get_clarifications
# ============================================================================


def get_clarifications(brief_id: str) -> Dict[str, Any]:
    """
    Lấy tất cả clarifications (Q&A) cho một brief.

    Args:
        brief_id: ID của brief

    Returns:
        Dictionary với:
        - brief_id: ID của brief
        - clarifications: list của clarification records
          (id, round, question, answer, is_memo, created_at)
        - total: tổng số clarifications
        - by_round: group by round number
        - memos: list của memos (is_memo=True)

    Raises:
        MidicoderError: Nếu brief_id không hợp lệ hoặc database error
    """
    if not brief_id or not brief_id.strip():
        EM.raise_error(
            ErrorCode.INVALID_INPUT,
            detail="brief_id không được để trống",
        )

    brief_id = brief_id.strip()

    try:
        mgr = _get_briefs_manager()
        clarifications = mgr.get_clarifications(brief_id)
    except Exception as e:
        EM.raise_error(
            ErrorCode.DB_CONNECTION_FAILED,
            detail=f"Không thể lấy clarifications: {e}",
            brief_id=brief_id,
        )

    # Group by round
    by_round: Dict[str, List[Dict]] = {}
    memos: List[Dict] = []

    for clar in clarifications:
        round_num = str(clar.get("round", 0))
        if round_num not in by_round:
            by_round[round_num] = []
        by_round[round_num].append(clar)

        if clar.get("is_memo"):
            memos.append(clar)

    return {
        "brief_id": brief_id,
        "clarifications": clarifications,
        "total": len(clarifications),
        "by_round": by_round,
        "memos": memos,
        "memo_count": len(memos),
    }


# ============================================================================
# MCP Tool: list_artifacts
# ============================================================================


def list_artifacts(brief_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Lấy danh sách tất cả artifacts (contracts, generated files) cho một brief.

    Args:
        brief_id: ID của brief để filter artifacts. Nếu None, trả về tất cả.

    Returns:
        Dictionary với:
        - brief_id: ID của brief (nếu có filter)
        - artifacts: list của artifact records
          (artifact_id, type, name, version, status, metadata, created_at)
        - total: tổng số artifacts
        - by_type: group by artifact type (contract, code, analysis, plan, mir)
        - by_status: group by status (pending, generated, validated, applied)

    Raises:
        MidicoderError: Nếu database error
    """
    try:
        mgr = _get_artifacts_manager()

        if brief_id:
            artifacts = mgr.list(brief_id=brief_id)
        else:
            artifacts = mgr.list()
    except Exception as e:
        EM.raise_error(
            ErrorCode.DB_CONNECTION_FAILED,
            detail=f"Không thể lấy artifacts: {e}",
            brief_id=brief_id or "all",
        )

    # Group by type
    by_type: Dict[str, List[str]] = {}
    # Group by status
    by_status: Dict[str, List[str]] = {}

    for artifact in artifacts:
        atype = artifact.get("type", "unknown")
        astatus = artifact.get("status", "unknown")
        a_id = artifact.get("artifact_id", "")

        if atype not in by_type:
            by_type[atype] = []
        by_type[atype].append(a_id)

        if astatus not in by_status:
            by_status[astatus] = []
        by_status[astatus].append(a_id)

    # Parse metadata JSON strings
    for artifact in artifacts:
        if isinstance(artifact.get("metadata"), str):
            try:
                artifact["metadata"] = json.loads(artifact["metadata"])
            except (json.JSONDecodeError, TypeError):
                pass

    result: Dict[str, Any] = {
        "artifacts": artifacts,
        "total": len(artifacts),
        "by_type": by_type,
        "by_status": by_status,
    }

    if brief_id:
        result["brief_id"] = brief_id

    return result
