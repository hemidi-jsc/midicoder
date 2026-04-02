"""Integration metadata builders for code-plan artifacts."""

from __future__ import annotations

from typing import Any

from .models import IRPlanItem, IntegrationContext, RequiredFile, SuggestedPath


def build_integration_context(
    *,
    ir: dict[str, Any],
    seams: list[dict[str, Any]],
    virtual_seams: list[dict[str, Any]],
    profile: dict[str, Any] | None,
) -> IntegrationContext:
    modules = ir.get("modules") if isinstance(ir.get("modules"), dict) else {}
    routes_by_command, routes_by_query = _build_route_indexes(modules)
    permissions_by_item = _build_policy_index(modules)
    errors_by_key = _build_error_index(modules)
    workflow_transitions_by_command = _build_workflow_transition_index(modules)
    io_by_ref, io_by_symbol = _build_io_index(modules)
    return IntegrationContext(
        canonical_symbols=_build_canonical_symbols(ir),
        routes_by_command=routes_by_command,
        routes_by_query=routes_by_query,
        permissions_by_item=permissions_by_item,
        errors_by_key=errors_by_key,
        workflow_transitions_by_command=workflow_transitions_by_command,
        io_by_ref=io_by_ref,
        io_by_symbol=io_by_symbol,
        seams=seams,
        virtual_seams=virtual_seams,
        profile=profile,
    )


def build_plan_contracts(
    *,
    item: IRPlanItem,
    target: str,
    pseudo_struct: dict[str, Any],
    suggested_paths: list[SuggestedPath],
    required_files: list[RequiredFile],
    context: IntegrationContext,
) -> tuple[
    dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]
]:
    integration_contract = _build_integration_contract(
        item, target, pseudo_struct, context
    )
    io_reconciliation = _build_io_reconciliation(item, pseudo_struct, context)
    security_contract = _build_security_contract(item, context)
    error_contract = _build_error_contract(item, context)
    merge_contract = _build_merge_contract(
        item, target, suggested_paths, required_files
    )
    return (
        integration_contract,
        io_reconciliation,
        security_contract,
        error_contract,
        merge_contract,
    )


def _build_integration_contract(
    item: IRPlanItem,
    target: str,
    pseudo_struct: dict[str, Any],
    context: IntegrationContext,
) -> dict[str, Any]:
    raw_key = _normalize_symbol(item.raw_id)
    canonical = context.canonical_symbols
    expected_imports: list[str] = []
    if target.startswith("fastapi_"):
        expected_imports = ["fastapi", "pydantic"]
    elif target.startswith("nest_"):
        expected_imports = ["@nestjs/common"]

    service_signature = {
        "name": item.raw_id,
        "inputs": sorted(_field_names(item.io_contract.get("inputs", []))),
        "outputs": sorted(_field_names(item.io_contract.get("outputs", []))),
    }

    repo_methods = _infer_repo_methods(item)
    workflow_bindings = context.workflow_transitions_by_command.get(raw_key, [])
    routes = (
        pseudo_struct.get("api", {}).get("routes", [])
        if isinstance(pseudo_struct.get("api"), dict)
        else []
    )
    return {
        "public_symbols": {
            "ir_ref": item.id,
            "type": item.type_name,
            "id": item.raw_id,
            "module": item.module,
            "target": target,
            "canonical": canonical.get(item.type_name.lower(), {}).get(raw_key),
        },
        "expected_imports": expected_imports,
        "service_signature": service_signature,
        "repo_signature": {"methods": sorted(repo_methods)},
        "route_handler_contract": [
            {
                "route_id": route.get("id"),
                "method": route.get("method"),
                "path": route.get("path"),
                "handler_symbol": item.raw_id,
            }
            for route in routes
            if isinstance(route, dict)
        ],
        "workflow_integration_contract": workflow_bindings,
    }


def _build_io_reconciliation(
    item: IRPlanItem,
    pseudo_struct: dict[str, Any],
    context: IntegrationContext,
) -> dict[str, Any]:
    routes = (
        pseudo_struct.get("api", {}).get("routes", [])
        if isinstance(pseudo_struct.get("api"), dict)
        else []
    )
    outputs = _field_names(item.io_contract.get("outputs", []))
    response_mapping = (
        pseudo_struct.get("api", {}).get("response_mapping", [])
        if isinstance(pseudo_struct.get("api"), dict)
        else []
    )
    public_fields: set[str] = set()
    runtime_fields: set[str] = set()
    for route in routes:
        if not isinstance(route, dict):
            continue
        for field in route.get("response_schema", []):
            if isinstance(field, dict):
                name = str(field.get("name", "")).strip()
                if name:
                    public_fields.add(name)
    for mapping in response_mapping:
        if not isinstance(mapping, dict):
            continue
        api_field = str(mapping.get("api_field", "")).strip()
        source = str(mapping.get("source", "")).strip()
        if api_field and source.startswith("runtime."):
            runtime_fields.add(api_field)

    raw_key = _normalize_symbol(item.raw_id)
    symbol_io = context.io_by_symbol.get(raw_key, {})
    related_command = symbol_io.get("Command", {}).get("outputs", [])
    related_query = symbol_io.get("Query", {}).get("outputs", [])
    command_fields = _field_names(related_command)
    query_fields = _field_names(related_query)
    return {
        "public_response_fields": sorted(public_fields),
        "internal_fields": sorted(
            name for name in outputs if name not in public_fields
        ),
        "runtime_bridge_fields": sorted(runtime_fields),
        "cross_source": {
            "command_outputs": sorted(command_fields),
            "query_outputs": sorted(query_fields),
        },
        "status": "consistent"
        if (not public_fields or public_fields.issubset(outputs | runtime_fields))
        else "needs_runtime_bridge",
    }


