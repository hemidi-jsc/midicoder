"""LLM client utilities for contract generation and repair."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from midicoder.commands.base import MidicoderPaths


@dataclass(frozen=True)
class LlmConfig:
    base_url: str
    model: str
    api_key: str | None
    provider: str | None
    cache_enabled: bool
    cache_type: str | None


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


def _resolve_endpoint(base_url: str) -> str:
    if base_url.endswith("/chat/completions"):
        return base_url
    if base_url.endswith("/v1"):
        return urljoin(base_url + "/", "chat/completions")
    return urljoin(base_url.rstrip("/") + "/", "v1/chat/completions")


def _read_secret_api_key(paths: MidicoderPaths, tier: str) -> str | None:
    secrets_path = paths.secrets / "secrets.json"
    if not secrets_path.exists():
        return None
    secrets = _read_json(secrets_path)
    if isinstance(secrets, dict):
        llm_section = secrets.get("llm", {})
        tier_section = (
            llm_section.get(tier, {}) if isinstance(llm_section, dict) else {}
        )
        if isinstance(tier_section, dict) and tier_section.get("api_key"):
            return str(tier_section["api_key"])
        if secrets.get("api_key"):
            return str(secrets["api_key"])
    return None


def load_llm_config(paths: MidicoderPaths, *, tier: str) -> LlmConfig:
    if not paths.config.exists():
        raise RuntimeError(
            "Missing .midicoder/config.json. Run `midicoder init` first."
        )
    config = _read_json(paths.config)
    llm = config.get("llm", {})
    tier_config = llm.get(tier) if isinstance(llm, dict) else None
    if not isinstance(tier_config, dict):
        raise RuntimeError(f"LLM {tier} config missing. Run `midicoder init` again.")
    base_url = tier_config.get("base_url") or tier_config.get("baseUrl")
    model = tier_config.get("model") or tier_config.get("model_name")
    provider = tier_config.get("provider")
    api_key = tier_config.get("api_key") or _read_secret_api_key(paths, tier)
    if not base_url or not model:
        raise RuntimeError(f"LLM {tier} config must include base_url and model.")
    cache_config = llm.get("cache", {}) if isinstance(llm, dict) else {}
    cache_enabled = (
        bool(cache_config.get("enabled", False))
        if isinstance(cache_config, dict)
        else False
    )
    cache_type = None
    if cache_enabled and isinstance(cache_config, dict):
        cache_type = str(cache_config.get("type", "ephemeral"))
    return LlmConfig(
        base_url=str(base_url),
        model=str(model),
        api_key=str(api_key) if api_key else None,
        provider=str(provider) if provider else None,
        cache_enabled=cache_enabled,
        cache_type=cache_type,
    )


def _should_apply_prompt_cache(config: LlmConfig) -> bool:
    if not config.cache_enabled or not config.cache_type:
        return False
    return config.provider in {"anthropic", "openai"}


def call_llm(
    config: LlmConfig,
    *,
    prompt: str | None = None,
    system: str | None = None,
    context: str | None = None,
    temperature: float = 0.2,
    max_tokens: int | None = None,
) -> LlmResponse:
    messages: list[dict[str, Any]] = []

    if system:
        messages.append({"role": "system", "content": system})

    if context:
        context_message: dict[str, Any] = {"role": "user", "content": context}
        if _should_apply_prompt_cache(config):
            context_message["cache_control"] = {"type": config.cache_type}
        messages.append(context_message)

    if prompt:
        messages.append({"role": "user", "content": prompt})

    if not messages:
        raise ValueError("call_llm requires at least one of system, context, or prompt")

    payload = {
        "model": config.model,
        "messages": messages,
        "temperature": temperature,
    }

    # Add max_tokens if specified, otherwise use a reasonable default for contract generation
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens
    elif any("contract" in str(msg.get("content", "")).lower() for msg in messages):
        # For contract generation, use higher token limit to avoid truncation
        payload["max_tokens"] = 8192
    endpoint = _resolve_endpoint(config.base_url)
    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if config.api_key:
        headers["Authorization"] = f"Bearer {config.api_key}"

    request = Request(endpoint, data=data, headers=headers, method="POST")
    try:
        with urlopen(request, timeout=120) as response:
            raw_bytes = response.read()
    except HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise LlmRequestError(
            f"LLM request failed ({exc.code}): {error_body}",
            raw_response=error_body,
        ) from exc
    except URLError as exc:
        raise LlmRequestError(f"LLM request failed: {exc}") from exc

    raw_text = raw_bytes.decode("utf-8", errors="replace")
    try:
        response_json = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise LlmRequestError(
            f"LLM response was not valid JSON: {raw_text}",
            raw_response=raw_text,
        ) from exc

    try:
        content = response_json["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LlmRequestError(
            f"LLM response missing content: {raw_text}",
            raw_response=raw_text,
        ) from exc

    raw_pretty = json.dumps(response_json, indent=2, ensure_ascii=False)
    return LlmResponse(content=str(content), raw=raw_pretty)
