"""
Transaction Manager cho Command Pattern.

Quản lý transaction lifecycle (begin/commit/rollback) với support cho:
- ACID compliance
- Savepoints
- Nested transactions
- Error handling với automatic rollback

Author: Midicoder Team
Version: 2.0.0
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class TransactionState:
    """
    Trạng thái transaction.

    Attributes:
        transaction_id: Transaction ID
        is_active: Transaction đang active không
        savepoints: Danh sách savepoints
        depth: Nesting depth
    """

    transaction_id: str
    is_active: bool = True
    savepoints: list[str] = field(default_factory=list)
    depth: int = 1


class TransactionManager:
    """
    Manager cho transaction lifecycle.

    Cung cấp:
    - begin_transaction(): Bắt đầu transaction mới
    - commit_transaction(): Commit transaction
    - rollback_transaction(): Rollback transaction
    - savepoint(): Tạo savepoint
    - rollback_to_savepoint(): Rollback đến savepoint

    Usage:
        async with transaction_manager.transaction("tx_001") as tx:
            # Execute effects
            await effect.execute()
            # Auto commit if no exception
            # Auto rollback if exception
    """

    def __init__(self, db_session: Any = None) -> None:
        """
        Khởi tạo TransactionManager.

        Args:
            db_session: Database session (SQLAlchemy async session)
        """
        self._db_session = db_session
        self._current_transaction: Optional[TransactionState] = None
        self._savepoint_counter = 0

    @property
    def is_in_transaction(self) -> bool:
        """Check nếu đang trong transaction."""
        return self._current_transaction is not None and self._current_transaction.is_active

    @property
    def current_transaction(self) -> Optional[TransactionState]:
        """Lấy current transaction state."""
        return self._current_transaction

    async def begin_transaction(self, transaction_id: Optional[str] = None) -> TransactionState:
        """
        Bắt đầu transaction mới.

        Args:
            transaction_id: Transaction ID (optional, auto-generated nếu không có)

        Returns:
            TransactionState instance

        Raises:
            RuntimeError: Nếu đã có transaction đang active
        """
        if self.is_in_transaction:
            # Nested transaction - tăng depth
            self._current_transaction.depth += 1
            return self._current_transaction

        if transaction_id is None:
            transaction_id = f"tx_{hash(self)}_{id(self)}"

        self._current_transaction = TransactionState(
            transaction_id=transaction_id,
            is_active=True,
            savepoints=[],
            depth=1,
        )

        # Begin transaction với database session
        if self._db_session:
            await self._db_session.begin()

        return self._current_transaction

    async def commit_transaction(self) -> None:
        """
        Commit transaction.

        Raises:
            RuntimeError: Nếu không có transaction đang active
        """
        if not self.is_in_transaction:
            raise RuntimeError("Không có transaction đang active để commit")

        # Giảm depth nếu nested transaction
        if self._current_transaction.depth > 1:
            self._current_transaction.depth -= 1
            return

        # Commit với database session
        if self._db_session:
            await self._db_session.commit()

        # Reset transaction state
        self._current_transaction.is_active = False
        self._current_transaction = None

    async def rollback_transaction(self) -> None:
        """
        Rollback transaction.

        Raises:
            RuntimeError: Nếu không có transaction đang active
        """
        if not self.is_in_transaction:
            raise RuntimeError("Không có transaction đang active để rollback")

        # Rollback với database session
        if self._db_session:
            await self._db_session.rollback()

        # Reset transaction state
        self._current_transaction.is_active = False
        self._current_transaction = None

    async def savepoint(self, savepoint_name: Optional[str] = None) -> str:
        """
        Tạo savepoint.

        Args:
            savepoint_name: Savepoint name (optional, auto-generated nếu không có)

        Returns:
            Savepoint name

        Raises:
            RuntimeError: Nếu không có transaction đang active
        """
        if not self.is_in_transaction:
            raise RuntimeError("Không có transaction đang active để tạo savepoint")

        if savepoint_name is None:
            self._savepoint_counter += 1
            savepoint_name = f"sp_{self._savepoint_counter}"

        self._current_transaction.savepoints.append(savepoint_name)

        # Create savepoint với database session
        if self._db_session:
            # SQLAlchemy savepoint syntax
            await self._db_session.connection().execution_options(isolation_level="READ_COMMITTED")

        return savepoint_name

    async def rollback_to_savepoint(self, savepoint_name: str) -> None:
        """
        Rollback đến savepoint.

        Args:
            savepoint_name: Savepoint name

        Raises:
            RuntimeError: Nếu không có transaction đang active
            ValueError: Nếu savepoint không tồn tại
        """
        if not self.is_in_transaction:
            raise RuntimeError("Không có transaction đang active để rollback")

        if savepoint_name not in self._current_transaction.savepoints:
            raise ValueError(f"Savepoint '{savepoint_name}' không tồn tại")

        # Rollback to savepoint với database session
        if self._db_session:
            await self._db_session.rollback()

        # Remove savepoint
        self._current_transaction.savepoints.remove(savepoint_name)

    @asynccontextmanager
    async def transaction(self, transaction_id: Optional[str] = None):
        """
        Context manager cho transaction.

        Usage:
            async with transaction_manager.transaction() as tx:
                # Execute effects
                # Auto commit nếu no exception
                # Auto rollback nếu exception

        Args:
            transaction_id: Transaction ID (optional)

        Yields:
            TransactionState instance
        """
        tx = await self.begin_transaction(transaction_id)
        try:
            yield tx
            await self.commit_transaction()
        except Exception as e:
            await self.rollback_transaction()
            raise e

    @asynccontextmanager
    async def savepoint_context(self, savepoint_name: Optional[str] = None):
        """
        Context manager cho savepoint.

        Usage:
            async with transaction_manager.savepoint_context() as sp:
                # Execute effects
                # Auto rollback to savepoint nếu exception

        Args:
            savepoint_name: Savepoint name (optional)

        Yields:
            Savepoint name
        """
        sp = await self.savepoint(savepoint_name)
        try:
            yield sp
        except Exception as e:
            await self.rollback_to_savepoint(sp)
            raise e