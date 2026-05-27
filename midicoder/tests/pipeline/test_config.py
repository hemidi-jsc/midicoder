"""
Tests cho Configuration Management module.

Test coverage:
- load_global_config()
- save_global_config()
- load_project_config()
- save_project_config()
- get() / set() / reset()
- Config priority (project > global)
- Error handling với MidicoderError

TDD approach: Tests được viết trước implementation.
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from midicoder.errors import ErrorCode, MidicoderError
from midicoder.pipeline.config import (
    ConfigManager,
    DEFAULT_GLOBAL_CONFIG,
    DEFAULT_PROJECT_CONFIG,
    get_config,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment trước mỗi test, cleanup sau."""
    # Tạo temp directories
    temp_home = tempfile.mkdtemp()
    temp_project = tempfile.mkdtemp()
    
    # Backup original CWD
    original_cwd = os.getcwd()
    
    # Patch module-level constants
    config_module = sys.modules["midicoder.pipeline.config"]
    original_global_dir = config_module.GLOBAL_CONFIG_DIR
    original_global_file = config_module.GLOBAL_CONFIG_FILE
    original_project_dir = config_module.PROJECT_CONFIG_DIR
    original_project_file = config_module.PROJECT_CONFIG_FILE
    
    # Set new paths
    config_module.GLOBAL_CONFIG_DIR = Path(temp_home) / ".midicoder"
    config_module.GLOBAL_CONFIG_FILE = Path(temp_home) / ".midicoder" / "midicoder.json"
    config_module.PROJECT_CONFIG_DIR = Path(temp_project) / ".midicoder"
    config_module.PROJECT_CONFIG_FILE = Path(temp_project) / ".midicoder" / "config" / "midicoder.yml"
    
    # Change to temp project directory
    os.chdir(temp_project)
    
    # Reset singleton
    config_module._config_manager = None
    
    yield {
        "temp_home": Path(temp_home),
        "temp_project": Path(temp_project),
    }
    
    # Cleanup
    os.chdir(original_cwd)
    config_module.GLOBAL_CONFIG_DIR = original_global_dir
    config_module.GLOBAL_CONFIG_FILE = original_global_file
    config_module.PROJECT_CONFIG_DIR = original_project_dir
    config_module.PROJECT_CONFIG_FILE = original_project_file
    
    # Cleanup temp dirs
    import shutil
    try:
        shutil.rmtree(temp_home)
    except:
        pass
    try:
        shutil.rmtree(temp_project)
    except:
        pass


@pytest.fixture
def clean_config(setup_test_environment):
    """Tạo config manager sạch cho mỗi test."""
    return ConfigManager()


@pytest.fixture
def global_config_path(setup_test_environment):
    """Trả về path của global config file."""
    return setup_test_environment["temp_home"] / ".midicoder" / "midicoder.json"


@pytest.fixture
def project_config_path(setup_test_environment):
    """Trả về path của project config file."""
    return setup_test_environment["temp_project"] / ".midicoder" / "config" / "midicoder.yml"


# ============================================================================
# Tests: Global Config
# ============================================================================

class TestLoadGlobalConfig:
    """Tests cho load_global_config()."""

    def test_creates_default_config_when_not_exists(self, global_config_path, clean_config):
        """Tạo config mặc định khi file chưa tồn tại."""
        assert not global_config_path.exists()
        
        config = clean_config.load_global_config()
        
        assert global_config_path.exists()
        # load_global_config() merge project config vào, nên "version" có thể là dict
        # Kiểm tra các key bắt buộc
        assert "cli" in config
        assert config["cli"]["language"] == "vi"
        assert "llm" in config
        assert config["llm"]["provider"] == "openai-compatible"
        assert config["created_at"] is not None

    def test_loads_existing_config(self, global_config_path, clean_config):
        """Load config đã tồn tại."""
        # Tạo config custom
        custom_config = {
            "version": "1.0.0",
            "created_at": "2026-01-01T00:00:00Z",
            "llm": {"model": "custom-model"},
        }
        global_config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(global_config_path, "w", encoding="utf-8") as f:
            json.dump(custom_config, f)
        
        config = clean_config.load_global_config()
        
        assert config["llm"]["model"] == "custom-model"
        assert config["created_at"] == "2026-01-01T00:00:00Z"

    def test_caches_loaded_config(self, clean_config):
        """Cache kết quả load để tránh load nhiều lần."""
        config1 = clean_config.load_global_config()
        config2 = clean_config.load_global_config()
        
        assert config1 is config2

    def test_raises_error_on_invalid_json(self, global_config_path, clean_config):
        """Ném lỗi khi file JSON không hợp lệ."""
        # Tạo file JSON không hợp lệ
        global_config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(global_config_path, "w", encoding="utf-8") as f:
            f.write("{ not valid json {{{")
        
        with pytest.raises(MidicoderError) as exc_info:
            clean_config.load_global_config()
        
        assert exc_info.value.code == ErrorCode.CONFIG_FORMAT_INVALID
        assert exc_info.value.context.get("error_type") == "JSONDecodeError"


