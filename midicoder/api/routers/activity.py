"""
Router cho activity log
Đọc từ artifacts.db.activity_log table
"""

import sqlite3
from pathlib import Path

from fastapi import APIRouter, Request, Query

from midicoder.api.i18n import i18n
from midicoder.api.models import ApiResponse

router = APIRouter(prefix="/activity", tags=["Activity"])


def _get_artifacts_db() -> Path:
    """Lấy đường dẫn đến artifacts.db của project active."""
    from midicoder.api.config import get_project_cwd
    project_cwd = get_project_cwd()
    return Path(project_cwd) / ".midicoder" / "data" / "artifacts.db"


@router.get("/recent", response_model=ApiResponse)
async def get_recent_activity(request: Request):
    """
    Lấy hoạt động gần đây (3 ngày gần nhất).
    """
    language = i18n.get_language_from_request(request)
    db_path = _get_artifacts_db()

    if not db_path.exists():
        return ApiResponse(
            success=True,
            data={"activities": [], "count": 0},
            message=i18n.translate("common.success", language),
            language=language,
        )

    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """SELECT id, timestamp, user, action, resource_type, resource_id,
                      details, status
               FROM activity_log
               WHERE timestamp >= datetime('now', '-3 days')
               ORDER BY timestamp DESC""",
        )
        rows = cursor.fetchall()
        conn.close()

        activities = []
        for row in rows:
            activities.append({
                "id": row["id"],
                "timestamp": row["timestamp"],
                "user": row["user"],
                "action": row["action"],
                "resource_type": row["resource_type"],
                "resource_id": row["resource_id"],
                "details": row["details"],
                "status": row["status"],
            })

        return ApiResponse(
            success=True,
            data={"activities": activities, "count": len(activities)},
            message=i18n.translate("common.success", language),
            language=language,
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            data={"activities": [], "count": 0},
            message=f"Failed to load recent activity: {str(e)}",
            language=language,
        )


@router.get("/all", response_model=ApiResponse)
async def get_all_activity(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=200, description="Items per page"),
):
    """
    Lấy tất cả hoạt động với phân trang.
    """
    language = i18n.get_language_from_request(request)
    db_path = _get_artifacts_db()

    if not db_path.exists():
        return ApiResponse(
            success=True,
            data={"activities": [], "total": 0, "page": page, "per_page": per_page, "total_pages": 0},
            message=i18n.translate("common.success", language),
            language=language,
        )

    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Count total
        cursor.execute("SELECT COUNT(*) as cnt FROM activity_log")
        total = cursor.fetchone()["cnt"]

        offset = (page - 1) * per_page
        cursor.execute(
            """SELECT id, timestamp, user, action, resource_type, resource_id,
                      details, status
               FROM activity_log
               ORDER BY timestamp DESC
               LIMIT ? OFFSET ?""",
            (per_page, offset),
        )
        rows = cursor.fetchall()
        conn.close()

        activities = []
        for row in rows:
            activities.append({
                "id": row["id"],
                "timestamp": row["timestamp"],
                "user": row["user"],
                "action": row["action"],
                "resource_type": row["resource_type"],
                "resource_id": row["resource_id"],
                "details": row["details"],
                "status": row["status"],
            })

        total_pages = (total + per_page - 1) // per_page if total > 0 else 0

        return ApiResponse(
            success=True,
            data={
                "activities": activities,
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
            },
            message=i18n.translate("common.success", language),
            language=language,
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            data={"activities": [], "total": 0, "page": page, "per_page": per_page, "total_pages": 0},
            message=f"Failed to load activity: {str(e)}",
            language=language,
        )
