"""
Query Effects Module.

Module này cung cấp QueryEffects class để execute query effects:
- WRITE_AUDIT_LOG: Write audit trail (RX11: Immutable Audit Evidence)
- RECORD_METRIC: Record metrics (CP15: Observability)

Theo clarification Q1: Query cần subset effects (WRITE_AUDIT_LOG, RECORD_METRIC).

Usage:
    from midicoder.packs.cp_base_domain_model import QueryEffects

    effects = QueryEffects(query)
    await effects.execute_all(context)

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from typing import Any

from .models import Query, QueryEffectType


class QueryEffects:
    """
    Query Effects - Execute query effects after query execution.
    
    Theo clarification Q1:
    - WRITE_AUDIT_LOG: Audit trail (RX11: Immutable Audit Evidence)
    - RECORD_METRIC: Metrics (CP15: Observability)
    
    Usage:
        effects = QueryEffects(query)
        await effects.execute_all(context)
    """

    def __init__(self, query: Query) -> None:
        """
        Khởi tạo QueryEffects.
        
        Args:
            query: Query definition
        """
        self._query = query

    async def execute_all(self, context: dict[str, Any]) -> None:
        """
        Execute tất cả effects của query.
        
        Args:
            context: Execution context với query result, user_id, tenant_id
        """
        for effect in self._query.effects:
            if effect.effect_type == QueryEffectType.WRITE_AUDIT_LOG:
                await self._write_audit_log(effect, context)
            elif effect.effect_type == QueryEffectType.RECORD_METRIC:
                await self._record_metric(effect, context)

    async def _write_audit_log(
        self,
        effect: Any,
        context: dict[str, Any],
    ) -> None:
        """
        Write audit log entry.
        
        Theo RX11: Immutable Audit Evidence.
        
        Args:
            effect: QueryEffect với effect_type=WRITE_AUDIT_LOG
            context: Execution context
        """
        # Placeholder: Audit log sẽ được write vào immutable storage
        # Context chứa: query_id, user_id, tenant_id, result_count, timestamp
        pass

    async def _record_metric(
        self,
        effect: Any,
        context: dict[str, Any],
    ) -> None:
        """
        Record metric cho observability.

        Theo CP15: Observability Stack Generator.
        Wire vào MetricRegistry để ghi metric thực tế.

        Args:
            effect: QueryEffect với effect_type=RECORD_METRIC
            context: Execution context với metric_name, metric_value
        """
        from midicoder.packs.cp15_observability.metrics import MetricRegistry

        metric_name = getattr(effect, "metric_name", "query.duration")
        metric_value = float(getattr(effect, "metric_value", 1) or 1)
        labels = {
            "query_id": context.get("query_id", ""),
            "user_id": context.get("user_id", ""),
            "tenant_id": context.get("tenant_id", ""),
        }
        registry = MetricRegistry()
        registry.record(metric_name, metric_value, labels)