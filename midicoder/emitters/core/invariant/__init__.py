"""
Invariant Enforcement System (P2-001)

Hệ thống enforce business invariants cho Midicoder, gồm 3 tầng:
- Business Invariants: Đảm bảo domain logic đúng (CRUD consistency)
- Compliance Invariants: Đảm bảo regulatory compliance (GDPR, HIPAA, SOX)
- Failure-Mode Invariants: Đảm bảo reliability (error handling, retry, circuit breaker)

Sử dụng:
    from midicoder.emitters.core.invariant import InvariantManager

    manager = InvariantManager()
    manager.initialize()  # Đăng ký built-in invariants
    report = manager.validate(graph)  # Chạy tất cả checks
    print(report.is_passing)  # True/False

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from midicoder.emitters.core.invariant.models import (
        InvariantCategory,
        EnforcementMode,
        InvariantSeverity,
        InvariantDefinition,
        InvariantResult,
        InvariantReport,
        CompileTimeCheckSpec,
        RuntimeGuardSpec,
    )
    from midicoder.emitters.core.invariant.registry import InvariantRegistry
    from midicoder.emitters.core.invariant.manager import InvariantManager


def __getattr__(name: str) -> object:
    """
    Lazy imports để tránh circular dependency.

    Khi import từ module này, các classes sẽ được load on-demand
    thay vì load tất cả tại lúc import.
    """
    if name in ("InvariantCategory", "EnforcementMode", "InvariantSeverity",
                "InvariantDefinition", "InvariantResult", "InvariantReport",
                "CompileTimeCheckSpec", "RuntimeGuardSpec"):
        from midicoder.emitters.core.invariant import models
        return getattr(models, name)
    elif name == "InvariantRegistry":
        from midicoder.emitters.core.invariant.registry import InvariantRegistry
        return InvariantRegistry
    elif name == "InvariantManager":
        from midicoder.emitters.core.invariant.manager import InvariantManager
        return InvariantManager
    else:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    # Models
    "InvariantCategory",
    "EnforcementMode",
    "InvariantSeverity",
    "InvariantDefinition",
    "InvariantResult",
    "InvariantReport",
    "CompileTimeCheckSpec",
    "RuntimeGuardSpec",
    # Registry
    "InvariantRegistry",
    # Manager
    "InvariantManager",
]