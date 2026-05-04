from __future__ import annotations

from pathlib import Path
from typing import Any, get_args, get_origin

from pydantic import BaseModel
from ruamel.yaml import YAML

from . import (
    DSL_SCHEMA_VERSION,
    access_policy_model,
    command_model,
    entity_model,
    enum_model,
    error_model,
    event_model,
    glossary_model,
    graphql_api_model,
    guard_effect_model,
    http_api_model,
    info_model,
    integration_model,
    named_field_model,
    observability_model,
    persistence_model,
    policy_model,
    profiles_model,
    projection_model,
    query_model,
    reliability_model,
    rule_model,
    scenario_model,
    secrets_contract_model,
    security_baseline_model,
    testing_model,
    value_object_model,
    workflow_model,
)
from .model_meta import ModelMeta

yaml = YAML(typ="rt")


SCHEMA_MODULES = [
    info_model,
    profiles_model,
    secrets_contract_model,
    security_baseline_model,
    glossary_model,
    named_field_model,
    entity_model,
    persistence_model,
    value_object_model,
    enum_model,
    error_model,
    event_model,
    guard_effect_model,
    command_model,
    query_model,
    projection_model,
    rule_model,
    workflow_model,
    policy_model,
    access_policy_model,
    reliability_model,
    observability_model,
    http_api_model,
    graphql_api_model,
    integration_model,
    scenario_model,
    testing_model,
]


def _format_type(annotation: Any) -> str:
    """Render a best-effort, LLM-friendly string for a field annotation.

    Key goals:
    - Preserve list element types (e.g. list[str], list[NamedField]).
    - Preserve dict key/value types where possible.
    - Make Optional/Union explicit using ``|`` (e.g. str | None).
    """
    origin = get_origin(annotation)
    args = get_args(annotation)

    # list[T] / list[str] / list[Model]
    if origin is list:
        if not args:
            return "list[Any]"
        inner = " | ".join(_format_type(arg) for arg in args)
        return f"list[{inner}]"

    # dict[K, V]
    if origin is dict:
        if len(args) == 2:
            key_str = _format_type(args[0])
            val_str = _format_type(args[1])
            return f"dict[{key_str}, {val_str}]"
        return "dict[Any, Any]"

    # Union / Optional – render as "A | B | None"
    if origin is not None and args:
        # Generic fallback for other typing constructs (Union, etc.)
        joined = " | ".join(_format_type(arg) for arg in args)
        base = getattr(origin, "__name__", str(origin))
        # Union-style types are clearer without the "Union" wrapper.
        if base == "Union":
            return joined
        return f"{base}[{joined}]"

    # ForwardRef or stringified type (from __future__ annotations)
    forward_arg = getattr(annotation, "__forward_arg__", None)
    if forward_arg:
        return str(forward_arg)

    # Regular classes / builtins
    name = getattr(annotation, "__name__", None)
    if name:
        return name

    return str(annotation)


def _field_type_to_string(annotation: Any) -> str:
    """Render a best-effort string for a field annotation.

    This wrapper exists for backward compatibility; the main logic
    lives in ``_format_type``.
    """
    return _format_type(annotation)


def _model_to_dict(model_cls: type[BaseModel]) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    for name, field in model_cls.model_fields.items():
        fields[name] = {
            "type": _field_type_to_string(field.annotation),
            "required": field.is_required(),
        }

    meta_dict: dict[str, Any] | None = None
    meta: ModelMeta | None = getattr(model_cls, "model_meta", None)
    if isinstance(meta, ModelMeta):
        # For LLM cheat-sheet purposes we only keep the minimal
        # classification signal; long descriptions and examples add
        # noise and tokens without improving schema adherence.
        meta_dict = {
            "kind": meta.kind,
        }

    model_data: dict[str, Any] = {"fields": fields}
    if meta_dict is not None:
        model_data["meta"] = meta_dict
    return model_data


def build_schema_tree(version: str = DSL_SCHEMA_VERSION) -> dict[str, Any]:
    """Build an in-memory representation of the DSL schema tree."""
    tree: dict[str, Any] = {"version": version, "modules": {}}

    for module in SCHEMA_MODULES:
        module_name = module.__name__
        models_section: dict[str, Any] = {}
        catalogs_section: dict[str, list[str]] = {}

        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, BaseModel)
                and attr is not BaseModel
            ):
                models_section[attr.__name__] = _model_to_dict(attr)

        for attr_name in dir(module):
            if not attr_name.isupper() or not attr_name.endswith("_CATALOG"):
                continue
            value = getattr(module, attr_name)
            if isinstance(value, (set, list, tuple)):
                catalogs_section[attr_name] = sorted(str(item) for item in value)
            elif isinstance(value, dict):
                catalogs_section[attr_name] = sorted(str(key) for key in value.keys())

        if models_section or catalogs_section:
            tree["modules"][module_name] = {
                "models": models_section,
                "catalogs": catalogs_section,
            }

    return tree


def write_schema_tree(
    path: Path | None = None, version: str = DSL_SCHEMA_VERSION
) -> Path:
    """Write the schema tree YAML file to disk and return its path."""
    tree = build_schema_tree(version=version)
    if path is None:
        path = Path(__file__).with_name(f"tree_{version}.yml")
    with path.open("w", encoding="utf-8") as handle:
        yaml.dump(tree, handle)
    return path


__all__ = ["build_schema_tree", "write_schema_tree"]
