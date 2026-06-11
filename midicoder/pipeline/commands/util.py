"""
Utility Commands cho Midicoder Pipeline.

Module này chứa implementation của các utility commands:
- status: Hiển thị project status (E20)
- feedback: Thu thập và lưu feedback (E20)
- config: Quản lý cấu hình (E20)

E20: CLI Commands - Utility Commands
"""

import json
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

import yaml

from midicoder.errors import MidicoderErrorManager as EM, ErrorCode
from midicoder.storage.sqlite import (
    BriefsManager,
    ArtifactsManager,
    DB_BRIEFS,
    DB_ARTIFACTS,
    get_connection
)

# ============================================================================
# Logging
# ============================================================================

logger = logging.getLogger(__name__)


def _log_activity(action: str, resource_type: str = "system", resource_id: str = "", details: dict = None, status: str = "success") -> None:
    """Ghi activity log vào artifacts.db activity_log table."""
    log(action=action, resource_type=resource_type, resource_id=resource_id, details=details, status=status)

# ============================================================================
# Config Schema
# ============================================================================

# Schema mặc định cho config validation
DEFAULT_CONFIG_SCHEMA = {
    "cli": {
        "theme": "default",
        "language": "vi",
        "output_format": "human"
    },
    "llm": {
        "provider": "openai-compatible",
        "model": "qwen3.5-27B",
        "api_url": "http://localhost:11434/v1",
        "api_key": None,
        "max_tokens": 8192,
        "temperature": 0.3,
        "timeout_seconds": 300,
        "retry_attempts": 3,
        "cache_enabled": True
    },
    "mcp": {
        "host": "localhost",
        "port": 2026
    },
    "neo4j": {
        "host": "localhost",
        "port": 7687,
        "username": "neo4j",
        "password": "password",
        "docker_auto_start": True
    },
    "webgui": {
        "host": "localhost",
        "port": 6868,
        "frontend_port": 7272,
        "auto_start": True,
        "open_browser": True
    },
    "version": {
        "max_versions": 5
    }
}


def get_config_schema() -> Dict[str, Any]:
    """
    Lấy config schema cho validation.
    
    Returns:
        Schema dictionary với tất cả sections và default values
    """
    return DEFAULT_CONFIG_SCHEMA.copy()


def validate_config_key(key: str) -> bool:
    """
    Validate config key theo schema.
    
    Args:
        key: Config key để validate (ví dụ: "llm.model", "cli.language")
        
    Returns:
        True nếu key hợp lệ, False nếu không
    """
    if not key:
        return False
    
    schema = get_config_schema()
    
    # Nếu key là section name (không có dấu chấm)
    if "." not in key:
        return key in schema
    
    # Nếu key là nested key (ví dụ: "llm.model")
    parts = key.split(".")
    if len(parts) != 2:
        return False
    
    section, field = parts
    return section in schema and field in schema.get(section, {})


# ============================================================================
# Feedback Validation
# ============================================================================

VALID_FEEDBACK_TYPES = ["bug", "enhancement", "clarification"]


def validate_feedback_type(feedback_type: str) -> bool:
    """
    Validate feedback type.
    
    Args:
        feedback_type: Type để validate
        
    Returns:
        True nếu type hợp lệ, False nếu không
    """
    return feedback_type in VALID_FEEDBACK_TYPES


# ============================================================================
# Feedback Schema
# ============================================================================

# Schema cho feedback table
SCHEMA_FEEDBACK = """
-- Feedback table: lưu trữ user feedback
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version TEXT NOT NULL,
    brief_id INTEGER REFERENCES briefs(id),
    type TEXT NOT NULL,
    message TEXT NOT NULL,
    auto_applied INTEGER DEFAULT 1,
    applied_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_feedback_version ON feedback(version);
CREATE INDEX IF NOT EXISTS idx_feedback_brief ON feedback(brief_id);
"""