def _build_security_contract(
    item: IRPlanItem, context: IntegrationContext
) -> dict[str, Any]:
    raw_key = _normalize_symbol(item.raw_id)
    rules = item.rules_contract.get("rules", [])
    hash_rule_ids = [
        str(rule.get("id", "")).strip()
        for rule in rules
        if isinstance(rule, dict)
        and "hash" in str(rule.get("id", "")).lower()
        and "password" in str(rule.get("id", "")).lower()
    ]
    outputs = _field_names(item.io_contract.get("outputs", []))
    token_policy: dict[str, Any] | None = None
    if {"access_token", "refresh_token"} & outputs or {
        "refresh_token_hash",
        "expired_at",
    } & outputs:
        token_policy = {
            "access_token_output": "access_token" in outputs,
            "refresh_token_output": "refresh_token" in outputs,
            "refresh_token_hash_output": "refresh_token_hash" in outputs,
            "expired_at_output": "expired_at" in outputs,
        }
    return {
        "authz_checks": context.permissions_by_item.get(raw_key, []),
        "password_hashing": {
            "required": bool(hash_rule_ids),
            "rules": hash_rule_ids,
        },
        "token_policy": token_policy,
    }


def _build_error_contract(
    item: IRPlanItem, context: IntegrationContext
) -> dict[str, Any]:
    raw_key = _normalize_symbol(item.raw_id)
    behavior_errors = [
        str(err).strip()
        for err in item.behavior_contract.get("errors", [])
        if isinstance(err, (str, int))
    ]
    known_errors = context.errors_by_key.get(raw_key, [])
    if not known_errors:
        known_errors = context.errors_by_key.get("*", [])
    return {
        "errors": known_errors,
        "behavior_error_refs": behavior_errors,
    }


def _build_merge_contract(
    item: IRPlanItem,
    target: str,
    suggested_paths: list[SuggestedPath],
    required_files: list[RequiredFile],
) -> dict[str, Any]:
    ownership = [path.file for path in suggested_paths if path.file]
    for required in required_files:
        pattern = required.path_pattern.strip()
        # Only include concrete file paths in ownership.
        if not pattern or "*" in pattern:
            continue
        ownership.append(pattern)

    mode = "create"
    if item.type_name in {"Command", "Query"}:
        mode = "patch"
    elif target.endswith("_workflow"):
        mode = "append"

    target_key = target.strip().lower()
    runtime_targets = {
        "fastapi_endpoint",
        "fastapi_route",
        "fastapi_service",
        "fastapi_model",
        "fastapi_repository",
        "fastapi_workflow",
        "fastapi_projection",
        "nest_endpoint",
        "nest_route",
        "nest_service",
        "nest_model",
        "nest_repository",
        "nest_workflow",
        "nest_projection",
    }
    write_scope = "runtime" if target_key in runtime_targets else "metadata_only"

    return {
        "mode": mode,
        "ownership": sorted(set(ownership)),
        "required_path_patterns": [
            entry.path_pattern for entry in required_files if entry.path_pattern
        ],
        "write_scope": write_scope,
    }


def _build_route_indexes(
    modules: dict[str, Any]
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]]]:
    routes = _resolve_records(modules, "api.http.routes")
    by_command: dict[str, list[dict[str, Any]]] = {}
    by_query: dict[str, list[dict[str, Any]]] = {}
    for route in routes:
        if not isinstance(route, dict):
            continue
        summary = {
            "id": route.get("id"),
            "method": route.get("method"),
            "path": route.get("path"),
            "request_schema": route.get("request_schema", []),
            "response_schema": route.get("response_schema", []),
        }
        command_ref = route.get("command")
        if isinstance(command_ref, dict):
            key = _normalize_symbol(str(command_ref.get("id", "")))
            if key:
                by_command.setdefault(key, []).append(summary)
        query_ref = route.get("query")
        if isinstance(query_ref, dict):
            key = _normalize_symbol(str(query_ref.get("id", "")))
            if key:
                by_query.setdefault(key, []).append(summary)
    return by_command, by_query


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
            permission_id = str(permission.get("id", "")).strip()
            if not permission_id:
                continue
            key = _normalize_symbol(permission_id)
            roles = [
                role for role, ids in role_bindings.items() if permission_id in ids
            ]
            by_item.setdefault(key, []).append(
                {
                    "id": permission_id,
                    "resource": permission.get("resource"),
                    "actions": permission.get("actions", []),
                    "roles": sorted(roles),
                }
            )
    return by_item


