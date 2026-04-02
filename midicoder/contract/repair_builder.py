"""Repair prompt building and helper functions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def build_direct_repair_prompt(
    *,
    version: str,
    master_brief: str,
    file_path: str,
    feedback_items: list[Any],
    target_file_content: str,
    current_validation_errors: list[dict],
    existing_ids: dict[str, list[str]],
    available_refs: dict[str, list[str]],
    context: dict[str, Any],
    comprehensive_schema: dict,
) -> str:
    """Build a streamlined repair prompt using 3-step workflow and enhanced schema context."""
    is_multi_item = len(feedback_items) > 1
    first_item = feedback_items[0]

    items_summary = []
    patch_locations = []

    for i, item in enumerate(feedback_items, 1):
        target_item_id = get_target_item_id(target_file_content, item.location)
        if not target_item_id:
            target_item_id = (
                fallback_target_item_id(item.location, item.file) or "unknown"
            )

        patch_location = get_patch_location_template(item.location, target_item_id)
        if target_item_id != "unknown":
            patch_location = patch_location.replace("ITEM_ID", target_item_id)
        patch_locations.append(patch_location)

        location_format = explain_location_format(item.location)

        items_summary.append(
            f"""
**Item {i}: {item.id}**
- **Issue**: {item.issue}
- **Location**: `{item.location}` → patch as `{patch_location}`
- **Format**: {location_format}"""
        )

    schema_cheatsheet = extract_schema_cheatsheet_for_debugging(context, file_path)

    context_usage = []
    if "symbols" in context:
        if isinstance(context["symbols"], dict):
            symbols_count = len(context["symbols"].get("entities", [])) + len(
                context["symbols"].get("classes", [])
            )
        else:
            symbols_count = len(context["symbols"]) if context["symbols"] else 0
        context_usage.append(f"- **symbols**: {symbols_count} real names from codebase")

    if "exemplars" in context:
        if isinstance(context["exemplars"], dict):
            exemplars_count = len(context["exemplars"].get("patterns", []))
        else:
            exemplars_count = len(context["exemplars"]) if context["exemplars"] else 0
        context_usage.append(f"- **exemplars**: {exemplars_count} code patterns")

    if "profile_summary" in context and "stack" in context["profile_summary"]:
        stack_info = context["profile_summary"]["stack"]
        context_usage.append(f"- **profile_summary.stack**: {stack_info}")

    if "memos" in context and isinstance(context["memos"], list):
        memos_count = len(context["memos"])
        if memos_count > 0:
            context_usage.append(f"- **memos**: {memos_count} learned patterns")

    title = (
        f"# File-Level Contract Repair ({len(feedback_items)} Items)"
        if is_multi_item
        else "# Contract Repair Task"
    )
    mission = (
        f"Execute 3-step repair for **{len(feedback_items)} items** in `{file_path}`"
        if is_multi_item
        else f"Execute 3-step repair for `{first_item.id}` in `{file_path}`"
    )

    from midicoder.contract.contract_utils import format_validation_errors

    validation_errors_text = format_validation_errors(current_validation_errors)

    return "\n".join(
        [
            title,
            "",
            mission,
            "",
            "## Step 1: Analyze Issues 🔍",
            "",
            "**Feedback Items to Fix:**",
            "\n".join(items_summary),
            "",
            "**Schema Context (schema_cheatsheet):**",
            "```json",
            json.dumps(schema_cheatsheet, indent=2, ensure_ascii=False),
            "```",
            "",
            "**Context for Quality:**",
            "\n".join(context_usage) if context_usage else "No additional context.",
            "",
            "**Current Validation Errors:**",
            validation_errors_text,
            "",
            "## Step 2: Generate Fixes 🔧",
            "",
            "**Current File Content:**",
            "```yaml",
            target_file_content,
            "```",
            "",
            "**Existing IDs:**",
            "\n".join([f"- **{k}**: {', '.join(v)}" for k, v in existing_ids.items()])
            if existing_ids
            else "None.",
            "",
            "**Available Reference IDs:**",
            "\n".join([f"- **{k}**: {', '.join(v)}" for k, v in available_refs.items()])
            if available_refs
            else "None needed.",
            "",
            "## Step 3: Update Status ✅",
            "",
            "**CRITICAL: Generate ONLY pure YAML output (no markdown, no explanations, no code fences)**",
            "",
            "Expected output format (YAML only):",
            "",
            "```yaml",
            "patches:",
        ]
        + [
            f'  - file: "{file_path}"\n    kind: "replace_node"\n    location: "{loc}"\n    new_content: |\n      # Complete YAML content here'
            for loc in patch_locations
        ]
        + [
            "",
            "feedback_status_updates:",
        ]
        + [
            f'  - id: "{item.id}"\n    status: "done"\n    last_error: null'
            for item in feedback_items
        ]
        + [
            "",
            "memos:",
            '  - id: "SCHEMA_LESSON_[type]_[number]"',
            '    text: "Detailed learning about schema violations and fixes"',
            '  - id: "PROJECT_PATTERN_[domain]_[number]"',
            '    text: "Observed patterns from actual project code"',
            "```",
            "",
            "**Output Requirements:**",
            f"✅ Return ONLY the YAML structure above (no markdown headers, no explanations)",
            f"✅ Fix all {len(feedback_items)} feedback items with exact patch locations",
            "✅ Use schema_cheatsheet for 100% schema compliance",
            "✅ ONLY use IDs from 'Available Reference IDs' - never invent new ones",
            "✅ Use symbols for real names (not placeholders)",
            "✅ Generate learning memos with specific patterns discovered",
        ]
    )


def get_target_item_id(target_file_content: str, location: str) -> str | None:
    """Pre-calculate target item ID from feedback location."""
    from midicoder.contract.contract_utils import load_yaml_safe

    data = load_yaml_safe(target_file_content)
    if data is None:
        return None

    try:
        parts = location.split(".")
        current = data

        for i, part in enumerate(parts):
            if part.isdigit():
                index = int(part)
                if isinstance(current, list) and 0 <= index < len(current):
                    target_item = current[index]
                    if isinstance(target_item, dict):
                        if "id" in target_item:
                            return str(target_item["id"])
                        elif "method" in target_item and "path" in target_item:
                            method = target_item.get("method", "")
                            path = target_item.get("path", "")
                            return (
                                f"{method}_{path}".replace("/", "_")
                                .replace("{", "")
                                .replace("}", "")
                            )
                        else:
                            return f"item_{index}"
                break
            else:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    break
        return None
    except Exception:
        return None


def fallback_target_item_id(location: str, file_path: str) -> str | None:
    return "MALFORMED_YAML_USE_NUMERIC"


def get_patch_location_template(
    location: str, target_item_id: str | None = None
) -> str:
    """Generate patch location template from feedback location."""
    parts = location.split(".")

    for i, part in enumerate(parts):
        if part.isdigit():
            path_to_array = ".".join(parts[:i])

            if target_item_id == "MALFORMED_YAML_USE_NUMERIC":
                return f"{path_to_array}.{part}"
            elif target_item_id and any(
                target_item_id.startswith(p)
                for p in ["GET_", "POST_", "PUT_", "DELETE_", "item_", "route_"]
            ):
                return f"{path_to_array}.{part}"
            else:
                return f"{path_to_array}[id=ITEM_ID]"

    return location


def explain_location_format(location: str) -> str:
    """Explain feedback location format."""
    if "." in location:
        parts = location.split(".")
        explanation_parts = []

        for i, part in enumerate(parts):
            if part.isdigit():
                prev_part = parts[i - 1] if i > 0 else ""
                explanation_parts.append(f"index {part} in {prev_part}")
            else:
                explanation_parts.append(part)

        return f"Navigate: {' → '.join(explanation_parts)}"
    return f"Simple field: {location}"


def extract_existing_ids_from_file(contract_path: Path) -> dict[str, list[str]]:
    """Extract existing IDs from contract file."""
    from midicoder.contract.contract_utils import (
        extract_ids_from_yaml_list,
        load_yaml_safe,
    )

    try:
        content = contract_path.read_text(encoding="utf-8")
        data = load_yaml_safe(content)

        if data is None:
            return {}

        existing_ids = {}
        common_lists = [
            "commands",
            "queries",
            "entities",
            "errors",
            "events",
            "routes",
            "terms",
        ]

        for list_name in common_lists:
            ids = extract_ids_from_yaml_list(data, list_name)
            if ids:
                existing_ids[list_name] = ids

        # Special handling for nested glossary.terms
        if "glossary" in data and isinstance(data["glossary"], dict):
            ids = extract_ids_from_yaml_list(data["glossary"], "terms")
            if ids:
                existing_ids["glossary.terms"] = ids

        return existing_ids
    except Exception:
        return {}


def extract_available_reference_ids(
    contracts_root: Path,
    current_validation_errors: list[dict],
    feedback_items: list[Any],
) -> dict[str, list[str]]:
    """Extract available reference IDs from dependency files."""
    from midicoder.contract.reference_loader import collect_reference_catalog

    reference_ids: dict[str, list[str]] = collect_reference_catalog(contracts_root)
    needed_refs = set()

    for error in current_validation_errors:
        message = error.get("message", "").lower()
        if "unknown error" in message:
            needed_refs.add("errors")
        elif "unknown entity" in message:
            needed_refs.add("entities")
        elif "unknown event" in message:
            needed_refs.add("events")
        elif "unknown command" in message or "unknown query" in message:
            needed_refs.add("commands")
            needed_refs.add("queries")

    for item in feedback_items:
        issue = getattr(item, "issue", "").lower()
        if "unknown error" in issue:
            needed_refs.add("errors")
        elif "unknown entity" in issue:
            needed_refs.add("entities")
        elif "unknown event" in issue:
            needed_refs.add("events")
        elif "unknown command" in issue:
            needed_refs.add("commands")
            needed_refs.add("queries")

    ref_file_map = {
        "errors": "domain/errors.yaml",
        "entities": "domain/entities.yaml",
        "events": "domain/events.yaml",
        "commands": "app/commands.yaml",
        "queries": "app/queries.yaml",
    }

    for ref_type in needed_refs:
        file_path = ref_file_map.get(ref_type)
        if not file_path:
            continue

        full_path = contracts_root / file_path
        if not full_path.exists():
            continue

        try:
            from midicoder.contract.contract_utils import (
                extract_ids_from_yaml_list,
                load_yaml_safe,
            )

            content = full_path.read_text(encoding="utf-8")
            data = load_yaml_safe(content)

            if data is not None:
                ids = extract_ids_from_yaml_list(data, ref_type)
                if ids:
                    reference_ids[f"available_{ref_type}"] = sorted(ids)
        except Exception:
            continue

    return reference_ids


def save_repair_debug_files(
    debug_dir: Path,
    prompt: str,
    context: dict,
    current_validation_errors: list[dict],
    existing_ids: dict,
    target_content: str,
    file_path: str,
) -> None:
    """Save essential repair debugging files."""
    debug_dir.mkdir(exist_ok=True)

    schema_cheatsheet = extract_schema_cheatsheet_for_debugging(context, file_path)

    (debug_dir / "prompt.txt").write_text(prompt, encoding="utf-8")
    (debug_dir / "context.json").write_text(
        json.dumps(context, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (debug_dir / "validation_errors.json").write_text(
        json.dumps(current_validation_errors, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (debug_dir / "existing_ids.json").write_text(
        json.dumps(existing_ids, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (debug_dir / "original_content.yaml").write_text(target_content, encoding="utf-8")
    (debug_dir / "schema_used_in_prompt.json").write_text(
        json.dumps(schema_cheatsheet, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def extract_schema_cheatsheet_for_debugging(context: dict, file_path: str) -> dict:
    """Extract the actual schema_cheatsheet that was used in prompt for debugging."""
    schema_cheatsheet = context.get("schema_cheatsheet", {})
    if not schema_cheatsheet:
        from midicoder.llm.context_builder import slice_schema_for_targets

        file_without_contracts = (
            file_path.replace("contracts/", "")
            if file_path.startswith("contracts/")
            else file_path
        )
        sliced_schema = slice_schema_for_targets(
            context.get("schema_tree", {}), [file_without_contracts]
        )
        schema_cheatsheet = {
            "version": sliced_schema.get("version", "v0"),
            "description": f"Schema context for {file_path} (sliced)",
            "modules": sliced_schema.get("modules", {}),
            "catalogs": sliced_schema.get("catalogs", {}),
        }
    return schema_cheatsheet


def get_file_validation_errors(contract_path: Path, file_path: str) -> list[dict]:
    """Get validation errors for a specific file."""
    from midicoder.contract.contract_utils import validate_single_contract_file

    try:
        return validate_single_contract_file(contract_path, file_path)
    except Exception as exc:
        return [
            {"location": str(contract_path), "message": f"Validation failed: {exc}"}
        ]
