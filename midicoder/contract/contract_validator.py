from __future__ import annotations

import difflib
import inspect
from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError

import midicoder.dsl.models as dsl_models
from midicoder.dsl.catalogs import (
    AUTH_TYPE_CATALOG,
    AWS_SERVICE_CATALOG,
    AZURE_SERVICE_CATALOG,
    CLOUD_PROVIDER_CATALOG,
    CONTRACT_TEST_STEP_TYPE_CATALOG,
    EFFECT_CATALOG,
    EMAIL_TRANSPORT_CATALOG,
    GCP_SERVICE_CATALOG,
    GUARD_CATALOG,
    INTEGRATION_TYPE_CATALOG,
    OBSERVABILITY_KIND_CATALOG,
    PERSISTENCE_ENGINE_CATALOG,
    RELIABILITY_TARGET_KIND_CATALOG,
    SECRET_PROVIDER_CATALOG,
    TEST_FRAMEWORK_CATALOG,
    TEST_KIND_CATALOG,
    WEBHOOK_SIGNATURE_ALG_CATALOG,
)
from midicoder.dsl.loader import (
    load_access_policy,
    load_commands,
    load_entities,
    load_enums,
    load_errors,
    load_events,
    load_glossary,
    load_graphql,
    load_http,
    load_info,
    load_integrations,
    load_observability,
    load_persistence,
    load_policies,
    load_profiles,
    load_projections,
    load_queries,
    load_reliability,
    load_rules,
    load_scenarios,
    load_secrets_contract,
    load_security_baseline,
    load_testing,
    load_value_objects,
    load_workflows,
)
from midicoder.dsl.models import (
    AccessPolicyFile,
    CommandsFile,
    EntitiesFile,
    EnumsFile,
    ErrorsFile,
    EventsFile,
    GlossaryFile,
    GraphQLApiFile,
    HttpApiFile,
    InfoFile,
    IntegrationsFile,
    ObservabilityFile,
    Permission,
    PersistenceModelFile,
    PoliciesFile,
    Policy,
    ProfilesFile,
    ProjectionsFile,
    QueriesFile,
    ReliabilityPoliciesFile,
    RulesFile,
    ScenariosFile,
    SecretsContractFile,
    SecurityBaselineFile,
    TestingFile,
    ValueObjectsFile,
    WorkflowsFile,
)
from midicoder.dsl.schemas.entity_model import CONSTRAINT_TYPE_CATALOG
from midicoder.dsl.schemas.named_field_model import extract_type_refs


@dataclass(frozen=True)
class ContractIssue:
    location: str
    message: str


def _validate_file(path: Path, loader) -> tuple[object | None, list[ContractIssue]]:
    issues: list[ContractIssue] = []
    if not path.exists():
        issues.append(ContractIssue(str(path), "File is missing"))
        return None, issues
    try:
        return loader(path), issues
    except ValidationError as exc:
        for error in exc.errors():
            location = ".".join(str(part) for part in error.get("loc", []))
            message = error.get("msg", "Invalid schema")
            issues.append(ContractIssue(f"{path}:{location}", message))
        return None, issues


def _collect_ids(items, location: str) -> tuple[set[str], list[ContractIssue]]:
    issues: list[ContractIssue] = []
    ids: set[str] = set()
    for item in items:
        if item.id in ids:
            issues.append(ContractIssue(location, f"Duplicate id: {item.id}"))
        else:
            ids.add(item.id)
    return ids, issues


def _format_location(path: Path, *parts: str) -> str:
    if parts:
        return f"{path}:{'.'.join(parts)}"
    return str(path)


def _lint_model_meta_graph() -> list[ContractIssue]:
    """Dynamic lint from schema metadata graph (includes/included_by)."""
    issues: list[ContractIssue] = []
    kind_to_class: dict[str, str] = {}
    kind_to_meta: dict[str, object] = {}

    for name in sorted(dir(dsl_models)):
        candidate = getattr(dsl_models, name)
        if not inspect.isclass(candidate):
            continue
        meta = getattr(candidate, "model_meta", None)
        if meta is None:
            continue
        if meta.kind in kind_to_class:
            issues.append(
                ContractIssue(
                    f"dsl/schemas:model_meta:{meta.kind}",
                    f"Duplicate model_meta kind declared by '{name}' and '{kind_to_class[meta.kind]}'",
                )
            )
            continue
        kind_to_class[meta.kind] = name
        kind_to_meta[meta.kind] = meta

    known_kinds = set(kind_to_meta.keys())
    for kind, meta in kind_to_meta.items():
        for field_name in ("includes", "included_by"):
            refs = list(getattr(meta, field_name))
            seen: set[str] = set()
            for index, ref_kind in enumerate(refs):
                location = f"dsl/schemas:model_meta:{kind}.{field_name}[{index}]"
                if ref_kind in seen:
                    issues.append(
                        ContractIssue(
                            location,
                            f"Duplicate {field_name} reference '{ref_kind}'",
                        )
                    )
                    continue
                seen.add(ref_kind)
                if ref_kind in known_kinds:
                    continue
                suggestions = difflib.get_close_matches(
                    ref_kind, sorted(known_kinds), n=1, cutoff=0.75
                )
                if suggestions:
                    issues.append(
                        ContractIssue(
                            location,
                            f"Unknown model kind '{ref_kind}' in {field_name}; did you mean '{suggestions[0]}'?",
                        )
                    )
                else:
                    issues.append(
                        ContractIssue(
                            location,
                            f"Unknown model kind '{ref_kind}' in {field_name}",
                        )
                    )
    return issues


GUARD_REQUIRED_PARAMS: dict[str, tuple[str, ...]] = {
    "auth.role": ("role",),
    "auth.permission": ("permission",),
    "exists": ("entity", "field"),
    "not_exists": ("entity", "field"),
    "state.equals": ("field", "value"),
    "state.in": ("field", "values"),
    "feature.enabled": ("flag",),
}

EFFECT_REQUIRED_PARAMS: dict[str, tuple[str, ...]] = {
    "db.insert": ("entity",),
    "db.update": ("entity",),
    "db.delete": ("entity",),
    "db.upsert": ("entity",),
    "emit.event": ("event",),
}


def _missing_params(params: dict | None, required: tuple[str, ...]) -> list[str]:
    payload = params or {}
    missing: list[str] = []
    for key in required:
        value = payload.get(key)
        if value is None:
            missing.append(key)
            continue
        if isinstance(value, str) and not value.strip():
            missing.append(key)
    return missing


def _lint_guard_ref(
    *,
    guard_id: str,
    params: dict | None,
    path: Path,
    location_prefix: str,
) -> list[ContractIssue]:
    issues: list[ContractIssue] = []
    if guard_id not in GUARD_CATALOG:
        issues.append(
            ContractIssue(
                _format_location(path, f"{location_prefix}.id"),
                f"guard '{guard_id}' is not in guard catalog",
            )
        )
        return issues

    # auth.role supports either singular role or plural roles.
    if guard_id == "auth.role":
        payload = params or {}
        if payload.get("role") is None and payload.get("roles") is None:
            issues.append(
                ContractIssue(
                    _format_location(path, f"{location_prefix}.params.role"),
                    "auth.role guard missing 'role' parameter",
                )
            )
        return issues

    # auth.permission supports either singular permission or plural permissions.
    if guard_id == "auth.permission":
        payload = params or {}
        if payload.get("permission") is None and payload.get("permissions") is None:
            issues.append(
                ContractIssue(
                    _format_location(path, f"{location_prefix}.params.permission"),
                    "auth.permission guard missing 'permission' parameter",
                )
            )
        return issues

    required = GUARD_REQUIRED_PARAMS.get(guard_id, ())
    for param in _missing_params(params, required):
        issues.append(
            ContractIssue(
                _format_location(path, f"{location_prefix}.params.{param}"),
                f"{guard_id} guard missing '{param}' parameter",
            )
        )
    return issues


def _lint_effect_ref(
    *,
    effect_id: str,
    params: dict | None,
    path: Path,
    location_prefix: str,
    event_ids: set[str],
) -> tuple[list[ContractIssue], str | None]:
    issues: list[ContractIssue] = []
    emitted_event: str | None = None
    if effect_id not in EFFECT_CATALOG:
        issues.append(
            ContractIssue(
                _format_location(path, f"{location_prefix}.id"),
                f"effect '{effect_id}' is not in effect catalog",
            )
        )
        return issues, emitted_event

    for param in _missing_params(params, EFFECT_REQUIRED_PARAMS.get(effect_id, ())):
        issues.append(
            ContractIssue(
                _format_location(path, f"{location_prefix}.params.{param}"),
                f"{effect_id} effect missing '{param}' parameter",
            )
        )

    payload = params or {}
    if effect_id == "emit.event":
        raw_event = payload.get("event")
        event_name = str(raw_event).strip() if raw_event is not None else ""
        if event_name:
            emitted_event = event_name
            if event_name not in event_ids:
                issues.append(
                    ContractIssue(
                        _format_location(path, f"{location_prefix}.params.event"),
                        f"emit.event references unknown event '{event_name}'",
                    )
                )
    if effect_id == "call.integration":
        has_target = any(
            bool(str(payload.get(key)).strip())
            for key in ("target", "integration", "service")
            if payload.get(key) is not None
        )
        if not has_target:
            issues.append(
                ContractIssue(
                    _format_location(path, f"{location_prefix}.params"),
                    "call.integration requires one of 'target', 'integration', or 'service'",
                )
            )
    return issues, emitted_event


def _lint_named_field_types(
    *,
    field_records: list[tuple[str, str]],
    entity_ids: set[str],
    value_object_ids: set[str],
    enum_ids: set[str],
) -> list[ContractIssue]:
    issues: list[ContractIssue] = []
    for location, type_expr in field_records:
        refs = extract_type_refs(type_expr)
        for kind, ref_id in refs:
            if kind == "entity":
                if ref_id not in entity_ids:
                    issues.append(
                        ContractIssue(
                            location, f"type references unknown entity '{ref_id}'"
                        )
                    )
            elif kind == "valueobject":
                if ref_id not in value_object_ids:
                    issues.append(
                        ContractIssue(
                            location, f"type references unknown value object '{ref_id}'"
                        )
                    )
            elif kind == "enum":
                if ref_id not in enum_ids:
                    issues.append(
                        ContractIssue(
                            location, f"type references unknown enum '{ref_id}'"
                        )
                    )
            elif kind == "legacy":
                if (
                    ref_id not in entity_ids
                    and ref_id not in value_object_ids
                    and ref_id not in enum_ids
                ):
                    issues.append(
                        ContractIssue(
                            location,
                            f"type legacy ref '{ref_id}' not found in entities/value_objects/enums",
                        )
                    )
    return issues


def _extract_simple_ref(raw: str | None) -> tuple[str, str]:
    if raw is None:
        return "", ""
    value = str(raw).strip()
    if ":" in value:
        return value, value.split(":", 1)[1].strip()
    return value, value


def _lint_query_references(
    queries: QueriesFile,
    queries_path: Path,
    *,
    entity_ids: set[str],
    role_ids: set[str],
    permission_ids: set[str],
    persistence_table_ids: set[str],
    datasource_ids: set[str],
) -> list[ContractIssue]:
    """Validate Query cross-references."""
    issues: list[ContractIssue] = []
    for query_index, query in enumerate(queries.queries):
        query_prefix = f"queries[{query_index}]"
        for read_index, entity_id in enumerate(query.reads):
            if entity_id not in entity_ids:
                issues.append(
                    ContractIssue(
                        _format_location(
                            queries_path,
                            f"{query_prefix}.reads[{read_index}]",
                        ),
                        f"reads references unknown entity '{entity_id}'",
                    )
                )

        for role_index, role_ref in enumerate(
            getattr(query, "required_roles", []) or []
        ):
            role_raw, role_id = _extract_simple_ref(role_ref)
            if role_id not in role_ids:
                issues.append(
                    ContractIssue(
                        _format_location(
                            queries_path,
                            f"{query_prefix}.required_roles[{role_index}]",
                        ),
                        f"required_roles references unknown role '{role_raw}'",
                    )
                )
        for perm_index, perm_ref in enumerate(
            getattr(query, "required_permissions", []) or []
        ):
            perm_raw, perm_id = _extract_simple_ref(perm_ref)
            if perm_id not in permission_ids:
                issues.append(
                    ContractIssue(
                        _format_location(
                            queries_path,
                            f"{query_prefix}.required_permissions[{perm_index}]",
                        ),
                        f"required_permissions references unknown permission '{perm_raw}'",
                    )
                )
        for table_index, table_ref in enumerate(getattr(query, "reads_from", []) or []):
            table_raw, table_id = _extract_simple_ref(table_ref)
            if table_id not in persistence_table_ids:
                issues.append(
                    ContractIssue(
                        _format_location(
                            queries_path,
                            f"{query_prefix}.reads_from[{table_index}]",
                        ),
                        f"reads_from references unknown persistence table '{table_raw}'",
                    )
                )
        datasource_ref = getattr(query, "datasource", None)
        if datasource_ref:
            ds_raw, ds_id = _extract_simple_ref(datasource_ref)
            if ds_id not in datasource_ids:
                issues.append(
                    ContractIssue(
                        _format_location(queries_path, f"{query_prefix}.datasource"),
                        f"datasource references unknown datasource '{ds_raw}'",
                    )
                )
    return issues


