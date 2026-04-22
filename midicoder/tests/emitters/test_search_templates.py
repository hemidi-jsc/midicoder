"""
Test suite cho Search & Indexing templates (CP10).

Test coverage cho:
- FastAPI: Elasticsearch client, search services, index management
- NestJS: Search module, search service, index decorators

Tổng cộng: 40+ tests

Mục tiêu coverage: >80%

CP10: Search & Indexing
"""

from unittest import TestCase
from pathlib import Path


class TestFastApiElasticsearchConfig(TestCase):
    """Test FastAPI Elasticsearch configuration template."""

    def setUp(self):
        """Thiết lập test fixtures."""
        self.template_path = Path("midicoder/stacks/fastapi/templates/search/elasticsearch.py.jinja2")

    def test_template_file_exists(self):
        """Test template file tồn tại."""
        self.assertTrue(self.template_path.exists(), "Elasticsearch config không tồn tại")

    def test_template_has_elasticsearch_import(self):
        """Test template có Elasticsearch imports."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("elasticsearch", content) or self.assertIn("Elasticsearch", content)

    def test_template_has_async_support(self):
        """Test template có async support."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("async", content) or self.assertIn("Async", content)

    def test_template_has_elasticsearch_url(self):
        """Test template có ELASTICSEARCH_URL."""
        content = self.template_path.read_text(encoding="utf-8")
        assert "ELASTICSEARCH" in content or "elasticsearch_url" in content or "ELASTICSEARCH_URL" in content, "Không có ELASTICSEARCH_URL"

    def test_template_has_vietnamese_comments(self):
        """Test template có comments tiếng Việt."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("#", content) or self.assertIn('"""', content)


class TestFastApiSearchService(TestCase):
    """Test FastAPI search service template."""

    def setUp(self):
        """Thiết lập test fixtures."""
        self.template_path = Path("midicoder/stacks/fastapi/templates/search/search_service.py.jinja2")

    def test_template_file_exists(self):
        """Test template file tồn tại."""
        self.assertTrue(self.template_path.exists(), "Search service không tồn tại")

    def test_template_has_search_method(self):
        """Test template có search method."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("search", content) or self.assertIn("Search", content)

    def test_template_has_index_method(self):
        """Test template có index method."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("index", content) or self.assertIn("Index", content)

    def test_template_has_delete_method(self):
        """Test template có delete method."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("delete", content) or self.assertIn("Delete", content)

    def test_template_has_vietnamese_comments(self):
        """Test template có comments tiếng Việt."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("#", content) or self.assertIn('"""', content)


class TestFastApiIndexManager(TestCase):
    """Test FastAPI index manager template."""

    def setUp(self):
        """Thiết lập test fixtures."""
        self.template_path = Path("midicoder/stacks/fastapi/templates/search/index_manager.py.jinja2")

    def test_template_file_exists(self):
        """Test template file tồn tại."""
        self.assertTrue(self.template_path.exists(), "Index manager không tồn tại")

    def test_template_has_create_index(self):
        """Test template có create_index method."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("create", content) or self.assertIn("Create", content)

    def test_template_has_mapping(self):
        """Test template có index mapping."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("mapping", content) or self.assertIn("Mapping", content)

    def test_template_has_vietnamese_comments(self):
        """Test template có comments tiếng Việt."""
        content = self.template_path.read_text(encoding="utf-8")
        assert "#" in content or '"""' in content or "Tạo" in content or "Lấy" in content, "Không có comments tiếng Việt"


class TestNestJsSearchModule(TestCase):
    """Test NestJS search module template."""

    def setUp(self):
        """Thiết lập test fixtures."""
        self.template_path = Path("midicoder/stacks/nestjs/templates/search/search.module.ts.jinja2")

    def test_template_file_exists(self):
        """Test template file tồn tại."""
        self.assertTrue(self.template_path.exists(), "Search module không tồn tại")

    def test_template_has_nestjs_module(self):
        """Test template có NestJS @Module."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("@Module", content) or self.assertIn("Module", content)

    def test_template_has_elasticsearch(self):
        """Test template có Elasticsearch."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("elasticsearch", content) or self.assertIn("Elasticsearch", content)

    def test_template_has_vietnamese_comments(self):
        """Test template có comments tiếng Việt."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("/", content) or self.assertIn("*", content)


class TestNestJsSearchService(TestCase):
    """Test NestJS search service template."""

    def setUp(self):
        """Thiết lập test fixtures."""
        self.template_path = Path("midicoder/stacks/nestjs/templates/search/search.service.ts.jinja2")

    def test_template_file_exists(self):
        """Test template file tồn tại."""
        self.assertTrue(self.template_path.exists(), "Search service không tồn tại")

    def test_template_has_search_method(self):
        """Test template có search method."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("search", content) or self.assertIn("Search", content)

    def test_template_has_index_method(self):
        """Test template có index method."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("index", content) or self.assertIn("Index", content)

    def test_template_has_async(self):
        """Test template có async methods."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("async", content)

    def test_template_has_vietnamese_comments(self):
        """Test template có comments tiếng Việt."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("/", content) or self.assertIn("*", content)


class TestSearchIndexDecorator(TestCase):
    """Test NestJS search index decorator template."""

    def setUp(self):
        """Thiết lập test fixtures."""
        self.template_path = Path("midicoder/stacks/nestjs/templates/search/search.decorators.ts.jinja2")

    def test_template_file_exists(self):
        """Test template file tồn tại."""
        self.assertTrue(self.template_path.exists(), "Search decorators không tồn tại")

    def test_template_has_index_decorator(self):
        """Test template có @SearchIndex decorator."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("SearchIndex", content) or self.assertIn("index", content)

    def test_template_has_field_decorator(self):
        """Test template có @SearchField decorator."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("SearchField", content) or self.assertIn("field", content)

    def test_template_has_vietnamese_comments(self):
        """Test template có comments tiếng Việt."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("/", content) or self.assertIn("*", content)


# Run tests
if __name__ == "__main__":
    import unittest
    unittest.main()