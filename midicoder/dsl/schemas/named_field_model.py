from __future__ import annotations

import re
from typing import Any, ClassVar, Optional

from pydantic import BaseModel, Field, field_validator

from .model_meta import ModelMeta

SCALAR_TYPE_CATALOG = {
    "string",
    "text",
    "int",
    "float",
    "decimal",
    "bool",
    "datetime",
    "date",
    "time",
    "uuid",
    "json",
}

COMPOSITE_TYPE_CATALOG = {
    "list<string>",
    "list<int>",
    "list<float>",
    "list<uuid>",
    "map<string,string>",
    "map<string,int>",
}

REF_TYPE_PREFIXES = {
    "Entity:",
    "ValueObject:",
    "Enum:",
    "Integration:",
    "IntegrationOperation:",
    "Role:",
    "Permission:",
    "Scenario:",
    "PersistenceTable:",
    "PersistenceDatasource:",
}

_REF_TYPE_RE = re.compile(
    r"^(Entity|ValueObject|Enum|Integration|IntegrationOperation|Role|Permission|Scenario|PersistenceTable|PersistenceDatasource):([A-Za-z_][A-Za-z0-9_]*)$"
)
_LEGACY_MODEL_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _split_generic_args(raw: str) -> list[str]:
    parts: list[str] = []
    depth = 0
    start = 0
    for idx, char in enumerate(raw):
        if char == "<":
            depth += 1
        elif char == ">":
            depth -= 1
            if depth < 0:
                return []
        elif char == "," and depth == 0:
            parts.append(raw[start:idx].strip())
            start = idx + 1
    if depth != 0:
        return []
    parts.append(raw[start:].strip())
    return [part for part in parts if part]


def is_valid_type_expression(type_expr: str) -> bool:
    value = type_expr.strip()
    if not value:
        return False
    if value.lower() in SCALAR_TYPE_CATALOG:
        return True
    if value in COMPOSITE_TYPE_CATALOG:
        return True
    if _REF_TYPE_RE.match(value):
        return True
    if _LEGACY_MODEL_RE.match(value):
        # Backward compatibility for legacy model refs like `AttendanceRecord`.
        return True
    if value.startswith("list<") and value.endswith(">"):
        return is_valid_type_expression(value[5:-1].strip())
    if value.startswith("map<") and value.endswith(">"):
        args = _split_generic_args(value[4:-1].strip())
        return len(args) == 2 and all(is_valid_type_expression(arg) for arg in args)
    return False


def extract_type_refs(type_expr: str) -> list[tuple[str, str]]:
    value = type_expr.strip()
    match = _REF_TYPE_RE.match(value)
    if match:
        return [(match.group(1).lower(), match.group(2))]
    if _LEGACY_MODEL_RE.match(value) and value.lower() not in SCALAR_TYPE_CATALOG:
        return [("legacy", value)]
    if value.startswith("list<") and value.endswith(">"):
        return extract_type_refs(value[5:-1].strip())
    if value.startswith("map<") and value.endswith(">"):
        refs: list[tuple[str, str]] = []
        for arg in _split_generic_args(value[4:-1].strip()):
            refs.extend(extract_type_refs(arg))
        return refs
    return []


class NamedField(BaseModel):
    name: str
    type: str
    required: bool = True
    description: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    default: Any | None = None
    constraints: dict[str, Any] = Field(default_factory=dict)
    source: Optional[str] = None
    introduced_in: Optional[str] = None
    deprecated_in: Optional[str] = None
    replaced_by: Optional[str] = None
    status: Optional[str] = None

    model_config = {"extra": "forbid"}

    @field_validator("type")
    @classmethod
    def validate_type_expression(cls, value: str) -> str:
        if not is_valid_type_expression(value):
            raise ValueError(
                "Invalid type expression. Use scalar, list<...>, map<k,v>, "
                "Entity:<id>, ValueObject:<id>, Enum:<id>, "
                "Integration:<id>, IntegrationOperation:<id>, Role:<id>, Permission:<id>, "
                "Scenario:<id>, PersistenceTable:<id>, PersistenceDatasource:<id>, or legacy model id."
            )
        return value

    model_meta: ClassVar[ModelMeta] = ModelMeta(
        kind="shared.named_field",
        usage_en=(
            "Reusable field descriptor used across entities, value objects, commands, queries, "
            "events and API schemas to describe typed inputs and outputs."
        ),
        included_by=[
            "domain.entity",
            "domain.value_object",
            "domain.event",
            "app.command",
            "app.query",
            "app.projection",
            "api.http_route",
            "api.graphql",
            "scenario.definition",
        ],
        includes=[],
        real_world_examples=[
            "User.email string field with validation constraints",
            "Subscription.plan_id enum reference field",
            "Invoice.total_amount decimal field",
            "AuditEvent.occurred_at datetime field",
            "Search.query text field for free-text search",
        ],
        visualizers=[
            "dbdiagram.io",
            "Mermaid ERD",
            "OpenAPI/Swagger UI",
        ],
    )
