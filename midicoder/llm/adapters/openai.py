from __future__ import annotations

from typing import Any, TYPE_CHECKING

from midicoder.llm.adapters.base import BaseAdapter

if TYPE_CHECKING:
    from midicoder.llm.client import LlmConfig


class OpenAIAdapter(BaseAdapter):
    provider = "openai"

    def model_identifier(self, config: LlmConfig) -> str:
        return config.model.strip()

    def completion_params(self, config: LlmConfig) -> dict[str, Any]:
        return self._completion_api_base_params(config)
