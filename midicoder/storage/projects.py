"""
Projects Manager — lưu trữ registry projects trong SQLite.

Database toàn cục: ~/.midicoder/data/projects.db

Mỗi project có:
- name: tên project
- path: đường dẫn tuyệt đối đến folder project
- active: chỉ 1 project active tại 1 thời điểm

Dùng chung helper `get_connection` từ midicoder.storage.sqlite
để có retry mechanism.
"""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from midicoder.storage.sqlite import get_connection, init_database

logger = logging.getLogger(__name__)

# Global DB path — ~/.midicoder/data/projects.db
GLOBAL_DATA_DIR = Path.home() / ".midicoder" / "data"
DB_PROJECTS = GLOBAL_DATA_DIR / "projects.db"

SCHEMA_PROJECTS = """
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    path TEXT NOT NULL,
    active INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_projects_active ON projects(active);
CREATE INDEX IF NOT EXISTS idx_projects_path ON projects(path);
"""


class ProjectsManager:
    """Quản lý registry projects trong SQLite."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DB_PROJECTS

    def init(self):
        """Khởi tạo database với schema."""
        init_database(self.db_path, SCHEMA_PROJECTS)

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def create(
        self,
        project_id: str,
        name: str,
        path: str,
        set_active: bool = True,
    ) -> Dict[str, Any]:
        """
        Tạo project mới trong registry.

        Args:
            project_id: ID duy nhất (hash hoặc slug)
            name: Tên hiển thị
            path: Đường dẫn tuyệt đối đến folder project
            set_active: Nếu True, tự động deactivate project cũ

        Returns:
            Project record dict
        """
        if set_active:
            self._deactivate_all()

        try:
            with get_connection(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO projects (project_id, name, path, active)
                    VALUES (?, ?, ?, ?)
                    """,
                    (project_id, name, path, 1 if set_active else 0),
                )
                return self.get(project_id) or {
                    "project_id": project_id,
                    "name": name,
                    "path": path,
                    "active": True,
                }
        except Exception as e:
            # Constraint violation — project_id đã tồn tại
            logger.warning(f"Project {project_id} already exists, updating instead: {e}")
            return self.update(project_id, name=name, path=path, set_active=set_active)

    def get(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Lấy project theo ID."""
        with get_connection(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM projects WHERE project_id = ?", (project_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_active(self) -> Optional[Dict[str, Any]]:
        """Lấy project đang active."""
        with get_connection(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM projects WHERE active = 1 LIMIT 1"
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_by_path(self, path: str) -> Optional[Dict[str, Any]]:
        """Lấy project theo đường dẫn."""
        with get_connection(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM projects WHERE path = ? LIMIT 1", (path,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def list_all(self) -> List[Dict[str, Any]]:
        """Lấy tất cả projects."""
        with get_connection(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM projects ORDER BY updated_at DESC"
            )
            return [dict(row) for row in cursor.fetchall()]

    def update(
        self,
        project_id: str,
        name: str = None,
        path: str = None,
        set_active: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """Cập nhật project."""
        with get_connection(self.db_path) as conn:
            if set_active:
                self._deactivate_all(conn)

            updates = []
            params = []

            if name is not None:
                updates.append("name = ?")
                params.append(name)
            if path is not None:
                updates.append("path = ?")
                params.append(path)
            if set_active:
                updates.append("active = 1")

            if not updates:
                return self.get(project_id)

            params.append(project_id)
            updates.append("updated_at = datetime('now')")

            conn.execute(
                f"UPDATE projects SET {', '.join(updates)} WHERE project_id = ?",
                params,
            )
            return self.get(project_id)

    def activate(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Đánh dấu project là active (deactivate các project khác)."""
        with get_connection(self.db_path) as conn:
            self._deactivate_all(conn)
            conn.execute(
                "UPDATE projects SET active = 1, updated_at = datetime('now') WHERE project_id = ?",
                (project_id,),
            )
        return self.get(project_id)

    def delete(self, project_id: str) -> bool:
        """Xóa project khỏi registry."""
        with get_connection(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM projects WHERE project_id = ?", (project_id,)
            )
            return cursor.rowcount > 0

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _deactivate_all(self, conn=None):
        """Deactivate tất cả projects. Nếu conn=None, tự tạo connection."""
        if conn is not None:
            conn.execute("UPDATE projects SET active = 0")
        else:
            with get_connection(self.db_path) as c:
                c.execute("UPDATE projects SET active = 0")

    # ------------------------------------------------------------------
    # Convenience: get active project path
    # ------------------------------------------------------------------

    def get_active_project_path(self) -> Optional[str]:
        """Lấy path của project đang active."""
        active = self.get_active()
        if active:
            return active.get("path")
        return None
