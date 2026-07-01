"""
MCP-B: DSL Schema Tools.

Cung cấp 2 MCP tools:
- get_dsl_schema: Trả về schema đầy đủ của DSL (node types, fields, required/optional)
- get_dsl_section: Trả về schema cho một section cụ thể (entities, commands, ui_components, ...)

Source: midicoder.dsl.projection (TypedDict models)
"""

from __future__ import annotations

import inspect
import logging
from typing import Any, Dict, List, Optional

from midicoder.errors import MidicoderErrorManager as EM, ErrorCode

logger = logging.getLogger(__name__)

# ============================================================================
# TypedDict registry — ánh xạ section → TypedDict classes
# ============================================================================

# Các TypedDict chính từ projection.py, nhóm theo sections
DSL_SECTIONS: Dict[str, List[str]] = {
    "entities": [
        "EntityParams",
        "ValueObjectParams",
        "AggregateParams",
        "EnumParams",
        "ErrorParams",
        "EventParams",
        "ExtendedValueObjectParams",
        "EventSourcedAggregateParams",
        "TemporalEntityParams",
        "PolymorphicEntityParams",
    ],
    "commands": [
        "CommandParams",
        "QueryParams",
        "WorkflowParams",
        "RuleParams",
        "GuardParams",
        "EffectParams",
        "AggregationQueryParams",
        "SagaParams",
    ],
    "api": [
        "HTTPRouteParams",
        "GraphQLResolverParams",
    ],
    "render_context": [
        "RenderContextParams",
        "StyleComponentParams",
        "PageConfigParams",
        "LayoutParams",
    ],
    "infrastructure": [
        "DataSourceParams",
        "TableParams",
        "IndexParams",
        "CacheParams",
        "QueueParams",
    ],
    "access_control": [
        "RoleParams",
        "PermissionParams",
        "PolicyParams",
    ],
    "observability": [
        "MetricParams",
        "LogParams",
        "TraceParams",
        "AlertParams",
    ],
    "supporting": [
        "FieldDefinition",
        "MethodDefinition",
        "ValidationRule",
    ],
}


def _extract_typeddict_fields(cls: type) -> Dict[str, Any]:
    """
    Extract fields từ một TypedDict class.

    Args:
        cls: TypedDict class

    Returns:
        Dictionary với fields, required keys, total flag
    """
    info: Dict[str, Any] = {
        "name": cls.__name__,
        "description": (cls.__doc__ or "").strip().split("\n")[0],
        "fields": {},
        "total": getattr(cls, "__total__", True),
    }

    # Lấy annotations để biết các fields
    annotations = getattr(cls, "__annotations__", {})
    required_keys = set(getattr(cls, "__required_keys__", set()))
    optional_keys = set(getattr(cls, "__optional_keys__", set()))

    for field_name, field_type in annotations.items():
        info["fields"][field_name] = {
            "type": _type_to_string(field_type),
            "required": field_name in required_keys and field_name not in optional_keys,
        }

    return info


def _type_to_string(tp: Any) -> str:
    """Chuyển đổi type annotation thành string."""
    if hasattr(tp, "__name__"):
        return tp.__name__
    if hasattr(tp, "_name"):
        return tp._name
    return str(tp)


def _build_styles_schema() -> Dict[str, List[str]]:
    """
    Build schema của các style properties available từ presets.

    Đọc tất cả preset files và extract các CSS properties
    cho từng component type.

    Returns:
        Dictionary mapping component_name → sorted list của property names
    """
    try:
        from midicoder.presets import load_preset, list_presets
    except ImportError:
        logger.warning("Không thể import midicoder.presets")
        return {}

    schema: Dict[str, set] = {}

    for preset_name in list_presets():
        preset = load_preset(preset_name)
        if not preset:
            continue

        # Preset structure: {stack_name: {component_name: {prop: value}}}
        for stack_name, stacks in preset.items():
            if not isinstance(stacks, dict):
                continue
            for component_name, props in stacks.items():
                if component_name not in schema:
                    schema[component_name] = set()
                if isinstance(props, dict):
                    for prop in props.keys():
                        schema[component_name].add(prop)

    return {k: sorted(v) for k, v in schema.items()}


def _load_projection_classes() -> Dict[str, type]:
    """
    Load tất cả TypedDict classes từ midicoder.dsl.projection.

    Returns:
        Dictionary mapping class_name → class
    """
    try:
        from midicoder.dsl import projection
    except ImportError:
        logger.warning("Không thể import midicoder.dsl.projection")
        return {}

    classes = {}
    for name in list(DSL_SECTIONS.keys()):
        pass  # We scan all names in the module

    # Scan all TypedDict classes in projection module
    for attr_name in dir(projection):
        attr = getattr(projection, attr_name)
        if (
            inspect.isclass(attr)
            and hasattr(attr, "__annotations__")
            and hasattr(attr, "__total__")
        ):
            classes[attr_name] = attr

    return classes