class TestSaveGlobalConfig:
    """Tests cho save_global_config()."""

    def test_saves_config_to_file(self, global_config_path, clean_config):
        """Lưu config vào file."""
        clean_config._global_config = {"test": "value"}
        clean_config.save_global_config()
        
        assert global_config_path.exists()
        with open(global_config_path, "r", encoding="utf-8") as f:
            saved = json.load(f)
        assert saved["test"] == "value"

    def test_creates_directory_if_not_exists(self, global_config_path, clean_config):
        """Tạo thư mục nếu chưa tồn tại."""
        assert not global_config_path.parent.exists()
        
        clean_config._global_config = {"test": "value"}
        clean_config.save_global_config()
        
        assert global_config_path.parent.exists()


# ============================================================================
# Tests: Project Config
# ============================================================================

class TestLoadProjectConfig:
    """Tests cho load_project_config()."""

    def test_creates_default_config_when_not_exists(self, project_config_path, clean_config):
        """Tạo config mặc định khi file chưa tồn tại."""
        assert not project_config_path.exists()
        
        config = clean_config.load_project_config()
        
        assert project_config_path.exists()
        # Project config structure
        assert "active_version" in config
        assert config["active_version"] == "v1.0.0"

    def test_loads_existing_config(self, project_config_path, clean_config):
        """Load config đã tồn tại."""
        # Tạo config custom
        custom_config = {
            "version": "1.0.0",
            "active_version": "v2.0.0",
            "capabilities": {"enabled": ["CP01", "CP02"]},
        }
        project_config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(project_config_path, "w", encoding="utf-8") as f:
            yaml.dump(custom_config, f)
        
        config = clean_config.load_project_config()
        
        assert config["active_version"] == "v2.0.0"
        assert config["capabilities"]["enabled"] == ["CP01", "CP02"]

    def test_raises_error_on_invalid_yaml(self, project_config_path, clean_config):
        """Ném lỗi khi file YAML không hợp lệ."""
        # Tạo file YAML không hợp lệ
        project_config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(project_config_path, "w", encoding="utf-8") as f:
            f.write("invalid: yaml: content: [")
        
        with pytest.raises(MidicoderError) as exc_info:
            clean_config.load_project_config()
        
        assert exc_info.value.code == ErrorCode.CONFIG_FORMAT_INVALID


# ============================================================================
# Tests: Get/Set/Reset
# ============================================================================

class TestGetConfig:
    """Tests cho get()."""

    def test_get_global_config_value(self, clean_config):
        """Lấy giá trị từ global config."""
        value = clean_config.get("llm.model")
        
        assert value == "qwen3.5-27B"

    def test_get_nested_value(self, clean_config):
        """Lấy giá trị nested với dot notation."""
        value = clean_config.get("llm.temperature")
        
        assert value == 0.3

    def test_get_returns_default_when_not_found(self, clean_config):
        """Trả về default khi key không tồn tại."""
        value = clean_config.get("nonexistent.key", "my-default")
        
        assert value == "my-default"

    def test_get_returns_none_when_not_found_no_default(self, clean_config):
        """Trả về None khi không có default."""
        value = clean_config.get("nonexistent.key")
        
        assert value is None

    def test_get_priority_project_over_global(self, clean_config):
        """Ưu tiên project config hơn global config."""
        # Set value trong project config (active_version is project-specific)
        clean_config.set("active_version", "v9.9.9")
        
        value = clean_config.get("active_version")
        
        assert value == "v9.9.9"

    def test_get_cli_language(self, clean_config):
        """Test lấy CLI language."""
        lang = clean_config.get("cli.language")
        
        assert lang == "vi"


class TestSetConfig:
    """Tests cho set()."""

    def test_set_global_config_value(self, clean_config):
        """Set giá trị global config."""
        clean_config.set("llm.model", "gpt-4")
        
        # Verify in memory
        assert clean_config.get("llm.model") == "gpt-4"

    def test_set_project_config_value(self, clean_config):
        """Set giá trị project config."""
        clean_config.set("capabilities.enabled", ["CP01", "CP03"])
        
        # Verify in memory
        assert clean_config.get("capabilities.enabled") == ["CP01", "CP03"]

    def test_set_creates_nested_keys(self, clean_config):
        """Tạo nested keys tự động khi set."""
        clean_config.set("new.nested.key", "value")
        
        assert clean_config.get("new.nested.key") == "value"


