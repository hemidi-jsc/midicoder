from __future__ import annotations

from typing import ClassVar, Optional

from pydantic import BaseModel, Field

from .model_meta import ModelMeta

SECRET_PROVIDER_CATALOG = {
    "env",
    "vault",
    "aws_secrets_manager",
    "gcp_secret_manager",
    "azure_key_vault",
}


class SecretRef(BaseModel):
    id: str
    provider: str
    key: str
    description: Optional[str] = None
    required: bool = True
    tags: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class SecretsContractFile(BaseModel):
    secrets: list[SecretRef]

    model_config = {"extra": "forbid"}

    model_meta: ClassVar[ModelMeta] = ModelMeta(
        kind="ops.secrets",
        usage_en=(
            "Secret references used by contracts. Secret values are never stored "
            "in DSL files, only references to secret providers."
        ),
    )
