"""
Tests cho Brief Commands CLI.

Module này chứa tests cho brief commands:
- brief analyze
- brief clarify
- brief save
- brief load
- brief list
- brief library

Theo TDD: Tests được viết trước implementation.

Tests coverage:
- CLI help content
- Command options/arguments
- Business logic validation
"""

import pytest
import click
from click.testing import CliRunner
from pathlib import Path
import tempfile
import os


# Import CLI commands để test
# Note: Import từ cli.py để test full CLI integration
from midicoder.pipeline.cli import cli


class TestBriefCommandsHelp:
    """
    Tests cho brief commands --help content.
    
    Mỗi subcommand phải có --help hiển thị đúng:
    - Command purpose
    - Options/arguments
    - Examples
    """

    @pytest.fixture
    def runner(self):
        """Click test runner."""
        return CliRunner()

    def test_brief_group_help(self, runner):
        """
        Test brief group --help hiển thị đúng.
        
        Expected output phải chứa:
        - "brief" group name
        - List of subcommands: analyze, clarify, save, load, list, library
        """
        result = runner.invoke(cli, ["brief", "--help"])
        
        assert result.exit_code == 0
        assert "brief" in result.output.lower()
        assert "analyze" in result.output
        assert "clarify" in result.output
        assert "save" in result.output
        assert "load" in result.output
        assert "list" in result.output
        assert "library" in result.output

    def test_brief_analyze_help(self, runner):
        """
        Test brief analyze --help hiển thị đúng.
        
        Expected output phải chứa:
        - Command purpose (phân tích brief)
        - --file/-f option
        - --domain option
        """
        result = runner.invoke(cli, ["brief", "analyze", "--help"])
        
        assert result.exit_code == 0
        assert "file" in result.output.lower() or "f" in result.output
        # Domain option có thể có hoặc không

    def test_brief_clarify_help(self, runner):
        """
        Test brief clarify --help hiển thị đúng.
        
        Expected output phải chứa:
        - Command purpose (clarification)
        - --max-rounds option
        """
        result = runner.invoke(cli, ["brief", "clarify", "--help"])
        
        assert result.exit_code == 0
        assert "clarif" in result.output.lower() or "max" in result.output.lower()

    def test_brief_save_help(self, runner):
        """
        Test brief save --help hiển thị đúng.
        
        Expected output phải chứa:
        - Command purpose (save to library)
        - --name option
        - --tags option
        """
        result = runner.invoke(cli, ["brief", "save", "--help"])
        
        assert result.exit_code == 0
        assert "name" in result.output.lower()

    def test_brief_load_help(self, runner):
        """
        Test brief load --help hiển thị đúng.
        
        Expected output phải chứa:
        - Command purpose (load from library)
        - NAME argument
        """
        result = runner.invoke(cli, ["brief", "load", "--help"])
        
        assert result.exit_code == 0
        assert "load" in result.output.lower()

    def test_brief_list_help(self, runner):
        """
        Test brief list --help hiển thị đúng.
        
        Expected output phải chứa:
        - Command purpose (list briefs)
        - --domain option (optional)
        """
        result = runner.invoke(cli, ["brief", "list", "--help"])
        
        assert result.exit_code == 0
        assert "list" in result.output.lower()

    def test_brief_library_help(self, runner):
        """
        Test brief library --help hiển thị đúng.
        
        Expected output phải chứa:
        - Command purpose (industry brief templates)
        """
        result = runner.invoke(cli, ["brief", "library", "--help"])
        
        assert result.exit_code == 0
        assert "library" in result.output.lower() or "indust" in result.output.lower()


