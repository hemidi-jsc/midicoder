"""Quality validation rules for code-plan contract checks."""

from __future__ import annotations

from typing import Any

from .logging import emit_error, emit_warning
from .models import IRPlanItem, RequiredFile, SuggestedPath

STRICT_TARGET_PREFIXES = ("fastapi_", "nest_")
LOW_CONFIDENCE_THRESHOLD = 0.6


def validate_plan_quality(
    *,
    item: IRPlanItem,
    target: str,
    pseudo_struct: dict[str, Any],
    suggested_paths: list[SuggestedPath],
    required_files: list[RequiredFile],
    symbol_ids: dict[str, set[str]],
    io_reconciliation: dict[str, Any] | None = None,
    integration_contract: dict[str, Any] | None = None,
    merge_contract: dict[str, Any] | None = None,
    security_contract: dict[str, Any] | None = None,
    strict_mode: bool = False,
) -> tuple[list[str], list[str]]:
    strict_target = strict_mode and _is_strict_target(target)
    errors: list[str] = []
    warnings: list[str] = []

    def report(code: str, message: str, phase: str, action: str, *, hard: bool = True) -> None:
        if hard and strict_target:
            errors.append(emit_error(code, message, phase=phase, action=action))
            return
        warning_code = code if not hard else f"W{code[1:]}" if code.startswith("E") else code
        warnings.append(emit_warning(warning_code, message, phase=phase, action=action))

    api_payload = pseudo_struct.get("api", {})
    routes = _as_list(api_payload.get("routes")) if isinstance(api_payload, dict) else []
    request_mapping = _as_list(api_payload.get("request_mapping")) if isinstance(api_payload, dict) else []
    response_mapping = _as_list(api_payload.get("response_mapping")) if isinstance(api_payload, dict) else []
    inputs = _as_list(pseudo_struct.get("inputs"))
    outputs = _as_list(pseudo_struct.get("outputs"))
    return_outputs = _find_return_outputs(pseudo_struct)

    if item.type_name in {"Command", "Query"}:
        input_names = _field_names(inputs)
        response_output_names = _field_names(outputs)
        for route in routes:
            if not isinstance(route, dict):
                continue
            route_id = str(route.get("id", "")).strip()
            request_fields = _required_field_names(_as_list(route.get("request_schema")))
            response_fields = _required_field_names(_as_list(route.get("response_schema")))

            unresolved_request = _unmapped_required_fields(
                route_id=route_id,
                required_fields=request_fields,
                mappings=request_mapping,
                accepted_prefixes=("inputs.",),
                fallback_names=input_names,
            )
            if unresolved_request:
                report(
                    "E354",
                    "request_schema required fields are not mapped to inputs",
                    phase="quality",
                    action=f"ir_ref={item.id};route={route_id};fields={','.join(sorted(unresolved_request))}",
                )

            unresolved_response = _unmapped_required_fields(
                route_id=route_id,
                required_fields=response_fields,
                mappings=response_mapping,
                accepted_prefixes=("outputs.", "runtime."),
                fallback_names=response_output_names,
            )
            if unresolved_response:
                report(
                    "E354",
                    "response_schema required fields are not mapped",
                    phase="quality",
                    action=f"ir_ref={item.id};route={route_id};fields={','.join(sorted(unresolved_response))}",
                )
            runtime_response = _runtime_mapped_required_fields(
                route_id=route_id,
                required_fields=response_fields,
                mappings=response_mapping,
            )
            if runtime_response:
                warnings.append(
                    emit_warning(
                        "W344",
                        "response_schema fields are mapped from runtime instead of outputs",
                        phase="quality",
                        action=f"ir_ref={item.id};route={route_id};fields={','.join(sorted(runtime_response))}",
                    )
                )
        _validate_io_reconciliation(
            item=item,
            io_reconciliation=io_reconciliation or {},
            outputs=outputs,
            report=report,
        )

    if _field_signature(return_outputs) != _field_signature(outputs):
        report(
            "E355",
            "steps.return.outputs does not match outputs contract",
            phase="quality",
            action=f"ir_ref={item.id}",
        )

    if target in {"fastapi_model", "nest_model"}:
        entity_payload = pseudo_struct.get("entity")
        entity_fields = []
        if isinstance(entity_payload, dict):
            entity_fields = _as_list(entity_payload.get("fields"))
        if not entity_fields or not _fields_have_minimal_semantics(entity_fields):
            report(
                "E356",
                "entity model is missing semantic fields",
                phase="quality",
                action=f"ir_ref={item.id}",
            )

    _validate_cross_links(item, pseudo_struct, symbol_ids, report)
    _validate_integration_contract(item, integration_contract or {}, report)
    _validate_merge_contract(item, merge_contract or {}, report)
    _validate_security_contract(item, security_contract or {}, io_reconciliation or {}, report)

    if strict_target:
        if not required_files:
            report(
                "E358",
                "required_files is empty for strict target",
                phase="quality",
                action=f"target={target}",
            )
        for required in required_files:
            if not required.path_pattern.strip():
                report(
                    "E358",
                    "required_files contains empty path_pattern",
                    phase="quality",
                    action=f"target={target}",
                )

    if suggested_paths and all(path.resolver_source == "fallback" for path in suggested_paths):
        best = max((path.confidence or 0.0) for path in suggested_paths)
        if best < LOW_CONFIDENCE_THRESHOLD:
            warnings.append(
                emit_warning(
                    "W343",
                    "Only fallback suggested_paths with low confidence",
                    phase="quality",
                    action=f"target={target}",
                )
            )

    return errors, warnings


