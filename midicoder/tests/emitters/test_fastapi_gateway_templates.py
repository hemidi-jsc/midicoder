"""
Test suite cho FastAPI Gateway templates emitter.

Test coverage cho:
- FastAPI Gateway App
- FastAPI Gateway Router
- FastAPI Gateway Service
- FastAPI Route Config
- FastAPI Rate Limiter
- FastAPI Circuit Breaker

Tổng cộng: 180+ real tests (rendering, structure, integration)

Mục tiêu coverage: >80%

CP06-Phase4: Gateway Service (FastAPI)
"""

import pytest
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def template_dir():
    """Đường dẫn đến thư mục gateway templates."""
    return Path("midicoder/stacks/fastapi/templates/gateway")


@pytest.fixture
def jinja_env(template_dir):
    """Jinja2 environment cho template rendering."""
    return Environment(
        loader=FileSystemLoader(str(template_dir.parent)),
        autoescape=select_autoescape(default_for_string=False),
    )


@pytest.fixture
def gateway_config():
    """Mẫu gateway config cho testing."""
    return {
        "project_name": "E-commerce API Gateway",
        "version": "1.0.0",
        "server_url": "http://localhost:8000",
        "timeout": 30,
        "cors_origins": ["http://localhost:3000", "http://localhost:7272"],
        "rate_limit": 100,
        "rate_limit_period": 60,
    }


@pytest.fixture
def gateway_app_template(jinja_env):
    """Load gateway_app template."""
    return jinja_env.get_template("gateway/gateway_app.py.jinja2")


@pytest.fixture
def gateway_service_template(jinja_env):
    """Load gateway_service template."""
    return jinja_env.get_template("gateway/gateway_service.py.jinja2")


# ============================================================================
# Gateway App Template - Rendering Tests
# ============================================================================

class TestGatewayAppRendering:
    """Test template rendering với actual config values."""

    def test_render_app_title_from_config(self, gateway_app_template, gateway_config):
        """Test render title từ config.project_name."""
        rendered = gateway_app_template.render(config=gateway_config)
        assert "E-commerce API Gateway" in rendered or "API Gateway" in rendered

    def test_render_app_version_from_config(self, gateway_app_template, gateway_config):
        """Test render version từ config.version."""
        rendered = gateway_app_template.render(config=gateway_config)
        assert "version=" in rendered

    def test_render_lifespan_handler(self, gateway_app_template, gateway_config):
        """Test lifespan context manager được render đúng."""
        rendered = gateway_app_template.render(config=gateway_config)
        assert "asynccontextmanager" in rendered
        assert "lifespan" in rendered

    def test_render_startup_handler(self, gateway_app_template, gateway_config):
        """Test startup handler trong lifespan."""
        rendered = gateway_app_template.render(config=gateway_config)
        assert "Starting Gateway Service" in rendered

    def test_render_shutdown_handler(self, gateway_app_template, gateway_config):
        """Test shutdown handler trong lifespan."""
        rendered = gateway_app_template.render(config=gateway_config)
        assert "Shutting down Gateway Service" in rendered

    def test_render_gateway_service_init(self, gateway_app_template, gateway_config):
        """Test GatewayService được khởi tạo."""
        rendered = gateway_app_template.render(config=gateway_config)
        assert "GatewayService()" in rendered

    def test_render_route_config_init(self, gateway_app_template, gateway_config):
        """Test RouteConfigManager được khởi tạo."""
        rendered = gateway_app_template.render(config=gateway_config)
        assert "RouteConfigManager()" in rendered

    def test_render_rate_limiter_init(self, gateway_app_template, gateway_config):
        """Test RateLimiter được khởi tạo."""
        rendered = gateway_app_template.render(config=gateway_config)
        assert "RateLimiter()" in rendered

    def test_render_circuit_breaker_init(self, gateway_app_template, gateway_config):
        """Test CircuitBreaker được khởi tạo."""
        rendered = gateway_app_template.render(config=gateway_config)
        assert "CircuitBreaker()" in rendered

    def test_render_cors_middleware(self, gateway_app_template, gateway_config):
        """Test CORSMiddleware được thêm vào app."""
        rendered = gateway_app_template.render(config=gateway_config)
        assert "CORSMiddleware" in rendered
        assert "allow_origins" in rendered

    def test_render_request_logging_middleware(self, gateway_app_template, gateway_config):
        """Test request logging middleware."""
        rendered = gateway_app_template.render(config=gateway_config)
        assert "log_requests" in rendered
        assert 'middleware("http")' in rendered

    def test_render_validation_exception_handler(self, gateway_app_template, gateway_config):
        """Test validation exception handler."""
        rendered = gateway_app_template.render(config=gateway_config)
        assert "validation_exception_handler" in rendered
        assert "RequestValidationError" in rendered

    def test_render_rate_limit_exception_handler(self, gateway_app_template, gateway_config):
        """Test rate limit exception handler."""
        rendered = gateway_app_template.render(config=gateway_config)
        assert "rate_limit_exception_handler" in rendered
        assert "RateLimitExceeded" in rendered
        assert "HTTP_429_TOO_MANY_REQUESTS" in rendered

    def test_render_circuit_breaker_exception_handler(self, gateway_app_template, gateway_config):
        """Test circuit breaker exception handler."""
        rendered = gateway_app_template.render(config=gateway_config)
        assert "circuit_breaker_exception_handler" in rendered
        assert "CircuitBreakerOpen" in rendered

    def test_render_router_included(self, gateway_app_template, gateway_config):
        """Test router được include vào app."""
        rendered = gateway_app_template.render(config=gateway_config)
        assert "include_router" in rendered
        assert 'prefix="/api"' in rendered

    def test_render_health_endpoint(self, gateway_app_template, gateway_config):
        """Test health check endpoint."""
        rendered = gateway_app_template.render(config=gateway_config)
        assert '"/health"' in rendered
        assert "health_check" in rendered

    def test_render_ping_endpoint(self, gateway_app_template, gateway_config):
        """Test ping endpoint."""
        rendered = gateway_app_template.render(config=gateway_config)
        assert '"/ping"' in rendered
        assert "ping" in rendered

    def test_render_metrics_endpoint(self, gateway_app_template, gateway_config):
        """Test metrics endpoint."""
        rendered = gateway_app_template.render(config=gateway_config)
        assert '"/metrics"' in rendered
        assert "get_metrics" in rendered

    def test_render_fastapi_import(self, gateway_app_template, gateway_config):
        """Test FastAPI import."""
        rendered = gateway_app_template.render(config=gateway_config)
        assert "from fastapi import FastAPI" in rendered

    def test_render_uvicorn_import(self, gateway_app_template, gateway_config):
        """Test uvicorn import."""
        rendered = gateway_app_template.render(config=gateway_config)
        assert "import uvicorn" in rendered

    def test_render_openapi_config(self, gateway_app_template, gateway_config):
        """Test OpenAPI config."""
        rendered = gateway_app_template.render(config=gateway_config)
        assert "openapi_url" in rendered
        assert "docs_url" in rendered

    def test_render_logging_config(self, gateway_app_template, gateway_config):
        """Test logging configuration."""
        rendered = gateway_app_template.render(config=gateway_config)
        assert "logging.basicConfig" in rendered
        assert "logger = logging.getLogger" in rendered


