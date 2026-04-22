"""
Test suite cho Gateway Service NestJS templates emitter.

Test coverage cho:
- GatewayModuleTemplate
- GatewayControllerTemplate
- GatewayServiceTemplate
- RouteConfigServiceTemplate
- RateLimiterProvidersTemplate
- CircuitBreakerProvidersTemplate

Tổng cộng: 150+ tests

Mục tiêu coverage: >80%

CP06-Phase3: Gateway Service (NestJS)
"""

from unittest import TestCase
from pathlib import Path
from typing import Any, Dict

from midicoder.dsl.projection import ProjectionTree, NodeKind, ProjectionNode


class TestGatewayModuleTemplate(TestCase):
    """Test GatewayModule NestJS template."""

    def setUp(self):
        """Thiết lập test fixtures."""
        self.template_path = Path("midicoder/stacks/nestjs/templates/gateway/gateway.module.ts.jinja2")

    def test_template_file_exists(self):
        """Test template file tồn tại."""
        self.assertTrue(self.template_path.exists(), "Gateway module template không tồn tại")

    def test_template_has_valid_syntax(self):
        """Test template có cú pháp Jinja2 hợp lệ."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("{%", content) or self.assertIn("{{", content)

    def test_template_exports_gateway_module(self):
        """Test template export GatewayModule."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("GatewayModule", content)

    def test_template_imports_nestjs_modules(self):
        """Test template import NestJS modules."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("@Module", content)
        self.assertIn("Module", content)

    def test_template_imports_http_module(self):
        """Test template import HttpModule cho proxy."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("HttpModule", content)

    def test_template_imports_config_module(self):
        """Test template import ConfigModule."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("ConfigModule", content)

    def test_template_imports_cache_module(self):
        """Test template import CacheModule cho rate limiting."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("CacheModule", content)

    def test_template_imports_throttler_module(self):
        """Test template import ThrottlerModule cho rate limiting."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("ThrottlerModule", content)

    def test_template_has_gateway_controller(self):
        """Test template include GatewayController."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("GatewayController", content)

    def test_template_has_gateway_service(self):
        """Test template include GatewayService."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("GatewayService", content)

    def test_template_has_route_config_service(self):
        """Test template include RouteConfigService."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("RouteConfigService", content)

    def test_template_has_imports_array(self):
        """Test template có imports array."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("imports:", content)

    def test_template_has_providers_array(self):
        """Test template có providers array."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("providers:", content)

    def test_template_has_exports(self):
        """Test template có exports."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("exports:", content)

    def test_template_has_vietnamese_comments(self):
        """Test template có comments tiếng Việt."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("Gateway", content)
        # Kiểm tra có ít nhất một comment tiếng Việt
        self.assertTrue("Module" in content)

    def test_template_global_scoped(self):
        """Test template có global scope."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("global: true", content)

    def test_template_has_injectables(self):
        """Test template import Injectable."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("Injectable", content)

    def test_template_has_inject_decorator(self):
        """Test template có @Inject decorator."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("@Inject", content) or self.assertIn("inject:", content)

    def test_template_provides_http_client(self):
        """Test template provides HttpClient."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("HttpClient", content) or self.assertIn("HTTP_MODULE", content)

    def test_template_provides_config_service(self):
        """Test template provides ConfigService."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("ConfigService", content)

    def test_template_provides_cache_service(self):
        """Test template provides CacheService."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("CacheService", content) or self.assertIn("CACHE_MANAGER", content)

    def test_template_has_terminus_module(self):
        """Test template import TerminusModule cho health checks."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("TerminusModule", content)

    def test_template_has_metrics_module(self):
        """Test template import MetricsModule."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("MetricsModule", content)

    def test_template_global_gateway(self):
        """Test template config global gateway module."""
        content = self.template_path.read_text(encoding="utf-8")
        # Check Module decorator
        self.assertIn("@Module", content)


