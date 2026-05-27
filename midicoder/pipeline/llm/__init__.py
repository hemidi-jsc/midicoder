"""
Package LLM Client cho Midicoder Pipeline (REBUILD với litellm).

Sử dụng litellm SDK để wrap multiple LLM providers:
- openai-compatible: Custom URL với OpenAI API format (default)
- openai: OpenAI API
- anthropic: Anthropic API
- aws-bedrock: AWS Bedrock
- azure: Azure AI Foundry
- vertex: Google Vertex AI

Sử dụng:
    from midicoder.pipeline.llm import load_llm_config, call_llm, call_llm_async, call_llm_stream

    # Load config từ file
    config = load_llm_config()

    # Sync call
    response = call_llm(
        config=config,
        system="You are a helpful assistant",
        messages=[{"role": "user", "content": "Hello!"}]
    )
    print(response.content)

    # Async call
    response = await call_llm_async(config=config, messages=...)

    # Streaming
    async for chunk in call_llm_stream(config=config, messages=...):
        print(chunk.content, end="", flush=True)
"""

from midicoder.pipeline.llm.client import (
    # Data classes
    LlmConfig,
    LlmResponse,
    LlmStreamChunk,
    # Config loading
    load_llm_config,
    # Sync API
    call_llm,
    # Async API
    call_llm_async,
    call_llm_stream,
)

__all__ = [
    # Data classes
    "LlmConfig",
    "LlmResponse",
    "LlmStreamChunk",
    # Config loading
    "load_llm_config",
    # Sync API
    "call_llm",
    # Async API
    "call_llm_async",
    "call_llm_stream",
]