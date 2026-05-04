"""Emit code plan objects."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import PurePosixPath
from typing import Any

from midicoder import __version__

from .constants import CODE_PLAN_SCHEMA_VERSION
from .models import CodePlanItem, IRPlanItem, PlanMeta, RequiredFile, SuggestedPath


def build_plan_stub(item: IRPlanItem, stack: str) -> str:
    inputs = item.io_contract.get("inputs", [])
    outputs = item.io_contract.get("outputs", [])
    route_count = (
        len(item.api_contract.get("routes", []))
        if isinstance(item.api_contract, dict)
        else 0
    )
    workflow_transition_count = (
        len(item.state_contract.get("workflow_transitions", []))
        if isinstance(item.state_contract, dict)
        else 0
    )
    return (
        f"# plan-level stub\n"
        f"# ir_ref: {item.id}\n"
        f"# stack: {stack}\n"
        f"# kind: {item.kind}\n"
        f"# module: {item.module}\n"
        f"# inputs: {len(inputs)}\n"
        f"# outputs: {len(outputs)}\n"
        f"# routes: {route_count}\n"
        f"# workflow_transitions: {workflow_transition_count}"
    )


def build_pseudo_struct(item: IRPlanItem, stack: str) -> dict[str, Any]:
    behavior = item.behavior_contract
    rules = item.rules_contract.get("rules", [])
    permissions = item.policy_contract.get("permissions", [])
    workflow_transitions = item.state_contract.get("workflow_transitions", [])
    workflow_definition_transitions = item.state_contract.get("transitions", [])
    routes = item.api_contract.get("routes", [])

    steps: list[dict[str, Any]] = []
    if behavior.get("fetches") or behavior.get("reads"):
        steps.append(
            {
                "type": "fetch",
                "description": "Resolve required dependencies and read models",
                "fetches": behavior.get("fetches", []),
                "reads": behavior.get("reads", []),
            }
        )
    if rules:
        steps.append(
            {
                "type": "apply_rules",
                "description": "Validate business rules before mutation",
                "rules": [rule.get("id") for rule in rules],
            }
        )
    if behavior.get("guards") or permissions:
        steps.append(
            {
                "type": "authorize",
                "description": "Apply guard checks and permissions",
                "guards": behavior.get("guards", []),
                "permissions": permissions,
            }
        )
    if workflow_transitions:
        steps.append(
            {
                "type": "state_transition",
                "description": "Apply workflow transitions",
                "transitions": workflow_transitions,
            }
        )
    elif workflow_definition_transitions:
        steps.append(
            {
                "type": "state_transition",
                "description": "Define workflow transition graph",
                "transitions": workflow_definition_transitions,
            }
        )
    if behavior.get("effects"):
        steps.append(
            {
                "type": "persist",
                "description": "Apply effects and persist changes",
                "effects": behavior.get("effects", []),
                "transaction": behavior.get("transaction"),
            }
        )
    if behavior.get("emits"):
        steps.append(
            {
                "type": "emit_event",
                "description": "Publish domain events",
                "events": behavior.get("emits", []),
            }
        )
    steps.append(
        {
            "type": "return",
            "description": "Return output contract",
            "outputs": item.io_contract.get("outputs", []),
        }
    )

    pseudo_struct = {
        "intent": {
            "kind": item.kind,
            "module": item.module,
            "type": item.type_name,
            "stack": stack,
        },
        "inputs": item.io_contract.get("inputs", []),
        "outputs": item.io_contract.get("outputs", []),
        "preconditions": {
            "guards": behavior.get("guards", []),
            "rules": rules,
            "tenant_scope": behavior.get("tenant_scope"),
            "permissions": permissions,
        },
        "steps": steps,
        "dependencies": {
            "fetches": behavior.get("fetches", []),
            "reads": behavior.get("reads", []),
        },
        "errors": behavior.get("errors", []),
        "events": behavior.get("emits", []),
        "workflow": {
            "entity": item.state_contract.get("entity"),
            "initial_state": item.state_contract.get("initial_state"),
            "states": item.state_contract.get("states", []),
            "transitions": item.state_contract.get("transitions", []),
            "related_transitions": workflow_transitions,
            "error_handlers": item.state_contract.get("error_handlers", []),
        },
        "api": {
            "routes": routes,
            "request_mapping": _build_route_request_mapping(
                routes, item.io_contract.get("inputs", [])
            ),
            "response_mapping": _build_route_response_mapping(
                routes, item.io_contract.get("outputs", [])
            ),
        },
        "trace": item.trace_contract,
    }
    if item.type_name == "Entity":
        pseudo_struct["entity"] = {
            "primary_key": item.payload.get("primary_key"),
            "fields": item.payload.get("fields", []),
            "indexes": item.payload.get("indexes", []),
            "constraints": item.payload.get("constraints", []),
        }
    return pseudo_struct


def build_required_files(
    target: str, suggested_paths: list[SuggestedPath]
) -> list[RequiredFile]:
    primary = suggested_paths[0].file if suggested_paths else ""
    directory = _parent_dir(primary)
    normalized_target = target.strip().lower()

    if normalized_target == "fastapi_endpoint":
        return [
            RequiredFile(
                path_pattern=f"{directory}/controller.py",
                required=True,
                role="endpoint_controller",
                reason="HTTP endpoint",
            ),
            RequiredFile(
                path_pattern=f"{directory}/schema.py",
                required=True,
                role="dto_schema",
                reason="request/response contract",
            ),
            RequiredFile(
                path_pattern=f"{directory}/service.py",
                required=True,
                role="business_service",
                reason="runtime business logic",
            ),
        ]
    if normalized_target == "fastapi_model":
        return [
            RequiredFile(
                path_pattern=f"{directory}/model.py",
                required=True,
                role="domain_model",
                reason="runtime entity model",
            ),
            RequiredFile(
                path_pattern=f"{directory}/migrations/*.py",
                required=False,
                role="migration_stub",
                reason="optional persistence migration",
            ),
        ]
    if normalized_target == "nest_endpoint":
        return [
            RequiredFile(
                path_pattern=f"{directory}/*.controller.ts",
                required=True,
                role="endpoint_controller",
                reason="HTTP endpoint",
            ),
            RequiredFile(
                path_pattern=f"{directory}/*.service.ts",
                required=True,
                role="business_service",
                reason="runtime business logic",
            ),
            RequiredFile(
                path_pattern=f"{directory}/dto/*.dto.ts",
                required=True,
                role="dto_schema",
                reason="request/response contract",
            ),
            RequiredFile(
                path_pattern=f"{directory}/*.module.ts",
                required=True,
                role="module_wiring",
                reason="dependency wiring",
            ),
        ]
    if normalized_target == "nest_model":
        return [
            RequiredFile(
                path_pattern=f"{directory}/*.entity.ts",
                required=True,
                role="domain_model",
                reason="runtime entity model",
            ),
            RequiredFile(
                path_pattern=f"{directory}/migrations/*.ts",
                required=False,
                role="migration_stub",
                reason="optional persistence migration",
            ),
        ]

    if primary:
        return [
            RequiredFile(
                path_pattern=primary,
                required=True,
                role="primary_output",
                reason="resolved from suggested path",
            )
        ]
    return []


def collect_used_ir_kinds(item: IRPlanItem, ir: dict[str, Any]) -> list[str]:
    used = {item.id.split(".", 1)[0]}
    payload = item.payload

    for key in ("fetches", "errors", "emits", "reads", "source_events"):
        values = payload.get(key)
        if not isinstance(values, list):
            continue
        for value in values:
            if isinstance(value, dict):
                ref_type = value.get("type")
                if isinstance(ref_type, str) and ref_type:
                    used.add(ref_type)
    transitions = item.state_contract.get("workflow_transitions", [])
    if isinstance(transitions, list) and transitions:
        used.add("Workflow")

    if "modules" in ir:
        used.add("IR")
    return sorted(used)


def build_plan_meta(item: IRPlanItem, ir: dict[str, Any]) -> PlanMeta:
    source_checksum = _ir_source_checksum(ir)
    return PlanMeta(
        generated_at=datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        generator_version=__version__,
        source_ir_checksum=source_checksum,
        ir_kinds_used=collect_used_ir_kinds(item, ir),
    )


def emit_code_plan_item(
    *,
    ir_ref: str,
    target: str,
    pseudo: str,
    pseudo_struct: dict[str, Any] | None,
    suggested_paths: list[SuggestedPath],
    required_files: list[RequiredFile],
    meta: PlanMeta,
    integration_contract: dict[str, Any] | None = None,
    io_reconciliation: dict[str, Any] | None = None,
    security_contract: dict[str, Any] | None = None,
    error_contract: dict[str, Any] | None = None,
    merge_contract: dict[str, Any] | None = None,
) -> CodePlanItem:
    return CodePlanItem(
        schema_version=CODE_PLAN_SCHEMA_VERSION,
        ir_ref=ir_ref,
        target=target,
        pseudo=pseudo,
        pseudo_struct=pseudo_struct,
        suggested_paths=suggested_paths,
        required_files=required_files,
        meta=meta,
        integration_contract=integration_contract,
        io_reconciliation=io_reconciliation,
        security_contract=security_contract,
        error_contract=error_contract,
        merge_contract=merge_contract,
    )


def _ir_source_checksum(ir: dict[str, Any]) -> str:
    payload = json.dumps(ir, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _parent_dir(path: str) -> str:
    normalized = str(PurePosixPath(path.replace("\\", "/")))
    if not normalized or normalized == ".":
        return "."
    parent = str(PurePosixPath(normalized).parent)
    return "." if parent in {"", "."} else parent


def _build_route_request_mapping(
    routes: list[Any], inputs: list[Any]
) -> list[dict[str, Any]]:
    input_names = {
        str(field.get("name", "")).strip()
        for field in inputs
        if isinstance(field, dict) and str(field.get("name", "")).strip()
    }
    mappings: list[dict[str, Any]] = []
    for route in routes:
        if not isinstance(route, dict):
            continue
        route_id = str(route.get("id", "")).strip()
        for field in route.get("request_schema", []):
            if not isinstance(field, dict):
                continue
            name = str(field.get("name", "")).strip()
            if not name:
                continue
            if name in input_names:
                source = f"inputs.{name}"
            else:
                source = f"api_only.{name}"
            mappings.append(
                {
                    "route_id": route_id,
                    "api_field": name,
                    "source": source,
                }
            )
    return mappings


def _build_route_response_mapping(
    routes: list[Any], outputs: list[Any]
) -> list[dict[str, Any]]:
    output_names = {
        str(field.get("name", "")).strip()
        for field in outputs
        if isinstance(field, dict) and str(field.get("name", "")).strip()
    }
    mappings: list[dict[str, Any]] = []
    for route in routes:
        if not isinstance(route, dict):
            continue
        route_id = str(route.get("id", "")).strip()
        for field in route.get("response_schema", []):
            if not isinstance(field, dict):
                continue
            name = str(field.get("name", "")).strip()
            if not name:
                continue
            if name in output_names:
                source = f"outputs.{name}"
            else:
                source = f"runtime.{name}"
            mappings.append(
                {
                    "route_id": route_id,
                    "api_field": name,
                    "source": source,
                }
            )
    return mappings
