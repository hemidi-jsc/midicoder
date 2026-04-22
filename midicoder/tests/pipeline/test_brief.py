"""
Tests cho Brief Commands.

Tests này validate:
- brief analyze: Phân tích brief file, tạo working-brief trong SQLite
- brief clarify: Interactive clarification (placeholder tests)
- brief list: Hiển thị danh sách briefs
- brief save/load: Library operations

SoT: requirement.md E02, E20
"""

import pytest
import sqlite3
import tempfile
from pathlib import Path
from click.testing import CliRunner
from unittest.mock import patch, MagicMock

from midicoder.pipeline.cli import cli
from midicoder.pipeline.commands.brief import (
    analyze_brief,
    clarify_brief,
    list_briefs,
    save_brief,
    load_brief,
)
from midicoder.storage.sqlite import BriefsManager, ArtifactsManager


class TestBriefAnalyze:
    """Tests cho brief analyze command."""

    @pytest.fixture
    def runner(self):
        """Click test runner fixture."""
        return CliRunner()

    @pytest.fixture
    def tmp_brief(self, tmp_path: Path):
        """Tạo temporary brief file."""
        brief_content = """# E-commerce D2C Platform

### Product Name
E-commerce Direct-to-Consumer Platform

### Description
A full-featured e-commerce platform for direct-to-consumer businesses.

### Core Capabilities
- Product catalog management
- Shopping cart and checkout
- Order management
- Customer accounts
- Payment processing
"""
        brief_file = tmp_path / "brief.md"
        brief_file.write_text(brief_content, encoding="utf-8")
        return brief_file

    def test_analyze_command_exists(self, runner):
        """Kiểm tra brief analyze command tồn tại."""
        result = runner.invoke(cli, ["brief", "analyze", "--help"])
        assert result.exit_code == 0
        assert "analyze" in result.output.lower()

    def test_analyze_missing_file(self):
        """Test analyze với file không tồn tại."""
        with pytest.raises(SystemExit) as exc_info:
            analyze_brief(brief_path="nonexistent.md")
        assert exc_info.value.code == 1

    def test_analyze_creates_working_brief(self, tmp_path: Path, tmp_brief: Path):
        """Test analyze tạo working-brief trong SQLite."""
        # Sử dụng temporary database
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "briefs.db"
            
            # Patch database path
            with patch("midicoder.storage.sqlite.DB_BRIEFS", db_path):
                with patch("midicoder.storage.sqlite.DATABASE_DIR", Path(tmpdir)):
                    # Initialize database
                    manager = BriefsManager(db_path)
                    manager.init()
                    
                    # Run analyze
                    analyze_brief(brief_path=str(tmp_brief), force=True)
                    
                    # Verify brief was created
                    briefs = manager.list()
                    assert len(briefs) > 0
                    
                    # Find the brief with matching source file
                    found_brief = None
                    for brief in briefs:
                        if brief.get("source_file") == str(tmp_brief.absolute()):
                            found_brief = brief
                            break
                    
                    assert found_brief is not None
                    assert found_brief["type"] == "working"
                    assert found_brief["status"] == "analyzed"

    def test_analyze_title_extraction(self, tmp_path: Path, tmp_brief: Path):
        """Test extract title từ brief content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "briefs.db"
            
            with patch("midicoder.storage.sqlite.DB_BRIEFS", db_path):
                with patch("midicoder.storage.sqlite.DATABASE_DIR", Path(tmpdir)):
                    manager = BriefsManager(db_path)
                    manager.init()
                    
                    analyze_brief(brief_path=str(tmp_brief), force=True)
                    
                    briefs = manager.list()
                    assert len(briefs) > 0
                    
                    # Title should be extracted from first line
                    brief = briefs[0]
                    assert "E-commerce" in brief.get("title", "") or "D2C" in brief.get("title", "")

    def test_analyze_cli_integration(self, runner, tmp_path: Path, tmp_brief: Path):
        """Test brief analyze qua CLI."""
        # Change to tmp directory
        with runner.isolated_filesystem(temp_dir=tmp_path):
            # Copy brief to current directory
            Path("brief.md").write_text(tmp_brief.read_text(), encoding="utf-8")
            
            # Run CLI command
            result = runner.invoke(cli, ["brief", "analyze", "brief.md"])
            
            # Should succeed (exit code 0)
            assert result.exit_code == 0
            assert "Đang phân tích brief" in result.output or "Working-brief" in result.output


class TestBriefClarify:
    """Tests cho brief clarify command."""

    @pytest.fixture
    def runner(self):
        """Click test runner fixture."""
        return CliRunner()

    def test_clarify_command_exists(self, runner):
        """Kiểm tra brief clarify command tồn tại."""
        result = runner.invoke(cli, ["brief", "clarify", "--help"])
        assert result.exit_code == 0
        assert "clarify" in result.output.lower()

    def test_clarify_no_working_brief(self, tmp_path: Path):
        """Test clarify khi không có working-brief."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "briefs.db"
            
            with patch("midicoder.storage.sqlite.DB_BRIEFS", db_path):
                with patch("midicoder.storage.sqlite.DATABASE_DIR", Path(tmpdir)):
                    # Initialize empty database
                    manager = BriefsManager(db_path)
                    manager.init()
                    
                    # Run clarify - should show error
                    clarify_brief()
                    
                    # Database should still be empty
                    briefs = manager.list()
                    assert len(briefs) == 0


