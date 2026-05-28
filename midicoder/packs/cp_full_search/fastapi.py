# coding: utf-8
"""
FastAPI Search Emitter (CP10).

Module nay cung cap FastAPISearchEmitter de generate FastAPI search code
tu SearchCollection (CP10):
- elasticsearch.py - ES client config (tenant-aware)
- search_service.py - Full-text search service
- index_manager.py - CRUD index operations

KPI-029: Tenant-aware caching qua key prefix.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from midicoder.packs.cp_full_search.models import SearchCollection, SearchIndex
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# ============================================================================
# Generated File
# ============================================================================


@dataclass
class GeneratedFile:
    """
    File da generate tu emitter.

    Attributes:
        path: Duong dan file
        content: Noi dung file
        template: Ten template
        capability: Core Capability code (CP10)
    """
    path: Path
    content: str
    template: str
    capability: str


# ============================================================================
# FastAPI Search Emitter
# ============================================================================


class FastAPISearchEmitter:
    """
    Emitter cho FastAPI search code.

    Generate code tu SearchCollection cho:
    - search/elasticsearch.py
    - search/search_service.py
    - search/index_manager.py
    """

    def __init__(self, stack_dir: Path | None = None) -> None:
        """
        Khoi tao FastAPISearchEmitter.

        Args:
            stack_dir: Duong dan den templates directory (optional)
        """
        self.stack_dir = stack_dir

    def emit(
        self,
        collection: SearchCollection,
        output_dir: Path,
    ) -> list[GeneratedFile]:
        """
        Emit FastAPI search code tu SearchCollection.

        Args:
            collection: SearchCollection instance
            output_dir: Output directory

        Returns:
            List of GeneratedFile instances
        """
        if not collection.indices:
            return []

        files: list[GeneratedFile] = []
        search_dir = output_dir / "search"
        search_dir.mkdir(parents=True, exist_ok=True)

        files.append(self._emit_elasticsearch_config(collection, search_dir))
        files.append(self._emit_search_service(collection, search_dir))
        files.append(self._emit_index_manager(collection, search_dir))
        files.append(self._emit_init(search_dir))

        return files

    def _emit_elasticsearch_config(
        self,
        collection: SearchCollection,
        output_dir: Path,
    ) -> GeneratedFile:
        """Sinh elasticsearch.py - ES client config voi tenant awareness."""
        # Xay danh sach providers tu collection
        has_elasticsearch = any(
            idx.provider.value == "elasticsearch" for idx in collection.indices
        )
        has_meilisearch = any(
            idx.provider.value == "meilisearch" for idx in collection.indices
        )

        # Xay danh sach index names
        index_names = [idx.id for idx in collection.indices]
        index_lines = ", ".join(f"'{name}'" for name in index_names)

        # KPI-029: Tenant isolation config
        has_tenant_isolation = any(idx.tenant_isolated for idx in collection.indices)

        content = (
            '"""\\\n'
            "Elasticsearch Configuration cho FastAPI.\n"
            "\n"
            "Cung cap:\n"
            "- Async Elasticsearch client\n"
            "- Index management\n"
            "- Search operations\n"
        )
        if has_tenant_isolation:
            content += "- KPI-029: Tenant-specific index prefix\n"
        content += (
            '"""\\\n'
            "\n"
            "import os\n"
            "from typing import Optional\n"
            "\n"
        )
        if has_elasticsearch:
            content += "from elasticsearch import AsyncElasticsearch\n"
        if has_meilisearch:
            content += "from meilisearch import AsyncClient as MeiliSearchAsyncClient\n"

        content += (
            "\n"
            f"# Danh sach indices da cau hinh: {index_lines}\n"
            "# Elasticsearch URL tu environment\n"
            'ELASTICSEARCH_URL = os.getenv(\n'
            '    "ELASTICSEARCH_URL",\n'
            '    "http://localhost:9200",\n'
            ")\n"
            "\n"
            "# Connection settings\n"
            'ES_MAX_RETRIES = int(os.getenv("ES_MAX_RETRIES", "3"))\n'
            'ES_TIMEOUT = int(os.getenv("ES_TIMEOUT", "30"))\n'
            'ES_SNIFF_ON_START = os.getenv("ES_SNIFF_ON_START", "false").lower() == "true"\n'
            "\n"
        )

        if has_tenant_isolation:
            content += (
                "# KPI-029: Tenant index prefix settings\n"
                'ES_TENANT_INDEX_PREFIX = os.getenv("ES_TENANT_INDEX_PREFIX", "tenant")\n'
                'ES_TENANT_ISOLATION = os.getenv("ES_TENANT_ISOLATION", "true").lower() == "true"\n'
                "\n"
            )

        content += (
            "# Async Elasticsearch client\n"
            "_es_client: Optional[Any] = None\n"
            "\n"
            "# KPI-029: Tenant-specific clients cache\n"
            "_tenant_es_clients: dict[str, Any] = {}\n"
            "\n"
            "\n"
            "def get_elasticsearch() -> Any:\n"
            '    """Tao hoac tra ve async Elasticsearch client."""\n'
            "    global _es_client\n"
            "\n"
            "    if _es_client is None:\n"
            "        _es_client = AsyncElasticsearch(\n"
            "            hosts=[ELASTICSEARCH_URL],\n"
            "            max_retries=ES_MAX_RETRIES,\n"
            "            retry_on_timeout=True,\n"
            "            timeout=ES_TIMEOUT,\n"
            "            sniff_on_start=ES_SNIFF_ON_START,\n"
            "        )\n"
            "\n"
            "    return _es_client\n"
            "\n"
            "\n"
        )

        if has_tenant_isolation:
            content += (
                "def get_tenant_elasticsearch(tenant_id: str) -> Any:\n"
                '    """KPI-029: Tao hoac tra ve async Elasticsearch client cho tenant."""\n'
                "    global _tenant_es_clients\n"
                "\n"
                "    if tenant_id not in _tenant_es_clients:\n"
                "        _tenant_es_clients[tenant_id] = AsyncElasticsearch(\n"
                "            hosts=[ELASTICSEARCH_URL],\n"
                "            max_retries=ES_MAX_RETRIES,\n"
                "            retry_on_timeout=True,\n"
                "            timeout=ES_TIMEOUT,\n"
                "            sniff_on_start=ES_SNIFF_ON_START,\n"
                "        )\n"
                "\n"
                "    return _tenant_es_clients[tenant_id]\n"
                "\n"
                "\n"
                "def get_tenant_index_name(base_index: str, tenant_id: Optional[str] = None) -> str:\n"
                '    """KPI-029: Tao index name voi tenant prefix."""\n'
                "    if not ES_TENANT_ISOLATION or not tenant_id:\n"
                "        return base_index\n"
                "\n"
                '    return f"{ES_TENANT_INDEX_PREFIX}_{tenant_id}_{base_index}"\n'
                "\n"
                "\n"
            )

        content += (
            "async def es_health_check() -> bool:\n"
            '    """Kiem tra Elasticsearch health."""\n'
            "    client = get_elasticsearch()\n"
            "    try:\n"
            "        await client.ping()\n"
            "        return True\n"
            "    except Exception:\n"
            "        return False\n"
            "\n"
            "\n"
            "async def close_elasticsearch() -> None:\n"
            '    """Dong Elasticsearch connection."""\n'
            "    global _es_client\n"
            "\n"
            "    if _es_client:\n"
            "        await _es_client.close()\n"
            "        _es_client = None\n"
        )

        file_path = output_dir / "elasticsearch.py"
        file_path.write_text(content, encoding="utf-8")
        return GeneratedFile(
            path=file_path, content=content,
            template="search/elasticsearch.py.jinja2", capability="CP10",
        )

    def _emit_search_service(
        self,
        collection: SearchCollection,
        output_dir: Path,
    ) -> GeneratedFile:
        """Sinh search_service.py - Full-text search service."""
        has_tenant = any(idx.tenant_isolated for idx in collection.indices)

        content = (
            '"""\\\n'
            "Search Service cho FastAPI.\n"
            "\n"
            "Cung cap:\n"
            "- Full-text search\n"
            "- Filtering & sorting\n"
            "- Pagination\n"
        )
        if has_tenant:
            content += "- KPI-029: Tenant-specific search filtering\n"
        content += (
            '"""\\\n'
            "\n"
            "from typing import Any, Dict, List, Optional\n"
            "\n"
            "from .elasticsearch import get_elasticsearch"
        )
        if has_tenant:
            content += ", get_tenant_elasticsearch, get_tenant_index_name"
        content += "\n\n"

        content += (
            "class SearchService:\n"
            '    """Service cho Elasticsearch search operations."""\n'
            "\n"
            "    def __init__(self, index: str = \"documents\", tenant_id: Optional[str] = None) -> None:\n"
            '        """Khoi tao search service."""\n'
            "        self.index = index\n"
            "        self.tenant_id = tenant_id\n"
            "\n"
            "    async def search(\n"
            "        self,\n"
            "        query: str,\n"
            "        index: Optional[str] = None,\n"
            "        filters: Optional[Dict[str, Any]] = None,\n"
            "        sort: Optional[List[str]] = None,\n"
            "        size: int = 20,\n"
            "        from_page: int = 0,\n"
            "        highlight: bool = False,\n"
            "        tenant_id: Optional[str] = None,\n"
            "    ) -> Dict[str, Any]:\n"
            '        """Thuc hien full-text search."""\n'
        )

        if has_tenant:
            content += (
                "        effective_tenant_id = tenant_id or self.tenant_id\n"
                "        target_index = get_tenant_index_name(index or self.index, effective_tenant_id)\n"
                "        client = get_tenant_elasticsearch(effective_tenant_id) if effective_tenant_id else get_elasticsearch()\n"
                "\n"
            )
        else:
            content += (
                "        target_index = index or self.index\n"
                "        client = get_elasticsearch()\n"
                "\n"
            )

        content += (
            "        search_body = {\n"
            "            \"query\": {\n"
            "                \"multi_match\": {\n"
            "                    \"query\": query,\n"
            "                    \"fields\": [\"*\"],\n"
            "                    \"fuzziness\": \"AUTO\",\n"
            "                }\n"
            "            },\n"
            "            \"size\": size,\n"
            "            \"from\": from_page,\n"
            "        }\n"
            "\n"
            "        if filters:\n"
            '            search_body["query"] = {\n'
            '                "bool": {\n'
            '                    "must": [search_body["query"]],\n'
            '                    "filter": [{"term": {k: v}} for k, v in filters.items()],\n'
            "                }\n"
            "            }\n"
            "\n"
            "        if sort:\n"
            '            search_body["sort"] = [{"field": s} for s in sort]\n'
            "\n"
            "        if highlight:\n"
            '            search_body["highlight"] = {"fields": {"*": {}}}\n'
            "\n"
            "        response = await client.search(index=target_index, body=search_body)\n"
            "\n"
            "        return {\n"
            '            "hits": response["hits"]["hits"],\n'
            '            "total": response["hits"]["total"]["value"],\n'
            '            "took": response["took"],\n'
            "        }\n"
        )

        file_path = output_dir / "search_service.py"
        file_path.write_text(content, encoding="utf-8")
        return GeneratedFile(
            path=file_path, content=content,
            template="search/search_service.py.jinja2", capability="CP10",
        )

    def _emit_index_manager(
        self,
        collection: SearchCollection,
        output_dir: Path,
    ) -> GeneratedFile:
        """Sinh index_manager.py - CRUD index operations."""
        has_tenant = any(idx.tenant_isolated for idx in collection.indices)

        content = (
            '"""\\\n'
            "Index Manager cho Elasticsearch.\n"
            "\n"
            "Cung cap:\n"
            "- Create/delete index\n"
            "- Manage mappings\n"
            "- Index lifecycle management\n"
        )
        if has_tenant:
            content += "- KPI-029: Tenant-specific index operations\n"
        content += (
            '"""\\\n'
            "\n"
            "from typing import Any, Dict, Optional\n"
            "\n"
            "from .elasticsearch import get_elasticsearch"
        )
        if has_tenant:
            content += ", get_tenant_elasticsearch, get_tenant_index_name"
        content += "\n\n"

        content += (
            "class IndexManager:\n"
            '    """Manager cho Elasticsearch index operations."""\n'
            "\n"
        )
        if has_tenant:
            content += "    def __init__(self, tenant_id: Optional[str] = None) -> None:\n"
            "        self.tenant_id = tenant_id\n"
            "\n"
        else:
            content += "    def __init__(self) -> None:\n"
            "        pass\n"
            "\n"

        content += (
            "    async def create_index(\n"
            "        self,\n"
            "        name: str,\n"
            "        mapping: Optional[Dict[str, Any]] = None,\n"
            "        settings: Optional[Dict[str, Any]] = None,\n"
        )
        if has_tenant:
            content += "        tenant_id: Optional[str] = None,\n"
        content += (
            "    ) -> Dict[str, Any]:\n"
            '        """Tao Elasticsearch index."""\n'
        )
        if has_tenant:
            content += (
                "        effective_tenant_id = tenant_id or self.tenant_id\n"
                "        index_name = get_tenant_index_name(name, effective_tenant_id)\n"
                "        client = get_tenant_elasticsearch(effective_tenant_id) if effective_tenant_id else get_elasticsearch()\n"
            )
        else:
            content += (
                "        index_name = name\n"
                "        client = get_elasticsearch()\n"
            )
        content += (
            "\n"
            "        body = {}\n"
            "        if mapping:\n"
            '            body["mappings"] = mapping\n'
            "        if settings:\n"
            '            body["settings"] = settings\n'
            "\n"
            "        return await client.indices.create(index=index_name, body=body)\n"
            "\n"
            "    async def delete_index(self, name: str"
        )
        if has_tenant:
            content += ", tenant_id: Optional[str] = None"
        content += (
            ") -> Dict[str, Any]:\n"
            '        """Xoa Elasticsearch index."""\n'
        )
        if has_tenant:
            content += (
                "        effective_tenant_id = tenant_id or self.tenant_id\n"
                "        index_name = get_tenant_index_name(name, effective_tenant_id)\n"
                "        client = get_tenant_elasticsearch(effective_tenant_id) if effective_tenant_id else get_elasticsearch()\n"
            )
        else:
            content += "        client = get_elasticsearch()\n"
        content += "        return await client.indices.delete(index=index_name)\n"

        file_path = output_dir / "index_manager.py"
        file_path.write_text(content, encoding="utf-8")
        return GeneratedFile(
            path=file_path, content=content,
            template="search/index_manager.py.jinja2", capability="CP10",
        )

    def _emit_init(self, output_dir: Path) -> GeneratedFile:
        """Sinh __init__.py."""
        content = '"""Search package - auto-generated by Midicoder CE."""\n'
        file_path = output_dir / "__init__.py"
        file_path.write_text(content, encoding="utf-8")
        return GeneratedFile(
            path=file_path, content=content,
            template="search/__init__.py.jinja2", capability="CP10",
        )