class FeedbackManager:
    """
    Quản lý feedback trong SQLite.
    
    Cung cấp CRUD operations cho feedback table.
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Khởi tạo FeedbackManager.
        
        Args:
            db_path: Đường dẫn đến database (default: .midicoder/data/briefs.db)
        """
        self.db_path = db_path or DB_BRIEFS
        self._ensure_table_exists()
    
    def _ensure_table_exists(self):
        """Đảm bảo feedback table tồn tại."""
        try:
            with get_connection(self.db_path) as conn:
                conn.executescript(SCHEMA_FEEDBACK)
        except Exception as e:
            logger.warning(f"Could not create feedback table: {e}")
    
    def get_active_brief(self) -> Optional[Dict]:
        """
        Lấy active brief hiện tại.
        
        Returns:
            Brief record hoặc None nếu không tìm thấy
        """
        try:
            briefs_mgr = BriefsManager(self.db_path)
            # Lấy brief mới nhất
            briefs = briefs_mgr.list(version="v1.0.0")
            return briefs[0] if briefs else None
        except Exception as e:
            logger.warning(f"Could not get active brief: {e}")
            return None
    
    def save_feedback(
        self,
        feedback_type: str,
        message: str,
        auto_apply: bool = True
    ) -> int:
        """
        Lưu feedback vào database.
        
        Args:
            feedback_type: Type của feedback (bug, enhancement, clarification)
            message: Nội dung feedback
            auto_apply: Có tự động trigger pipeline không
            
        Returns:
            ID của feedback mới
            
        Raises:
            MidicoderError: Nếu có lỗi database
        """
        # Get active version
        version = "v1.0.0"  # Default version
        active_file = Path(".midicoder/active_version")
        if active_file.exists():
            version = active_file.read_text().strip()
        
        # Get brief_id if exists
        active_brief = self.get_active_brief()
        brief_id = active_brief.get("id") if active_brief else None
        
        try:
            with get_connection(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO feedback (version, brief_id, type, message, auto_applied)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (version, brief_id, feedback_type, message, 1 if auto_apply else 0)
                )
                return cursor.lastrowid
        except sqlite3.Error as e:
            raise EM.wrap_exception(
                e, ErrorCode.DB_CONNECTION_FAILED, 
                db_path=str(self.db_path),
                operation="save_feedback"
            )


# ============================================================================
# Status Helpers
# ============================================================================

def get_workspace_status() -> Dict[str, Any]:
    """
    Lấy workspace status.
    
    Returns:
        Dictionary với workspace status info
    """
    workspace_path = Path.cwd()
    midicoder_dir = workspace_path / ".midicoder"
    
    status = {
        "path": str(workspace_path),
        "initialized": midicoder_dir.exists()
    }
    
    if midicoder_dir.exists():
        # Check active version
        active_file = midicoder_dir / "active_version"
        if active_file.exists():
            status["active_version"] = active_file.read_text().strip()
    
    return status


def get_pipeline_progress() -> Dict[str, Dict[str, Any]]:
    """
    Lấy pipeline progress.
    
    Returns:
        Dictionary với progress cho mỗi stage
    """
    artifacts_mgr = ArtifactsManager(DB_ARTIFACTS)
    
    # Get active version
    active_file = Path(".midicoder/active_version")
    version = "v1.0.0"
    if active_file.exists():
        version = active_file.read_text().strip()
    
    # Check artifacts for each stage
    progress = {
        "brief": {"status": "not_started", "progress": 0},
        "contract": {"status": "not_started", "progress": 0},
        "mir": {"status": "not_started", "progress": 0},
        "code": {"status": "not_started", "progress": 0}
    }
    
    try:
        artifacts = artifacts_mgr.list()
        
        for artifact in artifacts:
            artifact_type = artifact.get("type", "")
            status = artifact.get("status", "pending")
            
            if artifact_type == "brief":
                progress["brief"] = {"status": status, "progress": 100 if status != "not_started" else 0}
            elif artifact_type == "contract":
                progress["contract"] = {"status": status, "progress": 100 if status != "not_started" else 0}
            elif artifact_type == "mir":
                progress["mir"] = {"status": status, "progress": 100 if status != "not_started" else 0}
            elif artifact_type == "plan":
                progress["code"] = {"status": status, "progress": 100 if status != "not_started" else 0}
                
    except Exception as e:
        logger.warning(f"Could not get pipeline progress: {e}")
    
    return progress


