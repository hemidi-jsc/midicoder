"""
Mô-đun models cho CP33: Financial Engine.

Định nghĩa các dataclass cho:
- Currency: Thông tin tiền tệ ISO 4217
- FXRate: Tỷ giá hối đoái
- Account: Sổ kế toán
- LedgerEntry: Entry trong ledger (double-entry)
- FinancialTransaction: Giao dịch tài chính
- RoundingRule: Quy tắc làm tròn theo ISO 4217
- LedgerSnapshot: Snapshot để verify hash chain
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, ROUND_HALF_EVEN, ROUND_HALF_DOWN, ROUND_FLOOR, ROUND_CEILING
from enum import Enum
from typing import Any, Optional


from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# ===========================================================================
# Enum types
# ===========================================================================

class RoundingMode(str, Enum):
    """Các chế độ làm tròn theo chuẩn ISO 4217."""
    HALF_UP = "half_up"
    HALF_EVEN = "half_even"
    HALF_DOWN = "half_down"
    FLOOR = "floor"
    CEILING = "ceiling"


class EntryType(str, Enum):
    """Loại ledger entry (nợ hoặc có)."""
    DEBIT = "debit"
    CREDIT = "credit"


class TransactionType(str, Enum):
    """Loại giao dịch tài chính."""
    SINGLE_ENTRY = "single_entry"
    DOUBLE_ENTRY = "double_entry"


class TransactionStatus(str, Enum):
    """Trạng thái giao dịch."""
    PENDING = "pending"
    POSTED = "posted"
    REVERSED = "reversed"


class AccountType(str, Enum):
    """Loại sổ kế toán."""
    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    INCOME = "income"
    EXPENSE = "expense"


class FXSource(str, Enum):
    """Nguồn tỷ giá hối đoái."""
    MANUAL = "manual"
    API = "api"


# Mapping từ RoundingMode sang constant của Decimal
ROUNDING_MAP: dict[RoundingMode, Any] = {
    RoundingMode.HALF_UP: ROUND_HALF_UP,
    RoundingMode.HALF_EVEN: ROUND_HALF_EVEN,
    RoundingMode.HALF_DOWN: ROUND_HALF_DOWN,
    RoundingMode.FLOOR: ROUND_FLOOR,
    RoundingMode.CEILING: ROUND_CEILING,
}


# ===========================================================================
# Currency
# ===========================================================================

@dataclass
class Currency:
    """
    Đại diện cho 1 loại tiền tệ ISO 4217.

    Attributes:
        code: Mã tiền tệ 3 ký tự (vd: USD, EUR, VND).
        name: Tên đầy đủ của tiền tệ.
        symbol: Ký hiệu hiển thị (vd: $, €, ₫).
        decimal_places: Số chữ số thập phân chuẩn.
        rounding_mode: Chế độ làm tròn mặc định.
        is_active: Còn đang sử dụng hay không.
        metadata: Metadata bổ sung.
    """
    code: str
    name: str
    symbol: str
    decimal_places: int = 2
    rounding_mode: RoundingMode = RoundingMode.HALF_UP
    is_active: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate currency fields sau khi khởi tạo."""
        # Mã tiền tệ phải là 3 ký tự chữ hoa
        if not self.code or len(self.code) != 3 or not self.code.isalpha():
            raise EM.raise_error(
                ErrorCode.CP33_CURRENCY_INVALID,
                currency=self.code,
                reason="ISO 4217 code must be 3 uppercase letters"
            )
        self.code = self.code.upper()

        # Số chữ số thập phân hợp lệ: 0-6
        if not 0 <= self.decimal_places <= 6:
            raise EM.raise_error(
                ErrorCode.CP33_INVALID_DECIMAL_PRECISION,
                currency=self.code,
                decimal_places=self.decimal_places
            )

    def to_dict(self) -> dict[str, Any]:
        """Serialize thành dictionary."""
        return {
            "code": self.code,
            "name": self.name,
            "symbol": self.symbol,
            "decimal_places": self.decimal_places,
            "rounding_mode": self.rounding_mode.value,
            "is_active": self.is_active,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Currency:
        """Khởi tạo từ dictionary."""
        rounding = data.get("rounding_mode", RoundingMode.HALF_UP.value)
        if isinstance(rounding, str):
            rounding = RoundingMode(rounding)
        return cls(
            code=data["code"],
            name=data["name"],
            symbol=data["symbol"],
            decimal_places=data.get("decimal_places", 2),
            rounding_mode=rounding,
            is_active=data.get("is_active", True),
            metadata=data.get("metadata", {}),
        )

    def format_amount(self, amount: Decimal) -> str:
        """
        Định dạng số tiền theo quy tắc của currency.

        Args:
            amount: Số tiền cần định dạng.

        Returns:
            String đã định dạng với đúng số chữ số thập phân.
        """
        quantize_val = Decimal(10) ** -self.decimal_places
        rounded = amount.quantize(
            quantize_val,
            rounding=ROUNDING_MAP[self.rounding_mode]
        )
        return f"{self.symbol}{rounded}"


# ===========================================================================
# FXRate
# ===========================================================================

@dataclass
class FXRate:
    """
    Tỷ giá hối đoái giữa 2 tiền tệ.

    Attributes:
        from_currency: Tiền tệ nguồn.
        to_currency: Tiền tệ đích.
        rate: Tỷ giá (1 đơn vị from = rate đơn vị to).
        effective_from: Ngày bắt đầu có hiệu lực.
        effective_to: Ngày kết thúc hiệu lực (None = vẫn đang hiệu lực).
        source: Nguồn tỷ giá (manual hay api).
        metadata: Metadata bổ sung.
    """
    from_currency: str
    to_currency: str
    rate: Decimal
    effective_from: datetime
    effective_to: Optional[datetime] = None
    source: FXSource = FXSource.MANUAL
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate FXRate fields sau khi khởi tạo."""
        # Không được convert cùng 1 currency
        if self.from_currency == self.to_currency:
            raise EM.raise_error(
                ErrorCode.CP33_INVALID_CURRENCY_PAIR,
                from_currency=self.from_currency,
                to_currency=self.to_currency,
                reason="from_currency and to_currency must differ"
            )

        # Rate phải > 0
        try:
            rate_val = Decimal(str(self.rate))
        except (InvalidOperation, ValueError):
            raise EM.raise_error(
                ErrorCode.CP33_FX_RATE_NOT_FOUND,
                reason="Invalid rate value"
            )
        if rate_val <= 0:
            raise EM.raise_error(
                ErrorCode.CP33_FX_RATE_NOT_FOUND,
                reason="Rate must be positive"
            )
        self.rate = rate_val

        # effective_to >= effective_from
        if self.effective_to and self.effective_to < self.effective_from:
            raise EM.raise_error(
                ErrorCode.CP33_FX_RATE_NOT_FOUND,
                reason="effective_to must be >= effective_from"
            )

    @property
    def pair(self) -> str:
        """Trả về ký hiệu cặp tiền tệ (vd: EUR/USD)."""
        return f"{self.from_currency}/{self.to_currency}"

    @property
    def is_active(self) -> bool:
        """Kiểm tra xem rate còn hiệu lực không."""
        if self.effective_to:
            return datetime.now() <= self.effective_to
        return datetime.now() >= self.effective_from

    def to_dict(self) -> dict[str, Any]:
        """Serialize thành dictionary."""
        return {
            "from_currency": self.from_currency,
            "to_currency": self.to_currency,
            "rate": str(self.rate),
            "effective_from": self.effective_from.isoformat(),
            "effective_to": self.effective_to.isoformat() if self.effective_to else None,
            "source": self.source.value,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FXRate:
        """Khởi tạo từ dictionary."""
        source = data.get("source", FXSource.MANUAL.value)
        if isinstance(source, str):
            source = FXSource(source)
        return cls(
            from_currency=data["from_currency"],
            to_currency=data["to_currency"],
            rate=Decimal(data["rate"]),
            effective_from=datetime.fromisoformat(data["effective_from"]),
            effective_to=datetime.fromisoformat(data["effective_to"]) if data.get("effective_to") else None,
            source=source,
            metadata=data.get("metadata", {}),
        )


# ===========================================================================
# Account
# ===========================================================================

@dataclass
class Account:
    """
    Sổ kế toán (account trong chart of accounts).

    Attributes:
        code: Mã tài khoản (vd: 1000, 1010, 4000).
        name: Tên tài khoản.
        account_type: Loại tài khoản (asset, liability, ...).
        is_active: Còn đang sử dụng.
        parent_account: Mã tài khoản cha (None = root).
        currency: Tiền tệ mặc định của tài khoản.
        metadata: Metadata bổ sung.
    """
    code: str
    name: str
    account_type: AccountType
    is_active: bool = True
    parent_account: Optional[str] = None
    currency: str = "USD"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate account fields sau khi khởi tạo."""
        if not self.code:
            raise EM.raise_error(
                ErrorCode.CP33_ACCOUNT_NOT_FOUND,
                reason="Account code cannot be empty",
            )

        if not self.name:
            raise EM.raise_error(
                ErrorCode.CP33_ACCOUNT_NOT_FOUND,
                reason="Account name cannot be empty",
            )

    def to_dict(self) -> dict[str, Any]:
        """Serialize thành dictionary."""
        return {
            "code": self.code,
            "name": self.name,
            "account_type": self.account_type.value,
            "is_active": self.is_active,
            "parent_account": self.parent_account,
            "currency": self.currency,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Account:
        """Khởi tạo từ dictionary."""
        atype = data.get("account_type", AccountType.ASSET.value)
        if isinstance(atype, str):
            atype = AccountType(atype)
        return cls(
            code=data["code"],
            name=data["name"],
            account_type=atype,
            is_active=data.get("is_active", True),
            parent_account=data.get("parent_account"),
            currency=data.get("currency", "USD"),
            metadata=data.get("metadata", {}),
        )


# ===========================================================================
# LedgerEntry
# ===========================================================================

@dataclass
class LedgerEntry:
    """
    1 entry trong ledger (nợ hoặc có).

    Attributes:
        id: ID duy nhất của entry.
        transaction_id: ID của giao dịch cha.
        entry_type: Nợ (debit) hay có (credit).
        account_code: Mã tài khoản.
        amount: Số tiền (luôn >= 0).
        currency: Tiền tệ của entry.
        description: Mô tả.
        previous_hash: Hash của entry trước trong chain.
        created_at: Thời gian tạo.
        metadata: Metadata bổ sung.
    """
    id: str
    transaction_id: str
    entry_type: EntryType
    account_code: str
    amount: Decimal
    currency: str
    description: str = ""
    previous_hash: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate ledger entry fields sau khi khởi tạo."""
        if not self.id:
            raise EM.raise_error(
                ErrorCode.CP33_INVALID_ENTRY_TYPE,
                reason="Entry ID cannot be empty"
            )

        # Amount phải >= 0
        try:
            amount_val = Decimal(str(self.amount))
        except (InvalidOperation, ValueError):
            raise EM.raise_error(
                ErrorCode.CP33_INVALID_DECIMAL_PRECISION,
                reason="Invalid amount value"
            )
        if amount_val < 0:
            raise EM.raise_error(
                ErrorCode.CP33_INVALID_ENTRY_TYPE,
                reason="Amount cannot be negative"
            )
        self.amount = amount_val

    @property
    def hash(self) -> str:
        """
        Tính SHA-256 hash của entry này (cho hash chain).

        Returns:
            Hex string của hash SHA-256.
        """
        data = f"{self.id}:{self.transaction_id}:{self.entry_type.value}:{self.account_code}:{self.amount}:{self.currency}:{self.previous_hash}"
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        """Serialize thành dictionary."""
        return {
            "id": self.id,
            "transaction_id": self.transaction_id,
            "entry_type": self.entry_type.value,
            "account_code": self.account_code,
            "amount": str(self.amount),
            "currency": self.currency,
            "description": self.description,
            "previous_hash": self.previous_hash,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LedgerEntry:
        """Khởi tạo từ dictionary."""
        etype = data.get("entry_type", EntryType.DEBIT.value)
        if isinstance(etype, str):
            etype = EntryType(etype)
        return cls(
            id=data["id"],
            transaction_id=data["transaction_id"],
            entry_type=etype,
            account_code=data["account_code"],
            amount=Decimal(data["amount"]),
            currency=data["currency"],
            description=data.get("description", ""),
            previous_hash=data.get("previous_hash", ""),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            metadata=data.get("metadata", {}),
        )


# ===========================================================================
# FinancialTransaction
# ===========================================================================

@dataclass
class FinancialTransaction:
    """
    Giao dịch tài chính (chứa 1+ ledger entries).

    Attributes:
        id: ID duy nhất của giao dịch.
        transaction_type: Single hay double-entry.
        status: Trạng thái giao dịch.
        tenant_id: ID tenant (cho multi-tenant).
        entries: Danh sách entries trong giao dịch.
        total_debit: Tổng nợ.
        total_credit: Tổng có.
        description: Mô tả giao dịch.
        created_at: Thời gian tạo.
        metadata: Metadata bổ sung.
    """
    id: str
    transaction_type: TransactionType
    status: TransactionStatus = TransactionStatus.PENDING
    tenant_id: str = ""
    entries: list[LedgerEntry] = field(default_factory=list)
    total_debit: Decimal = Decimal("0")
    total_credit: Decimal = Decimal("0")
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate transaction sau khi khởi tạo."""
        if not self.id:
            raise EM.raise_error(
                ErrorCode.CP33_TRANSACTION_NOT_FOUND,
                reason="Transaction ID cannot be empty"
            )
        # Tính lại total từ entries
        self._recalculate_totals()

    def add_entry(self, entry: LedgerEntry) -> None:
        """
        Thêm entry vào giao dịch.

        Args:
            entry: LedgerEntry cần thêm.
        """
        entry.transaction_id = self.id
        self.entries.append(entry)
        self._recalculate_totals()

    def _recalculate_totals(self) -> None:
        """Tính lại tổng debit và credit từ entries."""
        total_d = Decimal("0")
        total_c = Decimal("0")
        for e in self.entries:
            if e.entry_type == EntryType.DEBIT:
                total_d += e.amount
            else:
                total_c += e.amount
        self.total_debit = total_d
        self.total_credit = total_c

    def validate_balance(self) -> bool:
        """
        Kiểm tra cân bằng (chỉ cho double-entry).

        Returns:
            True nếu cân bằng hoặc là single-entry.

        Raises:
            MidicoderError: Nếu double-entry không cân bằng.
        """
        if self.transaction_type == TransactionType.DOUBLE_ENTRY:
            if self.total_debit != self.total_credit:
                raise EM.raise_error(
                    ErrorCode.CP33_DOUBLE_ENTRY_IMBALANCE,
                    transaction_id=self.id,
                    total_debit=str(self.total_debit),
                    total_credit=str(self.total_credit)
                )
        return True

    def post(self) -> None:
        """Đăng ký giao dịch (chuyển sang trạng thái POSTED)."""
        self.validate_balance()
        self.status = TransactionStatus.POSTED

    def to_dict(self) -> dict[str, Any]:
        """Serialize thành dictionary."""
        return {
            "id": self.id,
            "transaction_type": self.transaction_type.value,
            "status": self.status.value,
            "tenant_id": self.tenant_id,
            "entries": [e.to_dict() for e in self.entries],
            "total_debit": str(self.total_debit),
            "total_credit": str(self.total_credit),
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FinancialTransaction:
        """Khởi tạo từ dictionary."""
        ttype = data.get("transaction_type", TransactionType.SINGLE_ENTRY.value)
        if isinstance(ttype, str):
            ttype = TransactionType(ttype)
        tstatus = data.get("status", TransactionStatus.PENDING.value)
        if isinstance(tstatus, str):
            tstatus = TransactionStatus(tstatus)
        raw_entries = data.get("entries", [])
        return cls(
            id=data["id"],
            transaction_type=ttype,
            status=tstatus,
            tenant_id=data.get("tenant_id", ""),
            entries=[LedgerEntry.from_dict(e) for e in raw_entries],
            total_debit=Decimal(data.get("total_debit", "0")),
            total_credit=Decimal(data.get("total_credit", "0")),
            description=data.get("description", ""),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            metadata=data.get("metadata", {}),
        )


# ===========================================================================
# RoundingRule
# ===========================================================================

@dataclass
class RoundingRule:
    """
    Quy tắc làm tròn cho 1 tiền tệ cụ thể.

    Attributes:
        currency_code: Mã tiền tệ ISO 4217.
        mode: Chế độ làm tròn.
        decimals: Số chữ số thập phân sau khi làm tròn.
    """
    currency_code: str
    mode: RoundingMode
    decimals: int = 2

    def __post_init__(self) -> None:
        """Validate rounding rule sau khi khởi tạo."""
        if not self.currency_code or len(self.currency_code) != 3:
            raise EM.raise_error(
                ErrorCode.CP33_ROUNDING_RULE_NOT_FOUND,
                currency=self.currency_code,
                reason="Invalid currency code for rounding rule"
            )
        if not 0 <= self.decimals <= 6:
            raise EM.raise_error(
                ErrorCode.CP33_INVALID_DECIMAL_PRECISION,
                currency=self.currency_code,
                decimals=self.decimals
            )

    def apply(self, amount: Decimal) -> Decimal:
        """
        Áp dụng quy tắc làm tròn cho số tiền.

        Args:
            amount: Số tiền cần làm tròn.

        Returns:
            Số tiền đã làm tròn.
        """
        try:
            val = Decimal(str(amount))
        except (InvalidOperation, ValueError):
            raise EM.raise_error(
                ErrorCode.CP33_INVALID_DECIMAL_PRECISION,
                reason="Invalid amount for rounding"
            )
        quantize_val = Decimal(10) ** -self.decimals
        return val.quantize(quantize_val, rounding=ROUNDING_MAP[self.mode])

    def to_dict(self) -> dict[str, Any]:
        """Serialize thành dictionary."""
        return {
            "currency_code": self.currency_code,
            "mode": self.mode.value,
            "decimals": self.decimals,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RoundingRule:
        """Khởi tạo từ dictionary."""
        mode = data.get("mode", RoundingMode.HALF_UP.value)
        if isinstance(mode, str):
            mode = RoundingMode(mode)
        return cls(
            currency_code=data["currency_code"],
            mode=mode,
            decimals=data.get("decimals", 2),
        )


# ===========================================================================
# LedgerSnapshot
# ===========================================================================

@dataclass
class LedgerSnapshot:
    """
    Snapshot của ledger tại 1 thời điểm (cho compliance audit).

    Attributes:
        id: ID duy nhất của snapshot.
        timestamp: Thời gian tạo snapshot.
        chain_hash: Hash cuối cùng của chain tại thời điểm này.
        entry_count: Số entries trong ledger tại thời điểm này.
        metadata: Metadata bổ sung.
    """
    id: str
    timestamp: datetime
    chain_hash: str
    entry_count: int
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate ledger snapshot sau khi khởi tạo."""
        if not self.id:
            raise EM.raise_error(
                ErrorCode.CP33_HASH_CHAIN_FAILED,
                reason="Snapshot ID cannot be empty"
            )
        if self.entry_count < 0:
            raise EM.raise_error(
                ErrorCode.CP33_HASH_CHAIN_FAILED,
                reason="Entry count cannot be negative"
            )

    def to_dict(self) -> dict[str, Any]:
        """Serialize thành dictionary."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "chain_hash": self.chain_hash,
            "entry_count": self.entry_count,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LedgerSnapshot:
        """Khởi tạo từ dictionary."""
        return cls(
            id=data["id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            chain_hash=data["chain_hash"],
            entry_count=data["entry_count"],
            metadata=data.get("metadata", {}),
        )
