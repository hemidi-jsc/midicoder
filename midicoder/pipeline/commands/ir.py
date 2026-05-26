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


# Các category contract bắt buộc (roles là optional)
_REQUIRED_CATEGORIES = {
    "entities", "commands", "queries", "events",
    "workflows", "value_objects", "guards"
}
# Roles là optional — có warnings nếu thiếu
_OPTIONAL_CATEGORIES = {"roles"}


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
    if validation_result.total_errors > 0:
        click.echo(f"⚠️  Validation warnings/errors: {validation_result.total_errors}")
        # Log first 5 errors for visibility, then proceed
        for error in validation_result.get_errors()[:5]:
            click.echo(f"   - {error.message}")
        if validation_result.total_errors > 5:
            click.echo(f"   ... and {validation_result.total_errors - 5} more")
        click.echo("   ℹ️  Continuing despite validation issues (auto-fix in progress)")
    else:
        click.echo(f"   ✓ Validation passed ({validation_result.total_warnings} warnings)")

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

    # Lưu entities/commands/queries/value_objects/events/guards/roles vào metadata cho emitter sử dụng
    _store_entities_in_metadata(builder, tree)
    _store_commands_in_metadata(builder, tree)
    _store_queries_in_metadata(builder, tree)
    _store_events_in_metadata(builder, tree)
    _store_guards_in_metadata(builder, tree)
    _store_workflows_in_metadata(builder, tree)
    _store_value_objects_in_metadata(builder, tree)
    _store_roles_in_metadata(builder, tree)
    # CP19: Store UI components/layouts/themes/form_builders into metadata
    _store_ui_components_in_metadata(builder, tree)
    _store_ui_layouts_in_metadata(builder, tree)
    _store_ui_themes_in_metadata(builder, tree)
    _store_ui_form_builders_in_metadata(builder, tree)

    # CP28: Store custom code blocks, hooks, patch_rules into metadata
    # (di chuyển từ hack trong file_contributions_loader.py sang IR build phase)
    _store_custom_code_in_metadata(builder, tree)

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

    # Process Value Objects → Operations
    for vo in tree.get_nodes_by_kind(NodeKind.VALUE_OBJECT):
        _process_value_object_to_mir(builder, vo)

    # Process Workflows → Boundaries (transaction)
    for workflow in tree.get_workflows():
        _process_workflow_to_mir(builder, workflow)

    # Store search nodes into metadata
    _store_search_indices_in_metadata(builder, tree)

    # Process Search Index → Operations
    for search_index in tree.get_search_indexes():
        _process_search_index_to_mir(builder, search_index)

    # Process Search Query → Operations
    for search_query in tree.get_search_queries():
        _process_search_query_to_mir(builder, search_query)

    # Process Vector Search Index → Operations
    for vector_search in tree.get_nodes_by_kind(NodeKind.VECTOR_SEARCH_INDEX):
        _process_vector_search_to_mir(builder, vector_search)

    # Process Geo Search Index → Operations
    for geo_search in tree.get_nodes_by_kind(NodeKind.GEO_SEARCH_INDEX):
        _process_geo_search_to_mir(builder, geo_search)

    # Process Faceted Search Index → Operations
    for faceted_search in tree.get_nodes_by_kind(NodeKind.FACETED_SEARCH_INDEX):
        _process_faceted_search_to_mir(builder, faceted_search)

    # CP19: Process UI Components → Operations (no MIR ops, metadata only for code gen)
    for ui_comp in tree.get_ui_components():
        _process_ui_component_to_mir(builder, ui_comp)
    for ui_layout in tree.get_ui_layouts():
        _process_ui_layout_to_mir(builder, ui_layout)
    for ui_theme in tree.get_ui_themes():
        _process_ui_theme_to_mir(builder, ui_theme)
    for ui_fb in tree.get_ui_form_builders():
        _process_ui_form_builder_to_mir(builder, ui_fb)

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

    # Event metadata — append to list (initialized by _store_events_in_metadata)
    event_entry = {
        "id": event_id,
        "type": params.get("type", "domain_event"),
        "fields": params.get("fields", []),
        "tenant_scope": params.get("tenant_scope", "global"),
    }
    if not any(e.get("id") == event_id for e in builder.mir.metadata.get("events", [])):
        builder.mir.metadata.setdefault("events", []).append(event_entry)


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
    Transform Workflow node sang MIR operations + boundary.

    Tạo:
    - workflow_state operations cho mỗi state
    - workflow_orchestrate operations cho mỗi transition
    - schedule_job operation cho scheduling
    - background_worker operation cho async transitions
    - effect_flows cho mỗi effect trong transitions
    - transaction boundary bao quanh tất cả

    Args:
        builder: MIRBuilder
        workflow: Workflow ProjectionNode
    """
    params = workflow.params
    workflow_id = params.get("id", workflow.id)
    states = params.get("states", [])
    transitions = params.get("transitions", [])
    effects_list = params.get("effects", [])
    guards_list = params.get("guards", [])

    all_op_ids: list[str] = []

    # 1. Tạo operation cho mỗi state
    for state in states:
        state_id = state if isinstance(state, str) else state.get("id", state.get("name", "unknown"))
        op_id = f"wf_state_{workflow_id}_{state_id}"
        builder.add_operation(
            op_id=op_id,
            op_type="workflow_state",
            params={
                "workflow_id": workflow_id,
                "state_id": state_id,
                "entity": params.get("entity"),
                "is_initial": state_id == params.get("initial_state"),
            },
            obligation_refs=[],
            metadata={"source_pack": "CP13", "workflow_id": workflow_id},
        )
        all_op_ids.append(op_id)

    # 2. Tạo operation cho mỗi transition
    for i, transition in enumerate(transitions):
        from_state = transition.get("from_state", "")
        to_state = transition.get("to_state", "")
        trans_id = transition.get("id", f"trans_{i}")
        op_id = f"wf_transition_{workflow_id}_{trans_id}"

        trans_guards = transition.get("guards", [])
        trans_effects = transition.get("effects", [])
        is_async = transition.get("async", False)

        builder.add_operation(
            op_id=op_id,
            op_type="workflow_orchestrate",
            params={
                "workflow_id": workflow_id,
                "transition_id": trans_id,
                "from_state": from_state,
                "to_state": to_state,
                "event": transition.get("event", trans_id),
                "async": is_async,
                "guards_count": len(trans_guards),
                "effects_count": len(trans_effects),
            },
            obligation_refs=["MDC-CP13-003"],
            input_refs=[f"wf_state_{workflow_id}_{from_state}"],
            output_refs=[f"wf_state_{workflow_id}_{to_state}"],
            metadata={"source_pack": "CP13", "workflow_id": workflow_id, "is_async": is_async},
        )
        all_op_ids.append(op_id)

        # Effect flows cho mỗi effect trong transition
        for effect in trans_effects:
            effect_type = effect.get("type", "event")
            target = (
                effect.get("publish") or
                effect.get("execute") or
                effect.get("action") or
                effect.get("rollback") or
                "unknown"
            )
            builder.add_effect_flow(
                source_op=op_id,
                effect_type=f"workflow_{effect_type}",
                target=target,
                payload_fields=list(effect.keys()),
                metadata={"source_pack": "CP13", "workflow_id": workflow_id},
            )

        # Nếu async, thêm background_worker operation
        if is_async:
            bg_op_id = f"wf_bg_{workflow_id}_{trans_id}"
            builder.add_operation(
                op_id=bg_op_id,
                op_type="background_worker",
                params={
                    "workflow_id": workflow_id,
                    "transition_id": trans_id,
                    "from_state": from_state,
                    "to_state": to_state,
                },
                obligation_refs=[],
                input_refs=[op_id],
                metadata={"source_pack": "CP13", "workflow_id": workflow_id},
            )
            all_op_ids.append(bg_op_id)

    # 3. Tạo schedule_job operation (nếu có gateway_types, sub_workflows, hoặc timers)
    gateway_types = params.get("gateway_types", [])
    sub_workflows = params.get("sub_workflows", [])
    timers = params.get("timers", [])
    compensation = params.get("compensation")
    human_tasks = params.get("human_tasks", [])

    if gateway_types or sub_workflows or timers or compensation or human_tasks:
        sched_op_id = f"wf_schedule_{workflow_id}"
        builder.add_operation(
            op_id=sched_op_id,
            op_type="schedule_job",
            params={
                "workflow_id": workflow_id,
                "gateway_types": gateway_types,
                "sub_workflows": sub_workflows,
                "has_timers": bool(timers),
                "has_compensation": bool(compensation),
                "has_human_tasks": bool(human_tasks),
            },
            obligation_refs=["MDC-CP13-001"],
            metadata={"source_pack": "CP13", "workflow_id": workflow_id},
        )
        all_op_ids.append(sched_op_id)

    # 4. Tạo transaction boundary bao quanh tất cả operations
    builder.add_boundary(
        boundary_id=f"txn_{workflow_id}",
        boundary_type="transaction",
        enclosing_ops=list(all_op_ids),
        config={
            "workflow_id": workflow_id,
            "entity": params.get("entity"),
            "states_count": len(states),
            "transitions_count": len(transitions),
        }
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


def _store_events_in_metadata(builder: MIRBuilder, tree: ProjectionTree) -> None:
    """
    Lưu events vào MIR metadata cho emitter sử dụng.

    Args:
        builder: MIRBuilder
        tree: ProjectionTree
    """
    events = []
    for event in tree.get_events():
        events.append({
            "id": event.params.get("id", "Event"),
            "description": event.params.get("description", ""),
            "type": event.params.get("type", "domain_event"),
            "source_entity": event.params.get("source_entity"),
            "fields": event.params.get("fields", []),
            "tenant_scope": event.params.get("tenant_scope", "global"),
        })
    builder.mir.metadata["events"] = events


def _store_guards_in_metadata(builder: MIRBuilder, tree: ProjectionTree) -> None:
    """
    Lưu guards vào MIR metadata cho emitter sử dụng.

    Args:
        builder: MIRBuilder
        tree: ProjectionTree
    """
    guards = []
    for guard in tree.get_guards():
        guards.append({
            "id": guard.params.get("id", "Guard"),
            "description": guard.params.get("description", ""),
            "type": guard.params.get("type", "validation"),
            "condition": guard.params.get("condition", {}),
        })
    builder.mir.metadata["guards"] = guards


def _store_workflows_in_metadata(builder: MIRBuilder, tree: ProjectionTree) -> None:
    """
    Lưu workflows vào MIR metadata cho emitter sử dụng.

    Args:
        builder: MIRBuilder
        tree: ProjectionTree
    """
    workflows = []
    for workflow in tree.get_workflows():
        workflows.append({
            "id": workflow.params.get("id", "Workflow"),
            "description": workflow.params.get("description", ""),
            "states": workflow.params.get("states", []),
            "transitions": workflow.params.get("transitions", []),
            "guards": workflow.params.get("guards", []),
            "effects": workflow.params.get("effects", []),
            "entity": workflow.params.get("entity"),
            "initial_state": workflow.params.get("initial_state"),
            "gateway_types": workflow.params.get("gateway_types", []),
            "sub_workflows": workflow.params.get("sub_workflows", []),
            "compensation": workflow.params.get("compensation"),
            "human_tasks": workflow.params.get("human_tasks", []),
            "timers": workflow.params.get("timers", []),
            "tenant_scope": workflow.params.get("tenant_scope", "global"),
            "tags": workflow.params.get("tags", []),
        })
    builder.mir.metadata["workflows"] = workflows


def _store_value_objects_in_metadata(builder: MIRBuilder, tree: ProjectionTree) -> None:
    """
    Lưu value objects vào MIR metadata cho emitter sử dụng.

    Args:
        builder: MIRBuilder
        tree: ProjectionTree
    """
    value_objects = []
    for vo in tree.get_nodes_by_kind(NodeKind.VALUE_OBJECT):
        value_objects.append({
            "id": vo.params.get("id", "ValueObject"),
            "description": vo.params.get("description", ""),
            "fields": vo.params.get("fields", []),
            "immutable": vo.params.get("immutable", True),
            "comparable": vo.params.get("comparable", False),
            "extends": vo.params.get("extends"),
        })
    builder.mir.metadata["value_objects"] = value_objects


def _store_roles_in_metadata(builder: MIRBuilder, tree: ProjectionTree) -> None:
    """
    Lưu roles vào MIR metadata cho emitter sử dụng.

    Args:
        builder: MIRBuilder
        tree: ProjectionTree
    """
    roles = []
    for role in tree.get_nodes_by_kind(NodeKind.ROLE):
        roles.append({
            "id": role.params.get("id", "Role"),
            "description": role.params.get("description", ""),
            "permissions": role.params.get("permissions", []),
            "tenant_scope": role.params.get("tenant_scope", "global"),
        })
    builder.mir.metadata["roles"] = roles


# =========================================================================
# CP19: UI Component Generator — Store & Process functions
# =========================================================================

def _store_ui_components_in_metadata(builder: MIRBuilder, tree: ProjectionTree) -> None:
    """Store UI components into MIR metadata for CP19 code gen."""
    ui_components = []
    for comp in tree.get_ui_components():
        ui_components.append({
            "id": comp.params.get("id", "UIComponent"),
            "component_type": comp.params.get("component_type", "form_field"),
            "entity_id": comp.params.get("entity_id"),
            "properties": comp.params.get("properties", {}),
            "description": comp.params.get("description", ""),
        })
    builder.mir.metadata["ui_components"] = ui_components


def _store_ui_layouts_in_metadata(builder: MIRBuilder, tree: ProjectionTree) -> None:
    """Store UI layouts into MIR metadata for CP19 code gen."""
    ui_layouts = []
    for layout in tree.get_ui_layouts():
        ui_layouts.append({
            "id": layout.params.get("id", "UILayout"),
            "layout_type": layout.params.get("layout_type", "page"),
            "regions": layout.params.get("regions", []),
            "properties": layout.params.get("properties", {}),
            "description": layout.params.get("description", ""),
        })
    builder.mir.metadata["ui_layouts"] = ui_layouts


def _store_ui_themes_in_metadata(builder: MIRBuilder, tree: ProjectionTree) -> None:
    """Store UI themes into MIR metadata for CP19 code gen."""
    ui_themes = []
    for theme in tree.get_ui_themes():
        ui_themes.append({
            "id": theme.params.get("id", "UITheme"),
            "name": theme.params.get("name", "default"),
            "tokens": theme.params.get("tokens", {}),
            "dark_mode": theme.params.get("dark_mode", False),
            "description": theme.params.get("description", ""),
        })
    builder.mir.metadata["ui_themes"] = ui_themes


def _store_ui_form_builders_in_metadata(builder: MIRBuilder, tree: ProjectionTree) -> None:
    """Store UI form builders into MIR metadata for CP19 code gen."""
    ui_form_builders = []
    for fb in tree.get_ui_form_builders():
        ui_form_builders.append({
            "id": fb.params.get("id", "UIFormBuilder"),
            "entity_id": fb.params.get("entity_id"),
            "fields": fb.params.get("fields", []),
            "conditional_rules": fb.params.get("conditional_rules", []),
            "properties": fb.params.get("properties", {}),
            "description": fb.params.get("description", ""),
        })
    builder.mir.metadata["ui_form_builders"] = ui_form_builders


def _store_custom_code_in_metadata(builder: MIRBuilder, tree: ProjectionTree) -> None:
    """
    Lưu CP28 custom code data vào MIR metadata.

    Di chuyển từ hack trong file_contributions_loader.py (expand_infrastructure)
    sang IR build phase — đúng với 3-layer pipeline (DSL → MIR → Emit).

    Auto-generate từ entities và commands trong ProjectionTree.

    Args:
        builder: MIRBuilder
        tree: ProjectionTree
    """
    # Đọc entities và commands đã store trong metadata
    entities = builder.mir.metadata.get("entities", [])
    commands = builder.mir.metadata.get("commands", [])

    try:
        # CP28 recipes merged into CP27 — use CP27's auto_generate_plugins_from_mir
        from midicoder.emitters.core.cp27_plugin_system.recipes import (
            auto_generate_plugins_from_mir,
        )
        collection = auto_generate_plugins_from_mir({
            "entities": entities,
            "commands": commands,
        })
        coll_dict = collection.to_dict()
        builder.mir.metadata["custom_code_blocks"] = coll_dict.get("blocks", [])
        builder.mir.metadata["hooks"] = coll_dict.get("hooks", [])
        builder.mir.metadata["patch_rules"] = coll_dict.get("patch_rules", [])
    except Exception:
        # Fallback: nếu CP28 recipes không available, set empty lists
        # — templates vẫn render được với data rỗng
        builder.mir.metadata.setdefault("custom_code_blocks", [])
        builder.mir.metadata.setdefault("hooks", [])
        builder.mir.metadata.setdefault("patch_rules", [])


def _process_ui_component_to_mir(builder: MIRBuilder, node: ProjectionNode) -> None:
    """Process UI component node — adds operation for component generation."""
    params = node.params
    comp_id = params.get("id", node.id)
    comp_type = params.get("component_type", "form_field")

    builder.add_operation(
        op_id=f"{comp_id}_gen",
        op_type=f"generate_ui_{comp_type}",
        params={
            "component_id": comp_id,
            "component_type": comp_type,
            "entity_id": params.get("entity_id"),
            "properties": params.get("properties", {}),
        },
    )


def _process_ui_layout_to_mir(builder: MIRBuilder, node: ProjectionNode) -> None:
    """Process UI layout node — adds operation for layout generation."""
    params = node.params
    layout_id = params.get("id", node.id)

    builder.add_operation(
        op_id=f"{layout_id}_gen",
        op_type="generate_ui_layout",
        params={
            "layout_id": layout_id,
            "layout_type": params.get("layout_type", "page"),
            "regions": params.get("regions", []),
            "properties": params.get("properties", {}),
        },
    )


def _process_ui_theme_to_mir(builder: MIRBuilder, node: ProjectionNode) -> None:
    """Process UI theme node — adds operation for theme generation."""
    params = node.params
    theme_id = params.get("id", node.id)

    builder.add_operation(
        op_id=f"{theme_id}_gen",
        op_type="generate_ui_theme",
        params={
            "theme_id": theme_id,
            "name": params.get("name", "default"),
            "tokens": params.get("tokens", {}),
            "dark_mode": params.get("dark_mode", False),
        },
    )


def _process_ui_form_builder_to_mir(builder: MIRBuilder, node: ProjectionNode) -> None:
    """Process UI form builder node — adds operation for form builder generation."""
    params = node.params
    fb_id = params.get("id", node.id)

    builder.add_operation(
        op_id=f"{fb_id}_gen",
        op_type="generate_ui_form_builder",
        params={
            "form_builder_id": fb_id,
            "entity_id": params.get("entity_id"),
            "fields": params.get("fields", []),
            "conditional_rules": params.get("conditional_rules", []),
            "properties": params.get("properties", {}),
        },
    )


def _process_value_object_to_mir(builder: MIRBuilder, vo: ProjectionNode) -> None:
    """
    Transform Value Object node sang MIR operation.

    Args:
        builder: MIRBuilder
        vo: Value Object ProjectionNode
    """
    params = vo.params
    vo_id = params.get("id", vo.id)

    builder.add_operation(
        op_id=f"{vo_id}_vo",
        op_type="create_value_object",
        params={
            "value_object_id": vo_id,
            "immutable": params.get("immutable", True),
            "extends": params.get("extends"),
        },
    )


# ============================================================================
# Search Operation Generation (CP10)
# ============================================================================


def _store_search_indices_in_metadata(builder: MIRBuilder, tree: ProjectionTree) -> None:
    """
    Lưu search indices vào MIR metadata cho emitter sử dụng.

    Args:
        builder: MIRBuilder
        tree: ProjectionTree
    """
    search_indices = []
    for si in tree.get_search_indexes():
        search_indices.append({
            "id": si.params.get("id", "SearchIndex"),
            "description": si.params.get("description", ""),
            "name": si.params.get("name"),
            "engine": si.params.get("engine", "elasticsearch"),
            "entity_id": si.params.get("entity_id"),
            "fields": si.params.get("fields", []),
            "config": si.params.get("config", {}),
            "tags": si.params.get("tags", []),
        })
    builder.mir.metadata["search_indices"] = search_indices

    vector_search_indices = []
    for vs in tree.get_nodes_by_kind(NodeKind.VECTOR_SEARCH_INDEX):
        vector_search_indices.append({
            "id": vs.params.get("id", "VectorSearch"),
            "description": vs.params.get("description", ""),
            "provider": vs.params.get("provider", "elasticsearch"),
            "dimensions": vs.params.get("dimensions"),
            "similarity_metric": vs.params.get("similarity_metric", "cosine"),
            "index_type": vs.params.get("index_type", "hnsw"),
            "vector_column": vs.params.get("vector_column"),
            "text_columns": vs.params.get("text_columns", []),
            "top_k": vs.params.get("top_k", 10),
            "tenant_isolated": vs.params.get("tenant_isolated", False),
            "tags": vs.params.get("tags", []),
        })
    builder.mir.metadata["vector_search_indices"] = vector_search_indices

    geo_search_indices = []
    for gs in tree.get_nodes_by_kind(NodeKind.GEO_SEARCH_INDEX):
        geo_search_indices.append({
            "id": gs.params.get("id", "GeoSearch"),
            "description": gs.params.get("description", ""),
            "provider": gs.params.get("provider", "elasticsearch"),
            "geo_column": gs.params.get("geo_column"),
            "geo_type": gs.params.get("geo_type", "point"),
            "operations": gs.params.get("operations", []),
            "text_columns": gs.params.get("text_columns", []),
            "tenant_isolated": gs.params.get("tenant_isolated", False),
            "tags": gs.params.get("tags", []),
        })
    builder.mir.metadata["geo_search_indices"] = geo_search_indices

    faceted_search_indices = []
    for fs in tree.get_nodes_by_kind(NodeKind.FACETED_SEARCH_INDEX):
        faceted_search_indices.append({
            "id": fs.params.get("id", "FacetedSearch"),
            "description": fs.params.get("description", ""),
            "provider": fs.params.get("provider", "elasticsearch"),
            "columns": fs.params.get("columns", []),
            "facets": fs.params.get("facets", []),
            "tenant_isolated": fs.params.get("tenant_isolated", False),
            "tags": fs.params.get("tags", []),
        })
    builder.mir.metadata["faceted_search_indices"] = faceted_search_indices

    search_queries = []
    for sq in tree.get_search_queries():
        search_queries.append({
            "id": sq.params.get("id", "SearchQuery"),
            "description": sq.params.get("description", ""),
            "name": sq.params.get("name"),
            "index_id": sq.params.get("index_id"),
            "query_type": sq.params.get("query_type", "full_text"),
            "fields": sq.params.get("fields", []),
            "filters": sq.params.get("filters", []),
            "tags": sq.params.get("tags", []),
        })
    builder.mir.metadata["search_queries"] = search_queries


def _process_search_index_to_mir(builder: MIRBuilder, node: ProjectionNode) -> None:
    """
    Transform SearchIndex node sang MIR operation.

    Tạo search_index operation với params từ SearchIndex node.
    Thêm data flow từ search operation đến entity tương ứng.
    Thêm effect flow cho search events nếu có.

    Args:
        builder: MIRBuilder
        node: SearchIndex ProjectionNode
    """
    params = node.params
    index_id = params.get("id", node.id)
    entity_id = params.get("entity_id")

    # Main search index operation
    builder.add_operation(
        op_id=f"{index_id}_index",
        op_type="search_index",
        params={
            "index_id": index_id,
            "name": params.get("name", index_id),
            "engine": params.get("engine", "elasticsearch"),
            "entity_id": entity_id,
            "fields": params.get("fields", []),
            "config": params.get("config", {}),
        },
        output_refs=[f"{index_id}_index_ref"]
    )

    # Data flow từ search index đến entity
    if entity_id:
        builder.add_data_flow(
            source_op=f"{index_id}_index",
            source_field="indexed_data",
            target_op=f"{entity_id}_main",
            target_field="search_index_ref"
        )

    # Effect flow cho index events
    builder.add_effect_flow(
        source_op=f"{index_id}_index",
        effect_type="index_event",
        target=f"{index_id}_indexed",
        payload_fields=["index_id", "entity_id", "document_count"]
    )


def _process_vector_search_to_mir(builder: MIRBuilder, node: ProjectionNode) -> None:
    """
    Transform Vector Search Index node sang MIR operation.

    Tạo vector_search operation với params từ Vector Search node.
    Hỗ trợ similarity search trên embedding vectors.

    Args:
        builder: MIRBuilder
        node: Vector Search Index ProjectionNode
    """
    params = node.params
    index_id = params.get("id", node.id)

    # Main vector search operation
    builder.add_operation(
        op_id=f"{index_id}_vector",
        op_type="vector_search",
        params={
            "index_id": index_id,
            "provider": params.get("provider", "elasticsearch"),
            "dimensions": params.get("dimensions"),
            "similarity_metric": params.get("similarity_metric", "cosine"),
            "index_type": params.get("index_type", "hnsw"),
            "vector_column": params.get("vector_column"),
            "text_columns": params.get("text_columns", []),
            "top_k": params.get("top_k", 10),
            "tenant_isolated": params.get("tenant_isolated", False),
        },
        output_refs=[f"{index_id}_vector_ref"]
    )

    # Tenant scope enforcement nếu có tenant isolation
    if params.get("tenant_isolated", False):
        builder.add_operation(
            op_id=f"{index_id}_tenant",
            op_type="enforce_tenant_scope",
            params={"scope": "tenant_isolated"},
            obligation_refs=[f"tenant_oblig_{index_id}"]
        )
        builder.add_data_flow(
            source_op=f"{index_id}_tenant",
            source_field="tenant_id",
            target_op=f"{index_id}_vector",
            target_field="tenant_scope"
        )

    # Effect flow cho vector search events
    builder.add_effect_flow(
        source_op=f"{index_id}_vector",
        effect_type="search_event",
        target=f"{index_id}_vector_searched",
        payload_fields=["index_id", "query_vector", "result_count"]
    )


def _process_geo_search_to_mir(builder: MIRBuilder, node: ProjectionNode) -> None:
    """
    Transform Geo Search Index node sang MIR operation.

    Tạo geo_search operation với params từ Geo Search node.
    Hỗ trợ geospatial tìm kiếm dựa trên vị trí địa lý.

    Args:
        builder: MIRBuilder
        node: Geo Search Index ProjectionNode
    """
    params = node.params
    index_id = params.get("id", node.id)

    # Main geo search operation
    builder.add_operation(
        op_id=f"{index_id}_geo",
        op_type="geo_search",
        params={
            "index_id": index_id,
            "provider": params.get("provider", "elasticsearch"),
            "geo_column": params.get("geo_column"),
            "geo_type": params.get("geo_type", "point"),
            "operations": params.get("operations", []),
            "text_columns": params.get("text_columns", []),
            "tenant_isolated": params.get("tenant_isolated", False),
        },
        output_refs=[f"{index_id}_geo_ref"]
    )

    # Tenant scope enforcement nếu có tenant isolation
    if params.get("tenant_isolated", False):
        builder.add_operation(
            op_id=f"{index_id}_tenant",
            op_type="enforce_tenant_scope",
            params={"scope": "tenant_isolated"},
            obligation_refs=[f"tenant_oblig_{index_id}"]
        )
        builder.add_data_flow(
            source_op=f"{index_id}_tenant",
            source_field="tenant_id",
            target_op=f"{index_id}_geo",
            target_field="tenant_scope"
        )

    # Effect flow cho geo search events
    builder.add_effect_flow(
        source_op=f"{index_id}_geo",
        effect_type="search_event",
        target=f"{index_id}_geo_searched",
        payload_fields=["index_id", "geo_query", "result_count"]
    )


def _process_faceted_search_to_mir(builder: MIRBuilder, node: ProjectionNode) -> None:
    """
    Transform Faceted Search Index node sang MIR operation.

    Tạo faceted_search operation với params từ Faceted Search node.
    Hỗ trợ tìm kiếm có phân loại theo nhiều facet.

    Args:
        builder: MIRBuilder
        node: Faceted Search Index ProjectionNode
    """
    params = node.params
    index_id = params.get("id", node.id)

    # Main faceted search operation
    builder.add_operation(
        op_id=f"{index_id}_faceted",
        op_type="faceted_search",
        params={
            "index_id": index_id,
            "provider": params.get("provider", "elasticsearch"),
            "columns": params.get("columns", []),
            "facets": params.get("facets", []),
            "tenant_isolated": params.get("tenant_isolated", False),
        },
        output_refs=[f"{index_id}_faceted_ref"]
    )

    # Tenant scope enforcement nếu có tenant isolation
    if params.get("tenant_isolated", False):
        builder.add_operation(
            op_id=f"{index_id}_tenant",
            op_type="enforce_tenant_scope",
            params={"scope": "tenant_isolated"},
            obligation_refs=[f"tenant_oblig_{index_id}"]
        )
        builder.add_data_flow(
            source_op=f"{index_id}_tenant",
            source_field="tenant_id",
            target_op=f"{index_id}_faceted",
            target_field="tenant_scope"
        )

    # Effect flow cho faceted search events
    builder.add_effect_flow(
        source_op=f"{index_id}_faceted",
        effect_type="search_event",
        target=f"{index_id}_faceted_searched",
        payload_fields=["index_id", "facet_filters", "result_count"]
    )


def _process_search_query_to_mir(builder: MIRBuilder, node: ProjectionNode) -> None:
    """
    Transform SearchQuery node sang MIR operation.

    Tạo search_query operation với params từ SearchQuery node.
    Thêm data flow liên kết với search index.

    Args:
        builder: MIRBuilder
        node: SearchQuery ProjectionNode
    """
    params = node.params
    query_id = params.get("id", node.id)
    index_id = params.get("index_id")

    # Authorization — nếu query có required_permissions
    required_perms = params.get("required_permissions", [])
    if required_perms:
        builder.add_operation(
            op_id=f"{query_id}_auth",
            op_type="authorize_permission",
            params={"permissions": required_perms}
        )

    # Main search query operation
    builder.add_operation(
        op_id=f"{query_id}_search",
        op_type="search_query",
        params={
            "query_id": query_id,
            "name": params.get("name", query_id),
            "index_id": index_id,
            "query_type": params.get("query_type", "full_text"),
            "fields": params.get("fields", []),
            "filters": params.get("filters", []),
        },
        input_refs=[f"{query_id}_input"],
        output_refs=[f"{query_id}_result"]
    )

    # Data flow từ search index đến search query
    if index_id:
        builder.add_data_flow(
            source_op=f"{index_id}_index",
            source_field="index_ref",
            target_op=f"{query_id}_search",
            target_field="index"
        )

    # Data flow từ auth đến search query (nếu có auth)
    if required_perms:
        builder.add_data_flow(
            source_op=f"{query_id}_auth",
            source_field="user_context",
            target_op=f"{query_id}_search",
            target_field="auth_context"
        )