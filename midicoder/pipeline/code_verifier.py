"""
Code Verifier — Kiểm tra compile/syntax cho file đã generate.

Hỗ trợ:
- Python: py_compile + import check
- TypeScript: tsc --noEmit (nếu có)
- JavaScript: node check

Dùng trong Phase 0.1 — thêm --verify flag vào `code gen`.
"""

import ast
import py_compile
import subprocess
import sys
import tempfile
import tokenize
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class VerificationResult:
    """
    Kết quả verification của một file.

    Attributes:
        file_path: Đường dẫn file đã verify
        language: Ngôn ngữ (python, typescript, javascript, unknown)
        success: True nếu verify pass
        errors: Danh sách error messages (trống nếu pass)
    """
    file_path: str
    language: str
    success: bool
    errors: list[str] = field(default_factory=list)


@dataclass
class VerificationReport:
    """
    Báo cáo tổng hợp verification cho nhiều file.

    Attributes:
        results: Danh sách tất cả kết quả
        total: Tổng số file
        passed: Số file pass
        failed: Số file fail
    """
    results: list[VerificationResult]
    total: int
    passed: int
    failed: int

    def summary(self) -> str:
        """Trả về summary string ngắn gọn."""
        lines = [
            f"Verification: {self.total} files checked",
            f"  ✓ Passed: {self.passed}",
            f"  ✗ Failed: {self.failed}",
        ]
        if self.failed > 0:
            lines.append("")
            lines.append("Files failed:")
            for r in self.results:
                if not r.success:
                    lines.append(f"  - {r.file_path}")
                    for err in r.errors:
                        lines.append(f"    → {err}")
        return "\n".join(lines)


