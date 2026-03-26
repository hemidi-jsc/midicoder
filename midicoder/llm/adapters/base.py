from __future__ import annotations

import ipaddress
from typing import Any, Protocol, TYPE_CHECKING
from urllib.parse import urlsplit, urlunsplit

if TYPE_CHECKING:
    from midicoder.llm.client import LlmConfig


class ProviderAdapter(Protocol):
    provider: str

    def model_identifier(self, config: LlmConfig) -> str:
        ...

    def completion_params(self, config: LlmConfig) -> dict[str, Any]:
        ...

    def build_context_message(self, config: LlmConfig, context: str) -> dict[str, Any]:
        ...

    def build_request(
        self,
        config: LlmConfig,
        *,
        messages: list[dict[str, Any]],
        temperature: float,
        max_tokens: int | None,
    ) -> dict[str, Any]:
        ...


class BaseAdapter:
    provider = "default"

    def _should_upgrade_to_https(self, scheme: str, hostname: str | None) -> bool:
        if scheme.lower() != "http":
            return False
        if not hostname:
            return False

        host = hostname.strip().lower()
        if host in {"localhost", "::1"}:
            return False

        try:
            ip = ipaddress.ip_address(host)
            if ip.is_loopback or ip.is_private:
                return False
        except ValueError:
            # Hostname is not an IP; treat it as public domain and prefer HTTPS.
            return True

        return False

    def _normalized_model(self, model: str) -> str:
        return model.strip()

    def _with_prefix(self, model: str, prefix: str) -> str:
        normalized_model = self._normalized_model(model)
        if not normalized_model:
            return normalized_model
        if "/" in normalized_model:
            return normalized_model
        return f"{prefix}/{normalized_model}"

    def _completion_api_base_params(self, config: LlmConfig) -> dict[str, Any]:
        if not config.base_url:
            return {}
        return {"api_base": config.base_url}

    def _normalize_openai_api_base(self, base_url: str) -> str:
        """
        Normalize OpenAI-compatible api_base to preserve backward compatibility.

        Accepted legacy forms:
        - http://host                       -> http://host/v1
        - http://host/chat/completions      -> http://host/v1
        - http://host/v1/chat/completions   -> http://host/v1
        """
        normalized = base_url.strip().rstrip("/")
        if not normalized:
            return normalized

        lower = normalized.lower()
        if lower.endswith("/v1/chat/completions"):
            return normalized[: -len("/chat/completions")]
        if lower.endswith("/chat/completions"):
            return normalized[: -len("/chat/completions")] + "/v1"
        if lower.endswith("/v1"):
            return normalized

        parts = urlsplit(normalized)
        scheme = parts.scheme
        if self._should_upgrade_to_https(scheme, parts.hostname):
            scheme = "https"

        path = parts.path or ""
        if not path:
            new_path = "/v1"
        elif path.endswith("/"):
            new_path = path.rstrip("/") + "/v1"
        else:
            new_path = path + "/v1"

        return urlunsplit((scheme, parts.netloc, new_path, parts.query, parts.fragment))

    def model_identifier(self, config: LlmConfig) -> str:
        return config.model

    def completion_params(self, config: LlmConfig) -> dict[str, Any]:
        return {}

    def build_context_message(self, config: LlmConfig, context: str) -> dict[str, Any]:
        return {"role": "user", "content": context}

    def build_request(
        self,
        config: LlmConfig,
        *,
        messages: list[dict[str, Any]],
        temperature: float,
        max_tokens: int | None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "model": self.model_identifier(config),
            "messages": messages,
            "temperature": temperature,
        }

        if max_tokens is not None:
            params["max_tokens"] = max_tokens
        elif any("contract" in str(msg.get("content", "")).lower() for msg in messages):
            params["max_tokens"] = 8192

        if config.api_key:
            params["api_key"] = config.api_key

        params.update(self.completion_params(config))
        return params
