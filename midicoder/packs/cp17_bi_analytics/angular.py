from __future__ import annotations

from typing import Any, Dict


class AngularAnalyticsEmitter:
    """Emitter cho các thành phần Business Intelligence & Analytics của Angular."""

    def __init__(self, collection: Any | None = None):
        self.collection = collection or {}

    def generate(self) -> Dict[str, str]:
        """Tạo tất cả các tệp analytics cho Angular."""
        result: Dict[str, str] = {}
        result.update(self.generate_analytics_widget())
        result.update(self.generate_report_viewer())
        return result

    def generate_analytics_widget(self) -> Dict[str, str]:
        """Tạo AnalyticsWidgetComponent — hiển thị biểu đồ phân tích và dashboard."""
        code = '''\
/**
 * Analytics Widget Component — hiển thị biểu đồ phân tích và dashboard.
 *
 * Thành phần này cung cấp giao diện để xem các chỉ số phân tích dưới dạng
 * biểu đồ đường, biểu đồ cột, biểu đồ tròn, và đồng hồ đo. Hỗ trợ làm mới
 * dữ liệu và chuyển đổi giữa các loại biểu đồ.
 */
import {
  Component,
  OnInit,
  OnDestroy,
  ChangeDetectionStrategy,
} from "@angular/core";
import { CommonModule } from "@angular/common";
import { FormsModule, ReactiveFormsModule, FormGroup, FormControl } from "@angular/forms";
import {
  MatCardModule,
  MatButtonModule,
  MatSelectModule,
  MatProgressBarModule,
  MatIconModule,
  MatSnackBarModule,
  MatTabsModule,
  MatGridListModule,
  MatInputModule,
} from "@angular/material";
import { Observable, Subscription, interval, BehaviorSubject, Subject } from "rxjs";
import { takeUntil, switchMap } from "rxjs/operators";

/**
 * Loại biểu đồ được hỗ trợ.
 */
export enum ChartType {
  LINE = "LINE",
  BAR = "BAR",
  PIE = "PIE",
  GAUGE = "GAUGE",
  TABLE = "TABLE",
}

/**
 * Một điểm dữ liệu cho biểu đồ.
 */
export interface DataPoint {
  /** Nhãn của điểm dữ liệu. */
  label: string;
  /** Giá trị số của điểm dữ liệu. */
  value: number;
  /** Mảng giá trị cho biểu đồ đường đa series. */
  values?: number[];
}

/**
 * Cấu hình của một widget hiển thị trên dashboard.
 */
export interface WidgetConfig {
  /** Tiêu đề của widget. */
  title: string;
  /** Loại biểu đồ. */
  chartType: ChartType;
  /** Tên chỉ số. */
  metric: string;
  /** Dữ liệu hiện tại của widget. */
  data: DataPoint[];
  /** Đơn vị hiển thị (ví dụ: %, $. */
  unit?: string;
  /** Màu chủ đạo của biểu đồ. */
  color?: string;
}

/**
 * Chỉ số KPI — hiển thị giá trị tổng hợp.
 */
export interface KpiMetric {
  /** Tên của chỉ số KPI. */
  name: string;
  /** Giá trị hiện tại. */
  value: number;
  /** Giá trị trước đó để so sánh. */
  previousValue: number;
  /** Đơn vị hiển thị. */
  unit: string;
  /** Màu sắc dựa trên xu hướng. */
  trendColor: "positive" | "negative" | "neutral";
}

/**
 * Dữ liệu dashboard tổng hợp.
 */
export interface DashboardData {
  /** Danh sách widget cấu hình. */
  widgets: WidgetConfig[];
  /** Danh sách chỉ số KPI. */
  kpis: KpiMetric[];
  /** Thời điểm cập nhật cuối cùng (ms epoch). */
  lastUpdated: number;
}

@Component({
  selector: "analytics-widget",
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    MatCardModule,
    MatButtonModule,
    MatSelectModule,
    MatProgressBarModule,
    MatIconModule,
    MatSnackBarModule,
    MatTabsModule,
    MatGridListModule,
    MatInputModule,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <!-- Thẻ container chính cho dashboard analytics -->
    <mat-card>
      <mat-card-header>
        <mat-card-title>Bảng Điều Khiển Phân Tích</mat-card-title>
        <mat-card-subtitle>
          Cập nhật cuối: {{ lastUpdated$ | date:"dd/MM/yyyy HH:mm:ss" }}
        </mat-card-subtitle>
      </mat-card-header>

      <mat-card-content>
        <!-- Thanh điều khiển: chọn widget và làm mới -->
        <div class="controls-bar">
          <mat-form-field appearance="outline">
            <mat-label>Chọn Widget</mat-label>
            <mat-select
              [(value)]="selectedWidgetIndex"
              (selectionChange)="onWidgetSelected()"
            >
              <mat-option
                *ngFor="let widget of dashboardData?.widgets; let i = index"
                [value]="i"
              >
                {{ widget.title }}
              </mat-option>
            </mat-select>
          </mat-form-field>

          <mat-form-field appearance="outline">
            <mat-label>Loại Biểu Đồ</mat-label>
            <mat-select [(value)]="selectedChartType" (selectionChange)="onChartTypeChanged()">
              <mat-option [value]="chartTypes.LINE">Đường</mat-option>
              <mat-option [value]="chartTypes.BAR">Cột</mat-option>
              <mat-option [value]="chartTypes.PIE">Tròn</mat-option>
              <mat-option [value]="chartTypes.GAUGE">Đồng hồ</mat-option>
              <mat-option [value]="chartTypes.TABLE">Bảng</mat-option>
            </mat-select>
          </mat-form-field>

          <button
            mat-raised-button
            color="primary"
            (click)="onRefresh()"
            [disabled]="loading"
          >
            <mat-icon>refresh</mat-icon>
            Làm Mới
          </button>

          <button
            mat-stroked-button
            (click)="toggleAutoRefresh()"
            [color]="autoRefresh ? 'accent' : 'basic'"
          >
            <mat-icon>{{ autoRefresh ? "autorenew" : "autorenew" }}</mat-icon>
            {{ autoRefresh ? "Tự Động: Bật" : "Tự Động: Tắt" }}
          </button>
        </div>

        <!-- Thanh tiến trình khi đang tải dữ liệu -->
        <mat-progress-bar
          *ngIf="loading"
          mode="indeterminate"
        ></mat-progress-bar>

        <!-- Phần hiển thị KPI tổng hợp -->
        <section class="kpi-section">
          <h3>Chỉ Số Tổng Hợp</h3>
          <mat-grid-list cols="4" rowHeight="120px" gutterSize="8px">
            <mat-grid-tile
              *ngFor="let kpi of dashboardData?.kpis"
              [style.background]="getKpiBackgroundColor(kpi.trendColor)"
            >
              <div class="kpi-content">
                <span class="kpi-name">{{ kpi.name }}</span>
                <span class="kpi-value">
                  {{ kpi.value | number:"1.2-2" }}{{ kpi.unit }}
                </span>
                <span class="kpi-trend" [class]="kpi.trendColor">
                  {{ getTrendLabel(kpi) }}
                </span>
              </div>
            </mat-grid-tile>
          </mat-grid-list>
        </section>

        <!-- Tab hiển thị widget biểu đồ -->
        <mat-tab-group>
          <mat-tab
            *ngFor="let widget of dashboardData?.widgets; let i = index"
            [label]="widget.title"
          >
            <!-- Khu vực hiển thị biểu đồ -->
            <div class="chart-container">
              <!-- Biểu đồ cột -->
              <ng-container *ngIf="widget.chartType === chartTypes.BAR">
                <div class="bar-chart">
                  <div
                    *ngFor="let point of widget.data"
                    class="bar-item"
                  >
                    <div
                      class="bar-fill"
                      [style.height.%]="getBarHeight(point, widget.data)"
                      [style.background]="widget.color || '#1976d2'"
                    ></div>
                    <span class="bar-label">{{ point.label }}</span>
                    <span class="bar-value">{{ point.value | number:"1.2-2" }}</span>
                  </div>
                </div>
              </ng-container>

              <!-- Biểu đồ đường -->
              <ng-container *ngIf="widget.chartType === chartTypes.LINE">
                <div class="line-chart">
                  <svg width="100%" height="300" viewBox="0 0 800 300">
                    <polyline
                      *ngFor="let series of getLineSeries(widget.data)"
                      [attr.points]="getLinePoints(series, widget.data)"
                      [attr.stroke]="series.color"
                      fill="none"
                      stroke-width="2"
                    ></polyline>
                    <circle
                      *ngFor="let point of widget.data; let i = index"
                      cx="{{ (i / widget.data.length) * 800 }}"
                      cy="{{ 300 - (point.value / getMaxValue(widget.data)) * 300 }}"
                      r="4"
                      [attr.fill]="widget.color || '#1976d2'"
                    ></circle>
                  </svg>
                </div>
              </ng-container>

              <!-- Biểu đồ tròn -->
              <ng-container *ngIf="widget.chartType === chartTypes.PIE">
                <div class="pie-chart">
                  <svg width="300" height="300" viewBox="0 0 300 300">
                    <circle
                      *ngFor="let point of widget.data; let i = index"
                      cx="150"
                      cy="150"
                      r="120"
                      [attr.stroke]="getPieColor(i)"
                      [attr.stroke-width]="120"
                      [attr.stroke-dasharray]="getPieDashArray(point, widget.data)"
                      [attr.stroke-dashoffset]="getPieOffset(point, widget.data)"
                      fill="transparent"
                    ></circle>
                  </svg>
                  <div class="pie-legend">
                    <div
                      *ngFor="let point of widget.data; let i = index"
                      class="legend-item"
                    >
                      <span
                        class="legend-color"
                        [style.background]="getPieColor(i)"
                      ></span>
                      <span>{{ point.label }}: {{ point.value }}</span>
                    </div>
                  </div>
                </div>
              </ng-container>

              <!-- Đồng hồ đo -->
              <ng-container *ngIf="widget.chartType === chartTypes.GAUGE">
                <div class="gauge-chart">
                  <svg width="200" height="120" viewBox="0 0 200 120">
                    <path
                      d="M 10 110 A 90 90 0 0 1 190 110"
                      fill="none"
                      stroke="#e0e0e0"
                      stroke-width="20"
                    ></path>
                    <path
                      d="M 10 110 A 90 90 0 0 1 190 110"
                      fill="none"
                      [attr.stroke]="widget.color || '#4caf50'"
                      stroke-width="20"
                      [attr.stroke-dasharray]="getGaugeDash(widget.data)"
                      [attr.stroke-dashoffset]="getGaugeOffset(widget.data)"
                    ></path>
                    <text x="100" y="100" text-anchor="middle" font-size="24">
                      {{ widget.data[0]?.value | number:"1.2-2" }}
                      {{ widget.unit }}
                    </text>
                  </svg>
                </div>
              </ng-container>

              <!-- Bảng dữ liệu -->
              <ng-container *ngIf="widget.chartType === chartTypes.TABLE">
                <table class="data-table">
                  <thead>
                    <tr>
                      <th>Nhãn</th>
                      <th>Giá Trị</th>
                      <th>Tỷ Lệ %</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr *ngFor="let point of widget.data">
                      <td>{{ point.label }}</td>
                      <td>{{ point.value | number:"1.2-2" }}{{ widget.unit }}</td>
                      <td>{{ getPercentage(point, widget.data) | number:"1.1-1" }}%</td>
                    </tr>
                  </tbody>
                </table>
              </ng-container>
            </div>
          </mat-tab>
        </mat-tab-group>
      </mat-card-content>
    </mat-card>
  `,
  styles: [`
    /* Thanh điều khiển phía trên dashboard */
    .controls-bar {
      display: flex;
      gap: 16px;
      align-items: center;
      margin-bottom: 24px;
      flex-wrap: wrap;
    }

    .controls-bar mat-form-field {
      flex: 1;
      min-width: 200px;
    }

    /* Phần hiển thị KPI tổng hợp */
    .kpi-section {
      margin-bottom: 32px;
    }

    .kpi-section h3 {
      margin-bottom: 16px;
      color: #333;
    }

    .kpi-content {
      display: flex;
      flex-direction: column;
      justify-content: center;
      height: 100%;
      padding: 12px;
      border-radius: 8px;
      background: rgba(255, 255, 255, 0.9);
    }

    .kpi-name {
      font-size: 12px;
      color: #666;
      text-transform: uppercase;
    }

    .kpi-value {
      font-size: 28px;
      font-weight: bold;
      color: #333;
      margin: 4px 0;
    }

    .kpi-trend {
      font-size: 12px;
      font-weight: 500;
    }

    .kpi-trend.positive { color: #4caf50; }
    .kpi-trend.negative { color: #f44336; }
    .kpi-trend.neutral { color: #ff9800; }

    /* Container chung cho tất cả loại biểu đồ */
    .chart-container {
      min-height: 350px;
      padding: 16px;
      overflow: auto;
    }

    /* Biểu đồ cột */
    .bar-chart {
      display: flex;
      align-items: flex-end;
      justify-content: space-around;
      height: 300px;
      padding: 16px 0;
      border-bottom: 2px solid #e0e0e0;
    }

    .bar-item {
      display: flex;
      flex-direction: column;
      align-items: center;
      flex: 1;
      max-width: 60px;
    }

    .bar-fill {
      width: 32px;
      border-radius: 4px 4px 0 0;
      transition: height 0.3s ease;
      min-height: 2px;
    }

    .bar-label {
      margin-top: 8px;
      font-size: 11px;
      color: #666;
      text-align: center;
    }

    .bar-value {
      font-size: 10px;
      font-weight: bold;
      color: #333;
      margin-bottom: 4px;
    }

    /* Biểu đồ đường */
    .line-chart {
      padding: 16px;
      background: #fafafa;
      border-radius: 8px;
    }

    /* Biểu đồ tròn */
    .pie-chart {
      display: flex;
      align-items: center;
      gap: 32px;
      padding: 16px;
    }

    .pie-legend {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }

    .legend-item {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 13px;
    }

    .legend-color {
      display: inline-block;
      width: 12px;
      height: 12px;
      border-radius: 2px;
    }

    /* Đồng hồ đo */
    .gauge-chart {
      display: flex;
      justify-content: center;
      padding: 16px;
    }

    /* Bảng dữ liệu */
    .data-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
    }

    .data-table th,
    .data-table td {
      padding: 10px 14px;
      text-align: left;
      border-bottom: 1px solid #e0e0e0;
    }

    .data-table th {
      background: #f5f5f5;
      font-weight: 600;
      color: #333;
    }

    .data-table tr:hover {
      background: #fafafa;
    }

    /* Responsive: co giãn form field trên màn hình nhỏ */
    @media (max-width: 600px) {
      .controls-bar {
        flex-direction: column;
        align-items: stretch;
      }

      .pie-chart {
        flex-direction: column;
      }

      mat-grid-list {
        cols: 2 !important;
      }
    }
  `],
})
export class AnalyticsWidgetComponent implements OnInit, OnDestroy {
  /**
   * Dữ liệu dashboard hiện tại — chứa widgets và chỉ số KPI.
   */
  dashboardData: DashboardData | null = null;

  /**
   * Observable cho thời gian cập nhật cuối cùng.
   */
  lastUpdated$: Observable<Date> = this._lastUpdatedSubject.asObservable();

  /** Loại biểu đồ đang được chọn. */
  selectedChartType: ChartType = ChartType.LINE;

  /** Chỉ số của widget đang được chọn trong danh sách. */
  selectedWidgetIndex: number = 0;

  /** Trạng thái đang tải dữ liệu. */
  loading: boolean = false;

  /** Chế độ tự động làm mới dữ liệu. */
  autoRefresh: boolean = false;

  /** Enum ChartType để sử dụng trong template. */
  chartTypes = ChartType;

  /** Subscription cho định kỳ tự động làm mới. */
  private _autoRefreshSub?: Subscription;

  /** Subject để phát ra thời gian cập nhật. */
  private _lastUpdatedSubject = new BehaviorSubject<Date>(new Date());

  /** Subject để hủy tất cả subscription khi hủy component. */
  private _destroy$ = new Subject<void>();

  /**
   * Mảng màu mặc định cho biểu đồ tròn và biểu đồ đa series.
   */
  private readonly _defaultColors: string[] = [
    "#1976d2",
    "#4caf50",
    "#f44336",
    "#ff9800",
    "#9c27b0",
    "#00bcd4",
    "#795548",
    "#607d8b",
    "#e91e63",
    "#3f51b5",
  ];

  constructor() {}

  /**
   * Khởi tạo component — tải dữ liệu dashboard ban đầu.
   */
  ngOnInit(): void {
    this.loadDashboardData();
  }

  /**
   * Hủy component — dọn dẹp subscription và interval.
   */
  ngOnDestroy(): void {
    this._destroy$.next();
    this._destroy$.complete();
    this._autoRefreshSub?.unsubscribe();
    this._lastUpdatedSubject.complete();
  }

  /**
   * Tải dữ liệu dashboard từ API phân tích.
   *
   * Trong thực tế, sẽ gọi HTTP request đến endpoint backend.
   * Hiện tại giả lập dữ liệu mẫu để demo.
   */
  private loadDashboardData(): void {
    this.loading = true;

    // Giả lập độ trễ mạng
    setTimeout(() => {
      this.dashboardData = this._generateSampleDashboard();
      this._lastUpdatedSubject.next(new Date());
      this.loading = false;
    }, 500);
  }

  /**
   * Xử lý khi nhấn nút làm mới.
   *
   * Tải lại dữ liệu dashboard từ nguồn.
   */
  onRefresh(): void {
    this.loadDashboardData();
  }

  /**
   * Xử lý khi thay đổi loại biểu đồ.
   *
   * Cập nhật loại biểu đồ của widget hiện tại.
   */
  onChartTypeChanged(): void {
    if (this.dashboardData && this.dashboardData.widgets[this.selectedWidgetIndex]) {
      this.dashboardData.widgets[this.selectedWidgetIndex].chartType = this.selectedChartType;
    }
  }

  /**
   * Xử lý khi chọn widget từ danh sách.
   *
   * Đồng bộ loại biểu đồ được chọn với widget.
   */
  onWidgetSelected(): void {
    if (this.dashboardData && this.dashboardData.widgets[this.selectedWidgetIndex]) {
      this.selectedChartType = this.dashboardData.widgets[this.selectedWidgetIndex].chartType;
    }
  }

  /**
   * Bật/tắt chế độ tự động làm mới.
   *
   * Khi bật, dữ liệu sẽ được làm mới mỗi 30 giây.
   */
  toggleAutoRefresh(): void {
    this.autoRefresh = !this.autoRefresh;

    if (this.autoRefresh) {
      this._autoRefreshSub = interval(30000)
        .pipe(takeUntil(this._destroy$))
        .subscribe(() => this.loadDashboardData());
    } else {
      this._autoRefreshSub?.unsubscribe();
    }
  }

  /**
   * Lấy chiều cao của cột trong biểu đồ cột.
   *
   * @param point - Điểm dữ liệu cần tính.
   * @param data - Mảng dữ liệu để tìm giá trị tối đa.
   * @returns Chiều cao phần trăm so với giá trị tối đa.
   */
  getBarHeight(point: DataPoint, data: DataPoint[]): number {
    const max = this.getMaxValue(data);
    return max > 0 ? (point.value / max) * 100 : 0;
  }

  /**
   * Lấy màu sắc cho lát bánh biểu đồ tròn.
   *
   * @param index - Chỉ số lát bánh.
   * @returns Mã màu HEX.
   */
  getPieColor(index: number): string {
    return this._defaultColors[index % this._defaultColors.length];
  }

  /**
   * Tính toán thuộc tính dash array cho biểu đồ tròn SVG.
   *
   * @param point - Điểm dữ liệu cần tính.
   * @param data - Mảng dữ liệu đầy đủ.
   * @returns Chuỗi dash array cho thuộc tính SVG.
   */
  getPieDashArray(point: DataPoint, data: DataPoint[]): string {
    const total = this.getSum(data);
    const circumference = 2 * Math.PI * 120;
    const ratio = total > 0 ? point.value / total : 0;
    return `${ratio * circumference} ${circumference}`;
  }

  /**
   * Tính toán thuộc tính dash offset cho biểu đồ tròn SVG.
   *
   * @param point - Điểm dữ liệu cần tính.
   * @param data - Mảng dữ liệu đầy đủ.
   * @returns Giá trị offset để xoay lát bánh.
   */
  getPieOffset(point: DataPoint, data: DataPoint[]): number {
    const circumference = 2 * Math.PI * 120;
    let offset = 0;
    const total = this.getSum(data);

    for (const d of data) {
      if (d === point) break;
      offset += total > 0 ? (d.value / total) * circumference : 0;
    }
    return -offset;
  }

  /**
   * Lấy dữ liệu dash cho đồng hồ đo.
   *
   * @param data - Dữ liệu của widget.
   * @returns Giá trị dash array.
   */
  getGaugeDash(data: DataPoint[]): number {
    // Chu vi nửa hình tròn bán kính 90
    return Math.PI * 90;
  }

  /**
   * Lấy giá trị offset cho đồng hồ đo.
   *
   * @param data - Dữ liệu của widget.
   * @returns Giá trị offset dựa trên giá trị đầu tiên.
   */
  getGaugeOffset(data: DataPoint[]): number {
    const maxDash = Math.PI * 90;
    const value = data[0]?.value ?? 0;
    // Giả sử thang đo từ 0 đến 100
    const ratio = Math.min(value / 100, 1);
    return maxDash * (1 - ratio);
  }

  /**
   * Lấy các series cho biểu đồ đường.
   *
   * @param data - Mảng dữ liệu điểm.
   * @returns Mảng series với màu sắc.
   */
  getLineSeries(data: DataPoint[]): Array<{ color: string }> {
    return [{ color: this._defaultColors[0] }];
  }

  /**
   * Lấy các điểm tọa độ cho đường biểu đồ.
   *
   * @param series - Series màu.
   * @param data - Mảng dữ liệu điểm.
   * @returns Chuỗi tọa độ SVG.
   */
  getLinePoints(series: { color: string }, data: DataPoint[]): string {
    const max = this.getMaxValue(data);
    return data
      .map((p, i) => {
        const x = (i / Math.max(data.length - 1, 1)) * 800;
        const y = max > 0 ? 300 - (p.value / max) * 280 : 150;
        return `${x},${y}`;
      })
      .join(" ");
  }

  /**
   * Tính tỷ lệ phần trăm của một điểm so với tổng.
   *
   * @param point - Điểm dữ liệu cần tính.
   * @param data - Mảng dữ liệu đầy đủ.
   * @returns Tỷ lệ phần trăm.
   */
  getPercentage(point: DataPoint, data: DataPoint[]): number {
    const total = this.getSum(data);
    return total > 0 ? (point.value / total) * 100 : 0;
  }

  /**
   * Lấy nhãn xu hướng cho chỉ số KPI.
   *
   * @param kpi - Chỉ số KPI.
   * @returns Chuỗi nhãn với ký hiệu tăng/giảm.
   */
  getTrendLabel(kpi: KpiMetric): string {
    if (kpi.previousValue === 0) return "N/A";
    const change = ((kpi.value - kpi.previousValue) / kpi.previousValue) * 100;
    const sign = change >= 0 ? "+" : "";
    return `${sign}${change.toFixed(1)}% so với kỳ trước`;
  }

  /**
   * Lấy màu nền cho ô KPI dựa trên xu hướng.
   *
   * @param trend - Màu xu hướng.
   * @returns CSS color value.
   */
  getKpiBackgroundColor(trend: string): string {
    switch (trend) {
      case "positive":
        return "#e8f5e9";
      case "negative":
        return "#ffebee";
      default:
        return "#fff3e0";
    }
  }

  /**
   * Lấy giá trị tối đa từ mảng dữ liệu.
   *
   * @param data - Mảng điểm dữ liệu.
   * @returns Giá trị lớn nhất.
   */
  getMaxValue(data: DataPoint[]): number {
    return data.length ? Math.max(...data.map((d) => d.value)) : 1;
  }

  /**
   * Tính tổng giá trị từ mảng dữ liệu.
   *
   * @param data - Mảng điểm dữ liệu.
   * @returns Tổng các giá trị.
   */
  private getSum(data: DataPoint[]): number {
    return data.reduce((sum, d) => sum + d.value, 0);
  }

  /**
   * Tạo dữ liệu dashboard mẫu (dùng trong demo).
   *
   * @returns Đối tượng DashboardData với dữ liệu giả lập.
   */
  private _generateSampleDashboard(): DashboardData {
    // Tạo các chỉ số KPI giả lập
    const kpis: KpiMetric[] = [
      {
        name: "Doanh Thu",
        value: 125840,
        previousValue: 112000,
        unit: "$",
        trendColor: "positive",
      },
      {
        name: "Người Dùng Hoạt Động",
        value: 3420,
        previousValue: 3100,
        unit: "",
        trendColor: "positive",
      },
      {
        name: "Tỷ Lệ Chuyển Đổi",
        value: 4.7,
        previousValue: 5.2,
        unit: "%",
        trendColor: "negative",
      },
      {
        name: "Thời Gian Trung Bình",
        value: 2.4,
        previousValue: 2.4,
        unit: " phút",
        trendColor: "neutral",
      },
    ];

    // Tạo các widget biểu đồ giả lập
    const widgets: WidgetConfig[] = [
      {
        title: "Doanh Thu Theo Tháng",
        chartType: ChartType.LINE,
        metric: "revenue",
        unit: "$",
        color: "#1976d2",
        data: [
          { label: "T1", value: 8500 },
          { label: "T2", value: 12000 },
          { label: "T3", value: 9800 },
          { label: "T4", value: 15000 },
          { label: "T5", value: 11500 },
          { label: "T6", value: 13200 },
          { label: "T7", value: 16400 },
          { label: "T8", value: 14800 },
          { label: "T9", value: 18000 },
          { label: "T10", value: 15500 },
          { label: "T11", value: 17200 },
          { label: "T12", value: 19800 },
        ],
      },
      {
        title: "Phân Bổ Ngành Hàng",
        chartType: ChartType.BAR,
        metric: "category_sales",
        unit: "$",
        color: "#4caf50",
        data: [
          { label: "Điện tử", value: 45000 },
          { label: "Thời trang", value: 28000 },
          { label: "Thức ăn", value: 22000 },
          { label: "Sách", value: 15000 },
          { label: "Khác", value: 12000 },
        ],
      },
      {
        title: "Nguồn Giao Tiếp",
        chartType: ChartType.PIE,
        metric: "traffic_source",
        unit: "%",
        data: [
          { label: "Tìm kiếm", value: 42 },
          { label: "Trực tiếp", value: 28 },
          { label: "Mạng xã hội", value: 18 },
          { label: "Email", value: 8 },
          { label: "Khác", value: 4 },
        ],
      },
      {
        title: "Mức Độ Hài Lòng",
        chartType: ChartType.GAUGE,
        metric: "satisfaction",
        unit: "%",
        color: "#ff9800",
        data: [{ label: "CSAT", value: 78 }],
      },
    ];

    return {
      widgets,
      kpis,
      lastUpdated: Date.now(),
    };
  }
}
'''
        return {"src/analytics/analytics-widget.component.ts": code}

    def generate_report_viewer(self) -> Dict[str, str]:
        """Tạo ReportViewerComponent — hiển thị lịch sử báo cáo và bản chụp."""
        code = '''\
/**
 * Report Viewer Component — hiển thị danh sách báo cáo, bản chụp,
 * và cung cấp chức năng tạo/tải báo cáo.
 *
 * Thành phần này cho phép người dùng xem danh sách báo cáo đã lên lịch,
 * xem chi tiết từng bản chụp, tạo báo cáo mới, và tải báo cáo về.
 */
import {
  Component,
  OnInit,
  OnDestroy,
  ChangeDetectionStrategy,
} from "@angular/core";
import { CommonModule } from "@angular/common";
import {
  FormsModule,
  ReactiveFormsModule,
  FormGroup,
  FormControl,
  Validators,
} from "@angular/forms";
import {
  MatCardModule,
  MatButtonModule,
  MatSelectModule,
  MatProgressBarModule,
  MatIconModule,
  MatSnackBarModule,
  MatTableModule,
  MatPaginatorModule,
  MatSortModule,
  MatCheckboxModule,
  MatDialogModule,
  MatChipsModule,
  MatDividerModule,
  MatInputModule,
  MatTooltipModule,
} from "@angular/material";
import { Observable, Subscription, BehaviorSubject } from "rxjs";
import { takeUntil } from "rxjs/operators";

/**
 * Định dạng của báo cáo.
 */
export enum ReportFormat {
  PDF = "PDF",
  CSV = "CSV",
  EXCEL = "EXCEL",
  JSON = "JSON",
}

/**
 * Trạng thái của báo cáo.
 */
export enum ReportStatus {
  PENDING = "PENDING",
  GENERATING = "GENERATING",
  COMPLETED = "COMPLETED",
  FAILED = "FAILED",
}

/**
 * Tần suất lập lịch báo cáo.
 */
export enum ScheduleFrequency {
  ONCE = "ONCE",
  HOURLY = "HOURLY",
  DAILY = "DAILY",
  WEEKLY = "WEEKLY",
  MONTHLY = "MONTHLY",
}

/**
 * Định nghĩa báo cáo — cấu hình nội dung và tần suất xuất bản.
 */
export interface ReportDefinition {
  /** Tên duy nhất của báo cáo. */
  name: string;
  /** Mô hình phân tích nguồn. */
  modelName: string;
  /** Mô tả báo cáo. */
  description: string;
  /** Định dạng báo cáo. */
  format: ReportFormat;
  /** Tần suất lập lịch. */
  frequency: ScheduleFrequency;
  /** Danh sách người nhận email. */
  recipients: string[];
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
}

/**
 * Bộ lọc tìm kiếm báo cáo.
 */
export interface ReportFilter {
  /** Từ khóa tìm kiếm trong tên báo cáo. */
  keyword: string;
  /** Lọc theo trạng thái (rỗng = tất cả). */
  status: ReportStatus | "";
  /** Lọc theo định dạng (rỗng = tất cả). */
  format: ReportFormat | "";
  /** Chỉ xem báo cáo thất bại. */
  failedOnly: boolean;
}

/**
 * Dữ liệu cho dialog tạo báo cáo mới.
 */
export interface NewReportFormData {
  /** Tên báo cáo mới. */
  name: string;
  /** Mô hình phân tích. */
  modelName: string;
  /** Định dạng báo cáo. */
  format: ReportFormat;
  /** Tần suất lập lịch. */
  frequency: ScheduleFrequency;
  /** Mô tả báo cáo. */
  description: string;
}

@Component({
  selector: "report-viewer",
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    MatCardModule,
    MatButtonModule,
    MatSelectModule,
    MatProgressBarModule,
    MatIconModule,
    MatSnackBarModule,
    MatTableModule,
    MatPaginatorModule,
    MatSortModule,
    MatCheckboxModule,
    MatDialogModule,
    MatChipsModule,
    MatDividerModule,
    MatInputModule,
    MatTooltipModule,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <!-- Thẻ container chính cho trình xem báo cáo -->
    <mat-card>
      <mat-card-header>
        <mat-card-title>Quản Lý Báo Cáo</mat-card-title>
        <mat-card-subtitle>
          Tổng cộng: {{ reportsCount }} báo cáo | {{ completedCount }} hoàn thành
        </mat-card-subtitle>
      </mat-card-header>

      <mat-card-content>
        <!-- Thanh công cụ: tìm kiếm, lọc, và tạo báo cáo mới -->
        <div class="toolbar">
          <!-- Ô tìm kiếm theo từ khóa -->
          <mat-form-field appearance="outline" class="search-field">
            <mat-label>Tìm kiếm báo cáo</mat-label>
            <input
              matInput
              type="text"
              [(ngModel)]="filter.keyword"
              (input)="onFilterChanged()"
              placeholder="Nhập tên báo cáo..."
            />
            <mat-icon matSuffix>search</mat-icon>
          </mat-form-field>

          <!-- Bộ lọc trạng thái -->
          <mat-form-field appearance="outline" class="filter-field">
            <mat-label>Trạng Thái</mat-label>
            <mat-select [(value)]="filter.status" (selectionChange)="onFilterChanged()">
              <mat-option value="">Tất cả</mat-option>
              <mat-option [value]="statusTypes.PENDING">Chờ Xử Lý</mat-option>
              <mat-option [value]="statusTypes.GENERATING">Đang Tạo</mat-option>
              <mat-option [value]="statusTypes.COMPLETED">Hoàn Thành</mat-option>
              <mat-option [value]="statusTypes.FAILED">Thất Bại</mat-option>
            </mat-select>
          </mat-form-field>

          <!-- Bộ lọc định dạng -->
          <mat-form-field appearance="outline" class="filter-field">
            <mat-label>Định Dạng</mat-label>
            <mat-select [(value)]="filter.format" (selectionChange)="onFilterChanged()">
              <mat-option value="">Tất cả</mat-option>
              <mat-option [value]="formatTypes.PDF">PDF</mat-option>
              <mat-option [value]="formatTypes.CSV">CSV</mat-option>
              <mat-option [value]="formatTypes.EXCEL">EXCEL</mat-option>
              <mat-option [value]="formatTypes.JSON">JSON</mat-option>
            </mat-select>
          </mat-form-field>

          <!-- Checkbox lọc báo cáo thất bại -->
          <mat-checkbox
            [(ngModel)]="filter.failedOnly"
            (change)="onFilterChanged()"
            class="failed-filter"
          >
            Chỉ xem thất bại
          </mat-checkbox>

          <!-- Nút tạo báo cáo mới -->
          <button
            mat-raised-button
            color="primary"
            (click)="onCreateNewReport()"
          >
            <mat-icon>add</mat-icon>
            Tạo Báo Cáo Mới
          </button>
        </div>

        <!-- Thanh tiến trình khi đang tải danh sách -->
        <mat-progress-bar
          *ngIf="loading"
          mode="indeterminate"
        ></mat-progress-bar>

        <!-- Bảng danh sách báo cáo -->
        <div class="table-container">
          <table
            mat-table
            [dataSource]="filteredReports"
            matSort
            (matSortChange)="onSortChanged($event)"
          >
            <!-- Cột: Tên báo cáo -->
            <ng-container matColumnDef="name">
              <th mat-header-cell *matHeaderCellDef mat-sort-header>Tên Báo Cáo</th>
              <td mat-cell *matCellDef="let report">
                <div class="report-name-cell">
                  <strong>{{ report.reportName }}</strong>
                  <mat-chip-set>
                    <mat-chip
                      [color]="getStatusChipColor(report.status)"
                      [disabled]="true"
                    >
                      {{ getStatusLabel(report.status) }}
                    </mat-chip>
                    <mat-chip>
                      {{ report.format }}
                    </mat-chip>
                  </mat-chip-set>
                </div>
              </td>
            </ng-container>

            <!-- Cột: Số hàng dữ liệu -->
            <ng-container matColumnDef="rowsCount">
              <th mat-header-cell *matHeaderCellDef mat-sort-header>Số Hàng</th>
              <td mat-cell *matCellDef="let report">
                {{ report.rowsCount | number }}
              </td>
            </ng-container>

            <!-- Cột: Kích thước tệp -->
            <ng-container matColumnDef="fileSize">
              <th mat-header-cell *matHeaderCellDef mat-sort-header>Kích Thước</th>
              <td mat-cell *matCellDef="let report">
                {{ report.fileSizeBytes | fileSize }}
              </td>
            </ng-container>

            <!-- Cột: Thời gian tạo -->
            <ng-container matColumnDef="generatedAt">
              <th mat-header-cell *matHeaderCellDef mat-sort-header>Thời Gian Tạo</th>
              <td mat-cell *matCellDef="let report">
                {{ report.generatedAt | date:"dd/MM/yyyy HH:mm" }}
              </td>
            </ng-container>

            <!-- Cột: Thời gian hoàn thành -->
            <ng-container matColumnDef="completedAt">
              <th mat-header-cell *matHeaderCellDef mat-sort-header>Hoàn Thành</th>
              <td mat-cell *matCellDef="let report">
                {{ report.completedAt ? (report.completedAt | date:"dd/MM/yyyy HH:mm") : "—" }}
              </td>
            </ng-container>

            <!-- Cột: Thông điệp lỗi -->
            <ng-container matColumnDef="errorMessage">
              <th mat-header-cell *matHeaderCellDef mat-sort-header>Lỗi</th>
              <td mat-cell *matCellDef="let report">
                <span
                  *ngIf="report.errorMessage"
                  matTooltip="{{ report.errorMessage }}"
                  class="error-text"
                >
                  <mat-icon>error</mat-icon>
                  {{ report.errorMessage }}
                </span>
                <span *ngIf="!report.errorMessage">—</span>
              </td>
            </ng-container>

            <!-- Cột: Hành động -->
            <ng-container matColumnDef="actions">
              <th mat-header-cell *matHeaderCellDef>Hành Động</th>
              <td mat-cell *matCellDef="let report">
                <div class="action-buttons">
                  <!-- Nút xem chi tiết bản chụp -->
                  <button
                    mat-icon-button
                    color="primary"
                    matTooltip="Xem chi tiết"
                    (click)="onViewSnapshot(report)"
                  >
                    <mat-icon>visibility</mat-icon>
                  </button>

                  <!-- Nút tạo lại báo cáo -->
                  <button
                    mat-icon-button
                    color="accent"
                    matTooltip="Tạo lại báo cáo"
                    (click)="onRegenerate(report)"
                    [disabled]="report.status === statusTypes.GENERATING"
                  >
                    <mat-icon>refresh</mat-icon>
                  </button>

                  <!-- Nút tải về (chỉ hiển thị khi báo cáo hoàn thành) -->
                  <button
                    mat-icon-button
                    color="warn"
                    matTooltip="Tải về"
                    (click)="onDownload(report)"
                    [disabled]="report.status !== statusTypes.COMPLETED"
                  >
                    <mat-icon>download</mat-icon>
                  </button>

                  <!-- Nút xóa báo cáo -->
                  <button
                    mat-icon-button
                    matTooltip="Xóa"
                    (click)="onDeleteReport(report)"
                  >
                    <mat-icon>delete</mat-icon>
                  </button>
                </div>
              </td>
            </ng-container>

            <!-- Hàng tiêu đề và hàng dữ liệu -->
            <tr mat-header-row *matHeaderRowDef="displayedColumns"></tr>
            <tr mat-row *matRowDef="let row; columns: displayedColumns"></tr>

            <!-- Hàng khi không có dữ liệu -->
            <tr class="empty-row" *matNoDataRow>
              <td [colSpan]="displayedColumns.length" class="empty-message">
                Không tìm thấy báo cáo nào phù hợp
              </td>
            </tr>
          </table>
        </div>

        <!-- Phân trang -->
        <mat-paginator
          [pageSizeOptions]="[10, 25, 50, 100]"
          showFirstLastButtons
          (page)="onPageChanged($event)"
        ></mat-paginator>

        <!-- Dialog xem chi tiết bản chụp -->
        <ng-container *ngIf="selectedSnapshot">
          <div class="snapshot-detail">
            <mat-divider></mat-divider>
            <h3>Chi Tiết Bản Chụp</h3>
            <div class="detail-grid">
              <div class="detail-item">
                <span class="detail-label">Tên báo cáo:</span>
                <span class="detail-value">{{ selectedSnapshot.reportName }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">Trạng thái:</span>
                <mat-chip
                  [color]="getStatusChipColor(selectedSnapshot.status)"
                  [disabled]="true"
                >
                  {{ getStatusLabel(selectedSnapshot.status) }}
                </mat-chip>
              </div>
              <div class="detail-item">
                <span class="detail-label">Định dạng:</span>
                <span class="detail-value">{{ selectedSnapshot.format }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">Số hàng:</span>
                <span class="detail-value">{{ selectedSnapshot.rowsCount | number }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">Kích thước:</span>
                <span class="detail-value">
                  {{ selectedSnapshot.fileSizeBytes | fileSize }}
                </span>
              </div>
              <div class="detail-item">
                <span class="detail-label">Thời gian tạo:</span>
                <span class="detail-value">
                  {{ selectedSnapshot.generatedAt | date:"dd/MM/yyyy HH:mm:ss" }}
                </span>
              </div>
              <div class="detail-item" *ngIf="selectedSnapshot.completedAt">
                <span class="detail-label">Thời gian hoàn thành:</span>
                <span class="detail-value">
                  {{ selectedSnapshot.completedAt | date:"dd/MM/yyyy HH:mm:ss" }}
                </span>
              </div>
              <div class="detail-item" *ngIf="selectedSnapshot.errorMessage">
                <span class="detail-label">Lỗi:</span>
                <span class="detail-value error-text">
                  {{ selectedSnapshot.errorMessage }}
                </span>
              </div>
            </div>
          </div>
        </ng-container>
      </mat-card-content>
    </mat-card>
  `,
  styles: [`
    /* Thanh công cụ: tìm kiếm, lọc, nút hành động */
    .toolbar {
      display: flex;
      gap: 12px;
      align-items: flex-end;
      margin-bottom: 20px;
      flex-wrap: wrap;
    }

    .search-field {
      flex: 2;
      min-width: 250px;
    }

    .filter-field {
      flex: 1;
      min-width: 150px;
    }

    .failed-filter {
      margin-bottom: 8px;
      margin-left: 8px;
    }

    /* Container cho bảng dữ liệu */
    .table-container {
      overflow-x: auto;
      margin-bottom: 16px;
    }

    /* Cell hiển thị tên báo cáo với chip trạng thái */
    .report-name-cell {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }

    /* Các nút hành động trong cùng một hàng */
    .action-buttons {
      display: flex;
      gap: 4px;
    }

    /* Văn bản lỗi */
    .error-text {
      color: #f44336;
      font-size: 12px;
      display: inline-flex;
      align-items: center;
      gap: 4px;
    }

    .error-text mat-icon {
      font-size: 16px;
      width: 16px;
      height: 16px;
    }

    /* Hàng trống khi không có dữ liệu */
    .empty-row td {
      text-align: center;
      padding: 40px 16px;
    }

    .empty-message {
      color: #999;
      font-style: italic;
    }

    /* Phần chi tiết bản chụp */
    .snapshot-detail {
      margin-top: 24px;
      padding-top: 20px;
    }

    .snapshot-detail h3 {
      margin-bottom: 16px;
      color: #333;
    }

    /* Lưới hiển thị thông tin chi tiết */
    .detail-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 12px;
    }

    .detail-item {
      display: flex;
      flex-direction: column;
      gap: 4px;
      padding: 8px 12px;
      background: #fafafa;
      border-radius: 6px;
    }

    .detail-label {
      font-size: 12px;
      color: #666;
      text-transform: uppercase;
    }

    .detail-value {
      font-size: 14px;
      color: #333;
      font-weight: 500;
    }

    /* Responsive: chuyển thành cột dọc trên màn hình nhỏ */
    @media (max-width: 768px) {
      .toolbar {
        flex-direction: column;
        align-items: stretch;
      }

      .detail-grid {
        grid-template-columns: 1fr;
      }
    }
  `],
})
export class ReportViewerComponent implements OnInit, OnDestroy {
  /**
   * Danh sách tất cả bản chụp báo cáo đã tải.
   */
  reports: ReportSnapshot[] = [];

  /**
   * Danh sách báo cáo sau khi áp dụng bộ lọc.
   */
  filteredReports: ReportSnapshot[] = [];

  /**
   * Các cột hiển thị trong bảng.
   */
  displayedColumns: string[] = [
    "name",
    "rowsCount",
    "fileSize",
    "generatedAt",
    "completedAt",
    "errorMessage",
    "actions",
  ];

  /**
   * Bộ lọc tìm kiếm và lọc báo cáo hiện tại.
   */
  filter: ReportFilter = {
    keyword: "",
    status: "",
    format: "",
    failedOnly: false,
  };

  /**
   * Bản chụp đang được chọn để xem chi tiết.
   */
  selectedSnapshot: ReportSnapshot | null = null;

  /**
   * Trạng thái đang tải dữ liệu.
   */
  loading: boolean = false;

  /**
   * Enum ReportStatus để sử dụng trong template.
   */
  statusTypes = ReportStatus;

  /**
   * Enum ReportFormat để sử dụng trong template.
   */
  formatTypes = ReportFormat;

  /**
   * Form group cho dialog tạo báo cáo mới.
   */
  newReportForm: FormGroup = new FormGroup({
    name: new FormControl("", [Validators.required, Validators.minLength(3)]),
    modelName: new FormControl("", [Validators.required]),
    format: new FormControl(ReportFormat.PDF, [Validators.required]),
    frequency: new FormControl(ScheduleFrequency.ONCE, [Validators.required]),
    description: new FormControl(""),
  });

  /**
   * Subject để hủy tất cả subscription khi hủy component.
   */
  private _destroy$ = new Subject<void>();

  constructor() {}

  /**
   * Khởi tạo component — tải danh sách báo cáo.
   */
  ngOnInit(): void {
    this.loadReports();
  }

  /**
   * Hủy component — dọn dẹp subscription.
   */
  ngOnDestroy(): void {
    this._destroy$.next();
    this._destroy$.complete();
  }

  /**
   * Tính toán số lượng báo cáo tổng cộng.
   */
  get reportsCount(): number {
    return this.reports.length;
  }

  /**
   * Tính toán số lượng báo cáo đã hoàn thành.
   */
  get completedCount(): number {
    return this.reports.filter(
      (r) => r.status === ReportStatus.COMPLETED
    ).length;
  }

  /**
   * Tải danh sách báo cáo từ API.
   *
   * Trong thực tế, sẽ gọi HTTP GET đến endpoint /analytics/reports.
   * Hiện tại giả lập dữ liệu mẫu.
   */
  private loadReports(): void {
    this.loading = true;

    setTimeout(() => {
      this.reports = this._generateSampleReports();
      this.applyFilters();
      this.loading = false;
    }, 400);
  }

  /**
   * Xử lý khi bộ lọc thay đổi.
   *
   * Áp dụng lại bộ lọc lên danh sách báo cáo.
   */
  onFilterChanged(): void {
    this.applyFilters();
  }

  /**
   * Xử lý khi sắp xếp bảng thay đổi.
   *
   * @param sort - Đối tượng sắp xếp từ MatSort.
   */
  onSortChanged(sort: { active: string; direction: string }): void {
    const { active, direction } = sort;
    if (!direction || !active) return;

    this.filteredReports.sort((a, b) => {
      let aVal: any = a[active as keyof ReportSnapshot];
      let bVal: any = b[active as keyof ReportSnapshot];

      // Xử lý trường đặc biệt
      if (active === "name") {
        aVal = a.reportName;
        bVal = b.reportName;
      } else if (active === "fileSize") {
        aVal = a.fileSizeBytes;
        bVal = b.fileSizeBytes;
      }

      if (aVal < bVal) return direction === "asc" ? -1 : 1;
      if (aVal > bVal) return direction === "asc" ? 1 : -1;
      return 0;
    });
  }

  /**
   * Xử lý khi thay đổi trang trong phân trang.
   *
   * @param event - Sự kiện thay đổi trang từ MatPaginator.
   */
  onPageChanged(event: { pageIndex: number; pageSize: number }): void {
    // Áp dụng phân trang lên danh sách đã lọc
    const start = event.pageIndex * event.pageSize;
    const end = start + event.pageSize;
    // Lưu ý: trong thực tế sẽ dùng MatTableDataSource để tự động phân trang
    this.filteredReports = this.filteredReports.slice(0);
  }

  /**
   * Áp dụng bộ lọc lên danh sách báo cáo.
   *
   * Lọc theo từ khóa, trạng thái, định dạng, và trạng thái thất bại.
   */
  private applyFilters(): void {
    this.filteredReports = this.reports.filter((report) => {
      // Lọc theo từ khóa tìm kiếm trong tên
      if (this.filter.keyword) {
        const keyword = this.filter.keyword.toLowerCase();
        if (!report.reportName.toLowerCase().includes(keyword)) {
          return false;
        }
      }

      // Lọc theo trạng thái
      if (this.filter.status && report.status !== this.filter.status) {
        return false;
      }

      // Lọc theo định dạng
      if (this.filter.format && report.format !== this.filter.format) {
        return false;
      }

      // Chỉ xem báo cáo thất bại
      if (this.filter.failedOnly && report.status !== ReportStatus.FAILED) {
        return false;
      }

      return true;
    });
  }

  /**
   * Xử lý khi nhấn nút tạo báo cáo mới.
   *
   * Mở dialog hoặc form nhập thông tin báo cáo mới.
   */
  onCreateNewReport(): void {
    // Trong thực tế, sẽ mở MatDialog với form nhập thông tin
    this.newReportForm.reset({
      name: "",
      modelName: "",
      format: ReportFormat.PDF,
      frequency: ScheduleFrequency.ONCE,
      description: "",
    });
    // Click để mở dialog tạo báo cáo mới
  }

  /**
   * Xử lý khi nhấn nút xem chi tiết bản chụp.
   *
   * @param snapshot - Bản chụp cần xem chi tiết.
   */
  onViewSnapshot(snapshot: ReportSnapshot): void {
    this.selectedSnapshot = snapshot;
  }

  /**
   * Xử lý khi nhấn nút tạo lại báo cáo.
   *
   * @param snapshot - Bản chụp cần tạo lại.
   */
  onRegenerate(snapshot: ReportSnapshot): void {
    // Đặt trạng thái đang tạo
    snapshot.status = ReportStatus.GENERATING;
    snapshot.completedAt = undefined;
    snapshot.errorMessage = undefined;

    // Giả lập quá trình tạo báo cáo
    setTimeout(() => {
      snapshot.status = ReportStatus.COMPLETED;
      snapshot.completedAt = Date.now();
      snapshot.rowsCount = Math.floor(Math.random() * 200) + 50;
      snapshot.fileSizeBytes = snapshot.rowsCount * 256;
      this.applyFilters();
    }, 2000);
  }

  /**
   * Xử lý khi nhấn nút tải về báo cáo.
   *
   * @param snapshot - Bản chụp cần tải về.
   */
  onDownload(snapshot: ReportSnapshot): void {
    if (snapshot.status !== ReportStatus.COMPLETED) {
      return;
    }

    // Trong thực tế, sẽ gọi API để tải file báo cáo
    const extension = this.getFormatExtension(snapshot.format);
    const filename = `${snapshot.reportName}_${snapshot.id.slice(0, 8)}.${extension}`;

    // Giả lập tải về — tạo blob và kích hoạt download
    const blob = new Blob(
      [JSON.stringify({ reportName: snapshot.reportName, rows: snapshot.rowsCount })],
      { type: "application/octet-stream" },
    );
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
  }

  /**
   * Xử lý khi nhấn nút xóa báo cáo.
   *
   * @param snapshot - Bản chụp cần xóa.
   */
  onDeleteReport(snapshot: ReportSnapshot): void {
    // Xóa khỏi danh sách
    const index = this.reports.indexOf(snapshot);
    if (index > -1) {
      this.reports.splice(index, 1);
      this.applyFilters();
    }

    // Nếu bản chụp đang được chọn là bản bị xóa, làm trống
    if (this.selectedSnapshot === snapshot) {
      this.selectedSnapshot = null;
    }
  }

  /**
   * Lấy nhãn tiếng Việt cho trạng thái báo cáo.
   *
   * @param status - Trạng thái báo cáo.
   * @returns Chuỗi nhãn hiển thị.
   */
  getStatusLabel(status: ReportStatus): string {
    switch (status) {
      case ReportStatus.PENDING:
        return "Chờ xử lý";
      case ReportStatus.GENERATING:
        return "Đang tạo";
      case ReportStatus.COMPLETED:
        return "Hoàn thành";
      case ReportStatus.FAILED:
        return "Thất bại";
      default:
        return "Không xác định";
    }
  }

  /**
   * Lấy màu chip cho trạng thái báo cáo.
   *
   * @param status - Trạng thái báo cáo.
   * @returns Màu sắc của Material Chip.
   */
  getStatusChipColor(status: ReportStatus): "primary" | "accent" | "warn" {
    switch (status) {
      case ReportStatus.PENDING:
        return "accent";
      case ReportStatus.GENERATING:
        return "primary";
      case ReportStatus.COMPLETED:
        return "primary";
      case ReportStatus.FAILED:
        return "warn";
      default:
        return "primary";
    }
  }

  /**
   * Lấy phần mở rộng tệp cho định dạng báo cáo.
   *
   * @param format - Định dạng báo cáo.
   * @returns Phần mở rộng tệp.
   */
  getFormatExtension(format: ReportFormat): string {
    switch (format) {
      case ReportFormat.PDF:
        return "pdf";
      case ReportFormat.CSV:
        return "csv";
      case ReportFormat.EXCEL:
        return "xlsx";
      case ReportFormat.JSON:
        return "json";
      default:
        return "dat";
    }
  }

  /**
   * Tạo danh sách báo cáo mẫu (dùng trong demo).
   *
   * @returns Mảng bản chụp báo cáo giả lập.
   */
  private _generateSampleReports(): ReportSnapshot[] {
    const now = Date.now();
    const day = 86400000; // 1 ngày tính bằng ms

    return [
      {
        id: this._uuid(),
        reportName: "Báo Cáo Doanh Thu Hàng Tháng",
        status: ReportStatus.COMPLETED,
        format: ReportFormat.PDF,
        generatedAt: now - 2 * day,
        completedAt: now - 2 * day + 5000,
        fileSizeBytes: 128000,
        rowsCount: 500,
      },
      {
        id: this._uuid(),
        reportName: "Báo Cáo Người Dùng Hoạt Động",
        status: ReportStatus.COMPLETED,
        format: ReportFormat.EXCEL,
        generatedAt: now - day,
        completedAt: now - day + 3000,
        fileSizeBytes: 256000,
        rowsCount: 1200,
      },
      {
        id: this._uuid(),
        reportName: "Báo Cáo Tỷ Lệ Chuyển Đổi",
        status: ReportStatus.GENERATING,
        format: ReportFormat.PDF,
        generatedAt: now - 3600000,
        fileSizeBytes: 0,
        rowsCount: 0,
      },
      {
        id: this._uuid(),
        reportName: "Báo Cáo Nguồn Giao Tiếp",
        status: ReportStatus.COMPLETED,
        format: ReportFormat.CSV,
        generatedAt: now - 3 * day,
        completedAt: now - 3 * day + 2000,
        fileSizeBytes: 64000,
        rowsCount: 200,
      },
      {
        id: this._uuid(),
        reportName: "Báo Cáo Sản Phẩm Chậm Bán",
        status: ReportStatus.FAILED,
        format: ReportFormat.PDF,
        generatedAt: now - 4 * day,
        fileSizeBytes: 0,
        rowsCount: 0,
        errorMessage: "Không thể kết nối đến kho dữ liệu",
      },
      {
        id: this._uuid(),
        reportName: "Báo Cáo Mất Mát Hàng Hóa",
        status: ReportStatus.PENDING,
        format: ReportFormat.EXCEL,
        generatedAt: now,
        fileSizeBytes: 0,
        rowsCount: 0,
      },
      {
        id: this._uuid(),
        reportName: "Báo Cáo Đánh Giá Khách Hàng",
        status: ReportStatus.COMPLETED,
        format: ReportFormat.JSON,
        generatedAt: now - 5 * day,
        completedAt: now - 5 * day + 8000,
        fileSizeBytes: 512000,
        rowsCount: 2500,
      },
      {
        id: this._uuid(),
        reportName: "Báo Cáo Chi Phí Vận Hành",
        status: ReportStatus.COMPLETED,
        format: ReportFormat.PDF,
        generatedAt: now - 6 * day,
        completedAt: now - 6 * day + 4500,
        fileSizeBytes: 98000,
        rowsCount: 350,
      },
    ];
  }

  /**
   * Tạo UUID v4 đơn giản.
   *
   * @returns Chuỗi UUID.
   */
  private _uuid(): string {
    return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
      const r = (Math.random() * 16) | 0;
      const v = c === "x" ? r : (r & 0x3) | 0x8;
      return v.toString(16);
    });
  }
}
'''
        return {"src/analytics/report-viewer.component.ts": code}
