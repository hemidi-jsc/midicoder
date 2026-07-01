"""
Contract Commands Implementation (SQLite-Only Architecture).

Tất cả contract artifacts được lưu vào SQLite (ArtifactsManager).
Không sử dụng filesystem để lưu contracts.

Commands:
- contract gen: Generate DSL contracts từ brief analysis → SQLite
- contract check: Validate contracts từ SQLite với DSL schema
- contract repair: Sửa contracts có lỗi bằng LLM → SQLite

Pipeline:
- Input: Brief (SQLite)
- Output: Contract artifacts (SQLite, artifact_type="contract")
- Pipeline: contract gen → contract check → ir build

Author: Midicoder Team
Version: 4.0.0 (LLM Contract Generation)
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncIterator, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

from midicoder.errors import MidicoderErrorManager as EM, ErrorCode
from midicoder.storage.sqlite import BriefsManager, ArtifactsManager, get_connection
from midicoder.storage.activity import log
from midicoder.storage.sqlite import get_project_db_path, get_active_project_cwd
from midicoder.pipeline.commands.brief import _find_brief
from midicoder.pipeline.commands.version import get_active_version as _get_active_version
from midicoder.dsl.projection import ProjectionTree
from midicoder.dsl.validator import validate_tree, ValidationStatus, ValidationReport
from midicoder.pipeline.dsl_parser import DSLParser
from midicoder.pipeline.prompts import load_prompt
from openai import APIError
from midicoder.pipeline.llm.client import (
    LlmConfig,
    call_llm,
    load_llm_config,
)

# 9 categories bắt buộc theo DSL strict mode
REQUIRED_CATEGORIES = [
    "entities", "commands", "queries", "events",
    "workflows", "value_objects", "guards", "roles", "ui_components"
]

# Số lần thử tối đa để LLM fix contracts
MAX_REPAIR_ATTEMPTS = 5


def _log_activity(action: str, resource_type: str = "contract", resource_id: str = "", details: dict = None, status: str = "success") -> None:
    """Ghi activity log vào artifacts.db activity_log table."""
    log(action=action, resource_type=resource_type, resource_id=resource_id, details=details, status=status)


# ============================================================================
# LLM Contract Generation (P0-4)
# ============================================================================

# Mapping category → tên file prompt
_CATEGORY_PROMPT_MAP = {
    "entities": "contract_entities",
    "commands": "contract_commands",
    "queries": "contract_queries",
    "events": "contract_events",
    "workflows": "contract_workflows",
    "value_objects": "contract_value_objects",
    "guards": "contract_guards",
    "roles": "contract_roles",
    "ui_components": "contract_ui_components",
}


# ============================================================================
# MCP context helpers (Step 3 — Wire MCP tools vào contract gen)
# ============================================================================

def _build_mcp_context(category: str) -> str:
    """
    Build MCP context string từ MCP tools để inject vào LLM prompt.

    Dùng MCP-B tool `get_dsl_section` để lấy schema cho category,
    giúp LLM biết property nào hợp lệ.

    Args:
        category: Tên category (entities, commands, ...)

    Returns:
        String context để append vào system prompt, hoặc "" nếu không available
    """
    try:
        from midicoder.mcp.tools.dsl_schema import get_dsl_section
        section_schema = get_dsl_section(category)
        if section_schema:
            return (
                f"\n<mcp_dsl_context category=\"{category}\">\n"
                f"Dưới đây là DSL schema cho category \"{category}\". "
                f"Sử dụng schema này để biết fields nào required và optional.\n\n"
                f"{json.dumps(section_schema, indent=2, ensure_ascii=False)}\n"
                f"</mcp_dsl_context>"
            )
    except Exception:
        # MCP tool không available — không break flow
        pass
    return ""


def _get_styles_schema_for_category(category: str) -> str:
    """
    Build render_context.styles reference string từ presets.

    Dùng để LLM biết có những CSS property nào hợp lệ cho mỗi component
    khi generate contract với render_context.styles.

    Args:
        category: Tên category — chỉ inject cho UI-related categories

    Returns:
        String styles reference, hoặc "" nếu không applicable
    """
    # Chỉ inject cho UI-related categories
    ui_categories = {"ui_components", "entities", "workflows"}
    if category not in ui_categories:
        return ""

    try:
        from midicoder.presets import load_preset, list_presets

        # Aggregate style properties từ tất cả presets
        component_props: dict[str, list[str]] = {}
        for preset_name in list_presets():
            if preset_name == "infrastructure":
                continue
            preset = load_preset(preset_name)
            for stack_name, stacks in preset.items():
                if not isinstance(stacks, dict):
                    continue
                for comp_name, props in stacks.items():
                    if isinstance(props, dict):
                        if comp_name not in component_props:
                            component_props[comp_name] = []
                        for prop in props.keys():
                            if prop not in component_props[comp_name]:
                                component_props[comp_name].append(prop)

        if component_props:
            lines = [
                "Dưới đây là các CSS property hợp lệ trong render_context.styles[{stack}][{component}].",
                "Khi cần override styling, dùng format:",
                "  render_context:",
                "    styles:",
                "      react:",
                "        ComponentName:",
                "          property_name: value",
                "",
                "Components và properties available:",
            ]
            for comp, props in sorted(component_props.items()):
                lines.append(f"  {comp}: {', '.join(sorted(props))}")
            return "\n".join(lines)
    except Exception:
        pass
    return ""


# ============================================================================
# Pipeline validation functions (MCP tools delegate đến đây)
# ============================================================================

def _validate_single_category(category: str, yaml_content: str) -> Dict[str, Any]:
    """
    Validate YAML của 1 category qua DSL constraint system.

    REUSES: DSLParser.parse_yaml_string(), validate_tree(), ValidationReport.to_dict()

    Args:
        category: Tên category (entities, commands, ...)
        yaml_content: Raw YAML string

    Returns:
        Dict với: status, total_errors, total_warnings, errors (list), warnings (list), is_valid
    """
    try:
        parser = DSLParser()
        nodes = parser.parse_yaml_string(yaml_content, category)
        tree = ProjectionTree(nodes={n.id: n for n in nodes})
        tree.nodes_by_kind = {}
        for n in nodes:
            if n.kind not in tree.nodes_by_kind:
                tree.nodes_by_kind[n.kind] = []
            tree.nodes_by_kind[n.kind].append(n)
        report = validate_tree(tree)
        result = report.to_dict()
        result["yaml_valid"] = True
        return result
    except yaml.YAMLError as e:
        return {
            "status": "error",
            "yaml_valid": False,
            "is_valid": False,
            "total_errors": 1,
            "total_warnings": 0,
            "total_info": 0,
            "errors": [{"constraint_id": "YAML001", "level": "error", "message": f"YAML parse error: {e}"}],
            "warnings": [],
            "info": [],
        }
    except Exception as e:
        return {
            "status": "error",
            "yaml_valid": False,
            "is_valid": False,
            "total_errors": 1,
            "total_warnings": 0,
            "total_info": 0,
            "errors": [{"constraint_id": "DSL001", "level": "error", "message": f"DSL parse error: {e}"}],
            "warnings": [],
            "info": [],
        }


def _cross_check_category(category: str, yaml_content: str) -> Dict[str, Any]:
    """
    Cross-reference category hiện tại với các category đã generate trong SQLite.

    Kiểm tra:
    - Commands/Queries tham chiếu đến entities → entities phải tồn tại
    - Commands tham chiếu đến events → events phải tồn tại
    - Guards tham chiếu đến roles → roles phải tồn tại
    - Workflows tham chiếu đến commands → commands phải tồn tại

    REUSES: ArtifactsManager.get(), YAML parsing

    Args:
        category: Tên category đang check
        yaml_content: Raw YAML string của category này

    Returns:
        Dict với: valid (bool), errors (list), warnings (list), checked_references (int)
    """
    errors: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []
    checked_refs = 0

    try:
        data = yaml.safe_load(yaml_content)
        if not data or not isinstance(data, dict):
            return {"valid": True, "errors": [], "warnings": [], "checked_references": 0}

        # Lấy current nodes để extract IDs
        current_ids: set = set()
        current_nodes = data.get(category, [])
        if isinstance(current_nodes, list):
            for node in current_nodes:
                if isinstance(node, dict):
                    nid = node.get("id", node.get("name", ""))
                    if nid:
                        current_ids.add(nid)

        # Load entities từ SQLite để check reference
        entities: set = set()
        events_ids: set = set()
        roles_ids: set = set()

        try:
            project_cwd = get_active_project_cwd()
            if project_cwd:
                artifacts_db = get_project_db_path(project_cwd, "artifacts.db")
                a_mgr = ArtifactsManager(db_path=artifacts_db)
                a_mgr.init()

                # Load entities
                ent_art = a_mgr.get("contract_entities")
                if ent_art:
                    ent_content = ent_art.get("content", "{}")
                    ent_data = yaml.safe_load(ent_content)
                    if ent_data:
                        ents_list = ent_data.get("entities", [])
                        if isinstance(ents_list, list):
                            for e in ents_list:
                                if isinstance(e, dict):
                                    eid = e.get("id", "")
                                    if eid:
                                        entities.add(eid)

                # Load events
                evt_art = a_mgr.get("contract_events")
                if evt_art:
                    evt_content = evt_art.get("content", "{}")
                    evt_data = yaml.safe_load(evt_content)
                    if evt_data:
                        evts_list = evt_data.get("events", [])
                        if isinstance(evts_list, list):
                            for e in evts_list:
                                if isinstance(e, dict):
                                    eid = e.get("id", "")
                                    if eid:
                                        events_ids.add(eid)

                # Load roles
                rol_art = a_mgr.get("contract_roles")
                if rol_art:
                    rol_content = rol_art.get("content", "{}")
                    rol_data = yaml.safe_load(rol_content)
                    if rol_data:
                        roles_list = rol_data.get("roles", [])
                        if isinstance(roles_list, list):
                            for r in roles_list:
                                if isinstance(r, dict):
                                    rid = r.get("id", "")
                                    if rid:
                                        roles_ids.add(rid)
        except Exception:
            pass  # SQLite không available — skip cross-check

        # Cross-check logic dựa trên category
        if category == "commands":
            for cmd in current_nodes:
                if not isinstance(cmd, dict):
                    continue
                # Check entity_references
                ent_refs = cmd.get("entity_references", cmd.get("entity_reference", []))
                if isinstance(ent_refs, dict):
                    ent_refs = [ent_refs]
                if isinstance(ent_refs, list):
                    for ref in ent_refs:
                        if isinstance(ref, dict):
                            ref_id = ref.get("entity_id", ref.get("entity", ref.get("id", "")))
                        else:
                            ref_id = str(ref)
                        if ref_id and ref_id not in entities:
                            errors.append({
                                "type": "missing_entity_reference",
                                "node": cmd.get("id", "unknown"),
                                "reference": ref_id,
                                "message": f"Command '{cmd.get('id', '')}' tham chiếu entity '{ref_id}' không tồn tại"
                            })
                            checked_refs += 1
                # Check output_events
                out_events = cmd.get("output_events", cmd.get("output_event", []))
                if isinstance(out_events, str):
                    out_events = [out_events]
                if isinstance(out_events, list):
                    for ev in out_events:
                        ev_id = str(ev)
                        if ev_id and ev_id not in events_ids:
                            warnings.append({
                                "type": "missing_event_reference",
                                "node": cmd.get("id", "unknown"),
                                "reference": ev_id,
                                "message": f"Command '{cmd.get('id', '')}' output event '{ev_id}' chưa được định nghĩa (có thể sẽ có sau)"
                            })
                            checked_refs += 1

        elif category == "queries":
            for qry in current_nodes:
                if not isinstance(qry, dict):
                    continue
                ent_refs = qry.get("entity_references", qry.get("entity_reference", []))
                if isinstance(ent_refs, dict):
                    ent_refs = [ent_refs]
                if isinstance(ent_refs, list):
                    for ref in ent_refs:
                        if isinstance(ref, dict):
                            ref_id = ref.get("entity_id", ref.get("entity", ref.get("id", "")))
                        else:
                            ref_id = str(ref)
                        if ref_id and ref_id not in entities:
                            errors.append({
                                "type": "missing_entity_reference",
                                "node": qry.get("id", "unknown"),
                                "reference": ref_id,
                                "message": f"Query '{qry.get('id', '')}' tham chiếu entity '{ref_id}' không tồn tại"
                            })
                            checked_refs += 1

        elif category == "guards":
            for guard in current_nodes:
                if not isinstance(guard, dict):
                    continue
                req_roles = guard.get("required_roles", guard.get("required_role", []))
                if isinstance(req_roles, str):
                    req_roles = [req_roles]
                if isinstance(req_roles, list):
                    for rid in req_roles:
                        if rid and rid not in roles_ids:
                            warnings.append({
                                "type": "missing_role_reference",
                                "node": guard.get("id", "unknown"),
                                "reference": rid,
                                "message": f"Guard '{guard.get('id', '')}' yêu cầu role '{rid}' chưa được định nghĩa"
                            })
                            checked_refs += 1

        elif category == "workflows":
            for wf in current_nodes:
                if not isinstance(wf, dict):
                    continue
                steps = wf.get("steps", wf.get("transitions", []))
                if isinstance(steps, list):
                    for step in steps:
                        if isinstance(step, dict):
                            action = step.get("action", step.get("command", ""))
                            if action and action not in current_ids:
                                # Check if it references a command from commands category
                                # (commands may not be generated yet, so warning not error)
                                warnings.append({
                                    "type": "missing_command_reference",
                                    "node": wf.get("id", "unknown"),
                                    "reference": action,
                                    "message": f"Workflow '{wf.get('id', '')}' step tham chiếu command '{action}' chưa tìm thấy"
                                })
                                checked_refs += 1

    except yaml.YAMLError:
        return {"valid": True, "errors": [], "warnings": ["Cannot parse YAML for cross-check"], "checked_references": 0}
    except Exception:
        return {"valid": True, "errors": [], "warnings": ["Cross-check failed"], "checked_references": 0}

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "checked_references": checked_refs,
    }


def _get_artifact_for_category(category: str) -> Dict[str, Any]:
    """
    Lấy nội dung artifact đã generate từ SQLite.

    REUSES: ArtifactsManager.get()

    Args:
        category: Tên category

    Returns:
        Dict với: found (bool), content (str hoặc None), artifact_id, metadata
    """
    try:
        project_cwd = get_active_project_cwd()
        if not project_cwd:
            return {"found": False, "content": None, "artifact_id": None, "error": "No active project"}

        artifacts_db = get_project_db_path(project_cwd, "artifacts.db")
        a_mgr = ArtifactsManager(db_path=artifacts_db)
        a_mgr.init()

        artifact_id = f"contract_{category}"
        art = a_mgr.get(artifact_id)

        if art:
            return {
                "found": True,
                "artifact_id": artifact_id,
                "content": art.get("content", ""),
                "metadata": art.get("metadata", {}),
                "name": art.get("name", ""),
            }
        else:
            return {
                "found": False,
                "artifact_id": artifact_id,
                "content": None,
                "metadata": {},
                "message": f"Artifact '{artifact_id}' chưa được generate"
            }
    except Exception as e:
        return {"found": False, "content": None, "artifact_id": None, "error": str(e)}


# ============================================================================
# Prompt building
# ============================================================================

def _build_category_prompt(
    category: str,
    analysis_data: dict,
    clarifications: list,
    brief_content: str,
    include_mcp_context: bool = True,  # Set False for tool-use flow to avoid duplication
) -> tuple[str, str]:
    """
    Xây dựng prompt cho LLM để generate DSL contracts cho một category.

    Tải system prompt từ file Markdown riêng cho từng category.
    User prompt bao gồm: analysis data, clarifications, brief content,
    và MCP tool context (DSL schema + render_context styles).

    Args:
        category: Tên category (entities, commands, queries, events, workflows, value_objects, guards)
        analysis_data: JSON data từ brief analysis
        clarifications: Danh sách Q&A clarifications
        brief_content: Content của brief ban đầu
        include_mcp_context: If True, inject DSL schema into system prompt. Set False when using tool-use flow.

    Returns:
        Tuple (system_prompt, user_prompt)
    """
    # Load system prompt từ file Markdown
    prompt_name = _CATEGORY_PROMPT_MAP.get(category)
    if prompt_name:
        system = load_prompt(prompt_name)
    else:
        # Fallback nếu không có prompt file
        system = f"Generate DSL contracts for the \"{category}\" category. Output valid YAML dict."

    # MCP: Inject DSL schema context — ONLY when NOT using tool-use (to avoid duplication)
    if include_mcp_context:
        mcp_context = _build_mcp_context(category)
        if mcp_context:
            system = system + "\n\n" + mcp_context

    # Xây dựng user prompt
    user_parts = []

    # Thêm brief content
    user_parts.append(f"## Brief Content:\n{brief_content}")

    # Thêm analysis data
    if analysis_data:
        user_parts.append(f"## Analysis Data:\n{json.dumps(analysis_data, indent=2, ensure_ascii=False)}")

    # Thêm clarifications
    if clarifications:
        clar_text = "\n".join(
            f"- Q: {q.get('question', '')}\n  A: {q.get('answer', '')}"
            for q in clarifications
        )
        user_parts.append(f"## Clarifications:\n{clar_text}")

    # MCP: Inject render_context styles schema (EU-0.3)
    styles_schema = _get_styles_schema_for_category(category)
    if styles_schema:
        user_parts.append(f"## Render Context Styles Reference:\n{styles_schema}")
    # Category request
    user_parts.append(f"\n## Task: Generate contracts for the \"{category}\" category.")
    user_parts.append("Output ONLY the YAML dict with the category key as the top-level key.")

    user = "\n\n".join(user_parts)

    return system, user


# Số lần retry tối đa cho mỗi LLM category call
_MAX_CATEGORY_RETRIES = 10


def _generate_category_with_retry(
    config: LlmConfig,
    category: str,
    system: str,
    user: str,
    max_retries: int = _MAX_CATEGORY_RETRIES,
) -> str:
    """
    Gọi LLM để generate YAML cho một category, retry tới khi thành công.

    Hàm sẽ retry tối đa `max_retries` lần. Nếu hết lần retry → raise Exception.
    Loại bỏ markdown code blocks nếu có.

    Args:
        config: LLM config
        category: Tên category
        system: System prompt
        user: User prompt
        max_retries: Số lần retry tối đa

    Returns:
        YAML string hợp lệ cho category

    Raises:
        RuntimeError: Nếu hết lần retry mà vẫn không có valid YAML
    """
    attempt = 0

    while attempt < max_retries:
        attempt += 1

        try:
            response = call_llm(
                config,
                system=system,
                messages=[{"role": "user", "content": user}],
            )

            # Extract YAML from LLM response
            yaml_content = _extract_yaml_from_text(response.content, category)

            # Kiểm tra xem có phải valid YAML không
            yaml.safe_load(yaml_content)

            # Nếu đến được đây thì là valid YAML
            return yaml_content

        except yaml.YAMLError:
            # LLM output không phải valid YAML → retry
            _log_activity("contract.gen.retry", resource_id=category,
                         details={"reason": "invalid_yaml", "attempt": attempt, "max_retries": max_retries},
                         status="warning")
            if attempt >= max_retries:
                raise RuntimeError(f"Failed to generate valid YAML for {category} after {max_retries} attempts")
            continue
        except Exception as e:
            # Loại lỗi khác (API error, ...) → retry
            _log_activity("contract.gen.retry", resource_id=category,
                         details={"reason": str(e), "attempt": attempt, "max_retries": max_retries},
                         status="warning")
            if attempt >= max_retries:
                raise RuntimeError(f"LLM failed for {category} after {max_retries} attempts: {e}")
            continue

    raise RuntimeError(f"Exceeded max retries ({max_retries}) for category {category}")


def _generate_contracts_with_llm(
    config: LlmConfig,
    analysis_data: dict,
    clarifications: list,
    brief_content: str,
) -> Dict[str, str]:
    """
    Generate DSL contracts cho tất cả 7 categories bằng LLM.

    Gọi LLM 7 lần riêng biệt, mỗi lần generate 1 category.
    Mỗi call có prompt riêng phù hợp với schema của category đó.

    Args:
        config: LLM config
        analysis_data: JSON data từ brief analysis
        clarifications: Danh sách clarifications
        brief_content: Content của brief ban đầu

    Returns:
        Dictionary mapping category → YAML string
    """
    result = {}

    for category in REQUIRED_CATEGORIES:
        _log_activity("contract.gen.started", resource_id=category,
                     details={"category": category})

        system, user = _build_category_prompt(
            category, analysis_data, clarifications, brief_content
        )

        yaml_content = _generate_category_with_retry(
            config, category, system, user
        )

        result[category] = yaml_content
        _log_activity("contract.category.generated", resource_id=category,
                     details={"category": category})

    return result


def _auto_fix_contracts(
    artifacts_manager: ArtifactsManager,
    yaml_dict: Dict[str, str],
    brief_id: str,
    config: LlmConfig,
) -> bool:
    """
    Auto-fix loop: validate → error → LLM fix → revalidate (max 5 iterations).

    Sau khi generate, nếu validation có errors, hàm này sẽ:
    1. Parse errors từ validation report
    2. Gọi LLM để fix các categories có lỗi
    3. Re-validate TOÀN BỘ 7 categories
    4. Kiểm tra total_errors == 0

    Args:
        artifacts_manager: ArtifactsManager instance
        yaml_dict: Dictionary category → YAML content
        brief_id: Brief ID
        config: LLM config

    Returns:
        True nếu valid sau fix, False nếu sau 5 iterations vẫn có errors
    """
    dsl_parser = DSLParser()

    for iteration in range(1, MAX_REPAIR_ATTEMPTS + 1):
        _log_activity("contract.auto_fix.iteration", details={"iteration": iteration, "max": MAX_REPAIR_ATTEMPTS})

        # Build ProjectionTree và validate
        try:
            tree = dsl_parser.build_projection_tree(yaml_dict)
            report = validate_tree(tree)
        except Exception as e:
            _log_activity("contract.auto_fix.error", details={"error": str(e)}, status="error")
            break

        if report.total_errors == 0:
            _log_activity("contract.auto_fix.valid", details={"iterations": iteration}, status="success")
            return True

        _log_activity("contract.auto_fix.errors_remain", details={"total_errors": report.total_errors})

        # Fix các categories có lỗi
        errors_by_node = report.get_errors_by_node()
        error_messages = []
        for node_id, node_errors in errors_by_node.items():
            for error in node_errors:
                error_messages.append(getattr(error, 'message', str(error)))

        for category in REQUIRED_CATEGORIES:
            if category not in yaml_dict:
                continue

            current_content = yaml_dict[category]
            try:
                parsed_data = yaml.safe_load(current_content)
            except Exception:
                parsed_data = {}

            # Gọi LLM để fix
            try:
                response = call_llm(
                    config,
                    system="""You are a DSL contract repair expert. Fix validation errors.
