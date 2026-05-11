from __future__ import annotations

from typing import Any, Dict


class AngularMonitoringEmitter:
    """Emitter cho các thành phần monitoring của Angular."""

    def __init__(self, collection: Any | None = None):
        self.collection = collection or {}

    def generate(self) -> Dict[str, str]:
        """Tạo tất cả các tệp monitoring cho Angular."""
        result: Dict[str, str] = {}
        result.update(self.generate_dashboard_widget())
        result.update(self.generate_alert_panel())
        return result

    def generate_dashboard_widget(self) -> Dict[str, str]:
        """Tạo DashboardWidget component — hiển thị dashboard panels với metric."""
        code = '''\
/**
 * Component widget dashboard — hiển thị các panel metric trên dashboard monitoring.
 *
 * Kết nối với API monitoring để tải danh sách dashboard và hiển thị
 * các panel metric với thông tin thời gian thực.
 */
import { Component, OnInit, OnDestroy, ChangeDetectionStrategy } from \'@angular/core\';
import { CommonModule } from \'@angular/common\';
import { HttpClient } from \'@angular/common/http\';
import { Subscription } from \'rxjs\';

/**
 * Mức độ nghiêm trọng của cảnh báo.
 */
export type AlertSeverity = \'INFO\' | \'WARNING\' | \'CRITICAL\' | \'FATAL\';

/**
 * Một panel hiển thị metric trên dashboard.
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
  /** Ngưỡng cảnh báo. */
  thresholds: number[];
  /** Mô tả panel. */
  description: string;
}

/**
 * Dashboard chứa nhiều panel.
 */
export interface Dashboard {
  /** Tên duy nhất của dashboard. */
  name: string;
  /** Danh sách các panel. */
  panels: Panel[];
  /** Mô tả dashboard. */
  description: string;
  /** Thời điểm tạo (ms epoch). */
  created_at: number;
  /** Thời điểm cập nhật cuối (ms epoch). */
  updated_at: number;
}

/**
 * Thành phần panel metric — giá trị hiện tại và trạng thái.
 */
interface MetricPanelState {
  panel: Panel;
  value: number;
  healthy: boolean;
}

/**
 * Component widget dashboard.
 *
 * Hiển thị danh sách dashboard và các panel metric bên trong,
 * tự động làm mới dữ liệu theo khoảng thời gian định kỳ.
 */
@Component({
  selector: \'app-dashboard-widget\',
  standalone: true,
  imports: [CommonModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="dashboard-widget">
      <h2>{{ dashboard?.name || \'Dashboard\' }}</h2>
      <p *ngIf="dashboard?.description" class="dashboard-description">
        {{ dashboard.description }}
      </p>

      <!-- Trạng thái tải -->
      <div *ngIf="loading" class="dashboard-loading">
        Đang tải dữ liệu dashboard...
      </div>

      <!-- Danh sách panel -->
      <div *ngIf="!loading" class="dashboard-panels">
        <div
          *ngFor="let panelState of panelStates"
          [class]="'panel panel--' + panelState.panel.type + ' panel--' + (panelState.healthy ? \'healthy\' : \'unhealthy\')"
        >
          <div class="panel-header">
            <h3>{{ panelState.panel.name }}</h3>
            <span *ngIf="!panelState.healthy" class="panel-badge panel-badge--unhealthy">
              Cảnh báo
            </span>
          </div>

          <div class="panel-body">
            <span class="panel-value">{{ panelState.value | number:\'.2-2\' }}</span>
            <span class="panel-unit">{{ panelState.panel.unit }}</span>
          </div>

          <div class="panel-footer">
            <span class="panel-metric">{{ panelState.panel.metric }}</span>
            <span *ngIf="panelState.panel.description" class="panel-description">
              {{ panelState.panel.description }}
            </span>
          </div>
        </div>
      </div>

      <!-- Thông báo trống -->
      <div *ngIf="!loading && panelStates.length === 0" class="dashboard-empty">
        Không có panel nào trên dashboard.
      </div>

      <!-- Nút làm mới -->
      <button (click)="loadDashboard()" class="refresh-btn" [disabled]="loading">
        {{ loading ? \'Đang tải...\' : \'Làm mới\' }}
      </button>
    </div>
  `,
  styles: [`
    .dashboard-widget {
      padding: 16px;
      font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif;
    }
    .dashboard-description {
      color: #666;
      margin-bottom: 16px;
    }
    .dashboard-panels {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 16px;
      margin-bottom: 16px;
    }
    .panel {
      border: 1px solid #e0e0e0;
      border-radius: 8px;
      padding: 16px;
      background: #fff;
      transition: box-shadow 0.2s;
    }
    .panel:hover {
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
    .panel--unhealthy {
      border-color: #f44336;
    }
    .panel-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
    }
    .panel-header h3 {
      margin: 0;
      font-size: 14px;
      font-weight: 600;
    }
    .panel-badge {
      font-size: 11px;
      padding: 2px 8px;
      border-radius: 12px;
      font-weight: 500;
    }
    .panel-badge--unhealthy {
      background: #ffebee;
      color: #c62828;
    }
    .panel-body {
      display: flex;
      align-items: baseline;
      gap: 8px;
      margin-bottom: 8px;
    }
    .panel-value {
      font-size: 32px;
      font-weight: 700;
      font-variant-numeric: tabular-nums;
    }
    .panel-unit {
      font-size: 14px;
      color: #666;
    }
    .panel-footer {
      display: flex;
      flex-direction: column;
      gap: 4px;
    }
    .panel-metric {
      font-size: 12px;
      color: #999;
      font-family: monospace;
    }
    .panel-description {
      font-size: 12px;
      color: #666;
    }
    .dashboard-loading, .dashboard-empty {
      text-align: center;
      padding: 32px;
      color: #666;
    }
    .refresh-btn {
      margin-top: 8px;
      padding: 8px 16px;
      border: 1px solid #e0e0e0;
      border-radius: 4px;
      background: #fff;
      cursor: pointer;
    }
    .refresh-btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
  `],
})
export class DashboardWidgetComponent implements OnInit, OnDestroy {
  /** URL cơ sở của API monitoring. */
  private readonly apiBaseUrl = \'/api\';

  /** Dashboard hiện tại. */
  dashboard: Dashboard | null = null;

  /** Trạng thái của từng panel. */
  panelStates: MetricPanelState[] = [];

  /** Trạng thái tải. */
  loading = false;

  /** Subscription để dọn dẹp. */
  private sub?: Subscription;
  private refreshTimer?: ReturnType<typeof setInterval>;

  /**
   * Khoảng thời gian tự động làm mới (ms).
   */
  private readonly refreshInterval = 30000;

  /** Tên dashboard mặc định. */
  private readonly defaultDashboard = \'main\';

  ngOnInit(): void {
    this.loadDashboard();
    // Tự động làm mới dữ liệu
    this.refreshTimer = setInterval(() => {
      this.loadDashboard();
    }, this.refreshInterval);
  }

  ngOnDestroy(): void {
    this.sub?.unsubscribe();
    if (this.refreshTimer) clearInterval(this.refreshTimer);
  }

  /**
   * Tải dashboard từ API backend.
   */
  loadDashboard(): void {
    this.loading = true;
    const http = new HttpClient();

    this.sub = http
      .get<Dashboard>(`${this.apiBaseUrl}/monitoring/dashboards/${this.defaultDashboard}`)
      .subscribe({
        next: (data) => {
          this.dashboard = data;
          this.panelStates = data.panels.map((panel) => ({
            panel,
            value: this._generateSampleValue(panel),
            healthy: this._isHealthy(this._generateSampleValue(panel), panel.thresholds),
          }));
          this.loading = false;
        },
        error: (err) => {
          console.error(\'Lỗi khi tải dashboard:\', err);
          this.loading = false;
        },
      });
  }

  /**
   * Tạo giá trị mẫu cho panel (trong thực tế sẽ lấy từ API metric).
   */
  private _generateSampleValue(panel: Panel): number {
    // Giả lập giá trị — trong thực tế sẽ gọi API metric
    return Math.random() * 100;
  }

  /**
   * Kiểm tra panel có đạt ngưỡng hay không.
   */
  private _isHealthy(value: number, thresholds: number[]): boolean {
    if (thresholds.length === 0) return true;
    // Ngưỡng đầu tiên là ngưỡng cảnh báo
    return value < thresholds[0];
  }
}
'''
        return {"src/app/core/monitoring/dashboard_widget.component.ts": code}

    def generate_alert_panel(self) -> Dict[str, str]:
        """Tạo AlertPanel component — hiển thị cảnh báo với severity badge."""
        code = '''\
/**
 * Component hiển thị danh sách cảnh báo đang kích hoạt với badge mức độ nghiêm trọng.
 *
 * Kết nối với API monitoring để tải danh sách cảnh báo và hiển thị
 * dưới dạng danh sách có thể lọc theo mức độ và xác nhận/giải quyết.
 */
import { Component, OnInit, OnDestroy, ChangeDetectionStrategy } from \'@angular/core\';
import { CommonModule } from \'@angular/common\';
import { FormsModule } from \'@angular/forms\';
import { HttpClient } from \'@angular/common/http\';
import { Subscription } from \'rxjs\';

/**
 * Mức độ nghiêm trọng của cảnh báo.
 */
export type AlertSeverity = \'INFO\' | \'WARNING\' | \'CRITICAL\' | \'FATAL\';

/**
 * Trạng thái của cảnh báo.
 */
export type AlertStatus = \'ACTIVE\' | \'RESOLVED\' | \'ACKNOWLEDGED\';

/**
 * Một cảnh báo đang được kích hoạt.
 */
export interface FiredAlert {
  /** ID duy nhất của cảnh báo. */
  id: string;
  /** Tên của quy tắc kích hoạt cảnh báo. */
  rule_name: string;
  /** Mức độ nghiêm trọng. */
  severity: AlertSeverity;
  /** Trạng thái của cảnh báo. */
  status: AlertStatus;
  /** Thông điệp cảnh báo. */
  message: string;
  /** Giá trị metric hiện tại. */
  current_value: number;
  /** Ngưỡng kích hoạt. */
  threshold: number;
  /** Thời điểm kích hoạt (ms epoch). */
  fired_at: number;
  /** Thời điểm xác nhận (nếu có). */
  acknowledged_at?: number;
  /** Thời điểm giải quyết (nếu có). */
  resolved_at?: number;
}

/**
 * Màu sắc tương ứng với mỗi mức độ nghiêm trọng.
 */
const SEVERITY_COLORS: Record<AlertSeverity, string> = {
  INFO: \'#2196f3\',
  WARNING: \'#ff9800\',
  CRITICAL: \'#f44336\',
  FATAL: \'#9c27b0\',
};

/**
 * Component bảng cảnh báo.
 *
 * Hiển thị danh sách cảnh báo đang kích hoạt với:
 * - Badge màu theo mức độ nghiêm trọng
 * - Lọc theo mức độ
 * - Xác nhận và giải quyết cảnh báo
 * - Tự động làm mới dữ liệu
 */
@Component({
  selector: \'app-alert-panel\',
  standalone: true,
  imports: [CommonModule, FormsModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="alert-panel">
      <h2>Cảnh Báo Đang Kích Hoạt</h2>

      <!-- Bộ lọc theo mức độ -->
      <div class="alert-filters">
        <label for="severity-filter">
          Mức độ:{\'\'}
          <select
            id="severity-filter"
            [(ngModel)]="severityFilter"
            (change)="onFilterChange()"
          >
            <option [ngValue]="null">Tất cả</option>
            <option value="INFO">INFO</option>
            <option value="WARNING">WARNING</option>
            <option value="CRITICAL">CRITICAL</option>
            <option value="FATAL">FATAL</option>
          </select>
        </label>

        <span class="alert-count">
          {{ filteredAlerts.length }} cảnh báo
        </span>
      </div>

      <!-- Trạng thái tải -->
      <div *ngIf="loading" class="alert-loading">
        Đang tải cảnh báo...
      </div>

      <!-- Danh sách cảnh báo -->
      <div *ngIf="!loading && filteredAlerts.length === 0" class="alert-empty">
        Không có cảnh báo nào đang kích hoạt.
      </div>

      <div *ngIf="!loading && filteredAlerts.length > 0" class="alert-list">
        <div
          *ngFor="let alert of filteredAlerts"
          [class]="'alert-item alert-item--' + alert.severity.toLowerCase() + ' alert-item--' + alert.status.toLowerCase()"
        >
          <!-- Badge mức độ nghiêm trọng -->
          <span
            class="alert-severity-badge"
            [style.borderColor]="getSeverityColor(alert.severity)"
          >
            {{ alert.severity }}
          </span>

          <!-- Nội dung cảnh báo -->
          <div class="alert-content">
            <div class="alert-title">
              <span class="alert-rule">{{ alert.rule_name }}</span>
              <span *ngIf="alert.status === \'ACKNOWLEDGED\'" class="alert-ack-badge">
                Đã xác nhận
              </span>
            </div>
            <p class="alert-message">{{ alert.message }}</p>
            <div class="alert-details">
              <span>Giá trị: {{ alert.current_value }}</span>
              <span>Ngưỡng: {{ alert.threshold }}</span>
            </div>
            <div class="alert-time">
              Kích hoạt: {{ alert.fired_at | date:\'medium\' }}
            </div>
          </div>

          <!-- Hành động -->
          <div class="alert-actions">
            <button
              *ngIf="alert.status === \'ACTIVE\'"
              (click)="acknowledgeAlert(alert.id)"
              class="btn btn--ack"
            >
              Xác nhận
            </button>
            <button
              *ngIf="alert.status !== \'RESOLVED\'"
              (click)="resolveAlert(alert.id)"
              class="btn btn--resolve"
            >
              Giải quyết
            </button>
          </div>
        </div>
      </div>

      <!-- Nút làm mới -->
      <button (click)="loadAlerts()" class="refresh-btn" [disabled]="loading">
        {{ loading ? \'Đang tải...\' : \'Làm mới\' }}
      </button>
    </div>
  `,
  styles: [`
    .alert-panel {
      padding: 16px;
      font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif;
    }
    .alert-filters {
      display: flex;
      gap: 16px;
      margin-bottom: 16px;
      align-items: center;
    }
    .alert-count {
      font-size: 14px;
      color: #666;
    }
    .alert-list {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .alert-item {
      display: flex;
      gap: 12px;
      padding: 12px;
      border: 1px solid #e0e0e0;
      border-radius: 8px;
      background: #fff;
      align-items: flex-start;
    }
    .alert-item--critical {
      border-left: 4px solid #f44336;
    }
    .alert-item--fatal {
      border-left: 4px solid #9c27b0;
    }
    .alert-item--warning {
      border-left: 4px solid #ff9800;
    }
    .alert-item--info {
      border-left: 4px solid #2196f3;
    }
    .alert-item--acknowledged {
      opacity: 0.7;
      background: #f5f5f5;
    }
    .alert-severity-badge {
      font-size: 11px;
      font-weight: 600;
      padding: 2px 8px;
      border-radius: 12px;
      border: 1px solid;
      min-width: 70px;
      text-align: center;
      flex-shrink: 0;
    }
    .alert-content {
      flex: 1;
      min-width: 0;
    }
    .alert-title {
      display: flex;
      gap: 8px;
      align-items: center;
      margin-bottom: 4px;
    }
    .alert-rule {
      font-weight: 600;
      font-size: 14px;
    }
    .alert-ack-badge {
      font-size: 11px;
      padding: 1px 6px;
      border-radius: 8px;
      background: #e0e0e0;
      color: #666;
    }
    .alert-message {
      margin: 4px 0;
      font-size: 13px;
      color: #333;
    }
    .alert-details {
      display: flex;
      gap: 16px;
      font-size: 12px;
      color: #666;
      font-family: monospace;
    }
    .alert-time {
      font-size: 11px;
      color: #999;
      margin-top: 4px;
    }
    .alert-actions {
      display: flex;
      gap: 8px;
      flex-shrink: 0;
    }
    .btn {
      padding: 4px 12px;
      border: 1px solid #e0e0e0;
      border-radius: 4px;
      background: #fff;
      font-size: 12px;
      cursor: pointer;
    }
    .btn--ack {
      border-color: #ff9800;
      color: #e65100;
    }
    .btn--resolve {
      border-color: #4caf50;
      color: #2e7d32;
    }
    .alert-loading, .alert-empty {
      text-align: center;
      padding: 32px;
      color: #666;
    }
    .refresh-btn {
      margin-top: 16px;
      padding: 8px 16px;
      border: 1px solid #e0e0e0;
      border-radius: 4px;
      background: #fff;
      cursor: pointer;
    }
    .refresh-btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
  `],
})
export class AlertPanelComponent implements OnInit, OnDestroy {
  /** URL cơ sở của API monitoring. */
  private readonly apiBaseUrl = \'/api\';

  /** Danh sách cảnh báo. */
  alerts: FiredAlert[] = [];

  /** Bộ lọc mức độ. */
  severityFilter: AlertSeverity | null = null;

  /** Trạng thái tải. */
  loading = false;

  /** Subscription để dọn dẹp. */
  private sub?: Subscription;
  private refreshTimer?: ReturnType<typeof setInterval>;

  /** Màu sắc theo mức độ nghiêm trọng. */
  readonly severityColors = SEVERITY_COLORS;

  /** Khoảng thời gian tự động làm mới (ms). */
  private readonly refreshInterval = 15000;

  ngOnInit(): void {
    this.loadAlerts();
    // Tự động làm mới dữ liệu cảnh báo
    this.refreshTimer = setInterval(() => {
      this.loadAlerts();
    }, this.refreshInterval);
  }

  ngOnDestroy(): void {
    this.sub?.unsubscribe();
    if (this.refreshTimer) clearInterval(this.refreshTimer);
  }

  /**
   * Lấy danh sách cảnh báo đã lọc.
   */
  get filteredAlerts(): FiredAlert[] {
    if (!this.severityFilter) return this.alerts;
    return this.alerts.filter((a) => a.severity === this.severityFilter);
  }

  /**
   * Tải danh sách cảnh báo từ API backend.
   */
  loadAlerts(): void {
    this.loading = true;
    const http = new HttpClient();

    this.sub = http.get<FiredAlert[]>(`${this.apiBaseUrl}/monitoring/alerts`).subscribe({
      next: (data) => {
        this.alerts = data;
        this.loading = false;
      },
      error: (err) => {
        console.error(\'Lỗi khi tải cảnh báo:\', err);
        this.loading = false;
      },
    });
  }

  /**
   * Xử lý khi bộ lọc thay đổi.
   */
  onFilterChange(): void {
    // Việc lọc được xử lý tự động qua filteredAlerts getter
  }

  /**
   * Xác nhận cảnh báo.
   *
   * @param alertId - ID của cảnh báo cần xác nhận.
   */
  acknowledgeAlert(alertId: string): void {
    const alert = this.alerts.find((a) => a.id === alertId);
    if (alert) {
      alert.status = \'ACKNOWLEDGED\';
      alert.acknowledged_at = Date.now();
    }
  }

  /**
   * Giải quyết cảnh báo.
   *
   * @param alertId - ID của cảnh báo cần giải quyết.
   */
  resolveAlert(alertId: string): void {
    const alert = this.alerts.find((a) => a.id === alertId);
    if (alert) {
      alert.status = \'RESOLVED\';
      alert.resolved_at = Date.now();
    }
  }

  /**
   * Lấy màu sắc theo mức độ nghiêm trọng.
   *
   * @param severity - Mức độ nghiêm trọng.
   * @returns Màu sắc tương ứng.
   */
  getSeverityColor(severity: AlertSeverity): string {
    return SEVERITY_COLORS[severity];
  }
}
'''
        return {"src/app/core/monitoring/alert_panel.component.ts": code}
