"""
LLM Client cho Midicoder Pipeline.

Cung cấp wrapper abstraction cho nhiều LLM providers:
- openai-compatible: Custom URL với OpenAI API format (default)
- openai: OpenAI API
- anthropic: Anthropic API
- aws-bedrock: AWS Bedrock
- azure: Azure AI Foundry
- vertex: Google Vertex AI

E20: CLI Commands
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from midicoder.errors import ErrorCode, MidicoderError, MidicoderErrorManager as EM
from midicoder.pipeline.config import get_config


class LlmProvider(Enum):
    """Các LLM providers được hỗ trợ."""
    
    OPENAI_COMPATIBLE = "openai-compatible"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AWS_BEDROCK = "aws-bedrock"
    AZURE = "azure"
    VERTEX = "vertex"


@dataclass(frozen=True)
class LlmConfig:
    """
    Cấu hình cho LLM client.
    
    Attributes:
        provider: LLM provider để sử dụng
        model: Model name (vd: "gpt-4o", "claude-3-sonnet")
        api_url: API endpoint URL
        api_key: API key cho authentication (optional)
        max_tokens: Max tokens cho response
        temperature: Temperature cho sampling (0.0-1.0)
        timeout_seconds: Timeout cho request
        retry_attempts: Số lần retry khi fail
    """
    
    provider: LlmProvider
    model: str
    api_url: str
    api_key: Optional[str] = None
    max_tokens: int = 8192
    temperature: float = 0.3
    timeout_seconds: int = 300
    retry_attempts: int = 3


@dataclass
class LlmResponse:
    """
    Response từ LLM.
    
    Attributes:
        content: Content từ LLM response
        raw: Raw JSON response
        usage: Token usage info (nếu có)
    """
    
    content: str
    raw: str
    usage: Optional[dict] = None


# ============================================================================
# LLM Error Classes
# ============================================================================

class LlmError(MidicoderError):
    """Base class cho tất cả LLM errors."""
    
    pass


class LlmRequestError(LlmError):
    """
    Lỗi khi request đến LLM fail.
    
    Attributes:
        status_code: HTTP status code (nếu có)
        raw_response: Raw response từ server
    """
    
    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        raw_response: Optional[str] = None,
    ) -> None:
        context = _filter_null_values({
            "status_code": status_code,
            "raw_response": raw_response,
        })
        self._raw_message = message  # Store raw message for custom str
        super().__init__(
            code=ErrorCode.LLM_REQUEST_FAILED,
            message=message,  # Store raw message
            context=context,
        )
        self.status_code = status_code
        self.raw_response = raw_response
    
    def __str__(self) -> str:
        parts = [f"[LLM-001] LLM request thất bại: {self._raw_message}"]
        if self.status_code:
            parts.append(f"(status_code={self.status_code})")
        return " ".join(parts)


class LlmAuthError(LlmError):
    """Lỗi authentication (401)."""
    
    def __init__(self, message: str = "Authentication failed") -> None:
        super().__init__(
            code=ErrorCode.LLM_AUTH_FAILED,
            message=f"LLM authentication thất bại: {message}",
        )


class LlmRateLimitError(LlmError):
    """
    Lỗi rate limit (429).
    
    Attributes:
        retry_after: Số giây cần chờ trước khi retry
    """
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        *,
        retry_after: Optional[int] = None,
    ) -> None:
        super().__init__(
            code=ErrorCode.LLM_RATE_LIMIT,
            message=f"LLM rate limit: {message}",
            context={"retry_after": retry_after} if retry_after else {},
        )
        self.retry_after = retry_after


class LlmTimeoutError(LlmError):
    """
    Lỗi timeout khi call LLM.
    
    Attributes:
        timeout: Timeout seconds đã thiết lập
    """
    
    def __init__(
        self,
        message: str = "Request timeout",
        *,
        timeout: int = 300,
    ) -> None:
        super().__init__(
            code=ErrorCode.LLM_TIMEOUT,
            message=f"LLM request timeout: {message}",
            context={"timeout": timeout},
        )
        self.timeout = timeout


def _filter_null_values(d: dict) -> dict:
    """
    Lọc các key với None values từ dict.
    
    Args:
        d: Dict source
        
    Returns:
        Dict không chứa None values
    """
    return {k: v for k, v in d.items() if v is not None}


# ============================================================================
# Config Loading
# ============================================================================

def load_llm_config(tier: str = "analyze") -> LlmConfig:
    """
    Load LLM config từ global config.
    
    Load config theo thứ tự ưu tiên:
    1. Tier-specific overrides (llm.<tier>.*)
    2. Base LLM config (llm.*)
    3. Environment variables
    4. Defaults
    
    Args:
        tier: Tier name ("analyze", "repair", "code")
        
    Returns:
        LlmConfig instance
        
    Raises:
        MidicoderError: Nếu config không hợp lệ
    """
    config = get_config()
    
    # Load base LLM config
    provider_str = config.get("llm.provider", "openai-compatible")
    model = config.get("llm.model")
    api_url = config.get("llm.api_url")
    api_key = config.get("llm.api_key")
    max_tokens = config.get("llm.max_tokens", 8192)
    temperature = config.get("llm.temperature", 0.3)
    timeout_seconds = config.get("llm.timeout_seconds", 300)
    retry_attempts = config.get("llm.retry_attempts", 3)
    
    # Validate required fields
    if not model or not api_url:
        raise EM.raise_error(
            ErrorCode.LLM_CONFIG_INVALID,
            message="Thiếu model hoặc api_url trong LLM config",
        )
    
    # Apply tier-specific overrides
    tier_max_tokens = config.get(f"llm.{tier}.max_tokens")
    tier_temperature = config.get(f"llm.{tier}.temperature")
    
    if tier_max_tokens is not None:
        max_tokens = tier_max_tokens
    if tier_temperature is not None:
        temperature = tier_temperature
    
    # Try to get API key from environment if not in config
    if not api_key:
        api_key = _get_api_key_from_env(provider_str)
    
    # Convert provider string to enum
    try:
        provider = LlmProvider(provider_str)
    except ValueError:
        raise EM.raise_error(
            ErrorCode.LLM_CONFIG_INVALID,
            message=f"Provider không hợp lệ: {provider_str}",
        )
    
    return LlmConfig(
        provider=provider,
        model=model,
        api_url=api_url,
        api_key=api_key,
        max_tokens=max_tokens,
        temperature=temperature,
        timeout_seconds=timeout_seconds,
        retry_attempts=retry_attempts,
    )


def _get_api_key_from_env(provider: str) -> Optional[str]:
    """
    Lấy API key từ environment variable.
    
    Args:
        provider: Provider name
        
    Returns:
        API key hoặc None
    """
    env_key_mapping = {
        "openai": "OPENAI_API_KEY",
        "openai-compatible": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "aws-bedrock": "AWS_bedrock_API_KEY",
        "azure": "AZURE_API_KEY",
        "vertex": "VERTEX_API_KEY",
    }
    
    env_var = env_key_mapping.get(provider)
    if env_var:
        return os.environ.get(env_var)
    
    return None


# ============================================================================
# LLM Calling
# ============================================================================

def call_llm(
    config: LlmConfig,
    *,
    system: Optional[str] = None,
    context: Optional[str] = None,
    prompt: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> LlmResponse:
    """
    Call LLM với retry logic và error handling.
    
    Xây dựng messages theo OpenAI format và gửi request đến LLM.
    Hỗ trợ retry với exponential backoff.
    
    Args:
        config: LLM config
        system: System prompt (optional)
        context: Context message (optional)
        prompt: User prompt (optional)
        temperature: Override temperature (optional)
        max_tokens: Override max tokens (optional)
        
    Returns:
        LlmResponse với content và raw response
        
    Raises:
        ValueError: Nếu không có system, context, hoặc prompt
        LlmAuthError: Nếu authentication fail (401)
        LlmRateLimitError: Nếu rate limited (429)
        LlmTimeoutError: Nếu request timeout
        LlmRequestError: Nếu request fail khác
    """
    if not any([system, context, prompt]):
        raise ValueError("call_llm requires at least one of system, context, or prompt")
    
    # Build messages
    messages: list[dict[str, Any]] = []
    
    if system:
        messages.append({"role": "system", "content": system})
    
    if context:
        messages.append({"role": "user", "content": context})
    
    if prompt:
        messages.append({"role": "user", "content": prompt})
    
    # Build payload
    payload = _build_payload(
        config=config,
        messages=messages,
        temperature=temperature or config.temperature,
        max_tokens=max_tokens or config.max_tokens,
    )
    
    # Retry loop
    last_error: Optional[Exception] = None
    
    for attempt in range(config.retry_attempts):
        try:
            return _send_request(config, payload)
        except (LlmAuthError, LlmRateLimitError, LlmTimeoutError):
            # Re-raise immediately for these errors
            raise
        except LlmRequestError as e:
            last_error = e
            if attempt < config.retry_attempts - 1:
                # Exponential backoff
                wait_time = (2 ** attempt) * 1
                time.sleep(wait_time)
            else:
                raise
        except Exception as e:
            last_error = e
            if attempt < config.retry_attempts - 1:
                wait_time = (2 ** attempt) * 1
                time.sleep(wait_time)
            else:
                raise LlmRequestError(f"Unknown error: {e}") from e
    
    raise LlmRequestError("Max retry attempts exceeded") from last_error


def _build_payload(
    config: LlmConfig,
    messages: list[dict[str, Any]],
    temperature: float,
    max_tokens: int,
) -> dict[str, Any]:
    """
    Build request payload theo provider.
    
    Args:
        config: LLM config
        messages: Messages list
        temperature: Temperature
        max_tokens: Max tokens
        
    Returns:
        Payload dict
    """
    base_payload = {
        "model": config.model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    
    # Provider-specific adjustments
    if config.provider == LlmProvider.ANTHROPIC:
        return _build_anthropic_payload(base_payload, messages)
    elif config.provider == LlmProvider.AWS_BEDROCK:
        return _build_bedrock_payload(base_payload)
    elif config.provider == LlmProvider.AZURE:
        return _build_azure_payload(base_payload)
    elif config.provider == LlmProvider.VERTEX:
        return _build_vertex_payload(base_payload)
    
    # Default: OpenAI-compatible format
    return base_payload


def _build_anthropic_payload(
    base_payload: dict,
    messages: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build Anthropic-specific payload."""
    # Anthropic uses different field names
    return {
        "model": base_payload["model"],
        "messages": messages,
        "temperature": base_payload["temperature"],
        "max_tokens": base_payload["max_tokens"],
        "system": next(
            (m["content"] for m in messages if m.get("role") == "system"),
            None,
        ),
    }


