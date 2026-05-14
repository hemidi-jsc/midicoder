from __future__ import annotations

from typing import Any, Dict


class NestJSObservabilityEmitter:
    """Emitter cho các thành phần observability của NestJS."""

    def __init__(self, collection: Any | None = None):
        self.collection = collection or {}

    def generate(self) -> Dict[str, str]:
        """Tạo tất cả các tệp observability cho NestJS."""
        result: Dict[str, str] = {}
        result.update(self.generate_module())
        result.update(self.generate_service())
        result.update(self.generate_interceptor())
        result.update(self.generate_metrics_endpoint())
        return result

    def generate_module(self) -> Dict[str, str]:
        """Tạo NestJS module cho observability."""
        code = '''\
/**
 * Module quan sát — cung cấp dịch vụ metric, log cấu trúc, và trace cho toàn ứng dụng.
 *
 * Xuất ObservabilityService để các module khác có thể inject và sử dụng.
 */
import { Module, Global } from \'@nestjs/common\';
import { ObservabilityService } from \'./observability.service\';
import { ObservabilityInterceptor } from \'./observability.interceptor\';

/**
 * Module quan sát toàn cục.
 *
 * Tự động đăng ký ObservabilityInterceptor cho mọi route.
 */
@Global()
@Module({
  providers: [
    ObservabilityService,
    {
      provide: \'APP_INTERCEPTOR\',
      useClass: ObservabilityInterceptor,
    },
  ],
  exports: [ObservabilityService],
})
export class ObservabilityModule {}
'''
        return {"src/observability/observability.module.ts": code}

    def generate_service(self) -> Dict[str, str]:
        """Tạo ObservabilityService — ghi metric, log cấu trúc, trace span."""
        code = '''\
/**
 * Dịch vụ observability — ghi metric, log có cấu trúc, và trace span.
 *
 * Cung cấp giao diện thống nhất để theo dõi hiệu suất và chẩn đoán
 * các vấn đề trong ứng dụng NestJS.
 */
import { Injectable, LoggerService } from \'@nestjs/common\';

/**
 * Mức độ log.
 */
export enum LogLevel {
  DEBUG = \'DEBUG\',
  LOG = \'LOG\',
  WARN = \'WARN\',
  ERROR = \'ERROR\',
  FATAL = \'FATAL\',
}

/**
 * Một entry log có cấu trúc.
 */
export interface LogEntry {
  timestamp: number;
  level: LogLevel;
  service: string;
  message: string;
  fields?: Record<string, any>;
}

/**
 * Đại diện cho một trace span.
 */
export interface Span {
  traceId: string;
  spanId: string;
  name: string;
  startTime: number;
  endTime?: number;
  attributes?: Record<string, any>;
  durationMs?: number;
}

/**
 * Dữ liệu metric đã được ghi nhận.
 */
export interface MetricData {
  name: string;
  labels?: Record<string, string>;
  values: number[];
}

/**
 * Registry đơn giản để lưu trữ và xuất metric (tương thích Prometheus).
 */
class MetricRegistry {
  private counters: Map<string, number> = new Map();
  private gauges: Map<string, number> = new Map();
  private histograms: Map<string, number[]> = new Map();

  /** Tăng giá trị counter. */
  inc(name: string, value: number = 1, labels?: Record<string, string>): void {
    const key = this._key(name, labels);
    this.counters.set(key, (this.counters.get(key) || 0) + value);
  }

  /** Đặt giá trị gauge. */
  set(name: string, value: number, labels?: Record<string, string>): void {
    const key = this._key(name, labels);
    this.gauges.set(key, value);
  }

  /** Ghi nhận observation vào histogram. */
  observe(name: string, value: number, labels?: Record<string, string>): void {
    const key = this._key(name, labels);
    const bucket = this.histograms.get(key) || [];
    bucket.push(value);
    this.histograms.set(key, bucket);
  }

  /** Xuất tất cả metric dưới định dạng Prometheus text. */
  export(): string {
    const lines: string[] = [];

    for (const [key, value] of this.counters) {
      lines.push(`# TYPE ${this._base(key)} counter`);
      lines.push(`${key} ${value}`);
    }

    for (const [key, value] of this.gauges) {
      lines.push(`# TYPE ${this._base(key)} gauge`);
      lines.push(`${key} ${value}`);
    }

    for (const [key, values] of this.histograms) {
      lines.push(`# TYPE ${this._base(key)} histogram`);
      lines.push(`${key}_count ${values.length}`);
      if (values.length > 0) {
        lines.push(`${key}_sum ${values.reduce((a, b) => a + b, 0)}`);
        lines.push(`${key}_min ${Math.min(...values)}`);
        lines.push(`${key}_max ${Math.max(...values)}`);
      }
    }

    return lines.join(\'\\n\');
  }

  private _key(name: string, labels?: Record<string, string>): string {
    if (!labels) return name;
    const labelStr = Object.entries(labels)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([k, v]) => `${k}=${v}`)
      .join(\',\');
    return `${name}{${labelStr}}`;
  }

  private _base(key: string): string {
    return key.split(\'{\')[0];
  }
}

/**
 * Dịch vụ chính cho observability.
 *
 * Tích hợp metric, log có cấu trúc, và distributed tracing
 * để cung cấp khả năng quan sát toàn diện cho ứng dụng.
 */
@Injectable()
export class ObservabilityService implements LoggerService {
  private readonly metrics = new MetricRegistry();
  private readonly logEntries: LogEntry[] = [];
  private readonly activeSpans: Map<string, Span> = new Map();
  private readonly completedSpans: Span[] = [];

  constructor(private readonly serviceName: string = \'midicoder\') {}

  /**
   * Ghi nhận một metric (dạng gauge).
   *
   * @param name - Tên của metric.
   * @param value - Giá trị số của metric.
   * @param labels - Các label để phân loại metric.
   */
  recordMetric(name: string, value: number, labels?: Record<string, string>): void {
    this.metrics.set(name, value, labels);
    this.log(LogLevel.DEBUG, `Metric recorded: ${name}=${value}`, { name, value, labels });
  }

  /**
   * Tăng counter metric.
   *
   * @param name - Tên counter.
   * @param value - Giá trị tăng (mặc định 1).
   * @param labels - Các label để phân loại.
   */
  incrementCounter(name: string, value?: number, labels?: Record<string, string>): void {
    this.metrics.inc(name, value, labels);
  }

  /**
   * Ghi nhận observation vào histogram.
   *
   * @param name - Tên histogram.
   * @param value - Giá trị observation.
   * @param labels - Các label để phân loại.
   */
  observeHistogram(name: string, value: number, labels?: Record<string, string>): void {
    this.metrics.observe(name, value, labels);
  }

  /**
   * Ghi một log entry có cấu trúc.
   *
   * @param level - Mức độ log.
   * @param message - Thông điệp log.
   * @param fields - Các trường metadata bổ sung.
   */
  log(level: LogLevel, message: string, fields?: Record<string, any>): void {
    const entry: LogEntry = {
      timestamp: Date.now(),
      level,
      service: this.serviceName,
      message,
      fields,
    };
    this.logEntries.push(entry);
    console.log(`[${level}] ${this.serviceName}: ${message}`, fields || \`{}\`);
  }

  /** Các phương thức LoggerService của NestJS. */

  /** Log mức INFO. */
  verbose(message: string, context?: string): void {
    this.log(LogLevel.DEBUG, message, context ? { context } : undefined);
  }

  /** Log mức LOG. */
  debug(message: string, context?: string): void {
    this.log(LogLevel.LOG, message, context ? { context } : undefined);
  }

  /** Log mức WARN. */
  warn(message: string, context?: string): void {
    this.log(LogLevel.WARN, message, context ? { context } : undefined);
  }

  /** Log mức ERROR. */
  error(message: string, trace?: string, context?: string): void {
    this.log(LogLevel.ERROR, message, {
      context,
      ...(trace ? { stack: trace } : {}),
    });
  }

  /** Log mức FATAL. */
  fatal(message: string, trace?: string, context?: string): void {
    this.log(LogLevel.FATAL, message, {
      context,
      ...(trace ? { stack: trace } : {}),
    });
  }

  /**
   * Bắt đầu một trace span mới.
   *
   * @param name - Tên của span.
   * @param attributes - Các attribute gắn với span.
   * @returns ID duy nhất của span được tạo.
   */
  startSpan(name: string, attributes?: Record<string, any>): string {
    const traceId = this._uuid();
    const spanId = this._uuid();
    const span: Span = {
      traceId,
      spanId,
      name,
      startTime: Date.now(),
      attributes,
    };
    this.activeSpans.set(spanId, span);
    this.log(LogLevel.DEBUG, `Span started: ${name}`, { traceId, spanId });
    return spanId;
  }

  /**
   * Kết thúc một trace span.
   *
   * @param spanId - ID của span cần kết thúc.
   * @returns Span đã hoàn thành hoặc undefined nếu không tìm thấy.
   */
  finishSpan(spanId: string): Span | undefined {
    const span = this.activeSpans.get(spanId);
    if (!span) return undefined;

    span.endTime = Date.now();
    span.durationMs = span.endTime - span.startTime;
    this.activeSpans.delete(spanId);
    this.completedSpans.push(span);
    this.log(LogLevel.DEBUG, `Span finished: ${span.name} (${span.durationMs}ms)`, {
      spanId,
      durationMs: span.durationMs,
    });
    return span;
  }

  /**
   * Xuất tất cả metric dưới định dạng Prometheus text.
   *
   * @returns Chuỗi metric đã được định dạng.
   */
  exportMetrics(): string {
    return this.metrics.export();
  }

  /**
   * Lấy các log entries gần đây.
   *
   * @param level - Lọc theo mức độ log (tùy chọn).
   * @param limit - Số lượng entries tối đa.
   * @returns Danh sách các log entries.
   */
  getLogs(level?: LogLevel, limit: number = 100): LogEntry[] {
    let entries = this.logEntries;
    if (level) {
      entries = entries.filter((e) => e.level === level);
    }
    return entries.slice(-limit);
  }

  /**
   * Lấy các span đã hoàn thành gần đây.
   *
   * @param limit - Số lượng span tối đa.
   * @returns Danh sách các span.
   */
  getRecentSpans(limit: number = 50): Span[] {
    return this.completedSpans.slice(-limit);
  }

  /** Tạo UUID v4 đơn giản. */
  private _uuid(): string {
    return \'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx\'.replace(/[xy]/g, (c) => {
      const r = (Math.random() * 16) | 0;
      const v = c === \'x\' ? r : (r & 0x3) | 0x8;
      return v.toString(16);
    });
  }
}
'''
        return {"src/observability/observability.service.ts": code}

    def generate_interceptor(self) -> Dict[str, str]:
        """Tạo NestJS interceptor để tự động instrument HTTP request."""
        code = '''\
/**
 * Interceptor quan sát — tự động ghi metric, log, và trace cho mỗi request HTTP.
 *
 * Đo lường thời gian xử lý, ghi nhận histogram và counter,
 * đồng thời tạo trace span cho từng yêu cầu.
 */
import {
  Injectable,
  NestInterceptor,
  ExecutionContext,
  CallHandler,
} from \'@nestjs/common\';
import { Observable } from \'rxjs\';
import { tap, finalize } from \'rxjs/operators\';
import { ObservabilityService, LogLevel } from \'./observability.service\';

/**
 * Các đường dẫn mặc định bị loại trừ khỏi quan sát.
 */
const DEFAULT_EXCLUDE_PATHS = [\'/health\', \'/metrics\'];

/**
 * Interceptor quan sát toàn cầu.
 *
 * Tự động thêm vào pipeline của NestJS thông qua APP_INTERCEPTOR token.
 */
@Injectable()
export class ObservabilityInterceptor implements NestInterceptor {
  /** Các đường dẫn bị loại trừ. */
  private readonly excludePaths: string[] = DEFAULT_EXCLUDE_PATHS;

  constructor(private readonly observability: ObservabilityService) {}

  /**
   * Xử lý yêu cầu và tự động ghi observability data.
   *
   * @param context - Ngữ cảnh thực thi hiện tại.
   * @param next - Handler tiếp theo trong pipeline.
   * @returns Observable của response đã được quan sát.
   */
  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    const request = context.switchToHttp().getRequest<Request>();
    const path = request.url || request.originalUrl || \'/\';

    // Bỏ qua các đường dẫn bị loại trừ
    if (this.excludePaths.includes(path)) {
      return next.handle();
    }

    const method = request.method || \'UNKNOWN\';
    const spanId = this.observability.startSpan(`${method} ${path}`, {
      \'http.method\': method,
      \'http.url\': path,
      \'http.client_ip\': request.ip,
    });

    // Ghi log request đến
    this.observability.log(LogLevel.LOG, `Request received: ${method} ${path}`, {
      method,
      path,
      query: request.query,
      contentType: request.headers[\'content-type\'],
      userAgent: request.headers[\'user-agent\'],
    });

    // Đo thời gian xử lý
    const startTime = Date.now();

    return next.handle().pipe(
      tap((response) => {
        // Tính thời gian xử lý
        const durationMs = Date.now() - startTime;
        const statusCode = this._getStatusCode(response);

        // Ghi histogram cho thời gian request
        this.observability.observeHistogram(\'http_request_duration_ms\', durationMs, {
          method,
          path,
          status: String(statusCode),
        });

        // Tăng counter cho số lượng request
        this.observability.incrementCounter(\'http_requests_total\', 1, {
          method,
          path,
          status: String(statusCode),
        });

        // Log response
        this.observability.log(
          statusCode >= 500 ? LogLevel.ERROR : LogLevel.LOG,
          `Request completed: ${method} ${path} -> ${statusCode}`,
          {
            method,
            path,
            statusCode,
            durationMs,
          },
        );
      }),
      finalize(() => {
        // Hoàn thành trace span
        const span = this.observability.finishSpan(spanId);
        if (span) {
          span.attributes = {
            ...span.attributes,
            \'http.duration_ms\': span.durationMs,
          };
        }
      }),
    );
  }

  /**
   * Trích xuất mã trạng thái HTTP từ response.
   *
   * @param response - Response object từ NestJS.
   * @returns Mã trạng thái HTTP.
   */
  private _getStatusCode(response: any): number {
    if (typeof response === \'object\' && response !== null) {
      if (typeof response.status === \'number\') return response.status;
      if (typeof response.statusCode === \'number\') return response.statusCode;
    }
    return 200;
  }
}
'''
        return {"src/observability/observability.interceptor.ts": code}

    def generate_metrics_endpoint(self) -> Dict[str, str]:
        """Tạo NestJS controller /metrics để export Prometheus metrics."""
        code = '''\\
/**
 * Controller /metrics — export Prometheus metrics.
 *
 * Cung cấp endpoint GET /metrics để Prometheus hoặc các công cụ
 * thu thập metrics khác có thể scrape dữ liệu.
 */
import { Controller, Get, Headers } from \'@nestjs/common\';
import { ObservabilityService } from \'./observability.service\';

@Controller(\'metrics\')
export class MetricsController {
  constructor(private readonly observability: ObservabilityService) {}

  /**
   * GET /metrics — xuất tất cả metric dưới định dạng Prometheus text.
   *
   * @returns Chuỗi metric đã được định dạng.
   */
  @Get()
  getMetrics(): string {
    return this.observability.exportMetrics();
  }
}
'''
        return {"src/observability/metrics.controller.ts": code}
