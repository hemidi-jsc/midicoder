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

import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, AsyncIterator, Optional

import tiktoken
from openai import OpenAI, AsyncOpenAI, APIError, RateLimitError, AuthenticationError

from midicoder.pipeline.config import get_config

logger = __import__("logging").getLogger(__name__)

# Setup file handler — writes to project root so uvicorn users can find it
_DEBUG_LOG_DIR = Path(__file__).parent.parent.parent.parent / "debug_logs"
_DEBUG_LOG_DIR.mkdir(exist_ok=True)
_DEBUG_LOG_FILE = _DEBUG_LOG_DIR / "tool_use_debug.log"
_fh = __import__("logging").FileHandler(str(_DEBUG_LOG_FILE), encoding="utf-8")
_fh.setFormatter(__import__("logging").Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(_fh)
logger.setLevel(__import__("logging").DEBUG)


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


@dataclass
class LlmStreamChunkWithTools:
    """
    Chunk từ streaming LLM response với tool-use support.

    Attributes:
        content: Incremental text content (có thể empty)
        tool_calls: List of tool call deltas [{id, type, function: {name, arguments}}] — None nếu không có
        tool_results: List of tool results [{id, name, result_json}] — None nếu không có
        usage: Token usage (chỉ có trong last chunk)
    """

    content: str = ""
    tool_calls: Optional[list[dict]] = None
    tool_results: Optional[list[dict]] = None
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

        # Build extra_body for provider-specific params (not standard OpenAI)
        extra = {}
        if config.top_k and config.top_k != 0:
            extra["top_k"] = config.top_k
        if config.min_p is not None and config.min_p != 0:
            extra["min_p"] = config.min_p
        if config.repetition_penalty is not None and config.repetition_penalty != 0:
            extra["repetition_penalty"] = config.repetition_penalty

        response = client.chat.completions.create(
            model=config.model,
            messages=messages_list,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            top_p=config.top_p,
            presence_penalty=config.presence_penalty,
            extra_body=extra if extra else None,
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

        # Build extra_body for provider-specific params (not standard OpenAI)
        extra = {}
        if config.top_k and config.top_k != 0:
            extra["top_k"] = config.top_k
        if config.min_p is not None and config.min_p != 0:
            extra["min_p"] = config.min_p
        if config.repetition_penalty is not None and config.repetition_penalty != 0:
            extra["repetition_penalty"] = config.repetition_penalty

        response = await client.chat.completions.create(
            model=config.model,
            messages=messages_list,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            top_p=config.top_p,
            presence_penalty=config.presence_penalty,
            extra_body=extra if extra else None,
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

        # Build extra_body for provider-specific params (not standard OpenAI)
        extra = {}
        if config.top_k and config.top_k != 0:
            extra["top_k"] = config.top_k
        if config.min_p is not None and config.min_p != 0:
            extra["min_p"] = config.min_p
        if config.repetition_penalty is not None and config.repetition_penalty != 0:
            extra["repetition_penalty"] = config.repetition_penalty

        stream = await client.chat.completions.create(
            model=config.model,
            messages=messages_list,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            top_p=config.top_p,
            presence_penalty=config.presence_penalty,
            extra_body=extra if extra else None,
            stream=True,
        )

        last_chunk_usage = None

        async for chunk in stream:
            content = ""
            reasoning = ""
            if chunk.choices:
                choice = chunk.choices[0]
                delta = choice.get("delta", {}) if isinstance(choice, dict) else choice.delta
                if isinstance(delta, dict):
                    content = delta.get("content", "") or ""
                    reasoning = delta.get("reasoning_content", "") or delta.get("reasoning", "") or ""
                elif hasattr(delta, "content") and delta.content:
                    content = delta.content
                    reasoning = getattr(delta, "reasoning_content", "") or getattr(delta, "reasoning", "") or ""

            if hasattr(chunk, "usage") and chunk.usage:
                last_chunk_usage = _extract_usage(chunk.usage)

            # Prepend reasoning with thinking tags so downstream detectors pick it up
            if reasoning:
                content = f"<antThinking>{reasoning}</antThinking>" + content

            yield LlmStreamChunk(content=content, usage=last_chunk_usage)

        latency_ms = int((time.time() - start_time) * 1000)
        _log_call(config, "success", last_chunk_usage.get("total_tokens", 0) if last_chunk_usage else 0, latency_ms)

    except (APIError, RateLimitError, AuthenticationError):
        latency_ms = int((time.time() - start_time) * 1000)
        _log_call(config, "error", 0, latency_ms)
        raise


async def call_llm_with_tools_stream(
    config: LlmConfig,
    *,
    system: Optional[str] = None,
    messages: Optional[list[dict[str, str]]] = None,
    tools: list[dict],
    tool_executor,  # Callable[[str, dict], str] — (tool_name, parsed_args) -> json_result_str
    max_rounds: int = 10,
) -> AsyncIterator[LlmStreamChunkWithTools]:
    """
    Streaming LLM call với tool-use (function calling) support.

    Flow:
    1. Gửi request với tools= đến LLM (streaming)
    2. Parse stream — detect tool_calls từ delta
    3. Khi LLM gửi tool_calls → execute từng tool via tool_executor()
    4. Inject tool results vào messages, call lại LLM
    5. Lặp tối đa max_rounds, hoặc đến khi LLM không call tool nữa

    Args:
        config: LLM config
        system: System prompt
        messages: User messages
        tools: List of tool definitions trong OpenAI format
        tool_executor: Callable(tool_name: str, args: dict) -> str (JSON string result)
        max_rounds: Số vòng gọi LLM tối đa

    Yields:
        LlmStreamChunkWithTools với content, tool_calls, tool_results
    """
    conversation = _build_messages(system, messages or [])
    round_num = 0
    SAFETY_CAP = 9999  # LLM decides when to stop

    # Safety: track repeated same tool with same args — break if 3+ consecutive rounds
    repeated_tool_name = None
    repeated_args = None
    repeat_count = 0

    while round_num < SAFETY_CAP:
        round_num += 1

        # Build extra_body — NO parallel_tool_calls flag (models may ignore it)
        extra = {}
        if config.top_k and config.top_k != 0:
            extra["top_k"] = config.top_k
        if config.min_p is not None and config.min_p != 0:
            extra["min_p"] = config.min_p
        if config.repetition_penalty is not None and config.repetition_penalty != 0:
            extra["repetition_penalty"] = config.repetition_penalty

        client = AsyncOpenAI(
            base_url=config.api_url,
            api_key=config.api_key or "not-needed",
            timeout=config.timeout,
        )

        stream = await client.chat.completions.create(
            model=config.model,
            messages=conversation,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            top_p=config.top_p,
            presence_penalty=config.presence_penalty,
            extra_body=extra if extra else None,
            stream=True,
            tools=tools,
        )

        # Accumulate tool calls from stream
        pending_tool_calls: dict[str, dict] = {}  # call_id -> {id, type, function: {name, arguments}}
        last_chunk_usage = None

        async for chunk in stream:
            if chunk.choices:
                choice = chunk.choices[0]
                delta = choice.get("delta", {}) if isinstance(choice, dict) else choice.delta

                if isinstance(delta, dict):
                    content = delta.get("content", "") or ""
                    # Qwen DashScope sends thinking into reasoning_content when enable_thinking=True
                    reasoning = delta.get("reasoning_content", "") or delta.get("reasoning", "") or ""
                    raw_tool_calls = delta.get("tool_calls", []) or []
                elif hasattr(delta, "content") and delta.content:
                    content = delta.content
                    reasoning = getattr(delta, "reasoning_content", "") or getattr(delta, "reasoning", "") or ""
                    raw_tool_calls = getattr(delta, "tool_calls", []) or []
                else:
                    content = ""
                    reasoning = ""
                    raw_tool_calls = getattr(delta, "tool_calls", []) or []

                # Yield reasoning as content with special marker for thinking detection
                if reasoning:
                    yield LlmStreamChunkWithTools(content=f"<antThinking>{reasoning}</antThinking>")
                # Handle content
                if content:
                    yield LlmStreamChunkWithTools(content=content)

                # Handle tool_calls deltas
                if raw_tool_calls:
                    # DEBUG: log each raw tool_call chunk from stream (first 3 rounds only)
                    if round_num <= 3:
                        for tc in raw_tool_calls:
                            if isinstance(tc, dict):
                                tc_id = tc.get("id", "")
                                tc_func = tc.get("function", {})
                            else:
                                tc_id = getattr(tc, "id", "")
                                tc_func = getattr(tc, "function", {})
                            logger.info(f"[TOOL_USE ROUND_{round_num}] CHUNK tool_call: id={tc_id!r}, function={tc_func!r}")

                    for tc in raw_tool_calls:
                        if isinstance(tc, dict):
                            tc_id = tc.get("id", "")
                        else:
                            tc_id = getattr(tc, "id", "")

                        if tc_id:
                            if tc_id not in pending_tool_calls:
                                pending_tool_calls[tc_id] = {
                                    "id": tc_id,
                                    "type": "function",
                                    "function": {"name": "", "arguments": ""}
                                }
                            last_tc_id = tc_id  # Track last known id for merging id=None chunks
                        elif pending_tool_calls:
                            # DashScope Qwen sends id=None in subsequent chunks — merge into last known tool call
                            last_tc_id = list(pending_tool_calls.keys())[-1]
                        else:
                            last_tc_id = None

                        if last_tc_id:
                            func_info = tc.get("function", {}) if isinstance(tc, dict) else getattr(tc, "function", {})
                            if isinstance(func_info, dict):
                                name_delta = func_info.get("name", "") or ""
                                args_delta = func_info.get("arguments", "") or ""
                            else:
                                name_delta = getattr(func_info, "name", "") or ""
                                args_delta = getattr(func_info, "arguments", "") or ""

                            if name_delta:
                                pending_tool_calls[last_tc_id]["function"]["name"] = name_delta
                            if args_delta:
                                # Qwen DashScope may send FULL arguments in each chunk (not delta).
                                # Detect: if args_delta is valid non-empty JSON, replace instead of append.
                                # CRITICAL: {} (empty object) is valid JSON but NOT complete — keep accumulating.
                                try:
                                    parsed = json.loads(args_delta)
                                    if isinstance(parsed, dict) and len(parsed) > 0:
                                        # Valid JSON with keys — complete argument, replace
                                        pending_tool_calls[last_tc_id]["function"]["arguments"] = args_delta
                                    else:
                                        # Empty {} or non-dict — keep accumulating
                                        pending_tool_calls[last_tc_id]["function"]["arguments"] += args_delta
                                except (ValueError, TypeError):
                                    # Not valid JSON yet — accumulate as delta
                                    pending_tool_calls[last_tc_id]["function"]["arguments"] += args_delta

                # Handle usage
                if hasattr(chunk, "usage") and chunk.usage:
                    last_chunk_usage = _extract_usage(chunk.usage)

        # If we have tool calls, dedup, execute ALL unique ones, inject results.
        # LLM decides when to stop by not calling any tools in the next round.
        if pending_tool_calls:
            # DEBUG: log raw accumulated tool calls BEFORE dedup — to see exactly what LLM sent
            logger.info(f"[TOOL_USE ROUND_{round_num}] RAW tool_calls from LLM ({len(pending_tool_calls)} total):")
            for tc_id, tc_info in pending_tool_calls.items():
                logger.info(f"  {tc_id}: name={tc_info['function']['name']!r}, arguments={tc_info['function']['arguments']!r}")

            # Dedup: if same tool+args called multiple times, only execute once
            seen: dict[str, str] = {}  # "name|args" -> tc_id (keep first)
            unique_calls: list[tuple[str, dict]] = []
            for tc_id, tc_info in pending_tool_calls.items():
                key = f"{tc_info['function']['name']}|{tc_info['function']['arguments']}"
                if key not in seen:
                    seen[key] = tc_id
                    unique_calls.append((tc_id, tc_info))

            # Also dedup by tool name only — if same tool called with different args, keep first
            seen_names: set[str] = set()
            final_calls: list[tuple[str, dict]] = []
            for tc_id, tc_info in unique_calls:
                tool_name = tc_info["function"]["name"]
                if tool_name not in seen_names:
                    seen_names.add(tool_name)
                    final_calls.append((tc_id, tc_info))

            tool_call_messages = []
            for tc_id, tc_info in final_calls:
                tool_name = tc_info["function"]["name"]
                args_str = tc_info["function"]["arguments"]

                # Yield tool_call event to frontend
                yield LlmStreamChunkWithTools(tool_calls=[tc_info])

                # Parse args
                try:
                    parsed_args = json.loads(args_str) if args_str else {}
                except Exception:
                    parsed_args = {}

                # Execute the tool IN-PROCESS
                try:
                    result_str = await tool_executor(tool_name, parsed_args)
                except Exception as e:
                    result_str = f"Error executing {tool_name}: {str(e)}"

                # Yield tool_result to frontend
                yield LlmStreamChunkWithTools(
                    tool_results=[{
                        "id": tc_id,
                        "name": tool_name,
                        "result": result_str,
                    }]
                )

                tool_call_messages.append({
                    "role": "tool",
                    "tool_call_id": tc_id,
                    "content": str(result_str),
                })

            # Inject ALL assistant tool_calls + tool results into conversation
            conversation.append({
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": tc_id,
                        "type": "function",
                        "function": {
                            "name": info["function"]["name"],
                            "arguments": info["function"]["arguments"],
                        }
                    }
                    for tc_id, info in final_calls
                ],
            })
            conversation.extend(tool_call_messages)

            # Check if ANY tool returned an error — inject user reminder to teach LLM
            for tr_msg in tool_call_messages:
                content = tr_msg.get("content", "")
                if '"error"' in content:
                    try:
                        error_obj = json.loads(content)
                        error_text = error_obj.get("error", "")
                        tool_name = error_text.split("'")[1] if "'" in error_text else "unknown"
                        # Extract missing params from error
                        if "missing required parameters" in error_text:
                            # Find the example in error message
                            if "Example:" in error_text:
                                example = error_text.split("Example:")[1].strip()
                            else:
                                example = ""
                            conversation.append({
                                "role": "user",
                                "content": (
                                    f"Your call to {tool_name} failed because required parameters were missing. "
                                    f"Call it again with the correct arguments. Format: {example}"
                                ),
                            })
                    except Exception:
                        pass

            # DEBUG: log conversation state after each tool round
            logger.info(f"[TOOL_USE ROUND_{round_num}] Injected {len(final_calls)} tool call(s) + {len(tool_call_messages)} tool result(s)")
            logger.info(f"[TOOL_USE ROUND_{round_num}] Conversation now has {len(conversation)} messages:")
            for i, msg in enumerate(conversation):
                role = msg.get("role", "unknown")
                if role == "assistant" and msg.get("tool_calls"):
                    for tc in msg["tool_calls"]:
                        logger.info(f"  [{i}] {role}: tool_call {tc['function']['name']}({tc['function']['arguments']})")
                elif role == "tool":
                    content_preview = str(msg.get("content", ""))[:200]
                    logger.info(f"  [{i}] {role}: {content_preview}")
                elif role == "user":
                    content_preview = str(msg.get("content", ""))[:200]
                    logger.info(f"  [{i}] {role}: {content_preview}")
                elif role == "system":
                    logger.info(f"  [{i}] {role}: (system prompt, {len(msg.get('content', ''))} chars)")

            continue  # Loop — LLM processes results and decides next step

        # No more tool calls — LLM is done
        break
