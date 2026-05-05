"""Angular Client Emitter (P2-002-D).

Module này cung cấp AngularClientEmitter để emit HTTP client services
cho Angular frontend với features:
- CRUD REST API calls
- Pagination (offset/cursor)
- Filtering (dynamic query params)
- Caching (HttpResponseCache)
- Error handling (standardized error interceptor)

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


class AngularClientEmitter:
    """Emitter cho Angular HTTP Client services.

    Generate code cho:
    - Entity API Services (CRUD + Pagination + Filtering)
    - HTTP Error Interceptor
    - Response Cache Service

    Usage:
        emitter = AngularClientEmitter.create_emitter()
        files = emitter.emit(entities, output_dir)
    """

    @classmethod
    def create_emitter(cls) -> AngularClientEmitter:
        """Tạo instance mới."""
        return cls()

    def emit(
        self,
        entities: list[dict[str, Any]],
        output_dir: Path,
    ) -> list[GeneratedFile]:
        """Emit Angular client services.

        Args:
            entities: Danh sách entities với id và fields
            output_dir: Output directory

        Returns:
            List of GeneratedFile instances
        """
        files: list[GeneratedFile] = []

        services_dir = output_dir / "services"
        services_dir.mkdir(parents=True, exist_ok=True)

        # Emit entity services
        for entity in entities:
            files.extend(self._emit_entity_service(entity, services_dir))

        # Emit error interceptor
        files.extend(self._emit_error_interceptor(services_dir))

        # Emit cache service
        files.extend(self._emit_cache_service(services_dir))

        return files

    def _emit_entity_service(
        self,
        entity: dict[str, Any],
        output_dir: Path,
    ) -> list[GeneratedFile]:
        """Emit service cho 1 entity."""
        entity_id = entity["id"]
        entity_lower = entity_id.lower()
        fields = entity.get("fields", [])

        content = self._generate_service(entity_id, entity_lower, fields)
        filename = f"{entity_lower}-service.ts"

        return [self._write_file(filename, content, output_dir)]

    def _generate_service(
        self,
        entity_id: str,
        entity_lower: str,
        fields: list[dict[str, Any]],
    ) -> str:
        """Generate Angular Injectable service."""
        # Generate TypeScript interface fields
        interface_fields = "\n".join(
            f"  {f['name']}: {self._to_ts_type(f.get('type', 'any'))};" for f in fields
        )

        # Generate paginated response interface
        paginated_interface = f"""
export interface Paginated{entity_id} {{
  items: {entity_id}[];
  total: number;
  page: number;
  limit: number;
  hasMore: boolean;
}}"""

        # Generate filter interface
        filter_fields = "\n".join(
            f"  {f['name']}?: {self._to_ts_type(f.get('type', 'any'))};" for f in fields
        )
        filter_interface = f"""
