"""
Tests cho LLM Client module (REBUILD với litellm).

E20: CLI Commands - LLM Client Integration
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from litellm import APIError, RateLimitError, AuthenticationError

from midicoder.pipeline.llm import (
    LlmConfig,
    LlmResponse,
    LlmStreamChunk,
    load_llm_config,
    call_llm,
    call_llm_async,
    call_llm_stream,
)


# ============================================================================
# Tests cho LlmConfig
# ============================================================================

class TestLlmConfig:
    """Tests cho LlmConfig dataclass."""

    def test_create_config_with_defaults(self):
        """Test tạo config với giá trị mặc định."""
        config = LlmConfig(
            provider="openai-compatible",
            model="qwen3.5-27B",
            api_url="http://localhost:11434/v1",
        )
        
        assert config.provider == "openai-compatible"
        assert config.model == "qwen3.5-27B"
        assert config.api_url == "http://localhost:11434/v1"
        assert config.api_key is None
        assert config.max_tokens == 8192
        assert config.temperature == 0.3
        assert config.timeout == 300
        assert config.retry_attempts == 3

    def test_create_config_with_custom_values(self):
        """Test tạo config với giá trị custom."""
        config = LlmConfig(
            provider="anthropic",
            model="claude-3-sonnet",
            api_url="https://api.anthropic.com",
            api_key="sk-ant-key",
            max_tokens=4096,
            temperature=0.7,
            timeout=120,
            retry_attempts=5,
        )
        
        assert config.provider == "anthropic"
        assert config.model == "claude-3-sonnet"
        assert config.api_key == "sk-ant-key"
        assert config.max_tokens == 4096
        assert config.temperature == 0.7
        assert config.timeout == 120
        assert config.retry_attempts == 5


# ============================================================================
# Tests cho load_llm_config
# ============================================================================

class TestLoadLlmConfig:
    """Tests cho load_llm_config function."""

    @patch("midicoder.pipeline.llm.client.get_config")
    def test_load_config_success(self, mock_get_config):
        """Test load config thành công."""
        # Mock config manager
        mock_manager = MagicMock()
        mock_manager.get.side_effect = {
            "llm.provider": "openai-compatible",
            "llm.model": "qwen3.5-27B",
            "llm.api_url": "http://localhost:11434/v1",
            "llm.api_key": "test-key",
            "llm.max_tokens": 8192,
            "llm.temperature": 0.3,
            "llm.timeout": 300,
            "llm.retry_attempts": 3,
        }.get
        mock_get_config.return_value = mock_manager

        config = load_llm_config()
        
        assert config.provider == "openai-compatible"
        assert config.model == "qwen3.5-27B"
        assert config.api_url == "http://localhost:11434/v1"
        assert config.api_key == "test-key"

    @patch("midicoder.pipeline.llm.client.get_config")
    def test_load_config_with_defaults(self, mock_get_config):
        """Test load config áp dụng defaults."""
        mock_manager = MagicMock()
        mock_manager.get.side_effect = {
            "llm.provider": "openai",
            "llm.model": "gpt-4o",
            "llm.api_url": "https://api.openai.com/v1",
            "llm.api_key": None,
            "llm.max_tokens": None,  # Should use default
            "llm.temperature": None,  # Should use default
            "llm.timeout": None,  # Should use default
            "llm.retry_attempts": None,  # Should use default
        }.get
        mock_get_config.return_value = mock_manager

        config = load_llm_config()
        
        assert config.max_tokens == 8192  # Default
        assert config.temperature == 0.3  # Default
        assert config.timeout == 300  # Default
        assert config.retry_attempts == 3  # Default

    @patch("midicoder.pipeline.llm.client.get_config")
    def test_load_config_missing_required_field(self, mock_get_config):
        """Test lỗi khi thiếu required field."""
        mock_manager = MagicMock()
        mock_manager.get.return_value = None  # Missing all fields
        
        mock_get_config.return_value = mock_manager

        with pytest.raises(ValueError) as exc_info:
            load_llm_config()
        
        assert "model" in str(exc_info.value).lower() or "api_url" in str(exc_info.value).lower()

    @patch("midicoder.pipeline.llm.client.get_config")
    def test_load_config_invalid_provider(self, mock_get_config):
        """Test lỗi khi provider không hợp lệ."""
        mock_manager = MagicMock()
        mock_manager.get.side_effect = {
            "llm.provider": "invalid-provider",
            "llm.model": "gpt-4o",
            "llm.api_url": "https://api.openai.com/v1",
            "llm.api_key": "test",
            "llm.max_tokens": 8192,
            "llm.temperature": 0.3,
            "llm.timeout": 300,
            "llm.retry_attempts": 3,
        }.get
        mock_get_config.return_value = mock_manager

        with pytest.raises(ValueError) as exc_info:
            load_llm_config()
        
        assert "provider" in str(exc_info.value).lower()


# ============================================================================
# Tests cho call_llm (sync)
# ============================================================================

class TestCallLlm:
    """Tests cho call_llm function (sync)."""

    @patch("midicoder.pipeline.llm.client.litellm.completion")
    def test_call_llm_success(self, mock_completion):
        """Test call LLM sync thành công."""
        # Mock litellm response (object format)
        mock_message = MagicMock()
        mock_message.content = "Hello from LLM"
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = MagicMock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 20
        mock_response.usage.total_tokens = 30
        mock_completion.return_value = mock_response

        config = LlmConfig(
            provider="openai-compatible",
            model="qwen3.5-27B",
            api_url="http://localhost:11434/v1",
        )

        response = call_llm(
            config=config,
            system="You are a helpful assistant",
            messages=[{"role": "user", "content": "Hello!"}]
        )
        
        assert isinstance(response, LlmResponse)
        assert response.content == "Hello from LLM"
        assert response.usage["total_tokens"] == 30

    @patch("midicoder.pipeline.llm.client.litellm.completion")
    def test_call_llm_with_api_key(self, mock_completion):
        """Test call LLM với API key."""
        mock_message = MagicMock()
        mock_message.content = "Response"
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = MagicMock()
        mock_response.usage.prompt_tokens = 5
        mock_response.usage.completion_tokens = 10
        mock_response.usage.total_tokens = 15
        mock_completion.return_value = mock_response

        config = LlmConfig(
            provider="openai",
            model="gpt-4o",
            api_url="https://api.openai.com/v1",
            api_key="sk-test-key",
        )

        call_llm(config=config, messages=[{"role": "user", "content": "Test"}])
        
        # Verify API key passed to litellm
        mock_completion.assert_called_once()
        call_kwargs = mock_completion.call_args.kwargs
        assert call_kwargs.get("api_key") == "sk-test-key"

    @patch("midicoder.pipeline.llm.client.litellm.completion")
    def test_call_llm_litellm_api_error(self, mock_completion):
        """Test xử lý litellm APIError."""
        # litellm APIError với params đúng
        mock_completion.side_effect = APIError(
            message="API error",
            status_code=500,
            llm_provider="openai",
            model="gpt-4o",
        )

        config = LlmConfig(
            provider="openai",
            model="gpt-4o",
            api_url="https://api.openai.com/v1",
        )

        with pytest.raises(APIError):
            call_llm(config=config, messages=[{"role": "user", "content": "Test"}])

    @patch("midicoder.pipeline.llm.client.litellm.completion")
    def test_call_llm_litellm_rate_limit_error(self, mock_completion):
        """Test xử lý litellm RateLimitError."""
        mock_completion.side_effect = RateLimitError(
            message="Rate limit exceeded",
            llm_provider="openai",
            model="gpt-4o",
        )

        config = LlmConfig(
            provider="openai",
            model="gpt-4o",
            api_url="https://api.openai.com/v1",
        )

        with pytest.raises(RateLimitError):
            call_llm(config=config, messages=[{"role": "user", "content": "Test"}])

    @patch("midicoder.pipeline.llm.client.litellm.completion")
    def test_call_llm_litellm_auth_error(self, mock_completion):
        """Test xử lý litellm AuthenticationError."""
        mock_completion.side_effect = AuthenticationError(
            message="Invalid API key",
            llm_provider="openai",
            model="gpt-4o",
        )

        config = LlmConfig(
            provider="openai",
            model="gpt-4o",
            api_url="https://api.openai.com/v1",
            api_key="invalid-key",
        )

        with pytest.raises(AuthenticationError):
            call_llm(config=config, messages=[{"role": "user", "content": "Test"}])


# ============================================================================
# Tests cho call_llm_async
# ============================================================================

class TestCallLlmAsync:
    """Tests cho call_llm_async function."""

    @pytest.mark.asyncio
    @patch("midicoder.pipeline.llm.client.litellm.acompletion")
    async def test_call_llm_async_success(self, mock_acompletion):
        """Test call LLM async thành công."""
        # Mock litellm async response (object format)
        mock_message = MagicMock()
        mock_message.content = "Async response"
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = MagicMock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 20
        mock_response.usage.total_tokens = 30
        mock_acompletion.return_value = mock_response

        config = LlmConfig(
            provider="openai-compatible",
            model="qwen3.5-27B",
            api_url="http://localhost:11434/v1",
        )

        response = await call_llm_async(
            config=config,
            system="You are helpful",
            messages=[{"role": "user", "content": "Hello!"}]
        )
        
        assert isinstance(response, LlmResponse)
        assert response.content == "Async response"
        assert response.usage["total_tokens"] == 30

    @pytest.mark.asyncio
    @patch("midicoder.pipeline.llm.client.litellm.acompletion")
    async def test_call_llm_async_error(self, mock_acompletion):
        """Test call LLM async với error."""
        mock_acompletion.side_effect = APIError(
            message="Async error",
            status_code=500,
            llm_provider="openai",
            model="gpt-4o",
        )

        config = LlmConfig(
            provider="openai",
            model="gpt-4o",
            api_url="https://api.openai.com/v1",
        )

        with pytest.raises(APIError):
            await call_llm_async(config=config, messages=[{"role": "user", "content": "Test"}])


# ============================================================================
# Tests cho call_llm_stream
# ============================================================================

class TestCallLlmStream:
    """Tests cho call_llm_stream function."""

    @pytest.mark.asyncio
    @patch("midicoder.pipeline.llm.client.litellm.acompletion")
    async def test_call_llm_stream_success(self, mock_acompletion):
        """Test streaming LLM response."""
        # Mock async generator for litellm stream (object format)
        async def mock_stream():
            # Chunk 1
            mock_delta1 = MagicMock()
            mock_delta1.content = "Hello"
            mock_choice1 = MagicMock()
            mock_choice1.delta = mock_delta1
            mock_chunk1 = MagicMock()
            mock_chunk1.choices = [mock_choice1]
            yield mock_chunk1
            
            # Chunk 2
            mock_delta2 = MagicMock()
            mock_delta2.content = " world"
            mock_choice2 = MagicMock()
            mock_choice2.delta = mock_delta2
            mock_chunk2 = MagicMock()
            mock_chunk2.choices = [mock_choice2]
            yield mock_chunk2
            
            # Chunk 3 (with usage)
            mock_delta3 = MagicMock()
            mock_delta3.content = "!"
            mock_choice3 = MagicMock()
            mock_choice3.delta = mock_delta3
            mock_usage = MagicMock()
            mock_usage.prompt_tokens = 5
            mock_usage.completion_tokens = 10
            mock_usage.total_tokens = 15
            mock_chunk3 = MagicMock()
            mock_chunk3.choices = [mock_choice3]
            mock_chunk3.usage = mock_usage
            yield mock_chunk3
        
        mock_acompletion.return_value = mock_stream()

        config = LlmConfig(
            provider="openai-compatible",
            model="qwen3.5-27B",
            api_url="http://localhost:11434/v1",
        )

        chunks = []
        async for chunk in call_llm_stream(
            config=config,
            messages=[{"role": "user", "content": "Hello!"}]
        ):
            chunks.append(chunk)
        
        assert len(chunks) == 3
        assert chunks[0].content == "Hello"
        assert chunks[1].content == " world"
        assert chunks[2].content == "!"
        assert chunks[2].usage["total_tokens"] == 15  # Last chunk has usage

    @pytest.mark.asyncio
    @patch("midicoder.pipeline.llm.client.litellm.acompletion")
    async def test_call_llm_stream_empty_content(self, mock_acompletion):
        """Test streaming với empty content chunks."""
        async def mock_stream():
            # Empty chunk
            mock_delta1 = MagicMock()
            mock_delta1.content = ""
            mock_choice1 = MagicMock()
            mock_choice1.delta = mock_delta1
            mock_chunk1 = MagicMock()
            mock_chunk1.choices = [mock_choice1]
            yield mock_chunk1
            
            # Content chunk
            mock_delta2 = MagicMock()
            mock_delta2.content = "Content"
            mock_choice2 = MagicMock()
            mock_choice2.delta = mock_delta2
            mock_chunk2 = MagicMock()
            mock_chunk2.choices = [mock_choice2]
            yield mock_chunk2
        
        mock_acompletion.return_value = mock_stream()

        config = LlmConfig(
            provider="openai-compatible",
            model="test",
            api_url="http://test.com/v1",
        )

        chunks = []
        async for chunk in call_llm_stream(
            config=config,
            messages=[{"role": "user", "content": "Test"}]
        ):
            chunks.append(chunk)
        
        assert len(chunks) == 2
        assert chunks[0].content == ""  # Empty chunk
        assert chunks[1].content == "Content"


# ============================================================================
# Tests cho Logging
# ============================================================================

class TestLogging:
    """Tests cho logging functionality."""

    @patch("midicoder.pipeline.llm.client.litellm.completion")
    @patch("midicoder.pipeline.llm.client.logger")
    def test_logging_metadata_only(self, mock_logger, mock_completion):
        """Test logging chỉ log metadata, không log content."""
        # Mock response với object format
        mock_message = MagicMock()
        mock_message.content = "Secret response"
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = MagicMock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 20
        mock_response.usage.total_tokens = 30
        mock_completion.return_value = mock_response

        config = LlmConfig(
            provider="openai",
            model="gpt-4o",
            api_url="https://api.openai.com/v1",
        )

        call_llm(
            config=config,
            system="System prompt",
            messages=[{"role": "user", "content": "Secret prompt"}]
        )
        
        # Verify logging was called
        assert mock_logger.info.called
        
        # Get log call args
        log_call = mock_logger.info.call_args
        
        # Verify metadata is logged (in kwargs extra)
        log_kwargs = log_call.kwargs if log_call.kwargs else {}
        extra = log_kwargs.get("extra", {})
        assert extra.get("provider") == "openai"
        assert extra.get("model") == "gpt-4o"
        
        # Verify content is NOT logged
        log_str = str(log_call)
        assert "Secret response" not in log_str
        assert "Secret prompt" not in log_str
