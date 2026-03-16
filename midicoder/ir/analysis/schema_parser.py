"""Schema tree parser for dynamic intent inference.

This module extracts metadata and rules from schema tree (tree_v0.yml)
to drive intent inference logic without hardcoding.
"""

from __future__ import annotations

from typing import Any


# Confidence levels (aligned with intent.py)
CONFIDENCE_CERTAIN = 1.0
CONFIDENCE_HIGH = 0.9
CONFIDENCE_MEDIUM = 0.7
CONFIDENCE_LOW = 0.5
CONFIDENCE_VERY_LOW = 0.3


def extract_meta_kind_mapping(schema_tree: dict[str, Any]) -> dict[str, str]:
    """
    Extract mapping: ModelType → meta.kind from schema tree.
    
    Args:
        schema_tree: Full schema tree from tree_v0.yml
    
    Returns:
        Dictionary mapping model names to their meta.kind values
        Example: {"Entity": "domain.entity", "Command": "app.command"}
    """
    mapping: dict[str, str] = {}
    
    modules = schema_tree.get("modules", {})
    for module_path, module_data in modules.items():
        if not isinstance(module_data, dict):
            continue
        
        models = module_data.get("models", {})
        if not isinstance(models, dict):
            continue
        
        for model_name, model_schema in models.items():
            if not isinstance(model_schema, dict):
                continue
            
            meta = model_schema.get("meta", {})
            if not isinstance(meta, dict):
                continue
            
            kind = meta.get("kind")
            if kind:
                mapping[model_name] = kind
    
    return mapping


def extract_catalogs(schema_tree: dict[str, Any]) -> dict[str, list[str]]:
    """
    Extract all catalogs from schema tree.
    
    Args:
        schema_tree: Full schema tree from tree_v0.yml
    
    Returns:
        Dictionary of catalog_name → list of values
        Example: {"COMMAND_CATEGORY_CATALOG": ["crud.create", "crud.update", ...]}
    """
    catalogs: dict[str, list[str]] = {}
    
    modules = schema_tree.get("modules", {})
    for module_path, module_data in modules.items():
        if not isinstance(module_data, dict):
            continue
        
        module_catalogs = module_data.get("catalogs", {})
        if not isinstance(module_catalogs, dict):
            continue
        
        for catalog_name, catalog_values in module_catalogs.items():
            if isinstance(catalog_values, list):
                # Merge catalogs if same name appears in multiple modules
                if catalog_name in catalogs:
                    catalogs[catalog_name].extend(catalog_values)
                else:
                    catalogs[catalog_name] = list(catalog_values)
    
    return catalogs


def infer_intent_kind_from_meta(meta_kind: str) -> tuple[str, float]:
    """
    Map meta.kind → (intent.kind, confidence).
    
    This provides default intent.kind based on meta.kind patterns.
    Commands and Queries can be overridden by signals (routes, workflows).
    
    Args:
        meta_kind: The meta.kind value from schema (e.g., "domain.entity")
    
    Returns:
        Tuple of (intent_kind, confidence)
    """
    if not meta_kind:
        return ("service", CONFIDENCE_VERY_LOW)
    
    # Domain models → always "model"
    if meta_kind.startswith("domain."):
        return ("model", CONFIDENCE_CERTAIN)
    
    # Application layer → default "service" (can be overridden by signals)
    if meta_kind.startswith("app."):
        if meta_kind == "app.projection":
            return ("projection", CONFIDENCE_CERTAIN)
        # app.command, app.query → "service" by default
        return ("service", CONFIDENCE_LOW)
    
    # Workflow → always "workflow"
    if meta_kind.startswith("workflow."):
        return ("workflow", CONFIDENCE_CERTAIN)
    
    # API layer → these are signal sources, not direct IR nodes
    if meta_kind.startswith("api."):
        return ("controller", CONFIDENCE_HIGH)
    
    # Policy, rules, scenarios → map to their own kinds
    if meta_kind.startswith("policy."):
        return ("policy", CONFIDENCE_CERTAIN)
    
    if meta_kind.startswith("rules."):
        return ("rule", CONFIDENCE_CERTAIN)
    
    if meta_kind.startswith("scenario."):
        return ("scenario", CONFIDENCE_CERTAIN)
    
    # Meta types (info, glossary) → not used for intent
    if meta_kind.startswith("meta."):
        return ("meta", CONFIDENCE_CERTAIN)
    
    # Shared types (named_field, guard_ref, effect_ref) → not used for intent
    if meta_kind.startswith("shared."):
        return ("shared", CONFIDENCE_CERTAIN)
    
    # Unknown → fallback
    return ("service", CONFIDENCE_VERY_LOW)


