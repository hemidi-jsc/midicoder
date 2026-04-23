"""
Tests cho LLM Client module.

E20: CLI Commands - LLM Client Integration
"""

import json
import os
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from midicoder.errors import ErrorCode, MidicoderError
from midicoder.pipeline.llm.client import (
    LlmConfig,
    LlmProvider,
    LlmResponse,
    LlmError,
    LlmRequestError,
    LlmAuthError,
    LlmRateLimitError,
    LlmTimeoutError,
    load_llm_config,
    call_llm,
)


# ============================================================================
# Tests cho LlmConfig
# ============================================================================

class TestLlmConfig:
    """Tests cho LlmConfig dataclass."""

    def test_create_config_with_defaults(self):
        """Test tạo config với giá trị mặc định."""
        config = LlmConfig(
            provider=LlmProvider.OPENAI_COMPATIBLE,
            model="qwen3.5-27B",
            api_url="http://localhost:11434/v1",
        )
        
        assert config.provider == LlmProvider.OPENAI_COMPATIBLE
        assert config.model == "qwen3.5-27B"
        assert config.api_url == "http://localhost:11434/v1"
        assert config.api_key is None
        assert config.max_tokens == 8192
        assert config.temperature == 0.3
        assert config.timeout_seconds == 300
        assert config.retry_attempts == 3

    def test_create_config_with_custom_values(self):
        """Test tạo config với giá trị custom."""
        config = LlmConfig(
            provider=LlmProvider.ANTHROPIC,
            model="claude-3-sonnet",
            api_url="https://api.anthropic.com",
            api_key="sk-test-key",
            max_tokens=4096,
            temperature=0.7,
            timeout_seconds=120,
            retry_attempts=5,
        )
        
        assert config.provider == LlmProvider.ANTHROPIC
        assert config.model == "claude-3-sonnet"
        assert config.api_key == "sk-test-key"
        assert config.max_tokens == 4096
        assert config.temperature == 0.7
        assert config.timeout_seconds == 120
        assert config.retry_attempts == 5


# ============================================================================
# Tests cho load_llm_config
# ============================================================================

class TestLoadLlmConfig:
    """Tests cho load_llm_config function."""

    @patch("midicoder.pipeline.llm.client.get_config")
    def test_load_config_analyze_tier(self, mock_get_config):
        """Test load config cho tier analyze."""
        # Mock config manager
        mock_manager = MagicMock()
        mock_manager.get.side_effect = {
            "llm.provider": "openai-compatible",
            "llm.model": "qwen3.5-27B",
            "llm.api_url": "http://localhost:11434/v1",
            "llm.api_key": None,
            "llm.max_tokens": 8192,
            "llm.temperature": 0.3,
            "llm.timeout_seconds": 300,
            "llm.retry_attempts": 3,
            "llm.analyze.max_tokens": 4096,
            "llm.analyze.temperature": 0.1,
        }.get
        mock_get_config.return_value = mock_manager

        config = load_llm_config(tier="analyze")
        
        assert config.provider == LlmProvider.OPENAI_COMPATIBLE
        assert config.model == "qwen3.5-27B"
        # Tier-specific overrides
        assert config.max_tokens == 4096
        assert config.temperature == 0.1

    @patch("midicoder.pipeline.llm.client.get_config")
    def test_load_config_repair_tier(self, mock_get_config):
        """Test load config cho tier repair."""
        mock_manager = MagicMock()
        mock_manager.get.side_effect = {
            "llm.provider": "openai",
            "llm.model": "gpt-4o",
            "llm.api_url": "https://api.openai.com/v1",
            "llm.api_key": "sk-openai-key",
            "llm.max_tokens": 8192,
            "llm.temperature": 0.3,
            "llm.timeout_seconds": 300,
            "llm.retry_attempts": 3,
            "llm.repair.temperature": 0.0,
        }.get
        mock_get_config.return_value = mock_manager

        config = load_llm_config(tier="repair")
        
        assert config.provider == LlmProvider.OPENAI
        assert config.temperature == 0.0  # Repair tier override

    @patch("midicoder.pipeline.llm.client.get_config")
    def test_load_config_code_tier(self, mock_get_config):
        """Test load config cho tier code."""
        mock_manager = MagicMock()
        mock_manager.get.side_effect = {
            "llm.provider": "openai-compatible",
            "llm.model": "qwen3.5-27B",
            "llm.api_url": "http://localhost:11434/v1",
            "llm.api_key": None,
            "llm.max_tokens": 8192,
            "llm.temperature": 0.3,
            "llm.timeout_seconds": 300,
            "llm.retry_attempts": 3,
            "llm.code.max_tokens": 16384,
            "llm.code.temperature": 0.2,
        }.get
        mock_get_config.return_value = mock_manager

        config = load_llm_config(tier="code")
        
        assert config.max_tokens == 16384  # Code tier needs more tokens
        assert config.temperature == 0.2

    @patch("midicoder.pipeline.llm.client.get_config")
    def test_load_config_from_env_api_key(self, mock_get_config):
        """Test load API key từ environment variable."""
        mock_manager = MagicMock()
        mock_manager.get.side_effect = {
            "llm.provider": "openai",
            "llm.model": "gpt-4o",
            "llm.api_url": "https://api.openai.com/v1",
            "llm.api_key": None,  # No key in config
            "llm.max_tokens": 8192,
            "llm.temperature": 0.3,
            "llm.timeout_seconds": 300,
            "llm.retry_attempts": 3,
        }.get
        mock_get_config.return_value = mock_manager

        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-from-env"}):
            config = load_llm_config(tier="analyze")
            
            assert config.api_key == "sk-from-env"

    @patch("midicoder.pipeline.llm.client.get_config")
    def test_load_config_anthropic_provider(self, mock_get_config):
        """Test load config cho Anthropic provider."""
        mock_manager = MagicMock()
        mock_manager.get.side_effect = {
            "llm.provider": "anthropic",
            "llm.model": "claude-3-5-sonnet",
            "llm.api_url": "https://api.anthropic.com",
            "llm.api_key": "sk-ant-key",
            "llm.max_tokens": 8192,
            "llm.temperature": 0.3,
            "llm.timeout_seconds": 300,
            "llm.retry_attempts": 3,
        }.get
        mock_get_config.return_value = mock_manager

        config = load_llm_config(tier="analyze")
        
        assert config.provider == LlmProvider.ANTHROPIC
        assert config.model == "claude-3-5-sonnet"

    def test_load_config_missing_required_field(self):
        """Test lỗi khi thiếu required field."""
        mock_manager = MagicMock()
        mock_manager.get.return_value = None  # Missing all fields
        
        with patch("midicoder.pipeline.llm.client.get_config", return_value=mock_manager):
            with pytest.raises(MidicoderError) as exc_info:
                load_llm_config(tier="analyze")
            
            assert exc_info.value.code == ErrorCode.LLM_CONFIG_INVALID


