"""
SQLite Persistence Layer cho Midicoder.

Module này cung cấp:
- Quản lý SQLite databases
- Schema cho các tables (briefs, clarifications, artifacts, activity_log, provenance)
- CRUD operations với error handling và structured logging

E09: SQLite Persistence
"""

import sqlite3
import json
import hashlib
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, List, Dict
from contextlib import contextmanager

from midicoder.errors import MidicoderErrorManager as EM, ErrorCode

# ============================================================================
# Logging
# ============================================================================

logger = logging.getLogger(__name__)

# ============================================================================
# Configuration
# ============================================================================

# Database directory
DATABASE_DIR = Path(".midicoder/data")

# Default connection timeout (seconds) - Q12=A: 30s
DEFAULT_TIMEOUT = 30.0

# Retry configuration for concurrent writes - Q13=A
MAX_RETRIES = 3
BACKOFF_DELAYS = [0.1, 0.5, 1.0]  # 100ms, 500ms, 1000ms

# Database file paths (theo E09)
DB_BRIEFS = DATABASE_DIR / "briefs.db"
DB_ARTIFACTS = DATABASE_DIR / "artifacts.db"
DB_PROVENANCE = DATABASE_DIR / "provenance.db"
DB_CONTEXT = DATABASE_DIR / "context.db"

# ============================================================================
# Database Connection Helper với Error Handling
# ============================================================================


def _create_connection(db_path: Path, timeout: float = DEFAULT_TIMEOUT) -> sqlite3.Connection:
    """
    Tạo SQLite connection với retry mechanism cho "database is locked".

    Args:
        db_path: Đường dẫn đến file database
        timeout: Timeout cho locking (default: 30s)

    Returns:
        SQLite connection object

    Raises:
        MidicoderError: DB_CONNECTION_FAILED, DB_PERMISSION_DENIED, DB_FILE_CORRUPTED
    """
    retry_count = 0

    while retry_count <= MAX_RETRIES:
        try:
            # Đảm bảo folder tồn tại
            db_path.parent.mkdir(parents=True, exist_ok=True)

            conn = sqlite3.connect(str(db_path), timeout=timeout)
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            return conn

        except sqlite3.OperationalError as e:
            error_msg = str(e).lower()
            if "locked" in error_msg and retry_count < MAX_RETRIES:
                retry_count += 1
                delay = BACKOFF_DELAYS[retry_count - 1]
                logger.warning(
                    f"Database locked, retry {retry_count}/{MAX_RETRIES} after {delay*1000}ms",
                    extra={"db_path": str(db_path), "retry": retry_count},
                )
                time.sleep(delay)
                continue
            else:
                logger.error(
                    f"Database connection failed: {e}",
                    extra={"db_path": str(db_path)},
                )
                raise EM.wrap_exception(
                    e, ErrorCode.DB_CONNECTION_FAILED, db_path=str(db_path)
                )
        except PermissionError as e:
            logger.error(
                f"Permission denied for database: {db_path}",
                extra={"db_path": str(db_path)},
            )
            raise EM.wrap_exception(
                e, ErrorCode.DB_PERMISSION_DENIED, db_path=str(db_path)
            )
        except sqlite3.DatabaseError as e:
            error_msg = str(e).lower()
            if "database disk image is malformed" in error_msg:
                logger.error(
                    f"Database file corrupted: {db_path}",
                    extra={"db_path": str(db_path)},
                )
                raise EM.wrap_exception(
                    e, ErrorCode.DB_FILE_CORRUPTED, db_path=str(db_path)
                )
            raise


@contextmanager
def get_connection(db_path: Path, timeout: float = DEFAULT_TIMEOUT):
    """
    Context manager cho SQLite connection.

    Args:
        db_path: Đường dẫn đến file database
        timeout: Timeout cho locking (default: 30s)

    Yields:
        SQLite connection object

    Raises:
        MidicoderError: DB_CONNECTION_FAILED, DB_PERMISSION_DENIED
    """
    conn = _create_connection(db_path, timeout)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_database(db_path: Path, schema_sql: str, timeout: float = DEFAULT_TIMEOUT):
    """
    Khởi tạo database với schema.

    Args:
        db_path: Đường dẫn đến file database
        schema_sql: SQL schema definition
        timeout: Connection timeout

    Raises:
        MidicoderError: DB_SCHEMA_ERROR
    """
    logger.info(
        "Initializing database",
        extra={"db_path": str(db_path), "schema_size": len(schema_sql)},
    )

    try:
        with get_connection(db_path, timeout) as conn:
            conn.executescript(schema_sql)

        logger.info(
            "Database initialized successfully",
            extra={"db_path": str(db_path), "tables": schema_sql.count("CREATE TABLE")},
        )
    except sqlite3.DatabaseError as e:
        logger.error(
            f"Schema initialization failed: {e}",
            extra={"db_path": str(db_path)},
        )
        raise EM.wrap_exception(e, ErrorCode.DB_SCHEMA_ERROR, db_path=str(db_path))


