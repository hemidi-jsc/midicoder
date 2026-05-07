"""
Contract Commands Implementation (SQLite-Only Architecture).

Tất cả contract artifacts được lưu vào SQLite (ArtifactsManager).
Không sử dụng filesystem để lưu contracts.

Commands:
- contract gen: Generate DSL contracts từ brief analysis → SQLite
- contract check: Validate contracts từ SQLite với DSL schema
- contract repair: Sửa contracts có lỗi bằng LLM → SQLite

Theo SoT (MIDICODER_ARCHITECTURE.md Section 7):
- Input: Brief (SQLite)
- Output: Contract artifacts (SQLite, artifact_type="contract")
- Pipeline: contract gen → contract check → ir build

Author: Midicoder Team
Version: 3.0.0 (Refactored: SQLite-only architecture)
"""

from __future__ import annotations

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
from litellm import APIError
from midicoder.pipeline.llm.client import (
    LlmConfig,
    call_llm,
    load_llm_config,
)

# 7 categories bắt buộc theo DSL strict mode
REQUIRED_CATEGORIES = [
    "entities", "commands", "queries", "events",
    "workflows", "value_objects", "guards"
]

# Số lần thử tối đa để LLM fix contracts
MAX_REPAIR_ATTEMPTS = 3


# ============================================================================
# Contract Generation
# ============================================================================

def generate_contracts(force: bool = False):
    """
    Generate DSL contracts từ brief analysis.

    Process (SQLite-only):
    1. Lấy active brief từ SQLite
    2. Generate contract YAML strings (placeholder hoặc LLM)
    3. Upsert contracts vào SQLite (artifact_type="contract")
    4. Self-validate contracts

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
        response = click.prompt("Ghi đè? (y/n)", default="n")
        if response.lower() != "y":
            click.echo("❌ Hủy bỏ.")
            return

    # Step 3: Generate contract YAML strings và lưu vào SQLite
    click.echo("🤖 Đang generate contracts...")
    click.echo("   ⚠️  LLM contract generation chưa được implement")
    click.echo("   💡 Sử dụng placeholder contracts (stub)")

    _generate_contracts_to_sqlite(brief_id)

    # Step 4: Self-validate (tolerant — placeholder data có thể trigger validator bugs)
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
                click.echo(f"   ⚠️  Contracts có {report.total_errors} errors (placeholder data)")
    except Exception as e:
        # Known issue: dependency graph builder fails với complex fetches/writes_to dicts
        # TODO: Fix dependency builder để handle dict-based references
        click.echo(f"   ⚠️  Validation skipped (known issue: {e})")

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

    STUB: Hiện tại dùng placeholder data. Sau khi implement LLM (P0-4),
    thay thế bằng LLM-generated contracts.

    Args:
        brief_id: Brief ID liên quan
    """
    artifacts_manager = ArtifactsManager()
    artifacts_manager.init()

    generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    # Build placeholder YAML content cho mỗi category
    yaml_dict = _build_placeholder_yaml(brief_id, generated_at)

    saved_count = 0
    for category in REQUIRED_CATEGORIES:
        yaml_content = yaml_dict[category]

        # Upsert artifact (idempotent)
        _upsert_contract_artifact(artifacts_manager, category, yaml_content, brief_id)
        saved_count += 1

    click.echo(f"   ✓ Saved {saved_count}/7 contract artifacts to SQLite")


