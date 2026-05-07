"""
IR Build Command Implementation.

Lệnh build MIR (Midicoder Intermediate Representation) từ Contract Artifacts:
- ir build: Build MIR từ contract artifacts trong SQLite

Theo SoT E04/E05:
- Input: Contract artifacts (YAML strings) từ artifacts table (SQLite)
- Process: DSLParser → ProjectionTree → MIR với typed IR
- Output: MIR JSON content lưu vào artifacts table

E04: IR Build Command
E05: MIR Typed IR

Author: Midicoder Team
Version: 2.0.0 (Refactored: contract artifacts input)
"""

from __future__ import annotations

import click
from pathlib import Path
from typing import Any

from midicoder.errors import MidicoderErrorManager as EM, ErrorCode
from midicoder.storage.sqlite import ArtifactsManager
from midicoder.pipeline.mir import (
    MIR, Operation, DataFlow, EffectFlow, Boundary, MIRBuilder
)
from midicoder.dsl.projection import ProjectionNode, ProjectionTree, NodeKind
from midicoder.dsl.validator import Validator
from midicoder.pipeline.dsl_parser import DSLParser


# Các category contract bắt buộc
_REQUIRED_CATEGORIES = {
    "entities", "commands", "queries", "events",
    "workflows", "value_objects", "guards"
}


def build_mir(verbose: bool = False) -> MIR:
    """
    Build MIR từ contract artifacts trong SQLite.

    Process:
    1. Query contract artifacts từ artifacts table (type="contract")
    2. Validate tất cả 7 categories present (strict mode)
    3. Parse YAML strings → ProjectionTree (qua DSLParser)
    4. Validate ProjectionTree
    5. Build MIR từ ProjectionTree
    6. Save MIR JSON vào artifacts table

    Args:
        verbose: Verbose output

    Returns:
        MIR instance

    Raises:
        MidicoderError: Nếu thiếu contracts, parse fail, validation fail, hoặc save fail
    """
    click.echo("🏗️  Đang build MIR từ contract artifacts...")

    # Bước 1: Load contract artifacts từ SQLite
    artifacts_manager = ArtifactsManager()
    artifacts_manager.init()

    # Tìm tất cả contract artifacts
    contracts = artifacts_manager.list_by_type("contract")
    if not contracts:
        click.echo("❌ Không tìm thấy contract artifacts trong artifacts")
        click.echo("💡 Chạy 'midicoder contract gen' trước")
        EM.raise_error(ErrorCode.MIR_GRAPH_NOT_FOUND)

    click.echo(f"   → Found {len(contracts)} contract artifacts")

    # Bước 2: Phân loại contracts theo category
    # artifact_id naming convention: "contract_<category>" (ví dụ: "contract_entities")
    yaml_dict = {}
    for artifact in contracts:
        artifact_id = artifact.get("artifact_id", "")
        # Trích xuất category từ artifact_id (format: "contract_<category>")
        if artifact_id.startswith("contract_"):
            category = artifact_id[len("contract_"):]
            if category in _REQUIRED_CATEGORIES:
                yaml_content = artifact.get("content", "")
                yaml_dict[category] = yaml_content
                click.echo(f"   → Loaded contract: {category}")

    # Bước 3: Validate tất cả categories present (strict mode)
    missing_categories = _REQUIRED_CATEGORIES - set(yaml_dict.keys())
    if missing_categories:
        click.echo(f"❌ Thiếu contract categories: {', '.join(sorted(missing_categories))}")
        click.echo("💡 Đảm bảo tất cả 7 categories đều được tạo bởi 'contract gen'")
        EM.raise_error(
            ErrorCode.MIR_DSL_PARSE_FAILED,
            missing_categories=sorted(missing_categories)
        )

    click.echo(f"   ✓ Tất cả {len(_REQUIRED_CATEGORIES)} categories present")

    # Bước 4: Parse YAML strings → ProjectionTree
    dsl_parser = DSLParser()
    projection_tree = dsl_parser.build_projection_tree(yaml_dict)
    click.echo(f"   → ProjectionTree: {projection_tree.node_count()} nodes")

    # Bước 5: Validate ProjectionTree
    validator = Validator()
    validation_result = validator.validate(projection_tree)
    if validation_result.errors:
        click.echo("❌ Validation errors:")
        for error in validation_result.errors:
            click.echo(f"   - {error}")
        EM.raise_error(ErrorCode.MIR_VALIDATION_FAILED, errors=len(validation_result.errors))

    click.echo(f"   ✓ Validation passed ({len(validation_result.warnings)} warnings)")

    # Bước 6: Build MIR từ ProjectionTree
    mir = _build_mir_from_projection_tree(projection_tree)
    click.echo(f"   → MIR: {len(mir.operations)} operations, "
               f"{len(mir.data_flows)} data flows, "
               f"{len(mir.effect_flows)} effect flows, "
               f"{len(mir.boundaries)} boundaries")

    # Bước 7: Save MIR vào SQLite
    mir_json = mir.to_json()
    mir_hash = mir.compute_hash()

    try:
        artifacts_manager.create(
            artifact_id="mir-v1.0.0",
            artifact_type="mir",
            name="MIR (Midicoder Intermediate Representation)",
            version="v1.0.0",
            content=mir_json,
            metadata={
                "hash": mir_hash,
                "operation_count": len(mir.operations),
                "data_flow_count": len(mir.data_flows),
                "effect_flow_count": len(mir.effect_flows),
                "boundary_count": len(mir.boundaries),
            }
        )
        click.echo(f"   ✓ MIR saved to artifacts (hash: {mir_hash[:16]}...)")
    except Exception as e:
        EM.raise_error(
            ErrorCode.MIR_SAVE_FAILED,
            error=str(e)
        )

    click.echo("")
    click.echo("✅ MIR build hoàn tất!")
    click.echo("")
    click.echo("Tiếp theo:")
    click.echo("  1. Chạy: midicoder code plan (create implementation plan)")
    click.echo("  2. Chạy: midicoder code gen (generate code)")

    return mir


