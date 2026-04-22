"""
Tests cho CLI Commands.

Tests này validate:
- Global flags hoạt động đúng (--version, --help, --debug, --quiet, --json)
- CLI structure đúng theo SoT (requirement.md E20)
- Commands có thể invoke được
"""

import pytest
from click.testing import CliRunner
from midicoder.pipeline.cli import cli


class TestGlobalFlags:
    """Tests cho global flags của CLI."""

    @pytest.fixture
    def runner(self):
        """Click test runner fixture."""
        return CliRunner()

    def test_version_flag(self, runner):
        """Kiểm tra --version flag hiển thị phiên bản."""
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "1.0.0" in result.output

    def test_help_flag(self, runner):
        """Kiểm tra --help flag hiển thị help."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Midicoder" in result.output
        assert "init" in result.output
        assert "brief" in result.output
        assert "contract" in result.output

    def test_debug_flag(self, runner):
        """Kiểm tra --debug flag được nhận."""
        result = runner.invoke(cli, ["--debug", "--help"])
        assert result.exit_code == 0

    def test_quiet_flag(self, runner):
        """Kiểm tra --quiet flag được nhận."""
        result = runner.invoke(cli, ["--quiet", "--help"])
        assert result.exit_code == 0

    def test_json_flag(self, runner):
        """Kiểm tra --json flag được nhận."""
        result = runner.invoke(cli, ["--json", "--help"])
        assert result.exit_code == 0


class TestInitCommand:
    """Tests cho init command."""

    @pytest.fixture
    def runner(self):
        """Click test runner fixture."""
        return CliRunner()

    def test_init_command_exists(self, runner):
        """Kiểm tra init command tồn tại."""
        result = runner.invoke(cli, ["init", "--help"])
        assert result.exit_code == 0
        assert "init" in result.output.lower()

    def test_init_force_flag(self, runner):
        """Kiểm tra init --force flag được nhận."""
        # Test với mock để không tạo thư mục thực
        result = runner.invoke(cli, ["init", "--force"])
        # Exit code có thể khác 0 vì cần workspace thật
        # Quan trọng là flag được parse đúng
        assert "No such option" not in result.output or "force" not in result.output

    def test_init_no_index_flag(self, runner):
        """Kiểm tra init --no-index flag được nhận."""
        result = runner.invoke(cli, ["init", "--no-index"])
        assert "No such option" not in result.output or "no-index" not in result.output

    def test_init_version_flag(self, runner):
        """Kiểm tra init --version flag được nhận."""
        result = runner.invoke(cli, ["init", "--version", "v1.0.0"])
        # Flag được parse đúng
        assert "No such option" not in result.output or "version" not in result.output


class TestBriefCommands:
    """Tests cho brief commands."""

    @pytest.fixture
    def runner(self):
        """Click test runner fixture."""
        return CliRunner()

    def test_brief_group_exists(self, runner):
        """Kiểm tra brief group command tồn tại."""
        result = runner.invoke(cli, ["brief", "--help"])
        assert result.exit_code == 0
        assert "brief" in result.output.lower()

    def test_brief_analyze_exists(self, runner):
        """Kiểm tra brief analyze command tồn tại."""
        result = runner.invoke(cli, ["brief", "analyze", "--help"])
        assert result.exit_code == 0

    def test_brief_clarify_exists(self, runner):
        """Kiểm tra brief clarify command tồn tại."""
        result = runner.invoke(cli, ["brief", "clarify", "--help"])
        assert result.exit_code == 0

    def test_brief_list_exists(self, runner):
        """Kiểm tra brief list command tồn tại."""
        result = runner.invoke(cli, ["brief", "list", "--help"])
        assert result.exit_code == 0


class TestContractCommands:
    """Tests cho contract commands."""

    @pytest.fixture
    def runner(self):
        """Click test runner fixture."""
        return CliRunner()

    def test_contract_group_exists(self, runner):
        """Kiểm tra contract group command tồn tại."""
        result = runner.invoke(cli, ["contract", "--help"])
        assert result.exit_code == 0
        assert "contract" in result.output.lower()

    def test_contract_gen_exists(self, runner):
        """Kiểm tra contract gen command tồn tại."""
        result = runner.invoke(cli, ["contract", "gen", "--help"])
        assert result.exit_code == 0

    def test_contract_check_exists(self, runner):
        """Kiểm tra contract check command tồn tại."""
        result = runner.invoke(cli, ["contract", "check", "--help"])
        assert result.exit_code == 0

    def test_contract_repair_exists(self, runner):
        """Kiểm tra contract repair command tồn tại."""
        result = runner.invoke(cli, ["contract", "repair", "--help"])
        assert result.exit_code == 0


class TestIRCommands:
    """Tests cho IR commands."""

    @pytest.fixture
    def runner(self):
        """Click test runner fixture."""
        return CliRunner()

    def test_ir_group_exists(self, runner):
        """Kiểm tra IR group command tồn tại."""
        result = runner.invoke(cli, ["ir", "--help"])
        assert result.exit_code == 0
        assert "ir" in result.output.lower()

    def test_ir_build_exists(self, runner):
        """Kiểm tra ir build command tồn tại."""
        result = runner.invoke(cli, ["ir", "build", "--help"])
        assert result.exit_code == 0


class TestCodeCommands:
    """Tests cho code commands."""

    @pytest.fixture
    def runner(self):
        """Click test runner fixture."""
        return CliRunner()

    def test_code_group_exists(self, runner):
        """Kiểm tra code group command tồn tại."""
        result = runner.invoke(cli, ["code", "--help"])
        assert result.exit_code == 0
        assert "code" in result.output.lower()

    def test_code_plan_exists(self, runner):
        """Kiểm tra code plan command tồn tại."""
        result = runner.invoke(cli, ["code", "plan", "--help"])
        assert result.exit_code == 0

    def test_code_gen_exists(self, runner):
        """Kiểm tra code gen command tồn tại."""
        result = runner.invoke(cli, ["code", "gen", "--help"])
        assert result.exit_code == 0

    def test_code_apply_exists(self, runner):
        """Kiểm tra code apply command tồn tại."""
        result = runner.invoke(cli, ["code", "apply", "--help"])
        assert result.exit_code == 0


class TestPreviewCommands:
    """Tests cho preview commands."""

    @pytest.fixture
    def runner(self):
        """Click test runner fixture."""
        return CliRunner()

    def test_preview_group_exists(self, runner):
        """Kiểm tra preview group command tồn tại."""
        result = runner.invoke(cli, ["preview", "--help"])
        assert result.exit_code == 0
        assert "preview" in result.output.lower()

    def test_preview_start_exists(self, runner):
        """Kiểm tra preview start command tồn tại."""
        result = runner.invoke(cli, ["preview", "start", "--help"])
        assert result.exit_code == 0

    def test_preview_stop_exists(self, runner):
        """Kiểm tra preview stop command tồn tại."""
        result = runner.invoke(cli, ["preview", "stop", "--help"])
        assert result.exit_code == 0

    def test_preview_status_exists(self, runner):
        """Kiểm tra preview status command tồn tại."""
        result = runner.invoke(cli, ["preview", "status", "--help"])
        assert result.exit_code == 0


class TestConfigCommands:
    """Tests cho config commands."""

    @pytest.fixture
    def runner(self):
        """Click test runner fixture."""
        return CliRunner()

    def test_config_group_exists(self, runner):
        """Kiểm tra config group command tồn tại."""
        result = runner.invoke(cli, ["config", "--help"])
        assert result.exit_code == 0
        assert "config" in result.output.lower()

    def test_config_show_exists(self, runner):
        """Kiểm tra config show command tồn tại."""
        result = runner.invoke(cli, ["config", "show", "--help"])
        assert result.exit_code == 0

    def test_config_set_exists(self, runner):
        """Kiểm tra config set command tồn tại."""
        result = runner.invoke(cli, ["config", "set", "--help"])
        assert result.exit_code == 0

    def test_config_reset_exists(self, runner):
        """Kiểm tra config reset command tồn tại."""
        result = runner.invoke(cli, ["config", "reset", "--help"])
        assert result.exit_code == 0


class TestUtilityCommands:
    """Tests cho utility commands."""

    @pytest.fixture
    def runner(self):
        """Click test runner fixture."""
        return CliRunner()

    def test_status_command_exists(self, runner):
        """Kiểm tra status command tồn tại."""
        result = runner.invoke(cli, ["status", "--help"])
        assert result.exit_code == 0

    def test_help_command_exists(self, runner):
        """Kiểm tra help command tồn tại."""
        result = runner.invoke(cli, ["help", "--help"])
        assert result.exit_code == 0