def _lint_command_references(
    commands: CommandsFile,
    commands_path: Path,
    *,
    entity_ids: set[str],
    value_object_ids: set[str],
    error_ids: set[str],
    event_ids: set[str],
    events_missing: bool,
    role_ids: set[str],
    permission_ids: set[str],
    persistence_table_ids: set[str],
    datasource_ids: set[str],
) -> list[ContractIssue]:
    issues: list[ContractIssue] = []
    requires_events = any(
        effect.id == "emit.event"
        for command in commands.commands
        for effect in command.effects
    )
    if events_missing and requires_events:
        issues.append(
            ContractIssue(
                str(commands_path.parent.parent / "domain" / "events.yaml"),
                "events.yaml is missing while emit.event effects are declared",
            )
        )
    for command_index, command in enumerate(commands.commands):
        command_prefix = f"commands[{command_index}]"
        for fetch_index, fetched_ref in enumerate(command.fetches):
            if fetched_ref not in entity_ids and fetched_ref not in value_object_ids:
                issues.append(
                    ContractIssue(
                        _format_location(
                            commands_path,
                            f"{command_prefix}.fetches[{fetch_index}]",
                        ),
                        f"fetches references unknown entity/value object '{fetched_ref}'",
                    )
                )
        for error_index, error_id in enumerate(command.errors):
            if error_id not in error_ids:
                issues.append(
                    ContractIssue(
                        _format_location(
                            commands_path,
                            f"{command_prefix}.errors[{error_index}]",
                        ),
                        f"errors references unknown error '{error_id}'",
                    )
                )

        for role_index, role_ref in enumerate(
            getattr(command, "required_roles", []) or []
        ):
            role_raw, role_id = _extract_simple_ref(role_ref)
            if role_id not in role_ids:
                issues.append(
                    ContractIssue(
                        _format_location(
                            commands_path,
                            f"{command_prefix}.required_roles[{role_index}]",
                        ),
                        f"required_roles references unknown role '{role_raw}'",
                    )
                )
        for perm_index, perm_ref in enumerate(
            getattr(command, "required_permissions", []) or []
        ):
            perm_raw, perm_id = _extract_simple_ref(perm_ref)
            if perm_id not in permission_ids:
                issues.append(
                    ContractIssue(
                        _format_location(
                            commands_path,
                            f"{command_prefix}.required_permissions[{perm_index}]",
                        ),
                        f"required_permissions references unknown permission '{perm_raw}'",
                    )
                )
        for table_index, table_ref in enumerate(
            getattr(command, "writes_to", []) or []
        ):
            table_raw, table_id = _extract_simple_ref(table_ref)
            if table_id not in persistence_table_ids:
                issues.append(
                    ContractIssue(
                        _format_location(
                            commands_path,
                            f"{command_prefix}.writes_to[{table_index}]",
                        ),
                        f"writes_to references unknown persistence table '{table_raw}'",
                    )
                )
        datasource_ref = getattr(command, "datasource", None)
        if datasource_ref:
            ds_raw, ds_id = _extract_simple_ref(datasource_ref)
            if ds_id not in datasource_ids:
                issues.append(
                    ContractIssue(
                        _format_location(commands_path, f"{command_prefix}.datasource"),
                        f"datasource references unknown datasource '{ds_raw}'",
                    )
                )
        for guard_index, guard in enumerate(command.guards):
            issues.extend(
                _lint_guard_ref(
                    guard_id=guard.id,
                    params=guard.params,
                    path=commands_path,
                    location_prefix=f"{command_prefix}.guards[{guard_index}]",
                )
            )

        effect_event_refs: set[str] = set()
        for effect_index, effect in enumerate(command.effects):
            effect_prefix = f"{command_prefix}.effects[{effect_index}]"
            effect_issues, emitted_event = _lint_effect_ref(
                effect_id=effect.id,
                params=effect.params,
                path=commands_path,
                location_prefix=effect_prefix,
                event_ids=event_ids,
            )
            issues.extend(effect_issues)
            if emitted_event:
                effect_event_refs.add(emitted_event)

        declared_emits: set[str] = set()
        for emit_index, event_id in enumerate(command.emits):
            if event_id not in event_ids:
                issues.append(
                    ContractIssue(
                        _format_location(
                            commands_path, f"{command_prefix}.emits[{emit_index}]"
                        ),
                        f"emits references unknown event '{event_id}'",
                    )
                )
                continue
            declared_emits.add(event_id)

        for event_id in sorted(declared_emits - effect_event_refs):
            issues.append(
                ContractIssue(
                    _format_location(commands_path, f"{command_prefix}.emits"),
                    f"event '{event_id}' is declared in emits but missing emit.event effect",
                )
            )
        for event_id in sorted(effect_event_refs - declared_emits):
            issues.append(
                ContractIssue(
                    _format_location(commands_path, f"{command_prefix}.effects"),
                    f"emit.event references '{event_id}' but command.emits does not include it",
                )
            )
    return issues


def _lint_rule_references(
    rules: RulesFile,
    rules_path: Path,
    *,
    command_ids: set[str],
    query_ids: set[str],
    workflow_ids: set[str],
    policy_ids: set[str],
    scenario_ids: set[str],
) -> list[ContractIssue]:
    issues: list[ContractIssue] = []
    target_ids_by_kind = {
        "command": command_ids,
        "query": query_ids,
        "workflow": workflow_ids,
        "policy": policy_ids,
    }
    for rule_index, rule in enumerate(rules.rules):
        scenario_ref = getattr(rule, "applies_to_scenario", None)
        if scenario_ref:
            _, scenario_id = _extract_simple_ref(scenario_ref)
            if scenario_id not in scenario_ids:
                issues.append(
                    ContractIssue(
                        _format_location(
                            rules_path, f"rules[{rule_index}].applies_to_scenario"
                        ),
                        f"applies_to_scenario references unknown scenario '{scenario_ref}'",
                    )
                )
        if not rule.applies_to:
            continue
        target_kind = "command"
        target_ref = rule.applies_to
        if ":" in rule.applies_to:
            target_kind, target_ref = [
                part.strip() for part in rule.applies_to.split(":", 1)
            ]
        elif target_ref in query_ids and target_ref not in command_ids:
            # Backward compatibility: untyped applies_to historically defaulted to command.
            # If the ref exists only as a query ID, treat it as query to avoid false negatives.
            target_kind = "query"
        ids = target_ids_by_kind.get(target_kind)
        if ids is None:
            issues.append(
                ContractIssue(
                    _format_location(rules_path, f"rules[{rule_index}].applies_to"),
                    f"applies_to has unsupported target kind '{target_kind}'",
                )
            )
            continue
        if target_ref not in ids:
            issues.append(
                ContractIssue(
                    _format_location(rules_path, f"rules[{rule_index}].applies_to"),
                    f"applies_to references unknown {target_kind} '{target_ref}'",
                )
            )
    return issues


def _lint_http_routes(
    http: HttpApiFile,
    http_path: Path,
    command_ids: set[str],
    query_ids: set[str],
) -> list[ContractIssue]:
    issues: list[ContractIssue] = []
    for route_index, route in enumerate(http.routes):
        route_prefix = f"routes[{route_index}]"
        if route.command:
            if route.command not in command_ids:
                issues.append(
                    ContractIssue(
                        _format_location(http_path, f"{route_prefix}.command"),
                        f"route references unknown command '{route.command}'",
                    )
                )
        if route.query:
            if route.query not in query_ids:
                issues.append(
                    ContractIssue(
                        _format_location(http_path, f"{route_prefix}.query"),
                        f"route references unknown query '{route.query}'",
                    )
                )
        if route.command and route.query:
            issues.append(
                ContractIssue(
                    _format_location(http_path, route_prefix),
                    "route must target exactly one of command or query",
                )
            )
        if not route.command and not route.query:
            issues.append(
                ContractIssue(
                    _format_location(http_path, route_prefix),
                    "route must define either command or query",
                )
            )
    return issues


def _lint_workflow_references(
    workflows: WorkflowsFile,
    workflows_path: Path,
    *,
    entity_ids: set[str],
    command_ids: set[str],
    event_ids: set[str],
    error_ids: set[str],
    role_ids: set[str],
    permission_ids: set[str],
    scenario_ids: set[str],
) -> list[ContractIssue]:
    """Validate Workflow cross-references."""
    issues: list[ContractIssue] = []
    for workflow_index, workflow in enumerate(workflows.workflows):
        workflow_prefix = f"workflows[{workflow_index}]"

        # Validate workflow.entity references
        if workflow.entity not in entity_ids:
            issues.append(
                ContractIssue(
                    _format_location(workflows_path, f"{workflow_prefix}.entity"),
                    f"entity references unknown entity '{workflow.entity}'",
                )
            )

        for scenario_index, scenario_ref in enumerate(
            getattr(workflow, "scenarios", []) or []
        ):
            _, scenario_id = _extract_simple_ref(scenario_ref)
            if scenario_id not in scenario_ids:
                issues.append(
                    ContractIssue(
                        _format_location(
                            workflows_path,
                            f"{workflow_prefix}.scenarios[{scenario_index}]",
                        ),
                        f"scenarios references unknown scenario '{scenario_ref}'",
                    )
                )

        # Collect state IDs for validation
        state_ids = {state.id for state in workflow.states}

        # Validate initial_state exists in states
        if workflow.initial_state not in state_ids:
            issues.append(
                ContractIssue(
                    _format_location(
                        workflows_path, f"{workflow_prefix}.initial_state"
                    ),
                    f"initial_state '{workflow.initial_state}' not found in states",
                )
            )

        # Validate transitions
        for transition_index, transition in enumerate(workflow.transitions):
            transition_prefix = f"{workflow_prefix}.transitions[{transition_index}]"

            # Validate from_state and to_state
            if transition.from_state not in state_ids:
                issues.append(
                    ContractIssue(
                        _format_location(
                            workflows_path, f"{transition_prefix}.from_state"
                        ),
                        f"from_state '{transition.from_state}' not found in states",
                    )
                )
            if transition.to_state not in state_ids:
                issues.append(
                    ContractIssue(
                        _format_location(
                            workflows_path, f"{transition_prefix}.to_state"
                        ),
                        f"to_state '{transition.to_state}' not found in states",
                    )
                )

            # Validate on_command references
            if transition.on_command and transition.on_command not in command_ids:
                issues.append(
                    ContractIssue(
                        _format_location(
                            workflows_path, f"{transition_prefix}.on_command"
                        ),
                        f"on_command references unknown command '{transition.on_command}'",
                    )
                )

            # Validate on_event references
            if transition.on_event and transition.on_event not in event_ids:
                issues.append(
                    ContractIssue(
                        _format_location(
                            workflows_path, f"{transition_prefix}.on_event"
                        ),
                        f"on_event references unknown event '{transition.on_event}'",
                    )
                )

            if bool(transition.on_command) == bool(transition.on_event):
                issues.append(
                    ContractIssue(
                        _format_location(workflows_path, transition_prefix),
                        "transition must define exactly one of on_command or on_event",
                    )
                )

            for guard_index, guard in enumerate(transition.guards):
                issues.extend(
                    _lint_guard_ref(
                        guard_id=guard.id,
                        params=guard.params,
                        path=workflows_path,
                        location_prefix=f"{transition_prefix}.guards[{guard_index}]",
                    )
                )
            for effect_index, effect in enumerate(transition.effects):
                effect_issues, _ = _lint_effect_ref(
                    effect_id=effect.id,
                    params=effect.params,
                    path=workflows_path,
                    location_prefix=f"{transition_prefix}.effects[{effect_index}]",
                    event_ids=event_ids,
                )
                issues.extend(effect_issues)

        # Validate error handlers
        for handler_index, handler in enumerate(workflow.error_handlers):
            handler_prefix = f"{workflow_prefix}.error_handlers[{handler_index}]"

            # Validate error references
            if handler.error not in error_ids:
                issues.append(
                    ContractIssue(
                        _format_location(workflows_path, f"{handler_prefix}.error"),
                        f"error references unknown error '{handler.error}'",
                    )
                )

            # Validate transition_to if present
            if handler.transition_to and handler.transition_to not in state_ids:
                issues.append(
                    ContractIssue(
                        _format_location(
                            workflows_path, f"{handler_prefix}.transition_to"
                        ),
                        f"transition_to '{handler.transition_to}' not found in states",
                    )
                )

        for role_index, role_ref in enumerate(
            getattr(workflow, "required_roles", []) or []
        ):
            role_raw, role_id = _extract_simple_ref(role_ref)
            if role_id not in role_ids:
                issues.append(
                    ContractIssue(
                        _format_location(
                            workflows_path,
                            f"{workflow_prefix}.required_roles[{role_index}]",
                        ),
                        f"required_roles references unknown role '{role_raw}'",
                    )
                )
        for perm_index, perm_ref in enumerate(
            getattr(workflow, "required_permissions", []) or []
        ):
            perm_raw, perm_id = _extract_simple_ref(perm_ref)
            if perm_id not in permission_ids:
                issues.append(
                    ContractIssue(
                        _format_location(
                            workflows_path,
                            f"{workflow_prefix}.required_permissions[{perm_index}]",
                        ),
                        f"required_permissions references unknown permission '{perm_raw}'",
                    )
                )

    return issues