# ============================================================================
# Schema Definitions (Updated theo requirement doc)
# ============================================================================

# Briefs table schema (Q1=A, Q2=B, Q4=A, Q7=A)
SCHEMA_BRIEFS = """
-- Briefs table: lưu trữ briefs (requirements documents)
CREATE TABLE IF NOT EXISTS briefs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brief_id TEXT NOT NULL,
    version TEXT NOT NULL DEFAULT 'v1.0.0',
    type TEXT NOT NULL DEFAULT 'working',
    title TEXT,
    content TEXT,  -- Full content (Q1=A)
    status TEXT DEFAULT 'draft',
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    source_file TEXT,
    hash TEXT,  -- Content hash (Q4=A)
    UNIQUE(brief_id, version)
);

-- Clarifications table: lưu trữ Q&A clarification sessions
CREATE TABLE IF NOT EXISTS clarifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brief_id TEXT NOT NULL,
    round INTEGER NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    is_memo INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (brief_id) REFERENCES briefs(brief_id) ON DELETE CASCADE
);

-- Brief lineage table: tracking brief evolution (Q2=B: separate table)
CREATE TABLE IF NOT EXISTS brief_lineage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brief_id TEXT NOT NULL,
    parent_brief_id TEXT,
    version TEXT NOT NULL,
    change_type TEXT,
    change_description TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (brief_id) REFERENCES briefs(brief_id) ON DELETE CASCADE,
    FOREIGN KEY (parent_brief_id) REFERENCES briefs(brief_id) ON DELETE SET NULL
);

-- Indexes (Q7=A: composite indexes)
CREATE INDEX IF NOT EXISTS idx_briefs_version ON briefs(version);
CREATE INDEX IF NOT EXISTS idx_briefs_type ON briefs(type);
CREATE INDEX IF NOT EXISTS idx_briefs_status ON briefs(status);
CREATE INDEX IF NOT EXISTS idx_briefs_version_status ON briefs(brief_id, status);

-- Indexes for clarifications table
CREATE INDEX IF NOT EXISTS idx_clarifications_brief ON clarifications(brief_id);
CREATE INDEX IF NOT EXISTS idx_clarifications_round ON clarifications(brief_id, round);

-- Indexes for brief_lineage table
CREATE INDEX IF NOT EXISTS idx_lineage_brief ON brief_lineage(brief_id);
"""

# Artifacts table schema (Q1=A: full content in DB, Q7=A)
SCHEMA_ARTIFACTS = """
-- Artifacts table: lưu trữ generated artifacts
CREATE TABLE IF NOT EXISTS artifacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    artifact_id TEXT UNIQUE NOT NULL,
    type TEXT NOT NULL,  -- analysis, contract, mir, plan, code
    name TEXT NOT NULL,
    version TEXT NOT NULL,
    brief_id TEXT,
    content TEXT,  -- Full content (Q1=A: theo SoT)
    status TEXT DEFAULT 'pending',
    metadata TEXT,  -- JSON
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (brief_id) REFERENCES briefs(brief_id) ON DELETE CASCADE
);

-- Indexes (Q7=A: composite)
CREATE INDEX IF NOT EXISTS idx_artifacts_type ON artifacts(type);
CREATE INDEX IF NOT EXISTS idx_artifacts_brief ON artifacts(brief_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_status ON artifacts(status);
CREATE INDEX IF NOT EXISTS idx_artifacts_type_status ON artifacts(type, status);
"""