def _build_bedrock_payload(base_payload: dict) -> dict[str, Any]:
    """Build AWS Bedrock-specific payload."""
    # Bedrock wraps payload in additional structure
    return {
        "modelId": base_payload["model"],
        "inputs": base_payload["messages"],
        "parameters": {
            "temperature": base_payload["temperature"],
            "max_tokens": base_payload["max_tokens"],
        },
    }


def _build_azure_payload(base_payload: dict) -> dict[str, Any]:
    """Build Azure-specific payload."""
    # Azure uses similar format to OpenAI
    return base_payload


def _build_vertex_payload(base_payload: dict) -> dict[str, Any]:
    """Build Google Vertex-specific payload."""
    # Vertex uses instances and parameters
    return {
        "instances": [{"content": msg["content"] for msg in base_payload["messages"]}],
        "parameters": {
            "temperature": base_payload["temperature"],
            "maxOutputTokens": base_payload["max_tokens"],
        },
    }


def _send_request(config: LlmConfig, payload: dict[str, Any]) -> LlmResponse:
    """
    Gửi request đến LLM.
    
    Args:
        config: LLM config
        payload: Request payload
        
    Returns:
        LlmResponse
        
    Raises:
        LlmAuthError: Nếu 401
        LlmRateLimitError: Nếu 429
        LlmTimeoutError: Nếu timeout
        LlmRequestError: Nếu fail khác
    """
    # Build URL
    url = _build_url(config)
    
    # Build headers
    headers = _build_headers(config)
    
    # Build request
    data = json.dumps(payload).encode("utf-8")
    request = Request(url, data=data, headers=headers, method="POST")
    
    try:
        with urlopen(request, timeout=config.timeout_seconds) as response:
            raw_bytes = response.read()
    except HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        
        if exc.code == 401:
            raise LlmAuthError(f"Invalid API key: {error_body}")
        elif exc.code == 429:
            retry_after = exc.headers.get("Retry-After")
            raise LlmRateLimitError(
                f"Rate limit exceeded: {error_body}",
                retry_after=int(retry_after) if retry_after else None,
            )
        else:
            raise LlmRequestError(
                f"HTTP {exc.code}: {error_body}",
                status_code=exc.code,
                raw_response=error_body,
            ) from exc
    except URLError as exc:
        if "timed out" in str(exc).lower():
            raise LlmTimeoutError(
                "Connection timed out",
                timeout=config.timeout_seconds,
            ) from exc
        raise LlmRequestError(f"Request failed: {exc}") from exc
    except TimeoutError:
        raise LlmTimeoutError(
            "Request timeout",
            timeout=config.timeout_seconds,
        )
    
    # Parse response
    raw_text = raw_bytes.decode("utf-8", errors="replace")
    
    try:
        response_json = json.loads(raw_text)
    except json.JSONDecodeError:
        raise LlmRequestError(
            f"Response was not valid JSON: {raw_text}",
            raw_response=raw_text,
        )
    
    # Extract content based on provider
    content = _extract_content(response_json, config.provider)
    
    # Get usage info if available
    usage = response_json.get("usage")
    
    raw_pretty = json.dumps(response_json, indent=2, ensure_ascii=False)
    
    return LlmResponse(content=content, raw=raw_pretty, usage=usage)


