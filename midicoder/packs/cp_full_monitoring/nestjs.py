from __future__ import annotations

from typing import Any, Dict


class NestJSMonitoringEmitter:
    """Emitter cho các thành phần monitoring của NestJS."""

    def __init__(self, collection: Any | None = None):
        self.collection = collection or {}

    def generate(self) -> Dict[str, str]:
        """Tạo tất cả các tệp monitoring cho NestJS."""
        result: Dict[str, str] = {}
        result.update(self.generate_module())
        result.update(self.generate_service())
        result.update(self.generate_controller())
        return result

    def generate_module(self) -> Dict[str, str]:
        """Tạo NestJS module cho monitoring."""
        code = '''\
/**
 * Module monitoring — cung cấp dịch vụ quản lý dashboard, cảnh báo, và SLI.
 *
 * Xuất MonitoringService để các module khác có thể inject và sử dụng.
 */
import { Module, Global } from \'@nestjs/common\';
import { MonitoringService } from \'./monitoring.service\';
import { MonitoringController } from \'./monitoring.controller\';

/**
 * Module monitoring toàn cục.
 *
 * Đăng ký MonitoringService và MonitoringController
 * để cung cấp endpoint REST cho dashboard, cảnh báo, và SLI.
 */
@Global()
@Module({
  providers: [MonitoringService],
  controllers: [MonitoringController],
  exports: [MonitoringService],
})
export class MonitoringModule {}
'''
        return {"src/monitoring/monitoring.module.ts": code}

    def generate_service(self) -> Dict[str, str]:
        """Tạo MonitoringService — quản lý dashboard, cảnh báo, và SLI."""
        code = '''\
/**
 * Dịch vụ monitoring — quản lý dashboard, động cơ cảnh báo, và giám sát SLI.
 *
 * Cung cấp giao diện thống nhất để tạo dashboard, định nghĩa quy tắc cảnh báo,
 * và theo dõi chỉ số mức độ dịch vụ trong ứng dụng NestJS.
 */
import { Injectable } from \'@nestjs/common\';

/**
 * Mức độ nghiêm trọng của cảnh báo.
 */
export enum AlertSeverity {
  INFO = \'INFO\',
  WARNING = \'WARNING\',
  CRITICAL = \'CRITICAL\',
  FATAL = \'FATAL\',
}

/**
 * Trạng thái của cảnh báo.
 */
export enum AlertStatus {
  ACTIVE = \'ACTIVE\',
  RESOLVED = \'RESOLVED\',
  ACKNOWLEDGED = \'ACKNOWLEDGED\',
}

/**
 * Quy tắc cảnh báo — định nghĩa điều kiện để kích hoạt cảnh báo.
 */
export interface AlertRule {
  /** Tên duy nhất của quy tắc. */
  name: string;
  /** Tên metric cần giám sát. */
  metric: string;
  /** Toán tử so sánh (> < >= <= == !=). */
  operator: string;
  /** Ngưỡng kích hoạt cảnh báo. */
  threshold: number;
  /** Mức độ nghiêm trọng. */
  severity: AlertSeverity;
  /** Thông điệp cảnh báo tùy chỉnh. */
  message: string;
  /** Khoảng thời gian đánh giá (giây). */
  evaluationInterval: number;
}

/**
 * Cảnh báo đang được kích hoạt.
 */
export interface FiredAlert {
  /** ID duy nhất của cảnh báo. */
  id: string;
  /** Tên của quy tắc kích hoạt cảnh báo. */
  ruleName: string;
  /** Mức độ nghiêm trọng. */
  severity: AlertSeverity;
  /** Trạng thái của cảnh báo. */
  status: AlertStatus;
  /** Thông điệp cảnh báo. */
  message: string;
  /** Giá trị metric hiện tại. */
  currentValue: number;
  /** Ngưỡng kích hoạt. */
  threshold: number;
  /** Thời điểm kích hoạt (ms epoch). */
  firedAt: number;
  /** Thời điểm xác nhận (nếu có). */
  acknowledgedAt?: number;
  /** Thời điểm giải quyết (nếu có). */
  resolvedAt?: number;
}

/**
 * Panel hiển thị metric trên dashboard.
 */
export interface Panel {
  /** Tên của panel. */
  name: string;
  /** Tên metric cần hiển thị. */
  metric: string;
  /** Đơn vị đo lường. */
  unit: string;
  /** Loại panel (gauge, counter, histogram, timeseries). */
  type: string;
  /** Ngưỡng cảnh báo (màu sắc thay đổi theo ngưỡng). */
  thresholds: number[];
  /** Mô tả panel. */
  description: string;
}

/**
 * Dashboard chứa nhiều panel để hiển thị metric.
 */
export interface Dashboard {
  /** Tên duy nhất của dashboard. */
  name: string;
  /** Danh sách các panel. */
  panels: Panel[];
  /** Mô tả dashboard. */
  description: string;
  /** Thời điểm tạo (ms epoch). */
  createdAt: number;
  /** Thời điểm cập nhật cuối (ms epoch). */
  updatedAt: number;
}

/**
 * Định nghĩa chỉ số mức độ dịch vụ (SLI).
 */
export interface SLIDefinition {
  /** Tên duy nhất của SLI. */
  name: string;
  /** Tên metric cần giám sát. */
  metric: string;
  /** Mục tiêu (ví dụ: 99.9 cho tỷ lệ thành công). */
  target: number;
  /** Cửa sổ đánh giá (giây). */
  window: number;
  /** Mô tả SLI. */
  description: string;
}

/**
 * Trạng thái hiện tại của SLI.
 */
export interface SLIStatus {
  /** Tên của SLI. */
  name: string;
  /** Giá trị hiện tại. */
  currentValue: number;
  /** Mục tiêu. */
  target: number;
  /** Có đạt mục tiêu hay không. */
  healthy: boolean;
  /** Bắt đầu cửa sổ đánh giá (ms epoch). */
  windowStart: number;
  /** Kết thúc cửa sổ đánh giá (ms epoch). */
  windowEnd: number;
  /** Số lượng mẫu trong cửa sổ. */
  samples: number;
}

/**
 * Dịch vụ chính cho monitoring.
 *
 * Quản lý dashboard, động cơ cảnh báo, và giám sát SLI
 * để cung cấp khả năng quan sát toàn diện cho ứng dụng.
 */
@Injectable()
export class MonitoringService {
  /** Danh sách dashboard. */
  private readonly dashboards: Map<string, Dashboard> = new Map();
  /** Danh sách quy tắc cảnh báo. */
  private readonly alertRules: Map<string, AlertRule> = new Map();
  /** Danh sách cảnh báo đang kích hoạt. */
  private readonly firedAlerts: FiredAlert[] = [];
  /** Định nghĩa SLI. */
  private readonly sliDefinitions: Map<string, SLIDefinition> = new Map();
  /** Mẫu metric cho SLI. */
  private readonly sliSamples: Map<string, number[]> = new Map();

  /**
   * Tạo dashboard mới với các panel hiển thị metric.
   *
   * @param name - Tên duy nhất của dashboard.
   * @param panels - Danh sách các panel hiển thị metric.
   * @param description - Mô tả dashboard.
   * @returns Dashboard mới được tạo.
   */
  createDashboard(name: string, panels: Panel[], description: string = \'\'): Dashboard {
    const dashboard: Dashboard = {
      name,
      panels,
      description,
      createdAt: Date.now(),
      updatedAt: Date.now(),
    };
    this.dashboards.set(name, dashboard);
    return dashboard;
  }

  /**
   * Lấy dashboard theo tên.
   *
   * @param name - Tên của dashboard.
   * @returns Dashboard nếu tìm thấy, ngược lại undefined.
   */
  getDashboard(name: string): Dashboard | undefined {
    return this.dashboards.get(name);
  }

  /**
   * Lấy tất cả dashboard đã tạo.
   *
   * @returns Mảng tất cả dashboard.
   */
  listDashboards(): Dashboard[] {
    return Array.from(this.dashboards.values());
  }

  /**
   * Thêm quy tắc cảnh báo mới.
   *
   * @param rule - Quy tắc cảnh báo cần thêm.
   */
  addAlertRule(rule: AlertRule): void {
    this.alertRules.set(rule.name, rule);
  }

  /**
   * Xóa quy tắc cảnh báo theo tên.
   *
   * @param name - Tên của quy tắc cần xóa.
   * @returns True nếu xóa thành công, False nếu không tồn tại.
   */
  removeAlertRule(name: string): boolean {
    return this.alertRules.delete(name);
  }

  /**
   * Đánh giá tất cả quy tắc cảnh báo với metric hiện tại.
   *
   * @param metrics - Bản đồ metric theo tên và giá trị hiện tại.
   * @returns Mảng cảnh báo mới được kích hoạt.
   */
  evaluateAlerts(metrics: Record<string, number>): FiredAlert[] {
    const newAlerts: FiredAlert[] = [];

    for (const rule of this.alertRules.values()) {
      const value = metrics[rule.metric];
      if (value === undefined) continue;

      const triggered = this._evaluateCondition(value, rule.operator, rule.threshold);
      if (triggered) {
        const alert: FiredAlert = {
          id: this._uuid(),
          ruleName: rule.name,
          severity: rule.severity,
          status: AlertStatus.ACTIVE,
          message: rule.message,
          currentValue: value,
          threshold: rule.threshold,
          firedAt: Date.now(),
        };
        this.firedAlerts.push(alert);
        newAlerts.push(alert);
      }
    }

    return newAlerts;
  }

  /**
   * Lấy tất cả cảnh báo đang kích hoạt.
   *
   * @returns Mảng cảnh báo có trạng thái ACTIVE hoặc ACKNOWLEDGED.
   */
  getFiredAlerts(): FiredAlert[] {
    return this.firedAlerts.filter(
      (a) => a.status === AlertStatus.ACTIVE || a.status === AlertStatus.ACKNOWLEDGED,
    );
  }

  /**
   * Giải quyết tất cả cảnh báo đang kích hoạt.
   *
   * @returns Số lượng cảnh báo đã được giải quyết.
   */
  resolveAllAlerts(): number {
    let count = 0;
    for (const alert of this.firedAlerts) {
      if (alert.status === AlertStatus.ACTIVE || alert.status === AlertStatus.ACKNOWLEDGED) {
        alert.status = AlertStatus.RESOLVED;
        alert.resolvedAt = Date.now();
        count++;
      }
    }
    return count;
  }

  /**
   * Thêm định nghĩa SLI mới.
   *
   * @param definition - Định nghĩa SLI cần thêm.
   */
  addSLIDefinition(definition: SLIDefinition): void {
    this.sliDefinitions.set(definition.name, definition);
    this.sliSamples.set(definition.name, []);
  }

  /**
   * Ghi nhận mẫu metric cho SLI.
   *
   * @param name - Tên của SLI.
   * @param value - Giá trị mẫu metric.
   */
  recordSLISample(name: string, value: number): void {
    const samples = this.sliSamples.get(name) || [];
    samples.push(value);
    this.sliSamples.set(name, samples);
  }

  /**
   * Kiểm tra trạng thái của tất cả SLI.
   *
   * @returns Mảng trạng thái SLI hiện tại.
   */
  checkSlis(): SLIStatus[] {
    const statuses: SLIStatus[] = [];
    const now = Date.now();

    for (const [name, definition] of this.sliDefinitions) {
      const samples = this.sliSamples.get(name) || [];
      const windowMs = definition.window * 1000;
      const windowStart = now - windowMs;

      // Lọc mẫu trong cửa sổ thời gian
      const windowed = samples.filter((s) => s >= windowStart);
      const currentValue = windowed.length > 0 ? windowed.reduce((a, b) => a + b, 0) / windowed.length : 0;

      statuses.push({
        name,
        currentValue,
        target: definition.target,
        healthy: currentValue >= definition.target,
        windowStart,
        windowEnd: now,
        samples: windowed.length,
      });
    }

    return statuses;
  }

  /**
   * Lấy tất cả định nghĩa SLI.
   *
   * @returns Mảng định nghĩa SLI.
   */
  getSLIDefinitions(): SLIDefinition[] {
    return Array.from(this.sliDefinitions.values());
  }

  /**
   * Đánh giá điều kiện so sánh giữa giá trị và ngưỡng.
   *
   * @param value - Giá trị metric hiện tại.
   * @param operator - Toán tử so sánh.
   * @param threshold - Ngưỡng so sánh.
   * @returns True nếu điều kiện được thỏa mãn.
   */
  private _evaluateCondition(value: number, operator: string, threshold: number): boolean {
    switch (operator) {
      case \'>\': return value > threshold;
      case \'>=\': return value >= threshold;
      case \'<\': return value < threshold;
      case \'<=\': return value <= threshold;
      case \'==\': return value === threshold;
      case \'!=\': return value !== threshold;
      default: return false;
    }
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
        return {"src/monitoring/monitoring.service.ts": code}

    def generate_controller(self) -> Dict[str, str]:
        """Tạo NestJS controller cho các endpoint monitoring."""
        code = '''\
