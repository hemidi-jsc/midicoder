"""LLM client utilities for contract generation and repair."""

from __future__ import annotations

import asyncio
import json
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from midicoder.commands.base import MidicoderPaths
from midicoder.llm.adapters import ProviderAdapter, get_adapter

MIN_LLM_TIMEOUT_SECONDS = 300.0


@dataclass(frozen=True)
class LlmConfig:
    base_url: str | None
    model: str
    api_key: str | None
    provider: str | None
    cache_enabled: bool
    cache_type: str | None
    aws_region_name: str | None = None
    azure_openai_endpoint: str | None = None
    azure_openai_api_version: str | None = None
    azure_openai_deployment: str | None = None
    vertex_project: str | None = None
    vertex_location: str | None = None
    timeout_seconds: float = MIN_LLM_TIMEOUT_SECONDS


@dataclass(frozen=True)
class LlmResponse:
    content: str
    raw: str


class LlmRequestError(RuntimeError):
    def __init__(self, message: str, *, raw_response: str | None = None) -> None:
        super().__init__(message)
        self.raw_response = raw_response


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_secret_api_key(paths: MidicoderPaths, tier: str) -> str | None:
    secrets_path = paths.secrets / "secrets.json"
    if not secrets_path.exists():
        return None

    secrets = _read_json(secrets_path)
    if isinstance(secrets, dict):
        llm_section = secrets.get("llm", {})
        tier_section = llm_section.get(tier, {}) if isinstance(llm_section, dict) else {}
        if isinstance(tier_section, dict) and tier_section.get("api_key"):
            return str(tier_section["api_key"])
        if secrets.get("api_key"):
            return str(secrets["api_key"])
    return None


def _normalize_cache_config(config: dict[str, Any]) -> tuple[bool, str | None]:
    cache_config: dict[str, Any] = {}

    llm_section = config.get("llm")
    if isinstance(llm_section, dict):
        llm_cache = llm_section.get("cache")
        if isinstance(llm_cache, dict):
            cache_config = llm_cache

    if not cache_config:
        top_level_cache = config.get("cache")
        if isinstance(top_level_cache, dict):
            cache_config = top_level_cache

    enabled_value = cache_config.get("enabled")
    if enabled_value is None:
        enabled_value = cache_config.get("enable", False)

    cache_enabled = bool(enabled_value)
    cache_type = str(cache_config.get("type", "ephemeral")) if cache_enabled else None
    return cache_enabled, cache_type


def _normalize_timeout_seconds(value: Any) -> float:
    if value is None:
        return MIN_LLM_TIMEOUT_SECONDS

    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return MIN_LLM_TIMEOUT_SECONDS

    if parsed <= 0:
        return MIN_LLM_TIMEOUT_SECONDS
    return max(parsed, MIN_LLM_TIMEOUT_SECONDS)


def load_llm_config(paths: MidicoderPaths, *, tier: str) -> LlmConfig:
    if not paths.config.exists():
        raise RuntimeError("Missing .midicoder/config.json. Run `midicoder init` first.")

    config = _read_json(paths.config)
    llm = config.get("llm", {})
    tier_config = llm.get(tier) if isinstance(llm, dict) else None
    if not isinstance(tier_config, dict):
        raise RuntimeError(f"LLM {tier} config missing. Run `midicoder init` again.")

    model = tier_config.get("model") or tier_config.get("model_name")
    provider = tier_config.get("provider")
    api_key = tier_config.get("api_key") or _read_secret_api_key(paths, tier)
    base_url = tier_config.get("base_url") or tier_config.get("baseUrl")
    timeout_seconds = _normalize_timeout_seconds(
        tier_config.get("timeout_seconds") or tier_config.get("timeout")
    )

    if not model:
        raise RuntimeError(f"LLM {tier} config must include model.")

    cache_enabled, cache_type = _normalize_cache_config(config)

    return LlmConfig(
        base_url=str(base_url) if base_url else None,
        model=str(model),
        api_key=str(api_key) if api_key else None,
        provider=str(provider) if provider else None,
        cache_enabled=cache_enabled,
        cache_type=cache_type,
        aws_region_name=(
            str(
                tier_config.get("aws_region_name")
                or tier_config.get("aws_region")
            )
            if (
                tier_config.get("aws_region_name")
                or tier_config.get("aws_region")
            )
            else None
        ),
        azure_openai_endpoint=(
            str(tier_config["azure_openai_endpoint"])
            if tier_config.get("azure_openai_endpoint")
            else None
        ),
        azure_openai_api_version=(
            str(tier_config["azure_openai_api_version"])
            if tier_config.get("azure_openai_api_version")
            else None
        ),
        azure_openai_deployment=(
            str(tier_config["azure_openai_deployment"])
            if tier_config.get("azure_openai_deployment")
            else None
        ),
        vertex_project=(
            str(tier_config["vertex_project"])
            if tier_config.get("vertex_project")
            else None
        ),
        vertex_location=(
            str(tier_config["vertex_location"])
            if tier_config.get("vertex_location")
            else None
        ),
        timeout_seconds=timeout_seconds,
    )


def _build_messages(
    config: LlmConfig,
    *,
    prompt: str | None,
    system: str | None,
    context: str | None,
    adapter: ProviderAdapter,
) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []

    if system:
        messages.append({"role": "system", "content": system})

    if context:
        messages.append(adapter.build_context_message(config, context))

    if prompt:
        messages.append({"role": "user", "content": prompt})

    if not messages:
        raise ValueError("call_llm requires at least one of system, context, or prompt")

    return messages


