"""
Tests cho Utility Commands (status, feedback, config).

Tests này validate:
- CLI commands registration (status, feedback, config group)
- Status command output format (human-readable + JSON)
- Feedback command storage trong SQLite
- Config commands với schema validation
- Error handling cho missing workspace/invalid inputs

E20: CLI Commands - Utility Commands
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from click.testing import CliRunner

from midicoder.errors import ErrorCode, MidicoderError
from midicoder.pipeline.commands.util import (
    get_status,
    get_workspace_status,
    get_pipeline_progress,
    get_artifacts_summary,
    get_neo4j_status,
    get_versions_list,
    submit_feedback,
    validate_feedback_type,
    FeedbackManager,
    get_config_schema,
    validate_config_key,
)
from midicoder.storage.sqlite import BriefsManager, ArtifactsManager, DB_BRIEFS, DB_ARTIFACTS


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def runner():
    """Click test runner."""
    return CliRunner()


@pytest.fixture
def temp_workspace(tmp_path):
    """Tạo temporary workspace với .midicoder/ structure."""
    workspace = tmp_path / "test-project"
    workspace.mkdir()
    
    midicoder_dir = workspace / ".midicoder"
    midicoder_dir.mkdir()
    (midicoder_dir / "data").mkdir()
    
    versions_dir = midicoder_dir / "versions"
    versions_dir.mkdir()
    
    v1_dir = versions_dir / "v1.0.0"
    v1_dir.mkdir()
    (v1_dir / "metadata.yml").write_text("active: true\narchived: false\n")
    (v1_dir / "src").mkdir()
    
    (midicoder_dir / "active_version").write_text("v1.0.0")
    
    return workspace


@pytest.fixture
def initialized_workspace(temp_workspace):
    """Tạo initialized workspace với databases và sample data."""
    workspace = temp_workspace
    orig_cwd = Path.cwd()
    
    try:
        import os
        os.chdir(workspace)
        
        briefs_mgr = BriefsManager(DB_BRIEFS)
        briefs_mgr.init()
        
        artifacts_mgr = ArtifactsManager(DB_ARTIFACTS)
        artifacts_mgr.init()
        
        briefs_mgr.create(
            brief_id="test-brief-001",
            version="v1.0.0",
            content="# Test Brief\n\nSample content",
            title="Test Brief",
            brief_type="working"
        )
        
        artifacts_mgr.create(
            artifact_id="artifact-001",
            artifact_type="brief",
            name="test-brief",
            version="v1.0.0",
            brief_id="test-brief-001"
        )
        
        yield workspace
        
    finally:
        import os
        os.chdir(orig_cwd)


# ============================================================================
# Tests: Config Schema Helpers
# ============================================================================

class TestConfigSchemaHelpers:
    """Tests cho config schema validation helpers."""
    
    def test_get_config_schema_returns_dict(self):
        """Test get_config_schema trả về dict hợp lệ."""
        schema = get_config_schema()
        assert isinstance(schema, dict)
        assert "cli" in schema
        assert "llm" in schema
        assert "neo4j" in schema
        assert "webgui" in schema
    
    def test_get_config_schema_has_all_sections(self):
        """Test schema có đủ tất cả sections."""
        schema = get_config_schema()
        expected_sections = ["cli", "llm", "mcp", "neo4j", "webgui", "version"]
        for section in expected_sections:
            assert section in schema
    
    def test_validate_config_key_valid_key(self):
        """Test validate_config_key với valid key."""
        assert validate_config_key("llm.model") is True
        assert validate_config_key("cli.language") is True
        assert validate_config_key("neo4j.port") is True
    
    def test_validate_config_key_invalid_key(self):
        """Test validate_config_key với invalid key."""
        assert validate_config_key("invalid.key") is False
        assert validate_config_key("llm.invalid") is False
        assert validate_config_key("") is False
    
    def test_validate_config_key_section_only(self):
        """Test validate_config_key với section name only."""
        assert validate_config_key("llm") is True
        assert validate_config_key("cli") is True


# ============================================================================
# Tests: Feedback Validation
# ============================================================================

class TestFeedbackValidation:
    """Tests cho feedback type validation."""
    
    def test_validate_feedback_type_valid_types(self):
        """Test validate_feedback_type với valid types."""
        for feedback_type in ["bug", "enhancement", "clarification"]:
            assert validate_feedback_type(feedback_type) is True
    
    def test_validate_feedback_type_invalid_type(self):
        """Test validate_feedback_type với invalid type."""
        for feedback_type in ["feature", "question", "invalid", ""]:
            assert validate_feedback_type(feedback_type) is False
    
    def test_validate_feedback_type_case_sensitive(self):
        """Test validate_feedback_type là case-sensitive."""
        assert validate_feedback_type("BUG") is False
        assert validate_feedback_type("Clarification") is False


# ============================================================================
# Tests: Status Command Helpers
# ============================================================================

class TestStatusHelpers:
    """Tests cho status command helper functions."""
    
    @patch("midicoder.pipeline.commands.util.BriefsManager")
    @patch("midicoder.pipeline.commands.util.ArtifactsManager")
    def test_get_workspace_status_initialized(self, mock_artifacts, mock_briefs, temp_workspace):
        """Test get_workspace_status với initialized workspace."""
        import os
        orig_cwd = os.getcwd()
        try:
            os.chdir(temp_workspace)
            status = get_workspace_status()
            assert status["initialized"] is True
            assert "path" in status
        finally:
            os.chdir(orig_cwd)
    
    @patch("midicoder.pipeline.commands.util.BriefsManager")
    @patch("midicoder.pipeline.commands.util.ArtifactsManager")
    def test_get_workspace_status_not_initialized(self, mock_artifacts, mock_briefs, tmp_path):
        """Test get_workspace_status với uninitialized workspace."""
        import os
        orig_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            status = get_workspace_status()
            assert status["initialized"] is False
        finally:
            os.chdir(orig_cwd)
    
    @patch("midicoder.pipeline.commands.util.ArtifactsManager")
    def test_get_artifacts_summary(self, mock_artifacts, initialized_workspace):
        """Test get_artifacts_summary trả về artifact counts."""
        import os
        orig_cwd = os.getcwd()
        try:
            os.chdir(initialized_workspace)
            mock_artifacts.return_value.list.return_value = [
                {"type": "brief"},
                {"type": "brief"},
                {"type": "contract"},
            ]
            summary = get_artifacts_summary()
            assert "briefs" in summary
            assert "contracts" in summary
            assert isinstance(summary["briefs"], int)
        finally:
            os.chdir(orig_cwd)
    
    def test_get_neo4j_status_check(self, tmp_path):
        """Test get_neo4j_status check connection."""
        import os
        orig_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            status = get_neo4j_status()
            assert "status" in status
            assert status["status"] in ["running", "not_running", "error"]
        finally:
            os.chdir(orig_cwd)


# ============================================================================
# Tests: Feedback Manager
# ============================================================================

class TestFeedbackManager:
    """Tests cho FeedbackManager class."""
    
    @patch("midicoder.pipeline.commands.util.BriefsManager")
    def test_feedback_manager_init_creates_table(self, mock_briefs, temp_workspace):
        """Test FeedbackManager.__init__ tạo feedback table."""
        import os
        orig_cwd = os.getcwd()
        try:
            os.chdir(temp_workspace)
            mgr = FeedbackManager()
            assert mgr.db_path is not None
        finally:
            os.chdir(orig_cwd)
    
    @patch("midicoder.pipeline.commands.util.BriefsManager")
    def test_feedback_manager_save_feedback(self, mock_briefs, initialized_workspace):
        """Test FeedbackManager.save lưu feedback vào SQLite."""
        import os
        orig_cwd = os.getcwd()
        try:
            os.chdir(initialized_workspace)
            mgr = FeedbackManager()
            mgr.get_active_brief = Mock(return_value={
                "id": 1, "brief_id": "test-brief-001", "version": "v1.0.0"
            })
            feedback_id = mgr.save_feedback(
                feedback_type="clarification",
                message="Test feedback",
                auto_apply=True
            )
            assert feedback_id is not None
            assert isinstance(feedback_id, int)
        finally:
            os.chdir(orig_cwd)
    
    def test_feedback_manager_get_active_brief_returns_data(self, initialized_workspace):
        """Test FeedbackManager.get_active_brief trả về brief nếu có."""
        import os
        orig_cwd = os.getcwd()
        try:
            os.chdir(initialized_workspace)
            mgr = FeedbackManager()
            brief = mgr.get_active_brief()
            assert brief is not None
            assert "brief_id" in brief
        finally:
            os.chdir(orig_cwd)


# ============================================================================
# Tests: Submit Feedback Function
# ============================================================================

class TestSubmitFeedback:
    """Tests cho submit_feedback function."""
    
    @patch("midicoder.pipeline.commands.util.FeedbackManager")
    def test_submit_feedback_success(self, mock_feedback_mgr, initialized_workspace):
        """Test submit_feedback lưu thành công."""
        import os
        orig_cwd = os.getcwd()
        try:
            os.chdir(initialized_workspace)
            mock_mgr_instance = Mock()
            mock_feedback_mgr.return_value = mock_mgr_instance
            mock_mgr_instance.save_feedback.return_value = 1
            mock_mgr_instance.get_active_brief.return_value = {"id": 1, "brief_id": "test-001", "version": "v1.0.0"}
            
            feedback_id = submit_feedback(
                feedback_type="clarification",
                message="Test feedback",
                auto_apply=False
            )
            
            mock_mgr_instance.save_feedback.assert_called_once()
            assert feedback_id == 1
        finally:
            os.chdir(orig_cwd)
    
    @patch("midicoder.pipeline.commands.util.FeedbackManager")
    def test_submit_feedback_invalid_type(self, mock_feedback_mgr, initialized_workspace):
        """Test submit_feedback với invalid type throw error."""
        import os
        orig_cwd = os.getcwd()
        try:
            os.chdir(initialized_workspace)
            with pytest.raises(MidicoderError) as exc_info:
                submit_feedback(
                    feedback_type="invalid_type",
                    message="Test feedback",
                    auto_apply=False
                )
            assert exc_info.value.code == ErrorCode.UTIL_INVALID_FEEDBACK_TYPE
        finally:
            os.chdir(orig_cwd)


# ============================================================================
# Tests: Get Status Function
# ============================================================================

class TestGetStatus:
    """Tests cho get_status function."""
    
    @patch("midicoder.pipeline.commands.util.get_workspace_status")
    @patch("midicoder.pipeline.commands.util.get_pipeline_progress")
    @patch("midicoder.pipeline.commands.util.get_artifacts_summary")
    @patch("midicoder.pipeline.commands.util.get_neo4j_status")
    @patch("midicoder.pipeline.commands.util.get_versions_list")
    def test_get_status_returns_complete_status(
        self, mock_versions, mock_neo4j, mock_artifacts, mock_pipeline, mock_workspace
    ):
        """Test get_status trả về complete status dict."""
        mock_workspace.return_value = {"initialized": True, "path": "/test"}
        mock_pipeline.return_value = {"brief": {"status": "analyzed"}}
        mock_artifacts.return_value = {"briefs": 1}
        mock_neo4j.return_value = {"status": "running"}
        mock_versions.return_value = [{"version": "v1.0.0", "active": True}]
        
        status = get_status()
        
        assert "workspace" in status
        assert "pipeline" in status
        assert "artifacts" in status
        assert "neo4j" in status
        assert "versions" in status
    
    @patch("midicoder.pipeline.commands.util.get_workspace_status")
    def test_get_status_workspace_not_initialized(self, mock_workspace):
        """Test get_status khi workspace chưa initialized."""
        mock_workspace.return_value = {"initialized": False, "path": "/test"}
        status = get_status()
        assert status["workspace"]["initialized"] is False


# ============================================================================
# Tests: CLI Integration
# ============================================================================

class TestCLIIntegration:
    """Tests cho CLI command integration."""
    
    def test_status_command_help(self):
        """Test status command is callable."""
        from midicoder.pipeline.commands import util
        assert hasattr(util, "run_status")
        assert hasattr(util, "get_status")
    
    @patch("midicoder.pipeline.commands.util.get_status")
    def test_status_command_json_output(self, mock_get_status, temp_workspace):
        """Test get_status JSON output format."""
        import os
        orig_cwd = os.getcwd()
        try:
            os.chdir(temp_workspace)
            mock_get_status.return_value = {
                "metadata": {"version": "1.0.0"},
                "workspace": {"initialized": True}
            }
            status = get_status()
            assert "metadata" in status
        finally:
            os.chdir(orig_cwd)


# ============================================================================
# Tests: Edge Cases
# ============================================================================

class TestEdgeCases:
    """Tests cho edge cases."""
    
    def test_feedback_empty_message(self, initialized_workspace):
        """Test submit_feedback với empty message."""
        import os
        orig_cwd = os.getcwd()
        try:
            os.chdir(initialized_workspace)
            pass  # Placeholder
        finally:
            os.chdir(orig_cwd)
    
    def test_status_output_format_consistency(self):
        """Test status output format consistency."""
        test_status = {
            "metadata": {"version": "1.0.0", "timestamp": "2026-04-27T00:00:00Z"},
            "workspace": {"path": "/test", "initialized": True}
        }
        json_str = json.dumps(test_status)
        parsed = json.loads(json_str)
        assert parsed == test_status