from __future__ import annotations

from typing import Any, TYPE_CHECKING

from midicoder.llm.adapters.base import BaseAdapter

if TYPE_CHECKING:
    from midicoder.llm.client import LlmConfig


class AnthropicAdapter(BaseAdapter):
    provider = "anthropic"

    def model_identifier(self, config: LlmConfig) -> str:
        return self._with_prefix(config.model, "anthropic")

    def completion_params(self, config: LlmConfig) -> dict[str, Any]:
        return self._completion_api_base_params(config)

    def build_context_message(self, config: LlmConfig, context: str) -> dict[str, Any]:
        if config.cache_enabled and config.cache_type:
            return {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": context,
                        "cache_control": {"type": config.cache_type},
                    }
                ],
            }
        return super().build_context_message(config, context)
