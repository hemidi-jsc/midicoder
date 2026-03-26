from __future__ import annotations

import json
import types
from pathlib import Path

import pytest

from midicoder.commands.base import MidicoderPaths
from midicoder.llm.client import LlmRequestError, call_llm, load_llm_config


def _write_workspace(root: Path, config: dict, secrets: dict | None = None) -> MidicoderPaths:
    dot = root / ".midicoder"
    (dot / "secrets").mkdir(parents=True, exist_ok=True)
    (dot / "config.json").write_text(json.dumps(config), encoding="utf-8")
    if secrets is not None:
        (dot / "secrets" / "secrets.json").write_text(json.dumps(secrets), encoding="utf-8")
    return MidicoderPaths(root=root)


def _patch_litellm_client(
    monkeypatch: pytest.MonkeyPatch,
    *,
    create_fn,
) -> None:
    async def _fake_acompletion(**kwargs):
        return create_fn(**kwargs)

    monkeypatch.setitem(
        __import__("sys").modules,
        "litellm",
        types.SimpleNamespace(acompletion=_fake_acompletion),
    )


def test_load_llm_config_allows_missing_base_url_for_bedrock(tmp_path: Path) -> None:
    paths = _write_workspace(
        tmp_path,
        {
            "llm": {
                "high": {
                    "provider": "aws_bedrock",
                    "model": "bedrock/anthropic.claude-3-5-sonnet-20240620-v1:0",
                    "aws_bedrock_region": "us-east-1",
                }
            },
            "cache": {"enable": True, "type": "ephemeral"},
        },
        secrets={"llm": {"high": {"api_key": "test-key"}}},
    )

    cfg = load_llm_config(paths, tier="high")

    assert cfg.base_url is None
    assert cfg.model == "bedrock/anthropic.claude-3-5-sonnet-20240620-v1:0"
    assert cfg.aws_bedrock_region == "us-east-1"
    assert cfg.cache_enabled is True
    assert cfg.cache_type == "ephemeral"


