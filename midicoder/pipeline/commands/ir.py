"""
IR Build Command Implementation.

Lệnh build MIR (Midicoder Intermediate Representation) từ Capability Graph:
- ir build: Build MIR từ Capability Graph trong SQLite

Theo SoT E04/E05:
- Input: Capability Graph từ artifacts table (SQLite)
- Process: ProjectionTree → MIR với typed IR
- Output: MIR JSON content lưu vào artifacts table

E04: IR Build Command
E05: MIR Typed IR

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import click
import json
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


def build_mir(verbose: bool = False) -> MIR:
    """
    Build MIR từ Capability Graph trong SQLite.

    Process:
    1. Query Capability Graph từ artifacts table
    2. Parse JSON sang ProjectionTree (DSL kernel)
    3. Validate ProjectionTree
    4. Build MIR từ ProjectionTree
    5. Save MIR JSON vào artifacts table

    Args:
        verbose: Verbose output

    Returns:
        MIR instance

    Raises:
        MidicoderError: Nếu không tìm thấy graph, parse fail, hoặc save fail
    """
    click.echo("🏗️  Đang build MIR từ Capability Graph...")

    # Step 1: Load Capability Graph từ SQLite
    artifacts_manager = ArtifactsManager()
    artifacts_manager.init()

    # Tìm capability graph artifact
    graph_artifact = artifacts_manager.get_by_type("capability_graph")
    if not graph_artifact:
        click.echo("❌ Không tìm thấy Capability Graph trong artifacts")
        click.echo("💡 Chạy 'midicoder contract gen' trước")
        EM.raise_error(ErrorCode.MIR_GRAPH_NOT_FOUND)

    click.echo(f"   → Found capability graph: {graph_artifact['artifact_id']}")

    # Parse JSON content thành dict
    try:
        graph_data = json.loads(graph_artifact['content'])
    except json.JSONDecodeError as e:
        EM.raise_error(
            ErrorCode.MIR_DSL_PARSE_FAILED,
            error=str(e)
        )

    # Step 2: Convert dict → ProjectionTree
    projection_tree = _dict_to_projection_tree(graph_data)
    click.echo(f"   → ProjectionTree: {projection_tree.node_count()} nodes")

    # Step 3: Validate ProjectionTree
    validator = Validator()
    validation_result = validator.validate(projection_tree)
    if validation_result.errors:
        click.echo("❌ Validation errors:")
        for error in validation_result.errors:
            click.echo(f"   - {error}")
        EM.raise_error(ErrorCode.MIR_VALIDATION_FAILED, errors=len(validation_result.errors))

    click.echo(f"   ✓ Validation passed ({len(validation_result.warnings)} warnings)")

    # Step 4: Build MIR từ ProjectionTree
    mir = _build_mir_from_projection_tree(projection_tree)
    click.echo(f"   → MIR: {len(mir.operations)} operations, "
               f"{len(mir.data_flows)} data flows, "
               f"{len(mir.effect_flows)} effect flows, "
               f"{len(mir.boundaries)} boundaries")

    # Step 5: Save MIR vào SQLite
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


def _dict_to_projection_tree(data: dict[str, Any]) -> ProjectionTree:
    """
    Chuyển dict từ SQLite sang ProjectionTree.

    Deprecated: Sử dụng DSLParser.parse_directory() thay thế.

    Args:
        data: Dictionary chứa capability graph data

    Returns:
        ProjectionTree instance
    """
    tree = ProjectionTree()

    # Process nodes từ dict
    for node_id, node_data in data.get("nodes", {}).items():
        kind_value = node_data.get("kind", "")
        params = node_data.get("params", {})

        # Map string kind to NodeKind enum
        try:
            kind = NodeKind(kind_value)
        except ValueError:
            # Unknown kind, skip
            continue

        node = ProjectionNode(
            id=node_id,
            kind=kind,
            params=params
        )
        tree.add_node(node)

    return tree


def _build_mir_from_contracts_directory(contracts_dir: str) -> MIR:
    """
    Build MIR từ contracts directory sử dụng DSLParser.

    Đây là preferred method để build MIR từ YAML contracts.

    Args:
        contracts_dir: Path đến contracts directory

    Returns:
        MIR instance
    """
    click.echo(f"📁 Parsing contracts từ: {contracts_dir}")

    # Parse YAML files → ProjectionTree
    dsl_parser = DSLParser()
    tree = dsl_parser.parse_directory(contracts_dir)

    click.echo(f"   → ProjectionTree: {tree.node_count()} nodes")

    # Validate ProjectionTree
    validator = Validator()
    validation_result = validator.validate(tree)
    if validation_result.errors:
        click.echo("❌ Validation errors:")
        for error in validation_result.errors:
            click.echo(f"   - {error}")
        EM.raise_error(ErrorCode.MIR_VALIDATION_FAILED, errors=len(validation_result.errors))

    click.echo(f"   ✓ Validation passed ({len(validation_result.warnings)} warnings)")

    # Build MIR từ ProjectionTree
    mir = _build_mir_from_projection_tree(tree)
    click.echo(f"   → MIR: {len(mir.operations)} operations, "
               f"{len(mir.data_flows)} data flows, "
               f"{len(mir.effect_flows)} effect flows, "
               f"{len(mir.boundaries)} boundaries")

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

    return builder.build()


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

    # Extract operation IDs from workflow states
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