# Activity log schema (E09, Q7=A)
SCHEMA_ACTIVITY = """
-- Activity log: audit trail cho user actions
CREATE TABLE IF NOT EXISTS activity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT DEFAULT (datetime('now')),
    user TEXT DEFAULT 'cli',
    action TEXT NOT NULL,
    resource_type TEXT,
    resource_id TEXT,
    details TEXT,  -- JSON
    duration_ms INTEGER,
    status TEXT DEFAULT 'success'
);

-- Indexes (Q7=A: composite)
CREATE INDEX IF NOT EXISTS idx_activity_timestamp ON activity_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_activity_action ON activity_log(action);
CREATE INDEX IF NOT EXISTS idx_activity_action_timestamp ON activity_log(action, timestamp);
CREATE INDEX IF NOT EXISTS idx_activity_resource ON activity_log(resource_type, resource_id);
"""

# Provenance schema (Q5=B: DDD-AIF, Q6=B: polymorphic, Q7=A)
SCHEMA_PROVENANCE = """
-- Lineage table: tracking data lineage (Q6=B: polymorphic)
CREATE TABLE IF NOT EXISTS lineage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id TEXT NOT NULL,
    entity_type TEXT NOT NULL,  -- brief, artifact, code, etc.
    source_id TEXT,
    source_type TEXT,
    relationship TEXT NOT NULL,  -- generated_from, derived_from, etc.
    metadata TEXT,  -- JSON
    created_at TEXT DEFAULT (datetime('now'))
);

-- Indexes (Q7=A: composite)
CREATE INDEX IF NOT EXISTS idx_lineage_entity ON lineage(entity_id, entity_type);
CREATE INDEX IF NOT EXISTS idx_lineage_source ON lineage(source_id, source_type);

-- Decisions table: DDD-AIF complete (Q5=B)
CREATE TABLE IF NOT EXISTS decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    decision_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    status TEXT NOT NULL,  -- proposed, accepted, rejected, deprecated
    description TEXT,
    rationale TEXT,
    consequences TEXT,
    decision_date TEXT DEFAULT (datetime('now')),
    decided_by TEXT,
    related_brief_id TEXT,
    related_version TEXT
);

CREATE INDEX IF NOT EXISTS idx_decisions_status ON decisions(status);
CREATE INDEX IF NOT EXISTS idx_decisions_brief ON decisions(related_brief_id);
"""

# Context schema - Q3=C: thêm files, bỏ graphs
SCHEMA_CONTEXT = """
-- Symbols table: codebase index
CREATE TABLE IF NOT EXISTS symbols (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT NOT NULL,  -- function, class, interface, entity
    file_path TEXT NOT NULL,
    line_number INTEGER,
    signature TEXT,
    description TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    UNIQUE(name, type, file_path)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_symbols_type ON symbols(type);
CREATE INDEX IF NOT EXISTS idx_symbols_file ON symbols(file_path);
CREATE INDEX IF NOT EXISTS idx_symbols_type_file ON symbols(type, file_path);

-- Files table (Q3=C: thêm theo SoT)
CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT UNIQUE NOT NULL,
    content_hash TEXT,
    language TEXT,
    size_bytes INTEGER,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_files_language ON files(language);
CREATE INDEX IF NOT EXISTS idx_files_path ON files(path);

-- References table: symbol relationships
CREATE TABLE IF NOT EXISTS "references" (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_symbol TEXT NOT NULL,
    from_type TEXT NOT NULL,
    from_file TEXT NOT NULL,
    to_symbol TEXT NOT NULL,
    to_type TEXT,
    to_file TEXT,
    ref_type TEXT NOT NULL,  -- calls, extends, implements, uses
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_references_from ON "references"(from_symbol, from_file);
CREATE INDEX IF NOT EXISTS idx_references_to ON "references"(to_symbol, to_file);
"""

# ============================================================================
# Briefs Manager (Updated với Q14=B, Q17=B)
# ============================================================================