def _lint_scenario_references(
    scenarios: ScenariosFile,
    scenarios_path: Path,
    *,
    command_ids: set[str],
    query_ids: set[str],
    event_ids: set[str],
) -> list[ContractIssue]:
    """Validate Scenario cross-references."""
    issues: list[ContractIssue] = []
    for scenario_index, scenario in enumerate(scenarios.scenarios):
        scenario_prefix = f"scenarios[{scenario_index}]"

        # Validate steps
        for step_index, step in enumerate(scenario.steps):
            step_prefix = f"{scenario_prefix}.steps[{step_index}]"

            # Validate step.ref based on step.type
            if step.type == "command":
                if step.ref not in command_ids:
                    issues.append(
                        ContractIssue(
                            _format_location(scenarios_path, f"{step_prefix}.ref"),
                            f"step of type 'command' references unknown command '{step.ref}'",
                        )
                    )
            elif step.type == "query":
                if step.ref not in query_ids:
                    issues.append(
                        ContractIssue(
                            _format_location(scenarios_path, f"{step_prefix}.ref"),
                            f"step of type 'query' references unknown query '{step.ref}'",
                        )
                    )
            elif step.type == "event":
                if step.ref not in event_ids:
                    issues.append(
                        ContractIssue(
                            _format_location(scenarios_path, f"{step_prefix}.ref"),
                            f"step of type 'event' references unknown event '{step.ref}'",
                        )
                    )

    return issues


def _lint_projection_references(
    projections: ProjectionsFile,
    projections_path: Path,
    *,
    event_ids: set[str],
    persistence_table_ids: set[str],
) -> list[ContractIssue]:
    """Validate Projection cross-references."""
    issues: list[ContractIssue] = []
    for projection_index, projection in enumerate(projections.projections):
        projection_prefix = f"projections[{projection_index}]"

        # Validate source_events references
        for event_index, event_id in enumerate(projection.source_events):
            if event_id not in event_ids:
                issues.append(
                    ContractIssue(
                        _format_location(
                            projections_path,
                            f"{projection_prefix}.source_events[{event_index}]",
                        ),
                        f"source_events references unknown event '{event_id}'",
                    )
                )
        if projection.storage:
            storage_ref = projection.storage
            if storage_ref.startswith("table:"):
                storage_ref = storage_ref.split(":", 1)[1].strip()
            if persistence_table_ids and storage_ref not in persistence_table_ids:
                issues.append(
                    ContractIssue(
                        _format_location(
                            projections_path, f"{projection_prefix}.storage"
                        ),
                        f"storage references unknown persistence table '{projection.storage}'",
                    )
                )
        if getattr(projection, "storage_ref", None):
            storage_raw, storage_id = _extract_simple_ref(projection.storage_ref)
            if storage_id not in persistence_table_ids:
                issues.append(
                    ContractIssue(
                        _format_location(
                            projections_path, f"{projection_prefix}.storage_ref"
                        ),
                        f"storage_ref references unknown persistence table '{storage_raw}'",
                    )
                )

    return issues


def _lint_persistence_references(
    persistence: PersistenceModelFile,
    persistence_path: Path,
    *,
    integration_ids: set[str],
    operation_ids: set[str],
) -> list[ContractIssue]:
    """Validate Persistence contract internals."""
    issues: list[ContractIssue] = []

    datasource_ids: set[str] = set()
    datasource_engines: dict[str, str] = {}
    for idx, datasource in enumerate(persistence.datasources):
        prefix = f"datasources[{idx}]"
        if datasource.id in datasource_ids:
            issues.append(
                ContractIssue(
                    _format_location(persistence_path, f"{prefix}.id"),
                    f"Duplicate datasource id: {datasource.id}",
                )
            )
        else:
            datasource_ids.add(datasource.id)
            datasource_engines[datasource.id] = datasource.engine

        if datasource.engine not in PERSISTENCE_ENGINE_CATALOG:
            issues.append(
                ContractIssue(
                    _format_location(persistence_path, f"{prefix}.engine"),
                    f"engine '{datasource.engine}' is not supported",
                )
            )
        if getattr(datasource, "integration_id", None):
            integration_raw, integration_id = _extract_simple_ref(
                datasource.integration_id
            )
            if integration_id not in integration_ids:
                issues.append(
                    ContractIssue(
                        _format_location(persistence_path, f"{prefix}.integration_id"),
                        f"integration_id references unknown integration '{integration_raw}'",
                    )
                )

    table_ids: set[str] = set()
    for table_idx, table in enumerate(persistence.tables):
        table_prefix = f"tables[{table_idx}]"
        if table.id in table_ids:
            issues.append(
                ContractIssue(
                    _format_location(persistence_path, f"{table_prefix}.id"),
                    f"Duplicate table id: {table.id}",
                )
            )
        else:
            table_ids.add(table.id)

        if table.datasource:
            if table.datasource not in datasource_ids:
                issues.append(
                    ContractIssue(
                        _format_location(
                            persistence_path, f"{table_prefix}.datasource"
                        ),
                        f"datasource '{table.datasource}' not found",
                    )
                )
        elif datasource_ids:
            issues.append(
                ContractIssue(
                    _format_location(persistence_path, f"{table_prefix}.datasource"),
                    "datasource is required when datasources are declared",
                )
            )
        if getattr(table, "operation_id", None):
            operation_raw, op_id = _extract_simple_ref(table.operation_id)
            if op_id not in operation_ids:
                issues.append(
                    ContractIssue(
                        _format_location(
                            persistence_path, f"{table_prefix}.operation_id"
                        ),
                        f"operation_id references unknown integration operation '{operation_raw}'",
                    )
                )

        field_names: set[str] = set()
        for column_idx, column in enumerate(table.columns):
            col_prefix = f"{table_prefix}.columns[{column_idx}]"
            if column.name in field_names:
                issues.append(
                    ContractIssue(
                        _format_location(persistence_path, f"{col_prefix}.name"),
                        f"Duplicate column name '{column.name}' in table '{table.id}'",
                    )
                )
            else:
                field_names.add(column.name)

        for index_idx, index in enumerate(table.indexes):
            index_prefix = f"{table_prefix}.indexes[{index_idx}]"
            for col_idx, col_name in enumerate(index.columns):
                if col_name not in field_names:
                    issues.append(
                        ContractIssue(
                            _format_location(
                                persistence_path,
                                f"{index_prefix}.columns[{col_idx}]",
                            ),
                            f"index column '{col_name}' not found in table '{table.id}'",
                        )
                    )

        engine = datasource_engines.get(table.datasource) if table.datasource else None
        if engine == "redis":
            for column_idx, column in enumerate(table.columns):
                fk = column.constraints.get("foreign_key")
                if fk is not None:
                    issues.append(
                        ContractIssue(
                            _format_location(
                                persistence_path,
                                f"{table_prefix}.columns[{column_idx}].constraints.foreign_key",
                            ),
                            "foreign_key is not supported for redis datasource",
                        )
                    )

    # Validate foreign key target table/column references
    table_column_map = {
        table.id: {column.name for column in table.columns}
        for table in persistence.tables
    }
    for table_idx, table in enumerate(persistence.tables):
        table_prefix = f"tables[{table_idx}]"
        for column_idx, column in enumerate(table.columns):
            fk = column.constraints.get("foreign_key")
            if not isinstance(fk, dict):
                continue
            ref_table = fk.get("table")
            ref_column = fk.get("column")
            if ref_table not in table_column_map:
                issues.append(
                    ContractIssue(
                        _format_location(
                            persistence_path,
                            f"{table_prefix}.columns[{column_idx}].constraints.foreign_key.table",
                        ),
                        f"foreign_key references unknown table '{ref_table}'",
                    )
                )
                continue
            if ref_column not in table_column_map.get(ref_table, set()):
                issues.append(
                    ContractIssue(
                        _format_location(
                            persistence_path,
                            f"{table_prefix}.columns[{column_idx}].constraints.foreign_key.column",
                        ),
                        f"foreign_key references unknown column '{ref_column}' on table '{ref_table}'",
                    )
                )

    return issues


