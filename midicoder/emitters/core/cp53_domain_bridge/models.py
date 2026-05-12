# coding: utf-8
"""
Mô-đun models cho Domain Pack Runtime Bridge (CP53).

Định nghĩa các data classes để biểu diễn runtime bridge giữa
generic CPs và domain-specific semantics:

- DomainPackDescriptor: Metadata của domain pack (discover/register)
- BridgeBinding: Ánh xạ CP capability → DP handler
- RuntimeInvoker: Cấu hình dispatch để invoke DP capability

Obligations:
1. BridgeBinding PHẢI reference CP capability tồn tại (MDC-CP53-001)
2. RuntimeInvoker PHẢI có DP target được registered (MDC-CP53-002)

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from midicoder.errors import ErrorCode, MidicoderError, MidicoderErrorManager as EM


# ===========================================================================
# DomainPackDescriptor
# ===========================================================================


@dataclass
class DomainPackDescriptor:
    """
    Metadata của domain pack để discover và register vào runtime bridge.

    DomainPackDescriptor chứa thông tin cần thiết để runtime bridge
    có thể nhận biết và invoke domain pack: pack_id, internal_id,
    capabilities, dependencies.

    Attributes:
        pack_id: ID của domain pack (vd: DP01, DP02)
        internal_id: Internal ID từ taxonomy (vd: dp01-commerce)
        name: Tên hiển thị của domain pack
        capabilities: Danh sách capabilities mà DP cung cấp
        depends_on: Danh sách CP dependencies
        metadata: Metadata bổ sung (optional)

    Raises:
        MidicoderError: Nếu pack_id rỗng (MDC-CP53-003)
        MidicoderError: Nếu capabilities rỗng (MDC-CP53-005)
    """

    pack_id: str
    internal_id: str
    name: str
    capabilities: list[str]
    depends_on: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate sau khi khởi tạo — enforce invariants."""
        # Pack ID không được rỗng
        if not self.pack_id or not self.pack_id.strip():
            EM.raise_error(
                ErrorCode.CP53_DUPLICATE_DP_ID,
                pack_id=self.pack_id,
            )

        # Capabilities không được rỗng — DP phải có ít nhất một capability
        if not self.capabilities or len(self.capabilities) == 0:
            EM.raise_error(
                ErrorCode.CP53_INVOKER_CONFIG_EMPTY,
                pack_id=self.pack_id,
                detail="capabilities list không được rỗng",
            )

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize thành dictionary.

        Returns:
            Dictionary representation của DomainPackDescriptor
        """
        return {
            "pack_id": self.pack_id,
            "internal_id": self.internal_id,
            "name": self.name,
            "capabilities": self.capabilities,
            "depends_on": self.depends_on,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DomainPackDescriptor:
        """
        Tạo DomainPackDescriptor từ dictionary.

        Args:
            data: Dictionary chứa các fields của DomainPackDescriptor

        Returns:
            Instance của DomainPackDescriptor
        """
        return cls(
            pack_id=data["pack_id"],
            internal_id=data.get("internal_id", ""),
            name=data.get("name", ""),
            capabilities=data.get("capabilities", []),
            depends_on=data.get("depends_on", []),
            metadata=data.get("metadata", {}),
        )


# ===========================================================================
# BridgeBinding
# ===========================================================================


@dataclass
class BridgeBinding:
    """
    Ánh xạ giữa CP capability và DP-specific handler.

    BridgeBinding cấu hình binding từ generic CP capability invocation
    đến DP-specific implementation. Đây là cầu nối giữa generic CP
    và domain-specific DP.

    Attributes:
        binding_id: ID duy nhất của binding
        cp_capability: CP capability cần bind (vd: create_record)
        dp_pack_id: ID của domain pack target (vd: DP01)
        dp_handler: Tên handler method trong DP
        priority: Ưu tiên resolve (mặc định: 0, cao hơn = ưu tiên hơn)
        metadata: Metadata bổ sung (optional)

    Raises:
        MidicoderError: Nếu cp_capability rỗng (MDC-CP53-001) — Obligation 1
        MidicoderError: Nếu binding_id rỗng (MDC-CP53-004)
        MidicoderError: Nếu dp_pack_id rỗng (MDC-CP53-002)
    """

    binding_id: str
    cp_capability: str
    dp_pack_id: str
    dp_handler: str
    priority: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate sau khi khởi tạo — enforce obligations."""
        # Obligation 1: cp_capability không được rỗng
        if not self.cp_capability or not self.cp_capability.strip():
            EM.raise_error(
                ErrorCode.CP53_BRIDGE_CAPABILITY_INVALID,
                binding_id=self.binding_id,
                cp_capability=self.cp_capability,
            )

        # Binding ID không được rỗng
        if not self.binding_id or not self.binding_id.strip():
            EM.raise_error(
                ErrorCode.CP53_INVALID_BINDING_ID,
                cp_capability=self.cp_capability,
            )

        # DP pack ID không được rỗng
        if not self.dp_pack_id or not self.dp_pack_id.strip():
            EM.raise_error(
                ErrorCode.CP53_DP_NOT_REGISTERED,
                binding_id=self.binding_id,
                dp_pack_id=self.dp_pack_id,
            )

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize thành dictionary.

        Returns:
            Dictionary representation của BridgeBinding
        """
        return {
            "binding_id": self.binding_id,
            "cp_capability": self.cp_capability,
            "dp_pack_id": self.dp_pack_id,
            "dp_handler": self.dp_handler,
            "priority": self.priority,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BridgeBinding:
        """
        Tạo BridgeBinding từ dictionary.

        Args:
            data: Dictionary chứa các fields của BridgeBinding

        Returns:
            Instance của BridgeBinding
        """
        return cls(
            binding_id=data["binding_id"],
            cp_capability=data.get("cp_capability", ""),
            dp_pack_id=data.get("dp_pack_id", ""),
            dp_handler=data.get("dp_handler", ""),
            priority=data.get("priority", 0),
            metadata=data.get("metadata", {}),
        )


# ===========================================================================
# RuntimeInvoker
# ===========================================================================


@dataclass
class RuntimeInvoker:
    """
    Cấu hình dispatch/routing để invoke DP capability tại runtime.

    RuntimeInvoker xử lý việc dispatch từ CP call đến DP handler
    tại runtime. Mỗi invoker binding một capability cụ thể với
    DP target và handler method.

    Attributes:
        capability: CP capability cần invoke (vd: create_record)
        dp_pack_id: ID của domain pack target (vd: DP01)
        handler_method: Tên method trong DP handler
        timeout_ms: Timeout cho invocation (mặc định: 30000ms)
        retry_count: Số lần retry nếu fail (mặc định: 0)
        metadata: Metadata bổ sung (optional)

    Raises:
        MidicoderError: Nếu capability rỗng (MDC-CP53-005)
        MidicoderError: Nếu dp_pack_id rỗng (MDC-CP53-002) — Obligation 2
        MidicoderError: Nếu handler_method rỗng (MDC-CP53-005)
    """

    capability: str
    dp_pack_id: str
    handler_method: str
    timeout_ms: int = 30000
    retry_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate sau khi khởi tạo — enforce obligations."""
        # Capability không được rỗng
        if not self.capability or not self.capability.strip():
            EM.raise_error(
                ErrorCode.CP53_INVOKER_CONFIG_EMPTY,
                detail="capability không được rỗng",
            )

        # Obligation 2: dp_pack_id không được rỗng — target phải registered
        if not self.dp_pack_id or not self.dp_pack_id.strip():
            EM.raise_error(
                ErrorCode.CP53_DP_NOT_REGISTERED,
                capability=self.capability,
                dp_pack_id=self.dp_pack_id,
            )

        # Handler method không được rỗng
        if not self.handler_method or not self.handler_method.strip():
            EM.raise_error(
                ErrorCode.CP53_INVOKER_CONFIG_EMPTY,
                detail="handler_method không được rỗng",
                capability=self.capability,
            )

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize thành dictionary.

        Returns:
            Dictionary representation của RuntimeInvoker
        """
        return {
            "capability": self.capability,
            "dp_pack_id": self.dp_pack_id,
            "handler_method": self.handler_method,
            "timeout_ms": self.timeout_ms,
            "retry_count": self.retry_count,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RuntimeInvoker:
        """
        Tạo RuntimeInvoker từ dictionary.

        Args:
            data: Dictionary chứa các fields của RuntimeInvoker

        Returns:
            Instance của RuntimeInvoker
        """
        return cls(
            capability=data["capability"],
            dp_pack_id=data.get("dp_pack_id", ""),
            handler_method=data.get("handler_method", ""),
            timeout_ms=data.get("timeout_ms", 30000),
            retry_count=data.get("retry_count", 0),
            metadata=data.get("metadata", {}),
        )


__all__ = [
    "DomainPackDescriptor",
    "BridgeBinding",
    "RuntimeInvoker",
]
