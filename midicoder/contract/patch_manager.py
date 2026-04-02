"""Patch management for contract repair operations."""

from __future__ import annotations

import re
from io import StringIO
from pathlib import Path
from typing import Any

from midicoder.commands.base import write_yaml

# Constants
SUPPORTED_PATCH_KINDS = ["replace_node", "replace_all", "append", "prepend"]


def _parse_yaml_content(yaml_loader: Any, content: Any) -> Any:
    """
    Parse YAML content if it's a string, otherwise return as-is.

    Args:
        yaml_loader: YAML loader instance
        content: Content to parse (string or already parsed object)

    Returns:
        Parsed content or original content if not a string or if parsing fails
    """
    if isinstance(content, str):
        try:
            return yaml_loader.load(content)
        except Exception:
            # If parsing fails, return as raw string
            return content
    return content


def apply_contract_patches(
    contracts_root: Path,
    patches: list[dict[str, Any]],
    *,
    errors: list[str],
) -> list[str]:
    """Apply patches to contract files."""
    from ruamel.yaml import YAML

    yaml_loader = YAML(typ="safe")
    updated_files: set[Path] = set()

    for patch in patches:
        if not isinstance(patch, dict):
            errors.append("Patch entry must be a mapping.")
            continue

        file_path = patch.get("file")
        kind = patch.get("kind")
        location = patch.get("location")
        has_new_content = "new_content" in patch
        new_content = patch.get("new_content")

        if not file_path or not kind:
            errors.append("Patch entry missing required fields (file, kind).")
            continue

        if kind not in SUPPORTED_PATCH_KINDS:
            errors.append(
                f"Unsupported patch kind: {kind}. Supported: {', '.join(SUPPORTED_PATCH_KINDS)}"
            )
            continue

        if kind in {"replace_node", "append", "prepend"} and not location:
            errors.append(f"Patch kind '{kind}' requires location field.")
            continue

        if not has_new_content:
            errors.append("Patch entry missing new_content field.")
            continue

        try:
            target_path = _normalize_contract_path(contracts_root, str(file_path))
            if not target_path.exists():
                errors.append(
                    f"Patch target not found: {file_path} (resolved to: {target_path})"
                )
                continue
        except Exception as path_exc:
            errors.append(f"Failed to resolve path {file_path}: {path_exc}")
            continue

        # Apply different patch kinds
        success = False
        if kind == "replace_all":
            success = _apply_replace_all_patch(
                target_path, new_content, errors, file_path
            )
        else:
            # For other kinds, need to parse YAML first
            raw = target_path.read_text(encoding="utf-8")

            # First, try to clean malformed YAML
            from midicoder.contract.yaml_processor import clean_malformed_yaml

            cleaned_raw = clean_malformed_yaml(raw)

            try:
                data = yaml_loader.load(cleaned_raw)
            except Exception as yaml_exc:
                # If still malformed after cleaning, use direct text replacement as fallback
                print(
                    f"[patch] YAML parsing failed for {file_path}, using direct text replacement: {yaml_exc}"
                )
                if kind == "replace_node":
                    success = _apply_direct_text_replacement(
                        target_path, str(location), new_content, errors, file_path
                    )
                else:
                    errors.append(
                        f"Cannot apply {kind} patch to malformed YAML: {file_path}, {yaml_exc}"
                    )
                    continue
                if success:
                    updated_files.add(target_path)
                    continue
                else:
                    errors.append(
                        f"Failed to apply patch to malformed YAML: {file_path}, {yaml_exc}"
                    )
                    continue

            if not isinstance(data, dict):
                errors.append(f"Patch target invalid YAML mapping: {file_path}")
                continue

            # Apply patch based on kind using properly parsed YAML
            if kind == "replace_node":
                success = _apply_replace_node_patch(
                    data, str(location), new_content, errors, file_path, yaml_loader
                )
            elif kind == "append":
                success = _apply_append_patch(
                    data, str(location), new_content, errors, file_path, yaml_loader
                )
            elif kind == "prepend":
                success = _apply_prepend_patch(
                    data, str(location), new_content, errors, file_path, yaml_loader
                )
            else:
                errors.append(f"Unsupported patch kind: {kind}")
                continue

            if success:
                # Write back the cleaned and updated data
                write_yaml(target_path, data)
            else:
                continue

        if success:
            updated_files.add(target_path)

    return [path.as_posix() for path in sorted(updated_files)]


