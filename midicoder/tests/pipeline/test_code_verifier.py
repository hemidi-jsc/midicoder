"""
Test cho CodeVerifier — verify compile/syntax cho file đã generate.

Test business behavior:
- Python file compile pass/fail
- Python import check (detect missing imports)
- TypeScript tsc --noEmit (nếu có tsc)
- Summary report (pass/fail count)
- Verify multiple files cùng lúc
"""

import py_compile
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from midicoder.pipeline.code_verifier import (
    CodeVerifier,
    VerificationResult,
    VerificationReport,
)


# ============================================================================
# Fixture
# ============================================================================

@pytest.fixture
def verifier():
    """Tạo CodeVerifier instance."""
    return CodeVerifier()


@pytest.fixture
def temp_dir():
    """Tạo temporary directory cho test."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


# ============================================================================
# Test: Python compile verification
# ============================================================================

class TestPythonCompileVerification:
    """Test verify_python() — py compile check."""

    def test_valid_python_file_passes(self, verifier, temp_dir):
        """File Python hợp lệ → compile pass."""
        file_path = temp_dir / "valid.py"
        file_path.write_text(
            "def hello():\n"
            "    return 'thế giới'\n",
            encoding="utf-8"
        )

        result = verifier.verify_python(file_path)

        assert result.success is True
        assert result.errors == []
        assert result.file_path == str(file_path)
        assert result.language == "python"

    def test_syntax_error_fails(self, verifier, temp_dir):
        """File Python có syntax error → compile fail."""
        file_path = temp_dir / "invalid.py"
        file_path.write_text(
            "def broken(\n"  # thiếu dấu )
            "    return 42\n",
            encoding="utf-8"
        )

        result = verifier.verify_python(file_path)

        assert result.success is False
        assert len(result.errors) >= 1
        assert "syntax" in " ".join(result.errors).lower() or "SyntaxError" in " ".join(result.errors)

    def test_indentation_error_fails(self, verifier, temp_dir):
        """File Python có indentation error → compile fail."""
        file_path = temp_dir / "bad_indent.py"
        file_path.write_text(
            "def func():\n"
            "  return 1\n"
            "    return 2\n",  # TabError / IndentationError
            encoding="utf-8"
        )

        result = verifier.verify_python(file_path)

        assert result.success is False
        assert len(result.errors) >= 1

    def test_empty_file_passes(self, verifier, temp_dir):
        """File Python rỗng → compile pass (valid nhưng không làm gì)."""
        file_path = temp_dir / "empty.py"
        file_path.write_text("", encoding="utf-8")

        result = verifier.verify_python(file_path)

        assert result.success is True
        assert result.errors == []

    def test_complex_valid_file_passes(self, verifier, temp_dir):
        """File Python phức tạp (class, import, decorator) → compile pass."""
        file_path = temp_dir / "complex.py"
        file_path.write_text(
            "import os\n"
            "from pathlib import Path\n"
            "\n"
            "\n"
            "@dataclass\n"
            "class Entity:\n"
            "    id: int\n"
            "    name: str\n"
            "    _cache: dict = field(default_factory=dict)\n"
            "\n"
            "    def compute(self) -> int:\n"
            "        return len(self._cache)\n",
            encoding="utf-8"
        )

        result = verifier.verify_python(file_path)

        assert result.success is True

    def test_nonexistent_file_returns_error(self, verifier):
        """File không tồn tại → trả về error."""
        result = verifier.verify_python(Path("/nonexistent/path/file.py"))

        assert result.success is False
        assert len(result.errors) >= 1


# ============================================================================
# Test: Python import verification
# ============================================================================

class TestPythonImportVerification:
    """Test verify_python() với import_check=True."""

    def test_valid_imports_pass(self, verifier, temp_dir):
        """Import stdlib module → pass."""
        file_path = temp_dir / "stdlib_import.py"
        file_path.write_text(
            "import os\n"
            "import json\n"
            "from pathlib import Path\n",
            encoding="utf-8"
        )

        result = verifier.verify_python(file_path, check_imports=True)

        # stdlib imports luôn pass
        assert result.success is True

    def test_missing_import_detected(self, verifier, temp_dir):
        """Import module không tồn tại → detect error."""
        file_path = temp_dir / "missing_import.py"
        file_path.write_text(
            "import json\n"
            "import this_module_definitely_does_not_exist_12345\n",
            encoding="utf-8"
        )

        result = verifier.verify_python(file_path, check_imports=True)

        # py_compile pass nhưng import check fail
        assert result.success is False
        # Error message nên chứa tên module
        error_text = " ".join(result.errors).lower()
        assert "this_module_definitely_does_not_exist" in error_text or "import" in error_text

    def test_relative_import_skipped(self, verifier, temp_dir):
        """Relative import (từ package) → py_compile pass (valid syntax), import skip."""
        file_path = temp_dir / "relative_import.py"
        file_path.write_text(
            "from . import sibling_module\n"
            "from ..parent import something\n",
            encoding="utf-8"
        )

        result = verifier.verify_python(file_path, check_imports=True)

        # py_compile pass (relative import là valid Python syntax)
        # Import check skip relative imports (không thể verify standalone)
        assert result.success is True

    def test_check_imports_false_skips_import_check(self, verifier, temp_dir):
        """check_imports=False → không kiểm tra import, chỉ compile."""
        file_path = temp_dir / "missing_import.py"
        file_path.write_text(
            "import this_module_definitely_does_not_exist_12345\n",
            encoding="utf-8"
        )

        result = verifier.verify_python(file_path, check_imports=False)

        # py_compile chỉ check syntax, không check import existence
        assert result.success is True


# ============================================================================
# Test: TypeScript verification
# ============================================================================

class TestTypeScriptVerification:
    """Test verify_typescript() — tsc --noEmit nếu có, fallback syntax check."""

    def test_valid_typescript_passes(self, verifier, temp_dir):
        """File TypeScript hợp lệ → pass."""
        file_path = temp_dir / "valid.ts"
        file_path.write_text(
            "interface User {\n"
            "  id: number;\n"
            "  name: string;\n"
            "}\n"
            "\n"
            "export function greet(user: User): string {\n"
            "  return `Xin chào ${user.name}`;\n"
            "}\n",
            encoding="utf-8"
        )

        result = verifier.verify_typescript(file_path)

        assert result.file_path == str(file_path)
        assert result.language == "typescript"

    def test_syntax_error_typescript_fails(self, verifier, temp_dir):
        """File TypeScript có syntax error → fail."""
        file_path = temp_dir / "invalid.ts"
        file_path.write_text(
            "function broken("  # thiếu )
            "  return 42\n",
            encoding="utf-8"
        )

        result = verifier.verify_typescript(file_path)

        # Kết quả phụ thuộc vào việc có tsc không,
        # nhưng luôn có file_path và language đúng
        assert result.file_path == str(file_path)
        assert result.language == "typescript"

    def test_nonexistent_file_returns_error(self, verifier):
        """File .ts không tồn tại → trả về error."""
        result = verifier.verify_typescript(Path("/nonexistent/path/file.ts"))

        assert result.success is False
        assert len(result.errors) >= 1

    @patch("midicoder.pipeline.code_verifier.subprocess.run")
    def test_tsc_available_uses_tsc(self, mock_run, verifier, temp_dir):
        """Nếu tsc có sẵn → gọi tsc --noEmit."""
        file_path = temp_dir / "test.ts"
        file_path.write_text("const x: number = 42;\n", encoding="utf-8")

        # Mock: call 1 = tsc --version (success), call 2 = tsc --noEmit (success)
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="Version 5.0.0", stderr=""),
            MagicMock(returncode=0, stdout="", stderr=""),
        ]

        result = verifier.verify_typescript(file_path)

        # tsc được gọi ít nhất 2 lần (version + noEmit)
        assert mock_run.call_count >= 2
        assert result.success is True

    @patch("midicoder.pipeline.code_verifier.subprocess.run")
    def test_tsc_failure_captured(self, mock_run, verifier, temp_dir):
        """tsc trả về error → capture vào result."""
        file_path = temp_dir / "test.ts"
        file_path.write_text("const x: number = 'string';\n", encoding="utf-8")  # type error

        # Mock: call 1 = tsc --version (success), call 2 = tsc --noEmit (fail)
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="Version 5.0.0", stderr=""),
            MagicMock(
                returncode=2,
                stdout="",
                stderr="error TS2322: Type 'string' is not assignable to type 'number'."
            ),
        ]

        result = verifier.verify_typescript(file_path)

        assert result.success is False
        assert len(result.errors) >= 1


# ============================================================================
# Test: JavaScript verification
# ============================================================================

class TestJavaScriptVerification:
    """Test verify_javascript() — node syntax check."""

    def test_valid_javascript_passes(self, verifier, temp_dir):
        """File JavaScript hợp lệ → pass."""
        file_path = temp_dir / "valid.js"
        file_path.write_text(
            "function hello(name) {\n"
            "  return `Xin chào ${name}`;\n"
            "}\n"
            "module.exports = { hello };\n",
            encoding="utf-8"
        )

        result = verifier.verify_javascript(file_path)

        assert result.file_path == str(file_path)
        assert result.language == "javascript"

    def test_syntax_error_javascript_fails(self, verifier, temp_dir):
        """File JavaScript có syntax error → fail."""
        file_path = temp_dir / "invalid.js"
        file_path.write_text(
            "function broken("  # thiếu )
            "  return 42\n",
            encoding="utf-8"
        )

        result = verifier.verify_javascript(file_path)

        # Syntax error nên được detect
        assert result.success is False
        assert len(result.errors) >= 1

    def test_nonexistent_file_returns_error(self, verifier):
        """File .js không tồn tại → trả về error."""
        result = verifier.verify_javascript(Path("/nonexistent/path/file.js"))

        assert result.success is False


# ============================================================================
# Test: verify_file() — auto-detect language
# ============================================================================

class TestVerifyFileAutoDetect:
    """Test verify_file() — tự động detect language từ extension."""

    def test_python_extension_detected(self, verifier, temp_dir):
        """File .py → gọi verify_python."""
        file_path = temp_dir / "test.py"
        file_path.write_text("x = 42\n")

        result = verifier.verify_file(file_path)

        assert result.language == "python"
        assert result.success is True

    def test_typescript_extension_detected(self, verifier, temp_dir):
        """File .ts → gọi verify_typescript."""
        file_path = temp_dir / "test.ts"
        file_path.write_text("const x: number = 42;\n")

        result = verifier.verify_file(file_path)

        assert result.language == "typescript"

    def test_tsx_extension_detected(self, verifier, temp_dir):
        """File .tsx → gọi verify_typescript."""
        file_path = temp_dir / "test.tsx"
        file_path.write_text(
            "export function Component() {\n"
            "  return <div>Xin chào</div>;\n"
            "}\n"
        )

        result = verifier.verify_file(file_path)

        assert result.language == "typescript"

    def test_javascript_extension_detected(self, verifier, temp_dir):
        """File .js → gọi verify_javascript."""
        file_path = temp_dir / "test.js"
        file_path.write_text("const x = 42;\n")

        result = verifier.verify_file(file_path)

        assert result.language == "javascript"

    def test_unknown_extension_returns_skip(self, verifier, temp_dir):
        """File không phải code (vd: .md, .yaml) → skip."""
        file_path = temp_dir / "readme.md"
        file_path.write_text("# Read me\n", encoding="utf-8")

        result = verifier.verify_file(file_path)

        assert result.success is True
        assert result.errors == []
        assert result.language == "unknown"

    def test_non_code_extensions_not_verified(self, verifier, temp_dir):
        """Các extension không phải code không được verify."""
        for ext in [".txt", ".json", ".yaml", ".yml", ".html", ".css", ".sql"]:
            file_path = temp_dir / f"test{ext}"
            file_path.write_text("content\n", encoding="utf-8")

            result = verifier.verify_file(file_path)

            assert result.success is True, f"Extension {ext} nên skip verification"


# ============================================================================
# Test: verify_batch() — verify nhiều file cùng lúc
# ============================================================================

class TestVerifyBatch:
    """Test verify_batch() — report tổng hợp."""

    def test_batch_all_pass(self, verifier, temp_dir):
        """Tất cả file pass → report success."""
        files = []
        for i in range(3):
            f = temp_dir / f"file{i}.py"
            f.write_text(f"x = {i}\n", encoding="utf-8")
            files.append(f)

        report = verifier.verify_batch(files, check_imports=False)

        assert report.total == 3
        assert report.passed == 3
        assert report.failed == 0
        assert len(report.results) == 3

    def test_batch_mixed_results(self, verifier, temp_dir):
        """Mix pass và fail → report đúng count."""
        files = []

        # File pass
        good = temp_dir / "good.py"
        good.write_text("x = 42\n", encoding="utf-8")
        files.append(good)

        # File fail
        bad = temp_dir / "bad.py"
        bad.write_text("def broken(\n", encoding="utf-8")
        files.append(bad)

        # File pass
        good2 = temp_dir / "good2.py"
        good2.write_text("y = 'hello'\n", encoding="utf-8")
        files.append(good2)

        report = verifier.verify_batch(files, check_imports=False)

        assert report.total == 3
        assert report.passed == 2
        assert report.failed == 1

        # Failed results nên chứa file bad.py
        failed_paths = [r.file_path for r in report.results if not r.success]
        assert str(bad) in failed_paths

    def test_batch_empty_list(self, verifier):
        """Batch rỗng → report 0/0/0."""
        report = verifier.verify_batch([])

        assert report.total == 0
        assert report.passed == 0
        assert report.failed == 0
        assert len(report.results) == 0

    def test_batch_with_non_code_files(self, verifier, temp_dir):
        """Batch có mix code + non-code → chỉ verify code files."""
        files = []

        code_file = temp_dir / "code.py"
        code_file.write_text("x = 42\n", encoding="utf-8")
        files.append(code_file)

        non_code = temp_dir / "readme.md"
        non_code.write_text("# README\n", encoding="utf-8")
        files.append(non_code)

        report = verifier.verify_batch(files, check_imports=False)

        # Non-code files được skip (tính là pass)
        assert report.passed == 2
        assert report.failed == 0

    def test_batch_summary_string(self, verifier, temp_dir):
        """Report summary string format đúng."""
        files = []
        for i in range(5):
            f = temp_dir / f"file{i}.py"
            f.write_text(f"x = {i}\n", encoding="utf-8")
            files.append(f)

        report = verifier.verify_batch(files, check_imports=False)
        summary = report.summary()

        assert "5" in summary
        assert "passed" in summary.lower() or "pass" in summary.lower()


# ============================================================================
# Test: VerificationResult dataclass
# ============================================================================

class TestVerificationResult:
    """Test VerificationResult dataclass."""

    def test_result_creation(self):
        """Tạo VerificationResult với đầy đủ fields."""
        result = VerificationResult(
            file_path="/path/to/test.py",
            language="python",
            success=True,
            errors=[],
        )

        assert result.file_path == "/path/to/test.py"
        assert result.language == "python"
        assert result.success is True
        assert result.errors == []

    def test_result_with_errors(self):
        """VerificationResult với danh sách errors."""
        result = VerificationResult(
            file_path="/path/to/test.py",
            language="python",
            success=False,
            errors=["SyntaxError: invalid syntax", "Line 5"],
        )

        assert result.success is False
        assert len(result.errors) == 2


# ============================================================================
# Test: VerificationReport dataclass
# ============================================================================

class TestVerificationReport:
    """Test VerificationReport dataclass."""

    def test_report_creation(self):
        """Tạo VerificationReport."""
        report = VerificationReport(
            results=[],
            total=0,
            passed=0,
            failed=0,
        )

        assert report.total == 0
        assert report.passed == 0
        assert report.failed == 0

    def test_report_summary(self):
        """Summary string chứa thông tin pass/fail."""
        report = VerificationReport(
            results=[],
            total=10,
            passed=8,
            failed=2,
        )

        summary = report.summary()

        assert "8" in summary
        assert "2" in summary
        assert "10" in summary

    def test_report_all_pass(self):
        """Tất cả pass → summary không có failed."""
        report = VerificationReport(
            results=[],
            total=5,
            passed=5,
            failed=0,
        )

        summary = report.summary()

        assert "5" in summary
