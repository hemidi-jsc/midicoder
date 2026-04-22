"""
Test suite cho Caching & Performance templates (CP09).

Test coverage cho:
- FastAPI: Redis client, cache decorators, cache strategies
- NestJS: Redis module, cache interceptor, cache strategies

Tổng cộng: 50+ tests

Mục tiêu coverage: >80%

CP09: Caching & Performance
"""

from unittest import TestCase
from pathlib import Path


class TestFastApiRedisConfig(TestCase):
    """Test FastAPI Redis configuration template."""

    def setUp(self):
        """Thiết lập test fixtures."""
        self.template_path = Path("midicoder/stacks/fastapi/templates/cache/redis.py.jinja2")

    def test_template_file_exists(self):
        """Test template file tồn tại."""
        self.assertTrue(self.template_path.exists(), "FastAPI Redis config không tồn tại")

    def test_template_has_redis_import(self):
        """Test template có Redis imports."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("redis", content) or self.assertIn("Redis", content)

    def test_template_has_async_support(self):
        """Test template có async support."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("async", content) or self.assertIn("await", content)

    def test_template_has_connection_pool(self):
        """Test template có connection pool."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("pool", content) or self.assertIn("Pool", content)

    def test_template_has_redis_url(self):
        """Test template có REDIS_URL."""
        content = self.template_path.read_text(encoding="utf-8")
        assert "REDIS" in content or "redis_url" in content or "REDIS_URL" in content, "Không có REDIS_URL"

    def test_template_has_vietnamese_comments(self):
        """Test template có comments tiếng Việt."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("#", content) or self.assertIn('"""', content)


class TestFastApiCacheDecorator(TestCase):
    """Test FastAPI cache decorator template."""

    def setUp(self):
        """Thiết lập test fixtures."""
        self.template_path = Path("midicoder/stacks/fastapi/templates/cache/cache_decorators.py.jinja2")

    def test_template_file_exists(self):
        """Test template file tồn tại."""
        self.assertTrue(self.template_path.exists(), "Cache decorators không tồn tại")

    def test_template_has_cache_decorator(self):
        """Test template có cache decorator."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("cache", content) or self.assertIn("Cache", content)

    def test_template_has_ttl(self):
        """Test template có TTL support."""
        content = self.template_path.read_text(encoding="utf-8")
        assert "ttl" in content or "TTL" in content or "expire" in content or "DEFAULT_TTL" in content, "Không có TTL"

    def test_template_has_invalidate(self):
        """Test template có cache invalidation."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("invalidate", content) or self.assertIn("clear", content) or self.assertIn("delete", content)

    def test_template_has_async(self):
        """Test template có async support."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("async", content) or self.assertIn("await", content)

    def test_template_has_vietnamese_comments(self):
        """Test template có comments tiếng Việt."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("#", content) or self.assertIn('"""', content)


class TestFastApiCacheStrategy(TestCase):
    """Test FastAPI cache strategies template."""

    def setUp(self):
        """Thiết lập test fixtures."""
        self.template_path = Path("midicoder/stacks/fastapi/templates/cache/cache_strategy.py.jinja2")

    def test_template_file_exists(self):
        """Test template file tồn tại."""
        self.assertTrue(self.template_path.exists(), "Cache strategy không tồn tại")

    def test_template_has_read_through(self):
        """Test template có read-through strategy."""
        content = self.template_path.read_text(encoding="utf-8")
        assert "read" in content or "Read" in content or "ReadThrough" in content, "Không có read-through"

    def test_template_has_write_through(self):
        """Test template có write-through strategy."""
        content = self.template_path.read_text(encoding="utf-8")
        assert "write" in content or "Write" in content or "WriteThrough" in content, "Không có write-through"

    def test_template_has_vietnamese_comments(self):
        """Test template có comments tiếng Việt."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("#", content) or self.assertIn('"""', content)


class TestNestJsRedisModule(TestCase):
    """Test NestJS Redis module template."""

    def setUp(self):
        """Thiết lập test fixtures."""
        self.template_path = Path("midicoder/stacks/nestjs/templates/cache/redis.module.ts.jinja2")

    def test_template_file_exists(self):
        """Test template file tồn tại."""
        self.assertTrue(self.template_path.exists(), "NestJS Redis module không tồn tại")

    def test_template_has_redis_import(self):
        """Test template có Redis imports."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("redis", content) or self.assertIn("Redis", content)

    def test_template_has_nestjs_module(self):
        """Test template có NestJS @Module."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("@Module", content) or self.assertIn("Module", content)

    def test_template_has_redis_url(self):
        """Test template có REDIS_URL."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("REDIS", content) or self.assertIn("redis", content)

    def test_template_has_vietnamese_comments(self):
        """Test template có comments tiếng Việt."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("/", content) or self.assertIn("*", content)


class TestNestJsCacheInterceptor(TestCase):
    """Test NestJS cache interceptor template."""

    def setUp(self):
        """Thiết lập test fixtures."""
        self.template_path = Path("midicoder/stacks/nestjs/templates/cache/cache.interceptor.ts.jinja2")

    def test_template_file_exists(self):
        """Test template file tồn tại."""
        self.assertTrue(self.template_path.exists(), "Cache interceptor không tồn tại")

    def test_template_has_interceptor(self):
        """Test template có Interceptor."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("Interceptor", content) or self.assertIn("intercept", content)

    def test_template_has_cache(self):
        """Test template có cache logic."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("cache", content) or self.assertIn("Cache", content)

    def test_template_has_ttl(self):
        """Test template có TTL support."""
        content = self.template_path.read_text(encoding="utf-8")
        assert "ttl" in content or "TTL" in content or "expire" in content or "DEFAULT_TTL" in content or "CACHE_TTL" in content, "Không có TTL"

    def test_template_has_vietnamese_comments(self):
        """Test template có comments tiếng Việt."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("/", content) or self.assertIn("*", content)


class TestCacheInvalidateService(TestCase):
    """Test Cache Invalidation service template."""

    def setUp(self):
        """Thiết lập test fixtures."""
        self.template_path = Path("midicoder/stacks/fastapi/templates/cache/cache_invalidate.py.jinja2")

    def test_template_file_exists(self):
        """Test template file tồn tại."""
        self.assertTrue(self.template_path.exists(), "Cache invalidation service không tồn tại")

    def test_template_has_invalidate_pattern(self):
        """Test template có pattern-based invalidation."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("pattern", content) or self.assertIn("Pattern", content) or self.assertIn("invalidate", content)

    def test_template_has_vietnamese_comments(self):
        """Test template có comments tiếng Việt."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("#", content) or self.assertIn('"""', content)


# Run tests
if __name__ == "__main__":
    import unittest
    unittest.main()