def extract_verb_prefixes_from_catalog(catalog: list[str]) -> set[str]:
    """
    Extract verb prefixes from COMMAND_CATEGORY_CATALOG.
    
    Patterns:
    - "crud.create" → "create"
    - "auth.login" → "login"
    - "billing.charge" → "charge"
    - "subscription.cancel" → "cancel"
    
    Args:
        catalog: List of category values (e.g., COMMAND_CATEGORY_CATALOG)
    
    Returns:
        Set of verb prefixes
    """
    prefixes: set[str] = set()
    
    for category in catalog:
        if not isinstance(category, str):
            continue
        
        # Split by dot and take last part (verb)
        if "." in category:
            parts = category.rsplit(".", 1)
            if len(parts) == 2:
                verb = parts[1].strip().lower()
                if verb:
                    prefixes.add(verb)
        else:
            # No dot, treat whole string as verb
            verb = category.strip().lower()
            if verb:
                prefixes.add(verb)
    
    return prefixes


def extract_event_suffixes_from_catalog(catalog: list[str]) -> set[str]:
    """
    Extract event suffixes from COMMAND_CATEGORY_CATALOG or EVENT_KIND_CATALOG.
    
    Event-style commands typically end with past-tense verbs:
    - "workflow.transition" might have events like "transitioned"
    - Pattern: look for past-tense endings
    
    Args:
        catalog: List of category values
    
    Returns:
        Set of common event suffixes
    """
    # Common past-tense patterns for events
    common_suffixes = {
        "created", "updated", "deleted", "removed",
        "succeeded", "failed", "completed", "started", "finished",
        "activated", "deactivated", "suspended", "resumed",
        "cancelled", "canceled", "expired",
        "sent", "received", "processed",
        "charged", "refunded", "paid",
        "logged_in", "logged_out", "signed_in", "signed_out",
    }
    
    # Extract from catalog if present
    extracted: set[str] = set()
    for category in catalog:
        if not isinstance(category, str):
            continue
        
        # Look for past-tense patterns in category names
        category_lower = category.lower()
        for suffix in common_suffixes:
            if suffix in category_lower:
                extracted.add(suffix)
    
    # Return union of common suffixes and extracted ones
    return common_suffixes | extracted


def extract_container_dirs(schema_tree: dict[str, Any]) -> set[str]:
    """
    Extract container directory names from schema structure.
    
    These are directories that organize contract files but are not module names:
    - "domain" (contains entities, events, errors)
    - "app" (contains commands, queries)
    - "api" (contains http, graphql)
    - "workflows" (contains workflow definitions)
    - etc.
    
    Args:
        schema_tree: Full schema tree
    
    Returns:
        Set of container directory names to ignore in module extraction
    """
    # These are standard container directories based on schema organization
    # We can infer them from module paths in schema tree
    
    container_dirs: set[str] = set()
    
    # Known patterns from schema structure
    known_containers = {
        "domain",      # domain/entities.yaml, domain/events.yaml
        "app",         # app/commands.yaml, app/queries.yaml
        "api",         # api/http.yaml, api/graphql.yaml
        "workflows",   # workflows/workflows.yaml
        "policy",      # policy/policies.yaml, policy/rbac.yaml
        "rules",       # rules/rules.yaml
        "scenarios",   # scenarios/scenarios.yaml
        "meta",        # meta/info.yaml
        "projections", # projections/*.yaml (inferred)
    }
    
    container_dirs.update(known_containers)
    
    # Additionally, extract from meta.kind patterns
    modules = schema_tree.get("modules", {})
    for module_path, module_data in modules.items():
        if not isinstance(module_data, dict):
            continue
        
        models = module_data.get("models", {})
        for model_name, model_schema in models.items():
            if not isinstance(model_schema, dict):
                continue
            
            meta = model_schema.get("meta", {})
            if not isinstance(meta, dict):
                continue
            
            kind = meta.get("kind", "")
            if isinstance(kind, str) and "." in kind:
                # "domain.entity" → "domain"
                # "app.command" → "app"
                prefix = kind.split(".", 1)[0]
                if prefix and prefix not in {"shared", "meta"}:
                    container_dirs.add(prefix)
    
    return container_dirs


