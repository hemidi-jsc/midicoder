"""Test cho React Emitter của CP33: Financial Engine."""

import tempfile
from pathlib import Path
from midicoder.packs.cp33_financial.react import (
    FinancialReactEmitter,
    GeneratedFile,
)


class TestFinancialReactEmitter:
    """Test cho FinancialReactEmitter."""

    def setup_method(self) -> None:
        """Setup fixture cho mỗi test."""
        self.tmpdir = tempfile.mkdtemp()
        template_dir = Path(self.tmpdir) / "core" / "cp33_financial"
        template_dir.mkdir(parents=True)
        (template_dir / "LedgerDashboard.tsx.jinja2").write_text(
            "// dashboard: {{ base_currency }}"
        )
        (template_dir / "TransactionDetail.tsx.jinja2").write_text(
            "// detail: {{ currencies }}"
        )

    def test_emit_returns_files(self) -> None:
        """Kiểm tra emit trả về danh sách GeneratedFile."""
        emitter = FinancialReactEmitter(str(Path(self.tmpdir) / "core"))
        config = {
            "currencies": [{"code": "USD", "name": "US Dollar"}],
            "accounts": [{"code": "1000", "name": "Cash"}],
            "base_currency": "USD",
        }
        result = emitter.emit(config, self.tmpdir)
        assert len(result) >= 1

    def test_emit_returns_correct_count(self) -> None:
        """Kiểm tra emit trả về đúng số file khi có đầy đủ templates."""
        emitter = FinancialReactEmitter(str(Path(self.tmpdir) / "core"))
        config = {
            "currencies": [],
            "accounts": [],
            "base_currency": "USD",
        }
        result = emitter.emit(config, self.tmpdir)
        assert len(result) == 2

    def test_emit_file_has_path_and_content(self) -> None:
        """Kiểm tra GeneratedFile có path và content."""
        emitter = FinancialReactEmitter(str(Path(self.tmpdir) / "core"))
        config = {
            "currencies": [],
            "accounts": [],
            "base_currency": "USD",
        }
        result = emitter.emit(config, self.tmpdir)
        for f in result:
            assert f.path  # type: ignore
            assert f.content  # type: ignore

    def test_emit_files_are_generated_file_instances(self) -> None:
        """Kiểm tra các phần tử trong result là GeneratedFile."""
        emitter = FinancialReactEmitter(str(Path(self.tmpdir) / "core"))
        config = {
            "currencies": [],
            "accounts": [],
            "base_currency": "USD",
        }
        result = emitter.emit(config, self.tmpdir)
        for f in result:
            assert isinstance(f, GeneratedFile)

    def test_emit_ledger_dashboard_path(self) -> None:
        """Kiểm tra path của LedgerDashboard đúng."""
        emitter = FinancialReactEmitter(str(Path(self.tmpdir) / "core"))
        config = {
            "currencies": [],
            "accounts": [],
            "base_currency": "USD",
        }
        result = emitter.emit(config, self.tmpdir)
        paths = [f.path for f in result]
        assert "src/financial/components/LedgerDashboard.tsx" in paths

    def test_emit_transaction_detail_path(self) -> None:
        """Kiểm tra path của TransactionDetail đúng."""
        emitter = FinancialReactEmitter(str(Path(self.tmpdir) / "core"))
        config = {
            "currencies": [],
            "accounts": [],
            "base_currency": "USD",
        }
        result = emitter.emit(config, self.tmpdir)
        paths = [f.path for f in result]
        assert "src/financial/components/TransactionDetail.tsx" in paths

    def test_emit_writes_files_to_output(self) -> None:
        """Kiểm tra emit ghi file vào output directory."""
        emitter = FinancialReactEmitter(str(Path(self.tmpdir) / "core"))
        config = {
            "currencies": [{"code": "EUR", "name": "Euro"}],
            "accounts": [{"code": "4000", "name": "Revenue"}],
            "base_currency": "EUR",
        }
        result = emitter.emit(config, self.tmpdir)
        assert len(result) >= 1

    def test_emit_renders_template_content(self) -> None:
        """Kiểm tra nội dung template được render đúng."""
        emitter = FinancialReactEmitter(str(Path(self.tmpdir) / "core"))
        config = {
            "currencies": [],
            "accounts": [],
            "base_currency": "GBP",
        }
        result = emitter.emit(config, self.tmpdir)
        dashboard = [f for f in result if "LedgerDashboard" in f.path][0]
        assert "GBP" in dashboard.content  # type: ignore

    def test_emit_empty_config(self) -> None:
        """Kiểm tra emit với config rỗng vẫn hoạt động."""
        emitter = FinancialReactEmitter(str(Path(self.tmpdir) / "core"))
        result = emitter.emit({}, self.tmpdir)
        assert len(result) == 2

    def test_emit_with_missing_template(self) -> None:
        """Kiểm tra emit bỏ qua template không tồn tại."""
        template_dir = Path(self.tmpdir) / "core" / "cp33_financial"
        (template_dir / "TransactionDetail.tsx.jinja2").unlink()

        emitter = FinancialReactEmitter(str(Path(self.tmpdir) / "core"))
        config = {
            "currencies": [],
            "accounts": [],
            "base_currency": "USD",
        }
        result = emitter.emit(config, self.tmpdir)
        assert len(result) == 1

    def test_emit_currency_count_in_context(self) -> None:
        """Kiểm tra currency_count được truyền vào context."""
        template_dir = Path(self.tmpdir) / "core" / "cp33_financial"
        (template_dir / "LedgerDashboard.tsx.jinja2").write_text(
            "// count: {{ currency_count }}"
        )

        emitter = FinancialReactEmitter(str(Path(self.tmpdir) / "core"))
        config = {
            "currencies": [
                {"code": "USD", "name": "US Dollar"},
                {"code": "EUR", "name": "Euro"},
            ],
            "accounts": [],
            "base_currency": "USD",
        }
        result = emitter.emit(config, self.tmpdir)
        dashboard_file = [f for f in result if "LedgerDashboard" in f.path][0]
        assert "count: 2" in dashboard_file.content  # type: ignore

    def test_emit_account_count_in_context(self) -> None:
        """Kiểm tra account_count được truyền vào context."""
        template_dir = Path(self.tmpdir) / "core" / "cp33_financial"
        (template_dir / "TransactionDetail.tsx.jinja2").write_text(
            "// count: {{ account_count }}"
        )

        emitter = FinancialReactEmitter(str(Path(self.tmpdir) / "core"))
        config = {
            "currencies": [],
            "accounts": [
                {"code": "1000", "name": "Cash"},
                {"code": "2000", "name": "Bank"},
                {"code": "3000", "name": "Inventory"},
            ],
            "base_currency": "USD",
        }
        result = emitter.emit(config, self.tmpdir)
        detail_file = [f for f in result if "TransactionDetail" in f.path][0]
        assert "count: 3" in detail_file.content  # type: ignore