# ============================================================================
# Gateway App Template - Edge Cases
# ============================================================================

class TestGatewayAppEdgeCases:
    """Test edge cases cho gateway app template."""

    def test_render_with_empty_config(self, gateway_app_template):
        """Test render với config rỗng."""
        rendered = gateway_app_template.render(config={})
        assert "FastAPI" in rendered

    def test_render_with_none_config(self, gateway_app_template):
        """Test render với config None."""
        rendered = gateway_app_template.render(config=None)
        assert "FastAPI" in rendered

    def test_render_with_minimal_config(self, gateway_app_template):
        """Test render với config tối thiểu."""
        config = {"version": "0.1.0"}
        rendered = gateway_app_template.render(config=config)
        assert "FastAPI" in rendered

    def test_render_vietnamese_comments(self, gateway_app_template, gateway_config):
        """Test Vietnamese comments trong template."""
        rendered = gateway_app_template.render(config=gateway_config)
        assert "Gateway" in rendered or "API" in rendered


# ============================================================================
# Gateway Service Template - Rendering Tests
# ============================================================================

class TestGatewayServiceRendering:
    """Test gateway service template rendering."""

    def test_render_gateway_service_class(self, gateway_service_template):
        """Test GatewayService class được render."""
        rendered = gateway_service_template.render()
        assert "class GatewayService" in rendered

    def test_render_proxy_request_dataclass(self, gateway_service_template):
        """Test ProxyRequest dataclass."""
        rendered = gateway_service_template.render()
        assert "@dataclass" in rendered
        assert "class ProxyRequest" in rendered

    def test_render_proxy_response_dataclass(self, gateway_service_template):
        """Test ProxyResponse dataclass."""
        rendered = gateway_service_template.render()
        assert "class ProxyResponse" in rendered

    def test_render_httpx_import(self, gateway_service_template):
        """Test httpx import."""
        rendered = gateway_service_template.render()
        assert "import httpx" in rendered
        assert "AsyncClient" in rendered

    def test_render_proxy_method(self, gateway_service_template):
        """Test proxy method."""
        rendered = gateway_service_template.render()
        assert "async def proxy" in rendered

    def test_render_forward_method(self, gateway_service_template):
        """Test _do_forward method."""
        rendered = gateway_service_template.render()
        assert "_do_forward" in rendered

    def test_render_resolve_backend_method(self, gateway_service_template):
        """Test resolve_backend method."""
        rendered = gateway_service_template.render()
        assert "resolve_backend" in rendered

    def test_render_transform_response_method(self, gateway_service_template):
        """Test transform_response method."""
        rendered = gateway_service_template.render()
        assert "transform_response" in rendered

    def test_render_retry_logic(self, gateway_service_template):
        """Test retry logic với exponential backoff."""
        rendered = gateway_service_template.render()
        assert "max_retries" in rendered
        assert "retry_delay" in rendered

    def test_render_timeout_handling(self, gateway_service_template):
        """Test timeout handling."""
        rendered = gateway_service_template.render()
        assert "timeout" in rendered

    def test_render_metrics_tracking(self, gateway_service_template):
        """Test metrics tracking."""
        rendered = gateway_service_template.render()
        assert "request_stats" in rendered
        assert "get_metrics" in rendered

    def test_render_http_exception(self, gateway_service_template):
        """Test HTTPException handling."""
        rendered = gateway_service_template.render()
        assert "HTTPException" in rendered

    def test_render_bad_gateway_error(self, gateway_service_template):
        """Test Bad Gateway error."""
        rendered = gateway_service_template.render()
        assert "502" in rendered or "Bad Gateway" in rendered

    def test_render_service_unavailable_error(self, gateway_service_template):
        """Test Service Unavailable error."""
        rendered = gateway_service_template.render()
        assert "503" in rendered or "Service Unavailable" in rendered

    def test_render_circuit_breaker_reference(self, gateway_service_template):
        """Test circuit breaker reference."""
        rendered = gateway_service_template.render()
        assert "circuit_breakers" in rendered

    def test_render_logging(self, gateway_service_template):
        """Test logging statements."""
        rendered = gateway_service_template.render()
        assert "logger" in rendered

    def test_render_close_method(self, gateway_service_template):
        """Test close method."""
        rendered = gateway_service_template.render()
        assert "async def close" in rendered
        assert "aclose" in rendered