def test_call_llm_uses_azure_deployment_model_and_provider_params(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = _write_workspace(
        tmp_path,
        {
            "llm": {
                "cheap": {
                    "provider": "azure_openai",
                    "model": "gpt-4o-mini",
                    "azure_openai_deployment": "gpt4o-mini-deploy",
                    "azure_openai_endpoint": "https://example-azure.openai.azure.com",
                    "azure_openai_api_version": "2024-10-21",
                }
            },
            "cache": {"enabled": False},
        },
        secrets={"llm": {"cheap": {"api_key": "azure-key"}}},
    )

    captured: dict[str, object] = {}

    class _FakeResponse:
        def model_dump(self) -> dict:
            return {
                "choices": [{"message": {"content": "ok"}}],
                "id": "resp_123",
            }

    def _fake_create(**kwargs):
        captured.update(kwargs)
        return _FakeResponse()

    _patch_litellm_client(monkeypatch, create_fn=_fake_create)

    cfg = load_llm_config(paths, tier="cheap")
    resp = call_llm(cfg, prompt="Hello")

    assert resp.content == "ok"
    assert captured["model"] == "azure/gpt4o-mini-deploy"
    assert captured["api_base"] == "https://example-azure.openai.azure.com"
    assert captured["api_version"] == "2024-10-21"
    assert captured["api_key"] == "azure-key"
    assert captured["timeout"] == 300.0
    assert captured["extra_headers"] == {"x-litellm-timeout": "300"}


def test_call_llm_applies_anthropic_prompt_cache_when_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    class _FakeResponse:
        def model_dump(self) -> dict:
            return {"choices": [{"message": {"content": "cached"}}]}

    def _fake_create(**kwargs):
        captured.update(kwargs)
        return _FakeResponse()

    _patch_litellm_client(monkeypatch, create_fn=_fake_create)

    from midicoder.llm.client import LlmConfig

    cfg = LlmConfig(
        base_url="https://api.anthropic.com",
        model="anthropic/claude-3-7-sonnet-latest",
        api_key="k",
        provider="anthropic",
        cache_enabled=True,
        cache_type="ephemeral",
    )

    call_llm(cfg, context="ctx", prompt="task")
    messages = captured["messages"]

    assert isinstance(messages, list)
    context_msg = messages[0]
    content = context_msg["content"]
    assert isinstance(content, list)
    assert content[0]["cache_control"] == {"type": "ephemeral"}


def test_call_llm_maps_litellm_errors_to_llm_request_error(monkeypatch: pytest.MonkeyPatch) -> None:
    class AuthenticationError(Exception):
        status_code = 401

    def _fake_create(**kwargs):
        raise AuthenticationError("bad key")

    _patch_litellm_client(monkeypatch, create_fn=_fake_create)

    from midicoder.llm.client import LlmConfig

    cfg = LlmConfig(
        base_url="https://api.openai.com/v1",
        model="openai/gpt-4o-mini",
        api_key="bad",
        provider="openai",
        cache_enabled=False,
        cache_type=None,
    )

    with pytest.raises(LlmRequestError, match=r"LLM auth error \(401\)"):
        call_llm(cfg, prompt="hello")


def test_call_llm_maps_vertex_provider_specific_params(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    class _FakeResponse:
        def model_dump(self) -> dict:
            return {"choices": [{"message": {"content": "vertex ok"}}]}

    def _fake_create(**kwargs):
        captured.update(kwargs)
        return _FakeResponse()

    _patch_litellm_client(monkeypatch, create_fn=_fake_create)

    from midicoder.llm.client import LlmConfig

    cfg = LlmConfig(
        base_url=None,
        model="gemini-1.5-pro",
        api_key=None,
        provider="vertex_partner",
        cache_enabled=False,
        cache_type=None,
        vertex_project="demo-project",
        vertex_location="asia-southeast1",
    )

    resp = call_llm(cfg, prompt="hello")

    assert resp.content == "vertex ok"
    assert captured["model"] == "vertex_ai/gemini-1.5-pro"
    assert captured["vertex_project"] == "demo-project"
    assert captured["vertex_location"] == "asia-southeast1"


def test_call_llm_openai_compatible_with_nvidia_model_sets_custom_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    class _FakeResponse:
        def model_dump(self) -> dict:
            return {"choices": [{"message": {"content": "ok"}}]}

    def _fake_create(**kwargs):
        captured.update(kwargs)
        return _FakeResponse()

    _patch_litellm_client(monkeypatch, create_fn=_fake_create)

    from midicoder.llm.client import LlmConfig

    cfg = LlmConfig(
        base_url="http://localhost:1234/v1",
        model="nvidia/nemotron-3-nano-4b",
        api_key=None,
        provider="openai_compatible",
        cache_enabled=False,
        cache_type=None,
    )

    resp = call_llm(cfg, prompt="hello")

    assert resp.content == "ok"
    assert captured["model"] == "nvidia/nemotron-3-nano-4b"
    assert captured["api_base"] == "http://localhost:1234/v1"
    assert captured["custom_llm_provider"] == "openai"
    assert captured["timeout"] == 300.0
    assert captured["extra_headers"] == {"x-litellm-timeout": "300"}


def test_call_llm_openai_compatible_normalizes_api_base_without_v1(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    class _FakeResponse:
        def model_dump(self) -> dict:
            return {"choices": [{"message": {"content": "ok"}}]}

    def _fake_create(**kwargs):
        captured.update(kwargs)
        return _FakeResponse()

    _patch_litellm_client(monkeypatch, create_fn=_fake_create)

    from midicoder.llm.client import LlmConfig

    cfg = LlmConfig(
        base_url="http://litellm.4hmd.com",
        model="sonnet4-5",
        api_key=None,
        provider="openai_compatible",
        cache_enabled=False,
        cache_type=None,
    )

    resp = call_llm(cfg, prompt="hello")

    assert resp.content == "ok"
    assert captured["api_base"] == "https://litellm.4hmd.com/v1"


def test_call_llm_openai_compatible_normalizes_chat_completions_endpoint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    class _FakeResponse:
        def model_dump(self) -> dict:
            return {"choices": [{"message": {"content": "ok"}}]}

    def _fake_create(**kwargs):
        captured.update(kwargs)
        return _FakeResponse()

    _patch_litellm_client(monkeypatch, create_fn=_fake_create)

    from midicoder.llm.client import LlmConfig

    cfg = LlmConfig(
        base_url="http://localhost:4000/v1/chat/completions",
        model="gpt-4o-mini",
        api_key=None,
        provider="openai_compatible",
        cache_enabled=False,
        cache_type=None,
    )

    resp = call_llm(cfg, prompt="hello")

    assert resp.content == "ok"
    assert captured["api_base"] == "http://localhost:4000/v1"


def test_call_llm_openai_compatible_keeps_http_for_private_ip(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    class _FakeResponse:
        def model_dump(self) -> dict:
            return {"choices": [{"message": {"content": "ok"}}]}

    def _fake_create(**kwargs):
        captured.update(kwargs)
        return _FakeResponse()

    _patch_litellm_client(monkeypatch, create_fn=_fake_create)

    from midicoder.llm.client import LlmConfig

    cfg = LlmConfig(
        base_url="http://10.0.0.8:4000",
        model="gpt-4o-mini",
        api_key=None,
        provider="openai_compatible",
        cache_enabled=False,
        cache_type=None,
    )

    resp = call_llm(cfg, prompt="hello")

    assert resp.content == "ok"
    assert captured["api_base"] == "http://10.0.0.8:4000/v1"


def test_load_llm_config_clamps_timeout_to_minimum_5_minutes(tmp_path: Path) -> None:
    paths = _write_workspace(
        tmp_path,
        {
            "llm": {
                "high": {
                    "provider": "openai_compatible",
                    "model": "gpt-4o-mini",
                    "base_url": "http://localhost:1234/v1",
                    "timeout_seconds": 30,
                }
            }
        },
    )

    cfg = load_llm_config(paths, tier="high")

    assert cfg.timeout_seconds == 300.0


def test_call_llm_vertex_partner_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    class _FakeResponse:
        def model_dump(self) -> dict:
            return {"choices": [{"message": {"content": "ok"}}]}

    def _fake_create(**kwargs):
        captured.update(kwargs)
        return _FakeResponse()

    _patch_litellm_client(monkeypatch, create_fn=_fake_create)

    from midicoder.llm.client import LlmConfig

    cfg = LlmConfig(
        base_url=None,
        model="gemini-1.5-pro",
        api_key=None,
        provider="vertex_partner",
        cache_enabled=False,
        cache_type=None,
        vertex_project="demo-project",
        vertex_location="asia-southeast1",
    )

    resp = call_llm(cfg, prompt="hello")

    assert resp.content == "ok"
    assert captured["model"] == "vertex_ai/gemini-1.5-pro"
    assert captured["vertex_project"] == "demo-project"
    assert captured["vertex_location"] == "asia-southeast1"


def test_call_llm_openai_provider_keeps_plain_model_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    class _FakeResponse:
        def model_dump(self) -> dict:
            return {"choices": [{"message": {"content": "ok"}}]}

    def _fake_create(**kwargs):
        captured.update(kwargs)
        return _FakeResponse()

    _patch_litellm_client(monkeypatch, create_fn=_fake_create)

    from midicoder.llm.client import LlmConfig

    cfg = LlmConfig(
        base_url="https://api.openai.com/v1",
        model="gpt-4o-mini",
        api_key="k",
        provider="openai",
        cache_enabled=False,
        cache_type=None,
    )

    call_llm(cfg, prompt="hello")

    assert captured["model"] == "gpt-4o-mini"
    assert captured["api_base"] == "https://api.openai.com/v1"


def test_call_llm_maps_bedrock_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    class _FakeResponse:
        def model_dump(self) -> dict:
            return {"choices": [{"message": {"content": "ok"}}]}

    def _fake_create(**kwargs):
        captured.update(kwargs)
        return _FakeResponse()

    _patch_litellm_client(monkeypatch, create_fn=_fake_create)

    from midicoder.llm.client import LlmConfig

    cfg = LlmConfig(
        base_url=None,
        model="anthropic.claude-3-5-sonnet-20240620-v1:0",
        api_key="k",
        provider="bedrock",
        cache_enabled=False,
        cache_type=None,
        aws_region_name="us-east-1",
    )

    call_llm(cfg, prompt="hello")

    assert captured["model"] == "bedrock/anthropic.claude-3-5-sonnet-20240620-v1:0"
    assert captured["aws_region_name"] == "us-east-1"


def test_call_llm_extract_headers_forces_litellm_timeout_300_seconds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    class _FakeResponse:
        def model_dump(self) -> dict:
            return {"choices": [{"message": {"content": "ok"}}]}

    def _fake_create(**kwargs):
        captured.update(kwargs)
        return _FakeResponse()

    _patch_litellm_client(monkeypatch, create_fn=_fake_create)

    from midicoder.llm.client import LlmConfig

    cfg = LlmConfig(
        base_url="http://localhost:1234/v1",
        model="openai/gpt-4o-mini",
        api_key=None,
        provider="openai_compatible",
        cache_enabled=False,
        cache_type=None,
        timeout_seconds=900.0,
    )

    call_llm(cfg, prompt="hello")

    assert captured["timeout"] == 900.0
    assert captured["extra_headers"] == {"x-litellm-timeout": "300"}


def test_call_llm_uses_litellm_acompletion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    class _FakeResponse:
        def model_dump(self) -> dict:
            return {"choices": [{"message": {"content": "ok"}}]}

    def _fake_create(**kwargs):
        captured.update(kwargs)
        return _FakeResponse()

    from midicoder.llm.client import LlmConfig

    _patch_litellm_client(monkeypatch, create_fn=_fake_create)

    cfg = LlmConfig(
        base_url="http://localhost:1234/v1",
        model="openai/gpt-4o-mini",
        api_key=None,
        provider="openai_compatible",
        cache_enabled=False,
        cache_type=None,
        timeout_seconds=900.0,
    )

    response = call_llm(cfg, prompt="hello")

    assert response.content == "ok"
    assert captured["model"] == "openai/gpt-4o-mini"
