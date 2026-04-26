"""
Contract Commands Implementation.

Lệnh tạo và quản lý DSL contracts:
- contract gen: Generate DSL contracts từ brief analysis
- contract check: Validate contracts với DSL schema
- contract repair: Sửa contracts có lỗi bằng LLM

E03: Contract Commands
"""

import click
from pathlib import Path
import tempfile
import yaml
from datetime import datetime, timezone
from typing import Any, Dict, List

from midicoder.storage.sqlite import BriefsManager
from midicoder.dsl.loader import load_projection_tree
from midicoder.dsl.validator import validate_tree, ValidationStatus
from litellm import APIError
from midicoder.pipeline.llm.client import (
    LlmConfig,
    call_llm,
    load_llm_config,
)


def generate_contracts(force: bool = False):
    """
    Generate DSL contracts từ brief analysis.
    
    Process:
    1. Lấy active brief từ SQLite
    2. Sử dụng LLM để generate DSL contracts
    3. Lưu contracts vào .midicoder/contracts/
    4. Validate contracts
    
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
        # Get any brief
        active_brief = briefs[0]
        click.echo(f"ℹ️  Sử dụng brief: {active_brief.get('brief_id')}")
    
    click.echo(f"   → Brief ID: {active_brief.get('brief_id')}")
    click.echo(f"   → Title: {active_brief.get('title')}")
    
    # Step 2: Create contracts directory
    contracts_dir = Path(".midicoder/contracts")
    contracts_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if contracts already exist (cả .yml và .yaml)
    existing_files = list(contracts_dir.glob("*.yml")) + list(contracts_dir.glob("*.yaml"))
    if existing_files and not force:
        click.echo(f"⚠️  Contracts đã tồn tại ({len(existing_files)} files)")
        response = click.prompt("Ghi đè? (y/n)", default="n")
        if response.lower() != "y":
            click.echo("❌ Hủy bỏ.")
            return
    
    # Step 3: Generate contracts (placeholder - LLM integration coming)
    click.echo("🤖 Đang generate contracts bằng LLM...")
    click.echo("   ⚠️  LLM contract generation chưa được implement")
    click.echo("   💡 Sẽ integrate với MCP server và DSL schema")
    
    # Create placeholder contracts
    generate_placeholder_contracts(contracts_dir, active_brief.get('brief_id'))
    
    # Done
    click.echo("")
    click.echo("✅ Contracts generated!")
    click.echo("")
    click.echo("Tiếp theo:")
    click.echo("  1. Chạy: midicoder contract check (validate contracts)")
    click.echo("  2. Chạy: midicoder ir build (build MIR)")


def generate_placeholder_contracts(contracts_dir: Path, brief_id: str):
    """
    Tạo placeholder contracts cho testing theo DSL schema v1.
    
    Theo DSL loader (midicoder/dsl/loader.py), format đúng là:
    - entities.yaml: entities với id, description, fields, tags, tenant_scope
    - commands.yaml: commands với id, description, input, fetches, guards, effects, errors, returns, category, emits, required_roles, required_permissions, writes_to, datasource, transaction, tenant_scope
    - queries.yaml: queries với id, description, input, fetches, guards, returns, category, reads_from, required_roles, required_permissions, datasource, tenant_scope
    
    Args:
        contracts_dir: Đường dẫn đến contracts folder
        brief_id: Brief ID
    """
    generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    # Entities theo DSL schema v1
    # Theo loader.py: _load_entities expects "entities" key with list of entity dicts
    entities = {
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
    }
    
    # Commands theo DSL schema v1
    # Theo loader.py: _load_commands expects "commands" key with list of command dicts
    commands = {
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
    }
    
    # Queries theo DSL schema v1
    # Theo loader.py: _load_queries expects "queries" key with list of query dicts
    queries = {
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
    }
    
    # Events theo DSL schema v1
    events = {
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
    }
    
    # Write files theo DSL file naming convention (với UTF-8 encoding để hỗ trợ tiếng Việt)
    (contracts_dir / "entities.yaml").write_text(
        yaml.dump(entities, default_flow_style=False, allow_unicode=True),
        encoding="utf-8"
    )
    (contracts_dir / "commands.yaml").write_text(
        yaml.dump(commands, default_flow_style=False, allow_unicode=True),
        encoding="utf-8"
    )
    (contracts_dir / "queries.yaml").write_text(
        yaml.dump(queries, default_flow_style=False, allow_unicode=True),
        encoding="utf-8"
    )
    (contracts_dir / "events.yaml").write_text(
        yaml.dump(events, default_flow_style=False, allow_unicode=True),
        encoding="utf-8"
    )
    
    click.echo("   ✓ entities.yaml (3 entities)")
    click.echo("   ✓ commands.yaml (2 commands)")
    click.echo("   ✓ queries.yaml (3 queries)")
    click.echo("   ✓ events.yaml (2 events)")


def check_contracts(auto_fix: bool = False, strict: bool = False):
    """
    Validate contracts với DSL schema.
    
    Process:
    1. Load contracts from .midicoder/contracts/
    2. Load vào ProjectionTree bằng DSL loader
    3. Validate với DSL validator
    4. Report errors/warnings với actionable insights
    
    Args:
        auto_fix: Attempt to fix errors automatically (chưa implement)
        strict: Treat warnings as errors
    """
    click.echo("🔍 Đang kiểm tra contracts...")
    
    contracts_dir = Path(".midicoder/contracts")
    if not contracts_dir.exists():
        click.echo("❌ Contracts directory không tồn tại")
        click.echo("💡 Chạy 'midicoder contract gen' trước")
        return
    
    # Find contract files
    contract_files = list(contracts_dir.glob("*.yml"))
    if not contract_files:
        click.echo("❌ Không có contract files nào")
        return
    
    click.echo(f"   → Found {len(contract_files)} contract files")
    
    # Step 1: Basic YAML validation
    errors = []
    warnings = []
    
    for contract_file in contract_files:
        click.echo(f"   Checking: {contract_file.name}")
        
        try:
            content = yaml.safe_load(contract_file.read_text())
            
            # Basic validation
            if not isinstance(content, dict):
                errors.append(f"{contract_file.name}: Expected YAML dict")
                continue
            
            # Check for required 'meta' section
            if 'meta' not in content:
                warnings.append(f"{contract_file.name}: Missing 'meta' section")
            
            click.echo(f"      ✓ YAML syntax valid")
            
        except yaml.YAMLError as e:
            errors.append(f"{contract_file.name}: {e}")
        except Exception as e:
            errors.append(f"{contract_file.name}: {e}")
    
    # Nếu có YAML errors, report và return
    if errors:
        click.echo("")
        click.echo(f"❌ {len(errors)} YAML errors found:")
        for error in errors:
            click.echo(f"   - {error}")
        return
    
    # Step 2: Load into ProjectionTree
    click.echo("")
    click.echo("   → Loading into ProjectionTree...")
    
    try:
        tree = load_projection_tree(contracts_dir)
        click.echo(f"      ✓ Loaded {tree.node_count()} nodes")
    except Exception as e:
        click.echo(f"      ❌ Failed to load: {e}")
        return
    
    # Step 3: Validate với DSL validator
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
                for error in node_errors[:3]:  # Show first 3 errors
                    click.echo(f"       • {error.message}")
        
        # Report warnings
        if report.total_warnings > 0:
            click.echo("")
            click.echo("   Warnings:")
            for warning in report.get_warnings()[:5]:  # Show first 5 warnings
                click.echo(f"     • {warning.node_id}: {warning.message}")
        
        # Report dependency cycles if any
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
    
    has_errors = report.status == ValidationStatus.ERRORS
    has_warnings = report.status == ValidationStatus.WARNINGS
    
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
            click.echo("  1. Chạy: midicoder contract check --strict (kiểm tra nghiêm ngặt)")
            click.echo("  2. Hoặc: midicoder ir build (build MIR from contracts)")
    elif has_errors:
        click.echo("❌ Contracts có errors")
        
        # Nếu có --auto-fix, tự động gọi repair
        if auto_fix:
            click.echo("")
            click.echo("🔧 Tự động repair với LLM...")
            click.echo("")
            repair_contracts()
        else:
            click.echo("")
            click.echo("Tiếp theo:")
            click.echo("  1. Sửa errors thủ công hoặc chạy: midicoder contract repair")
            click.echo("  2. Hoặc: midicoder contract check --auto-fix (tự động sửa)")
    else:  # FATAL
        click.echo("❌ Fatal validation errors")
        click.echo("")
        click.echo("Tiếp theo:")
        click.echo("  1. Sửa errors nghiêm trọng hoặc chạy lại: midicoder contract gen")


# Số lần thử tối đa để LLM fix contracts
MAX_REPAIR_ATTEMPTS = 3


def _build_repair_prompt(
    contract_file: Path,
    content: dict,
    errors: list,
) -> tuple[str, str]:
    """
    Xây dựng prompt để LLM fix contracts.
    
    Args:
        contract_file: File contract cần sửa
        content: Nội dung YAML hiện tại
        errors: Danh sách validation errors
        
    Returns:
        Tuple của (system prompt, user prompt)
    """
    # System prompt - hướng dẫn LLM cách fix
    system = """You are a DSL contract repair expert. Your task is to fix validation errors in DSL contracts.
    
