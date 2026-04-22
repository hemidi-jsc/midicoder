"""
Test suite cho CP06: Gateway & Service Mesh Macro Capabilities.

Test coverage cho:
- proxy_with_auth: Proxy request với auth + tenant scope
- resilient_service_call: Full resilience pattern (circuit breaker + retry + rate limit)
- aggregate_dashboard: Parallel aggregation + cache
- aggregate_order_details: Sequential aggregation
- cache_with_invalidation: Cache + event-driven invalidation
- multi_tenant_aggregation: Tenant-isolated aggregation
- rate_limited_proxy: Rate limit + proxy
- cached_fallback: Cache với fallback
- tenant_rate_limit: Per-tenant rate limiting
- circuit_breaker_proxy: Circuit breaker + proxy

Tổng cộng: 10 macro capabilities mới cho CP06

Mục tiêu coverage: >80%
"""

from unittest import TestCase

from midicoder.contracts.graph import MacroCapability
from midicoder.contracts.macro_capabilities import GatewayMacroCapabilities


# ============================================================================
# Gateway Macro Tests
# ============================================================================


class TestProxyWithAuthMacro(TestCase):
    """Test proxy_with_auth macro capability."""

    def test_proxy_with_auth_exists(self):
        """Test proxy_with_auth macro tồn tại."""
        macros = GatewayMacroCapabilities()
        self.assertIsNotNone(macros.PROXY_WITH_AUTH)
        self.assertEqual(macros.PROXY_WITH_AUTH.id, "proxy_with_auth")

    def test_proxy_with_auth_expands_to(self):
        """Test proxy_with_auth expand về đúng core capabilities."""
        macros = GatewayMacroCapabilities()
        expands = macros.PROXY_WITH_AUTH.expands_to
        
        # Check required core capabilities
        self.assertIn("authorize_permission", expands)
        self.assertIn("enforce_tenant_scope", expands)
        self.assertIn("proxy_request", expands)

    def test_proxy_with_auth_params_schema(self):
        """Test proxy_with_auth params có service_id và permission fields."""
        macros = GatewayMacroCapabilities()
        schema = macros.PROXY_WITH_AUTH.params_schema
        
        self.assertIn("service_id", schema)
        self.assertIn("permission", schema)
        self.assertTrue(schema["service_id"]["required"])
        self.assertTrue(schema["permission"]["required"])


class TestResilientServiceCallMacro(TestCase):
    """Test resilient_service_call macro capability."""

    def test_resilient_service_call_exists(self):
        """Test resilient_service_call macro tồn tại."""
        macros = GatewayMacroCapabilities()
        self.assertIsNotNone(macros.RESILIENT_SERVICE_CALL)
        self.assertEqual(macros.RESILIENT_SERVICE_CALL.id, "resilient_service_call")

    def test_resilient_service_call_expands_to(self):
        """Test resilient_service_call expand về resilience caps."""
        macros = GatewayMacroCapabilities()
        expands = macros.RESILIENT_SERVICE_CALL.expands_to
        
        # Check resilience capabilities
        self.assertIn("check_circuit_breaker", expands)
        self.assertIn("execute_with_retry", expands)
        self.assertIn("apply_rate_limit", expands)
        self.assertIn("proxy_request", expands)
        self.assertIn("emit_metric", expands)


class TestAggregateDashboardMacro(TestCase):
    """Test aggregate_dashboard macro capability."""

    def test_aggregate_dashboard_exists(self):
        """Test aggregate_dashboard macro tồn tại."""
        macros = GatewayMacroCapabilities()
        self.assertIsNotNone(macros.AGGREGATE_DASHBOARD)
        self.assertEqual(macros.AGGREGATE_DASHBOARD.id, "aggregate_dashboard")

    def test_aggregate_dashboard_expands_to(self):
        """Test aggregate_dashboard expand về parallel aggregation + cache."""
        macros = GatewayMacroCapabilities()
        expands = macros.AGGREGATE_DASHBOARD.expands_to
        
        self.assertIn("authorize_permission", expands)
        self.assertIn("aggregate_data_parallel", expands)
        self.assertIn("cache_response", expands)

    def test_aggregate_dashboard_description(self):
        """Test aggregate_dashboard description đề cập dashboard."""
        macros = GatewayMacroCapabilities()
        self.assertIn("dashboard", macros.AGGREGATE_DASHBOARD.description.lower())


class TestAggregateOrderDetailsMacro(TestCase):
    """Test aggregate_order_details macro capability."""

    def test_aggregate_order_details_exists(self):
        """Test aggregate_order_details macro tồn tại."""
        macros = GatewayMacroCapabilities()
        self.assertIsNotNone(macros.AGGREGATE_ORDER_DETAILS)
        self.assertEqual(macros.AGGREGATE_ORDER_DETAILS.id, "aggregate_order_details")

    def test_aggregate_order_details_expands_to(self):
        """Test aggregate_order_details expand về sequential aggregation."""
        macros = GatewayMacroCapabilities()
        expands = macros.AGGREGATE_ORDER_DETAILS.expands_to
        
        self.assertIn("authorize_permission", expands)
        self.assertIn("aggregate_data_sequential", expands)

    def test_aggregate_order_details_description(self):
        """Test aggregate_order_details description đề cập sequential."""
        macros = GatewayMacroCapabilities()
        self.assertIn("sequential", macros.AGGREGATE_ORDER_DETAILS.description.lower())