def _lint_integration_references(
    integrations: IntegrationsFile,
    integrations_path: Path,
    *,
    error_ids: set[str],
    event_ids: set[str],
    secret_ids: set[str],
    operation_ids: set[str],
) -> list[ContractIssue]:
    """Validate Integrations contract internals."""
    issues: list[ContractIssue] = []

    integration_ids: set[str] = set()
    for idx, target in enumerate(integrations.integrations):
        prefix = f"integrations[{idx}]"
        if target.id in integration_ids:
            issues.append(
                ContractIssue(
                    _format_location(integrations_path, f"{prefix}.id"),
                    f"Duplicate integration id: {target.id}",
                )
            )
        else:
            integration_ids.add(target.id)

        if target.type not in INTEGRATION_TYPE_CATALOG:
            issues.append(
                ContractIssue(
                    _format_location(integrations_path, f"{prefix}.type"),
                    f"integration type '{target.type}' is not supported",
                )
            )
        if target.provider and target.provider not in CLOUD_PROVIDER_CATALOG:
            issues.append(
                ContractIssue(
                    _format_location(integrations_path, f"{prefix}.provider"),
                    f"cloud provider '{target.provider}' is not supported",
                )
            )
        if (
            target.provider == "aws"
            and target.service
            and target.service not in AWS_SERVICE_CATALOG
        ):
            issues.append(
                ContractIssue(
                    _format_location(integrations_path, f"{prefix}.service"),
                    f"AWS service '{target.service}' is not supported",
                )
            )
        if (
            target.provider == "gcp"
            and target.service
            and target.service not in GCP_SERVICE_CATALOG
        ):
            issues.append(
                ContractIssue(
                    _format_location(integrations_path, f"{prefix}.service"),
                    f"GCP service '{target.service}' is not supported",
                )
            )
        if (
            target.provider == "azure"
            and target.service
            and target.service not in AZURE_SERVICE_CATALOG
        ):
            issues.append(
                ContractIssue(
                    _format_location(integrations_path, f"{prefix}.service"),
                    f"Azure service '{target.service}' is not supported",
                )
            )
        if target.auth and target.auth.type not in AUTH_TYPE_CATALOG:
            issues.append(
                ContractIssue(
                    _format_location(integrations_path, f"{prefix}.auth.type"),
                    f"auth type '{target.auth.type}' is not supported",
                )
            )
        if target.auth and target.auth.secret_ref:
            secret_raw, secret_id = _extract_simple_ref(target.auth.secret_ref)
            if secret_id not in secret_ids:
                issues.append(
                    ContractIssue(
                        _format_location(
                            integrations_path, f"{prefix}.auth.secret_ref"
                        ),
                        f"auth.secret_ref references unknown secret '{secret_raw}'",
                    )
                )
        if (
            target.auth
            and target.auth.secret_ref
            and not _extract_simple_ref(target.auth.secret_ref)[0].startswith("Secret:")
        ):
            issues.append(
                ContractIssue(
                    _format_location(integrations_path, f"{prefix}.auth.secret_ref"),
                    "auth.secret_ref should use typed format 'Secret:<id>'",
                )
            )

    for idx, op in enumerate(integrations.operations):
        if op.integration_id not in integration_ids:
            issues.append(
                ContractIssue(
                    _format_location(
                        integrations_path, f"operations[{idx}].integration_id"
                    ),
                    f"operation references unknown integration '{op.integration_id}'",
                )
            )
        for map_index, error_map in enumerate(op.error_mapping):
            if error_map.target_error not in error_ids:
                issues.append(
                    ContractIssue(
                        _format_location(
                            integrations_path,
                            f"operations[{idx}].error_mapping[{map_index}].target_error",
                        ),
                        f"error_mapping references unknown error '{error_map.target_error}'",
                    )
                )

    for idx, s3_resource in enumerate(integrations.s3_resources):
        if s3_resource.integration_id not in integration_ids:
            issues.append(
                ContractIssue(
                    _format_location(
                        integrations_path, f"s3_resources[{idx}].integration_id"
                    ),
                    f"s3 resource references unknown integration '{s3_resource.integration_id}'",
                )
            )
        for op_index, op_ref in enumerate(s3_resource.operations):
            if op_ref not in operation_ids:
                issues.append(
                    ContractIssue(
                        _format_location(
                            integrations_path,
                            f"s3_resources[{idx}].operations[{op_index}]",
                        ),
                        f"s3 resource operation '{op_ref}' not found in operations.id",
                    )
                )

    for idx, webhook in enumerate(integrations.webhooks):
        if (
            webhook.signature
            and webhook.signature.alg not in WEBHOOK_SIGNATURE_ALG_CATALOG
        ):
            issues.append(
                ContractIssue(
                    _format_location(
                        integrations_path, f"webhooks[{idx}].signature.alg"
                    ),
                    f"signature algorithm '{webhook.signature.alg}' is not supported",
                )
            )
        if webhook.signature:
            secret_raw, secret_id = _extract_simple_ref(webhook.signature.secret_ref)
            if secret_id not in secret_ids:
                issues.append(
                    ContractIssue(
                        _format_location(
                            integrations_path, f"webhooks[{idx}].signature.secret_ref"
                        ),
                        f"signature.secret_ref references unknown secret '{secret_raw}'",
                    )
                )
            if not secret_raw.startswith("Secret:"):
                issues.append(
                    ContractIssue(
                        _format_location(
                            integrations_path, f"webhooks[{idx}].signature.secret_ref"
                        ),
                        "signature.secret_ref should use typed format 'Secret:<id>'",
                    )
                )
        for event_index, event_id in enumerate(webhook.events):
            if event_id not in event_ids:
                issues.append(
                    ContractIssue(
                        _format_location(
                            integrations_path, f"webhooks[{idx}].events[{event_index}]"
                        ),
                        f"webhook event references unknown event '{event_id}'",
                    )
                )

    for idx, email_provider in enumerate(integrations.email_providers):
        if email_provider.transport not in EMAIL_TRANSPORT_CATALOG:
            issues.append(
                ContractIssue(
                    _format_location(
                        integrations_path, f"email_providers[{idx}].transport"
                    ),
                    f"email transport '{email_provider.transport}' is not supported",
                )
            )
        if email_provider.username_secret:
            secret_raw, secret_id = _extract_simple_ref(email_provider.username_secret)
            if secret_id not in secret_ids:
                issues.append(
                    ContractIssue(
                        _format_location(
                            integrations_path, f"email_providers[{idx}].username_secret"
                        ),
                        f"username_secret references unknown secret '{secret_raw}'",
                    )
                )
            if not secret_raw.startswith("Secret:"):
                issues.append(
                    ContractIssue(
                        _format_location(
                            integrations_path, f"email_providers[{idx}].username_secret"
                        ),
                        "username_secret should use typed format 'Secret:<id>'",
                    )
                )
        if email_provider.password_secret:
            secret_raw, secret_id = _extract_simple_ref(email_provider.password_secret)
            if secret_id not in secret_ids:
                issues.append(
                    ContractIssue(
                        _format_location(
                            integrations_path, f"email_providers[{idx}].password_secret"
                        ),
                        f"password_secret references unknown secret '{secret_raw}'",
                    )
                )
            if not secret_raw.startswith("Secret:"):
                issues.append(
                    ContractIssue(
                        _format_location(
                            integrations_path, f"email_providers[{idx}].password_secret"
                        ),
                        "password_secret should use typed format 'Secret:<id>'",
                    )
                )

    for idx, oauth_provider in enumerate(integrations.oauth2_providers):
        if oauth_provider.client_id_secret:
            secret_raw, secret_id = _extract_simple_ref(oauth_provider.client_id_secret)
            if secret_id not in secret_ids:
                issues.append(
                    ContractIssue(
                        _format_location(
                            integrations_path,
                            f"oauth2_providers[{idx}].client_id_secret",
                        ),
                        f"client_id_secret references unknown secret '{secret_raw}'",
                    )
                )
            if not secret_raw.startswith("Secret:"):
                issues.append(
                    ContractIssue(
                        _format_location(
                            integrations_path,
                            f"oauth2_providers[{idx}].client_id_secret",
                        ),
                        "client_id_secret should use typed format 'Secret:<id>'",
                    )
                )
        if oauth_provider.client_secret_secret:
            secret_raw, secret_id = _extract_simple_ref(
                oauth_provider.client_secret_secret
            )
            if secret_id not in secret_ids:
                issues.append(
                    ContractIssue(
                        _format_location(
                            integrations_path,
                            f"oauth2_providers[{idx}].client_secret_secret",
                        ),
                        f"client_secret_secret references unknown secret '{secret_raw}'",
                    )
                )
            if not secret_raw.startswith("Secret:"):
                issues.append(
                    ContractIssue(
                        _format_location(
                            integrations_path,
                            f"oauth2_providers[{idx}].client_secret_secret",
                        ),
                        "client_secret_secret should use typed format 'Secret:<id>'",
                    )
                )

    return issues


def _lint_integration_effect_references(
    *,
    commands: CommandsFile,
    commands_path: Path,
    workflows: WorkflowsFile | None,
    workflows_path: Path,
    integration_ids: set[str],
    operation_ids: set[str],
) -> list[ContractIssue]:
    """Validate call.integration refs from command/workflow effects."""
    issues: list[ContractIssue] = []

    for command_idx, command in enumerate(commands.commands):
        prefix = f"commands[{command_idx}]"
        for effect_idx, effect in enumerate(command.effects):
            if effect.id != "call.integration":
                continue
            effect_prefix = f"{prefix}.effects[{effect_idx}].params"
            params = effect.params or {}
            target = (
                params.get("target")
                or params.get("integration")
                or params.get("service")
            )
            operation_id = params.get("operation_id")
            if target:
                target_raw, target_id = _extract_simple_ref(str(target))
            else:
                target_raw, target_id = "", ""
            if target_id and target_id not in integration_ids:
                issues.append(
                    ContractIssue(
                        _format_location(commands_path, f"{effect_prefix}.target"),
                        f"call.integration target '{target_raw}' not found",
                    )
                )
            if operation_id:
                op_raw, op_id = _extract_simple_ref(str(operation_id))
            else:
                op_raw, op_id = "", ""
            if op_id and op_id not in operation_ids:
                issues.append(
                    ContractIssue(
                        _format_location(
                            commands_path, f"{effect_prefix}.operation_id"
                        ),
                        f"call.integration operation_id '{op_raw}' not found",
                    )
                )

    if not isinstance(workflows, WorkflowsFile):
        return issues

    for workflow_idx, workflow in enumerate(workflows.workflows):
        workflow_prefix = f"workflows[{workflow_idx}]"
        for transition_idx, transition in enumerate(workflow.transitions):
            trans_prefix = f"{workflow_prefix}.transitions[{transition_idx}]"
            for effect_idx, effect in enumerate(transition.effects):
                if effect.id != "call.integration":
                    continue
                effect_prefix = f"{trans_prefix}.effects[{effect_idx}].params"
                params = effect.params or {}
                target = (
                    params.get("target")
                    or params.get("integration")
                    or params.get("service")
                )
                operation_id = params.get("operation_id")
                if target:
                    target_raw, target_id = _extract_simple_ref(str(target))
                else:
                    target_raw, target_id = "", ""
                if target_id and target_id not in integration_ids:
                    issues.append(
                        ContractIssue(
                            _format_location(workflows_path, f"{effect_prefix}.target"),
                            f"call.integration target '{target_raw}' not found",
                        )
                    )
                if operation_id:
                    op_raw, op_id = _extract_simple_ref(str(operation_id))
                else:
                    op_raw, op_id = "", ""
                if op_id and op_id not in operation_ids:
                    issues.append(
                        ContractIssue(
                            _format_location(
                                workflows_path, f"{effect_prefix}.operation_id"
                            ),
                            f"call.integration operation_id '{op_raw}' not found",
                        )
                    )

    return issues


def _lint_profiles_contract(
    profiles: ProfilesFile, profiles_path: Path
) -> list[ContractIssue]:
    issues: list[ContractIssue] = []
    seen: set[str] = set()
    for idx, profile in enumerate(profiles.profiles):
        prefix = f"profiles[{idx}]"
        if profile.name in seen:
            issues.append(
                ContractIssue(
                    _format_location(profiles_path, f"{prefix}.name"),
                    f"Duplicate profile name '{profile.name}'",
                )
            )
        else:
            seen.add(profile.name)
    return issues


def _lint_secrets_contract(
    secrets: SecretsContractFile, secrets_path: Path
) -> list[ContractIssue]:
    issues: list[ContractIssue] = []
    seen: set[str] = set()
    for idx, secret in enumerate(secrets.secrets):
        prefix = f"secrets[{idx}]"
        if secret.id in seen:
            issues.append(
                ContractIssue(
                    _format_location(secrets_path, f"{prefix}.id"),
                    f"Duplicate secret id '{secret.id}'",
                )
            )
        else:
            seen.add(secret.id)
        if secret.provider not in SECRET_PROVIDER_CATALOG:
            issues.append(
                ContractIssue(
                    _format_location(secrets_path, f"{prefix}.provider"),
                    f"Unknown secret provider '{secret.provider}'",
                )
            )
    return issues


def _lint_reliability_contract(
    reliability: ReliabilityPoliciesFile,
    reliability_path: Path,
    *,
    command_ids: set[str],
    workflow_ids: set[str],
    integration_ids: set[str],
    integration_operation_ids: set[str],
) -> list[ContractIssue]:
    issues: list[ContractIssue] = []
    for idx, policy in enumerate(reliability.reliability_policies):
        prefix = f"reliability_policies[{idx}]"
        if policy.target_kind not in RELIABILITY_TARGET_KIND_CATALOG:
            issues.append(
                ContractIssue(
                    _format_location(reliability_path, f"{prefix}.target_kind"),
                    f"Unknown target_kind '{policy.target_kind}'",
                )
            )
            continue

        if policy.target_kind == "command" and policy.target_ref not in command_ids:
            issues.append(
                ContractIssue(
                    _format_location(reliability_path, f"{prefix}.target_ref"),
                    f"Unknown command target_ref '{policy.target_ref}'",
                )
            )
        elif policy.target_kind == "workflow" and policy.target_ref not in workflow_ids:
            issues.append(
                ContractIssue(
                    _format_location(reliability_path, f"{prefix}.target_ref"),
                    f"Unknown workflow target_ref '{policy.target_ref}'",
                )
            )
        elif (
            policy.target_kind == "integration"
            and policy.target_ref not in integration_ids
        ):
            issues.append(
                ContractIssue(
                    _format_location(reliability_path, f"{prefix}.target_ref"),
                    f"Unknown integration target_ref '{policy.target_ref}'",
                )
            )
        elif (
            policy.target_kind == "integration_operation"
            and policy.target_ref not in integration_operation_ids
        ):
            issues.append(
                ContractIssue(
                    _format_location(reliability_path, f"{prefix}.target_ref"),
                    f"Unknown integration operation target_ref '{policy.target_ref}'",
                )
            )
    return issues


def _lint_testing_contract(
    testing: TestingFile,
    testing_path: Path,
    *,
    command_ids: set[str],
    query_ids: set[str],
    event_ids: set[str],
    scenario_ids: set[str],
) -> list[ContractIssue]:
    issues: list[ContractIssue] = []
    for test_idx, test in enumerate(testing.tests):
        test_prefix = f"tests[{test_idx}]"
        if test.kind not in TEST_KIND_CATALOG:
            issues.append(
                ContractIssue(
                    _format_location(testing_path, f"{test_prefix}.kind"),
                    f"Unknown test kind '{test.kind}'",
                )
            )
        if test.framework and test.framework not in TEST_FRAMEWORK_CATALOG:
            issues.append(
                ContractIssue(
                    _format_location(testing_path, f"{test_prefix}.framework"),
                    f"Unknown test framework '{test.framework}'",
                )
            )
        if test.framework in {"pytest", "jest"} and test.kind != "unit":
            issues.append(
                ContractIssue(
                    _format_location(testing_path, f"{test_prefix}.kind"),
                    f"{test.framework} is restricted to unit tests for coverage",
                )
            )
        if test.framework == "selenium" and test.kind != "e2e":
            issues.append(
                ContractIssue(
                    _format_location(testing_path, f"{test_prefix}.kind"),
                    "selenium should be used with e2e tests",
                )
            )
        for step_idx, step in enumerate(test.steps):
            step_prefix = f"{test_prefix}.steps[{step_idx}]"
            if step.type not in CONTRACT_TEST_STEP_TYPE_CATALOG:
                issues.append(
                    ContractIssue(
                        _format_location(testing_path, f"{step_prefix}.type"),
                        f"Unknown step type '{step.type}'",
                    )
                )
                continue
            if step.type == "command" and step.ref not in command_ids:
                issues.append(
                    ContractIssue(
                        _format_location(testing_path, f"{step_prefix}.ref"),
                        f"step references unknown command '{step.ref}'",
                    )
                )
            elif step.type == "query" and step.ref not in query_ids:
                issues.append(
                    ContractIssue(
                        _format_location(testing_path, f"{step_prefix}.ref"),
                        f"step references unknown query '{step.ref}'",
                    )
                )
            elif step.type == "event" and step.ref not in event_ids:
                issues.append(
                    ContractIssue(
                        _format_location(testing_path, f"{step_prefix}.ref"),
                        f"step references unknown event '{step.ref}'",
                    )
                )
        scenario_ref = getattr(test, "scenario", None)
        if scenario_ref:
            _, scenario_id = _extract_simple_ref(scenario_ref)
            if scenario_id not in scenario_ids:
                issues.append(
                    ContractIssue(
                        _format_location(testing_path, f"{test_prefix}.scenario"),
                        f"scenario references unknown scenario '{scenario_ref}'",
                    )
                )
    return issues


