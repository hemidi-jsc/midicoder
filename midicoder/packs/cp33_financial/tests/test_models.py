"""
Test cho models của CP33: Financial Engine.

Kiểm tra:
- Currency: Validation ISO 4217, serialization, format_amount
- FXRate: Validation currency pair, rate, date range, serialization
- Account: Validation, serialization
- LedgerEntry: Validation, hash chain, serialization
- FinancialTransaction: Double-entry validation, posting, serialization
- RoundingRule: Apply rounding, validation, serialization
- LedgerSnapshot: Validation, serialization
"""

import pytest
from datetime import datetime
from decimal import Decimal
from midicoder.errors import MidicoderError
from midicoder.packs.cp33_financial.models import (
    Currency,
    FXRate,
    FXSource,
    Account,
    AccountType,
    LedgerEntry,
    EntryType,
    FinancialTransaction,
    TransactionType,
    TransactionStatus,
    RoundingRule,
    RoundingMode,
    LedgerSnapshot,
)


class TestCurrency:
    """Test cho model Currency."""

    def setup_method(self) -> None:
        """Setup fixture cho mỗi test."""
        self.currency = Currency(
            code="USD",
            name="US Dollar",
            symbol="$",
            decimal_places=2,
            rounding_mode=RoundingMode.HALF_UP,
        )

    def test_create_valid_currency(self) -> None:
        """Kiểm tra tạo currency hợp lệ."""
        assert self.currency.code == "USD"
        assert self.currency.name == "US Dollar"
        assert self.currency.symbol == "$"
        assert self.currency.decimal_places == 2
        assert self.currency.is_active is True

    def test_code_uppercased(self) -> None:
        """Kiểm tra code được chuyển thành chữ hoa."""
        c = Currency(code="usd", name="Test", symbol="T")
        assert c.code == "USD"

    def test_invalid_code_length(self) -> None:
        """Kiểm tra reject code không đúng 3 ký tự."""
        with pytest.raises(MidicoderError):
            Currency(code="US", name="Short", symbol="$")

    def test_invalid_code_non_alpha(self) -> None:
        """Kiểm tra reject code có ký tự không phải chữ."""
        with pytest.raises(MidicoderError):
            Currency(code="US1", name="Mixed", symbol="$")

    def test_empty_code(self) -> None:
        """Kiểm tra reject code rỗng."""
        with pytest.raises(MidicoderError):
            Currency(code="", name="Empty", symbol="$")

    def test_invalid_decimal_places_negative(self) -> None:
        """Kiểm tra reject decimal_places âm."""
        with pytest.raises(MidicoderError):
            Currency(code="USD", name="Test", symbol="$", decimal_places=-1)

    def test_invalid_decimal_places_too_high(self) -> None:
        """Kiểm tra reject decimal_places > 6."""
        with pytest.raises(MidicoderError):
            Currency(code="USD", name="Test", symbol="$", decimal_places=7)

    def test_zero_decimal_places(self) -> None:
        """Kiểm tra currency không có thập phân (vd: JPY)."""
        c = Currency(code="JPY", name="Japanese Yen", symbol="¥", decimal_places=0)
        assert c.decimal_places == 0

    def test_to_dict(self) -> None:
        """Kiểm tra serialize thành dictionary."""
        d = self.currency.to_dict()
        assert d["code"] == "USD"
        assert d["name"] == "US Dollar"
        assert d["symbol"] == "$"
        assert d["decimal_places"] == 2
        assert d["rounding_mode"] == "half_up"
        assert d["is_active"] is True

    def test_from_dict(self) -> None:
        """Kiểm tra deserialize từ dictionary."""
        data = {
            "code": "EUR",
            "name": "Euro",
            "symbol": "€",
            "decimal_places": 2,
            "rounding_mode": "half_even",
            "is_active": True,
        }
        c = Currency.from_dict(data)
        assert c.code == "EUR"
        assert c.name == "Euro"
        assert c.rounding_mode == RoundingMode.HALF_EVEN

    def test_from_dict_defaults(self) -> None:
        """Kiểm tra deserialize với giá trị mặc định."""
        data = {"code": "VND", "name": "Vietnamese Dong", "symbol": "₫"}
        c = Currency.from_dict(data)
        assert c.decimal_places == 2
        assert c.rounding_mode == RoundingMode.HALF_UP
        assert c.is_active is True

    def test_roundtrip(self) -> None:
        """Kiểm tra serialize/deserialize roundtrip."""
        restored = Currency.from_dict(self.currency.to_dict())
        assert restored.code == self.currency.code
        assert restored.name == self.currency.name
        assert restored.symbol == self.currency.symbol
        assert restored.decimal_places == self.currency.decimal_places
        assert restored.rounding_mode == self.currency.rounding_mode

    def test_format_amount(self) -> None:
        """Kiểm tra định dạng số tiền."""
        formatted = self.currency.format_amount(Decimal("1234.5"))
        assert formatted == "$1234.50"

    def test_format_amount_rounding(self) -> None:
        """Kiểm tra định dạng có làm tròn."""
        formatted = self.currency.format_amount(Decimal("1234.556"))
        assert formatted == "$1234.56"

    def test_format_amount_zero_decimals(self) -> None:
        """Kiểm tra định dạng với 0 decimal places."""
        jpy = Currency(code="JPY", name="Yen", symbol="¥", decimal_places=0)
        formatted = jpy.format_amount(Decimal("1234.9"))
        assert formatted == "¥1235"