/**
 * Controller monitoring — endpoint REST cho dashboard, cảnh báo, và SLI.
 *
 * Cung cấp API cho phía client để truy vấn và quản lý
 * dashboard, quy tắc cảnh báo, và trạng thái SLI.
 */
import {
  Controller,
  Get,
  Post,
  Body,
  Param,
  Query,
} from \'@nestjs/common\';
import { MonitoringService, Dashboard, FiredAlert, SLIStatus, AlertRule } from \'./monitoring.service\';

/**
 * Controller cho endpoint monitoring.
 *
 * Quản lý các route REST để truy vấn dashboard,
 * thêm/xóa quy tắc cảnh báo, và kiểm tra trạng thái SLI.
 */
@Controller(\'monitoring\')
export class MonitoringController {
  constructor(private readonly monitoring: MonitoringService) {}

  /**
   * Liệt kê tất cả dashboard.
   *
   * @returns Mảng dashboard.
   */
  @Get(\'dashboards\')
  listDashboards(): Dashboard[] {
    return this.monitoring.listDashboards();
  }

  /**
   * Lấy thông tin chi tiết của một dashboard.
   *
   * @param name - Tên của dashboard.
   * @returns Dashboard nếu tìm thấy, ngược lại undefined.
   */
  @Get(\'dashboards/:name\')
  getDashboard(@Param(\'name\') name: string): Dashboard | undefined {
    return this.monitoring.getDashboard(name);
  }

  /**
   * Thêm quy tắc cảnh báo mới.
   *
   * @param rule - Quy tắc cảnh báo cần thêm.
   * @returns Quy tắc đã thêm.
   */
  @Post(\'alerts\')
  addAlertRule(@Body() rule: AlertRule): AlertRule {
    this.monitoring.addAlertRule(rule);
    return rule;
  }

  /**
   * Lấy tất cả cảnh báo đang kích hoạt.
   *
   * @returns Mảng cảnh báo đang kích hoạt.
   */
  @Get(\'alerts\')
  getFiredAlerts(): FiredAlert[] {
    return this.monitoring.getFiredAlerts();
  }

  /**
   * Đánh giá tất cả quy tắc cảnh báo với metric hiện tại.
   *
   * @param metrics - Bản đồ metric theo tên và giá trị.
   * @returns Kết quả đánh giá với danh sách cảnh báo mới.
   */
  @Post(\'alerts/evaluate\')
  evaluateAlerts(@Body() metrics: Record<string, number>) {
    const newAlerts = this.monitoring.evaluateAlerts(metrics);
    return {
      evaluatedAt: Date.now(),
      newAlertsCount: newAlerts.length,
      newAlerts,
    };
  }

  /**
   * Lấy trạng thái hiện tại của tất cả SLI.
   *
   * @returns Mảng trạng thái SLI.
   */
  @Get(\'slis\')
  getSLIStatus(): SLIStatus[] {
    return this.monitoring.checkSlis();
  }

  /**
   * Giải quyết tất cả cảnh báo đang kích hoạt.
   *
   * @returns Số lượng cảnh báo đã được giải quyết.
   */
  @Post(\'alerts/resolve-all\')
  resolveAllAlerts(): { resolved: number } {
    const count = this.monitoring.resolveAllAlerts();
    return { resolved: count };
  }
}
'''
        return {"src/monitoring/monitoring.controller.ts": code}