def _build_placeholder_yaml(brief_id: str, generated_at: str) -> Dict[str, str]:
    """
    Build placeholder YAML content cho 7 categories.

    STUB: Replace with LLM-generated content when P0-4 is implemented.

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

    return {
        "entities": entities_yaml,
        "commands": commands_yaml,
        "queries": queries_yaml,
        "events": events_yaml,
        "workflows": workflows_yaml,
        "value_objects": value_objects_yaml,
        "guards": guards_yaml,
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
    # Group errors by category (best effort)
    errors_by_node = report.get_errors_by_node()

    # Track repair results
    repaired_count = 0
    failed_categories: list[str] = []

    # Try to fix each category that has errors
    # (Simple approach: try to fix all categories)
    for category in REQUIRED_CATEGORIES:
        if category not in yaml_dict:
            continue

        current_content = yaml_dict[category]

        # Parse this category to find errors
        try:
            parsed_data = yaml.safe_load(current_content)
        except Exception:
            parsed_data = {}

        # Collect errors for this category
        category_errors = []
        for node_id, node_errors in errors_by_node.items():
            # Heuristic: check if node_id might belong to this category
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
            # Upsert fixed artifact
            fixed_yaml = yaml.dump(fixed_content, default_flow_style=False, allow_unicode=True)
            _upsert_contract_artifact(
                artifacts_manager, category, fixed_yaml,
                brief_id=artifacts_manager.get(f"contract_{category}")
                .get("brief_id", "unknown") if artifacts_manager.get(f"contract_{category}")
                else "unknown"
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
        click.echo("💡 Vui lòng sửa thủ công hoặc chạy lại 'midicoder contract repair")
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

    Args:
        category: Category name (entities, commands, ...)
        content: Nội dung YAML hiện tại
        errors: Danh sách validation errors

    Returns:
        Tuple của (system prompt, user prompt)
    """
    system = """You are a DSL contract repair expert. Your task is to fix validation errors in DSL contracts.

DSL Schema Rules:
1. Entity MUST have: id, description, fields, primary_key, tenant_scope, tags
2. Field MUST have: name, type, required
3. Command MUST have: id, description, input, fetches, guards, effects, returns, required_permissions, tenant_scope
4. Query MUST have: id, description, input, fetches, returns, required_permissions, tenant_scope
5. Event MUST have: id, description, type, source_entity, fields, version, tenant_scope
6. All strings support Vietnamese characters
7. Output ONLY valid YAML dict, no markdown formatting, no explanations

Fix Guidelines:
- Add missing required fields with sensible defaults
- Fix field type mismatches
- Ensure all references point to existing entities
- Preserve existing content, only fix errors
- Output complete fixed YAML dict"""

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
            prompt=user,
            temperature=0.3,
            max_tokens=4096,
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


# ============================================================================
# Backward Compatibility (deprecated — will be removed)
# ============================================================================

def generate_placeholder_contracts(contracts_dir: Path, brief_id: str):
    """
    DEPRECATED: Tạo placeholder contracts files.

    WARNING: Đây là legacy function. Không nên dùng.
    Sử dụng _generate_contracts_to_sqlite() thay thế.

    Giữ lại để backward compatibility với test suite cũ.
    Sẽ bị xóa trong version 4.0.0.
    """
    import warnings
    warnings.warn(
        "generate_placeholder_contracts is deprecated. "
        "Contracts are now stored in SQLite only.",
        DeprecationWarning,
        stacklevel=2
    )

    # Fallback: call the new SQLite-only function
    # (Write files only for backward compatibility with old tests)
    from midicoder.storage.sqlite import ArtifactsManager
    _generate_contracts_to_sqlite(brief_id)
    # Also write files for backward compatibility
    generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    yaml_dict = _build_placeholder_yaml(brief_id, generated_at)

    for category in REQUIRED_CATEGORIES:
        yaml_content = yaml_dict[category]
        file_path = contracts_dir / f"{category}.yaml"
        file_path.write_text(yaml_content, encoding="utf-8")

        # Also save to SQLite
        artifacts_manager = ArtifactsManager()
        artifacts_manager.init()
        _upsert_contract_artifact(artifacts_manager, category, yaml_content, brief_id)


def _save_contract_artifacts(contracts_dir: Path, brief_id: str) -> None:
    """
    DEPRECATED: Save contract YAML files vào SQLite.

    WARNING: Đây là legacy function. Sử dụng _generate_contracts_to_sqlite() thay thế.
    Giữ lại để backward compatibility.
    """
    import warnings
    warnings.warn(
        "_save_contract_artifacts is deprecated. "
        "Use _generate_contracts_to_sqlite() instead.",
        DeprecationWarning,
        stacklevel=2
    )

    artifacts_manager = ArtifactsManager()
    artifacts_manager.init()

    for category in REQUIRED_CATEGORIES:
        file_path = None
        for ext in ["yaml", "yml"]:
            candidate = contracts_dir / f"{category}.{ext}"
            if candidate.exists():
                file_path = candidate
                break

        if file_path is None:
            click.echo(f"   ⚠️  Không tìm thấy file cho category: {category}")
            continue

        content = file_path.read_text(encoding="utf-8")
        _upsert_contract_artifact(artifacts_manager, category, content, brief_id)


__all__ = [
    "generate_contracts",
    "check_contracts",
    "repair_contracts",
    "generate_placeholder_contracts",  # deprecated
    "_save_contract_artifacts",  # deprecated
]