from __future__ import annotations

from typing import Any, Dict


class AngularObservabilityEmitter:
    """Emitter cho các thành phần observability của Angular."""

    def __init__(self, collection: Any | None = None):
        self.collection = collection or {}

    def generate(self) -> Dict[str, str]:
        """Tạo tất cả các tệp observability cho Angular."""
        result: Dict[str, str] = {}
        result.update(self.generate_service())
        result.update(self.generate_component())
        return result

    def generate_service(self) -> Dict[str, str]:
        """Tạo LoggingService — ghi log và truy vấn log từ phía client."""
        code = '''\
/**
 * Dịch vụ ghi log cho Angular — ghi log client-side và truy vấn log từ API.
 *
 * Cung cấp khả năng ghi log cấu trúc trong trình duyệt và
 * tải các log entry từ backend để hiển thị trong LogViewer.
 */
import { Injectable, inject } from \'@angular/core\';
import { HttpClient } from \'@angular/common/http\';
import { Observable, of } from \'rxjs\';

/**
 * Mức độ log.
 */
export enum LogLevel {
  DEBUG = \'DEBUG\',
  INFO = \'INFO\',
  WARN = \'WARN\',
  ERROR = \'ERROR\',
}

/**
 * Một entry log có cấu trúc.
 */
export interface LogEntry {
  id?: string;
  timestamp: number;
  level: LogLevel;
  service: string;
  message: string;
  fields?: Record<string, any>;
}

/**
 * Tham số truy vấn log.
 */
export interface LogQueryParams {
  level?: LogLevel;
  service?: string;
  from?: number;
  to?: number;
  limit?: number;
  offset?: number;
  search?: string;
}

/**
 * Cấu hình dịch vụ log.
 */
interface LoggingConfig {
  apiBaseUrl: string;
  serviceName: string;
  maxLocalEntries: number;
}

/**
 * Cấu hình mặc định.
 */
const DEFAULT_CONFIG: LoggingConfig = {
  apiBaseUrl: \'/api\',
  serviceName: \'midicoder-angular\',
  maxLocalEntries: 500,
};

/**
 * Dịch vụ log cho Angular.
 *
 * Ghi log local trong trình duyệt và hỗ trợ truy vấn log
 * từ API backend để hiển thị trong giao diện quản trị.
 */
@Injectable({
  providedIn: \'root\',
})
export class LoggingService {
  private readonly http = inject(HttpClient);
  private readonly config: LoggingConfig = DEFAULT_CONFIG;
  private readonly localEntries: LogEntry[] = [];

  /**
   * Cấu hình dịch vụ log.
   *
   * @param config - Cấu hình tùy chỉnh.
   */
  configure(config?: Partial<LoggingConfig>): void {
    Object.assign(this.config, config);
  }

  /**
   * Ghi một log entry có cấu trúc.
   *
   * Lưu log vào bộ nhớ local và gửi về backend nếu có kết nối.
   *
   * @param level - Mức độ log.
   * @param message - Thông điệp log.
   * @param fields - Các trường metadata bổ sung.
   */
  log(level: LogLevel, message: string, fields?: Record<string, any>): void {
    const entry: LogEntry = {
      id: this._generateId(),
      timestamp: Date.now(),
      level,
      service: this.config.serviceName,
      message,
      fields,
    };

    // Lưu vào bộ nhớ local
    this.localEntries.push(entry);
    if (this.localEntries.length > this.config.maxLocalEntries) {
      this.localEntries.splice(0, this.localEntries.length - this.config.maxLocalEntries);
    }

    // Ghi log ra console theo mức độ
    this._consoleLog(level, message, fields);

    // Gửi về backend cho các mức WARN và ERROR
    if (level === LogLevel.WARN || level === LogLevel.ERROR) {
      this._sendToBackend(entry).subscribe({
        error: (err) => console.error(\'Failed to send log to backend:\', err),
      });
    }
  }

  /**
   * Log mức DEBUG.
   */
  debug(message: string, fields?: Record<string, any>): void {
    this.log(LogLevel.DEBUG, message, fields);
  }

  /**
   * Log mức INFO.
   */
  info(message: string, fields?: Record<string, any>): void {
    this.log(LogLevel.INFO, message, fields);
  }

  /**
   * Log mức WARN.
   */
  warn(message: string, fields?: Record<string, any>): void {
    this.log(LogLevel.WARN, message, fields);
  }

  /**
   * Log mức ERROR.
   */
  error(message: string, error?: any, fields?: Record<string, any>): void {
    this.log(LogLevel.ERROR, message, {
      ...fields,
      ...(error ? { error: error.message || String(error), stack: error?.stack } : {}),
    });
  }

  /**
   * Truy vấn log từ API backend.
   *
   * @param params - Các tham số truy vấn.
   * @returns Observable chứa danh sách log entries.
   */
  queryLogs(params?: LogQueryParams): Observable<LogEntry[]> {
    const queryParams: Record<string, string> = {};
    if (params?.level) queryParams[\'level\'] = params.level;
    if (params?.service) queryParams[\'service\'] = params.service;
    if (params?.from) queryParams[\'from\'] = String(params.from);
    if (params?.to) queryParams[\'to\'] = String(params.to);
    if (params?.limit) queryParams[\'limit\'] = String(params.limit);
    if (params?.offset) queryParams[\'offset\'] = String(params.offset);
    if (params?.search) queryParams[\'search\'] = params.search;

    return this.http.get<LogEntry[]>(`${this.config.apiBaseUrl}/observability/logs`, {
      params: queryParams,
    });
  }

  /**
   * Lấy các log entries local.
   *
   * @param level - Lọc theo mức độ (tùy chọn).
   * @param limit - Số lượng tối đa.
   * @returns Danh sách log entries.
   */
  getLocalLogs(level?: LogLevel, limit: number = 100): LogEntry[] {
    let entries = this.localEntries;
    if (level) {
      entries = entries.filter((e) => e.level === level);
    }
    return entries.slice(-limit);
  }

  /**
   * Xóa tất cả log entries local.
   */
  clearLocalLogs(): void {
    this.localEntries.length = 0;
  }

  /**
   * Ghi log ra console theo mức độ tương ứng.
   */
  private _consoleLog(level: LogLevel, message: string, fields?: Record<string, any>): void {
    const prefix = `[${level}] ${this.config.serviceName}:`;
    switch (level) {
      case LogLevel.DEBUG:
        console.debug(prefix, message, fields || \`{}\`);
        break;
      case LogLevel.INFO:
        console.info(prefix, message, fields || \`{}\`);
        break;
      case LogLevel.WARN:
        console.warn(prefix, message, fields || \`{}\`);
        break;
      case LogLevel.ERROR:
        console.error(prefix, message, fields || \`{}\`);
        break;
    }
  }

  /**
   * Gửi log entry về backend API.
   */
  private _sendToBackend(entry: LogEntry): Observable<void> {
    return this.http.post<void>(`${this.config.apiBaseUrl}/observability/logs`, entry);
  }

  /** Tạo ID duy nhất. */
  private _generateId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }
}
'''
        return {"src/app/core/observability/logging_service.ts": code}

    def generate_component(self) -> Dict[str, str]:
        """Tạo LogViewerComponent — hiển thị log entries với bộ lọc."""
        code = '''\
/**
 * Component hiển thị danh sách log entries với khả năng lọc và tìm kiếm.
 *
 * Kết nối với LoggingService để tải log từ backend và hiển thị
 * dưới dạng bảng với các bộ lọc theo mức độ, dịch vụ, và từ khóa.
 */
import { Component, OnInit, OnDestroy, ChangeDetectionStrategy } from \'@angular/core\';
import { CommonModule } from \'@angular/common\';
import { FormsModule } from \'@angular/forms\';
import { Subscription } from \'rxjs\';
import { LoggingService, LogEntry, LogLevel, LogQueryParams } from \'./logging_service\';

/**
 * Trạng thái bộ lọc hiện tại.
 */
interface FilterState {
  level: LogLevel | null;
  search: string;
  limit: number;
  offset: number;
}

/**
 * Component xem log.
 *
 * Hiển thị danh sách log entries từ backend với các bộ lọc
 * theo mức độ, tìm kiếm theo từ khóa, và phân trang.
 */
@Component({
  selector: \'app-log-viewer\',
  standalone: true,
  imports: [CommonModule, FormsModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="log-viewer">
      <h2>Tất cả Log Entries</h2>

      <!-- Bộ lọc -->
      <div class="log-filters">
        <label for="level-filter">
          Mức độ:
          <select id="level-filter" [(ngModel)]="filter.level" (change)="onFilterChange()">
            <option [ngValue]="null">Tất cả</option>
            <option [ngValue]="'DEBUG'">DEBUG</option>
            <option [ngValue]="'INFO'">INFO</option>
            <option [ngValue]="'WARN'">WARN</option>
            <option [ngValue]="'ERROR'">ERROR</option>
          </select>
        </label>

        <label for="search-input">
          Tìm kiếm:
          <input
            id="search-input"
            type="text"
            [(ngModel)]="filter.search"
            (input)="onSearchDebounce()"
            placeholder="Tìm theo nội dung..."
          />
        </label>

        <button (click)="loadLogs()" class="refresh-btn">
          Làm mới
        </button>
      </div>

      <!-- Trạng thái tải -->
      <div *ngIf="loading" class="loading">Đang tải log...</div>

      <!-- Danh sách log -->
      <div *ngIf="!loading && logs.length === 0" class="empty-state">
        Không có log entry nào.
      </div>

      <div *ngIf="!loading && logs.length > 0" class="log-list">
        <div
          *ngFor="let entry of logs"
          [class]="\'log-entry log-entry--\' + entry.level.toLowerCase()"
        >
          <span class="log-timestamp">{{ entry.timestamp | date:\'medium\' }}</span>
          <span [class]="'log-level log-level--\' + entry.level.toLowerCase()">
            {{ entry.level }}
          </span>
          <span class="log-service">{{ entry.service }}</span>
          <span class="log-message">{{ entry.message }}</span>
          <span *ngIf="entry.fields" class="log-fields">
            {{ entry.fields | json }}
          </span>
        </div>
      </div>

      <!-- Phân trang -->
      <div *ngIf="!loading && logs.length > 0" class="pagination">
        <button (click)="previousPage()" [disabled]="filter.offset === 0">
          Trước
        </button>
        <span>Trang {{ currentPage() }}</span>
        <button (click)="nextPage()" [disabled]="logs.length < filter.limit">
          Sau
        </button>
      </div>
    </div>
  `,
  styles: [`
    .log-viewer {
      padding: 16px;
      font-family: monospace;
    }
    .log-filters {
      display: flex;
      gap: 16px;
      margin-bottom: 16px;
      align-items: center;
    }
    .log-list {
      display: flex;
      flex-direction: column;
      gap: 4px;
    }
    .log-entry {
      display: flex;
      gap: 12px;
      padding: 8px;
      border-radius: 4px;
      background: #f5f5f5;
      font-size: 13px;
    }
    .log-entry--error {
      background: #ffe0e0;
    }
    .log-entry--warn {
      background: #fff3e0;
    }
    .log-level {
      font-weight: bold;
      min-width: 60px;
    }
    .log-level--error {
      color: #c62828;
    }
    .log-level--warn {
      color: #e65100;
    }
    .log-timestamp {
      min-width: 120px;
      color: #666;
    }
    .log-service {
      min-width: 80px;
      color: #1565c0;
    }
    .log-message {
      flex: 1;
    }
    .log-fields {
      color: #666;
      font-size: 11px;
    }
    .pagination {
      display: flex;
      gap: 12px;
      margin-top: 16px;
      align-items: center;
    }
    .loading, .empty-state {
      text-align: center;
      padding: 32px;
      color: #666;
    }
  `],
})
export class LogViewerComponent implements OnInit, OnDestroy {
  /** Dịch vụ log. */
  private readonly logging = new LoggingService();

  /** Danh sách log entries. */
  logs: LogEntry[] = [];

  /** Trạng thái tải. */
  loading = false;

  /** Trạng thái bộ lọc. */
  filter: FilterState = {
    level: null,
    search: \'\',
    limit: 50,
    offset: 0,
  };

  /** Subscription để dọn dẹp. */
  private sub?: Subscription;

  /** Bộ debounce cho tìm kiếm. */
  private searchTimeout?: ReturnType<typeof setTimeout>;

  ngOnInit(): void {
    this.loadLogs();
  }

  ngOnDestroy(): void {
    this.sub?.unsubscribe();
    if (this.searchTimeout) clearTimeout(this.searchTimeout);
  }

  /**
   * Tải log từ backend.
   */
  loadLogs(): void {
    this.loading = true;
    const params: LogQueryParams = {
      level: this.filter.level ?? undefined,
      search: this.filter.search || undefined,
      limit: this.filter.limit,
      offset: this.filter.offset,
    };

    this.sub = this.logging.queryLogs(params).subscribe({
      next: (entries) => {
        this.logs = entries;
        this.loading = false;
      },
      error: (err) => {
        console.error(\'Failed to load logs:\', err);
        this.loading = false;
      },
    });
  }

  /**
   * Xử lý khi bộ lọc thay đổi.
   */
  onFilterChange(): void {
    this.filter.offset = 0;
    this.loadLogs();
  }

  /**
   * Xử lý tìm kiếm với debounce.
   */
  onSearchDebounce(): void {
    if (this.searchTimeout) clearTimeout(this.searchTimeout);
    this.searchTimeout = setTimeout(() => {
      this.filter.offset = 0;
      this.loadLogs();
    }, 300);
  }

  /** Chuyển sang trang trước. */
  previousPage(): void {
    if (this.filter.offset > 0) {
      this.filter.offset -= this.filter.limit;
      this.loadLogs();
    }
  }

  /** Chuyển sang trang sau. */
  nextPage(): void {
    this.filter.offset += this.filter.limit;
    this.loadLogs();
  }

  /** Tính số trang hiện tại. */
  currentPage(): number {
    return Math.floor(this.filter.offset / this.filter.limit) + 1;
  }
}
'''
        return {"src/app/core/observability/log_viewer.component.ts": code}