def _normalize_contract_path(contracts_root: Path, relative_path: str) -> Path:
    """Normalize contract file path."""
    path_str = relative_path.strip().lstrip("/")
    if path_str.startswith("contracts/"):
        path_str = path_str[len("contracts/") :]
    candidate = (contracts_root / path_str).resolve()
    try:
        candidate.relative_to(contracts_root.resolve())
    except ValueError as exc:
        raise RuntimeError(f"Invalid contract file path: {relative_path}") from exc
    return candidate


def _apply_replace_all_patch(
    target_path: Path, new_content: Any, errors: list[str], file_path: str
) -> bool:
    """Replace entire file content with new content."""
    try:
        if isinstance(new_content, str):
            target_path.write_text(new_content, encoding="utf-8")
        else:
            write_yaml(target_path, new_content)
        return True
    except Exception as exc:
        errors.append(f"Failed to replace all content in {file_path}: {exc}")
        return False


def _apply_replace_node_patch(
    data: dict,
    location: str,
    new_content: Any,
    errors: list[str],
    file_path: str,
    yaml_loader: Any,
) -> bool:
    """Replace a specific node/field in the YAML structure."""
    # Check for array index paths like "commands[0]" or "commands[0].effects[1]"
    if _is_array_index_path(location):
        return _apply_array_index_path_patch(
            data, location, new_content, errors, file_path, yaml_loader
        )
    elif _is_yaml_path(location):
        return _apply_yaml_path_patch(
            data, location, new_content, errors, file_path, yaml_loader
        )
    elif _parse_location_selector(location):
        parsed_location = _parse_location_selector(location)
        list_path, item_id = parsed_location

        items = _navigate_to_nested_path(data, list_path)
        if not isinstance(items, list):
            errors.append(f"Location list not found: {list_path} in {file_path}")
            return False

        replacement = _parse_yaml_content(yaml_loader, new_content)
        replaced = False
        for idx, entry in enumerate(items):
            if isinstance(entry, dict) and entry.get("id") == item_id:
                items[idx] = replacement
                replaced = True
                break
        if not replaced:
            errors.append(f"Item id not found in {file_path}: {item_id}")
            return False

        success = _set_nested_path(data, list_path, items)
        if not success:
            errors.append(f"Failed to update nested path {list_path} in {file_path}")
            return False
        return True
    else:
        # Simple field replacement (top-level or single key)
        # Make sure location doesn't contain array brackets
        if "[" in location and "]" in location:
            # Last-chance fallback: parser can handle mixed field/index paths in some cases
            # even when detector regex is too strict.
            parser_errors: list[str] = []
            if _apply_array_index_path_patch(
                data, location, new_content, parser_errors, file_path, yaml_loader
            ):
                return True
            errors.append(
                f"Invalid location format '{location}' - use proper array index path"
            )
            return False

        replacement = _parse_yaml_content(yaml_loader, new_content)
        data[location] = replacement
        return True


def _apply_append_patch(
    data: dict,
    location: str,
    new_content: Any,
    errors: list[str],
    file_path: str,
    yaml_loader: Any,
) -> bool:
    """Append content to a list at the specified location."""
    target = _navigate_to_location(data, location)

    # Handle missing field - create empty list if field doesn't exist
    if target is None:
        if not _ensure_location_exists(data, location, errors, file_path):
            errors.append(f"Location not found for append: {location} in {file_path}")
            return False
        target = _navigate_to_location(data, location)
        if target is None:
            errors.append(
                f"Failed to create location for append: {location} in {file_path}"
            )
            return False

    if not isinstance(target, list):
        errors.append(
            f"Cannot append to non-list at location {location} in {file_path}"
        )
        return False

    content_to_append = _parse_yaml_content(yaml_loader, new_content)

    if isinstance(content_to_append, list):
        target.extend(content_to_append)
    else:
        target.append(content_to_append)

    return True