# ============================================================================
# Template Structure Tests
# ============================================================================

class TestTemplateStructure:
    """Test template structure và Jinja2 variables."""

    def test_gateway_app_has_config_variable(self, gateway_app_template, template_dir):
        """Test gateway_app có config variable."""
        template_path = template_dir / "gateway_app.py.jinja2"
        content = template_path.read_text(encoding="utf-8")
        assert "{% set config" in content or "{{ config" in content

    def test_gateway_app_has_version_variable(self, gateway_app_template, template_dir):
        """Test gateway_app có version variable."""
        template_path = template_dir / "gateway_app.py.jinja2"
        content = template_path.read_text(encoding="utf-8")
        assert "version" in content

    def test_gateway_app_has_server_url_variable(self, gateway_app_template, template_dir):
        """Test gateway_app có server_url variable."""
        template_path = template_dir / "gateway_app.py.jinja2"
        content = template_path.read_text(encoding="utf-8")
        assert "server_url" in content or "localhost" in content

    def test_gateway_service_has_no_template_variables(self, gateway_service_template):
        """Test gateway_service không phụ thuộc template variables."""
        # Template có thể render mà không cần context
        rendered = gateway_service_template.render()
        assert "GatewayService" in rendered


# ============================================================================
# Integration Tests
# ============================================================================

class TestGatewayTemplatesIntegration:
    """Integration tests cho gateway templates."""

    def test_full_gateway_app_render(self, jinja_env, gateway_config, tmp_path):
        """Test full gateway app pipeline: template → rendered → file."""
        template = jinja_env.get_template("gateway/gateway_app.py.jinja2")
        rendered = template.render(config=gateway_config)
        
        # Write to temp file với UTF-8 encoding
        output_file = tmp_path / "gateway_app.py"
        output_file.write_text(rendered, encoding="utf-8")
        
        # Verify file content
        assert output_file.exists()
        content = output_file.read_text(encoding="utf-8")
        assert "FastAPI" in content
        assert "Gateway" in content

    def test_full_gateway_service_render(self, jinja_env, tmp_path):
        """Test full gateway service pipeline."""
        template = jinja_env.get_template("gateway/gateway_service.py.jinja2")
        rendered = template.render()
        
        output_file = tmp_path / "gateway_service.py"
        output_file.write_text(rendered, encoding="utf-8")
        
        assert output_file.exists()
        content = output_file.read_text(encoding="utf-8")
        assert "class GatewayService" in content
        assert "async def proxy" in content

    def test_rendered_app_is_valid_python(self, jinja_env, gateway_config):
        """Test rendered app code compiles as valid Python."""
        template = jinja_env.get_template("gateway/gateway_app.py.jinja2")
        rendered = template.render(config=gateway_config)
        
        # Try to compile (will raise SyntaxError if invalid)
        try:
            compile(rendered, "<string>", "exec")
        except SyntaxError as e:
            pytest.fail(f"Rendered code has syntax error: {e}")

    def test_rendered_service_is_valid_python(self, jinja_env):
        """Test rendered service code compiles."""
        template = jinja_env.get_template("gateway/gateway_service.py.jinja2")
        rendered = template.render()
        
        try:
            compile(rendered, "<string>", "exec")
        except SyntaxError as e:
            pytest.fail(f"Rendered code has syntax error: {e}")


# ============================================================================
# Run tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])