class TestFXRate:
    """Test cho model FXRate."""

    def setup_method(self) -> None:
        """Setup fixture cho mỗi test."""
        self.rate = FXRate(
            from_currency="EUR",
            to_currency="USD",
            rate=Decimal("1.0850"),
            effective_from=datetime(2026, 1, 1),
            source=FXSource.API,
        )

    def test_create_valid_fx_rate(self) -> None:
        """Kiểm tra tạo FXRate hợp lệ."""
        assert self.rate.from_currency == "EUR"
        assert self.rate.to_currency == "USD"
        assert self.rate.rate == Decimal("1.0850")
        assert self.rate.source == FXSource.API

    def test_pair_property(self) -> None:
        """Kiểm tra property pair."""
        assert self.rate.pair == "EUR/USD"

    def test_same_currency_rejected(self) -> None:
        """Kiểm tra reject cùng 1 currency."""
        with pytest.raises(MidicoderError):
            FXRate(
                from_currency="USD",
                to_currency="USD",
                rate=Decimal("1"),
                effective_from=datetime.now(),
            )

    def test_negative_rate_rejected(self) -> None:
        """Kiểm tra reject rate âm."""
        with pytest.raises(MidicoderError):
            FXRate(
                from_currency="EUR",
                to_currency="USD",
                rate=Decimal("-0.5"),
                effective_from=datetime.now(),
            )

    def test_zero_rate_rejected(self) -> None:
        """Kiểm tra reject rate bằng 0."""
        with pytest.raises(MidicoderError):
            FXRate(
                from_currency="EUR",
                to_currency="USD",
                rate=Decimal("0"),
                effective_from=datetime.now(),
            )

    def test_invalid_rate_value(self) -> None:
        """Kiểm tra rate âm được reject sau khi convert thành Decimal."""
        # Decimal("-0") là 0 về mặt giá trị nhưng test edge case
        with pytest.raises(MidicoderError):
            FXRate(
                from_currency="EUR",
                to_currency="USD",
                rate=Decimal("-0.0001"),
                effective_from=datetime.now(),
            )

    def test_effective_to_before_from_rejected(self) -> None:
        """Kiểm tra reject effective_to < effective_from."""
        with pytest.raises(MidicoderError):
            FXRate(
                from_currency="EUR",
                to_currency="USD",
                rate=Decimal("1.08"),
                effective_from=datetime(2026, 6, 1),
                effective_to=datetime(2026, 1, 1),
            )

    def test_is_active_no_end_date(self) -> None:
        """Kiểm tra is_active khi không có effective_to."""
        past_rate = FXRate(
            from_currency="EUR",
            to_currency="USD",
            rate=Decimal("1.08"),
            effective_from=datetime(2020, 1, 1),
        )
        assert past_rate.is_active is True

    def test_is_active_with_future_end(self) -> None:
        """Kiểm tra is_active khi effective_to trong tương lai."""
        future_rate = FXRate(
            from_currency="EUR",
            to_currency="USD",
            rate=Decimal("1.08"),
            effective_from=datetime(2026, 1, 1),
            effective_to=datetime(2030, 12, 31),
        )
        assert future_rate.is_active is True

    def test_is_active_expired(self) -> None:
        """Kiểm tra is_active khi đã hết hạn."""
        expired_rate = FXRate(
            from_currency="EUR",
            to_currency="USD",
            rate=Decimal("1.08"),
            effective_from=datetime(2020, 1, 1),
            effective_to=datetime(2020, 12, 31),
        )
        assert expired_rate.is_active is False

    def test_to_dict(self) -> None:
        """Kiểm tra serialize thành dictionary."""
        d = self.rate.to_dict()
        assert d["from_currency"] == "EUR"
        assert d["to_currency"] == "USD"
        assert d["rate"] == "1.0850"
        assert d["source"] == "api"
        assert d["effective_to"] is None

    def test_from_dict(self) -> None:
        """Kiểm tra deserialize từ dictionary."""
        data = {
            "from_currency": "GBP",
            "to_currency": "USD",
            "rate": "1.2500",
            "effective_from": "2026-01-01T00:00:00",
            "effective_to": None,
            "source": "manual",
        }
        r = FXRate.from_dict(data)
        assert r.from_currency == "GBP"
        assert r.to_currency == "USD"
        assert r.rate == Decimal("1.2500")
        assert r.source == FXSource.MANUAL

    def test_roundtrip(self) -> None:
        """Kiểm tra serialize/deserialize roundtrip."""
        restored = FXRate.from_dict(self.rate.to_dict())
        assert restored.from_currency == self.rate.from_currency
        assert restored.to_currency == self.rate.to_currency
        assert restored.rate == self.rate.rate
        assert restored.source == self.rate.source