class CodeVerifier:
    """
    Verifier cho code files đã generate.

    Verify compile/syntax đúng trước khi apply code vào target directory.
    """

    # Mapping extension → language
    LANGUAGE_MAP: dict[str, str] = {
        ".py": "python",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".js": "javascript",
        ".jsx": "javascript",
    }

    def verify_file(
        self,
        file_path: Path,
        check_imports: bool = False,
    ) -> VerificationResult:
        """
        Verify một file — tự động detect language từ extension.

        Args:
            file_path: Đường dẫn file
            check_imports: Nếu True, kiểm tra import validity (chỉ Python)

        Returns:
            VerificationResult
        """
        suffix = file_path.suffix
        language = self.LANGUAGE_MAP.get(suffix)

        if language is None:
            # Không phải code file — skip verification (tính là pass)
            return VerificationResult(
                file_path=str(file_path),
                language="unknown",
                success=True,
                errors=[],
            )

        if language == "python":
            return self.verify_python(file_path, check_imports=check_imports)
        elif language == "typescript":
            return self.verify_typescript(file_path)
        elif language == "javascript":
            return self.verify_javascript(file_path)

        # Language không hỗ trợ — trả về skip
        return VerificationResult(
            file_path=str(file_path),
            language=language,
            success=True,
            errors=[],
        )

    def verify_python(
        self,
        file_path: Path,
        check_imports: bool = False,
    ) -> VerificationResult:
        """
        Verify file Python — py_compile + (optional) import check.

        Bước 1: py_compile.compile() — check syntax
        Bước 2 (nếu check_imports): parse AST và kiểm tra import validity

        Args:
            file_path: Đường dẫn file .py
            check_imports: Nếu True, kiểm tra import modules tồn tại

        Returns:
            VerificationResult
        """
        errors = []

        # Kiểm tra file tồn tại
        if not file_path.exists():
            return VerificationResult(
                file_path=str(file_path),
                language="python",
                success=False,
                errors=[f"File không tồn tại: {file_path}"],
            )

        # Bước 1: py_compile — syntax check
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                py_compile.compile(
                    str(file_path),
                    cfile=str(Path(tmpdir) / f"{file_path.stem}.pyc"),
                    doraise=True,
                )
        except py_compile.PyCompileError as e:
            return VerificationResult(
                file_path=str(file_path),
                language="python",
                success=False,
                errors=[f"Compile error: {e}"],
            )
        except SyntaxError as e:
            return VerificationResult(
                file_path=str(file_path),
                language="python",
                success=False,
                errors=[f"Syntax error: {e}"],
            )

        # Bước 2: Import check (optional)
        if check_imports:
            errors.extend(self._check_python_imports(file_path))

        return VerificationResult(
            file_path=str(file_path),
            language="python",
            success=len(errors) == 0,
            errors=errors,
        )

    def _check_python_imports(self, file_path: Path) -> list[str]:
        """
        Kiểm tra import statements trong file Python.

        Parse AST và thử import từng module để detect missing imports.

        Args:
            file_path: Đường dẫn file .py

        Returns:
            Danh sách error messages (trống nếu tất cả imports valid)
        """
        errors = []

        try:
            source = file_path.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except SyntaxError as e:
            # Đã được py_compile catch rồi, nhưng fallback
            return [f"Không thể parse AST: {e}"]
        except Exception as e:
            return [f"Lỗi đọc file: {e}"]

        # builtin modules — không cần check
        import builtins
        builtin_names = set(dir(builtins))

        # stdlib modules phổ biến (không check existence, luôn valid)
        stdlib_whitelist = {
            "os", "sys", "json", "pathlib", "typing", "dataclasses",
            "collections", "functools", "itertools", "abc", "enum",
            "datetime", "time", "math", "random", "re", "string",
            "io", "tempfile", "shutil", "glob", "logging", "unittest",
            "pytest", "click", "pydantic", "fastapi", "uvicorn",
            "sqlalchemy", "alembic", "httpx", "requests",
            # stdlib built-in (luôn có)
            "importlib", "importlib.metadata", "importlib.util",
        }

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name.split(".")[0]  # "os.path" → "os"
                    if module_name in builtin_names or module_name in stdlib_whitelist:
                        continue
                    if not self._is_importable(module_name):
                        errors.append(f"Import không tìm thấy: {alias.name}")

            elif isinstance(node, ast.ImportFrom):
                if node.module is None:
                    # Relative import — skip (không thể verify standalone)
                    continue
                if node.level and node.level > 0:
                    # Relative import (vd: from . import foo) — skip
                    continue
                top_level = node.module.split(".")[0]
                if top_level in builtin_names or top_level in stdlib_whitelist:
                    continue
                if not self._is_importable(top_level):
                    errors.append(f"Import không tìm thấy: {node.module}")

        return errors

    def _is_importable(self, module_name: str) -> bool:
        """
        Kiểm tra module có thể import được không.

        Args:
            module_name: Tên module

        Returns:
            True nếu import thành công
        """
        try:
            import importlib
            importlib.import_module(module_name)
            return True
        except ImportError:
            return False

    def verify_typescript(self, file_path: Path) -> VerificationResult:
        """
        Verify file TypeScript — tsc --noEmit nếu có, fallback syntax check.

        Args:
            file_path: Đường dẫn file .ts hoặc .tsx

        Returns:
            VerificationResult
        """
        # Kiểm tra file tồn tại
        if not file_path.exists():
            return VerificationResult(
                file_path=str(file_path),
                language="typescript",
                success=False,
                errors=[f"File không tồn tại: {file_path}"],
            )

        # Thử gọi tsc --noEmit
        tsc_result = self._try_tsc(file_path)
        if tsc_result is not None:
            return tsc_result

        # Fallback: basic syntax check (không có tsc)
        return self._check_typescript_syntax(file_path)

    def _try_tsc(self, file_path: Path) -> Optional[VerificationResult]:
        """
        Thử chạy tsc --noEmit nếu TypeScript compiler có sẵn.

        Returns:
            VerificationResult nếu tsc có sẵn, None nếu không
        """
        try:
            # Kiểm tra tsc có sẵn không
            result = subprocess.run(
                ["tsc", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                return None

            # Chạy tsc --noEmit
            result = subprocess.run(
                ["tsc", "--noEmit", "--strict", str(file_path)],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                return VerificationResult(
                    file_path=str(file_path),
                    language="typescript",
                    success=True,
                    errors=[],
                )
            else:
                errors = []
                if result.stderr:
                    errors.append(f"TypeScript error: {result.stderr.strip()}")
                if result.stdout:
                    # tsc đôi khi output error qua stdout
                    output_lines = result.stdout.strip().split("\n")
                    for line in output_lines:
                        if "error TS" in line:
                            errors.append(line.strip())
                if not errors:
                    errors.append(f"tsc failed with exit code {result.returncode}")

                return VerificationResult(
                    file_path=str(file_path),
                    language="typescript",
                    success=False,
                    errors=errors,
                )

        except FileNotFoundError:
            # tsc không cài đặt
            return None
        except subprocess.TimeoutExpired:
            return VerificationResult(
                file_path=str(file_path),
                language="typescript",
                success=False,
                errors=["tsc timeout sau 60 giây"],
            )

    def _check_typescript_syntax(self, file_path: Path) -> VerificationResult:
        """
        Basic syntax check cho TypeScript (không có tsc).

        Dùng method đơn giản: check balanced braces/parentheses.

        Args:
            file_path: Đường dẫn file .ts

        Returns:
            VerificationResult
        """
        try:
            content = file_path.read_text(encoding="utf-8")

            # Basic checks
            errors = []

            # Check balanced braces
            brace_count = content.count("{") - content.count("}")
            if brace_count != 0:
                errors.append(f"Unbalanced braces (net: {brace_count})")

            # Check balanced parentheses
            paren_count = content.count("(") - content.count(")")
            if paren_count != 0:
                errors.append(f"Unbalanced parentheses (net: {paren_count})")

            # Check balanced brackets
            bracket_count = content.count("[") - content.count("]")
            if bracket_count != 0:
                errors.append(f"Unbalanced brackets (net: {bracket_count})")

            return VerificationResult(
                file_path=str(file_path),
                language="typescript",
                success=len(errors) == 0,
                errors=errors,
            )

        except Exception as e:
            return VerificationResult(
                file_path=str(file_path),
                language="typescript",
                success=False,
                errors=[f"Lỗi đọc file: {e}"],
            )

    def verify_javascript(self, file_path: Path) -> VerificationResult:
        """
        Verify file JavaScript — node syntax check.

        Args:
            file_path: Đường dẫn file .js hoặc .jsx

        Returns:
            VerificationResult
        """
        # Kiểm tra file tồn tại
        if not file_path.exists():
            return VerificationResult(
                file_path=str(file_path),
                language="javascript",
                success=False,
                errors=[f"File không tồn tại: {file_path}"],
            )

        # Thử Node.js syntax check
        node_result = self._try_node_check(file_path)
        if node_result is not None:
            return node_result

        # Fallback: basic syntax check
        return self._check_basic_syntax(file_path)

    def _try_node_check(self, file_path: Path) -> Optional[VerificationResult]:
        """
        Thử chạy node để check syntax JavaScript.

        Returns:
            VerificationResult nếu node có sẵn, None nếu không
        """
        try:
            # Check node có sẵn không
            result = subprocess.run(
                ["node", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                return None

            # Syntax check: node --check (chỉ check syntax, không execute)
            result = subprocess.run(
                ["node", "--check", str(file_path)],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                return VerificationResult(
                    file_path=str(file_path),
                    language="javascript",
                    success=True,
                    errors=[],
                )
            else:
                errors = []
                if result.stderr:
                    errors.append(f"JavaScript error: {result.stderr.strip()}")
                if not errors:
                    errors.append(f"node --check failed with exit code {result.returncode}")

                return VerificationResult(
                    file_path=str(file_path),
                    language="javascript",
                    success=False,
                    errors=errors,
                )

        except FileNotFoundError:
            return None
        except subprocess.TimeoutExpired:
            return VerificationResult(
                file_path=str(file_path),
                language="javascript",
                success=False,
                errors=["node --check timeout sau 30 giây"],
            )

    def _check_basic_syntax(self, file_path: Path) -> VerificationResult:
        """
        Basic syntax check (không có node/tsc).

        Check balanced braces/parentheses/brackets.

        Args:
            file_path: Đường dẫn file

        Returns:
            VerificationResult
        """
        try:
            content = file_path.read_text(encoding="utf-8")

            errors = []
            brace_count = content.count("{") - content.count("}")
            if brace_count != 0:
                errors.append(f"Unbalanced braces (net: {brace_count})")

            paren_count = content.count("(") - content.count(")")
            if paren_count != 0:
                errors.append(f"Unbalanced parentheses (net: {paren_count})")

            bracket_count = content.count("[") - content.count("]")
            if bracket_count != 0:
                errors.append(f"Unbalanced brackets (net: {bracket_count})")

            return VerificationResult(
                file_path=str(file_path),
                language=file_path.suffix.lstrip("."),
                success=len(errors) == 0,
                errors=errors,
            )

        except Exception as e:
            return VerificationResult(
                file_path=str(file_path),
                language="unknown",
                success=False,
                errors=[f"Lỗi đọc file: {e}"],
            )

    def verify_batch(
        self,
        file_paths: list[Path],
        check_imports: bool = False,
    ) -> VerificationReport:
        """
        Verify danh sách file cùng lúc.

        Args:
            file_paths: Danh sách đường dẫn file
            check_imports: Nếu True, kiểm tra import validity

        Returns:
            VerificationReport tổng hợp
        """
        results = []
        passed = 0
        failed = 0

        for fp in file_paths:
            result = self.verify_file(fp, check_imports=check_imports)
            results.append(result)
            if result.success:
                passed += 1
            else:
                failed += 1

        return VerificationReport(
            results=results,
            total=len(file_paths),
            passed=passed,
            failed=failed,
        )
