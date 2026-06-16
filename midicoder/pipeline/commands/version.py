"""
Version Management Commands Implementation.

Lệnh `midicoder version` quản lý versions cho Midicoder project.

Version metadata lưu kép (cả hai đều bắt buộc):
  - SQLite global: projects.db table `versions` (multi-project registry, active state)
  - File system: .midicoder/versions/{v}/metadata.yml (on-disk identity, git trackable)

SQLite cho biết project nào đang active, version nào active ở máy hiện tại.
File system metadata.yml cho phép clone repo và hiểu project mà không cần DB.

Các sub-commands:
- create: Tạo version mới
- use: Switch version
- list: List tất cả versions
- delete: Xóa version
"""

import re
import hashlib
import shutil
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM
from midicoder.storage.projects import ProjectsManager
from midicoder.storage.sqlite import get_connection
from midicoder.storage.activity import log


# SemVer regex pattern (strict)
SEMVER_PATTERN = re.compile(
    r'^v?\d+\.\d+\.\d+(-[a-zA-Z0-9]+(\.[a-zA-Z0-9]+)*)?(\+[a-zA-Z0-9]+(\.[a-zA-Z0-9]+)*)?$'
)


def validate_version_name(name: str) -> bool:
    return bool(SEMVER_PATTERN.match(name))


def normalize_version(name: str) -> str:
    """Luôn trả về version string có prefix 'v'.

    Ví dụ: "1.0.0" → "v1.0.0", "v1.0.0" → "v1.0.0"
    Đây là single source of truth cho format version.
    """
    if not name:
        return name
    stripped = name.lstrip("v")
    return f"v{stripped}"


def _version_query_variants(name: str) -> list:
    """Trả về danh sách variants để query DB — cả có/không có prefix 'v'.

    Dùng cho read path để khớp data cũ đã lưu không có 'v'.
    """
    if not name:
        return []
    variants = set()
    variants.add(name)
    stripped = name.lstrip("v")
    variants.add(stripped)
    variants.add(f"v{stripped}")
    return list(variants)


def _log_activity(action: str, resource_type: str = "version", resource_id: str = "", details: dict = None, status: str = "success") -> None:
    """Ghi activity log vào artifacts.db activity_log table."""
    log(action=action, resource_type=resource_type, resource_id=resource_id, details=details, status=status)


def _get_project_id() -> str:
    """Lấy project_id từ path của project hiện tại."""
    project_root = _get_project_root()
    cwd = str(project_root.resolve())
    return hashlib.md5(cwd.encode()).hexdigest()[:12]


def _get_project_root() -> Path:
    """Get the active project root directory.
    
    Priority: ConfigManager._project_path → active project from projects.db → Path.cwd()
    """
    try:
        from midicoder.pipeline.config import get_config
        cfg = get_config()
        if cfg._project_path:
            return Path(cfg._project_path)
    except Exception:
        pass
    # Fallback: query projects.db for active project
    try:
        mgr = _get_manager()
        active = mgr.get_active()
        if active and active.get("path"):
            return Path(active["path"])
    except Exception:
        pass
    # Final fallback
    return Path.cwd()


def get_workspace_dir() -> Path:
    workspace_dir = _get_project_root() / ".midicoder"
    if not workspace_dir.exists():
        EM.raise_error(
            ErrorCode.CONFIG_READ_FAILED,
            message="Workspace chưa được khởi tạo. Hãy tạo project từ WebGUI trước.",
            path=str(workspace_dir),
        )
    return workspace_dir


def get_versions_dir() -> Path:
    return get_workspace_dir() / "versions"


def get_config_file() -> Path:
    return get_workspace_dir() / "config" / "midicoder.yml"


def load_project_config() -> dict:
    config_file = get_config_file()
    if not config_file.exists():
        EM.raise_error(ErrorCode.CONFIG_READ_FAILED, path=str(config_file))
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        EM.raise_error(ErrorCode.CONFIG_FORMAT_INVALID, path=str(config_file), cause=e)


