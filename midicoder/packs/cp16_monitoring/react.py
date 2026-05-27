from __future__ import annotations

from typing import Any, Dict


class ReactMonitoringEmitter:
    """Emitter cho các thành phần monitoring của React."""

    def __init__(self, collection: Any | None = None):
        self.collection = collection or {}

    def generate(self) -> Dict[str, str]:
        """Tạo tất cả các tệp monitoring cho React."""
        result: Dict[str, str] = {}
        result.update(self.generate_types())
        result.update(self.generate_dashboard_panel())
        result.update(self.generate_alert_banner())
        return result

    def generate_types(self) -> Dict[str, str]:
        """Tạo TypeScript interfaces cho monitoring."""
        code = '''\
/**
 * Định nghĩa TypeScript cho hệ thống monitoring phía client.
 *
 * Bao gồm giao diện cho dashboard, panel, cảnh báo,
 * và trạng thái SLI để sử dụng trong component React.
 */

/**
 * Mức độ nghiêm trọng của cảnh báo.
 */
export type AlertSeverity = \'INFO\' | \'WARNING\' | \'CRITICAL\' | \'FATAL\';

/**
 * Trạng thái của cảnh báo.
 */
export type AlertStatus = \'ACTIVE\' | \'RESOLVED\' | \'ACKNOWLEDGED\';

/**
 * Màu sắc tương ứng với mỗi mức độ nghiêm trọng.
 */
export const SEVERITY_COLORS: Record<AlertSeverity, string> = {
  INFO: \'#2196f3\',
  WARNING: \'#ff9800\',
  CRITICAL: \'#f44336\',
  FATAL: \'#9c27b0\',
};

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
  created_at: number;
  /** Thời điểm cập nhật cuối (ms epoch). */
  updated_at: number;
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
  evaluation_interval: number;
}

/**
 * Cảnh báo đang được kích hoạt.
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
  current_value: number;
  /** Mục tiêu. */
  target: number;
  /** Có đạt mục tiêu hay không. */
  healthy: boolean;
  /** Bắt đầu cửa sổ đánh giá (ms epoch). */
  window_start: number;
  /** Kết thúc cửa sổ đánh giá (ms epoch). */
  window_end: number;
  /** Số lượng mẫu trong cửa sổ. */
  samples: number;
}

/**
 * Trạng thái của DashboardPanel component.
 */
export interface DashboardPanelState {
  /** Dashboard hiện tại. */
  dashboard: Dashboard | null;
  /** Đang tải dữ liệu hay không. */
  loading: boolean;
  /** Lỗi nếu có. */
  error: Error | null;
  /** Giá trị metric cho từng panel. */
  panelValues: Record<string, number>;
}

/**
 * Trạng thái của AlertBanner component.
 */
export interface AlertBannerState {
  /** Danh sách cảnh báo. */
  alerts: FiredAlert[];
  /** Đang tải dữ liệu hay không. */
  loading: boolean;
  /** Lỗi nếu có. */
  error: Error | null;
  /** Bộ lọc mức độ nghiêm trọng. */
  severityFilter: AlertSeverity | null;
}
'''
        return {"src/monitoring/types.ts": code}

    def generate_dashboard_panel(self) -> Dict[str, str]:
        """Tạo DashboardPanel component — hiển thị panel metric."""
        code = '''\
/**
 * Component DashboardPanel — hiển thị các panel metric trên dashboard monitoring.
 *
 * Kết nối với API monitoring để tải thông tin dashboard và hiển thị
 * các panel metric với giá trị, ngưỡng, và trạng thái sức khỏe.
 */
import React, { useState, useEffect, useCallback } from \'react\';
import { Dashboard, Panel, SEVERITY_COLORS } from \'./types\';

/**
 * Props cho DashboardPanel component.
 */
interface DashboardPanelProps {
  /** URL cơ sở của API. */
  apiBaseUrl?: string;
  /** Tên dashboard cần hiển thị. */
  dashboardName?: string;
  /** Khoảng thời gian tự động làm mới (ms). */
  refreshInterval?: number;
  /** Callback khi tải xong. */
  onLoad?: (dashboard: Dashboard) => void;
}

/**
 * Trạng thái của một panel metric.
 */
interface PanelState {
  panel: Panel;
  value: number;
  healthy: boolean;
}

/**
 * DashboardPanel component.
 *
 * Hiển thị dashboard với các panel metric bên trong:
 * - Tự động tải dashboard theo tên
 * - Hiển thị giá trị metric, đơn vị, ngưỡng
 * - Đánh dấu panel không đạt ngưỡng
 * - Tự động làm mới dữ liệu
 */
export const DashboardPanel: React.FC<DashboardPanelProps> = ({
  apiBaseUrl = \'/api\',
  dashboardName = \'main\',
  refreshInterval = 30000,
  onLoad,
}) => {
  // Trạng thái dashboard
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  // Trạng thái tải
  const [loading, setLoading] = useState(false);
  // Lỗi nếu có
  const [error, setError] = useState<Error | null>(null);
  // Giá trị metric cho từng panel
  const [panelStates, setPanelStates] = useState<PanelState[]>([]);

  /**
   * Tải dashboard từ API backend.
   */
  const loadDashboard = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${apiBaseUrl}/monitoring/dashboards/${dashboardName}`);

      if (!response.ok) {
        throw new Error(`Không thể tải dashboard: ${response.statusText}`);
      }

      const data: Dashboard = await response.json();
      setDashboard(data);
      onLoad?.(data);

      // Tạo trạng thái ban đầu cho từng panel
      // Trong thực tế, sẽ gọi API metric để lấy giá trị
      const states: PanelState[] = data.panels.map((panel) => ({
        panel,
        value: Math.random() * 100,  // Giả lập giá trị
        healthy: panel.thresholds.length === 0 || Math.random() * 100 < panel.thresholds[0],
      }));
      setPanelStates(states);
    } catch (err) {
      setError(err instanceof Error ? err : new Error(String(err)));
      console.error(\'Lỗi khi tải dashboard:\', err);
    } finally {
      setLoading(false);
    }
  }, [apiBaseUrl, dashboardName, onLoad]);

  // Tự động tải khi mount
  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  // Tự động làm mới dữ liệu
  useEffect(() => {
    const timer = setInterval(() => {
      loadDashboard();
    }, refreshInterval);
    return () => clearInterval(timer);
  }, [loadDashboard, refreshInterval]);

  /**
   * Lấy màu sắc theo trạng thái sức khỏe của panel.
   */
  const getPanelColor = (healthy: boolean): string => {
    return healthy ? \'#4caf50\' : SEVERITY_COLORS.CRITICAL;
  };

  return (
    <div className="dashboard-panel">
      {dashboard && (
        <>
          <h2>{dashboard.name}</h2>
          {dashboard.description && (
            <p className="dashboard-panel__description">{dashboard.description}</p>
          )}
        </>
      )}

      {/* Trạng thái tải */}
      {loading && !dashboard && (
        <div className="dashboard-panel__loading">Đang tải dashboard...</div>
      )}

      {/* Thông báo lỗi */}
      {error && (
        <div className="dashboard-panel__error">
          Lỗi: {error.message}
          <button onClick={loadDashboard}>Thử lại</button>
        </div>
      )}

      {/* Danh sách panel */}
      {!loading && panelStates.length > 0 && (
        <div className="dashboard-panel__grid">
          {panelStates.map((state) => (
            <div
              key={state.panel.name}
              className={`dashboard-panel__card dashboard-panel__card--${state.panel.type} ${state.healthy ? \'\' : \'dashboard-panel__card--unhealthy\'}`}
            >
              {/* Header panel */}
              <div className="dashboard-panel__card-header">
                <h3>{state.panel.name}</h3>
                {!state.healthy && (
                  <span
                    className="dashboard-panel__badge"
                    style={{ color: getPanelColor(false), borderColor: getPanelColor(false) }}
                  >
                    Cảnh báo
                  </span>
                )}
              </div>

              {/* Giá trị metric */}
              <div className="dashboard-panel__card-body">
                <span className="dashboard-panel__value">
                  {state.value.toFixed(2)}
                </span>
                {state.panel.unit && (
                  <span className="dashboard-panel__unit">{state.panel.unit}</span>
                )}
              </div>

              {/* Footer panel */}
              <div className="dashboard-panel__card-footer">
                <span className="dashboard-panel__metric">{state.panel.metric}</span>
                {state.panel.description && (
                  <span className="dashboard-panel__desc">{state.panel.description}</span>
                )}
                {state.panel.thresholds.length > 0 && (
                  <span className="dashboard-panel__threshold">
                    Ngưỡng: {state.panel.thresholds.join(\', \')}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Thông báo trống */}
      {!loading && !error && panelStates.length === 0 && (
        <div className="dashboard-panel__empty">Không có panel nào trên dashboard.</div>
      )}

      {/* Nút làm mới */}
      <button
        className="dashboard-panel__refresh"
        onClick={loadDashboard}
        disabled={loading}
      >
        {loading ? \'Đang tải...\' : \'Làm mới\'}
      </button>
    </div>
  );
};

export default DashboardPanel;
'''
        return {"src/monitoring/DashboardPanel.tsx": code}

    def generate_alert_banner(self) -> Dict[str, str]:
        """Tạo AlertBanner component — hiển thị cảnh báo với notification."""
        code = '''\
/**
 * Component AlertBanner — hiển thị danh sách cảnh báo đang kích hoạt dưới dạng thông báo.
 *
 * Kết nối với API monitoring để tải danh sách cảnh báo và hiển thị
 * dưới dạng banner notification có thể lọc, xác nhận, và giải quyết.
 */
import React, { useState, useEffect, useCallback } from \'react\';
import { FiredAlert, AlertSeverity, SEVERITY_COLORS } from \'./types\';

/**
 * Props cho AlertBanner component.
 */
interface AlertBannerProps {
  /** URL cơ sở của API. */
  apiBaseUrl?: string;
  /** Khoảng thời gian tự động làm mới (ms). */
  refreshInterval?: number;
  /** Callback khi cảnh báo được xác nhận. */
  onAcknowledge?: (alert: FiredAlert) => void;
  /** Callback khi cảnh báo được giải quyết. */
  onResolve?: (alert: FiredAlert) => void;
  /** Callback khi cảnh báo được click. */
  onAlertClick?: (alert: FiredAlert) => void;
}

/**
 * AlertBanner component.
 *
 * Hiển thị danh sách cảnh báo dưới dạng banner notification:
 * - Badge màu theo mức độ nghiêm trọng
 * - Lọc theo mức độ
 * - Xác nhận và giải quyết cảnh báo
 * - Tự động làm mới dữ liệu
 * - Hiển thị thông tin chi tiết
 */
export const AlertBanner: React.FC<AlertBannerProps> = ({
  apiBaseUrl = \'/api\',
  refreshInterval = 15000,
  onAcknowledge,
  onResolve,
  onAlertClick,
}) => {
  // Trạng thái cảnh báo
  const [alerts, setAlerts] = useState<FiredAlert[]>([]);
  // Trạng thái tải
  const [loading, setLoading] = useState(false);
  // Lỗi nếu có
  const [error, setError] = useState<Error | null>(null);
  // Bộ lọc mức độ nghiêm trọng
  const [severityFilter, setSeverityFilter] = useState<AlertSeverity | null>(null);
  // Cảnh báo đang hiển thị chi tiết
  const [selectedAlert, setSelectedAlert] = useState<FiredAlert | null>(null);

  /**
   * Lấy danh sách cảnh báo đã lọc.
   */
  const filteredAlerts = severityFilter
    ? alerts.filter((a) => a.severity === severityFilter)
    : alerts;

  /**
   * Tải danh sách cảnh báo từ API backend.
   */
  const loadAlerts = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${apiBaseUrl}/monitoring/alerts`);

      if (!response.ok) {
        throw new Error(`Không thể tải cảnh báo: ${response.statusText}`);
      }

      const data: FiredAlert[] = await response.json();
      setAlerts(data);
    } catch (err) {
      setError(err instanceof Error ? err : new Error(String(err)));
      console.error(\'Lỗi khi tải cảnh báo:\', err);
    } finally {
      setLoading(false);
    }
  }, [apiBaseUrl]);

  // Tự động tải khi mount
  useEffect(() => {
    loadAlerts();
  }, [loadAlerts]);

  // Tự động làm mới dữ liệu
  useEffect(() => {
    const timer = setInterval(() => {
      loadAlerts();
    }, refreshInterval);
    return () => clearInterval(timer);
  }, [loadAlerts, refreshInterval]);

  /**
   * Xử lý khi thay đổi bộ lọc mức độ.
   */
  const handleSeverityChange = useCallback((e: React.ChangeEvent<HTMLSelectElement>) => {
    setSeverityFilter(e.target.value as AlertSeverity || null);
  }, []);

  /**
   * Xác nhận cảnh báo.
   */
  const handleAcknowledge = useCallback((alert: FiredAlert) => {
    setAlerts((prev) =>
      prev.map((a) =>
        a.id === alert.id
          ? { ...a, status: \'ACKNOWLEDGED\' as const, acknowledged_at: Date.now() }
          : a
      )
    );
    onAcknowledge?.(alert);
  }, [onAcknowledge]);

  /**
   * Giải quyết cảnh báo.
   */
  const handleResolve = useCallback((alert: FiredAlert) => {
    setAlerts((prev) =>
      prev.map((a) =>
        a.id === alert.id
          ? { ...a, status: \'RESOLVED\' as const, resolved_at: Date.now() }
          : a
      )
    );
    setSelectedAlert(null);
    onResolve?.(alert);
  }, [onResolve]);

  /**
   * Hiển thị chi tiết cảnh báo.
   */
  const handleAlertClick = useCallback((alert: FiredAlert) => {
    setSelectedAlert(alert);
    onAlertClick?.(alert);
  }, [onAlertClick]);

  /**
   * Đóng chi tiết cảnh báo.
   */
  const closeDetail = useCallback(() => {
    setSelectedAlert(null);
  }, []);

  /**
   * Định dạng thời gian.
   */
  const formatTime = (timestamp: number): string => {
    return new Date(timestamp).toLocaleString(\'vi-VN\');
  };

  return (
    <div className="alert-banner">
      <div className="alert-banner__header">
        <h2>Cảnh Báo Đang Kích Hoạt</h2>

        {/* Bộ lọc mức độ */}
        <div className="alert-banner__filters">
          <label htmlFor="severity-filter">Mức độ:</label>
          <select
            id="severity-filter"
            value={severityFilter || \'\'}
            onChange={handleSeverityChange}
          >
            <option value="">Tất cả</option>
            <option value="INFO">INFO</option>
            <option value="WARNING">WARNING</option>
            <option value="CRITICAL">CRITICAL</option>
            <option value="FATAL">FATAL</option>
          </select>
          <span className="alert-banner__count">
            {filteredAlerts.length} cảnh báo
          </span>
        </div>
      </div>

      {/* Trạng thái tải */}
      {loading && !alerts.length && (
        <div className="alert-banner__loading">Đang tải cảnh báo...</div>
      )}

      {/* Thông báo lỗi */}
      {error && (
        <div className="alert-banner__error">
          Lỗi: {error.message}
          <button onClick={loadAlerts}>Thử lại</button>
        </div>
      )}

      {/* Thông báo trống */}
      {!loading && !error && filteredAlerts.length === 0 && (
        <div className="alert-banner__empty">
          Không có cảnh báo nào đang kích hoạt.
        </div>
      )}

      {/* Danh sách cảnh báo */}
      <div className="alert-banner__list">
        {filteredAlerts.map((alert) => (
          <div
            key={alert.id}
            className={`alert-banner__item alert-banner__item--${alert.severity.toLowerCase()} ${alert.status === \'ACKNOWLEDGED\' ? \'alert-banner__item--acknowledged\' : \'\'} ${alert.status === \'RESOLVED\' ? \'alert-banner__item--resolved\' : \'\'} `}
            style={{ borderLeftColor: SEVERITY_COLORS[alert.severity] }}
            onClick={() => handleAlertClick(alert)}
          >
            {/* Badge mức độ nghiêm trọng */}
            <span
              className="alert-banner__severity-badge"
              style={{
                color: SEVERITY_COLORS[alert.severity],
                borderColor: SEVERITY_COLORS[alert.severity],
              }}
            >
              {alert.severity}
            </span>

            {/* Nội dung cảnh báo */}
            <div className="alert-banner__content">
              <div className="alert-banner__title">
                <span className="alert-banner__rule">{alert.rule_name}</span>
                {alert.status === \'ACKNOWLEDGED\' && (
                  <span className="alert-banner__ack-badge">Đã xác nhận</span>
                )}
              </div>
              <p className="alert-banner__message">{alert.message}</p>
              <div className="alert-banner__details">
                <span>Giá trị: {alert.current_value}</span>
                <span>Ngưỡng: {alert.threshold}</span>
              </div>
              <div className="alert-banner__time">
                Kích hoạt: {formatTime(alert.fired_at)}
              </div>
            </div>

            {/* Hành động */}
            <div className="alert-banner__actions">
              {alert.status === \'ACTIVE\' && (
                <button
                  className="alert-banner__btn alert-banner__btn--ack"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleAcknowledge(alert);
                  }}
                >
                  Xác nhận
                </button>
              )}
              {alert.status !== \'RESOLVED\' && (
                <button
                  className="alert-banner__btn alert-banner__btn--resolve"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleResolve(alert);
                  }}
                >
                  Giải quyết
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Chi tiết cảnh báo */}
      {selectedAlert && (
        <div className="alert-banner__detail-overlay" onClick={closeDetail}>
          <div className="alert-banner__detail" onClick={(e) => e.stopPropagation()}>
            <button className="alert-banner__close" onClick={closeDetail}>Đóng</button>
            <h3>Chi Tiết Cảnh Báo</h3>
            <dl>
              <dt>Mức độ</dt>
              <dd style={{ color: SEVERITY_COLORS[selectedAlert.severity] }}>
                {selectedAlert.severity}
              </dd>
              <dt>Quy tắc</dt>
              <dd>{selectedAlert.rule_name}</dd>
              <dt>Trạng thái</dt>
              <dd>{selectedAlert.status}</dd>
              <dt>Thông điệp</dt>
              <dd>{selectedAlert.message}</dd>
              <dt>Giá trị hiện tại</dt>
              <dd>{selectedAlert.current_value}</dd>
              <dt>Ngưỡng</dt>
              <dd>{selectedAlert.threshold}</dd>
              <dt>Kích hoạt lúc</dt>
              <dd>{formatTime(selectedAlert.fired_at)}</dd>
              {selectedAlert.acknowledged_at && (
                <>
                  <dt>Xác nhận lúc</dt>
                  <dd>{formatTime(selectedAlert.acknowledged_at)}</dd>
                </>
              )}
              {selectedAlert.resolved_at && (
                <>
                  <dt>Giải quyết lúc</dt>
                  <dd>{formatTime(selectedAlert.resolved_at)}</dd>
                </>
              )}
            </dl>
            <div className="alert-banner__detail-actions">
              {selectedAlert.status === \'ACTIVE\' && (
                <button
                  className="alert-banner__btn alert-banner__btn--ack"
                  onClick={() => handleAcknowledge(selectedAlert)}
                >
                  Xác nhận
                </button>
              )}
              {selectedAlert.status !== \'RESOLVED\' && (
                <button
                  className="alert-banner__btn alert-banner__btn--resolve"
                  onClick={() => handleResolve(selectedAlert)}
                >
                  Giải quyết
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Nút làm mới */}
      <button
        className="alert-banner__refresh"
        onClick={loadAlerts}
        disabled={loading}
      >
        {loading ? \'Đang tải...\' : \'Làm mới\'}
      </button>
    </div>
  );
};

export default AlertBanner;
'''
        return {"src/monitoring/AlertBanner.tsx": code}