Output ONLY valid YAML dict, no markdown formatting.""",
                    messages=[{
                        "role": "user",
                        "content": f"""Category: {category}

Current content:
{current_content}

Validation errors:
{"; ".join(error_messages)}

Fix the YAML. Output ONLY the fixed YAML content."""
                    }],
                )

                fixed_yaml = _extract_yaml_from_text(response.content, category)

                # Validate là fixed YAML hợp lệ
                yaml.safe_load(fixed_yaml)
                yaml_dict[category] = fixed_yaml
                _log_activity("contract.auto_fix.fixed", resource_id=category, details={"category": category})

            except Exception as e:
                _log_activity("contract.auto_fix.fail", resource_id=category, details={"category": category, "error": str(e)}, status="error")

        # Update artifacts trong SQLite
        for category, content in yaml_dict.items():
            _upsert_contract_artifact(artifacts_manager, category, content, brief_id)

    # Sau MAX_REPAIR_ATTEMPTS iterations, kiểm tra cuối cùng
    try:
        tree = dsl_parser.build_projection_tree(yaml_dict)
        report = validate_tree(tree)
        if report.total_errors == 0:
            return True
    except Exception:
        pass

    return False


# ============================================================================
# Contract Generation
# ============================================================================

def generate_contracts(force: bool = False):
    """
    Generate DSL contracts từ brief analysis.

    Process (SQLite-only):
    1. Lấy active brief từ SQLite
    2. Load analysis data + clarifications
    3. Gọi LLM để generate 7 categories (fallback: placeholder)
    4. Self-validate + auto-fix nếu có errors
    5. Save contracts vào SQLite (artifact_type="contract")

    Args:
        force: Force regenerate even if exists
    """
    _log_activity("contract.gen.started", details={"force": force})

    # Step 1: Check if brief exists và đã freezed
    briefs_manager = BriefsManager()
    briefs_manager.init()
    briefs = briefs_manager.list()

    if not briefs:
        _log_activity("contract.gen.no_brief", details={}, status="error")
        raise SystemExit("Không có brief nào")

    # Tìm brief có status = freezed
    active_brief = None
    for brief in briefs:
        if brief.get('status') == 'freezed':
            active_brief = brief
            break

    if not active_brief:
        _log_activity("contract.gen.no_freezed_brief", details={}, status="error")
        raise SystemExit("Chưa có brief nào được freeze. Hãy freeze brief trước khi generate contract.")

    brief_id = active_brief.get('brief_id')
    _log_activity("contract.brief_loaded", resource_id=brief_id,
                 details={"brief_id": brief_id, "title": active_brief.get('title'), "status": "freezed"})

    # Step 2: Check if contracts already exist
    artifacts_manager = ArtifactsManager()
    artifacts_manager.init()
    existing = artifacts_manager.list_by_type("contract")

    if existing and not force:
        _log_activity("contract.gen.exists", details={"count": len(existing)}, status="warning")
        return

    # Step 3: Delegate đến _generate_contracts_to_sqlite (có placeholder fallback)
    _log_activity("contract.gen.in_progress", resource_id=brief_id)
    _generate_contracts_to_sqlite(brief_id)

    # Step 4: Self-validate + auto-fix nếu có errors
    _log_activity("contract.validate.self", resource_id=brief_id)

    tree = _load_contracts_from_sqlite()
    if tree is not None:
        report = validate_tree(tree)
        if report.status == ValidationStatus.VALID:
            _log_activity("contract.validate.valid", resource_id=brief_id)
        elif report.status == ValidationStatus.WARNINGS:
            _log_activity("contract.validate.warnings", resource_id=brief_id,
                         details={"total_warnings": report.total_warnings}, status="warning")
        else:
            _log_activity("contract.validate.errors", resource_id=brief_id,
                         details={"total_errors": report.total_errors}, status="warning")
            # Tự động fix nếu có errors
            _log_activity("contract.auto_fix.triggered", resource_id=brief_id,
                         details={"total_errors": report.total_errors})
            # Load yaml_dict từ SQLite để feed vào auto-fix
            yaml_dict_for_fix = {}
            for artifact in artifacts_manager.list_by_type("contract"):
                aid = artifact.get("artifact_id", "")
                if aid.startswith("contract_"):
                    yaml_dict_for_fix[aid[len("contract_"):]] = artifact.get("content", "")
            if yaml_dict_for_fix:
                try:
                    llm_config = load_llm_config()
                    _auto_fix_contracts(artifacts_manager, yaml_dict_for_fix, brief_id, llm_config)
                except Exception as fix_err:
                    _log_activity("contract.auto_fix.failed", resource_id=brief_id,
                                 details={"error": str(fix_err)}, status="error")
    else:
        _log_activity("contract.validate.no_tree", resource_id=brief_id, status="error")

    # Done
    _log_activity("contract.gen.completed", resource_id=brief_id, details={"status": "success"})


def _generate_contracts_to_sqlite(brief_id: str) -> None:
    """
    Generate contract YAML strings và lưu trực tiếp vào SQLite.

    Sử dụng LLM để generate contracts. Nếu LLM không được cấu hình,
    sử dụng placeholder data làm fallback.

    Args:
        brief_id: Brief ID liên quan
    """
    artifacts_manager = ArtifactsManager()
    artifacts_manager.init()
    briefs_manager = BriefsManager()
    briefs_manager.init()

    # Lấy brief content
    brief_record = briefs_manager.get(brief_id)
    brief_content = brief_record.get('content', '') if brief_record else ''

    # Lấy analysis data
    analysis_data = {}
    try:
        analysis_artifact = artifacts_manager.get(f"analysis-{brief_id}")
        if analysis_artifact:
            analysis_data = json.loads(analysis_artifact.get("content", "{}"))
    except Exception:
        pass

    # Lấy clarifications
    clarifications = []
    try:
        clarifications = briefs_manager.get_clarifications(brief_id)
    except Exception:
        pass

    # Thử load LLM config
    try:
        config = load_llm_config()
        yaml_dict = _generate_contracts_with_llm(
            config=config,
            analysis_data=analysis_data,
            clarifications=clarifications,
            brief_content=brief_content,
        )
    except Exception:
        # Fallback: sử dụng placeholder nếu LLM không hợp lệ
        generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        yaml_dict = _build_placeholder_yaml(brief_id, generated_at)

    saved_count = 0
    for category in REQUIRED_CATEGORIES:
        yaml_content = yaml_dict[category]
        _upsert_contract_artifact(artifacts_manager, category, yaml_content, brief_id)
        saved_count += 1
        _log_activity("contract.saved", resource_id=f"contract_{category}",
                     details={"category": category, "brief_id": brief_id})

    _log_activity("contract.gen.saved_all", resource_id=brief_id,
                 details={"saved_count": saved_count, "total": len(REQUIRED_CATEGORIES)})


def _build_placeholder_yaml(brief_id: str, generated_at: str) -> Dict[str, str]:
    """
    Build placeholder YAML content cho 7 categories.

    EMERGENCY FALLBACK ONLY — chỉ sử dụng khi LLM không thể gọi được.

    Args:
        brief_id: Brief ID
        generated_at: Timestamp

    Returns:
        Dictionary mapping category → YAML string
    """
    # ===== Entities =====
    entities_yaml = yaml.dump({
        "meta": {
            "version": "1.0.0",
            "brief_id": brief_id,
            "generated_at": generated_at
        },
        "entities": [
            {
                "id": "User",
                "description": "Người dùng hệ thống",
                "fields": [
                    {"name": "id", "type": "UUID", "required": True},
                    {"name": "email", "type": "String", "required": True},
                    {"name": "name", "type": "String", "required": False},
                    {"name": "created_at", "type": "DateTime", "required": True},
                    {"name": "updated_at", "type": "DateTime", "required": True}
                ],
                "primary_key": "id",
                "indexes": [["email"]],
                "tenant_scope": "tenant_isolated",
                "tags": ["core", "auth"]
            },
            {
                "id": "Product",
                "description": "Sản phẩm trong hệ thống",
                "fields": [
                    {"name": "id", "type": "UUID", "required": True},
                    {"name": "name", "type": "String", "required": True},
                    {"name": "description", "type": "Text", "required": False},
                    {"name": "price", "type": "Decimal", "required": True},
                    {"name": "stock", "type": "Integer", "required": True},
                    {"name": "created_at", "type": "DateTime", "required": True},
                    {"name": "updated_at", "type": "DateTime", "required": True}
                ],
                "primary_key": "id",
                "indexes": [["name"], ["price"]],
                "tenant_scope": "tenant_isolated",
                "tags": ["core", "catalog"]
            },
            {
                "id": "Order",
                "description": "Đơn hàng của khách hàng",
                "fields": [
                    {"name": "id", "type": "UUID", "required": True},
                    {"name": "user_id", "type": "UUID", "required": True},
                    {"name": "status", "type": "String", "required": True},
                    {"name": "total", "type": "Decimal", "required": True},
                    {"name": "created_at", "type": "DateTime", "required": True},
                    {"name": "updated_at", "type": "DateTime", "required": True}
                ],
                "primary_key": "id",
                "indexes": [["user_id"], ["status"]],
                "constraints": [
                    {"type": "foreign_key", "fields": ["user_id"], "references": "User.id"}
                ],
                "tenant_scope": "tenant_isolated",
                "tags": ["core", "order"]
            }
        ]
    }, default_flow_style=False, allow_unicode=True)

    # ===== Commands =====
    commands_yaml = yaml.dump({
        "meta": {
            "version": "1.0.0",
            "brief_id": brief_id,
            "generated_at": generated_at
        },
        "commands": [
            {
                "id": "CreateUser",
                "description": "Tạo người dùng mới",
                "input": [
                    {"name": "email", "type": "String", "required": True},
                    {"name": "name", "type": "String", "required": False}
                ],
                "fetches": [],
                "guards": [
                    {"type": "email_unique", "message": "Email đã tồn tại"}
                ],
                "effects": [
                    {"type": "create", "entity": "User"},
                    {"type": "emit", "event": "UserCreated"}
                ],
                "errors": [
                    {"code": "USER_EMAIL_EXISTS", "message": "Email đã được đăng ký"}
                ],
                "returns": [{"name": "user", "type": "User"}],
                "category": "auth",
                "emits": ["UserCreated"],
                "required_roles": [],
                "required_permissions": ["user.create"],
                "writes_to": ["User"],
                "datasource": "primary",
                "transaction": True,
                "tenant_scope": "tenant_isolated",
                "tags": ["auth"]
            },
            {
                "id": "CreateOrder",
                "description": "Tạo đơn hàng mới",
                "input": [
                    {"name": "user_id", "type": "UUID", "required": True},
                    {"name": "items", "type": "Array", "required": True}
                ],
                "fetches": [
                    {"entity": "User", "field": "user_id", "alias": "user"},
                    {"entity": "Product", "field": "product_id", "alias": "products"}
                ],
                "guards": [
                    {"type": "user_exists", "message": "User không tồn tại"},
                    {"type": "stock_available", "message": "Sản phẩm hết hàng"}
                ],
                "effects": [
                    {"type": "create", "entity": "Order"},
                    {"type": "update", "entity": "Product", "action": "decrement_stock"},
                    {"type": "emit", "event": "OrderCreated"}
                ],
                "errors": [
                    {"code": "USER_NOT_FOUND", "message": "Không tìm thấy người dùng"},
                    {"code": "INSUFFICIENT_STOCK", "message": "Số lượng hàng không đủ"}
                ],
                "returns": [{"name": "order", "type": "Order"}],
                "category": "order",
                "emits": ["OrderCreated"],
                "required_roles": ["customer"],
                "required_permissions": ["order.create"],
                "writes_to": ["Order", "Product"],
                "datasource": "primary",
                "transaction": True,
                "tenant_scope": "tenant_isolated",
                "tags": ["order"]
            }
        ]
    }, default_flow_style=False, allow_unicode=True)

    # ===== Queries =====
    queries_yaml = yaml.dump({
        "meta": {
            "version": "1.0.0",
            "brief_id": brief_id,
            "generated_at": generated_at
        },
        "queries": [
            {
                "id": "GetUserById",
                "description": "Lấy thông tin người dùng theo ID",
                "input": [
                    {"name": "userId", "type": "UUID", "required": True}
                ],
                "fetches": [{"entity": "User", "filter": "id = :userId"}],
                "guards": [
                    {"type": "user_exists", "message": "User không tồn tại"}
                ],
                "returns": [{"name": "user", "type": "User"}],
                "category": "auth",
                "reads_from": ["User"],
                "required_roles": ["admin", "self"],
                "required_permissions": ["user.read"],
                "datasource": "primary",
                "tenant_scope": "tenant_isolated",
                "tags": ["auth"]
            },
            {
                "id": "ListProducts",
                "description": "Danh sách sản phẩm với phân trang",
                "input": [
                    {"name": "page", "type": "Integer", "required": False},
                    {"name": "pageSize", "type": "Integer", "required": False},
                    {"name": "search", "type": "String", "required": False}
                ],
                "fetches": [{"entity": "Product", "filter": "name LIKE :search"}],
                "guards": [],
                "returns": [{"name": "products", "type": "Product[]"}],
                "category": "catalog",
                "reads_from": ["Product"],
                "required_roles": [],
                "required_permissions": ["product.read"],
                "datasource": "primary",
                "tenant_scope": "tenant_isolated",
                "tags": ["catalog"]
            },
            {
                "id": "GetOrdersByUser",
                "description": "Lấy danh sách đơn hàng của người dùng",
                "input": [
                    {"name": "userId", "type": "UUID", "required": True}
                ],
                "fetches": [{"entity": "Order", "filter": "user_id = :userId"}],
                "guards": [],
                "returns": [{"name": "orders", "type": "Order[]"}],
                "category": "order",
                "reads_from": ["Order"],
                "required_roles": ["customer"],
                "required_permissions": ["order.read"],
                "datasource": "primary",
                "tenant_scope": "tenant_isolated",
                "tags": ["order"]
            }
        ]
    }, default_flow_style=False, allow_unicode=True)

    # ===== Events =====
    events_yaml = yaml.dump({
        "meta": {
            "version": "1.0.0",
            "brief_id": brief_id,
            "generated_at": generated_at
        },
        "events": [
            {
                "id": "UserCreated",
                "description": "Sự kiện người dùng được tạo mới",
                "type": "domain",
                "source_entity": "User",
                "fields": [
                    {"name": "user_id", "type": "UUID", "required": True},
                    {"name": "email", "type": "String", "required": True},
                    {"name": "occurred_at", "type": "DateTime", "required": True}
                ],
                "version": "v1",
                "tenant_scope": "tenant_isolated",
                "tags": ["auth"]
            },
            {
                "id": "OrderCreated",
                "description": "Sự kiện đơn hàng được tạo mới",
                "type": "domain",
                "source_entity": "Order",
                "fields": [
                    {"name": "order_id", "type": "UUID", "required": True},
                    {"name": "user_id", "type": "UUID", "required": True},
                    {"name": "total", "type": "Decimal", "required": True},
                    {"name": "occurred_at", "type": "DateTime", "required": True}
                ],
                "version": "v1",
                "tenant_scope": "tenant_isolated",
                "tags": ["order"]
            }
        ]
    }, default_flow_style=False, allow_unicode=True)

    # ===== Placeholders cho 4 categories còn lại (với data mẫu) =====
    placeholder_meta = {
        "meta": {
            "version": "1.0.0",
            "brief_id": brief_id,
            "generated_at": generated_at
        }
    }

    workflows_yaml = yaml.dump({
        **placeholder_meta,
        "workflows": [
            {
                "id": "OrderFulfillment",
                "description": "Quy trình xử lý đơn hàng từ khi tạo đến khi giao hàng",
                "states": [
                    {"id": "pending", "description": "Chờ xử lý"},
                    {"id": "processing", "description": "Đang xử lý"},
                    {"id": "shipped", "description": "Đã giao hàng"},
                    {"id": "delivered", "description": "Đã nhận hàng"},
                    {"id": "cancelled", "description": "Đã hủy"}
                ],
                "transitions": [
                    {"from": "pending", "to": "processing", "event": "OrderConfirmed", "guard": "PaymentVerified"},
                    {"from": "processing", "to": "shipped", "event": "OrderShipped", "guard": "InventoryAvailable"},
                    {"from": "shipped", "to": "delivered", "event": "OrderDelivered"},
                    {"from": "pending", "to": "cancelled", "event": "OrderCancelled"},
                    {"from": "processing", "to": "cancelled", "event": "OrderCancelled"}
                ],
                "tenant_scope": "tenant_isolated"
            }
        ]
    }, default_flow_style=False, allow_unicode=True)

    value_objects_yaml = yaml.dump({
        **placeholder_meta,
        "value_objects": [
            {
                "id": "Money",
                "description": "Giá trị tiền tệ với đơn vị",
                "fields": [
                    {"name": "amount", "type": "Decimal", "required": True},
                    {"name": "currency", "type": "String", "required": True}
                ],
                "methods": [
                    {"name": "add", "returns": "Money"},
                    {"name": "multiply", "returns": "Money"},
                    {"name": "to_string", "returns": "String"}
                ],
                "immutable": True,
                "comparable": True
            },
            {
                "id": "Address",
                "description": "Địa chỉ giao hàng",
                "fields": [
                    {"name": "street", "type": "String", "required": True},
                    {"name": "city", "type": "String", "required": True},
                    {"name": "province", "type": "String", "required": True},
                    {"name": "postal_code", "type": "String", "required": False},
                    {"name": "country", "type": "String", "required": True}
                ],
                "methods": [
                    {"name": "is_complete", "returns": "Boolean"},
                    {"name": "to_string", "returns": "String"}
                ],
                "immutable": True
            }
        ]
    }, default_flow_style=False, allow_unicode=True)

    guards_yaml = yaml.dump({
        **placeholder_meta,
        "guards": [
            {
                "id": "PaymentVerified",
                "description": "Kiểm tra thanh toán đã được xác nhận",
                "type": "business_rule",
                "condition": {"payment_status": "confirmed"},
                "error": "Thanh toán chưa được xác nhận"
            },
            {
                "id": "InventoryAvailable",
                "description": "Kiểm tra kho còn hàng",
                "type": "validation",
                "condition": {"stock": {">": 0}},
                "error": "Sản phẩm hết hàng"
            },
            {
                "id": "OrderNotCancelled",
                "description": "Kiểm tra đơn hàng chưa bị hủy",
                "type": "validation",
                "condition": {"order_status": {"!=": "cancelled"}},
                "error": "Đơn hàng đã bị hủy"
            }
        ]
    }, default_flow_style=False, allow_unicode=True)

    roles_yaml = yaml.dump({
        **placeholder_meta,
        "roles": [
            {
                "id": "admin",
                "description": "Quản trị viên hệ thống",
                "permissions": [
                    {"action": "manage", "resource": "*"},
                    {"action": "create", "resource": "User"},
                    {"action": "read", "resource": "User"},
                    {"action": "update", "resource": "User"},
                    {"action": "delete", "resource": "User"},
                    {"action": "create", "resource": "Product"},
                    {"action": "read", "resource": "Product"},
                    {"action": "update", "resource": "Product"},
                    {"action": "delete", "resource": "Product"},
                    {"action": "manage", "resource": "Order"}
                ],
                "tenant_scope": "global"
            },
            {
                "id": "customer",
                "description": "Khách hàng mua hàng",
                "permissions": [
                    {"action": "create", "resource": "Order"},
                    {"action": "read", "resource": "Order"},
                    {"action": "read", "resource": "Product"},
                    {"action": "read", "resource": "User"}
                ],
                "tenant_scope": "tenant_isolated"
            },
            {
                "id": "staff",
                "description": "Nhân viên xử lý đơn hàng",
                "permissions": [
                    {"action": "read", "resource": "Order"},
                    {"action": "update", "resource": "Order"},
                    {"action": "read", "resource": "Product"},
                    {"action": "update", "resource": "Product"},
                    {"action": "read", "resource": "User"}
                ],
                "tenant_scope": "tenant_isolated"
            }
        ]
    }, default_flow_style=False, allow_unicode=True)

    ui_components_yaml = yaml.dump({
        **placeholder_meta,
        "ui_components": [
            {
                "id": "UserForm",
                "description": "Form nhập thông tin người dùng",
                "component_type": "form_field",
                "entity_id": "User",
                "properties": {"layout": "single_column"}
            },
            {
                "id": "UserTable",
                "description": "Bảng danh sách người dùng",
                "component_type": "data_table",
                "entity_id": "User",
                "properties": {"pagination": True, "sortable": True, "filterable": True}
            },
            {
                "id": "ProductCardList",
                "description": "Danh sách sản phẩm dạng card",
                "component_type": "card_list",
                "entity_id": "Product",
                "properties": {"grid_columns": 3}
            },
            {
                "id": "OrderDialog",
                "description": "Dialog chi tiết đơn hàng",
                "component_type": "dialog",
                "entity_id": "Order",
                "properties": {"size": "large"}
            },
            {
                "id": "PrimaryTheme",
                "description": "Theme mặc định",
                "component_type": "theme_provider",
                "entity_id": None,
                "properties": {"primary_color": "#3b82f6", "dark_mode": True}
            }
        ],
        "ui_layouts": [
            {
                "id": "UserListLayout",
                "description": "Layout danh sách người dùng",
                "layout_type": "page",
                "regions": ["header", "main", "sidebar"],
                "properties": {}
            }
        ],
        "ui_themes": [
            {
                "id": "DefaultTheme",
                "description": "Theme mặc định cho ứng dụng",
                "name": "default",
                "tokens": {"primary_color": "#3b82f6", "secondary_color": "#64748b"},
                "dark_mode": True
            }
        ]
    }, default_flow_style=False, allow_unicode=True)

    return {
        "entities": entities_yaml,
        "commands": commands_yaml,
        "queries": queries_yaml,
        "events": events_yaml,
        "workflows": workflows_yaml,
        "value_objects": value_objects_yaml,
        "guards": guards_yaml,
        "roles": roles_yaml,
        "ui_components": ui_components_yaml,
    }


def _extract_yaml_from_text(text: str, category: str) -> str:
    """Extract valid YAML from LLM text response.

    Handles:
    1. Thinking tags (<thinking>, <antThinking>)
    2. Markdown code blocks (```yaml ... ```)
    3. Preamble text before YAML block (e.g. "Looking at the schema...")
    4. Pure YAML (no wrapping)

    Returns the YAML string that starts with the expected category key (e.g., "entities:").
    """
    import re

    # Step 1: strip thinking tags
    cleaned = text
    for tag in ["<thinking>", "</thinking>", "<antThinking>", "</antThinking>", "<anthinking>", "</anthinking>", "<think>", "</think>"]:
        cleaned = cleaned.replace(tag, "")
    cleaned = cleaned.strip()

    # Step 2: try to extract from markdown code block ```yaml ... ``` or ``` ... ```
    yaml_block = re.search(r"```(?:yaml|yml)?\s*\n(.*?)```", cleaned, re.DOTALL)
    if yaml_block:
        return yaml_block.group(1).strip()

    # Step 3: try to find the YAML starting from category key (e.g., "entities:")
    # This handles case where LLM outputs preamble before YAML without code fence
    category_key = f"{category}:"
    idx = cleaned.find(category_key)
    if idx >= 0:
        return cleaned[idx:].strip()

    # Step 4: fallback — try to find first YAML dict key pattern at start of line
    yaml_start = re.search(r"^\w[\w_]*:", cleaned, re.MULTILINE)
    if yaml_start:
        return cleaned[yaml_start.start():].strip()

    # Step 5: nothing worked — return as-is
    return cleaned


def _upsert_contract_artifact(
    manager: ArtifactsManager,
    category: str,
    content: str,
    brief_id: str,
) -> None:
    """
    Upsert contract artifact vào SQLite (idempotent).

    Nếu artifact đã tồn tại → update_content.
    Nếu chưa tồn tại → create mới.

    Args:
        manager: ArtifactsManager instance
        category: Category name (entities, commands, ...)
        content: YAML content string
        brief_id: Brief ID
    """
    artifact_id = f"contract_{category}"
    existing = manager.get(artifact_id)

    if existing:
        manager.update_content(artifact_id, content)
    else:
        manager.create(
            artifact_id=artifact_id,
            artifact_type="contract",
            name=f"Contract: {category}",
            version="1.0.0",
            brief_id=brief_id,
            content=content,
            metadata={"brief_id": brief_id, "category": category}
        )


# ============================================================================
# Contract Validation
# ============================================================================

def check_contracts(auto_fix: bool = False, strict: bool = False):
    """
    Validate contracts với DSL schema.

    Process (SQLite-only):
    1. Load contract artifacts từ SQLite
    2. Parse YAML strings → ProjectionTree (qua DSLParser)
    3. Validate với DSL validator
    4. Report errors/warnings với actionable insights

    Args:
        auto_fix: Attempt to fix errors automatically
        strict: Treat warnings as errors
    """
    _log_activity("contract.check.started", details={"auto_fix": auto_fix, "strict": strict})

    # Step 1: Load contract artifacts từ SQLite
    artifacts_manager = ArtifactsManager()
    artifacts_manager.init()

    contracts = artifacts_manager.list_by_type("contract")
    if not contracts:
        _log_activity("contract.check.no_artifacts", details={}, status="error")
        return

    _log_activity("contract.check.loaded", details={"count": len(contracts)})

    # Step 2: Build yaml_dict từ artifacts
    yaml_dict = {}
    for artifact in contracts:
        artifact_id = artifact.get("artifact_id", "")
        if artifact_id.startswith("contract_"):
            category = artifact_id[len("contract_"):]
            yaml_content = artifact.get("content", "")
            yaml_dict[category] = yaml_content
            _log_activity("contract.check.category_loaded", resource_id=category,
                         details={"category": category})

    # Check missing categories
    missing = set(REQUIRED_CATEGORIES) - set(yaml_dict.keys())
    if missing:
        _log_activity("contract.check.missing_categories",
                     details={"missing": sorted(missing)}, status="warning")

    # Step 3: Parse YAML strings → ProjectionTree
    _log_activity("contract.check.parsing")

    try:
        dsl_parser = DSLParser()
        tree = dsl_parser.build_projection_tree(yaml_dict)
        _log_activity("contract.check.parsed", details={"node_count": tree.node_count()})
    except Exception as e:
        _log_activity("contract.check.parse_failed", details={"error": str(e)}, status="error")
        return

    # Step 4: Validate với DSL validator
    _log_activity("contract.check.validating")

    try:
        report = validate_tree(tree)

        _log_activity("contract.check.complete", details={
            "total_errors": report.total_errors,
            "total_warnings": report.total_warnings,
            "total_info": report.total_info
        })

        # Report errors by node
        if report.total_errors > 0:
            errors_by_node = report.get_errors_by_node()
            error_details = {}
            for node_id, node_errors in errors_by_node.items():
                error_details[node_id] = len(node_errors)
                for error in node_errors[:3]:
                    error_details.setdefault(node_id, [])
            _log_activity("contract.check.errors", details=error_details, status="error")

        # Report warnings
        if report.total_warnings > 0:
            warning_details = []
            for warning in report.get_warnings()[:5]:
                warning_details.append({"node_id": warning.node_id, "message": warning.message})
            _log_activity("contract.check.warnings", details={"warnings": warning_details}, status="warning")

        # Report dependency cycles
        if report.dependency_analysis and report.dependency_analysis.cycles:
            cycle_details = []
            for cycle in report.dependency_analysis.cycles[:3]:
                cycle_details.append(" → ".join(cycle.nodes))
            _log_activity("contract.check.cycles", details={"cycles": cycle_details}, status="warning")

    except Exception as e:
        _log_activity("contract.check.validation_failed", details={"error": str(e)}, status="error")
        return

    # Final report
    if report.status == ValidationStatus.VALID:
        _log_activity("contract.check.valid", details={"status": "passed"})
    elif report.status == ValidationStatus.WARNINGS:
        if strict:
            _log_activity("contract.check.warnings_strict", details={"status": "error_in_strict_mode"}, status="error")
        else:
            _log_activity("contract.check.warnings", details={"status": "valid_with_warnings"}, status="warning")
    elif report.status == ValidationStatus.ERRORS:
        _log_activity("contract.check.errors_found", details={"auto_fix": auto_fix}, status="error")

        if auto_fix:
            _log_activity("contract.check.auto_fix_triggered")
            repair_contracts()
    else:  # FATAL
        _log_activity("contract.check.fatal", details={"status": "fatal_validation_errors"}, status="error")


def _load_contracts_from_sqlite() -> Optional[ProjectionTree]:
    """
    Load contract artifacts từ SQLite và build ProjectionTree.

    Returns:
        ProjectionTree hoặc None nếu không có contracts
    """
    artifacts_manager = ArtifactsManager()
    artifacts_manager.init()

    contracts = artifacts_manager.list_by_type("contract")
    if not contracts:
        return None

    yaml_dict = {}
    for artifact in contracts:
        artifact_id = artifact.get("artifact_id", "")
        if artifact_id.startswith("contract_"):
            category = artifact_id[len("contract_"):]
            yaml_content = artifact.get("content", "")
            yaml_dict[category] = yaml_content

    if not yaml_dict:
        return None

    dsl_parser = DSLParser()
    return dsl_parser.build_projection_tree(yaml_dict)


# ============================================================================
# Contract Repair (LLM-based)
# ============================================================================

def repair_contracts():
    """
    Sửa contracts có lỗi bằng LLM.

    Process (SQLite-only):
    1. Load contract artifacts từ SQLite
    2. Validate để tìm errors
    3. Nếu có errors → gọi LLM để fix YAML content
    4. Re-validate để confirm fix thành công
    5. Upsert fixed artifacts vào SQLite
    6. Retry tối đa MAX_REPAIR_ATTEMPTS lần
    """
    _log_activity("contract.repair.started")

    # Step 1: Load contracts từ SQLite
    artifacts_manager = ArtifactsManager()
    artifacts_manager.init()

    contracts = artifacts_manager.list_by_type("contract")
    if not contracts:
        _log_activity("contract.repair.no_artifacts", details={}, status="error")
        return

    _log_activity("contract.repair.loaded", details={"count": len(contracts)})

    # Load LLM config
    try:
        config = load_llm_config()
    except Exception as e:
        _log_activity("contract.repair.llm_config_failed", details={"error": str(e)}, status="error")
        return

    # Build yaml_dict
    yaml_dict = {}
    for artifact in contracts:
        artifact_id = artifact.get("artifact_id", "")
        if artifact_id.startswith("contract_"):
            category = artifact_id[len("contract_"):]
            yaml_content = artifact.get("content", "")
            yaml_dict[category] = yaml_content

    # Step 2: Validate để tìm errors
    _log_activity("contract.repair.validating")

    dsl_parser = DSLParser()
    tree = dsl_parser.build_projection_tree(yaml_dict)
    report = validate_tree(tree)

    if report.total_errors == 0:
        _log_activity("contract.repair.already_valid", details={}, status="success")
        return

    _log_activity("contract.repair.errors_found", details={"total_errors": report.total_errors})

    # Step 3: Repair bằng LLM
    errors_by_node = report.get_errors_by_node()

    repaired_count = 0
    failed_categories: list[str] = []

    for category in REQUIRED_CATEGORIES:
        if category not in yaml_dict:
            continue

        current_content = yaml_dict[category]

        try:
            parsed_data = yaml.safe_load(current_content)
        except Exception:
            parsed_data = {}

        # Collect errors for this category
        category_errors = []
        for node_id, node_errors in errors_by_node.items():
            category_errors.extend(node_errors)

        if not category_errors:
            _log_activity("contract.repair.no_errors", resource_id=category,
                         details={"category": category})
            continue

        _log_activity("contract.repair.category.started", resource_id=category,
                     details={"category": category})

        success = False
        fixed_content = None

        for attempt in range(1, MAX_REPAIR_ATTEMPTS + 1):
            if attempt > 1:
                _log_activity("contract.repair.retry", resource_id=category,
                             details={"attempt": attempt, "max": MAX_REPAIR_ATTEMPTS})

            result, fixed = _try_fix_with_llm(
                config, category, parsed_data, category_errors
            )

            if not result or fixed is None:
                continue

            fixed_content = fixed
            fixed_yaml = yaml.dump(fixed, default_flow_style=False, allow_unicode=True)

            # Validate fix
            try:
                temp_yaml_dict = {category: fixed_yaml}
                temp_tree = dsl_parser.build_projection_tree(temp_yaml_dict)
                temp_report = validate_tree(temp_tree)

                if temp_report.total_errors == 0:
                    success = True
                    _log_activity("contract.repair.category.fixed", resource_id=category,
                                 details={"category": category, "attempts": attempt})
                    break
                else:
                    category_errors = []
                    for node_id, node_errors in temp_report.get_errors_by_node().items():
                        category_errors.extend(node_errors)
                    _log_activity("contract.repair.still_errors", resource_id=category,
                                 details={"remaining_errors": temp_report.total_errors},
                                 status="warning")
            except Exception as e:
                _log_activity("contract.repair.validation_error", resource_id=category,
                             details={"error": str(e)}, status="warning")

        if success and fixed_content is not None:
            fixed_yaml = yaml.dump(fixed_content, default_flow_style=False, allow_unicode=True)
            existing_artifact = artifacts_manager.get(f"contract_{category}")
            brief_id = existing_artifact.get("brief_id", "unknown") if existing_artifact else "unknown"
            _upsert_contract_artifact(
                artifacts_manager, category, fixed_yaml, brief_id
            )
            repaired_count += 1
        else:
            _log_activity("contract.repair.category.failed", resource_id=category,
                         details={"category": category, "max_attempts": MAX_REPAIR_ATTEMPTS},
                         status="error")
            failed_categories.append(category)

    # Final report
    if repaired_count > 0:
        _log_activity("contract.repair.completed", details={"repaired_count": repaired_count})

    if failed_categories:
        _log_activity("contract.repair.partial_failure",
                     details={"failed_categories": failed_categories, "failed_count": len(failed_categories)},
                     status="warning")
    else:
        _log_activity("contract.repair.all_success", details={"repaired_count": repaired_count})


def _build_repair_prompt(
    category: str,
    content: dict,
    errors: list,
) -> tuple[str, str]:
    """
    Xây dựng prompt để LLM fix contracts.

    Tải system prompt từ file Markdown.

    Args:
        category: Category name (entities, commands, ...)
        content: Nội dung YAML hiện tại
        errors: Danh sách validation errors

    Returns:
        Tuple của (system prompt, user prompt)
    """
    # Load system prompt từ file
    system = load_prompt("contract_repair")

    error_messages = "\n".join(
        f"- {getattr(e, 'message', str(e))}" for e in errors
    )

    yaml_content = yaml.dump(content, default_flow_style=False, allow_unicode=True)

    user = f"""Category: {category}

