"""Validation and IR iteration for code planning."""

from __future__ import annotations

import re
from typing import Any, Iterator

from .models import IRPlanItem

TYPED_ID_PATTERN = re.compile(r"^[A-Z][A-Za-z0-9]*\.[a-z0-9_]+$")

IR_BUCKETS: dict[str, tuple[str, str, str]] = {
    "application.commands": ("Command", "modules.application.commands", "commands"),
    "application.queries": ("Query", "modules.application.queries", "queries"),
    "application.projections": (
        "Projection",
        "modules.application.projections",
        "projections",
    ),
    "domain.entities": ("Entity", "modules.domain.entities", "entities"),
    "domain.value_objects": (
        "ValueObject",
        "modules.domain.value_objects",
        "value_objects",
    ),
    "domain.enums": ("Enum", "modules.domain.enums", "enums"),
    "workflow.workflows": ("Workflow", "modules.workflow.workflows", "workflows"),
}


def validate_typed_id(ir_ref: str) -> bool:
    return bool(TYPED_ID_PATTERN.match(ir_ref))


def iter_plan_items(ir: dict[str, Any]) -> Iterator[IRPlanItem]:
    modules = ir.get("modules")
    if not isinstance(modules, dict):
        return

    routes_by_command, routes_by_query = _build_route_indexes(modules)
    rules_by_item = _build_rule_index(modules)
    permissions_by_item = _build_policy_index(modules)
    workflow_transitions_by_command = _build_workflow_transition_index(modules)

    for bucket, (type_name, _, _) in IR_BUCKETS.items():
        records = _resolve_records(modules, bucket)
        for index, record in enumerate(records):
            if not isinstance(record, dict):
                continue

            raw_id = str(record.get("id", "")).strip()
            if not raw_id:
                continue

            intent = record.get("intent")
            if not isinstance(intent, dict):
                continue

            kind = str(intent.get("kind", "")).strip().lower()
            module = str(intent.get("module", "")).strip()
            if not kind or not module:
                continue

            ir_ref = f"{type_name}.{raw_id}"
            source = (
                record.get("source") if isinstance(record.get("source"), dict) else {}
            )
            source_order = source.get("source_order")
            if not isinstance(source_order, int):
                source_order = index

            io_contract = {
                "inputs": record.get("input", []),
                "outputs": record.get("returns", []),
            }
            behavior_contract = {
                "guards": record.get("guards", []),
                "effects": record.get("effects", []),
                "errors": record.get("errors", []),
                "emits": record.get("emits", []),
                "fetches": record.get("fetches", []),
                "reads": record.get("reads", []),
                "transaction": record.get("transaction"),
                "tenant_scope": record.get("tenant_scope"),
                "category": record.get("category"),
                "tags": record.get("tags", []),
                "filters": record.get("filters"),
                "pagination": record.get("pagination"),
            }
            api_contract = _build_api_contract(
                type_name=type_name,
                raw_id=raw_id,
                routes_by_command=routes_by_command,
                routes_by_query=routes_by_query,
            )
            state_contract = _build_state_contract(
                type_name=type_name,
                raw_id=raw_id,
                payload=record,
                workflow_transitions_by_command=workflow_transitions_by_command,
            )
            rules_contract = {"rules": rules_by_item.get(_normalize_symbol(raw_id), [])}
            policy_contract = {
                "permissions": permissions_by_item.get(_normalize_symbol(raw_id), [])
            }
            trace_contract = {
                "source_file": source.get("file"),
                "line_start": source.get("line_start"),
                "line_end": source.get("line_end"),
                "source_order": source_order,
            }

            yield IRPlanItem(
                raw_id=raw_id,
                type_name=type_name,
                id=ir_ref,
                kind=kind,
                module=module,
                source=source,
                payload=record,
                source_order=source_order,
                io_contract=io_contract,
                behavior_contract=behavior_contract,
                api_contract=api_contract,
                state_contract=state_contract,
                rules_contract=rules_contract,
                policy_contract=policy_contract,
                trace_contract=trace_contract,
            )


def collect_ir_refs(ir: dict[str, Any]) -> set[str]:
    return {item.id for item in iter_plan_items(ir)}


def collect_ir_symbol_ids(ir: dict[str, Any]) -> dict[str, set[str]]:
    symbol_map: dict[str, set[str]] = {
        "command": set(),
        "query": set(),
        "entity": set(),
        "workflow": set(),
        "event": set(),
    }
    indexes = ir.get("indexes")
    if not isinstance(indexes, dict):
        return symbol_map
    symbols = indexes.get("symbols")
    if not isinstance(symbols, dict):
        return symbol_map

    for key, entries in symbols.items():
        if not isinstance(entries, dict):
            continue
        lowered = str(key).strip().lower()
        if lowered not in symbol_map:
            continue
        for symbol_id in entries.keys():
            if isinstance(symbol_id, str) and symbol_id.strip():
                symbol_map[lowered].add(symbol_id.strip().lower())
    return symbol_map


def _resolve_records(modules: dict[str, Any], bucket: str) -> list[dict[str, Any]]:
    current: Any = modules
    for segment in bucket.split("."):
        if not isinstance(current, dict):
            return []
        current = current.get(segment)
    if isinstance(current, list):
        return [item for item in current if isinstance(item, dict)]
    return []


