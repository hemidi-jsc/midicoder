"""Schema extraction and helper functions for contract operations."""

from __future__ import annotations

from typing import Any


def get_comprehensive_schema_for_file(*, schema_tree: dict, file_path: str) -> dict:
    """
    Extract comprehensive schema context for contract file repair.

    Reuses the same schema slicing logic as contract generation to ensure
    consistency and compatibility with schema tree structure.
    """
    try:
        # Import the slice function from context_builder to reuse logic
        from midicoder.llm.context_builder import slice_schema_for_targets

        # Use the same slicing logic as contract generation
        sliced_schema = slice_schema_for_targets(schema_tree, [file_path])

        # Enhanced schema cheatsheet with additional repair-specific context
        schema_cheatsheet = {
            "version": sliced_schema.get("version", "v0"),
            "description": f"Schema context for {file_path} repair (using contract gen logic)",
            "modules": sliced_schema.get("modules", {}),
            "catalogs": {},
            "cross_references": {},
            "repair_enhancements": {},
        }

        # Extract catalogs from sliced schema modules (authoritative for target file).
        for module_data in schema_cheatsheet["modules"].values():
            if not isinstance(module_data, dict):
                continue
            module_catalogs = module_data.get("catalogs", {})
            if not isinstance(module_catalogs, dict):
                continue
            for key, value in module_catalogs.items():
                if value is None:
                    continue
                if isinstance(value, list):
                    schema_cheatsheet["catalogs"][key] = value
                elif isinstance(value, set):
                    schema_cheatsheet["catalogs"][key] = sorted(
                        str(item) for item in value
                    )
                else:
                    schema_cheatsheet["catalogs"][key] = [str(value)]

        # Add file-specific cross-references dynamically
        file_cross_refs = get_file_cross_references(file_path)
        for cross_ref_type, cross_ref_info in file_cross_refs.items():
            schema_cheatsheet["cross_references"][cross_ref_type] = cross_ref_info

        # Add repair-specific enhancements
        schema_cheatsheet["repair_enhancements"] = {
            "validation_rules": get_file_validation_rules(file_path),
            "common_patterns": {
                "id_pattern": {
                    "type": "string",
                    "pattern": "^[A-Za-z][A-Za-z0-9_]*$",
                    "description": "Identifier must start with letter, contain only alphanumeric and underscore",
                },
                "description_pattern": {
                    "type": "string",
                    "min_length": 10,
                    "description": "Meaningful description of functionality or purpose",
                },
            },
            "extraction_summary": {
                "file_path": file_path,
                "modules_found": len(schema_cheatsheet["modules"]),
                "catalogs_found": len(schema_cheatsheet["catalogs"]),
                "cross_refs": len(schema_cheatsheet["cross_references"]),
                "reused_contract_gen_logic": True,
            },
        }

        return schema_cheatsheet

    except ImportError as import_exc:
        print(
            f"[schema extraction] Warning: Could not import slice_schema_for_targets: {import_exc}"
        )
        return get_fallback_schema_for_file(
            schema_tree, file_path, f"Import error: {import_exc}"
        )
    except Exception as exc:
        print(
            f"[schema extraction] Error: Failed to extract schema for {file_path}: {exc}"
        )
        return get_fallback_schema_for_file(
            schema_tree, file_path, f"Extraction error: {exc}"
        )


