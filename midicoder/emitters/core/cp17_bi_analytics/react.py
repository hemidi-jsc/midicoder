from __future__ import annotations

from typing import Any, Dict


class ReactAnalyticsEmitter:
    """Emitter cho các thành phần Business Intelligence & Analytics của React.

    Tạo ra mã React/TypeScript cho giao diện analytics:
    - TypeScript interfaces cho dữ liệu phân tích
    - AnalyticsChart component để hiển thị biểu đồ
    - ReportTable component để hiển thị bảng báo cáo
    """

    def __init__(self, collection: Any | None = None):
        self.collection = collection or {}

    def generate(self) -> Dict[str, str]:
        """Tạo tất cả các tệp analytics cho React."""
        result: Dict[str, str] = {}
        result.update(self.generate_types())
        result.update(self.generate_analytics_chart())
        result.update(self.generate_report_table())
        return result

    def generate_types(self) -> Dict[str, str]:
        """Tạo TypeScript interfaces cho Analytics, Dashboard, Report."""
        code = '''\
/**
 * Analytics Types — TypeScript interfaces cho phân tích, dashboard, và báo cáo.
 *
 * Cung cấp định nghĩa kiểu cho toàn bộ module analytics của React:
 * - AnalyticsData, AnalyticsChartConfig: dữ liệu và cấu hình biểu đồ
 * - DashboardWidget: widget hiển thị trên dashboard
 * - ReportSnapshot, ReportDefinition: báo cáo đã tạo và định nghĩa
 */

/**
 * Loại biểu đồ hỗ trợ trên dashboard.
 */
export enum ChartType {
  LINE = "LINE",
  BAR = "BAR",
  PIE = "PIE",
  GAUGE = "GAUGE",
}

/**
 * Định dạng xuất báo cáo.
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
 * Một hàng dữ liệu phân tích — kết quả từ truy vấn.
 *
 * @example
 *   { label: "Tháng 1", value: 1250, category: "revenue" }
 */
export interface AnalyticsDataPoint {
  /** Nhãn hiển thị (thời gian, danh mục). */
  label: string;
  /** Giá trị số của chỉ số. */
  value: number;
  /** Danh mục/phân nhóm (tùy chọn). */
  category?: string;
  /** Dữ liệu bổ sung (tùy chọn). */
  metadata?: Record<string, unknown>;
}

/**
 * Dữ liệu phân tích — tập hợp các điểm dữ liệu cho một chỉ số.
 *
 * @example
 *   {
 *     metric: "revenue",
 *     label: "Doanh thu",
 *     unit: "VNĐ",
 *     data: [ { label: "T1", value: 100 }, { label: "T2", value: 150 } ]
 *   }
 */
export interface AnalyticsData {
  /** Tên kỹ thuật của chỉ số. */
  metric: string;
  /** Nhãn hiển thị của chỉ số. */
  label: string;
  /** Đơn vị đo (tùy chọn). */
  unit?: string;
  /** Danh sách điểm dữ liệu. */
  data: AnalyticsDataPoint[];
  /** Màu mặc định cho biểu đồ (tùy chọn). */
  color?: string;
}

/**
 * Cấu hình hiển thị biểu đồ phân tích.
 *
 * @example
 *   {
 *     type: ChartType.LINE,
 *     title: "Doanh thu theo tháng",
 *     width: 600,
 *     height: 300,
 *     showLegend: true,
 *     showGrid: true,
 *     colors: ["#3b82f6", "#10b981"],
 *     xLabel: "Tháng",
 *     yLabel: "Doanh thu (VNĐ)",
 *   }
 */
export interface AnalyticsChartConfig {
  /** Loại biểu đồ. */
  type: ChartType;
  /** Tiêu đề biểu đồ. */
  title: string;
  /** Chiều rộng (px). */
  width: number;
  /** Chiều cao (px). */
  height: number;
  /** Hiển thị chú giải. */
  showLegend: boolean;
  /** Hiển thị lưới. */
  showGrid: boolean;
  /** Danh sách màu cho từng dataset. */
  colors?: string[];
  /** Nhãn trục X. */
  xLabel?: string;
  /** Nhãn trục Y. */
  yLabel?: string;
  /** Format giá trị hiển thị (tùy chọn). */
  valueFormat?: (value: number) => string;
  /** Format tooltip (tùy chọn). */
  tooltipFormat?: (point: AnalyticsDataPoint) => string;
}

/**
 * Dữ liệu của một widget dashboard.
 */
export interface WidgetData {
  /** ID duy nhất của widget. */
  id: string;
  /** Tên widget. */
  name: string;
  /** Loại biểu đồ. */
  chartType: ChartType;
  /** Chỉ số hiển thị. */
  metric: string;
  /** Tiêu đề widget. */
  title: string;
  /** Mô tả widget. */
  description?: string;
  /** Dữ liệu phân tích. */
  data: AnalyticsData[];
  /** Cấu hình biểu đồ. */
  config: AnalyticsChartConfig;
  /** Vị trí trên lưới. */
  positionX: number;
  /** Vị trí trên lưới. */
  positionY: number;
  /** Chiều rộng (số ô). */
  width: number;
  /** Chiều cao (số ô). */
  height: number;
}

/**
 * Dashboard — tập hợp widget hiển thị dữ liệu phân tích.
 */
export interface DashboardWidget {
  /** Tên duy nhất của dashboard. */
  name: string;
  /** Mô tả dashboard. */
  description: string;
  /** Danh sách widget. */
  widgets: WidgetData[];
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
  /** Mô tả báo cáo. */
  description: string;
  /** Bộ lọc áp dụng. */
  filters: Record<string, unknown>;
  /** Danh sách chỉ số. */
  metrics: string[];
  /** Định dạng xuất. */
  format: ReportFormat;
  /** Tần suất lập lịch. */
  frequency: ScheduleFrequency;
  /** Lần chạy kế tiếp (ms epoch, nếu có). */
  nextRun?: number;
  /** Danh sách người nhận. */
  recipients: string[];
  /** Thời điểm tạo (ms epoch). */
  createdAt: number;
}

/**
 * Bản chụp báo cáo đã tạo — lưu kết quả thực tế.
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
  data: Record<string, unknown>;
}

/**
 * Cấu hình cột cho bảng báo cáo.
 */
export interface ReportColumn {
  /** Khóa của trường dữ liệu. */
  key: string;
  /** Tiêu đề hiển thị. */
  title: string;
  /** Loại dữ liệu. */
  dataType: "string" | "number" | "date" | "boolean";
  /** Có thể sắp xếp. */
  sortable: boolean;
  /** Có thể lọc. */
  filterable: boolean;
  /** Chiều rộng cột (tùy chọn). */
  width?: string;
  /** Format giá trị (tùy chọn). */
  format?: (value: unknown, row: Record<string, unknown>) => string;
}

/**
 * Cấu hình phân trang cho bảng.
 */
export interface PaginationConfig {
  /** currentPage: Trang hiện tại (bắt đầu từ 1). */
  currentPage: number;
  /** Số hàng trên mỗi trang. */
  pageSize: number;
  /** Tổng số hàng. */
  totalItems: number;
  /** Các lựa chọn số hàng trên trang. */
  pageSizeOptions?: number[];
}

/**
 * Trạng thái sắp xếp cho bảng.
 */
export interface SortConfig {
  /** Khóa cột sắp xếp. */
  key: string;
  /** Hướng sắp xếp. */
  direction: "asc" | "desc";
}
'''
        return {"src/analytics/types.ts": code}

    def generate_analytics_chart(self) -> Dict[str, str]:
        """Tạo AnalyticsChart React component — hiển thị biểu đồ phân tích.

        Component hỗ trợ các loại biểu đồ: LINE, BAR, PIE, GAUGE
        với SVG rendering và tương tác tooltip.
        """
        code = '''\
/**
 * AnalyticsChart — Component hiển thị biểu đồ phân tích.
 *
 * Hỗ trợ các loại biểu đồ SVG: LINE, BAR, PIE, GAUGE.
 * Nhận dữ liệu phân tích và cấu hình để render tương ứng.
 *
 * Usage:
 *   <AnalyticsChart
 *     data={analyticsData}
 *     config={chartConfig}
 *     onPointClick={handleClick}
 *   />
 */

import React, { useState, useMemo, useCallback } from "react";
import {
  AnalyticsData,
  AnalyticsDataPoint,
  AnalyticsChartConfig,
  ChartType,
} from "./types";

// ============================================================================
// Props & Kiểu dữ liệu
// ============================================================================

/** Props cho AnalyticsChart component */
export interface AnalyticsChartProps {
  /** Dữ liệu phân tích — mảng các dataset. */
  data: AnalyticsData[];
  /** Cấu hình hiển thị biểu đồ. */
  config: AnalyticsChartConfig;
  /** Callback khi click vào điểm dữ liệu (tùy chọn). */
  onPointClick?: (point: AnalyticsDataPoint, metric: string) => void;
  /** Class CSS tùy chỉnh (tùy chọn). */
  className?: string;
}

// ============================================================================
// Hằng số mặc định
// ============================================================================

/** Màu mặc định cho từng dataset khi không có colors trong config */
const DEFAULT_COLORS: string[] = [
  "#3b82f6", // xanh dương
  "#10b981", // xanh lá
  "#f59e0b", // vàng cam
  "#ef4444", // đỏ
  "#8b5cf6", // tím
  "#ec4899", // hồng
  "#06b6d4", // xanh ngọc
  "#84cc16", // xanh vàng
];

/** Padding cho vùng vẽ biểu đồ */
const CHART_PADDING = { top: 30, right: 20, bottom: 50, left: 60 };

/** Chiều cao tooltip */
const TOOLTIP_HEIGHT = 40;

// ============================================================================
// Hook phụ trợ
// ============================================================================

/**
 * Tính toán giá trị min/max từ dữ liệu để vẽ trục.
 *
 * @param data - Mảng dataset
 * @returns Đối tượng chứa minValue và maxValue
 */
function useDataRange(data: AnalyticsData[]) {
  return useMemo(() => {
    let minValue = Infinity;
    let maxValue = -Infinity;

    for (const dataset of data) {
      for (const point of dataset.data) {
        if (point.value < minValue) minValue = point.value;
        if (point.value > maxValue) maxValue = point.value;
      }
    }

    // Nếu không có dữ liệu, trả về khoảng mặc định
    if (minValue === Infinity) {
      minValue = 0;
      maxValue = 100;
    }

    // Thêm 10% padding ở trên cùng
    const range = maxValue - minValue;
    maxValue = maxValue + range * 0.1;
    if (minValue > 0) {
      minValue = 0;
    }

    return { minValue, maxValue };
  }, [data]);
}

/**
 * Lấy danh sách nhãn trục X duy nhất từ tất cả dataset.
 *
 * @param data - Mảng dataset
 * @returns Mảng nhãn duy nhất
 */
function useUniqueLabels(data: AnalyticsData[]) {
  return useMemo(() => {
    const labels = new Set<string>();
    for (const dataset of data) {
      for (const point of dataset.data) {
        labels.add(point.label);
      }
    }
    return Array.from(labels);
  }, [data]);
}

// ============================================================================
// Component con: Tooltip
// ============================================================================

/** Props cho tooltip */
interface TooltipProps {
  /** Vị trí X. */
  x: number;
  /** Vị trí Y. */
  y: number;
  /** Nội dung hiển thị. */
  content: string;
  /** Màu nền. */
  color: string;
}

/**
 * Tooltip hiển thị thông tin điểm dữ liệu khi hover.
 */
function Tooltip({ x, y, content, color }: TooltipProps) {
  return (
    <g className="analytics-chart-tooltip">
      <rect
        x={x - 60}
        y={y - TOOLTIP_HEIGHT - 8}
        width={120}
        height={TOOLTIP_HEIGHT}
        rx={4}
        fill={color}
        opacity={0.9}
      />
      <text
        x={x}
        y={y - TOOLTIP_HEIGHT + 8}
        textAnchor="middle"
        fill="white"
        fontSize={12}
      >
        {content}
      </text>
    </g>
  );
}

// ============================================================================
// Component: Biểu đồ đường (LINE)
// ============================================================================

/** Props cho LineChart */
interface LineChartProps {
  /** Dữ liệu phân tích. */
  data: AnalyticsData[];
  /** Cấu hình biểu đồ. */
  config: AnalyticsChartConfig;
  /** Giá trị min. */
  minValue: number;
  /** Giá trị max. */
  maxValue: number;
  /** Danh sách nhãn. */
  labels: string[];
  /** Callback khi click điểm dữ liệu. */
  onPointClick?: (point: AnalyticsDataPoint, metric: string) => void;
}

/**
 * Render biểu đồ đường — nối các điểm dữ liệu bằng đường thẳng.
 *
 * Tính toán vị trí từng điểm dựa trên tỷ lệ phần trăm so với
 * khoảng giá trị min/max và chiều rộng/cao của vùng vẽ.
 */
function LineChart({
  data,
  config,
  minValue,
  maxValue,
  labels,
  onPointClick,
}: LineChartProps) {
  const [hoveredPoint, setHoveredPoint] = useState<{
    x: number;
    y: number;
    content: string;
    color: string;
  } | null>(null);

  const width = config.width - CHART_PADDING.left - CHART_PADDING.right;
  const height = config.height - CHART_PADDING.top - CHART_PADDING.bottom;
  const valueRange = maxValue - minValue || 1;
  const xStep = labels.length > 1 ? width / (labels.length - 1) : width / 2;

  const formatValue = useCallback(
    (v: number) => config.valueFormat?.(v) ?? v.toLocaleString(),
    [config.valueFormat],
  );

  return (
    <svg
      width={config.width}
      height={config.height}
      className="analytics-chart-svg"
    >
      {/* Vẽ lưới ngang */}
      {config.showGrid &&
        Array.from({ length: 5 }).map((_, i) => {
          const y = CHART_PADDING.top + (height / 4) * i;
          const val = maxValue - (valueRange / 4) * i;
          return (
            <g key={`grid-${i}`}>
              <line
                x1={CHART_PADDING.left}
                y1={y}
                x2={CHART_PADDING.left + width}
                y2={y}
                stroke="#e5e7eb"
                strokeDasharray="4 4"
              />
              <text
                x={CHART_PADDING.left - 8}
                y={y + 4}
                textAnchor="end"
                fontSize={11}
                fill="#6b7280"
              >
                {formatValue(val)}
              </text>
            </g>
          );
        })}

      {/* Vẽ nhãn trục X */}
      {labels.map((label, i) => {
        const x = CHART_PADDING.left + i * xStep;
        return (
          <text
            key={`x-label-${i}`}
            x={x}
            y={config.height - 10}
            textAnchor="middle"
            fontSize={11}
            fill="#6b7280"
          >
            {label}
          </text>
        );
      })}

      {/* Nhãn trục Y */}
      {config.yLabel && (
        <text
          x={15}
          y={config.height / 2}
          textAnchor="middle"
          fontSize={12}
          fill="#374151"
          transform={`rotate(-90, 15, ${config.height / 2})`}
        >
          {config.yLabel}
        </text>
      )}

      {/* Vẽ đường cho từng dataset */}
      {data.map((dataset, di) => {
        const color = config.colors?.[di] ?? DEFAULT_COLORS[di % DEFAULT_COLORS.length];
        const points = dataset.data.map((point, pi) => {
          const x = CHART_PADDING.left + (labels.indexOf(point.label) ?? pi) * xStep;
          const y =
            CHART_PADDING.top +
            height -
            ((point.value - minValue) / valueRange) * height;
          return { x, y, point };
        });

        // Tạo path string cho đường line
        const pathD = points
          .map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`)
          .join(" ");

        return (
          <g key={`line-${di}`} className={`line-dataset line-dataset-${di}`}>
            {/* Đường line */}
            <path
              d={pathD}
              fill="none"
              stroke={color}
              strokeWidth={2.5}
              strokeLinejoin="round"
              strokeLinecap="round"
            />
            {/* Điểm dữ liệu */}
            {points.map((p, pi) => (
              <g key={`point-${di}-${pi}`}>
                <circle
                  cx={p.x}
                  cy={p.y}
                  r={4}
                  fill={color}
                  stroke="white"
                  strokeWidth={2}
                  className="analytics-chart-point"
                  style={{ cursor: "pointer" }}
                  onMouseEnter={() =>
                    setHoveredPoint({
                      x: p.x,
                      y: p.y,
                      content: `${dataset.label}: ${formatValue(p.point.value)}`,
                      color,
                    })
                  }
                  onMouseLeave={() => setHoveredPoint(null)}
                  onClick={() => onPointClick?.(p.point, dataset.metric)}
                />
              </g>
            ))}
          </g>
        );
      })}

      {/* Tooltip */}
      {hoveredPoint && (
        <Tooltip
          x={hoveredPoint.x}
          y={hoveredPoint.y}
          content={hoveredPoint.content}
          color={hoveredPoint.color}
        />
      )}

      {/* Tiêu đề biểu đồ */}
      {config.title && (
        <text
          x={config.width / 2}
          y={16}
          textAnchor="middle"
          fontSize={14}
          fontWeight={600}
          fill="#111827"
        >
          {config.title}
        </text>
      )}
    </svg>
  );
}

// ============================================================================
// Component: Biểu đồ cột (BAR)
// ============================================================================

/** Props cho BarChart */
interface BarChartProps {
  /** Dữ liệu phân tích. */
  data: AnalyticsData[];
  /** Cấu hình biểu đồ. */
  config: AnalyticsChartConfig;
  /** Giá trị min. */
  minValue: number;
  /** Giá trị max. */
  maxValue: number;
  /** Danh sách nhãn. */
  labels: string[];
  /** Callback khi click điểm dữ liệu. */
  onPointClick?: (point: AnalyticsDataPoint, metric: string) => void;
}

/**
 * Render biểu đồ cột — vẽ thanh dọc cho từng nhóm nhãn.
 *
 * Nếu có nhiều dataset, các thanh sẽ được nhóm lại cạnh nhau
 * cho mỗi nhãn để dễ so sánh.
 */
function BarChart({
  data,
  config,
  minValue,
  maxValue,
  labels,
  onPointClick,
}: BarChartProps) {
  const [hoveredPoint, setHoveredPoint] = useState<{
    x: number;
    y: number;
    content: string;
    color: string;
  } | null>(null);

  const width = config.width - CHART_PADDING.left - CHART_PADDING.right;
  const height = config.height - CHART_PADDING.top - CHART_PADDING.bottom;
  const valueRange = maxValue - minValue || 1;
  const groupWidth = width / labels.length;
  const barWidth = Math.min(groupWidth * 0.7 / data.length, 40);
  const barGap = (groupWidth - barWidth * data.length) / (data.length + 1);

  const formatValue = useCallback(
    (v: number) => config.valueFormat?.(v) ?? v.toLocaleString(),
    [config.valueFormat],
  );

  return (
    <svg
      width={config.width}
      height={config.height}
      className="analytics-chart-svg"
    >
      {/* Vẽ lưới ngang */}
      {config.showGrid &&
        Array.from({ length: 5 }).map((_, i) => {
          const y = CHART_PADDING.top + (height / 4) * i;
          const val = maxValue - (valueRange / 4) * i;
          return (
            <g key={`grid-${i}`}>
              <line
                x1={CHART_PADDING.left}
                y1={y}
                x2={CHART_PADDING.left + width}
                y2={y}
                stroke="#e5e7eb"
                strokeDasharray="4 4"
              />
              <text
                x={CHART_PADDING.left - 8}
                y={y + 4}
                textAnchor="end"
                fontSize={11}
                fill="#6b7280"
              >
                {formatValue(val)}
              </text>
            </g>
          );
        })}

      {/* Vẽ nhóm cột cho từng nhãn */}
      {labels.map((label, li) => {
        const groupX = CHART_PADDING.left + li * groupWidth;

        // Vẽ từng cột trong nhóm
        const bars = data.map((dataset, di) => {
          const point = dataset.data.find((p) => p.label === label);
          if (!point) return null;

          const color = config.colors?.[di] ?? DEFAULT_COLORS[di % DEFAULT_COLORS.length];
          const barHeight =
            ((point.value - minValue) / valueRange) * height;
          const x = groupX + barGap + di * (barWidth + barGap);
          const y = CHART_PADDING.top + height - barHeight;

          return (
            <g key={`bar-${li}-${di}`}>
              <rect
                x={x}
                y={y}
                width={barWidth}
                height={barHeight}
                fill={color}
                rx={2}
                className="analytics-chart-bar"
                style={{ cursor: "pointer" }}
                onMouseEnter={() =>
                  setHoveredPoint({
                    x: x + barWidth / 2,
                    y: y,
                    content: `${dataset.label}: ${formatValue(point.value)}`,
                    color,
                  })
                }
                onMouseLeave={() => setHoveredPoint(null)}
                onClick={() => onPointClick?.(point, dataset.metric)}
              />
            </g>
          );
        });

        // Nhãn trục X cho nhóm
        const labelX = groupX + groupWidth / 2;
        return (
          <g key={`group-${li}`}>
            {bars}
            <text
              x={labelX}
              y={config.height - 10}
              textAnchor="middle"
              fontSize={11}
              fill="#6b7280"
            >
              {label}
            </text>
          </g>
        );
      })}

      {/* Nhãn trục Y */}
      {config.yLabel && (
        <text
          x={15}
          y={config.height / 2}
          textAnchor="middle"
          fontSize={12}
          fill="#374151"
          transform={`rotate(-90, 15, ${config.height / 2})`}
        >
          {config.yLabel}
        </text>
      )}

      {/* Tooltip */}
      {hoveredPoint && (
        <Tooltip
          x={hoveredPoint.x}
          y={hoveredPoint.y}
          content={hoveredPoint.content}
          color={hoveredPoint.color}
        />
      )}

      {/* Tiêu đề */}
      {config.title && (
        <text
          x={config.width / 2}
          y={16}
          textAnchor="middle"
          fontSize={14}
          fontWeight={600}
          fill="#111827"
        >
          {config.title}
        </text>
      )}
    </svg>
  );
}

// ============================================================================
// Component: Biểu đồ tròn (PIE)
// ============================================================================

/** Props cho PieChart */
interface PieChartProps {
  /** Dữ liệu phân tích. */
  data: AnalyticsData[];
  /** Cấu hình biểu đồ. */
  config: AnalyticsChartConfig;
  /** Callback khi click điểm dữ liệu. */
  onPointClick?: (point: AnalyticsDataPoint, metric: string) => void;
}

/**
 * Render biểu đồ tròn (pie chart) — hiển thị tỷ lệ phần trăm.
 *
 * Dữ liệu từ dataset đầu tiên được dùng để vẽ các сектора tròn.
 * Mỗi điểm dữ liệu là một miếng pie với góc tương ứng với tỷ lệ
 * so với tổng giá trị.
 */
function PieChart({ data, config, onPointClick }: PieChartProps) {
  const [hoveredPoint, setHoveredPoint] = useState<{
    x: number;
    y: number;
    content: string;
    color: string;
  } | null>(null);

  const cx = config.width / 2;
  const cy = config.height / 2 + 10;
  const radius = Math.min(config.width, config.height) / 2 - 60;

  const formatValue = useCallback(
    (v: number) => config.valueFormat?.(v) ?? v.toLocaleString(),
    [config.valueFormat],
  );

  // Tính tổng và các сектора từ dataset đầu tiên
  const { total, slices } = useMemo(() => {
    const points = data.length > 0 ? data[0].data : [];
    const t = points.reduce((sum, p) => sum + p.value, 0);

    const sl: Array<{
      startAngle: number;
      endAngle: number;
      point: AnalyticsDataPoint;
      color: string;
      metric: string;
    }> = [];

    let currentAngle = 0;
    const colors = config.colors ?? DEFAULT_COLORS;

    for (let i = 0; i < points.length; i++) {
      const fraction = t > 0 ? points[i].value / t : 0;
      const sweepAngle = fraction * 360;
      const color = colors[i % colors.length];
      sl.push({
        startAngle: currentAngle,
        endAngle: currentAngle + sweepAngle,
        point: points[i],
        color,
        metric: data[0].metric,
      });
      currentAngle += sweepAngle;
    }

    return { total: t, slices: sl };
  }, [data, config.colors]);

  /**
   * Tính toán path SVG cho một сектора tròn.
   *
   * @param startAngle - Góc bắt đầu (độ)
   * @param endAngle - Góc kết thúc (độ)
   * @returns Đường path SVG
   */
  function describeArc(startAngle: number, endAngle: number): string {
    const start = polarToCartesian(cx, cy, radius, endAngle);
    const end = polarToCartesian(cx, cy, radius, startAngle);
    const largeArcFlag = endAngle - startAngle <= 180 ? 0 : 1;

    if (endAngle - startAngle >= 359.99) {
      // Toàn bộ hình tròn
      return `M ${cx} ${cy - radius} A ${radius} ${radius} 0 1 1 ${cx} ${cy + radius} A ${radius} ${radius} 0 1 1 ${cx} ${cy - radius} Z`;
    }

    return `M ${cx} ${cy} L ${start.x} ${start.y} A ${radius} ${radius} 0 ${largeArcFlag} 0 ${end.x} ${end.y} Z`;
  }

  /**
   * Chuyển đổi tọa độ cực sang tọa độ Descartes.
   *
   * @param center_x - Tọa độ X tâm
   * @param center_y - Tọa độ Y tâm
   * @param r - Bán kính
   * @param angleInDegrees - Góc (độ)
   * @returns Tọa độ Descartes { x, y }
   */
  function polarToCartesian(
    center_x: number,
    center_y: number,
    r: number,
    angleInDegrees: number,
  ) {
    const angleInRadians = ((angleInDegrees - 90) * Math.PI) / 180;
    return {
      x: center_x + r * Math.cos(angleInRadians),
      y: center_y + r * Math.sin(angleInRadians),
    };
  }

  return (
    <svg
      width={config.width}
      height={config.height}
      className="analytics-chart-svg"
    >
      {/* Tiêu đề */}
      {config.title && (
        <text
          x={config.width / 2}
          y={16}
          textAnchor="middle"
          fontSize={14}
          fontWeight={600}
          fill="#111827"
        >
          {config.title}
        </text>
      )}

      {/* Vẽ các сектора */}
      {slices.map((slice, i) => (
        <path
          key={`slice-${i}`}
          d={describeArc(slice.startAngle, slice.endAngle)}
          fill={slice.color}
          stroke="white"
          strokeWidth={2}
          className="analytics-chart-pie-slice"
          style={{ cursor: "pointer" }}
          onMouseEnter={() => {
            const midAngle = (slice.startAngle + slice.endAngle) / 2;
            const midPoint = polarToCartesian(cx, cy, radius * 0.7, midAngle);
            const pct = total > 0 ? ((slice.point.value / total) * 100).toFixed(1) : "0";
            setHoveredPoint({
              x: midPoint.x,
              y: midPoint.y,
              content: `${slice.point.label}: ${formatValue(slice.point.value)} (${pct}%)`,
              color: slice.color,
            });
          }}
          onMouseLeave={() => setHoveredPoint(null)}
          onClick={() => onPointClick?.(slice.point, slice.metric)}
        />
      ))}

      {/* Tooltip */}
      {hoveredPoint && (
        <Tooltip
          x={hoveredPoint.x}
          y={hoveredPoint.y}
          content={hoveredPoint.content}
          color={hoveredPoint.color}
        />
      )}

      {/* Chú giải (legend) */}
      {config.showLegend &&
        slices.map((slice, i) => {
          const legendY = config.height - 20 + i * 0;
          // Vẽ legend bên dưới biểu đồ
          const itemWidth = config.width / Math.min(slices.length, 4);
          const row = Math.floor(i / 4);
          const col = i % 4;
          const lx = col * itemWidth + 10;
          const ly = config.height - 25 + row * 18;

          return (
            <g key={`legend-${i}`}>
              <rect x={lx} y={ly} width={12} height={12} fill={slice.color} rx={2} />
              <text x={lx + 16} y={ly + 11} fontSize={11} fill="#374151">
                {slice.point.label}
              </text>
            </g>
          );
        })}
    </svg>
  );
}

// ============================================================================
// Component: Đồng hồ đo (GAUGE)
// ============================================================================

/** Props cho GaugeChart */
interface GaugeChartProps {
  /** Dữ liệu phân tích. */
  data: AnalyticsData[];
  /** Cấu hình biểu đồ. */
  config: AnalyticsChartConfig;
  /** Giá trị max. */
  maxValue: number;
}

/**
 * Render đồng hồ đo (gauge chart) — hiển thị một giá trị so với ngưỡng tối đa.
 *
 * Dạng hình bán nguyệt, kim chỉ vào vị trí tương ứng với giá trị.
 * Dùng cho KPI, chỉ số đơn lẻ.
 */
function GaugeChart({ data, config, maxValue }: GaugeChartProps) {
  const cx = config.width / 2;
  const cy = config.height / 2 + 20;
  const radius = Math.min(config.width, config.height) / 2 - 50;

  const formatValue = useCallback(
    (v: number) => config.valueFormat?.(v) ?? v.toLocaleString(),
    [config.valueFormat],
  );

  // Lấy giá trị từ điểm đầu tiên của dataset đầu tiên
  const { currentValue, metricLabel, color } = useMemo(() => {
    if (!data.length || !data[0].data.length) {
      return { currentValue: 0, metricLabel: "", color: DEFAULT_COLORS[0] };
    }
    const firstPoint = data[0].data[0];
    return {
      currentValue: firstPoint.value,
      metricLabel: data[0].label,
      color: config.colors?.[0] ?? data[0].color ?? DEFAULT_COLORS[0],
    };
  }, [data, config.colors]);

  // Tính góc chỉ kim (từ -180 đến 0 độ — bán nguyệt)
  const gaugeAngle = useMemo(() => {
    const ratio = maxValue > 0 ? Math.min(currentValue / maxValue, 1) : 0;
    return -180 + ratio * 180;
  }, [currentValue, maxValue]);

  // Tính tọa độ đầu kim
  const needleEnd = useMemo(() => {
    const angleInRadians = ((gaugeAngle - 90) * Math.PI) / 180;
    return {
      x: cx + (radius - 10) * Math.cos(angleInRadians),
      y: cy + (radius - 10) * Math.sin(angleInRadians),
    };
  }, [cx, cy, radius, gaugeAngle]);

  // Path vòng cung nền
  const arcPath = `M ${cx - radius} ${cy} A ${radius} ${radius} 0 1 1 ${cx + radius} ${cy}`;

  // Path vòng cung giá trị
  const valueAngle = gaugeAngle;
  const valueEndX = cx + radius * Math.cos(((valueAngle - 90) * Math.PI) / 180);
  const valueEndY = cy + radius * Math.sin(((valueAngle - 90) * Math.PI) / 180);
  const largeArc = gaugeAngle - (-180) > 180 ? 1 : 0;
  const valueArcPath =
    gaugeAngle > -180
      ? `M ${cx - radius} ${cy} A ${radius} ${radius} 0 ${largeArc} 1 ${valueEndX} ${valueEndY}`
      : "";

  return (
    <svg
      width={config.width}
      height={config.height}
      className="analytics-chart-svg"
    >
      {/* Tiêu đề */}
      {config.title && (
        <text
          x={config.width / 2}
          y={16}
          textAnchor="middle"
          fontSize={14}
          fontWeight={600}
          fill="#111827"
        >
          {config.title}
        </text>
      )}

      {/* Vòng cung nền */}
      <path
        d={arcPath}
        fill="none"
        stroke="#e5e7eb"
        strokeWidth={20}
        strokeLinecap="round"
      />

      {/* Vòng cung giá trị */}
      {valueArcPath && (
        <path
          d={valueArcPath}
          fill="none"
          stroke={color}
          strokeWidth={20}
          strokeLinecap="round"
        />
      )}

      {/* Kim chỉ thị */}
      <line
        x1={cx}
        y1={cy}
        x2={needleEnd.x}
        y2={needleEnd.y}
        stroke="#374151"
        strokeWidth={2}
        strokeLinecap="round"
      />
      <circle cx={cx} cy={cy} r={5} fill="#374151" />

      {/* Giá trị hiện tại */}
      <text
        x={cx}
        y={cy + 40}
        textAnchor="middle"
        fontSize={24}
        fontWeight={700}
        fill="#111827"
      >
        {formatValue(currentValue)}
      </text>
      <text
        x={cx}
        y={cy + 58}
        textAnchor="middle"
        fontSize={12}
        fill="#6b7280"
      >
        {metricLabel}
      </text>

      {/* Nhãn min/max */}
      <text
        x={cx - radius + 10}
        y={cy + 25}
        textAnchor="middle"
        fontSize={10}
        fill="#9ca3af"
      >
        0
      </text>
      <text
        x={cx + radius - 10}
        y={cy + 25}
        textAnchor="middle"
        fontSize={10}
        fill="#9ca3af"
      >
        {formatValue(maxValue)}
      </text>
    </svg>
  );
}

// ============================================================================
// Component chính: AnalyticsChart
// ============================================================================

/**
 * AnalyticsChart — Component chính để hiển thị biểu đồ phân tích.
 *
 * Tự động chọn renderer tương ứng với loại biểu đồ trong config.type.
 * Sử dụng SVG native, không phụ thuộc thư viện bên ngoài.
 *
 * @example
 *   const chartConfig: AnalyticsChartConfig = {
 *     type: ChartType.LINE,
 *     title: "Doanh thu theo tháng",
 *     width: 600,
 *     height: 350,
 *     showLegend: true,
 *     showGrid: true,
 *     yLabel: "Doanh thu (VNĐ)",
 *   };
 *
 *   return (
 *     <AnalyticsChart data={revenueData} config={chartConfig} />
 *   );
 */
export function AnalyticsChart({
  data,
  config,
  onPointClick,
  className,
}: AnalyticsChartProps) {
  const { minValue, maxValue } = useDataRange(data);
  const labels = useUniqueLabels(data);

  // Không có dữ liệu — hiển thị thông báo trống
  if (!data || data.length === 0 || !data.some((d) => d.data.length > 0)) {
    return (
      <div
        className={`analytics-chart-empty ${className ?? ""}`}
        style={{
          width: config.width,
          height: config.height,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "#9ca3af",
          fontSize: 14,
        }}
      >
        Không có dữ liệu để hiển thị
      </div>
    );
  }

  // Chọn renderer dựa trên loại biểu đồ
  switch (config.type) {
    case ChartType.LINE:
      return (
        <div className={`analytics-chart analytics-chart-line ${className ?? ""}`}>
          <LineChart
            data={data}
            config={config}
            minValue={minValue}
            maxValue={maxValue}
            labels={labels}
            onPointClick={onPointClick}
          />
          {config.showLegend && <ChartLegend data={data} colors={config.colors} />}
        </div>
      );

    case ChartType.BAR:
      return (
        <div className={`analytics-chart analytics-chart-bar ${className ?? ""}`}>
          <BarChart
            data={data}
            config={config}
            minValue={minValue}
            maxValue={maxValue}
            labels={labels}
            onPointClick={onPointClick}
          />
          {config.showLegend && <ChartLegend data={data} colors={config.colors} />}
        </div>
      );

    case ChartType.PIE:
      return (
        <div className={`analytics-chart analytics-chart-pie ${className ?? ""}`}>
          <PieChart data={data} config={config} onPointClick={onPointClick} />
        </div>
      );

    case ChartType.GAUGE:
      return (
        <div className={`analytics-chart analytics-chart-gauge ${className ?? ""}`}>
          <GaugeChart data={data} config={config} maxValue={maxValue} />
        </div>
      );

    default:
      return (
        <div
          className={`analytics-chart-empty ${className ?? ""}`}
          style={{
            width: config.width,
            height: config.height,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "#ef4444",
            fontSize: 14,
          }}
        >
          Loại biểu đồ không được hỗ trợ: {config.type}
        </div>
      );
  }
}

// ============================================================================
// Component phụ: Chú giải (Legend)
// ============================================================================

/** Props cho ChartLegend */
interface ChartLegendProps {
  /** Dữ liệu phân tích. */
  data: AnalyticsData[];
  /** Danh sách màu tùy chỉnh. */
  colors?: string[];
}

/**
 * Hiển thị chú giải cho biểu đồ — danh sách màu + nhãn cho từng dataset.
 */
function ChartLegend({ data, colors }: ChartLegendProps) {
  return (
    <div className="analytics-chart-legend" style={{ display: "flex", gap: 16, justifyContent: "center", marginTop: 8, flexWrap: "wrap" }}>
      {data.map((dataset, i) => {
        const color = colors?.[i] ?? DEFAULT_COLORS[i % DEFAULT_COLORS.length];
        return (
          <div
            key={`legend-${dataset.metric}`}
            style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12 }}
          >
            <span
              style={{
                display: "inline-block",
                width: 12,
                height: 12,
                backgroundColor: color,
                borderRadius: 2,
              }}
            />
            <span style={{ color: "#374151" }}>{dataset.label}</span>
          </div>
        );
      })}
    </div>
  );
}

export default AnalyticsChart;
'''
        return {"src/analytics/AnalyticsChart.tsx": code}

    def generate_report_table(self) -> Dict[str, str]:
        """Tạo ReportTable React component — hiển thị dữ liệu báo cáo dạng bảng.

        Component hỗ trợ sắp xếp cột, phân trang, và hiển thị dữ liệu
        theo cấu hình cột linh hoạt.
        """
        code = '''\
/**
 * ReportTable — Component hiển thị dữ liệu báo cáo dạng bảng.
 *
 * Hỗ trợ:
 * - Sắp xếp theo cột (tăng/giảm)
 * - Phân trang (chọn số hàng/trang, chuyển trang)
 * - Cấu hình cột linh hoạt (kiểu dữ liệu, format, chiều rộng)
 *
 * Usage:
 *   <ReportTable
 *     data={reportData}
 *     columns={columnDefs}
 *     pagination={{ currentPage: 1, pageSize: 20, totalItems: 150 }}
 *     onPaginationChange={handlePagination}
 *     onSortChange={handleSort}
 *   />
 */

import React, { useState, useMemo, useCallback } from "react";
import {
  ReportColumn,
  PaginationConfig,
  SortConfig,
} from "./types";

// ============================================================================
// Props & Kiểu dữ liệu
// ============================================================================

/** Props cho ReportTable component */
export interface ReportTableProps {
  /** Dữ liệu báo cáo — mảng hàng. */
  data: Record<string, unknown>[];
  /** Cấu hình cột. */
  columns: ReportColumn[];
  /** Cấu hình phân trang. */
  pagination: PaginationConfig;
  /** Callback khi thay đổi phân trang. */
  onPaginationChange: (pagination: PaginationConfig) => void;
  /** Callback khi thay đổi sắp xếp. */
  onSortChange?: (sort: SortConfig) => void;
  /** Trạng thái sắp xếp hiện tại (tùy chọn). */
  sort?: SortConfig;
  /** Class CSS tùy chỉnh (tùy chọn). */
  className?: string;
  /** Hiển thị loading (tùy chọn). */
  isLoading?: boolean;
  /** Callback khi click hàng (tùy chọn). */
  onRowClick?: (row: Record<string, unknown>, index: number) => void;
}

/** State phân trang nội bộ */
interface InternalPagination {
  /** Trang hiện tại. */
  currentPage: number;
  /** Số hàng/trang. */
  pageSize: number;
  /** Tổng số trang. */
  totalPages: number;
  /** Chỉ số bắt đầu của trang hiện tại. */
  startIndex: number;
  /** Chỉ số kết thúc của trang hiện tại. */
  endIndex: number;
}

// ============================================================================
// Hằng số mặc định
// ============================================================================

/** Các lựa chọn mặc định cho số hàng trên trang */
const DEFAULT_PAGE_SIZE_OPTIONS = [10, 20, 50, 100];

/** Số trang tối đa hiển thị trong điều hướng */
const MAX_VISIBLE_PAGES = 5;

// ============================================================================
// Icon SVG nội tuyến
// ============================================================================

/**
 * Icon mũi tên lên — dùng cho sắp xếp giảm dần.
 */
function ArrowUpIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
      <path d="M6 3L10 8H2L6 3Z" fill="currentColor" />
    </svg>
  );
}

/**
 * Icon mũi tên xuống — dùng cho sắp xếp tăng dần.
 */
function ArrowDownIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
      <path d="M6 9L2 4H10L6 9Z" fill="currentColor" />
    </svg>
  );
}

/**
 * Icon sắp xếp trung tính — hiển thị khi cột có thể sắp xếp.
 */
function SortIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" opacity={0.4}>
      <path d="M6 3L10 8H2L6 3Z" fill="currentColor" />
      <path d="M6 9L2 4H10L6 9Z" fill="currentColor" />
    </svg>
  );
}

// ============================================================================
// Hàm phụ trợ
// ============================================================================

/**
 * Format giá trị theo kiểu dữ liệu cột.
 *
 * @param value - Giá trị thô
 * @param dataType - Kiểu dữ liệu của cột
 * @param customFormat - Hàm format tùy chỉnh (nếu có)
 * @param row - Hàng dữ liệu đầy đủ
 * @returns Chuỗi đã format
 */
function formatCellValue(
  value: unknown,
  dataType: ReportColumn["dataType"],
  customFormat?: (value: unknown, row: Record<string, unknown>) => string,
  row?: Record<string, unknown>,
): string {
  // Ưu tiên format tùy chỉnh
  if (customFormat && row) {
    return customFormat(value, row);
  }

  // Xử lý null/undefined
  if (value === null || value === undefined) {
    return "-";
  }

  switch (dataType) {
    case "number":
      if (typeof value === "number") {
        return value.toLocaleString();
      }
      return String(value);

    case "date":
      if (value instanceof Date) {
        return value.toLocaleDateString("vi-VN");
      }
      if (typeof value === "number") {
        return new Date(value).toLocaleDateString("vi-VN");
      }
      if (typeof value === "string") {
        const parsed = new Date(value);
        if (!isNaN(parsed.getTime())) {
          return parsed.toLocaleDateString("vi-VN");
        }
      }
      return String(value);

    case "boolean":
      return value ? "Đúng" : "Sai";

    case "string":
    default:
      return String(value);
  }
}

/**
 * Tính toán state phân trang nội bộ từ cấu hình đầu vào.
 *
 * @param pagination - Cấu hình phân trang đầu vào
 * @param pageSizeOptions - Các lựa chọn số hàng/trang
 * @returns State phân trang nội bộ
 */
function computePagination(
  pagination: PaginationConfig,
  pageSizeOptions: number[],
): InternalPagination {
  const pageSize = pagination.pageSize || pageSizeOptions[0];
  const totalItems = pagination.totalItems || 0;
  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));
  const currentPage = Math.min(Math.max(1, pagination.currentPage), totalPages);
  const startIndex = (currentPage - 1) * pageSize;
  const endIndex = Math.min(startIndex + pageSize, totalItems);

  return {
    currentPage,
    pageSize,
    totalPages,
    startIndex,
    endIndex,
  };
}

// ============================================================================
// Component con: Thanh phân trang
// ============================================================================

/** Props cho PaginationBar */
interface PaginationBarProps {
  /** State phân trang nội bộ. */
  pagination: InternalPagination;
  /** Các lựa chọn số hàng/trang. */
  pageSizeOptions: number[];
  /** Callback khi chuyển trang. */
  onPageChange: (page: number) => void;
  /** Callback khi thay đổi số hàng/trang. */
  onPageSizeChange: (pageSize: number) => void;
}

/**
 * Thanh phân trang — hiển thị thông tin trang và điều hướng.
 *
 * Cho phép chuyển trang bằng nút trước/sau, nhấp vào số trang,
 * và thay đổi số hàng trên mỗi trang.
 */
function PaginationBar({
  pagination,
  pageSizeOptions,
  onPageChange,
  onPageSizeChange,
}: PaginationBarProps) {
  // Tính danh sách số trang hiển thị
  const visiblePages = useMemo(() => {
    const pages: number[] = [];
    const total = pagination.totalPages;
    const current = pagination.currentPage;

    if (total <= MAX_VISIBLE_PAGES) {
      // Hiển thị tất cả nếu số trang ít
      for (let i = 1; i <= total; i++) {
        pages.push(i);
      }
    } else {
      // Hiển thị trang đầu
      pages.push(1);

      let start = Math.max(2, current - 1);
      let end = Math.min(total - 1, current + 1);

      // Điều chỉnh để có đủ số trang hiển thị
      if (end - start < MAX_VISIBLE_PAGES - 3) {
        if (current <= total / 2) {
          end = Math.min(total - 1, start + MAX_VISIBLE_PAGES - 3);
        } else {
          start = Math.max(2, end - (MAX_VISIBLE_PAGES - 3));
        }
      }

      if (start > 2) {
        // Thêm dấu ... sau trang 1
        pages.push(-1); // -1 là marker cho dấu ba chấm
      }

      for (let i = start; i <= end; i++) {
        pages.push(i);
      }

      if (end < total - 1) {
        // Thêm dấu ... trước trang cuối
        pages.push(-1);
      }

      // Hiển thị trang cuối
      pages.push(total);
    }

    return pages;
  }, [pagination.totalPages, pagination.currentPage]);

  return (
    <div
      className="report-table-pagination"
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "12px 16px",
        borderTop: "1px solid #e5e7eb",
        flexWrap: "wrap",
        gap: 8,
      }}
    >
      {/* Thông tin và chọn số hàng/trang */}
      <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13 }}>
        <span style={{ color: "#6b7280" }}>Hiển thị</span>
        <select
          value={pagination.pageSize}
          onChange={(e) => onPageSizeChange(Number(e.target.value))}
          style={{
            padding: "4px 8px",
            border: "1px solid #d1d5db",
            borderRadius: 4,
            fontSize: 13,
          }}
        >
          {pageSizeOptions.map((size) => (
            <option key={size} value={size}>
              {size}
            </option>
          ))}
        </select>
        <span style={{ color: "#6b7280" }}>
          trong {pagination.totalItems > 0 ? `${pagination.startIndex + 1}–${pagination.endIndex} của ${pagination.totalItems}` : "0"} bản ghi
        </span>
      </div>

      {/* Nút điều hướng trang */}
      <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
        {/* Nút trang trước */}
        <button
          onClick={() => onPageChange(pagination.currentPage - 1)}
          disabled={pagination.currentPage <= 1}
          style={{
            padding: "4px 10px",
            border: "1px solid #d1d5db",
            borderRadius: 4,
            background: pagination.currentPage <= 1 ? "#f9fafb" : "white",
            cursor: pagination.currentPage <= 1 ? "not-allowed" : "pointer",
            opacity: pagination.currentPage <= 1 ? 0.5 : 1,
            fontSize: 13,
          }}
        >
          Trước
        </button>

        {/* Số trang */}
        {visiblePages.map((page, i) => {
          if (page === -1) {
            return (
              <span
                key={`ellipsis-${i}`}
                style={{ padding: "4px 6px", color: "#9ca3af", fontSize: 13 }}
              >
                ...
              </span>
            );
          }
          const isActive = page === pagination.currentPage;
          return (
            <button
              key={`page-${page}`}
              onClick={() => onPageChange(page)}
              style={{
                padding: "4px 10px",
                border: isActive ? "1px solid #3b82f6" : "1px solid #d1d5db",
                borderRadius: 4,
                background: isActive ? "#3b82f6" : "white",
                color: isActive ? "white" : "#374151",
                fontWeight: isActive ? 600 : 400,
                cursor: "pointer",
                fontSize: 13,
                minWidth: 32,
              }}
            >
              {page}
            </button>
          );
        })}

        {/* Nút trang sau */}
        <button
          onClick={() => onPageChange(pagination.currentPage + 1)}
          disabled={pagination.currentPage >= pagination.totalPages}
          style={{
            padding: "4px 10px",
            border: "1px solid #d1d5db",
            borderRadius: 4,
            background: pagination.currentPage >= pagination.totalPages ? "#f9fafb" : "white",
            cursor: pagination.currentPage >= pagination.totalPages ? "not-allowed" : "pointer",
            opacity: pagination.currentPage >= pagination.totalPages ? 0.5 : 1,
            fontSize: 13,
          }}
        >
          Sau
        </button>
      </div>
    </div>
  );
}

// ============================================================================
// Component chính: ReportTable
// ============================================================================

/**
 * ReportTable — Component hiển thị dữ liệu báo cáo dạng bảng.
 *
 * Đặc điểm:
 * - Hỗ trợ sắp xếp cột (click tiêu đề để đổi hướng)
 * - Phân trang linh hoạt với điều hướng đầy đủ
 * - Format giá trị theo kiểu dữ liệu (number, date, boolean, string)
 * - Custom format function cho từng cột
 * - Loading state và empty state
 *
 * @example
 *   const columns: ReportColumn[] = [
 *     { key: "id", title: "Mã", dataType: "string", sortable: true },
 *     { key: "name", title: "Tên", dataType: "string", sortable: true },
 *     { key: "revenue", title: "Doanh thu", dataType: "number", sortable: true },
 *     { key: "created_at", title: "Ngày tạo", dataType: "date", sortable: true },
 *   ];
 *
 *   return (
 *     <ReportTable
 *       data={reportRows}
 *       columns={columns}
 *       pagination={{ currentPage: 1, pageSize: 20, totalItems: reportRows.length }}
 *       onPaginationChange={setPagination}
 *     />
 *   );
 */
export function ReportTable({
  data,
  columns,
  pagination,
  onPaginationChange,
  onSortChange,
  sort,
  className,
  isLoading,
  onRowClick,
}: ReportTableProps) {
  // State nội bộ cho sắp xếp
  const [internalSort, setInternalSort] = useState<SortConfig | undefined>(sort);

  // Tính toán phân trang nội bộ
  const internalPagination = useMemo(
    () => computePagination(pagination, pagination.pageSizeOptions ?? DEFAULT_PAGE_SIZE_OPTIONS),
    [pagination],
  );

  // Xử lý click tiêu đề cột để đổi hướng sắp xếp
  const handleSortClick = useCallback(
    (column: ReportColumn) => {
      if (!column.sortable) return;

      const newSort: SortConfig = (() => {
        if (internalSort?.key === column.key) {
          // Nếu đang sort theo cột này, đổi hướng
          if (internalSort.direction === "asc") {
            return { key: column.key, direction: "desc" };
          }
          // Nếu đang desc, bỏ sort
          return { key: column.key, direction: "asc" };
        }
        // Cột mới, mặc định asc
        return { key: column.key, direction: "asc" };
      })();

      setInternalSort(newSort);
      onSortChange?.(newSort);
    },
    [internalSort, onSortChange],
  );

  // Xử lý chuyển trang
  const handlePageChange = useCallback(
    (page: number) => {
      onPaginationChange({
        ...pagination,
        currentPage: page,
      });
    },
    [pagination, onPaginationChange],
  );

  // Xử lý thay đổi số hàng/trang
  const handlePageSizeChange = useCallback(
    (pageSize: number) => {
      onPaginationChange({
        ...pagination,
        currentPage: 1, // Về trang đầu khi đổi số hàng
        pageSize,
      });
    },
    [pagination, onPaginationChange],
  );

  // Xác định icon sắp xếp cho từng cột
  const getSortIcon = useCallback(
    (column: ReportColumn) => {
      if (!column.sortable) return null;

      if (internalSort?.key === column.key) {
        return internalSort.direction === "asc" ? (
          <ArrowUpIcon />
        ) : (
          <ArrowDownIcon />
        );
      }
      return <SortIcon />;
    },
    [internalSort],
  );

  // State loading
  if (isLoading) {
    return (
      <div
        className={`report-table report-table-loading ${className ?? ""}`}
        style={{
          border: "1px solid #e5e7eb",
          borderRadius: 8,
          overflow: "hidden",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          minHeight: 200,
          color: "#6b7280",
          fontSize: 14,
        }}
      >
        Đang tải dữ liệu...
      </div>
    );
  }

  return (
    <div className={`report-table ${className ?? ""}`} style={{ border: "1px solid #e5e7eb", borderRadius: 8, overflow: "hidden", background: "white" }}>
      {/* Bảng dữ liệu */}
      <div style={{ overflowX: "auto" }}>
        <table
          style={{
            width: "100%",
            borderCollapse: "collapse",
            fontSize: 13,
          }}
        >
          {/* Header */}
          <thead>
            <tr style={{ background: "#f9fafb", borderBottom: "2px solid #e5e7eb" }}>
              {columns.map((column) => (
                <th
                  key={column.key}
                  onClick={() => handleSortClick(column)}
                  style={{
                    padding: "10px 16px",
                    textAlign: column.dataType === "number" ? "right" : "left",
                    fontWeight: 600,
                    color: "#374151",
                    cursor: column.sortable ? "pointer" : "default",
                    userSelect: "none",
                    whiteSpace: "nowrap",
                    width: column.width,
                    minWidth: column.sortable ? 100 : undefined,
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: 4, justifyContent: column.dataType === "number" ? "flex-end" : "flex-start" }}>
                    <span>{column.title}</span>
                    {column.sortable && (
                      <span style={{ display: "inline-flex", flexShrink: 0 }}>
                        {getSortIcon(column)}
                      </span>
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>

          {/* Body */}
          <tbody>
            {data.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length}
                  style={{
                    textAlign: "center",
                    padding: "40px 16px",
                    color: "#9ca3af",
                    fontSize: 14,
                  }}
                >
                  Không có dữ liệu báo cáo
                </td>
              </tr>
            ) : (
              data.map((row, rowIndex) => (
                <tr
                  key={rowIndex}
                  onClick={() => onRowClick?.(row, rowIndex)}
                  style={{
                    borderBottom: "1px solid #f3f4f6",
                    cursor: onRowClick ? "pointer" : "default",
                    transition: "background-color 0.15s",
                  }}
                  onMouseEnter={(e) => {
                    (e.currentTarget as HTMLTableRowElement).style.backgroundColor = "#f9fafb";
                  }}
                  onMouseLeave={(e) => {
                    (e.currentTarget as HTMLTableRowElement).style.backgroundColor = "";
                  }}
                >
                  {columns.map((column) => {
                    const value = row[column.key];
                    const formattedValue = formatCellValue(
                      value,
                      column.dataType,
                      column.format,
                      row,
                    );
                    const isError = column.dataType === "boolean" && value === false;

                    return (
                      <td
                        key={`${rowIndex}-${column.key}`}
                        style={{
                          padding: "8px 16px",
                          textAlign: column.dataType === "number" ? "right" : "left",
                          color: isError ? "#ef4444" : "#374151",
                          whiteSpace: column.dataType === "string" ? "normal" : "nowrap",
                        }}
                      >
                        {formattedValue}
                      </td>
                    );
                  })}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Thanh phân trang */}
      <PaginationBar
        pagination={{
          ...internalPagination,
          totalItems: pagination.totalItems,
        }}
        pageSizeOptions={pagination.pageSizeOptions ?? DEFAULT_PAGE_SIZE_OPTIONS}
        onPageChange={handlePageChange}
        onPageSizeChange={handlePageSizeChange}
      />
    </div>
  );
}

export default ReportTable;
'''
        return {"src/analytics/ReportTable.tsx": code}