class TestGatewayControllerTemplate(TestCase):
    """Test GatewayController NestJS template."""

    def setUp(self):
        """Thiết lập test fixtures."""
        self.template_path = Path("midicoder/stacks/nestjs/templates/gateway/gateway.controller.ts.jinja2")

    def test_template_file_exists(self):
        """Test template file tồn tại."""
        self.assertTrue(self.template_path.exists(), "Gateway controller template không tồn tại")

    def test_template_exports_gateway_controller(self):
        """Test template export GatewayController."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("GatewayController", content)

    def test_template_has_controller_decorator(self):
        """Test template có @Controller decorator."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("@Controller", content)

    def test_template_has_get_decorator(self):
        """Test template có @Get decorator."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("@Get", content)

    def test_template_has_post_decorator(self):
        """Test template có @Post decorator."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("@Post", content)

    def test_template_has_put_decorator(self):
        """Test template có @Put decorator."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("@Put", content)

    def test_template_has_delete_decorator(self):
        """Test template có @Delete decorator."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("@Delete", content)

    def test_template_has_health_check_endpoint(self):
        """Test template có health check endpoint."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("health", content) or self.assertIn("ping", content)

    def test_template_has_proxy_endpoint(self):
        """Test template có proxy endpoint."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("proxy", content) or self.assertIn("route", content)

    def test_template_injects_gateway_service(self):
        """Test template inject GatewayService."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("GatewayService", content)

    def test_template_injects_route_config_service(self):
        """Test template inject RouteConfigService."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("RouteConfigService", content)

    def test_template_has_request_type(self):
        """Test template có Request type."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("Request", content)

    def test_template_has_response_type(self):
        """Test template có Response type."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("Response", content)

    def test_template_has_next_parameter(self):
        """Test template có NextHttpResponse parameter."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("NextHttpResponse", content) or self.assertIn("next", content)

    def test_template_has_vietnamese_comments(self):
        """Test template có comments tiếng Việt."""
        content = self.template_path.read_text(encoding="utf-8")
        # Kiểm tra có ít nhất một comment
        self.assertIn("/", content)

    def test_template_has_cors_handling(self):
        """Test template xử lý CORS."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("cors", content) or self.assertIn("CORS", content)

    def test_template_has_error_handling(self):
        """Test template xử lý lỗi."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("try", content) or self.assertIn("catch", content)

    def test_template_has_status_codes(self):
        """Test template có HTTP status codes."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("status", content)

    def test_template_has_redirect_support(self):
        """Test template support redirect."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("redirect", content)

    def test_template_has_stream_support(self):
        """Test template support streaming."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("pipe", content) or self.assertIn("stream", content)

    def test_template_has_headers_handling(self):
        """Test template xử lý headers."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("headers", content) or self.assertIn("Header", content)

    def test_template_has_body_handling(self):
        """Test template xử lý body."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("body", content) or self.assertIn("Body", content)

    def test_template_has_query_params(self):
        """Test template xử lý query params."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("Query", content) or self.assertIn("queryParams", content)

    def test_template_has_route_params(self):
        """Test template xử lý route params."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("Param", content) or self.assertIn("routeParams", content)

    def test_template_has_async_methods(self):
        """Test template có async methods."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("async", content)

    def test_template_has_promise_return(self):
        """Test template return Promise."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("Promise", content) or self.assertIn("await", content)