def _build_mir_from_projection_tree(tree: ProjectionTree) -> MIR:
    """
    Build MIR từ ProjectionTree.

    Transform DSL nodes sang typed MIR structure:
    - Commands → Operations (authorize, create, update, delete)
    - Queries → Operations (query, read)
    - Events → EffectFlows
    - Guards → Operations (validation, auth)
    - Roles/Permissions → Boundaries (auth)
    - Transactions → Boundaries (transaction)

    Args:
        tree: ProjectionTree từ DSL

    Returns:
        MIR instance
    """
    builder = MIRBuilder().with_version("1.0.0").with_source("DSL ProjectionTree")

    # Lưu entities vào metadata cho emitter sử dụng
    _store_entities_in_metadata(builder, tree)
    _store_commands_in_metadata(builder, tree)
    _store_queries_in_metadata(builder, tree)

    # Process Commands → Operations
    for command in tree.get_commands():
        _process_command_to_mir(builder, command)

    # Process Queries → Operations
    for query in tree.get_queries():
        _process_query_to_mir(builder, query)

    # Process Events → EffectFlows
    for event in tree.get_events():
        _process_event_to_mir(builder, event)

    # Process Guards → Operations
    for guard in tree.get_guards():
        _process_guard_to_mir(builder, guard)

    # Process Roles → Boundaries
    for role in tree.get_nodes_by_kind(NodeKind.ROLE):
        _process_role_to_mir(builder, role)

    # Process Workflows → Boundaries (transaction)
    for workflow in tree.get_workflows():
        _process_workflow_to_mir(builder, workflow)

    # Auto-generate IAC operations nếu có backend services (commands/queries)
    # Theo CP07: luôn generate cả 2 IAC ops (docker cho local dev, terraform cho AWS prod)
    has_backend = (len(tree.get_commands()) > 0 or len(tree.get_queries()) > 0)
    if has_backend:
        _auto_generate_iac_ops(builder)

    return builder.build()