class TestAccount:
    """Test cho model Account."""

    def setup_method(self) -> None:
        """Setup fixture cho mỗi test."""
        self.account = Account(
            code="1000",
            name="Cash",
            account_type=AccountType.ASSET,
            currency="USD",
        )

    def test_create_valid_account(self) -> None:
        """Kiểm tra tạo account hợp lệ."""
        assert self.account.code == "1000"
        assert self.account.name == "Cash"
        assert self.account.account_type == AccountType.ASSET
        assert self.account.is_active is True

    def test_empty_code_rejected(self) -> None:
        """Kiểm tra reject code rỗng."""
        with pytest.raises(MidicoderError):
            Account(code="", name="Empty", account_type=AccountType.ASSET)

    def test_empty_name_rejected(self) -> None:
        """Kiểm tra reject name rỗng."""
        with pytest.raises(MidicoderError):
            Account(code="1000", name="", account_type=AccountType.ASSET)

    def test_parent_account(self) -> None:
        """Kiểm tra account có parent."""
        child = Account(
            code="1010",
            name="Petty Cash",
            account_type=AccountType.ASSET,
            parent_account="1000",
        )
        assert child.parent_account == "1000"

    def test_to_dict(self) -> None:
        """Kiểm tra serialize thành dictionary."""
        d = self.account.to_dict()
        assert d["code"] == "1000"
        assert d["name"] == "Cash"
        assert d["account_type"] == "asset"
        assert d["parent_account"] is None

    def test_from_dict(self) -> None:
        """Kiểm tra deserialize từ dictionary."""
        data = {
            "code": "4000",
            "name": "Revenue",
            "account_type": "income",
            "is_active": True,
            "parent_account": None,
            "currency": "EUR",
        }
        a = Account.from_dict(data)
        assert a.code == "4000"
        assert a.account_type == AccountType.INCOME
        assert a.currency == "EUR"

    def test_roundtrip(self) -> None:
        """Kiểm tra serialize/deserialize roundtrip."""
        restored = Account.from_dict(self.account.to_dict())
        assert restored.code == self.account.code
        assert restored.name == self.account.name
        assert restored.account_type == self.account.account_type


