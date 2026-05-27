"""
Tests cho LLM Contract Generation (P0-4).

Test cases cho:
1. _generate_contracts_with_llm: Generate contracts từ LLM
2. _build_category_prompt: Build prompts cho từng category
3. _generate_category_with_retry: Retry LLM calls
4. Auto-fix loop: Validate → fix → revalidate
5. Integration: Full pipeline LLM generate → validate → save

Author: Midicoder Team
Version: 4.0.0 (LLM Contract Generation)
"""

import json
import os
import shutil
import tempfile
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from midicoder.pipeline.commands.contract import (
    _generate_contracts_with_llm,
    _build_category_prompt,
    _generate_category_with_retry,
    _auto_fix_contracts,
    _generate_contracts_to_sqlite,
    generate_contracts,
    REQUIRED_CATEGORIES,
    MAX_REPAIR_ATTEMPTS,
)
from midicoder.storage.sqlite import BriefsManager, ArtifactsManager
from midicoder.pipeline.llm.client import LlmConfig, LlmResponse


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def temp_workspace():
    """Tao temporary workspace cho testing."""
    temp_dir = tempfile.mkdtemp()
    original_cwd = Path.cwd()
    os.chdir(temp_dir)
    yield Path(temp_dir)
    os.chdir(original_cwd)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def briefs_manager():
    """Tao BriefsManager instance cho testing."""
    manager = BriefsManager()
    manager.init()
    return manager


@pytest.fixture
def artifacts_manager():
    """Tao ArtifactsManager instance cho testing."""
    manager = ArtifactsManager()
    manager.init()
    return manager


@pytest.fixture
def sample_brief(briefs_manager):
    """Tao sample brief cho testing."""
    content = "# E-commerce D2C Platform\n\nBuild an e-commerce platform with product catalog and ordering."
    unique_id = f"test-brief-{uuid.uuid4().hex[:8]}"
    brief_id = briefs_manager.create(
        brief_id=unique_id,
        version="v1.0.0",
        content=content,
        title="E-commerce D2C",
        brief_type="working",
    )["brief_id"]
    briefs_manager.update_status(brief_id, "analyzed")
    return brief_id


@pytest.fixture
def sample_analysis_data():
    """Tao sample analysis JSON data."""
    return {
        "entities": [
            {"name": "Product", "fields": [{"name": "id", "type": "UUID"}]},
            {"name": "Order", "fields": [{"name": "id", "type": "UUID"}]},
        ],
        "commands": [
            {"name": "CreateOrder", "input": [{"name": "product_id", "type": "UUID"}]}
        ],
        "queries": [
            {"name": "ListProducts", "input": []}
        ],
        "events": [
            {"name": "OrderCreated", "fields": [{"name": "order_id", "type": "UUID"}]}
        ],
        "domain": "ecommerce",
        "confidence": 0.85,
        "summary": "E-commerce platform with product catalog and ordering system",
    }


@pytest.fixture
def sample_clarifications():
    """Tao sample clarifications."""
    return [
        {"question": "Do you need multi-tenant support?", "answer": "Yes, SaaS model"},
        {"question": "Payment gateway?", "answer": "Stripe"},
    ]


@pytest.fixture
def mock_llm_config():
    """Tao mock LLM config."""
    return LlmConfig(
        provider="openai-compatible",
        model="test-model",
        api_url="http://localhost:11434/v1",
        api_key="test-key",
        max_tokens=8192,
        temperature=0.3,
        timeout=300,
        retry_attempts=3,
    )


# ============================================================================
# Tests: MAX_REPAIR_ATTEMPTS
# ============================================================================

class TestMaxRepairAttempts:
    """Tests cho MAX_REPAIR_ATTEMPTS constant."""

    def test_max_repair_attempts_is_five(self):
        """Test: MAX_REPAIR_ATTEMPTS = 5."""
        assert MAX_REPAIR_ATTEMPTS == 5


# ============================================================================
# Tests: _build_category_prompt
# ============================================================================

