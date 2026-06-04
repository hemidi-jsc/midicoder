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
import click
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from midicoder.errors import MidicoderErrorManager as EM, ErrorCode
from midicoder.storage.sqlite import BriefsManager, ArtifactsManager
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
            click.echo(f"      ⚠️  {category}: LLM output not valid YAML (attempt {attempt}/{max_retries}), retrying...")
            if attempt >= max_retries:
                raise RuntimeError(f"Failed to generate valid YAML for {category} after {max_retries} attempts")
            continue
        except Exception as e:
            # Loại lỗi khác (API error, ...) → retry
            click.echo(f"      ⚠️  {category}: LLM error (attempt {attempt}/{max_retries}): {e}, retrying...")
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
        click.echo(f"   → Generating {category}...")

        system, user = _build_category_prompt(
            category, analysis_data, clarifications, brief_content
        )

        yaml_content = _generate_category_with_retry(
            config, category, system, user
        )

        result[category] = yaml_content
        click.echo(f"      ✓ {category} generated")

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
        click.echo("")
        click.echo(f"   → Auto-fix iteration {iteration}/{MAX_REPAIR_ATTEMPTS}")

        # Build ProjectionTree và validate
        try:
            tree = dsl_parser.build_projection_tree(yaml_dict)
            report = validate_tree(tree)
        except Exception as e:
            click.echo(f"      ⚠️  Validation error: {e}")
            break

        if report.total_errors == 0:
            click.echo(f"      ✓ Contracts valid sau {iteration} iteration(s)")
            return True

        click.echo(f"      → Vẫn có {report.total_errors} errors, fix...")

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
                click.echo(f"      ✓ Fixed {category}")

            except Exception as e:
                click.echo(f"      ⚠️  Failed to fix {category}: {e}")

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
    click.echo("📝 Đang generate DSL contracts...")

    # Step 1: Check if brief exists
    briefs_manager = BriefsManager()
    briefs = briefs_manager.list()

    if not briefs:
        click.echo("❌ Không có brief nào được phân tích")
        click.echo("💡 Chạy 'midicoder brief analyze' trước")
        return

    # Get latest analyzed brief
    active_brief = None
    for brief in briefs:
        if brief.get('status') == 'analyzed':
            active_brief = brief
            break

    if not active_brief:
        active_brief = briefs[0]
        click.echo(f"ℹ️  Sử dụng brief: {active_brief.get('brief_id')}")

    brief_id = active_brief.get('brief_id')
    click.echo(f"   → Brief ID: {brief_id}")
    click.echo(f"   → Title: {active_brief.get('title')}")

    # Step 2: Check if contracts already exist
    artifacts_manager = ArtifactsManager()
    artifacts_manager.init()
    existing = artifacts_manager.list_by_type("contract")

    if existing and not force:
        click.echo(f"⚠️  Contracts đã tồn tại ({len(existing)} artifacts)")
        click.echo("   → Không ghi đè (dùng --force để ghi đè)")
        return

    # Step 3: Delegate đến _generate_contracts_to_sqlite (có placeholder fallback)
    click.echo("")
    click.echo("   → Đang generate contracts...")
    _generate_contracts_to_sqlite(brief_id)

    # Step 4: Self-validate + auto-fix
    click.echo("")
    click.echo("   → Self-validating contracts...")

    try:
        tree = _load_contracts_from_sqlite()
        if tree is not None:
            report = validate_tree(tree)
            if report.status == ValidationStatus.VALID:
                click.echo("   ✓ Contracts valid")
            elif report.status == ValidationStatus.WARNINGS:
                click.echo(f"   ⚠️  Contracts valid với {report.total_warnings} warnings")
            else:
                click.echo(f"   → Contracts có {report.total_errors} errors")
    except Exception as e:
        click.echo(f"   ⚠️  Validation error: {e}")

    # Done
    click.echo("")
    click.echo("✅ Contracts generated!")
    click.echo("")
    click.echo("Tiếp theo:")
    click.echo("  1. Chạy: midicoder contract check (validate contracts)")
    click.echo("  2. Chạy: midicoder ir build (build MIR)")


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

    click.echo(f"   ✓ Saved {saved_count}/7 contract artifacts to SQLite")


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
    click.echo("🔍 Đang kiểm tra contracts...")

    # Step 1: Load contract artifacts từ SQLite
    artifacts_manager = ArtifactsManager()
    artifacts_manager.init()

    contracts = artifacts_manager.list_by_type("contract")
    if not contracts:
        click.echo("❌ Không có contract artifacts nào")
        click.echo("💡 Chạy 'midicoder contract gen' trước")
        return

    click.echo(f"   → Found {len(contracts)} contract artifacts")

    # Step 2: Build yaml_dict từ artifacts
    yaml_dict = {}
    for artifact in contracts:
        artifact_id = artifact.get("artifact_id", "")
        if artifact_id.startswith("contract_"):
            category = artifact_id[len("contract_"):]
            yaml_content = artifact.get("content", "")
            yaml_dict[category] = yaml_content
            click.echo(f"   → Loaded: {category}")

    # Check missing categories
    missing = set(REQUIRED_CATEGORIES) - set(yaml_dict.keys())
    if missing:
        click.echo(f"   ⚠️  Thiếu categories: {', '.join(sorted(missing))}")

    # Step 3: Parse YAML strings → ProjectionTree
    click.echo("")
    click.echo("   → Loading vào ProjectionTree...")

    try:
        dsl_parser = DSLParser()
        tree = dsl_parser.build_projection_tree(yaml_dict)
        click.echo(f"      ✓ Loaded {tree.node_count()} nodes")
    except Exception as e:
        click.echo(f"      ❌ Failed to parse: {e}")
        return

    # Step 4: Validate với DSL validator
    click.echo("")
    click.echo("   → Running DSL validation...")

    try:
        report = validate_tree(tree)

        click.echo(f"      ✓ Validation complete")
        click.echo(f"        - Errors: {report.total_errors}")
        click.echo(f"        - Warnings: {report.total_warnings}")
        click.echo(f"        - Info: {report.total_info}")

        # Report errors by node
        if report.total_errors > 0:
            click.echo("")
            click.echo("   Errors by node:")
            errors_by_node = report.get_errors_by_node()
            for node_id, node_errors in errors_by_node.items():
                click.echo(f"     - {node_id}: {len(node_errors)} errors")
                for error in node_errors[:3]:
                    click.echo(f"       • {error.message}")

        # Report warnings
        if report.total_warnings > 0:
            click.echo("")
            click.echo("   Warnings:")
            for warning in report.get_warnings()[:5]:
                click.echo(f"     • {warning.node_id}: {warning.message}")

        # Report dependency cycles
        if report.dependency_analysis and report.dependency_analysis.cycles:
            click.echo("")
            click.echo("   Dependency cycles detected:")
            for cycle in report.dependency_analysis.cycles[:3]:
                cycle_str = " → ".join(cycle.nodes)
                click.echo(f"     • {cycle_str}")

    except Exception as e:
        click.echo(f"      ❌ Validation failed: {e}")
        return

    # Final report
    click.echo("")

    if report.status == ValidationStatus.VALID:
        click.echo("✅ Contracts validation passed!")
        click.echo("")
        click.echo("Tiếp theo:")
        click.echo("  1. Chạy: midicoder ir build (build MIR from contracts)")
    elif report.status == ValidationStatus.WARNINGS:
        if strict:
            click.echo("⚠️  Warnings found (strict mode = error)")
            click.echo("")
            click.echo("Tiếp theo:")
            click.echo("  1. Sửa warnings hoặc chạy: midicoder contract check --auto-fix")
        else:
            click.echo("⚠️  Contracts valid with warnings")
            click.echo("")
            click.echo("Tiếp theo:")
            click.echo("  1. Chạy: midicoder contract check --strict")
            click.echo("  2. Hoặc: midicoder ir build")
    elif report.status == ValidationStatus.ERRORS:
        click.echo("❌ Contracts có errors")

        if auto_fix:
            click.echo("")
            click.echo("🔧 Tự động repair với LLM...")
            click.echo("")
            repair_contracts()
        else:
            click.echo("")
            click.echo("Tiếp theo:")
            click.echo("  1. Sửa errors thủ công hoặc chạy: midicoder contract repair")
            click.echo("  2. Hoặc: midicoder contract check --auto-fix")
    else:  # FATAL
        click.echo("❌ Fatal validation errors")
        click.echo("")
        click.echo("Tiếp theo:")
        click.echo("  1. Sửa errors nghiêm trọng hoặc chạy lại: midicoder contract gen")


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
    click.echo("🔧 Đang repair contracts bằng LLM...")

    # Step 1: Load contracts từ SQLite
    artifacts_manager = ArtifactsManager()
    artifacts_manager.init()

    contracts = artifacts_manager.list_by_type("contract")
    if not contracts:
        click.echo("❌ Không có contract artifacts nào")
        click.echo("💡 Chạy 'midicoder contract gen' trước")
        return

    click.echo(f"   → Found {len(contracts)} contract artifacts")

    # Load LLM config
    try:
        config = load_llm_config()
    except Exception as e:
        click.echo(f"❌ Không thể load LLM config: {e}")
        click.echo("💡 Kiểm tra ~/.midicoder/midicoder.json")
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
    click.echo("")
    click.echo("   → Đang validate contracts...")

    dsl_parser = DSLParser()
    tree = dsl_parser.build_projection_tree(yaml_dict)
    report = validate_tree(tree)

    if report.total_errors == 0:
        click.echo("✅ Tất cả contracts đã valid, không cần repair!")
        return

    click.echo(f"   → Found {report.total_errors} errors")

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
            click.echo(f"      ✓ {category}: no errors")
            continue

        click.echo(f"")
        click.echo(f"   → Repairing: {category}")

        success = False
        fixed_content = None

        for attempt in range(1, MAX_REPAIR_ATTEMPTS + 1):
            if attempt > 1:
                click.echo(f"      → Retry attempt {attempt}/{MAX_REPAIR_ATTEMPTS}")

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
                    click.echo(f"      ✓ Fixed after {attempt} attempt(s)")
                    break
                else:
                    category_errors = []
                    for node_id, node_errors in temp_report.get_errors_by_node().items():
                        category_errors.extend(node_errors)
                    click.echo(f"      ⚠️  Still {temp_report.total_errors} errors, retrying...")
            except Exception as e:
                click.echo(f"      ⚠️  Validation error: {e}")

        if success and fixed_content is not None:
            fixed_yaml = yaml.dump(fixed_content, default_flow_style=False, allow_unicode=True)
            existing_artifact = artifacts_manager.get(f"contract_{category}")
            brief_id = existing_artifact.get("brief_id", "unknown") if existing_artifact else "unknown"
            _upsert_contract_artifact(
                artifacts_manager, category, fixed_yaml, brief_id
            )
            repaired_count += 1
        else:
            click.echo(f"      ❌ Failed to repair after {MAX_REPAIR_ATTEMPTS} attempts")
            failed_categories.append(category)

    # Final report
    click.echo("")

    if repaired_count > 0:
        click.echo(f"✅ Repaired {repaired_count} category(s)")

    if failed_categories:
        click.echo(f"")
        click.echo(f"⚠️  Failed to repair {len(failed_categories)} category(s):")
        for name in failed_categories:
            click.echo(f"    - {name}")
        click.echo("💡 Vui lòng sửa thủ công hoặc chạy lại 'midicoder contract repair'")
    else:
        click.echo("")
        click.echo("Tiếp theo:")
        click.echo("  1. Chạy: midicoder contract check (verify repairs)")
        click.echo("  2. Chạy: midicoder ir build (build MIR)")


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
            click.echo(f"      ⚠️  LLM output không phải dict")
            return False, None

        return True, fixed_content

    except APIError as e:
        click.echo(f"      ❌ LLM error: {e}")
        return False, None
    except yaml.YAMLError as e:
        click.echo(f"      ❌ LLM output không phải valid YAML: {e}")
        return False, None
    except Exception as e:
        click.echo(f"      ❌ Error processing LLM response: {e}")
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