def extract_http_path_ignore_segments(schema_tree: dict[str, Any]) -> set[str]:
    """
    Extract segments to ignore when parsing HTTP paths for module hints.
    
    Common segments: "api", "v1", "v2", "admin"
    
    Args:
        schema_tree: Full schema tree
    
    Returns:
        Set of path segments to ignore
    """
    # Standard API versioning and common prefixes
    ignore_segments = {
        "api",
        "v1", "v2", "v3",  # Versioning
        "admin",           # Admin routes
        "internal",        # Internal APIs
        "public",          # Public APIs
        "private",         # Private APIs
    }
    
    # Could be extended based on schema configuration if needed
    # For now, use standard patterns
    
    return ignore_segments


def get_pluralization_rules() -> dict[str, str]:
    """
    Get irregular pluralization rules for module name extraction.
    
    Returns:
        Dictionary of singular → plural mappings
    """
    return {
        "person": "people",
        "money": "money",      # Uncountable
        "data": "data",        # Uncountable
        "information": "information",  # Uncountable
        "child": "children",
        "man": "men",
        "woman": "women",
        "tooth": "teeth",
        "foot": "feet",
        "mouse": "mice",
        "goose": "geese",
    }


def extract_model_file_mapping(schema_tree: dict[str, Any]) -> dict[str, str]:
    """
    Extract mapping: ModelType → typical file location.
    
    This helps determine which file types contribute to which signals.
    
    Args:
        schema_tree: Full schema tree
    
    Returns:
        Dictionary: model_name → file_pattern
        Example: {"HttpApiFile": "api/http.yaml"}
    """
    mapping: dict[str, str] = {}
    
    # Infer from meta.kind patterns
    modules = schema_tree.get("modules", {})
    for module_path, module_data in modules.items():
        if not isinstance(module_data, dict):
            continue
        
        models = module_data.get("models", {})
        for model_name, model_schema in models.items():
            if not isinstance(model_schema, dict):
                continue
            
            if not model_name.endswith("File"):
                continue
            
            meta = model_schema.get("meta", {})
            if not isinstance(meta, dict):
                continue
            
            kind = meta.get("kind", "")
            
            # Map kind to file path pattern
            # "api.http_file" → "api/http.yaml"
            # "domain.entity" → "domain/entities.yaml"
            
            if kind == "api.http_file":
                mapping[model_name] = "api/http.yaml"
            elif kind == "api.graphql":
                mapping[model_name] = "api/graphql.yaml"
            elif kind == "workflow.definition":
                mapping[model_name] = "workflows/*.yaml"
            # Add more as needed
    
    return mapping


def should_apply_signals_for_model(meta_kind: str) -> bool:
    """
    Check if model type should have signal-based intent.kind inference.
    
    Only Commands and Queries have signal-based inference (routes, workflows).
    Other types have fixed intent.kind based on meta.kind.
    
    Args:
        meta_kind: The meta.kind value from schema
    
    Returns:
        True if signals should be collected and applied
    """
    # Only app.command and app.query use signals
    return meta_kind in {"app.command", "app.query"}


def get_signal_intent_kind(signal_type: str) -> tuple[str, float]:
    """
    Get intent.kind and confidence for a given signal type.
    
    Args:
        signal_type: Type of signal (e.g., "http_route", "graphql_mutation")
    
    Returns:
        Tuple of (intent_kind, confidence)
    """
    signal_mapping = {
        "http_route": ("controller", CONFIDENCE_HIGH),
        "graphql_mutation": ("controller", CONFIDENCE_HIGH),
        "graphql_query": ("controller", CONFIDENCE_HIGH),
        "workflow_transition": ("service", CONFIDENCE_MEDIUM),
    }
    
    return signal_mapping.get(signal_type, ("service", CONFIDENCE_LOW))