def _lint_observability_contract(
    observability: ObservabilityFile,
    observability_path: Path,
    *,
    command_ids: set[str],
    workflow_ids: set[str],
    integration_ids: set[str],
    integration_operation_ids: set[str],
    persistence_table_ids: set[str],
    datasource_ids: set[str],
) -> list[ContractIssue]:
    issues: list[ContractIssue] = []
    for idx, target in enumerate(observability.observability):
        prefix = f"observability[{idx}]"
        if target.kind not in OBSERVABILITY_KIND_CATALOG:
            issues.append(
                ContractIssue(
                    _format_location(observability_path, f"{prefix}.kind"),
                    f"Unknown observability kind '{target.kind}'",
                )
            )
            continue
        if target.kind == "command":
            if target.ref not in command_ids:
                issues.append(
                    ContractIssue(
                        _format_location(observability_path, f"{prefix}.ref"),
                        f"observability references unknown command '{target.ref}'",
                    )
                )
        elif target.kind == "workflow":
            if target.ref not in workflow_ids:
                issues.append(
                    ContractIssue(
                        _format_location(observability_path, f"{prefix}.ref"),
                        f"observability references unknown workflow '{target.ref}'",
                    )
                )
        elif target.kind == "integration":
            if target.ref not in integration_ids:
                issues.append(
                    ContractIssue(
                        _format_location(observability_path, f"{prefix}.ref"),
                        f"observability references unknown integration '{target.ref}'",
                    )
                )
        elif target.kind == "integration_operation":
            if target.ref not in integration_operation_ids:
                issues.append(
                    ContractIssue(
                        _format_location(observability_path, f"{prefix}.ref"),
                        f"observability references unknown integration operation '{target.ref}'",
                    )
                )
        elif target.kind == "persistence.table":
            if target.ref not in persistence_table_ids:
                issues.append(
                    ContractIssue(
                        _format_location(observability_path, f"{prefix}.ref"),
                        f"observability references unknown persistence table '{target.ref}'",
                    )
                )
        elif target.kind == "persistence.datasource":
            if target.ref not in datasource_ids:
                issues.append(
                    ContractIssue(
                        _format_location(observability_path, f"{prefix}.ref"),
                        f"observability references unknown datasource '{target.ref}'",
                    )
                )
    return issues


def _lint_entity_constraints(
    entities: EntitiesFile,
    entities_path: Path,
    *,
    entity_ids: set[str],
) -> list[ContractIssue]:
    """Validate Entity constraints and indexes."""
    issues: list[ContractIssue] = []

    for entity_index, entity in enumerate(entities.entities):
        entity_prefix = f"entities[{entity_index}]"

        # Collect field names for validation
        field_names = {field.name for field in entity.fields}

        # Validate primary_key exists in fields
        if entity.primary_key and entity.primary_key not in field_names:
            issues.append(
                ContractIssue(
                    _format_location(entities_path, f"{entity_prefix}.primary_key"),
                    f"primary_key '{entity.primary_key}' not found in entity fields",
                )
            )

        # Validate indexes
        for index_index, index in enumerate(entity.indexes):
            index_prefix = f"{entity_prefix}.indexes[{index_index}]"

            # Validate index.fields exist in entity.fields
            for field_index, field_name in enumerate(index.fields):
                if field_name not in field_names:
                    issues.append(
                        ContractIssue(
                            _format_location(
                                entities_path,
                                f"{index_prefix}.fields[{field_index}]",
                            ),
                            f"index field '{field_name}' not found in entity fields",
                        )
                    )

        # Validate constraints
        for constraint_index, constraint in enumerate(entity.constraints):
            constraint_prefix = f"{entity_prefix}.constraints[{constraint_index}]"

            # Validate constraint.type is in catalog
            if constraint.type not in CONSTRAINT_TYPE_CATALOG:
                issues.append(
                    ContractIssue(
                        _format_location(entities_path, f"{constraint_prefix}.type"),
                        f"constraint type '{constraint.type}' not in CONSTRAINT_TYPE_CATALOG",
                    )
                )

            # Validate constraint.fields exist in entity.fields
            for field_index, field_name in enumerate(constraint.fields):
                if field_name not in field_names:
                    issues.append(
                        ContractIssue(
                            _format_location(
                                entities_path,
                                f"{constraint_prefix}.fields[{field_index}]",
                            ),
                            f"constraint field '{field_name}' not found in entity fields",
                        )
                    )

            # Validate foreign_key constraint.ref references valid entity
            # Support both formats: "EntityName" and "EntityName.fieldName"
            if constraint.type == "foreign_key" and constraint.ref:
                ref_entity = constraint.ref.split(".")[
                    0
                ]  # Extract entity name before dot
                if ref_entity not in entity_ids:
                    issues.append(
                        ContractIssue(
                            _format_location(entities_path, f"{constraint_prefix}.ref"),
                            f"foreign_key constraint references unknown entity '{ref_entity}' in '{constraint.ref}'",
                        )
                    )
                # Optional: Validate field name if specified
                elif "." in constraint.ref:
                    _, ref_field = constraint.ref.split(".", 1)
                    # Find the referenced entity and check if field exists
                    for ref_entity_obj in entities.entities:
                        if ref_entity_obj.id == ref_entity:
                            ref_field_names = {
                                field.name for field in ref_entity_obj.fields
                            }
                            if ref_field not in ref_field_names:
                                issues.append(
                                    ContractIssue(
                                        _format_location(
                                            entities_path, f"{constraint_prefix}.ref"
                                        ),
                                        f"foreign_key constraint references unknown field '{ref_field}' in entity '{ref_entity}'",
                                    )
                                )
                            break

    return issues


def _lint_graphql_references(
    graphql: GraphQLApiFile,
    graphql_path: Path,
    *,
    command_ids: set[str],
    query_ids: set[str],
) -> list[ContractIssue]:
    """Validate GraphQL API cross-references."""
    issues: list[ContractIssue] = []

    # Validate GraphQL queries
    for query_index, query_field in enumerate(graphql.api.queries):
        query_prefix = f"api.queries[{query_index}]"

        # GraphQL query resolver should reference a Query ID
        if query_field.resolver not in query_ids:
            issues.append(
                ContractIssue(
                    _format_location(graphql_path, f"{query_prefix}.resolver"),
                    f"resolver references unknown query '{query_field.resolver}'",
                )
            )

    # Validate GraphQL mutations
    for mutation_index, mutation_field in enumerate(graphql.api.mutations):
        mutation_prefix = f"api.mutations[{mutation_index}]"

        # GraphQL mutation resolver should reference a Command ID
        if mutation_field.resolver not in command_ids:
            issues.append(
                ContractIssue(
                    _format_location(graphql_path, f"{mutation_prefix}.resolver"),
                    f"resolver references unknown command '{mutation_field.resolver}'",
                )
            )

    return issues


def _lint_access_policy_references(
    access_policy: AccessPolicyFile,
    access_policy_path: Path,
    *,
    entity_ids: set[str],
    command_ids: set[str],
    query_ids: set[str],
    projection_ids: set[str],
) -> list[ContractIssue]:
    """Validate AccessPolicy cross-references."""
    issues: list[ContractIssue] = []

    # Collect role and permission IDs for cross-validation
    role_ids = {role.id for role in access_policy.access.roles}
    permission_ids = {permission.id for permission in access_policy.access.permissions}

    # Check for duplicate role IDs
    seen_roles: set[str] = set()
    for role_index, role in enumerate(access_policy.access.roles):
        if role.id in seen_roles:
            issues.append(
                ContractIssue(
                    _format_location(
                        access_policy_path, f"access.roles[{role_index}].id"
                    ),
                    f"Duplicate role id: {role.id}",
                )
            )
        seen_roles.add(role.id)

    # Check for duplicate permission IDs
    seen_permissions: set[str] = set()
    for permission_index, permission in enumerate(access_policy.access.permissions):
        if permission.id in seen_permissions:
            issues.append(
                ContractIssue(
                    _format_location(
                        access_policy_path, f"access.permissions[{permission_index}].id"
                    ),
                    f"Duplicate permission id: {permission.id}",
                )
            )
        seen_permissions.add(permission.id)

        if permission.resource and ":" in permission.resource:
            resource_kind, resource_ref = [
                part.strip() for part in permission.resource.split(":", 1)
            ]
            target_catalog: set[str] | None
            if resource_kind == "entity":
                target_catalog = entity_ids
            elif resource_kind == "command":
                target_catalog = command_ids
            elif resource_kind == "query":
                target_catalog = query_ids
            elif resource_kind == "api":
                target_catalog = command_ids | query_ids
            elif resource_kind == "projection":
                target_catalog = projection_ids
            elif resource_kind in {"document"}:
                target_catalog = None
            else:
                issues.append(
                    ContractIssue(
                        _format_location(
                            access_policy_path,
                            f"access.permissions[{permission_index}].resource",
                        ),
                        f"resource kind '{resource_kind}' is not supported",
                    )
                )
                target_catalog = None
            if target_catalog is not None and resource_ref not in target_catalog:
                issues.append(
                    ContractIssue(
                        _format_location(
                            access_policy_path,
                            f"access.permissions[{permission_index}].resource",
                        ),
                        f"resource '{permission.resource}' references unknown target '{resource_ref}'",
                    )
                )

    # Validate bindings
    for binding_index, binding in enumerate(access_policy.access.bindings):
        binding_prefix = f"access.bindings[{binding_index}]"

        # Validate binding.role references
        if binding.role not in role_ids:
            issues.append(
                ContractIssue(
                    _format_location(access_policy_path, f"{binding_prefix}.role"),
                    f"role references unknown role '{binding.role}'",
                )
            )

        # Validate binding.permissions references
        for perm_index, perm_id in enumerate(binding.permissions):
            if perm_id not in permission_ids:
                issues.append(
                    ContractIssue(
                        _format_location(
                            access_policy_path,
                            f"{binding_prefix}.permissions[{perm_index}]",
                        ),
                        f"permissions references unknown permission '{perm_id}'",
                    )
                )

    return issues


def _lint_policy_references(
    policies: PoliciesFile,
    policy_path: Path,
    *,
    entity_field_map: dict[str, set[str]],
    command_ids: set[str],
    query_ids: set[str],
    workflow_ids: set[str],
    projection_ids: set[str],
    integration_ids: set[str],
) -> list[ContractIssue]:
    issues: list[ContractIssue] = []
    scope_catalog: dict[str, set[str]] = {
        "entity": set(entity_field_map.keys()),
        "command": command_ids,
        "query": query_ids,
        "workflow": workflow_ids,
        "projection": projection_ids,
        "integration": integration_ids,
    }

    # Common computed/runtime fields that may not be in entity schema but valid in policies
    RUNTIME_FIELDS = {
        "file_size",
        "access_method",
        "request_ip",
        "request_time",
        "session_id",
        "user_agent",
        "referrer",
        "content_type",
        "content_length",
        "upload_size",
        "download_count",
        "access_count",
        "last_accessed_at",
        "computed_hash",
        "checksum",
        "mime_type",
        "file_extension",
        "storage_size",
        "cache_status",
        "is_complete",
    }

    for policy_index, policy in enumerate(policies.policies):
        policy_prefix = f"policies[{policy_index}]"
        scope = policy.scope.strip()
        if scope.lower() == "global":
            continue
        if ":" not in scope:
            issues.append(
                ContractIssue(
                    _format_location(policy_path, f"{policy_prefix}.scope"),
                    "scope must use 'kind:ref' format (e.g. entity:User or command:CreateUser)",
                )
            )
            continue
        raw_kind, scope_ref = [part.strip() for part in scope.split(":", 1)]
        scope_kind = raw_kind.lower()
        target_ids = scope_catalog.get(scope_kind)
        if target_ids is None:
            issues.append(
                ContractIssue(
                    _format_location(policy_path, f"{policy_prefix}.scope"),
                    f"scope kind '{raw_kind}' is not supported",
                )
            )
            continue
        if scope_ref not in target_ids:
            issues.append(
                ContractIssue(
                    _format_location(policy_path, f"{policy_prefix}.scope"),
                    f"scope references unknown {scope_kind} '{scope_ref}'",
                )
            )
            continue

        if scope_kind == "entity":
            known_fields = entity_field_map.get(scope_ref, set())
            for condition_index, condition in enumerate(policy.conditions):
                # Skip nested fields (with dots)
                if "." in condition.field:
                    continue

                # Check if field exists in entity schema
                if condition.field not in known_fields:
                    # Allow common runtime/computed fields without error
                    if condition.field in RUNTIME_FIELDS:
                        # This is acceptable - runtime field used in policy
                        continue

                    # Otherwise report as error
                    issues.append(
                        ContractIssue(
                            _format_location(
                                policy_path,
                                f"{policy_prefix}.conditions[{condition_index}].field",
                            ),
                            f"condition.field '{condition.field}' is not a field of entity '{scope_ref}' (hint: add to entity schema or verify spelling)",
                        )
                    )
    return issues