class BriefsManager:
    """
    Quản lý briefs trong SQLite.

    Cung cấp CRUD operations cho briefs, clarifications, và brief_lineage.
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Khởi tạo BriefsManager.

        Args:
            db_path: Đường dẫn đến database (default: .midicoder/data/briefs.db)
        """
        self.db_path = db_path or DB_BRIEFS

    def _get_connection(self):
        """
        Lấy SQLite connection context manager.

        Dùng cho internal operations và testing.

        Returns:
            Context manager cho connection
        """
        return get_connection(self.db_path)

    def init(self):
        """Khởi tạo database với schema."""
        init_database(self.db_path, SCHEMA_BRIEFS)

    def create(
        self,
        brief_id: str,
        version: str,
        content: str,
        title: str = None,
        brief_type: str = "working",
    ) -> Dict:
        """
        Tạo brief mới.

        Args:
            brief_id: ID duy nhất cho brief
            version: Version number
            content: Nội dung brief (markdown) - Q1=A: lưu full content
            title: Tiêu đề brief
            brief_type: 'working' hoặc 'master'

        Returns:
            Brief record dictionary

        Raises:
            MidicoderError: DB_CONSTRAINT_VIOLATION nếu brief_id + version trùng
        """
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        try:
            with get_connection(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO briefs (brief_id, version, type, title, content, hash)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (brief_id, version, brief_type, title, content, content_hash),
                )

                return {
                    "id": cursor.lastrowid,
                    "brief_id": brief_id,
                    "version": version,
                    "type": brief_type,
                    "title": title,
                    "content": content,
                    "hash": content_hash,
                    "status": "draft",
                }
        except sqlite3.IntegrityError as e:
            raise EM.wrap_exception(
                e, ErrorCode.DB_CONSTRAINT_VIOLATION, brief_id=brief_id, version=version
            )

    def get(self, brief_id: str, version: str = None) -> Optional[Dict]:
        """
        Lấy brief theo ID.

        Args:
            brief_id: Brief ID
            version: Version (optional, default: latest) - Q17=B

        Returns:
            Brief record or None
        """
        with get_connection(self.db_path) as conn:
            if version:
                cursor = conn.execute(
                    "SELECT * FROM briefs WHERE brief_id = ? AND version = ?",
                    (brief_id, version),
                )
            else:
                # Sắp xếp theo id DESC để lấy record mới nhất
                cursor = conn.execute(
                    "SELECT * FROM briefs WHERE brief_id = ? ORDER BY id DESC LIMIT 1",
                    (brief_id,),
                )

            row = cursor.fetchone()
            return dict(row) if row else None

    def get_by_version(self, brief_id: str, version: str) -> Optional[Dict]:
        """
        Lấy brief theo ID và version cụ thể.

        Args:
            brief_id: Brief ID
            version: Version number

        Returns:
            Brief record or None
        """
        return self.get(brief_id, version)

    def get_latest(self, brief_id: str) -> Optional[Dict]:
        """
        Lấy brief mới nhất theo ID.

        Args:
            brief_id: Brief ID

        Returns:
            Latest brief record or None
        """
        return self.get(brief_id)

    def list(self, version: str = None) -> List[Dict]:
        """
        Danh sách tất cả briefs.

        Args:
            version: Filter by version (optional)

        Returns:
            List of brief records
        """
        with get_connection(self.db_path) as conn:
            if version:
                cursor = conn.execute(
                    "SELECT * FROM briefs WHERE version = ? ORDER BY created_at DESC",
                    (version,),
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM briefs ORDER BY created_at DESC"
                )

            return [dict(row) for row in cursor.fetchall()]

    def search_by_status(self, status: str) -> List[Dict]:
        """
        Tìm briefs theo status.

        Args:
            status: Status để filter (draft, clarified, frozen, archived)

        Returns:
            List of brief records with matching status
        """
        with get_connection(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM briefs WHERE status = ? ORDER BY created_at DESC",
                (status,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def update_status(self, brief_id: str, status: str) -> bool:
        """
        Cập nhật status của brief.

        Args:
            brief_id: Brief ID
            status: Status mới

        Returns:
            True nếu thành công
        """
        with get_connection(self.db_path) as conn:
            conn.execute(
                "UPDATE briefs SET status = ?, updated_at = datetime('now') WHERE brief_id = ?",
                (status, brief_id),
            )
            return True

    def _update_source_file(self, brief_id: str, source_file: str) -> bool:
        """
        Cập nhật source_file của brief (internal method).

        Args:
            brief_id: Brief ID
            source_file: Đường dẫn file nguồn

        Returns:
            True nếu thành công
        """
        with get_connection(self.db_path) as conn:
            conn.execute(
                "UPDATE briefs SET source_file = ?, updated_at = datetime('now') WHERE brief_id = ?",
                (source_file, brief_id),
            )
            return True

    # Clarification methods
    def add_clarification(
        self, brief_id: str, round_num: int, question: str, answer: str, is_memo: bool = False
    ) -> int:
        """
        Thêm clarification Q&A.

        Args:
            brief_id: Brief ID
            round_num: Round number
            question: Câu hỏi
            answer: Câu trả lời
            is_memo: Có phải memo (highlighted memory) không

        Returns:
            ID của clarification mới
        """
        with get_connection(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO clarifications (brief_id, round, question, answer, is_memo)
                VALUES (?, ?, ?, ?, ?)
            """,
                (brief_id, round_num, question, answer, 1 if is_memo else 0),
            )
            return cursor.lastrowid

    def get_clarifications(self, brief_id: str) -> List[Dict]:
        """
        Lấy tất cả clarifications cho brief.

        Args:
            brief_id: Brief ID

        Returns:
            List of clarification records
        """
        with get_connection(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM clarifications WHERE brief_id = ? ORDER BY round, created_at",
                (brief_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def _convert_to_master(self, brief_id: str) -> bool:
        """
        Convert working-brief → master-brief.

        Cập nhật type='master' và status='clarified'.

        Args:
            brief_id: Brief ID để convert

        Returns:
            True nếu thành công
        """
        with get_connection(self.db_path) as conn:
            conn.execute(
                "UPDATE briefs SET type = 'master', status = 'clarified', updated_at = datetime('now') WHERE brief_id = ?",
                (brief_id,),
            )
            return True

    # Lineage method
    def record_lineage(
        self,
        brief_id: str,
        parent_brief_id: str,
        version: str,
        change_type: str,
        change_description: str,
    ) -> int:
        """
        Record brief lineage (evolution tracking).

        Args:
            brief_id: Current brief ID
            parent_brief_id: Parent brief ID
            version: Version number
            change_type: Type of change (clarify, update, patch, etc.)
            change_description: Description of changes

        Returns:
            ID của lineage record mới
        """
        with get_connection(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO brief_lineage (brief_id, parent_brief_id, version, change_type, change_description)
                VALUES (?, ?, ?, ?, ?)
            """,
                (brief_id, parent_brief_id, version, change_type, change_description),
            )
            return cursor.lastrowid


# ============================================================================
# Artifacts Manager (Updated với Q15=B, Q1=A)
# ============================================================================


class ArtifactsManager:
    """
    Quản lý artifacts trong SQLite.

    Cung cấp CRUD operations cho generated artifacts.
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Khởi tạo ArtifactsManager.

        Args:
            db_path: Đường dẫn đến database
        """
        self.db_path = db_path or DB_ARTIFACTS

    def _get_connection(self):
        """
        Lấy SQLite connection context manager.

        Returns:
            Context manager cho connection
        """
        return get_connection(self.db_path)

    def init(self):
        """Khởi tạo database với schema."""
        # Artifacts và activity_log cùng trong artifacts.db
        init_database(self.db_path, SCHEMA_ARTIFACTS + "\n" + SCHEMA_ACTIVITY)

    def create(
        self,
        artifact_id: str,
        artifact_type: str,
        name: str,
        version: str,
        brief_id: str = None,
        content: str = None,  # Q1=A: full content
        metadata: Dict = None,
    ) -> Dict:
        """
        Tạo artifact mới.

        Args:
            artifact_id: ID duy nhất
            artifact_type: Loại artifact (analysis, contract, mir, plan, code)
            name: Tên artifact
            version: Version
            brief_id: Brief ID liên quan
            content: Full content (Q1=A: theo SoT)
            metadata: Metadata (JSON)

        Returns:
            Artifact record

        Raises:
            MidicoderError: DB_CONSTRAINT_VIOLATION nếu artifact_id trùng
        """
        try:
            with get_connection(self.db_path) as conn:
                # Upsert: INSERT ... ON CONFLICT REPLACE so re-running pipeline is safe
                cursor = conn.execute(
                    """
                    INSERT INTO artifacts
                    (artifact_id, type, name, version, brief_id, content, metadata, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
                    ON CONFLICT(artifact_id) DO UPDATE SET
                        type = excluded.type,
                        name = excluded.name,
                        version = excluded.version,
                        brief_id = excluded.brief_id,
                        content = excluded.content,
                        metadata = excluded.metadata,
                        updated_at = datetime('now')
                    """,
                    (
                        artifact_id,
                        artifact_type,
                        name,
                        version,
                        brief_id,
                        content,
                        json.dumps(metadata) if metadata else None,
                    ),
                )

                return {
                    "id": cursor.lastrowid,
                    "artifact_id": artifact_id,
                    "type": artifact_type,
                    "name": name,
                    "version": version,
                    "brief_id": brief_id,
                }
        except sqlite3.IntegrityError as e:
            raise EM.wrap_exception(
                e, ErrorCode.DB_CONSTRAINT_VIOLATION, artifact_id=artifact_id
            )

    def get(self, artifact_id: str) -> Optional[Dict]:
        """
        Lấy artifact theo ID.

        Args:
            artifact_id: Artifact ID

        Returns:
            Artifact record or None
        """
        with get_connection(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM artifacts WHERE artifact_id = ?", (artifact_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def list(self, artifact_type: str = None, brief_id: str = None) -> List[Dict]:
        """
        Danh sách artifacts.

        Args:
            artifact_type: Filter by type (optional)
            brief_id: Filter by brief (optional)

        Returns:
            List of artifacts
        """
        with get_connection(self.db_path) as conn:
            query = "SELECT * FROM artifacts WHERE 1=1"
            params = []

            if artifact_type:
                query += " AND type = ?"
                params.append(artifact_type)

            if brief_id:
                query += " AND brief_id = ?"
                params.append(brief_id)

            query += " ORDER BY created_at DESC"

            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def list_by_type(self, artifact_type: str) -> List[Dict]:
        """
        Lấy danh sách artifacts theo type.

        Args:
            artifact_type: Loại artifact

        Returns:
            List of artifacts với matching type
        """
        return self.list(artifact_type=artifact_type)

    def update_status(self, artifact_id: str, status: str) -> bool:
        """
        Cập nhật status của artifact.

        Args:
            artifact_id: Artifact ID
            status: Status mới (pending, generated, validated, applied)

        Returns:
            True nếu thành công
        """
        with get_connection(self.db_path) as conn:
            conn.execute(
                "UPDATE artifacts SET status = ?, updated_at = datetime('now') WHERE artifact_id = ?",
                (status, artifact_id),
            )
            return True

    def update_content(self, artifact_id: str, content: str) -> bool:
        """
        Cập nhật content của artifact.

        Args:
            artifact_id: Artifact ID
            content: New content

        Returns:
            True nếu thành công
        """
        with get_connection(self.db_path) as conn:
            conn.execute(
                "UPDATE artifacts SET content = ?, updated_at = datetime('now') WHERE artifact_id = ?",
                (content, artifact_id),
            )
            return True


# ============================================================================
# Activity Logger (Updated với Q16=A)
# ============================================================================


class ActivityLogger:
    """
    Logger cho activity/audit trail.

    Lưu trong artifacts.db cùng với artifacts table.
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Khởi tạo ActivityLogger.

        Args:
            db_path: Đường dẫn đến database (default: .midicoder/data/artifacts.db)
        """
        self.db_path = db_path or DB_ARTIFACTS

    def _get_connection(self):
        """
        Lấy SQLite connection context manager.

        Returns:
            Context manager cho connection
        """
        return get_connection(self.db_path)

    def init(self):
        """Khởi tạo database với schema."""
        # Artifacts và activity_log cùng trong artifacts.db
        init_database(self.db_path, SCHEMA_ARTIFACTS + "\n" + SCHEMA_ACTIVITY)

    def log(
        self,
        action: str,
        resource_type: str = None,
        resource_id: str = None,
        details: Dict = None,
        status: str = "success",
        duration_ms: int = None,
    ) -> int:
        """
        Ghi log activity.

        Args:
            action: Hành động (init, analyze, generate, etc.)
            resource_type: Loại resource
            resource_id: ID resource
            details: Chi tiết (dict)
            status: Status (success, failed)
            duration_ms: Thời gian thực hiện (ms)

        Returns:
            ID của log entry mới
        """
        logger.debug(
            f"Logging activity: {action}",
            extra={
                "action": action,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "status": status,
            },
        )

        with get_connection(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO activity_log 
                (action, resource_type, resource_id, details, status, duration_ms)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    action,
                    resource_type,
                    resource_id,
                    json.dumps(details) if details else None,
                    status,
                    duration_ms,
                ),
            )
            return cursor.lastrowid

    def query(
        self,
        start_time: str = None,
        end_time: str = None,
        action: str = None,
        status: str = None,
        limit: int = 100,
    ) -> List[Dict]:
        """
        Query activity logs với filters (Q16=A: full filters).

        Args:
            start_time: Start time filter (ISO format)
            end_time: End time filter (ISO format)
            action: Action filter
            status: Status filter
            limit: Maximum results to return

        Returns:
            List of activity log records
        """
        with get_connection(self.db_path) as conn:
            query = "SELECT * FROM activity_log WHERE 1=1"
            params = []

            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time)

            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time)

            if action:
                query += " AND action = ?"
                params.append(action)

            if status:
                query += " AND status = ?"
                params.append(status)

            query += f" ORDER BY timestamp DESC LIMIT {limit}"

            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]