def _apply_prepend_patch(
    data: dict,
    location: str,
    new_content: Any,
    errors: list[str],
    file_path: str,
    yaml_loader: Any,
) -> bool:
    """Prepend content to a list at the specified location."""
    target = _navigate_to_location(data, location)

    # Handle missing field - create empty list if field doesn't exist
    if target is None:
        if not _ensure_location_exists(data, location, errors, file_path):
            errors.append(f"Location not found for prepend: {location} in {file_path}")
            return False
        target = _navigate_to_location(data, location)
        if target is None:
            errors.append(
                f"Failed to create location for prepend: {location} in {file_path}"
            )
            return False

    if not isinstance(target, list):
        errors.append(
            f"Cannot prepend to non-list at location {location} in {file_path}"
        )
        return False

    content_to_prepend = _parse_yaml_content(yaml_loader, new_content)

    if isinstance(content_to_prepend, list):
        target[:0] = content_to_prepend
    else:
        target.insert(0, content_to_prepend)

    return True


def _apply_direct_text_replacement(
    target_path: Path,
    location: str,
    new_content: str,
    errors: list[str],
    file_path: str,
) -> bool:
    """Apply patch using direct text replacement for malformed YAML files."""
    try:
        from ruamel.yaml import YAML

        yaml_loader = YAML(typ="safe")

        try:
            replacement_data = yaml_loader.load(new_content)
        except Exception as yaml_exc:
            errors.append(f"Invalid replacement content for {file_path}: {yaml_exc}")
            return False

        if not isinstance(replacement_data, dict):
            errors.append(f"Replacement content must be a dict for {file_path}")
            return False

        array_name = None
        array_index = None
        target_item_id = None

        if "[id=" in location and "]" in location:
            parts = location.split("[id=")
            array_name = parts[0]
            target_item_id = parts[1].replace("]", "")
        else:
            parts = location.split(".")
            if len(parts) >= 2 and parts[-1].isdigit():
                array_name = parts[-2]
                array_index = int(parts[-1])

        if not array_name:
            errors.append(f"Cannot parse location format: {location}")
            return False

        raw_content = target_path.read_text(encoding="utf-8")
        lines = raw_content.splitlines()

        new_lines = []
        in_target_array = False
        current_item_index = -1
        skip_until_next_item = False

        for line in lines:
            if line.strip() == f"{array_name}:":
                in_target_array = True
                new_lines.append(line)
                continue

            if (
                in_target_array
                and line
                and not line.startswith(" ")
                and not line.startswith("\t")
                and ":" in line
            ):
                in_target_array = False
                skip_until_next_item = False

            if in_target_array and line.strip().startswith("- id:"):
                current_item_index += 1

                is_target = False
                if array_index is not None:
                    is_target = current_item_index == array_index
                elif target_item_id is not None:
                    match = re.match(r"\s*-\s+id:\s*(\S+)", line)
                    if match:
                        line_item_id = match.group(1)
                        is_target = line_item_id == target_item_id

                if is_target:
                    yaml_formatter = YAML()
                    yaml_formatter.default_flow_style = False
                    yaml_formatter.indent(mapping=2, sequence=4, offset=2)

                    stream = StringIO()
                    yaml_formatter.dump([replacement_data], stream)
                    formatted_yaml = stream.getvalue()

                    formatted_lines = formatted_yaml.splitlines()
                    for i, formatted_line in enumerate(formatted_lines):
                        if i == 0:
                            continue
                        if formatted_line.strip():
                            new_lines.append("  " + formatted_line)

                    skip_until_next_item = True
                    continue
                else:
                    new_lines.append(line)
            elif in_target_array and skip_until_next_item:
                if line.strip().startswith("- id:"):
                    skip_until_next_item = False
                    new_lines.append(line)
                continue
            else:
                new_lines.append(line)

        target_path.write_text("\n".join(new_lines), encoding="utf-8")
        return True

    except Exception as exc:
        errors.append(f"Direct text replacement failed for {file_path}: {exc}")
        return False


def _is_array_index_path(location: str) -> bool:
    """Check if location is an array index path like 'commands[0]' or 'commands[0].errors[2]'."""
    # Match patterns like:
    # - commands[0]
    # - access.bindings[0].permissions[1]
    # - commands[0].errors[2]
    # - commands[0].effects
    # Require at least one numeric array index anywhere in the path.
    pattern = r"^(?=.*\[\d+\])[a-zA-Z_][a-zA-Z0-9_]*(\[\d+\])?(\.[a-zA-Z_][a-zA-Z0-9_]*(\[\d+\])?)*$"
    return bool(re.match(pattern, location))


def _is_yaml_path(location: str) -> bool:
    """Check if location is a YAML path like 'glossary.terms.26.examples.0'."""
    return "." in location and "[" not in location