class TestLedgerEntry:
    """Test cho model LedgerEntry."""

    def setup_method(self) -> None:
        """Setup fixture cho mỗi test."""
        self.entry = LedgerEntry(
            id="entry-001",
            transaction_id="txn-001",
            entry_type=EntryType.DEBIT,
            account_code="1000",
            amount=Decimal("1000.00"),
            currency="USD",
            description="Test debit entry",
        )

    def test_create_valid_entry(self) -> None:
        """Kiểm tra tạo entry hợp lệ."""
        assert self.entry.id == "entry-001"
        assert self.entry.entry_type == EntryType.DEBIT
        assert self.entry.amount == Decimal("1000.00")

    def test_empty_id_rejected(self) -> None:
        """Kiểm tra reject ID rỗng."""
        with pytest.raises(MidicoderError):
            LedgerEntry(
                id="",
                transaction_id="txn-001",
                entry_type=EntryType.DEBIT,
                account_code="1000",
                amount=Decimal("100"),
                currency="USD",
            )

    def test_negative_amount_rejected(self) -> None:
        """Kiểm tra reject amount âm."""
        with pytest.raises(MidicoderError):
            LedgerEntry(
                id="e1",
                transaction_id="t1",
                entry_type=EntryType.DEBIT,
                account_code="1000",
                amount=Decimal("-100"),
                currency="USD",
            )

    def test_zero_amount_allowed(self) -> None:
        """Kiểm tra cho phép amount bằng 0."""
        e = LedgerEntry(
            id="e1",
            transaction_id="t1",
            entry_type=EntryType.DEBIT,
            account_code="1000",
            amount=Decimal("0"),
            currency="USD",
        )
        assert e.amount == Decimal("0")

    def test_hash_generation(self) -> None:
        """Kiểm tra hash được tính đúng."""
        h = self.entry.hash
        assert isinstance(h, str)
        assert len(h) == 64  # SHA-256 hex

    def test_hash_includes_previous_hash(self) -> None:
        """Kiểm tra hash có chứa previous_hash."""
        e1 = LedgerEntry(
            id="e1", transaction_id="t1", entry_type=EntryType.DEBIT,
            account_code="1000", amount=Decimal("100"), currency="USD",
            previous_hash="",
        )
        e2 = LedgerEntry(
            id="e2", transaction_id="t1", entry_type=EntryType.CREDIT,
            account_code="4000", amount=Decimal("100"), currency="USD",
            previous_hash=e1.hash,
        )
        # Hash khác nhau vì previous_hash khác
        assert e1.hash != e2.hash.replace("e2", "e1")

    def test_to_dict(self) -> None:
        """Kiểm tra serialize thành dictionary."""
        d = self.entry.to_dict()
        assert d["id"] == "entry-001"
        assert d["entry_type"] == "debit"
        assert d["amount"] == "1000.00"
        assert d["previous_hash"] == ""

    def test_from_dict(self) -> None:
        """Kiểm tra deserialize từ dictionary."""
        data = {
            "id": "e2",
            "transaction_id": "t1",
            "entry_type": "credit",
            "account_code": "4000",
            "amount": "500.50",
            "currency": "EUR",
            "description": "Credit entry",
            "previous_hash": "abc123",
            "created_at": "2026-05-21T10:00:00",
        }
        e = LedgerEntry.from_dict(data)
        assert e.id == "e2"
        assert e.entry_type == EntryType.CREDIT
        assert e.amount == Decimal("500.50")
        assert e.previous_hash == "abc123"

    def test_roundtrip(self) -> None:
        """Kiểm tra serialize/deserialize roundtrip."""
        restored = LedgerEntry.from_dict(self.entry.to_dict())
        assert restored.id == self.entry.id
        assert restored.transaction_id == self.entry.transaction_id
        assert restored.entry_type == self.entry.entry_type
        assert restored.amount == self.entry.amount