def _auto_generate_iac_ops(builder: MIRBuilder) -> None:
    """
    Tự động generate IAC operations cho backend services.

    Theo CP07 spec, khi có backend services (commands/queries),
    luôn generate cả 2 IAC ops:
    - emit_iac_docker: Docker Compose cho local development
    - emit_iac_aws: Terraform cho AWS production

    Args:
        builder: MIRBuilder
    """
    # Docker Compose cho local dev
    builder.add_operation(
        op_id="iac_docker_001",
        op_type="emit_iac_docker",
        params={
            "target": "docker-compose.yml",
            "services": ["backend", "postgres", "redis", "neo4j"]
        }
    )

    # Terraform cho AWS prod
    builder.add_operation(
        op_id="iac_aws_001",
        op_type="emit_iac_aws",
        params={
            "target": "terraform/",
            "services": ["ecs", "rds", "elasticache", "neo4j_aura", "s3"]
        }
    )

    # Lưu metadata để emitters sử dụng
    builder.mir.metadata["iac"] = {
        "auto_generated": True,
        "docker_target": "docker-compose.yml",
        "aws_target": "terraform/"
    }


def _process_command_to_mir(builder: MIRBuilder, command: ProjectionNode) -> None:
    """
    Transform Command node sang MIR operations.

    Args:
        builder: MIRBuilder
        command: Command ProjectionNode
    """
    params = command.params
    cmd_id = params.get("id", command.id)

    # Authorization operation
    required_perms = params.get("required_permissions", [])
    if required_perms:
        builder.add_operation(
            op_id=f"{cmd_id}_auth",
            op_type="authorize_permission",
            params={"permissions": required_perms},
            obligation_refs=[f"perm_oblig_{cmd_id}"]
        )

    # Tenant scope operation
    tenant_scope = params.get("tenant_scope", "global")
    if tenant_scope != "global":
        builder.add_operation(
            op_id=f"{cmd_id}_tenant",
            op_type="enforce_tenant_scope",
            params={"scope": tenant_scope},
            obligation_refs=[f"tenant_oblig_{cmd_id}"]
        )
        # Data flow from auth to tenant
        builder.add_data_flow(
            source_op=f"{cmd_id}_auth",
            source_field="tenant_id",
            target_op=f"{cmd_id}_tenant",
            target_field="tenant_id"
        )

    # Transaction boundary nếu có
    transaction = params.get("transaction", False)
    if transaction:
        builder.add_boundary(
            boundary_id=f"txn_{cmd_id}",
            boundary_type="transaction",
            enclosing_ops=[f"{cmd_id}_main"],
            config={"isolation_level": "read_committed"}
        )

    # Main operation (create/update/delete)
    category = params.get("category", "custom")
    op_type_map = {
        "create": "create_record",
        "update": "update_record",
        "delete": "delete_record",
        "custom": "execute_command"
    }
    main_op_type = op_type_map.get(category, "execute_command")

    builder.add_operation(
        op_id=f"{cmd_id}_main",
        op_type=main_op_type,
        params={
            "entity": params.get("writes_to", [])[0] if params.get("writes_to") else cmd_id,
            "command_id": cmd_id
        },
        input_refs=[f"{cmd_id}_input"]
    )

    # Event publish effects
    emits = params.get("emits", [])
    for event_id in emits:
        builder.add_effect_flow(
            source_op=f"{cmd_id}_main",
            effect_type="event_publish",
            target=event_id,
            payload_fields=["id", "timestamp"]
        )


def _process_query_to_mir(builder: MIRBuilder, query: ProjectionNode) -> None:
    """
    Transform Query node sang MIR operations.

    Args:
        builder: MIRBuilder
        query: Query ProjectionNode
    """
    params = query.params
    query_id = params.get("id", query.id)

    # Authorization
    required_perms = params.get("required_permissions", [])
    if required_perms:
        builder.add_operation(
            op_id=f"{query_id}_auth",
            op_type="authorize_permission",
            params={"permissions": required_perms}
        )

    # Tenant scope
    tenant_scope = params.get("tenant_scope", "global")
    if tenant_scope != "global":
        builder.add_operation(
            op_id=f"{query_id}_tenant",
            op_type="enforce_tenant_scope",
            params={"scope": tenant_scope}
        )

    # Query operation
    builder.add_operation(
        op_id=f"{query_id}_main",
        op_type="query_records",
        params={
            "entity": params.get("reads_from", [])[0] if params.get("reads_from") else query_id,
            "query_id": query_id,
            "category": params.get("category", "list")
        }
    )


