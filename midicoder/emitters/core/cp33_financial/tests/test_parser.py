"""
Test cho parser của CP33: Financial Engine.

Kiểm tra:
- Parse currency, fx_rate, account, ledger_entry, transaction, rounding_rule, snapshot
- Parse list currencies, fx_rates, accounts, ledger_entries, transactions, rounding_rules
- Validation errors khi thiếu field required
"""

import pytest
from datetime import datetime
from decimal import Decimal
from midicoder.errors import MidicoderError
from midicoder.emitters.core.cp33_financial.parser import FinancialParser


class TestFinancialParserCurrency:
    """Test cho parse_currency và parse_currencies."""

    def test_parse_valid_currency(self) -> None:
        """Kiểm tra parse currency hợp lệ."""
        data = {
            "code": "USD",
            "name": "US Dollar",
            "symbol": "$",
            "decimal_places": 2,
            "rounding_mode": "half_up",
        }
        c = FinancialParser.parse_currency(data)
        assert c.code == "USD"
        assert c.name == "US Dollar"

    def test_parse_currency_missing_code(self) -> None:
        """Kiểm tra reject currency thiếu code."""
        data = {"name": "Test", "symbol": "T"}
        with pytest.raises(MidicoderError):
            FinancialParser.parse_currency(data)

    def test_parse_currencies_list(self) -> None:
        """Kiểm tra parse danh sách currencies."""
        data = [
            {"code": "USD", "name": "US Dollar", "symbol": "$"},
            {"code": "EUR", "name": "Euro", "symbol": "€"},
        ]
        currencies = FinancialParser.parse_currencies(data)
        assert len(currencies) == 2
        assert currencies[0].code == "USD"
        assert currencies[1].code == "EUR"


class TestFinancialParserFXRate:
    """Test cho parse_fx_rate và parse_fx_rates."""

    def test_parse_valid_fx_rate(self) -> None:
        """Kiểm tra parse FXRate hợp lệ."""
        data = {
            "from_currency": "EUR",
            "to_currency": "USD",
            "rate": "1.0850",
            "effective_from": "2026-01-01T00:00:00",
        }
        r = FinancialParser.parse_fx_rate(data)
        assert r.from_currency == "EUR"
        assert r.rate == Decimal("1.0850")

    def test_parse_fx_rate_missing_field(self) -> None:
        """Kiểm tra reject FXRate thiếu required field."""
        data = {"from_currency": "EUR"}
        with pytest.raises(MidicoderError):
            FinancialParser.parse_fx_rate(data)

    def test_parse_fx_rates_list(self) -> None:
        """Kiểm tra parse danh sách FX rates."""
        data = [
            {"from_currency": "EUR", "to_currency": "USD", "rate": "1.08", "effective_from": "2026-01-01T00:00:00"},
            {"from_currency": "GBP", "to_currency": "USD", "rate": "1.25", "effective_from": "2026-01-01T00:00:00"},
        ]
        rates = FinancialParser.parse_fx_rates(data)
        assert len(rates) == 2
        assert rates[0].pair == "EUR/USD"


class TestFinancialParserAccount:
    """Test cho parse_account và parse_accounts."""

    def test_parse_valid_account(self) -> None:
        """Kiểm tra parse account hợp lệ."""
        data = {
            "code": "1000",
            "name": "Cash",
            "account_type": "asset",
        }
        a = FinancialParser.parse_account(data)
        assert a.code == "1000"
        assert a.name == "Cash"

    def test_parse_account_missing_code(self) -> None:
        """Kiểm tra reject account thiếu code."""
        data = {"name": "Test"}
        with pytest.raises(MidicoderError):
            FinancialParser.parse_account(data)

    def test_parse_account_missing_name(self) -> None:
        """Kiểm tra reject account thiếu name."""
        data = {"code": "1000"}
        with pytest.raises(MidicoderError):
            FinancialParser.parse_account(data)

    def test_parse_accounts_list(self) -> None:
        """Kiểm tra parse danh sách accounts."""
        data = [
            {"code": "1000", "name": "Cash", "account_type": "asset"},
            {"code": "4000", "name": "Revenue", "account_type": "income"},
        ]
        accounts = FinancialParser.parse_accounts(data)
        assert len(accounts) == 2
        assert accounts[0].code == "1000"