DSL Schema Rules:
1. Entity MUST have: id, description, fields, primary_key, tenant_scope, tags
2. Field MUST have: name, type, required
3. Command MUST have: id, description, input, fetches, guards, effects, returns, required_permissions, tenant_scope
4. Query MUST have: id, description, input, fetches, returns, required_permissions, tenant_scope
5. Event MUST have: id, description, type, source_entity, fields, version, tenant_scope
6. All strings support Vietnamese characters
7. Output ONLY valid YAML, no markdown formatting, no explanations

Fix Guidelines:
- Add missing required fields with sensible defaults
- Fix field type mismatches
- Ensure all references point to existing entities
- Preserve existing content, only fix errors
- Output complete fixed YAML content"""
    
    # User prompt - cung cấp context cụ thể
    error_messages = "\n".join(
        f"- {getattr(e, 'message', str(e))}" for e in errors
    )
    
    yaml_content = yaml.dump(content, default_flow_style=False, allow_unicode=True)
    
    user = f"""File: {contract_file.name}

Current YAML content:
{yaml_content}

Validation errors:
{error_messages}

Please fix the YAML to resolve all validation errors. Output ONLY the complete fixed YAML content, no markdown formatting."""
    
    return system, user


def _try_fix_with_llm(
    config: LlmConfig,
    contract_file: Path,
    content: dict,
    errors: list,
) -> tuple[bool, dict | None]:
    """
    Thử fix contracts bằng LLM.
    
    Args:
        config: LLM config
        contract_file: File contract cần sửa
        content: Nội dung YAML hiện tại
        errors: Danh sách validation errors
        
    Returns:
        Tuple của (success, fixed_content hoặc None)
    """
    try:
        # Build prompt
        system, user = _build_repair_prompt(contract_file, content, errors)
        
        # Call LLM
        response = call_llm(
            config,
            system=system,
            prompt=user,
            temperature=0.3,  # Low temperature cho deterministic output
            max_tokens=4096,
        )
        
        # Parse YAML từ response
        yaml_content = response.content.strip()
        
        # Remove markdown code blocks nếu có
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


def repair_contracts():
    """
    Sửa contracts có lỗi bằng LLM.
    
    Process:
    1. Load contracts từ .midicoder/contracts/
    2. Validate để tìm errors
    3. Nếu có errors → gọi LLM để fix từng file
    4. Re-validate để confirm fix thành công
    5. Retry tối đa MAX_REPAIR_ATTEMPTS lần
    """
    click.echo("🔧 Đang repair contracts bằng LLM...")
    
    contracts_dir = Path(".midicoder/contracts")
    if not contracts_dir.exists():
        click.echo("❌ Contracts directory không tồn tại")
        click.echo("💡 Chạy 'midicoder contract gen' trước")
        return
    
    # Tìm contract files (cả .yml và .yaml)
    contract_files = list(contracts_dir.glob("*.yml")) + list(contracts_dir.glob("*.yaml"))
    if not contract_files:
        click.echo("❌ Không có contract files nào")
        click.echo("💡 Chạy 'midicoder contract gen' trước")
        return
    
    click.echo(f"   → Found {len(contract_files)} contract files")
    
    # Load LLM config
    try:
        config = load_llm_config()
    except Exception as e:
        click.echo(f"❌ Không thể load LLM config: {e}")
        click.echo("💡 Kiểm tra ~/.midicoder/midicoder.json")
        return
    
    # Track files cần fix
    files_to_fix: list[tuple[Path, dict, list]] = []
    
    # Step 1: Validate từng file để tìm errors
    click.echo("")
    click.echo("   → Đang validate contracts...")
    
    for contract_file in contract_files:
        try:
            content = yaml.safe_load(contract_file.read_text(encoding="utf-8"))
            
            # Tạo temp tree chỉ từ file này để validate
            temp_dir = Path(tempfile.mkdtemp())
            temp_file = temp_dir / contract_file.name
            temp_file.write_text(
                yaml.dump(content, default_flow_style=False, allow_unicode=True),
                encoding="utf-8"
            )
            
            try:
                tree = load_projection_tree(temp_dir)
                report = validate_tree(tree)
                
                if report.total_errors > 0:
                    errors = []
                    for node_id, node_errors in report.get_errors_by_node().items():
                        errors.extend(node_errors)
                    files_to_fix.append((contract_file, content, errors))
                    click.echo(f"      ⚠️  {contract_file.name}: {report.total_errors} errors")
                else:
                    click.echo(f"      ✓ {contract_file.name}: valid")
            finally:
                # Cleanup temp dir
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
                
        except yaml.YAMLError as e:
            click.echo(f"      ❌ {contract_file.name}: YAML error - {e}")
            files_to_fix.append((contract_file, {}, [e]))
        except Exception as e:
            click.echo(f"      ❌ {contract_file.name}: {e}")
            files_to_fix.append((contract_file, {}, [e]))
    
    # Nếu không có file nào cần fix
    if not files_to_fix:
        click.echo("")
        click.echo("✅ Tất cả contracts đã valid, không cần repair!")
        return
    
    click.echo("")
    click.echo(f"   → Found {len(files_to_fix)} file(s) to repair")
    
    # Step 2: Repair từng file bằng LLM
    repaired_count = 0
    failed_files: list[str] = []
    
    for contract_file, content, errors in files_to_fix:
        click.echo(f"")
        click.echo(f"   → Repairing: {contract_file.name}")
        
        success = False
        fixed_content = None
        
        for attempt in range(1, MAX_REPAIR_ATTEMPTS + 1):
            if attempt > 1:
                click.echo(f"      → Retry attempt {attempt}/{MAX_REPAIR_ATTEMPTS}")
            
            # Try fix với LLM
            result, fixed = _try_fix_with_llm(config, contract_file, content, errors)
            
            if not result or fixed is None:
                continue
            
            fixed_content = fixed
            
            # Validate fix bằng cách write temp và re-validate
            temp_dir = Path(tempfile.mkdtemp())
            temp_file = temp_dir / contract_file.name
            
            try:
                temp_file.write_text(
                    yaml.dump(fixed_content, default_flow_style=False, allow_unicode=True),
                    encoding="utf-8"
                )
                
                tree = load_projection_tree(temp_dir)
                report = validate_tree(tree)
                
                if report.total_errors == 0:
                    success = True
                    click.echo(f"      ✓ Fixed after {attempt} attempt(s)")
                    break
                else:
                    # Update errors cho next retry
                    errors = []
                    for node_id, node_errors in report.get_errors_by_node().items():
                        errors.extend(node_errors)
                    click.echo(f"      ⚠️  Still {report.total_errors} errors, retrying...")
                    
            except Exception as e:
                click.echo(f"      ⚠️  Validation error: {e}")
            finally:
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
        
        if success and fixed_content is not None:
            # Write fixed content to file
            try:
                contract_file.write_text(
                    yaml.dump(fixed_content, default_flow_style=False, allow_unicode=True),
                    encoding="utf-8"
                )
                repaired_count += 1
            except Exception as e:
                click.echo(f"      ❌ Failed to write: {e}")
                failed_files.append(contract_file.name)
        else:
            click.echo(f"      ❌ Failed to repair after {MAX_REPAIR_ATTEMPTS} attempts")
            failed_files.append(contract_file.name)
    
    # Final report
    click.echo("")
    
    if repaired_count > 0:
        click.echo(f"✅ Repaired {repaired_count} file(s)")
    
    if failed_files:
        click.echo(f"")
        click.echo(f"⚠️  Failed to repair {len(failed_files)} file(s):")
        for name in failed_files:
            click.echo(f"    - {name}")
        click.echo("💡 Vui lòng sửa thủ công hoặc chạy lại 'midicoder contract repair'")
    else:
        click.echo("")
        click.echo("Tiếp theo:")
        click.echo("  1. Chạy: midicoder contract check (verify repairs)")
        click.echo("  2. Chạy: midicoder ir build (build MIR)")