def _collect_named_field_records(
    *,
    entities: EntitiesFile,
    events: EventsFile | None,
    commands: CommandsFile,
    queries: QueriesFile,
    projections_files: list[tuple[Path, ProjectionsFile]],
    http: HttpApiFile | None,
    graphql: GraphQLApiFile | None,
    integrations: IntegrationsFile | None,
    value_objects: ValueObjectsFile | None,
) -> list[tuple[str, str]]:
    records: list[tuple[str, str]] = []

    for entity_index, entity in enumerate(entities.entities):
        for field_index, field in enumerate(entity.fields):
            records.append(
                (
                    f"domain/entities.yaml:entities[{entity_index}].fields[{field_index}].type",
                    field.type,
                )
            )

    if isinstance(value_objects, ValueObjectsFile):
        for vo_index, value_object in enumerate(value_objects.value_objects):
            for field_index, field in enumerate(value_object.fields):
                records.append(
                    (
                        f"domain/value_objects.yaml:value_objects[{vo_index}].fields[{field_index}].type",
                        field.type,
                    )
                )

    if isinstance(events, EventsFile):
        for event_index, event in enumerate(events.events):
            for field_index, field in enumerate(event.payload):
                records.append(
                    (
                        f"domain/events.yaml:events[{event_index}].payload[{field_index}].type",
                        field.type,
                    )
                )

    for command_index, command in enumerate(commands.commands):
        for field_index, field in enumerate(command.input):
            records.append(
                (
                    f"app/commands.yaml:commands[{command_index}].input[{field_index}].type",
                    field.type,
                )
            )
        for field_index, field in enumerate(command.returns):
            records.append(
                (
                    f"app/commands.yaml:commands[{command_index}].returns[{field_index}].type",
                    field.type,
                )
            )

    for query_index, query in enumerate(queries.queries):
        for field_index, field in enumerate(query.input):
            records.append(
                (
                    f"app/queries.yaml:queries[{query_index}].input[{field_index}].type",
                    field.type,
                )
            )
        for field_index, field in enumerate(query.returns):
            records.append(
                (
                    f"app/queries.yaml:queries[{query_index}].returns[{field_index}].type",
                    field.type,
                )
            )

    for projection_path, projections in projections_files:
        for projection_index, projection in enumerate(projections.projections):
            for field_index, field in enumerate(projection.fields):
                records.append(
                    (
                        _format_location(
                            projection_path,
                            f"projections[{projection_index}].fields[{field_index}].type",
                        ),
                        field.type,
                    )
                )

    if isinstance(http, HttpApiFile):
        for route_index, route in enumerate(http.routes):
            for field_index, field in enumerate(route.request_schema or []):
                records.append(
                    (
                        f"api/http.yaml:routes[{route_index}].request_schema[{field_index}].type",
                        field.type,
                    )
                )
            for field_index, field in enumerate(route.response_schema or []):
                records.append(
                    (
                        f"api/http.yaml:routes[{route_index}].response_schema[{field_index}].type",
                        field.type,
                    )
                )

    if isinstance(graphql, GraphQLApiFile):
        for type_index, gql_type in enumerate(graphql.api.types):
            for field_index, field in enumerate(gql_type.fields):
                records.append(
                    (
                        f"api/graphql.yaml:api.types[{type_index}].fields[{field_index}].type",
                        field.type,
                    )
                )
        for query_index, gql_query in enumerate(graphql.api.queries):
            for arg_index, arg in enumerate(gql_query.args):
                records.append(
                    (
                        f"api/graphql.yaml:api.queries[{query_index}].args[{arg_index}].type",
                        arg.type,
                    )
                )
            for ret_index, ret in enumerate(gql_query.returns):
                records.append(
                    (
                        f"api/graphql.yaml:api.queries[{query_index}].returns[{ret_index}].type",
                        ret.type,
                    )
                )
        for mutation_index, gql_mutation in enumerate(graphql.api.mutations):
            for arg_index, arg in enumerate(gql_mutation.args):
                records.append(
                    (
                        f"api/graphql.yaml:api.mutations[{mutation_index}].args[{arg_index}].type",
                        arg.type,
                    )
                )
            for ret_index, ret in enumerate(gql_mutation.returns):
                records.append(
                    (
                        f"api/graphql.yaml:api.mutations[{mutation_index}].returns[{ret_index}].type",
                        ret.type,
                    )
                )

    if isinstance(integrations, IntegrationsFile):
        for op_index, operation in enumerate(integrations.operations):
            for req_index, req in enumerate(operation.request_schema):
                records.append(
                    (
                        f"integrations/integrations.yaml:operations[{op_index}].request_schema[{req_index}].type",
                        req.type,
                    )
                )
            for resp_index, resp in enumerate(operation.response_schema):
                records.append(
                    (
                        f"integrations/integrations.yaml:operations[{op_index}].response_schema[{resp_index}].type",
                        resp.type,
                    )
                )
    return records