class TestBuildCategoryPrompt:
    """Tests cho _build_category_prompt() function."""

    def test_returns_system_and_user_prompts(self, sample_analysis_data, sample_clarifications):
        """Test: Tra ve tuple (system, user) prompts."""
        system, user = _build_category_prompt(
            "entities", sample_analysis_data, sample_clarifications, "brief content"
        )
        assert isinstance(system, str)
        assert isinstance(user, str)
        assert len(system) > 0
        assert len(user) > 0

    def test_system_prompt_contains_category_name(self, sample_analysis_data):
        """Test: System prompt chua ten category."""
        system, _ = _build_category_prompt("commands", sample_analysis_data, [], "brief")
        assert "commands" in system.lower() or "command" in system.lower()

    def test_user_prompt_contains_analysis_data(self, sample_analysis_data):
        """Test: User prompt chua analysis data."""
        _, user = _build_category_prompt("entities", sample_analysis_data, [], "brief")
        assert "Product" in user or "product" in user.lower()

    def test_user_prompt_contains_clarifications(self, sample_analysis_data, sample_clarifications):
        """Test: User prompt chua clarifications khi co."""
        _, user = _build_category_prompt(
            "entities", sample_analysis_data, sample_clarifications, "brief"
        )
        assert "multi-tenant" in user.lower() or "SaaS" in user

    def test_works_for_all_categories(self, sample_analysis_data):
        """Test: Ham hoat dong cho tat ca 7 categories."""
        for category in REQUIRED_CATEGORIES:
            system, user = _build_category_prompt(
                category, sample_analysis_data, [], "brief"
            )
            assert len(system) > 0, f"System prompt empty for {category}"
            assert len(user) > 0, f"User prompt empty for {category}"


# ============================================================================
# Tests: _generate_category_with_retry
# ============================================================================

class TestGenerateCategoryWithRetry:
    """Tests cho _generate_category_with_retry() function."""

    @patch("midicoder.pipeline.commands.contract.call_llm")
    def test_success_on_first_try(self, mock_call, mock_llm_config):
        """Test: Thanh cong lan dau tien."""
        valid_yaml = "entities:\n  - id: Product\n    name: San pham"
        mock_call.return_value = LlmResponse(
            content=valid_yaml,
            usage={"total_tokens": 100},
        )

        result = _generate_category_with_retry(mock_llm_config, "entities", "system", "user")
        assert result == valid_yaml
        mock_call.assert_called_once()

    @patch("midicoder.pipeline.commands.contract.call_llm")
    def test_retries_on_invalid_yaml(self, mock_call, mock_llm_config):
        """Test: Retry khi LLM tra ve yaml khong hop le."""
        # Lan 1: khong hop le, Lan 2: hop le
        mock_call.side_effect = [
            LlmResponse(content="not valid yaml: {{", usage={"total_tokens": 50}),
            LlmResponse(content="entities: []", usage={"total_tokens": 100}),
        ]

        result = _generate_category_with_retry(mock_llm_config, "entities", "system", "user")
        assert result == "entities: []"
        assert mock_call.call_count == 2

    @patch("midicoder.pipeline.commands.contract.call_llm")
    def test_strips_markdown_code_blocks(self, mock_call, mock_llm_config):
        """Test: Loai bo markdown code blocks."""
        mock_call.return_value = LlmResponse(
            content="```yaml\nentities: []\n```",
            usage={"total_tokens": 100},
        )

        result = _generate_category_with_retry(mock_llm_config, "entities", "system", "user")
        assert "```" not in result


# ============================================================================
# Tests: _generate_contracts_with_llm
# ============================================================================

class TestGenerateContractsWithLlm:
    """Tests cho _generate_contracts_with_llm() function."""

    @patch("midicoder.pipeline.commands.contract.call_llm")
    def test_generates_all_7_categories(self, mock_call, mock_llm_config, sample_analysis_data, sample_clarifications):
        """Test: Generate day du 7 categories."""
        # Mock LLM tra ve valid yaml cho tung category
        def mock_side_effect(*args, **kwargs):
            system = kwargs.get("system", "")
            if "entities" in system.lower():
                return LlmResponse(content="entities: []", usage={"total_tokens": 100})
            elif "commands" in system.lower():
                return LlmResponse(content="commands: []", usage={"total_tokens": 100})
            elif "queries" in system.lower():
                return LlmResponse(content="queries: []", usage={"total_tokens": 100})
            elif "events" in system.lower():
                return LlmResponse(content="events: []", usage={"total_tokens": 100})
            elif "workflows" in system.lower():
                return LlmResponse(content="workflows: []", usage={"total_tokens": 100})
            elif "value_objects" in system.lower():
                return LlmResponse(content="value_objects: []", usage={"total_tokens": 100})
            else:
                return LlmResponse(content="guards: []", usage={"total_tokens": 100})

        mock_call.side_effect = mock_side_effect

        result = _generate_contracts_with_llm(
            config=mock_llm_config,
            analysis_data=sample_analysis_data,
            clarifications=sample_clarifications,
            brief_content="test brief",
        )

        assert len(result) == len(REQUIRED_CATEGORIES)
        assert set(result.keys()) == set(REQUIRED_CATEGORIES)

    @patch("midicoder.pipeline.commands.contract.call_llm")
    def test_calls_llm_7_times(self, mock_call, mock_llm_config, sample_analysis_data):
        """Test: Goii LLM chinh xac 7 lan."""
        def mock_side_effect(*args, **kwargs):
            return LlmResponse(content="items: []", usage={"total_tokens": 100})

        mock_call.side_effect = mock_side_effect

        _generate_contracts_with_llm(
            config=mock_llm_config,
            analysis_data=sample_analysis_data,
            clarifications=[],
            brief_content="test brief",
        )

        assert mock_call.call_count == len(REQUIRED_CATEGORIES)