class TestFinancialParserLedgerEntry:
    """Test cho parse_ledger_entry và parse_ledger_entries."""

    def test_parse_valid_entry(self) -> None:
        """Kiểm tra parse ledger entry hợp lệ."""
        data = {
            "id": "e1",
            "transaction_id": "t1",
            "entry_type": "debit",
            "account_code": "1000",
            "amount": "1000.00",
            "currency": "USD",
        }
        e = FinancialParser.parse_ledger_entry(data)
        assert e.id == "e1"
        assert e.amount == Decimal("1000.00")

    def test_parse_entry_missing_field(self) -> None:
        """Kiểm tra reject entry thiếu required field."""
        data = {"id": "e1"}
        with pytest.raises(MidicoderError):
            FinancialParser.parse_ledger_entry(data)

    def test_parse_ledger_entries_list(self) -> None:
        """Kiểm tra parse danh sách ledger entries."""
        data = [
            {"id": "e1", "transaction_id": "t1", "entry_type": "debit", "account_code": "1000", "amount": "100", "currency": "USD"},
            {"id": "e2", "transaction_id": "t1", "entry_type": "credit", "account_code": "4000", "amount": "100", "currency": "USD"},
        ]
        entries = FinancialParser.parse_ledger_entries(data)
        assert len(entries) == 2


class TestFinancialParserTransaction:
    """Test cho parse_transaction và parse_transactions."""

    def test_parse_valid_transaction(self) -> None:
        """Kiểm tra parse transaction hợp lệ."""
        data = {
            "id": "t1",
            "transaction_type": "double_entry",
            "entries": [],
        }
        t = FinancialParser.parse_transaction(data)
        assert t.id == "t1"

    def test_parse_transaction_missing_id(self) -> None:
        """Kiểm tra reject transaction thiếu ID."""
        data = {"transaction_type": "single_entry"}
        with pytest.raises(MidicoderError):
            FinancialParser.parse_transaction(data)

    def test_parse_transactions_list(self) -> None:
        """Kiểm tra parse danh sách transactions."""
        data = [
            {"id": "t1", "transaction_type": "double_entry", "entries": []},
            {"id": "t2", "transaction_type": "single_entry", "entries": []},
        ]
        txns = FinancialParser.parse_transactions(data)
        assert len(txns) == 2


class TestFinancialParserRoundingRule:
    """Test cho parse_rounding_rule và parse_rounding_rules."""

    def test_parse_valid_rule(self) -> None:
        """Kiểm tra parse rounding rule hợp lệ."""
        data = {
            "currency_code": "USD",
            "mode": "half_up",
            "decimals": 2,
        }
        r = FinancialParser.parse_rounding_rule(data)
        assert r.currency_code == "USD"

    def test_parse_rule_missing_currency(self) -> None:
        """Kiểm tra reject rule thiếu currency_code."""
        data = {"mode": "half_up"}
        with pytest.raises(MidicoderError):
            FinancialParser.parse_rounding_rule(data)

    def test_parse_rounding_rules_list(self) -> None:
        """Kiểm tra parse danh sách rounding rules."""
        data = [
            {"currency_code": "USD", "mode": "half_up"},
            {"currency_code": "EUR", "mode": "half_even"},
        ]
        rules = FinancialParser.parse_rounding_rules(data)
        assert len(rules) == 2


class TestFinancialParserSnapshot:
    """Test cho parse_ledger_snapshot."""

    def test_parse_valid_snapshot(self) -> None:
        """Kiểm tra parse ledger snapshot hợp lệ."""
        data = {
            "id": "snap-001",
            "timestamp": "2026-05-21T12:00:00",
            "chain_hash": "abc123",
            "entry_count": 100,
        }
        s = FinancialParser.parse_ledger_snapshot(data)
        assert s.id == "snap-001"
        assert s.entry_count == 100

    def test_parse_snapshot_missing_field(self) -> None:
        """Kiểm tra reject snapshot thiếu required field."""
        data = {"id": "snap-001"}
        with pytest.raises(MidicoderError):
            FinancialParser.parse_ledger_snapshot(data)
