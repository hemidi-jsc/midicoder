"""Feedback file processing and management."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from midicoder.contract.feedback_model import FeedbackFile


def load_feedback_data(feedback_path: Path) -> dict[str, Any]:
    """Load feedback YAML file."""
    from ruamel.yaml import YAML

    yaml_loader = YAML(typ="safe")
    try:
        data = yaml_loader.load(feedback_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError(f"Failed to parse contract-feedbacks.yml: {exc}") from exc
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise RuntimeError(
            "contract-feedbacks.yml must contain a YAML mapping at the root."
        )
    return data


def validate_feedback(
    paths: Any, *, version: str, feedback_path: Path
) -> tuple[FeedbackFile | None, list[str]]:
    """
    Validate feedback file structure and content.

    Returns:
        Tuple of (validated_feedback, errors)
    """
    from midicoder.contract.yaml_processor import _normalize_contract_path

    data = load_feedback_data(feedback_path)
    errors: list[str] = []
    feedback = None

    try:
        feedback = FeedbackFile.model_validate(data)
    except ValidationError as exc:
        for err in exc.errors():
            loc = ".".join(str(part) for part in err.get("loc", []))
            msg = err.get("msg", "Invalid feedback file.")
            errors.append(f"{loc}: {msg}" if loc else msg)

    if feedback:
        if feedback.meta.version != str(version):
            errors.append(
                f"meta.version mismatch: expected {version}, got {feedback.meta.version}"
            )
        contracts_root = paths.versions / str(version) / "contracts"
        for item in feedback.items:
            try:
                contract_path = _normalize_contract_path(contracts_root, item.file)
            except RuntimeError as exc:
                errors.append(f"{item.id}: {exc}")
                continue
            if not contract_path.exists():
                errors.append(f"{item.id}: file not found ({item.file})")

    return feedback, errors


def update_feedback_status(
    feedback: FeedbackFile,
    updates: list[dict[str, Any]],
    *,
    failed_ids: set[str],
    error_message: str | None,
) -> None:
    """Update feedback item statuses after repair."""
    updates_map: dict[str, dict[str, Any]] = {}
    for update in updates:
        if isinstance(update, dict) and update.get("id"):
            updates_map[str(update["id"])] = update

    for item in feedback.items:
        if item.id in failed_ids:
            item.status = "error"
            item.last_error = error_message
            continue
        update = updates_map.get(item.id)
        if update:
            status = update.get("status")
            if status in {"pending", "in_progress", "done", "error"}:
                item.status = status
            if "last_error" in update:
                item.last_error = update.get("last_error")


def write_feedback_file(path: Path, feedback: FeedbackFile) -> None:
    """Write feedback file with proper formatting."""
    from midicoder.commands.base import write_yaml

    write_yaml(path, feedback.model_dump(mode="python"))


def group_feedback_by_file(pending_items: list[Any]) -> dict[str, list[Any]]:
    """
    Group feedback items by file path for file-level repair processing.

    This enables comprehensive file-level repair that maintains consistency
    and provides better context than single-item repairs.
    """
    grouped = {}
    for item in pending_items:
        file_path = item.file
        if file_path not in grouped:
            grouped[file_path] = []
        grouped[file_path].append(item)

    return grouped


def determine_file_repair_order(grouped_files: dict[str, list[Any]]) -> list[str]:
    """
    Determine optimal order for file repairs based on dependencies.

    Uses dynamic pattern matching to identify foundation vs dependent files
    without hardcoding specific file paths.
    """
    from midicoder.contract.contract_utils import is_dependent_file, is_foundation_file

    files_to_process = set(grouped_files.keys())
    foundation_files = []
    dependent_files = []
    other_files = []

    # Classify files using centralized helper functions
    for file_path in files_to_process:
        if is_foundation_file(file_path):
            foundation_files.append(file_path)
        elif is_dependent_file(file_path):
            dependent_files.append(file_path)
        else:
            other_files.append(file_path)

    # Return ordered list: foundation → other → dependent
    return sorted(foundation_files) + sorted(other_files) + sorted(dependent_files)


def update_file_feedback_items_status(
    paths: Any,
    version: str,
    feedback_updates: list[dict[str, Any]],
    feedback_items: list[Any],
    success: bool,
    error_message: str | None = None,
) -> None:
    """
    Update feedback status for all items in a file after file-level processing.
    """
    try:
        feedback_path = paths.versions / version / "contract-feedbacks.yml"
        feedback, errors = validate_feedback(
            paths, version=version, feedback_path=feedback_path
        )

        if feedback and not errors:
            # Apply LLM-generated status updates
            failed_ids = {item.id for item in feedback_items} if not success else set()
            update_feedback_status(
                feedback,
                feedback_updates,
                failed_ids=failed_ids,
                error_message=error_message,
            )
            write_feedback_file(feedback_path, feedback)

            status_text = "done" if success else "error"
            item_ids = [item.id for item in feedback_items]
            print(f"[feedback] Updated status for {len(item_ids)} items: {status_text}")
            print(f"[feedback] Items: {', '.join(item_ids)}")
        else:
            print(
                f"[feedback] Warning: Could not update status for {len(feedback_items)} items"
            )
    except Exception as exc:
        print(
            f"[feedback] Error updating status for {len(feedback_items)} items: {exc}"
        )


def update_single_feedback_item_status(
    paths: Any,
    version: str,
    feedback_updates: list[dict[str, Any]],
    item_id: str,
    success: bool,
    error_message: str | None = None,
) -> None:
    """
    Update feedback status immediately after processing single item.
    """
    try:
        feedback_path = paths.versions / version / "contract-feedbacks.yml"
        feedback, errors = validate_feedback(
            paths, version=version, feedback_path=feedback_path
        )

        if feedback and not errors:
            # Apply LLM-generated status updates
            update_feedback_status(
                feedback,
                feedback_updates,
                failed_ids={item_id} if not success else set(),
                error_message=error_message,
            )
            write_feedback_file(feedback_path, feedback)
            print(
                f"[feedback] Updated status for {item_id}: {'done' if success else 'error'}"
            )
        else:
            print(f"[feedback] Warning: Could not update status for {item_id}")
    except Exception as exc:
        print(f"[feedback] Error updating status for {item_id}: {exc}")


def create_feedback_file(
    paths: Any, version: str, contracts_root: Path, issues: list[Any]
) -> tuple[Path, int]:
    """
    Create or update feedback file from contract validation issues.

    Returns:
        Tuple of (feedback_path, new_items_count)
    """

    from ruamel.yaml import YAML

    from midicoder.commands.base import write_yaml
    from midicoder.contract.contract_utils import (
        issue_to_feedback_target,
        next_feedback_index,
    )

    version_root = paths.versions / str(version)
    feedback_path = version_root / "contract-feedbacks.yml"

    yaml_loader = YAML(typ="safe")
    if feedback_path.exists():
        loaded = yaml_loader.load(feedback_path.read_text(encoding="utf-8")) or {}
        feedback_data: dict[str, Any] = loaded if isinstance(loaded, dict) else {}
    else:
        feedback_data = {}

    now = datetime.now(timezone.utc).isoformat()
    meta = feedback_data.get("meta")
    if not isinstance(meta, dict):
        meta = {
            "version": str(version),
            "author": "you@team",
            "created_at": now,
            "scope": "contracts",
        }
        feedback_data["meta"] = meta
    else:
        if "version" not in meta:
            meta["version"] = str(version)
        if "author" not in meta:
            meta["author"] = "you@team"
        if "created_at" not in meta:
            meta["created_at"] = now
        if "scope" not in meta:
            meta["scope"] = "contracts"

    items = feedback_data.get("items")
    if isinstance(items, list):
        feedback_items: list[Any] = items
    else:
        feedback_items = []
        feedback_data["items"] = feedback_items

    notes = feedback_data.get("notes")
    if isinstance(notes, list):
        feedback_notes: list[Any] = notes
    elif notes is None:
        feedback_notes = []
        feedback_data["notes"] = feedback_notes
    else:
        feedback_notes = [str(notes)]
        feedback_data["notes"] = feedback_notes

    # Build a signature index to avoid duplicating the same feedback across runs.
    existing_by_signature: dict[tuple[str, str, str], dict[str, Any]] = {}
    for raw_item in feedback_items:
        if not isinstance(raw_item, dict):
            continue
        sig_file = str(raw_item.get("file", "")).strip()
        sig_location = str(raw_item.get("location", "")).strip()
        sig_issue = str(raw_item.get("issue", "")).strip()
        if sig_file and sig_location and sig_issue:
            existing_by_signature[(sig_file, sig_location, sig_issue)] = raw_item

    # Get next available index for new feedback items
    next_index = next_feedback_index(feedback_items)
    new_items_count = 0

    for issue in issues:
        file_value, location_value = issue_to_feedback_target(
            contracts_root, issue.location
        )
        signature = (file_value, location_value, str(issue.message).strip())

        existing_item = existing_by_signature.get(signature)
        if existing_item is not None:
            # Re-open previously closed issue instead of creating duplicate row.
            if existing_item.get("status") in {"done", "error"}:
                existing_item["status"] = "pending"
                existing_item["last_error"] = None
            continue

        feedback_items.append(
            {
                "id": f"FB-{next_index:03d}",
                "file": file_value,
                "location": location_value,
                "status": "pending",
                "issue": issue.message,
                "suggestion": None,
                "last_error": None,
            }
        )
        next_index += 1
        new_items_count += 1

    write_yaml(feedback_path, feedback_data)

    return feedback_path, new_items_count


def report_repair_status(
    *, label: str, feedback: FeedbackFile | None, errors: list[str]
) -> None:
    """Report repair validation status."""
    if errors:
        print(f"[contract repair {label}] FAILED – {len(errors)} error(s) found")
        for error in errors[:10]:
            print(f"- {error}")
        raise SystemExit(1)
    print(
        f"[contract repair {label}] OK – validated {len(feedback.items) if feedback else 0} "
        "feedback item(s)"
    )
