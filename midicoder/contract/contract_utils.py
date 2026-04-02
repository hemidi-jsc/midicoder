"""Utility functions for contract operations."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import ValidationError

# Constants
MIN_VALID_CONTRACT_SIZE = 50  # bytes - minimum size for valid contract file
MAX_VALIDATION_ERRORS_DISPLAY = 5  # maximum validation errors to show in prompts


def normalize_contract_path(contracts_root: Path, relative_path: str) -> Path:
    """
    Normalize contract file path to ensure correct resolution.

    Handles paths that may or may not have "contracts/" prefix.

    Args:
        contracts_root: Root contracts directory
        relative_path: Relative path (may have "contracts/" prefix)

    Returns:
        Resolved Path object

    Raises:
        RuntimeError: If path is invalid or outside contracts root
    """
    path_str = relative_path.strip().lstrip("/")
    if path_str.startswith("contracts/"):
        path_str = path_str[len("contracts/") :]
    candidate = (contracts_root / path_str).resolve()
    try:
        candidate.relative_to(contracts_root.resolve())
    except ValueError as exc:
        raise RuntimeError(f"Invalid contract file path: {relative_path}") from exc
    return candidate


def load_yaml_safe(content: str) -> Any:
    """
    Safely load YAML content with consistent error handling.

    Args:
        content: YAML string content to parse

    Returns:
        Parsed YAML data or None if parsing fails
    """
    try:
        from ruamel.yaml import YAML

        yaml_loader = YAML(typ="safe")
        return yaml_loader.load(content)
    except Exception:
        return None


def extract_ids_from_yaml_list(data: dict, list_name: str) -> list[str]:
    """
    Extract IDs from a list in YAML data.

    Args:
        data: Parsed YAML data (dict)
        list_name: Name of the list field (e.g., 'commands', 'entities')

    Returns:
        List of ID strings found in the list
    """
    if not isinstance(data, dict):
        return []

    if list_name not in data:
        return []

    items = data[list_name]
    if not isinstance(items, list):
        return []

    ids = []
    for item in items:
        if isinstance(item, dict) and "id" in item:
            ids.append(str(item["id"]))

    return ids


def read_json(path: Path) -> dict[str, Any]:
    """Read JSON file."""
    if not path.exists():
        raise RuntimeError(f"Missing config file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def read_schema_tree(root: Path) -> dict[str, Any]:
    """Read schema tree from package resources."""
    try:
        from importlib.resources import files

        schema_tree_path = Path(files("midicoder.dsl.schemas") / "tree_v0.yml")
    except Exception:
        schema_tree_path = root / "midicoder" / "dsl" / "schemas" / "tree_v0.yml"
    if not schema_tree_path.exists():
        raise RuntimeError(f"Missing schema tree: {schema_tree_path}")
    from ruamel.yaml import YAML

    yaml_loader = YAML(typ="safe")
    data = yaml_loader.load(schema_tree_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError("Schema tree is invalid.")
    return data


def chunk_list(values: list[str], size: int) -> list[list[str]]:
    """Chunk list into smaller lists of specified size."""
    if size <= 0:
        raise ValueError("Chunk size must be positive.")
    return [values[idx : idx + size] for idx in range(0, len(values), size)]


def validate_contract_file(contract_path: Path, required_file: str) -> bool:
    """
    Validate that a contract file is properly formed and contains expected content.

    Args:
        contract_path: Path to the contract file
        required_file: Expected relative path of the file

    Returns:
        True if file is valid, False otherwise
    """
    try:
        from ruamel.yaml import YAML

        yaml_loader = YAML(typ="safe")
        content = contract_path.read_text(encoding="utf-8")
        data = yaml_loader.load(content)

        # Basic structure validation
        if not isinstance(data, dict):
            return False

        # Check expected structure for each contract type
        expected_keys = {
            "meta/info.yaml": "info",
            "meta/profiles.yaml": "profiles",
            "meta/secrets.yaml": "secrets",
            "glossary.yaml": "glossary",
            "domain/entities.yaml": "entities",
            "domain/value_objects.yaml": "value_objects",
            "domain/enums.yaml": "enums",
            "domain/errors.yaml": "errors",
            "domain/events.yaml": "events",
            "app/commands.yaml": "commands",
            "app/queries.yaml": "queries",
            "app/projections.yaml": "projections",
            "persistence/model.yaml": "tables",
            "api/http.yaml": "routes",
            "api/graphql.yaml": "api",
            "rules/rules.yaml": "rules",
            "workflows/workflows.yaml": "workflows",
            "policy/policies.yaml": "policies",
            "policy/rbac.yaml": "access",
            "policy/security.yaml": "security",
            "policy/reliability.yaml": "reliability_policies",
            "integrations/integrations.yaml": "integrations",
            "ops/observability.yaml": "observability",
            "scenarios/scenarios.yaml": "scenarios",
            "testing/tests.yaml": "tests",
        }

        expected_key = expected_keys.get(required_file)
        if expected_key:
            if expected_key not in data:
                return False

            # Check if the content is not just empty structure
            content_value = data[expected_key]
            if isinstance(content_value, list) and len(content_value) == 0:
                return False
            elif isinstance(content_value, dict) and len(content_value) == 0:
                return False

        # File size check - very small files are likely incomplete
        if len(content.strip()) < MIN_VALID_CONTRACT_SIZE:
            return False

        return True

    except Exception:
        return False


def analyze_run_logs(
    run_dir: Path, required_files: list[str]
) -> tuple[set[str], set[str]]:
    """
    Analyze run logs to determine which files were attempted and which succeeded.

    Args:
        run_dir: Path to the run directory
        required_files: List of expected contract files

    Returns:
        Tuple of (attempted_files, successful_files)
    """
    attempted_files = set()
    successful_files = set()

    try:
        # Check summary.json for overall results
        summary_file = run_dir / "summary.json"
        if summary_file.exists():
            summary = json.loads(summary_file.read_text(encoding="utf-8"))
            created_files = summary.get("created_files", [])

            # Extract relative paths from created files
            for file_path in created_files:
                # Convert absolute path or contracts-relative path to our format
                if "contracts/" in file_path:
                    relative_file = file_path.split("contracts/", 1)[1]
                    if relative_file in required_files:
                        successful_files.add(relative_file)

        # Check trace files to see what was attempted
        trace_files = list(run_dir.glob("trace_pass_*.json"))
        for trace_file in trace_files:
            try:
                trace_data = json.loads(trace_file.read_text(encoding="utf-8"))
                batch = trace_data.get("batch", [])
                attempted_files.update(batch)
            except:
                continue

        # Alternative: check prompt files to see what was attempted
        if not trace_files:
            prompt_files = list(run_dir.glob("prompt_pass_*.txt"))
            for prompt_file in prompt_files:
                try:
                    content = prompt_file.read_text(encoding="utf-8")
                    # Look for target files mentioned in prompts
                    for required_file in required_files:
                        if required_file in content:
                            attempted_files.add(required_file)
                except:
                    continue

        # Check response files to see what actually got processed
        response_files = list(run_dir.glob("response_pass_*.txt"))
        for response_file in response_files:
            try:
                content = response_file.read_text(encoding="utf-8")

                # Try to parse as JSON (raw response)
                try:
                    response_data = json.loads(content)
                    llm_content = (
                        response_data.get("choices", [{}])[0]
                        .get("message", {})
                        .get("content", "")
                    )
                except:
                    # If not JSON, treat as direct content
                    llm_content = content

                # Look for file declarations in the response
                for required_file in required_files:
                    if (
                        f"file: contracts/{required_file}" in llm_content
                        or f"file: {required_file}" in llm_content
                    ):
                        attempted_files.add(required_file)

                        # Check if the response seems complete (not truncated)
                        if "finish_reason" in content:
                            try:
                                response_data = json.loads(content)
                                finish_reason = response_data.get("choices", [{}])[
                                    0
                                ].get("finish_reason")
                                if finish_reason == "stop":  # Complete response
                                    # Additional validation: check if YAML structure seems complete
                                    if (
                                        "content:" in llm_content
                                        and not llm_content.strip().endswith("type")
                                    ):
                                        successful_files.add(required_file)
                            except:
                                pass
                        elif not llm_content.strip().endswith(("type", "type:")):
                            # Heuristic: if content doesn't end abruptly, consider it successful
                            successful_files.add(required_file)

            except:
                continue

    except Exception as e:
        print(f"[contract gen resume] Warning: Failed to analyze run logs: {e}")

    return attempted_files, successful_files


def issue_to_feedback_target(
    contracts_root: Path, issue_location: str
) -> tuple[str, str]:
    """Convert issue location to feedback file and location."""
    full_location = issue_location.strip()
    file_part = full_location
    inner_location = ""

    # On Windows, absolute paths include a drive letter (e.g. "D:\path\file.yaml"),
    # so we must skip the first colon when splitting "<path>:<location>".
    separator_index = -1
    if re.match(r"^[A-Za-z]:[\\/]", full_location):
        separator_index = full_location.find(":", 2)
    else:
        separator_index = full_location.find(":")

    if separator_index != -1:
        file_part = full_location[:separator_index]
        inner_location = full_location[separator_index + 1 :].lstrip()
    path_object = Path(file_part)
    try:
        relative_path = (
            path_object.resolve().relative_to(contracts_root.resolve()).as_posix()
        )
    except Exception:  # noqa: BLE001
        relative_path = path_object.as_posix()
        if relative_path.startswith("contracts/"):
            relative_path = relative_path[len("contracts/") :]
    if not inner_location:
        inner_location = "root"
    normalized_relative = relative_path.lstrip("/")
    file_value = f"contracts/{normalized_relative}"
    return file_value, inner_location


def next_feedback_index(items: list[Any]) -> int:
    """Get next feedback index from items list."""
    max_index = 0
    for raw_item in items:
        if not isinstance(raw_item, dict):
            continue
        identifier = str(raw_item.get("id", "") or "").strip()
        match = re.search(r"(\d+)$", identifier)
        if not match:
            continue
        value = int(match.group(1))
        if value > max_index:
            max_index = value
    return max_index + 1


def determine_file_type(file_path: str) -> str:
    """
    Determine the contract file type from file path.

    Args:
        file_path: Path to contract file (e.g., 'domain/entities.yaml')

    Returns:
        File type string ('glossary', 'entities', 'commands', etc.)
    """
    file_path_lower = file_path.lower()

    # Order matters - check more specific patterns first
    if "glossary" in file_path_lower:
        return "glossary"
    elif "entit" in file_path_lower:  # matches 'entities' or 'entity'
        return "entities"
    elif "value_object" in file_path_lower:
        return "value_objects"
    elif "enum" in file_path_lower:
        return "enums"
    elif "error" in file_path_lower:
        return "errors"
    elif "event" in file_path_lower:
        return "events"
    elif "command" in file_path_lower:
        return "commands"
    elif "quer" in file_path_lower:  # matches 'queries' or 'query'
        return "queries"
    elif "projection" in file_path_lower:
        return "projections"
    elif "graphql" in file_path_lower:
        return "graphql"
    elif "http" in file_path_lower or "api" in file_path_lower:
        return "http"
    elif "info" in file_path_lower or "meta" in file_path_lower:
        return "info"
    elif "rbac" in file_path_lower or "permission" in file_path_lower:
        return "access_policy"
    elif "polic" in file_path_lower:
        return "policies"
    elif "rule" in file_path_lower:
        return "rules"
    elif "workflow" in file_path_lower:
        return "workflows"
    elif "persist" in file_path_lower:
        return "persistence"
    elif "integration" in file_path_lower:
        return "integrations"
    elif "profile" in file_path_lower:
        return "profiles"
    elif "secrets" in file_path_lower:
        return "secrets"
    elif "security" in file_path_lower:
        return "security"
    elif "reliability" in file_path_lower:
        return "reliability"
    elif "observability" in file_path_lower:
        return "observability"
    elif "test" in file_path_lower:
        return "testing"
    else:
        return "unknown"


def is_foundation_file(file_path: str) -> bool:
    """
    Check if file is a foundation file (should be generated first).

    Foundation files are those that other files depend on:
    - glossary (defines terms)
    - entities (defines domain objects)
    - errors (defines error types)
    - events (defines domain events)
    """
    file_type = determine_file_type(file_path)
    return file_type in {
        "glossary",
        "entities",
        "errors",
        "events",
        "info",
        "persistence",
        "integrations",
        "profiles",
        "secrets",
        "security",
    }


def is_dependent_file(file_path: str) -> bool:
    """
    Check if file is a dependent file (should be generated after foundation files).

    Dependent files reference foundation files:
    - commands (reference entities, errors)
    - queries (reference entities, errors)
    - http (reference commands, queries, errors)
    - rules (reference entities, commands)
    - workflows (reference commands, entities)
    """
    file_type = determine_file_type(file_path)
    return file_type in {
        "commands",
        "queries",
        "projections",
        "http",
        "graphql",
        "rules",
        "workflows",
        "policies",
        "access_policy",
        "reliability",
        "observability",
        "testing",
    }


def validate_single_contract_file(
    contract_path: Path, file_path: str
) -> list[dict[str, str]]:
    """
    Validate a single contract file with cross-reference checking.

    This validates both schema structure AND cross-references by running
    the full contract validator and filtering results for the target file.

    Args:
        contract_path: Absolute path to the contract file
        file_path: Relative path (e.g., 'api/http.yaml')

    Returns:
        List of validation errors for this specific file
    """
    validation_errors = []

    try:
        # Get contracts root (parent of file path)
        contracts_root = contract_path.parent
        path_parts = Path(file_path.replace("contracts/", "")).parts
        for _ in range(len(path_parts) - 1):
            contracts_root = contracts_root.parent

        # Run full contract validation to check cross-references
        from midicoder.contract.contract_validator import check_contract

        all_issues = check_contract(contracts_root)

        # Filter issues for this specific file
        file_path_normalized = str(contract_path.resolve())

        for issue in all_issues:
            issue_location = issue.location

            # Check if this issue belongs to our target file
            if (
                file_path_normalized in issue_location
                or str(contract_path) in issue_location
            ):
                # Extract the inner location (after file path)
                inner_location = _extract_inner_issue_location(issue_location)

                validation_errors.append(
                    {
                        "location": f"{contract_path}:{inner_location}",
                        "message": issue.message,
                    }
                )

        return validation_errors

    except Exception as exc:
        # Fallback: try simple schema validation only
        try:
            from midicoder.dsl.loader import (
                load_glossary,
                load_entities,
                load_errors,
                load_events,
                load_commands,
                load_http,
                load_info,
                load_rules,
                load_workflows,
                load_persistence,
                load_integrations,
                load_profiles,
                load_secrets_contract,
                load_security_baseline,
                load_reliability,
                load_observability,
                load_testing,
            )

            file_type = determine_file_type(file_path)

            loader_map = {
                "glossary": load_glossary,
                "entities": load_entities,
                "errors": load_errors,
                "events": load_events,
                "commands": load_commands,
                "http": load_http,
                "info": load_info,
                "rules": load_rules,
                "workflows": load_workflows,
                "persistence": load_persistence,
                "integrations": load_integrations,
                "profiles": load_profiles,
                "secrets": load_secrets_contract,
                "security": load_security_baseline,
                "reliability": load_reliability,
                "observability": load_observability,
                "testing": load_testing,
            }

            if file_type in loader_map:
                loader = loader_map[file_type]
                loader(contract_path)
                return []

        except ValidationError as val_exc:
            for error in val_exc.errors():
                location = ".".join(str(part) for part in error.get("loc", []))
                message = error.get("msg", "Invalid schema")
                validation_errors.append(
                    {
                        "location": f"{contract_path}:{location}"
                        if location
                        else str(contract_path),
                        "message": message,
                    }
                )
        except Exception:
            pass

        # If all validation fails, return the original error
        if not validation_errors:
            validation_errors.append(
                {
                    "location": str(contract_path),
                    "message": f"Failed to validate file: {exc}",
                }
            )

    return validation_errors


def _extract_inner_issue_location(issue_location: str) -> str:
    """Extract inner location after '<path>:<location>' with Windows drive-safe parsing."""
    inner_location = "root"
    separator_index = -1
    if re.match(r"^[A-Za-z]:[\\/]", issue_location):
        separator_index = issue_location.find(":", 2)
    else:
        separator_index = issue_location.find(":")

    if separator_index != -1:
        inner_candidate = issue_location[separator_index + 1 :].strip()
        if inner_candidate:
            inner_location = inner_candidate
    return inner_location


def format_validation_errors(validation_errors: list[dict[str, str]]) -> str:
    """Format validation errors for prompt display."""
    if not validation_errors:
        return "✅ No validation errors found."

    formatted_errors = []
    for error in validation_errors[:MAX_VALIDATION_ERRORS_DISPLAY]:
        location = error.get("location", "unknown")
        message = error.get("message", "Unknown error")
        formatted_errors.append(f"- **{location}**: {message}")

    if len(validation_errors) > MAX_VALIDATION_ERRORS_DISPLAY:
        formatted_errors.append(
            f"... and {len(validation_errors) - MAX_VALIDATION_ERRORS_DISPLAY} more validation errors"
        )

    return "\n".join(formatted_errors)


def write_contract_files(files: list[tuple[Path, Any]]) -> list[str]:
    """Write contract files from parsed documents."""
    from midicoder.commands.base import write_yaml

    created: list[str] = []
    for path, content in files:
        if isinstance(content, str):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        else:
            write_yaml(path, content)
        created.append(path.as_posix())
    return created


def write_memos(paths: Any, memos: list[dict[str, Any]]) -> None:
    """Write learning memos to context directory."""
    memos_dir = paths.context / "memos"
    memos_dir.mkdir(parents=True, exist_ok=True)
    for memo in memos:
        if not isinstance(memo, dict):
            continue
        memo_id = memo.get("id")
        text = memo.get("text")
        if not memo_id or not text:
            continue
        memo_path = memos_dir / f"{memo_id}.md"
        memo_path.write_text(str(text).strip() + "\n", encoding="utf-8")
