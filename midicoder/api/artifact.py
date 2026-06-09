"""
Artifact helpers — đọc artifact files từ .midicoder/versions/{v}/

Cung cấp utility functions cho tất cả routers để đọc JSON, YAML, và markdown
từ version directories.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import get_project_cwd, get_active_version, get_version_status


def _check_version_not_archived(version: Optional[str]) -> None:
    """Block access if version is archived. Raises ValueError if archived."""
    if version:
        status = get_version_status(version)
        if status == "archived":
            raise ValueError(
                f"Version '{version}' đã bị archived và không thể truy cập nữa. "
                f"Hãy switch sang version đang active."
            )


def _version_root(version: Optional[str] = None) -> Path | None:
    """
    Lấy path root của version directory.
    Nếu không có version, lấy active version.
    Returns None nếu không có project active.
    Raises ValueError nếu version bị archived.
    """
    _check_version_not_archived(version)
    project_cwd = get_project_cwd()
    if not project_cwd:
        return None
    versions_dir = Path(project_cwd) / ".midicoder" / "versions"
    v = version or get_active_version()
    if not v:
        # Fallback: lấy version đầu tiên
        if versions_dir.exists():
            for child in versions_dir.iterdir():
                if child.is_dir():
                    v = child.name
                    break
    if not v:
        return versions_dir / "default"
    return versions_dir / v


def read_json_file(version: Optional[str], *path_parts: str) -> Optional[Dict[str, Any]]:
    """
    Đọc file JSON từ version directory.

    Args:
        version: Version name (None = active version)
        *path_parts: Relative path components (e.g., "contracts", "ir.json")

    Returns:
        Parsed JSON dict, or None if file doesn't exist
    """
    try:
        file_path = _version_root(version) / "/".join(path_parts)
        if not file_path.exists():
            return None
        content = file_path.read_text(encoding="utf-8")
        return json.loads(content)
    except Exception as e:
        print(f"Error reading JSON {file_path}: {e}")
        return None


def read_text_file(version: Optional[str], *path_parts: str) -> Optional[str]:
    """
    Đọc text file (YAML, markdown, graphml, etc.) từ version directory.

    Args:
        version: Version name (None = active version)
        *path_parts: Relative path components

    Returns:
        File content as string, or None if file doesn't exist
    """
    try:
        file_path = _version_root(version) / "/".join(path_parts)
        if not file_path.exists():
            return None
        return file_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Error reading text {file_path}: {e}")
        return None


def list_directory(version: Optional[str], *path_parts: str) -> List[Dict[str, Any]]:
    """
    List files trong một directory của version.

    Args:
        version: Version name (None = active version)
        *path_parts: Directory path components

    Returns:
        List of file info dicts: {name, path, size, is_dir}
    """
    result: List[Dict[str, Any]] = []
    try:
        dir_path = _version_root(version) / "/".join(path_parts)
        if not dir_path.exists() or not dir_path.is_dir():
            return result
        for child in sorted(dir_path.iterdir()):
            result.append({
                "name": child.name,
                "path": str(child.relative_to(_version_root(version))),
                "size": child.stat().st_size if child.is_file() else 0,
                "is_dir": child.is_dir(),
            })
    except Exception as e:
        print(f"Error listing dir {dir_path}: {e}")
    return result


def file_exists(version: Optional[str], *path_parts: str) -> bool:
    """Check nếu artifact file tồn tại."""
    try:
        file_path = _version_root(version) / "/".join(path_parts)
        return file_path.exists()
    except Exception:
        return False


# ============================================================
# Convenience functions cho artifact types cụ thể
# ============================================================

def get_contracts_ir(version: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Read contracts/ir.json"""
    return read_json_file(version, "contracts", "ir.json")


def get_contracts_manifest(version: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Read contracts/manifest.json"""
    return read_json_file(version, "contracts", "manifest.json")


def get_contracts_entities_yaml(version: Optional[str] = None) -> Optional[str]:
    """Read contracts/entities.yaml"""
    return read_text_file(version, "contracts", "entities.yaml")


def get_contracts_contracts_yaml(version: Optional[str] = None) -> Optional[str]:
    """Read contracts/contracts.yaml"""
    return read_text_file(version, "contracts", "contracts.yaml")


def get_ir_mir(version: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Read ir/mir.json"""
    return read_json_file(version, "ir", "mir.json")


def get_ir_symbol_table(version: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Read ir/symbol-table.json"""
    return read_json_file(version, "ir", "symbol-table.json")


def get_ir_dependency_graph(version: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Read ir/dependency-graph.json"""
    return read_json_file(version, "ir", "dependency-graph.json")


def get_ir_entity_relationship(version: Optional[str] = None) -> Optional[str]:
    """Read ir/entity-relationship.graphml"""
    return read_text_file(version, "ir", "entity-relationship.graphml")


def get_plan_lowering(version: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Read plan/lowering.json"""
    return read_json_file(version, "plan", "lowering.json")


def get_generated_code_files(version: Optional[str] = None) -> List[Dict[str, Any]]:
    """List generated code files in code/generated/"""
    files = []
    try:
        code_dir = _version_root(version) / "code" / "generated"
        if not code_dir.exists():
            return files
        for child in sorted(code_dir.rglob("*")):
            if child.is_file():
                rel_path = str(child.relative_to(code_dir))
                files.append({
                    "path": rel_path,
                    "type": child.suffix.lstrip("."),
                    "size": child.stat().st_size,
                    "status": "generated",
                })
    except Exception as e:
        print(f"Error listing code files: {e}")
    return files


def get_generated_file_content(version: Optional[str], file_path: str) -> Optional[str]:
    """Read content of a specific generated code file."""
    return read_text_file(version, "code", "generated", file_path)


def get_brief_master(version: Optional[str] = None) -> Optional[str]:
    """Read briefs/master-brief.md"""
    return read_text_file(version, "briefs", "master-brief.md")


def get_brief_working(version: Optional[str] = None) -> Optional[str]:
    """Read briefs/working-brief.md"""
    return read_text_file(version, "briefs", "working-brief.md")


def get_brief_raw(version: Optional[str] = None) -> Optional[str]:
    """Read brief.md (root brief file used by CLI)"""
    return read_text_file(version, "brief.md")


def list_patches(version: Optional[str] = None) -> List[Dict[str, Any]]:
    """List patch files in patches/"""
    return list_directory(version, "patches")


def get_patch_content(version: Optional[str], patch_name: str) -> Optional[str]:
    """Read a specific patch file."""
    return read_text_file(version, "patches", patch_name)
