"""Main entrypoint for code plan phase."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .emitter import (
    build_plan_meta,
    build_plan_stub,
    build_pseudo_struct,
    build_required_files,
    emit_code_plan_item,
)
from .integration import build_integration_context, build_plan_contracts
from .loaders import load_profile, load_seams, load_virtual_seams, preflight_check
from .logging import emit_error, emit_info, emit_success, emit_warning
from .models import BuildResult, CodePlanItem
from .quality import validate_plan_quality
from .resolution import (
    build_dependency_graph,
    map_target,
    resolve_stack,
    resolve_suggested_paths,
    traverse_graph_for_target,
)
from .validation import collect_ir_refs, collect_ir_symbol_ids, iter_plan_items, validate_typed_id
from .writer import build_index_payload, write_plan_file, write_plan_index


class BuildError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def build_code_plan(
    *,
    ir: dict[str, Any],
    plans_dir: Path,
    version: str,
    context_dir: Path,
    config: dict[str, Any] | None = None,
    strict_mode: bool = False,
) -> BuildResult:
    ok, preflight_errors = preflight_check(context_dir.parent / "versions" / str(version) / "irs" / "ir.json", context_dir)
    if not ok:
        for message in preflight_errors:
            emit_error("E300", "Preflight failed", phase="preflight", action=message)
        raise BuildError("E300", "preflight failed")

    seams = load_seams(context_dir)
    virtual_seams = load_virtual_seams(context_dir)
    profile = load_profile(context_dir)

    stack, stack_warning = resolve_stack(profile, config, seams, virtual_seams)
    warnings: list[str] = []
    errors: list[str] = []
    if stack_warning:
        warnings.append(
            emit_warning(
                "W300",
                "Stack unresolved",
                phase="stack",
                action="fallback to fastapi",
            )
        )

    emit_info("I300", "Build code plan started", phase="build", action=f"stack={stack}")

    nodes, _edges = build_dependency_graph(seams, virtual_seams, ir=ir)
    plans: list[CodePlanItem] = []
    symbol_ids = collect_ir_symbol_ids(ir)
    integration_context = build_integration_context(
        ir=ir,
        seams=seams,
        virtual_seams=virtual_seams,
        profile=profile,
    )

    for item in iter_plan_items(ir):
        if not validate_typed_id(item.id):
            raise BuildError(
                "E311",
                emit_error(
                    "E311",
                    "Invalid typed id format",
                    phase="validation",
                    action="use Type.name",
                ),
            )

        target = map_target(stack, item.kind)
        candidates = traverse_graph_for_target(nodes, item)
        suggested_paths, source_kind = resolve_suggested_paths(
            item=item,
            candidates=candidates,
            seams=seams,
            virtual_seams=virtual_seams,
            profile=profile,
            stack=stack,
        )
        if not suggested_paths:
            raise BuildError(
                "E351",
                emit_error(
                    "E351",
                    "suggested_paths is empty",
                    phase="resolve_paths",
                    action="add seam/virtual seam or module_layout",
                ),
            )

        if item.api_contract.get("routes") and source_kind == "fallback":
            raise BuildError(
                "E352",
                emit_error(
                    "E352",
                    "Route exists but endpoint path is unresolved",
                    phase="resolve_paths",
                    action="resolve route-aware endpoint path",
                ),
            )

        if source_kind == "fallback":
            warnings.append(
                emit_warning(
                    "W342",
                    "Anchor unresolved",
                    phase="resolve_paths",
                    action="fallback to convention path",
                )
            )

        pseudo_struct = build_pseudo_struct(item, stack)
        required_files = build_required_files(target, suggested_paths)
        if item.type_name == "Workflow":
            transitions = item.state_contract.get("transitions", [])
            has_state_step = any(step.get("type") == "state_transition" for step in pseudo_struct.get("steps", []))
            if transitions and not has_state_step:
                raise BuildError(
                    "E353",
                    emit_error(
                        "E353",
                        "Workflow transitions exist but pseudo struct has no state step",
                        phase="emit",
                        action="add state_transition step",
                    ),
                )

        (
            integration_contract,
            io_reconciliation,
            security_contract,
            error_contract,
            merge_contract,
        ) = build_plan_contracts(
            item=item,
            target=target,
            pseudo_struct=pseudo_struct,
            suggested_paths=suggested_paths,
            required_files=required_files,
            context=integration_context,
        )

        quality_errors, quality_warnings = validate_plan_quality(
            item=item,
            target=target,
            pseudo_struct=pseudo_struct,
            suggested_paths=suggested_paths,
            required_files=required_files,
            symbol_ids=symbol_ids,
            io_reconciliation=io_reconciliation,
            integration_contract=integration_contract,
            merge_contract=merge_contract,
            security_contract=security_contract,
            strict_mode=strict_mode,
        )
        errors.extend(quality_errors)
        warnings.extend(quality_warnings)

        plans.append(
            emit_code_plan_item(
                ir_ref=item.id,
                target=target,
                pseudo=build_plan_stub(item, stack),
                pseudo_struct=pseudo_struct,
                suggested_paths=suggested_paths,
                required_files=required_files,
                meta=build_plan_meta(item, ir),
                integration_contract=integration_contract,
                io_reconciliation=io_reconciliation,
                security_contract=security_contract,
                error_contract=error_contract,
                merge_contract=merge_contract,
            )
        )

    plan_paths = [write_plan_file(plans_dir, plan) for plan in plans]
    write_plan_index(
        plans_dir,
        build_index_payload(
            str(version),
            plan_paths,
            plans=plans,
            stack=stack,
        ),
    )

    warnings.extend(validate_cross_ir_ref(plans, ir))
    warnings.extend(validate_cross_anchor(plans, seams, virtual_seams))
    merge_errors, merge_warnings = validate_merge_conflicts(plans, strict_mode=strict_mode)
    errors.extend(merge_errors)
    warnings.extend(merge_warnings)
    errors.extend(validate_artifact_count(plans_dir, len(plan_paths)))

    if errors:
        raise BuildError("E390", "; ".join(errors))

    emit_success(
        f"code build completed | items={len(plans)} | warnings={len(warnings)} | errors={len(errors)} | stack={stack}"
    )
    return BuildResult(
        plans=plans,
        plan_paths=plan_paths,
        warnings=warnings,
        errors=errors,
        stack=stack,
    )


def validate_cross_ir_ref(plans: list[CodePlanItem], ir: dict[str, Any]) -> list[str]:
    ir_refs = collect_ir_refs(ir)
    warnings: list[str] = []
    for plan in plans:
        if plan.ir_ref not in ir_refs:
            warnings.append(
                    emit_warning(
                        "W341",
                        "ir_ref not found in IR",
                        phase="cross_validate",
                        action="check planner input",
                    )
                )
    return warnings


def validate_cross_anchor(
    plans: list[CodePlanItem],
    seams: list[dict[str, Any]],
    virtual_seams: list[dict[str, Any]],
) -> list[str]:
    known_anchors = set()
    for seam in seams + virtual_seams:
        group_id = str(seam.get("group_id", "")).strip()
        detail = str(seam.get("detail", "")).strip()
        if group_id:
            known_anchors.add(f"seam:{group_id}")
            known_anchors.add(f"virtual:{group_id}")
        if detail:
            known_anchors.add(detail)

    warnings: list[str] = []
    for plan in plans:
        for path in plan.suggested_paths:
            anchor = path.anchor
            if anchor.startswith("graph:") or anchor.startswith("fallback:"):
                continue
            if anchor.startswith("route:"):
                continue
            if anchor not in known_anchors:
                warnings.append(
                    emit_warning(
                        "W342",
                        "Anchor unresolved",
                        phase="cross_validate",
                        action="fallback to convention path",
                    )
                )
    return warnings


def validate_artifact_count(plans_dir: Path, expected_count: int) -> list[str]:
    actual_count = len(list(plans_dir.rglob("*.code-plan.json")))
    if actual_count != expected_count:
        return [
            emit_error(
                "E390",
                "Artifact count mismatch",
                phase="cross_validate",
                action=f"actual={actual_count}",
            )
        ]
    return []


def validate_merge_conflicts(
    plans: list[CodePlanItem],
    *,
    strict_mode: bool = False,
) -> tuple[list[str], list[str]]:
    path_modes: dict[str, set[str]] = {}
    for plan in plans:
        merge = plan.merge_contract if isinstance(plan.merge_contract, dict) else {}
        mode = str(merge.get("mode", "")).strip()
        ownership = merge.get("ownership")
        if not mode or not isinstance(ownership, list):
            continue
        for file_path in ownership:
            normalized = str(file_path).strip()
            if not normalized:
                continue
            path_modes.setdefault(normalized, set()).add(mode)

    errors: list[str] = []
    warnings: list[str] = []
    for file_path, modes in path_modes.items():
        if len(modes) <= 1:
            continue
        if strict_mode:
            errors.append(
                emit_error(
                    "E403",
                    "merge mode conflicts on shared target file",
                    phase="cross_validate",
                    action=f"file={file_path};modes={','.join(sorted(modes))}",
                )
            )
        else:
            warnings.append(
                emit_warning(
                    "W403",
                    "merge mode conflicts on shared target file",
                    phase="cross_validate",
                    action=f"file={file_path};modes={','.join(sorted(modes))}",
                )
            )
    return errors, warnings