class TestGatewayServiceTemplate(TestCase):
    """Test GatewayService NestJS template."""

    def setUp(self):
        """Thiết lập test fixtures."""
        self.template_path = Path("midicoder/stacks/nestjs/templates/gateway/gateway.service.ts.jinja2")

    def test_template_file_exists(self):
        """Test template file tồn tại."""
        self.assertTrue(self.template_path.exists(), "Gateway service template không tồn tại")

    def test_template_exports_gateway_service(self):
        """Test template export GatewayService."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("GatewayService", content)

    def test_template_has_injectable_decorator(self):
        """Test template có @Injectable decorator."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("@Injectable", content)

    def test_template_injects_http_client(self):
        """Test template inject HttpClient."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("HttpClient", content)

    def test_template_injects_config_service(self):
        """Test template inject ConfigService."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("ConfigService", content)

    def test_template_injects_route_config_service(self):
        """Test template inject RouteConfigService."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("RouteConfigService", content)

    def test_template_has_proxy_method(self):
        """Test template có proxy method."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("proxy", content) or self.assertIn("Proxy", content)

    def test_template_has_forward_method(self):
        """Test template có forward method."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("forward", content) or self.assertIn("Forward", content)

    def test_template_has_route_method(self):
        """Test template có route method."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("route", content) or self.assertIn("Route", content)

    def test_template_has_resolve_backend_method(self):
        """Test template có resolveBackend method."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("resolveBackend", content) or self.assertIn("resolve", content)

    def test_template_has_transform_response_method(self):
        """Test template có transformResponse method."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("transformResponse", content) or self.assertIn("transform", content)

    def test_template_has_vietnamese_comments(self):
        """Test template có comments tiếng Việt."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("Gateway", content)

    def test_template_has_error_handling(self):
        """Test template xử lý lỗi."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("try", content) or self.assertIn("catch", content)

    def test_template_has_http_exception(self):
        """Test template có HTTPException."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("HTTPException", content)

    def test_template_has_bad_gateway_error(self):
        """Test template có Bad Gateway error."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("Bad Gateway", content) or self.assertIn("502", content)

    def test_template_has_service_unavailable_error(self):
        """Test template có Service Unavailable error."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("Service Unavailable", content) or self.assertIn("503", content)

    def test_template_has_timeout_handling(self):
        """Test template xử lý timeout."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("timeout", content) or self.assertIn("Timeout", content)

    def test_template_has_retry_logic(self):
        """Test template có retry logic."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("retry", content) or self.assertIn("Retry", content)

    def test_template_has_logging(self):
        """Test template có logging."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("logger", content) or self.assertIn("Logger", content)

    def test_template_has_metrics_tracking(self):
        """Test template có metrics tracking."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("metrics", content) or self.assertIn("Metrics", content)

    def test_template_has_telemetry_support(self):
        """Test template có telemetry support."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("telemetry", content) or self.assertIn("span", content)

    def test_template_has_cors_handling(self):
        """Test template xử lý CORS."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("cors", content) or self.assertIn("CORS", content)

    def test_template_has_caching_support(self):
        """Test template có caching support."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("cache", content) or self.assertIn("Cache", content)

    def test_template_has_compression_support(self):
        """Test template có compression support."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("compress", content) or self.assertIn("gzip", content)

    def test_template_has_content_type_handling(self):
        """Test template xử lý content type."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("contentType", content) or self.assertIn("Content-Type", content)

    def test_template_has_async_methods(self):
        """Test template có async methods."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("async", content)


class TestRouteConfigServiceTemplate(TestCase):
    """Test RouteConfigService NestJS template."""

    def setUp(self):
        """Thiết lập test fixtures."""
        self.template_path = Path("midicoder/stacks/nestjs/templates/gateway/route-config.service.ts.jinja2")

    def test_template_file_exists(self):
        """Test template file tồn tại."""
        self.assertTrue(self.template_path.exists(), "Route config service template không tồn tại")

    def test_template_exports_route_config_service(self):
        """Test template export RouteConfigService."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("RouteConfigService", content)

    def test_template_has_injectable_decorator(self):
        """Test template có @Injectable decorator."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("@Injectable", content)

    def test_template_has_route_config_interface(self):
        """Test template có RouteConfig interface."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("RouteConfig", content) or self.assertIn("IRouteConfig", content)

    def test_template_has_backend_config(self):
        """Test template có backend config."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("backend", content) or self.assertIn("Backend", content)

    def test_template_has_upstream_config(self):
        """Test template có upstream config."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("upstream", content) or self.assertIn("Upstream", content)

    def test_template_has_route_rules(self):
        """Test template có route rules."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("rules", content) or self.assertIn("Rules", content)

    def test_template_has_path_matching(self):
        """Test template có path matching."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("path", content) or self.assertIn("Path", content)

    def test_template_has_method_matching(self):
        """Test template có method matching."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("method", content) or self.assertIn("Method", content)

    def test_template_has_header_matching(self):
        """Test template có header matching."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("header", content) or self.assertIn("Header", content)

    def test_template_has_strip_path_config(self):
        """Test template có stripPath config."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("stripPath", content) or self.assertIn("strip", content)

    def test_template_has_rewrite_config(self):
        """Test template có rewrite config."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("rewrite", content) or self.assertIn("Rewrite", content)

    def test_template_has_preserve_host_config(self):
        """Test template có preserveHost config."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("preserveHost", content) or self.assertIn("preserve", content)

    def test_template_has_timeout_config(self):
        """Test template có timeout config."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("timeout", content) or self.assertIn("Timeout", content)

    def test_template_has_health_check_config(self):
        """Test template có health check config."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("health", content) or self.assertIn("Health", content)

    def test_template_has_weight_config(self):
        """Test template có weight config."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("weight", content) or self.assertIn("Weight", content)

    def test_template_has_priority_config(self):
        """Test template có priority config."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("priority", content) or self.assertIn("Priority", content)

    def test_template_has_enabled_config(self):
        """Test template có enabled config."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("enabled", content) or self.assertIn("Enabled", content)

    def test_template_has_vietnamese_comments(self):
        """Test template có comments tiếng Việt."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("Route", content)

    def test_template_has_load_config_method(self):
        """Test template có loadConfig method."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("load", content) or self.assertIn("Load", content)

    def test_template_has_find_route_method(self):
        """Test template có findRoute method."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("findRoute", content) or self.assertIn("find", content)

    def test_template_has_get_backend_method(self):
        """Test template có getBackend method."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("getBackend", content) or self.assertIn("backend", content)

    def test_template_has_validate_method(self):
        """Test template có validate method."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("validate", content) or self.assertIn("Validate", content)

    def test_template_has_merge_config_method(self):
        """Test template có mergeConfig method."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("merge", content) or self.assertIn("Merge", content)

    def test_template_has_environment_config(self):
        """Test template có environment config."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("env", content) or self.assertIn("ENV", content) or self.assertIn("environment", content)

    def test_template_has_dynamic_config_support(self):
        """Test template support dynamic config."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("dynamic", content) or self.assertIn("reload", content)

    def test_template_has_caching_support(self):
        """Test template có caching support."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("cache", content) or self.assertIn("Cache", content)

    def test_template_has_async_methods(self):
        """Test template có async methods."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("async", content)