def _build_error_index(modules: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    errors = _resolve_records(modules, "application.errors")
    by_key: dict[str, list[dict[str, Any]]] = {"*": []}
    for error in errors:
        if not isinstance(error, dict):
            continue
        entry = {
            "id": error.get("id"),
            "code": error.get("code"),
            "http_status": error.get("http_status"),
            "category": error.get("category"),
            "description": error.get("description"),
        }
        tags = error.get("tags")
        if isinstance(tags, list):
            for tag in tags:
                key = _normalize_symbol(str(tag))
                if key:
                    by_key.setdefault(key, []).append(entry)
        by_key["*"].append(entry)
    return by_key


def _build_workflow_transition_index(
    modules: dict[str, Any]
) -> dict[str, list[dict[str, Any]]]:
    workflows = _resolve_records(modules, "workflow.workflows")
    by_command: dict[str, list[dict[str, Any]]] = {}
    for workflow in workflows:
        if not isinstance(workflow, dict):
            continue
        workflow_id = workflow.get("id")
        entity = workflow.get("entity")
        transitions = workflow.get("transitions", [])
        if not isinstance(transitions, list):
            continue
        for transition in transitions:
            if not isinstance(transition, dict):
                continue
            on_command = transition.get("on_command")
            if not isinstance(on_command, dict):
                continue
            key = _normalize_symbol(str(on_command.get("id", "")))
            if not key:
                continue
            by_command.setdefault(key, []).append(
                {
                    "workflow_id": workflow_id,
                    "entity": entity,
                    "from_state": transition.get("from_state"),
                    "to_state": transition.get("to_state"),
                    "guards": transition.get("guards", []),
                    "effects": transition.get("effects", []),
                }
            )
    return by_command


def _build_io_index(
    modules: dict[str, Any]
) -> tuple[
    dict[str, dict[str, list[dict[str, Any]]]],
    dict[str, dict[str, dict[str, list[dict[str, Any]]]]],
]:
    io_by_ref: dict[str, dict[str, list[dict[str, Any]]]] = {}
    io_by_symbol: dict[str, dict[str, dict[str, list[dict[str, Any]]]]] = {}
    for type_name, bucket in (
        ("Command", "application.commands"),
        ("Query", "application.queries"),
    ):
        records = _resolve_records(modules, bucket)
        for record in records:
            if not isinstance(record, dict):
                continue
            raw_id = str(record.get("id", "")).strip()
            if not raw_id:
                continue
            ref = f"{type_name}.{raw_id}"
            key = _normalize_symbol(raw_id)
            io = {
                "inputs": record.get("input", []),
                "outputs": record.get("returns", []),
            }
            io_by_ref[ref] = io
            io_by_symbol.setdefault(key, {})[type_name] = io
    return io_by_ref, io_by_symbol


def _build_canonical_symbols(ir: dict[str, Any]) -> dict[str, dict[str, Any]]:
    canonical: dict[str, dict[str, Any]] = {}
    indexes = ir.get("indexes")
    symbols = indexes.get("symbols") if isinstance(indexes, dict) else None
    if not isinstance(symbols, dict):
        return canonical
    for symbol_type, entries in symbols.items():
        if not isinstance(entries, dict):
            continue
        type_key = str(symbol_type).strip().lower()
        for symbol_id, payload in entries.items():
            key = _normalize_symbol(str(symbol_id))
            if not key:
                continue
            canonical.setdefault(type_key, {})[key] = payload
    return canonical


def _infer_repo_methods(item: IRPlanItem) -> set[str]:
    methods: set[str] = set()
    for dep in item.behavior_contract.get("fetches", []) + item.behavior_contract.get(
        "reads", []
    ):
        if not isinstance(dep, dict):
            continue
        dep_id = _normalize_symbol(str(dep.get("id", "")))
        if dep_id:
            methods.add(f"get_{dep_id}")
    for effect in item.behavior_contract.get("effects", []):
        if not isinstance(effect, dict):
            continue
        effect_id = str(effect.get("id", "")).strip().lower()
        params = effect.get("params")
        entity = ""
        if isinstance(params, dict):
            entity = _normalize_symbol(str(params.get("entity", "")))
        if effect_id == "db.insert" and entity:
            methods.add(f"insert_{entity}")
    return methods


def _field_names(fields: list[Any]) -> set[str]:
    names: set[str] = set()
    for field in fields:
        if isinstance(field, dict):
            name = str(field.get("name", "")).strip()
            if name:
                names.add(name)
    return names


def _resolve_records(modules: dict[str, Any], dotted_path: str) -> list[dict[str, Any]]:
    current: Any = modules
    for segment in dotted_path.split("."):
        if not isinstance(current, dict):
            return []
        current = current.get(segment)
    if isinstance(current, list):
        return [item for item in current if isinstance(item, dict)]
    return []


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
