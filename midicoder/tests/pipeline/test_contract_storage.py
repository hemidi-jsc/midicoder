"""
Tests cho Contract Storage Bridge — SQLite-Only Architecture.

Verify pipeline: contract gen → save artifacts → ir build

Tất cả contract artifacts được lưu vào SQLite (ArtifactsManager).
Không sử dụng filesystem để lưu contracts.

Author: Midicoder Team
Version: 3.0.0 (Refactored: SQLite-only architecture)
"""
import os
import shutil
import tempfile
import uuid
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from midicoder.pipeline.commands.contract import (
    _generate_contracts_to_sqlite,
    _load_contracts_from_sqlite,
    _upsert_contract_artifact,
    REQUIRED_CATEGORIES,
)
from midicoder.storage.sqlite import ArtifactsManager


@pytest.fixture
def artifacts_manager():
    """Tạo ArtifactsManager instance cho testing."""
    manager = ArtifactsManager()
    manager.init()
    return manager


class TestContractStorageBridge:
    """Tests cho bridge giữa contract gen và ir build."""

    def test_save_all_7_categories(self, artifacts_manager):
        """Test: Lưu đủ 7 contract artifacts vào SQLite."""
        brief_id = f"test-brief-{uuid.uuid4().hex[:8]}"
        _generate_contracts_to_sqlite(brief_id)

        artifacts = artifacts_manager.list_by_type("contract")
        assert len(artifacts) == 7
        artifact_ids = {a["artifact_id"] for a in artifacts}
        expected = {
            "contract_entities", "contract_commands", "contract_queries",
            "contract_events", "contract_workflows", "contract_value_objects",
            "contract_guards"
        }
        assert artifact_ids == expected

    def test_artifacts_have_correct_metadata(self, artifacts_manager):
        """Test: Metadata của artifacts đúng format."""
        brief_id = f"test-brief-{uuid.uuid4().hex[:8]}"
        _generate_contracts_to_sqlite(brief_id)

        artifact = artifacts_manager.get("contract_entities")
        assert artifact is not None
        assert artifact["type"] == "contract"
        assert artifact["name"] == "Contract: entities"
        assert artifact["version"] == "1.0.0"
        # brief_id matches either the new one or was updated
        assert artifact["brief_id"] is not None

    def test_artifacts_have_content(self, artifacts_manager):
        """Test: Content của artifacts không rỗng."""
        brief_id = f"test-brief-{uuid.uuid4().hex[:8]}"
        _generate_contracts_to_sqlite(brief_id)

        for category in ["entities", "commands", "queries", "events"]:
            artifact = artifacts_manager.get(f"contract_{category}")
            assert artifact is not None
            assert artifact["content"] is not None
            assert len(artifact["content"]) > 0
            # Verify content is valid YAML
            data = yaml.safe_load(artifact["content"])
            assert category in data


class TestContractGenToIrBuildFlow:
    """Integration tests cho flow contract gen → ir build."""

    def test_artifacts_are_consistent(self, artifacts_manager):
        """Test: Content trong SQLite khớp với expected YAML."""
        brief_id = f"test-brief-{uuid.uuid4().hex[:8]}"
        _generate_contracts_to_sqlite(brief_id)

        for category in ["entities", "commands", "queries", "events"]:
            artifact = artifacts_manager.get(f"contract_{category}")
            assert artifact is not None
            data = yaml.safe_load(artifact["content"])
            assert "meta" in data
            assert data["meta"]["brief_id"] == brief_id

    def test_load_contracts_from_sqlite(self, artifacts_manager):
        """Test: _load_contracts_from_sqlite trả về ProjectionTree."""
        brief_id = f"test-brief-{uuid.uuid4().hex[:8]}"
        _generate_contracts_to_sqlite(brief_id)

        tree = _load_contracts_from_sqlite()
        assert tree is not None
        assert tree.node_count() > 0


class TestIrBuildCanReadContracts:
    """Verify ir build có thể đọc contract artifacts."""

    def test_list_by_type_returns_contracts(self, artifacts_manager):
        """Test: list_by_type('contract') trả về đúng artifacts."""
        brief_id = f"test-brief-{uuid.uuid4().hex[:8]}"
        _generate_contracts_to_sqlite(brief_id)

        contracts = artifacts_manager.list_by_type("contract")
        assert len(contracts) == 7
        for contract in contracts:
            assert contract["type"] == "contract"
            assert contract["artifact_id"].startswith("contract_")

    def test_contract_format_matches_ir_expectations(self, artifacts_manager):
        """Test: Format artifact khớp với expectation của ir.py."""
        brief_id = f"test-brief-{uuid.uuid4().hex[:8]}"
        _generate_contracts_to_sqlite(brief_id)

        contracts = artifacts_manager.list_by_type("contract")

        # ir.py expects artifact_id format "contract_<category>"
        categories_found = set()
        for contract in contracts:
            artifact_id = contract.get("artifact_id", "")
            if artifact_id.startswith("contract_"):
                category = artifact_id[len("contract_"):]
                categories_found.add(category)

        required_categories = {
            "entities", "commands", "queries", "events",
            "workflows", "value_objects", "guards"
        }
        assert categories_found == required_categories

    def test_idempotent_generate(self, artifacts_manager):
        """Test: Chạy generate 2 lần không crash."""
        brief_id = f"test-brief-{uuid.uuid4().hex[:8]}"
        _generate_contracts_to_sqlite(brief_id)
        _generate_contracts_to_sqlite(brief_id)

        contracts = artifacts_manager.list_by_type("contract")
        assert len(contracts) == 7


if __name__ == "__main__":
    pytest.main([__file__, "-v"])