def _validate_io_reconciliation(
    *,
    item: IRPlanItem,
    io_reconciliation: dict[str, Any],
    outputs: list[Any],
    report: Any,
) -> None:
    public_fields = {
        str(value).strip()
        for value in _as_list(io_reconciliation.get("public_response_fields"))
        if str(value).strip()
    }
    runtime_fields = {
        str(value).strip()
        for value in _as_list(io_reconciliation.get("runtime_bridge_fields"))
        if str(value).strip()
    }
    output_names = _field_names(outputs)
    cross_source = io_reconciliation.get("cross_source")
    command_outputs: set[str] = set()
    query_outputs: set[str] = set()
    if isinstance(cross_source, dict):
        command_outputs = {
            str(value).strip()
            for value in _as_list(cross_source.get("command_outputs"))
            if str(value).strip()
        }
        query_outputs = {
            str(value).strip()
            for value in _as_list(cross_source.get("query_outputs"))
            if str(value).strip()
        }

    unresolved_public = public_fields - output_names - runtime_fields - command_outputs - query_outputs
    if unresolved_public:
        report(
            "E401",
            "public response fields are not reconcilable across route/runtime/contracts",
            phase="quality",
            action=f"ir_ref={item.id};fields={','.join(sorted(unresolved_public))}",
        )

    if command_outputs and query_outputs and command_outputs != query_outputs:
        report(
            "E402",
            "public symbol has incompatible command/query output signatures",
            phase="quality",
            action=f"ir_ref={item.id}",
        )


def _validate_integration_contract(
    item: IRPlanItem,
    integration_contract: dict[str, Any],
    report: Any,
) -> None:
    workflow_contract = integration_contract.get("workflow_integration_contract")
    if item.type_name in {"Command", "Query"}:
        if isinstance(workflow_contract, list):
            related = item.state_contract.get("workflow_transitions", [])
            if isinstance(related, list) and related and not workflow_contract:
                report(
                    "E404",
                    "workflow transitions are present but missing integration runtime hook",
                    phase="quality",
                    action=f"ir_ref={item.id}",
                )


def _validate_merge_contract(item: IRPlanItem, merge_contract: dict[str, Any], report: Any) -> None:
    mode = str(merge_contract.get("mode", "")).strip()
    if not mode:
        report(
            "E403",
            "merge contract mode is missing",
            phase="quality",
            action=f"ir_ref={item.id}",
        )
    elif mode not in {"create", "append", "patch"}:
        report(
            "E403",
            "merge contract mode is invalid",
            phase="quality",
            action=f"ir_ref={item.id};mode={mode}",
        )


def _validate_security_contract(
    item: IRPlanItem,
    security_contract: dict[str, Any],
    io_reconciliation: dict[str, Any],
    report: Any,
) -> None:
    password_hashing = security_contract.get("password_hashing")
    required = False
    if isinstance(password_hashing, dict):
        required = bool(password_hashing.get("required"))
    if not required:
        return

    internal_fields = {
        str(value).strip()
        for value in _as_list(io_reconciliation.get("internal_fields"))
        if str(value).strip()
    }
    outputs = _field_names(_as_list(item.io_contract.get("outputs")))
    if "password_hash" not in internal_fields and "password_hash" not in outputs:
        report(
            "E405",
            "password hashing is required but no password_hash destination is mapped",
            phase="quality",
            action=f"ir_ref={item.id}",
        )


