from __future__ import annotations

from typing import ClassVar

from pydantic import BaseModel, Field

from .model_meta import ModelMeta

OBSERVABILITY_KIND_CATALOG = {
    "command",
    "workflow",
    "integration",
    "integration_operation",
    "persistence.table",
    "persistence.datasource",
}


class ObservabilityTarget(BaseModel):
    kind: str
    ref: str
    log_fields: list[str] = Field(default_factory=list)
    metrics: list[str] = Field(default_factory=list)
    trace_enabled: bool = True
    alert_rules: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class ObservabilityFile(BaseModel):
    observability: list[ObservabilityTarget]

    model_config = {"extra": "forbid"}

    model_meta: ClassVar[ModelMeta] = ModelMeta(
        kind="ops.observability",
        usage_en=(
            "Observability declarations for logs, metrics, traces and alerting "
            "targets bound to commands, workflows and integrations."
        ),
    )
