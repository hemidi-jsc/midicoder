"""Intent inference utilities for IR build."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Iterable

from midicoder.dsl.models import GraphQLApiFile, HttpApiFile, WorkflowsFile

from ..normalize.normalizer import Normalizer
from ..schema.ir_schema import IR, IntentIR, IntentStats
from ..symbols.symbol_table import SYMBOL_TYPE_COMMAND, SYMBOL_TYPE_QUERY

UNKNOWN_MODULE = "unknown"

# Confidence levels aligned with ir-build-intent-algorithm.md
CONFIDENCE_CERTAIN = 1.0
CONFIDENCE_HIGH = 0.9
CONFIDENCE_MEDIUM = 0.7
CONFIDENCE_LOW = 0.5
CONFIDENCE_VERY_LOW = 0.3


def confidence_label(confidence: float) -> str:
    if confidence >= 0.95:
        return "CERTAIN"
    if confidence >= 0.85:
        return "HIGH"
    if confidence >= 0.65:
        return "MEDIUM"
    if confidence >= 0.45:
        return "LOW"
    return "VERY_LOW"


@dataclass
class KindSignalIndex:
    """Signals needed for intent.kind inference."""

    command_routes: dict[str, list["RouteSignal"]] = field(default_factory=dict)
    query_routes: dict[str, list["RouteSignal"]] = field(default_factory=dict)
    command_workflows: dict[str, list[str]] = field(default_factory=dict)


@dataclass(frozen=True)
class RouteSignal:
    source: str
    kind: str


@dataclass(frozen=True)
class ModuleCandidate:
    """Module inference candidate."""

    module: str
    confidence: float
    source: str
    specificity: int = 0
    order: int = 0


def apply_intent_kind(
    ir: IR,
    validated_data: dict[str, Any],
    normalizer: Normalizer,
    schema_tree: dict[str, Any] | None = None,
) -> None:
    """Infer and attach intent.kind for supported IR nodes using schema-driven rules."""
    from .schema_parser import (
        extract_meta_kind_mapping,
        infer_intent_kind_from_meta,
        should_apply_signals_for_model,
    )

    # Extract meta.kind mapping from schema tree
    meta_mapping = extract_meta_kind_mapping(schema_tree) if schema_tree else {}

    # Build signals for commands and queries
    signals = build_kind_signal_index(validated_data, normalizer)

    # Entity: use meta.kind from schema
    entity_meta_kind = meta_mapping.get("Entity", "domain.entity")
    default_kind, default_conf = infer_intent_kind_from_meta(entity_meta_kind)
    for entity in ir.modules.domain.entities:
        entity.intent = IntentIR(
            kind=default_kind,
            module=UNKNOWN_MODULE,
            confidence=default_conf,
            source=f"meta_kind:{entity_meta_kind}",
            alternatives=None,
        )

    # ValueObject: use meta.kind from schema
    vo_meta_kind = meta_mapping.get("ValueObject", "domain.value_object")
    default_kind, default_conf = infer_intent_kind_from_meta(vo_meta_kind)
    for value_object in ir.modules.domain.value_objects:
        value_object.intent = IntentIR(
            kind=default_kind,
            module=UNKNOWN_MODULE,
            confidence=default_conf,
            source=f"meta_kind:{vo_meta_kind}",
            alternatives=None,
        )

    # Enum: use meta.kind from schema
    enum_meta_kind = meta_mapping.get("EnumDef", "domain.enum")
    default_kind, default_conf = infer_intent_kind_from_meta(enum_meta_kind)
    for enum in ir.modules.domain.enums:
        enum.intent = IntentIR(
            kind=default_kind,
            module=UNKNOWN_MODULE,
            confidence=default_conf,
            source=f"meta_kind:{enum_meta_kind}",
            alternatives=None,
        )

    # Event: use meta.kind from schema
    event_meta_kind = meta_mapping.get("EventDef", "domain.event")
    default_kind, default_conf = infer_intent_kind_from_meta(event_meta_kind)
    for event in ir.modules.domain.events:
        event.intent = IntentIR(
            kind=default_kind,
            module=UNKNOWN_MODULE,
            confidence=default_conf,
            source=f"meta_kind:{event_meta_kind}",
            alternatives=None,
        )

    # Command: use signals if available, otherwise meta.kind
    command_meta_kind = meta_mapping.get("Command", "app.command")
    for command in ir.modules.application.commands:
        if should_apply_signals_for_model(command_meta_kind):
            command.intent = _infer_command_intent_kind(command.id, signals)
        else:
            default_kind, default_conf = infer_intent_kind_from_meta(command_meta_kind)
            command.intent = IntentIR(
                kind=default_kind,
                module=UNKNOWN_MODULE,
                confidence=default_conf,
                source=f"meta_kind:{command_meta_kind}",
                alternatives=None,
            )

    # Query: use signals if available, otherwise meta.kind
    query_meta_kind = meta_mapping.get("Query", "app.query")
    for query in ir.modules.application.queries:
        if should_apply_signals_for_model(query_meta_kind):
            query.intent = _infer_query_intent_kind(query.id, signals)
        else:
            default_kind, default_conf = infer_intent_kind_from_meta(query_meta_kind)
            query.intent = IntentIR(
                kind=default_kind,
                module=UNKNOWN_MODULE,
                confidence=default_conf,
                source=f"meta_kind:{query_meta_kind}",
                alternatives=None,
            )

    # Projection: use meta.kind from schema
    projection_meta_kind = meta_mapping.get("Projection", "app.projection")
    default_kind, default_conf = infer_intent_kind_from_meta(projection_meta_kind)
    for projection in ir.modules.application.projections:
        projection.intent = IntentIR(
            kind=default_kind,
            module=UNKNOWN_MODULE,
            confidence=default_conf,
            source=f"meta_kind:{projection_meta_kind}",
            alternatives=None,
        )

    # Workflow: use meta.kind from schema
    workflow_meta_kind = meta_mapping.get("Workflow", "workflow.definition")
    default_kind, default_conf = infer_intent_kind_from_meta(workflow_meta_kind)
    for workflow in ir.modules.workflow.workflows:
        workflow.intent = IntentIR(
            kind=default_kind,
            module=UNKNOWN_MODULE,
            confidence=default_conf,
            source=f"meta_kind:{workflow_meta_kind}",
            alternatives=None,
        )


def apply_intent_module(
    ir: IR,
    validated_data: dict[str, Any],
    normalizer: Normalizer,
    reporter: Any | None = None,
    schema_tree: dict[str, Any] | None = None,
) -> None:
    """Infer and attach intent.module for supported IR nodes using schema-driven rules."""
    route_candidates = _collect_route_module_candidates(
        validated_data, normalizer, schema_tree
    )

    entity_modules: dict[str, str] = {}
    for entity in ir.modules.domain.entities:
        chosen, alternatives = _infer_module_for_element(
            element_id=entity.id,
            source_file=entity.source.file,
            candidates=[],
            allow_file_stem=False,
            schema_tree=schema_tree,
        )
        _apply_module_to_intent(entity, chosen, alternatives, reporter)
        entity_modules[entity.id] = chosen.module

    for value_object in ir.modules.domain.value_objects:
        chosen, alternatives = _infer_module_for_element(
            element_id=value_object.id,
            source_file=value_object.source.file,
            candidates=[],
            allow_file_stem=False,
            schema_tree=schema_tree,
        )
        _apply_module_to_intent(value_object, chosen, alternatives, reporter)

    for enum in ir.modules.domain.enums:
        chosen, alternatives = _infer_module_for_element(
            element_id=enum.id,
            source_file=enum.source.file,
            candidates=[],
            allow_file_stem=False,
            schema_tree=schema_tree,
        )
        _apply_module_to_intent(enum, chosen, alternatives, reporter)

    for workflow in ir.modules.workflow.workflows:
        candidates: list[ModuleCandidate] = []
        entity_module = entity_modules.get(workflow.entity.id)
        if entity_module:
            candidates.append(
                ModuleCandidate(
                    module=entity_module,
                    confidence=CONFIDENCE_MEDIUM,
                    source=f"entity_ref:{workflow.entity.id}",
                )
            )
        chosen, alternatives = _infer_module_for_element(
            element_id=workflow.id,
            source_file=workflow.source.file,
            candidates=candidates,
            allow_file_stem=False,
            schema_tree=schema_tree,
        )
        _apply_module_to_intent(workflow, chosen, alternatives, reporter)

    workflow_candidates = _collect_workflow_command_candidates(
        validated_data, normalizer, ir
    )
    workflow_event_candidates = _collect_workflow_event_candidates(
        validated_data, normalizer, ir
    )

    for event in ir.modules.domain.events:
        candidates: list[ModuleCandidate] = []
        for wf_candidate in workflow_event_candidates.get(event.id, []):
            candidates.append(wf_candidate)
        chosen, alternatives = _infer_module_for_element(
            element_id=event.id,
            source_file=event.source.file,
            candidates=candidates,
            allow_file_stem=False,
            schema_tree=schema_tree,
        )
        _apply_module_to_intent(event, chosen, alternatives, reporter)

    for projection in ir.modules.application.projections:
        chosen, alternatives = _infer_module_for_element(
            element_id=projection.id,
            source_file=projection.source.file,
            candidates=[],
            allow_file_stem=False,
            schema_tree=schema_tree,
        )
        _apply_module_to_intent(projection, chosen, alternatives, reporter)

    for command in ir.modules.application.commands:
        candidates: list[ModuleCandidate] = []

        for candidate in route_candidates.get(command.id, []):
            candidates.append(candidate)

        for fetch in command.fetches:
            if fetch.type in {"Entity", "Unknown"}:
                entity_module = entity_modules.get(fetch.id)
                if entity_module:
                    candidates.append(
                        ModuleCandidate(
                            module=entity_module,
                            confidence=CONFIDENCE_MEDIUM,
                            source=f"entity_ref:{fetch.id}",
                        )
                    )

        for wf_candidate in workflow_candidates.get(command.id, []):
            candidates.append(wf_candidate)

        chosen, alternatives = _infer_module_for_element(
            element_id=command.id,
            source_file=command.source.file,
            candidates=candidates,
            allow_file_stem=False,
            schema_tree=schema_tree,
        )
        _apply_module_to_intent(command, chosen, alternatives, reporter)

    for query in ir.modules.application.queries:
        candidates: list[ModuleCandidate] = []

        for candidate in route_candidates.get(query.id, []):
            candidates.append(candidate)

        for read in query.reads:
            if read.type in {"Entity", "Unknown"}:
                entity_module = entity_modules.get(read.id)
                if entity_module:
                    candidates.append(
                        ModuleCandidate(
                            module=entity_module,
                            confidence=CONFIDENCE_MEDIUM,
                            source=f"entity_ref:{read.id}",
                        )
                    )

        chosen, alternatives = _infer_module_for_element(
            element_id=query.id,
            source_file=query.source.file,
            candidates=candidates,
            allow_file_stem=False,
            schema_tree=schema_tree,
        )
        _apply_module_to_intent(query, chosen, alternatives, reporter)


def validate_intents(
    ir: IR,
    validated_data: dict[str, Any],
    normalizer: Normalizer,
    reporter: Any,
) -> None:
    """Validate inferred intents and emit warnings/errors."""
    from ..diagnostics.error_codes import E321, I304, I305, W302, W303

    target_groups = [
        ("Entity", ir.modules.domain.entities),
        ("ValueObject", ir.modules.domain.value_objects),
        ("Enum", ir.modules.domain.enums),
        ("Event", ir.modules.domain.events),
        ("Projection", ir.modules.application.projections),
        ("Workflow", ir.modules.workflow.workflows),
        ("Command", ir.modules.application.commands),
        ("Query", ir.modules.application.queries),
    ]

    for _, elements in target_groups:
        for element in elements:
            if (
                element.intent is None
                or not element.intent.kind
                or not element.intent.module
            ):
                reporter.add_error(
                    stage="intent",
                    code=E321,
                    file=element.source.file,
                    message=f"Missing intent metadata for {element.id}",
                    severity="error",
                )
                continue

            if element.intent.confidence <= CONFIDENCE_VERY_LOW:
                reporter.add_error(
                    stage="intent",
                    code=W302,
                    file=element.source.file,
                    message=(
                        f"Low confidence intent for {element.id}: "
                        f"{confidence_label(element.intent.confidence)}"
                    ),
                    severity="warning",
                    context={
                        "suggestion": (
                            "Consider adding explicit route mapping or module annotation"
                        )
                    },
                )

    _validate_module_consistency(ir, reporter, W303)
    _validate_cross_module_dependencies(ir, reporter, I304)
    _validate_orphan_commands(validated_data, normalizer, ir, reporter, I305)


def compute_intent_stats(ir: IR) -> IntentStats:
    """Compute intent statistics for IR metadata."""
    elements = [
        *ir.modules.domain.entities,
        *ir.modules.domain.value_objects,
        *ir.modules.domain.enums,
        *ir.modules.domain.events,
        *ir.modules.application.projections,
        *ir.modules.workflow.workflows,
        *ir.modules.application.commands,
        *ir.modules.application.queries,
    ]

    total = len(elements)
    with_intent = 0
    missing = 0
    low_confidence = 0

    for element in elements:
        if not element.intent or not element.intent.kind or not element.intent.module:
            missing += 1
            continue
        with_intent += 1
        if element.intent.confidence <= CONFIDENCE_VERY_LOW:
            low_confidence += 1

    return IntentStats(
        total=total,
        with_intent=with_intent,
        missing=missing,
        low_confidence=low_confidence,
    )


def compute_intent_summary(ir: IR) -> dict[str, dict[str, int]]:
    by_kind: dict[str, int] = {}
    by_module: dict[str, int] = {}

    elements = [
        *ir.modules.domain.entities,
        *ir.modules.domain.value_objects,
        *ir.modules.domain.enums,
        *ir.modules.domain.events,
        *ir.modules.application.projections,
        *ir.modules.workflow.workflows,
        *ir.modules.application.commands,
        *ir.modules.application.queries,
    ]

    for element in elements:
        if not element.intent or not element.intent.kind or not element.intent.module:
            continue
        by_kind[element.intent.kind] = by_kind.get(element.intent.kind, 0) + 1
        by_module[element.intent.module] = by_module.get(element.intent.module, 0) + 1

    return {
        "by_kind": dict(sorted(by_kind.items())),
        "by_module": dict(sorted(by_module.items())),
    }


def compute_confidence_distribution(ir: IR) -> dict[str, int]:
    distribution: dict[str, int] = {}

    elements = [
        *ir.modules.domain.entities,
        *ir.modules.domain.value_objects,
        *ir.modules.domain.enums,
        *ir.modules.domain.events,
        *ir.modules.application.projections,
        *ir.modules.workflow.workflows,
        *ir.modules.application.commands,
        *ir.modules.application.queries,
    ]

    for element in elements:
        if not element.intent:
            continue
        label = confidence_label(element.intent.confidence)
        distribution[label] = distribution.get(label, 0) + 1

    return dict(sorted(distribution.items()))


def build_kind_signal_index(
    validated_data: dict[str, Any], normalizer: Normalizer
) -> KindSignalIndex:
    """Collect route/workflow signals needed for intent.kind inference."""
    index = KindSignalIndex()

    for _, data in validated_data.items():
        if isinstance(data, HttpApiFile):
            _collect_http_routes(data, index, normalizer)
        elif isinstance(data, GraphQLApiFile):
            _collect_graphql_operations(data, index, normalizer)
        elif isinstance(data, WorkflowsFile):
            _collect_workflow_transitions(data, index, normalizer)

    return index


def _collect_route_module_candidates(
    validated_data: dict[str, Any],
    normalizer: Normalizer,
    schema_tree: dict[str, Any] | None = None,
) -> dict[str, list[ModuleCandidate]]:
    candidates: dict[str, list[ModuleCandidate]] = {}
    route_index = 0

    for _, data in validated_data.items():
        if not isinstance(data, HttpApiFile):
            continue
        for route in data.routes:
            module_hint = _module_from_http_path(route.path, schema_tree=schema_tree)
            if not module_hint:
                route_index += 1
                continue

            candidate = ModuleCandidate(
                module=module_hint,
                confidence=CONFIDENCE_HIGH,
                source=f"route_path:{route.path}",
                specificity=_route_specificity(route.path, module_hint),
                order=route_index,
            )

            route_command_ids, route_query_ids = _resolve_http_route_targets(
                route, normalizer
            )

            for query_id in sorted(route_query_ids):
                _add_candidate(candidates, query_id, candidate)

            for command_id in sorted(route_command_ids):
                _add_candidate(candidates, command_id, candidate)

            route_index += 1

    return candidates


def _collect_workflow_command_candidates(
    validated_data: dict[str, Any],
    normalizer: Normalizer,
    ir: IR,
) -> dict[str, list[ModuleCandidate]]:
    workflow_module_map = {
        w.id: w.intent.module for w in ir.modules.workflow.workflows if w.intent
    }
    candidates: dict[str, list[ModuleCandidate]] = {}

    for _, data in validated_data.items():
        if not isinstance(data, WorkflowsFile):
            continue
        for workflow in data.workflows:
            workflow_id = normalizer.normalize_id(workflow.id)
            module_hint = workflow_module_map.get(workflow_id)
            if not module_hint:
                continue

            for transition in workflow.transitions:
                if not transition.on_command:
                    continue
                command_id = _normalize_ref_id(transition.on_command, normalizer)
                candidate = ModuleCandidate(
                    module=module_hint,
                    confidence=CONFIDENCE_MEDIUM,
                    source=f"workflow:{workflow_id}",
                )
                _add_candidate(candidates, command_id, candidate)

    return candidates


def _collect_workflow_event_candidates(
    validated_data: dict[str, Any],
    normalizer: Normalizer,
    ir: IR,
) -> dict[str, list[ModuleCandidate]]:
    workflow_module_map = {
        w.id: w.intent.module for w in ir.modules.workflow.workflows if w.intent
    }
    candidates: dict[str, list[ModuleCandidate]] = {}

    for _, data in validated_data.items():
        if not isinstance(data, WorkflowsFile):
            continue
        for workflow in data.workflows:
            workflow_id = normalizer.normalize_id(workflow.id)
            module_hint = workflow_module_map.get(workflow_id)
            if not module_hint:
                continue

            for transition in workflow.transitions:
                if not transition.on_event:
                    continue
                event_id = _normalize_ref_id(transition.on_event, normalizer)
                candidate = ModuleCandidate(
                    module=module_hint,
                    confidence=CONFIDENCE_MEDIUM,
                    source=f"workflow:{workflow_id}",
                )
                _add_candidate(candidates, event_id, candidate)

    return candidates


def _collect_graphql_operations(
    data: GraphQLApiFile, index: KindSignalIndex, normalizer: Normalizer
) -> None:
    api = data.api

    for operation in api.mutations:
        _collect_graphql_operation(operation, "mutation", index, normalizer)

    for operation in api.queries:
        _collect_graphql_operation(operation, "query", index, normalizer)


def _collect_graphql_operation(
    operation: Any,
    operation_type: str,
    index: KindSignalIndex,
    normalizer: Normalizer,
) -> None:
    resolver = getattr(operation, "resolver", "") or ""
    if not resolver:
        return

    source = f"graphql:{operation_type}:{operation.name}"

    if ":" not in resolver:
        return

    prefix, _ = resolver.split(":", 1)
    prefix = prefix.strip().lower()

    if prefix == "command":
        command_id = _normalize_ref_id(resolver, normalizer)
        _add_route_signal(index.command_routes, command_id, source, "controller")
        return

    if prefix == "query":
        query_id = _normalize_ref_id(resolver, normalizer)
        _add_route_signal(index.query_routes, query_id, source, "controller")


def _collect_http_routes(
    data: HttpApiFile, index: KindSignalIndex, normalizer: Normalizer
) -> None:
    for route in data.routes:
        source = f"route:{route.path}"
        route_kind = "controller"

        route_command_ids, route_query_ids = _resolve_http_route_targets(
            route, normalizer
        )

        for query_id in sorted(route_query_ids):
            _add_route_signal(index.query_routes, query_id, source, route_kind)

        for command_id in sorted(route_command_ids):
            _add_route_signal(index.command_routes, command_id, source, route_kind)


def _resolve_http_route_targets(
    route: Any, normalizer: Normalizer
) -> tuple[set[str], set[str]]:
    command_ids: set[str] = set()
    query_ids: set[str] = set()

    if getattr(route, "command", None):
        command_id = _normalize_ref_id(route.command, normalizer)
        _assign_http_target(
            command_id,
            normalizer,
            preferred_type="command",
            command_ids=command_ids,
            query_ids=query_ids,
        )

    if getattr(route, "query", None):
        query_id = _normalize_ref_id(route.query, normalizer)
        _assign_http_target(
            query_id,
            normalizer,
            preferred_type="query",
            command_ids=command_ids,
            query_ids=query_ids,
        )

    return command_ids, query_ids


def _assign_http_target(
    ref_id: str,
    normalizer: Normalizer,
    preferred_type: str,
    *,
    command_ids: set[str],
    query_ids: set[str],
) -> None:
    is_command = bool(normalizer.symbols.resolve(SYMBOL_TYPE_COMMAND, ref_id))
    is_query = bool(normalizer.symbols.resolve(SYMBOL_TYPE_QUERY, ref_id))

    if preferred_type == "command":
        if is_command:
            command_ids.add(ref_id)
            return
        if is_query:
            query_ids.add(ref_id)
            return
        command_ids.add(ref_id)
        return

    if preferred_type == "query":
        if is_query:
            query_ids.add(ref_id)
            return
        if is_command:
            command_ids.add(ref_id)
            return
        query_ids.add(ref_id)


def _collect_workflow_transitions(
    data: WorkflowsFile, index: KindSignalIndex, normalizer: Normalizer
) -> None:
    for workflow in data.workflows:
        workflow_id = normalizer.normalize_id(workflow.id)
        source = f"workflow:{workflow_id}"

        for transition in workflow.transitions:
            if transition.on_command:
                cmd_id = _normalize_ref_id(transition.on_command, normalizer)
                _add_signal(index.command_workflows, cmd_id, source)


def _infer_command_intent_kind(command_id: str, signals: KindSignalIndex) -> IntentIR:
    route_signals = signals.command_routes.get(command_id, [])
    if route_signals:
        return IntentIR(
            kind="controller",
            module=UNKNOWN_MODULE,
            confidence=CONFIDENCE_HIGH,
            source=_select_route_source(route_signals),
            alternatives=None,
        )

    workflow_sources = signals.command_workflows.get(command_id, [])
    if workflow_sources:
        return IntentIR(
            kind="service",
            module=UNKNOWN_MODULE,
            confidence=CONFIDENCE_MEDIUM,
            source=_select_source(workflow_sources),
            alternatives=None,
        )

    return IntentIR(
        kind="service",
        module=UNKNOWN_MODULE,
        confidence=CONFIDENCE_LOW,
        source="default:no_external_mapping",
        alternatives=None,
    )


def _infer_query_intent_kind(query_id: str, signals: KindSignalIndex) -> IntentIR:
    route_signals = signals.query_routes.get(query_id, [])
    if route_signals:
        return IntentIR(
            kind="controller",
            module=UNKNOWN_MODULE,
            confidence=CONFIDENCE_HIGH,
            source=_select_route_source(route_signals),
            alternatives=None,
        )

    return IntentIR(
        kind="service",
        module=UNKNOWN_MODULE,
        confidence=CONFIDENCE_LOW,
        source="default:no_external_mapping",
        alternatives=None,
    )


def _fixed_intent(kind: str, source: str) -> IntentIR:
    return IntentIR(
        kind=kind,
        module=UNKNOWN_MODULE,
        confidence=CONFIDENCE_CERTAIN,
        source=source,
        alternatives=None,
    )


def _select_route_source(signals: list[RouteSignal]) -> str:
    http_sources = [s.source for s in signals if s.source.startswith("route:")]
    if http_sources:
        return _select_source(http_sources)
    return _select_source([s.source for s in signals])


def _select_source(sources: list[str]) -> str:
    return sorted(sources)[0] if sources else ""


def _infer_module_for_element(
    element_id: str,
    source_file: str,
    candidates: Iterable[ModuleCandidate],
    allow_file_stem: bool,
    schema_tree: dict[str, Any] | None = None,
) -> tuple[ModuleCandidate, list[dict[str, Any]] | None]:
    resolved: dict[str, ModuleCandidate] = {}

    file_module = _module_from_file_path(
        source_file, allow_file_stem=allow_file_stem, schema_tree=schema_tree
    )
    if file_module:
        _consider_candidate(
            resolved,
            ModuleCandidate(
                module=file_module,
                confidence=CONFIDENCE_MEDIUM,
                source=f"file_path:{source_file}",
            ),
        )

    id_module = _module_from_id_pattern(element_id, schema_tree=schema_tree)
    if id_module:
        _consider_candidate(
            resolved,
            ModuleCandidate(
                module=id_module,
                confidence=CONFIDENCE_LOW,
                source=f"id_pattern:{element_id}",
            ),
        )

    for candidate in candidates:
        _consider_candidate(resolved, candidate)

    if not resolved:
        fallback = ModuleCandidate(
            module="core",
            confidence=CONFIDENCE_VERY_LOW,
            source="fallback:default",
        )
        return fallback, None

    sorted_candidates = sorted(
        resolved.values(),
        key=lambda c: (-c.confidence, -c.specificity, c.order, c.source, c.module),
    )
    chosen = sorted_candidates[0]

    alternatives: list[dict[str, Any]] | None = None
    if len(sorted_candidates) >= 2:
        if sorted_candidates[0].confidence == sorted_candidates[1].confidence:
            alternatives = [
                {
                    "module": c.module,
                    "confidence": c.confidence,
                    "source": c.source,
                }
                for c in sorted_candidates
            ]

    return chosen, alternatives


def _apply_module_to_intent(
    element: Any,
    chosen: ModuleCandidate,
    alternatives: list[dict[str, Any]] | None,
    reporter: Any | None,
) -> None:
    from ..diagnostics.error_codes import W304

    if element.intent is None:
        element.intent = IntentIR(
            kind="service",
            module=chosen.module,
            confidence=chosen.confidence,
            source=chosen.source,
            alternatives=alternatives,
        )
    else:
        element.intent.module = chosen.module
        element.intent.confidence = min(element.intent.confidence, chosen.confidence)
        element.intent.source = _combine_sources(element.intent.source, chosen.source)
        element.intent.alternatives = alternatives

    if alternatives and reporter is not None:
        top = alternatives[0]
        runner_up = alternatives[1] if len(alternatives) > 1 else None
        if runner_up:
            reporter.add_error(
                stage="intent",
                code=W304,
                file=element.source.file,
                message=(
                    f"Ambiguous module for {element.id}: "
                    f"{top['module']}({top['confidence']}) vs "
                    f"{runner_up['module']}({runner_up['confidence']})"
                ),
                severity="warning",
                context={"candidates": alternatives},
            )


def _combine_sources(kind_source: str, module_source: str) -> str:
    if not kind_source:
        return module_source
    if not module_source:
        return kind_source
    if module_source in kind_source:
        return kind_source
    if kind_source in module_source:
        return module_source
    return f"{kind_source} + {module_source}"


def _route_specificity(path: str, module_hint: str) -> int:
    segments = [s for s in path.strip("/").split("/") if s]
    ignore = {"api", "v1", "v2", "admin"}
    filtered = [s for s in segments if s not in ignore]
    depth = len(filtered)
    module_len = len(module_hint or "")
    return (module_len * 100) + depth


def _module_from_http_path(
    path: str, schema_tree: dict[str, Any] | None = None
) -> str | None:
    """Extract module from HTTP path using schema-driven ignore list."""
    from .schema_parser import extract_http_path_ignore_segments

    segments = [s for s in path.strip("/").split("/") if s]

    # Use schema tree if available, otherwise fallback to defaults
    if schema_tree:
        ignore = extract_http_path_ignore_segments(schema_tree)
    else:
        ignore = {"api", "v1", "v2", "admin"}

    for segment in segments:
        if segment in ignore:
            continue
        return segment.lower()
    return None


def _module_from_file_path(
    path: str, allow_file_stem: bool, schema_tree: dict[str, Any] | None = None
) -> str | None:
    """Extract module from file path using schema-driven container dirs."""
    from .schema_parser import extract_container_dirs

    normalized = path.replace("\\", "/")
    parts = [p for p in normalized.split("/") if p]
    if not parts:
        return None

    file_part = parts[-1]
    dir_parts = parts[:-1]

    # Use schema tree if available, otherwise fallback to defaults
    if schema_tree:
        ignore_dirs = extract_container_dirs(schema_tree)
    else:
        ignore_dirs = {
            "app",
            "domain",
            "api",
            "workflows",
            "policy",
            "rules",
            "scenarios",
        }

    dir_parts = [p for p in dir_parts if p not in ignore_dirs]

    if dir_parts:
        return dir_parts[0].lower()

    if allow_file_stem:
        if "." in file_part:
            return file_part.rsplit(".", 1)[0].lower()
        return file_part.lower()

    return None


def _module_from_id_pattern(
    element_id: str, schema_tree: dict[str, Any] | None = None
) -> str | None:
    """Extract module from ID pattern using schema-driven catalogs."""
    from .schema_parser import (
        extract_catalogs,
        extract_event_suffixes_from_catalog,
        extract_verb_prefixes_from_catalog,
        get_pluralization_rules,
    )

    if not element_id:
        return None

    tokens = _split_identifier(element_id)
    if not tokens:
        return None

    # Extract prefixes and suffixes from schema catalogs
    if schema_tree:
        catalogs = extract_catalogs(schema_tree)
        command_catalog = catalogs.get("COMMAND_CATEGORY_CATALOG", [])
        prefixes = extract_verb_prefixes_from_catalog(command_catalog)
        action_suffixes = extract_event_suffixes_from_catalog(command_catalog)
    else:
        # Fallback to hardcoded values
        prefixes = {
            "create",
            "update",
            "delete",
            "list",
            "get",
            "find",
            "cancel",
            "activate",
        }

    lowered = [token.lower() for token in tokens if token]
    if lowered and lowered[0] in prefixes:
        lowered = lowered[1:]

    # Event/action-style identifiers usually end with a verb-like suffix.
    # Keep the domain noun part to avoid modules like "payment_succeededs".
    if len(lowered) > 1 and lowered[-1] in action_suffixes:
        lowered = lowered[:-1]

    if not lowered:
        return None

    if len(lowered) == 1:
        return _pluralize_module_token(lowered[0], schema_tree)

    head = lowered[:-1]
    tail = _pluralize_module_token(lowered[-1], schema_tree)
    return "_".join([*head, tail])


def _pluralize_module_token(
    token: str, schema_tree: dict[str, Any] | None = None
) -> str:
    """Pluralize module token using schema-driven rules."""
    from .schema_parser import get_pluralization_rules

    # Use schema tree if available
    if schema_tree:
        irregular = get_pluralization_rules()
    else:
        irregular = {
            "money": "money",
            "person": "people",
        }

    if token in irregular:
        return irregular[token]
    if token.endswith("s"):
        return token
    if token.endswith(("x", "z", "ch", "sh")):
        return f"{token}es"
    if len(token) > 1 and token.endswith("y") and token[-2] not in "aeiou":
        return f"{token[:-1]}ies"
    return f"{token}s"


def _split_identifier(value: str) -> list[str]:
    cleaned = re.sub(r"[^A-Za-z0-9]+", " ", value).strip()
    if not cleaned:
        return []

    parts: list[str] = []
    for chunk in cleaned.split():
        tokens = re.findall(r"[A-Z]+(?![a-z])|[A-Z]?[a-z]+|[0-9]+", chunk)
        parts.extend(tokens if tokens else [chunk])

    return parts


def _normalize_ref_id(ref: Any, normalizer: Normalizer) -> str:
    return normalizer.normalize_id(_extract_ref_id(ref))


def _extract_ref_id(ref: Any) -> str:
    if isinstance(ref, str):
        if ":" in ref:
            return ref.split(":", 1)[1].strip()
        return ref.strip()
    if isinstance(ref, dict):
        return ref.get("id", "")
    return str(ref)


def _add_candidate(
    mapping: dict[str, list[ModuleCandidate]], key: str, candidate: ModuleCandidate
) -> None:
    mapping.setdefault(key, []).append(candidate)


def _add_signal(mapping: dict[str, list[str]], key: str, source: str) -> None:
    mapping.setdefault(key, []).append(source)


def _add_route_signal(
    mapping: dict[str, list[RouteSignal]],
    key: str,
    source: str,
    kind: str,
) -> None:
    mapping.setdefault(key, []).append(RouteSignal(source=source, kind=kind))


def _consider_candidate(
    resolved: dict[str, ModuleCandidate], candidate: ModuleCandidate
) -> None:
    if not candidate.module:
        return
    existing = resolved.get(candidate.module)
    if existing is None:
        resolved[candidate.module] = candidate
        return
    if candidate.confidence > existing.confidence:
        resolved[candidate.module] = candidate
        return
    if candidate.confidence == existing.confidence:
        if candidate.specificity > existing.specificity:
            resolved[candidate.module] = candidate
            return
        if candidate.specificity == existing.specificity:
            if candidate.order < existing.order:
                resolved[candidate.module] = candidate
                return
            if candidate.order == existing.order and candidate.source < existing.source:
                resolved[candidate.module] = candidate


def _validate_module_consistency(ir: IR, reporter: Any, code: str) -> None:
    by_file: dict[str, list[str]] = {}

    groups = [
        ir.modules.domain.entities,
        ir.modules.domain.value_objects,
        ir.modules.domain.enums,
        ir.modules.domain.events,
        ir.modules.application.projections,
        ir.modules.workflow.workflows,
        ir.modules.application.commands,
        ir.modules.application.queries,
    ]

    for elements in groups:
        for element in elements:
            if not element.intent:
                continue
            module = element.intent.module
            if not module:
                continue
            by_file.setdefault(element.source.file, []).append(module)

    for file, modules in by_file.items():
        # Skip validation for aggregate contract files
        if _is_aggregate_contract_file(file):
            continue

        # Need at least 2 elements to check consistency
        if len(modules) < 2:
            continue

        counts: dict[str, int] = {}
        for module in modules:
            counts[module] = counts.get(module, 0) + 1

        # Calculate diversity metrics
        total = len(modules)
        unique_modules = len(counts)
        top_module, top_count = max(counts.items(), key=lambda kv: kv[1])
        top_ratio = top_count / total if total > 0 else 0

        # More lenient thresholds for small files
        if total <= 3:
            # 2-3 elements: allow up to 2 different modules
            if unique_modules > 2:
                summary = ", ".join(
                    f"{name}({count})" for name, count in sorted(counts.items())
                )
                reporter.add_error(
                    stage="intent",
                    code=code,
                    file=file,
                    message=(
                        f"Inconsistent modules in file {file}: {summary}. "
                        f"Consider splitting into separate files per module."
                    ),
                    severity="warning",
                    context={"modules": counts},
                )
        elif total <= 10:
            # 4-10 elements: require at least 40% in top module
            if top_ratio < 0.4:
                summary = ", ".join(
                    f"{name}({count})" for name, count in sorted(counts.items())
                )
                reporter.add_error(
                    stage="intent",
                    code=code,
                    file=file,
                    message=(
                        f"Inconsistent modules in file {file}: {summary}. "
                        f"Top module '{top_module}' only {top_ratio:.0%}. "
                        f"Consider splitting into separate files per module."
                    ),
                    severity="warning",
                    context={"modules": counts},
                )
        else:
            # 11+ elements: require at least 50% in top module
            if top_ratio < 0.5:
                summary = ", ".join(
                    f"{name}({count})" for name, count in sorted(counts.items())
                )
                reporter.add_error(
                    stage="intent",
                    code=code,
                    file=file,
                    message=(
                        f"Inconsistent modules in file {file}: {summary}. "
                        f"Top module '{top_module}' only {top_ratio:.0%}. "
                        f"Consider splitting into separate files per module."
                    ),
                    severity="warning",
                    context={"modules": counts},
                )


def _is_aggregate_contract_file(path: str) -> bool:
    """
    Detect if file is an aggregate contract file (contains multiple modules).

    Aggregate files are top-level files that collect all contracts of a type:
    - domain/entities.yaml (all entities from all modules)
    - app/commands.yaml (all commands from all modules)
    - app/queries.yaml (all queries from all modules)

    vs. module-specific files:
    - domain/payments/entities.yaml (only payment entities)
    - app/payments/commands.yaml (only payment commands)
    """
    # Try dynamic inference first
    try:
        from midicoder.contract.schema_helper import infer_file_scope_traits

        traits = infer_file_scope_traits(path)
        return bool(traits.get("is_aggregate_contract_file"))
    except Exception:
        pass

    # Fallback: heuristic detection
    normalized = path.replace("\\", "/")
    parts = normalized.split("/")

    # Pattern: "domain/entities.yaml" (2 parts) = aggregate
    # Pattern: "domain/payments/entities.yaml" (3+ parts) = module-specific
    if len(parts) == 2:
        # Top-level files in domain/, app/, api/ are typically aggregates
        container = parts[0]
        if container in {"domain", "app", "api", "policy", "rules", "scenarios"}:
            return True

    # If file has module subfolder, it's module-specific
    if len(parts) >= 3:
        # Example: domain/payments/entities.yaml
        # parts[1] is likely the module name
        return False

    # Default: not aggregate (be conservative)
    return False


def _validate_cross_module_dependencies(ir: IR, reporter: Any, code: str) -> None:
    entity_modules = {
        entity.id: entity.intent.module
        for entity in ir.modules.domain.entities
        if entity.intent and entity.intent.module
    }

    for command in ir.modules.application.commands:
        if not command.intent or not command.intent.module:
            continue
        own_module = command.intent.module
        refs = []
        for fetch in command.fetches:
            if fetch.type in {"Entity", "Unknown"}:
                target_module = entity_modules.get(fetch.id)
                if target_module:
                    refs.append(target_module)

        if not refs:
            continue

        counts: dict[str, int] = {}
        for module in refs:
            if module == own_module:
                continue
            counts[module] = counts.get(module, 0) + 1

        if not counts:
            continue

        total_refs = len(refs)
        total_external_refs = sum(counts.values())
        top_module, top_count = max(counts.items(), key=lambda kv: kv[1])
        # Avoid noisy "heavy dependency" signals when a command only touches
        # one cross-module entity (a common and acceptable pattern).
        if (
            total_refs >= 3
            and total_external_refs >= 2
            and top_count >= 2
            and (top_count / total_refs) >= 0.6
        ):
            reporter.add_error(
                stage="intent",
                code=code,
                file=command.source.file,
                message=(
                    f"Command {command.id} in module {own_module} "
                    f"has heavy dependencies on module {top_module}"
                ),
                severity="info",
                context={"module": top_module, "count": top_count, "total": total_refs},
            )


def _validate_orphan_commands(
    validated_data: dict[str, Any],
    normalizer: Normalizer,
    ir: IR,
    reporter: Any,
    code: str,
) -> None:
    signals = build_kind_signal_index(validated_data, normalizer)

    for command in ir.modules.application.commands:
        has_route = bool(signals.command_routes.get(command.id))
        has_workflow = bool(signals.command_workflows.get(command.id))
        if not has_route and not has_workflow:
            reporter.add_error(
                stage="intent",
                code=code,
                file=command.source.file,
                message=f"Command {command.id} is internal-only (no external exposure)",
                severity="info",
            )