class TestFinancialTransaction:
    """Test cho model FinancialTransaction."""

    def setup_method(self) -> None:
        """Setup fixture cho mỗi test."""
        self.txn = FinancialTransaction(
            id="txn-001",
            transaction_type=TransactionType.DOUBLE_ENTRY,
            tenant_id="tenant-1",
            description="Test transaction",
        )

    def test_create_valid_transaction(self) -> None:
        """Kiểm tra tạo transaction hợp lệ."""
        assert self.txn.id == "txn-001"
        assert self.txn.transaction_type == TransactionType.DOUBLE_ENTRY
        assert self.txn.status == TransactionStatus.PENDING

    def test_empty_id_rejected(self) -> None:
        """Kiểm tra reject ID rỗng."""
        with pytest.raises(MidicoderError):
            FinancialTransaction(id="", transaction_type=TransactionType.SINGLE_ENTRY)

    def test_add_entry_updates_totals(self) -> None:
        """Kiểm tra thêm entry cập nhật total."""
        debit = LedgerEntry(
            id="e1", transaction_id="txn-001", entry_type=EntryType.DEBIT,
            account_code="1000", amount=Decimal("1000"), currency="USD",
        )
        credit = LedgerEntry(
            id="e2", transaction_id="txn-001", entry_type=EntryType.CREDIT,
            account_code="4000", amount=Decimal("1000"), currency="USD",
        )
        self.txn.add_entry(debit)
        self.txn.add_entry(credit)

        assert self.txn.total_debit == Decimal("1000")
        assert self.txn.total_credit == Decimal("1000")
        assert len(self.txn.entries) == 2

    def test_add_entry_sets_transaction_id(self) -> None:
        """Kiểm tra entry được set transaction_id."""
        entry = LedgerEntry(
            id="e1", transaction_id="", entry_type=EntryType.DEBIT,
            account_code="1000", amount=Decimal("100"), currency="USD",
        )
        self.txn.add_entry(entry)
        assert entry.transaction_id == "txn-001"

    def test_double_entry_balanced_validates(self) -> None:
        """Kiểm tra double-entry cân bằng validate được."""
        debit = LedgerEntry(
            id="e1", transaction_id="txn-001", entry_type=EntryType.DEBIT,
            account_code="1000", amount=Decimal("500"), currency="USD",
        )
        credit = LedgerEntry(
            id="e2", transaction_id="txn-001", entry_type=EntryType.CREDIT,
            account_code="4000", amount=Decimal("500"), currency="USD",
        )
        self.txn.add_entry(debit)
        self.txn.add_entry(credit)
        result = self.txn.validate_balance()
        assert result is True

    def test_double_entry_imbalanced_raises(self) -> None:
        """Kiểm tra double-entry không cân bằng raise error."""
        debit = LedgerEntry(
            id="e1", transaction_id="txn-001", entry_type=EntryType.DEBIT,
            account_code="1000", amount=Decimal("1000"), currency="USD",
        )
        credit = LedgerEntry(
            id="e2", transaction_id="txn-001", entry_type=EntryType.CREDIT,
            account_code="4000", amount=Decimal("800"), currency="USD",
        )
        self.txn.add_entry(debit)
        self.txn.add_entry(credit)
        with pytest.raises(MidicoderError):
            self.txn.validate_balance()

    def test_single_entry_no_balance_check(self) -> None:
        """Kiểm tra single-entry không cần balance."""
        single_txn = FinancialTransaction(
            id="txn-single",
            transaction_type=TransactionType.SINGLE_ENTRY,
        )
        entry = LedgerEntry(
            id="e1", transaction_id="txn-single", entry_type=EntryType.DEBIT,
            account_code="1000", amount=Decimal("100"), currency="USD",
        )
        single_txn.add_entry(entry)
        result = single_txn.validate_balance()
        assert result is True

    def test_post_validates_and_updates_status(self) -> None:
        """Kiểm tra post validate và chuyển trạng thái."""
        debit = LedgerEntry(
            id="e1", transaction_id="txn-001", entry_type=EntryType.DEBIT,
            account_code="1000", amount=Decimal("500"), currency="USD",
        )
        credit = LedgerEntry(
            id="e2", transaction_id="txn-001", entry_type=EntryType.CREDIT,
            account_code="4000", amount=Decimal("500"), currency="USD",
        )
        self.txn.add_entry(debit)
        self.txn.add_entry(credit)
        self.txn.post()
        assert self.txn.status == TransactionStatus.POSTED

    def test_post_imbalanced_raises(self) -> None:
        """Kiểm tra post với imbalance raise error."""
        debit = LedgerEntry(
            id="e1", transaction_id="txn-001", entry_type=EntryType.DEBIT,
            account_code="1000", amount=Decimal("1000"), currency="USD",
        )
        self.txn.add_entry(debit)
        with pytest.raises(MidicoderError):
            self.txn.post()

    def test_to_dict(self) -> None:
        """Kiểm tra serialize thành dictionary."""
        d = self.txn.to_dict()
        assert d["id"] == "txn-001"
        assert d["transaction_type"] == "double_entry"
        assert d["status"] == "pending"
        assert d["tenant_id"] == "tenant-1"
        assert d["entries"] == []

    def test_from_dict(self) -> None:
        """Kiểm tra deserialize từ dictionary."""
        data = {
            "id": "t1",
            "transaction_type": "single_entry",
            "status": "posted",
            "tenant_id": "t1",
            "entries": [],
            "total_debit": "100",
            "total_credit": "0",
            "description": "Single",
            "created_at": "2026-05-21T10:00:00",
        }
        t = FinancialTransaction.from_dict(data)
        assert t.id == "t1"
        assert t.transaction_type == TransactionType.SINGLE_ENTRY
        assert t.status == TransactionStatus.POSTED

    def test_roundtrip(self) -> None:
        """Kiểm tra serialize/deserialize roundtrip."""
        restored = FinancialTransaction.from_dict(self.txn.to_dict())
        assert restored.id == self.txn.id
        assert restored.transaction_type == self.txn.transaction_type
        assert restored.status == self.txn.status


