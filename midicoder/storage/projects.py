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

-- Versions table: mỗi project có nhiều versions, chỉ 1 active mỗi lúc
CREATE TABLE IF NOT EXISTS versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version_name TEXT NOT NULL,
    project_id TEXT NOT NULL,
    active INTEGER DEFAULT 0,
    parent_version TEXT,
    status TEXT DEFAULT 'draft',
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    UNIQUE(version_name, project_id),
    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_versions_active ON versions(active);
CREATE INDEX IF NOT EXISTS idx_versions_project ON versions(project_id);
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
        """Lấy tất cả projects — sort theo id (thứ tự tạo, không nhảy khi activate)."""
        with get_connection(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM projects ORDER BY id DESC"
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

    # ------------------------------------------------------------------
    # Version CRUD — lưu vào SQLite projects.db
    # ------------------------------------------------------------------

    def version_create(
        self,
        project_id: str,
        version_name: str,
        parent_version: Optional[str] = None,
        set_active: bool = True,
    ) -> Dict[str, Any]:
        """Tạo version mới cho project."""
        if set_active:
            # 1. Archive các version có status='inbuild' (lifecycle)
            self.version_archive_inbuild(project_id)
            # 2. Deselect version đang chọn (selection pointer) — không đổi status
            self.version_deselect_all(project_id)

        try:
            with get_connection(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO versions (version_name, project_id, active, parent_version, status)
                    VALUES (?, ?, ?, ?, 'draft')
                    """,
                    (version_name, project_id, 1 if set_active else 0, parent_version),
                )
            return self.version_get(project_id, version_name) or {
                "version_name": version_name,
                "project_id": project_id,
                "active": True,
                "parent_version": parent_version,
                "status": "draft",
            }
        except Exception as e:
            # UNIQUE constraint violation
            if "UNIQUE" in str(e) or "unique" in str(e).lower():
                return self.version_get(project_id, version_name)
            raise

    def version_get(
        self,
        project_id: str,
        version_name: str,
    ) -> Optional[Dict[str, Any]]:
        """Lấy version theo project_id + version_name."""
        with get_connection(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM versions WHERE project_id = ? AND version_name = ?",
                (project_id, version_name),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def version_get_active(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Lấy version đang active của project."""
        with get_connection(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM versions WHERE project_id = ? AND active = 1 LIMIT 1",
                (project_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def version_list(self, project_id: str) -> List[Dict[str, Any]]:
        """Lấy tất cả versions của project."""
        with get_connection(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM versions WHERE project_id = ? ORDER BY created_at DESC",
                (project_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def version_use(
        self,
        project_id: str,
        version_name: str,
    ) -> Optional[Dict[str, Any]]:
        """Switch active version của project.

        Chỉ đổi active flag, KHÔNG tự động đổi status thành 'inbuild'.
        Status chỉ được chuyển sang 'inbuild' khi brief của version đó được frozen.
        """
        v = self.version_get(project_id, version_name)
        if not v:
            return None

        with get_connection(self.db_path) as conn:
            conn.execute(
                "UPDATE versions SET active = 0 WHERE project_id = ?",
                (project_id,),
            )
            conn.execute(
                "UPDATE versions SET active = 1, updated_at = datetime('now') WHERE project_id = ? AND version_name = ?",
                (project_id, version_name),
            )
        return self.version_get(project_id, version_name)

    def version_update_status(
        self,
        project_id: str,
        version_name: str,
        status: str,
    ) -> Optional[Dict[str, Any]]:
        """Cập nhật status của version (draft → inbuild)."""
        with get_connection(self.db_path) as conn:
            conn.execute(
                "UPDATE versions SET status = ?, updated_at = datetime('now') WHERE project_id = ? AND version_name = ?",
                (status, project_id, version_name),
            )
        return self.version_get(project_id, version_name)

    def version_delete(
        self,
        project_id: str,
        version_name: str,
        force: bool = False,
    ) -> bool:
        """Xóa version (không cho xóa active version trừ khi force)."""
        v = self.version_get(project_id, version_name)
        if not v:
            return False

        if v.get("active") and not force:
            raise ValueError(f"Cannot delete active version '{version_name}'. Use force=True.")

        with get_connection(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM versions WHERE project_id = ? AND version_name = ?",
                (project_id, version_name),
            )
            return cursor.rowcount > 0

    def version_archive_inbuild(self, project_id: str):
        """Archive các version có status='inbuild' — lifecycle rule."""
        with get_connection(self.db_path) as conn:
            conn.execute(
                "UPDATE versions SET active = 0, status = 'archived', updated_at = datetime('now') WHERE project_id = ? AND status = 'inbuild'",
                (project_id,),
            )

    def version_deselect_all(self, project_id: str):
        """Deselect version đang chọn (active=1 → active=0) — không đổi status."""
        with get_connection(self.db_path) as conn:
            conn.execute(
                "UPDATE versions SET active = 0, updated_at = datetime('now') WHERE project_id = ? AND active = 1",
                (project_id,),
            )

    def version_deactivate_all(self, project_id: str):
        """Legacy alias — keep for backward compatibility."""
        self.version_archive_inbuild(project_id)
        self.version_deselect_all(project_id)