def _parse_location_selector(location: str) -> tuple[str, str] | None:
    """Parse location selector like 'entities[id=User]'."""
    if "[" not in location or "]" not in location:
        return None
    prefix, rest = location.split("[", 1)
    selector = rest.rstrip("]")
    if "=" not in selector:
        return None
    key, value = selector.split("=", 1)
    if key != "id":
        return None
    return prefix, value


def _navigate_to_location(data: dict, location: str) -> Any:
    """Navigate to a location in YAML data and return the target object."""
    if "." not in location and "[" not in location:
        return data.get(location)

    if "." in location and "[" not in location:
        parts = location.split(".")
        current = data
        for part in parts:
            if part.isdigit():
                index = int(part)
                if not isinstance(current, list) or index >= len(current):
                    return None
                current = current[index]
            else:
                if not isinstance(current, dict) or part not in current:
                    return None
                current = current[part]
        return current

    parsed_location = _parse_location_selector(location)
    if parsed_location:
        list_path, item_id = parsed_location
        items = _navigate_to_nested_path(data, list_path)
        if isinstance(items, list):
            return items

    return None


def _ensure_location_exists(
    data: dict, location: str, errors: list[str], file_path: str
) -> bool:
    """
    Ensure a location exists by creating missing fields/arrays.
    Used for append/prepend operations on fields that may not exist yet.

    Args:
        data: Root data dict
        location: Location path (e.g., "commands[0].effects")
        errors: Error list to append to if creation fails
        file_path: File path for error messages

    Returns:
        True if location was created or already exists, False on failure
    """
    # Parse array index path like "commands[0].effects"
    array_match = re.match(
        r"^([a-zA-Z_][a-zA-Z0-9_]*)\[(\d+)\]\.([a-zA-Z_][a-zA-Z0-9_]*)$", location
    )
    if array_match:
        array_name = array_match.group(1)
        array_index = int(array_match.group(2))
        field_name = array_match.group(3)

        # Check if array exists
        if not isinstance(data, dict) or array_name not in data:
            return False

        array = data[array_name]
        if not isinstance(array, list) or array_index >= len(array):
            return False

        item = array[array_index]
        if not isinstance(item, dict):
            return False

        # Create missing field as empty list
        if field_name not in item:
            item[field_name] = []

        return True

    # Parse simple path like "glossary.terms"
    if "." in location and "[" not in location:
        parts = location.split(".")
        current = data

        for i, part in enumerate(parts):
            if not isinstance(current, dict):
                return False

            if part not in current:
                # Create missing intermediate or final field
                if i == len(parts) - 1:
                    # Final field - create as empty list for append/prepend
                    current[part] = []
                else:
                    # Intermediate field - create as empty dict
                    current[part] = {}

            if i < len(parts) - 1:
                current = current[part]

        return True

    # For simple top-level field
    if "." not in location and "[" not in location:
        if location not in data:
            data[location] = []
        return True

    return False


def _navigate_to_nested_path(data: dict, path: str) -> Any:
    """Navigate to nested path like 'glossary.terms' in YAML data."""
    current = data
    if "." in path:
        parts = path.split(".")
        for part in parts:
            if not isinstance(current, dict) or part not in current:
                return None
            current = current[part]
    else:
        if not isinstance(current, dict) or path not in current:
            return None
        current = current[path]

    return current


def _set_nested_path(data: dict, path: str, value: Any) -> bool:
    """Set value at nested path like 'glossary.terms' in YAML data."""
    current = data
    if "." in path:
        parts = path.split(".")
        for part in parts[:-1]:
            if not isinstance(current, dict) or part not in current:
                return False
            current = current[part]

        final_key = parts[-1]
        if not isinstance(current, dict):
            return False
        current[final_key] = value
    else:
        if not isinstance(current, dict):
            return False
        current[path] = value

    return True


