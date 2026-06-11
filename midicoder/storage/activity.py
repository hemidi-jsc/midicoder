"""
Shared Activity Logger — read + write cho project-level artifacts.db.

Tất cả module của Midicoder dùng chung module này cho cả ghi VÀ đọc activity log.
Không được INSERT/SELECT trực tiếp vào table `activity_log` từ module khác.

Activity log table nằm trong `artifacts.db` (.midicoder/data/artifacts.db).

Mỗi record có `project_id` và `version` tự động resolve từ context hiện tại.
"""

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from midicoder.storage.sqlite import get_connection


# ============================================================================
# Project root resolution
# ============================================================================


def _get_project_root() -> Optional[Path]:
    """
    Lấy root directory của project đang active.

    Pipeline commands: chạy với cwd = project root.
    API router: dùng ProjectsManager để resolve project path.
    """
    # Case 1: cwd chính là project root (có .midicoder directory)
    cwd = Path.cwd()
    if (cwd / ".midicoder").is_dir():
        return cwd

    # Case 2: fallback — dùng ProjectsManager để tìm project active
    try:
        from midicoder.storage.projects import ProjectsManager
        mgr = ProjectsManager()
        mgr.init()
        active = mgr.get_active()
        if active and active.get("path"):
            return Path(active["path"])
    except Exception:
        pass

    return None


def _resolve_project_id() -> Optional[str]:
    """Lấy project_id từ context hiện tại."""
    try:
        from midicoder.storage.projects import ProjectsManager, DB_PROJECTS
        mgr = ProjectsManager(db_path=DB_PROJECTS)
        mgr.init()
        active = mgr.get_active()
        if active:
            return active.get("project_id")
    except BaseException:
        pass
    return None


def _resolve_active_version() -> Optional[str]:
    """Lấy version đang active từ config YAML."""
    try:
        from midicoder.pipeline.config import get_config
        cfg = get_config()
        if cfg:
            return cfg.get("active_version")
    except BaseException:
        pass
    return None


# ============================================================================
# DB path
# ============================================================================


def _get_artifacts_db_path() -> Path:
    """Lấy đường dẫn đến artifacts.db của project đang active."""
    root = _get_project_root()
    if root:
        return root / ".midicoder" / "data" / "artifacts.db"
    return Path(".midicoder/data/artifacts.db")


def _db_exists() -> bool:
    return _get_artifacts_db_path().is_file()


# ============================================================================
# Migration
# ============================================================================


def _ensure_columns(db_path: Path) -> None:
    """Thêm column project_id và version nếu chưa có (migration)."""
    try:
        with get_connection(db_path) as conn:
            # Check existing columns
            cursor = conn.execute("PRAGMA table_info(activity_log)")
            columns = {row[1] for row in cursor.fetchall()}

            if "project_id" not in columns:
                conn.execute("ALTER TABLE activity_log ADD COLUMN project_id TEXT")

            if "version" not in columns:
                conn.execute("ALTER TABLE activity_log ADD COLUMN version TEXT")

            # Backfill existing records
            if "project_id" not in columns or "version" not in columns:
                project_id = _resolve_project_id()
                # Update old records that don't have project_id
                if project_id:
                    conn.execute(
                        "UPDATE activity_log SET project_id = ? WHERE project_id IS NULL",
                        (project_id,),
                    )

            # Add indexes if missing
            idx_cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_activity_%'"
            )
            existing_indexes = {row[0] for row in idx_cursor.fetchall()}

            if "idx_activity_project" not in existing_indexes:
                conn.execute("CREATE INDEX IF NOT EXISTS idx_activity_project ON activity_log(project_id)")

            if "idx_activity_version" not in existing_indexes:
                conn.execute("CREATE INDEX IF NOT EXISTS idx_activity_version ON activity_log(version)")
    except Exception:
        pass


# ============================================================================
# Write
# ============================================================================


