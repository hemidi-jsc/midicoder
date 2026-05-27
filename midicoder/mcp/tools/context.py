"""
MCP-F: Context Tools.

Cung cấp 2 MCP tools:
- get_project_context: Trả về project context (domain, stack, ui_framework, entities count, ...)
- list_symbols: Trả về danh sách symbols (entities, commands, queries, events) từ contracts/SQLite

Source: midicoder.pipeline.config, midicoder.storage.sqlite, project DSL files
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from midicoder.errors import MidicoderErrorManager as EM, ErrorCode
from midicoder.pipeline.config import get_config

logger = logging.getLogger(__name__)


def _count_dsl_nodes(dsl_dir: Path, node_type: str) -> int:
    """
    Đếm số nodes của một loại trong DSL files.

    Args:
        dsl_dir: Đường dẫn đến DSL directory
        node_type: Loại node (entities, commands, queries, events, ...)

    Returns:
        Số lượng nodes
    """
    count = 0
    if not dsl_dir.exists():
        return 0

    for yaml_file in list(dsl_dir.rglob("*.yaml")) + list(dsl_dir.rglob("*.yml")):
        try:
            with open(yaml_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if not data or not isinstance(data, dict):
                continue
            # DSL files có thể wrap trong root key
            if "definitions" in data:
                data = data["definitions"]
            elif "pack" in data:
                data = data["pack"]

            # Đếm nodes theo loại
            if node_type in data and isinstance(data[node_type], list):
                count += len(data[node_type])
        except Exception:
            continue

    return count


def _count_files_by_extension(directory: Path, extension: str) -> int:
    """Đếm số files với extension cụ thể."""
    if not directory.exists():
        return 0
    return len(list(directory.rglob(f"*{extension}")))


def _load_project_stack_config() -> Dict[str, str]:
    """
    Load stack configuration từ project.

    Kiểm tra các nguồn theo thứ tự ưu tiên:
    1. midicoder.config.yml (user config)
    2. .midicoder/config/midicoder.yml (project config)
    3. Global config

    Returns:
        Dictionary với stack, ui_framework, domain keys
    """
    result: Dict[str, str] = {}

    # 1. User config (midicoder.config.yml)
    user_config_path = Path("midicoder.config.yml")
    if user_config_path.exists():
        try:
            with open(user_config_path, "r", encoding="utf-8") as f:
                user_config = yaml.safe_load(f) or {}
            if "stack" in user_config:
                result["backend_stack"] = user_config["stack"].get("backend", "")
                result["frontend_stack"] = user_config["stack"].get("frontend", "")
            if "ui_framework" in user_config:
                result["ui_framework"] = user_config["ui_framework"]
            if "domain" in user_config:
                result["domain"] = user_config["domain"]
        except Exception:
            pass

    # 2. Project config
    project_config_path = Path(".midicoder/config/midicoder.yml")
    if project_config_path.exists():
        try:
            with open(project_config_path, "r", encoding="utf-8") as f:
                project_config = yaml.safe_load(f) or {}
            if not result.get("domain") and "domain" in project_config:
                result["domain"] = project_config["domain"]
        except Exception:
            pass

    # 3. Global config
    try:
        config = get_config()
        if not result.get("domain"):
            domain = config.get("project.domain")
            if domain:
                result["domain"] = domain
    except Exception:
        pass

    return result


# ============================================================================
# MCP Tool: get_project_context
# ============================================================================


def get_project_context() -> Dict[str, Any]:
    """
    Trả về project context — thông tin tổng quan về project hiện tại.

    Bao gồm:
    - Domain và stack configuration
    - Số lượng entities, commands, queries hiện có
    - Số lượng DSL files
    - Database status (briefs, artifacts có trong DB không)
    - Output directory status

    Returns:
        Dictionary với:
        - domain: domain hiện tại (nếu có)
        - stack: backend_stack, frontend_stack, ui_framework
        - counts: entities, commands, queries, events, value_objects
        - databases: status của các SQLite databases
        - output: thông tin về output directories
        - config_paths: các config files đã được tìm thấy
    """
    # Stack & domain config
    stack_config = _load_project_stack_config()

    # Tìm DSL directories
    dsl_dirs = [
        Path("dsl"),
        Path(".midicoder/dsl"),
        Path(".midicoder/output/dsl"),
    ]
    active_dsl_dir = None
    for d in dsl_dirs:
        if d.exists():
            active_dsl_dir = d
            break

    # Đếm DSL nodes
    counts: Dict[str, int] = {
        "entities": 0,
        "commands": 0,
        "queries": 0,
        "events": 0,
        "value_objects": 0,
        "aggregates": 0,
        "workflows": 0,
    }

    if active_dsl_dir:
        counts["entities"] = _count_dsl_nodes(active_dsl_dir, "entities")
        counts["commands"] = _count_dsl_nodes(active_dsl_dir, "commands")
        counts["queries"] = _count_dsl_nodes(active_dsl_dir, "queries")
        counts["events"] = _count_dsl_nodes(active_dsl_dir, "events")
        counts["value_objects"] = _count_dsl_nodes(active_dsl_dir, "value_objects")
        counts["aggregates"] = _count_dsl_nodes(active_dsl_dir, "aggregates")
        counts["workflows"] = _count_dsl_nodes(active_dsl_dir, "workflows")

    # Database status
    db_status: Dict[str, Any] = {}
    try:
        from midicoder.storage.sqlite import (
            DB_BRIEFS, DB_ARTIFACTS, DB_PROVENANCE, DB_CONTEXT,
            BriefsManager, ArtifactsManager,
        )

        db_status["briefs_db"] = {
            "exists": DB_BRIEFS.exists(),
            "path": str(DB_BRIEFS),
        }
        db_status["artifacts_db"] = {
            "exists": DB_ARTIFACTS.exists(),
            "path": str(DB_ARTIFACTS),
        }
        db_status["provenance_db"] = {
            "exists": DB_PROVENANCE.exists(),
            "path": str(DB_PROVENANCE),
        }
        db_status["context_db"] = {
            "exists": DB_CONTEXT.exists(),
            "path": str(DB_CONTEXT),
        }

        # Đếm briefs
        if DB_BRIEFS.exists():
            try:
                briefs_mgr = BriefsManager(DB_BRIEFS)
                briefs = briefs_mgr.list()
                db_status["brief_count"] = len(briefs)
            except Exception:
                pass

        # Đếm artifacts
        if DB_ARTIFACTS.exists():
            try:
                artifacts_mgr = ArtifactsManager(DB_ARTIFACTS)
                artifacts = artifacts_mgr.list()
                db_status["artifact_count"] = len(artifacts)
            except Exception:
                pass

    except ImportError:
        db_status["error"] = "Không thể import storage module"

    # Output directories
    output_status: Dict[str, Any] = {}
    output_dirs = {
        "contracts": Path(".midicoder/output/contracts"),
        "code": Path(".midicoder/output/code"),
        "dsl": Path(".midicoder/output/dsl"),
        "mir": Path(".midicoder/output/mir"),
    }

    for name, path in output_dirs.items():
        if path.exists():
            file_count = sum(1 for _ in path.rglob("*") if _.is_file())
            output_status[name] = {
                "exists": True,
                "path": str(path),
                "file_count": file_count,
            }
        else:
            output_status[name] = {
                "exists": False,
                "path": str(path),
                "file_count": 0,
            }

    # Config files
    config_paths: Dict[str, Any] = {
        "user_config": {
            "path": str(Path("midicoder.config.yml")),
            "exists": Path("midicoder.config.yml").exists(),
        },
        "project_config": {
            "path": str(Path(".midicoder/config/midicoder.yml")),
            "exists": Path(".midicoder/config/midicoder.yml").exists(),
        },
    }

    return {
        "domain": stack_config.get("domain", "unknown"),
        "stack": {
            "backend": stack_config.get("backend_stack", ""),
            "frontend": stack_config.get("frontend_stack", ""),
            "ui_framework": stack_config.get("ui_framework", ""),
        },
        "counts": counts,
        "total_nodes": sum(counts.values()),
        "databases": db_status,
        "output": output_status,
        "config": config_paths,
    }


# ============================================================================
# MCP Tool: list_symbols
# ============================================================================


def list_symbols() -> Dict[str, Any]:
    """
    Trả về danh sách tất cả symbols (entities, commands, queries, events)
    từ project hiện tại.

    Sources:
    1. SQLite context.db (symbols table)
    2. DSL YAML files (parse entities, commands, queries, events)
    3. Generated contracts

    Returns:
        Dictionary với:
        - entities: list của entity symbols
        - commands: list của command symbols
        - queries: list của query symbols
        - events: list của event symbols
        - value_objects: list của VO symbols
        - total: tổng số symbols
    """
    symbols: Dict[str, List[Dict[str, Any]]] = {
        "entities": [],
        "commands": [],
        "queries": [],
        "events": [],
        "value_objects": [],
        "aggregates": [],
        "workflows": [],
    }

    # 1. Parse từ DSL files
    dsl_dirs = [
        Path("dsl"),
        Path(".midicoder/dsl"),
        Path(".midicoder/output/dsl"),
    ]

    for dsl_dir in dsl_dirs:
        if not dsl_dir.exists():
            continue

        for yaml_file in list(dsl_dir.rglob("*.yaml")) + list(dsl_dir.rglob("*.yml")):
            try:
                with open(yaml_file, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                if not data or not isinstance(data, dict):
                    continue

                # Unwrap root keys
                if "definitions" in data:
                    data = data["definitions"]
                elif "pack" in data:
                    data = data["pack"]

                # Parse entities
                if "entities" in data and isinstance(data["entities"], list):
                    for entity in data["entities"]:
                        if isinstance(entity, dict):
                            symbols["entities"].append({
                                "name": entity.get("id", entity.get("name", "")),
                                "description": entity.get("description", ""),
                                "fields_count": len(entity.get("fields", [])),
                                "source": str(yaml_file),
                            })

                # Parse commands
                if "commands" in data and isinstance(data["commands"], list):
                    for command in data["commands"]:
                        if isinstance(command, dict):
                            symbols["commands"].append({
                                "name": command.get("id", command.get("name", "")),
                                "description": command.get("description", ""),
                                "category": command.get("category", ""),
                                "source": str(yaml_file),
                            })

                # Parse queries
                if "queries" in data and isinstance(data["queries"], list):
                    for query in data["queries"]:
                        if isinstance(query, dict):
                            symbols["queries"].append({
                                "name": query.get("id", query.get("name", "")),
                                "description": query.get("description", ""),
                                "category": query.get("category", ""),
                                "source": str(yaml_file),
                            })

                # Parse events
                if "events" in data and isinstance(data["events"], list):
                    for event in data["events"]:
                        if isinstance(event, dict):
                            symbols["events"].append({
                                "name": event.get("id", event.get("name", "")),
                                "description": event.get("description", ""),
                                "type": event.get("type", ""),
                                "source": str(yaml_file),
                            })

                # Parse value_objects
                if "value_objects" in data and isinstance(data["value_objects"], list):
                    for vo in data["value_objects"]:
                        if isinstance(vo, dict):
                            symbols["value_objects"].append({
                                "name": vo.get("id", vo.get("name", "")),
                                "description": vo.get("description", ""),
                                "immutable": vo.get("immutable", True),
                                "source": str(yaml_file),
                            })

                # Parse aggregates
                if "aggregates" in data and isinstance(data["aggregates"], list):
                    for agg in data["aggregates"]:
                        if isinstance(agg, dict):
                            symbols["aggregates"].append({
                                "name": agg.get("id", agg.get("name", "")),
                                "description": agg.get("description", ""),
                                "source": str(yaml_file),
                            })

                # Parse workflows
                if "workflows" in data and isinstance(data["workflows"], list):
                    for wf in data["workflows"]:
                        if isinstance(wf, dict):
                            symbols["workflows"].append({
                                "name": wf.get("id", wf.get("name", "")),
                                "description": wf.get("description", ""),
                                "source": str(yaml_file),
                            })

            except Exception as e:
                logger.debug(f"Không thể parse {yaml_file}: {e}")

    # 2. Cũng đọc từ SQLite context.db nếu có
    try:
        from midicoder.storage.sqlite import DB_CONTEXT, get_connection

        if DB_CONTEXT.exists():
            with get_connection(DB_CONTEXT) as conn:
                cursor = conn.execute(
                    "SELECT name, type, file_path, description FROM symbols"
                )
                for row in cursor.fetchall():
                    row_dict = dict(row)
                    sym_type = row_dict.get("type", "").lower()
                    if sym_type in symbols:
                        # Tránh duplicate
                        existing_names = {s["name"] for s in symbols[sym_type]}
                        if row_dict["name"] not in existing_names:
                            symbols[sym_type].append({
                                "name": row_dict["name"],
                                "description": row_dict.get("description", ""),
                                "file_path": row_dict.get("file_path", ""),
                                "source": "sqlite",
                            })
    except Exception:
        pass

    # Calculate total
    total = sum(len(v) for v in symbols.values())

    return {
        **symbols,
        "total": total,
    }
