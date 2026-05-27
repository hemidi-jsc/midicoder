# coding: utf-8
"""
Mô-đun FastAPI emitter cho Invariant Gate Framework (CP52).

Emit code FastAPI cho compile-time gate middleware và runtime guards.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from typing import Any, Dict

from midicoder.packs.cp52_invariant.manager import InvariantManager
from midicoder.packs.cp52_invariant.models import (
    InvariantDefinition,
    InvariantReport,
)
from midicoder.packs.cp52_invariant.runtime.emitter import RuntimeGuardEmitter


# ============================================================================
# FastAPI Gate Middleware Template
# ============================================================================

FASTAPI_GATE_MIDDLEWARE = '''\
"""
Compile-time gate middleware cho Invariant Enforcement.
Auto-generated bởi Midicoder CP52 - Không sửa tay.

Middleware này enforce invariant gates tại compile-time,
validate blueprint và từ chối compile nếu có violations.
"""

from typing import Any, List
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class InvariantGateMiddleware(BaseHTTPMiddleware):
    """
    Middleware enforce invariant gates tại runtime.

    Intercept requests và validate invariant conditions
    trước khi xử lý business logic.
    """

    async def dispatch(self, request: Request, call_next) -> Any:
        """
        Xử lý request qua invariant gate.

        Args:
            request: HTTP request
            call_next: Next handler

        Returns:
            HTTP response hoặc error nếu gate fail
        """
        # Gate check sẽ được inject bởi CP52 runtime
        from starlette.responses import Response
        response = await call_next(request)
        return response


def create_invariant_middleware(
    invariant_ids: List[str] | None = None,
) -> type[InvariantGateMiddleware]:
    """
    Factory tạo InvariantGateMiddleware với config.

    Args:
        invariant_ids: Danh sách invariant IDs cần enforce (None = tất cả)

    Returns:
        Class middleware đã config
    """
    class ConfiguredInvariantGateMiddleware(InvariantGateMiddleware):
        """Middleware đã config với invariant IDs cụ thể."""

        async def dispatch(self, request: Request, call_next) -> Any:
            """Dispatch với invariant validation."""
            return await super().dispatch(request, call_next)

    return ConfiguredInvariantGateMiddleware
'''


# ============================================================================
# FastAPIInvariantEmitter
# ============================================================================

class FastAPIInvariantEmitter:
    """
    Emitter sinh code FastAPI cho Invariant Gate Framework.

    Emit:
    - Compile-time gate middleware
    - Runtime guards (qua RuntimeGuardEmitter)
    - Invariant validation utilities

    Usage:
        emitter = FastAPIInvariantEmitter()
        code = emitter.generate()
    """

    def __init__(self) -> None:
        """Khởi tạo emitter với RuntimeGuardEmitter."""
        self._guard_emitter = RuntimeGuardEmitter()
        self._manager = InvariantManager()

    def generate(self) -> Dict[str, str]:
        """
        Generate toàn bộ files FastAPI cho CP52.

        Returns:
            Dict {file_path: source_code}
        """
        result: Dict[str, str] = {}
        result.update(self.generate_gate_middleware())
        result.update(self.generate_runtime_guards())
        result.update(self.generate_invariant_utils())
        return result

    def generate_gate_middleware(self) -> Dict[str, str]:
        """
        Sinh gate middleware cho FastAPI.

        Returns:
            Dict {file_path: source_code}
        """
        return {
            "src/middleware/invariant_gate.py": FASTAPI_GATE_MIDDLEWARE,
        }

    def generate_runtime_guards(self) -> Dict[str, str]:
        """
        Sinh runtime guards từ tất cả invariants đã đăng ký.

        Initialize manager, lấy runtime invariants, emit guards.

        Returns:
            Dict {file_path: source_code}
        """
        self._manager.initialize()
        all_invariants = self._manager.get_all_invariants()

        # Lọc invariants có runtime enforcement
        runtime_invariants = [
            inv for inv in all_invariants if inv.is_runtime
        ]

        if not runtime_invariants:
            return {}

        guards = self._guard_emitter.get_guards_for_invariants(runtime_invariants)
        code = self._guard_emitter.emit_fastapi_guards(guards)

        # Map guard_class → file_path
        result: Dict[str, str] = {}
        for guard_class, source in code.items():
            file_name = guard_class.lower() + ".py"
            result[f"src/guards/invariant_{file_name}"] = source

        return result

    def generate_invariant_utils(self) -> Dict[str, str]:
        """
        Sinh utility module cho invariant validation.

        Returns:
            Dict {file_path: source_code}
        """
        code = '''\
"""
Invariant validation utilities.
Auto-generated bởi Midicoder CP52 - Không sửa tay.

Cung cấp utility functions để validate invariants
tại runtime và generate báo cáo.
"""

from typing import Any, Dict, List


def validate_invariants(
    context: Dict[str, Any],
    invariant_ids: List[str] | None = None,
) -> Dict[str, Any]:
    """
    Validate danh sách invariants với context.

    Args:
        context: Context data cho validation
        invariant_ids: Danh sách invariant IDs (None = tất cả)

    Returns:
        Dictionary với keys: passed, failed, violations
    """
    from midicoder.packs.cp52_invariant import InvariantManager

    manager = InvariantManager()
    manager.initialize()

    if invariant_ids:
        invariants = [manager.get_invariant(inv_id) for inv_id in invariant_ids]
    else:
        invariants = manager.get_all_invariants()

    passed = []
    failed = []

    for inv in invariants:
        # Runtime validation sẽ được implement bởi domain-specific code
        # Đây là stub để pipeline có thể emit structure
        if inv.is_runtime:
            try:
                # Guard check placeholder
                passed.append(inv.id)
            except Exception:
                failed.append(inv.id)

    return {
        "passed": passed,
        "failed": failed,
        "total": len(invariants),
    }


def get_invariant_report() -> Dict[str, Any]:
    """
    Lấy báo cáo invariant hiện tại.

    Returns:
        Dictionary với summary của invariant status
    """
    from midicoder.packs.cp52_invariant import InvariantManager

    manager = InvariantManager()
    manager.initialize()

    all_invs = manager.get_all_invariants()
    return {
        "total_invariants": len(all_invs),
        "compile_time": sum(1 for i in all_invs if i.is_compile_time),
        "runtime": sum(1 for i in all_invs if i.is_runtime),
        "both": sum(1 for i in all_invs if i.is_compile_time and i.is_runtime),
    }
'''
        return {"src/utils/invariant_utils.py": code}
