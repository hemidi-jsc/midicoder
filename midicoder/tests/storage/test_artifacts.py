"""
Tests cho ArtifactsManager và ActivityLogger.

E09: SQLite Persistence - Artifacts + Activity Log
E10: Artifact Contracts
"""

import pytest
import tempfile
import shutil
import json
from pathlib import Path
from midicoder.storage.sqlite import (
    ArtifactsManager,
    ActivityLogger,
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


class TestActivityLogger:
    """Tests cho ActivityLogger class."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """
        Setup trước mỗi test - tạo temp database.
        """
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_activity.db"
        self.logger = ActivityLogger(self.db_path)
        self.logger.init()
        yield
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init_creates_tables(self):
        """
        Test: init() tạo đúng tables artifacts và activity_log.
        
        Verification: Cả 2 tables đều tồn tại.
        """
        with self.logger._get_connection() as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = {row[0] for row in cursor.fetchall()}
            
            assert "artifacts" in tables
            assert "activity_log" in tables

    def test_log_activity_success(self):
        """
        Test: log() ghi activity log thành công.
        
        Verification: Record được lưu vào activity_log table.
        """
        self.logger.log(
            action="init",
            resource_type="project",
            resource_id="proj-001"
        )
        
        # Verify
        with self.logger._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM activity_log WHERE action = ?",
                ("init",)
            )
            row = cursor.fetchone()
            
            assert row is not None
            assert row["action"] == "init"
            assert row["resource_type"] == "project"
            assert row["resource_id"] == "proj-001"
            assert row["status"] == "success"

    def test_log_activity_with_details(self):
        """
        Test: log() với details dict được serialize thành JSON.
        
        Verification: details field chứa JSON string hợp lệ.
        """
        details = {
            "files_created": 10,
            "duration": "5s"
        }
        
        self.logger.log(
            action="generate",
            details=details
        )
        
        with self.logger._get_connection() as conn:
            cursor = conn.execute(
                "SELECT details FROM activity_log WHERE action = ?",
                ("generate",)
            )
            row = cursor.fetchone()
            
            parsed = json.loads(row["details"])
            assert parsed == details

    def test_log_activity_failed_status(self):
        """
        Test: log() với status='failed'.
        
        Verification: status field được lưu đúng.
        """
        self.logger.log(
            action="compile",
            status="failed",
            details={"error": "Syntax error"}
        )
        
        with self.logger._get_connection() as conn:
            cursor = conn.execute(
                "SELECT status FROM activity_log WHERE action = ?",
                ("compile",)
            )
            row = cursor.fetchone()
            
            assert row["status"] == "failed"

    def test_log_activity_with_duration(self):
        """
        Test: log() với duration_ms.
        
        Verification: duration_ms được lưu đúng giá trị.
        """
        self.logger.log(
            action="analyze",
            duration_ms=1523
        )
        
        with self.logger._get_connection() as conn:
            cursor = conn.execute(
                "SELECT duration_ms FROM activity_log WHERE action = ?",
                ("analyze",)
            )
            row = cursor.fetchone()
            
            assert row["duration_ms"] == 1523

    def test_log_activity_defaults(self):
        """
        Test: log() với các tham số mặc định.
        
        Verification: 
        - user mặc định là 'cli'
        - status mặc định là 'success'
        - details là NULL khi không có
        """
        self.logger.log(action="simple-action")
        
        with self.logger._get_connection() as conn:
            cursor = conn.execute(
                "SELECT user, status, details FROM activity_log LIMIT 1"
            )
            row = cursor.fetchone()
            
            assert row["user"] == "cli"
            assert row["status"] == "success"
            assert row["details"] is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])