class TestBriefList:
    """Tests cho brief list command."""

    @pytest.fixture
    def runner(self):
        """Click test runner fixture."""
        return CliRunner()

    def test_list_command_exists(self, runner):
        """Kiểm tra brief list command tồn tại."""
        result = runner.invoke(cli, ["brief", "list", "--help"])
        assert result.exit_code == 0

    def test_list_empty_database(self, tmp_path: Path, capsys):
        """Test list với database rỗng."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "briefs.db"
            
            with patch("midicoder.storage.sqlite.DB_BRIEFS", db_path):
                with patch("midicoder.storage.sqlite.DATABASE_DIR", Path(tmpdir)):
                    manager = BriefsManager(db_path)
                    manager.init()
                    
                    # Run list
                    list_briefs()
                    
                    # Capture output
                    captured = capsys.readouterr()
                    assert "không có brief" in captured.out.lower() or "total: 0" in captured.out.lower()

    def test_list_with_briefs(self, tmp_path: Path, capsys):
        """Test list với briefs đã có."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "briefs.db"
            
            with patch("midicoder.storage.sqlite.DB_BRIEFS", db_path):
                with patch("midicoder.storage.sqlite.DATABASE_DIR", Path(tmpdir)):
                    manager = BriefsManager(db_path)
                    manager.init()
                    
                    # Create test briefs
                    manager.create(
                        brief_id="brief-test-1",
                        version="v1.0.0",
                        content="# Test Brief 1",
                        title="Test Brief 1",
                        brief_type="working"
                    )
                    manager.create(
                        brief_id="brief-test-2",
                        version="v1.0.0",
                        content="# Test Brief 2",
                        title="Test Brief 2",
                        brief_type="master"
                    )
                    
                    # Run list
                    list_briefs()
                    
                    # Capture output
                    captured = capsys.readouterr()
                    assert "Test Brief" in captured.out
                    assert "Total: 2" in captured.out


class TestBriefSaveLoad:
    """Tests cho brief save và load commands."""

    @pytest.fixture
    def runner(self):
        """Click test runner fixture."""
        return CliRunner()

    def test_save_no_master_brief(self, tmp_path: Path, capsys):
        """Test save khi không có master-brief."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "briefs.db"
            
            with patch("midicoder.storage.sqlite.DB_BRIEFS", db_path):
                with patch("midicoder.storage.sqlite.DATABASE_DIR", Path(tmpdir)):
                    manager = BriefsManager(db_path)
                    manager.init()
                    
                    # Run save - should show error
                    save_brief(name="test-library-brief")
                    
                    captured = capsys.readouterr()
                    assert "không có master-brief" in captured.out.lower()

    def test_load_nonexistent_brief(self, tmp_path: Path, capsys):
        """Test load brief không tồn tại."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "briefs.db"
            
            with patch("midicoder.storage.sqlite.DB_BRIEFS", db_path):
                with patch("midicoder.storage.sqlite.DATABASE_DIR", Path(tmpdir)):
                    manager = BriefsManager(db_path)
                    manager.init()
                    
                    # Run load with nonexistent brief
                    load_brief(name="nonexistent-brief")
                    
                    captured = capsys.readouterr()
                    assert "không tìm thấy" in captured.out.lower()


class TestBriefLifecycle:
    """Tests cho brief lifecycle end-to-end."""

    def test_full_lifecycle(self, tmp_path: Path):
        """
        Test full brief lifecycle:
        1. analyze -> working-brief (status: analyzed)
        2. clarify -> working-brief (status: clarified)
        3. save -> library-brief
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "briefs.db"
            tmpdir_path = Path(tmpdir)
            
            # Create test brief file
            brief_file = tmpdir_path / "brief.md"
            brief_file.write_text("# Test Brief\n\nTest content", encoding="utf-8")
            
            with patch("midicoder.storage.sqlite.DB_BRIEFS", db_path):
                with patch("midicoder.storage.sqlite.DATABASE_DIR", Path(tmpdir)):
                    manager = BriefsManager(db_path)
                    manager.init()
                    
                    # Step 1: Analyze
                    analyze_brief(brief_path=str(brief_file), force=True)
                    
                    briefs = manager.list()
                    assert len(briefs) == 1
                    assert briefs[0]["status"] == "analyzed"
                    assert briefs[0]["type"] == "working"
                    
                    # Step 2: Clarify
                    clarify_brief()
                    
                    # Status should change to clarified
                    briefs = manager.list()
                    assert briefs[0]["status"] == "clarified"

    def test_analyze_with_force_flag(self, tmp_path: Path):
        """Test analyze với force flag ghi đè brief cũ."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "briefs.db"
            tmpdir_path = Path(tmpdir)
            
            brief_file = tmpdir_path / "brief.md"
            brief_file.write_text("# Test Brief", encoding="utf-8")
            
            with patch("midicoder.storage.sqlite.DB_BRIEFS", db_path):
                with patch("midicoder.storage.sqlite.DATABASE_DIR", Path(tmpdir)):
                    manager = BriefsManager(db_path)
                    manager.init()
                    
                    # First analyze
                    analyze_brief(brief_path=str(brief_file), force=True)
                    assert len(manager.list()) == 1
                    
                    # Second analyze with force
                    analyze_brief(brief_path=str(brief_file), force=True)
                    # Should create new brief (force=True)
                    assert len(manager.list()) >= 1


class TestBriefDomainFilter:
    """Tests cho brief domain filtering."""

    def test_list_with_domain_filter(self, tmp_path: Path, capsys):
        """Test list với domain filter (placeholder - domain field not in schema yet)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "briefs.db"
            
            with patch("midicoder.storage.sqlite.DB_BRIEFS", db_path):
                with patch("midicoder.storage.sqlite.DATABASE_DIR", Path(tmpdir)):
                    manager = BriefsManager(db_path)
                    manager.init()
                    
                    # List with domain filter (should work, just no filter applied yet)
                    list_briefs(domain="ecommerce")
                    
                    # Should not crash
                    captured = capsys.readouterr()
                    # Domain filter is not implemented in schema yet
                    # This test documents the expected behavior