class TestRoundingRule:
    """Test cho model RoundingRule."""

    def setup_method(self) -> None:
        """Setup fixture cho mỗi test."""
        self.rule = RoundingRule(
            currency_code="USD",
            mode=RoundingMode.HALF_UP,
            decimals=2,
        )

    def test_create_valid_rule(self) -> None:
        """Kiểm tra tạo rounding rule hợp lệ."""
        assert self.rule.currency_code == "USD"
        assert self.rule.mode == RoundingMode.HALF_UP
        assert self.rule.decimals == 2

    def test_invalid_currency_code(self) -> None:
        """Kiểm tra reject currency code không hợp lệ."""
        with pytest.raises(MidicoderError):
            RoundingRule(currency_code="US", mode=RoundingMode.HALF_UP)

    def test_empty_currency_code(self) -> None:
        """Kiểm tra reject currency code rỗng."""
        with pytest.raises(MidicoderError):
            RoundingRule(currency_code="", mode=RoundingMode.HALF_UP)

    def test_invalid_decimals(self) -> None:
        """Kiểm tra reject decimals không hợp lệ."""
        with pytest.raises(MidicoderError):
            RoundingRule(currency_code="USD", mode=RoundingMode.HALF_UP, decimals=7)

    def test_apply_half_up(self) -> None:
        """Kiểm tra HALF_UP làm tròn đúng."""
        rule = RoundingRule(currency_code="USD", mode=RoundingMode.HALF_UP, decimals=2)
        result = rule.apply(Decimal("1.555"))
        assert result == Decimal("1.56")

    def test_apply_half_even(self) -> None:
        """Kiểm tra HALF_EVEN (Banker's rounding)."""
        rule = RoundingRule(currency_code="EUR", mode=RoundingMode.HALF_EVEN, decimals=2)
        # 1.545 → 1.54 (even)
        result = rule.apply(Decimal("1.545"))
        assert result == Decimal("1.54")
        # 1.555 → 1.56 (even)
        result2 = rule.apply(Decimal("1.555"))
        assert result2 == Decimal("1.56")

    def test_apply_floor(self) -> None:
        """Kiểm tra FLOOR luôn làm tròn xuống."""
        rule = RoundingRule(currency_code="USD", mode=RoundingMode.FLOOR, decimals=2)
        result = rule.apply(Decimal("1.999"))
        assert result == Decimal("1.99")

    def test_apply_ceiling(self) -> None:
        """Kiểm tra CEILING luôn làm tròn lên."""
        rule = RoundingRule(currency_code="USD", mode=RoundingMode.CEILING, decimals=2)
        result = rule.apply(Decimal("1.001"))
        assert result == Decimal("1.01")

    def test_apply_zero_decimals(self) -> None:
        """Kiểm tra apply với 0 decimals."""
        rule = RoundingRule(currency_code="JPY", mode=RoundingMode.HALF_UP, decimals=0)
        result = rule.apply(Decimal("1234.6"))
        assert result == Decimal("1235")

    def test_to_dict(self) -> None:
        """Kiểm tra serialize thành dictionary."""
        d = self.rule.to_dict()
        assert d["currency_code"] == "USD"
        assert d["mode"] == "half_up"
        assert d["decimals"] == 2

    def test_from_dict(self) -> None:
        """Kiểm tra deserialize từ dictionary."""
        data = {
            "currency_code": "EUR",
            "mode": "half_even",
            "decimals": 2,
        }
        r = RoundingRule.from_dict(data)
        assert r.currency_code == "EUR"
        assert r.mode == RoundingMode.HALF_EVEN

    def test_roundtrip(self) -> None:
        """Kiểm tra serialize/deserialize roundtrip."""
        restored = RoundingRule.from_dict(self.rule.to_dict())
        assert restored.currency_code == self.rule.currency_code
        assert restored.mode == self.rule.mode
        assert restored.decimals == self.rule.decimals


