# coding: utf-8
"""
NestJS Search Emitter (CP10).

Module nay cung cap NestJSSearchEmitter de generate NestJS search code
tu SearchCollection (CP10):
- search.module.ts - NestJS SearchModule
- search.service.ts - SearchService
- search.decorators.ts - Search decorators

KPI-029: Tenant-aware qua tenant-specific indices.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from midicoder.packs.cp_full_search.models import SearchCollection


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


class NestJSSearchEmitter:
    """
    Emitter cho NestJS search code.

    Generate code tu SearchCollection cho:
    - search/search.module.ts
    - search/search.service.ts
    - search/search.decorators.ts
    """

    def __init__(self, stack_dir: Path | None = None) -> None:
        """Khoi tao NestJSSearchEmitter."""
        self.stack_dir = stack_dir

    def emit(
        self,
        collection: SearchCollection,
        output_dir: Path,
    ) -> list[GeneratedFile]:
        """Emit NestJS search code tu SearchCollection."""
        if not collection.indices:
            return []

        files: list[GeneratedFile] = []
        search_dir = output_dir / "search"
        search_dir.mkdir(parents=True, exist_ok=True)

        files.append(self._emit_search_module(collection, search_dir))
        files.append(self._emit_search_service(collection, search_dir))
        files.append(self._emit_search_decorators(search_dir))

        return files

    def _emit_search_module(
        self,
        collection: SearchCollection,
        output_dir: Path,
    ) -> GeneratedFile:
        """Sinh search.module.ts."""
        content = (
            "/**\n"
            " * Search Module cho NestJS.\n"
            " *\n"
            " * Cau hinh Elasticsearch client va search services.\n"
            " * KPI-029: Tenant Isolation - Ho tro tenant-specific index configuration\n"
            " */\n\n"
            "import { Module } from \"@nestjs/common\";\n"
            "import { SearchService } from \"./search.service\";\n\n"
            "@Module({\n"
            "  providers: [SearchService],\n"
            "  exports: [SearchService],\n"
            "})\n"
            "export class SearchModule {}\n"
        )

        file_path = output_dir / "search.module.ts"
        file_path.write_text(content, encoding="utf-8")
        return GeneratedFile(
            path=file_path, content=content,
            template="search/search.module.ts.jinja2", capability="CP10",
        )

    def _emit_search_service(
        self,
        collection: SearchCollection,
        output_dir: Path,
    ) -> GeneratedFile:
        """Sinh search.service.ts."""
        content = (
            "/**\n"
            " * Search Service cho NestJS.\n"
            " *\n"
            " * Cung cap Elasticsearch search operations:\n"
            " * - Full-text search\n"
            " * - Document indexing\n"
            " * - Bulk operations\n"
            " *\n"
            " * KPI-029: Tenant Isolation - Ho tro tenant filtering\n"
            " */\n\n"
            "import { Injectable } from \"@nestjs/common\";\n"
            "import { Client } from \"@elastic/elasticsearch\";\n\n"
            "@Injectable()\n"
            "export class SearchService {\n"
            "  private readonly esClient: Client;\n\n"
            "  constructor() {\n"
            "    this.esClient = new Client({\n"
            "      node: process.env.ELASTICSEARCH_URL || 'http://localhost:9200',\n"
            "    });\n"
            "  }\n\n"
            "  // KPI-029: Tenant-aware index name building\n"
            "  private getIndexName(index: string, tenantId?: string): string {\n"
            "    return tenantId ? `${tenantId}_${index}` : index;\n"
            "  }\n\n"
            "  async search(index: string, query: string, tenantId?: string): Promise<unknown> {\n"
            "    const indexName = this.getIndexName(index, tenantId);\n"
            "    return this.esClient.search({ index: indexName, body: { query: { match: { _all: query } } } });\n"
            "  }\n\n"
            "  async indexDocument(index: string, id: string, doc: unknown, tenantId?: string): Promise<void> {\n"
            "    const indexName = this.getIndexName(index, tenantId);\n"
            "    await this.esClient.index({ index: indexName, id, body: doc });\n"
            "  }\n\n"
            "  async deleteDocument(index: string, id: string, tenantId?: string): Promise<void> {\n"
            "    const indexName = this.getIndexName(index, tenantId);\n"
            "    await this.esClient.delete({ index: indexName, id });\n"
            "  }\n"
            "}\n"
        )

        file_path = output_dir / "search.service.ts"
        file_path.write_text(content, encoding="utf-8")
        return GeneratedFile(
            path=file_path, content=content,
            template="search/search.service.ts.jinja2", capability="CP10",
        )

    def _emit_search_decorators(
        self,
        output_dir: Path,
    ) -> GeneratedFile:
        """Sinh search.decorators.ts."""
        content = (
            "/**\n"
            " * Search Decorators cho NestJS.\n"
            " *\n"
            " * Decorators de annotate entities cho Elasticsearch indexing.\n"
            " * KPI-029: Tenant Isolation\n"
            " */\n\n"
            "import { SetMetadata } from \"@nestjs/common\";\n\n"
            "export const SEARCH_INDEX = \"searchIndex\";\n"
            "export const SEARCH_FIELD = \"searchField\";\n\n"
            "export function SearchIndex(config: {\n"
            "  index: string;\n"
            "  tenantPrefix?: string;\n"
            "}) {\n"
            '  return SetMetadata(SEARCH_INDEX, config);\n'
            "}\n\n"
            "export function SearchField(options: {\n"
            '  type: "text" | "keyword" | "integer" | "date";\n'
            "}) {\n"
            '  return SetMetadata(SEARCH_FIELD, options);\n'
            "}\n"
        )

        file_path = output_dir / "search.decorators.ts"
        file_path.write_text(content, encoding="utf-8")
        return GeneratedFile(
            path=file_path, content=content,
            template="search/search.decorators.ts.jinja2", capability="CP10",
        )