def save_project_config(config: dict) -> None:
    config_file = get_config_file()
    config_file.parent.mkdir(parents=True, exist_ok=True)
    with open(config_file, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)


def _get_manager() -> ProjectsManager:
    """Lấy ProjectsManager với đúng DB path absolute."""
    from midicoder.storage.projects import DB_PROJECTS
    mgr = ProjectsManager(db_path=DB_PROJECTS)
    mgr.init()
    return mgr


# ---------------------------------------------------------------------------
# Version operations — metadata trong SQLite + file system (backward compat)
# ---------------------------------------------------------------------------


def get_active_version() -> Optional[str]:
    """Lấy active version name từ SQLite, fallback vào config YAML."""
    try:
        mgr = _get_manager()
        project_id = _get_project_id()
        v = mgr.version_get_active(project_id)
        if v:
            return v.get("version_name")
    except Exception:
        pass
    # Fallback: check config file
    config = load_project_config()
    return config.get("active_version")


def get_max_versions() -> int:
    config = load_project_config()
    return config.get("max_versions", 5)


def list_versions() -> list[dict]:
    """List tất cả versions từ SQLite + file system metadata."""
    versions = []
    try:
        mgr = _get_manager()
        project_id = _get_project_id()
        for v in mgr.version_list(project_id):
            vname = normalize_version(v.get("version_name", ""))
            metadata = {
                "version": vname,
                "status": v.get("status", "draft"),
                "parent_version": normalize_version(v.get("parent_version")) if v.get("parent_version") else None,
                "created_at": v.get("created_at", ""),
                "active": bool(v.get("active")),
            }
            # Load thêm metadata từ file nếu có
            mf = get_versions_dir() / vname / "metadata.yml"
            if mf.exists():
                try:
                    with open(mf, "r", encoding="utf-8") as f:
                        metadata.update(yaml.safe_load(f) or {})
                except Exception:
                    pass
            versions.append({"name": vname, "metadata": metadata})
    except Exception:
        # Fallback: scan từ file system
        versions_dir = get_versions_dir()
        if versions_dir.exists():
            for vd in versions_dir.iterdir():
                if vd.is_dir():
                    mf = vd / "metadata.yml"
                    if mf.exists():
                        try:
                            with open(mf, "r", encoding="utf-8") as f:
                                versions.append({"name": vd.name, "metadata": yaml.safe_load(f) or {}})
                        except Exception:
                            pass

    versions.sort(key=lambda v: v["metadata"].get("created_at", ""), reverse=True)
    return versions