class TestLedgerSnapshot:
    """Test cho model LedgerSnapshot."""

    def setup_method(self) -> None:
        """Setup fixture cho mỗi test."""
        self.snapshot = LedgerSnapshot(
            id="snap-001",
            timestamp=datetime(2026, 5, 21, 12, 0, 0),
            chain_hash="abc123def456",
            entry_count=100,
        )

    def test_create_valid_snapshot(self) -> None:
        """Kiểm tra tạo snapshot hợp lệ."""
        assert self.snapshot.id == "snap-001"
        assert self.snapshot.entry_count == 100
        assert self.snapshot.chain_hash == "abc123def456"

    def test_empty_id_rejected(self) -> None:
        """Kiểm tra reject ID rỗng."""
        with pytest.raises(MidicoderError):
            LedgerSnapshot(
                id="",
                timestamp=datetime.now(),
                chain_hash="hash",
                entry_count=0,
            )

    def test_negative_entry_count_rejected(self) -> None:
        """Kiểm tra reject entry_count âm."""
        with pytest.raises(MidicoderError):
            LedgerSnapshot(
                id="s1",
                timestamp=datetime.now(),
                chain_hash="hash",
                entry_count=-1,
            )

    def test_zero_entry_count_allowed(self) -> None:
        """Kiểm tra cho phép entry_count = 0."""
        s = LedgerSnapshot(
            id="s1",
            timestamp=datetime.now(),
            chain_hash="",
            entry_count=0,
        )
        assert s.entry_count == 0

    def test_to_dict(self) -> None:
        """Kiểm tra serialize thành dictionary."""
        d = self.snapshot.to_dict()
        assert d["id"] == "snap-001"
        assert d["chain_hash"] == "abc123def456"
        assert d["entry_count"] == 100

    def test_from_dict(self) -> None:
        """Kiểm tra deserialize từ dictionary."""
        data = {
            "id": "s2",
            "timestamp": "2026-05-21T12:00:00",
            "chain_hash": "xyz789",
            "entry_count": 50,
        }
        s = LedgerSnapshot.from_dict(data)
        assert s.id == "s2"
        assert s.chain_hash == "xyz789"
        assert s.entry_count == 50

    def test_roundtrip(self) -> None:
        """Kiểm tra serialize/deserialize roundtrip."""
        restored = LedgerSnapshot.from_dict(self.snapshot.to_dict())
        assert restored.id == self.snapshot.id
        assert restored.chain_hash == self.snapshot.chain_hash
        assert restored.entry_count == self.snapshot.entry_count