def check_contract(detail_path: Path) -> list[ContractIssue]:
    issues: list[ContractIssue] = []
    detail_path = detail_path.resolve()
    issues.extend(_lint_model_meta_graph())

    # Core contract files
    info_file = detail_path / "meta" / "info.yaml"
    glossary_file = detail_path / "glossary.yaml"
    entities_file = detail_path / "domain" / "entities.yaml"
    value_objects_file = detail_path / "domain" / "value_objects.yaml"
    enums_file = detail_path / "domain" / "enums.yaml"
    errors_file = detail_path / "domain" / "errors.yaml"
    events_file = detail_path / "domain" / "events.yaml"
    commands_file = detail_path / "app" / "commands.yaml"
    queries_file = detail_path / "app" / "queries.yaml"
    http_file = detail_path / "api" / "http.yaml"
    rules_dir = detail_path / "rules"

    # Extended contract files (optional)
    workflows_file = detail_path / "workflows" / "workflows.yaml"
    scenarios_file = detail_path / "scenarios" / "scenarios.yaml"
    projections_dir = detail_path / "projections"
    policies_dir = detail_path / "policy"
    access_policy_file = detail_path / "policy" / "rbac.yaml"
    graphql_file = detail_path / "api" / "graphql.yaml"
    persistence_file = detail_path / "persistence" / "model.yaml"
    integrations_file = detail_path / "integrations" / "integrations.yaml"
    profiles_file = detail_path / "meta" / "profiles.yaml"
    secrets_file = detail_path / "meta" / "secrets.yaml"
    security_file = detail_path / "policy" / "security.yaml"
    reliability_file = detail_path / "policy" / "reliability.yaml"
    observability_file = detail_path / "ops" / "observability.yaml"
    testing_file = detail_path / "testing" / "tests.yaml"

    # Validate new core files (info and glossary)
    info, info_issues = _validate_file(info_file, load_info)
    issues.extend(info_issues)
    glossary, glossary_issues = _validate_file(glossary_file, load_glossary)
    issues.extend(glossary_issues)

    # Validate existing files
    entities, entity_issues = _validate_file(entities_file, load_entities)
    issues.extend(entity_issues)
    value_objects: ValueObjectsFile | None = None
    if value_objects_file.exists():
        value_objects, value_object_issues = _validate_file(
            value_objects_file, load_value_objects
        )
        issues.extend(value_object_issues)
    enums: EnumsFile | None = None
    if enums_file.exists():
        enums, enum_issues = _validate_file(enums_file, load_enums)
        issues.extend(enum_issues)
    errors, error_issues = _validate_file(errors_file, load_errors)
    issues.extend(error_issues)
    events: EventsFile | None = None
    events_missing = not events_file.exists()
    if events_file.exists():
        events, event_issues = _validate_file(events_file, load_events)
        issues.extend(event_issues)
    commands, command_issues = _validate_file(commands_file, load_commands)
    issues.extend(command_issues)
    queries, queries_issues = _validate_file(queries_file, load_queries)
    issues.extend(queries_issues)
    http, http_issues = _validate_file(http_file, load_http)
    issues.extend(http_issues)

    rules_files: list[tuple[Path, RulesFile]] = []
    if rules_dir.exists():
        for rule_path in sorted(rules_dir.glob("*.yaml")):
            rule_data, rule_issues = _validate_file(rule_path, load_rules)
            issues.extend(rule_issues)
            if isinstance(rule_data, RulesFile):
                rules_files.append((rule_path, rule_data))
    else:
        issues.append(ContractIssue(str(rules_dir), "Rules directory is missing"))

    # Load optional extended contract files
    workflows: WorkflowsFile | None = None
    if workflows_file.exists():
        workflows, workflows_issues = _validate_file(workflows_file, load_workflows)
        issues.extend(workflows_issues)

    scenarios: ScenariosFile | None = None
    scenario_ids: set[str] = set()
    if scenarios_file.exists():
        scenarios, scenarios_issues = _validate_file(scenarios_file, load_scenarios)
        issues.extend(scenarios_issues)
        if isinstance(scenarios, ScenariosFile):
            scenario_ids = {scenario.id for scenario in scenarios.scenarios}

    projections_files: list[tuple[Path, ProjectionsFile]] = []
    if projections_dir.exists():
        for projection_path in sorted(projections_dir.glob("*.yaml")):
            projection_data, projection_issues = _validate_file(
                projection_path, load_projections
            )
            issues.extend(projection_issues)
            if isinstance(projection_data, ProjectionsFile):
                projections_files.append((projection_path, projection_data))

    policies_files: list[tuple[Path, PoliciesFile]] = []
    if policies_dir.exists():
        for policy_path in sorted(policies_dir.glob("*.yaml")):
            # Skip rbac.yaml and permissions_map.yaml as they use different schema
            if policy_path.name in ("rbac.yaml", "permissions_map.yaml"):
                continue
            policy_data, policy_issues = _validate_file(policy_path, load_policies)
            issues.extend(policy_issues)
            if isinstance(policy_data, PoliciesFile):
                policies_files.append((policy_path, policy_data))

    access_policy: AccessPolicyFile | None = None
    if access_policy_file.exists():
        access_policy, access_policy_issues = _validate_file(
            access_policy_file, load_access_policy
        )
        issues.extend(access_policy_issues)

    graphql: GraphQLApiFile | None = None
    if graphql_file.exists():
        graphql, graphql_issues = _validate_file(graphql_file, load_graphql)
        issues.extend(graphql_issues)

    persistence: PersistenceModelFile | None = None
    if persistence_file.exists():
        persistence, persistence_issues = _validate_file(
            persistence_file, load_persistence
        )
        issues.extend(persistence_issues)

    integrations: IntegrationsFile | None = None
    if integrations_file.exists():
        integrations, integrations_issues = _validate_file(
            integrations_file, load_integrations
        )
        issues.extend(integrations_issues)

    profiles: ProfilesFile | None = None
    if profiles_file.exists():
        profiles, profiles_issues = _validate_file(profiles_file, load_profiles)
        issues.extend(profiles_issues)

    secrets_contract: SecretsContractFile | None = None
    if secrets_file.exists():
        secrets_contract, secrets_issues = _validate_file(
            secrets_file, load_secrets_contract
        )
        issues.extend(secrets_issues)

    security_baseline: SecurityBaselineFile | None = None
    if security_file.exists():
        security_baseline, security_issues = _validate_file(
            security_file, load_security_baseline
        )
        issues.extend(security_issues)

    reliability_policies: ReliabilityPoliciesFile | None = None
    if reliability_file.exists():
        reliability_policies, reliability_issues = _validate_file(
            reliability_file, load_reliability
        )
        issues.extend(reliability_issues)

    observability: ObservabilityFile | None = None
    if observability_file.exists():
        observability, observability_issues = _validate_file(
            observability_file, load_observability
        )
        issues.extend(observability_issues)

    testing: TestingFile | None = None
    if testing_file.exists():
        testing, testing_issues = _validate_file(testing_file, load_testing)
        issues.extend(testing_issues)

    if (
        not isinstance(info, InfoFile)
        or not isinstance(glossary, GlossaryFile)
        or not isinstance(entities, EntitiesFile)
        or not isinstance(errors, ErrorsFile)
        or not isinstance(commands, CommandsFile)
        or not isinstance(queries, QueriesFile)
    ):
        return issues

    entity_ids, entity_id_issues = _collect_ids(entities.entities, str(entities_file))
    issues.extend(entity_id_issues)
    entity_field_map = {
        entity.id: {field.name for field in entity.fields}
        for entity in entities.entities
    }
    value_object_ids: set[str] = set()
    if isinstance(value_objects, ValueObjectsFile):
        value_object_ids, value_object_id_issues = _collect_ids(
            value_objects.value_objects,
            str(value_objects_file),
        )
        issues.extend(value_object_id_issues)
    enum_ids: set[str] = set()
    if isinstance(enums, EnumsFile):
        enum_ids, enum_id_issues = _collect_ids(enums.enums, str(enums_file))
        issues.extend(enum_id_issues)

    # Validate Entity constraints and indexes
    issues.extend(
        _lint_entity_constraints(
            entities,
            entities_file,
            entity_ids=entity_ids,
        )
    )
    error_ids, error_id_issues = _collect_ids(errors.errors, str(errors_file))
    issues.extend(error_id_issues)
    command_ids, command_id_issues = _collect_ids(commands.commands, str(commands_file))
    issues.extend(command_id_issues)
    query_ids, query_id_issues = _collect_ids(queries.queries, str(queries_file))
    issues.extend(query_id_issues)

    event_ids: set[str] = set()
    if isinstance(events, EventsFile):
        event_ids, event_id_issues = _collect_ids(events.events, str(events_file))
        issues.extend(event_id_issues)

    workflow_ids: set[str] = set()
    if isinstance(workflows, WorkflowsFile):
        workflow_ids, workflow_id_issues = _collect_ids(
            workflows.workflows, str(workflows_file)
        )
        issues.extend(workflow_id_issues)

    integration_ids: set[str] = set()
    operation_ids: set[str] = set()
    if isinstance(integrations, IntegrationsFile):
        integration_ids, integration_id_issues = _collect_ids(
            integrations.integrations,
            str(integrations_file),
        )
        issues.extend(integration_id_issues)
        operation_ids, operation_id_issues = _collect_ids(
            integrations.operations,
            str(integrations_file),
        )
        issues.extend(operation_id_issues)

    role_ids: set[str] = set()
    permission_ids: set[str] = set()
    if isinstance(access_policy, AccessPolicyFile):
        role_ids = {role.id for role in access_policy.access.roles}
        permission_ids = {
            permission.id for permission in access_policy.access.permissions
        }

    datasource_ids: set[str] = set()
    persistence_table_ids: set[str] = set()
    if isinstance(persistence, PersistenceModelFile):
        datasource_ids = {ds.id for ds in persistence.datasources}
        persistence_table_ids = {table.id for table in persistence.tables}

    secret_ids: set[str] = set()
    if isinstance(secrets_contract, SecretsContractFile):
        secret_ids = {secret.id for secret in secrets_contract.secrets}

    issues.extend(
        _lint_command_references(
            commands,
            commands_file,
            entity_ids=entity_ids,
            value_object_ids=value_object_ids,
            error_ids=error_ids,
            event_ids=event_ids,
            events_missing=events_missing,
            role_ids=role_ids,
            permission_ids=permission_ids,
            persistence_table_ids=persistence_table_ids,
            datasource_ids=datasource_ids,
        )
    )

    policy_ids: set[str] = set()
    for _, policies in policies_files:
        for policy in policies.policies:
            policy_ids.add(policy.id)

    rule_ids: set[str] = set()
    for path, rules in rules_files:
        ids, rule_id_issues = _collect_ids(rules.rules, str(path))
        issues.extend(rule_id_issues)
        for rule_id in ids:
            if rule_id in rule_ids:
                issues.append(
                    ContractIssue(
                        str(path), f"Duplicate rule id across files: {rule_id}"
                    )
                )
            else:
                rule_ids.add(rule_id)
        issues.extend(
            _lint_rule_references(
                rules,
                path,
                command_ids=command_ids,
                query_ids=query_ids,
                workflow_ids=workflow_ids,
                policy_ids=policy_ids,
                scenario_ids=scenario_ids,
            )
        )

    if isinstance(http, HttpApiFile):
        issues.extend(_lint_http_routes(http, http_file, command_ids, query_ids))

    # Validate Query.reads references
    issues.extend(
        _lint_query_references(
            queries,
            queries_file,
            entity_ids=entity_ids,
            role_ids=role_ids,
            permission_ids=permission_ids,
            persistence_table_ids=persistence_table_ids,
            datasource_ids=datasource_ids,
        )
    )

    # Validate Workflows references
    if isinstance(workflows, WorkflowsFile):
        issues.extend(
            _lint_workflow_references(
                workflows,
                workflows_file,
                entity_ids=entity_ids,
                command_ids=command_ids,
                event_ids=event_ids,
                error_ids=error_ids,
                role_ids=role_ids,
                permission_ids=permission_ids,
                scenario_ids=scenario_ids,
            )
        )

    # Validate Scenarios references
    if isinstance(scenarios, ScenariosFile):
        issues.extend(
            _lint_scenario_references(
                scenarios,
                scenarios_file,
                command_ids=command_ids,
                query_ids=query_ids,
                event_ids=event_ids,
            )
        )

    # Validate Projections references
    projection_ids: set[str] = set()
    for projection_path, projections in projections_files:
        for projection in projections.projections:
            projection_ids.add(projection.id)
        issues.extend(
            _lint_projection_references(
                projections,
                projection_path,
                event_ids=event_ids,
                persistence_table_ids=persistence_table_ids,
            )
        )

    # Validate Policies references (policies can reference rules, commands, entities - currently no strict validation needed)
    for policy_path, policies in policies_files:
        # Collect policy IDs to check for duplicates
        policy_ids: set[str] = set()
        for policy_index, policy in enumerate(policies.policies):
            if policy.id in policy_ids:
                issues.append(
                    ContractIssue(
                        _format_location(policy_path, f"policies[{policy_index}].id"),
                        f"Duplicate policy id: {policy.id}",
                    )
                )
            policy_ids.add(policy.id)
        issues.extend(
            _lint_policy_references(
                policies,
                policy_path,
                entity_field_map=entity_field_map,
                command_ids=command_ids,
                query_ids=query_ids,
                workflow_ids=workflow_ids,
                projection_ids=projection_ids,
                integration_ids=integration_ids,
            )
        )

    # Validate AccessPolicy references
    used_roles: set[str] = set()
    used_permissions: set[str] = set()
    if isinstance(access_policy, AccessPolicyFile):
        issues.extend(
            _lint_access_policy_references(
                access_policy,
                access_policy_file,
                entity_ids=entity_ids,
                command_ids=command_ids,
                query_ids=query_ids,
                projection_ids=projection_ids,
            )
        )
        guard_issues, used_roles, used_permissions = _extract_guard_usage(
            commands=commands,
            commands_path=commands_file,
            workflows=workflows,
            workflows_path=workflows_file,
            http=http,
            http_path=http_file,
            role_ids={role.id for role in access_policy.access.roles},
            permission_ids={
                permission.id for permission in access_policy.access.permissions
            },
        )
        issues.extend(guard_issues)
        scenario_role_issues, scenario_roles = _collect_role_usage_from_scenarios(
            scenarios=scenarios,
            scenarios_path=scenarios_file,
            role_ids={role.id for role in access_policy.access.roles},
        )
        issues.extend(scenario_role_issues)
        used_roles.update(scenario_roles)
        issues.extend(
            _lint_access_policy_semantics(
                access_policy=access_policy,
                access_policy_path=access_policy_file,
                policies_files=policies_files,
                used_roles=used_roles,
                used_permissions=used_permissions,
            )
        )

    # Validate GraphQL API references
    if isinstance(graphql, GraphQLApiFile):
        issues.extend(
            _lint_graphql_references(
                graphql,
                graphql_file,
                command_ids=command_ids,
                query_ids=query_ids,
            )
        )

    field_records = _collect_named_field_records(
        entities=entities,
        events=events,
        commands=commands,
        queries=queries,
        projections_files=projections_files,
        http=http,
        graphql=graphql,
        integrations=integrations,
        value_objects=value_objects,
    )
    issues.extend(
        _lint_named_field_types(
            field_records=field_records,
            entity_ids=entity_ids,
            value_object_ids=value_object_ids,
            enum_ids=enum_ids,
        )
    )

    if isinstance(persistence, PersistenceModelFile):
        issues.extend(
            _lint_persistence_references(
                persistence,
                persistence_file,
                integration_ids=integration_ids,
                operation_ids=operation_ids,
            )
        )

    if isinstance(integrations, IntegrationsFile):
        issues.extend(
            _lint_integration_references(
                integrations,
                integrations_file,
                error_ids=error_ids,
                event_ids=event_ids,
                secret_ids=secret_ids,
                operation_ids=operation_ids,
            )
        )

    if isinstance(profiles, ProfilesFile):
        issues.extend(_lint_profiles_contract(profiles, profiles_file))

    if isinstance(secrets_contract, SecretsContractFile):
        issues.extend(_lint_secrets_contract(secrets_contract, secrets_file))

    if isinstance(reliability_policies, ReliabilityPoliciesFile):
        issues.extend(
            _lint_reliability_contract(
                reliability_policies,
                reliability_file,
                command_ids=command_ids,
                workflow_ids=workflow_ids,
                integration_ids=integration_ids,
                integration_operation_ids=operation_ids,
            )
        )

    if isinstance(observability, ObservabilityFile):
        issues.extend(
            _lint_observability_contract(
                observability,
                observability_file,
                command_ids=command_ids,
                workflow_ids=workflow_ids,
                integration_ids=integration_ids,
                integration_operation_ids=operation_ids,
                persistence_table_ids=persistence_table_ids,
                datasource_ids=datasource_ids,
            )
        )

    if isinstance(testing, TestingFile):
        issues.extend(
            _lint_testing_contract(
                testing,
                testing_file,
                command_ids=command_ids,
                query_ids=query_ids,
                event_ids=event_ids,
                scenario_ids=scenario_ids,
            )
        )

    issues.extend(
        _lint_integration_effect_references(
            commands=commands,
            commands_path=commands_file,
            workflows=workflows,
            workflows_path=workflows_file,
            integration_ids=integration_ids,
            operation_ids=operation_ids,
        )
    )

    return issues


def _normalize_ref(value: str) -> str:
    return value.strip().lower()