def get_artifacts_summary() -> Dict[str, int]:
    """
    Lấy artifact summary (counts by type).
    
    Returns:
        Dictionary với artifact counts
    """
    summary = {
        "briefs": 0,
        "contracts": 0,
        "mir": 0,
        "plans": 0,
        "code": 0
    }
    
    try:
        artifacts_mgr = ArtifactsManager(DB_ARTIFACTS)
        artifacts = artifacts_mgr.list()
        
        for artifact in artifacts:
            artifact_type = artifact.get("type", "").lower()
            if artifact_type == "brief":
                summary["briefs"] += 1
            elif artifact_type == "contract":
                summary["contracts"] += 1
            elif artifact_type == "mir":
                summary["mir"] += 1
            elif artifact_type == "plan":
                summary["plans"] += 1
            elif artifact_type == "code":
                summary["code"] += 1
                
    except Exception as e:
        logger.warning(f"Could not get artifacts summary: {e}")
    
    return summary


def get_neo4j_status() -> Dict[str, Any]:
    """
    Kiểm tra Neo4j connection status.
    
    Returns:
        Dictionary với Neo4j status
    """
    from midicoder.pipeline.config import get_config
    
    try:
        cfg = get_config()

        host = cfg.get("neo4j.host", "localhost")
        port = cfg.get("neo4j.port", 7687)
        
        # Try to connect
        import neo4j
        driver = neo4j.driver(f"bolt://{host}:{port}", auth=None)
        
        try:
            driver.verify_connectivity()
            driver.close()
            return {"status": "running", "host": f"{host}:{port}"}
        except Exception:
            driver.close()
            return {"status": "not_running", "host": f"{host}:{port}"}
            
    except ImportError:
        return {"status": "error", "message": "neo4j driver not installed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def get_versions_list() -> List[Dict[str, Any]]:
    """
    Lấy danh sách versions.
    
    Returns:
        List of version dictionaries
    """
    versions = []
    versions_dir = Path(".midicoder/versions")
    
    if not versions_dir.exists():
        return versions
    
    # Get active version
    active_file = Path(".midicoder/active_version")
    active_version = active_file.read_text().strip() if active_file.exists() else None
    
    for version_dir in sorted(versions_dir.iterdir()):
        if version_dir.is_dir():
            version_name = version_dir.name
            
            # Read metadata if exists
            metadata_file = version_dir / "metadata.yml"
            archived = False
            if metadata_file.exists():
                try:
                    metadata = yaml.safe_load(metadata_file.read_text())
                    archived = metadata.get("archived", False)
                except Exception:
                    pass
            
            versions.append({
                "version": version_name,
                "active": version_name == active_version,
                "archived": archived
            })
    
    return versions


def get_last_activity() -> Optional[Dict[str, Any]]:
    """
    Lấy last activity log.

    Returns:
        Last activity record hoặc None
    """
    try:
        from midicoder.storage import activity
        logs = activity.query_recent(days=365)

        if logs:
            log = logs[0]
            return {
                "timestamp": log.get("timestamp"),
                "action": log.get("action")
            }
    except Exception as e:
        logger.warning(f"Could not get last activity: {e}")

    return None


# ============================================================================
# Status Command
# ============================================================================

def get_status(json_output: bool = False) -> Dict[str, Any]:
    """
    Get complete project status.
    
    Args:
        json_output: Nếu True, format cho JSON output
        
    Returns:
        Complete status dictionary
    """
    workspace = get_workspace_status()
    
    if not workspace["initialized"]:
        status = {
            "metadata": {
                "version": "1.0.0",
                "timestamp": datetime.now().isoformat()
            },
            "workspace": workspace,
            "error": "Project not initialized. Create project from WebGUI first."
        }
        return status
    
    # Gather all status info
    status = {
        "metadata": {
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat()
        },
        "workspace": workspace,
        "active_version": workspace.get("active_version", "N/A"),
        "pipeline": get_pipeline_progress(),
        "artifacts": get_artifacts_summary(),
        "last_activity": get_last_activity(),
        "neo4j": get_neo4j_status(),
        "versions": get_versions_list()
    }
    
    return status


def format_status_human(status: Dict[str, Any]) -> str:
    """
    Format status cho human-readable output.
    
    Args:
        status: Status dictionary
        
    Returns:
        Formatted string
    """
    lines = []
    
    lines.append("Midicoder Project Status")
    lines.append("=" * 40)
    lines.append("")
    
    # Workspace info
    workspace = status.get("workspace", {})
    lines.append(f"Workspace: {workspace.get('path', 'N/A')}")
    lines.append(f"Initialized: {'Yes' if workspace.get('initialized') else 'No'}")
    lines.append("")
    
    if not workspace.get("initialized"):
        lines.append("Project not initialized. Create project from WebGUI first.")
        return "\n".join(lines)
    
    # Active version
    lines.append(f"Active Version: {status.get('active_version', 'N/A')}")
    lines.append("")
    
    # Pipeline progress
    lines.append("Pipeline Progress:")
    pipeline = status.get("pipeline", {})
    stage_icons = {"analyzed": "✓", "generated": "✓", "validated": "✓", "applied": "✓", "not_started": " ", "pending": " "}
    
    for stage, info in pipeline.items():
        icon = stage_icons.get(info.get("status"), " ")
        lines.append(f"  {stage.capitalize():12} [{icon}] {info.get('status', 'N/A')}")
    lines.append("")
    
    # Artifacts summary
    lines.append("Artifacts:")
    artifacts = status.get("artifacts", {})
    for artifact_type, count in artifacts.items():
        lines.append(f"  {artifact_type.capitalize():12} {count}")
    lines.append("")
    
    # Last activity
    last_activity = status.get("last_activity")
    if last_activity:
        timestamp = last_activity.get("timestamp", "N/A")
        action = last_activity.get("action", "N/A")
        lines.append(f"Last Activity: {timestamp} ({action})")
    else:
        lines.append("Last Activity: None")
    lines.append("")
    
    # Neo4j status
    neo4j = status.get("neo4j", {})
    neo4j_status = neo4j.get("status", "unknown")
    neo4j_host = neo4j.get("host", "N/A")
    lines.append(f"Neo4j: {'Running' if neo4j_status == 'running' else 'Not Running'} ({neo4j_host})")
    lines.append("")
    
    # Versions
    lines.append("Versions:")
    versions = status.get("versions", [])
    for version in versions:
        marker = "* " if version.get("active") else "  "
        status_str = ""
        if version.get("archived"):
            status_str = " (archived)"
        lines.append(f"{marker}{version.get('version')}{status_str}")
    
    return "\n".join(lines)


# ============================================================================
# Feedback Command
# ============================================================================

def submit_feedback(
    feedback_type: str,
    message: str,
    auto_apply: bool = True
) -> int:
    """
    Submit feedback.
    
    Args:
        feedback_type: Type của feedback (bug, enhancement, clarification)
        message: Nội dung feedback
        auto_apply: Có tự động trigger pipeline không
        
    Returns:
        ID của feedback mới
        
    Raises:
        MidicoderError: Nếu feedback type không hợp lệ
    """
    # Validate feedback type
    if not validate_feedback_type(feedback_type):
        raise EM.raise_error(
            ErrorCode.UTIL_INVALID_FEEDBACK_TYPE,
            feedback_type=feedback_type,
            valid_types=", ".join(VALID_FEEDBACK_TYPES)
        )
    
    # Save feedback
    mgr = FeedbackManager()
    feedback_id = mgr.save_feedback(
        feedback_type=feedback_type,
        message=message,
        auto_apply=auto_apply
    )
    
    logger.info(
        f"Feedback saved (id={feedback_id}, type={feedback_type})",
        extra={"feedback_id": feedback_id, "type": feedback_type}
    )
    
    return feedback_id


# ============================================================================
# Config Commands
# ============================================================================

def config_show():
    """
    Hiển thị current configuration.
    
    Output config JSON formatted.
    """
    from midicoder.pipeline.config import get_config
    
    cfg = get_config()
    all_settings = cfg.load_global_config().get_all()

    _log_activity("settings.displayed", "config", details={"settings_count": len(all_settings)})


def config_set(key: str, value: str):
    """
    Set configuration value với schema validation.
    
    Args:
        key: Config key (ví dụ: "llm.model")
        value: Config value
        
    Raises:
        MidicoderError: Nếu key không hợp lệ
    """
    # Validate key
    if not validate_config_key(key):
        valid_keys = []
        schema = get_config_schema()
        for section, fields in schema.items():
            for field in fields.keys():
                valid_keys.append(f"{section}.{field}")
        
        raise EM.raise_error(
            ErrorCode.UTIL_INVALID_CONFIG_KEY,
            key=key,
            valid_keys=", ".join(valid_keys[:10]) + "..."
        )
    
    # Set value
    from midicoder.pipeline.config import get_config
    
    cfg = get_config()
    
    try:
        cfg.set(key, value)
        _log_activity("settings.set", "config", details={"key": key, "value": value})
    except Exception as e:
        raise EM.wrap_exception(
            e, ErrorCode.UTIL_CONFIG_WRITE_FAILED,
            key=key, value=value
        )


def config_reset(key: Optional[str] = None):
    """
    Reset configuration về mặc định.
    
    Args:
        key: Config key để reset (nếu None, reset toàn bộ)
    """
    from midicoder.pipeline.config import get_config
    
    cfg = get_config()
    
    try:
        cfg.reset(key)
        _log_activity("settings.reset", "config", details={"key": key if key else "all"})
    except Exception as e:
        raise EM.wrap_exception(
            e, ErrorCode.CONFIG_WRITE_FAILED,
            key=key or "all"
        )


# ============================================================================
# CLI Command Wrappers (cho cli.py integration)
# ============================================================================

def run_status(json_output: bool = False):
    """
    Run status command.
    
    Args:
        json_output: Nếu True, output JSON format
    """
    status = get_status(json_output=json_output)

    _log_activity("status.displayed", "system", details={"json_output": json_output})


def run_feedback(
    feedback_type: str = "clarification",
    message: Optional[str] = None,
    no_auto_apply: bool = False
):
    """
    Run feedback command.
    
    Args:
        feedback_type: Type của feedback
        message: Nội dung feedback (nếu None, hỏi interactive)
        no_auto_apply: Nếu True, không trigger pipeline
    """
    if message is None:
        message = ""  # Non-interactive: empty feedback

    auto_apply = not no_auto_apply
    
    try:
        feedback_id = submit_feedback(
            feedback_type=feedback_type,
            message=message,
            auto_apply=auto_apply
        )

        _log_activity("feedback.saved", "feedback", str(feedback_id),
                      details={"feedback_id": feedback_id, "type": feedback_type, "auto_apply": auto_apply})

        if auto_apply:
            _log_activity("feedback.auto_apply_info", "feedback", str(feedback_id))
        else:
            _log_activity("feedback.manual_apply_info", "feedback", str(feedback_id))

    except MidicoderError as e:
        _log_activity("feedback.error", "feedback", details={"error": str(e)}, status="error")
        raise SystemExit(1)


def run_config_show():
    """Run config show command."""
    config_show()


def run_config_set(key: str, value: str):
    """Run config set command."""
    config_set(key, value)


def run_config_reset(key: Optional[str] = None):
    """Run config reset command."""
    config_reset(key)