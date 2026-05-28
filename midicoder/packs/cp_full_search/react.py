# coding: utf-8
"""
React Search Emitter (CP10).

Module nay cung cap ReactEmitter de generate React search code
tu SearchCollection (CP10):
- search.types.ts - TypeScript interfaces
- SearchProvider.tsx - React context provider
- useSearch.ts - Custom hook
- search-utils.ts - Utility functions
- index.ts - Barrel exports

KPI-029: Tenant-aware search qua key prefix.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

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


class ReactEmitter:
    """
    Emitter cho React search code.

    Generate code tu SearchCollection cho:
    - src/search/search.types.ts
    - src/search/SearchProvider.tsx
    - src/search/useSearch.ts
    - src/search/search-utils.ts
    - src/search/index.ts
    """

    def __init__(self, stack_dir: Path | None = None) -> None:
        """Khoi tao ReactEmitter."""
        self.stack_dir = stack_dir

    def emit(
        self,
        collection: SearchCollection,
        output_dir: Path,
    ) -> list[GeneratedFile]:
        """Emit React search code tu SearchCollection."""
        if not collection.indices:
            return []

        files: list[GeneratedFile] = []
        search_dir = output_dir / "src" / "search"
        search_dir.mkdir(parents=True, exist_ok=True)

        files.append(self._emit_types(collection, search_dir))
        files.append(self._emit_search_provider(collection, search_dir))
        files.append(self._emit_use_search(search_dir))
        files.append(self._emit_search_utils(search_dir))
        files.append(self._emit_index(search_dir))

        return files

    def _emit_types(
        self,
        collection: SearchCollection,
        output_dir: Path,
    ) -> GeneratedFile:
        """Emit search.types.ts - TypeScript interfaces."""
        # Sinh danh sach index names
        index_names = [idx.id for idx in collection.indices]
        index_type = " | ".join(f"'{name}'" for name in index_names) if index_names else "'default'"

        content = (
            "/**\n"
            " * Search Types - CP10.\n"
            " *\n"
            " * TypeScript interfaces cho search layer.\n"
            " * KPI-029: Tenant-aware search.\n"
            " */\n\n"
            "/** Index names */\n"
            f"export type SearchIndexName = {index_type};\n\n"
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
            "  index?: SearchIndexName;\n"
            "  size?: number;\n"
            "  from?: number;\n"
            "  filters?: Record<string, any>;\n"
            "  sort?: Array<{ field: string; order?: 'asc' | 'desc' }>;\n"
            "  highlight?: boolean;\n"
            "  tenantId?: string;  // KPI-029\n"
            "}\n\n"
            "/** Config cho SearchProvider */\n"
            "export interface SearchContextConfig {\n"
            "  apiUrl: string;\n"
            "  defaultIndex?: SearchIndexName;\n"
            "  tenantId?: string;\n"
            "}\n\n"
            "/** Context type */\n"
            "export interface SearchContextType {\n"
            "  search: <T = any>(options: SearchOptions) => Promise<SearchResult<T>>;\n"
            "  indexDocument: <T = any>(index: SearchIndexName, id: string, document: T) => Promise<void>;\n"
            "  deleteDocument: (index: SearchIndexName, id: string) => Promise<void>;\n"
            "  tenantId: string | undefined;\n"
            "  setTenantId: (id: string | undefined) => void;\n"
            "}\n"
        )

        file_path = output_dir / "search.types.ts"
        file_path.write_text(content, encoding="utf-8")
        return GeneratedFile(
            path=file_path, content=content,
            template="search/search.types.ts.jinja2", capability="CP10",
        )

    def _emit_search_provider(
        self,
        collection: SearchCollection,
        output_dir: Path,
    ) -> GeneratedFile:
        """Emit SearchProvider.tsx."""
        default_index = collection.indices[0].id if collection.indices else "default"

        content = (
            "/**\n"
            " * Search Provider - CP10.\n"
            " *\n"
            " * React context de cung cap search capabilities.\n"
            " * KPI-029: Tenant-aware search.\n"
            " */\n\n"
            "import {\n"
            "  createContext,\n"
            "  useContext,\n"
            "  useState,\n"
            "  useCallback,\n"
            "  ReactNode,\n"
            "} from \"react\";\n"
            'import { SearchContextType, SearchResult, SearchOptions } from "./search.types";\n'
            'import { buildTenantHeader } from "./search-utils";\n\n'
            "const SearchContext = createContext<SearchContextType | undefined>(undefined);\n\n"
            "export interface SearchProviderProps {\n"
            "  children: ReactNode;\n"
            "  apiUrl?: string;\n"
            "  initialTenantId?: string;\n"
            "}\n\n"
            "/** SearchProvider - wrap app de cung cap search context */\n"
            "export function SearchProvider({\n"
            "  children,\n"
            '  apiUrl = "/api/search",\n'
            "  initialTenantId,\n"
            "}: SearchProviderProps) {\n"
            "  const [tenantId, setTenantIdState] = useState<string | undefined>(initialTenantId);\n\n"
            "  /** Thuc hien search (KPI-029: tenant-aware) */\n"
            "  const search = useCallback(async <T = any>(options: SearchOptions): Promise<SearchResult<T>> => {\n"
            "    const headers = buildTenantHeader(tenantId || options.tenantId);\n"
            "    const response = await fetch(apiUrl, {\n"
            "      method: \"POST\",\n"
            "      headers,\n"
            "      body: JSON.stringify(options),\n"
            "    });\n"
            "    return response.json();\n"
            "  }, [apiUrl, tenantId]);\n\n"
            "  /** Index document (KPI-029: tenant-aware) */\n"
            "  const indexDocument = useCallback(async <T = any>(\n"
            f'    index: string = "{default_index}",\n'
            "    id: string,\n"
            "    document: T,\n"
            "  ): Promise<void> => {\n"
            "    const headers = buildTenantHeader(tenantId);\n"
            "    headers.set(\"Content-Type\", \"application/json\");\n"
            "    await fetch(`${apiUrl}/${index}/${id}`, {\n"
            "      method: \"PUT\",\n"
            "      headers,\n"
            "      body: JSON.stringify(document),\n"
            "    });\n"
            "  }, [apiUrl, tenantId]);\n\n"
            "  /** Xoa document (KPI-029: tenant-aware) */\n"
            "  const deleteDocument = useCallback(async (\n"
            f'    index: string = "{default_index}",\n'
            "    id: string,\n"
            "  ): Promise<void> => {\n"
            "    const headers = buildTenantHeader(tenantId);\n"
            "    await fetch(`${apiUrl}/${index}/${id}`, {\n"
            "      method: \"DELETE\",\n"
            "      headers,\n"
            "    });\n"
            "  }, [apiUrl, tenantId]);\n\n"
            "  /** Dat tenant ID (KPI-029) */\n"
            "  const setTenantId = useCallback((id: string | undefined) => {\n"
            "    setTenantIdState(id);\n"
            "  }, []);\n\n"
            "  const value: SearchContextType = {\n"
            "    search,\n"
            "    indexDocument,\n"
            "    deleteDocument,\n"
            "    tenantId,\n"
            "    setTenantId,\n"
            "  };\n\n"
            "  return (\n"
            "    <SearchContext.Provider value={value}>\n"
            "      {children}\n"
            "    </SearchContext.Provider>\n"
            "  );\n"
            "}\n\n"
            "export { SearchContext };\n"
        )

        file_path = output_dir / "SearchProvider.tsx"
        file_path.write_text(content, encoding="utf-8")
        return GeneratedFile(
            path=file_path, content=content,
            template="search/SearchProvider.tsx.jinja2", capability="CP10",
        )

    def _emit_use_search(self, output_dir: Path) -> GeneratedFile:
        """Emit useSearch.ts - Custom hook."""
        content = (
            "/**\n"
            " * useSearch Hook - CP10.\n"
            " *\n"
            " * Custom hook de su dung search tu SearchProvider context.\n"
            " * KPI-029: Tenant-aware search.\n"
            " */\n\n"
            "import { useContext } from \"react\";\n"
            'import { SearchContext } from "./SearchProvider";\n'
            'import { SearchContextType } from "./search.types";\n\n'
            "/**\n"
            " * Hook de truy cap search operations.\n"
            " *\n"
            " * @throws Error neu dung ben ngoai SearchProvider\n"
            " *\n"
            " * @example\n"
            " *   const { search, indexDocument } = useSearch();\n"
            " *   const results = await search({ query: 'laptop' });\n"
            " */\n"
            "export function useSearch(): SearchContextType {\n"
            "  const context = useContext(SearchContext);\n\n"
            "  if (context === undefined) {\n"
            '    throw new Error("useSearch phai dung ben trong SearchProvider");\n'
            "  }\n\n"
            "  return context;\n"
            "}\n"
        )

        file_path = output_dir / "useSearch.ts"
        file_path.write_text(content, encoding="utf-8")
        return GeneratedFile(
            path=file_path, content=content,
            template="search/useSearch.ts.jinja2", capability="CP10",
        )

    def _emit_search_utils(self, output_dir: Path) -> GeneratedFile:
        """Emit search-utils.ts."""
        content = (
            "/**\n"
            " * Search Utilities - CP10.\n"
            " *\n"
            " * Helper functions cho search operations.\n"
            " * KPI-029: Tenant-aware header building.\n"
            " */\n\n"
            "/**\n"
            " * Xay dung headers voi tenant ID (KPI-029).\n"
            " *\n"
            " * @param tenantId Tenant ID (optional)\n"
            " * @returns Headers object voi x-tenant-id neu co\n"
            " */\n"
            "export function buildTenantHeader(tenantId?: string): Headers {\n"
            "  const headers = new Headers();\n"
            "  headers.set(\"Content-Type\", \"application/json\");\n"
            "  if (tenantId) {\n"
            '    headers.set("x-tenant-id", tenantId);\n'
            "  }\n"
            "  return headers;\n"
            "}\n\n"
            "/**\n"
            " * Build search query string.\n"
            " */\n"
            "export function buildSearchQuery(\n"
            "  query: string,\n"
            "  index?: string,\n"
            "  size?: number,\n"
            "  from?: number,\n"
            "): URLSearchParams {\n"
            "  const params = new URLSearchParams();\n"
            "  params.set(\"q\", query);\n"
            "  if (index) params.set(\"index\", index);\n"
            "  if (size) params.set(\"size\", String(size));\n"
            "  if (from) params.set(\"from\", String(from));\n"
            "  return params;\n"
            "}\n"
        )

        file_path = output_dir / "search-utils.ts"
        file_path.write_text(content, encoding="utf-8")
        return GeneratedFile(
            path=file_path, content=content,
            template="search/search-utils.ts.jinja2", capability="CP10",
        )

    def _emit_index(self, output_dir: Path) -> GeneratedFile:
        """Emit index.ts."""
        content = (
            "/**\n"
            " * Search Module Exports - CP10.\n"
            " */\n"
            'export * from "./search.types";\n'
            'export * from "./SearchProvider";\n'
            'export * from "./useSearch";\n'
            'export * from "./search-utils";\n'
        )

        file_path = output_dir / "index.ts"
        file_path.write_text(content, encoding="utf-8")
        return GeneratedFile(
            path=file_path, content=content,
            template="search/index.ts.jinja2", capability="CP10",
        )