def _build_route_indexes(
    modules: dict[str, Any]
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]]]:
    routes = _resolve_records(modules, "api.http.routes")
    by_command: dict[str, list[dict[str, Any]]] = {}
    by_query: dict[str, list[dict[str, Any]]] = {}
    for route in routes:
        method = str(route.get("method", "")).upper()
        path = str(route.get("path", ""))
        summary = {
            "id": route.get("id"),
            "method": method,
            "path": path,
            "request_schema": route.get("request_schema"),
            "response_schema": route.get("response_schema"),
            "source_order": (
                (route.get("source") or {}).get("source_order")
                if isinstance(route.get("source"), dict)
                else None
            ),
        }

        command_ref = route.get("command")
        if isinstance(command_ref, dict):
            command_id = command_ref.get("id")
            if isinstance(command_id, str) and command_id.strip():
                by_command.setdefault(command_id.strip().lower(), []).append(summary)

        query_ref = route.get("query")
        if isinstance(query_ref, dict):
            query_id = query_ref.get("id")
            if isinstance(query_id, str) and query_id.strip():
                by_query.setdefault(query_id.strip().lower(), []).append(summary)

    return by_command, by_query


def _build_rule_index(modules: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    rules = _resolve_records(modules, "rules.rules")
    by_item: dict[str, list[dict[str, Any]]] = {}
    for rule in rules:
        applies_to = rule.get("applies_to")
        if not isinstance(applies_to, str) or not applies_to.strip():
            continue
        key = _normalize_symbol(applies_to)
        by_item.setdefault(key, []).append(
            {
                "id": rule.get("id"),
                "severity": rule.get("severity"),
                "description": rule.get("description"),
                "table": rule.get("table", []),
            }
        )
    return by_item


def _build_policy_index(modules: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    access = _resolve_object(modules, "policy.access")
    if not isinstance(access, dict):
        return {}
    permissions = access.get("permissions", [])
    bindings = access.get("bindings", [])
    role_bindings: dict[str, list[str]] = {}
    if isinstance(bindings, list):
        for binding in bindings:
            if not isinstance(binding, dict):
                continue
            role = str(binding.get("role", "")).strip()
            permission_ids = binding.get("permissions")
            if role and isinstance(permission_ids, list):
                role_bindings[role] = [
                    str(pid).strip() for pid in permission_ids if isinstance(pid, str)
                ]

    by_item: dict[str, list[dict[str, Any]]] = {}
    if isinstance(permissions, list):
        for permission in permissions:
            if not isinstance(permission, dict):
                continue
            permission_id = permission.get("id")
            if not isinstance(permission_id, str) or not permission_id.strip():
                continue
            key = _normalize_symbol(permission_id)
            matched_roles = [
                role
                for role, permission_ids in role_bindings.items()
                if permission_id in permission_ids
            ]
            by_item.setdefault(key, []).append(
                {
                    "id": permission_id,
                    "resource": permission.get("resource"),
                    "actions": permission.get("actions", []),
                    "roles": sorted(matched_roles),
                }
            )
    return by_item


def _build_workflow_transition_index(
    modules: dict[str, Any]
) -> dict[str, list[dict[str, Any]]]:
    workflows = _resolve_records(modules, "workflow.workflows")
    by_command: dict[str, list[dict[str, Any]]] = {}
    for workflow in workflows:
        workflow_id = workflow.get("id")
        transitions = workflow.get("transitions")
        if not isinstance(transitions, list):
            continue
        for transition in transitions:
            if not isinstance(transition, dict):
                continue
            on_command = transition.get("on_command")
            if not isinstance(on_command, dict):
                continue
            command_id = on_command.get("id")
            if not isinstance(command_id, str) or not command_id.strip():
                continue
            by_command.setdefault(command_id.strip().lower(), []).append(
                {
                    "workflow_id": workflow_id,
                    "from_state": transition.get("from_state"),
                    "to_state": transition.get("to_state"),
                    "guards": transition.get("guards", []),
                    "effects": transition.get("effects", []),
                }
            )
    return by_command


def _build_api_contract(
    *,
    type_name: str,
    raw_id: str,
    routes_by_command: dict[str, list[dict[str, Any]]],
    routes_by_query: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    key = raw_id.strip().lower()
    routes: list[dict[str, Any]]
    if type_name == "Command":
        routes = list(routes_by_command.get(key, []))
    elif type_name == "Query":
        routes = list(routes_by_query.get(key, []))
    else:
        routes = []
    routes = sorted(
        routes,
        key=lambda route: (
            route.get("source_order", 0) or 0,
            route.get("method", ""),
            route.get("path", ""),
        ),
    )
    return {"routes": routes}


def _build_state_contract(
    *,
    type_name: str,
    raw_id: str,
    payload: dict[str, Any],
    workflow_transitions_by_command: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    key = raw_id.strip().lower()
    if type_name == "Workflow":
        return {
            "entity": payload.get("entity"),
            "initial_state": payload.get("initial_state"),
            "states": payload.get("states", []),
            "transitions": payload.get("transitions", []),
            "error_handlers": payload.get("error_handlers", []),
        }
    return {"workflow_transitions": list(workflow_transitions_by_command.get(key, []))}


def _resolve_object(modules: dict[str, Any], dotted_path: str) -> Any:
    current: Any = modules
    for segment in dotted_path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(segment)
    return current


def _normalize_symbol(value: str) -> str:
    lowered = value.strip().lower()
    return "".join(ch for ch in lowered if ch.isalnum())
