"""Comprehensive unit tests for the `midicoder init` command."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from midicoder.cli import _build_parser
from midicoder.commands.base import MidicoderPaths
from midicoder.commands.init import run
from midicoder.config import ConfigManager, SecretsManager


def _make_non_interactive_args(root: Path, **overrides: object) -> SimpleNamespace:
    """Create an args object matching CLI parser fields for non-interactive init."""
    defaults: dict[str, object] = {
        "config_list": False,
        "non_interactive": True,
        "env_prefix": "MIDICODER_",
        "rewrite_config": None,
        "working_dir": str(root),
        "stack": "fastapi",
        "llm_high_provider": "anthropic",
        "llm_high_model": "anthropic/claude-3-7-sonnet-latest",
        "llm_high_url": None,
        "llm_high_key": None,
        "llm_high_key_env": None,
        "llm_cheap_provider": "anthropic",
        "llm_cheap_model": "anthropic/claude-3-5-haiku-latest",
        "llm_cheap_url": None,
        "llm_cheap_key": None,
        "llm_cheap_key_env": None,
        "llm_high_aws_region_name": None,
        "llm_cheap_aws_region_name": None,
        "llm_high_azure_openai_endpoint": None,
        "llm_high_azure_openai_api_version": None,
        "llm_high_azure_openai_deployment": None,
        "llm_cheap_azure_openai_endpoint": None,
        "llm_cheap_azure_openai_api_version": None,
        "llm_cheap_azure_openai_deployment": None,
        "llm_high_vertex_project": None,
        "llm_high_vertex_location": None,
        "llm_cheap_vertex_project": None,
        "llm_cheap_vertex_location": None,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


class TestInitHappyPath:
    """Happy path scenarios for project initialization."""

    def test_init_in_empty_directory_creates_expected_files_and_defaults(self, tmp_path: Path) -> None:
        """Initialize in an empty directory and verify canonical files/default values."""
        args = _make_non_interactive_args(tmp_path)
        run(tmp_path, args)

        paths = MidicoderPaths(root=tmp_path)
        config_path = paths.config
        state_path = paths.state
        secrets_file = paths.secrets / "secrets.json"

        # Core workspace artifacts
        assert config_path.exists()
        assert state_path.exists()
        assert secrets_file.exists()
        assert (paths.dot_midicoder / ".gitignore").exists()

        # Default config fields
        config = ConfigManager(paths).load()
        assert config["working_dir"] == str(tmp_path)
        assert config["stack"] == ["fastapi"]
        assert config["commands"] == []
        assert config["cache"]["enable"] is True
        assert config["cache"]["type"] == "ephemeral"
        assert config["llm"]["high"]["provider"] == "anthropic"
        assert config["llm"]["high"]["base_url"] == "https://api.anthropic.com"
        assert config["llm"]["cheap"]["provider"] == "anthropic"
        assert config["llm"]["cheap"]["base_url"] == "https://api.anthropic.com"

        # Run output should be emitted under .midicoder/runs/init/<timestamp>/
        run_dirs = sorted((paths.runs / "init").iterdir())
        assert run_dirs, "expected at least one init run directory"
        summary = json.loads((run_dirs[-1] / "summary.json").read_text(encoding="utf-8"))
        assert summary["status"] == "initialized"
        assert summary["mode"] == "non-interactive"


class TestInitNonInteractiveMode:
    """Non-interactive mode behavior."""

    def test_non_interactive_never_calls_prompt_confirm(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """`--non-interactive` mode should skip interactive prompts entirely."""

        def _fail_if_called(*_args: object, **_kwargs: object) -> bool:
            raise AssertionError("prompt_confirm must not be called in non-interactive mode")

        monkeypatch.setattr("midicoder.commands.init.prompt_confirm", _fail_if_called)
        args = _make_non_interactive_args(tmp_path, stack=None)
        run(tmp_path, args)

        # Defaults still applied when stack flag is omitted.
        config = ConfigManager(MidicoderPaths(root=tmp_path)).load()
        assert config["stack"] == ["fastapi"]

    def test_non_interactive_sets_global_non_interactive_env(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Running non-interactive init should set MIDICODER_NON_INTERACTIVE=true."""
        monkeypatch.delenv("MIDICODER_NON_INTERACTIVE", raising=False)
        args = _make_non_interactive_args(tmp_path)
        run(tmp_path, args)
        import os

        # Read directly from process env to ensure the command performed the side effect.
        assert os.getenv("MIDICODER_NON_INTERACTIVE") == "true"