def log(
    action: str,
    resource_type: str = "system",
    resource_id: str = "",
    details: dict = None,
    status: str = "success",
    duration_ms: Optional[int] = None,
    version: Optional[str] = None,
) -> None:
    """
    Ghi activity log vào project-level artifacts.db.

    Shared function — dùng trong mọi pipeline command module.

    Args:
        action:        Hành động (vd: "brief.frozen", "contract.gen.completed")
        resource_type: Loại resource ("brief", "contract", "version", "code")
        resource_id:   ID của resource
        details:       Chi tiết (dict → JSON)
        status:        'success', 'error', 'warning'
        duration_ms:   Thời gian thực hiện (ms)
        version:       Version name (auto-resolve nếu không truyền)
    """
    if not _db_exists():
        return
    db_path = _get_artifacts_db_path()
    _ensure_columns(db_path)

    # Auto-resolve project_id
    project_id = _resolve_project_id()

    # Auto-resolve version nếu không được truyền explicit
    if version is None:
        version = _resolve_active_version()

    try:
        with get_connection(db_path) as conn:
            conn.execute(
                """INSERT INTO activity_log
                   (project_id, version, action, resource_type, resource_id,
                    details, status, duration_ms)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    project_id,
                    version,
                    action,
                    resource_type,
                    resource_id or None,
                    json.dumps(details, ensure_ascii=False) if details else None,
                    status,
                    duration_ms,
                ),
            )
    except Exception:
        pass


# ============================================================================
# Read helpers
# ============================================================================


def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    """Chuyển sqlite3.Row thành dict, parse JSON details, fix timestamp UTC."""
    d = dict(row)
    if d.get("details") and isinstance(d["details"], str):
        try:
            d["details"] = json.loads(d["details"])
        except (json.JSONDecodeError, TypeError):
            d["details"] = None
    # SQLite datetime('now') không có timezone — append 'Z' để frontend hiểu là UTC
    ts = d.get("timestamp")
    if ts and isinstance(ts, str) and not ts.endswith("Z") and "+" not in ts:
        d["timestamp"] = ts + "Z"
    return d


# ============================================================================
# Read
# ============================================================================


def query_recent(
    days: int = 3,
    version: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Lấy activity log trong N ngày gần nhất, sorted DESC by timestamp.

    Args:
        days:    Số ngày ngược về quá khứ
        version: Filter theo version (optional)

    Returns:
        List of activity dicts.
    """
    if not _db_exists():
        return []
    db_path = _get_artifacts_db_path()
    _ensure_columns(db_path)
    try:
        with get_connection(db_path) as conn:
            conn.row_factory = sqlite3.Row

            where = ["timestamp >= datetime('now', ?)"]
            params: list = [f"-{days} days"]

            if version:
                where.append("version = ?")
                params.append(version)

            cursor = conn.execute(
                f"""SELECT id, timestamp, user, project_id, version, action, resource_type,
                          resource_id, details, status, duration_ms
                   FROM activity_log
                   WHERE {' AND '.join(where)}
                   ORDER BY timestamp DESC""",
                params,
            )
            return [_row_to_dict(row) for row in cursor.fetchall()]
    except Exception:
        return []


def query_all(
    page: int = 1,
    per_page: int = 50,
    version: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Lấy tất cả activity log với phân trang.

    Args:
        page:     Trang hiện tại (1-based)
        per_page: Số bản ghi mỗi trang
        version:  Filter theo version (optional)

    Returns:
        Dict với keys: activities, total, page, per_page, total_pages
    """
    empty = {"activities": [], "total": 0, "page": page, "per_page": per_page, "total_pages": 0}
    if not _db_exists():
        return empty

    db_path = _get_artifacts_db_path()
    _ensure_columns(db_path)
    try:
        with get_connection(db_path) as conn:
            conn.row_factory = sqlite3.Row

            where = []
            params: list = []

            if version:
                where.append("version = ?")
                params.append(version)

            where_sql = (" WHERE " + " AND ".join(where)) if where else ""

            cursor = conn.execute(f"SELECT COUNT(*) as cnt FROM activity_log{where_sql}", params)
            total = cursor.fetchone()["cnt"]

            offset = (page - 1) * per_page
            cursor = conn.execute(
                f"""SELECT id, timestamp, user, project_id, version, action, resource_type,
                          resource_id, details, status, duration_ms
                   FROM activity_log{where_sql}
                   ORDER BY timestamp DESC
                   LIMIT ? OFFSET ?""",
                params + [per_page, offset],
            )
            rows = [_row_to_dict(row) for row in cursor.fetchall()]

            total_pages = (total + per_page - 1) // per_page if total > 0 else 0

            return {
                "activities": rows,
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
            }
    except Exception:
        return empty
