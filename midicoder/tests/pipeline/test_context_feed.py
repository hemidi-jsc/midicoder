"""
Tests cho Context Feed module.

Kiểm tra:
- calculate_adaptive_limit: Tính giới hạn context theo model
- get_brief_context: Query context cho brief analyze
- get_clarify_context: Query context cho brief clarify
- ContextFeedResult: Dataclass result

TDD: Tests được viết trước khi implement (nếu có thay đổi)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from midicoder.pipeline.context_feed import (
    ContextFeedResult,
    calculate_adaptive_limit,
    get_brief_context,
    get_clarify_context,
    format_context_inject,
    MODEL_CONTEXT_WINDOWS,
    CONTEXT_WINDOW_RATIO,
)
from midicoder.pipeline.indexer.query import ContextItem, Brief


class TestCalculateAdaptiveLimit:
    """Tests cho hàm calculate_adaptive_limit."""

    def test_default_model_returns_30_percent_of_8192(self):
        """Default model returns 30% of 8192 tokens."""
        result = calculate_adaptive_limit()
        expected = int(8192 * 0.30)  # 2457
        assert result == expected

    def test_gpt_4_returns_correct_limit(self):
        """GPT-4 model returns correct limit."""
        result = calculate_adaptive_limit("gpt-4")
        expected = int(8192 * 0.30)  # 2457
        assert result == expected

    def test_gpt_4_turbo_returns_correct_limit(self):
        """GPT-4-turbo model returns correct limit."""
        result = calculate_adaptive_limit("gpt-4-turbo")
        expected = int(128000 * 0.30)  # 38400
        assert result == expected

    def test_claude_3_sonnet_returns_correct_limit(self):
        """Claude-3-sonnet model returns correct limit."""
        result = calculate_adaptive_limit("claude-3-sonnet")
        expected = int(200000 * 0.30)  # 60000
        assert result == expected

    def test_unknown_model_falls_back_to_default(self):
        """Unknown model falls back to default."""
        result = calculate_adaptive_limit("unknown-model")
        expected = int(8192 * 0.30)  # 2457
        assert result == expected

    def test_model_name_case_insensitive(self):
        """Model name matching is case insensitive."""
        result_upper = calculate_adaptive_limit("GPT-4")
        result_lower = calculate_adaptive_limit("gpt-4")
        assert result_upper == result_lower

    def test_model_name_prefix_matching(self):
        """Model name with prefix matches base model."""
        result = calculate_adaptive_limit("gpt-4-0125-preview")
        expected = int(8192 * 0.30)  # Should match gpt-4
        assert result == expected


class TestCountTokens:
    """Tests cho hàm count_tokens (import từ llm module)."""

    def test_count_tokens_basic(self):
        """Test đếm tokens cơ bản."""
        from midicoder.pipeline.llm import count_tokens

        count = count_tokens("Hello world")
        assert count > 0

    def test_count_tokens_empty(self):
        """Test đếm tokens với text rỗng."""
        from midicoder.pipeline.llm import count_tokens

        count = count_tokens("")
        assert count == 0

    def test_count_tokens_longer_text(self):
        """Test đếm tokens với text dài."""
        from midicoder.pipeline.llm import count_tokens

        text = "This is a test sentence for token counting"
        count = count_tokens(text)
        assert count > 5  # Should be at least ~8 tokens


class TestContextFeedResult:
    """Tests cho ContextFeedResult dataclass."""

    def test_create_result_with_all_fields(self):
        """Create result with all fields."""
        items = [ContextItem(
            symbol_name="test",
            symbol_type="function",
            file_path="test.py",
            signature="def test():",
            description="Test function",
            content_snippet="def test(): pass",
            relevance_score=0.8,
        )]
        
        result = ContextFeedResult(
            context_items=items,
            formatted_context="Context",
            token_count=10,
            query_time_ms=100,
            warning=None,
        )
        
        assert len(result.context_items) == 1
        assert result.formatted_context == "Context"
        assert result.token_count == 10
        assert result.query_time_ms == 100
        assert result.warning is None

    def test_create_result_with_warning(self):
        """Create result with warning."""
        result = ContextFeedResult(
            context_items=[],
            formatted_context="",
            token_count=0,
            query_time_ms=50,
            warning="No context found",
        )
        
        assert result.warning == "No context found"


class TestGetBriefContext:
    """Tests cho hàm get_brief_context."""

    @patch("midicoder.pipeline.context_feed.get_relevant_context")
    def test_returns_context_items_when_db_exists(self, mock_query):
        """Returns context items when database exists."""
        # Mock context items
        mock_items = [ContextItem(
            symbol_name="UserService",
            symbol_type="class",
            file_path="auth/service.py",
            signature="class UserService:",
            description="Manages users",
            content_snippet="class UserService: pass",
            relevance_score=0.9,
        )]
        mock_query.return_value = mock_items
        
        # Mock _find_context_db
        with patch("midicoder.pipeline.context_feed._find_context_db", return_value="/tmp/context.db"):
            with patch("os.path.exists", return_value=True):
                result = get_brief_context(
                    brief_content="# Test Brief",
                    domain="ecommerce",
                    model_name="gpt-4",
                )
        
        assert isinstance(result, ContextFeedResult)
        assert len(result.context_items) == 1
        assert result.warning is None

    @patch("midicoder.pipeline.context_feed.get_relevant_context")
    def test_returns_warning_when_no_matches(self, mock_query):
        """Returns warning when no matches found."""
        mock_query.return_value = []
        
        with patch("midicoder.pipeline.context_feed._find_context_db", return_value="/tmp/context.db"):
            with patch("os.path.exists", return_value=True):
                result = get_brief_context(
                    brief_content="# Test Brief",
                    domain="ecommerce",
                )
        
        assert isinstance(result, ContextFeedResult)
        assert len(result.context_items) == 0
        assert result.warning is not None
        assert "không tìm thấy" in result.warning.lower()

    def test_returns_warning_when_db_not_found(self):
        """Returns warning when database not found."""
        with patch("midicoder.pipeline.context_feed._find_context_db", return_value=None):
            result = get_brief_context(
                brief_content="# Test Brief",
                domain="ecommerce",
            )
        
        assert isinstance(result, ContextFeedResult)
        assert len(result.context_items) == 0
        assert result.warning is not None
        assert "lỗi" in result.warning.lower()

    @patch("midicoder.pipeline.context_feed.get_relevant_context")
    def test_truncates_context_when_exceeds_limit(self, mock_query):
        """Truncates context when it exceeds adaptive limit."""
        # Create many context items that would exceed limit
        mock_items = [ContextItem(
            symbol_name=f"Function{i}",
            symbol_type="function",
            file_path=f"file{i}.py",
            signature=f"def function{i}():",
            description=f"Description for function {i} that is quite long",
            content_snippet=f"def function{i}():\n    pass\n",
            relevance_score=0.9 - (i * 0.05),  # Decreasing scores
        ) for i in range(20)]
        mock_query.return_value = mock_items
        
        with patch("midicoder.pipeline.context_feed._find_context_db", return_value="/tmp/context.db"):
            with patch("os.path.exists", return_value=True):
                # Use small model to force truncation
                result = get_brief_context(
                    brief_content="# Test Brief",
                    model_name="gpt-4",  # Small context window
                )
        
        # Should have truncated items
        assert isinstance(result, ContextFeedResult)
        assert result.token_count <= calculate_adaptive_limit("gpt-4")


class TestGetClarifyContext:
    """Tests cho hàm get_clarify_context."""

    @patch("midicoder.pipeline.context_feed.get_relevant_context")
    def test_returns_context_for_clarification(self, mock_query):
        """Returns context for clarification."""
        mock_items = [ContextItem(
            symbol_name="OrderService",
            symbol_type="class",
            file_path="orders/service.py",
            signature="class OrderService:",
            description="Manages orders",
            content_snippet="class OrderService: pass",
            relevance_score=0.85,
        )]
        mock_query.return_value = mock_items
        
        analysis_data = {
            "entities": [{"name": "Order"}, {"name": "Customer"}],
            "commands": [{"name": "create_order"}],
        }
        qa_history = [
            {"question": "What payment methods?", "answer": "Credit card, PayPal"}
        ]
        
        with patch("midicoder.pipeline.context_feed._find_context_db", return_value="/tmp/context.db"):
            with patch("os.path.exists", return_value=True):
                result = get_clarify_context(
                    analysis_data=analysis_data,
                    qa_history=qa_history,
                )
        
        assert isinstance(result, ContextFeedResult)
        assert len(result.context_items) == 1

    def test_empty_analysis_and_history(self):
        """Handles empty analysis and Q&A history."""
        with patch("midicoder.pipeline.context_feed._find_context_db", return_value=None):
            result = get_clarify_context(
                analysis_data={},
                qa_history=[],
            )
        
        assert isinstance(result, ContextFeedResult)
        assert result.warning is not None

    def test_extract_focus_from_qa_history(self):
        """Extracts focus from Q&A history."""
        analysis_data = {
            "entities": [{"name": "Product"}, {"name": "Category"}],
            "commands": [{"name": "add_product"}],
        }
        qa_history = [
            {"question": "How to handle inventory?", "answer": "Real-time tracking"}
        ]
        
        # This should not raise and should create focus text
        from midicoder.pipeline.context_feed import _extract_clarify_focus
        
        focus_text = _extract_clarify_focus(analysis_data, qa_history)
        
        assert "Product" in focus_text
        assert "add_product" in focus_text
        assert "inventory" in focus_text.lower()


class TestFormatContextInject:
    """Tests cho hàm format_context_inject."""

    def test_returns_formatted_context(self):
        """Returns formatted context."""
        result = ContextFeedResult(
            context_items=[],
            formatted_context="## Codebase Context\n\nTest",
            token_count=5,
            query_time_ms=10,
        )
        
        injected = format_context_inject(result)
        assert injected == "## Codebase Context\n\nTest"

    def test_returns_empty_string_for_empty_context(self):
        """Returns empty string for empty context."""
        result = ContextFeedResult(
            context_items=[],
            formatted_context="",
            token_count=0,
            query_time_ms=10,
        )
        
        injected = format_context_inject(result)
        assert injected == ""


class TestTruncateContextByTokens:
    """Tests cho hàm _truncate_context_by_tokens."""

    def test_truncates_by_relevance_score(self):
        """Truncates items with lowest relevance scores first."""
        from midicoder.pipeline.context_feed import _truncate_context_by_tokens
        
        items = [
            ContextItem(
                symbol_name=f"Func{i}",
                symbol_type="function",
                file_path="test.py",
                signature=f"def func{i}():",
                description=f"Desc {i}" * 10,  # Make it longer
                content_snippet=f"def func{i}(): pass",
                relevance_score=0.9 - (i * 0.1),  # Decreasing scores
            )
            for i in range(5)
        ]
        
        # Truncate to very small limit
        truncated = _truncate_context_by_tokens(items, max_tokens=10)
        
        # Should keep only highest scored items
        assert len(truncated) <= len(items)
        if truncated:
            # Highest score should be first
            assert truncated[0].relevance_score >= truncated[-1].relevance_score

    def test_empty_items_returns_empty(self):
        """Empty items returns empty list."""
        from midicoder.pipeline.context_feed import _truncate_context_by_tokens
        
        result = _truncate_context_by_tokens([], max_tokens=100)
        assert result == []


class TestIntegration:
    """Integration tests cho context feed flow."""

    def test_full_brief_context_flow(self):
        """Test full brief context flow."""
        with patch("midicoder.pipeline.context_feed.get_relevant_context") as mock_query:
            with patch("midicoder.pipeline.context_feed._find_context_db", return_value="/tmp/context.db"):
                with patch("os.path.exists", return_value=True):
                    # Setup mock
                    mock_query.return_value = []
                    
                    # Execute flow
                    result = get_brief_context(
                        brief_content="# E-commerce Platform\n\nBuild an online store.",
                        domain="ecommerce",
                        model_name="gpt-4",
                    )
                    
                    # Verify result structure
                    assert isinstance(result, ContextFeedResult)
                    assert hasattr(result, 'context_items')
                    assert hasattr(result, 'formatted_context')
                    assert hasattr(result, 'token_count')
                    assert hasattr(result, 'query_time_ms')
                    assert hasattr(result, 'warning')

    def test_full_clarify_context_flow(self):
        """Test full clarify context flow."""
        with patch("midicoder.pipeline.context_feed.get_relevant_context") as mock_query:
            with patch("midicoder.pipeline.context_feed._find_context_db", return_value="/tmp/context.db"):
                with patch("os.path.exists", return_value=True):
                    mock_query.return_value = []
                    
                    result = get_clarify_context(
                        analysis_data={"entities": [{"name": "Product"}]},
                        qa_history=[{"question": "Q?", "answer": "A"}],
                        model_name="gpt-4",
                    )
                    
                    assert isinstance(result, ContextFeedResult)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])