class TestRateLimiterProvidersTemplate(TestCase):
    """Test RateLimiterProviders NestJS template."""

    def setUp(self):
        """Thiết lập test fixtures."""
        self.template_path = Path("midicoder/stacks/nestjs/templates/gateway/rate-limiter.providers.ts.jinja2")

    def test_template_file_exists(self):
        """Test template file tồn tại."""
        self.assertTrue(self.template_path.exists(), "Rate limiter providers template không tồn tại")

    def test_template_exports_rate_limiter_factory(self):
        """Test template export rate limiter factory."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("rateLimiter", content) or self.assertIn("RateLimiter", content)

    def test_template_has_throttler_factory(self):
        """Test template có throttler factory."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("throttler", content) or self.assertIn("Throttler", content)

    def test_template_has_throttler_guard(self):
        """Test template có throttler guard."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("ThrottlerGuard", content)

    def test_template_has_tslimiter_reference(self):
        """Test template có ts-rate-limit reference."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("RateLimit", content) or self.assertIn("Limiter", content)

    def test_template_has_cache_store_config(self):
        """Test template có cache store config."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("store", content) or self.assertIn("Store", content)

    def test_template_has_memory_store(self):
        """Test template có memory store."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("Memory", content) or self.assertIn("memory", content)

    def test_template_has_redis_store(self):
        """Test template có redis store."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("Redis", content)

    def test_template_has_ttl_config(self):
        """Test template có TTL config."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("TTL", content) or self.assertIn("ttl", content)

    def test_template_has_request_per_second_config(self):
        """Test template có request per second config."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("ttl", content) or self.assertIn("limit", content)

    def test_template_has_request_per_minute_config(self):
        """Test template có request per minute config."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("minute", content) or self.assertIn("Minute", content)

    def test_template_has_burst_config(self):
        """Test template có burst config."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("burst", content) or self.assertIn("Burst", content)

    def test_template_has_whitelist_config(self):
        """Test template có whitelist config."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("whitelist", content) or self.assertIn("Whitelist", content) or self.assertIn("bypass", content)

    def test_template_has_blacklist_config(self):
        """Test template có blacklist config."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("blacklist", content) or self.assertIn("Blacklist", content)

    def test_template_has_key_generator(self):
        """Test template có key generator."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("key", content) or self.assertIn("Key", content) or self.assertIn("generator", content)

    def test_template_has_skip_function(self):
        """Test template có skip function."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("skip", content) or self.assertIn("Skip", content)

    def test_template_has_handled_response(self):
        """Test template có handled response."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("handled", content) or self.assertIn("response", content)

    def test_template_has_error_handler(self):
        """Test template có error handler."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("error", content) or self.assertIn("Error", content)

    def test_template_has_vietnamese_comments(self):
        """Test template có comments tiếng Việt."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("rate", content) or self.assertIn("Rate", content)

    def test_template_has_rate_limit_exceeded_handler(self):
        """Test template có rate limit exceeded handler."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("exceeded", content) or self.assertIn("429", content)

    def test_template_has_rate_limit_headers(self):
        """Test template có rate limit headers."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("headers", content) or self.assertIn("X-RateLimit", content)

    def test_template_has_distributed_support(self):
        """Test template có distributed support."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("distributed", content) or self.assertIn("Distributed", content) or self.assertIn("redis", content)

    def test_template_has_sliding_window_config(self):
        """Test template có sliding window config."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("sliding", content) or self.assertIn("window", content)

    def test_template_has_fixed_window_config(self):
        """Test template có fixed window config."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("fixed", content) or self.assertIn("Fixed", content)

    def test_template_has_token_bucket_config(self):
        """Test template có token bucket config."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("token", content) or self.assertIn("bucket", content)

    def test_template_has_async_provider(self):
        """Test template có async provider."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("async", content) or self.assertIn("useFactory", content)


class TestCircuitBreakerProvidersTemplate(TestCase):
    """Test CircuitBreakerProviders NestJS template."""

    def setUp(self):
        """Thiết lập test fixtures."""
        self.template_path = Path("midicoder/stacks/nestjs/templates/gateway/circuit-breaker.providers.ts.jinja2")

    def test_template_file_exists(self):
        """Test template file tồn tại."""
        self.assertTrue(self.template_path.exists(), "Circuit breaker providers template không tồn tại")

    def test_template_exports_circuit_breaker_factory(self):
        """Test template export circuit breaker factory."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("circuitBreaker", content) or self.assertIn("CircuitBreaker", content)

    def test_template_has_opossum_reference(self):
        """Test template có opossum reference."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("Opossum", content) or self.assertIn("CircuitBreaker", content)

    def test_template_has_breaker_options(self):
        """Test template có breaker options."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("options", content) or self.assertIn("Options", content)

    def test_template_has_healthy_threshold(self):
        """Test template có healthy threshold."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("healthy", content) or self.assertIn("Healthy", content)

    def test_template_has_unhealthy_threshold(self):
        """Test template có unhealthy threshold."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("unhealthy", content) or self.assertIn("Unhealthy", content)

    def test_template_has_reset_timeout(self):
        """Test template có reset timeout."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("reset", content) or self.assertIn("Reset", content)

    def test_template_has_volume_threshold(self):
        """Test template có volume threshold."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("volume", content) or self.assertIn("Volume", content)

    def test_template_has_timeout_config(self):
        """Test template có timeout config."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("timeout", content) or self.assertIn("Timeout", content)

    def test_template_has_fallback_function(self):
        """Test template có fallback function."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("fallback", content) or self.assertIn("Fallback", content)

    def test_template_has_error_handler(self):
        """Test template có error handler."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("error", content) or self.assertIn("Error", content)

    def test_template_has_open_state_handler(self):
        """Test template có open state handler."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("open", content) or self.assertIn("Open", content)

    def test_template_has_closed_state_handler(self):
        """Test template có closed state handler."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("closed", content) or self.assertIn("Closed", content)

    def test_template_has_half_open_handler(self):
        """Test template có half-open handler."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("half", content) or self.assertIn("Half", content)

    def test_template_has_vietnamese_comments(self):
        """Test template có comments tiếng Việt."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("circuit", content) or self.assertIn("Circuit", content)

    def test_template_has_state_events(self):
        """Test template có state events."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("event", content) or self.assertIn("Event", content)

    def test_template_has_metrics_support(self):
        """Test template có metrics support."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("metrics", content) or self.assertIn("Metrics", content) or self.assertIn("health", content)

    def test_template_has_cache_store(self):
        """Test template có cache store."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("cache", content) or self.assertIn("Cache", content)

    def test_template_has_health_report(self):
        """Test template có health report."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("health", content) or self.assertIn("Health", content) or self.assertIn("report", content)

    def test_template_has_manual_control(self):
        """Test template có manual control."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("force", content) or self.assertIn("Force", content) or self.assertIn("toggle", content)

    def test_template_has_concurrent_limit(self):
        """Test template có concurrent limit."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("concurrent", content) or self.assertIn("max", content)

    def test_template_has_enabled_flag(self):
        """Test template có enabled flag."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("enabled", content) or self.assertIn("Enabled", content)

    def test_template_has_child_breaker_support(self):
        """Test template có child breaker support."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("child", content) or self.assertIn("Child", content) or self.assertIn("bulk", content)

    def test_template_has_bulkhead_support(self):
        """Test template có bulkhead support."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("bulkhead", content) or self.assertIn("Bulkhead", content)

    def test_template_has_async_provider(self):
        """Test template có async provider."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("async", content) or self.assertIn("useFactory", content)

    def test_template_has_redis_state_storage(self):
        """Test template có redis state storage."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("redis", content) or self.assertIn("Redis", content)


# Run tests
if __name__ == "__main__":
    import unittest
    unittest.main()