class TestCacheWithInvalidationMacro(TestCase):
    """Test cache_with_invalidation macro capability."""

    def test_cache_with_invalidation_exists(self):
        """Test cache_with_invalidation macro tồn tại."""
        macros = GatewayMacroCapabilities()
        self.assertIsNotNone(macros.CACHE_WITH_INVALIDATION)
        self.assertEqual(macros.CACHE_WITH_INVALIDATION.id, "cache_with_invalidation")

    def test_cache_with_invalidation_expands_to(self):
        """Test cache_with_invalidation expand về cache + event subscription."""
        macros = GatewayMacroCapabilities()
        expands = macros.CACHE_WITH_INVALIDATION.expands_to
        
        self.assertIn("cache_response", expands)
        self.assertIn("publish_event", expands)


class TestMultiTenantAggregationMacro(TestCase):
    """Test multi_tenant_aggregation macro capability."""

    def test_multi_tenant_aggregation_exists(self):
        """Test multi_tenant_aggregation macro tồn tại."""
        macros = GatewayMacroCapabilities()
        self.assertIsNotNone(macros.MULTI_TENANT_AGGREGATION)
        self.assertEqual(macros.MULTI_TENANT_AGGREGATION.id, "multi_tenant_aggregation")

    def test_multi_tenant_aggregation_expands_to(self):
        """Test multi_tenant_aggregation expand về tenant scope."""
        macros = GatewayMacroCapabilities()
        expands = macros.MULTI_TENANT_AGGREGATION.expands_to
        
        self.assertIn("enforce_tenant_scope", expands)
        self.assertIn("aggregate_data_parallel", expands)

    def test_multi_tenant_aggregation_params_schema(self):
        """Test multi_tenant_aggregation params có tenant_id field."""
        macros = GatewayMacroCapabilities()
        schema = macros.MULTI_TENANT_AGGREGATION.params_schema
        
        self.assertIn("tenant_id", schema)
        self.assertTrue(schema["tenant_id"]["required"])


class TestRateLimitedProxyMacro(TestCase):
    """Test rate_limited_proxy macro capability."""

    def test_rate_limited_proxy_exists(self):
        """Test rate_limited_proxy macro tồn tại."""
        macros = GatewayMacroCapabilities()
        self.assertIsNotNone(macros.RATE_LIMITED_PROXY)
        self.assertEqual(macros.RATE_LIMITED_PROXY.id, "rate_limited_proxy")

    def test_rate_limited_proxy_expands_to(self):
        """Test rate_limited_proxy expand về rate limit + proxy."""
        macros = GatewayMacroCapabilities()
        expands = macros.RATE_LIMITED_PROXY.expands_to
        
        self.assertIn("apply_rate_limit", expands)
        self.assertIn("proxy_request", expands)


class TestCachedFallbackMacro(TestCase):
    """Test cached_fallback macro capability."""

    def test_cached_fallback_exists(self):
        """Test cached_fallback macro tồn tại."""
        macros = GatewayMacroCapabilities()
        self.assertIsNotNone(macros.CACHED_FALLBACK)
        self.assertEqual(macros.CACHED_FALLBACK.id, "cached_fallback")

    def test_cached_fallback_expands_to(self):
        """Test cached_fallback expand về cache + proxy."""
        macros = GatewayMacroCapabilities()
        expands = macros.CACHED_FALLBACK.expands_to
        
        self.assertIn("cache_response", expands)
        self.assertIn("proxy_request", expands)

    def test_cached_fallback_description(self):
        """Test cached_fallback description đề cập fallback."""
        macros = GatewayMacroCapabilities()
        self.assertIn("fallback", macros.CACHED_FALLBACK.description.lower())


class TestTenantRateLimitMacro(TestCase):
    """Test tenant_rate_limit macro capability."""

    def test_tenant_rate_limit_exists(self):
        """Test tenant_rate_limit macro tồn tại."""
        macros = GatewayMacroCapabilities()
        self.assertIsNotNone(macros.TENANT_RATE_LIMIT)
        self.assertEqual(macros.TENANT_RATE_LIMIT.id, "tenant_rate_limit")

    def test_tenant_rate_limit_expands_to(self):
        """Test tenant_rate_limit expand về tenant + rate limit."""
        macros = GatewayMacroCapabilities()
        expands = macros.TENANT_RATE_LIMIT.expands_to
        
        self.assertIn("enforce_tenant_scope", expands)
        self.assertIn("apply_rate_limit", expands)


class TestCircuitBreakerProxyMacro(TestCase):
    """Test circuit_breaker_proxy macro capability."""

    def test_circuit_breaker_proxy_exists(self):
        """Test circuit_breaker_proxy macro tồn tại."""
        macros = GatewayMacroCapabilities()
        self.assertIsNotNone(macros.CIRCUIT_BREAKER_PROXY)
        self.assertEqual(macros.CIRCUIT_BREAKER_PROXY.id, "circuit_breaker_proxy")

    def test_circuit_breaker_proxy_expands_to(self):
        """Test circuit_breaker_proxy expand về circuit breaker + proxy."""
        macros = GatewayMacroCapabilities()
        expands = macros.CIRCUIT_BREAKER_PROXY.expands_to
        
        self.assertIn("check_circuit_breaker", expands)
        self.assertIn("proxy_request", expands)

    def test_circuit_breaker_proxy_description(self):
        """Test circuit_breaker_proxy description đề cập circuit breaker."""
        macros = GatewayMacroCapabilities()
        self.assertIn("circuit", macros.CIRCUIT_BREAKER_PROXY.description.lower())