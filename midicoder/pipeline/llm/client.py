"""
LLM Client cho Midicoder Pipeline (sử dụng OpenAI SDK).

Sử dụng OpenAI SDK (openai package) để call LLM API — tương thích với mọi
OpenAI-compatible endpoint bao gồm Qwen, Ollama, v.v.

Xử lý đúng reasoning models:
- content: None khi model chưa sinh ra content (chỉ reasoning)
- reasoning: thinking process của model
- Kết hợp cả hai thành full output

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
from dataclasses import dataclass
from typing import Any, AsyncIterator, Optional

import tiktoken
from openai import OpenAI, AsyncOpenAI, APIError, RateLimitError, AuthenticationError

from midicoder.pipeline.config import get_config

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
# Max context windows per model family
# ============================================================================

MAX_CONTEXT_WINDOWS = {
    "qwen": 131072,
    "gpt": 128000,
    "claude": 200000,
    "llama": 128000,
    "default": 131072,
}


# ============================================================================
# Data Classes
# ============================================================================

@dataclass(frozen=True)
class LlmConfig:
    """
    Cấu hình cho LLM client.

    Attributes:
        provider: LLM provider (openai-compatible, openai, anthropic, v.v.)
        model: Model name (vd: "qwen3.5-27B", "gpt-4o")
        api_url: API endpoint URL
        api_key: API key cho authentication (optional)
        max_tokens: Max tokens cho response (default: max context window)
        temperature: Temperature cho sampling 0.0-1.0 (default: 0.3)
        top_p: Top-p nucleaus sampling (default: 0.9)
        top_k: Top-k sampling (default: 0 = disabled)
        min_p: Min-p sampling (default: 0.0 = disabled)
        presence_penalty: Presence penalty -1.0~2.0 (default: 0.0)
        repetition_penalty: Repetition penalty 1.0~2.0 (default: 1.0 = disabled)
        timeout: Timeout cho request bằng giây (default: 300)
        retry_attempts: Số lần retry khi fail (default: 3)
    """

    provider: str
    model: str
    api_url: str
    api_key: Optional[str] = None
    max_tokens: int = 131072
    temperature: float = 0.3
    top_p: float = 0.9
    top_k: int = 0
    min_p: float = 0.0
    presence_penalty: float = 0.0
    repetition_penalty: float = 1.0
    timeout: int = 300
    retry_attempts: int = 3


@dataclass
class LlmResponse:
    """
    Response từ LLM.

    Attributes:
        content: Content từ LLM (content + reasoning nếu có)
        usage: Token usage info (prompt_tokens, completion_tokens, total_tokens)
        raw: Raw response object từ OpenAI SDK
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

def _get_max_context_window(model: str) -> int:
    """
    Lấy max context window dựa trên tên model.
    """
    model_lower = model.lower()
    for key, window in MAX_CONTEXT_WINDOWS.items():
        if key in model_lower:
            return window
    return MAX_CONTEXT_WINDOWS["default"]


def load_llm_config() -> LlmConfig:
    """
    Load LLM config từ settings.db qua ConfigManager.

    Returns:
        LlmConfig instance với values từ config file + defaults

    Raises:
        ValueError: Nếu thiếu required fields (model, api_url)
    """
    config = get_config()

    provider = config.get("llm.provider", "openai-compatible")
    model = config.get("llm.model")
    api_url = config.get("llm.api_url")
    api_key = config.get("llm.api_key")

    max_tokens = config.get("llm.max_tokens")
    temperature = config.get("llm.temperature", 0.3)
    top_p = config.get("llm.top_p", 0.9)
    top_k = config.get("llm.top_k", 0)
    min_p = config.get("llm.min_p", 0.0)
    presence_penalty = config.get("llm.presence_penalty", 0.0)
    repetition_penalty = config.get("llm.repetition_penalty", 1.0)
    timeout = config.get("llm.timeout", 300)
    retry_attempts = config.get("llm.retry_attempts", 3)

    # Defaults
    if max_tokens is None:
        max_tokens = _get_max_context_window(model) if model else 131072
    if temperature is None:
        temperature = 0.3
    if top_p is None:
        top_p = 0.9
    if top_k is None:
        top_k = 0
    if min_p is None:
        min_p = 0.0
    if presence_penalty is None:
        presence_penalty = 0.0
    if repetition_penalty is None:
        repetition_penalty = 1.0
    if timeout is None:
        timeout = 300
    if retry_attempts is None:
        retry_attempts = 3

    if not model:
        raise ValueError("Thiếu 'llm.model' trong config file")
    if not api_url:
        raise ValueError("Thiếu 'llm.api_url' trong config file")

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
        top_p=top_p,
        top_k=top_k,
        min_p=min_p,
        presence_penalty=presence_penalty,
        repetition_penalty=repetition_penalty,
        timeout=timeout,
        retry_attempts=retry_attempts,
    )


# ============================================================================
# Helper Functions
# ============================================================================

def _build_messages(system: Optional[str], messages: list[dict[str, str]]) -> list[dict[str, str]]:
    """Build messages list từ system prompt + messages."""
    result = []
    if system:
        result.append({"role": "system", "content": system})
    result.extend(messages)
    return result


