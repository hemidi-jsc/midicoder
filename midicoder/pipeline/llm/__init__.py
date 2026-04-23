"""
Package LLM Client cho Midicoder Pipeline.

Cung cấp wrapper abstraction cho nhiều LLM providers:
- openai-compatible: Custom URL với OpenAI API format (default)
- openai: OpenAI API
- anthropic: Anthropic API
- aws-bedrock: AWS Bedrock
- azure: Azure AI Foundry
- vertex: Google Vertex AI

Sử dụng:
    from midicoder.pipeline.llm import load_llm_config, call_llm, LlmResponse

    # Load config cho tier cụ thể
    config = load_llm_config(tier="analyze")

    # Call LLM
    response = call_llm(
        config=config,
        system="You are a helpful assistant",
        prompt="Hello!"
    )
    print(response.content)
"""

from midicoder.pipeline.llm.client import (
    LlmConfig,
    LlmResponse,
    LlmError,
    LlmRequestError,
    LlmAuthError,
    LlmRateLimitError,
    LlmTimeoutError,
    load_llm_config,
    call_llm,
)

__all__ = [
    # Data classes
    "LlmConfig",
    "LlmResponse",
    # Exceptions
    "LlmError",
    "LlmRequestError",
    "LlmAuthError",
    "LlmRateLimitError",
    "LlmTimeoutError",
    # Functions
    "load_llm_config",
    "call_llm",
]