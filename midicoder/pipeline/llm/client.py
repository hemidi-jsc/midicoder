"""
LLM Client cho Midicoder Pipeline (REBUILD với litellm).

Sử dụng litellm SDK để wrap multiple LLM providers:
- openai-compatible: Custom URL với OpenAI API format
- openai: OpenAI API
- anthropic: Anthropic API
- aws-bedrock: AWS Bedrock
- azure: Azure AI Foundry
- vertex: Google Vertex AI

Sử dụng:
    from midicoder.pipeline.llm import load_llm_config, call_llm, call_llm_async, call_llm_stream

    # Load config
    config = load_llm_config()

    # Sync call
    response = call_llm(config=config, messages=[{"role": "user", "content": "Hello!"}])

    # Async call
    response = await call_llm_async(config=config, messages=...)

    # Streaming
    async for chunk in call_llm_stream(config=config, messages=...):
        print(chunk.content, end="")
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Optional

import litellm
from litellm import APIError, RateLimitError, AuthenticationError

from midicoder.pipeline.config import get_config

# Logger cho metadata logging
logger = __import__("logging").getLogger(__name__)


# ============================================================================
# Supported Providers
# ============================================================================

SUPPORTED_PROVIDERS = [
    "openai-compatible",
    "openai",
    "anthropic",
    "aws-bedrock",
    "azure",
    "vertex",
]


# ============================================================================
# Data Classes
# ============================================================================

@dataclass(frozen=True)
class LlmConfig:
    """
    Cấu hình cho LLM client.
    
    Attributes:
        provider: LLM provider (openai-compatible, openai, anthropic, aws-bedrock, azure, vertex)
        model: Model name (vd: "gpt-4o", "claude-3-sonnet", "qwen3.5-27B")
        api_url: API endpoint URL
        api_key: API key cho authentication (optional)
        max_tokens: Max tokens cho response (default: 8192)
        temperature: Temperature cho sampling 0.0-1.0 (default: 0.3)
        timeout: Timeout cho request bằng giây (default: 300)
        retry_attempts: Số lần retry khi fail (default: 3)
    """
    
    provider: str
    model: str
    api_url: str
    api_key: Optional[str] = None
    max_tokens: int = 8192
    temperature: float = 0.3
    timeout: int = 300
    retry_attempts: int = 3


@dataclass
class LlmResponse:
    """
    Response từ LLM.
    
    Attributes:
        content: Content từ LLM response
        usage: Token usage info (prompt_tokens, completion_tokens, total_tokens)
        raw: Raw response object từ litellm
    """
    
    content: str
    usage: dict
    raw: Any = None


@dataclass
class LlmStreamChunk:
    """
    Chunk từ streaming LLM response.
    
    Attributes:
        content: Incremental content (có thể empty)
        usage: Token usage (chỉ có trong last chunk)
    """
    
    content: str
    usage: Optional[dict] = None


# ============================================================================
# Config Loading
# ============================================================================

def load_llm_config() -> LlmConfig:
    """
    Load LLM config từ global config file.
    
    Đọc config từ ~/.midicoder/midicoder.json với structure:
    {
        "llm": {
            "provider": "openai-compatible",
            "model": "qwen3.5-27B",
            "api_url": "http://localhost:11434/v1",
            "api_key": "sk-...",
            "max_tokens": 8192,
            "temperature": 0.3,
            "timeout": 300,
            "retry_attempts": 3
        }
    }
    
    Returns:
        LlmConfig instance với values từ config file + defaults
    
    Raises:
        ValueError: Nếu thiếu required fields (model, api_url) hoặc provider không hợp lệ
    """
    config = get_config()
    
    # Read from nested llm.* keys
    provider = config.get("llm.provider", "openai-compatible")
    model = config.get("llm.model")
    api_url = config.get("llm.api_url")
    api_key = config.get("llm.api_key")
    
    # Optional fields với defaults
    max_tokens = config.get("llm.max_tokens", 8192)
    temperature = config.get("llm.temperature", 0.3)
    timeout = config.get("llm.timeout", 300)
    retry_attempts = config.get("llm.retry_attempts", 3)
    
    # Apply defaults nếu None
    if max_tokens is None:
        max_tokens = 8192
    if temperature is None:
        temperature = 0.3
    if timeout is None:
        timeout = 300
    if retry_attempts is None:
        retry_attempts = 3
    
    # Validate required fields
    if not model:
        raise ValueError("Thiếu 'llm.model' trong config file")
    if not api_url:
        raise ValueError("Thiếu 'llm.api_url' trong config file")
    
    # Validate provider
    if provider not in SUPPORTED_PROVIDERS:
        raise ValueError(
            f"Provider '{provider}' không hợp lệ. "
            f"Supported: {', '.join(SUPPORTED_PROVIDERS)}"
        )
    
    return LlmConfig(
        provider=provider,
        model=model,
        api_url=api_url,
        api_key=api_key,
        max_tokens=max_tokens,
        temperature=temperature,
        timeout=timeout,
        retry_attempts=retry_attempts,
    )


# ============================================================================
# Helper Functions
# ============================================================================

def _build_messages(system: Optional[str], messages: list[dict[str, str]]) -> list[dict[str, str]]:
    """
    Build messages list cho litellm từ system prompt + messages.
    
    Args:
        system: System prompt (optional)
        messages: User messages list
        
    Returns:
        Formatted messages list cho litellm
    """
    result = []
    
    if system:
        result.append({"role": "system", "content": system})
    
    result.extend(messages)
    
    return result


def _extract_usage(usage_obj: Any) -> dict:
    """
    Extract usage dict từ litellm response usage object.
    
    Args:
        usage_obj: Usage object từ litellm response
        
    Returns:
        Dict với prompt_tokens, completion_tokens, total_tokens
    """
    if usage_obj is None:
        return {}
    
    # litellm usage có thể là object hoặc dict
    if hasattr(usage_obj, "prompt_tokens"):
        return {
            "prompt_tokens": getattr(usage_obj, "prompt_tokens", 0),
            "completion_tokens": getattr(usage_obj, "completion_tokens", 0),
            "total_tokens": getattr(usage_obj, "total_tokens", 0),
        }
    
    # Nếu là dict
    return {
        "prompt_tokens": usage_obj.get("prompt_tokens", 0),
        "completion_tokens": usage_obj.get("completion_tokens", 0),
        "total_tokens": usage_obj.get("total_tokens", 0),
    }


def _log_call(
    config: LlmConfig,
    status: str,
    tokens_used: int = 0,
    latency_ms: int = 0,
) -> None:
    """
    Log LLM call metadata (không log content).
    
    Args:
        config: LLM config
        status: "success" hoặc "error"
        tokens_used: Số tokens đã dùng
        latency_ms: Latency bằng mili giây
    """
    logger.info(
        "LLM call completed",
        extra={
            "provider": config.provider,
            "model": config.model,
            "tokens_used": tokens_used,
            "latency_ms": latency_ms,
            "status": status,
        },
    )


# ============================================================================
# Sync API
# ============================================================================

def call_llm(
    config: LlmConfig,
    *,
    system: Optional[str] = None,
    messages: Optional[list[dict[str, str]]] = None,
) -> LlmResponse:
    """
    Call LLM sync, trả về full response.
    
    Sử dụng litellm.completion() để gọi LLM. Block cho đến khi response
    hoàn chỉnh. Retry logic do litellm handle.
    
    Args:
        config: LLM config
        system: System prompt (optional)
        messages: User messages list (OpenAI-style format)
        
    Returns:
        LlmResponse với content, usage, raw
        
    Raises:
        litellm.APIError: Khi API trả về error
        litellm.RateLimitError: Khi rate limit
        litellm.AuthenticationError: Khi auth fail
    """
    messages_list = _build_messages(system, messages or [])
    
    start_time = time.time()
    
    try:
        # Build model string for litellm
        # For openai-compatible providers, use "openai/{model}" so litellm routes correctly
        if config.provider == "openai-compatible":
            model_str = f"openai/{config.model}"
        else:
            model_str = f"{config.provider}/{config.model}"

        # Call litellm completion
        response = litellm.completion(
            model=model_str,
            messages=messages_list,
            api_base=config.api_url,
            api_key=config.api_key,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            timeout=config.timeout,
            num_retries=config.retry_attempts,
            stream=False,
        )
        
        # Extract content (handle cả dict và object response)
        content = ""
        reasoning = ""
        if response.choices:
            choice = response.choices[0]
            if isinstance(choice, dict):
                msg = choice.get("message", {})
                content = msg.get("content", "") or ""
                reasoning = msg.get("reasoning", "") or ""
            else:
                content = choice.message.content or ""
                reasoning = getattr(choice.message, "reasoning", "") or ""

        # For reasoning models: append reasoning after content
        if reasoning and not content:
            content = reasoning
        elif reasoning and content:
            content = content + "\n" + reasoning
        
        # Extract usage
        usage = _extract_usage(response.usage)
        
        latency_ms = int((time.time() - start_time) * 1000)
        _log_call(config, "success", usage.get("total_tokens", 0), latency_ms)
        
        return LlmResponse(
            content=content,
            usage=usage,
            raw=response,
        )
        
    except (APIError, RateLimitError, AuthenticationError):
        latency_ms = int((time.time() - start_time) * 1000)
        _log_call(config, "error", 0, latency_ms)
        raise


# ============================================================================
# Async API
# ============================================================================

async def call_llm_async(
    config: LlmConfig,
    *,
    system: Optional[str] = None,
    messages: Optional[list[dict[str, str]]] = None,
) -> LlmResponse:
    """
    Call LLM async, trả về full response.
    
    Sử dụng litellm.acompletion() để gọi LLM non-blocking.
    
    Args:
        config: LLM config
        system: System prompt (optional)
        messages: User messages list
        
    Returns:
        LlmResponse với content, usage, raw
        
    Raises:
        litellm.APIError: Khi API trả về error
        litellm.RateLimitError: Khi rate limit
        litellm.AuthenticationError: Khi auth fail
    """
    messages_list = _build_messages(system, messages or [])
    
    start_time = time.time()
    
    try:
        response = await litellm.acompletion(
            model=f"{config.provider}/{config.model}",
            messages=messages_list,
            api_base=config.api_url,
            api_key=config.api_key,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            timeout=config.timeout,
            num_retries=config.retry_attempts,
            stream=False,
        )
        
        # Extract content (handle cả dict và object response)
        content = ""
        reasoning = ""
        if response.choices:
            choice = response.choices[0]
            if isinstance(choice, dict):
                msg = choice.get("message", {})
                content = msg.get("content", "") or ""
                reasoning = msg.get("reasoning", "") or ""
            else:
                content = choice.message.content or ""
                reasoning = getattr(choice.message, "reasoning", "") or ""

        # For reasoning models: append reasoning after content
        if reasoning and not content:
            content = reasoning
        elif reasoning and content:
            content = content + "\n" + reasoning
        
        usage = _extract_usage(response.usage)
        
        latency_ms = int((time.time() - start_time) * 1000)
        _log_call(config, "success", usage.get("total_tokens", 0), latency_ms)
        
        return LlmResponse(
            content=content,
            usage=usage,
            raw=response,
        )
        
    except (APIError, RateLimitError, AuthenticationError):
        latency_ms = int((time.time() - start_time) * 1000)
        _log_call(config, "error", 0, latency_ms)
        raise


async def call_llm_stream(
    config: LlmConfig,
    *,
    system: Optional[str] = None,
    messages: Optional[list[dict[str, str]]] = None,
) -> AsyncIterator[LlmStreamChunk]:
    """
    Call LLM với streaming, trả về chunks qua async generator.
    
    Sử dụng litellm.acompletion(stream=True) để stream response.
    Yield từng chunk theo thời gian thực.
    
    Args:
        config: LLM config
        system: System prompt (optional)
        messages: User messages list
        
    Yields:
        LlmStreamChunk với content và usage (usage chỉ có trong last chunk)
        
    Raises:
        litellm.APIError: Khi API trả về error
        litellm.RateLimitError: Khi rate limit
        litellm.AuthenticationError: Khi auth fail
    """
    messages_list = _build_messages(system, messages or [])
    
    start_time = time.time()
    
    try:
        stream = await litellm.acompletion(
            model=f"{config.provider}/{config.model}",
            messages=messages_list,
            api_base=config.api_url,
            api_key=config.api_key,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            timeout=config.timeout,
            num_retries=config.retry_attempts,
            stream=True,
        )
        
        last_chunk_usage = None
        
        async for chunk in stream:
            # Extract content from delta (handle cả dict và object)
            content = ""
            if chunk.choices:
                choice = chunk.choices[0]
                if isinstance(choice, dict):
                    delta = choice.get("delta", {})
                    content = delta.get("content", "") if isinstance(delta, dict) else ""
                else:
                    delta = choice.delta
                    if hasattr(delta, "content") and delta.content:
                        content = delta.content
            
            # Check for usage in chunk (usually in last chunk)
            if hasattr(chunk, "usage") and chunk.usage:
                last_chunk_usage = _extract_usage(chunk.usage)
            elif isinstance(chunk, dict) and chunk.get("usage"):
                last_chunk_usage = _extract_usage(chunk["usage"])
            
            yield LlmStreamChunk(content=content, usage=last_chunk_usage)
        
        latency_ms = int((time.time() - start_time) * 1000)
        _log_call(config, "success", last_chunk_usage.get("total_tokens", 0) if last_chunk_usage else 0, latency_ms)
        
    except (APIError, RateLimitError, AuthenticationError):
        latency_ms = int((time.time() - start_time) * 1000)
        _log_call(config, "error", 0, latency_ms)
        raise