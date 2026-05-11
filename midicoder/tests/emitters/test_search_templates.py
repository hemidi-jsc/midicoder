# coding: utf-8
"""
Test suite cho Search & Indexing templates (CP10).

Test coverage cho:
- FastAPI: Elasticsearch client, search services, index management
- NestJS: Search module, search service, index decorators
- Angular: Search service, search module
- React: SearchProvider, useSearch hook

KPI-029: Tenant Isolation - Tat ca templates phai co tenant awareness

CP10: Search & Indexing
"""

from unittest import TestCase
from pathlib import Path


class TestFastApiElasticsearchConfig(TestCase):
    """Test FastAPI Elasticsearch configuration template."""

    def setUp(self):
        """Thiet lap test fixtures."""
        self.template_path = Path(
            "midicoder/stacks/fastapi/core/search/elasticsearch.py.jinja2"
        )

    def test_template_file_exists(self):
        """Test template file ton tai."""
        self.assertTrue(
            self.template_path.exists(),
            "Elasticsearch config khong ton tai",
        )

    def test_template_has_elasticsearch_import(self):
        """Test template co Elasticsearch imports."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("elasticsearch", content.lower())

    def test_template_has_async_support(self):
        """Test template co async support."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("async", content)

    def test_template_has_tenant_isolation(self):
        """Test template co tenant isolation (KPI-029)."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("tenant", content.lower())


class TestFastApiSearchService(TestCase):
    """Test FastAPI search service template."""

    def setUp(self):
        """Thiet lap test fixtures."""
        self.template_path = Path(
            "midicoder/stacks/fastapi/core/search/search_service.py.jinja2"
        )

    def test_template_file_exists(self):
        """Test template file ton tai."""
        self.assertTrue(
            self.template_path.exists(),
            "Search service khong ton tai",
        )

    def test_template_has_search_method(self):
        """Test template co search method."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("search", content.lower())

    def test_template_has_tenant_isolation(self):
        """Test template co tenant filtering (KPI-029)."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("tenant", content.lower())


class TestFastApiIndexManager(TestCase):
    """Test FastAPI index manager template."""

    def setUp(self):
        """Thiet lap test fixtures."""
        self.template_path = Path(
            "midicoder/stacks/fastapi/core/search/index_manager.py.jinja2"
        )

    def test_template_file_exists(self):
        """Test template file ton tai."""
        self.assertTrue(
            self.template_path.exists(),
            "Index manager khong ton tai",
        )

    def test_template_has_create_index(self):
        """Test template co create_index method."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("create", content.lower())

    def test_template_has_tenant_isolation(self):
        """Test template co tenant isolation (KPI-029)."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("tenant", content.lower())


class TestNestJsSearchModule(TestCase):
    """Test NestJS search module template."""

    def setUp(self):
        """Thiet lap test fixtures."""
        self.template_path = Path(
            "midicoder/stacks/nestjs/core/search/search.module.ts.jinja2"
        )

    def test_template_file_exists(self):
        """Test template file ton tai."""
        self.assertTrue(
            self.template_path.exists(),
            "Search module khong ton tai",
        )

    def test_template_has_nestjs_module(self):
        """Test template co NestJS @Module."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("@Module", content) or self.assertIn("Module", content)

    def test_template_has_elasticsearch(self):
        """Test template co Elasticsearch."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn(
            "elasticsearch", content.lower()
        ) or self.assertIn("Elasticsearch", content)


class TestNestJsSearchService(TestCase):
    """Test NestJS search service template."""

    def setUp(self):
        """Thiet lap test fixtures."""
        self.template_path = Path(
            "midicoder/stacks/nestjs/core/search/search.service.ts.jinja2"
        )

    def test_template_file_exists(self):
        """Test template file ton tai."""
        self.assertTrue(
            self.template_path.exists(),
            "Search service khong ton tai",
        )

    def test_template_has_search_method(self):
        """Test template co search method."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("search", content.lower())

    def test_template_has_async(self):
        """Test template co async methods."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("async", content)


class TestNestJsSearchDecorators(TestCase):
    """Test NestJS search decorators template."""

    def setUp(self):
        """Thiet lap test fixtures."""
        self.template_path = Path(
            "midicoder/stacks/nestjs/core/search/search.decorators.ts.jinja2"
        )

    def test_template_file_exists(self):
        """Test template file ton tai."""
        self.assertTrue(
            self.template_path.exists(),
            "Search decorators khong ton tai",
        )

    def test_template_has_index_decorator(self):
        """Test template co @SearchIndex decorator."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("SearchIndex", content)


class TestAngularSearchService(TestCase):
    """Test Angular search service template."""

    def setUp(self):
        """Thiet lap test fixtures."""
        self.template_path = Path(
            "midicoder/stacks/angular/core/search/search.service.ts.jinja2"
        )

    def test_template_file_exists(self):
        """Test template file ton tai."""
        self.assertTrue(
            self.template_path.exists(),
            "Angular Search service khong ton tai",
        )

    def test_template_has_injectable(self):
        """Test template co @Injectable."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("@Injectable", content)

    def test_template_has_http_client(self):
        """Test template co HttpClient."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("HttpClient", content)

    def test_template_has_tenant_isolation(self):
        """Test template co tenant isolation (KPI-029)."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("tenant", content.lower())


class TestAngularSearchModule(TestCase):
    """Test Angular search module template."""

    def setUp(self):
        """Thiet lap test fixtures."""
        self.template_path = Path(
            "midicoder/stacks/angular/core/search/search.module.ts.jinja2"
        )

    def test_template_file_exists(self):
        """Test template file ton tai."""
        self.assertTrue(
            self.template_path.exists(),
            "Angular Search module khong ton tai",
        )

    def test_template_has_ngmodule(self):
        """Test template co @NgModule."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("@NgModule", content)


class TestReactSearchProvider(TestCase):
    """Test React SearchProvider template."""

    def setUp(self):
        """Thiet lap test fixtures."""
        self.template_path = Path(
            "midicoder/stacks/react/core/search/SearchProvider.tsx.jinja2"
        )

    def test_template_file_exists(self):
        """Test template file ton tai."""
        self.assertTrue(
            self.template_path.exists(),
            "React SearchProvider khong ton tai",
        )

    def test_template_has_context(self):
        """Test template co createContext."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("createContext", content)

    def test_template_has_search_method(self):
        """Test template co search method."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("search", content.lower())

    def test_template_has_tenant_isolation(self):
        """Test template co tenant isolation (KPI-029)."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("tenant", content.lower())


class TestReactUseSearch(TestCase):
    """Test React useSearch hook template."""

    def setUp(self):
        """Thiet lap test fixtures."""
        self.template_path = Path(
            "midicoder/stacks/react/core/search/useSearch.ts.jinja2"
        )

    def test_template_file_exists(self):
        """Test template file ton tai."""
        self.assertTrue(
            self.template_path.exists(),
            "React useSearch khong ton tai",
        )

    def test_template_has_usecontext(self):
        """Test template co useContext."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("useContext", content)

    def test_template_has_error_handling(self):
        """Test template co error handling khi dung ben ngoai provider."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("throw", content.lower()) or self.assertIn("Error", content)


# Run tests
if __name__ == "__main__":
    import unittest

    unittest.main()