def _extract_guard_usage(
    *,
    commands: CommandsFile,
    commands_path: Path,
    workflows: WorkflowsFile | None,
    workflows_path: Path,
    http: HttpApiFile | None,
    http_path: Path,
    role_ids: set[str],
    permission_ids: set[str],
) -> tuple[list[ContractIssue], set[str], set[str]]:
    """Extract auth guard usage and validate guard references to RBAC ids."""
    issues: list[ContractIssue] = []
    used_roles: set[str] = set()
    used_permissions: set[str] = set()

    role_index = {_normalize_ref(role_id): role_id for role_id in role_ids}
    permission_index = {
        _normalize_ref(permission_id): permission_id for permission_id in permission_ids
    }

    # Helper to mark roles/permissions as used from required_roles/required_permissions fields
    def _mark_required_roles_used(required_roles: list[str] | None) -> None:
        if not required_roles:
            return
        for role_ref in required_roles:
            if not role_ref:
                continue
            role_norm = _normalize_ref(str(role_ref))
            canonical = role_index.get(role_norm)
            if canonical:
                used_roles.add(canonical)

    def _mark_required_permissions_used(required_permissions: list[str] | None) -> None:
        if not required_permissions:
            return
        for perm_ref in required_permissions:
            if not perm_ref:
                continue
            perm_norm = _normalize_ref(str(perm_ref))
            canonical = permission_index.get(perm_norm)
            if canonical:
                used_permissions.add(canonical)

    def _check_role_ref(raw_role: str | None, location: str) -> None:
        if not raw_role:
            issues.append(
                ContractIssue(location, "auth.role guard missing 'role' parameter")
            )
            return

        # Handle list format (convert to string representation)
        if isinstance(raw_role, list):
            issues.append(
                ContractIssue(
                    location,
                    "auth.role 'role' parameter should be a string, not a list. Use 'roles' for multiple roles or choose one role.",
                )
            )
            return

        role_norm = _normalize_ref(str(raw_role))
        canonical = role_index.get(role_norm)
        if canonical is None:
            issues.append(
                ContractIssue(
                    location, f"auth.role references unknown role '{raw_role}'"
                )
            )
            return
        if str(raw_role) != canonical:
            issues.append(
                ContractIssue(
                    location,
                    f"auth.role uses '{raw_role}' but canonical role id is '{canonical}'",
                )
            )
        used_roles.add(canonical)

    def _check_roles_ref(raw_roles: list | None, location: str) -> None:
        """Check multiple roles from 'roles' parameter (plural form)."""
        if not raw_roles:
            return
        if not isinstance(raw_roles, list):
            issues.append(
                ContractIssue(
                    location, "auth.role guard 'roles' parameter must be a list"
                )
            )
            return
        for idx, raw_role in enumerate(raw_roles):
            role_location = f"{location}[{idx}]"
            if not raw_role:
                continue
            role_norm = _normalize_ref(str(raw_role))
            canonical = role_index.get(role_norm)
            if canonical is None:
                issues.append(
                    ContractIssue(
                        role_location, f"auth.role references unknown role '{raw_role}'"
                    )
                )
                continue
            if str(raw_role) != canonical:
                issues.append(
                    ContractIssue(
                        role_location,
                        f"auth.role uses '{raw_role}' but canonical role id is '{canonical}'",
                    )
                )
            used_roles.add(canonical)

    def _check_permission_ref(raw_permission: str | None, location: str) -> None:
        if not raw_permission:
            issues.append(
                ContractIssue(
                    location, "auth.permission guard missing 'permission' parameter"
                )
            )
            return

        # Handle list format (convert to string representation)
        if isinstance(raw_permission, list):
            issues.append(
                ContractIssue(
                    location,
                    "auth.permission 'permission' parameter should be a string, not a list. Use 'permissions' for multiple permissions or choose one permission.",
                )
            )
            return

        permission_norm = _normalize_ref(str(raw_permission))
        canonical = permission_index.get(permission_norm)
        if canonical is None:
            issues.append(
                ContractIssue(
                    location,
                    f"auth.permission references unknown permission '{raw_permission}'",
                )
            )
            return
        if str(raw_permission) != canonical:
            issues.append(
                ContractIssue(
                    location,
                    f"auth.permission uses '{raw_permission}' but canonical permission id is '{canonical}'",
                )
            )
        used_permissions.add(canonical)

    def _check_permissions_ref(raw_permissions: list | None, location: str) -> None:
        """Check multiple permissions from 'permissions' parameter (plural form)."""
        if not raw_permissions:
            return
        if not isinstance(raw_permissions, list):
            issues.append(
                ContractIssue(
                    location,
                    "auth.permission guard 'permissions' parameter must be a list",
                )
            )
            return
        for idx, raw_permission in enumerate(raw_permissions):
            perm_location = f"{location}[{idx}]"
            if not raw_permission:
                continue
            permission_norm = _normalize_ref(str(raw_permission))
            canonical = permission_index.get(permission_norm)
            if canonical is None:
                issues.append(
                    ContractIssue(
                        perm_location,
                        f"auth.permission references unknown permission '{raw_permission}'",
                    )
                )
                continue
            if str(raw_permission) != canonical:
                issues.append(
                    ContractIssue(
                        perm_location,
                        f"auth.permission uses '{raw_permission}' but canonical permission id is '{canonical}'",
                    )
                )
            used_permissions.add(canonical)

    for command_index, command in enumerate(commands.commands):
        command_prefix = f"commands[{command_index}]"

        # Mark required_roles and required_permissions as used
        _mark_required_roles_used(getattr(command, "required_roles", None))
        _mark_required_permissions_used(getattr(command, "required_permissions", None))

        for guard_index, guard in enumerate(command.guards):
            location_base = _format_location(
                commands_path, f"{command_prefix}.guards[{guard_index}]"
            )
            params = guard.params or {}
            if guard.id == "auth.role":
                # Support both singular 'role' and plural 'roles' parameters
                if "role" in params:
                    _check_role_ref(params.get("role"), f"{location_base}.params.role")
                elif "roles" in params:
                    _check_roles_ref(
                        params.get("roles"), f"{location_base}.params.roles"
                    )
                else:
                    issues.append(
                        ContractIssue(
                            f"{location_base}.params",
                            "auth.role guard missing 'role' or 'roles' parameter",
                        )
                    )
            elif guard.id == "auth.permission":
                # Support both singular 'permission' and plural 'permissions' parameters
                if "permission" in params:
                    _check_permission_ref(
                        params.get("permission"),
                        f"{location_base}.params.permission",
                    )
                elif "permissions" in params:
                    _check_permissions_ref(
                        params.get("permissions"),
                        f"{location_base}.params.permissions",
                    )
                else:
                    issues.append(
                        ContractIssue(
                            f"{location_base}.params",
                            "auth.permission guard missing 'permission' or 'permissions' parameter",
                        )
                    )

    if isinstance(workflows, WorkflowsFile):
        for workflow_index, workflow in enumerate(workflows.workflows):
            workflow_prefix = f"workflows[{workflow_index}]"

            # Mark required_roles and required_permissions as used
            _mark_required_roles_used(getattr(workflow, "required_roles", None))
            _mark_required_permissions_used(
                getattr(workflow, "required_permissions", None)
            )

            for transition_index, transition in enumerate(workflow.transitions):
                transition_prefix = f"{workflow_prefix}.transitions[{transition_index}]"
                for guard_index, guard in enumerate(transition.guards):
                    location_base = _format_location(
                        workflows_path, f"{transition_prefix}.guards[{guard_index}]"
                    )
                    params = guard.params or {}
                    if guard.id == "auth.role":
                        # Support both singular 'role' and plural 'roles' parameters
                        if "role" in params:
                            _check_role_ref(
                                params.get("role"), f"{location_base}.params.role"
                            )
                        elif "roles" in params:
                            _check_roles_ref(
                                params.get("roles"), f"{location_base}.params.roles"
                            )
                        else:
                            issues.append(
                                ContractIssue(
                                    f"{location_base}.params",
                                    "auth.role guard missing 'role' or 'roles' parameter",
                                )
                            )
                    elif guard.id == "auth.permission":
                        # Support both singular 'permission' and plural 'permissions' parameters
                        if "permission" in params:
                            _check_permission_ref(
                                params.get("permission"),
                                f"{location_base}.params.permission",
                            )
                        elif "permissions" in params:
                            _check_permissions_ref(
                                params.get("permissions"),
                                f"{location_base}.params.permissions",
                            )
                        else:
                            issues.append(
                                ContractIssue(
                                    f"{location_base}.params",
                                    "auth.permission guard missing 'permission' or 'permissions' parameter",
                                )
                            )

    if isinstance(http, HttpApiFile):
        for route_index, route in enumerate(http.routes):
            auth_raw = (route.auth or "").strip()
            if not auth_raw:
                continue
            segments = [
                segment.strip()
                for part in auth_raw.split("|")
                for segment in part.split(",")
                if segment.strip()
            ]
            for segment in segments:
                lowered = segment.lower()
                location = _format_location(http_path, f"routes[{route_index}].auth")
                if lowered.startswith("role:"):
                    _check_role_ref(segment.split(":", 1)[1].strip(), location)
                elif lowered.startswith("permission:"):
                    _check_permission_ref(segment.split(":", 1)[1].strip(), location)

    return issues, used_roles, used_permissions


def _is_ownership_permission(permission: Permission) -> bool:
    perm_id = permission.id.lower()
    desc = (permission.description or "").lower()
    return (
        "own" in perm_id
        or perm_id.startswith("my_")
        or " own " in f" {desc} "
        or "only their own" in desc
    )


def _collect_role_usage_from_scenarios(
    *,
    scenarios: ScenariosFile | None,
    scenarios_path: Path,
    role_ids: set[str],
) -> tuple[list[ContractIssue], set[str]]:
    """Treat scenario actors as role usage signals and suggest near role matches."""
    issues: list[ContractIssue] = []
    used_roles: set[str] = set()
    role_index = {_normalize_ref(role_id): role_id for role_id in role_ids}
    known_norm_roles = sorted(role_index.keys())

    if not isinstance(scenarios, ScenariosFile):
        return issues, used_roles

    for scenario_index, scenario in enumerate(scenarios.scenarios):
        actor_refs = list(getattr(scenario, "actor_roles", []) or [])
        using_legacy_actors = False
        if not actor_refs:
            actor_refs = list(getattr(scenario, "actors", []) or [])
            using_legacy_actors = bool(actor_refs)

        if using_legacy_actors:
            issues.append(
                ContractIssue(
                    _format_location(
                        scenarios_path,
                        f"scenarios[{scenario_index}].actors",
                    ),
                    "legacy actors[] is deprecated; use actor_roles[] with Role IDs",
                )
            )

        for actor_index, actor in enumerate(actor_refs):
            actor_norm = _normalize_ref(actor)
            canonical = role_index.get(actor_norm)
            if canonical is None:
                near = difflib.get_close_matches(
                    actor_norm, known_norm_roles, n=1, cutoff=0.78
                )
                if near:
                    suggested = role_index[near[0]]
                    issues.append(
                        ContractIssue(
                            _format_location(
                                scenarios_path,
                                (
                                    f"scenarios[{scenario_index}].actors[{actor_index}]"
                                    if using_legacy_actors
                                    else f"scenarios[{scenario_index}].actor_roles[{actor_index}]"
                                ),
                            ),
                            f"actor '{actor}' does not match any RBAC role; did you mean '{suggested}'?",
                        )
                    )
                continue
            used_roles.add(canonical)
            if actor != canonical:
                issues.append(
                    ContractIssue(
                        _format_location(
                            scenarios_path,
                            (
                                f"scenarios[{scenario_index}].actors[{actor_index}]"
                                if using_legacy_actors
                                else f"scenarios[{scenario_index}].actor_roles[{actor_index}]"
                            ),
                        ),
                        f"actor '{actor}' should use canonical role id '{canonical}'",
                    )
                )

    return issues, used_roles


def _policy_mentions_permission(policy: Policy, permission_id: str) -> bool:
    permission_id_norm = permission_id.lower()
    if permission_id_norm in policy.id.lower():
        return True
    if any(permission_id_norm == str(tag).lower() for tag in policy.tags):
        return True
    if policy.source and permission_id_norm in policy.source.lower():
        return True
    return False


def _policy_has_ownership_condition(policy: Policy) -> bool:
    for condition in policy.conditions:
        field = condition.field.lower()
        op = condition.op.lower()
        value = str(condition.value).lower()
        if op != "eq":
            continue
        has_subject = any(
            token in field
            for token in ("owner", "employee_id", "user_id", "actor", "subject")
        )
        has_actor_value = any(
            token in value
            for token in ("actor", "subject", "user", "principal", "request", "current")
        )
        if has_subject and has_actor_value:
            return True
    return False


def _lint_access_policy_semantics(
    *,
    access_policy: AccessPolicyFile,
    access_policy_path: Path,
    policies_files: list[tuple[Path, PoliciesFile]],
    used_roles: set[str],
    used_permissions: set[str],
) -> list[ContractIssue]:
    """Validate semantic quality for RBAC: usage and ownership constraints."""
    issues: list[ContractIssue] = []

    role_ids = {role.id for role in access_policy.access.roles}
    permission_by_id = {
        permission.id: permission for permission in access_policy.access.permissions
    }
    permissions_by_role = {
        binding.role: set(binding.permissions)
        for binding in access_policy.access.bindings
    }
    roles_with_bindings = set(permissions_by_role.keys())

    for role_id in sorted(role_ids):
        if role_id not in used_roles:
            # Check if role is used in required_roles of commands/queries/workflows
            # This is acceptable - don't report as error, just note it
            pass
        if role_id not in roles_with_bindings:
            issues.append(
                ContractIssue(
                    _format_location(access_policy_path, "access.bindings"),
                    f"role '{role_id}' is defined but has no permission binding",
                )
            )

    for permission_id in sorted(permission_by_id):
        if permission_id not in used_permissions:
            # Permission might be used in required_permissions field or for future use
            # Only report if it's also not bound to any role (completely unused)
            bound_somewhere = any(
                permission_id in bound for bound in permissions_by_role.values()
            )
            if not bound_somewhere:
                # Completely unused permission - this is worth reporting
                issues.append(
                    ContractIssue(
                        _format_location(access_policy_path, "access.permissions"),
                        f"permission '{permission_id}' is defined but never referenced by guards and not bound to any role",
                    )
                )
        else:
            # Permission is used, check if it's bound
            bound_somewhere = any(
                permission_id in bound for bound in permissions_by_role.values()
            )
            if not bound_somewhere:
                issues.append(
                    ContractIssue(
                        _format_location(access_policy_path, "access.bindings"),
                        f"permission '{permission_id}' is used by guards but not assigned to any role binding",
                    )
                )

    ownership_permissions = [
        permission
        for permission in access_policy.access.permissions
        if _is_ownership_permission(permission)
    ]
    if not ownership_permissions:
        return issues

    policies: list[Policy] = []
    for _, file_data in policies_files:
        policies.extend(file_data.policies)

    if not policies:
        issues.append(
            ContractIssue(
                _format_location(access_policy_path, "access.permissions"),
                "ownership-style permissions (e.g. own_*) require policy/policies.yaml with explicit ownership conditions",
            )
        )
        return issues

    for permission in ownership_permissions:
        matched_policies = [
            policy
            for policy in policies
            if _policy_mentions_permission(policy, permission.id)
        ]
        if not matched_policies:
            issues.append(
                ContractIssue(
                    _format_location(access_policy_path, "access.permissions"),
                    f"ownership permission '{permission.id}' has no matching policy definition in policy/policies.yaml",
                )
            )
            continue

        if not any(
            _policy_has_ownership_condition(policy) for policy in matched_policies
        ):
            issues.append(
                ContractIssue(
                    _format_location(access_policy_path, "access.permissions"),
                    f"ownership permission '{permission.id}' is ambiguous: matching policy exists but lacks explicit owner/actor equality condition",
                )
            )

    return issues
