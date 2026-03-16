from __future__ import annotations

from typing import ClassVar, Optional

from pydantic import BaseModel, Field

from .model_meta import ModelMeta


class CorsPolicy(BaseModel):
    allowed_origins: list[str] = Field(default_factory=list)
    allowed_methods: list[str] = Field(default_factory=list)
    allowed_headers: list[str] = Field(default_factory=list)
    allow_credentials: bool = False

    model_config = {"extra": "forbid"}


class RateLimitRule(BaseModel):
    id: str
    requests: int
    per_seconds: int
    scope: str = "global"

    model_config = {"extra": "forbid"}


class PiiMaskingRule(BaseModel):
    field: str
    strategy: str

    model_config = {"extra": "forbid"}


class SecurityBaseline(BaseModel):
    auth_required: bool = True
    authz_required: bool = True
    cors: Optional[CorsPolicy] = None
    rate_limits: list[RateLimitRule] = Field(default_factory=list)
    pii_masking: list[PiiMaskingRule] = Field(default_factory=list)
    webhook_signature_required: bool = False

    model_config = {"extra": "forbid"}


class SecurityBaselineFile(BaseModel):
    security: SecurityBaseline

    model_config = {"extra": "forbid"}

    model_meta: ClassVar[ModelMeta] = ModelMeta(
        kind="ops.security_baseline",
        usage_en=(
            "Security baseline policy for minimum auth, authorization, CORS, "
            "rate limiting and PII masking requirements."
        ),
    )