def _validate_cross_links(
    item: IRPlanItem,
    pseudo_struct: dict[str, Any],
    symbol_ids: dict[str, set[str]],
    report: Any,
) -> None:
    workflow_ids = symbol_ids.get("workflow", set())
    entity_ids = symbol_ids.get("entity", set())
    command_ids = symbol_ids.get("command", set())
    event_ids = symbol_ids.get("event", set())

    workflow_payload = pseudo_struct.get("workflow")
    if isinstance(workflow_payload, dict):
        related = _as_list(workflow_payload.get("related_transitions"))
        for transition in related:
            if not isinstance(transition, dict):
                continue
            workflow_id = str(transition.get("workflow_id", "")).strip().lower()
            if workflow_id and workflow_id not in workflow_ids:
                report("E357", "workflow_id does not resolve", "quality", f"workflow_id={workflow_id}")

    dependencies = pseudo_struct.get("dependencies")
    if isinstance(dependencies, dict):
        for dep in _as_list(dependencies.get("fetches")) + _as_list(dependencies.get("reads")):
            if not isinstance(dep, dict):
                continue
            if str(dep.get("type", "")).strip().lower() == "entity":
                dep_id = str(dep.get("id", "")).strip().lower()
                if dep_id and not _entity_ref_exists(dep_id, entity_ids):
                    report("E357", "entity dependency does not resolve", "quality", f"entity={dep_id}")

    preconditions = pseudo_struct.get("preconditions")
    if isinstance(preconditions, dict):
        for permission in _as_list(preconditions.get("permissions")):
            if not isinstance(permission, dict):
                continue
            resource = str(permission.get("resource", "")).strip().lower()
            if resource and not _entity_ref_exists(resource, entity_ids):
                report("E357", "permission resource does not resolve", "quality", f"resource={resource}")

    for step in _as_list(pseudo_struct.get("steps")):
        if not isinstance(step, dict):
            continue
        for effect in _as_list(step.get("effects")):
            if not isinstance(effect, dict):
                continue
            params = effect.get("params")
            if isinstance(params, dict):
                entity = str(params.get("entity", "")).strip().lower()
                if entity and not _entity_ref_exists(entity, entity_ids):
                    report("E357", "effect entity does not resolve", "quality", f"entity={entity}")

    if item.type_name == "Workflow" and isinstance(workflow_payload, dict):
        workflow_entity = workflow_payload.get("entity")
        if isinstance(workflow_entity, dict):
            entity_id = str(workflow_entity.get("id", "")).strip().lower()
            if entity_id and not _entity_ref_exists(entity_id, entity_ids):
                report("E357", "workflow entity does not resolve", "quality", f"entity={entity_id}")

        states = {str(state.get("id", "")).strip() for state in _as_list(workflow_payload.get("states")) if isinstance(state, dict)}
        transitions = _as_list(workflow_payload.get("transitions"))
        step_transitions = []
        for step in _as_list(pseudo_struct.get("steps")):
            if isinstance(step, dict) and step.get("type") == "state_transition":
                step_transitions.extend(_as_list(step.get("transitions")))

        if _transition_signature(transitions) != _transition_signature(step_transitions):
            report("E357", "workflow.transitions mismatch with steps.state_transition", "quality", f"ir_ref={item.id}")

        for transition in transitions:
            if not isinstance(transition, dict):
                continue
            from_state = str(transition.get("from_state", "")).strip()
            to_state = str(transition.get("to_state", "")).strip()
            if from_state and states and from_state not in states:
                report("E357", "transition from_state not in workflow.states", "quality", f"state={from_state}")
            if to_state and states and to_state not in states:
                report("E357", "transition to_state not in workflow.states", "quality", f"state={to_state}")

            on_command = transition.get("on_command")
            if isinstance(on_command, dict):
                command_id = str(on_command.get("id", "")).strip().lower()
                if command_id and command_id not in command_ids:
                    report("E357", "transition on_command does not resolve", "quality", f"command={command_id}")
            on_event = transition.get("on_event")
            if isinstance(on_event, dict):
                event_id = str(on_event.get("id", "")).strip().lower()
                if event_id and event_id not in event_ids:
                    report("E357", "transition on_event does not resolve", "quality", f"event={event_id}")