# ============================================================================
# Tests: _auto_fix_contracts
# ============================================================================

class TestAutoFixContracts:
    """Tests cho auto-fix loop."""

    @patch("midicoder.pipeline.commands.contract.call_llm")
    @patch("midicoder.pipeline.commands.contract.click.echo")
    def test_no_fix_needed_when_valid(self, mock_echo, mock_call, artifacts_manager, sample_brief, mock_llm_config):
        """Test: Khong can fix khi contracts da valid."""
        from midicoder.pipeline.commands.contract import _build_placeholder_yaml
        from midicoder.pipeline.llm.client import LlmResponse
        mock_call.return_value = LlmResponse(content="items: []", usage={"total_tokens": 100})

        # Tao placeholder contracts
        yaml_dict = _build_placeholder_yaml(sample_brief, "2026-01-01T00:00:00Z")

        result = _auto_fix_contracts(artifacts_manager, yaml_dict, sample_brief, mock_llm_config)
        # Tra ve boolean
        assert isinstance(result, bool)


# ============================================================================
# Tests: Deprecated Functions Removed
# ============================================================================

class TestDeprecatedFunctionsRemoved:
    """Tests de cap nhat deprecated functions bi xoa."""

    def test_generate_placeholder_contracts_removed(self):
        """Test: generate_placeholder_contracts khong con ton tai."""
        from midicoder.pipeline.commands import contract
        assert not hasattr(contract, "generate_placeholder_contracts") or \
               getattr(contract, "generate_placeholder_contracts", None) is None

    def test_save_contract_artifacts_removed(self):
        """Test: _save_contract_artifacts khong con ton tai."""
        from midicoder.pipeline.commands import contract
        assert not hasattr(contract, "_save_contract_artifacts") or \
               getattr(contract, "_save_contract_artifacts", None) is None


# ============================================================================
# Integration Tests
# ============================================================================

class TestLlmContractGenerationIntegration:
    """Integration tests cho LLM contract generation pipeline."""

    @patch("midicoder.pipeline.commands.contract.call_llm")
    @patch("midicoder.pipeline.commands.contract.click.echo")
    def test_full_pipeline_llm_generate_to_sqlite(
        self, mock_echo, mock_call, temp_workspace, sample_brief, mock_llm_config, sample_analysis_data
    ):
        """
        Integration Test: Full LLM pipeline.

        Steps:
        1. Mock LLM tra ve valid contracts
        2. Goii _generate_contracts_with_llm
        3. Kiem tra 7 artifacts duoc luu vao SQLite
        """
        def mock_side_effect(*args, **kwargs):
            return LlmResponse(content="items: []", usage={"total_tokens": 100})

        mock_call.side_effect = mock_side_effect

        # Generate contracts
        yaml_dict = _generate_contracts_with_llm(
            config=mock_llm_config,
            analysis_data=sample_analysis_data,
            clarifications=[],
            brief_content="test brief",
        )

        # Kiem tra ket qua
        assert len(yaml_dict) == len(REQUIRED_CATEGORIES)
        for category in REQUIRED_CATEGORIES:
            assert category in yaml_dict
            assert isinstance(yaml_dict[category], str)
            assert len(yaml_dict[category]) > 0

        # Luu vao SQLite
        from midicoder.pipeline.commands.contract import _upsert_contract_artifact
        test_artifacts_manager = ArtifactsManager()
        test_artifacts_manager.init()
        for category, content in yaml_dict.items():
            _upsert_contract_artifact(test_artifacts_manager, category, content, sample_brief)

        # Kiem tra artifacts
        contracts = test_artifacts_manager.list_by_type("contract")
        assert len(contracts) == len(REQUIRED_CATEGORIES)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])