# ============================================================================
# MCP Tool: get_dsl_schema
# ============================================================================


def get_dsl_schema() -> Dict[str, Any]:
    """
    Trả về schema đầy đủ của DSL — tất cả node types, fields, required/optional.

    Source: midicoder.dsl.projection (TypedDict models)

    Returns:
        Dictionary với:
        - sections: mapping section_name → list của TypedDict info
        - node_kinds: danh sách tất cả NodeKind enum values
        - styles: schema của CSS properties từ presets
        - total_types: số lượng TypedDict classes

    Raises:
        MidicoderError: Nếu không thể load DSL module
    """
    classes = _load_projection_classes()

    if not classes:
        EM.raise_error(
            ErrorCode.DSL_LOAD_FAILED,
            detail="Không thể load DSL projection module",
        )

    # Nhóm classes theo sections
    sections: Dict[str, List[Dict[str, Any]]] = {}
    all_classes = set(classes.keys())

    for section_name, class_names in DSL_SECTIONS.items():
        matched = [
            _extract_typeddict_fields(classes[name])
            for name in class_names
            if name in classes
        ]
        if matched:
            sections[section_name] = matched

    # Classes không thuộc section nào → group vào "other"
    assigned = set()
    for names in DSL_SECTIONS.values():
        assigned.update(names)
    unassigned = all_classes - assigned

    if unassigned:
        sections["other"] = [
            _extract_typeddict_fields(classes[name]) for name in sorted(unassigned)
        ]

    # NodeKind enum
    try:
        from midicoder.dsl.projection import NodeKind

        node_kinds = [
            {"value": nk.value, "name": nk.name} for nk in NodeKind
        ]
    except Exception:
        node_kinds = []

    # Styles schema từ presets
    styles_schema = _build_styles_schema()

    return {
        "sections": sections,
        "node_kinds": node_kinds,
        "styles": styles_schema,
        "total_types": len(classes),
    }


# ============================================================================
# MCP Tool: get_dsl_section
# ============================================================================


def get_dsl_section(section: str) -> Dict[str, Any]:
    """
    Trả về schema cho một section cụ thể của DSL.

    Args:
        section: Tên section (ví dụ: "entities", "commands", "ui_components",
                 "render_context", "infrastructure", "access_control", "observability",
                 "api", "supporting")

    Returns:
        Dictionary với:
        - section: tên section
        - types: list của TypedDict info cho section này
        - styles: (nếu section là "render_context") schema của CSS properties

    Raises:
        MidicoderError: Nếu section không tồn tại
    """
    section = section.strip().lower()

    # Map aliases — contract categories → DSL sections
    section_aliases = {
        # render_context aliases
        "ui_components": "render_context",
        "render": "render_context",
        "style": "render_context",
        "styles": "render_context",
        # entities aliases (events, value_objects live here)
        "entity": "entities",
        "domain": "entities",
        "events": "entities",
        "event": "entities",
        "value_objects": "entities",
        "value_object": "entities",
        # commands aliases (queries, workflows, guards live here)
        "command": "commands",
        "application": "commands",
        "queries": "commands",
        "query": "commands",
        "workflows": "commands",
        "workflow": "commands",
        "guards": "commands",
        "guard": "commands",
        # access_control aliases (roles live here)
        "infra": "infrastructure",
        "access": "access_control",
        "rbac": "access_control",
        "roles": "access_control",
        "role": "access_control",
        # observability
        "ops": "observability",
    }

    resolved = section_aliases.get(section, section)

    if resolved not in DSL_SECTIONS:
        available = ", ".join(sorted(DSL_SECTIONS.keys()))
        EM.raise_error(
            ErrorCode.INVALID_INPUT,
            section=section,
            available_sections=available,
            detail=f"Section '{section}' không tồn tại. Sections: {available}",
        )

    classes = _load_projection_classes()
    class_names = DSL_SECTIONS[resolved]

    types = [
        _extract_typeddict_fields(classes[name])
        for name in class_names
        if name in classes
    ]

    result: Dict[str, Any] = {
        "section": resolved,
        "types": types,
    }

    # Thêm styles schema nếu là render_context
    if resolved == "render_context":
        result["styles"] = _build_styles_schema()

    return result
