"""
Parser cho CP33: Financial Engine.

Parse dữ liệu từ DSL/dict thành các model của Financial Engine:
- Currency, FXRate, Account, LedgerEntry, FinancialTransaction, RoundingRule, LedgerSnapshot
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM
from midicoder.emitters.core.cp33_financial.models import (
    Account,
    AccountType,
    Currency,
    EntryType,
    FXRate,
    FXSource,
    FinancialTransaction,
    LedgerEntry,
    LedgerSnapshot,
    RoundingMode,
    RoundingRule,
    TransactionStatus,
    TransactionType,
)


class FinancialParser:
    """
    Parser cho các model của Financial Engine.

    Parse dữ liệu từ dict/YAML thành typed models.
    """

    @staticmethod
    def parse_currency(data: dict[str, Any]) -> Currency:
        """
        Parse dict thành Currency.

        Args:
            data: Dictionary chứa thông tin currency.

        Returns:
            Currency instance đã validate.

        Raises:
            MidicoderError: Nếu dữ liệu không hợp lệ.
        """
        if not data.get("code"):
            raise EM.raise_error(
                ErrorCode.CP33_DSL_PARSE_ERROR,
                reason="Currency code is required"
            )
        return Currency.from_dict(data)

    @staticmethod
    def parse_fx_rate(data: dict[str, Any]) -> FXRate:
        """
        Parse dict thành FXRate.

        Args:
            data: Dictionary chứa thông tin tỷ giá.

        Returns:
            FXRate instance đã validate.

        Raises:
            MidicoderError: Nếu dữ liệu không hợp lệ.
        """
        required = ["from_currency", "to_currency", "rate", "effective_from"]
        for key in required:
            if key not in data:
                raise EM.raise_error(
                    ErrorCode.CP33_DSL_PARSE_ERROR,
                    reason=f"FXRate requires field: {key}"
                )
        return FXRate.from_dict(data)

    @staticmethod
    def parse_account(data: dict[str, Any]) -> Account:
        """
        Parse dict thành Account.

        Args:
            data: Dictionary chứa thông tin tài khoản.

        Returns:
            Account instance đã validate.

        Raises:
            MidicoderError: Nếu dữ liệu không hợp lệ.
        """
        if not data.get("code"):
            raise EM.raise_error(
                ErrorCode.CP33_DSL_PARSE_ERROR,
                reason="Account code is required"
            )
        if not data.get("name"):
            raise EM.raise_error(
                ErrorCode.CP33_DSL_PARSE_ERROR,
                reason="Account name is required"
            )
        return Account.from_dict(data)

    @staticmethod
    def parse_ledger_entry(data: dict[str, Any]) -> LedgerEntry:
        """
        Parse dict thành LedgerEntry.

        Args:
            data: Dictionary chứa thông tin ledger entry.

        Returns:
            LedgerEntry instance đã validate.

        Raises:
            MidicoderError: Nếu dữ liệu không hợp lệ.
        """
        required = ["id", "transaction_id", "entry_type", "account_code", "amount", "currency"]
        for key in required:
            if key not in data:
                raise EM.raise_error(
                    ErrorCode.CP33_DSL_PARSE_ERROR,
                    reason=f"LedgerEntry requires field: {key}"
                )
        return LedgerEntry.from_dict(data)

    @staticmethod
    def parse_transaction(data: dict[str, Any]) -> FinancialTransaction:
        """
        Parse dict thành FinancialTransaction.

        Args:
            data: Dictionary chứa thông tin giao dịch.

        Returns:
            FinancialTransaction instance đã validate.

        Raises:
            MidicoderError: Nếu dữ liệu không hợp lệ.
        """
        if not data.get("id"):
            raise EM.raise_error(
                ErrorCode.CP33_DSL_PARSE_ERROR,
                reason="Transaction ID is required"
            )
        return FinancialTransaction.from_dict(data)

    @staticmethod
    def parse_rounding_rule(data: dict[str, Any]) -> RoundingRule:
        """
        Parse dict thành RoundingRule.

        Args:
            data: Dictionary chứa thông tin rounding rule.

        Returns:
            RoundingRule instance đã validate.

        Raises:
            MidicoderError: Nếu dữ liệu không hợp lệ.
        """
        if not data.get("currency_code"):
            raise EM.raise_error(
                ErrorCode.CP33_DSL_PARSE_ERROR,
                reason="RoundingRule requires currency_code"
            )
        return RoundingRule.from_dict(data)

    @staticmethod
    def parse_ledger_snapshot(data: dict[str, Any]) -> LedgerSnapshot:
        """
        Parse dict thành LedgerSnapshot.

        Args:
            data: Dictionary chứa thông tin snapshot.

        Returns:
            LedgerSnapshot instance đã validate.

        Raises:
            MidicoderError: Nếu dữ liệu không hợp lệ.
        """
        required = ["id", "timestamp", "chain_hash", "entry_count"]
        for key in required:
            if key not in data:
                raise EM.raise_error(
                    ErrorCode.CP33_DSL_PARSE_ERROR,
                    reason=f"LedgerSnapshot requires field: {key}"
                )
        return LedgerSnapshot.from_dict(data)

    @classmethod
    def parse_currencies(cls, data: list[dict[str, Any]]) -> list[Currency]:
        """
        Parse danh sách currencies.

        Args:
            data: List dictionary chứa thông tin currencies.

        Returns:
            List Currency instances.
        """
        return [cls.parse_currency(d) for d in data]

    @classmethod
    def parse_fx_rates(cls, data: list[dict[str, Any]]) -> list[FXRate]:
        """
        Parse danh sách FX rates.

        Args:
            data: List dictionary chứa thông tin tỷ giá.

        Returns:
            List FXRate instances.
        """
        return [cls.parse_fx_rate(d) for d in data]

    @classmethod
    def parse_accounts(cls, data: list[dict[str, Any]]) -> list[Account]:
        """
        Parse danh sách accounts.

        Args:
            data: List dictionary chứa thông tin tài khoản.

        Returns:
            List Account instances.
        """
        return [cls.parse_account(d) for d in data]

    @classmethod
    def parse_ledger_entries(cls, data: list[dict[str, Any]]) -> list[LedgerEntry]:
        """
        Parse danh sách ledger entries.

        Args:
            data: List dictionary chứa thông tin ledger entries.

        Returns:
            List LedgerEntry instances.
        """
        return [cls.parse_ledger_entry(d) for d in data]

    @classmethod
    def parse_transactions(cls, data: list[dict[str, Any]]) -> list[FinancialTransaction]:
        """
        Parse danh sách transactions.

        Args:
            data: List dictionary chứa thông tin giao dịch.

        Returns:
            List FinancialTransaction instances.
        """
        return [cls.parse_transaction(d) for d in data]

    @classmethod
    def parse_rounding_rules(cls, data: list[dict[str, Any]]) -> list[RoundingRule]:
        """
        Parse danh sách rounding rules.

        Args:
            data: List dictionary chứa thông tin rounding rules.

        Returns:
            List RoundingRule instances.
        """
        return [cls.parse_rounding_rule(d) for d in data]
