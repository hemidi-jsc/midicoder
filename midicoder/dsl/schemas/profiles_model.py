from __future__ import annotations

from typing import Any, ClassVar

from pydantic import BaseModel, Field

from .model_meta import ModelMeta


ENVIRONMENT_CATALOG = {
    "local",
    "dev",
    "staging",
    "prod",
}


class EnvironmentProfile(BaseModel):
    name: str
    overrides: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class ProfilesFile(BaseModel):
    profiles: list[EnvironmentProfile]

    model_config = {"extra": "forbid"}

    model_meta: ClassVar[ModelMeta] = ModelMeta(
        kind="ops.profiles",
        usage_en=(
            "Environment profile overrides for local/dev/staging/prod deployment "
            "differences in endpoints, feature flags and operational settings."
        ),
    )