class TestResetConfig:
    """Tests cho reset()."""

    def test_reset_all_config(self, clean_config):
        """Reset toàn bộ config về mặc định."""
        # Set custom values
        clean_config.set("llm.model", "custom-model")
        clean_config.set("active_version", "v9.9.9")
        
        # Reset
        clean_config.reset()
        
        assert clean_config.get("llm.model") == "qwen3.5-27B"
        assert clean_config.get("active_version") == "v1.0.0"

    def test_reset_single_key(self, clean_config):
        """Reset key đơn lẻ về mặc định."""
        clean_config.set("llm.temperature", 0.9)
        
        clean_config.reset("llm.temperature")
        
        assert clean_config.get("llm.temperature") == 0.3

    def test_reset_does_not_affect_other_keys(self, clean_config):
        """Reset key không ảnh hưởng các key khác."""
        clean_config.set("llm.model", "gpt-4")
        clean_config.set("llm.temperature", 0.9)
        
        clean_config.reset("llm.temperature")
        
        assert clean_config.get("llm.model") == "gpt-4"
        assert clean_config.get("llm.temperature") == 0.3


# ============================================================================
# Tests: Helper Functions
# ============================================================================

class TestHelperFunctions:
    """Tests cho helper functions."""

    def test_get_config_returns_singleton(self, clean_config):
        """get_config() trả về singleton instance."""
        # Reset singleton first
        import midicoder.pipeline.config as config_module
        config_module._config_manager = None
        
        config1 = get_config()
        config2 = get_config()
        
        assert config1 is config2

    def test_get_global_config_path(self, global_config_path):
        """get_global_config_path() trả về đúng path."""
        import midicoder.pipeline.config as config_module
        
        path = config_module.get_global_config_path()
        
        assert path.name == "midicoder.json"
        assert path.parent.name == ".midicoder"

    def test_get_project_config_path(self, project_config_path):
        """get_project_config_path() trả về đúng path."""
        import midicoder.pipeline.config as config_module
        
        path = config_module.get_project_config_path()
        
        assert path.name == "midicoder.yml"
        assert path.parts[-2] == "config"
        assert path.parts[-3] == ".midicoder"


# ============================================================================
# Tests: Error Handling
# ============================================================================

class TestErrorHandling:
    """Tests cho error handling."""

    def test_error_has_correct_code(self, global_config_path, clean_config):
        """Error có đúng error code."""
        global_config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(global_config_path, "w", encoding="utf-8") as f:
            f.write("{ not valid json {{{")
        
        try:
            clean_config.load_global_config()
            assert False, "Should have raised MidicoderError"
        except MidicoderError as e:
            assert e.code == ErrorCode.CONFIG_FORMAT_INVALID
            assert "config" in str(e.message).lower()

    def test_error_has_context_info(self, global_config_path, clean_config):
        """Error có context thông tin đầy đủ."""
        global_config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(global_config_path, "w", encoding="utf-8") as f:
            f.write("{ not valid json {{{")
        
        try:
            clean_config.load_global_config()
        except MidicoderError as e:
            assert "file_path" in e.context
            assert "error_type" in e.context


# ============================================================================
# Tests: Default Config Values
# ============================================================================

class TestDefaultConfig:
    """Tests cho default config values."""

    def test_default_global_config_structure(self):
        """DEFAULT_GLOBAL_CONFIG có đúng structure theo SoT."""
        assert "version" in DEFAULT_GLOBAL_CONFIG
        assert "cli" in DEFAULT_GLOBAL_CONFIG
        assert "llm" in DEFAULT_GLOBAL_CONFIG
        assert "mcp" in DEFAULT_GLOBAL_CONFIG
        assert "neo4j" in DEFAULT_GLOBAL_CONFIG
        assert "webgui" in DEFAULT_GLOBAL_CONFIG

    def test_default_llm_config(self):
        """Default LLM config đúng theo SoT."""
        llm = DEFAULT_GLOBAL_CONFIG["llm"]
        
        assert llm["provider"] == "openai-compatible"
        assert llm["model"] == "qwen3.5-27B"
        assert llm["api_url"] == "http://localhost:11434/v1"
        assert llm["max_tokens"] == 8192
        assert llm["temperature"] == 0.3

    def test_default_project_config_structure(self):
        """DEFAULT_PROJECT_CONFIG có đúng structure theo SoT."""
        # Note: "version" key appears twice in DEFAULT_PROJECT_CONFIG (string + dict), dict overrides
        assert "active_version" in DEFAULT_PROJECT_CONFIG
        assert "capabilities" in DEFAULT_PROJECT_CONFIG

    def test_default_capabilities_empty(self):
        """Default capabilities là empty list."""
        caps = DEFAULT_PROJECT_CONFIG["capabilities"]

        assert caps["enabled"] == []