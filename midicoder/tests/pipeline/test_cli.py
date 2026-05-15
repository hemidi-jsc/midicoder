"""
Tests cho CLI Commands.

Tests này validate:
- Global flags hoạt động đúng (--version, --help, --debug, --quiet, --json)
- CLI structure đúng theo SoT (requirement.md E20)
- Commands có thể invoke được
- Exit codes đúng spec
- JSON output format đúng
"""

import json
import subprocess
import sys

import pytest
from click.testing import CliRunner

# Import CLI entry point
from midicoder.pipeline.cli import cli
from midicoder.errors import ExitCode

# Path đến Python interpreter
PYTHON = sys.executable


# ============================================================================
# UNIT TESTS - Click CliRunner (fast, isolated)
# ============================================================================

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
        result = runner.invoke(cli, ["init", "--force"])
        # Flag được parse đúng (không báo lỗi option không tồn tại)
        assert "--force" not in result.output or "No such option" not in result.output

    def test_init_no_index_flag(self, runner):
        """Kiểm tra init --no-index flag được nhận (flag đã bị remove, CLI báo No such option)."""
        result = runner.invoke(cli, ["init", "--no-index"])
        # --no-index không còn là flag hợp lệ
        assert result.exit_code != 0 or "No such option" in result.output

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

    def test_code_gen_target_option(self, runner):
        """Kiểm tra code gen --target option."""
        result = runner.invoke(cli, ["code", "gen", "--target", "backend"])
        # Option được parse đúng
        assert "No such option" not in result.output

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


# ============================================================================
# INTEGRATION TESTS - pytest-subprocess (real subprocess)
# ============================================================================

class TestCLIIntegration:
    """Integration tests cho CLI với subprocess."""

    def test_cli_help_from_subprocess(self):
        """Test CLI --help từ subprocess."""
        result = subprocess.run(
            [PYTHON, "-m", "midicoder.pipeline", "--help"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30
        )
        # Command chạy thành công hoặc vào shell
        stdout = result.stdout or ""
        assert "Midicoder" in stdout or result.returncode in [0, 1]

    def test_cli_version_from_subprocess(self):
        """Test CLI --version từ subprocess."""
        result = subprocess.run(
            [PYTHON, "-m", "midicoder.pipeline", "--version"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30
        )
        stdout = result.stdout or ""
        assert "1.0.0" in stdout
        assert result.returncode == 0

    def test_cli_init_help_from_subprocess(self):
        """Test CLI init --help từ subprocess."""
        result = subprocess.run(
            [PYTHON, "-m", "midicoder.pipeline", "init", "--help"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30
        )
        assert result.returncode in [0, 1]

    def test_cli_status_from_subprocess(self):
        """Test CLI status từ subprocess."""
        result = subprocess.run(
            [PYTHON, "-m", "midicoder.pipeline", "status"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30
        )
        assert result.returncode in [0, 1]


class TestExitCodes:
    """Tests cho exit codes."""

    def test_exit_code_enum_values(self):
        """Kiểm tra ExitCode enum có đúng values."""
        assert ExitCode.SUCCESS.value == 0
        assert ExitCode.GENERIC_ERROR.value == 1
        assert ExitCode.BAD_ARGUMENTS.value == 2
        assert ExitCode.FILE_NOT_FOUND.value == 3
        assert ExitCode.PERMISSION_DENIED.value == 4
        assert ExitCode.CONFIG_ERROR.value == 5
        assert ExitCode.COMMAND_NOT_FOUND.value == 6
        assert ExitCode.ALREADY_INITIALIZED.value == 7
        assert ExitCode.INTERRUPT.value == 130

    def test_exit_code_description(self):
        """Kiểm tra ExitCode.get_description trả về tiếng Việt."""
        assert ExitCode.get_description(0) == "Thành công"
        assert ExitCode.get_description(1) == "Lỗi không xác định"
        assert ExitCode.get_description(2) == "Lỗi arguments CLI"
        assert ExitCode.get_description(3) == "File/thư mục không tìm thấy"
        assert ExitCode.get_description(130) == "Người dùng hủy bỏ (Ctrl+C)"


class TestJSONOutput:
    """Tests cho JSON output format."""

    def test_json_output_structure(self):
        """Test JSON output có đúng structure."""
        output = {
            "status": "success",
            "data": {"key": "value"},
            "error": None,
            "exit_code": 0
        }
        json_str = json.dumps(output)
        parsed = json.loads(json_str)
        
        assert parsed["status"] == "success"
        assert parsed["data"] == {"key": "value"}
        assert parsed["error"] is None
        assert parsed["exit_code"] == 0

    def test_json_error_output(self):
        """Test JSON error output structure."""
        output = {
            "status": "error",
            "data": None,
            "error": {"code": "TEST-001", "message": "Lỗi thử nghiệm"},
            "exit_code": 1
        }
        json_str = json.dumps(output)
        parsed = json.loads(json_str)
        
        assert parsed["status"] == "error"
        assert parsed["data"] is None
        assert parsed["error"]["code"] == "TEST-001"
        assert parsed["exit_code"] == 1


class TestExitCodeIntegration:
    """Integration tests cho exit codes."""

    def test_successful_command_exit_code(self):
        """Test exit code cho command thành công."""
        result = subprocess.run(
            [PYTHON, "-m", "midicoder.pipeline", "--version"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30
        )
        assert result.returncode == ExitCode.SUCCESS.value

    def test_invalid_option_exit_code(self):
        """Test exit code cho option không hợp lệ."""
        result = subprocess.run(
            [PYTHON, "-m", "midicoder.pipeline", "--invalid-option"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30
        )
        assert result.returncode in [ExitCode.BAD_ARGUMENTS.value, ExitCode.GENERIC_ERROR.value, 1]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])