def _apply_array_index_path_patch(
    data: dict,
    location: str,
    new_content: Any,
    errors: list[str],
    file_path: str,
    yaml_loader: Any,
) -> bool:
    """Apply patch to array index path like 'commands[0].errors[2]'."""
    try:
        components = []
        remaining = location

        while remaining:
            array_match = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*)\[(\d+)\]", remaining)
            if array_match:
                array_name = array_match.group(1)
                array_index = int(array_match.group(2))
                components.append((array_name, array_index))
                remaining = remaining[array_match.end() :]
                if remaining.startswith("."):
                    remaining = remaining[1:]
            else:
                field_match = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*)", remaining)
                if field_match:
                    field_name = field_match.group(1)
                    components.append((field_name, None))
                    remaining = remaining[field_match.end() :]
                    if remaining.startswith("."):
                        remaining = remaining[1:]
                else:
                    break

        if not components:
            errors.append(f"Cannot parse array index path: {location} in {file_path}")
            return False

        current = data
        path_for_error = ""

        for i, (name, index) in enumerate(components):
            path_for_error += f".{name}" if path_for_error else name
            is_final = i == len(components) - 1

            if index is not None:
                if not isinstance(current, dict) or name not in current:
                    errors.append(
                        f"Array '{name}' not found at path '{path_for_error}' in {file_path}"
                    )
                    return False

                array = current[name]
                if not isinstance(array, list):
                    errors.append(
                        f"'{name}' is not an array at path '{path_for_error}' in {file_path}"
                    )
                    return False

                if index >= len(array):
                    errors.append(
                        f"Array index {index} out of range for '{name}' at path '{path_for_error}' in {file_path}"
                    )
                    return False

                if is_final:
                    replacement = _parse_yaml_content(yaml_loader, new_content)
                    array[index] = replacement
                    return True
                else:
                    current = array[index]
                    path_for_error += f"[{index}]"
            else:
                if is_final:
                    if not isinstance(current, dict):
                        errors.append(
                            f"Cannot set field '{name}' on non-object at path '{path_for_error}' in {file_path}"
                        )
                        return False

                    replacement = _parse_yaml_content(yaml_loader, new_content)
                    current[name] = replacement
                    return True
                else:
                    if not isinstance(current, dict):
                        errors.append(
                            f"Cannot navigate through non-dict at '{name}' in path '{path_for_error}' in {file_path}"
                        )
                        return False
                    if name not in current:
                        # Try to create missing field for nested paths
                        if i < len(components) - 1:
                            next_component = components[i + 1]
                            if next_component[1] is None:
                                # Next is a field, create empty dict
                                current[name] = {}
                            else:
                                # Next is an array index, create empty list
                                current[name] = []
                        else:
                            errors.append(
                                f"Field '{name}' not found at path '{path_for_error}' in {file_path}"
                            )
                            return False
                    current = current[name]

        errors.append(
            f"Unexpected end of path navigation for '{location}' in {file_path}"
        )
        return False

    except Exception as exc:
        errors.append(
            f"Failed to apply array index path patch '{location}' in {file_path}: {exc}"
        )
        return False


def _apply_yaml_path_patch(
    data: dict,
    location: str,
    new_content: Any,
    errors: list[str],
    file_path: str,
    yaml_loader: Any,
) -> bool:
    """Apply patch to nested YAML path like 'glossary.terms.26.examples.0'."""
    try:
        parts = location.split(".")
        current = data

        for i, part in enumerate(parts[:-1]):
            if part.isdigit():
                index = int(part)
                if not isinstance(current, list) or index >= len(current):
                    errors.append(
                        f"Invalid array index {part} in path {location} in {file_path}"
                    )
                    return False
                current = current[index]
            else:
                if not isinstance(current, dict):
                    errors.append(
                        f"Cannot navigate through non-dict at '{part}' in {location} in {file_path}"
                    )
                    return False
                if part not in current:
                    errors.append(
                        f"Path component '{part}' not found in {location} in {file_path}"
                    )
                    return False
                current = current[part]

        final_part = parts[-1]
        if final_part.isdigit():
            index = int(final_part)
            if not isinstance(current, list) or index >= len(current):
                errors.append(
                    f"Invalid array index {final_part} in path {location} in {file_path}"
                )
                return False

            replacement = _parse_yaml_content(yaml_loader, new_content)
            current[index] = replacement
        else:
            if not isinstance(current, dict):
                errors.append(
                    f"Cannot set property '{final_part}' on non-object in {location} in {file_path}"
                )
                return False

            replacement = _parse_yaml_content(yaml_loader, new_content)
            current[final_part] = replacement

        return True

    except Exception as exc:
        errors.append(
            f"Failed to apply YAML path patch {location} in {file_path}: {exc}"
        )
        return False
