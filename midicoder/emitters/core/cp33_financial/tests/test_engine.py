"""
Unit tests cho CP33 Financial Engine.

Kiểm tra các service class:
- FXRateService: get_rate, add_rate, find_active_rate
- RoundingService: get_rule, apply, add_rule
- MultiCurrencyCalculator: convert, add, subtract, multiply, divide
- LedgerService: create_transaction, verify_hash_chain, create_snapshot, get_entries
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal

from midicoder.errors import MidicoderError
from midicoder.emitters.core.cp33_financial.engine import (
    MultiCurrencyCalculator,
    FXRateService,
    LedgerService,
    RoundingService,
)
from midicoder.emitters.core.cp33_financial.models import (
    Currency,
    FXRate,
    FXSource,
    LedgerEntry,
    RoundingRule,
    RoundingMode,
    EntryType,
    TransactionType,
)


# ===========================================================================
# Helpers
# ===========================================================================

def _make_currencies():
    """Tạo danh sách currencies USD, EUR, VND cho test."""
    return [
        Currency(code="USD", name="US Dollar", symbol="$", decimal_places=2, rounding_mode=RoundingMode.HALF_UP),
        Currency(code="EUR", name="Euro", symbol="\u20ac", decimal_places=2, rounding_mode=RoundingMode.HALF_UP),
        Currency(code="VND", name="Vietnam Dong", symbol="\u20ab", decimal_places=0, rounding_mode=RoundingMode.HALF_UP),
    ]


def _make_rounding_rules():
    """Tạo danh sách rounding rules cho currencies test."""
    return [
        RoundingRule(currency_code="USD", mode=RoundingMode.HALF_UP, decimals=2),
        RoundingRule(currency_code="EUR", mode=RoundingMode.HALF_UP, decimals=2),
        RoundingRule(currency_code="VND", mode=RoundingMode.HALF_UP, decimals=0),
    ]


def _make_fx_rates(now: datetime = None):
    """Tạo danh sách FXRate cho test."""
    if now is None:
        now = datetime.now()
    return [
        FXRate(from_currency="USD", to_currency="EUR", rate=Decimal("0.85"), effective_from=now - timedelta(days=30), source=FXSource.MANUAL),
        FXRate(from_currency="USD", to_currency="VND", rate=Decimal("25000"), effective_from=now - timedelta(days=30), source=FXSource.MANUAL),
        FXRate(from_currency="EUR", to_currency="VND", rate=Decimal("29411"), effective_from=now - timedelta(days=30), source=FXSource.MANUAL),
    ]


def _make_ledger_entry(
    entry_id: str,
    entry_type: EntryType,
    account_code: str,
    amount: Decimal,
    currency: str = "USD",
    previous_hash: str = "",
    transaction_id: str = "",
) -> LedgerEntry:
    """Tạo LedgerEntry cho test."""
    return LedgerEntry(
        id=entry_id,
        transaction_id=transaction_id,
        entry_type=entry_type,
        account_code=account_code,
        amount=amount,
        currency=currency,
        description="test entry",
        previous_hash=previous_hash,
    )


# ===========================================================================
# TestFXRateService
# ===========================================================================

class TestFXRateService:
    """Test cho FXRateService."""

    def setup_method(self) -> None:
        """Setup fixture cho mỗi test."""
        self.now = datetime.now()
        self.rates = _make_fx_rates(self.now)
        self.service = FXRateService(self.rates)

    def test_get_direct_rate(self) -> None:
        """Lấy tỷ giá trực tiếp USD -> EUR."""
        rate = self.service.get_rate("USD", "EUR", date=self.now)
        assert rate == Decimal("0.85")

    def test_get_direct_rate_usd_to_vnd(self) -> None:
        """Lấy tỷ giá trực tiếp USD -> VND."""
        rate = self.service.get_rate("USD", "VND", date=self.now)
        assert rate == Decimal("25000")

    def test_get_inverse_rate(self) -> None:
        """Lấy tỷ giá nghịch đảo EUR -> USD (chỉ có USD -> EUR)."""
        rate = self.service.get_rate("EUR", "USD", date=self.now)
        # 1 / 0.85
        assert rate == Decimal("1") / Decimal("0.85")

    def test_get_same_currency_rate(self) -> None:
        """Lấy tỷ giá cùng currency trả về 1."""
        rate = self.service.get_rate("USD", "USD", date=self.now)
        assert rate == Decimal("1")

    def test_get_rate_not_found_raises_error(self) -> None:
        """Lấy tỷ giá không tồn tại raise MidicoderError."""
        with pytest.raises(MidicoderError):
            self.service.get_rate("JPY", "CHF", date=self.now)

    def test_add_rate(self) -> None:
        """Thêm tỷ giá mới và tra cứu thành công."""
        new_rate = FXRate(
            from_currency="JPY",
            to_currency="USD",
            rate=Decimal("0.0067"),
            effective_from=self.now - timedelta(days=10),
            source=FXSource.MANUAL,
        )
        self.service.add_rate(new_rate)
        rate = self.service.get_rate("JPY", "USD", date=self.now)
        assert rate == Decimal("0.0067")

    def test_find_active_rate(self) -> None:
        """Tìm tỷ giá đang hoạt động trả về FXRate object."""
        fx = self.service.find_active_rate("USD", "EUR", date=self.now)
        assert fx is not None
        assert fx.from_currency == "USD"
        assert fx.to_currency == "EUR"
        assert fx.rate == Decimal("0.85")

    def test_find_active_rate_not_found(self) -> None:
        """Tìm tỷ giá không tồn tại trả về None."""
        fx = self.service.find_active_rate("JPY", "CHF", date=self.now)
        assert fx is None

    def test_find_active_rate_same_currency(self) -> None:
        """Tìm tỷ giá cùng currency trả về None."""
        fx = self.service.find_active_rate("USD", "USD", date=self.now)
        assert fx is None

    def test_get_rate_case_insensitive(self) -> None:
        """Lấy tỷ giá không phân biệt chữ hoa/thường."""
        rate = self.service.get_rate("usd", "eur", date=self.now)
        assert rate == Decimal("0.85")

    def test_find_active_rate_outside_date_range(self) -> None:
        """Tìm tỷ giá ngoài khoảng thời gian hiệu lực trả về None."""
        future_rate = FXRate(
            from_currency="GBP",
            to_currency="USD",
            rate=Decimal("1.2"),
            effective_from=self.now + timedelta(days=10),
            effective_to=self.now + timedelta(days=20),
            source=FXSource.MANUAL,
        )
        svc = FXRateService([future_rate])
        fx = svc.find_active_rate("GBP", "USD", date=self.now)
        assert fx is None

    def test_cross_rate_through_base(self) -> None:
        """Lấy tỷ giá gián tiếp qua base currency USD."""
        # Cross-rate: GBP -> JPY qua USD
        # Cần GBP -> USD và USD -> JPY (direct, vì _find_rate không tìm inverse)
        gbp_usd = FXRate(
            from_currency="GBP", to_currency="USD", rate=Decimal("1.25"),
            effective_from=self.now - timedelta(days=10), source=FXSource.MANUAL,
        )
        usd_jpy = FXRate(
            from_currency="USD", to_currency="JPY", rate=Decimal("149.25"),
            effective_from=self.now - timedelta(days=10), source=FXSource.MANUAL,
        )
        svc = FXRateService([gbp_usd, usd_jpy])
        rate = svc.get_rate("GBP", "JPY", date=self.now)
        # GBP -> USD (1.25) * USD -> JPY (149.25)
        expected = Decimal("1.25") * Decimal("149.25")
        assert rate == expected


# ===========================================================================
# TestRoundingService
# ===========================================================================

class TestRoundingService:
    """Test cho RoundingService."""

    def setup_method(self) -> None:
        """Setup fixture cho mỗi test."""
        self.rules = _make_rounding_rules()
        self.service = RoundingService(self.rules)

    def test_get_rule(self) -> None:
        """Lấy quy tắc làm tròn cho currency tồn tại."""
        rule = self.service.get_rule("USD")
        assert rule.currency_code == "USD"
        assert rule.mode == RoundingMode.HALF_UP
        assert rule.decimals == 2

    def test_get_rule_case_insensitive(self) -> None:
        """Lấy quy tắc làm tròn không phân biệt chữ hoa/thường."""
        rule = self.service.get_rule("usd")
        assert rule.currency_code == "USD"

    def test_get_rule_not_found_raises_error(self) -> None:
        """Lấy quy tắc không tồn tại raise MidicoderError."""
        with pytest.raises(MidicoderError):
            self.service.get_rule("JPY")

    def test_apply_rounding_half_up(self) -> None:
        """Áp dụng làm tròn HALF_UP cho USD."""
        result = self.service.apply(Decimal("10.555"), "USD")
        assert result == Decimal("10.56")

    def test_apply_rounding_vnd_zero_decimals(self) -> None:
        """Áp dụng làm tròn VND (0 chữ số thập phân)."""
        result = self.service.apply(Decimal("1234.6"), "VND")
        assert result == Decimal("1235")

    def test_apply_rounding_negative_amount(self) -> None:
        """Áp dụng làm tròn cho số tiền âm."""
        result = self.service.apply(Decimal("-10.555"), "USD")
        assert result == Decimal("-10.56")

    def test_apply_rounding_exact_amount(self) -> None:
        """Áp dụng làm tròn cho số tiền đã đủ chính xác."""
        result = self.service.apply(Decimal("10.50"), "USD")
        assert result == Decimal("10.50")

    def test_add_rule(self) -> None:
        """Thêm quy tắc làm tròn mới."""
        new_rule = RoundingRule(currency_code="JPY", mode=RoundingMode.HALF_EVEN, decimals=0)
        self.service.add_rule(new_rule)
        rule = self.service.get_rule("JPY")
        assert rule.mode == RoundingMode.HALF_EVEN

    def test_apply_not_found_currency_raises_error(self) -> None:
        """Áp dụng làm tròn cho currency không có rule raise MidicoderError."""
        with pytest.raises(MidicoderError):
            self.service.apply(Decimal("100"), "JPY")

    def test_list_rules(self) -> None:
        """Lấy danh sách tất cả quy tắc làm tròn."""
        rules = self.service.list_rules()
        assert "USD" in rules
        assert "EUR" in rules
        assert "VND" in rules

    def test_remove_rule(self) -> None:
        """Xóa quy tắc làm tròn."""
        self.service.remove_rule("EUR")
        with pytest.raises(MidicoderError):
            self.service.get_rule("EUR")


# ===========================================================================
# TestMultiCurrencyCalculator
# ===========================================================================

class TestMultiCurrencyCalculator:
    """Test cho MultiCurrencyCalculator."""

    def setup_method(self) -> None:
        """Setup fixture cho mỗi test."""
        self.now = datetime.now()
        self.currencies = _make_currencies()
        self.rules = _make_rounding_rules()
        self.rates = _make_fx_rates(self.now)
        self.calculator = MultiCurrencyCalculator(
            base_currency="USD",
            currencies=self.currencies,
            rounding_rules=self.rules,
        )
        # Thêm FX rates vào calculator
        for rate in self.rates:
            self.calculator.fx_service.add_rate(rate)

    def test_add_same_currency(self) -> None:
        """Cộng hai số tiền cùng currency."""
        result, cur = self.calculator.add((Decimal("100"), "USD"), (Decimal("200"), "USD"))
        assert result == Decimal("300.00")
        assert cur == "USD"

    def test_subtract_same_currency(self) -> None:
        """Trừ hai số tiền cùng currency."""
        result, cur = self.calculator.subtract((Decimal("300"), "USD"), (Decimal("100"), "USD"))
        assert result == Decimal("200.00")
        assert cur == "USD"

    def test_multiply_same_currency(self) -> None:
        """Nhân hai số tiền cùng currency."""
        result, cur = self.calculator.multiply((Decimal("10"), "USD"), (Decimal("5"), "USD"))
        assert result == Decimal("50.00")
        assert cur == "USD"

    def test_divide_same_currency(self) -> None:
        """Chia hai số tiền cùng currency."""
        result, cur = self.calculator.divide((Decimal("100"), "USD"), (Decimal("4"), "USD"))
        assert result == Decimal("25.00")
        assert cur == "USD"

    def test_divide_by_zero_raises_error(self) -> None:
        """Chia cho số 0 raise MidicoderError."""
        with pytest.raises(MidicoderError):
            self.calculator.divide((Decimal("100"), "USD"), (Decimal("0"), "USD"))

    def test_add_different_currencies(self) -> None:
        """Cộng hai số tiền khác currency (convert về base)."""
        result, cur = self.calculator.add((Decimal("100"), "USD"), (Decimal("100"), "EUR"))
        assert cur == "USD"
        # 100 USD + 100 EUR -> USD (100 / 0.85 = 117.65)
        assert result == Decimal("217.65")

    def test_subtract_different_currencies(self) -> None:
        """Trừ hai số tiền khác currency."""
        result, cur = self.calculator.subtract((Decimal("100"), "USD"), (Decimal("100"), "EUR"))
        assert cur == "USD"
        # 100 USD - 117.65 USD
        assert result == Decimal("-17.65")

    def test_multiply_different_currencies(self) -> None:
        """Nhân hai số tiền khác currency."""
        result, cur = self.calculator.multiply((Decimal("10"), "USD"), (Decimal("10"), "EUR"))
        assert cur == "USD"

    def test_divide_different_currencies(self) -> None:
        """Chia hai số tiền khác currency."""
        result, cur = self.calculator.divide((Decimal("100"), "USD"), (Decimal("10"), "EUR"))
        assert cur == "USD"

    def test_convert_same_currency(self) -> None:
        """Chuyển đổi cùng currency (applies rounding)."""
        result = self.calculator.convert(Decimal("100.999"), "USD", "USD")
        assert result == Decimal("101.00")

    def test_convert_usd_to_eur(self) -> None:
        """Chuyển đổi USD sang EUR."""
        result = self.calculator.convert(Decimal("100"), "USD", "EUR")
        assert result == Decimal("85.00")

    def test_convert_vnd_zero_decimals(self) -> None:
        """Chuyển đổi sang VND (0 chữ số thập phân)."""
        result = self.calculator.convert(Decimal("1"), "USD", "VND")
        assert result == Decimal("25000")

    def test_convert_invalid_currency_raises_error(self) -> None:
        """Chuyển đổi currency không tồn tại raise MidicoderError."""
        with pytest.raises(MidicoderError):
            self.calculator.convert(Decimal("100"), "USD", "JPY")

    def test_convert_no_fx_rate_raises_error(self) -> None:
        """Chuyển đổi không có tỷ giá raise MidicoderError."""
        # Tạo calculator không có FX rate
        calc = MultiCurrencyCalculator(
            base_currency="USD",
            currencies=_make_currencies(),
            rounding_rules=_make_rounding_rules(),
        )
        with pytest.raises(MidicoderError):
            calc.convert(Decimal("100"), "USD", "EUR")

    def test_case_insensitive_currency(self) -> None:
        """Các phép toán không phân biệt chữ hoa/thường."""
        result, cur = self.calculator.add((Decimal("100"), "usd"), (Decimal("50"), "Usd"))
        assert cur == "USD"
        assert result == Decimal("150.00")

    def test_rounding_applied_to_result(self) -> None:
        """Kết quả được làm tròn theo quy tắc."""
        # VND làm tròn 0 chữ số thập phân
        result, cur = self.calculator.add((Decimal("100.6"), "VND"), (Decimal("200.4"), "VND"))
        assert cur == "VND"
        assert result == Decimal("301")


# ===========================================================================
# TestLedgerService
# ===========================================================================

class TestLedgerService:
    """Test cho LedgerService."""

    def setup_method(self) -> None:
        """Setup fixture cho mỗi test."""
        self.service = LedgerService()

    def test_create_single_entry_transaction(self) -> None:
        """Tạo giao dịch single-entry thành công."""
        entries = [_make_ledger_entry("e1", EntryType.DEBIT, "1000", Decimal("100"))]
        txn = self.service.create_transaction(TransactionType.SINGLE_ENTRY, entries)
        assert txn.transaction_type == TransactionType.SINGLE_ENTRY
        assert len(txn.entries) == 1
        assert txn.entries[0].transaction_id == txn.id

    def test_create_double_entry_balanced(self) -> None:
        """Tạo giao dịch double-entry cân bằng thành công."""
        entries = [
            _make_ledger_entry("e1", EntryType.DEBIT, "1000", Decimal("500")),
            _make_ledger_entry("e2", EntryType.CREDIT, "2000", Decimal("500")),
        ]
        txn = self.service.create_transaction(TransactionType.DOUBLE_ENTRY, entries)
        assert txn.total_debit == Decimal("500")
        assert txn.total_credit == Decimal("500")
        assert txn.validate_balance() is True

    def test_create_double_entry_imbalanced_raises_error(self) -> None:
        """Tạo giao dịch double-entry không cân bằng raise MidicoderError."""
        entries = [
            _make_ledger_entry("e1", EntryType.DEBIT, "1000", Decimal("500")),
            _make_ledger_entry("e2", EntryType.CREDIT, "2000", Decimal("300")),
        ]
        with pytest.raises(MidicoderError):
            self.service.create_transaction(TransactionType.DOUBLE_ENTRY, entries)

    def test_verify_hash_chain_valid(self) -> None:
        """Xác minh hash chain hợp lệ trả về True."""
        entries = [
            _make_ledger_entry("e1", EntryType.DEBIT, "1000", Decimal("100")),
            _make_ledger_entry("e2", EntryType.CREDIT, "2000", Decimal("100")),
        ]
        txn = self.service.create_transaction(TransactionType.DOUBLE_ENTRY, entries)
        assert self.service.verify_hash_chain(txn.id) is True

    def test_verify_hash_chain_tampered_fails(self) -> None:
        """Xác minh hash chain bị thay đổi raise MidicoderError."""
        entries = [
            _make_ledger_entry("e1", EntryType.DEBIT, "1000", Decimal("100")),
            _make_ledger_entry("e2", EntryType.CREDIT, "2000", Decimal("100")),
        ]
        txn = self.service.create_transaction(TransactionType.DOUBLE_ENTRY, entries)
        # Làm hỏng previous_hash của entry thứ hai
        stored = self.service.get_entries(txn.id)
        stored[1].previous_hash = "tampered_hash"
        with pytest.raises(MidicoderError):
            self.service.verify_hash_chain(txn.id)

    def test_verify_hash_chain_transaction_not_found(self) -> None:
        """Xác minh hash chain với transaction không tồn tại raise MidicoderError."""
        with pytest.raises(MidicoderError):
            self.service.verify_hash_chain("nonexistent")

    def test_create_snapshot(self) -> None:
        """Tạo snapshot ledger thành công."""
        entries = [_make_ledger_entry("e1", EntryType.DEBIT, "1000", Decimal("100"))]
        self.service.create_transaction(TransactionType.SINGLE_ENTRY, entries)
        snapshot = self.service.create_snapshot()
        assert snapshot.entry_count >= 1
        assert snapshot.chain_hash != ""
        assert snapshot.id != ""

    def test_create_snapshot_empty_ledger(self) -> None:
        """Tạo snapshot ledger rỗng."""
        snapshot = self.service.create_snapshot()
        assert snapshot.entry_count == 0
        assert snapshot.chain_hash == ""

    def test_get_entries(self) -> None:
        """Lấy entries của giao dịch thành công."""
        entries = [
            _make_ledger_entry("e1", EntryType.DEBIT, "1000", Decimal("200")),
            _make_ledger_entry("e2", EntryType.CREDIT, "2000", Decimal("200")),
        ]
        txn = self.service.create_transaction(TransactionType.DOUBLE_ENTRY, entries)
        retrieved = self.service.get_entries(txn.id)
        assert len(retrieved) == 2
        assert retrieved[0].amount == Decimal("200")

    def test_get_entries_transaction_not_found(self) -> None:
        """Lấy entries với transaction không tồn tại raise MidicoderError."""
        with pytest.raises(MidicoderError):
            self.service.get_entries("nonexistent")

    def test_hash_chain_links_across_transactions(self) -> None:
        """Hash chain nối liền giữa các giao dịch."""
        entries1 = [_make_ledger_entry("e1", EntryType.DEBIT, "1000", Decimal("100"))]
        txn1 = self.service.create_transaction(TransactionType.SINGLE_ENTRY, entries1)
        entries2 = [_make_ledger_entry("e2", EntryType.DEBIT, "1000", Decimal("200"))]
        txn2 = self.service.create_transaction(TransactionType.SINGLE_ENTRY, entries2)

        # previous_hash của entry trong txn2 phải = hash của entry cuối cùng trong txn1
        entries1_retrieved = self.service.get_entries(txn1.id)
        entries2_retrieved = self.service.get_entries(txn2.id)
        assert entries2_retrieved[0].previous_hash == entries1_retrieved[0].hash

    def test_create_transaction_sets_pending_status(self) -> None:
        """Tạo giao dịch có trạng thái PENDING."""
        entries = [_make_ledger_entry("e1", EntryType.DEBIT, "1000", Decimal("50"))]
        txn = self.service.create_transaction(TransactionType.SINGLE_ENTRY, entries)
        from midicoder.emitters.core.cp33_financial.models import TransactionStatus
        assert txn.status == TransactionStatus.PENDING

    def test_transaction_has_tenant_id(self) -> None:
        """Tạo giao dịch với tenant_id."""
        entries = [_make_ledger_entry("e1", EntryType.DEBIT, "1000", Decimal("50"))]
        txn = self.service.create_transaction(
            TransactionType.SINGLE_ENTRY, entries, tenant_id="tenant-abc"
        )
        assert txn.tenant_id == "tenant-abc"

    def test_multiple_entries_double_entry(self) -> None:
        """Double-entry với nhiều entries."""
        entries = [
            _make_ledger_entry("e1", EntryType.DEBIT, "1000", Decimal("300")),
            _make_ledger_entry("e2", EntryType.DEBIT, "1010", Decimal("200")),
            _make_ledger_entry("e3", EntryType.CREDIT, "2000", Decimal("500")),
        ]
        txn = self.service.create_transaction(TransactionType.DOUBLE_ENTRY, entries)
        assert txn.total_debit == Decimal("500")
        assert txn.total_credit == Decimal("500")

    def test_snapshot_after_multiple_transactions(self) -> None:
        """Snapshot sau nhiều giao dịch có đúng entry_count."""
        entries1 = [_make_ledger_entry("e1", EntryType.DEBIT, "1000", Decimal("100"))]
        self.service.create_transaction(TransactionType.SINGLE_ENTRY, entries1)
        entries2 = [_make_ledger_entry("e2", EntryType.DEBIT, "1000", Decimal("200"))]
        self.service.create_transaction(TransactionType.SINGLE_ENTRY, entries2)
        snapshot = self.service.create_snapshot()
        assert snapshot.entry_count == 2
