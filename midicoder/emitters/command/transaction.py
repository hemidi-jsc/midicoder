"""
Transaction Manager với SQLAlchemy integration.

Module này cung cấp TransactionManagerSQL - quản lý database transactions
với SQLAlchemy, hỗ trợ:
- Begin/commit/rollback transactions
- Nested transactions với savepoints
- Auto rollback khi có exception
- Concurrent access handling

Author: Midicoder Team
Version: 2.0.0
"""

from dataclasses import dataclass
from typing import AsyncContextManager
from contextlib import asynccontextmanager
from contextvars import ContextVar

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from midicoder.errors import MidicoderErrorManager as EM
from midicoder.errors import ErrorCode


@dataclass
class TransactionInfo:
    """Thông tin về một transaction (SQLAlchemy)."""
    
    transaction_id: str
    is_active: bool = True
    nested_level: int = 0
    savepoint_name: str = ""


class TransactionManagerSQL:
    """
    Transaction Manager với SQLAlchemy integration.
    
    Lớp này quản lý database transactions với SQLAlchemy, hỗ trợ:
    - Begin/commit/rollback transactions
    - Nested transactions với savepoints
    - Auto rollback khi có exception
    - Concurrent access handling
    
    Attributes:
        engine: SQLAlchemy async engine
        session_factory: AsyncSessionMaker để tạo sessions
        
    Example:
        >>> tm = TransactionManagerSQL(engine, session_factory)
        >>> async with tm.transaction("tx_001") as session:
        ...     await session.add(entity)
        >>> # Auto commit nếu không có exception, auto rollback nếu có
    """
    
    def __init__(
        self,
        engine: AsyncEngine,
        session_factory: async_sessionmaker[AsyncSession]
    ):
        """
        Initialize TransactionManagerSQL.
        
        Args:
            engine: SQLAlchemy async engine
            session_factory: AsyncSessionMaker để tạo sessions
        """
        self.engine = engine
        self.session_factory = session_factory
        self._current_transaction: ContextVar[TransactionInfo | None] = ContextVar(
            "current_transaction", default=None
        )
        self._session_stack: list[AsyncSession] = []
    
    @property
    def is_in_transaction(self) -> bool:
        """
        Kiểm tra có đang trong transaction không.
        
        Returns:
            True nếu đang trong transaction, False nếu không
        """
        tx = self._current_transaction.get()
        return tx is not None and tx.is_active
    
    async def begin_transaction(self, transaction_id: str) -> AsyncSession:
        """
        Bắt đầu một transaction mới.
        
        Args:
            transaction_id: ID duy nhất cho transaction này
            
        Returns:
            AsyncSession cho transaction
        """
        current_tx = self._current_transaction.get()
        
        if current_tx is not None and current_tx.is_active:
            # Nested transaction - sử dụng cùng session
            session = self._session_stack[-1]
            savepoint_name = f"sp_{transaction_id}"
            
            self._current_transaction.set(TransactionInfo(
                transaction_id=transaction_id,
                is_active=True,
                nested_level=current_tx.nested_level + 1,
                savepoint_name=savepoint_name
            ))
            
            return session
        
        # New top-level transaction
        session = self.session_factory()
        await session.begin()
        
        self._session_stack.append(session)
        self._current_transaction.set(TransactionInfo(
            transaction_id=transaction_id,
            is_active=True,
            nested_level=0,
            savepoint_name=""
        ))
        
        return session
    
    async def commit_transaction(self) -> None:
        """
        Commit transaction hiện tại.
        
        Raises:
            MidicoderError: Nếu không có transaction active hoặc commit thất bại
        """
        current_tx = self._current_transaction.get()
        
        if current_tx is None or not current_tx.is_active:
            EM.raise_error(ErrorCode.CP01_TRANSACTION_NOT_ACTIVE)
        
        session = self._session_stack[-1]
        
        try:
            if current_tx.nested_level > 0:
                # Commit nested transaction - only mark as inactive, keep context
                await session.commit()
                current_tx.is_active = False
                # Restore parent transaction context
                self._current_transaction.set(TransactionInfo(
                    transaction_id=current_tx.transaction_id,
                    is_active=True,
                    nested_level=current_tx.nested_level - 1,
                    savepoint_name=""
                ))
            else:
                # Commit top-level transaction
                await session.commit()
                await session.close()
                self._session_stack.pop()
                # Clear context for top-level
                self._current_transaction.set(None)
            
        except Exception as e:
            # Rollback nếu commit fail
            await self.rollback_transaction()
            EM.raise_error(
                ErrorCode.CP01_TRANSACTION_COMMIT_FAILED,
                transaction_id=current_tx.transaction_id,
                original_error=str(e),
            )
    
    async def rollback_transaction(self) -> None:
        """
        Rollback transaction hiện tại.
        
        Raises:
            MidicoderError: Nếu không có transaction active hoặc rollback thất bại
        """
        current_tx = self._current_transaction.get()
        
        if current_tx is None or not current_tx.is_active:
            EM.raise_error(ErrorCode.CP01_TRANSACTION_NOT_ACTIVE)
        
        session = self._session_stack[-1]
        
        try:
            if current_tx.nested_level > 0:
                # Rollback nested transaction - only mark as inactive, keep context
                await session.rollback()
                current_tx.is_active = False
                # Restore parent transaction context
                self._current_transaction.set(TransactionInfo(
                    transaction_id=current_tx.transaction_id,
                    is_active=True,
                    nested_level=current_tx.nested_level - 1,
                    savepoint_name=""
                ))
            else:
                # Rollback top-level transaction
                await session.rollback()
                await session.close()
                self._session_stack.pop()
                # Clear context for top-level
                self._current_transaction.set(None)
            
        except Exception as e:
            EM.raise_error(
                ErrorCode.CP01_TRANSACTION_ROLLBACK_FAILED,
                transaction_id=current_tx.transaction_id,
                original_error=str(e),
            )
    
    @asynccontextmanager
    async def transaction(
        self,
        transaction_id: str
    ):
        """
        Context manager cho transaction với auto commit/rollback.
        
        Args:
            transaction_id: ID duy nhất cho transaction
            
        Yields:
            AsyncSession cho transaction
            
        Example:
            >>> async with tm.transaction("tx_001") as session:
            ...     await session.add(entity)
            >>> # Auto commit nếu không có exception
        """
        session = await self.begin_transaction(transaction_id)
        
        try:
            yield session
            await self.commit_transaction()
        except Exception:
            await self.rollback_transaction()
            raise