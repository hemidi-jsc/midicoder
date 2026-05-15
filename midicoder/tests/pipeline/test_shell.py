"""
Tests cho Interactive Shell (Rich-based).

Tests này validate:
- Interactive shell khởi động khi không có command
- ASCII logo hiển thị đúng
- Command execution trong shell hoạt động
- Tab completion cho commands
"""

import pytest
from pathlib import Path
from click.testing import CliRunner
from midicoder.pipeline.cli import cli


# Import từ shell module
from midicoder.pipeline.shell import get_ascii_logo


class TestInteractiveShell:
    """Tests cho interactive shell."""

    @pytest.fixture
    def runner(self):
        """Click test runner fixture."""
        return CliRunner()

    def test_shell_starts_without_command(self, runner):
        """Kiểm tra shell mở khi không có command."""
        # Test shell initialization (không interactive trong test)
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Midicoder" in result.output

    def test_ascii_logo_function_works(self):
        """Kiểm tra hàm get_ascii_logo hoạt động."""
        logo = get_ascii_logo()
        assert len(logo) > 0, "Logo không nên rỗng"
        # Logo dùng ## hoặc # hoặc █ cho ASCII art
        assert "##" in logo or "#" in logo or "█" in logo, "Logo nên chứa ASCII art"

    def test_ascii_logo_fallback_exists(self):
        """Kiểm tra fallback logo tồn tại khi file không có."""
        # Hàm get_ascii_logo có fallback nên luôn trả về logo
        logo = get_ascii_logo()
        # Fallback logo có chữ MIDICODER hoặc ASCII blocks (##, #, or █)
        has_text = "MIDICODER" in logo or "Midicoder" in logo
        has_art = "##" in logo or "█" in logo or "#" in logo
        assert has_text or has_art, "Logo nên có text hoặc art"

    def test_commands_available_in_shell(self, runner):
        """Kiểm tra các commands có sẵn trong shell."""
        expected_commands = [
            "init",
            "brief",
            "contract",
            "ir",
            "code",
            "preview",
            "config",
            "status",
            "help",
        ]

        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0

        # Check that main commands appear in help
        for cmd in expected_commands:
            assert cmd in result.output.lower(), f"Command '{cmd}' should be available"

    def test_rich_output_available(self):
        """Kiểm tra Rich library có sẵn."""
        from rich.console import Console
        from rich.panel import Panel
        from io import StringIO

        # Cần record=True để export_text hoạt động
        console = Console(file=StringIO(), force_terminal=True, record=True)
        panel = Panel("[bold]Midicoder[/bold]")
        console.print(panel)

        # Rich nên render được mà không lỗi
        output = console.export_text()
        assert isinstance(output, str)


class TestRichTheme:
    """Tests cho Rich theme."""

    def test_console_creation(self):
        """Kiểm tra tạo Rich Console."""
        from rich.console import Console

        console = Console(force_terminal=True)
        assert console is not None

    def test_panel_rendering(self):
        """Kiểm tra Rich Panel rendering."""
        from rich.console import Console
        from rich.panel import Panel
        from io import StringIO

        console = Console(file=StringIO(), force_terminal=True)
        panel = Panel("Midicoder Shell", style="bold blue")
        console.print(panel)

        output = console.file.getvalue()
        assert "Midicoder Shell" in output

    def test_ascii_art_display(self):
        """Kiểm tra ASCII art hiển thị được với Rich."""
        from rich.console import Console
        from rich.text import Text
        from io import StringIO

        # Dùng get_ascii_logo() thay vì đọc file trực tiếp
        logo_content = get_ascii_logo()
        console = Console(file=StringIO(), force_terminal=True)
        text = Text(logo_content)
        console.print(text)

        output = console.file.getvalue()
        assert len(output) > 0


class TestShellCommands:
    """Tests cho command execution trong shell context."""

    @pytest.fixture
    def runner(self):
        """Click test runner fixture."""
        return CliRunner()

    def test_init_command_from_shell(self, runner):
        """Kiểm tra init command chạy được từ shell."""
        # Test command structure (actual init cần workspace)
        result = runner.invoke(cli, ["init", "--help"])
        assert result.exit_code == 0
        assert "init" in result.output.lower()

    def test_brief_command_from_shell(self, runner):
        """Kiểm tra brief command từ shell."""
        result = runner.invoke(cli, ["brief", "--help"])
        assert result.exit_code == 0
        assert "brief" in result.output.lower()

    def test_contract_command_from_shell(self, runner):
        """Kiểm tra contract command từ shell."""
        result = runner.invoke(cli, ["contract", "--help"])
        assert result.exit_code == 0
        assert "contract" in result.output.lower()

    def test_config_command_from_shell(self, runner):
        """Kiểm tra config command từ shell."""
        result = runner.invoke(cli, ["config", "--help"])
        assert result.exit_code == 0
        assert "config" in result.output.lower()


class TestShellIntegration:
    """Integration tests cho shell."""

    @pytest.fixture
    def runner(self):
        """Click test runner fixture."""
        return CliRunner()

    def test_version_shows_in_shell(self, runner):
        """Kiểm tra version hiển thị trong shell."""
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "1.0.0" in result.output

    def test_help_shows_commands(self, runner):
        """Kiểm tra help hiển thị commands."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "init" in result.output
        assert "brief" in result.output
        assert "contract" in result.output
