"""
SQLite Persistence Layer cho Midicoder.

Module này cung cấp:
- Quản lý SQLite databases
- Schema cho các tables (briefs, clarifications, artifacts, activity_log, provenance)
- CRUD operations

E09: SQLite Persistence
"""

import sqlite3
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, List, Dict
from contextlib import contextmanager


# ============================================================================
# Database Configuration
# ============================================================================

DATABASE_DIR = Path(".midicoder/data")

# Database files (theo E09)
DB_BRIEFS = DATABASE_DIR / "briefs.db"
DB_ARTIFACTS = DATABASE_DIR / "artifacts.db"
DB_PROVENANCE = DATABASE_DIR / "provenance.db"
DB_CONTEXT = DATABASE_DIR / "context.db"


# ============================================================================
# Database Connection Helper
# ============================================================================

@contextmanager
def get_connection(db_path: Path):
    """
    Context manager cho SQLite connection.
    
    Args:
        db_path: Đường dẫn đến file database
        
    Yields:
        SQLite connection object
    """
    # Đảm bảo folder tồn tại
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row  # Enable dict-like access
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_database(db_path: Path, schema_sql: str):
    """
    Khởi tạo database với schema.
    
    Args:
        db_path: Đường dẫn đến file database
        schema_sql: SQL schema definition
    """
    with get_connection(db_path) as conn:
        conn.executescript(schema_sql)


# ============================================================================
# Tables Schema Definitions (From requirement.md E09)
# ============================================================================

# Briefs table schema
SCHEMA_BRIEFS = """
-- Briefs table: lưu trữ briefs (requirements documents)
CREATE TABLE IF NOT EXISTS briefs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brief_id TEXT NOT NULL,
    version TEXT NOT NULL DEFAULT 'v1.0.0',
    type TEXT NOT NULL DEFAULT 'working',
    title TEXT,
    content TEXT,
    status TEXT DEFAULT 'draft',
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    source_file TEXT,
    hash TEXT,
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

-- Brief lineage table: tracking brief evolution
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

-- Indexes for briefs table
CREATE INDEX IF NOT EXISTS idx_briefs_version ON briefs(version);
CREATE INDEX IF NOT EXISTS idx_briefs_type ON briefs(type);
CREATE INDEX IF NOT EXISTS idx_briefs_status ON briefs(status);

-- Indexes for clarifications table
CREATE INDEX IF NOT EXISTS idx_clarifications_brief ON clarifications(brief_id);
CREATE INDEX IF NOT EXISTS idx_clarifications_round ON clarifications(brief_id, round);

-- Indexes for brief_lineage table
CREATE INDEX IF NOT EXISTS idx_lineage_brief ON brief_lineage(brief_id);
"""

# Artifacts table schema (E10)
SCHEMA_ARTIFACTS = """
-- Artifacts table: lưu trữ generated artifacts
CREATE TABLE IF NOT EXISTS artifacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    artifact_id TEXT UNIQUE NOT NULL,
    type TEXT NOT NULL,
    name TEXT NOT NULL,
    version TEXT NOT NULL,
    brief_id TEXT,
    status TEXT DEFAULT 'pending',
    content_path TEXT,
    metadata TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (brief_id) REFERENCES briefs(brief_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_artifacts_type ON artifacts(type);
CREATE INDEX IF NOT EXISTS idx_artifacts_brief ON artifacts(brief_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_status ON artifacts(status);
"""

# Activity log schema (E09)
SCHEMA_ACTIVITY = """
-- Activity log: audit trail cho user actions
CREATE TABLE IF NOT EXISTS activity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT DEFAULT (datetime('now')),
    user TEXT DEFAULT 'cli',
    action TEXT NOT NULL,
    resource_type TEXT,
    resource_id TEXT,
    details TEXT,
    duration_ms INTEGER,
    status TEXT DEFAULT 'success'
);

CREATE INDEX IF NOT EXISTS idx_activity_timestamp ON activity_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_activity_action ON activity_log(action);
CREATE INDEX IF NOT EXISTS idx_activity_resource ON activity_log(resource_type, resource_id);
"""

# Provenance schema (E09) - Lineage + Decisions
SCHEMA_PROVENANCE = """
-- Lineage table: tracking data lineage
CREATE TABLE IF NOT EXISTS lineage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    source_id TEXT,
    source_type TEXT,
    relationship TEXT NOT NULL,
    metadata TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_lineage_entity ON lineage(entity_id, entity_type);
CREATE INDEX IF NOT EXISTS idx_lineage_source ON lineage(source_id, source_type);

-- Decisions table: tracking architectural và implementation decisions
CREATE TABLE IF NOT EXISTS decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    decision_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    status TEXT NOT NULL,
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

# Context schema - Codebase index
SCHEMA_CONTEXT = """
-- Symbols table: codebase index
CREATE TABLE IF NOT EXISTS symbols (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    file_path TEXT NOT NULL,
    line_number INTEGER,
    signature TEXT,
    description TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    UNIQUE(name, type, file_path)
);

CREATE INDEX IF NOT EXISTS idx_symbols_type ON symbols(type);
CREATE INDEX IF NOT EXISTS idx_symbols_file ON symbols(file_path);

