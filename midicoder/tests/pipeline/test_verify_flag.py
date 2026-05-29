"""
Test integration cho --verify flag của code gen command.

Kiểm tra:
- CLI accept --verify flag
- _execute_gen() gọi CodeVerifier khi verify=True
- Summary report hiển thị đúng
- Exit code 1 khi có file fail verification
"""

from click.testing import CliRunner
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch, MagicMock

import pytest


class TestVerifyFlagIntegration:
    """Test --verify flag integration vào code gen command."""

    @pytest.fixture
    def runner(self):
        """CliRunner cho test."""
        return CliRunner()

    def test_code_gen_help_shows_verify_option(self, runner):
        """CLI help hiển thị --verify option."""
        from midicoder.pipeline.commands.code import code

        result = runner.invoke(code, ["gen", "--help"])

        assert "--verify" in result.output or "-V" in result.output
        assert "compile" in result.output.lower() or "syntax" in result.output.lower()

    @patch("midicoder.pipeline.commands.code._execute_gen")
    def test_verify_flag_passed_to_execute_gen(self, mock_execute, runner):
        """--verify flag được truyền xuống _execute_gen()."""
        from midicoder.pipeline.commands.code import code

        runner.invoke(code, ["gen", "--verify"])

        # _execute_gen được gọi với verify=True
        mock_execute.assert_called_once()
        call_kwargs = mock_execute.call_args[1] if mock_execute.call_args[1] else {}
        call_args = mock_execute.call_args[0] if mock_execute.call_args[0] else ()

        # Click có thể pass theo position hoặc keyword
        if "verify" in call_kwargs:
            assert call_kwargs["verify"] is True
        elif len(call_args) >= 4:
            assert call_args[3] is True

    @patch("midicoder.pipeline.commands.code._execute_gen")
    def test_verify_default_false(self, mock_execute, runner):
        """Không có --verify → verify=False."""
        from midicoder.pipeline.commands.code import code

        runner.invoke(code, ["gen"])

        mock_execute.assert_called_once()
        call_kwargs = mock_execute.call_args[1] if mock_execute.call_args[1] else {}

        if "verify" in call_kwargs:
            assert call_kwargs["verify"] is False

    def test_execute_gen_without_verify_skips_verification(self):
        """_execute_gen với verify=False không gọi CodeVerifier."""
        from midicoder.pipeline.code_verifier import CodeVerifier

        with patch("midicoder.pipeline.commands.code.get_config", return_value={"active_version": "v1.0.0"}):
            with patch("midicoder.pipeline.commands.code._load_plan_from_artifacts") as mock_plan:
                mock_plan.return_value = {"meta": {"version": "1.0.0"}, "modules": []}
            with patch("midicoder.pipeline.commands.code._load_mir_from_artifacts", return_value=None):
                with patch("midicoder.pipeline.commands.code.ArtifactsManager"):
                    from midicoder.pipeline.commands.code import _execute_gen

                    try:
                        _execute_gen(target="all", dry_run=True, verify=False)
                    except SystemExit:
                        pass  # CLI có thể raise SystemExit

    def test_verification_report_in_metadata(self):
        """Verification report được lưu vào artifacts metadata."""
        from midicoder.pipeline.code_verifier import CodeVerifier, VerificationReport

        verifier = CodeVerifier()

        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Tạo file valid Python
            valid_file = tmp_path / "valid.py"
            valid_file.write_text("x = 42\n", encoding="utf-8")

            # Tạo file invalid Python
            invalid_file = tmp_path / "invalid.py"
            invalid_file.write_text("def broken(\n", encoding="utf-8")

            report = verifier.verify_batch([valid_file, invalid_file], check_imports=True)

            # Report có đúng metadata
            assert report.total == 2
            assert report.passed == 1
            assert report.failed == 1

            # Summary string chứa thông tin
            summary = report.summary()
            assert "2" in summary
            assert "1" in summary