def create_version(name: str, from_version: Optional[str] = None) -> None:
    """Tạo version mới — metadata SQLite + file system.

    SQLite là nguồn sự thật của status. Sau khi SQLite hoàn tất,
    sync tất cả metadata.yml để khớp với SQLite status.

    Note: from_version parameter kept for CLI backward compat but not used in WebGUI flow.
    """
    # Validate
    if not validate_version_name(name):
        EM.raise_error(
            ErrorCode.VERSION_INVALID_NAME,
            version=name,
            suggestion="Sử dụng SemVer format (ví dụ: v1.0.0, v1.0.1-alpha)",
        )
    # Normalize: luôn có prefix 'v'
    name = normalize_version(name)

    # Check if already exists (file system check)
    version_dir = get_versions_dir() / name
    if version_dir.exists():
        EM.raise_error(ErrorCode.VERSION_ALREADY_EXISTS, version=name)

    # 1. Xác định parent version: version đang active hiện tại
    #    Version mới sẽ kế thừa toàn bộ source code từ parent.
    mgr = _get_manager()
    project_id = _get_project_id()
    active_version_info = mgr.version_get_active(project_id)
    parent_version_name = active_version_info.get("version_name") if active_version_info else None
    # Normalize parent version (luôn có prefix 'v')
    parent_version_normalized = normalize_version(parent_version_name) if parent_version_name else None

    # 2. Save into SQLite (bắt buộc — fail thì abort)
    #    SQLite lifecycle: archive các version status='inbuild', deselect active, insert mới
    mgr.version_create(
        project_id=project_id,
        version_name=name,
        parent_version=parent_version_normalized,
        set_active=True,
    )
    _log_activity("version.saved_to_sqlite", resource_id=name)

    # 3. Create file system structure
    version_dir.mkdir(parents=True, exist_ok=True)
    _log_activity("version.dir_created", resource_id=name,
                  details={"path": str(version_dir.relative_to(_get_project_root()))})
    (version_dir / "src").mkdir(parents=True, exist_ok=True)

    # 4. Copy source code từ parent version (nếu có)
    if parent_version_name:
        parent_src_dir = get_versions_dir() / parent_version_name / "src"
        new_src_dir = version_dir / "src"
        if parent_src_dir.exists():
            # Copy toàn bộ nội dung src từ parent → new version
            for item in parent_src_dir.iterdir():
                src = item
                dst = new_src_dir / item.name
                if src.is_dir():
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                else:
                    shutil.copy2(src, dst)
            _log_activity("version.src_inherited", resource_id=name,
                          details={"from": parent_version_name})
        # else: parent has no src directory — nothing to inherit

    # 4.5. Clone SQLite data từ parent version (briefs, artifacts, decisions)
    if parent_version_normalized:
        try:
            _clone_sqlite_data(parent_version_normalized, name)
            _log_activity("version.sqlite_data_inherited", resource_id=name,
                          details={"from": parent_version_name})
        except Exception:
            _log_activity("version.sqlite_data_inherit_failed", resource_id=name,
                          details={"from": parent_version_name}, status="failed")

    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    metadata = {
        "version": name,
        "created_at": now,
        "parent_version": parent_version_normalized,
        "status": "draft",
        "pipeline": {"brief": "none", "contract": "none", "ir": "none", "code": "none"},
        "artifacts": {"briefs": 0, "contracts": 0, "files": 0, "lines": 0},
    }
    mf = version_dir / "metadata.yml"
    with open(mf, "w", encoding="utf-8") as f:
        yaml.dump(metadata, f, default_flow_style=False, allow_unicode=True)

    # 5. Update config.active_version
    config = load_project_config()
    config["active_version"] = name
    save_project_config(config)

    # 6. Sync metadata.yml từ SQLite (SQLite là nguồn sự thật của status)
    #    Sau version_create(), các version status='inbuild' đã bị archive trong SQLite.
    #    Đọc lại từ SQLite và sync tất cả metadata.yml cho khớp.
    _sync_metadata_from_sqlite(project_id)

    # 7. Auto-cleanup
    _auto_cleanup()