export interface {entity_id}Filter {{
{filter_fields}
}}"""

        # Generate query params builder
        query_params = f"""
  private buildQueryParams(
    filter?: {entity_id}Filter,
    page?: number,
    limit?: number
  ): HttpParams {{
    let params = new HttpParams();

    // Pagination params
    if (page !== undefined) {{
      params = params.set('page', page.toString());
      params = params.set('limit', (limit || 20).toString());
    }}

    // Filter params
    if (filter) {{
      Object.entries(filter).forEach(([key, value]) => {{
        if (value !== undefined && value !== null) {{
          params = params.set(key, value.toString());
        }}
      }});
    }}

    return params;
  }}"""

        lines = []
        lines.append('/**')
        lines.append(f' * {entity_id} Service - HTTP Client cho {entity_id} API.')
        lines.append(' *')
        lines.append(' * Features:')
        lines.append(' * - CRUD REST API calls')
        lines.append(' * - Pagination (offset-based)')
        lines.append(' * - Filtering (dynamic query params)')
        lines.append(' * - Response caching')
        lines.append(' * - Error handling')
        lines.append(' */')
        lines.append('')
        lines.append("import { Injectable } from '@angular/core';")
        lines.append('import {')
        lines.append('  HttpClient,')
        lines.append('  HttpParams,')
        lines.append('  HttpResponse,')
        lines.append("} from '@angular/common/http';")
        lines.append("import { Observable, throwError } from 'rxjs';")
        lines.append('import {')
        lines.append('  catchError,')
        lines.append('  map,')
        lines.append('  tap,')
        lines.append("} from 'rxjs/operators';")
        lines.append("import { ApiErrorResponse } from './api-error-interceptor';")
        lines.append("import { ResponseCacheService } from './response-cache-service';")
        lines.append('')
        lines.append(f'export interface {entity_id} {{')
        lines.append(interface_fields)
        lines.append('}}')
        lines.append(paginated_interface)
        lines.append(filter_interface)
        lines.append('')
        lines.append('@Injectable({')
        lines.append("  providedIn: 'root',")
        lines.append('})')
        lines.append(f'export class {entity_id}Service {{')
        lines.append(f"  private readonly apiUrl = '/api/{entity_lower}';")
        lines.append(f"  private readonly cacheKey = '{entity_lower}';")
        lines.append('')
        lines.append('  constructor(')
        lines.append('    private readonly httpClient: HttpClient,')
        lines.append('    private readonly cacheService: ResponseCacheService,')
        lines.append('  ) {}')
        lines.append('')
        # buildQueryParams
        lines.append(f'  private buildQueryParams(')
        lines.append(f'    filter?: {entity_id}Filter,')
        lines.append(f'    page?: number,')
        lines.append(f'    limit?: number')
        lines.append(f'  ): HttpParams {{')
        lines.append(f"    let params = new HttpParams();")
        lines.append(f'')
        lines.append(f'    // Pagination params')
        lines.append(f'    if (page !== undefined) {{')
        lines.append(f"      params = params.set('page', page.toString());")
        lines.append(f"      params = params.set('limit', (limit || 20).toString());")
        lines.append(f'    }}')
        lines.append(f'')
        lines.append(f'    // Filter params')
        lines.append(f'    if (filter) {{')
        lines.append(f'      Object.entries(filter).forEach(([key, value]) => {{')
        lines.append(f'        if (value !== undefined && value !== null) {{')
        lines.append(f'          params = params.set(key, value.toString());')
        lines.append(f'        }}')
        lines.append(f'      }});')
        lines.append(f'    }}')
        lines.append(f'')
        lines.append(f'    return params;')
        lines.append(f'  }}')
        lines.append('')
        # list()
        lines.append(f'  /** Lấy danh sách {entity_lower} với pagination và filtering. */')
        lines.append(f'  list(')
        lines.append(f'    filter?: {entity_id}Filter,')
        lines.append(f'    page: number = 1,')
        lines.append(f'    limit: number = 20,')
        lines.append(f'    skipCache: boolean = false')
        lines.append(f'  ): Observable<Paginated{entity_id}> {{')
        lines.append(f"    const cacheKey = this.buildCacheKey('list', {{ filter, page, limit }});")
        lines.append(f'')
        lines.append(f'    if (!skipCache) {{')
        lines.append(f'      const cached = this.cacheService.get<Paginated{entity_id}>(cacheKey);')
        lines.append(f'      if (cached) {{')
        lines.append(f'        return new Observable(subscriber => {{')
        lines.append(f'          subscriber.next(cached);')
        lines.append(f'          subscriber.complete();')
        lines.append(f'        }});')
        lines.append(f'      }}')
        lines.append(f'    }}')
        lines.append(f'')
        lines.append(f'    const params = this.buildQueryParams(filter, page, limit);')
        lines.append(f'')
        lines.append(f'    return this.httpClient.get<{entity_id}[]>(this.apiUrl, {{ params }}).pipe(')
        lines.append(f'      map(items => {{')
        lines.append(f'        const response: Paginated{entity_id} = {{')
        lines.append(f'          items,')
        lines.append(f'          total: items.length,')
        lines.append(f'          page,')
        lines.append(f'          limit,')
        lines.append(f'          hasMore: items.length >= limit,')
        lines.append(f'        }};')
        lines.append(f'        this.cacheService.set(cacheKey, response, 30000);')
        lines.append(f'        return response;')
        lines.append(f'      }}),')
        lines.append(f"      catchError(error => this.handleError(error, 'get_{entity_lower}'))")
        lines.append(f'    );')
        lines.append(f'  }}')
        lines.append('')
        # getById()
        lines.append(f'  /** Lấy 1 {entity_lower} theo ID. */')
        lines.append(f'  getById(id: string, skipCache: boolean = false): Observable<{entity_id}> {{')
        lines.append(f"    const cacheKey = `${{this.cacheKey}}:byId:${{id}}`;")
        lines.append(f'')
        lines.append(f'    if (!skipCache) {{')
        lines.append(f'      const cached = this.cacheService.get<{entity_id}>(cacheKey);')
        lines.append(f'      if (cached) {{')
        lines.append(f'        return new Observable(subscriber => {{')
        lines.append(f'          subscriber.next(cached);')
        lines.append(f'          subscriber.complete();')
        lines.append(f'        }});')
        lines.append(f'      }}')
        lines.append(f'    }}')
        lines.append(f'')
        lines.append(f'    return this.httpClient.get<{entity_id}>(`${{this.apiUrl}}/${{id}}`).pipe(')
        lines.append(f'      tap(item => this.cacheService.set(cacheKey, item, 60000)),')
        lines.append(f"      catchError(error => this.handleError(error, 'get_{entity_lower}_by_id'))")
        lines.append(f'    );')
        lines.append(f'  }}')
        lines.append('')
        # create()
        lines.append(f'  /** Tạo mới {entity_lower}. */')
        lines.append(f'  create(data: Partial<{entity_id}>): Observable<{entity_id}> {{')
        lines.append(f'    return this.httpClient.post<{entity_id}>(this.apiUrl, data).pipe(')
        lines.append(f'      tap(() => this.invalidateCache()),')
        lines.append(f"      catchError(error => this.handleError(error, 'create_{entity_lower}'))")
        lines.append(f'    );')
        lines.append(f'  }}')
        lines.append('')
        # update()
        lines.append(f'  /** Cập nhật {entity_lower}. */')
        lines.append(f'  update(id: string, data: Partial<{entity_id}>): Observable<{entity_id}> {{')
        lines.append(f'    return this.httpClient.put<{entity_id}>(`${{this.apiUrl}}/${{id}}`, data).pipe(')
        lines.append(f'      tap(() => this.invalidateCache()),')
        lines.append(f"      catchError(error => this.handleError(error, 'update_{entity_lower}'))")
        lines.append(f'    );')
        lines.append(f'  }}')
        lines.append('')
        # delete()
        lines.append(f'  /** Xóa {entity_lower}. */')
        lines.append(f'  delete(id: string): Observable<void> {{')
        lines.append(f'    return this.httpClient.delete<void>(`${{this.apiUrl}}/${{id}}`).pipe(')
        lines.append(f'      tap(() => this.invalidateCache()),')
        lines.append(f"      catchError(error => this.handleError(error, 'delete_{entity_lower}'))")
        lines.append(f'    );')
        lines.append(f'  }}')
        lines.append('')
        # invalidateCache()
        lines.append(f'  /** Invalidates tất cả cache cho {entity_lower}. */')
        lines.append(f'  private invalidateCache(): void {{')
        lines.append(f"    this.cacheService.invalidatePattern(`${{this.cacheKey}}:*`);")
        lines.append(f'  }}')
        lines.append('')
        # buildCacheKey()
        lines.append(f'  /** Build cache key từ operation và params. */')
        lines.append(f'  private buildCacheKey(')
        lines.append(f'    operation: string,')
        lines.append(f'    params: Record<string, unknown>')
        lines.append(f'  ): string {{')
        lines.append(f"    return `${{this.cacheKey}}:${{operation}}:${{JSON.stringify(params)}}`;")
        lines.append(f'  }}')
        lines.append('')
        # handleError()
        lines.append(f'  /** Handle và transform API errors. */')
        lines.append(f'  private handleError(error: any, operation: string): Observable<never> {{')
        lines.append(f'    const apiError: ApiErrorResponse = {{')
        lines.append(f"      code: error?.status || 'UNKNOWN',")
        lines.append(f"      message: error?.error?.message || 'Lỗi khi ' + operation,")
        lines.append(f'      operation,')
        lines.append(f'      timestamp: new Date().toISOString(),')
        lines.append(f'    }};')
        lines.append(f'    return throwError(() => apiError);')
        lines.append(f'  }}')
        lines.append('}}')
        lines.append('')

        return '\n'.join(lines)

    def _emit_error_interceptor(
        self,
        output_dir: Path,
    ) -> list[GeneratedFile]:
        """Emit HTTP Error Interceptor."""
        content = '''/**
 * API Error Interceptor - Interceptor xử lý lỗi HTTP.
 *
 * Features:
 * - 401: Redirect về login
 * - 403: Hiển thị thông báo không có quyền
 * - 5xx: Hiển thị thông báo lỗi server
 * - Transform tất cả errors thành ApiErrorResponse
 */

import {
  HttpInterceptorFn,
  HttpErrorResponse,
} from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';

export interface ApiErrorResponse {
  code: string;
  message: string;
  operation?: string;
  timestamp: string;
}

export const apiErrorInterceptor: HttpInterceptorFn = (
  request,
  next
) => {
  const router = inject(Router);

  return next(request).pipe(
    catchError((error: HttpErrorResponse) => {
      const apiError: ApiErrorResponse = {
        code: `${error.status}`,
        message: getErrorMessage(error),
        timestamp: new Date().toISOString(),
      };

      // 401: Unauthenticated - redirect về login
      if (error.status === 401) {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('auth_user');
        router.navigate(['/login']);
      }

      // 403: Forbidden - log warning
      if (error.status === 403) {
        console.warn('[API Error] Không có quyền truy cập:', request.url);
      }

      // 5xx: Server error - log error
      if (error.status >= 500) {
        console.error('[API Error] Lỗi server:', apiError);
      }

      return throwError(() => apiError);
    })
  );
};

/**Extract error message từ HttpErrorResponse.*/
function getErrorMessage(error: HttpErrorResponse): string {
  if (error.error?.message) {
    return error.error.message;
  }
  if (error.error?.detail) {
    return error.error.detail;
  }
  const messages: Record<number, string> = {
    400: 'Dữ liệu không hợp lệ.',
    401: 'Phiên đăng nhập đã hết hạn.',
    403: 'Bạn không có quyền truy cập.',
    404: 'Không tìm thấy tài nguyên.',
    409: 'Xung đột dữ liệu.',
    500: 'Lỗi server nội bộ.',
  };
  return messages[error.status] || 'Đã xảy ra lỗi không mong muốn.';
}
'''
        return [self._write_file("api-error-interceptor.ts", content, output_dir)]

    def _emit_cache_service(
        self,
        output_dir: Path,
    ) -> list[GeneratedFile]:
        """Emit Response Cache Service."""
        content = '''/**
 * Response Cache Service - Dịch vụ cache cho HTTP responses.
 *
 * Features:
 * - In-memory cache với TTL
 * - Pattern-based invalidation
 * - Cache size management
 */

import { Injectable } from '@angular/core';

interface CacheEntry<T> {
  data: T;
  expiry: number;
  timestamp: number;
}

interface CacheConfig {
  maxSize: number;
  defaultTtl: number;
}

const DEFAULT_CONFIG: CacheConfig = {
  maxSize: 100,
  defaultTtl: 30000, // 30 giây
};

@Injectable({
  providedIn: 'root',
})
export class ResponseCacheService {
  private cache = new Map<string, CacheEntry<unknown>>();
  private config: CacheConfig;

  constructor(config?: Partial<CacheConfig>) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  /** Lấy dữ liệu từ cache. Returns null nếu không có hoặc hết hạn. */
  get<T>(key: string): T | null {
    const entry = this.cache.get(key);

    if (!entry) {
      return null;
    }

    // Kiểm tra expiry
    if (Date.now() > entry.expiry) {
      this.cache.delete(key);
      return null;
    }

    return entry.data as T;
  }

  /** Lưu dữ liệu vào cache với TTL. */
  set<T>(key: string, data: T, ttl?: number): void {
    // Nếu cache đầy, xóa entry cũ nhất
    if (this.cache.size >= this.config.maxSize) {
      this._evictOldest();
    }

    const now = Date.now();
    this.cache.set(key, {
      data,
      expiry: now + (ttl ?? this.config.defaultTtl),
      timestamp: now,
    });
  }

  /** Xóa entry khỏi cache. */
  invalidate(key: string): void {
    this.cache.delete(key);
  }

  /** Invalidate tất cả entries khớp với pattern. */
  invalidatePattern(pattern: string): void {
    const regex = new RegExp('^' + pattern.replace('*', '.*') + '$');
    for (const key of this.cache.keys()) {
      if (regex.test(key)) {
        this.cache.delete(key);
      }
    }
  }

  /** Xóa toàn bộ cache. */
  clear(): void {
    this.cache.clear();
  }

  /** Trả về số lượng entries trong cache. */
  get size(): number {
    return this.cache.size;
  }

  /** Xóa entry cũ nhất để giải phóng không gian. */
  private _evictOldest(): void {
    let oldestKey: string | null = null;
    let oldestTime = Infinity;

    for (const [key, entry] of this.cache.entries()) {
      if (entry.timestamp < oldestTime) {
        oldestTime = entry.timestamp;
        oldestKey = key;
      }
    }

    if (oldestKey) {
      this.cache.delete(oldestKey);
    }
  }
}
'''
        return [self._write_file("response-cache-service.ts", content, output_dir)]

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
            template=f"client/angular/{filename}",
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


__all__ = ["AngularClientEmitter", "GeneratedFile"]