def _build_url(config: LlmConfig) -> str:
    """Build API URL từ config."""
    url = config.api_url
    
    # Ensure proper endpoint
    if not url.endswith("chat/completions"):
        if url.endswith("/v1"):
            url = f"{url}/chat/completions"
        else:
            url = f"{url.rstrip('/')}/v1/chat/completions"
    
    return url


def _build_headers(config: LlmConfig) -> dict[str, str]:
    """Build request headers."""
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    
    if config.api_key:
        headers["Authorization"] = f"Bearer {config.api_key}"
    
    # Provider-specific headers
    if config.provider == LlmProvider.ANTHROPIC:
        headers["x-api-key"] = config.api_key or ""
        headers["anthropic-version"] = "2023-06-01"
    
    return headers


def _extract_content(response: dict, provider: LlmProvider) -> str:
    """Extract content từ response theo provider."""
    if provider == LlmProvider.ANTHROPIC:
        # Anthropic format
        content = response.get("content", [])
        if isinstance(content, list) and len(content) > 0:
            return content[0].get("text", "")
        return response.get("content", "")
    elif provider == LlmProvider.AWS_BEDROCK:
        # Bedrock format
        outputs = response.get("outputs", [])
        if outputs:
            return outputs[0].get("text", "")
        return response.get("text", "")
    else:
        # OpenAI-compatible format
        choices = response.get("choices", [])
        if choices:
            message = choices[0].get("message", {})
            return message.get("content", "")
        return ""