class TestExistingProjectBehavior:
    """Existing project state with and without explicit overwrite intent."""

    def test_existing_config_refuses_overwrite_without_rewrite_flag(self, tmp_path: Path) -> None:
        """Existing config should fail in non-interactive mode unless rewrite is explicitly enabled."""
        run(tmp_path, _make_non_interactive_args(tmp_path, rewrite_config=False))

        with pytest.raises(SystemExit):
            run(tmp_path, _make_non_interactive_args(tmp_path, rewrite_config=False))

    def test_existing_config_allows_overwrite_with_rewrite_flag(self, tmp_path: Path) -> None:
        """Existing config should be rewritten when rewrite policy is explicitly enabled."""
        run(tmp_path, _make_non_interactive_args(tmp_path, rewrite_config=False))
        marker = tmp_path / ".midicoder" / "runs" / "legacy-marker.txt"
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text("keep me", encoding="utf-8")

        run(
            tmp_path,
            _make_non_interactive_args(
                tmp_path,
                rewrite_config=True,
                stack="fastapi,nest",
                llm_high_model="anthropic/claude-3-5-sonnet-latest",
            ),
        )

        config = ConfigManager(MidicoderPaths(root=tmp_path)).load()
        assert config["stack"] == ["fastapi", "nest"]
        assert config["llm"]["high"]["model"] == "anthropic/claude-3-5-sonnet-latest"
        assert marker.exists(), "non-config workspace artifacts must be preserved"

    def test_existing_config_without_rewrite_shows_rewrite_not_allowed_only(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Without rewrite permission, output should not show Overwrite Mode panel."""
        run(tmp_path, _make_non_interactive_args(tmp_path, rewrite_config=False))

        with pytest.raises(SystemExit):
            run(tmp_path, _make_non_interactive_args(tmp_path, rewrite_config=False))

        output = capsys.readouterr().out
        assert "Rewrite Not Allowed" in output
        assert "Overwrite Mode" not in output

    def test_existing_config_with_rewrite_shows_overwrite_mode(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """With explicit rewrite permission, output should show Overwrite Mode panel."""
        run(tmp_path, _make_non_interactive_args(tmp_path, rewrite_config=False))
        capsys.readouterr()

        run(tmp_path, _make_non_interactive_args(tmp_path, rewrite_config=True))

        output = capsys.readouterr().out
        assert "Overwrite Mode" in output


class TestEnvironmentVariableHandling:
    """Environment-variable behavior for API key resolution and validation."""

    def test_uses_valid_midicoder_litellm_api_key_from_env_reference(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """A valid MIDICODER_LITELLM_API_KEY should be used when referenced via --llm-*-key-env."""
        monkeypatch.setenv("MIDICODER_LITELLM_API_KEY", "sk-litellm-test-key")
        args = _make_non_interactive_args(
            tmp_path,
            llm_high_key_env="MIDICODER_LITELLM_API_KEY",
            llm_cheap_key_env="MIDICODER_LITELLM_API_KEY",
        )
        run(tmp_path, args)

        llm_secrets = SecretsManager(MidicoderPaths(root=tmp_path).secrets).load_secrets("llm")
        assert llm_secrets["high"]["api_key"] == "sk-litellm-test-key"
        assert llm_secrets["cheap"]["api_key"] == "sk-litellm-test-key"

    def test_missing_api_key_env_reference_warns_and_continues(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Missing key env var should emit warning and still initialize deterministically."""
        args = _make_non_interactive_args(
            tmp_path,
            llm_high_key_env="MIDICODER_LITELLM_API_KEY",
            llm_cheap_key_env="MIDICODER_LITELLM_API_KEY",
        )
        run(tmp_path, args)

        output = capsys.readouterr().out
        assert "Environment variable MIDICODER_LITELLM_API_KEY not found" in output

        llm_secrets = SecretsManager(MidicoderPaths(root=tmp_path).secrets).load_secrets("llm")
        assert "api_key" not in llm_secrets["high"]
        assert "api_key" not in llm_secrets["cheap"]


class TestInitErrorHandling:
    """Error scenarios for init command."""

    def test_no_write_permission_surfaces_permission_error(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Simulate filesystem write denial by forcing ConfigManager.save to raise PermissionError."""

        def _raise_permission_error(self: ConfigManager, _config: dict) -> None:
            raise PermissionError("write access denied")

        monkeypatch.setattr(ConfigManager, "save", _raise_permission_error)
        with pytest.raises(PermissionError):
            run(tmp_path, _make_non_interactive_args(tmp_path))

    def test_invalid_flag_force_is_rejected_by_parser(self) -> None:
        """Unknown flag --force should fail parser validation for init."""
        parser = _build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["init", "--force"])

    def test_corrupted_existing_config_without_rewrite_exits(self, tmp_path: Path) -> None:
        """Corrupted existing config should still respect rewrite policy and fail without rewrite."""
        paths = MidicoderPaths(root=tmp_path)
        paths.config.parent.mkdir(parents=True, exist_ok=True)
        paths.config.write_text("{not-valid-json", encoding="utf-8")

        with pytest.raises(SystemExit):
            run(tmp_path, _make_non_interactive_args(tmp_path, rewrite_config=False))


class TestInitEdgeCases:
    """Edge-case behavior for init command robustness."""

    def test_non_empty_directory_initializes_successfully(self, tmp_path: Path) -> None:
        """Init should succeed even when repository root already has unrelated files."""
        (tmp_path / "README.md").write_text("# Existing project\n", encoding="utf-8")
        run(tmp_path, _make_non_interactive_args(tmp_path))
        assert MidicoderPaths(root=tmp_path).config.exists()

    def test_partial_initialization_leaves_recoverable_state_on_interrupted_run(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """If secrets write fails after config save, config should exist but run output is incomplete."""
        original_save_secrets = SecretsManager.save_secrets

        def _fail_after_attempt(self: SecretsManager, category: str, secrets: dict) -> None:
            if category == "llm":
                raise RuntimeError("simulated interruption during secrets save")
            original_save_secrets(self, category, secrets)

        monkeypatch.setattr(SecretsManager, "save_secrets", _fail_after_attempt)

        with pytest.raises(RuntimeError):
            run(tmp_path, _make_non_interactive_args(tmp_path))

        paths = MidicoderPaths(root=tmp_path)
        assert paths.config.exists(), "config write should have happened before interruption"
        assert not (paths.runs / "init").exists() or not any((paths.runs / "init").iterdir())

    def test_invalid_environment_value_for_rewrite_config_errors(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Invalid boolean env values should fail fast with SystemExit."""
        monkeypatch.setenv("MIDICODER_REWRITE_CONFIG", "maybe")
        with pytest.raises(SystemExit):
            run(tmp_path, _make_non_interactive_args(tmp_path, rewrite_config=None))
