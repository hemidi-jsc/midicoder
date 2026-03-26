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
        region = config.aws_region_name or config.aws_bedrock_region
        if region:
            params["aws_region_name"] = region
        return params
