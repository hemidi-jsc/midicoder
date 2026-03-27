from __future__ import annotations

from typing import TYPE_CHECKING

from midicoder.llm.adapters.anthropic import AnthropicAdapter
from midicoder.llm.adapters.azure import AzureAdapter
from midicoder.llm.adapters.base import ProviderAdapter
from midicoder.llm.adapters.bedrock import BedrockAdapter
from midicoder.llm.adapters.openai import OpenAIAdapter
from midicoder.llm.adapters.openai_compatible import OpenAICompatibleAdapter
from midicoder.llm.adapters.vertex_partner import VertexPartnerAdapter

if TYPE_CHECKING:
    from midicoder.llm.client import LlmConfig

_OPENAI_ADAPTER = OpenAIAdapter()
_OPENAI_COMPATIBLE_ADAPTER = OpenAICompatibleAdapter()
_ANTHROPIC_ADAPTER = AnthropicAdapter()
_AZURE_ADAPTER = AzureAdapter()
_VERTEX_PARTNER_ADAPTER = VertexPartnerAdapter()
_BEDROCK_ADAPTER = BedrockAdapter()

_PROVIDER_ADAPTERS: dict[str, ProviderAdapter] = {
    _OPENAI_ADAPTER.provider: _OPENAI_ADAPTER,
    _OPENAI_COMPATIBLE_ADAPTER.provider: _OPENAI_COMPATIBLE_ADAPTER,
    _ANTHROPIC_ADAPTER.provider: _ANTHROPIC_ADAPTER,
    _AZURE_ADAPTER.provider: _AZURE_ADAPTER,
    _VERTEX_PARTNER_ADAPTER.provider: _VERTEX_PARTNER_ADAPTER,
    _BEDROCK_ADAPTER.provider: _BEDROCK_ADAPTER,
}


def infer_provider_from_model(model: str) -> str | None:
    prefix = model.split("/", 1)[0].strip().lower() if "/" in model else ""
    return {
        "openai": "openai",
        "anthropic": "anthropic",
        "azure": "azure",
        "vertex_ai": "vertex_partner",
        "bedrock": "bedrock",
    }.get(prefix)


def get_adapter(config: LlmConfig) -> ProviderAdapter:
    provider_raw = (config.provider or "").strip().lower()
    provider = {
        "openai": "openai",
        "openai_compatible": "openai_compatible",
        "anthropic": "anthropic",
        "azure": "azure",
        "vertex_partner": "vertex_partner",
        "bedrock": "bedrock",
    }.get(provider_raw, provider_raw)

    if not provider:
        provider = infer_provider_from_model(config.model)

    if provider and provider in _PROVIDER_ADAPTERS:
        return _PROVIDER_ADAPTERS[provider]

    # Default to OpenAI-compatible behavior for unknown provider ids.
    return _OPENAI_COMPATIBLE_ADAPTER
