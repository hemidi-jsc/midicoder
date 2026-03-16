"""Normalization and canonicalization of DSL contracts."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from typing import Any

from ..symbols.symbol_table import SymbolTable


class Normalizer:
    """Normalizes and canonicalizes contract data."""
    
    def __init__(self, symbol_table: SymbolTable) -> None:
        self.symbols = symbol_table
    
    def normalize_id(self, id: str) -> str:
        """
        Normalize an ID to canonical snake_case form.
        
        Rules:
        - Convert to snake_case
        - Remove accents and special characters
        - Keep only alphanumeric and underscores
        - Lowercase
        - Trim leading/trailing underscores
        
        Examples:
        - "CreateUser" → "create_user"
        - "User Profile" → "user_profile"
        - "café-item" → "cafe_item"
        - "Item#123" → "item_123"
        - "  User  " → "user"
        
        Raises:
            ValueError: If ID is empty or contains only special characters
        """
        if not isinstance(id, str):
            id = str(id)
        
        # Trim whitespace first
        id = id.strip()
        
        if not id:
            raise ValueError("ID cannot be empty")
        
        # Remove accents (café → cafe)
        id = unicodedata.normalize('NFKD', id)
        id = id.encode('ascii', 'ignore').decode('ascii')
        
        # Convert camelCase/PascalCase to snake_case
        # Insert underscore before uppercase letters that follow lowercase
        id = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', id)
        
        # Handle consecutive uppercase letters (HTTPRequest → HTTP_Request)
        id = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', id)
        
        # Convert to lowercase
        id = id.lower()
        
        # Replace spaces, hyphens, and other special chars with underscore
        id = re.sub(r'[^a-z0-9_]+', '_', id)
        
        # Remove leading/trailing underscores
        id = id.strip('_')
        
        # Remove consecutive underscores
        id = re.sub(r'_+', '_', id)
        
        # Validate result
        if not id:
            raise ValueError("ID contains only special characters")
        
        # Ensure it starts with a letter (not a number)
        if not re.match(r'^[a-z]', id):
            raise ValueError(f"ID must start with a letter: '{id}'")
        
        # Final validation: must be valid identifier
        if not re.match(r'^[a-z][a-z0-9_]*$', id):
            raise ValueError(f"Invalid ID format after normalization: '{id}'")
        
        return id
    
    def normalize_ref(self, ref: Any) -> dict[str, str]:
        """
        Normalize a reference to structured format.
        
        Input formats:
        - "entity_id" → {"type": "Entity", "id": "entity_id"}
        - "Entity:user" → {"type": "Entity", "id": "user"}
        - {"type": "Entity", "id": "user"} → {"type": "Entity", "id": "user"}
        - ["Entity", "user"] → {"type": "Entity", "id": "user"}
        
        Returns:
            Normalized reference dict with type and id.
        """
        if isinstance(ref, dict):
            return {
                "type": ref.get("type", "Unknown"),
                "id": self.normalize_id(ref.get("id", "")),
            }
        elif isinstance(ref, str):
            # Check for Type:ID format
            if ":" in ref:
                type_part, id_part = ref.split(":", 1)
                return {
                    "type": type_part.strip(),
                    "id": self.normalize_id(id_part.strip()),
                }
            else:
                # Just an ID, infer type from context or use generic
                return {
                    "type": "Unknown",
                    "id": self.normalize_id(ref),
                }
        elif isinstance(ref, list) and len(ref) >= 2:
            return {
                "type": ref[0],
                "id": self.normalize_id(ref[1]),
            }
        else:
            return {
                "type": "Unknown",
                "id": self.normalize_id(str(ref)),
            }
    
    def normalize_object(self, obj: Any, preserve_order: bool = False) -> Any:
        """
        Recursively normalize an object.
        
        Args:
            obj: The object to normalize
            preserve_order: If True, keep original order; if False, sort by keys/ids
        
        Returns:
            Normalized object
        """
        if isinstance(obj, dict):
            normalized = {}
            
            # Normalize ID field if present
            if "id" in obj:
                normalized["id"] = self.normalize_id(obj["id"])
            
            # Process other fields
            for key, value in obj.items():
                if key == "id":
                    continue  # Already handled
                
                # Check if this is a reference field
                if self._is_reference_key(key):
                    normalized[key] = self._normalize_reference_field(value)
                else:
                    normalized[key] = self.normalize_object(value, preserve_order)
            
            # Sort keys for deterministic output (except if preserving order)
            if not preserve_order:
                return dict(sorted(normalized.items()))
            return normalized
            
        elif isinstance(obj, list):
            normalized_list = [self.normalize_object(item, preserve_order) for item in obj]
            
            # Sort list by 'id' field if all items have it (for deterministic output)
            if not preserve_order and normalized_list and all(
                isinstance(item, dict) and "id" in item for item in normalized_list
            ):
                return sorted(normalized_list, key=lambda x: x["id"])
            
            return normalized_list
            
        else:
            # Primitive types - return as is
            return obj
    
    def compute_hash(self, obj: Any) -> str:
        """
        Compute a stable hash of a normalized object.
        
        Args:
            obj: The object to hash (should be normalized)
        
        Returns:
            SHA256 hex digest
        """
        # Convert to JSON with sorted keys for deterministic hashing
        json_str = json.dumps(obj, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(json_str.encode("utf-8")).hexdigest()
    
    def expand_shorthand(self, obj: Any) -> Any:
        """
        Expand shorthand syntax to full form.
        
        Examples:
        - Guard shorthand: "auth.check" → {"id": "auth.check", "params": {}}
        - Effect shorthand: "entity.create" → {"id": "entity.create", "params": {}}
        - Field shorthand: "name" → {"name": "name", "type": "string", "required": True}
        
        Note: This is a placeholder. Full implementation depends on DSL schema details.
        """
        # For now, return as-is
        # TODO: Implement shorthand expansion based on schema
        return obj
    
    def apply_yaml_merge(self, obj: dict[str, Any]) -> dict[str, Any]:
        """
        Apply YAML merge (<<) operator.
        
        Args:
            obj: Dictionary that might contain << key
        
        Returns:
            Merged dictionary
        """
        if not isinstance(obj, dict) or "<<" not in obj:
            return obj
        
        merged = {}
        merge_value = obj.get("<<")
        
        # Handle list of merge sources
        if isinstance(merge_value, list):
            for item in merge_value:
                if isinstance(item, dict):
                    merged.update(item)
        # Handle single merge source
        elif isinstance(merge_value, dict):
            merged.update(merge_value)
        
        # Apply remaining keys (override merged values)
        for key, value in obj.items():
            if key == "<<":
                continue
            merged[key] = value
        
        return merged
    
    def _is_reference_key(self, key: str) -> bool:
        """Check if a key represents a reference field."""
        lowered = key.lower()
        return (
            lowered == "ref"
            or lowered.endswith("_ref")
            or lowered.endswith("_refs")
            or lowered in ["fetches", "reads", "errors", "emits", "entity", "command", "query"]
        )
    
    def _normalize_reference_field(self, value: Any) -> Any:
        """Normalize a reference field (handles single ref or list of refs)."""
        if isinstance(value, list):
            return [self.normalize_ref(ref) for ref in value]
        else:
            return self.normalize_ref(value)


def normalize_contracts(
    contracts: dict[str, Any],
    symbol_table: SymbolTable,
) -> dict[str, Any]:
    """
    Normalize all contracts.
    
    Args:
        contracts: Dictionary of contract data by file
        symbol_table: Symbol table for reference resolution
    
    Returns:
        Normalized contracts
    """
    normalizer = Normalizer(symbol_table)
    
    normalized = {}
    for file_path, data in contracts.items():
        normalized[file_path] = normalizer.normalize_object(data, preserve_order=False)
    
    return normalized