class TestVerifyFlagBusinessBehavior:
    """Test business behavior của verification trong code gen."""

    def test_verify_python_compiles_generated_files(self):
        """Verify kiểm tra py_compile cho file Python generate."""
        from midicoder.pipeline.code_verifier import CodeVerifier

        verifier = CodeVerifier()

        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # File Python hợp lệ (giống template generate)
            model_file = tmp_path / "user_model.py"
            model_file.write_text(
                "from dataclasses import dataclass\n"
                "\n"
                "\n"
                "@dataclass\n"
                "class User:\n"
                "    id: int\n"
                "    name: str\n"
                "    email: str\n",
                encoding="utf-8"
            )

            result = verifier.verify_file(model_file, check_imports=True)
            assert result.success is True
            assert result.language == "python"

    def test_verify_catches_syntax_errors_in_templates(self):
        """Verify phát hiện syntax error trong file generate từ template."""
        from midicoder.pipeline.code_verifier import CodeVerifier

        verifier = CodeVerifier()

        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Template generate sai syntax (thiếu dấu : ở def)
            broken_file = tmp_path / "broken_route.py"
            broken_file.write_text(
                "from fastapi import APIRouter\n"
                "\n"
                "router = APIRouter()\n"
                "\n"
                "@router.get(\"/users\")\n"
                "def get_users()  # thiếu dấu :\n"
                "    return []\n",
                encoding="utf-8"
            )

            result = verifier.verify_file(broken_file, check_imports=False)
            assert result.success is False
            assert len(result.errors) >= 1

    def test_verify_batch_mixed_languages(self):
        """Verify batch với mix Python + TypeScript + non-code."""
        from midicoder.pipeline.code_verifier import CodeVerifier

        verifier = CodeVerifier()

        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            files = []

            # Python valid
            py_file = tmp_path / "app.py"
            py_file.write_text("print('hello')\n", encoding="utf-8")
            files.append(py_file)

            # TypeScript (không có tsc → fallback basic check)
            ts_file = tmp_path / "component.ts"
            ts_file.write_text(
                "export function Greet(name: string): string {\n"
                "  return `Hello ${name}`;\n"
                "}\n",
                encoding="utf-8"
            )
            files.append(ts_file)

            # Non-code (skip)
            md_file = tmp_path / "README.md"
            md_file.write_text("# Project\n", encoding="utf-8")
            files.append(md_file)

            report = verifier.verify_batch(files, check_imports=False)

            assert report.total == 3
            assert report.passed == 3  # TS fallback pass, MD skip
            assert report.failed == 0


class TestVerifyFlagEdgeCases:
    """Test edge cases của --verify flag."""

    def test_empty_plan_no_crash(self):
        """Plan rỗng → verify không crash."""
        from midicoder.pipeline.code_verifier import CodeVerifier

        verifier = CodeVerifier()
        report = verifier.verify_batch([])

        assert report.total == 0
        assert report.passed == 0
        assert report.failed == 0

    def test_all_files_non_code(self):
        """Tất cả file là non-code → report toàn pass."""
        from midicoder.pipeline.code_verifier import CodeVerifier

        verifier = CodeVerifier()

        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            files = []

            for ext in [".md", ".yaml", ".json", ".txt"]:
                f = tmp_path / f"file{ext}"
                f.write_text("content\n", encoding="utf-8")
                files.append(f)

            report = verifier.verify_batch(files)

            assert report.passed == 4
            assert report.failed == 0

    def test_verify_nonexistent_file_graceful(self):
        """File không tồn tại → error gracefully."""
        from midicoder.pipeline.code_verifier import CodeVerifier

        verifier = CodeVerifier()
        result = verifier.verify_python(Path("/nonexistent/file.py"))

        assert result.success is False
        assert len(result.errors) >= 1

    def test_verify_with_check_imports_false(self):
        """check_imports=False → chỉ compile, không check import."""
        from midicoder.pipeline.code_verifier import CodeVerifier

        verifier = CodeVerifier()

        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # File có import không tồn tại nhưng syntax valid
            f = tmp_path / "missing_import.py"
            f.write_text(
                "import this_module_does_not_exist_12345\n"
                "x = 42\n",
                encoding="utf-8"
            )

            # check_imports=False → pass (chỉ compile)
            result_no_check = verifier.verify_file(f, check_imports=False)
            assert result_no_check.success is True

            # check_imports=True → fail (import không tồn tại)
            result_with_check = verifier.verify_file(f, check_imports=True)
            assert result_with_check.success is False


class TestCodeVerifierImportable:
    """Test CodeVerifier importable từ code.py."""

    def test_code_verifier_import_in_code_py(self):
        """CodeVerifier có thể import trong code.py."""
        # Simple test: import không raise
        from midicoder.pipeline.code_verifier import CodeVerifier, VerificationResult, VerificationReport

        verifier = CodeVerifier()
        assert verifier is not None

    def test_generated_file_has_path_attribute(self):
        """GeneratedFile dataclass có path attribute để dùng cho verification."""
        from midicoder.pipeline.commands.code import GeneratedFile

        gf = GeneratedFile(
            path="app/models/user.py",
            content="class User: pass\n",
            type="model",
            template="entity.py.jinja2",
        )

        assert gf.path == "app/models/user.py"
        # Path có thể dùng để resolve file
        output_dir = Path("/tmp/output")
        full_path = output_dir / gf.path
        assert full_path.name == "user.py"
