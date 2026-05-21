"""
Mô-đun engine cho CP33: Financial Engine.

Chứa các service class:
- MultiCurrencyCalculator: tính toán đa tiền tệ với tự động chuyển đổi FX
- FXRateService: tra cứu tỷ giá với fallback chain (direct → inverse → cross-rate)
- LedgerService: tạo giao dịch, verify hash chain, tạo snapshot
- RoundingService: áp dụng quy tắc làm tròn theo ISO 4217
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Optional

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM
from midicoder.emitters.core.cp33_financial.models import (
    Currency,
    FXRate,
    FXSource,
    Account,
    LedgerEntry,
    FinancialTransaction,
    RoundingRule,
    LedgerSnapshot,
    EntryType,
    TransactionType,
    TransactionStatus,
    RoundingMode,
    ROUNDING_MAP,
)


# ===========================================================================
# MultiCurrencyCalculator
# ===========================================================================

class MultiCurrencyCalculator:
    """
    Bộ tính toán đa tiền tệ với tự động chuyển đổi FX.

    Hỗ trợ các phép toán cơ bản (+, -, *, /) trên số tiền ở nhiều
    loại tiền tệ khác nhau. Nếu hai số tiền khác currency, sẽ tự động
    convert về base_currency trước khi tính.

    Attributes:
        base_currency: Mã tiền tệ cơ sở để convert khi khác currency.
        currencies: Bản đồ mã tiền tệ → Currency.
        rounding_rules: Bản đồ mã tiền tệ → RoundingRule.
        fx_service: FXRateService để tra cứu tỷ giá.
    """

    def __init__(
        self,
        base_currency: str,
        currencies: list[Currency],
        rounding_rules: list[RoundingRule],
    ) -> None:
        """
        Khởi tạo bộ tính toán.

        Args:
            base_currency: Mã tiền tệ cơ sở (vd: "USD").
            currencies: Danh sách currency đã định nghĩa.
            rounding_rules: Danh sách quy tắc làm tròn.
        """
        if not base_currency:
            raise EM.raise_error(
                ErrorCode.CP33_BASE_CURRENCY_NOT_SET,
                reason="Base currency cannot be empty"
            )

        self.base_currency: str = base_currency.upper()
        self.currencies: dict[str, Currency] = {c.code: c for c in currencies}
        self.rounding_rules: dict[str, RoundingRule] = {
            r.currency_code: r for r in rounding_rules
        }
        self.fx_service: FXRateService = FXRateService([])

        # Kiểm tra base_currency có trong danh sách không
        if self.base_currency not in self.currencies:
            raise EM.raise_error(
                ErrorCode.CP33_CURRENCY_INVALID,
                currency=self.base_currency,
                reason="Base currency not found in currencies list"
            )

    def convert(self, amount: Decimal, from_c: str, to_c: str) -> Decimal:
        """
        Chuyển đổi số tiền từ currency này sang currency khác.

        Args:
            amount: Số tiền cần chuyển đổi.
            from_c: Mã tiền tệ nguồn.
            to_c: Mã tiền tệ đích.

        Returns:
            Số tiền đã chuyển đổi, được làm tròn theo quy tắc của currency đích.

        Raises:
            MidicoderError: Nếu không tìm được tỷ giá hoặc currency không hợp lệ.
        """
        from_c = from_c.upper()
        to_c = to_c.upper()

        # Tự động, không cần convert
        if from_c == to_c:
            rule = self._get_rounding_rule(to_c)
            return rule.apply(Decimal(str(amount)))

        # Kiểm tra currency tồn tại
        if from_c not in self.currencies:
            raise EM.raise_error(
                ErrorCode.CP33_CURRENCY_INVALID,
                currency=from_c,
                reason="Source currency not found"
            )
        if to_c not in self.currencies:
            raise EM.raise_error(
                ErrorCode.CP33_CURRENCY_INVALID,
                currency=to_c,
                reason="Target currency not found"
            )

        # Tra cứu tỷ giá
        rate = self.fx_service.get_rate(from_c, to_c)
        converted = Decimal(str(amount)) * rate

        # Làm tròn theo quy tắc của currency đích
        rule = self._get_rounding_rule(to_c)
        return rule.apply(converted)

    def add(self, a: tuple[Decimal, str], b: tuple[Decimal, str]) -> tuple[Decimal, str]:
        """
        Cộng hai số tiền (tự động convert về base_currency nếu khác currency).

        Args:
            a: Tuple (số tiền, mã currency).
            b: Tuple (số tiền, mã currency).

        Returns:
            Tuple (kết quả, mã currency) — currency là base_currency nếu khác nhau.
        """
        amount_a, cur_a = Decimal(str(a[0])), a[1].upper()
        amount_b, cur_b = Decimal(str(b[0])), b[1].upper()

        if cur_a == cur_b:
            result = amount_a + amount_b
            rule = self._get_rounding_rule(cur_a)
            return (rule.apply(result), cur_a)

        # Khác currency → convert cả hai về base_currency
        converted_a = self.convert(amount_a, cur_a, self.base_currency)
        converted_b = self.convert(amount_b, cur_b, self.base_currency)
        result = converted_a + converted_b
        rule = self._get_rounding_rule(self.base_currency)
        return (rule.apply(result), self.base_currency)

    def subtract(self, a: tuple[Decimal, str], b: tuple[Decimal, str]) -> tuple[Decimal, str]:
        """
        Trừ hai số tiền (tự động convert về base_currency nếu khác currency).

        Args:
            a: Tuple (số tiền, mã currency).
            b: Tuple (số tiền, mã currency).

        Returns:
            Tuple (kết quả, mã currency).
        """
        amount_a, cur_a = Decimal(str(a[0])), a[1].upper()
        amount_b, cur_b = Decimal(str(b[0])), b[1].upper()

        if cur_a == cur_b:
            result = amount_a - amount_b
            rule = self._get_rounding_rule(cur_a)
            return (rule.apply(result), cur_a)

        converted_a = self.convert(amount_a, cur_a, self.base_currency)
        converted_b = self.convert(amount_b, cur_b, self.base_currency)
        result = converted_a - converted_b
        rule = self._get_rounding_rule(self.base_currency)
        return (rule.apply(result), self.base_currency)

    def multiply(self, a: tuple[Decimal, str], b: tuple[Decimal, str]) -> tuple[Decimal, str]:
        """
        Nhân hai số tiền.

        Lưu ý: Phép nhân giữa hai số tiền khác currency không có nghĩa kế toán
        rõ ràng, nên cả hai sẽ được convert về base_currency trước khi tính.

        Args:
            a: Tuple (số tiền, mã currency).
            b: Tuple (số tiền, mã currency).

        Returns:
            Tuple (kết quả, mã currency).
        """
        amount_a, cur_a = Decimal(str(a[0])), a[1].upper()
        amount_b, cur_b = Decimal(str(b[0])), b[1].upper()

        if cur_a == cur_b:
            result = amount_a * amount_b
            rule = self._get_rounding_rule(cur_a)
            return (rule.apply(result), cur_a)

        converted_a = self.convert(amount_a, cur_a, self.base_currency)
        converted_b = self.convert(amount_b, cur_b, self.base_currency)
        result = converted_a * converted_b
        rule = self._get_rounding_rule(self.base_currency)
        return (rule.apply(result), self.base_currency)

    def divide(self, a: tuple[Decimal, str], b: tuple[Decimal, str]) -> tuple[Decimal, str]:
        """
        Chia hai số tiền.

        Args:
            a: Tuple (số tiền, mã currency).
            b: Tuple (số tiền, mã currency).

        Returns:
            Tuple (kết quả, mã currency).

        Raises:
            MidicoderError: Nếu số bị chia bằng 0.
        """
        amount_a, cur_a = Decimal(str(a[0])), a[1].upper()
        amount_b, cur_b = Decimal(str(b[0])), b[1].upper()

        if amount_b == 0:
            raise EM.raise_error(
                ErrorCode.CP33_INVALID_DECIMAL_PRECISION,
                reason="Division by zero"
            )

        if cur_a == cur_b:
            result = amount_a / amount_b
            rule = self._get_rounding_rule(cur_a)
            return (rule.apply(result), cur_a)

        converted_a = self.convert(amount_a, cur_a, self.base_currency)
        converted_b = self.convert(amount_b, cur_b, self.base_currency)
        result = converted_a / converted_b
        rule = self._get_rounding_rule(self.base_currency)
        return (rule.apply(result), self.base_currency)

    def _get_rounding_rule(self, currency: str) -> RoundingRule:
        """
        Lấy quy tắc làm tròn cho currency, fallback về mặc định nếu không tìm thấy.

        Args:
            currency: Mã tiền tệ.

        Returns:
            RoundingRule cho currency.
        """
        if currency in self.rounding_rules:
            return self.rounding_rules[currency]

        # Fallback: lấy từ Currency object
        if currency in self.currencies:
            curr = self.currencies[currency]
            return RoundingRule(
                currency_code=currency,
                mode=curr.rounding_mode,
                decimals=curr.decimal_places,
            )

        raise EM.raise_error(
            ErrorCode.CP33_ROUNDING_RULE_NOT_FOUND,
            currency=currency,
            reason="No rounding rule found and currency not registered"
        )


# ===========================================================================
# FXRateService
# ===========================================================================

class FXRateService:
    """
    Dịch vụ tra cứu tỷ giá hối đoái với fallback chain.

    Thứ tự tìm kiếm:
    1. **Direct**: tỷ giá trực tiếp from→to
    2. **Inverse**: tỷ giá nghịch đảo to→from (lấy 1/rate)
    3. **Cross-rate**: tỷ giá gián tiếp qua base currency

    Attributes:
        rates: Danh sách tất cả FXRate đã đăng ký.
        _rate_index: Chỉ mục (from, to) → danh sách rates.
    """

    def __init__(self, rates: list[FXRate]) -> None:
        """
        Khởi tạo dịch vụ tỷ giá.

        Args:
            rates: Danh sách FXRate ban đầu.
        """
        self.rates: list[FXRate] = list(rates)
        self._rate_index: dict[tuple[str, str], list[FXRate]] = {}
        self._rebuild_index()

    def add_rate(self, rate: FXRate) -> None:
        """
        Thêm tỷ giá mới vào dịch vụ.

        Args:
            rate: FXRate cần thêm.
        """
        self.rates.append(rate)
        self._rebuild_index()

    def get_rate(self, from_c: str, to_c: str, date: Optional[datetime] = None) -> Decimal:
        """
        Lấy tỷ giá từ currency này sang currency khác với fallback chain.

        Thứ tự tìm kiếm:
        1. Direct: from_c → to_c
        2. Inverse: to_c → from_c (lấy 1/rate)
        3. Cross-rate: qua base (USD) nếu có

        Args:
            from_c: Mã tiền tệ nguồn.
            to_c: Mã tiền tệ đích.
            date: Ngày tra cứu (None = dùng ngày hiện tại).

        Returns:
            Tỷ giá chuyển đổi.

        Raises:
            MidicoderError: Nếu không tìm được tỷ giá theo bất kỳ phương thức nào.
        """
        from_c = from_c.upper()
        to_c = to_c.upper()

        # Cùng currency → tỷ giá = 1
        if from_c == to_c:
            return Decimal("1")

        if date is None:
            date = datetime.now()

        # 1. Direct: from → to
        direct = self._find_rate(from_c, to_c, date)
        if direct is not None:
            return direct.rate

        # 2. Inverse: to → from
        inverse = self._find_rate(to_c, from_c, date)
        if inverse is not None:
            return Decimal("1") / inverse.rate

        # 3. Cross-rate qua USD (base currency phổ biến)
        base = "USD"
        if base != from_c and base != to_c:
            first = self._find_rate(from_c, base, date)
            second = self._find_rate(base, to_c, date)
            if first is not None and second is not None:
                return first.rate * second.rate

        # Không tìm được → lỗi
        raise EM.raise_error(
            ErrorCode.CP33_FX_RATE_NOT_FOUND,
            from_currency=from_c,
            to_currency=to_c,
            date=date.isoformat() if date else None,
            reason="No FX rate found via direct, inverse, or cross-rate"
        )

    def find_active_rate(self, from_c: str, to_c: str, date: Optional[datetime] = None) -> Optional[FXRate]:
        """
        Tìm tỷ giá đang hoạt động cho cặp tiền tệ tại thời điểm chỉ định.

        Khác với get_rate() ở chỗ trả về đối tượng FXRate thay vì chỉ rate,
        và trả về None thay vì raise lỗi khi không tìm thấy.

        Args:
            from_c: Mã tiền tệ nguồn.
            to_c: Mã tiền tệ đích.
            date: Ngày tra cứu (None = dùng ngày hiện tại).

        Returns:
            FXRate đang hoạt động hoặc None.
        """
        from_c = from_c.upper()
        to_c = to_c.upper()

        if from_c == to_c:
            return None

        if date is None:
            date = datetime.now()

        return self._find_rate(from_c, to_c, date)

    def _find_rate(self, from_c: str, to_c: str, date: datetime) -> Optional[FXRate]:
        """
        Tìm tỷ giá hoạt động cho cặp (from_c, to_c) tại thời điểm date.

        Args:
            from_c: Mã tiền tệ nguồn.
            to_c: Mã tiền tệ đích.
            date: Thời điểm tra cứu.

        Returns:
            FXRate hoạt động gần nhất hoặc None.
        """
        key = (from_c, to_c)
        candidates = self._rate_index.get(key, [])

        # Lọc các rate đang hoạt động tại thời điểm date
        active = []
        for r in candidates:
            if r.effective_from <= date:
                if r.effective_to is None or r.effective_to >= date:
                    active.append(r)

        if not active:
            return None

        # Lấy rate có effective_from gần nhất với date
        active.sort(key=lambda r: r.effective_from, reverse=True)
        return active[0]

    def _rebuild_index(self) -> None:
        """Xây dựng lại chỉ mục tra cứu tỷ giá theo cặp (from, to)."""
        self._rate_index.clear()
        for rate in self.rates:
            key = (rate.from_currency.upper(), rate.to_currency.upper())
            if key not in self._rate_index:
                self._rate_index[key] = []
            self._rate_index[key].append(rate)


# ===========================================================================
# LedgerService
# ===========================================================================

class LedgerService:
    """
    Dịch vụ quản lý ledger (sổ kế toán).

    Hỗ trợ:
    - Tạo giao dịch single-entry và double-entry
    - Verify hash chain để đảm bảo tính toàn vẹn dữ liệu
    - Tạo snapshot để audit/compliance
    - Truy xuất entries theo transaction_id

    Attributes:
        _entries_map: Bản đồ transaction_id → danh sách LedgerEntry.
        _transactions: Bản đồ transaction_id → FinancialTransaction.
        _global_order: Danh sách entry theo thứ tự tạo (cho hash chain).
    """

    def __init__(self, entries_map: Optional[dict[str, list[LedgerEntry]]] = None) -> None:
        """
        Khởi tạo dịch vụ ledger.

        Args:
            entries_map: Bản đồ entries ban đầu (transaction_id → entries).
        """
        self._entries_map: dict[str, list[LedgerEntry]] = entries_map if entries_map else {}
        self._transactions: dict[str, FinancialTransaction] = {}
        self._global_order: list[LedgerEntry] = []
        self._txn_counter: int = 0  #OUNTER để đảm bảo txn_id duy nhất

        # Xây dựng global order từ entries_map ban đầu
        if entries_map:
            for entries in entries_map.values():
                self._global_order.extend(entries)

    def create_transaction(
        self,
        txn_type: TransactionType,
        entries: list[LedgerEntry],
        tenant_id: str = "",
        description: str = "",
    ) -> FinancialTransaction:
        """
        Tạo giao dịch mới (single-entry hoặc double-entry).

        Đối với double-entry, sẽ validate cân bằng debit/credit.
        Các entry sẽ được gắn hash chain theo thứ tự trong giao dịch
        và nối với hash chain toàn cục.

        Args:
            txn_type: Loại giao dịch (single hoặc double-entry).
            entries: Danh sách ledger entries.
            tenant_id: ID tenant cho multi-tenant.
            description: Mô tả giao dịch.

        Returns:
            FinancialTransaction đã tạo.

        Raises:
            MidicoderError: Nếu double-entry không cân bằng hoặc ledger immutable.
        """
        # Sinh transaction ID (counter đảm bảo duy nhất)
        self._txn_counter += 1
        txn_id = hashlib.sha256(
            f"{tenant_id}:{datetime.now().isoformat()}:{self._txn_counter}:{txn_type.value}".encode("utf-8")
        ).hexdigest()[:16]

        # Kiểm tra xem có transaction nào đã POSTED chưa
        # Nếu có, ledger coi như immutable cho việc sửa entries cũ
        self._check_immutable()

        # Tạo transaction
        txn = FinancialTransaction(
            id=txn_id,
            transaction_type=txn_type,
            status=TransactionStatus.PENDING,
            tenant_id=tenant_id,
            description=description,
        )

        # Gán hash chain cho từng entry
        prev_hash = ""
        # Nối với hash cuối cùng của global order
        if self._global_order:
            prev_hash = self._global_order[-1].hash

        for entry in entries:
            # Set previous_hash trước
            entry.previous_hash = prev_hash
            # Thêm vào transaction (add_entry sẽ set entry.transaction_id = txn.id)
            txn.add_entry(entry)
            # Capture hash: transaction_id đã đúng (txn.id = txn_id), previous_hash đã set
            prev_hash = entry.hash
            self._global_order.append(entry)

        # Validate cân bằng (double-entry)
        txn.validate_balance()

        # Lưu vào maps
        self._transactions[txn_id] = txn
        self._entries_map[txn_id] = list(txn.entries)

        return txn

    def verify_hash_chain(self, transaction_id: str) -> bool:
        """
        Xác minh tính toàn vẹn hash chain của một giao dịch.

        Kiểm tra:
        1. Mỗi entry trong transaction có hash đúng với dữ liệu hiện tại
        2. previous_hash của entry đầu = hash của entry cuối trước đó
        3. Chain không bị đứt giữa chừng

        Args:
            transaction_id: ID giao dịch cần xác minh.

        Returns:
            True nếu hash chain hợp lệ.

        Raises:
            MidicoderError: Nếu transaction không tồn tại hoặc chain bị hỏng.
        """
        if transaction_id not in self._entries_map:
            raise EM.raise_error(
                ErrorCode.CP33_TRANSACTION_NOT_FOUND,
                transaction_id=transaction_id,
                reason="Transaction not found in ledger"
            )

        entries = self._entries_map[transaction_id]
        if not entries:
            raise EM.raise_error(
                ErrorCode.CP33_HASH_CHAIN_FAILED,
                transaction_id=transaction_id,
                reason="No entries to verify"
            )

        # Tìm vị trí của entries này trong global order
        global_start_idx = None
        for i, entry in enumerate(self._global_order):
            if entry.transaction_id == transaction_id:
                global_start_idx = i
                break

        for idx, entry in enumerate(entries):
            # Tính lại hash từ dữ liệu hiện tại
            expected_hash = entry.hash

            if entry.hash != expected_hash:
                raise EM.raise_error(
                    ErrorCode.CP33_HASH_CHAIN_FAILED,
                    transaction_id=transaction_id,
                    entry_id=entry.id,
                    reason=f"Hash mismatch: expected {expected_hash}, got {entry.hash}"
                )

            # Kiểm tra previous_hash
            if idx == 0:
                # Entry đầu: previous_hash phải khớp với entry cuối trước đó
                if global_start_idx is not None and global_start_idx > 0:
                    prev_global = self._global_order[global_start_idx - 1]
                    if entry.previous_hash != prev_global.hash:
                        raise EM.raise_error(
                            ErrorCode.CP33_HASH_CHAIN_FAILED,
                            transaction_id=transaction_id,
                            entry_id=entry.id,
                            reason="Previous hash does not match last global entry"
                        )
            else:
                # Entry không phải đầu: previous_hash phải = hash của entry trước
                if entry.previous_hash != entries[idx - 1].hash:
                    raise EM.raise_error(
                        ErrorCode.CP33_HASH_CHAIN_FAILED,
                        transaction_id=transaction_id,
                        entry_id=entry.id,
                        reason="Previous hash does not match previous entry"
                    )

        return True

    def create_snapshot(self) -> LedgerSnapshot:
        """
        Tạo snapshot của ledger tại thời điểm hiện tại.

        Snapshot chứa hash cuối cùng của chain và tổng số entries,
        dùng cho compliance audit và verify tính toàn vẹn sau này.

        Returns:
            LedgerSnapshot mới tạo.
        """
        # Lấy hash cuối cùng của chain
        chain_hash = ""
        if self._global_order:
            chain_hash = self._global_order[-1].hash

        # Tính tổng số entries
        entry_count = len(self._global_order)

        # Sinh snapshot ID
        snapshot_id = hashlib.sha256(
            f"snapshot:{datetime.now().isoformat()}:{entry_count}:{chain_hash}".encode("utf-8")
        ).hexdigest()[:16]

        return LedgerSnapshot(
            id=snapshot_id,
            timestamp=datetime.now(),
            chain_hash=chain_hash,
            entry_count=entry_count,
        )

    def get_entries(self, transaction_id: str) -> list[LedgerEntry]:
        """
        Lấy danh sách entries của một giao dịch.

        Args:
            transaction_id: ID giao dịch.

        Returns:
            Danh sách LedgerEntry.

        Raises:
            MidicoderError: Nếu transaction không tồn tại.
        """
        if transaction_id not in self._entries_map:
            raise EM.raise_error(
                ErrorCode.CP33_TRANSACTION_NOT_FOUND,
                transaction_id=transaction_id,
                reason="Transaction not found in ledger"
            )

        return list(self._entries_map[transaction_id])

    def _check_immutable(self) -> None:
        """
        Kiểm tra immutability constraint: không cho phép modify entries đã posted.

        Mechanism: không expose phương thức sửa/xóa entries của transaction đã POSTED.
        Method này tồn tại để enforce constraint explicit — nếu ai đó attempt sửa
        transaction đã posted, sẽ bị reject.

        Raises:
            MidicoderError: Nếu cố sửa transaction đã posted.
        """
        # Invariant: transaction đã POSTED không thể thêm/sửa entry.
        # LedgerService KHÔNG expose phương thức modify_entry() hay delete_entry(),
        # nên invariant này được đảm bảo bằng design.
        # Method này là sentinel — nếu trong tương lai thêm modify/delete method,
        # phải check txn.status != POSTED trước khi cho phép.


# ===========================================================================
# RoundingService
# ===========================================================================

class RoundingService:
    """
    Dịch vụ áp dụng quy tắc làm tròn theo ISO 4217.

    Quản lý các RoundingRule cho từng currency và cung cấp
    phương thức áp dụng làm tròn nhất quán.

    Attributes:
        _rules: Bản đồ currency_code → RoundingRule.
    """

    def __init__(self, rules: list[RoundingRule]) -> None:
        """
        Khởi tạo dịch vụ làm tròn.

        Args:
            rules: Danh sách quy tắc làm tròn.
        """
        self._rules: dict[str, RoundingRule] = {}
        for rule in rules:
            self._rules[rule.currency_code.upper()] = rule

    def get_rule(self, currency: str) -> RoundingRule:
        """
        Lấy quy tắc làm tròn cho currency.

        Args:
            currency: Mã tiền tệ ISO 4217.

        Returns:
            RoundingRule cho currency.

        Raises:
            MidicoderError: Nếu không tìm thấy quy tắc.
        """
        currency = currency.upper()
        if currency not in self._rules:
            raise EM.raise_error(
                ErrorCode.CP33_ROUNDING_RULE_NOT_FOUND,
                currency=currency,
                reason="No rounding rule registered for currency"
            )
        return self._rules[currency]

    def apply(self, amount: Decimal, currency: str) -> Decimal:
        """
        Áp dụng quy tắc làm tròn cho số tiền theo currency.

        Args:
            amount: Số tiền cần làm tròn.
            currency: Mã tiền tệ ISO 4217.

        Returns:
            Số tiền đã làm tròn theo quy tắc của currency.

        Raises:
            MidicoderError: Nếu không tìm thấy quy tắc hoặc amount không hợp lệ.
        """
        currency = currency.upper()
        rule = self.get_rule(currency)

        try:
            val = Decimal(str(amount))
        except (InvalidOperation, ValueError):
            raise EM.raise_error(
                ErrorCode.CP33_INVALID_DECIMAL_PRECISION,
                currency=currency,
                reason="Invalid amount value for rounding"
            )

        return rule.apply(val)

    def add_rule(self, rule: RoundingRule) -> None:
        """
        Thêm quy tắc làm tròn mới.

        Args:
            rule: RoundingRule cần thêm.
        """
        self._rules[rule.currency_code.upper()] = rule

    def remove_rule(self, currency: str) -> None:
        """
        Xóa quy tắc làm tròn cho currency.

        Args:
            currency: Mã tiền tệ cần xóa quy tắc.
        """
        currency = currency.upper()
        self._rules.pop(currency, None)

    def list_rules(self) -> dict[str, RoundingRule]:
        """
        Lấy bản sao của tất cả quy tắc làm tròn.

        Returns:
            Bản đồ currency_code → RoundingRule.
        """
        return dict(self._rules)
