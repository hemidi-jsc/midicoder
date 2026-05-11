from __future__ import annotations

from typing import Any, Dict


class ReactObservabilityEmitter:
    """Emitter cho các thành phần observability của React."""

    def __init__(self, collection: Any | None = None):
        self.collection = collection or {}

    def generate(self) -> Dict[str, str]:
        """Tạo tất cả các tệp observability cho React."""
        result: Dict[str, str] = {}
        result.update(self.generate_types())
        result.update(self.generate_hook())
        result.update(self.generate_component())
        return result

    def generate_types(self) -> Dict[str, str]:
        """Tạo TypeScript interfaces cho observability."""
        code = '''\
/**
 * Định nghĩa TypeScript cho hệ thống observability phía client.
 *
 * Bao gồm giao diện cho log entry, tham số truy vấn,
 * và cấu hình dịch vụ log.
 */

/**
 * Mức độ log.
 */
export type LogLevel = \'DEBUG\' | \'INFO\' | \'WARN\' | \'ERROR\' | \'FATAL\';

/**
 * Màu sắc tương ứng với mỗi mức độ log (để hiển thị trong giao diện).
 */
export const LOG_LEVEL_COLORS: Record<LogLevel, string> = {
  DEBUG: \'#6c757d\',
  INFO: \'#0d6efd\',
  WARN: \'#fd7e14\',
  ERROR: \'#dc3545\',
  FATAL: \'#660000\',
};

/**
 * Một entry log có cấu trúc.
 */
export interface LogEntry {
  /** ID duy nhất của log entry. */
  id: string;
  /** Dấu thời gian (ms epoch). */
  timestamp: number;
  /** Mức độ log. */
  level: LogLevel;
  /** Tên dịch vụ tạo log. */
  service: string;
  /** Thông điệp chính. */
  message: string;
  /** Các trường metadata bổ sung. */
  fields?: Record<string, unknown>;
  /** Tên component (chỉ áp dụng cho log từ React component). */
  component?: string;
  /** Stack trace (chỉ cho lỗi). */
  stack?: string;
}

/**
 * Tham số truy vấn log từ API backend.
 */
export interface LogQueryParams {
  /** Lọc theo mức độ log. */
  level?: LogLevel;
  /** Lọc theo tên dịch vụ. */
  service?: string;
  /** Tên component. */
  component?: string;
  /** Thời gian bắt đầu (ms epoch). */
  from?: number;
  /** Thời gian kết thúc (ms epoch). */
  to?: number;
  /** Số lượng entries trả về. */
  limit?: number;
  /** Offset để phân trang. */
  offset?: number;
  /** Từ khóa tìm kiếm trong message. */
  search?: string;
}

/**
 * Phản hồi phân trang từ API.
 */
export interface PaginatedLogResponse {
  /** Danh sách log entries. */
  entries: LogEntry[];
  /** Tổng số entries phù hợp. */
  total: number;
  /** Offset hiện tại. */
  offset: number;
  /** Limit của trang hiện tại. */
  limit: number;
}

/**
 * Cấu hình dịch vụ log.
 */
export interface LoggingConfig {
  /** URL cơ sở của API backend. */
  apiBaseUrl: string;
  /** Tên dịch vụ hiện tại. */
  serviceName: string;
  /** Số lượng log entries tối đa lưu local. */
  maxLocalEntries: number;
  /** Tự động gửi log về backend. */
  autoSendToBackend: boolean;
  /** Các mức độ log cần gửi về backend. */
  backendLevels: LogLevel[];
}

/**
 * Cấu hình mặc định.
 */
export const DEFAULT_LOGGING_CONFIG: LoggingConfig = {
  apiBaseUrl: \'/api\',
  serviceName: \'midicoder-react\',
  maxLocalEntries: 500,
  autoSendToBackend: true,
  backendLevels: [\'WARN\', \'ERROR\', \'FATAL\'],
};

/**
 * Trạng thái của hook useLogging.
 */
export interface UseLoggingState {
  /** Danh sách log entries hiện tại. */
  logs: LogEntry[];
  /** Đang tải dữ liệu hay không. */
  loading: boolean;
  /** Lỗi nếu có. */
  error: Error | null;
  /** Tổng số entries (cho phân trang). */
  total: number;
}

/**
 * Trạng thái bộ lọc.
 */
export interface FilterState {
  /** Mức độ log đang lọc. */
  level: LogLevel | null;
  /** Từ khóa tìm kiếm. */
  search: string;
  /** Số entries mỗi trang. */
  pageSize: number;
  /** Số trang hiện tại (bắt đầu từ 0). */
  page: number;
}

/**
 * Cấu hình mặc định cho bộ lọc.
 */
export const DEFAULT_FILTER: FilterState = {
  level: null,
  search: \'\',
  pageSize: 20,
  page: 0,
};
'''
        return {"src/observability/types.ts": code}

    def generate_hook(self) -> Dict[str, str]:
        """Tạo useLogging hook — log và query logs."""
        code = '''\
/**
 * Custom hook useLogging — cung cấp khả năng ghi log và truy vấn log.
 *
 * Sử dụng trong các React component để ghi log có cấu trúc
 * và tải danh sách log từ API backend.
 */
import { useState, useCallback, useEffect, useRef } from \'react\';
import {
  LogEntry,
  LogLevel,
  LogQueryParams,
  LoggingConfig,
  UseLoggingState,
  DEFAULT_LOGGING_CONFIG,
} from \'./types\';

/**
 * Hàm để gọi API (sẽ được replace bằng thực tế fetch/axios).
 */
async function fetchLogs(
  baseUrl: string,
  params: LogQueryParams
): Promise<{ entries: LogEntry[]; total: number }> {
  const queryParams = new URLSearchParams();
  if (params.level) queryParams.set(\'level\', params.level);
  if (params.service) queryParams.set(\'service\', params.service);
  if (params.from) queryParams.set(\'from\', String(params.from));
  if (params.to) queryParams.set(\'to\', String(params.to));
  if (params.limit) queryParams.set(\'limit\', String(params.limit));
  if (params.offset) queryParams.set(\'offset\', String(params.offset));
  if (params.search) queryParams.set(\'search\', params.search);

  const url = `${baseUrl}/observability/logs?${queryParams.toString()}`;
  const response = await fetch(url);

  if (!response.ok) {
    throw new Error(`Failed to fetch logs: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Gửi một log entry về backend API.
 */
async function sendLogToBackend(
  baseUrl: string,
  entry: LogEntry
): Promise<void> {
  await fetch(`${baseUrl}/observability/logs`, {
    method: \'POST\',
    headers: { \'Content-Type\': \'application/json\' },
    body: JSON.stringify(entry),
  });
}

/**
 * Tạo ID duy nhất cho log entry.
 */
function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substring(2, 11)}`;
}

/**
 * Custom hook để ghi log và truy vấn log từ backend.
 *
 * @param config - Cấu hình tùy chỉnh cho dịch vụ log.
 * @returns Trạng thái log và các hàm thao tác.
 *
 * @example
 * ```tsx
 * const { logs, loading, log, queryLogs } = useLogging({
 *   apiBaseUrl: \'/api\',
 *   serviceName: \'my-app\',
 * });
 * ```
 */
export function useLogging(config?: Partial<LoggingConfig>) {
  const mergedConfig = { ...DEFAULT_LOGGING_CONFIG, ...config };
  const localLogsRef = useRef<LogEntry[]>([]);

  const [state, setState] = useState<UseLoggingState>({
    logs: [],
    loading: false,
    error: null,
    total: 0,
  });

  /**
   * Ghi một log entry có cấu trúc.
   *
   * @param level - Mức độ log.
   * @param message - Thông điệp log.
   * @param fields - Các trường metadata bổ sung.
   * @param component - Tên component (tùy chọn).
   */
  const log = useCallback(
    (level: LogLevel, message: string, fields?: Record<string, unknown>, component?: string) => {
      const entry: LogEntry = {
        id: generateId(),
        timestamp: Date.now(),
        level,
        service: mergedConfig.serviceName,
        message,
        fields,
        component,
      };

      // Lưu vào local buffer
      localLogsRef.current.push(entry);
      if (localLogsRef.current.length > mergedConfig.maxLocalEntries) {
        localLogsRef.current = localLogsRef.current.slice(-mergedConfig.maxLocalEntries);
      }

      // Ghi ra console theo mức độ
      const prefix = `[${level}] ${mergedConfig.serviceName}${component ? ` (${component})` : \'\'}:`;
      switch (level) {
        case \'DEBUG\':
          console.debug(prefix, message, fields || {});
          break;
        case \'INFO\':
          console.info(prefix, message, fields || {});
          break;
        case \'WARN\':
          console.warn(prefix, message, fields || {});
          break;
        case \'ERROR\':
        case \'FATAL\':
          console.error(prefix, message, fields || {});
          break;
      }

      // Gửi về backend nếu được cấu hình
      if (
        mergedConfig.autoSendToBackend &&
        mergedConfig.backendLevels.includes(level)
      ) {
        sendLogToBackend(mergedConfig.apiBaseUrl, entry).catch((err) => {
          console.error(\'Failed to send log to backend:\', err);
        });
      }
    },
    [mergedConfig]
  );

  /**
   * Truy vấn log từ API backend.
   *
   * @param params - Các tham số truy vấn.
   */
  const queryLogs = useCallback(
    async (params?: Partial<LogQueryParams>) => {
      setState((prev) => ({ ...prev, loading: true, error: null }));

      try {
        const queryParams: LogQueryParams = {
          level: params?.level,
          service: params?.service || mergedConfig.serviceName,
          limit: params?.limit || 20,
          offset: params?.offset || 0,
          search: params?.search,
          from: params?.from,
          to: params?.to,
        };

        const result = await fetchLogs(mergedConfig.apiBaseUrl, queryParams);
        setState({
          logs: result.entries,
          loading: false,
          error: null,
          total: result.total,
        });
      } catch (err) {
        setState((prev) => ({
          ...prev,
          loading: false,
          error: err instanceof Error ? err : new Error(String(err)),
        }));
      }
    },
    [mergedConfig]
  );

  /**
   * Lấy log entries lưu local.
   *
   * @param level - Lọc theo mức độ (tùy chọn).
   * @param limit - Số lượng tối đa.
   */
  const getLocalLogs = useCallback(
    (level?: LogLevel, limit: number = 100): LogEntry[] => {
      let entries = localLogsRef.current;
      if (level) {
        entries = entries.filter((e) => e.level === level);
      }
      return entries.slice(-limit);
    },
    []
  );

  /**
   * Xóa tất cả log entries local.
   */
  const clearLocalLogs = useCallback(() => {
    localLogsRef.current = [];
  }, []);

  /**
   * Các phương thức tiện ích cho từng mức độ.
   */
  const debug = useCallback(
    (message: string, fields?: Record<string, unknown>, component?: string) =>
      log(\'DEBUG\', message, fields, component),
    [log]
  );

  const info = useCallback(
    (message: string, fields?: Record<string, unknown>, component?: string) =>
      log(\'INFO\', message, fields, component),
    [log]
  );

  const warn = useCallback(
    (message: string, fields?: Record<string, unknown>, component?: string) =>
      log(\'WARN\', message, fields, component),
    [log]
  );

  const error = useCallback(
    (message: string, error?: unknown, component?: string) =>
      log(\'ERROR\', message, {
        error: error instanceof Error ? error.message : String(error),
        stack: error instanceof Error ? error.stack : undefined,
      }, component),
    [log]
  );

  return {
    ...state,
    log,
    debug,
    info,
    warn,
    error,
    queryLogs,
    getLocalLogs,
    clearLocalLogs,
  };
}
'''
        return {"src/observability/useLogging.ts": code}

    def generate_component(self) -> Dict[str, str]:
        """Tạo LogViewer component — hiển thị log với filter và pagination."""
        code = '''\
/**
 * Component LogViewer — hiển thị danh sách log entries với bộ lọc và phân trang.
 *
 * Kết hợp với useLogging hook để tải và hiển thị log từ backend API.
 */
import React, { useState, useEffect, useCallback } from \'react\';
import { useLogging } from \'./useLogging\';
import { LogEntry, LogLevel, FilterState, DEFAULT_FILTER, LOG_LEVEL_COLORS } from \'./types\';

/**
 * Props cho LogViewer component.
 */
interface LogViewerProps {
  /** URL cơ sở của API. */
  apiBaseUrl?: string;
  /** Tên dịch vụ. */
  serviceName?: string;
  /** Tự động tải log khi mount. */
  autoLoad?: boolean;
  /** Callback khi log được chọn. */
  onLogSelect?: (entry: LogEntry) => void;
}

/**
 * LogViewer component.
 *
 * Hiển thị danh sách log với:
 * - Bộ lọc theo mức độ log
 * - Tìm kiếm theo từ khóa
 * - Phân trang
 * - Hiển thị chi tiết khi click vào log entry
 */
export const LogViewer: React.FC<LogViewerProps> = ({
  apiBaseUrl = \'/api\',
  serviceName = \'midicoder-react\',
  autoLoad = true,
  onLogSelect,
}) => {
  // Hook log
  const { logs, loading, error, total, queryLogs } = useLogging({
    apiBaseUrl,
    serviceName,
  });

  // Trạng thái bộ lọc
  const [filter, setFilter] = useState<FilterState>(DEFAULT_FILTER);
  // Log entry đang được chọn để hiển thị chi tiết
  const [selectedLog, setSelectedLog] = useState<LogEntry | null>(null);

  // Tự động tải log khi mount
  useEffect(() => {
    if (autoLoad) {
      loadLogs();
    }
  }, []);

  // Tải lại khi bộ lọc thay đổi
  useEffect(() => {
    loadLogs();
  }, [filter.level, filter.page, filter.pageSize]);

  /**
   * Tải log từ backend.
   */
  const loadLogs = useCallback(() => {
    queryLogs({
      level: filter.level || undefined,
      search: filter.search || undefined,
      limit: filter.pageSize,
      offset: filter.page * filter.pageSize,
    });
  }, [filter, queryLogs]);

  /**
   * Xử lý khi bộ lọc mức độ thay đổi.
   */
  const handleLevelChange = useCallback((newLevel: LogLevel | null) => {
    setFilter((prev) => ({ ...prev, level: newLevel, page: 0 }));
  }, []);

  /**
   * Xử lý khi tìm kiếm thay đổi.
   */
  const handleSearchChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setFilter((prev) => ({ ...prev, search: e.target.value, page: 0 }));
  }, []);

  /**
   * Xử lý khi chọn log entry.
   */
  const handleLogClick = useCallback(
    (entry: LogEntry) => {
      setSelectedLog(entry);
      onLogSelect?.(entry);
    },
    [onLogSelect]
  );

  /**
   * Đóng chi tiết log.
   */
  const closeDetail = useCallback(() => {
    setSelectedLog(null);
  }, []);

  /**
   * Chuyển trang.
   */
  const goToPage = useCallback((page: number) => {
    setFilter((prev) => ({ ...prev, page }));
  }, []);

  /**
   * Tính tổng số trang.
   */
  const totalPages = Math.ceil(total / filter.pageSize);

  return (
    <div className="log-viewer">
      <h2>Log Viewer</h2>

      {/* Bộ lọc */}
      <div className="log-viewer__filters">
        <label htmlFor="level-filter">
          Mức độ:{\'\'}
          <select
            id="level-filter"
            value={filter.level || \'\'}
            onChange={(e) => handleLevelChange(e.target.value as LogLevel || null)}
          >
            <option value="">Tất cả</option>
            <option value="DEBUG">DEBUG</option>
            <option value="INFO">INFO</option>
            <option value="WARN">WARN</option>
            <option value="ERROR">ERROR</option>
            <option value="FATAL">FATAL</option>
          </select>
        </label>

        <label htmlFor="search-input">
          Tìm kiếm:{\'\'}
          <input
            id="search-input"
            type="text"
            value={filter.search}
            onChange={handleSearchChange}
            placeholder="Tìm theo nội dung..."
          />
        </label>

        <button onClick={loadLogs} disabled={loading}>
          {loading ? \'Đang tải...\' : \'Làm mới\'}
        </button>
      </div>

      {/* Thông báo lỗi */}
      {error && (
        <div className="log-viewer__error">
          Lỗi khi tải log: {error.message}
        </div>
      )}

      {/* Danh sách log */}
      <div className="log-viewer__list">
        {loading && !logs.length && <div className="log-viewer__loading">Đang tải log...</div>}
        {!loading && !logs.length && (
          <div className="log-viewer__empty">Không có log entry nào.</div>
        )}

        {logs.map((entry) => (
          <div
            key={entry.id}
            className={`log-viewer__entry log-viewer__entry--${entry.level.toLowerCase()}`}
            style={{ borderLeftColor: LOG_LEVEL_COLORS[entry.level] }}
            onClick={() => handleLogClick(entry)}
          >
            <span className="log-viewer__timestamp">
              {new Date(entry.timestamp).toLocaleString()}
            </span>
            <span
              className="log-viewer__level"
              style={{ color: LOG_LEVEL_COLORS[entry.level] }}
            >
              {entry.level}
            </span>
            <span className="log-viewer__service">{entry.service}</span>
            {entry.component && (
              <span className="log-viewer__component">{entry.component}</span>
            )}
            <span className="log-viewer__message">{entry.message}</span>
          </div>
        ))}
      </div>

      {/* Phân trang */}
      {totalPages > 1 && (
        <div className="log-viewer__pagination">
          <button
            onClick={() => goToPage(filter.page - 1)}
            disabled={filter.page === 0}
          >
            Trước
          </button>
          <span>
            Trang {filter.page + 1} / {totalPages}
          </span>
          <button
            onClick={() => goToPage(filter.page + 1)}
            disabled={filter.page >= totalPages - 1}
          >
            Sau
          </button>
        </div>
      )}

      {/* Chi tiết log */}
      {selectedLog && (
        <div className="log-viewer__detail">
          <button className="log-viewer__close" onClick={closeDetail}>
            Đóng
          </button>
          <h3>Chi tiết Log</h3>
          <dl>
            <dt>Thời gian</dt>
            <dd>{new Date(selectedLog.timestamp).toLocaleString()}</dd>
            <dt>Mức độ</dt>
            <dd>{selectedLog.level}</dd>
            <dt>Dịch vụ</dt>
            <dd>{selectedLog.service}</dd>
            {selectedLog.component && (
              <>
                <dt>Component</dt>
                <dd>{selectedLog.component}</dd>
              </>
            )}
            <dt>Thông điệp</dt>
            <dd>{selectedLog.message}</dd>
            {selectedLog.fields && (
              <>
                <dt>Trường bổ sung</dt>
                <dd>
                  <pre>{JSON.stringify(selectedLog.fields, null, 2)}</pre>
                </dd>
              </>
            )}
            {selectedLog.stack && (
              <>
                <dt>Stack Trace</dt>
                <dd>
                  <pre>{selectedLog.stack}</pre>
                </dd>
              </>
            )}
          </dl>
        </div>
      )}
    </div>
  );
};

export default LogViewer;
'''
        return {"src/observability/LogViewer.tsx": code}