def _process_event_to_mir(builder: MIRBuilder, event: ProjectionNode) -> None:
    """
    Transform Event node sang MIR effect flow definition.

    Args:
        builder: MIRBuilder
        event: Event ProjectionNode
    """
    params = event.params
    event_id = params.get("id", event.id)

    # Event metadata
    builder.mir.metadata.setdefault("events", {})
    builder.mir.metadata["events"][event_id] = {
        "type": params.get("type", "domain_event"),
        "fields": params.get("fields", []),
        "tenant_scope": params.get("tenant_scope", "global")
    }


def _process_guard_to_mir(builder: MIRBuilder, guard: ProjectionNode) -> None:
    """
    Transform Guard node sang MIR validation operation.

    Args:
        builder: MIRBuilder
        guard: Guard ProjectionNode
    """
    params = guard.params
    guard_id = params.get("id", guard.id)
    guard_type = params.get("type", "validation")

    builder.add_operation(
        op_id=f"{guard_id}_guard",
        op_type=f"validate_{guard_type}",
        params={"guard_id": guard_id, "condition": params.get("condition", {})}
    )


def _process_role_to_mir(builder: MIRBuilder, role: ProjectionNode) -> None:
    """
    Transform Role node sang MIR auth boundary.

    Args:
        builder: MIRBuilder
        role: Role ProjectionNode
    """
    params = role.params
    role_id = params.get("id", role.id)

    builder.add_boundary(
        boundary_id=f"auth_{role_id}",
        boundary_type="auth",
        enclosing_ops=[],
        config={
            "role_id": role_id,
            "permissions": params.get("permissions", []),
            "tenant_scope": params.get("tenant_scope", "global")
        }
    )


def _process_workflow_to_mir(builder: MIRBuilder, workflow: ProjectionNode) -> None:
    """
    Transform Workflow node sang MIR transaction boundary.

    Args:
        builder: MIRBuilder
        workflow: Workflow ProjectionNode
    """
    params = workflow.params
    workflow_id = params.get("id", workflow.id)

    # Extract operation IDs từ workflow states
    states = params.get("states", [])
    state_ops = [f"{workflow_id}_{state.get('id', str(i))}" for i, state in enumerate(states)]

    builder.add_boundary(
        boundary_id=f"txn_{workflow_id}",
        boundary_type="transaction",
        enclosing_ops=state_ops,
        config={"workflow_id": workflow_id}
    )


# ============================================================================
# Helper Functions for Metadata Storage
# ============================================================================

def _store_entities_in_metadata(builder: MIRBuilder, tree: ProjectionTree) -> None:
    """
    Lưu entities vào MIR metadata cho emitter sử dụng.

    Args:
        builder: MIRBuilder
        tree: ProjectionTree
    """
    entities = []
    for entity in tree.get_entities():
        entities.append({
            "id": entity.params.get("id", "Entity"),
            "description": entity.params.get("description", ""),
            "fields": entity.params.get("fields", []),
            "tenant_scope": entity.params.get("tenant_scope", "global"),
            "primary_key": entity.params.get("primary_key", "id"),
        })
    builder.mir.metadata["entities"] = entities


def _store_commands_in_metadata(builder: MIRBuilder, tree: ProjectionTree) -> None:
    """
    Lưu commands vào MIR metadata cho emitter sử dụng.

    Args:
        builder: MIRBuilder
        tree: ProjectionTree
    """
    commands = []
    for command in tree.get_commands():
        commands.append({
            "id": command.params.get("id", "Command"),
            "description": command.params.get("description", ""),
            "input": command.params.get("input", []),
            "writes_to": command.params.get("writes_to", []),
            "category": command.params.get("category", "custom"),
        })
    builder.mir.metadata["commands"] = commands


def _store_queries_in_metadata(builder: MIRBuilder, tree: ProjectionTree) -> None:
    """
    Lưu queries vào MIR metadata cho emitter sử dụng.

    Args:
        builder: MIRBuilder
        tree: ProjectionTree
    """
    queries = []
    for query in tree.get_queries():
        queries.append({
            "id": query.params.get("id", "Query"),
            "description": query.params.get("description", ""),
            "input": query.params.get("input", []),
            "reads_from": query.params.get("reads_from", []),
            "category": query.params.get("category", "list"),
        })
    builder.mir.metadata["queries"] = queries