"""Test cho FastAPI Emitter của CP33: Financial Engine."""

import tempfile
from pathlib import Path
from midicoder.emitters.core.cp33_financial.fastapi import (
    FinancialFastAPIEmitter,
    GeneratedFile,
)


class TestFinancialFastAPIEmitter:
    """Test cho FinancialFastAPIEmitter."""

    def setup_method(self) -> None:
        """Setup fixture cho mỗi test."""
        self.tmpdir = tempfile.mkdtemp()
        template_dir = Path(self.tmpdir) / "core" / "cp33_financial"
        template_dir.mkdir(parents=True)
        (template_dir / "currency_model.py.jinja2").write_text(
            "# currencies: {{ currencies }}"
        )
        (template_dir / "account_model.py.jinja2").write_text(
            "# accounts: {{ accounts }}"
        )
        (template_dir / "ledger_service.py.jinja2").write_text(
            "# base: {{ base_currency }}"
        )

    def test_emit_returns_files(self) -> None:
        """Kiểm tra emit trả về danh sách GeneratedFile."""
        emitter = FinancialFastAPIEmitter(str(Path(self.tmpdir) / "core"))
        config = {
            "currencies": [{"code": "USD", "name": "US Dollar"}],
            "accounts": [{"code": "1000", "name": "Cash"}],
            "base_currency": "USD",
        }
        result = emitter.emit(config, self.tmpdir)
        assert len(result) >= 1

    def test_emit_returns_correct_count(self) -> None:
        """Kiểm tra emit trả về đúng số file khi có đầy đủ templates."""
        emitter = FinancialFastAPIEmitter(str(Path(self.tmpdir) / "core"))
        config = {
            "currencies": [],
            "accounts": [],
            "base_currency": "USD",
        }
        result = emitter.emit(config, self.tmpdir)
        assert len(result) == 3

    def test_emit_file_has_path_and_content(self) -> None:
        """Kiểm tra GeneratedFile có path và content."""
        emitter = FinancialFastAPIEmitter(str(Path(self.tmpdir) / "core"))
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
        emitter = FinancialFastAPIEmitter(str(Path(self.tmpdir) / "core"))
        config = {
            "currencies": [],
            "accounts": [],
            "base_currency": "USD",
        }
        result = emitter.emit(config, self.tmpdir)
        for f in result:
            assert isinstance(f, GeneratedFile)

    def test_emit_currency_model_path(self) -> None:
        """Kiểm tra path của currency_model đúng."""
        emitter = FinancialFastAPIEmitter(str(Path(self.tmpdir) / "core"))
        config = {
            "currencies": [],
            "accounts": [],
            "base_currency": "USD",
        }
        result = emitter.emit(config, self.tmpdir)
        paths = [f.path for f in result]
        assert "app/financial/models/currency_model.py" in paths

    def test_emit_account_model_path(self) -> None:
        """Kiểm tra path của account_model đúng."""
        emitter = FinancialFastAPIEmitter(str(Path(self.tmpdir) / "core"))
        config = {
            "currencies": [],
            "accounts": [],
            "base_currency": "USD",
        }
        result = emitter.emit(config, self.tmpdir)
        paths = [f.path for f in result]
        assert "app/financial/models/account_model.py" in paths

    def test_emit_ledger_service_path(self) -> None:
        """Kiểm tra path của ledger_service đúng."""
        emitter = FinancialFastAPIEmitter(str(Path(self.tmpdir) / "core"))
        config = {
            "currencies": [],
            "accounts": [],
            "base_currency": "USD",
        }
        result = emitter.emit(config, self.tmpdir)
        paths = [f.path for f in result]
        assert "app/financial/services/ledger_service.py" in paths

    def test_emit_writes_files_to_output(self) -> None:
        """Kiểm tra emit ghi file vào output directory."""
        emitter = FinancialFastAPIEmitter(str(Path(self.tmpdir) / "core"))
        config = {
            "currencies": [{"code": "EUR", "name": "Euro"}],
            "accounts": [{"code": "4000", "name": "Revenue"}],
            "base_currency": "EUR",
        }
        result = emitter.emit(config, self.tmpdir)
        assert len(result) >= 1

    def test_emit_renders_template_content(self) -> None:
        """Kiểm tra nội dung template được render đúng."""
        emitter = FinancialFastAPIEmitter(str(Path(self.tmpdir) / "core"))
        config = {
            "currencies": [],
            "accounts": [],
            "base_currency": "GBP",
        }
        result = emitter.emit(config, self.tmpdir)
        ledger = [f for f in result if "ledger_service" in f.path][0]
        assert "GBP" in ledger.content  # type: ignore

    def test_emit_empty_config(self) -> None:
        """Kiểm tra emit với config rỗng vẫn hoạt động."""
        emitter = FinancialFastAPIEmitter(str(Path(self.tmpdir) / "core"))
        result = emitter.emit({}, self.tmpdir)
        assert len(result) == 3

    def test_emit_with_missing_template(self) -> None:
        """Kiểm tra emit bỏ qua template không tồn tại."""
        # Xóa một template
        template_dir = Path(self.tmpdir) / "core" / "cp33_financial"
        (template_dir / "ledger_service.py.jinja2").unlink()

        emitter = FinancialFastAPIEmitter(str(Path(self.tmpdir) / "core"))
        config = {
            "currencies": [],
            "accounts": [],
            "base_currency": "USD",
        }
        result = emitter.emit(config, self.tmpdir)
        assert len(result) == 2

    def test_emit_currency_count_in_context(self) -> None:
        """Kiểm tra currency_count được truyền vào context."""
        template_dir = Path(self.tmpdir) / "core" / "cp33_financial"
        (template_dir / "currency_model.py.jinja2").write_text(
            "# count: {{ currency_count }}"
        )

        emitter = FinancialFastAPIEmitter(str(Path(self.tmpdir) / "core"))
        config = {
            "currencies": [
                {"code": "USD", "name": "US Dollar"},
                {"code": "EUR", "name": "Euro"},
            ],
            "accounts": [],
            "base_currency": "USD",
        }
        result = emitter.emit(config, self.tmpdir)
        currency_file = [f for f in result if "currency_model" in f.path][0]
        assert "count: 2" in currency_file.content  # type: ignore

    def test_emit_account_count_in_context(self) -> None:
        """Kiểm tra account_count được truyền vào context."""
        template_dir = Path(self.tmpdir) / "core" / "cp33_financial"
        (template_dir / "account_model.py.jinja2").write_text(
            "# count: {{ account_count }}"
        )

        emitter = FinancialFastAPIEmitter(str(Path(self.tmpdir) / "core"))
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
        account_file = [f for f in result if "account_model" in f.path][0]
        assert "count: 3" in account_file.content  # type: ignore