Current YAML content:
{yaml_content}

Validation errors:
{error_messages}

Please fix the YAML to resolve all validation errors. Output ONLY the complete fixed YAML content, no markdown formatting."""

    return system, user


def _try_fix_with_llm(
    config: LlmConfig,
    category: str,
    content: dict,
    errors: list,
) -> tuple[bool, Optional[dict]]:
    """
    Thử fix contracts bằng LLM.

    Args:
        config: LLM config
        category: Category name
        content: Nội dung YAML hiện tại
        errors: Danh sách validation errors

    Returns:
        Tuple của (success, fixed_content hoặc None)
    """
    try:
        system, user = _build_repair_prompt(category, content, errors)

        response = call_llm(
            config,
            system=system,
            messages=[{"role": "user", "content": user}],
        )

        yaml_content = _extract_yaml_from_text(response.content, category)

        fixed_content = yaml.safe_load(yaml_content)

        if not isinstance(fixed_content, dict):
            _log_activity("contract.repair.not_dict", resource_id=category,
                         details={"category": category}, status="warning")
            return False, None

        return True, fixed_content

    except APIError as e:
        _log_activity("contract.repair.llm_error", resource_id=category,
                     details={"category": category, "error": str(e)}, status="error")
        return False, None
    except yaml.YAMLError as e:
        _log_activity("contract.repair.invalid_yaml", resource_id=category,
                     details={"category": category, "error": str(e)}, status="error")
        return False, None
    except Exception as e:
        _log_activity("contract.repair.processing_error", resource_id=category,
                     details={"category": category, "error": str(e)}, status="error")
        return False, None


# ============================================================================
# Single-Category SSE Streaming (for per-category generation with contract-gen-progress)
# ============================================================================

async def generate_category_stream_for_api(category: str, force: bool = False) -> AsyncIterator[Dict[str, Any]]:
    """
    Task-based SSE streaming — gen 1 category through 4 self-contained LLM tasks.

    Tasks:
      1. learn_schema  — LLM calls get_dsl_section, learns DSL rules
      2. draft_yaml    — LLM writes YAML draft (NO tools, pure text output)
      3. validate      — LLM validates + fixes YAML (tools: validate_contract_yaml, cross_check_category, tool loop allowed)
      4. final_review  — LLM outputs final YAML (NO tools)

    Each task starts with a FRESH conversation. Results are summarized and passed
    to the next task's prompt — no conversation accumulation.

    Compatible with contract-gen-progress component.

    Yields dict with keys: "event" (str) and "data" (str|dict).
    """
    # ── Resolve project path ──
    project_cwd = get_active_project_cwd()
    if not project_cwd:
        yield {"event": "error", "data": "Không có project active"}
        return

    # ── Category order enforcement ──
    order = REQUIRED_CATEGORIES
    idx = order.index(category) if category in order else -1

    artifacts_db = get_project_db_path(project_cwd, "artifacts.db")
    artifacts_manager = ArtifactsManager(db_path=artifacts_db)
    artifacts_manager.init()

    if idx > 0:
        for prev_cat in order[:idx]:
            art = artifacts_manager.get(f"contract_{prev_cat}")
            if not art:
                prev_display = _CATEGORY_PROMPT_MAP.get(prev_cat, prev_cat)
                yield {"event": "error", "data": f"Vui lòng tạo {prev_cat} trước khi tạo {category}"}
                return

    # ── Pre-checks: find brief via project-level DB ──
    briefs_db = get_project_db_path(project_cwd, "briefs.db")
    briefs_manager = BriefsManager(db_path=briefs_db)
    briefs_manager.init()

    active_version = _get_active_version()
    active_brief = _find_brief(briefs_manager, active_version)

    if not active_brief:
        yield {"event": "error", "data": "Không tìm thấy brief cho version này"}
        return

    if active_brief.get('status') != 'freezed':
        yield {"event": "error", "data": "Brief chưa được freeze"}
        return

    brief_id = active_brief.get('brief_id')
    brief_content = active_brief.get('content', '')

    # Check if already exists (unless force)
    if not force:
        existing = artifacts_manager.get(f"contract_{category}")
        if existing:
            yield {"event": "error", "data": f"Contract {category} đã tồn tại"}
            return

    # Load analysis data
    analysis_data = {}
    try:
        analysis_artifact = artifacts_manager.get(f"analysis-{brief_id}")
        if analysis_artifact:
            analysis_data = json.loads(analysis_artifact.get("content", "{}"))
    except Exception:
        pass

    # Load clarifications
    clarifications = []
    try:
        clarifications = briefs_manager.get_clarifications(brief_id)
    except Exception:
        pass

    # Load LLM config
    config = None
    try:
        config = load_llm_config()
    except Exception:
        yield {"event": "error", "data": "LLM chưa được cấu hình"}
        return

    # ── Load prerequisite artifact YAMLs (injected into task prompts) ──
    category_deps = {
        "entities": [],
        "commands": ["entities"],
        "queries": ["entities"],
        "events": ["entities"],
        "workflows": ["commands", "events", "queries"],
        "value_objects": ["entities"],
        "guards": ["entities", "commands", "queries", "roles"],
        "roles": ["entities"],
        "ui_components": ["entities"],
    }
    prerequisites = category_deps.get(category, [])
    prereq_yaml: Dict[str, str] = {}
    for dep in prerequisites:
        try:
            dep_artifact = artifacts_manager.get(f"contract_{dep}")
            if dep_artifact and dep_artifact.get("content"):
                prereq_yaml[dep] = dep_artifact["content"]
        except Exception:
            pass

    prereq_text = ""
    if prereq_yaml:
        parts = [f"## Pre-generated: {k}\n```yaml\n{v}\n```" for k, v in prereq_yaml.items()]
        prereq_text = "\n\n".join(parts) + "\n\nIMPORTANT: Use entity IDs from the pre-generated sections above. Do NOT invent new IDs."

    # ── Build category-specific base prompts ──
    base_system, base_user = _build_category_prompt(
        category, analysis_data, clarifications, brief_content, include_mcp_context=False
    )

    # ── Tool definitions (shared across tasks) ──
    tool_definitions = _build_tool_definitions(category)

    # ── Tool executor (in-process) ──
    _tool_executor = _build_tool_executor(category)

    # ── Send init events ──
    yield {"event": "started", "data": {"category": category, "brief_id": brief_id}}
    yield {"event": "system_prompt", "data": base_system}
    yield {"event": "llm_config", "data": {"model": config.model, "temperature": config.temperature, "max_tokens": config.max_tokens}}
    yield {"event": "user_payload", "data": {"user_message_length": len(base_user)}}

    # ── Load tool-use workflow instructions from shared prompt file ──
    try:
        workflow_prompt = load_prompt("_shared/tool_use_workflow")
        import re as _re
        workflow_prompt = _re.sub(r"\{\{\s*category\s*\}\}", category, workflow_prompt)
    except Exception:
        workflow_prompt = ""

    # ── Define the 4 tasks ──
    from midicoder.pipeline.llm.task_orchestrator import TaskOrchestrator, TaskDefinition

    tasks: list[TaskDefinition] = []

    # TASK 1: Learn Schema — LLM calls get_dsl_section to learn DSL rules
    task1_system = (
        f"You are a DSL schema learning assistant for the Midicoder platform.\n"
        f"Your task: Learn the DSL schema for the \"{category}\" category.\n\n"
        f"{workflow_prompt}"
    )
    task1_user = (
        f"Learn the DSL schema for category \"{category}\".\n"
        f"Call get_dsl_section(section=\"{category}\") to get the schema.\n"
        f"Pass the section parameter: {{\"section\": \"{category}\"}}\n"
        f"Do NOT call any other tools. Output the summary."
    )
    tasks.append(TaskDefinition(
        task_id="learn_schema",
        system=task1_system,
        user=task1_user,
        tools=[t for t in tool_definitions if t["function"]["name"] in ("get_dsl_section", "get_dsl_schema")],
        allow_tool_loop=False,
    ))

    # TASK 2: Draft YAML — pure text output, NO tools
    schema_summary = ""  # Will be filled after task 1
    task2_system = base_system
    task2_user = (
        f"## Context\n"
        f"You learned the DSL schema:\n{schema_summary}\n\n"
        f"{base_user}\n\n"
        f"{prereq_text}\n\n"
        f"## Task\n"
        f"Generate valid YAML contracts for the \"{category}\" category.\n"
        f"Output ONLY the YAML dict. Do NOT call any tools. Do NOT wrap in markdown code fences."
    )
    tasks.append(TaskDefinition(
        task_id="draft_yaml",
        system=task2_system,
        user=task2_user,
        tools=[],  # No tools — pure text output
        allow_tool_loop=False,
    ))

    # TASK 3: Validate & Fix — LLM validates + fixes YAML (tool loop allowed)
    yaml_draft = ""  # Will be filled after task 2
    task3_system = (
        f"You are a DSL contract validation and repair expert for the Midicoder platform.\n\n"
        f"{workflow_prompt}\n\n"
        f"## CRITICAL REMINDER\n"
        f"You MUST call validate_contract_yaml FIRST with the full YAML as yaml_content parameter.\n"
        f"Then call cross_check_category with the same YAML.\n"
        f"Never call tools without providing yaml_content.\n"
        f"Example: validate_contract_yaml(yaml_content=\"entities:\\\\n  - id: user\\n    ...\")"
    )
    task3_user = (
        f"Validate and fix this YAML for category \"{category}\":\n\n"
        f"```yaml\n{yaml_draft}\n```\n\n"
        f"## Steps:\n"
        f"1. Call validate_contract_yaml(yaml_content=\"FULL_YAML_HERE\") — pass the full YAML string above\n"
        f"2. If valid=true, call cross_check_category(yaml_content=\"FULL_YAML_HERE\") — cross-check references\n"
        f"3. If errors found, fix them and repeat from step 1 (max 3 attempts)\n"
        f"4. When both pass, output the validated YAML and stop\n\n"
        f"IMPORTANT: The yaml_content parameter MUST be a non-empty string with the full YAML content.\n"
        f"Wrong: validate_contract_yaml({{}})\n"
        f"Correct: validate_contract_yaml(yaml_content=\"entities:\\\\n  - id: example\")"
    )
    tasks.append(TaskDefinition(
        task_id="validate",
        system=task3_system,
        user=task3_user,
        tools=[t for t in tool_definitions if t["function"]["name"] in ("validate_contract_yaml", "cross_check_category")],
        allow_tool_loop=True,  # Allow tool loop for validate → fix → re-validate
    ))

    # TASK 4: Final Review — LLM outputs final YAML (no tools)
    validated_yaml = ""  # Will be filled after task 3
    validation_result = ""
    task4_system = (
        f"You are a DSL contract final review expert.\n"
        f"Your task: Output the final validated YAML for \"{category}\".\n"
        f"Do NOT call any tools. Output ONLY the YAML dict."
    )
    task4_user = (
        f"Output the final YAML for category \"{category}\".\n\n"
        f"Validation result: {validation_result}\n\n"
        f"YAML to output:\n```yaml\n{validated_yaml}\n```\n\n"
        f"Output the YAML dict directly. Do NOT call any tools."
    )
    tasks.append(TaskDefinition(
        task_id="final_review",
        system=task4_system,
        user=task4_user,
        tools=[],
        allow_tool_loop=False,
    ))

    # ── Execute tasks sequentially, wiring intermediate results ──
    start_time = time.time()
    final_content = ""
    round_count = 0

    def _capture_result(evt: Dict[str, Any]) -> Dict[str, Any]:
        """Extract captured results from the special task_result event."""
        data = evt.get("data", {})
        if data.get("_captured"):
            return {
                "accumulated_text": data.get("accumulated_text", ""),
                "tool_calls": data.get("tool_calls", []),
                "tool_results": data.get("tool_results", []),
            }
        return {}

    try:
        # ── TASK 1: Learn Schema ──
        schema_result = {}
        async for evt in _execute_task_and_capture(config, tasks[0], _tool_executor, category):
            yield evt
            r = _capture_result(evt)
            if r:
                schema_result = r
                round_count += len(r.get("tool_calls", []))
        schema_result_data = schema_result.get("tool_results", [{}])[0].get("result", {}) if schema_result.get("tool_results") else {}
        schema_text = json.dumps(schema_result_data, indent=2, ensure_ascii=False) if schema_result_data else ""

        # ── TASK 2: Draft YAML ──
        tasks[1] = TaskDefinition(
            task_id="draft_yaml",
            system=base_system,
            user=(
                f"## DSL Schema Context\n"
                f"Here is the DSL schema for \"{category}\":\n"
                f"{schema_text}\n\n"
                f"## Project Context\n"
                f"{base_user}\n\n"
                f"{prereq_text}\n\n"
                f"## Task\n"
                f"Generate valid YAML contracts for the \"{category}\" category.\n"
                f"Use the schema above for field structure. Use pre-generated IDs for references.\n"
                f"Output ONLY the YAML dict. Do NOT call any tools. Do NOT wrap in markdown code fences."
            ),
            tools=[],
            allow_tool_loop=False,
        )
        yaml_draft = ""
        async for evt in _execute_task_and_capture(config, tasks[1], _tool_executor, category):
            yield evt
            r = _capture_result(evt)
            if r:
                yaml_draft = _extract_yaml_from_text(r.get("accumulated_text", ""), category)

        # ── TASK 3: Validate & Fix ──
        tasks[2] = TaskDefinition(
            task_id="validate",
            system=task3_system,
            user=(
                f"Validate and fix this YAML for category \"{category}\":\n\n"
                f"```yaml\n{yaml_draft}\n```\n\n"
                f"Call validate_contract_yaml(yaml_content=\"...\") with the full YAML string.\n"
                f"If valid=true, output the validated YAML and stop.\n"
                f"If valid=false, fix the listed errors and call validate_contract_yaml again.\n"
                f"Max 3 validation attempts. Then output your best result."
            ),
            tools=[t for t in tool_definitions if t["function"]["name"] in ("validate_contract_yaml", "cross_check_category")],
            allow_tool_loop=True,
        )
        validated_yaml = yaml_draft
        validation_result_str = "PASSED ✓"
        async for evt in _execute_task_and_capture(config, tasks[2], _tool_executor, category):
            yield evt
            r = _capture_result(evt)
            if r:
                round_count += len(r.get("tool_calls", []))
                v_yaml = _extract_yaml_from_text(r.get("accumulated_text", ""), category)
                if v_yaml and len(v_yaml) >= len(yaml_draft):
                    validated_yaml = v_yaml
                # Check validation status
                for tr in r.get("tool_results", []):
                    if tr.get("name") == "validate_contract_yaml":
                        vr = tr.get("result", {})
                        is_valid = vr.get("is_valid", False) if isinstance(vr, dict) else False
                        val_errors = vr.get("total_errors", 0) if isinstance(vr, dict) else -1
                        validation_result_str = "PASSED ✓" if is_valid else f"FAILED: {val_errors} errors"

        # ── TASK 4: Final Review ──
        tasks[3] = TaskDefinition(
            task_id="final_review",
            system=task4_system,
            user=(
                f"Output the final YAML for category \"{category}\".\n\n"
                f"Validation: {validation_result_str}\n\n"
                f"YAML:\n```yaml\n{validated_yaml}\n```\n\n"
                f"Output the YAML dict directly. Do NOT call any tools. Do NOT add commentary."
            ),
            tools=[],
            allow_tool_loop=False,
        )
        final_content = validated_yaml
        async for evt in _execute_task_and_capture(config, tasks[3], _tool_executor, category):
            yield evt
            r = _capture_result(evt)
            if r:
                fc = _extract_yaml_from_text(r.get("accumulated_text", ""), category)
                if fc:
                    final_content = fc
        if not final_content:
            final_content = validated_yaml

        # ── Mandatory server-side validation ──
        validation_passed = False
        repair_round = 0
        while not validation_passed and repair_round < 3:
            try:
                yaml.safe_load(final_content)
                parser = DSLParser()
                nodes = parser.parse_yaml_string(final_content, category)
                tree = ProjectionTree(nodes={n.id: n for n in nodes})
                tree.nodes_by_kind = {}
                for n in nodes:
                    if n.kind not in tree.nodes_by_kind:
                        tree.nodes_by_kind[n.kind] = []
                    tree.nodes_by_kind[n.kind].append(n)
                report = validate_tree(tree)

                if report.total_errors == 0:
                    validation_passed = True
                else:
                    repair_round += 1
                    error_msgs = [r.message for r in report.constraint_results if r.level.value == "error"][:5]
                    yield {"event": "repair_round", "data": {"round": repair_round, "errors": error_msgs}}
                    logger.warning(f"[CONTRACT GEN] Post-validation failed (repair {repair_round}): {'; '.join(error_msgs)}")

                    repair_prompt = (
                        f"Fix validation errors in YAML for '{category}':\n\n"
                        f"Errors:\n" + "\n".join(f"  - {e}" for e in error_msgs) + "\n\n"
                        f"YAML:\n```\n{final_content}\n```\n\n"
                        f"Output ONLY the fixed YAML. No commentary."
                    )
                    repair_result = await _execute_task_and_capture(
                        config, TaskDefinition(
                            task_id="validate",
                            system="You are a YAML repair expert. Fix errors and output valid YAML.",
                            user=repair_prompt,
                            tools=[],
                            allow_tool_loop=False,
                        ),
                        _tool_executor, category, yield_event=True
                    )
                    final_content = _extract_yaml_from_text(repair_result.get("accumulated_text", ""), category)

            except yaml.YAMLError as ye:
                repair_round += 1
                yield {"event": "repair_round", "data": {"round": repair_round, "errors": [f"YAML syntax error: {str(ye)}"]}}
                if repair_round >= 3:
                    break

        if not validation_passed:
            raise ValueError(f"Contract validation failed after 3 repair rounds. Contract NOT saved.")

        # Save to SQLite
        _upsert_contract_artifact(artifacts_manager, category, final_content, brief_id)
        latency_ms = int((time.time() - start_time) * 1000)
        _log_activity("contract.category_gen", resource_id=category, details={"category": category, "tool_rounds": round_count, "repair_rounds": repair_round})

        # Estimate tokens
        tokens_used = prompt_tokens = completion_tokens = 0
        try:
            from midicoder.pipeline.llm import count_tokens
            prompt_tokens = count_tasks_token_estimate(tasks, category)
            completion_tokens = count_tokens(final_content, config.model)
            tokens_used = prompt_tokens + completion_tokens
        except Exception:
            pass

        yield {"event": "final_content", "data": final_content}
        yield {"event": "complete", "data": {
            "category": category,
            "total_tokens": tokens_used,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "latency_ms": latency_ms,
            "tool_rounds": round_count,
        }}

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"[CONTRACT GEN ERROR] category={category}: {e}\n{tb}")
        yield {"event": "error", "data": f"{e}\nTraceback:\n{tb}"}
        _log_activity("contract.category_gen_error", resource_id=category, details={"error": str(e)}, status="error")


def count_tasks_token_estimate(tasks: list, category: str) -> int:
    """Rough estimate of prompt tokens across all tasks."""
    try:
        from midicoder.pipeline.llm import count_tokens
        total = 0
        for t in tasks:
            total += count_tokens(t.system + t.user, "cl100k_base")
        return total
    except Exception:
        return 0


async def _execute_task_and_capture(
    config: LlmConfig,
    task: Any,
    tool_executor,
    category: str,
) -> AsyncIterator[Dict[str, Any]]:
    """
    Async generator: yields SSE events in real-time as LLM streams.
    The LAST event is a special 'task_result' with captured data.
    """
    from midicoder.pipeline.llm.task_orchestrator import call_llm_task

    _TASK_LABEL_MAP = {
        "learn_schema": "Học Schema",
        "draft_yaml": "Viết YAML Draft",
        "validate": "Validate & Sửa",
        "final_review": "Output Final",
    }

    accumulated_text = ""
    tool_calls_list: list[Dict[str, Any]] = []
    tool_results_list: list[Dict[str, Any]] = []

    task_name = _TASK_LABEL_MAP.get(task.task_id, task.task_id)
    yield {"event": "task_started", "data": {"task": task.task_id, "task_name": task_name}}

    async for chunk in call_llm_task(config, task, tool_executor):
        if chunk.content:
            content = chunk.content
            if content == "\n":
                yield {"event": "heartbeat", "data": {"round": len(tool_calls_list)}}
                continue

            if "<antThinking>" in content or "<thinking>" in content or "<think>" in content:
                yield {"event": "thinking", "data": {"text": content}}
            elif content.strip() and len(content.strip()) > 1:
                accumulated_text += content
                yield {"event": "content", "data": {"text": content, "accumulated": accumulated_text}}

            if "</antThinking>" in content or "</thinking>" in content or "</think>" in content:
                yield {"event": "thinking_end", "data": ""}

        if chunk.tool_calls:
            for tc in chunk.tool_calls:
                tool_name = tc.get("function", {}).get("name", "unknown")
                args_json = tc.get("function", {}).get("arguments", "{}")
                try:
                    parsed_args = json.loads(args_json) if args_json else {}
                except Exception:
                    parsed_args = {}
                tool_calls_list.append({"name": tool_name, "arguments": parsed_args})
                yield {"event": "tool_call", "data": {
                    "name": tool_name, "arguments": parsed_args, "duration_ms": 0
                }}

        if chunk.tool_results:
            for tr in chunk.tool_results:
                tool_name = tr.get("name", "unknown")
                result_str = tr.get("result", "")
                try:
                    result_obj = json.loads(result_str) if result_str else {}
                except Exception:
                    result_obj = {"raw": str(result_str)[:200]}

                is_error = "error" in result_obj if isinstance(result_obj, dict) else False
                summary = _result_summary(tool_name, result_obj, is_error)
                tool_results_list.append({"name": tool_name, "result": result_obj, "is_error": is_error})
                yield {"event": "tool_result", "data": {
                    "name": tool_name, "summary": summary, "full_result": result_obj, "duration_ms": 0
                }}

    # Task completed summary
    if task.task_id == "learn_schema":
        summary_text = f"Schema đã tải ({len(tool_results_list)} tool calls)"
    elif task.task_id == "draft_yaml":
        summary_text = f"YAML draft ({len(accumulated_text)} chars)"
    elif task.task_id == "validate":
        valid_tr = [t for t in tool_results_list if t["name"] == "validate_contract_yaml"]
        if valid_tr and valid_tr[-1].get("result", {}).get("is_valid"):
            summary_text = "Validation passed ✓"
        else:
            summary_text = "Validation completed"
    else:
        summary_text = "Final YAML ready"
    yield {"event": "task_completed", "data": {
        "task": task.task_id, "task_name": task_name, "summary": summary_text
    }}
    # Last event: captured results for caller
    yield {"event": "task_result", "data": {
        "_captured": True,
        "accumulated_text": accumulated_text,
        "tool_calls": tool_calls_list,
        "tool_results": tool_results_list,
    }}


def _result_summary(tool_name: str, result_obj: dict, is_error: bool) -> dict:
    if is_error:
        return {"valid": False, "error": result_obj.get("error", "Unknown error")}
    if tool_name == "validate_contract_yaml":
        return {
            "valid": result_obj.get("is_valid", False),
            "errors": result_obj.get("total_errors", 0),
            "warnings": result_obj.get("total_warnings", 0),
        }
    if tool_name == "cross_check_category":
        return {
            "valid": result_obj.get("valid", True),
            "errors": len(result_obj.get("errors", [])),
            "warnings": len(result_obj.get("warnings", [])),
        }
    return {"found": bool(result_obj)}


def _build_tool_definitions(category: str) -> list[dict]:
    """Build OpenAI-format tool definitions for contract generation."""
    return [
        {
            "type": "function",
            "function": {
                "name": "get_dsl_section",
                "description": f"Returns DSL schema for a specific section. Use to learn fields for category '{category}'.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "section": {
                            "type": "string",
                            "description": f"Section name. For current category use '{category}'.",
                        },
                    },
                    "required": ["section"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "validate_contract_yaml",
                "description": f"Validate YAML + DSL constraints for category '{category}'.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "yaml_content": {
                            "type": "string",
                            "description": "Raw YAML string to validate",
                        },
                    },
                    "required": ["yaml_content"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "cross_check_category",
                "description": f"Cross-check references in category '{category}' against other generated categories.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "yaml_content": {
                            "type": "string",
                            "description": "Raw YAML string to cross-check",
                        },
                    },
                    "required": ["yaml_content"],
                },
            },
        },
    ]


def _build_tool_executor(category: str):
    """Build the in-process tool executor for contract generation."""
    _TOOL_REQUIRED_PARAMS = {
        "get_dsl_section": ["section"],
        "validate_contract_yaml": ["yaml_content"],
        "cross_check_category": ["yaml_content"],
    }

    async def _tool_executor(tool_name: str, args: dict) -> str:
        try:
            required = _TOOL_REQUIRED_PARAMS.get(tool_name, [])
            missing = [p for p in required if not args.get(p)]
            if missing:
                return json.dumps({
                    "error": f"Tool '{tool_name}' missing required parameters: {missing}. "
                             f"Required: {', '.join(required)}."
                }, ensure_ascii=False)

            if tool_name == "get_dsl_section":
                from midicoder.mcp.tools.dsl_schema import get_dsl_section
                result = get_dsl_section(args["section"])
            elif tool_name == "validate_contract_yaml":
                result = _validate_single_category(category, args["yaml_content"])
            elif tool_name == "cross_check_category":
                result = _cross_check_category(category, args["yaml_content"])
            else:
                result = {"error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            result = {"error": f"Tool execution failed: {str(e)}"}
        return json.dumps(result, ensure_ascii=False)

    return _tool_executor


# ============================================================================
# Contract Freeze
# ============================================================================

def freeze_contracts() -> Dict[str, Any]:
    """
    Freeze all contract artifacts — lock as source of truth for code gen.

    Process:
    1. Load all contract artifacts
    2. Validate they are complete (all 9 categories present)
    3. Set status to 'freezed' for each
    4. Record snapshot hash per category

    Returns:
        Dict with freeze result
    """
    _log_activity("contract.freeze.started")

    artifacts_manager = ArtifactsManager()
    artifacts_manager.init()

    contracts = artifacts_manager.list_by_type("contract")
    if not contracts:
        _log_activity("contract.freeze.no_artifacts", status="error")
        return {"success": False, "error": "Không có contracts để freeze"}

    # Check all categories present
    category_set = set()
    for art in contracts:
        aid = art.get("artifact_id", "")
        if aid.startswith("contract_"):
            category_set.add(aid[len("contract_"):])

    missing = set(REQUIRED_CATEGORIES) - category_set
    if missing:
        _log_activity("contract.freeze.incomplete", details={"missing": sorted(missing)}, status="warning")
        return {
            "success": False,
            "error": f"Thiếu categories: {', '.join(sorted(missing))}",
            "missing": sorted(missing),
        }

    # Validate before freeze
    try:
        yaml_dict = {}
        for art in contracts:
            aid = art.get("artifact_id", "")
            if aid.startswith("contract_"):
                yaml_dict[aid[len("contract_"):]] = art.get("content", "")

        dsl_parser = DSLParser()
        tree = dsl_parser.build_projection_tree(yaml_dict)
        report = validate_tree(tree)

        if report.status == ValidationStatus.FATAL:
            return {
                "success": False,
                "error": f"Contracts có {report.total_errors} lỗi nghiêm trọng, không thể freeze",
                "errors": report.total_errors,
            }
    except Exception as e:
        _log_activity("contract.freeze.validation_error", details={"error": str(e)}, status="error")
        return {"success": False, "error": f"Validation failed: {e}"}

    # Freeze: update status + record snapshot
    import hashlib
    frozen_count = 0
    for art in contracts:
        aid = art.get("artifact_id", "")
        content = art.get("content", "")
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        artifacts_manager.update_content(aid, content)
        # Update metadata with freeze info
        existing_meta = art.get("metadata", {})
        existing_meta.update({
            "frozen": True,
            "frozen_at": datetime.now(timezone.utc).isoformat(),
            "content_hash": content_hash,
            "validation_status": report.status.value,
        })

        frozen_count += 1
        _log_activity("contract.freeze.category", resource_id=aid,
                     details={"hash": content_hash})

    _log_activity("contract.freeze.completed", details={
        "frozen_count": frozen_count,
        "validation_status": report.status.value,
        "errors": report.total_errors,
        "warnings": report.total_warnings,
    })

    return {
        "success": True,
        "frozen_count": frozen_count,
        "validation_status": report.status.value,
        "errors": report.total_errors,
        "warnings": report.total_warnings,
    }


__all__ = [
    "generate_contracts",
    "generate_category_stream_for_api",
    "check_contracts",
    "repair_contracts",
    "freeze_contracts",
    "_generate_contracts_with_llm",
    "_build_category_prompt",
    "_build_mcp_context",
    "_get_styles_schema_for_category",
    "_generate_category_with_retry",
    "_auto_fix_contracts",
    "_generate_contracts_to_sqlite",
    "_build_placeholder_yaml",
    "_upsert_contract_artifact",
    "_load_contracts_from_sqlite",
    "_try_fix_with_llm",
    "_build_repair_prompt",
    "REQUIRED_CATEGORIES",
    "MAX_REPAIR_ATTEMPTS",
]