def _parse_semver(ver: str) -> tuple:
    """Parse v1.2.3 or v1.2.3-beta → (1, 2, 3)."""
    m = re.match(r'^v(\d+)\.(\d+)\.(\d+)', ver)
    if m:
        return (int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return (0, 0, 0)


def check_create_version(name: str) -> dict:
    """Kiểm tra impact trước khi tạo version mới.

    Trả về dict:
      - error: str | None — nếu có lỗi validate
      - will_archive: list[dict] — versions sẽ bị archive (status='inbuild')
      - will_delete: list[dict] — versions sẽ bị auto-cleanup
      - max_versions: int
      - current_count: int
    """
    # Normalize: luôn có prefix 'v'
    name = normalize_version(name)

    # Validate semver
    if not validate_version_name(name):
        return {
            "error": f"Tên '{name}' không đúng định dạng SemVer. Ví dụ: v1.0.0, v2.1.0, v1.0.0-beta",
            "will_archive": [],
            "will_delete": [],
            "max_versions": 5,
            "current_count": 0,
            "parent_version": None,
        }

    mgr = _get_manager()
    active_project = mgr.get_active()
    if not active_project:
        return {
            "error": None,
            "will_archive": [],
            "will_delete": [],
            "max_versions": 5,
            "current_count": 0,
            "parent_version": None,
        }

    project_id = active_project["project_id"]
    max_versions = get_max_versions()

    # Xác định parent: version đang active
    active_version_info = mgr.version_get_active(project_id)
    parent_version_name = active_version_info.get("version_name") if active_version_info else None

    # Check already exists
    existing = mgr.version_get(project_id, name)
    if existing:
        return {
            "error": f"Version '{name}' đã tồn tại",
            "will_archive": [],
            "will_delete": [],
            "max_versions": max_versions,
            "current_count": 0,
            "parent_version": parent_version_name,
        }

    # Get all versions
    versions = mgr.version_list(project_id)
    current_count = len(versions)

    # Semver must be greater than existing
    new_ver_tuple = _parse_semver(name)
    max_existing = max((_parse_semver(v.get("version_name", "")) for v in versions), default=(0, 0, 0))
    if new_ver_tuple <= max_existing:
        max_ver_name = max(
            (v.get("version_name", "") for v in versions if _parse_semver(v.get("version_name", "")) == max_existing),
            default=""
        )
        return {
            "error": f"Version '{name}' phải lớn hơn version cao nhất hiện có ('{max_ver_name}')",
            "will_archive": [],
            "will_delete": [],
            "max_versions": max_versions,
            "current_count": current_count,
            "parent_version": parent_version_name,
        }

    # Will archive: versions with status='inbuild'
    will_archive = []
    for v in versions:
        if v.get("status") == "inbuild":
            will_archive.append({
                "version": v.get("version_name", ""),
                "status": v.get("status", "draft"),
            })

    # Will delete: if exceeding max_versions
    will_delete = []
    if current_count + 1 > max_versions:
        to_delete_count = current_count + 1 - max_versions

        def sort_key(vv):
            status = vv.get("status", "draft")
            created = vv.get("created_at", "")
            status_order = {"archived": 0, "draft": 1, "inbuild": 2}.get(status, 3)
            return (status_order, created)

        sorted_versions = sorted(versions, key=sort_key)
        deleted = 0
        for v in sorted_versions:
            if deleted >= to_delete_count:
                break
            if v.get("active") == 1:
                continue
            will_delete.append({
                "version": v.get("version_name", ""),
                "status": v.get("status", "draft"),
                "created_at": v.get("created_at", ""),
            })
            deleted += 1

    return {
        "error": None,
        "will_archive": will_archive,
        "will_delete": will_delete,
        "max_versions": max_versions,
        "current_count": current_count,
        "parent_version": active_version_info.get("version_name") if active_version_info else None,
    }


def use_version(name: str) -> None:
    """Switch sang version khác — SQLite + config file."""
    name = normalize_version(name)

    # Validate version tồn tại trong SQLite (không require directory trong filesystem)
    mgr = _get_manager()
    project_id = _get_project_id()
    existing = mgr.version_get(project_id, name)
    if not existing:
        EM.raise_error(ErrorCode.VERSION_NOT_FOUND, version=name)

    # Tạo metadata directory nếu chưa tồn tại (backward compat cho version legacy chỉ trong SQLite)
    try:
        version_dir = get_versions_dir() / name
        if not version_dir.exists():
            version_dir.mkdir(parents=True, exist_ok=True)
            meta_file = version_dir / "metadata.yml"
            if not meta_file.exists():
                import yaml
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                meta = {
                    "version": name,
                    "status": existing.get("status", "draft"),
                    "created_at": existing.get("created_at", now),
                    "description": f"Version {name}",
                    "parent_version": None,
                }
                with open(meta_file, "w", encoding="utf-8") as f:
                    yaml.dump(meta, f, default_flow_style=False, allow_unicode=True)
    except Exception:
        pass

    mgr.version_use(project_id, name)

    # Config file
    config = load_project_config()
    config["active_version"] = name
    save_project_config(config)

    # KHÔNG touch status metadata.yml khi switch version.
    # Status chỉ thay đổi bởi:
    #   - create_version() → archive tất cả version cũ
    #   - freeze_brief()   → chuyển draft → active

    # Log switch event
    new_meta = get_versions_dir() / name / "metadata.yml"
    try:
        with open(new_meta, "r", encoding="utf-8") as f:
            meta = yaml.safe_load(f) or {}
        _log_activity("version.switched", resource_id=name,
                      details={"status": meta.get("status", "draft"),
                               "parent_version": meta.get("parent_version")})
    except Exception:
        _log_activity("version.switched", resource_id=name)


def list_versions_command() -> None:
    """CLI list versions — no longer used in WebGUI mode, kept for backward compat."""
    pass


def delete_version(name: str, force: bool = False) -> None:
    """Xóa version — SQLite + file system."""
    name = normalize_version(name)

    version_dir = get_versions_dir() / name
    if not version_dir.exists():
        EM.raise_error(ErrorCode.VERSION_NOT_FOUND, version=name)

    active_version = get_active_version()
    if name == active_version and not force:
        EM.raise_error(
            ErrorCode.VERSION_DELETE_ACTIVE,
            version=name,
            suggestion="Use --force to delete active version, or switch to another version first",
        )

    # SQLite delete (bắt buộc — global projects.db)
    mgr = _get_manager()
    project_id = _get_project_id()
    mgr.version_delete(project_id, name, force=force)

    # Xóa data SQLite project-level (.midicoder/data/)
    try:
        _delete_sqlite_data(name)
        _log_activity("version.sqlite_data_removed", resource_id=name)
    except Exception:
        pass

    # File system delete
    try:
        shutil.rmtree(version_dir)
        _log_activity("version.deleted", resource_id=name,
                      details={"path": str(version_dir.relative_to(_get_project_root()))})
    except Exception as e:
        EM.raise_error(ErrorCode.VERSION_CLEANUP_FAILED, version=name, cause=e)

    # Update active if deleted was active
    if name == active_version:
        config = load_project_config()
        versions = list_versions()
        if versions:
            new_active = versions[0]["name"]
            config["active_version"] = new_active
            save_project_config(config)
            mgr.version_use(_get_project_id(), new_active)
            # KHÔNG set status='inbuild' — status chỉ đổi khi brief frozen
            _log_activity("version.new_active_set", resource_id=new_active,
                          details={"reason": "previous_active_deleted"})
        else:
            if "active_version" in config:
                del config["active_version"]
            save_project_config(config)
            _log_activity("version.no_versions_remaining")

    _log_activity("version.delete_completed", resource_id=name)


def _sync_metadata_from_sqlite(project_id: str) -> None:
    """Sync metadata.yml từ SQLite (SQLite là nguồn sự thật).

    Sau khi SQLite thay đổi status hay parent_version,
    đọc lại từ SQLite và cập nhật metadata.yml của tất cả versions cho khớp.
    Fields sync: status, parent_version.
    """
    try:
        mgr = _get_manager()
        versions = mgr.version_list(project_id)
        versions_dir = get_versions_dir()

        for v in versions:
            vname = v.get("version_name", "")
            sqlite_status = v.get("status", "draft")
            sqlite_parent = v.get("parent_version")
            meta_file = versions_dir / vname / "metadata.yml"
            if meta_file.exists():
                try:
                    modified = False
                    with open(meta_file, "r", encoding="utf-8") as f:
                        meta = yaml.safe_load(f) or {}
                    if meta.get("status") != sqlite_status:
                        meta["status"] = sqlite_status
                        modified = True
                    if meta.get("parent_version") != sqlite_parent:
                        meta["parent_version"] = sqlite_parent
                        modified = True
                    if modified:
                        with open(meta_file, "w", encoding="utf-8") as f:
                            yaml.dump(meta, f, default_flow_style=False, allow_unicode=True)
                except Exception:
                    pass
    except Exception:
        pass


def _auto_cleanup() -> None:
    """Auto-cleanup versions khi vượt quá max_versions."""
    versions = list_versions()
    max_versions = get_max_versions()
    active_version = get_active_version()

    if len(versions) <= max_versions:
        return

    def sort_key(v):
        status = v["metadata"].get("status", "")
        created = v["metadata"].get("created_at", "")
        status_order = {"archived": 0, "draft": 1, "inbuild": 2}.get(status, 3)
        return (status_order, created)

    versions.sort(key=sort_key)

    to_delete = []
    for v in versions:
        if v["name"] == active_version:
            continue
        if len(to_delete) >= len(versions) - max_versions:
            break
        to_delete.append(v["name"])

    # Xóa cả SQLite entry lẫn file system
    mgr = _get_manager()
    project_id = _get_project_id()
    versions_dir = get_versions_dir()
    for vn in to_delete:
        # SQLite delete
        try:
            mgr.version_delete(project_id, vn, force=True)
            _log_activity("version.auto_cleanup_sqlite", resource_id=vn)
        except Exception:
            pass
        # File system delete
        vd = versions_dir / vn
        try:
            shutil.rmtree(vd, ignore_errors=True)
            _log_activity("version.auto_cleanup_dir", resource_id=vn)
        except Exception:
            pass
        # Xóa data SQLite project-level (.midicoder/data/)
        try:
            _delete_sqlite_data(vn)
            _log_activity("version.auto_cleanup_data", resource_id=vn)
        except Exception:
            pass


# ============================================================================
# SQLite project-level data management
# ============================================================================

def _get_data_dir() -> Path:
    """Lấy path đến .midicoder/data/ của project đang active."""
    return _get_project_root() / ".midicoder" / "data"


def _delete_sqlite_data(version_name: str) -> None:
    """Xóa tất cả dữ liệu thuộc về version trong các SQLite DB project-level.

    Xóa theo đúng thứ tự để tôn trọng foreign key constraints:
    1. clarifications (FK → briefs.brief_id) — xóa theo brief_ids của version
    2. brief_revisions (không có FK constraint) — xóa theo version
    3. briefs (FK → artifacts.brief_id via CASCADE) — xóa theo version
    4. artifacts — xóa theo version (CASCADE xóa clarifications đã được xóa ở trên)
    5. decisions — xóa theo related_version
    """
    data_dir = _get_data_dir()
    variants = _version_query_variants(version_name)
    # Ensure we have at least the normalized + stripped forms
    vname_stripped = version_name.lstrip("v")
    if vname_stripped not in variants:
        variants.append(vname_stripped)
    if version_name not in variants:
        variants.append(version_name)

    # 1. briefs.db: xóa clarifications → brief_revisions → briefs
    briefs_db = data_dir / "briefs.db"
    if briefs_db.exists():
        from midicoder.storage.sqlite import get_connection
        try:
            with get_connection(briefs_db) as conn:
                # Lấy tất cả brief_id thuộc version này (khớp tất cả variants)
                placeholders = ",".join(["?"] * len(variants))
                rows = conn.execute(
                    f"SELECT brief_id FROM briefs WHERE version IN ({placeholders})",
                    variants
                ).fetchall()
                brief_ids = [r[0] for r in rows]

                if brief_ids:
                    placeholders_c = ",".join(["?"] * len(brief_ids))
                    # Xóa clarifications (FK → briefs)
                    conn.execute(
                        f"DELETE FROM clarifications WHERE brief_id IN ({placeholders_c})",
                        brief_ids
                    )
                    # Xóa brief_revisions theo version
                    placeholders_r = ",".join(["?"] * len(variants))
                    conn.execute(
                        f"DELETE FROM brief_revisions WHERE version IN ({placeholders_r})",
                        variants
                    )

                # Xóa briefs theo version
                placeholders_b = ",".join(["?"] * len(variants))
                conn.execute(
                    f"DELETE FROM briefs WHERE version IN ({placeholders_b})",
                    variants
                )
        except Exception:
            pass

    # 2. artifacts.db: xóa artifacts theo version
    artifacts_db = data_dir / "artifacts.db"
    if artifacts_db.exists():
        from midicoder.storage.sqlite import get_connection
        try:
            with get_connection(artifacts_db) as conn:
                placeholders_a = ",".join(["?"] * len(variants))
                conn.execute(
                    f"DELETE FROM artifacts WHERE version IN ({placeholders_a})",
                    variants
                )
        except Exception:
            pass

    # 3. provenance.db: xóa decisions theo related_version, giữ lineage (không có field version)
    provenance_db = data_dir / "provenance.db"
    if provenance_db.exists():
        from midicoder.storage.sqlite import get_connection
        try:
            with get_connection(provenance_db) as conn:
                conn.execute(
                    "DELETE FROM decisions WHERE related_version = ? OR related_version = ?",
                    (version_name, vname)
                )
        except Exception:
            pass


def _clone_sqlite_data(parent_version: str, new_version: str) -> None:
    """Clone dữ liệu SQLite từ parent version sang version mới.

    Copy tất cả records thuộc về parent version và tạo bản sao với version mới.
    Đây là cơ chế inherit — user không phải bắt đầu từ scratch.

    Thứ tự clone (tôn trọng FK):
    1. briefs → clarifications (clone brief + copy Q&A)
    2. artifacts (clone tất cả artifacts: analysis, contract, mir, plan)
    3. decisions (clone architectural decisions)

    Note: Đọc data cũ với variants (backward compat), ghi mới luôn với prefix 'v'.
    """
    data_dir = _get_data_dir()
    # Normalize: luôn ghi mới với prefix 'v'
    normalized_new = normalize_version(new_version)
    # Read path: query cả variants để khớp data cũ
    parent_variants = _version_query_variants(parent_version)
    parent_stripped = parent_version.lstrip("v")
    new_stripped = normalized_new.lstrip("v")

    # Brief ID mapping: old_brief_id → new_brief_id (dùng khi clone artifacts)
    brief_id_map = {}

    # 1. briefs.db: clone briefs + clarifications
    briefs_db = data_dir / "briefs.db"
    if briefs_db.exists():
        from midicoder.storage.sqlite import get_connection
        try:
            with get_connection(briefs_db) as conn:
                # Tìm tất cả briefs của parent version (query tất cả variants)
                placeholders = ", ".join(["?"] * len(parent_variants))
                parent_briefs = conn.execute(
                    f"SELECT * FROM briefs WHERE version IN ({placeholders})",
                    parent_variants
                ).fetchall()

                for brief in parent_briefs:
                    brief_dict = dict(brief)
                    # Tạo brief_id mới cho version mới
                    old_brief_id = brief_dict.get("brief_id", "")
                    new_brief_id = old_brief_id.replace(parent_stripped, new_stripped, 1)
                    if new_brief_id == old_brief_id:
                        # Fallback: thêm suffix version mới
                        new_brief_id = f"{old_brief_id}-{new_stripped}"

                    # Ghi mapping để clone artifacts dùng sau
                    brief_id_map[old_brief_id] = new_brief_id

                    try:
                        conn.execute(
                            """INSERT INTO briefs
                            (brief_id, version, title, content, status, content_hash, created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))""",
                            (
                                new_brief_id, normalized_new,
                                brief_dict.get("title"),
                                brief_dict.get("content"),
                                "draft",  # Luôn set draft cho version mới
                                brief_dict.get("content_hash"),
                            )
                        )

                        # Clone clarifications — RESET round=0 để clarify counter mới bắt đầu từ 0
                        # Giữ nguyên Q&A history để user thấy context, nhưng round=0
                        # giúp max_rounds check (backend) đếm từ đầu cho version mới
                        clarifications = conn.execute(
                            "SELECT * FROM clarifications WHERE brief_id = ?",
                            (old_brief_id,)
                        ).fetchall()
                        for clar in clarifications:
                            clar_dict = dict(clar)
                            conn.execute(
                                """INSERT INTO clarifications
                                (brief_id, round, question, answer, is_memo, created_at)
                                VALUES (?, ?, ?, ?, ?, datetime('now'))""",
                                (
                                    new_brief_id,
                                    0,  # Reset round → clarify counter = 0 cho version mới
                                    clar_dict.get("question"),
                                    clar_dict.get("answer"),
                                    clar_dict.get("is_memo", 0),
                                )
                            )

                        # Chỉ tạo 1 revision "cloned" — không clone history cũ
                        # Lưu content_snapshot để diff so với revision này không tính toàn bộ content là "added"
                        import hashlib
                        content_snapshot = brief_dict.get("content", "")
                        snapshot_hash = hashlib.sha256(content_snapshot.encode()).hexdigest() if content_snapshot else None
                        try:
                            conn.execute(
                                """INSERT INTO brief_revisions
                                (brief_id, version, revision_number, event, snapshot_hash, diff_summary, content_snapshot, created_at)
                                VALUES (?, ?, 1, 'cloned', ?, ?, ?, datetime('now'))""",
                                (new_brief_id, normalized_new, snapshot_hash, f"Cloned from {parent_version}", content_snapshot)
                            )
                        except Exception:
                            pass
                    except Exception:
                        pass  # Skip nếu brief_id trùng hoặc có lỗi
        except Exception:
            pass

    # 2. artifacts.db: clone artifacts
    artifacts_db = data_dir / "artifacts.db"
    if artifacts_db.exists():
        from midicoder.storage.sqlite import get_connection
        try:
            with get_connection(artifacts_db) as conn:
                # Query tất cả variants của parent version (có/không có 'v' prefix)
                parent_artifact_variants = _version_query_variants(parent_version)
                placeholders = ", ".join(["?"] * len(parent_artifact_variants))
                parent_artifacts = conn.execute(
                    f"SELECT * FROM artifacts WHERE version IN ({placeholders})",
                    parent_artifact_variants
                ).fetchall()

                for art in parent_artifacts:
                    art_dict = dict(art)
                    old_artifact_id = art_dict.get("artifact_id", "")
                    new_artifact_id = old_artifact_id.replace(parent_stripped, new_stripped, 1)
                    if new_artifact_id == old_artifact_id:
                        new_artifact_id = f"{old_artifact_id}-{new_stripped}"

                    # Map brief_id từ parent → new (quan trọng: analysis phải link tới brief mới)
                    old_brief_ref = art_dict.get("brief_id")
                    new_brief_ref = brief_id_map.get(old_brief_ref, old_brief_ref)

                    try:
                        conn.execute(
                            """INSERT INTO artifacts
                            (artifact_id, type, name, version, brief_id, content, status, metadata, created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))""",
                            (
                                new_artifact_id,
                                art_dict.get("type"),
                                art_dict.get("name"),
                                normalized_new,
                                new_brief_ref,
                                art_dict.get("content"),
                                art_dict.get("status", "pending"),
                                art_dict.get("metadata"),
                            )
                        )
                    except Exception:
                        pass
        except Exception:
            pass

    # 3. provenance.db: clone decisions
    provenance_db = data_dir / "provenance.db"
    if provenance_db.exists():
        from midicoder.storage.sqlite import get_connection
        try:
            with get_connection(provenance_db) as conn:
                parent_decisions = conn.execute(
                    "SELECT * FROM decisions WHERE related_version = ? OR related_version = ?",
                    (parent_version, parent_stripped)
                ).fetchall()

                for dec in parent_decisions:
                    dec_dict = dict(dec)
                    old_decision_id = dec_dict.get("decision_id", "")
                    new_decision_id = old_decision_id.replace(parent_stripped, new_stripped, 1)
                    if new_decision_id == old_decision_id:
                        new_decision_id = f"{old_decision_id}-{new_stripped}"

                    try:
                        conn.execute(
                            """INSERT INTO decisions
                            (decision_id, title, status, description, rationale, consequences, decided_by, related_brief_id, related_version, decision_date)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))""",
                            (
                                new_decision_id,
                                dec_dict.get("title"),
                                dec_dict.get("status", "proposed"),
                                dec_dict.get("description"),
                                dec_dict.get("rationale"),
                                dec_dict.get("consequences"),
                                dec_dict.get("decided_by"),
                                dec_dict.get("related_brief_id"),
                                normalized_new,
                            )
                        )
                    except Exception:
                        pass
        except Exception:
            pass