def _extract_content(choice) -> tuple[str, str]:
    """
    Extract content và reasoning từ một choice trong response.

    Returns:
        (content, reasoning) — cả hai có thể empty string
    """
    content = ""
    reasoning = ""

    message = choice.get("message", {}) if isinstance(choice, dict) else choice.message

    if isinstance(message, dict):
        content = message.get("content", "") or ""
        reasoning = message.get("reasoning", "") or ""
    else:
        content = message.content or ""
        reasoning = getattr(message, "reasoning", "") or ""

    return content, reasoning


def _merge_content(content: str, reasoning: str) -> str:
    """
    Merge content + reasoning thành full output.

    - Nếu content rỗng nhưng có reasoning → dùng reasoning (reasoning models)
    - Nếu có cả hai → content + reasoning
    - Nếu chỉ có content → dùng content
    """
    if content and reasoning:
        return content
    return content or reasoning


def _extract_usage(usage_obj: Any) -> dict:
    """Extract usage dict từ response usage object."""
    if usage_obj is None:
        return {}

    if hasattr(usage_obj, "prompt_tokens"):
        return {
            "prompt_tokens": getattr(usage_obj, "prompt_tokens", 0),
            "completion_tokens": getattr(usage_obj, "completion_tokens", 0),
            "total_tokens": getattr(usage_obj, "total_tokens", 0),
        }

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
    """Log LLM call metadata (không log content)."""
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


def count_tokens(text: str, model: str = "cl100k_base") -> int:
    """
    Đếm số tokens bằng tiktoken.

    Args:
        text: Text cần đếm
        model: Tên tokenizer (default: cl100k_base cho GPT-4/Qwen compatible)

    Returns:
        Số tokens
    """
    try:
        encoding = tiktoken.get_encoding(model)
    except (KeyError, ValueError):
        encoding = tiktoken.get_encoding("cl100k_base")

    return len(encoding.encode(text))


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

    Args:
        config: LLM config
        system: System prompt (optional)
        messages: User messages list

    Returns:
        LlmResponse với content, usage, raw
    """
    messages_list = _build_messages(system, messages or [])

    start_time = time.time()

    try:
        client = OpenAI(
            base_url=config.api_url,
            api_key=config.api_key or "not-needed",
            timeout=config.timeout,
        )

        response = client.chat.completions.create(
            model=config.model,
            messages=messages_list,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            top_p=config.top_p,
            top_k=config.top_k,
            min_p=config.min_p,
            presence_penalty=config.presence_penalty,
            repetition_penalty=config.repetition_penalty,
        )

        content, reasoning = _extract_content(response.choices[0])
        merged = _merge_content(content, reasoning)
        usage = _extract_usage(response.usage)

        latency_ms = int((time.time() - start_time) * 1000)
        _log_call(config, "success", usage.get("total_tokens", 0), latency_ms)

        return LlmResponse(
            content=merged,
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

    Args:
        config: LLM config
        system: System prompt (optional)
        messages: User messages list

    Returns:
        LlmResponse với content, usage, raw
    """
    messages_list = _build_messages(system, messages or [])

    start_time = time.time()

    try:
        client = AsyncOpenAI(
            base_url=config.api_url,
            api_key=config.api_key or "not-needed",
            timeout=config.timeout,
        )

        response = await client.chat.completions.create(
            model=config.model,
            messages=messages_list,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            top_p=config.top_p,
            top_k=config.top_k,
            min_p=config.min_p,
            presence_penalty=config.presence_penalty,
            repetition_penalty=config.repetition_penalty,
        )

        content, reasoning = _extract_content(response.choices[0])
        merged = _merge_content(content, reasoning)
        usage = _extract_usage(response.usage)

        latency_ms = int((time.time() - start_time) * 1000)
        _log_call(config, "success", usage.get("total_tokens", 0), latency_ms)

        return LlmResponse(
            content=merged,
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

    Args:
        config: LLM config
        system: System prompt (optional)
        messages: User messages list

    Yields:
        LlmStreamChunk với content và usage
    """
    messages_list = _build_messages(system, messages or [])

    start_time = time.time()

    try:
        client = AsyncOpenAI(
            base_url=config.api_url,
            api_key=config.api_key or "not-needed",
            timeout=config.timeout,
        )

        stream = await client.chat.completions.create(
            model=config.model,
            messages=messages_list,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            top_p=config.top_p,
            top_k=config.top_k,
            min_p=config.min_p,
            presence_penalty=config.presence_penalty,
            repetition_penalty=config.repetition_penalty,
            stream=True,
        )

        last_chunk_usage = None

        async for chunk in stream:
            content = ""
            if chunk.choices:
                choice = chunk.choices[0]
                delta = choice.get("delta", {}) if isinstance(choice, dict) else choice.delta
                if isinstance(delta, dict):
                    content = delta.get("content", "") or ""
                elif hasattr(delta, "content") and delta.content:
                    content = delta.content

            if hasattr(chunk, "usage") and chunk.usage:
                last_chunk_usage = _extract_usage(chunk.usage)

            yield LlmStreamChunk(content=content, usage=last_chunk_usage)

        latency_ms = int((time.time() - start_time) * 1000)
        _log_call(config, "success", last_chunk_usage.get("total_tokens", 0) if last_chunk_usage else 0, latency_ms)

    except (APIError, RateLimitError, AuthenticationError):
        latency_ms = int((time.time() - start_time) * 1000)
        _log_call(config, "error", 0, latency_ms)
        raise
