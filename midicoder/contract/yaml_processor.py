"""YAML processing utilities for contract operations."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def strip_yaml_code_fences(raw_text: str) -> str:
    """
    Strip code fences from LLM output.
    Handles various markdown code fence formats.
    """
    text = raw_text.strip()
    
    # Handle empty input
    if not text:
        return text
    
    lines = text.splitlines()
    if not lines:
        return text
    
    # Check if first line starts with code fence
    first_line = lines[0].strip()
    if first_line.startswith("```"):
        # Find the closing fence
        closing_fence_index = -1
        for i in range(len(lines) - 1, 0, -1):  # Search from end
            if lines[i].strip().startswith("```"):  # More flexible matching
                closing_fence_index = i
                break
        
        # If we found both opening and closing fences
        if closing_fence_index > 0:
            # Extract content between fences
            content = "\n".join(lines[1:closing_fence_index]).strip()
            return content
        else:
            # If no closing fence found, try to extract everything after the opening fence
            if len(lines) > 1:
                content = "\n".join(lines[1:]).strip()
                return content
    
    # Additional safety check: if text still starts with backticks, remove them
    if text.startswith("```"):
        # Try to find and remove any remaining code fence markers
        lines = text.splitlines()
        # Remove first line if it's a code fence
        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]
        # Remove last line if it's a closing code fence
        if lines and lines[-1].strip() in ["```", "```yaml", "```yml"]:
            lines = lines[:-1]
        return "\n".join(lines).strip()
    
    return text


def clean_malformed_yaml(raw_content: str) -> str:
    """
    Clean malformed YAML by removing orphaned patch lines that were incorrectly appended.
    
    This handles the case where previous patch operations incorrectly appended lines like:
    commands[0].errors[2]: PasswordTooWeak
    commands[0].effects[1].params.event: UserRegistered
    
    These lines are invalid YAML and should be removed.
    """
    lines = raw_content.splitlines()
    cleaned_lines = []
    
    for line in lines:
        stripped = line.strip()
        
        # Check for common malformed patch patterns
        is_malformed_patch = (
            # Pattern: commands[0].errors[2]: PasswordTooWeak
            re.match(r'^[a-zA-Z_]+\[\d+\]\.[a-zA-Z_]+\[\d+\]:\s*\w+$', stripped) or
            # Pattern: commands[0].effects[1].params.event: UserRegistered  
            re.match(r'^[a-zA-Z_]+\[\d+\]\.[a-zA-Z_]+\[\d+\]\.[a-zA-Z_]+\.[a-zA-Z_]+:\s*\w+$', stripped) or
            # Pattern: commands[1].errors[2]: UserAccountInactive
            re.match(r'^[a-zA-Z_]+\[\d+\]\.[a-zA-Z_]+\[\d+\]:\s*[A-Za-z][A-Za-z0-9_]*$', stripped) or
            # Pattern: commands[3].fetches[1]: ProductCatalog
            re.match(r'^[a-zA-Z_]+\[\d+\]\.[a-zA-Z_]+\[\d+\]:\s*[A-Za-z][A-Za-z0-9_]*$', stripped)
        )
        
        if not is_malformed_patch:
            cleaned_lines.append(line)
        else:
            print(f"[clean yaml] Removing malformed patch line: {stripped}")
    
    return "\n".join(cleaned_lines)


def parse_contract_documents(raw_text: str, contracts_root: Path) -> list[tuple[Path, Any]]:
    """Parse contract documents from LLM output."""
    from ruamel.yaml import YAML

    yaml_loader = YAML(typ="safe")
    yaml_loader.allow_duplicate_keys = True
    docs = [doc for doc in yaml_loader.load_all(raw_text) if doc is not None]
    if not docs:
        raise RuntimeError("LLM output did not contain any YAML documents.")

    # Handle single document case (expected for single file generation)
    if len(docs) == 1 and isinstance(docs[0], dict):
        doc = docs[0]
        if "file" in doc and "content" in doc:
            # Single document format: {file: "...", content: {...}}
            file_path = _normalize_contract_path(contracts_root, str(doc["file"]))
            return [(file_path, doc["content"])]
        elif "files" in doc:
            # Legacy files array format: {files: [{file: "...", content: {...}}]}
            entries = doc["files"]
        else:
            raise RuntimeError("Single document must have either 'file' and 'content' keys, or 'files' array.")
    else:
        # Multi-document format (legacy support)
        entries = docs

    if not isinstance(entries, list):
        raise RuntimeError("LLM output must be a single document with file/content or a list of file documents.")

    files: list[tuple[Path, Any]] = []
    seen: set[Path] = set()
    for entry in entries:
        if not isinstance(entry, dict) or "file" not in entry or "content" not in entry:
            raise RuntimeError("Each YAML document must include 'file' and 'content' keys.")
        file_path = _normalize_contract_path(contracts_root, str(entry["file"]))
        if file_path in seen:
            raise RuntimeError(f"Duplicate file entry in LLM output: {entry['file']}")
        seen.add(file_path)
        files.append((file_path, entry["content"]))
    return files


def parse_repair_plan(raw_text: str) -> dict[str, Any]:
    """Parse repair plan from LLM output."""
    from ruamel.yaml import YAML

    yaml_loader = YAML(typ="safe")
    data = yaml_loader.load(raw_text)
    if not isinstance(data, dict):
        raise RuntimeError("Repair plan must be a YAML mapping.")
    patches = data.get("patches", [])
    if not isinstance(patches, list):
        raise RuntimeError("Repair plan 'patches' must be a list.")
    memos = data.get("memos", [])
    if memos and not isinstance(memos, list):
        raise RuntimeError("Repair plan 'memos' must be a list.")
    status_updates = data.get("feedback_status_updates", [])
    if status_updates and not isinstance(status_updates, list):
        raise RuntimeError("Repair plan 'feedback_status_updates' must be a list.")
    return {
        "patches": patches,
        "memos": memos,
        "feedback_status_updates": status_updates,
    }


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
