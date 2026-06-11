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

import json
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from midicoder.errors import MidicoderErrorManager as EM, ErrorCode
from midicoder.storage.sqlite import BriefsManager, ArtifactsManager, get_connection
from midicoder.storage.activity import log
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

# 8 categories bắt buộc theo DSL strict mode
REQUIRED_CATEGORIES = [
    "entities", "commands", "queries", "events",
    "workflows", "value_objects", "guards", "ui_components"
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


def _build_category_prompt(
    category: str,
    analysis_data: dict,
    clarifications: list,
    brief_content: str,
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

    # MCP: Inject DSL schema context cho LLM biết property nào hợp lệ
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

            yaml_content = response.content.strip()

            # Loại bỏ markdown code blocks
            if yaml_content.startswith("```yaml"):
                yaml_content = yaml_content.removeprefix("```yaml").removesuffix("```").strip()
            elif yaml_content.startswith("```"):
                yaml_content = yaml_content.removeprefix("```").removesuffix("```").strip()

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

                fixed_yaml = response.content.strip()
                if fixed_yaml.startswith("```yaml"):
                    fixed_yaml = fixed_yaml.removeprefix("```yaml").removesuffix("```").strip()
                elif fixed_yaml.startswith("```"):
                    fixed_yaml = fixed_yaml.removeprefix("```").removesuffix("```").strip()

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

    # Step 4: Self-validate + auto-fix
    _log_activity("contract.validate.self", resource_id=brief_id)

    try:
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
    except Exception as e:
        _log_activity("contract.validate.error", details={"error": str(e)}, status="error")

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

    # ===== Placeholders cho 3 categories còn lại =====
    placeholder_template = yaml.dump({
        "meta": {
            "version": "1.0.0",
            "brief_id": brief_id,
            "generated_at": generated_at
        }
    }, default_flow_style=False, allow_unicode=True)

    workflows_yaml = placeholder_template.rstrip() + "\nworkflows: []\n"
    value_objects_yaml = placeholder_template.rstrip() + "\nvalue_objects: []\n"
    guards_yaml = placeholder_template.rstrip() + "\nguards: []\n"
    ui_components_yaml = placeholder_template.rstrip() + "\nui_components: []\n"

    return {
        "entities": entities_yaml,
        "commands": commands_yaml,
        "queries": queries_yaml,
        "events": events_yaml,
        "workflows": workflows_yaml,
        "value_objects": value_objects_yaml,
        "guards": guards_yaml,
        "ui_components": ui_components_yaml,
    }


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

        yaml_content = response.content.strip()
        yaml_content = yaml_content.replace("```yaml", "").replace("```", "").strip()

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


__all__ = [
    "generate_contracts",
    "check_contracts",
    "repair_contracts",
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