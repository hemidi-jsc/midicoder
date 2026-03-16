"""Integration tests for non-interactive init."""

import os
from pathlib import Path
import pytest

from midicoder.commands.init import run
from midicoder.config import ConfigManager, SecretsManager
from midicoder.commands.base import MidicoderPaths


class TestInitNonInteractive:
    """Test non-interactive initialization."""
    
    def test_config_list_flag(self, capsys, tmp_path):
        """Test --config-list flag shows help and exits."""
        class Args:
            config_list = True
            non_interactive = False
        
        run(tmp_path, Args())
        
        captured = capsys.readouterr()
        assert "Configuration Keywords" in captured.out
        assert "--working-dir" in captured.out
        assert "--stack" in captured.out
        assert "--llm-high-provider" in captured.out
    
    def test_init_from_env_vars(self, tmp_path):
        """Test init using environment variables."""
        # Set environment variables
        os.environ.update({
            "MIDICODER_WORKING_DIR": str(tmp_path),
            "MIDICODER_STACK": "fastapi,nest",
            "MIDICODER_LLM_HIGH_PROVIDER": "anthropic",
            "MIDICODER_LLM_HIGH_MODEL": "claude-sonnet-4-5",
            "MIDICODER_LLM_HIGH_URL": "https://api.anthropic.com",
            "MIDICODER_LLM_HIGH_API_KEY": "sk-test-123",
            "MIDICODER_LLM_CHEAP_PROVIDER": "anthropic",
            "MIDICODER_LLM_CHEAP_MODEL": "claude-3-5-haiku",
            "MIDICODER_LLM_CHEAP_URL": "https://api.anthropic.com",
            "MIDICODER_LLM_CHEAP_API_KEY": "sk-test-456",
        })
        
        try:
            # Mock args
            class Args:
                config_list = False
                non_interactive = True
                env_prefix = "MIDICODER_"
                working_dir = None
                stack = None
                llm_high_provider = None
                llm_high_model = None
                llm_high_url = None
                llm_high_key = None
                llm_high_key_env = None
                llm_cheap_provider = None
                llm_cheap_model = None
                llm_cheap_url = None
                llm_cheap_key = None
                llm_cheap_key_env = None
            
            run(tmp_path, Args())
            
            # Verify config
            paths = MidicoderPaths(root=tmp_path)
            config_manager = ConfigManager(paths)
            config = config_manager.load()
            
            assert config["working_dir"] == str(tmp_path)
            assert config["stack"] == ["fastapi", "nest"]
            assert config["llm"]["high"]["provider"] == "anthropic"
            assert config["llm"]["high"]["model"] == "claude-sonnet-4-5"
            
            # Verify secrets
            secrets_manager = SecretsManager(paths.secrets)
            llm_secrets = secrets_manager.load_secrets("llm")
            assert llm_secrets["high"]["api_key"] == "sk-test-123"
            assert llm_secrets["cheap"]["api_key"] == "sk-test-456"
        
        finally:
            # Cleanup
            for key in list(os.environ.keys()):
                if key.startswith("MIDICODER_"):
                    del os.environ[key]
    
    def test_init_from_command_args(self, tmp_path):
        """Test init using command-line arguments."""
        os.environ["TEST_API_KEY_HIGH"] = "sk-cmd-123"
        os.environ["TEST_API_KEY_CHEAP"] = "sk-cmd-456"
        
        try:
            # Mock args
            class Args:
                config_list = False
                non_interactive = True
                env_prefix = "MIDICODER_"
                working_dir = str(tmp_path)
                stack = "nest,angular"
                llm_high_provider = "anthropic"
                llm_high_model = "claude-sonnet-4-5"
                llm_high_url = "https://api.anthropic.com"
                llm_high_key = None
                llm_high_key_env = "TEST_API_KEY_HIGH"
                llm_cheap_provider = "anthropic"
                llm_cheap_model = "claude-3-5-haiku"
                llm_cheap_url = "https://api.anthropic.com"
                llm_cheap_key = None
                llm_cheap_key_env = "TEST_API_KEY_CHEAP"
            
            run(tmp_path, Args())
            
            # Verify config
            paths = MidicoderPaths(root=tmp_path)
            config_manager = ConfigManager(paths)
            config = config_manager.load()
            
            assert config["working_dir"] == str(tmp_path)
            assert config["stack"] == ["nest", "angular"]
            assert config["llm"]["high"]["model"] == "claude-sonnet-4-5"
            
            # Verify secrets from env vars
            secrets_manager = SecretsManager(paths.secrets)
            llm_secrets = secrets_manager.load_secrets("llm")
            assert llm_secrets["high"]["api_key"] == "sk-cmd-123"
            assert llm_secrets["cheap"]["api_key"] == "sk-cmd-456"
        
        finally:
            del os.environ["TEST_API_KEY_HIGH"]
            del os.environ["TEST_API_KEY_CHEAP"]
    
    def test_init_priority_flag_over_env(self, tmp_path):
        """Test that flags take priority over environment variables."""
        os.environ["MIDICODER_STACK"] = "fastapi"
        os.environ["MIDICODER_LLM_HIGH_API_KEY"] = "sk-env-key"
        os.environ["MIDICODER_LLM_CHEAP_API_KEY"] = "sk-env-key-cheap"
        os.environ["MIDICODER_LLM_HIGH_PROVIDER"] = "anthropic"
        os.environ["MIDICODER_LLM_HIGH_MODEL"] = "claude-sonnet-4-5"
        os.environ["MIDICODER_LLM_HIGH_URL"] = "https://api.anthropic.com"
        os.environ["MIDICODER_LLM_CHEAP_PROVIDER"] = "anthropic"
        os.environ["MIDICODER_LLM_CHEAP_MODEL"] = "claude-3-5-haiku"
        os.environ["MIDICODER_LLM_CHEAP_URL"] = "https://api.anthropic.com"
        
        try:
            class Args:
                config_list = False
                non_interactive = True
                env_prefix = "MIDICODER_"
                working_dir = str(tmp_path)
                stack = "nest,angular"  # Flag overrides env var
                llm_high_provider = "anthropic"
                llm_high_model = "claude-sonnet-4-5"
                llm_high_url = "https://api.anthropic.com"
                llm_high_key = None
                llm_high_key_env = None
                llm_cheap_provider = "anthropic"
                llm_cheap_model = "claude-3-5-haiku"
                llm_cheap_url = "https://api.anthropic.com"
                llm_cheap_key = None
                llm_cheap_key_env = None
            
            run(tmp_path, Args())
            
            paths = MidicoderPaths(root=tmp_path)
            config_manager = ConfigManager(paths)
            config = config_manager.load()
            
            # Flag should override env var
            assert config["stack"] == ["nest", "angular"]
            
            # Env var should be used for API key (no flag provided)
            secrets_manager = SecretsManager(paths.secrets)
            llm_secrets = secrets_manager.load_secrets("llm")
            assert llm_secrets["high"]["api_key"] == "sk-env-key"
        
        finally:
            for key in ["MIDICODER_STACK", "MIDICODER_LLM_HIGH_API_KEY", 
                       "MIDICODER_LLM_CHEAP_API_KEY", "MIDICODER_LLM_HIGH_PROVIDER",
                       "MIDICODER_LLM_HIGH_MODEL", "MIDICODER_LLM_HIGH_URL",
                       "MIDICODER_LLM_CHEAP_PROVIDER", "MIDICODER_LLM_CHEAP_MODEL",
                       "MIDICODER_LLM_CHEAP_URL"]:
                if key in os.environ:
                    del os.environ[key]
    
    def test_init_validation_error_missing_required(self, tmp_path):
        """Test that validation errors are caught."""
        with pytest.raises(SystemExit):
            class Args:
                config_list = False
                non_interactive = True
                env_prefix = "MIDICODER_"
                working_dir = str(tmp_path)
                stack = "fastapi"
                llm_high_provider = None  # Missing required
                llm_high_model = None
                llm_high_url = None
                llm_high_key = None
                llm_high_key_env = None
                llm_cheap_provider = None
                llm_cheap_model = None
                llm_cheap_url = None
                llm_cheap_key = None
                llm_cheap_key_env = None
            
            run(tmp_path, Args())
    
    def test_init_validation_error_invalid_stack(self, tmp_path):
        """Test validation fails for invalid stack."""
        with pytest.raises(SystemExit):
            class Args:
                config_list = False
                non_interactive = True
                env_prefix = "MIDICODER_"
                working_dir = str(tmp_path)
                stack = "invalid-stack"  # Invalid
                llm_high_provider = "anthropic"
                llm_high_model = "claude-sonnet-4-5"
                llm_high_url = "https://api.anthropic.com"
                llm_high_key = "sk-test"
                llm_high_key_env = None
                llm_cheap_provider = "anthropic"
                llm_cheap_model = "claude-3-5-haiku"
                llm_cheap_url = "https://api.anthropic.com"
                llm_cheap_key = "sk-test"
                llm_cheap_key_env = None
            
            run(tmp_path, Args())
    
    def test_init_with_key_env_reference(self, tmp_path):
        """Test using --llm-*-key-env to reference custom env var."""
        os.environ["CUSTOM_HIGH_KEY"] = "sk-custom-high"
        os.environ["CUSTOM_CHEAP_KEY"] = "sk-custom-cheap"
        
        try:
            class Args:
                config_list = False
                non_interactive = True
                env_prefix = "MIDICODER_"
                working_dir = str(tmp_path)
                stack = "fastapi"
                llm_high_provider = "anthropic"
                llm_high_model = "claude-sonnet-4-5"
                llm_high_url = "https://api.anthropic.com"
                llm_high_key = None
                llm_high_key_env = "CUSTOM_HIGH_KEY"
                llm_cheap_provider = "anthropic"
                llm_cheap_model = "claude-3-5-haiku"
                llm_cheap_url = "https://api.anthropic.com"
                llm_cheap_key = None
                llm_cheap_key_env = "CUSTOM_CHEAP_KEY"
            
            run(tmp_path, Args())
            
            paths = MidicoderPaths(root=tmp_path)
            secrets_manager = SecretsManager(paths.secrets)
            llm_secrets = secrets_manager.load_secrets("llm")
            
            assert llm_secrets["high"]["api_key"] == "sk-custom-high"
            assert llm_secrets["cheap"]["api_key"] == "sk-custom-cheap"
        
        finally:
            del os.environ["CUSTOM_HIGH_KEY"]
            del os.environ["CUSTOM_CHEAP_KEY"]
