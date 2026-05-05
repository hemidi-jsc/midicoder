"""
RuntimeGuardEmitter: Sinh runtime guard code cho invariants.

Emitter này generate guard code cho FastAPI và NestJS stacks
để enforce invariants tại runtime.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from typing import Any

from midicoder.contracts.invariants.models import RuntimeGuardSpec


# ============================================================================
# FastAPI Guard Templates
# ============================================================================

FASTAPI_GUARD_TEMPLATE = '''\
"""
Runtime guard: {guard_class}
Invariant: {invariant_id}
Auto-generated bởi Midicoder - Không sửa tay.
"""

from fastapi import HTTPException, status
from typing import Any


class {guard_class}:
    """
    {guard_description}
    
    Violation Code: {error_code}
    """
    
    @staticmethod
    def check(**kwargs: Any) -> bool:
        """
        Execute guard check tại runtime.
        
        Args:
            **kwargs: Context data cho guard check
            
        Returns:
            True nếu check pass
            
        Raises:
            HTTPException: Nếu guard fail
        """
        # Guard logic sẽ được implement bởi domain-specific code
        pass
'''


# ============================================================================
# RuntimeGuardEmitter Class
# ============================================================================

class RuntimeGuardEmitter:
    """
    Emitter sinh runtime guard code cho invariants.
    
    Hỗ trợ:
    - FastAPI/Python guards
    - NestJS/TypeScript guards (stub)
    
    Usage:
        emitter = RuntimeGuardEmitter()
        guards = emitter.get_guards_for_invariants(invariants)
        code = emitter.emit_fastapi_guards(guards)
    """
    
    def get_guards_for_invariants(
        self,
        invariants: list[Any],
    ) -> list[RuntimeGuardSpec]:
        """
        Lấy runtime guard specs từ danh sách invariants.
        
        Args:
            invariants: Danh sách InvariantDefinition
            
        Returns:
            Danh sách RuntimeGuardSpec cho invariants có runtime enforcement
        """
        guards: list[RuntimeGuardSpec] = []
        
        for inv in invariants:
            if inv.is_runtime and inv.runtime_guard:
                guards.append(RuntimeGuardSpec(
                    invariant_id=inv.id,
                    guard_class=inv.runtime_guard,
                    target_component="handler",
                    error_code=inv.violation_code or "",
                    guard_params={
                        "description": inv.description,
                        "category": inv.category.value if hasattr(inv.category, "value") else str(inv.category),
                    },
                    stack="fastapi",
                ))
        
        return guards
    
    def emit_fastapi_guards(
        self,
        guards: list[RuntimeGuardSpec],
    ) -> dict[str, str]:
        """
        Sinh FastAPI guard code từ guard specs.
        
        Args:
            guards: Danh sách RuntimeGuardSpec
            
        Returns:
            Dictionary với key=guard_class, value=source code
        """
        result: dict[str, str] = {}
        
        for guard in guards:
            code = FASTAPI_GUARD_TEMPLATE.format(
                guard_class=guard.guard_class,
                invariant_id=guard.invariant_id,
                error_code=guard.error_code,
                guard_description=guard.guard_params.get("description", ""),
            )
            result[guard.guard_class] = code
        
        return result
    
    def emit_nestjs_guards(
        self,
        guards: list[RuntimeGuardSpec],
    ) -> dict[str, str]:
        """
        Sinh NestJS guard code từ guard specs (stub cho Phase 2).
        
        Args:
            guards: Danh sách RuntimeGuardSpec
            
        Returns:
            Dictionary với key=guard_class, value=source code
        """
        # NestJS support sẽ được implement trong Phase 2
        return {}