-- References table: symbol relationships (dùng quotes vì 'references' là reserved keyword)
CREATE TABLE IF NOT EXISTS "references" (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_symbol TEXT NOT NULL,
    from_type TEXT NOT NULL,
    from_file TEXT NOT NULL,
    to_symbol TEXT NOT NULL,
    to_type TEXT,
    to_file TEXT,
    ref_type TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_references_from ON "references"(from_symbol, from_file);
CREATE INDEX IF NOT EXISTS idx_references_to ON "references"(to_symbol, to_file);
"""


# ============================================================================
# Briefs Manager
# ============================================================================

class BriefsManager:
    """
    Quản lý briefs trong SQLite.
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
        Lấy SQLite connection.
        
        Dùng cho internal operations và testing.
        
        Returns:
            Context manager cho connection
        """
        return get_connection(self.db_path)
    
    def init(self):
        """Khởi tạo database với schema."""
        init_database(self.db_path, SCHEMA_BRIEFS)
    
    def create(self, brief_id: str, version: str, content: str, 
               title: str = None, brief_type: str = "working") -> Dict:
        """
        Tạo brief mới.
        
        Args:
            brief_id: ID duy nhất cho brief
            version: Version number
            content: Nội dung brief (markdown)
            title: Tiêu đề brief
            brief_type: 'working' hoặc 'master'
            
        Returns:
            Brief record dictionary
        """
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        
        with get_connection(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO briefs (brief_id, version, type, title, content, hash)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (brief_id, version, brief_type, title, content, content_hash))
            
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
    
    def get(self, brief_id: str, version: str = None) -> Optional[Dict]:
        """
        Lấy brief theo ID.
        
        Args:
            brief_id: Brief ID
            version: Version (optional, default: latest)
            
        Returns:
            Brief record or None
        """
        with get_connection(self.db_path) as conn:
            if version:
                cursor = conn.execute(
                    "SELECT * FROM briefs WHERE brief_id = ? AND version = ?",
                    (brief_id, version)
                )
            else:
                # Sắp xếp theo id DESC để lấy record mới nhất (id tự tăng)
                cursor = conn.execute(
                    "SELECT * FROM briefs WHERE brief_id = ? ORDER BY id DESC LIMIT 1",
                    (brief_id,)
                )
            
            row = cursor.fetchone()
            return dict(row) if row else None
    
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
                    (version,)
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM briefs ORDER BY created_at DESC"
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
                (status, brief_id)
            )
            return True


# ============================================================================
# Artifacts Manager
# ============================================================================

class ArtifactsManager:
    """
    Quản lý artifacts trong SQLite.
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
        Lấy SQLite connection.
        
        Dùng cho internal operations và testing.
        
        Returns:
            Context manager cho connection
        """
        return get_connection(self.db_path)
    
    def init(self):
        """Khởi tạo database với schema."""
        init_database(self.db_path, SCHEMA_ARTIFACTS)
    
    def create(self, artifact_id: str, artifact_type: str, name: str,
               version: str, brief_id: str = None, content_path: str = None) -> Dict:
        """
        Tạo artifact mới.
        
        Args:
            artifact_id: ID duy nhất
            artifact_type: Loại artifact (analysis, contract, mir, plan, code)
            name: Tên artifact
            version: Version
            brief_id: Brief ID liên quan
            content_path: Đường dẫn file
            
        Returns:
            Artifact record
        """
        with get_connection(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO artifacts 
                (artifact_id, type, name, version, brief_id, content_path)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (artifact_id, artifact_type, name, version, brief_id, content_path))
            
            return {
                "id": cursor.lastrowid,
                "artifact_id": artifact_id,
                "type": artifact_type,
                "name": name,
                "version": version,
            }
    
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


# ============================================================================
# Activity Logger
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
        Lấy SQLite connection.
        
        Dùng cho internal operations và testing.
        
        Returns:
            Context manager cho connection
        """
        return get_connection(self.db_path)
    
    def init(self):
        """Khởi tạo database với schema."""
        # Artifacts và activity_log cùng trong artifacts.db
        init_database(self.db_path, SCHEMA_ARTIFACTS + "\n" + SCHEMA_ACTIVITY)
    
    def log(self, action: str, resource_type: str = None, resource_id: str = None,
            details: Dict = None, status: str = "success", duration_ms: int = None):
        """
        Ghi log activity.
        
        Args:
            action: Hành động (init, analyze, generate, etc.)
            resource_type: Loại resource
            resource_id: ID resource
            details: Chi tiết (dict)
            status: Status (success, failed)
            duration_ms: Thời gian thực hiện (ms)
        """
        with get_connection(self.db_path) as conn:
            conn.execute("""
                INSERT INTO activity_log 
                (action, resource_type, resource_id, details, status, duration_ms)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (action, resource_type, resource_id, 
                  json.dumps(details) if details else None, status, duration_ms))


# ============================================================================
# Initialize All Databases
# ============================================================================

def init_all_databases():
    """
    Khởi tạo tất cả SQLite databases theo E09.
    
    Creates:
    - .midicoder/data/briefs.db       # Brief library + clarifications
    - .midicoder/data/artifacts.db    # Artifacts + activity_log
    - .midicoder/data/provenance.db   # Lineage + decisions
    - .midicoder/data/context.db      # Codebase index
    
    Returns:
        True nếu thành công
    """
    # Tạo directory
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Briefs database
    print(f"Initializing {DB_BRIEFS.name}...")
    init_database(DB_BRIEFS, SCHEMA_BRIEFS)
    
    # Artifacts database (bao gồm activity_log)
    print(f"Initializing {DB_ARTIFACTS.name}...")
    artifacts_schema = SCHEMA_ARTIFACTS + "\n" + SCHEMA_ACTIVITY
    init_database(DB_ARTIFACTS, artifacts_schema)
    
    # Provenance database (lineage + decisions)
    print(f"Initializing {DB_PROVENANCE.name}...")
    init_database(DB_PROVENANCE, SCHEMA_PROVENANCE)
    
    # Context database (codebase index)
    print(f"Initializing {DB_CONTEXT.name}...")
    init_database(DB_CONTEXT, SCHEMA_CONTEXT)
    
    print("✅ All databases initialized")
    return True