# ============================================================================
# Tests cho call_llm
# ============================================================================

class TestCallLlm:
    """Tests cho call_llm function."""

    @patch("midicoder.pipeline.llm.client.urlopen")
    @patch("midicoder.pipeline.llm.client.Request")
    def test_call_llm_success_openai_format(self, mock_request, mock_urlopen):
        """Test call LLM thành công với OpenAI format."""
        # Mock response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "choices": [{
                "message": {
                    "content": "Đây là câu trả lời từ LLM"
                }
            }]
        }).encode("utf-8")
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        config = LlmConfig(
            provider=LlmProvider.OPENAI_COMPATIBLE,
            model="qwen3.5-27B",
            api_url="http://localhost:11434/v1",
        )

        response = call_llm(
            config=config,
            system="You are a helpful assistant",
            prompt="Hello!"
        )
        
        assert isinstance(response, LlmResponse)
        assert response.content == "Đây là câu trả lời từ LLM"
        assert "choices" in response.raw

    @patch("midicoder.pipeline.llm.client.urlopen")
    @patch("midicoder.pipeline.llm.client.Request")
    def test_call_llm_with_api_key(self, mock_request, mock_urlopen):
        """Test call LLM với API key."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "choices": [{"message": {"content": "Response"}}]
        }).encode("utf-8")
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        config = LlmConfig(
            provider=LlmProvider.OPENAI,
            model="gpt-4o",
            api_url="https://api.openai.com/v1",
            api_key="sk-test-key",
        )

        call_llm(config=config, prompt="Test")
        
        # Verify Authorization header
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert "Authorization" in call_args.kwargs.get("headers", {})
        assert call_args.kwargs["headers"]["Authorization"] == "Bearer sk-test-key"

    @patch("midicoder.pipeline.llm.client.urlopen")
    def test_call_llm_rate_limit_error(self, mock_urlopen):
        """Test xử lý rate limit error (429)."""
        from urllib.error import HTTPError
        from http.client import HTTPMessage
        
        # Create HTTPError properly for Python 3.13
        mock_error = HTTPError(
            url="http://test.com",
            code=429,
            msg="Too Many Requests",
            hdrs=HTTPMessage(),
            fp=None
        )
        # Set headers after creation
        mock_error.headers = {"Retry-After": "60"}
        mock_error.read = MagicMock(return_value=b'{"error": "rate limit exceeded"}')
        mock_urlopen.side_effect = mock_error

        config = LlmConfig(
            provider=LlmProvider.OPENAI,
            model="gpt-4o",
            api_url="https://api.openai.com/v1",
        )

        with pytest.raises(LlmRateLimitError) as exc_info:
            call_llm(config=config, prompt="Test")
        
        assert "rate limit" in str(exc_info.value).lower()

    @patch("midicoder.pipeline.llm.client.urlopen")
    def test_call_llm_auth_error(self, mock_urlopen):
        """Test xử lý authentication error (401)."""
        from urllib.error import HTTPError
        from http.client import HTTPMessage
        
        # Create HTTPError properly for Python 3.13
        mock_error = HTTPError(
            url="http://test.com",
            code=401,
            msg="Unauthorized",
            hdrs=HTTPMessage(),
            fp=None
        )
        mock_error.headers = {}
        mock_error.read = MagicMock(return_value=b'{"error": "invalid api key"}')
        mock_urlopen.side_effect = mock_error

        config = LlmConfig(
            provider=LlmProvider.OPENAI,
            model="gpt-4o",
            api_url="https://api.openai.com/v1",
        )

        with pytest.raises(LlmAuthError) as exc_info:
            call_llm(config=config, prompt="Test")
        
        assert "authentication" in str(exc_info.value).lower() or "401" in str(exc_info.value)

    @patch("midicoder.pipeline.llm.client.urlopen")
    def test_call_llm_timeout_error(self, mock_urlopen):
        """Test xử lý timeout error."""
        import socket
        
        mock_urlopen.side_effect = socket.timeout("Connection timed out")

        config = LlmConfig(
            provider=LlmProvider.OPENAI,
            model="gpt-4o",
            api_url="https://api.openai.com/v1",
        )

        with pytest.raises(LlmTimeoutError):
            call_llm(config=config, prompt="Test")

    @patch("midicoder.pipeline.llm.client.urlopen")
    def test_call_llm_retry_on_failure(self, mock_urlopen):
        """Test retry logic khi request fail."""
        from urllib.error import URLError
        
        # Fail twice, then succeed
        call_count = [0]
        
        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] < 3:
                raise URLError("Connection failed")
            mock_response = MagicMock()
            mock_response.read.return_value = json.dumps({
                "choices": [{"message": {"content": "Success after retry"}}]
            }).encode("utf-8")
            mock_response.__enter__ = MagicMock(return_value=mock_response)
            mock_response.__exit__ = MagicMock(return_value=False)
            return mock_response
        
        mock_urlopen.side_effect = side_effect

        config = LlmConfig(
            provider=LlmProvider.OPENAI_COMPATIBLE,
            model="test",
            api_url="http://test.com/v1",
            retry_attempts=3,
        )

        response = call_llm(config=config, prompt="Test")
        
        assert response.content == "Success after retry"
        assert call_count[0] == 3  # 2 failures + 1 success

    def test_call_llm_missing_messages(self):
        """Test lỗi khi không có system, context, hoặc prompt."""
        config = LlmConfig(
            provider=LlmProvider.OPENAI_COMPATIBLE,
            model="test",
            api_url="http://test.com/v1",
        )

        with pytest.raises(ValueError) as exc_info:
            call_llm(config=config)
        
        assert "requires at least one of system, context, or prompt" in str(exc_info.value)


# ============================================================================
# Tests cho LLM Error classes
# ============================================================================

class TestLlmErrors:
    """Tests cho LLM error classes."""

    def test_llm_request_error(self):
        """Test LlmRequestError."""
        error = LlmRequestError("Request failed", status_code=500)
        
        assert str(error) == "[LLM-001] LLM request thất bại: Request failed (status_code=500)"
        assert error.status_code == 500

    def test_llm_auth_error(self):
        """Test LlmAuthError."""
        error = LlmAuthError("Invalid API key")
        
        assert "authentication" in str(error).lower()
        assert error.code == ErrorCode.LLM_AUTH_FAILED

    def test_llm_rate_limit_error(self):
        """Test LlmRateLimitError."""
        error = LlmRateLimitError("Rate limit exceeded", retry_after=60)
        
        assert "rate limit" in str(error).lower()
        assert error.retry_after == 60

    def test_llm_timeout_error(self):
        """Test LlmTimeoutError."""
        error = LlmTimeoutError("Connection timed out", timeout=300)
        
        assert "timeout" in str(error).lower()
        assert error.timeout == 300