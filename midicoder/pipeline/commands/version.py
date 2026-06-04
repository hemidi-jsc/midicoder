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
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import click
import yaml

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM
from midicoder.storage.projects import ProjectsManager


# SemVer regex pattern (strict)
SEMVER_PATTERN = re.compile(
    r'^v?\d+\.\d+\.\d+(-[a-zA-Z0-9]+(\.[a-zA-Z0-9]+)*)?(\+[a-zA-Z0-9]+(\.[a-zA-Z0-9]+)*)?$'
)


def validate_version_name(name: str) -> bool:
    return bool(SEMVER_PATTERN.match(name))


def _get_project_id() -> str:
    """Lấy project_id từ path của project hiện tại."""
    cwd = str(Path.cwd().resolve())
    return hashlib.md5(cwd.encode()).hexdigest()[:12]


def get_workspace_dir() -> Path:
    workspace_dir = Path.cwd() / ".midicoder"
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
    mgr = ProjectsManager()
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
            vname = v.get("version_name", "")
            metadata = {
                "version": vname.lstrip("v"),
                "status": v.get("status", "draft"),
                "parent_version": v.get("parent_version"),
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
    """Tạo version mới — metadata SQLite + file system."""
    # Validate
    if not validate_version_name(name):
        EM.raise_error(
            ErrorCode.VERSION_INVALID_NAME,
            version=name,
            suggestion="Sử dụng SemVer format (ví dụ: v1.0.0, v1.0.1-alpha)",
        )
    if not name.startswith("v"):
        name = "v" + name

    # Check if already exists (file system check)
    version_dir = get_versions_dir() / name
    if version_dir.exists():
        EM.raise_error(ErrorCode.VERSION_ALREADY_EXISTS, version=name)

    # Copy parent source if --from specified
    if from_version:
        if not from_version.startswith("v"):
            from_version = "v" + from_version
        parent_dir = get_versions_dir() / from_version
        if not parent_dir.exists():
            EM.raise_error(ErrorCode.VERSION_NOT_FOUND, version=from_version)
        parent_src = parent_dir / "src"
        if parent_src.exists():
            try:
                shutil.copytree(parent_src, version_dir / "src")
                click.echo(f"   ✓ Copied source from {from_version}")
            except Exception as e:
                click.echo(f"   ⚠️  Warning: Could not copy source from {from_version}: {e}")

    # 1. Save into SQLite (bắt buộc — fail thì.abort)
    mgr = _get_manager()
    project_id = _get_project_id()
    mgr.version_create(
        project_id=project_id,
        version_name=name,
        parent_version=from_version,
        set_active=True,
    )
    click.echo("   ✓ Saved to SQLite")

    # 2. Create file system structure
    version_dir.mkdir(parents=True, exist_ok=True)
    click.echo(f"   ✓ Created directory: {version_dir.relative_to(Path.cwd())}")
    (version_dir / "src").mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    metadata = {
        "version": name.lstrip("v"),
        "created_at": now,
        "parent_version": from_version.lstrip("v") if from_version else None,
        "status": "draft",
        "pipeline": {"brief": "none", "contract": "none", "ir": "none", "code": "none"},
        "artifacts": {"briefs": 0, "contracts": 0, "files": 0, "lines": 0},
    }
    mf = version_dir / "metadata.yml"
    with open(mf, "w", encoding="utf-8") as f:
        yaml.dump(metadata, f, default_flow_style=False, allow_unicode=True)
    click.echo(f"   ✓ Created metadata: {mf.relative_to(Path.cwd())}")

    # 3. Update config
    config = load_project_config()
    old_active = config.get("active_version")
    config["active_version"] = name
    save_project_config(config)
    click.echo("   ✓ Set as active version")

    if old_active and old_active != name:
        old_meta = get_versions_dir() / old_active / "metadata.yml"
        if old_meta.exists():
            try:
                with open(old_meta, "r", encoding="utf-8") as f:
                    d = yaml.safe_load(f) or {}
                d["status"] = "archived"
                with open(old_meta, "w", encoding="utf-8") as f:
                    yaml.dump(d, f, default_flow_style=False)
            except Exception:
                pass

    # 4. Auto-cleanup
    _auto_cleanup()
    click.echo("")
    click.echo(f"✅ Version {name} created successfully!")


def use_version(name: str) -> None:
    """Switch sang version khác — SQLite + config file."""
    if not name.startswith("v"):
        name = "v" + name

    version_dir = get_versions_dir() / name
    if not version_dir.exists():
        EM.raise_error(ErrorCode.VERSION_NOT_FOUND, version=name)

    # SQLite switch (bắt buộc)
    mgr = _get_manager()
    project_id = _get_project_id()
    mgr.version_use(project_id, name)

    # Config file
    config = load_project_config()
    old_active = config.get("active_version")
    config["active_version"] = name
    save_project_config(config)

    # Update metadata files
    if old_active and old_active != name:
        old_meta = get_versions_dir() / old_active / "metadata.yml"
        if old_meta.exists():
            try:
                with open(old_meta, "r", encoding="utf-8") as f:
                    d = yaml.safe_load(f) or {}
                d["status"] = "archived"
                with open(old_meta, "w", encoding="utf-8") as f:
                    yaml.dump(d, f, default_flow_style=False)
            except Exception:
                pass

    new_meta = version_dir / "metadata.yml"
    if new_meta.exists():
        try:
            with open(new_meta, "r", encoding="utf-8") as f:
                d = yaml.safe_load(f) or {}
            d["status"] = "active"
            with open(new_meta, "w", encoding="utf-8") as f:
                yaml.dump(d, f, default_flow_style=False)
        except Exception:
            pass

    # Show info
    with open(new_meta, "r", encoding="utf-8") as f:
        meta = yaml.safe_load(f) or {}
    click.echo(f"✓ Switched to {name}")
    click.echo("─────────────────────────────")
    click.echo(f"Version: {name}")
    click.echo(f"Status: active")
    click.echo(f"Created: {meta.get('created_at', 'unknown')}")
    if meta.get("parent_version"):
        click.echo(f"Parent: v{meta['parent_version']}")


def list_versions_command() -> None:
    versions = list_versions()
    active_version = get_active_version()

    if not versions:
        click.echo("No versions found. Create one with `midicoder version create <name>`")
        return

    click.echo(f"VERSIONS (active: {active_version or 'none'})")
    click.echo("─────────────────────────────")

    for v in versions:
        name = v["name"]
        metadata = v["metadata"]
        status = metadata.get("status", "unknown")
        created = metadata.get("created_at", "unknown")[:19].replace("T", " ")
        parent = metadata.get("parent_version")
        marker = "*" if name == active_version else " "
        line = f"{marker} {name}    {status}    {created}"
        if parent:
            line += f"  (parent: v{parent})"
        click.echo(line)


def delete_version(name: str, force: bool = False) -> None:
    """Xóa version — SQLite + file system."""
    if not name.startswith("v"):
        name = "v" + name

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

    # SQLite delete (bắt buộc)
    mgr = _get_manager()
    project_id = _get_project_id()
    mgr.version_delete(project_id, name, force=force)

    # File system delete
    try:
        shutil.rmtree(version_dir)
        click.echo(f"✓ Deleted version: {name}")
        click.echo(f"  Removed: {version_dir.relative_to(Path.cwd())}")
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
            mgr = _get_manager()
            mgr.version_use(_get_project_id(), new_active)
            new_meta = get_versions_dir() / new_active / "metadata.yml"
            if new_meta.exists():
                try:
                    with open(new_meta, "r") as f:
                        d = yaml.safe_load(f) or {}
                    d["status"] = "active"
                    with open(new_meta, "w") as f:
                        yaml.dump(d, f, default_flow_style=False)
                except Exception:
                    pass
            click.echo(f"✓ Set new active version: {new_active}")
        else:
            if "active_version" in config:
                del config["active_version"]
            save_project_config(config)
            click.echo("ℹ️  No versions remaining")

    click.echo(f"✅ Version {name} deleted successfully!")


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
        status_order = {"archived": 0, "draft": 1, "active": 2}.get(status, 3)
        return (status_order, created)

    versions.sort(key=sort_key)

    to_delete = []
    for v in versions:
        if v["name"] == active_version:
            continue
        if len(to_delete) >= len(versions) - max_versions:
            break
        to_delete.append(v["name"])

    versions_dir = get_versions_dir()
    for vn in to_delete:
        vd = versions_dir / vn
        try:
            shutil.rmtree(vd, ignore_errors=True)
            click.echo(f"   ✓ Auto-cleanup: removed {vn}")
        except Exception:
            pass