def _build_completion_params(
    config: LlmConfig,
    adapter: ProviderAdapter,
    messages: list[dict[str, Any]],
    *,
    temperature: float,
    max_tokens: int | None,
) -> dict[str, Any]:
    params = adapter.build_request(
        config,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    # Enforce timeout after adapter overrides so provider-specific params
    # cannot accidentally reset it.
    params["timeout"] = config.timeout_seconds
    return params


def _extract_extra_headers(params: dict[str, Any]) -> dict[str, str]:
    extra_headers = params.get("extra_headers")
    if isinstance(extra_headers, dict):
        return {str(k): str(v) for k, v in extra_headers.items()}
    return {}


def _with_litellm_timeout_headers(params: dict[str, Any]) -> dict[str, Any]:
    request_params = dict(params)
    normalized_headers = _extract_extra_headers(request_params)
    # Keep LiteLLM timeout header fixed to 300 seconds as operational default.
    normalized_headers["x-litellm-timeout"] = str(int(MIN_LLM_TIMEOUT_SECONDS))
    request_params["extra_headers"] = normalized_headers
    return request_params


def _extract_raw_error(exc: Exception) -> str | None:
    response = getattr(exc, "response", None)
    if response is not None:
        try:
            if hasattr(response, "text"):
                text = response.text
                if isinstance(text, str) and text:
                    return text
            if hasattr(response, "json"):
                payload = response.json()
                return json.dumps(payload, indent=2, ensure_ascii=False)
        except Exception:
            pass

    body = getattr(exc, "body", None)
    if body:
        return str(body)

    details = getattr(exc, "message", None)
    if details:
        return str(details)

    return None


def _map_litellm_error(exc: Exception) -> LlmRequestError:
    exc_name = exc.__class__.__name__.lower()
    status_code = getattr(exc, "status_code", None)
    raw_error = _extract_raw_error(exc)

    if "auth" in exc_name or "permission" in exc_name or "unauthorized" in exc_name:
        category = "auth"
    elif "timeout" in exc_name or "connection" in exc_name or "network" in exc_name:
        category = "network"
    elif (
        "ratelimit" in exc_name
        or "badrequest" in exc_name
        or "notfound" in exc_name
        or "contextwindow" in exc_name
        or "contentpolicy" in exc_name
        or "serviceunavailable" in exc_name
    ):
        category = "provider"
    else:
        category = "request"

    status_suffix = f" ({status_code})" if status_code is not None else ""
    detail = raw_error or str(exc)
    return LlmRequestError(
        f"LLM {category} error{status_suffix}: {detail}",
        raw_response=raw_error,
    )


def _run_awaitable_sync(awaitable: Any) -> Any:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(awaitable)

    result: dict[str, Any] = {}
    error: dict[str, BaseException] = {}

    def _runner() -> None:
        try:
            result["value"] = asyncio.run(awaitable)
        except BaseException as exc:  # pragma: no cover - defensive fallback
            error["exc"] = exc

    thread = threading.Thread(target=_runner, daemon=True)
    thread.start()
    thread.join()

    if "exc" in error:
        raise error["exc"]
    return result.get("value")


def call_llm(
    config: LlmConfig,
    *,
    prompt: str | None = None,
    system: str | None = None,
    context: str | None = None,
    temperature: float = 0.2,
    max_tokens: int | None = None,
) -> LlmResponse:
    try:
        import litellm
    except Exception as exc:  # pragma: no cover - import environment dependent
        raise LlmRequestError(
            "LiteLLM is not available. Install dependency 'litellm' to run LLM commands."
        ) from exc

    adapter = get_adapter(config)
    messages = _build_messages(
        config,
        prompt=prompt,
        system=system,
        context=context,
        adapter=adapter,
    )
    params = _build_completion_params(
        config,
        adapter,
        messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    request_params = _with_litellm_timeout_headers(params)

    try:
        response = _run_awaitable_sync(litellm.acompletion(**request_params))
    except Exception as exc:  # pragma: no cover - network/provider dependent
        raise _map_litellm_error(exc) from exc

    raw_dict: dict[str, Any]
    if hasattr(response, "model_dump"):
        raw_dict = response.model_dump()
    elif isinstance(response, dict):
        raw_dict = response
    else:
        raw_dict = {"response": str(response)}

    try:
        choices = raw_dict.get("choices", [])
        first_choice = choices[0] if choices else {}
        message = first_choice.get("message", {}) if isinstance(first_choice, dict) else {}
        content = message.get("content")

        if isinstance(content, list):
            text_parts = [
                str(part.get("text", ""))
                for part in content
                if isinstance(part, dict) and part.get("text") is not None
            ]
            content = "".join(text_parts).strip()

        if content is None:
            raise KeyError("content")
    except (KeyError, IndexError, TypeError) as exc:
        raw_text = json.dumps(raw_dict, ensure_ascii=False)
        raise LlmRequestError(
            f"LLM response missing content: {raw_text}",
            raw_response=raw_text,
        ) from exc

    raw_pretty = json.dumps(raw_dict, indent=2, ensure_ascii=False)
    return LlmResponse(content=str(content), raw=raw_pretty)
