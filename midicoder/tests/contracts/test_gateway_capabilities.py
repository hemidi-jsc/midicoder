"""
Test suite cho CP06: Gateway & Service Mesh Core Capabilities.

Test coverage cho:
- Gateway Operations (4 caps): proxy_request, aggregate_data_sequential, aggregate_data_parallel, cache_response
- Resilience Operations (3 caps): check_circuit_breaker, execute_with_retry, apply_rate_limit
- Service Mesh Operations (3 caps): register_service, service_discovery, emit_metric

Tổng cộng: 10 core capabilities mới

Mục tiêu coverage: >80%
"""

from unittest import TestCase

from midicoder.contracts.graph import CoreCapability
from midicoder.contracts.core_capabilities import GatewayCoreCapabilities


# ============================================================================
# Gateway Operations Tests
# ============================================================================


class TestProxyRequestCapability(TestCase):
    """Test proxy_request core capability."""

    def test_proxy_request_exists(self):
        """Test proxy_request capability tồn tại."""
        caps = GatewayCoreCapabilities()
        self.assertIsNotNone(caps.PROXY_REQUEST)
        self.assertEqual(caps.PROXY_REQUEST.id, "proxy_request")

    def test_proxy_request_params_schema(self):
        """Test proxy_request params schema có required fields."""
        caps = GatewayCoreCapabilities()
        schema = caps.PROXY_REQUEST.params_schema
        
        # Check required params
        self.assertIn("service_id", schema)
        self.assertIn("request", schema)
        
        # Verify required flags
        self.assertTrue(schema["service_id"]["required"])
        self.assertTrue(schema["request"]["required"])

    def test_proxy_request_obligations(self):
        """Test proxy_request có default obligations."""
        caps = GatewayCoreCapabilities()
        self.assertIsInstance(caps.PROXY_REQUEST.default_obligations, list)
        self.assertTrue(len(caps.PROXY_REQUEST.default_obligations) > 0)

    def test_proxy_request_effects(self):
        """Test proxy_request có effects."""
        caps = GatewayCoreCapabilities()
        # Proxy request nên có outbound_call effect
        self.assertIn("outbound_call", caps.PROXY_REQUEST.effects)


class TestAggregateDataSequentialCapability(TestCase):
    """Test aggregate_data_sequential core capability."""

    def test_aggregate_sequential_exists(self):
        """Test aggregate_data_sequential capability tồn tại."""
        caps = GatewayCoreCapabilities()
        self.assertIsNotNone(caps.AGGREGATE_DATA_SEQUENTIAL)
        self.assertEqual(caps.AGGREGATE_DATA_SEQUENTIAL.id, "aggregate_data_sequential")

    def test_aggregate_sequential_params_schema(self):
        """Test aggregate_data_sequential params có service_chain field."""
        caps = GatewayCoreCapabilities()
        schema = caps.AGGREGATE_DATA_SEQUENTIAL.params_schema
        
        self.assertIn("service_chain", schema)
        self.assertTrue(schema["service_chain"]["required"])

    def test_aggregate_sequential_description(self):
        """Test aggregate_data_sequential description đề cập sequential."""
        caps = GatewayCoreCapabilities()
        self.assertIn("sequential", caps.AGGREGATE_DATA_SEQUENTIAL.description.lower())


class TestAggregateDataParallelCapability(TestCase):
    """Test aggregate_data_parallel core capability."""

    def test_aggregate_parallel_exists(self):
        """Test aggregate_data_parallel capability tồn tại."""
        caps = GatewayCoreCapabilities()
        self.assertIsNotNone(caps.AGGREGATE_DATA_PARALLEL)
        self.assertEqual(caps.AGGREGATE_DATA_PARALLEL.id, "aggregate_data_parallel")

    def test_aggregate_parallel_params_schema(self):
        """Test aggregate_data_parallel params có services field."""
        caps = GatewayCoreCapabilities()
        schema = caps.AGGREGATE_DATA_PARALLEL.params_schema
        
        self.assertIn("services", schema)
        self.assertTrue(schema["services"]["required"])

    def test_aggregate_parallel_description(self):
        """Test aggregate_data_parallel description đề cập parallel."""
        caps = GatewayCoreCapabilities()
        self.assertIn("parallel", caps.AGGREGATE_DATA_PARALLEL.description.lower())


class TestCacheResponseCapability(TestCase):
    """Test cache_response core capability."""

    def test_cache_response_exists(self):
        """Test cache_response capability tồn tại."""
        caps = GatewayCoreCapabilities()
        self.assertIsNotNone(caps.CACHE_RESPONSE)
        self.assertEqual(caps.CACHE_RESPONSE.id, "cache_response")

    def test_cache_response_params_schema(self):
        """Test cache_response params có cache_key và ttl fields."""
        caps = GatewayCoreCapabilities()
        schema = caps.CACHE_RESPONSE.params_schema
        
        self.assertIn("cache_key", schema)
        self.assertIn("ttl", schema)
        self.assertTrue(schema["cache_key"]["required"])

    def test_cache_response_write_access(self):
        """Test cache_response có cache trong write_access."""
        caps = GatewayCoreCapabilities()
        self.assertIn("cache", caps.CACHE_RESPONSE.write_access)


