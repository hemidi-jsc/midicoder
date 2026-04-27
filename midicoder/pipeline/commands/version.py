"""
Version Management Commands Implementation.

Lệnh `midicoder version` quản lý versions cho Midicoder project theo SoT E01.

Các sub-commands:
- create: Tạo version mới
- use: Switch version
- list: List tất cả versions
- delete: Xóa version

SoT Reference: E01
"""

import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import click
import yaml

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# SemVer regex pattern (strict)
# Accept: v1.0.0, 1.0.0, v1.0.0-alpha, v1.0.0-beta.1, v1.0.0+build.123
SEMVER_PATTERN = re.compile(
    r'^v?\d+\.\d+\.\d+(-[a-zA-Z0-9]+(\.[a-zA-Z0-9]+)*)?(\+[a-zA-Z0-9]+(\.[a-zA-Z0-9]+)*)?$'
)


def validate_version_name(name: str) -> bool:
    """
    Validate version name theo SemVer strict format.
    
    Args:
        name: Version name để validate
        
    Returns:
        True nếu hợp lệ, False nếu không
    """
    return bool(SEMVER_PATTERN.match(name))


def get_workspace_dir() -> Path:
    """
    Lấy path đến .midicoder/ workspace.
    
    Returns:
        Path đến .midicoder/
        
    Raises:
        MidicoderError: Nếu workspace không tồn tại
    """
    workspace_dir = Path.cwd() / ".midicoder"
    if not workspace_dir.exists():
        EM.raise_error(
            ErrorCode.CONFIG_READ_FAILED,
            message="Workspace chưa được khởi tạo. Hãy chạy `midicoder init` trước.",
            path=str(workspace_dir)
        )
    return workspace_dir


def get_versions_dir() -> Path:
    """
    Lấy path đến .midicoder/versions/.
    
    Returns:
        Path đến .midicoder/versions/
    """
    return get_workspace_dir() / "versions"


def get_config_file() -> Path:
    """
    Lấy path đến project config file.
    
    Returns:
        Path đến .midicoder/config/midicoder.yml
    """
    return get_workspace_dir() / "config" / "midicoder.yml"


def load_project_config() -> dict:
    """
    Load project config từ .midicoder/config/midicoder.yml.
    
    Returns:
        Config dictionary
        
    Raises:
        MidicoderError: Nếu config file không tồn tại hoặc không hợp lệ
    """
    config_file = get_config_file()
    if not config_file.exists():
        EM.raise_error(
            ErrorCode.CONFIG_READ_FAILED,
            path=str(config_file)
        )
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        EM.raise_error(
            ErrorCode.CONFIG_FORMAT_INVALID,
            path=str(config_file),
            cause=e
        )


def save_project_config(config: dict) -> None:
    """
    Save project config vào .midicoder/config/midicoder.yml.
    
    Args:
        config: Config dictionary để save
    """
    config_file = get_config_file()
    config_file.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
    except Exception as e:
        EM.raise_error(
            ErrorCode.CONFIG_WRITE_FAILED,
            path=str(config_file),
            cause=e
        )


