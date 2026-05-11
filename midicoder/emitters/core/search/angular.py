# coding: utf-8
"""
Angular Search Emitter (CP10).

Module nay cung cap AngularEmitter de generate Angular search code
tu SearchCollection (CP10):
- search.models.ts - TypeScript interfaces cho search
- search.service.ts - SearchService (HTTP client wrapper)
- search.module.ts - SearchNgModule
- index.ts - Barrel exports

KPI-029: Tenant-aware search qua key prefix.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from midicoder.emitters.core.search.models import SearchCollection


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


class AngularEmitter:
    """
    Emitter cho Angular search code.

    Generate code tu SearchCollection cho:
    - src/app/core/search/search.models.ts
    - src/app/core/search/search.service.ts
    - src/app/core/search/search.module.ts
    - src/app/core/search/index.ts
    """

    def __init__(self, stack_dir: Path | None = None) -> None:
        """Khoi tao AngularEmitter."""
        self.stack_dir = stack_dir

    def emit(
        self,
        collection: SearchCollection,
        output_dir: Path,
    ) -> list[GeneratedFile]:
        """Emit Angular search code tu SearchCollection."""
        if not collection.indices:
            return []

        files: list[GeneratedFile] = []
        search_dir = output_dir / "src" / "app" / "core" / "search"
        search_dir.mkdir(parents=True, exist_ok=True)

        files.append(self._emit_models(search_dir))
        files.append(self._emit_search_service(collection, search_dir))
        files.append(self._emit_search_module(search_dir))
        files.append(self._emit_index(search_dir))

        return files

    def _emit_models(self, output_dir: Path) -> GeneratedFile:
        """Emit search.models.ts - TypeScript interfaces cho search."""
        content = (
            "/**\n"
            " * Search Models - CP10.\n"
            " *\n"
            " * TypeScript interfaces cho search layer.\n"
            " * KPI-029: Tenant-aware search.\n"
            " */\n\n"
            "/** Ket qua tu search operation */\n"
            "export interface SearchResult<T = any> {\n"
            "  hits: Array<{\n"
            "    _id: string;\n"
            "    _source: T;\n"
            "    _score: number;\n"
            "  }>;\n"
            "  total: number;\n"
            "  took: number;\n"
            "}\n\n"
            "/** Tu search query */\n"
            "export interface SearchOptions {\n"
            "  query: string;\n"
            "  index?: string;\n"
            "  size?: number;\n"
            "  from?: number;\n"
            "  filters?: Record<string, any>;\n"
            "  sort?: Array<{ field: string; order?: 'asc' | 'desc' }>;\n"
            "  highlight?: boolean;\n"
            "  tenantId?: string;  // KPI-029\n"
            "}\n\n"
            "/** Index search */\n"
            "export interface SearchIndexConfig {\n"
            "  id: string;\n"
            "  provider: 'elasticsearch' | 'meilisearch';\n"
            "  tenant_isolated: boolean;\n"
            "  sync_strategy: 'realtime' | 'near_realtime' | 'batch';\n"
            "}\n"
        )

        file_path = output_dir / "search.models.ts"
        file_path.write_text(content, encoding="utf-8")
        return GeneratedFile(
            path=file_path, content=content,
            template="search/search.models.ts.jinja2", capability="CP10",
        )

    def _emit_search_service(
        self,
        collection: SearchCollection,
        output_dir: Path,
    ) -> GeneratedFile:
        """Emit search.service.ts."""
        # Sinh danh sach index names
        index_names = [idx.id for idx in collection.indices]
        index_type = " | ".join(f"'{name}'" for name in index_names) if index_names else "'default'"

        content = (
            "/**\n"
            " * Search Service - CP10.\n"
            " *\n"
            " * Service nay xu ly search operations cho Angular application.\n"
            " * KPI-029: Tenant-aware search qua header x-tenant-id.\n"
            " */\n\n"
            "import { Injectable } from \"@angular/core\";\n"
            "import { HttpClient, HttpHeaders } from \"@angular/common/http\";\n"
            "import { Observable } from \"rxjs\";\n"
            "import { SearchResult, SearchOptions } from \"./search.models\";\n\n"
            "@Injectable({\n"
            '  providedIn: "root",\n'
            "})\n"
            "export class SearchService {\n"
            '  private searchUrl = \'/api/search\';\n'
            "  private tenantId: string | undefined;\n\n"
            "  constructor(private http: HttpClient) {}\n\n"
            "  /**\n"
            "   * Dat tenant ID cho tenant isolation (KPI-029).\n"
            "   */\n"
            "  setTenantId(tenantId: string | undefined): void {\n"
            "    this.tenantId = tenantId;\n"
            "  }\n\n"
            "  /**\n"
            "   * Thuc hien full-text search.\n"
            "   * KPI-029: Ho tro tenant filtering.\n"
            "   */\n"
            "  search<T = any>(options: SearchOptions): Observable<SearchResult<T>> {\n"
            "    let headers = new HttpHeaders();\n\n"
            "    // KPI-029: Them tenant ID vao header\n"
            "    const tenantId = options.tenantId || this.tenantId;\n"
            "    if (tenantId) {\n"
            '      headers = headers.set("x-tenant-id", tenantId);\n'
            "    }\n\n"
            "    return this.http.post<SearchResult<T>>(\n"
            "      this.searchUrl,\n"
            "      options,\n"
            "      { headers }\n"
            "    );\n"
            "  }\n\n"
            "  /**\n"
            "   * Index mot document.\n"
            "   * KPI-029: Tu dong them tenant_id.\n"
            "   */\n"
            "  indexDocument<T = any>(\n"
            "    index: " + index_type + ",\n"
            "    id: string,\n"
            "    document: T,\n"
            "    tenantId?: string,\n"
            "  ): Observable<{ result: string }> {\n"
            "    let headers = new HttpHeaders();\n"
            "    const tid = tenantId || this.tenantId;\n"
            "    if (tid) {\n"
            '      headers = headers.set("x-tenant-id", tid);\n'
            "    }\n\n"
            "    return this.http.put<{ result: string }>(\n"
            "      `${this.searchUrl}/${index}/${id}`,\n"
            "      document,\n"
            "      { headers }\n"
            "    );\n"
            "  }\n\n"
            "  /**\n"
            "   * Xoa document.\n"
            "   */\n"
            "  deleteDocument(\n"
            "    index: " + index_type + ",\n"
            "    id: string,\n"
            "    tenantId?: string,\n"
            "  ): Observable<{ result: string }> {\n"
            "    let headers = new HttpHeaders();\n"
            "    const tid = tenantId || this.tenantId;\n"
            "    if (tid) {\n"
            '      headers = headers.set("x-tenant-id", tid);\n'
            "    }\n\n"
            "    return this.http.delete<{ result: string }>(\n"
            "      `${this.searchUrl}/${index}/${id}`,\n"
            "      { headers }\n"
            "    );\n"
            "  }\n"
            "}\n"
        )

        file_path = output_dir / "search.service.ts"
        file_path.write_text(content, encoding="utf-8")
        return GeneratedFile(
            path=file_path, content=content,
            template="search/search.service.ts.jinja2", capability="CP10",
        )

    def _emit_search_module(self, output_dir: Path) -> GeneratedFile:
        """Emit search.module.ts."""
        content = (
            "/**\n"
            " * Search Module - CP10.\n"
            " *\n"
            " * Module nay cung cap search services.\n"
            " * KPI-029: Tenant-aware search.\n"
            " */\n\n"
            "import { NgModule } from \"@angular/core\";\n"
            "import { CommonModule } from \"@angular/common\";\n"
            "import { SearchService } from \"./search.service\";\n\n"
            "@NgModule({\n"
            "  imports: [CommonModule],\n"
            "  providers: [SearchService],\n"
            "})\n"
            "export class SearchNgModule {}\n"
        )

        file_path = output_dir / "search.module.ts"
        file_path.write_text(content, encoding="utf-8")
        return GeneratedFile(
            path=file_path, content=content,
            template="search/search.module.ts.jinja2", capability="CP10",
        )

    def _emit_index(self, output_dir: Path) -> GeneratedFile:
        """Emit index.ts."""
        content = (
            "/**\n"
            " * Search Module Exports - CP10.\n"
            " */\n"
            'export * from "./search.models";\n'
            'export * from "./search.service";\n'
            'export * from "./search.module";\n'
        )

        file_path = output_dir / "index.ts"
        file_path.write_text(content, encoding="utf-8")
        return GeneratedFile(
            path=file_path, content=content,
            template="search/index.ts.jinja2", capability="CP10",
        )
