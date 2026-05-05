"""React Client Emitter (P2-002-D).

Module này cung cấp ReactClientEmitter để emit RTK Query API slices
cho React frontend với features:
- RTK Query hooks (auto-generated CRUD)
- Pagination support
- Filtering support
- Built-in caching (RTK Query)
- Error handling

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class GeneratedFile:
    """File đã generate."""
    path: Path
    content: str
    template: str


class ReactClientEmitter:
    """Emitter cho React RTK Query API slices.

    Generate code cho:
    - Entity API Slices (RTK Query hooks)
    - API Error utilities
    - Store configuration

    Usage:
        emitter = ReactClientEmitter()
        files = emitter.emit(entities, output_dir)
    """

    def emit(
        self,
        entities: list[dict[str, Any]],
        output_dir: Path,
    ) -> list[GeneratedFile]:
        """Emit React client API slices.

        Args:
            entities: Danh sách entities với id và fields
            output_dir: Output directory

        Returns:
            List of GeneratedFile instances
        """
        files: list[GeneratedFile] = []

        services_dir = output_dir / "services"
        services_dir.mkdir(parents=True, exist_ok=True)

        # Emit base API slice
        files.extend(self._emit_base_api(services_dir))

        # Emit entity API slices
        for entity in entities:
            files.extend(self._emit_entity_slice(entity, services_dir))

        # Emit error utilities
        files.extend(self._emit_error_utils(services_dir))

        return files

    def _emit_base_api(
        self,
        output_dir: Path,
    ) -> list[GeneratedFile]:
        """Emit base API slice với fetchBaseQuery."""
        content = '''/**
 * Base API Slice - RTK Query API với JWT auth và error handling.
 *
 * Features:
 * - Auto JWT token injection
 * - Base URL configuration
 * - Tag types cho cache invalidation
 */

import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import { RootState } from '../store';

// Tag types cho cache invalidation
export const TAG_TYPES = [
  'Order',
  'Product',
  'User',
  'Config',
] as const;

export const baseApi = createApi({
  reducerPath: 'api',
  baseQuery: fetchBaseQuery({
    baseUrl: '/api',
    prepareHeaders: (headers) => {
      const token = localStorage.getItem('auth_token');
      if (token) {
        headers.set('Authorization', `Bearer ${token}`);
      }
      return headers;
    },
  }),
  /**
   * Cache tags - entity nào được query sẽ có tag.
   * Khi mutate (create/update/delete), tag bị invalidate → cache refetch tự động.
   */
  tagTypes: [...TAG_TYPES],
  endpoints: (builder) => ({}),
});

export default baseApi;
'''
        return [self._write_file("api.ts", content, output_dir)]

    def _emit_entity_slice(
        self,
        entity: dict[str, Any],
        output_dir: Path,
    ) -> list[GeneratedFile]:
        """Emit API slice cho 1 entity."""
        entity_id = entity["id"]
        entity_lower = entity_id.lower()
        entity_plural = f"{entity_lower}s"
        fields = entity.get("fields", [])

        content = self._generate_entity_slice(entity_id, entity_lower, entity_plural, fields)
        filename = f"{entity_lower}-api.ts"

        return [self._write_file(filename, content, output_dir)]

    def _generate_entity_slice(
        self,
        entity_id: str,
        entity_lower: str,
        entity_plural: str,
        fields: list[dict[str, Any]],
    ) -> str:
        """Generate RTK Query API slice cho entity."""
        # Generate TypeScript interface fields
        interface_fields = "\n".join(
            f"  {f['name']}: {self._to_ts_type(f.get('type', 'any'))};" for f in fields
        )

        # Generate filter type fields
        filter_fields = "\n".join(
            f"  {f['name']}?: {self._to_ts_type(f.get('type', 'any'))};" for f in fields
        )

        lines = []
        lines.append('/**')
        lines.append(f' * {entity_id} API Slice - RTK Query hooks cho {entity_id} API.')
        lines.append(' *')
        lines.append(' * Features:')
        lines.append(' * - Auto-generated CRUD hooks')
        lines.append(' * - Pagination support (page/limit)')
        lines.append(' * - Filtering support (dynamic query params)')
        lines.append(' * - Built-in caching với tag invalidation')
        lines.append(' * - Error handling')
        lines.append(' */')
        lines.append('')
        lines.append("import { injectApi } from './api';")
        lines.append('')
        lines.append(f'export interface {entity_id} {{')
        lines.append(interface_fields)
        lines.append('}}')
        lines.append('')
        lines.append(f'export interface Paginated{entity_id} {{')
        lines.append(f'  items: {entity_id}[];')
        lines.append('  total: number;')
        lines.append('  page: number;')
        lines.append('  limit: number;')
        lines.append('  hasMore: boolean;')
        lines.append('}}')
        lines.append('')
        lines.append(f'export interface {entity_id}Filter {{')
        lines.append(filter_fields)
        lines.append('}}')
        lines.append('')
        lines.append(f'export interface List{entity_id}Args {{')
        lines.append(f'  filter?: {entity_id}Filter;')
        lines.append('  page?: number;')
        lines.append('  limit?: number;')
        lines.append('}}')
        lines.append('')
        lines.append('// Inject endpoints vào baseApi')
        lines.append(f'export const {{')
        lines.append(f'  useGet{entity_id}sQuery,')
        lines.append(f'  useGet{entity_id}ByIdQuery,')
        lines.append(f'  useCreate{entity_id}Mutation,')
        lines.append(f'  useUpdate{entity_id}Mutation,')
        lines.append(f'  useDelete{entity_id}Mutation,')
        lines.append('}} = injectApi({')
        lines.append('  inject: (api) => ({')
        lines.append('    endpoints: (build) => ({')
        lines.append('')
        # list endpoint
        lines.append(f'      /** Lấy danh sách {entity_lower} với pagination và filtering. */')
        lines.append(f'      get{entity_id}s: build.query<Paginated{entity_id}, List{entity_id}Args>({{')
        lines.append("        query: ({ filter = {}, page = 1, limit = 20 }) => {")
        lines.append('          const params = new URLSearchParams();')
        lines.append("          params.set('page', String(page));")
        lines.append("          params.set('limit', String(limit));")
        lines.append('          Object.entries(filter).forEach(([key, value]) => {')
        lines.append('            if (value !== undefined && value !== null) {')
        lines.append('              params.set(key, String(value));')
        lines.append('            }')
        lines.append('          })')
        lines.append(f"          return {{")
        lines.append(f"            url: '/{entity_plural}',")
        lines.append('            params,')
        lines.append('          };')
        lines.append('        },')
        lines.append('        transformResponse: (items: Item[]) => ({')
        lines.append('          items,')
        lines.append('          total: items.length,')
        lines.append('          page: args.page ?? 1,')
        lines.append('          limit: args.limit ?? 20,')
        lines.append('          hasMore: items.length >= (args.limit ?? 20),')
        lines.append('        }),')
        lines.append(f'        providesTags: () => [{{ type: \'{entity_id}\', id: \'LIST\' }}],')
        lines.append('      }),')
        lines.append('')
        # getById endpoint
        lines.append(f'      /** Lấy 1 {entity_lower} theo ID. */')
        lines.append(f'      get{entity_id}ById: build.query<{entity_id}, string>({{')
        lines.append(f"        query: (id) => '/{entity_plural}/{{id}}',")
        lines.append(f'        providesTags: (result, error, id) => [')
        lines.append(f"          {{ type: '{entity_id}', id }},")
        lines.append('        ],')
        lines.append('      }),')
        lines.append('')
        # create endpoint
        lines.append(f'      /** Tạo mới {entity_lower}. */')
        lines.append(f'      create{entity_id}: build.mutation<{entity_id}, Partial<{entity_id}>>({{')
        lines.append(f"        query: (body) => ({{")
        lines.append(f"          url: '/{entity_plural}',")
        lines.append('          method: \'POST\',')
        lines.append('          body,')
        lines.append('        }}),')
        lines.append(f'        invalidatesTags: () => [{{ type: \'{entity_id}\', id: \'LIST\' }}],')
        lines.append('      }),')
        lines.append('')
        # update endpoint
        lines.append(f'      /** Cập nhật {entity_lower}. */')
        lines.append(f'      update{entity_id}: build.mutation<{entity_id}, {{ id: string; data: Partial<{entity_id}> }}>({{')
        lines.append(f"        query: ({{ id, data }}) => ({{")
        lines.append(f"          url: '/{entity_plural}/{{id}}',")
        lines.append('          method: \'PUT\',')
        lines.append('          body: data,')
        lines.append('        }}),')
        lines.append(f'        invalidatesTags: (result, error, {{ id }}) => [')
        lines.append(f"          {{ type: '{entity_id}', id }},")
        lines.append(f"          {{ type: '{entity_id}', id: 'LIST' }},")
        lines.append('        ],')
        lines.append('      }),')
        lines.append('')
        # delete endpoint
        lines.append(f'      /** Xóa {entity_lower}. */')
        lines.append(f'      delete{entity_id}: build.mutation<void, string>({{')
        lines.append(f"        query: (id) => ({{")
        lines.append(f"          url: '/{entity_plural}/{{id}}',")
        lines.append("          method: 'DELETE',")
        lines.append('        }}),')
        lines.append(f'        invalidatesTags: () => [{{ type: \'{entity_id}\', id: \'LIST\' }}],')
        lines.append('      }),')
        lines.append('')
        lines.append('    }}),')
        lines.append('  }}),')
        lines.append('}});')
        lines.append('')
        lines.append('type Item = any;')
        lines.append('type Args = ListArgs;')
        lines.append('')

        return '\n'.join(lines)

    def _emit_error_utils(
        self,
        output_dir: Path,
    ) -> list[GeneratedFile]:
        """Emit API error utilities."""
        content = '''/**
 * API Error Utilities - Xử lý lỗi từ RTK Query.
 *
 * Features:
 * - Parse RTK Query errors
 * - Extract error messages
 * - Type guards cho error types
 */

import { SerializedError } from '@reduxjs/toolkit';
import { FetchBaseQueryError } from '@reduxjs/toolkit/query/react';

export interface ApiError {
  code: string;
  message: string;
  status: number;
  timestamp: string;
}

/**
 * Convert RTK Query error thành ApiError.
 */
export function parseApiError(
  error: FetchBaseQueryError | SerializedError | undefined
): ApiError | null {
  if (!error) {
    return null;
  }

  if ('status' in error && typeof error.status === 'number') {
    return {
      code: String(error.status),
      message: extractMessage(error),
      status: error.status,
      timestamp: new Date().toISOString(),
    };
  }

  return {
    code: 'UNKNOWN',
    message: (error as SerializedError).message || 'Lỗi không xác định',
    status: 0,
    timestamp: new Date().toISOString(),
  };
}

/** Extract error message từ FetchBaseQueryError. */
function extractMessage(error: FetchBaseQueryError): string {
  if ('data' in error && typeof error.data === 'object' && error.data !== null) {
    const data = error.data as Record<string, unknown>;
    if ('message' in data && typeof data.message === 'string') {
      return data.message;
    }
    if ('detail' in data && typeof data.detail === 'string') {
      return data.detail;
    }
  }

  const messages: Record<number, string> = {
    400: 'Dữ liệu không hợp lệ.',
    401: 'Phiên đăng nhập đã hết hạn.',
    403: 'Bạn không có quyền truy cập.',
    404: 'Không tìm thấy tài nguyên.',
    409: 'Xung đột dữ liệu.',
    500: 'Lỗi server nội bộ.',
  };

  if ('status' in error && typeof error.status === 'number') {
    return messages[error.status] || 'Đã xảy ra lỗi không mong muốn.';
  }

  return 'Đã xảy ra lỗi không mong muốn.';
}

/** Type guard: kiểm tra có phải FetchBaseQueryError không. */
export function isFetchError(
  error: FetchBaseQueryError | SerializedError | undefined
): error is FetchBaseQueryError {
  return error !== undefined && 'status' in error;
}

/** Type guard: kiểm tra có phải authentication error không. */
export function isAuthError(error: FetchBaseQueryError | SerializedError | undefined): boolean {
  return isFetchError(error) && error.status === 401;
}

/** Handle authentication error: logout và redirect. */
export function handleAuthError(): void {
  localStorage.removeItem('auth_token');
  localStorage.removeItem('auth_user');
  window.location.href = '/login';
}
'''
        return [self._write_file("api-error-utils.ts", content, output_dir)]

    def _write_file(
        self,
        filename: str,
        content: str,
        output_dir: Path,
    ) -> GeneratedFile:
        """Write file và trả về GeneratedFile."""
        file_path = output_dir / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")

        return GeneratedFile(
            path=file_path.relative_to(output_dir.parent),
            content=content,
            template=f"client/react/{filename}",
        )

    def _to_ts_type(self, python_type: str) -> str:
        """Convert Python type sang TypeScript type."""
        type_map = {
            "str": "string",
            "int": "number",
            "float": "number",
            "bool": "boolean",
            "date": "string",
            "datetime": "string",
            "list": "any[]",
            "dict": "Record<string, any>",
        }
        return type_map.get(python_type.lower(), "any")


__all__ = ["ReactClientEmitter", "GeneratedFile"]