# ============================================================================
# Resilience Operations Tests
# ============================================================================


class TestCheckCircuitBreakerCapability(TestCase):
    """Test check_circuit_breaker core capability."""

    def test_check_circuit_breaker_exists(self):
        """Test check_circuit_breaker capability tồn tại."""
        caps = GatewayCoreCapabilities()
        self.assertIsNotNone(caps.CHECK_CIRCUIT_BREAKER)
        self.assertEqual(caps.CHECK_CIRCUIT_BREAKER.id, "check_circuit_breaker")

    def test_check_circuit_breaker_params_schema(self):
        """Test check_circuit_breaker params có service_id field."""
        caps = GatewayCoreCapabilities()
        schema = caps.CHECK_CIRCUIT_BREAKER.params_schema
        
        self.assertIn("service_id", schema)
        self.assertTrue(schema["service_id"]["required"])


class TestExecuteWithRetryCapability(TestCase):
    """Test execute_with_retry core capability."""

    def test_execute_with_retry_exists(self):
        """Test execute_with_retry capability tồn tại."""
        caps = GatewayCoreCapabilities()
        self.assertIsNotNone(caps.EXECUTE_WITH_RETRY)
        self.assertEqual(caps.EXECUTE_WITH_RETRY.id, "execute_with_retry")

    def test_execute_with_retry_params_schema(self):
        """Test execute_with_retry params có max_retries và backoff fields."""
        caps = GatewayCoreCapabilities()
        schema = caps.EXECUTE_WITH_RETRY.params_schema
        
        self.assertIn("max_retries", schema)
        self.assertIn("backoff_strategy", schema)


class TestApplyRateLimitCapability(TestCase):
    """Test apply_rate_limit core capability."""

    def test_apply_rate_limit_exists(self):
        """Test apply_rate_limit capability tồn tại."""
        caps = GatewayCoreCapabilities()
        self.assertIsNotNone(caps.APPLY_RATE_LIMIT)
        self.assertEqual(caps.APPLY_RATE_LIMIT.id, "apply_rate_limit")

    def test_apply_rate_limit_params_schema(self):
        """Test apply_rate_limit params có limit và window fields."""
        caps = GatewayCoreCapabilities()
        schema = caps.APPLY_RATE_LIMIT.params_schema
        
        self.assertIn("limit", schema)
        self.assertIn("window", schema)


# ============================================================================
# Service Mesh Operations Tests
# ============================================================================


class TestRegisterServiceCapability(TestCase):
    """Test register_service core capability."""

    def test_register_service_exists(self):
        """Test register_service capability tồn tại."""
        caps = GatewayCoreCapabilities()
        self.assertIsNotNone(caps.REGISTER_SERVICE)
        self.assertEqual(caps.REGISTER_SERVICE.id, "register_service")

    def test_register_service_params_schema(self):
        """Test register_service params có service_config field."""
        caps = GatewayCoreCapabilities()
        schema = caps.REGISTER_SERVICE.params_schema
        
        self.assertIn("service_config", schema)
        self.assertTrue(schema["service_config"]["required"])


class TestServiceDiscoveryCapability(TestCase):
    """Test service_discovery core capability."""

    def test_service_discovery_exists(self):
        """Test service_discovery capability tồn tại."""
        caps = GatewayCoreCapabilities()
        self.assertIsNotNone(caps.SERVICE_DISCOVERY)
        self.assertEqual(caps.SERVICE_DISCOVERY.id, "service_discovery")

    def test_service_discovery_params_schema(self):
        """Test service_discovery params có service_name field."""
        caps = GatewayCoreCapabilities()
        schema = caps.SERVICE_DISCOVERY.params_schema
        
        self.assertIn("service_name", schema)
        self.assertTrue(schema["service_name"]["required"])


class TestEmitMetricCapability(TestCase):
    """Test emit_metric core capability."""

    def test_emit_metric_exists(self):
        """Test emit_metric capability tồn tại."""
        caps = GatewayCoreCapabilities()
        self.assertIsNotNone(caps.EMIT_METRIC)
        self.assertEqual(caps.EMIT_METRIC.id, "emit_metric")

    def test_emit_metric_params_schema(self):
        """Test emit_metric params có metric_name và value fields."""
        caps = GatewayCoreCapabilities()
        schema = caps.EMIT_METRIC.params_schema
        
        self.assertIn("metric_name", schema)
        self.assertIn("value", schema)
        self.assertTrue(schema["metric_name"]["required"])
        self.assertTrue(schema["value"]["required"])

    def test_emit_metric_effects(self):
        """Test emit_metric có metric_emit effect."""
        caps = GatewayCoreCapabilities()
        self.assertIn("metric_emit", caps.EMIT_METRIC.effects)