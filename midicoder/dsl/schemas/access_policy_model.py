from __future__ import annotations

from typing import ClassVar, Optional

from pydantic import BaseModel, Field, constr, field_validator

from .model_meta import ModelMeta

PERMISSION_ACTION_CATALOG = {
    "read",
    "write",
    "delete",
    "admin",
}


ResourceRefStr = constr(
    pattern=r"^((entity|command|query|projection|api|document):.+|(Entity|Command|Query|Projection):[A-Za-z_][A-Za-z0-9_]*)$"
)


class Role(BaseModel):
    id: str
    description: Optional[str] = None

    model_config = {"extra": "forbid"}


class Permission(BaseModel):
    id: str
    description: Optional[str] = None
    resource: ResourceRefStr
    action: str

    model_config = {"extra": "forbid"}

    @field_validator("resource")
    @classmethod
    def normalize_legacy_resource(cls, value: str) -> str:
        # Backward compatibility: support legacy typed refs like Entity:Order
        # while normalizing to namespace resource refs.
        if ":" not in value:
            return value
        kind, ref = value.split(":", 1)
        kind_map = {
            "Entity": "entity",
            "Command": "command",
            "Query": "query",
            "Projection": "projection",
        }
        canonical_kind = kind_map.get(kind, kind)
        return f"{canonical_kind}:{ref}"


class Binding(BaseModel):
    role: str
    permissions: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class AccessPolicy(BaseModel):
    roles: list[Role] = Field(default_factory=list)
    permissions: list[Permission] = Field(default_factory=list)
    bindings: list[Binding] = Field(default_factory=list)

    model_config = {"extra": "forbid"}

    model_meta: ClassVar[ModelMeta] = ModelMeta(
        kind="policy.access",
        usage_en=(
            "Role and permission model used to express RBAC/ABAC style access policies across "
            "commands, queries, workflows and APIs."
        ),
        included_by=[
            "api.http_route",
            "scenario.definition",
        ],
        includes=[],
        real_world_examples=[
            "SaaS tenant roles owner, admin and member",
            "Permissions for managing users, billing and settings",
            "Role bindings for project-based access control",
            "Separated support and engineering access to tickets",
            "Fine-grained permissions for feature flags management",
        ],
        visualizers=[
            "Access control dashboards",
            "Security and compliance tools",
        ],
    )


class AccessPolicyFile(BaseModel):
    access: AccessPolicy

    model_config = {"extra": "forbid"}
