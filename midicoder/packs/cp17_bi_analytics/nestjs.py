from __future__ import annotations

from typing import Any, Dict


class NestJSAnalyticsEmitter:
    """Emitter cho các thành phần Business Intelligence & Analytics của NestJS."""

    def __init__(self, collection: Any | None = None):
        self.collection = collection or {}

    def generate(self) -> Dict[str, str]:
        """Tạo tất cả các tệp analytics cho NestJS."""
        result: Dict[str, str] = {}
        result.update(self.generate_module())
        result.update(self.generate_service())
        result.update(self.generate_controller())
        return result

    def generate_module(self) -> Dict[str, str]:
        """Tạo NestJS module cho analytics."""
        code = '''\
/**
 * Module Business Intelligence & Analytics — cung cấp dịch vụ truy vấn phân tích,
 * dashboard, và báo cáo tự động.
 *
 * Xuất AnalyticsService để các module khác có thể inject và sử dụng.
 */
import { Module, Global } from \'@nestjs/common\';
import { AnalyticsService } from \'./analytics.service\';
import { AnalyticsController } from \'./analytics.controller\';

/**
 * Module analytics toàn cục.
 *
 * Đăng ký AnalyticsService và AnalyticsController
 * để cung cấp endpoint REST cho truy vấn, dashboard, và báo cáo.
 */
@Global()
@Module({
  providers: [AnalyticsService],
  controllers: [AnalyticsController],
  exports: [AnalyticsService],
})
export class AnalyticsModule {}
'''
        return {"src/analytics/analytics.module.ts": code}

    def generate_service(self) -> Dict[str, str]:
        """Tạo AnalyticsService — quản lý truy vấn, dashboard, và báo cáo."""
        code = '''\
/**
 * Dịch vụ Business Intelligence & Analytics — truy vấn, dashboard, và báo cáo.
 *
 * Cung cấp giao diện thống nhất để truy vấn dữ liệu phân tích,
 * xây dựng dashboard BI, và lập lịch báo cáo tự động trong ứng dụng NestJS.
 */
import { Injectable } from \'@nestjs/common\';

/**
 * Định dạng của báo cáo.
 */
export enum ReportFormat {
  PDF = \'PDF\',
  CSV = \'CSV\',
  EXCEL = \'EXCEL\',
  JSON = \'JSON\',
}

/**
 * Trạng thái của báo cáo.
 */
export enum ReportStatus {
  PENDING = \'PENDING\',
  GENERATING = \'GENERATING\',
  COMPLETED = \'COMPLETED\',
  FAILED = \'FAILED\',
}

/**
 * Tần suất lập lịch báo cáo.
 */
export enum ScheduleFrequency {
  ONCE = \'ONCE\',
  HOURLY = \'HOURLY\',
  DAILY = \'DAILY\',
  WEEKLY = \'WEEKLY\',
  MONTHLY = \'MONTHLY\',
}

/**
 * Loại biểu đồ hiển thị trên dashboard.
 */
export enum ChartType {
  LINE = \'LINE\',
  BAR = \'BAR\',
  PIE = \'PIE\',
  GAUGE = \'GAUGE\',
  TABLE = \'TABLE\',
}

/**
 * Mô hình phân tích — định nghĩa nguồn dữ liệu và chỉ số có sẵn.
 */
export interface AnalyticsModel {
  /** Tên duy nhất của mô hình. */
  name: string;
  /** Mô tả mô hình. */
  description: string;
  /** Danh sách bộ lọc có thể áp dụng. */
  availableFilters: string[];
  /** Danh sách chỉ số có sẵn. */
  availableMetrics: string[];
  /** Thời điểm tạo (ms epoch). */
  createdAt: number;
}

/**
 * Truy vấn phân tích — định nghĩa bộ lọc và chỉ số cần trả về.
 */
export interface AnalyticsQuery {
  /** Tên của mô hình phân tích. */
  modelName: string;
  /** Bộ lọc áp dụng cho truy vấn. */
  filters: Record<string, any>;
  /** Danh sách chỉ số cần trả về. */
  metrics: string[];
  /** Nhóm kết quả theo các trường. */
  groupBy: string[];
  /** Sắp xếp kết quả theo trường. */
  orderBy?: string;
  /** Số lượng bản ghi tối đa. */
  limit: number;
  /** Số bản ghi bỏ qua. */
  offset: number;
}

/**
 * Kết quả từ truy vấn phân tích.
 */
export interface AnalyticsResult {
  /** ID duy nhất của truy vấn. */
  queryId: string;
  /** Tên mô hình được truy vấn. */
  modelName: string;
  /** Hàng dữ liệu kết quả. */
  rows: Record<string, any>[];
  /** Tổng số hàng. */
  totalCount: number;
  /** Thời gian thực thi (ms). */
  executionTimeMs: number;
  /** Thời điểm truy vấn (ms epoch). */
  queriedAt: number;
}

/**
 * Một widget hiển thị trên dashboard — biểu đồ, bảng, hoặc chỉ số.
 */
export interface Widget {
  /** ID duy nhất của widget. */
  id: string;
  /** Tên widget. */
  name: string;
  /** Loại biểu đồ. */
  chartType: ChartType;
  /** Tên chỉ số cần hiển thị. */
  metric: string;
  /** Tên mô hình phân tích. */
  modelName: string;
  /** Bộ lọc áp dụng. */
  filters: Record<string, any>;
  /** Vị trí ngang trên lưới. */
  positionX: number;
  /** Vị trí dọc trên lưới. */
  positionY: number;
  /** Chiều rộng (số ô lưới). */
  width: number;
  /** Chiều cao (số ô lưới). */
  height: number;
  /** Tiêu đề hiển thị. */
  title: string;
  /** Mô tả widget. */
  description: string;
}

/**
 * Dashboard chứa nhiều widget để hiển thị dữ liệu phân tích.
 */
export interface Dashboard {
  /** Tên duy nhất của dashboard. */
  name: string;
  /** Danh sách các widget. */
  widgets: Widget[];
  /** Mô tả dashboard. */
  description: string;
  /** Thời điểm tạo (ms epoch). */
  createdAt: number;
  /** Thời điểm cập nhật cuối (ms epoch). */
  updatedAt: number;
}

/**
 * Định nghĩa báo cáo — cấu hình nội dung và tần suất xuất bản.
 */
export interface ReportDefinition {
  /** Tên duy nhất của báo cáo. */
  name: string;
  /** Mô hình phân tích nguồn. */
  modelName: string;
  /** Bộ lọc áp dụng. */
  filters: Record<string, any>;
  /** Danh sách chỉ số. */
  metrics: string[];
  /** Định dạng báo cáo. */
  format: ReportFormat;
  /** Tần suất lập lịch. */
  frequency: ScheduleFrequency;
  /** Lần chạy kế tiếp (ms epoch, nếu có). */
  nextRun?: number;
  /** Danh sách người nhận. */
  recipients: string[];
  /** Mô tả báo cáo. */
  description: string;
  /** Thời điểm tạo (ms epoch). */
  createdAt: number;
}

/**
 * Một bản chụp báo cáo đã được tạo — lưu kết quả thực tế.
 */
export interface ReportSnapshot {
  /** ID duy nhất của bản chụp. */
  id: string;
  /** Tên của báo cáo. */
  reportName: string;
  /** Trạng thái báo cáo. */
  status: ReportStatus;
  /** Định dạng báo cáo. */
  format: ReportFormat;
  /** Thời điểm bắt đầu tạo (ms epoch). */
  generatedAt: number;
  /** Thời điểm hoàn thành (ms epoch, nếu có). */
  completedAt?: number;
  /** Kích thước tệp (byte). */
  fileSizeBytes: number;
  /** Số hàng dữ liệu. */
  rowsCount: number;
  /** Thông điệp lỗi (nếu có). */
  errorMessage?: string;
  /** Dữ liệu báo cáo. */
  data: Record<string, any>;
}

/**
 * Định nghĩa dashboard đầu vào từ API.
 */
export interface CreateDashboardDto {
  /** Tên dashboard. */
  name: string;
  /** Mô tả dashboard. */
  description?: string;
  /** Danh sách widget định nghĩa. */
  widgets?: Array<{
    name?: string;
    chartType?: string;
    metric?: string;
    modelName?: string;
    title?: string;
  }>;
}

/**
 * Định nghĩa báo cáo đầu vào từ API.
 */
export interface ScheduleReportDto {
  /** Tên báo cáo. */
  name: string;
  /** Mô hình phân tích. */
  modelName: string;
  /** Bộ lọc. */
  filters?: Record<string, any>;
  /** Chỉ số. */
  metrics?: string[];
  /** Định dạng. */
  format?: string;
  /** Tần suất. */
  frequency?: string;
  /** Người nhận. */
  recipients?: string[];
  /** Mô tả. */
  description?: string;
}

/**
 * Dịch vụ chính cho Business Intelligence & Analytics.
 *
 * Quản lý truy vấn phân tích, xây dựng dashboard,
 * và lập lịch báo cáo tự động để cung cấp khả năng
 * phân tích dữ liệu toàn diện cho ứng dụng.
 */
@Injectable()
export class AnalyticsService {
  /** Danh sách mô hình phân tích. */
  private readonly models: Map<string, AnalyticsModel> = new Map();
  /** Lịch sử truy vấn. */
  private readonly queryHistory: AnalyticsResult[] = [];
  /** Danh sách dashboard. */
  private readonly dashboards: Map<string, Dashboard> = new Map();
  /** Định nghĩa báo cáo. */
  private readonly reportDefinitions: Map<string, ReportDefinition> = new Map();
  /** Lịch sử báo cáo (tên báo cáo → mảng snapshot). */
  private readonly reportSnapshots: Map<string, ReportSnapshot[]> = new Map();

  /**
   * Đăng ký mô hình phân tích mới.
   *
   * @param model - Mô hình phân tích cần đăng ký.
   */
  registerModel(model: AnalyticsModel): void {
    this.models.set(model.name, model);
  }

  /**
   * Lấy danh sách tất cả mô hình phân tích.
   *
   * @returns Mảng mô hình phân tích.
   */
  listModels(): AnalyticsModel[] {
    return Array.from(this.models.values());
  }

  /**
   * Truy vấn dữ liệu phân tích từ mô hình chỉ định.
   *
   * @param modelName - Tên của mô hình phân tích.
   * @param filters - Bộ lọc áp dụng cho truy vấn.
   * @returns Kết quả truy vấn phân tích.
   */
  queryAnalytics(modelName: string, filters: Record<string, any> = {}): AnalyticsResult {
    const start = Date.now();
    const model = this.models.get(modelName);

    const queryId = this._uuid();
    const rows: Record<string, any>[] = [];

    if (model) {
      // Giả lập dữ liệu từ mô hình
      for (let i = 0; i < 100; i++) {
        const row: Record<string, any> = { row_index: i };
        for (const metric of model.availableMetrics) {
          row[metric] = this._generateSampleValue(metric, i);
        }
        rows.push(row);
      }
    }

    const executionTimeMs = Date.now() - start;

    const result: AnalyticsResult = {
      queryId,
      modelName,
      rows,
      totalCount: rows.length,
      executionTimeMs,
      queriedAt: Date.now(),
    };

    this.queryHistory.push(result);
    return result;
  }

  /**
   * Tạo dashboard BI mới từ định nghĩa.
   *
   * @param definition - Định nghĩa dashboard với tên, mô tả, và widget.
   * @returns Dashboard mới được tạo.
   */
  createDashboard(definition: CreateDashboardDto): Dashboard {
    const name = definition.name || `dashboard_${this._uuid().slice(0, 8)}`;
    const description = definition.description || \'\';

    const dashboard: Dashboard = {
      name,
      description,
      widgets: [],
      createdAt: Date.now(),
      updatedAt: Date.now(),
    };

    // Thêm widget từ định nghĩa
    if (definition.widgets) {
      for (const w of definition.widgets) {
        const widget: Widget = {
          id: this._uuid(),
          name: w.name || \'\',
          chartType: (w.chartType as ChartType) || ChartType.LINE,
          metric: w.metric || \'\',
          modelName: w.modelName || \'\',
          filters: {},
          positionX: 0,
          positionY: 0,
          width: 1,
          height: 1,
          title: w.title || w.name || w.metric || \'Widget\',
          description: \'\',
        };
        dashboard.widgets.push(widget);
      }
    }

    this.dashboards.set(name, dashboard);
    return dashboard;
  }

  /**
   * Lấy tất cả dashboard đã tạo.
   *
   * @returns Mảng dashboard.
   */
  getDashboards(): Dashboard[] {
    return Array.from(this.dashboards.values());
  }

  /**
   * Lên lịch báo cáo tự động.
   *
   * @param reportDef - Định nghĩa báo cáo với tên, mô hình, và tần suất.
   * @returns Định nghĩa báo cáo đã lên lịch.
   */
  scheduleReport(reportDef: ScheduleReportDto): ReportDefinition {
    const definition: ReportDefinition = {
      name: reportDef.name || `report_${this._uuid().slice(0, 8)}`,
      modelName: reportDef.modelName || \'\',
      filters: reportDef.filters || {},
      metrics: reportDef.metrics || [],
      format: (reportDef.format as ReportFormat) || ReportFormat.PDF,
      frequency: (reportDef.frequency as ScheduleFrequency) || ScheduleFrequency.ONCE,
      recipients: reportDef.recipients || [],
      description: reportDef.description || `Báo cáo: ${reportDef.name}`,
      createdAt: Date.now(),
    };

    this.reportDefinitions.set(definition.name, definition);
    return definition;
  }

  /**
   * Lấy danh sách báo cáo đã lên lịch.
   *
   * @returns Mảng định nghĩa báo cáo.
   */
  getReportDefinitions(): ReportDefinition[] {
    return Array.from(this.reportDefinitions.values());
  }

  /**
   * Tạo báo cáo thủ công theo tên.
   *
   * @param reportName - Tên của báo cáo cần tạo.
   * @returns Bản chụp báo cáo đã tạo.
   */
  generateReport(reportName: string): ReportSnapshot {
    const definition = this.reportDefinitions.get(reportName);

    if (!definition) {
      const snapshot: ReportSnapshot = {
        id: this._uuid(),
        reportName,
        status: ReportStatus.FAILED,
        format: ReportFormat.PDF,
        generatedAt: Date.now(),
        fileSizeBytes: 0,
        rowsCount: 0,
        errorMessage: `Không tìm thấy định nghĩa báo cáo: ${reportName}`,
        data: {},
      };
      this._addSnapshot(reportName, snapshot);
      return snapshot;
    }

    const snapshot: ReportSnapshot = {
      id: this._uuid(),
      reportName,
      status: ReportStatus.GENERATING,
      format: definition.format,
      generatedAt: Date.now(),
      fileSizeBytes: 0,
      rowsCount: 0,
      data: {},
    };

    // Giả lập quá trình tạo báo cáo
    try {
      const rowsCount = 50;
      snapshot.status = ReportStatus.COMPLETED;
      snapshot.completedAt = Date.now();
      snapshot.rowsCount = rowsCount;
      snapshot.fileSizeBytes = rowsCount * 256;
    } catch (error: any) {
      snapshot.status = ReportStatus.FAILED;
      snapshot.errorMessage = error?.message || String(error);
    }

    this._addSnapshot(reportName, snapshot);
    return snapshot;
  }

  /**
   * Lấy lịch sử báo cáo theo tên.
   *
   * @param reportName - Tên của báo cáo.
   * @returns Mảng bản chụp báo cáo theo thứ tự thời gian.
   */
  getReportHistory(reportName: string): ReportSnapshot[] {
    return this.reportSnapshots.get(reportName) || [];
  }

  /**
   * Thêm snapshot vào lịch sử báo cáo.
   */
  private _addSnapshot(reportName: string, snapshot: ReportSnapshot): void {
    const history = this.reportSnapshots.get(reportName) || [];
    history.push(snapshot);
    this.reportSnapshots.set(reportName, history);
  }

  /**
   * Tạo giá trị mẫu cho chỉ số (dùng trong demo).
   *
   * @param metric - Tên chỉ số.
   * @param index - Chỉ số hàng.
   * @returns Giá trị mẫu.
   */
  private _generateSampleValue(metric: string, index: number): number {
    // Tạo giá trị giả lập dựa trên tên metric và chỉ số
    let hash = 0;
    const str = `${metric}:${index}`;
    for (let i = 0; i < str.length; i++) {
      hash = ((hash << 5) - hash) + str.charCodeAt(i);
      hash |= 0;
    }
    return (Math.abs(hash) % 10000) / 100;
  }

  /**
   * Tạo UUID v4 đơn giản.
   */
  private _uuid(): string {
    return \'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx\'.replace(/[xy]/g, (c) => {
      const r = (Math.random() * 16) | 0;
      const v = c === \'x\' ? r : (r & 0x3) | 0x8;
      return v.toString(16);
    });
  }
}
'''
        return {"src/analytics/analytics.service.ts": code}

    def generate_controller(self) -> Dict[str, str]:
        """Tạo NestJS controller cho các endpoint analytics, dashboard, và báo cáo."""
        code = '''\
/**
 * Controller Business Intelligence & Analytics — endpoint REST cho truy vấn,
 * dashboard, và báo cáo.
 *
 * Cung cấp API cho phía client để truy vấn dữ liệu phân tích,
 * quản lý dashboard BI, và xuất bản báo cáo.
 */
import {
  Controller,
  Get,
  Post,
  Body,
  Param,
} from \'@nestjs/common\';
import {
  AnalyticsService,
  AnalyticsModel,
  AnalyticsResult,
  Dashboard,
  ReportDefinition,
  ReportSnapshot,
  CreateDashboardDto,
  ScheduleReportDto,
} from \'./analytics.service\';

/**
 * Controller cho endpoint analytics.
 *
 * Quản lý các route REST để:
 * - Liệt kê và truy vấn mô hình phân tích
 * - Tạo và liệt kê dashboard BI
 * - Lập lịch và tạo báo cáo
 */
@Controller(\'analytics\')
export class AnalyticsController {
  constructor(private readonly analytics: AnalyticsService) {}

  /**
   * Liệt kê tất cả mô hình phân tích có sẵn.
   *
   * @returns Mảng mô hình phân tích.
   */
  @Get(\'models\')
  listModels(): AnalyticsModel[] {
    return this.analytics.listModels();
  }

  /**
   * Truy vấn dữ liệu phân tích từ mô hình chỉ định.
   *
   * @param modelName - Tên của mô hình phân tích.
   * @param filters - Bộ lọc áp dụng cho truy vấn.
   * @returns Kết quả truy vấn phân tích.
   */
  @Post(\'query\')
  queryAnalytics(
    @Body(\'modelName\') modelName: string,
    @Body(\'filters\') filters?: Record<string, any>,
  ): AnalyticsResult {
    return this.analytics.queryAnalytics(modelName, filters || {});
  }

  /**
   * Liệt kê tất cả dashboard BI đã tạo.
   *
   * @returns Mảng dashboard.
   */
  @Get(\'dashboards\')
  listDashboards(): Dashboard[] {
    return this.analytics.getDashboards();
  }

  /**
   * Tạo dashboard BI mới từ định nghĩa.
   *
   * @param definition - Định nghĩa dashboard với tên, mô tả, và widget.
   * @returns Dashboard mới được tạo.
   */
  @Post(\'dashboards\')
  createDashboard(@Body() definition: CreateDashboardDto): Dashboard {
    return this.analytics.createDashboard(definition);
  }

  /**
   * Liệt kê tất cả báo cáo đã lên lịch.
   *
   * @returns Mảng định nghĩa báo cáo.
   */
  @Get(\'reports\')
  listReports(): ReportDefinition[] {
    return this.analytics.getReportDefinitions();
  }

  /**
   * Tạo báo cáo thủ công theo tên.
   *
   * @param name - Tên của báo cáo cần tạo.
   * @returns Bản chụp báo cáo đã tạo.
   */
  @Post(\'reports/generate\')
  generateReport(@Body(\'name\') name: string): ReportSnapshot {
    return this.analytics.generateReport(name);
  }

  /**
   * Lấy lịch sử báo cáo theo tên.
   *
   * @param name - Tên của báo cáo.
   * @returns Mảng bản chụp báo cáo.
   */
  @Get(\'reports/:name/history\')
  reportHistory(@Param(\'name\') name: string): ReportSnapshot[] {
    return this.analytics.getReportHistory(name);
  }
}
'''
        return {"src/analytics/analytics.controller.ts": code}