# ============================================================================
# Provenance Manager (Q18=A: dedicated manager)
# ============================================================================


class ProvenanceManager:
    """
    Quản lý provenance (lineage + decisions).

    Cung cấp operations cho tracking data lineage và architectural decisions.
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Khởi tạo ProvenanceManager.

        Args:
            db_path: Đường dẫn đến database (default: .midicoder/data/provenance.db)
        """
        self.db_path = db_path or DB_PROVENANCE

    def init(self):
        """Khởi tạo database với schema."""
        init_database(self.db_path, SCHEMA_PROVENANCE)

    # Lineage operations
    def record_lineage(
        self,
        entity_id: str,
        entity_type: str,
        source_id: str,
        source_type: str,
        relationship: str,
        metadata: Dict = None,
    ) -> int:
        """
        Record lineage relationship.

        Args:
            entity_id: Entity ID
            entity_type: Entity type (brief, artifact, code, etc.) - Q6=B: polymorphic
            source_id: Source entity ID
            source_type: Source entity type
            relationship: Relationship type (generated_from, derived_from, etc.)
            metadata: Additional metadata (JSON)

        Returns:
            ID của lineage record mới
        """
        with get_connection(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO lineage (entity_id, entity_type, source_id, source_type, relationship, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    entity_id,
                    entity_type,
                    source_id,
                    source_type,
                    relationship,
                    json.dumps(metadata) if metadata else None,
                ),
            )
            return cursor.lastrowid

    def get_lineage(self, entity_id: str, entity_type: str) -> List[Dict]:
        """
        Lấy lineage cho entity.

        Args:
            entity_id: Entity ID
            entity_type: Entity type

        Returns:
            List of lineage records
        """
        with get_connection(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT * FROM lineage 
                WHERE entity_id = ? AND entity_type = ?
                ORDER BY created_at
            """,
                (entity_id, entity_type),
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_lineage_graph(
        self, entity_id: str, entity_type: str, max_depth: int = 3
    ) -> Dict:
        """
        Lấy lineage graph (recursive).

        Args:
            entity_id: Entity ID
            entity_type: Entity type
            max_depth: Maximum recursion depth

        Returns:
            Lineage graph as nested dictionary
        """

        def build_graph(e_id: str, e_type: str, depth: int) -> Dict:
            if depth <= 0:
                return {"id": e_id, "type": e_type, "children": []}

            lineage = self.get_lineage(e_id, e_type)
            children = []

            for record in lineage:
                child = build_graph(
                    record.get("source_id") or "",
                    record.get("source_type") or "",
                    depth - 1,
                )
                child["relationship"] = record.get("relationship")
                children.append(child)

            return {"id": e_id, "type": e_type, "children": children}

        return build_graph(entity_id, entity_type, max_depth)

    # Decision operations (Q5=B: DDD-AIF complete)
    def record_decision(
        self,
        decision_id: str,
        title: str,
        status: str,
        description: str = None,
        rationale: str = None,
        consequences: str = None,
        decided_by: str = None,
        related_brief_id: str = None,
        related_version: str = None,
    ) -> int:
        """
        Record architectural decision (DDD-AIF style).

        Args:
            decision_id: Unique decision ID
            title: Decision title
            status: Status (proposed, accepted, rejected, deprecated)
            description: Decision description
            rationale: Rationale for decision
            consequences: Consequences of decision
            decided_by: Who made the decision
            related_brief_id: Related brief ID
            related_version: Related version

        Returns:
            ID của decision record mới
        """
        with get_connection(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO decisions 
                (decision_id, title, status, description, rationale, consequences, decided_by, related_brief_id, related_version)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    decision_id,
                    title,
                    status,
                    description,
                    rationale,
                    consequences,
                    decided_by,
                    related_brief_id,
                    related_version,
                ),
            )
            return cursor.lastrowid

    def get_decision(self, decision_id: str) -> Optional[Dict]:
        """
        Lấy decision theo ID.

        Args:
            decision_id: Decision ID

        Returns:
            Decision record or None
        """
        with get_connection(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM decisions WHERE decision_id = ?", (decision_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_decisions(self, brief_id: str = None, status: str = None) -> List[Dict]:
        """
        Lấy danh sách decisions.

        Args:
            brief_id: Filter by related brief (optional)
            status: Filter by status (optional)

        Returns:
            List of decision records
        """
        with get_connection(self.db_path) as conn:
            query = "SELECT * FROM decisions WHERE 1=1"
            params = []

            if brief_id:
                query += " AND related_brief_id = ?"
                params.append(brief_id)

            if status:
                query += " AND status = ?"
                params.append(status)

            query += " ORDER BY decision_date DESC"

            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def update_decision_status(self, decision_id: str, status: str) -> bool:
        """
        Cập nhật status của decision.

        Args:
            decision_id: Decision ID
            status: New status (proposed, accepted, rejected, deprecated)

        Returns:
            True nếu thành công
        """
        with get_connection(self.db_path) as conn:
            conn.execute(
                "UPDATE decisions SET status = ? WHERE decision_id = ?",
                (status, decision_id),
            )
            return True


# ============================================================================
# Initialize All Databases (Q11=A: all-or-nothing rollback)
# ============================================================================


def init_all_databases() -> bool:
    """
    Khởi tạo tất cả SQLite databases theo E09.

    Creates:
    - .midicoder/data/briefs.db       # Brief library + clarifications
    - .midicoder/data/artifacts.db    # Artifacts + activity_log
    - .midicoder/data/provenance.db   # Lineage + decisions
    - .midicoder/data/context.db      # Codebase index

    Q11=A: All-or-nothing rollback strategy

    Returns:
        True nếu thành công

    Raises:
        MidicoderError: DB_SCHEMA_ERROR nếu initialization thất bại
    """
    created_dbs = []  # Track created DBs for rollback

    try:
        # Tạo directory
        DATABASE_DIR.mkdir(parents=True, exist_ok=True)

        logger.info("Initializing all Midicoder databases")

        # Step 1: Briefs database
        logger.info(f"Initializing {DB_BRIEFS.name}...")
        init_database(DB_BRIEFS, SCHEMA_BRIEFS, DEFAULT_TIMEOUT)
        created_dbs.append(DB_BRIEFS)

        # Step 2: Artifacts database (bao gồm activity_log)
        logger.info(f"Initializing {DB_ARTIFACTS.name}...")
        artifacts_schema = SCHEMA_ARTIFACTS + "\n" + SCHEMA_ACTIVITY
        init_database(DB_ARTIFACTS, artifacts_schema, DEFAULT_TIMEOUT)
        created_dbs.append(DB_ARTIFACTS)

        # Step 3: Provenance database (lineage + decisions)
        logger.info(f"Initializing {DB_PROVENANCE.name}...")
        init_database(DB_PROVENANCE, SCHEMA_PROVENANCE, DEFAULT_TIMEOUT)
        created_dbs.append(DB_PROVENANCE)

        # Step 4: Context database (codebase index)
        logger.info(f"Initializing {DB_CONTEXT.name}...")
        init_database(DB_CONTEXT, SCHEMA_CONTEXT, DEFAULT_TIMEOUT)
        created_dbs.append(DB_CONTEXT)

        logger.info("✅ All databases initialized successfully")
        return True

    except Exception as e:
        # Q11=A: Rollback all created databases
        logger.error(
            f"Database initialization failed: {e}",
            extra={"created_dbs": [str(db) for db in created_dbs]},
        )

        for db_path in created_dbs:
            try:
                if db_path.exists():
                    db_path.unlink()
                    logger.info(f"Rollback: deleted {db_path.name}")
            except OSError as rollback_error:
                logger.warning(
                    f"Failed to rollback {db_path.name}: {rollback_error}",
                    extra={"db_path": str(db_path)},
                )

        # Re-raise the original error
        raise


# ============================================================================
# Export all
# ============================================================================

__all__ = [
    # Configuration
    "DATABASE_DIR",
    "DEFAULT_TIMEOUT",
    "DB_BRIEFS",
    "DB_ARTIFACTS",
    "DB_PROVENANCE",
    "DB_CONTEXT",
    # Schema definitions
    "SCHEMA_BRIEFS",
    "SCHEMA_ARTIFACTS",
    "SCHEMA_ACTIVITY",
    "SCHEMA_PROVENANCE",
    "SCHEMA_CONTEXT",
    # Helpers
    "get_connection",
    "init_database",
    # Managers
    "BriefsManager",
    "ArtifactsManager",
    "ActivityLogger",
    "ProvenanceManager",
    # Initialization
    "init_all_databases",
]