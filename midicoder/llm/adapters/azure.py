from __future__ import annotations

from typing import Any, TYPE_CHECKING

from midicoder.llm.adapters.base import BaseAdapter

if TYPE_CHECKING:
    from midicoder.llm.client import LlmConfig


class AzureAdapter(BaseAdapter):
    provider = "azure"

    def model_identifier(self, config: LlmConfig) -> str:
        normalized_model = config.model.strip()
        if normalized_model.startswith("azure/"):
            return normalized_model

        deployment = (config.azure_openai_deployment or "").strip()
        if deployment:
            return f"azure/{deployment}"

        return self._with_prefix(normalized_model, "azure")

    def completion_params(self, config: LlmConfig) -> dict[str, Any]:
        params: dict[str, Any] = {}
        if config.azure_openai_endpoint:
            params["api_base"] = config.azure_openai_endpoint
        elif config.base_url:
            params["api_base"] = config.base_url

        if config.azure_openai_api_version:
            params["api_version"] = config.azure_openai_api_version

        return params
