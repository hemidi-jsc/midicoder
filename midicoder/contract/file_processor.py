"""File-level repair processing and orchestration."""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any

from midicoder.llm.client import call_llm
from midicoder.llm.context_builder import build_context_for_contract_repair


def process_file_feedback_items(
    *,
    paths: Any,
    version: str,
    file_path: str,
    feedback_items: list[Any],
    master_brief: str,
    schema_tree: dict,
    llm_config: dict,
    run_dir: Path,
    file_index: int,
    available_contract_files: list[str] = None,
) -> dict[str, Any]:
    """
    Process multiple feedback items for a single file with comprehensive context.

    This provides better consistency and context than single-item repairs.

    Args:
        paths: MidicoderPaths for file operations
        version: Current version string
        file_path: Target file path relative to contracts/
        feedback_items: List of feedback items for this file
        master_brief: Master brief content
        schema_tree: Schema tree for validation
        llm_config: LLM configuration
        run_dir: Run directory for debug output
        file_index: Index of this file in batch
        available_contract_files: List of available contract files

    Returns:
        Dict with repair results including success status, patches applied, errors
    """
    from midicoder.contract.contract_utils import (
        validate_single_contract_file,
        normalize_contract_path,
    )
    from midicoder.contract.repair_builder import (
        build_direct_repair_prompt,
        extract_existing_ids_from_file,
        extract_available_reference_ids,
        save_repair_debug_files,
    )
    from midicoder.contract.schema_helper import get_comprehensive_schema_for_file
    from midicoder.contract.patch_manager import apply_contract_patches
    from midicoder.contract.yaml_processor import (
        strip_yaml_code_fences,
        parse_repair_plan,
    )
    from midicoder.contract.contract_utils import write_memos
    from midicoder.contract.feedback_processor import update_file_feedback_items_status
    from midicoder.contract.prompt_builder import CONTRACT_REPAIR_SYSTEM_PROMPT

    start_time = time.time()

    try:
        contracts_root = paths.versions / version / "contracts"
        contract_path = normalize_contract_path(contracts_root, file_path)
        target_content = contract_path.read_text(encoding="utf-8")
    except Exception as e:
        return {
            "file_path": file_path,
            "feedback_items": feedback_items,
            "success": False,
            "errors": [f"Failed to read target file: {e}"],
        }

    # Get current validation errors for this specific file only (not entire system)
    current_validation_errors = validate_single_contract_file(contract_path, file_path)

    # Extract existing IDs from fresh target file for consistency
    existing_ids = extract_existing_ids_from_file(contract_path)

    # Extract available reference IDs from dependency files
    available_refs = extract_available_reference_ids(
        contracts_root, current_validation_errors, feedback_items
    )

    # Build comprehensive context for this file with enhanced schema
    context, trace = build_context_for_contract_repair(
        root=paths.root,
        context_dir=paths.context,
        master_brief=master_brief,
        feedback_items=feedback_items,
        schema_tree=schema_tree,
        cache_dir=paths.versions / version / "cache",
        llm_config=llm_config,
        call_llm_func=call_llm,
        contracts_root=contracts_root,
    )

    # Get comprehensive schema information for this file type
    comprehensive_schema = get_comprehensive_schema_for_file(
        schema_tree=schema_tree, file_path=file_path
    )

    # Enhance cross-references with available contract files
    if available_contract_files:
        from midicoder.contract.schema_helper import get_file_cross_references

        file_cross_refs = get_file_cross_references(file_path, available_contract_files)
        comprehensive_schema["cross_references"].update(file_cross_refs)

    # Create comprehensive repair prompt
    prompt = build_direct_repair_prompt(
        version=version,
        master_brief=master_brief,
        file_path=file_path,
        feedback_items=feedback_items,
        target_file_content=target_content,
        current_validation_errors=current_validation_errors,
        existing_ids=existing_ids,
        available_refs=available_refs,
        context=context,
        comprehensive_schema=comprehensive_schema,
    )

    # Save file repair context for debugging
    file_dir = (
        run_dir
        / f"file_{file_index}_{file_path.replace('/', '_').replace('.yaml', '')}"
    )
    save_repair_debug_files(
        debug_dir=file_dir,
        prompt=prompt,
        context=context,
        current_validation_errors=current_validation_errors,
        existing_ids=existing_ids,
        target_content=target_content,
        file_path=file_path,
    )

    # Call LLM for comprehensive file repair
    try:
        response = call_llm(
            llm_config,
            prompt=prompt,
            system=CONTRACT_REPAIR_SYSTEM_PROMPT,
            max_tokens=64000,
        )
        (file_dir / "response.txt").write_text(response.raw, encoding="utf-8")

        # Parse repair plan
        plan = parse_repair_plan(strip_yaml_code_fences(response.content))
        (file_dir / "plan.json").write_text(
            json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        # Apply patches immediately after getting plan
        patch_errors = []
        patched_files = []

        try:
            if "patches" in plan and plan["patches"]:
                patched_files = apply_contract_patches(
                    contracts_root, plan["patches"], errors=patch_errors
                )
                print(
                    f"[file processor] Applied {len(plan['patches'])} patches to {file_path}"
                )

                # Safety net for RBAC semantic pitfalls frequently produced by LLM patches:
                # - unknown typed resource refs (e.g. entity:System)
                # - ownership permissions missing matching ownership policies
                if file_path == "contracts/policy/rbac.yaml":
                    safety_notes = _apply_rbac_repair_safety_fixes(contracts_root)
                    for note in safety_notes:
                        print(f"[file processor] RBAC safety fix: {note}")
                elif file_path in {
                    "contracts/workflows/workflows.yaml",
                    "contracts/app/commands.yaml",
                }:
                    safety_notes = _apply_auth_guard_param_safety_fixes(
                        contracts_root, file_path
                    )
                    for note in safety_notes:
                        print(f"[file processor] Guard safety fix: {note}")

            if "memos" in plan and plan["memos"]:
                write_memos(paths, plan["memos"])
                print(f"[file processor] Wrote {len(plan['memos'])} memo(s)")

        except Exception as exc:
            patch_errors.append(f"Patch application failed: {exc}")

        post_validation_errors = validate_single_contract_file(contract_path, file_path)
        if post_validation_errors:
            for err in post_validation_errors[:3]:
                location = err.get("location", file_path)
                message = err.get("message", "unknown validation error")
                patch_errors.append(
                    f"Post-patch validation failed at {location}: {message}"
                )

        success = len(patch_errors) == 0

        if success:
            print(f"[file processor] File repair: SUCCESS")
        else:
            print(
                f"[file processor] File repair: FAILED - {'; '.join(patch_errors[:2])}"
            )

        # Update feedback status for all items in this file
        feedback_updates = plan.get("feedback_status_updates", [])
        error_msg = "; ".join(patch_errors[:2]) if patch_errors else None
        update_file_feedback_items_status(
            paths=paths,
            version=version,
            feedback_updates=feedback_updates,
            feedback_items=feedback_items,
            success=success,
            error_message=error_msg,
        )

        elapsed_time = time.time() - start_time

        return {
            "file_path": file_path,
            "feedback_items": feedback_items,
            "plan": plan,
            "target_file": file_path,
            "original_content": target_content,
            "success": success,
            "patched_files": patched_files,
            "errors": patch_errors if patch_errors else [],
            "comprehensive_schema_modules": len(
                comprehensive_schema.get("modules", {})
            ),
            "validation_errors_count": len(current_validation_errors),
            "post_validation_errors_count": len(post_validation_errors),
            "elapsed_time": elapsed_time,
        }

    except Exception as exc:
        elapsed_time = time.time() - start_time
        error_msg = f"LLM call failed for file {file_path}: {exc}"

        # Enhanced error information for debugging
        debug_info = {
            "error_message": str(exc),
            "error_type": type(exc).__name__,
            "file_path": file_path,
            "feedback_items_count": len(feedback_items),
            "context_tokens": trace.estimated_tokens if "trace" in locals() else 0,
            "elapsed_time": elapsed_time,
        }

        (file_dir / "error.txt").write_text(error_msg, encoding="utf-8")
        (file_dir / "error_debug.json").write_text(
            json.dumps(debug_info, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        # Check if it's a timeout error and provide specific guidance
        if "timed out" in str(exc).lower() or "timeout" in str(exc).lower():
            timeout_msg = (
                f"LLM request timed out for file {file_path}. "
                f"Context size: {trace.estimated_tokens if 'trace' in locals() else 'unknown'} tokens, "
                f"Feedback items: {len(feedback_items)}. "
                f"Consider reducing context size or splitting into smaller batches."
            )
            print(f"[file processor] TIMEOUT: {timeout_msg}")
            raise RuntimeError(timeout_msg) from exc
        else:
            raise RuntimeError(error_msg) from exc


def _apply_rbac_repair_safety_fixes(contracts_root: Path) -> list[str]:
    """Apply deterministic safety fixes after rbac patching to reduce semantic regressions."""
    from midicoder.commands.base import write_yaml
    from midicoder.contract.contract_utils import (
        extract_ids_from_yaml_list,
        load_yaml_safe,
    )

    notes: list[str] = []
    rbac_path = contracts_root / "policy" / "rbac.yaml"
    if not rbac_path.exists():
        return notes

    rbac_data = load_yaml_safe(rbac_path.read_text(encoding="utf-8"))
    if not isinstance(rbac_data, dict):
        return notes
    access = rbac_data.get("access")
    if not isinstance(access, dict):
        return notes
    permissions = access.get("permissions")
    if not isinstance(permissions, list):
        return notes

    entity_ids = _load_ids_from_file(
        contracts_root / "domain" / "entities.yaml", "entities"
    )
    command_ids = _load_ids_from_file(
        contracts_root / "app" / "commands.yaml", "commands"
    )
    query_ids = _load_ids_from_file(contracts_root / "app" / "queries.yaml", "queries")
    projection_ids = _load_ids_from_file(
        contracts_root / "app" / "projections.yaml", "projections"
    )
    known_targets_by_kind = {
        "entity": entity_ids,
        "command": command_ids,
        "query": query_ids,
        "projection": projection_ids,
    }

    rbac_changed = False
    for permission in permissions:
        if not isinstance(permission, dict):
            continue
        permission_id = str(permission.get("id", "")).strip()
        resource = str(permission.get("resource", "")).strip()
        if ":" not in resource:
            continue
        kind, ref = [part.strip() for part in resource.split(":", 1)]
        kind = kind.lower()
        if kind not in known_targets_by_kind:
            continue
        target_ids = known_targets_by_kind[kind]
        if ref in target_ids:
            continue

        fallback_resource = _fallback_document_resource(permission_id, ref)
        permission["resource"] = fallback_resource
        rbac_changed = True
        notes.append(
            f"Re-mapped unknown {kind} target '{ref}' in permission '{permission_id}' to '{fallback_resource}'"
        )

    policies_path = contracts_root / "policy" / "policies.yaml"
    policies_data = (
        load_yaml_safe(policies_path.read_text(encoding="utf-8"))
        if policies_path.exists()
        else {}
    )
    if not isinstance(policies_data, dict):
        policies_data = {}
    policies = policies_data.get("policies")
    if not isinstance(policies, list):
        policies = []
        policies_data["policies"] = policies

    policies_changed = False
    for permission in permissions:
        if not isinstance(permission, dict):
            continue
        permission_id = str(permission.get("id", "")).strip()
        if not _is_ownership_permission_id(permission_id):
            continue

        matching_policies = [
            policy
            for policy in policies
            if isinstance(policy, dict)
            and _policy_mentions_permission_id(policy, permission_id)
        ]
        if not matching_policies:
            resource = str(permission.get("resource", "")).strip()
            scope = _scope_from_permission_resource(resource)
            policies.append(
                {
                    "id": f"{permission_id}_ownership_policy",
                    "description": f"Ownership policy for permission {permission_id}",
                    "scope": scope,
                    "conditions": [
                        {
                            "field": "actor.id",
                            "op": "eq",
                            "value": "actor.id",
                        }
                    ],
                    "effects": [
                        {
                            "type": "allow",
                            "params": {},
                        }
                    ],
                    "tags": [permission_id, "ownership"],
                    "source": "auto-generated by contract repair safety fix",
                }
            )
            policies_changed = True
            notes.append(
                f"Added missing ownership policy for permission '{permission_id}'"
            )
            continue

        if not any(
            _policy_has_ownership_condition_dict(policy) for policy in matching_policies
        ):
            first_policy = matching_policies[0]
            conditions = first_policy.get("conditions")
            if not isinstance(conditions, list):
                first_policy["conditions"] = []
                conditions = first_policy["conditions"]
            conditions.append(
                {
                    "field": "actor.id",
                    "op": "eq",
                    "value": "actor.id",
                }
            )
            policies_changed = True
            notes.append(
                f"Added explicit ownership condition to policy '{first_policy.get('id', 'unknown')}'"
            )

    if rbac_changed:
        write_yaml(rbac_path, rbac_data)
    if policies_changed:
        write_yaml(policies_path, policies_data)

    return notes


def _load_ids_from_file(path: Path, list_name: str) -> set[str]:
    from midicoder.contract.contract_utils import (
        extract_ids_from_yaml_list,
        load_yaml_safe,
    )

    if not path.exists():
        return set()
    data = load_yaml_safe(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return set()
    return set(extract_ids_from_yaml_list(data, list_name))


def _fallback_document_resource(permission_id: str, ref: str) -> str:
    base = "system_logs" if "log" in permission_id.lower() else ref
    normalized = re.sub(r"[^a-z0-9]+", "_", base.strip().lower()).strip("_")
    if not normalized:
        normalized = "resource"
    return f"document:{normalized}"


def _is_ownership_permission_id(permission_id: str) -> bool:
    lower_id = permission_id.lower()
    patterns = (
        "view_own_",
        "read_own_",
        "write_own_",
        "manage_own_",
        "delete_own_",
        "own_",
    )
    return lower_id.startswith(patterns)


def _policy_mentions_permission_id(policy: dict[str, Any], permission_id: str) -> bool:
    permission_id_norm = permission_id.lower()
    policy_id = str(policy.get("id", "")).lower()
    if permission_id_norm in policy_id:
        return True

    tags = policy.get("tags")
    if isinstance(tags, list):
        for tag in tags:
            if str(tag).lower() == permission_id_norm:
                return True

    source = policy.get("source")
    if source and permission_id_norm in str(source).lower():
        return True
    return False


def _policy_has_ownership_condition_dict(policy: dict[str, Any]) -> bool:
    conditions = policy.get("conditions")
    if not isinstance(conditions, list):
        return False
    for condition in conditions:
        if not isinstance(condition, dict):
            continue
        field = str(condition.get("field", "")).lower()
        op = str(condition.get("op", "")).lower()
        value = str(condition.get("value", "")).lower()
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


def _scope_from_permission_resource(resource: str) -> str:
    if ":" not in resource:
        return "global"
    kind, ref = [part.strip() for part in resource.split(":", 1)]
    kind = kind.lower()
    if (
        kind in {"entity", "command", "query", "workflow", "projection", "integration"}
        and ref
    ):
        return f"{kind}:{ref}"
    return "global"


def _apply_auth_guard_param_safety_fixes(
    contracts_root: Path, file_path: str
) -> list[str]:
    """Normalize auth guard params when model emits list in singular fields."""
    from midicoder.commands.base import write_yaml
    from midicoder.contract.contract_utils import load_yaml_safe

    notes: list[str] = []
    relative = file_path.replace("contracts/", "", 1)
    target_path = contracts_root / relative
    if not target_path.exists():
        return notes

    data = load_yaml_safe(target_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return notes

    changed = False

    def normalize_guard(guard: Any, location: str) -> None:
        nonlocal changed
        if not isinstance(guard, dict):
            return
        guard_id = str(guard.get("id", "")).strip()
        params = guard.get("params")
        if not isinstance(params, dict):
            return

        if guard_id == "auth.role":
            role_value = params.get("role")
            if isinstance(role_value, list):
                params.pop("role", None)
                params["roles"] = role_value
                changed = True
                notes.append(f"{location}: converted params.role(list) -> params.roles")

        if guard_id == "auth.permission":
            permission_value = params.get("permission")
            if isinstance(permission_value, list):
                params.pop("permission", None)
                params["permissions"] = permission_value
                changed = True
                notes.append(
                    f"{location}: converted params.permission(list) -> params.permissions"
                )

    commands = data.get("commands")
    if isinstance(commands, list):
        for i, command in enumerate(commands):
            if not isinstance(command, dict):
                continue
            guards = command.get("guards")
            if not isinstance(guards, list):
                continue
            for g, guard in enumerate(guards):
                normalize_guard(guard, f"commands[{i}].guards[{g}]")

    workflows = data.get("workflows")
    if isinstance(workflows, list):
        for i, workflow in enumerate(workflows):
            if not isinstance(workflow, dict):
                continue
            transitions = workflow.get("transitions")
            if not isinstance(transitions, list):
                continue
            for t, transition in enumerate(transitions):
                if not isinstance(transition, dict):
                    continue
                guards = transition.get("guards")
                if not isinstance(guards, list):
                    continue
                for g, guard in enumerate(guards):
                    normalize_guard(
                        guard, f"workflows[{i}].transitions[{t}].guards[{g}]"
                    )

    if changed:
        write_yaml(target_path, data)
    return notes
