"""Unit tests for interactive config initialization."""

from midicoder.commands.base import MidicoderPaths
from midicoder.config import ConfigManager, SecretsManager


def test_initialize_interactive_with_azure_provider_specific_fields(monkeypatch, tmp_path) -> None:
    """Interactive wizard should persist provider-specific Azure fields."""
    paths = MidicoderPaths(root=tmp_path)
    manager = ConfigManager(paths)

    choice_answers = iter(["azure_openai", "azure_openai"])
    text_answers = iter(
        [
            str(tmp_path),  # working directory
            "https://my-resource.openai.azure.com",  # high endpoint
            "2024-10-21",  # high api version
            "gpt-4o-prod",  # high deployment
            "azure/gpt-4o",  # high model
            "",  # cheap endpoint (blank => reuse high)
            "",  # cheap api version (blank => reuse high)
            "",  # cheap deployment (blank => reuse high)
            "azure/gpt-4o-mini",  # cheap model
        ]
    )
    secret_answers = iter(["sk-high", ""])  # cheap blank => reuse high key

    def fake_prompt_text(*args, **kwargs):
        return next(text_answers)

    def fake_prompt_choice(*args, **kwargs):
        return next(choice_answers)

    def fake_prompt_multichoice(*args, **kwargs):
        return ["fastapi"]

    def fake_prompt_secret(*args, **kwargs):
        return next(secret_answers)

    monkeypatch.setattr("midicoder.io.prompt_text", fake_prompt_text)
    monkeypatch.setattr("midicoder.io.prompt_choice", fake_prompt_choice)
    monkeypatch.setattr("midicoder.io.prompt_multichoice", fake_prompt_multichoice)
    monkeypatch.setattr("midicoder.io.prompt_secret", fake_prompt_secret)

    # Silence output helpers.
    monkeypatch.setattr("midicoder.io.messages.print_info", lambda *args, **kwargs: None)
    monkeypatch.setattr("midicoder.io.messages.print_success", lambda *args, **kwargs: None)
    monkeypatch.setattr("midicoder.io.messages.print_normal", lambda *args, **kwargs: None)

    manager.initialize_interactive()

    config = manager.load()
    assert config["llm"]["high"]["provider"] == "azure_openai"
    assert config["llm"]["high"]["base_url"] is None
    assert config["llm"]["high"]["azure_openai_endpoint"] == "https://my-resource.openai.azure.com"
    assert config["llm"]["high"]["azure_openai_api_version"] == "2024-10-21"
    assert config["llm"]["high"]["azure_openai_deployment"] == "gpt-4o-prod"

    # Cheap tier should reuse provider-specific fields from high when blank.
    assert config["llm"]["cheap"]["provider"] == "azure_openai"
    assert config["llm"]["cheap"]["base_url"] is None
    assert config["llm"]["cheap"]["azure_openai_endpoint"] == "https://my-resource.openai.azure.com"
    assert config["llm"]["cheap"]["azure_openai_api_version"] == "2024-10-21"
    assert config["llm"]["cheap"]["azure_openai_deployment"] == "gpt-4o-prod"

    llm_secrets = SecretsManager(paths.secrets).load_secrets("llm")
    assert llm_secrets["high"]["api_key"] == "sk-high"
    assert llm_secrets["cheap"]["api_key"] == "sk-high"
    assert llm_secrets["high"]["provider"] == "azure_openai"
    assert llm_secrets["cheap"]["provider"] == "azure_openai"


def test_initialize_interactive_uses_shared_validator(monkeypatch, tmp_path) -> None:
    """Interactive initialization should fail-fast when shared validator returns errors."""
    paths = MidicoderPaths(root=tmp_path)
    manager = ConfigManager(paths)

    choice_answers = iter(["anthropic", "anthropic"])
    text_answers = iter(
        [
            str(tmp_path),
            "anthropic/claude-3-7-sonnet-latest",
            "anthropic/claude-3-5-haiku-latest",
        ]
    )
    secret_answers = iter(["sk-high", "sk-cheap"])

    monkeypatch.setattr("midicoder.io.prompt_text", lambda *args, **kwargs: next(text_answers))
    monkeypatch.setattr("midicoder.io.prompt_choice", lambda *args, **kwargs: next(choice_answers))
    monkeypatch.setattr("midicoder.io.prompt_multichoice", lambda *args, **kwargs: ["fastapi"])
    monkeypatch.setattr("midicoder.io.prompt_secret", lambda *args, **kwargs: next(secret_answers))
    monkeypatch.setattr("midicoder.io.messages.print_info", lambda *args, **kwargs: None)
    monkeypatch.setattr("midicoder.io.messages.print_success", lambda *args, **kwargs: None)
    monkeypatch.setattr("midicoder.io.messages.print_normal", lambda *args, **kwargs: None)

    def reject_validator(config, llm_secrets):
        assert config["llm"]["high"]["provider"] == "anthropic"
        assert config["llm"]["high"]["base_url"] == "https://api.anthropic.com"
        assert llm_secrets["high"]["provider"] == "anthropic"
        return ["forced validation error"]

    try:
        manager.initialize_interactive(validate_fn=reject_validator)
        assert False, "Expected ValueError from validator"
    except ValueError as exc:
        assert "forced validation error" in str(exc)

    assert not paths.config.exists()