def load_version_metadata(version: str) -> dict:
    """
    Load version metadata từ .midicoder/versions/<v>/metadata.yml.
    
    Args:
        version: Version name
        
    Returns:
        Metadata dictionary
        
    Raises:
        MidicoderError: Nếu version không tồn tại hoặc metadata không hợp lệ
    """
    metadata_file = get_versions_dir() / version / "metadata.yml"
    if not metadata_file.exists():
        EM.raise_error(
            ErrorCode.VERSION_NOT_FOUND,
            version=version,
            path=str(metadata_file)
        )
    
    try:
        with open(metadata_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
            if 'version' not in data:
                EM.raise_error(
                    ErrorCode.VERSION_METADATA_INVALID,
                    version=version,
                    reason="missing 'version' field"
                )
            return data
    except yaml.YAMLError as e:
        EM.raise_error(
            ErrorCode.VERSION_METADATA_INVALID,
            version=version,
            path=str(metadata_file),
            cause=e
        )


def save_version_metadata(version: str, metadata: dict) -> None:
    """
    Save version metadata vào .midicoder/versions/<v>/metadata.yml.
    
    Args:
        version: Version name
        metadata: Metadata dictionary
    """
    metadata_file = get_versions_dir() / version / "metadata.yml"
    metadata_file.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(metadata_file, 'w', encoding='utf-8') as f:
            yaml.dump(metadata, f, default_flow_style=False, allow_unicode=True)
    except Exception as e:
        EM.raise_error(
            ErrorCode.VERSION_CREATE_FAILED,
            version=version,
            path=str(metadata_file),
            cause=e
        )


def list_versions() -> list[dict]:
    """
    List tất cả versions trong workspace.
    
    Returns:
        List của version info dictionaries
    """
    versions_dir = get_versions_dir()
    if not versions_dir.exists():
        return []
    
    versions = []
    for version_dir in versions_dir.iterdir():
        if version_dir.is_dir():
            metadata_file = version_dir / "metadata.yml"
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = yaml.safe_load(f) or {}
                        versions.append({
                            'name': version_dir.name,
                            'metadata': metadata
                        })
                except yaml.YAMLError:
                    # Skip invalid metadata files
                    continue
    
    # Sort theo created_at (newest first)
    versions.sort(
        key=lambda v: v['metadata'].get('created_at', ''),
        reverse=True
    )
    
    return versions


def get_active_version() -> Optional[str]:
    """
    Lấy active version name từ config.
    
    Returns:
        Active version name hoặc None nếu không có
    """
    config = load_project_config()
    return config.get('active_version')


def get_max_versions() -> int:
    """
    Lấy max_versions từ config.
    
    Returns:
        Max versions (default: 5)
    """
    config = load_project_config()
    return config.get('max_versions', 5)


def create_version(
    name: str,
    from_version: Optional[str] = None
) -> None:
    """
    Tạo version mới.
    
    Args:
        name: Version name (SemVer format)
        from_version: Parent version để copy (optional)
        
    Raises:
        MidicoderError: Nếu version name không hợp lệ hoặc tạo thất bại
    """
    # Validate version name
    if not validate_version_name(name):
        EM.raise_error(
            ErrorCode.VERSION_INVALID_NAME,
            version=name,
            suggestion="Sử dụng SemVer format (ví dụ: v1.0.0, v1.0.1-alpha)"
        )
    
    # Ensure name starts with 'v'
    if not name.startswith('v'):
        name = 'v' + name
    
    versions_dir = get_versions_dir()
    version_dir = versions_dir / name
    
    # Check if version already exists
    if version_dir.exists():
        EM.raise_error(
            ErrorCode.VERSION_ALREADY_EXISTS,
            version=name
        )
    
    # Load parent metadata if --from specified
    parent_version = None
    if from_version:
        if not from_version.startswith('v'):
            from_version = 'v' + from_version
        
        parent_dir = versions_dir / from_version
        if not parent_dir.exists():
            EM.raise_error(
                ErrorCode.VERSION_NOT_FOUND,
                version=from_version
            )
        parent_version = from_version
        
        # Copy parent source if exists
        parent_src = parent_dir / "src"
        if parent_src.exists():
            target_src = version_dir / "src"
            try:
                shutil.copytree(parent_src, target_src)
                click.echo(f"   ✓ Copied source from {from_version}")
            except Exception as e:
                click.echo(f"   ⚠️  Warning: Could not copy source from {from_version}: {e}")
    
    # Create version directory
    version_dir.mkdir(parents=True, exist_ok=True)
    click.echo(f"   ✓ Created directory: {version_dir.relative_to(Path.cwd())}")
    
    # Create src directory
    src_dir = version_dir / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    click.echo(f"   ✓ Created directory: {src_dir.relative_to(Path.cwd())}")
    
    # Create metadata
    now = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    metadata = {
        'version': name.lstrip('v'),
        'created_at': now,
        'parent_version': parent_version.lstrip('v') if parent_version else None,
        'status': 'draft',
        'pipeline': {
            'brief': 'none',
            'contract': 'none',
            'ir': 'none',
            'code': 'none'
        },
        'artifacts': {
            'briefs': 0,
            'contracts': 0,
            'files': 0,
            'lines': 0
        }
    }
    
    save_version_metadata(name, metadata)
    click.echo(f"   ✓ Created metadata: {version_dir / 'metadata.yml'}")
    
    # Update active version in config
    config = load_project_config()
    old_active = config.get('active_version')
    config['active_version'] = name
    
    if old_active and old_active != name:
        # Mark old active as archived
        try:
            old_metadata = load_version_metadata(old_active)
            old_metadata['status'] = 'archived'
            save_version_metadata(old_active, old_metadata)
        except Exception:
            pass  # Ignore if old metadata not found
    
    save_project_config(config)
    click.echo(f"   ✓ Set as active version")
    
    # Trigger auto-cleanup
    _auto_cleanup()
    
    click.echo("")
    click.echo(f"✅ Version {name} created successfully!")


def use_version(name: str) -> None:
    """
    Switch sang version khác.
    
    Args:
        name: Version name để switch
        
    Raises:
        MidicoderError: Nếu version không tồn tại
    """
    # Normalize name
    if not name.startswith('v'):
        name = 'v' + name
    
    # Validate version exists
    version_dir = get_versions_dir() / name
    if not version_dir.exists():
        EM.raise_error(
            ErrorCode.VERSION_NOT_FOUND,
            version=name
        )
    
    # Load metadata to verify
    metadata = load_version_metadata(name)
    
    # Update config
    config = load_project_config()
    old_active = config.get('active_version')
    
    if old_active and old_active != name:
        # Mark old active as archived
        try:
            old_metadata = load_version_metadata(old_active)
            old_metadata['status'] = 'archived'
            save_version_metadata(old_active, old_metadata)
        except Exception:
            pass
    
    config['active_version'] = name
    save_project_config(config)
    
    # Update new active status
    metadata['status'] = 'active'
    save_version_metadata(name, metadata)
    
    # Show version info
    click.echo(f"✓ Switched to {name}")
    click.echo("─────────────────────────────")
    click.echo(f"Version: {name}")
    click.echo(f"Status: active")
    click.echo(f"Created: {metadata.get('created_at', 'unknown')}")
    if metadata.get('parent_version'):
        click.echo(f"Parent: v{metadata['parent_version']}")


def list_versions_command() -> None:
    """
    List tất cả versions.
    """
    versions = list_versions()
    active_version = get_active_version()
    
    if not versions:
        click.echo("No versions found. Create one with `midicoder version create <name>`")
        return
    
    click.echo(f"VERSIONS (active: {active_version or 'none'})")
    click.echo("─────────────────────────────")
    
    for v in versions:
        name = v['name']
        metadata = v['metadata']
        status = metadata.get('status', 'unknown')
        created = metadata.get('created_at', 'unknown')[:19].replace('T', ' ')
        parent = metadata.get('parent_version')
        
        # Mark active version
        marker = '*' if name == active_version else ' '
        
        line = f"{marker} {name}    {status}    {created}"
        if parent:
            line += f"  (parent: v{parent})"
        
        click.echo(line)


def delete_version(name: str, force: bool = False) -> None:
    """
    Xóa version.
    
    Args:
        name: Version name để xóa
        force: Force delete active version
        
    Raises:
        MidicoderError: Nếu không thể xóa (active version)
    """
    # Normalize name
    if not name.startswith('v'):
        name = 'v' + name
    
    # Check if version exists
    version_dir = get_versions_dir() / name
    if not version_dir.exists():
        EM.raise_error(
            ErrorCode.VERSION_NOT_FOUND,
            version=name
        )
    
    # Check if active
    active_version = get_active_version()
    if name == active_version and not force:
        EM.raise_error(
            ErrorCode.VERSION_DELETE_ACTIVE,
            version=name,
            suggestion="Use --force to delete active version, or switch to another version first"
        )
    
    # Delete version directory
    try:
        shutil.rmtree(version_dir)
        click.echo(f"✓ Deleted version: {name}")
        click.echo(f"  Removed: {version_dir.relative_to(Path.cwd())}")
    except Exception as e:
        EM.raise_error(
            ErrorCode.VERSION_CLEANUP_FAILED,
            version=name,
            cause=e
        )
    
    # Update active version if deleted was active
    if name == active_version:
        config = load_project_config()
        versions = list_versions()
        if versions:
            # Set first available version as active
            new_active = versions[0]['name']
            config['active_version'] = new_active
            try:
                new_metadata = load_version_metadata(new_active)
                new_metadata['status'] = 'active'
                save_version_metadata(new_active, new_metadata)
            except Exception:
                pass
            save_project_config(config)
            click.echo(f"✓ Set new active version: {new_active}")
        else:
            del config['active_version']
            save_project_config(config)
            click.echo("ℹ️  No versions remaining")
    
    click.echo(f"✅ Version {name} deleted successfully!")


def _auto_cleanup() -> None:
    """
    Auto-cleanup versions khi vượt quá max_versions.
    
    Silent cleanup: archived versions được ưu tiên xóa trước,
    active version không bao giờ bị xóa.
    """
    versions = list_versions()
    max_versions = get_max_versions()
    active_version = get_active_version()
    
    if len(versions) <= max_versions:
        return  # Không cần cleanup
    
    # Sort: archived first, then by created_at (oldest first)
    def sort_key(v):
        status = v['metadata'].get('status', '')
        created = v['metadata'].get('created_at', '')
        # archived=0, draft=1, active=2
        status_order = {'archived': 0, 'draft': 1, 'active': 2}.get(status, 3)
        return (status_order, created)
    
    versions.sort(key=sort_key)
    
    # Find versions to delete (oldest non-active)
    versions_to_delete = []
    for v in versions:
        if v['name'] == active_version:
            continue  # Never delete active
        if len(versions_to_delete) >= len(versions) - max_versions:
            break
        versions_to_delete.append(v['name'])
    
    # Delete
    versions_dir = get_versions_dir()
    for version_name in versions_to_delete:
        version_dir = versions_dir / version_name
        try:
            shutil.rmtree(version_dir)
            click.echo(f"   ✓ Auto-cleanup: removed {version_name}")
        except Exception:
            pass  # Silent cleanup, ignore errors


# CLI Commands
@click.group()
def version() -> None:
    """
    Quản lý versions cho project.
    
    Midicoder sử dụng version-based workflow. Mỗi version chứa
    full state (briefs, contracts, code) và độc lập với versions khác.
    
    Sử dụng:
        midicoder version create <name>    # Tạo version mới
        midicoder version use <name>       # Switch version
        midicoder version list             # List versions
        midicoder version delete <name>    # Xóa version
    """
    pass


@version.command('create')
@click.argument('name')
@click.option('--from', 'from_version', help='Copy from existing version')
def create(name: str, from_version: Optional[str]) -> None:
    """
    Tạo version mới.
    
    NAME: Version name theo SemVer format (ví dụ: v1.0.1, 1.0.2-alpha)
    
    Ví dụ:
        midicoder version create v1.0.1
        midicoder version create v1.1.0 --from v1.0.0
    """
    click.echo(f"🚀 Creating version {name}...")
    create_version(name, from_version)


@version.command('use')
@click.argument('name')
def use(name: str) -> None:
    """
    Switch sang version khác.
    
    NAME: Version name để switch
    
    Ví dụ:
        midicoder version use v1.0.1
    """
    use_version(name)


@version.command('list')
def list_cmd() -> None:
    """
    List tất cả versions.
    
    Ví dụ:
        midicoder version list
    """
    list_versions_command()


@version.command('delete')
@click.argument('name')
@click.option('--force', is_flag=True, help='Force delete active version')
def delete(name: str, force: bool) -> None:
    """
    Xóa version.
    
    NAME: Version name để xóa
    
    Cảnh báo: Không thể xóa active version trừ khi dùng --force
    
    Ví dụ:
        midicoder version delete v1.0.0
        midicoder version delete v1.0.1 --force
    """
    delete_version(name, force)