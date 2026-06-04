"""
Settings Manager — global key-value store in SQLite.

Database: ~/.midicoder/data/settings.db

Global data layout:
  ~/.midicoder/
  ├── data/
  │   ├── projects.db      (project registry + versions)
  │   └── settings.db      (LLM config, UI preferences, auth session)
  └── logs/
      └── midicoder-YYYYMMDD.log
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from midicoder.storage.sqlite import get_connection, init_database

logger = logging.getLogger(__name__)

# =============================================================================
# Paths
# =============================================================================

GLOBAL_DATA_DIR = Path.home() / ".midicoder" / "data"
DB_SETTINGS = GLOBAL_DATA_DIR / "settings.db"

# =============================================================================
# Schema
# =============================================================================

SCHEMA_SETTINGS = """
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY NOT NULL,
    value TEXT NOT NULL,
    updated_at TEXT DEFAULT (datetime('now'))
);
"""

# =============================================================================
# Default settings
# =============================================================================

DEFAULT_SETTINGS: Dict[str, Any] = {
    "version": "1.0.0",
    "cli.theme": "default",
    "cli.language": "vi",
    "cli.output_format": "human",
    "llm.provider": "openai-compatible",
    "llm.model": "qwen3.5-27B",
    "llm.api_url": "http://localhost:11434/v1",
    "llm.api_key": "",
    "llm.max_tokens": 8192,
    "llm.temperature": 0.3,
    "llm.timeout_seconds": 300,
    "llm.retry_attempts": 3,
    "llm.cache_enabled": True,
    "mcp.host": "localhost",
    "mcp.port": 2026,
    "neo4j.host": "localhost",
    "neo4j.port": 7687,
    "neo4j.username": "neo4j",
    "neo4j.password": "password",
    "neo4j.docker_auto_start": True,
    "webgui.host": "localhost",
    "webgui.port": 6868,
    "webgui.frontend_port": 7272,
    "webgui.auto_start": True,
    "webgui.open_browser": True,
    "version.max_versions": 5,
}


class SettingsManager:
    """
    Quản lý settings toàn cục trong SQLite.

    Key-value store, key dùng dot notation (ví dụ: "llm.model").
    Value được lưu dưới dạng JSON string.

    Usage:
        mgr = SettingsManager()
        mgr.init()
        mgr.set("llm.model", "gpt-4")
        model = mgr.get("llm.model")  # "gpt-4"
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DB_SETTINGS

    def init(self) -> None:
        """Khởi tạo database + populate default settings."""
        GLOBAL_DATA_DIR.mkdir(parents=True, exist_ok=True)
        init_database(self.db_path, SCHEMA_SETTINGS)
        self._ensure_defaults()

    def _ensure_defaults(self) -> None:
        """Populate các default settings nếu chưa tồn tại."""
        with get_connection(self.db_path) as conn:
            for key, default_value in DEFAULT_SETTINGS.items():
                cursor = conn.execute(
                    "SELECT 1 FROM settings WHERE key = ?", (key,)
                )
                if not cursor.fetchone():
                    conn.execute(
                        "INSERT INTO settings (key, value) VALUES (?, ?)",
                        (key, self._serialize(default_value)),
                    )

    @staticmethod
    def _serialize(value: Any) -> str:
        """Serialize value to JSON string."""
        return json.dumps(value, ensure_ascii=False)

    @staticmethod
    def _deserialize(raw: str) -> Any:
        """Deserialize JSON string to value."""
        return json.loads(raw)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(self, key: str, default: Any = None) -> Any:
        """
        Lấy giá trị setting theo key.

        Args:
            key: Dot-notation key (ví dụ: "llm.model")
            default: Giá trị mặc định nếu key không tồn tại

        Returns:
            Giá trị setting, hoặc default
        """
        with get_connection(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT value FROM settings WHERE key = ?", (key,)
            )
            row = cursor.fetchone()
            if row is None:
                return default
            return self._deserialize(row["value"])

    def set(self, key: str, value: Any) -> None:
        """
        Set giá trị setting (upsert).

        Args:
            key: Dot-notation key
            value: Giá trị (bất kỳ JSON-serializable)
        """
        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO settings (key, value, updated_at)
                VALUES (?, ?, datetime('now'))
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = datetime('now')
                """,
                (key, self._serialize(value)),
            )

    def delete(self, key: str) -> bool:
        """Xóa setting theo key."""
        with get_connection(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM settings WHERE key = ?", (key,)
            )
            return cursor.rowcount > 0

    def get_all(self) -> Dict[str, Any]:
        """Lấy tất cả settings dưới dạng dict flat."""
        with get_connection(self.db_path) as conn:
            cursor = conn.execute("SELECT key, value FROM settings ORDER BY key")
            return {
                row["key"]: self._deserialize(row["value"])
                for row in cursor.fetchall()
            }

    def reset(self, key: Optional[str] = None) -> None:
        """
        Reset setting(s) về default.

        Args:
            key: Key cụ thể để reset, hoặc None để reset toàn bộ
        """
        if key is None:
            # Reset toàn bộ — xóa và populate lại defaults
            with get_connection(self.db_path) as conn:
                conn.execute("DELETE FROM settings")
            self._ensure_defaults()
        else:
            # Reset key cụ thể
            default_value = DEFAULT_SETTINGS.get(key)
            if default_value is not None:
                self.set(key, default_value)
            else:
                self.delete(key)

    def get_nested(self, key: str, default: Any = None) -> Any:
        """
        Lấy giá trị với dot notation traversal (compatible với ConfigManager.get).

        Ví dụ: "llm.model" → tìm key "llm.model" trong DB.
        """
        return self.get(key, default)

    def set_nested(self, key: str, value: Any) -> None:
        """Alias cho set() — compatible với ConfigManager.set."""
        self.set(key, value)