def get_file_cross_references(
    file_path: str, available_files: list[str] = None
) -> dict[str, dict]:
    """
    Get cross-reference information dynamically based on file patterns and available files.

    Args:
        file_path: Target file being repaired
        available_files: List of available contract files (from cache analysis)
    """
    from midicoder.contract.contract_utils import determine_file_type

    cross_refs = {}
    file_type = determine_file_type(file_path)

    # If available_files not provided, use common patterns
    if available_files is None:
        available_files = []

    # Create dynamic source mapping based on available files
    source_mapping = {}
    for available_file in available_files:
        available_file_type = determine_file_type(available_file)
        if available_file_type != "unknown":
            source_mapping[available_file_type] = available_file

    # Fallback to generic patterns if no available_files
    if not source_mapping:
        source_mapping = {
            "errors": "errors file",
            "entities": "entities file",
            "commands": "commands file",
            "queries": "queries file",
            "events": "events file",
        }

    # Dynamic cross-reference detection based on file type
    if file_type in {"commands", "queries"}:
        if "errors" in source_mapping:
            cross_refs["available_errors"] = {
                "description": "Available error definitions that can be referenced",
                "source": source_mapping["errors"],
                "format": "ErrorId (e.g., UserNotFound, InvalidInput)",
            }
        if "entities" in source_mapping:
            cross_refs["available_entities"] = {
                "description": "Available entity definitions that can be referenced",
                "source": source_mapping["entities"],
                "format": "EntityId (e.g., User, Product, Order)",
            }

    if file_type == "http":
        if "commands" in source_mapping:
            cross_refs["available_commands"] = {
                "description": "Available command definitions that can be referenced",
                "source": source_mapping["commands"],
                "format": "CommandId (e.g., CreateUser, UpdateProduct)",
            }
        if "queries" in source_mapping:
            cross_refs["available_queries"] = {
                "description": "Available query definitions that can be referenced",
                "source": source_mapping["queries"],
                "format": "QueryId (e.g., GetUser, ListProducts)",
            }
        if "errors" in source_mapping:
            cross_refs["available_errors"] = {
                "description": "Available error definitions for HTTP responses",
                "source": source_mapping["errors"],
                "format": "ErrorId (e.g., UserNotFound, ValidationError)",
            }

    if file_type in {"events", "rules", "workflows"}:
        if "entities" in source_mapping:
            cross_refs["available_entities"] = {
                "description": "Available entity definitions that can be referenced",
                "source": source_mapping["entities"],
                "format": "EntityId (e.g., User, Product, Order)",
            }

    return cross_refs


def get_file_validation_rules(file_path: str) -> dict:
    """
    Get file-specific validation rules and constraints dynamically based on file type.
    """
    from midicoder.contract.contract_utils import determine_file_type

    validation_rules: dict[str, Any] = {
        "source_of_truth": "schema_cheatsheet.modules",
        "guidance": "Do not assume generic required fields; follow exact Pydantic fields/types from sliced schema.",
        "file_type": None,
    }

    file_type = determine_file_type(file_path)
    validation_rules["file_type"] = file_type

    root_field_hints = {
        "info": ["info"],
        "glossary": ["glossary"],
        "entities": ["entities"],
        "value_objects": ["value_objects"],
        "enums": ["enums"],
        "errors": ["errors"],
        "events": ["events"],
        "commands": ["commands"],
        "queries": ["queries"],
        "projections": ["projections"],
        "http": ["routes"],
        "graphql": ["api"],
        "rules": ["rules"],
        "workflows": ["workflows"],
        "persistence": ["tables", "datasources"],
        "integrations": ["integrations", "operations", "storages", "webhooks"],
        "policies": ["policies"],
        "access_policy": ["access"],
        "security": ["security"],
        "reliability": ["reliability_policies"],
        "observability": ["observability"],
        "profiles": ["profiles"],
        "secrets": ["secrets"],
        "testing": ["tests"],
    }
    hints = root_field_hints.get(file_type)
    if hints:
        validation_rules["root_field_hints"] = hints

    return validation_rules


def get_fallback_schema_for_file(
    schema_tree: dict, file_path: str, error_msg: str
) -> dict:
    """
    Fallback schema extraction when main method fails.
    """
    return {
        "version": "v0",
        "description": f"Fallback schema for {file_path}",
        "modules": {},
        "catalogs": {},
        "cross_references": {},
        "repair_enhancements": {
            "fallback": True,
            "warning": "Schema extraction failed. Do not infer structure from generic patterns.",
            "error": error_msg,
            "schema_tree_keys": list(schema_tree.keys())
            if isinstance(schema_tree, dict)
            else [],
            "extraction_summary": {
                "file_path": file_path,
                "modules_found": 0,
                "catalogs_found": 0,
                "cross_refs": 0,
                "reused_contract_gen_logic": False,
            },
        },
    }
