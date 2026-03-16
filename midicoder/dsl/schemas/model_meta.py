from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from . import DSL_SCHEMA_VERSION


@dataclass(frozen=True)
class ModelMeta:
    """Metadata describing a DSL model type.

    This is used for documentation, tooling, and schema tree
    generation. It is not part of the DSL YAML surface and is
    therefore attached to Pydantic models as a `ClassVar`.
    """

    kind: str
    usage_en: str
    included_by: list[str] = field(default_factory=list)
    includes: list[str] = field(default_factory=list)
    real_world_examples: list[str] = field(default_factory=list)
    visualizers: list[str] = field(default_factory=list)
    introduced_in: str = DSL_SCHEMA_VERSION
    deprecated_in: str | None = None
    replaced_by: str | None = None
    status: Literal["active", "deprecated", "experimental"] = "active"


__all__ = ["ModelMeta"]