def _is_strict_target(target: str) -> bool:
    lowered = target.strip().lower()
    return any(lowered.startswith(prefix) for prefix in STRICT_TARGET_PREFIXES)


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _field_signature(fields: list[Any]) -> set[tuple[str, str, bool]]:
    signature: set[tuple[str, str, bool]] = set()
    for field in fields:
        if not isinstance(field, dict):
            continue
        name = str(field.get("name", "")).strip().lower()
        field_type = str(field.get("type", "")).strip().lower()
        required = bool(field.get("required", False))
        if name:
            signature.add((name, field_type, required))
    return signature


def _field_names(fields: list[Any]) -> set[str]:
    names: set[str] = set()
    for field in fields:
        if isinstance(field, dict):
            name = str(field.get("name", "")).strip()
            if name:
                names.add(name)
    return names


def _required_field_names(fields: list[Any]) -> set[str]:
    names: set[str] = set()
    for field in fields:
        if not isinstance(field, dict):
            continue
        name = str(field.get("name", "")).strip()
        if not name:
            continue
        if bool(field.get("required", False)):
            names.add(name)
    return names


def _unmapped_required_fields(
    *,
    route_id: str,
    required_fields: set[str],
    mappings: list[Any],
    accepted_prefixes: tuple[str, ...],
    fallback_names: set[str],
) -> set[str]:
    unresolved: set[str] = set()
    for field in required_fields:
        matched = False
        for mapping in mappings:
            if not isinstance(mapping, dict):
                continue
            if str(mapping.get("route_id", "")).strip() != route_id:
                continue
            if str(mapping.get("api_field", "")).strip() != field:
                continue
            source = str(mapping.get("source", "")).strip()
            if source.startswith(accepted_prefixes):
                matched = True
                break
        if not matched and field in fallback_names:
            matched = True
        if not matched:
            unresolved.add(field)
    return unresolved


def _runtime_mapped_required_fields(
    *,
    route_id: str,
    required_fields: set[str],
    mappings: list[Any],
) -> set[str]:
    runtime_fields: set[str] = set()
    for field in required_fields:
        for mapping in mappings:
            if not isinstance(mapping, dict):
                continue
            if str(mapping.get("route_id", "")).strip() != route_id:
                continue
            if str(mapping.get("api_field", "")).strip() != field:
                continue
            source = str(mapping.get("source", "")).strip()
            if source.startswith("runtime."):
                runtime_fields.add(field)
                break
    return runtime_fields


def _find_return_outputs(pseudo_struct: dict[str, Any]) -> list[Any]:
    for step in _as_list(pseudo_struct.get("steps")):
        if isinstance(step, dict) and step.get("type") == "return":
            return _as_list(step.get("outputs"))
    return []


def _fields_have_minimal_semantics(fields: list[Any]) -> bool:
    for field in fields:
        if not isinstance(field, dict):
            return False
        name = str(field.get("name", "")).strip()
        field_type = str(field.get("type", "")).strip()
        if not name or not field_type:
            return False
        if "required" not in field:
            return False
    return True


def _entity_ref_exists(value: str, entity_ids: set[str]) -> bool:
    value = value.strip().lower()
    if not value:
        return False
    candidates = {value}
    if value.endswith("s"):
        candidates.add(value[:-1])
    else:
        candidates.add(f"{value}s")
    return any(candidate in entity_ids for candidate in candidates)


def _transition_signature(transitions: list[Any]) -> set[tuple[str, str, str, str]]:
    signature: set[tuple[str, str, str, str]] = set()
    for transition in transitions:
        if not isinstance(transition, dict):
            continue
        from_state = str(transition.get("from_state", "")).strip()
        to_state = str(transition.get("to_state", "")).strip()
        on_command = transition.get("on_command")
        command_id = ""
        if isinstance(on_command, dict):
            command_id = str(on_command.get("id", "")).strip()
        on_event = transition.get("on_event")
        event_id = ""
        if isinstance(on_event, dict):
            event_id = str(on_event.get("id", "")).strip()
        signature.add((from_state, to_state, command_id, event_id))
    return signature
