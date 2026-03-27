from __future__ import annotations

from typing import Any, TYPE_CHECKING

from midicoder.llm.adapters.base import BaseAdapter

if TYPE_CHECKING:
    from midicoder.llm.client import LlmConfig


class BedrockAdapter(BaseAdapter):
    provider = "bedrock"

    def model_identifier(self, config: LlmConfig) -> str:
        return self._with_prefix(config.model, "bedrock")

    def completion_params(self, config: LlmConfig) -> dict[str, Any]:
        params: dict[str, Any] = {}
        region = config.aws_region_name
        if region:
            params["aws_region_name"] = region
        if config.aws_access_key_id:
            params["aws_access_key_id"] = config.aws_access_key_id
        if config.aws_secret_access_key:
            params["aws_secret_access_key"] = config.aws_secret_access_key
        return params
