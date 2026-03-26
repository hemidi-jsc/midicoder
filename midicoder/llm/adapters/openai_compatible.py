from __future__ import annotations

from typing import Any, TYPE_CHECKING

from midicoder.llm.adapters.base import BaseAdapter

if TYPE_CHECKING:
    from midicoder.llm.client import LlmConfig


class OpenAICompatibleAdapter(BaseAdapter):
    provider = "openai_compatible"

    def model_identifier(self, config: LlmConfig) -> str:
        # LiteLLM OpenAI-compatible routing uses the OpenAI provider with a custom base URL.
        return self._with_prefix(config.model, "openai")

    def completion_params(self, config: LlmConfig) -> dict[str, Any]:
        params = self._completion_api_base_params(config)
        api_base = params.get("api_base")
        if isinstance(api_base, str) and api_base.strip():
            params["api_base"] = self._normalize_openai_api_base(api_base)
        params["custom_llm_provider"] = "openai"
        return params
