"""
Tests cho ArtifactsManager.

E09: SQLite Persistence - Artifacts
Activity log tests moved to test_activity.py (uses storage/activity.py shared module).
"""

import pytest
import tempfile
import shutil
import json
from pathlib import Path
from midicoder.storage.sqlite import (
    ArtifactsManager,
    SCHEMA_ARTIFACTS,
    SCHEMA_ACTIVITY,
)


class TestArtifactsManager:
    """Tests cho ArtifactsManager class."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """
        Setup trước mỗi test - tạo temp database.
        """
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_artifacts.db"
        self.manager = ArtifactsManager(self.db_path)
        self.manager.init()
        yield
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init_creates_tables(self):
        """
        Test: init() tạo đúng tables artifacts.
        
        Verification: artifacts table tồn tại sau khi init.
        """
        with self.manager._get_connection() as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = {row[0] for row in cursor.fetchall()}
            
            assert "artifacts" in tables

    def test_create_artifact_success(self):
        """
        Test: create() tạo artifact mới thành công.
        
        Verification: Artifact được lưu vào DB với đúng thông tin.
        """
        result = self.manager.create(
            artifact_id="artifact-001",
            artifact_type="contract",
            name="Test Contract",
            version="v1.0.0",
            brief_id="brief-001",
            content_path="/path/to/contract.yaml"
        )
        
        assert result["artifact_id"] == "artifact-001"
        assert result["type"] == "contract"
        assert result["name"] == "Test Contract"
        assert result["version"] == "v1.0.0"
        assert "id" in result

    def test_create_artifact_without_brief(self):
        """
        Test: Tạo artifact không có brief_id (optional).
        
        Verification: brief_id là NULL trong DB.
        """
        result = self.manager.create(
            artifact_id="no-brief-001",
            artifact_type="plan",
            name="Stand-alone Plan",
            version="v1.0.0"
        )
        
        assert result["artifact_id"] == "no-brief-001"
        
        # Verify brief_id is None
        with self.manager._get_connection() as conn:
            cursor = conn.execute(
                "SELECT brief_id FROM artifacts WHERE artifact_id = ?",
                ("no-brief-001",)
            )
            row = cursor.fetchone()
            assert row["brief_id"] is None

    def test_create_artifact_unique_constraint(self):
        """
        Test: Không thể tạo 2 artifacts với cùng artifact_id.
        
        Verification: Lỗi integrity error khi duplicate.
        """
        self.manager.create(
            artifact_id="duplicate-001",
            artifact_type="contract",
            name="First",
            version="v1.0.0"
        )
        
        with pytest.raises(Exception):
            self.manager.create(
                artifact_id="duplicate-001",
                artifact_type="contract",
                name="Second",
                version="v1.0.0"
            )

    def test_list_artifacts_all(self):
        """
        Test: list() trả về tất cả artifacts.
        
        Verification: Số lượng artifacts trả về bằng số lượng đã tạo.
        """
        # Create multiple artifacts
        for i in range(3):
            self.manager.create(
                artifact_id=f"artifact-{i}",
                artifact_type="contract",
                name=f"Contract {i}",
                version="v1.0.0"
            )
        
        results = self.manager.list()
        
        assert len(results) == 3

    def test_list_artifacts_by_type(self):
        """
        Test: list() với artifact_type filter.
        
        Verification: Chỉ trả về artifacts đúng type.
        """
        # Create different types
        self.manager.create(
            artifact_id="contract-001",
            artifact_type="contract",
            name="Contract 1",
            version="v1.0.0"
        )
        self.manager.create(
            artifact_id="mir-001",
            artifact_type="mir",
            name="MIR 1",
            version="v1.0.0"
        )
        self.manager.create(
            artifact_id="contract-002",
            artifact_type="contract",
            name="Contract 2",
            version="v1.0.0"
        )
        
        results = self.manager.list(artifact_type="contract")
        
        assert len(results) == 2
        for artifact in results:
            assert artifact["type"] == "contract"

    def test_list_artifacts_by_brief(self):
        """
        Test: list() với brief_id filter.
        
        Verification: Chỉ trả về artifacts thuộc brief đó.
        """
        # Create artifacts for different briefs
        self.manager.create(
            artifact_id="brief1-001",
            artifact_type="contract",
            name="Contract 1",
            version="v1.0.0",
            brief_id="brief-a"
        )
        self.manager.create(
            artifact_id="brief2-001",
            artifact_type="contract",
            name="Contract 2",
            version="v1.0.0",
            brief_id="brief-b"
        )
        self.manager.create(
            artifact_id="brief1-002",
            artifact_type="mir",
            name="MIR 1",
            version="v1.0.0",
            brief_id="brief-a"
        )
        
        results = self.manager.list(brief_id="brief-a")
        
        assert len(results) == 2
        for artifact in results:
            assert artifact["brief_id"] == "brief-a"

    def test_list_artifacts_combined_filter(self):
        """
        Test: list() với cả artifact_type và brief_id filter.
        
        Verification: Trả về artifacts khớp cả 2 điều kiện.
        """
        self.manager.create(
            artifact_id="a1",
            artifact_type="contract",
            name="C1",
            version="v1.0.0",
            brief_id="brief-a"
        )
        self.manager.create(
            artifact_id="a2",
            artifact_type="contract",
            name="C2",
            version="v1.0.0",
            brief_id="brief-b"
        )
        self.manager.create(
            artifact_id="a3",
            artifact_type="mir",
            name="M1",
            version="v1.0.0",
            brief_id="brief-a"
        )
        
        results = self.manager.list(artifact_type="contract", brief_id="brief-a")
        
        assert len(results) == 1
        assert results[0]["artifact_id"] == "a1"


# Activity log tests moved to test_activity.py (uses storage/activity.py shared module)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])