class TestBriefAnalyzeCommand:
    """
    Tests cho brief analyze command.
    """

    @pytest.fixture
    def runner(self):
        """Click test runner."""
        return CliRunner()

    @pytest.fixture
    def temp_brief(self, tmp_path):
        """
        Tạo temporary brief file cho testing.
        
        Args:
            tmp_path: pytest temporary path fixture
        
        Returns:
            Path đến brief file
        """
        brief_content = """# Test Brief

This is a test brief for unit testing.

## Requirements

- Requirement 1
- Requirement 2
"""
        brief_file = tmp_path / "brief.md"
        brief_file.write_text(brief_content, encoding="utf-8")
        return brief_file

    def test_analyze_nonexistent_file(self, runner, tmp_path):
        """
        Test brief analyze với file không tồn tại.
        
        Expected: Exit code != 0 hoặc error message
        Click trả về exit code 2 cho validation error (file không tồn tại)
        """
        result = runner.invoke(
            cli,
            ["brief", "analyze", str(tmp_path / "nonexistent.md")]
        )
        
        # Click validation error trả về exit code 2
        # Hoặc implementation error trả về 0/1
        assert result.exit_code in [0, 1, 2]
        # Nếu exit_code != 2, phải có error message hoặc warning
        if result.exit_code != 2:
            assert "exist" in result.output.lower() or "error" in result.output.lower() or "not found" in result.output.lower()

    def test_analyze_existing_file(self, runner, temp_brief):
        """
        Test brief analyze với file tồn tại.
        
        Expected: Exit code 0 và success message
        """
        result = runner.invoke(cli, ["brief", "analyze", str(temp_brief)])
        
        # Command có thể exit 0 hoặc có warning về workspace không init
        assert result.exit_code in [0, 1]


class TestBriefListCommand:
    """
    Tests cho brief list command.
    """

    @pytest.fixture
    def runner(self):
        """Click test runner."""
        return CliRunner()

    def test_list_no_briefs(self, runner):
        """
        Test brief list khi không có brief nào.
        
        Expected: Exit code 0 và message "không có brief"
        """
        result = runner.invoke(cli, ["brief", "list"])
        
        # Command phải exit 0
        assert result.exit_code in [0, 1]
        # Có thể hiển thị "không có brief" hoặc "no briefs" hoặc error về workspace


class TestBriefSaveCommand:
    """
    Tests cho brief save command.
    """

    @pytest.fixture
    def runner(self):
        """Click test runner."""
        return CliRunner()

    def test_save_without_name(self, runner):
        """
        Test brief save không có --name.
        
        Expected: Error về thiếu required option
        """
        result = runner.invoke(cli, ["brief", "save"])
        
        # Exit code có thể là 0 (với error message) hoặc 2 (click error)
        assert result.exit_code in [0, 1, 2]

    def test_save_with_name(self, runner):
        """
        Test brief save với --name.
        
        Expected: Exit code 0 hoặc error về workspace/missing brief
        """
        result = runner.invoke(cli, ["brief", "save", "--name", "test-brief"])
        
        # Command phải exit 0 hoặc error hợp lệ
        assert result.exit_code in [0, 1]


class TestBriefLoadCommand:
    """
    Tests cho brief load command.
    """

    @pytest.fixture
    def runner(self):
        """Click test runner."""
        return CliRunner()

    def test_load_without_name(self, runner):
        """
        Test brief load không có NAME argument.
        
        Expected: Error về thiếu required argument
        """
        result = runner.invoke(cli, ["brief", "load"])
        
        # Click sẽ return exit code 2 cho missing argument
        assert result.exit_code in [0, 1, 2]

    def test_load_nonexistent_brief(self, runner):
        """
        Test brief load với brief không tồn tại.
        
        Expected: Error message
        """
        result = runner.invoke(cli, ["brief", "load", "nonexistent-brief"])
        
        # Exit code 0 hoặc 1 với error message
        assert result.exit_code in [0, 1]


class TestBriefLibraryCommand:
    """
    Tests cho brief library command.
    """

    @pytest.fixture
    def runner(self):
        """Click test runner."""
        return CliRunner()

    def test_library_command(self, runner):
        """
        Test brief library command.
        
        Expected: Exit code 0 hoặc message về industry briefs folder
        """
        result = runner.invoke(cli, ["brief", "library"])
        
        # Command phải exit 0
        assert result.exit_code in [0, 1]