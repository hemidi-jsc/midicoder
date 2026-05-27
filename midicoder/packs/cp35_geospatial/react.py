# coding: utf-8
"""
Mô-đun React emitter cho Geospatial Pack (CP35).

Emit code React cho:
- MapView.tsx: Hiển thị bản đồ với marker, polyline, geofence overlay
- GeofenceAlert.tsx: Hiển thị cảnh báo geofence enter/exit events

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from pathlib import Path

from midicoder.packs.cp35_geospatial.models import (
    Geofence,
    GeofenceShape,
    GeospatialCollection,
    GeospatialSpec,
    GeoPoint,
)
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


class ReactGeospatialEmitter:
    """Emitter sinh code React cho geospatial viewer components."""

    def emit(
        self, collection: GeospatialCollection, output_dir: Path | None = None
    ) -> list[dict[str, str]]:
        """
        Generate toàn bộ React components từ GeospatialCollection.

        Args:
            collection: GeospatialCollection chứa geospatial specs
            output_dir: Output directory (optional)

        Returns:
            List của {path, content} cho mỗi file
        """
        if not collection.reports:
            EM.raise_error(ErrorCode.CP35_COLLECTION_EMPTY, reason="Collection trống")

        result: list[dict[str, str]] = []
        result.extend(self.generate_map_view(collection))
        result.extend(self.generate_geofence_alert(collection))
        return result

    def generate_map_view(self, collection: GeospatialCollection) -> list[dict[str, str]]:
        """Sinh MapView.tsx — bản đồ với marker, polyline, geofence."""

        # Thu thập thông tin từ tất cả specs
        geofence_names: list[str] = []
        geofence_shapes: list[str] = []
        has_routing = False
        has_geofence = False

        for spec in collection.reports:
            if spec.routing_enabled:
                has_routing = True
            for gf in spec.geofences:
                geofence_names.append(gf.name)
                geofence_shapes.append(gf.shape.value)
                has_geofence = True

        unique_shapes = list(set(geofence_shapes)) if geofence_shapes else ["circle"]
        gf_summary = ", ".join(geofence_names) if geofence_names else "không có"

        # Build shape union type for TypeScript
        shape_union = " | ".join(f'"{s}"' for s in unique_shapes) if unique_shapes else '"circle"'

        # Build routing-specific blocks
        if has_routing:
            routes_in_fetch = ",\n          fetch(\"/api/geospatial/routes\")"
            routes_parse = "        const routesData: MapRoute[] = await routesRes.json();"
            routes_set = "          routes: routesData,"
        else:
            routes_in_fetch = ""
            routes_parse = ""
            routes_set = ""

        code = f'''// Map View — Hiển thị bản đồ với marker và route.
// CP35: Geospatial Services (React)
// Dùng react-leaflet
// Geofences định nghĩa: {gf_summary}
// Hỗ trợ routing: {"có" if has_routing else "không"}
// Hỗ trợ geofence: {"có" if has_geofence else "không"}

import React, {{ useState, useEffect, useCallback }} from "react";
import {{
  MapContainer,
  TileLayer,
  Marker,
  Polyline,
  Circle,
  Polygon,
  Popup,
  Rectangle,
}} from "react-leaflet";
import L from "leaflet";

// Override default marker icon
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({{
  icons: {{
    icon: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
    iconRetina: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
    shadow: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  }},
}});

export interface MapMarker {{
  position: [number, number];
  label: string;
  popup: string;
}}

export interface MapRoute {{
  name: string;
  positions: [number, number][];
  color: string;
  weight: number;
}}

export interface GeofenceZone {{
  id: string;
  name: string;
  shape: {shape_union};
  center?: [number, number];
  radius_m?: number;
  points?: [number, number][];
  bounds?: [[number, number], [number, number]];
}}

interface MapViewProps {{
  center?: [number, number];
  zoom?: number;
  height?: number;
  markers?: MapMarker[];
  routes?: MapRoute[];
  geofences?: GeofenceZone[];
  hasRouting?: boolean;
  onError?: (error: string) => void;
}}

interface MapViewState {{
  markers: MapMarker[];
  routes: MapRoute[];
  geofences: GeofenceZone[];
  loading: boolean;
  error: string | null;
}}

const MapView: React.FC<MapViewProps> = ({{
  center = [10.7769, 106.7009],
  zoom = 13,
  height = 400,
  markers: propMarkers = [],
  routes: propRoutes = [],
  geofences: propGeofences = [],
  hasRouting = false,
  onError,
}}) => {{
  const [state, setState] = useState<MapViewState>({{
    markers: propMarkers,
    routes: propRoutes,
    geofences: propGeofences,
    loading: false,
    error: null,
  }});

  const [mapCenter, setMapCenter] = useState<[number, number]>(center);
  const [mapZoom, setMapZoom] = useState<number>(zoom);

  // Load dữ liệu từ API nếu không được truyền qua props
  useEffect(() => {{
    const fetchData = async (): Promise<void> => {{
      if (propMarkers.length > 0) return;

      setState((prev) => ({{ ...prev, loading: true }}));
      try {{
        const [markersRes, geofencesRes{routes_in_fetch}] = await Promise.all([
          fetch("/api/geospatial/markers"),
          fetch("/api/geospatial/geofences"){routes_in_fetch},
        ]);

        const markersData: MapMarker[] = await markersRes.json();
        const geofencesData: GeofenceZone[] = await geofencesRes.json();
{routes_parse}

        setState((prev) => ({{
          ...prev,
          markers: markersData,
          geofences: geofencesData,
{routes_set}          loading: false,
        }}));
      }} catch (err: unknown) {{
        const message = err instanceof Error ? err.message : String(err);
        setState((prev) => ({{ ...prev, loading: false, error: message }}));
        onError?.(message);
      }}
    }};

    fetchData();
  }}, [propMarkers.length]);

  const handleZoomIn = useCallback((): void => {{
    setMapZoom((z) => Math.min(z + 1, 19));
  }}, []);

  const handleZoomOut = useCallback((): void => {{
    setMapZoom((z) => Math.max(z - 1, 1));
  }}, []);

  const handleReset = useCallback((): void => {{
    setMapCenter(center);
    setMapZoom(zoom);
  }}, [center, zoom]);

  const renderGeofence = (gf: GeofenceZone, index: number): React.ReactNode => {{
    const colorMap: Record<string, string> = {{
      circle: "red",
      polygon: "blue",
      rectangle: "green",
    }};
    const fillColorMap: Record<string, string> = {{
      circle: "rgba(255, 0, 0, 0.2)",
      polygon: "rgba(0, 0, 255, 0.2)",
      rectangle: "rgba(0, 255, 0, 0.2)",
    }};
    const color = colorMap[gf.shape] || "purple";
    const fillColor = fillColorMap[gf.shape] || "rgba(128, 0, 128, 0.2)";

    switch (gf.shape) {{
      case "circle":
        if (gf.center && gf.radius_m) {{
          return (
            <Circle
              key={{`circle-${{index}}`}}
              center={{gf.center}}
              radius={{gf.radius_m}}
              pathOptions={{{{ color, fillColor, weight: 2 }}}}
            />
          );
        }}
        return null;
      case "polygon":
        if (gf.points && gf.points.length >= 3) {{
          return (
            <Polygon
              key={{`polygon-${{index}}`}}
              positions={{gf.points}}
              pathOptions={{{{ color, fillColor, weight: 2 }}}}
            />
          );
        }}
        return null;
      case "rectangle":
        if (gf.bounds) {{
          return (
            <Rectangle
              key={{`rect-${{index}}`}}
              bounds={{gf.bounds}}
              pathOptions={{{{ color, fillColor, weight: 2 }}}}
            />
          );
        }}
        return null;
      default:
        return null;
    }}
  }};

  return (
    <div className="map-view">
      <div className="map-header">
        <h2>Bản đồ Địa lý</h2>
        <div className="map-controls">
          <button onClick={{handleZoomIn}}>Zoom In</button>
          <button onClick={{handleZoomOut}}>Zoom Out</button>
          <button onClick={{handleReset}}>Đặt lại</button>
        </div>
      </div>

      {{state.loading && <div className="loading">Đang tải bản đồ...</div>}}

      <MapContainer
        center={{mapCenter}}
        zoom={{mapZoom}}
        style={{{{ height: `${{height}}px`, width: "100%" }}}}
      >
        <TileLayer
          attribution='&amp;copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png"
        />

        {{state.markers.map((m: MapMarker, i: number) => (
          <Marker key={{`marker-${{i}}`}} position={{m.position}}>
            <Popup>
              <strong>{{m.label}}</strong>
              <br />
              {{m.popup}}
            </Popup>
          </Marker>
        ))}}

        {{state.routes.map((r: MapRoute, i: number) => (
          <Polyline
            key={{`route-${{i}}`}}
            positions={{r.positions}}
            pathOptions={{{{ color: r.color, weight: r.weight }}}}
          />
        ))}}

        {{state.geofences.map(renderGeofence)}}
      </MapContainer>

      <div className="map-legend">
        <h3>Hướng dẫn</h3>
        {{state.geofences.map((gf: GeofenceZone, i: number) => (
          <div key={{`legend-${{i}}`}} className="legend-item">
            <span className={{`legend-shape legend-${{gf.shape}}`}}></span>
            {{gf.name}} ({{gf.shape}})
          </div>
        ))}}
        {{hasRouting && (
          <div className="legend-item">
            <span className="legend-route"></span> Route (Polyline)
          </div>
        )}}
      </div>

      {{state.error && <div className="error-message">{{state.error}}</div>}}

      <style jsx>{{`
        .map-view {{ padding: 20px; }}
        .map-header {{
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
        }}
        .map-controls button {{
          margin-left: 8px;
          padding: 6px 12px;
          background: #2196f3;
          color: white;
          border: none;
          border-radius: 4px;
          cursor: pointer;
        }}
        .loading {{ text-align: center; padding: 40px; color: #666; }}
        .map-legend {{ margin-top: 16px; padding: 12px; background: #f5f5f5; border-radius: 4px; }}
        .legend-item {{
          display: flex;
          align-items: center;
          gap: 8px;
          margin: 4px 0;
          font-size: 14px;
        }}
        .legend-shape.legend-circle {{
          width: 12px;
          height: 12px;
          border-radius: 50%;
          background: rgba(255, 0, 0, 0.3);
          border: 2px solid red;
        }}
        .legend-shape.legend-polygon {{
          width: 12px;
          height: 12px;
          background: rgba(0, 0, 255, 0.3);
          border: 2px solid blue;
          clip-path: polygon(50% 0%, 0% 100%, 100% 100%);
        }}
        .legend-shape.legend-rectangle {{
          width: 16px;
          height: 10px;
          background: rgba(0, 255, 0, 0.3);
          border: 2px solid green;
        }}
        .legend-route {{
          width: 24px;
          height: 4px;
          background: #ff9800;
          border-radius: 2px;
        }}
        .error-message {{ color: red; margin-top: 16px; }}
      `}}
    </div>
  );
}};

export default MapView;
'''
        return [{"path": "src/components/geospatial/MapView.tsx", "content": code}]

    def generate_geofence_alert(self, collection: GeospatialCollection) -> list[dict[str, str]]:
        """Sinh GeofenceAlert.tsx — cảnh báo geofence enter/exit."""

        all_geofences: list[Geofence] = []
        for spec in collection.reports:
            all_geofences.extend(spec.geofences)

        geofence_names = [gf.name for gf in all_geofences]
        gf_summary = ", ".join(geofence_names) if geofence_names else "không có"

        code = f'''// Geofence Alert — Hiển thị cảnh báo geofence enter/exit.
// CP35: Geospatial Services (React)
// Dùng polling để cập nhật cảnh báo theo thời gian thực.
// Cleanup interval khi component unmount.
// Geofences định nghĩa: {gf_summary}

import React, {{ useState, useEffect, useCallback }} from "react";

export interface GeofenceEvent {{
  id: string;
  geofenceId: string;
  geofenceName: string;
  type: "enter" | "exit";
  message: string;
  timestamp: string;
  location: {{ latitude: number; longitude: number }};
  details?: string;
}}

interface GeofenceAlertProps {{
  geofenceId?: string;
  pollingInterval?: number;
  onDismiss?: (alertId: string) => void;
  onError?: (error: string) => void;
}}

interface GeofenceAlertState {{
  events: GeofenceEvent[];
  loading: boolean;
  error: string | null;
}}

const GeofenceAlert: React.FC<GeofenceAlertProps> = ({{
  geofenceId,
  pollingInterval = 30000,
  onDismiss,
  onError,
}}) => {{
  const [state, setState] = useState<GeofenceAlertState>({{
    events: [],
    loading: false,
    error: null,
  }});

  // Fetch alerts từ API
  const fetchAlerts = useCallback(async (): Promise<void> => {{
    setState((prev) => ({{ ...prev, loading: true }}));

    try {{
      const url = geofenceId
        ? `/api/geospatial/geofences/${{geofenceId}}/alerts`
        : "/api/geospatial/alerts";

      const res = await fetch(url);
      if (!res.ok) {{
        throw new Error(`HTTP ${{res.status}}: Không thể tải cảnh báo`);
      }}
      const data: GeofenceEvent[] = await res.json();
      setState((prev) => ({{ ...prev, events: data, loading: false }}));
    }} catch (err: unknown) {{
      const message = err instanceof Error ? err.message : String(err);
      setState((prev) => ({{ ...prev, loading: false, error: message }}));
      onError?.(message);
    }}
  }}, [geofenceId, onError]);

  // Load ban đầu và setup polling
  useEffect(() => {{
    fetchAlerts();

    const timer = setInterval(() => {{
      fetchAlerts();
    }}, pollingInterval);

    // Cleanup: xóa interval khi component unmount
    return () => clearInterval(timer);
  }}, [fetchAlerts, pollingInterval]);

  const handleDismiss = (alertId: string): void => {{
    setState((prev) => ({{
      ...prev,
      events: prev.events.filter((e) => e.id !== alertId),
    }}));
    onDismiss?.(alertId);
  }};

  const handleClearAll = (): void => {{
    setState((prev) => ({{ ...prev, events: [] }}));
  }};

  const formatDate = (timestamp: string): string => {{
    const date = new Date(timestamp);
    return date.toLocaleString("vi-VN", {{
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    }});
  }};

  const getTypeLabel = (type: "enter" | "exit"): string => {{
    return type === "enter" ? "Vào khu vực" : "Ra khỏi khu vực";
  }};

  return (
    <div className="geofence-alerts">
      <div className="alert-header">
        <h3>Cảnh báo Geofence ({{state.events.length}})</h3>
        <button onClick={{handleClearAll}}>Xóa tất cả</button>
      </div>

      {{state.loading && <div className="loading">Đang tải cảnh báo...</div>}}

      {{!state.loading && state.events.length === 0 && (
        <div className="empty-state">Không có cảnh báo geofence.</div>
      )}}

      {{state.events.map((e: GeofenceEvent) => (
        <div key={{e.id}} className={{`alert-item alert-${{e.type}}`}}>
          <div className="alert-icon">
            {{e.type === "enter" ? "[Vào]" : "[Ra]"}}
          </div>
          <div className="alert-content">
            <div className="alert-title">
              {{getTypeLabel(e.type)}}: {{e.geofenceName}}
            </div>
            <div className="alert-message">{{e.message}}</div>
            <div className="alert-time">{{formatDate(e.timestamp)}}</div>
            {{e.details && (
              <div className="alert-details">{{e.details}}</div>
            )}}
          </div>
          <div className="alert-actions">
            <button onClick={{() => handleDismiss(e.id)}}>Đóng</button>
          </div>
        </div>
      ))}}

      {{state.error && <div className="error-message">{{state.error}}</div>}}

      <style jsx>{{`
        .geofence-alerts {{ padding: 20px; }}
        .alert-header {{
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
        }}
        .loading {{ text-align: center; padding: 40px; color: #666; }}
        .empty-state {{ text-align: center; padding: 40px; color: #999; }}
        .alert-item {{
          display: flex;
          gap: 12px;
          padding: 12px;
          margin: 8px 0;
          border-radius: 8px;
          border: 1px solid #ddd;
          animation: slideIn 0.3s ease-out;
        }}
        .alert-enter {{
          border-left: 4px solid #ff9800;
          background: #fff8e1;
        }}
        .alert-exit {{
          border-left: 4px solid #4caf50;
          background: #e8f5e9;
        }}
        .alert-icon {{ font-size: 16px; font-weight: bold; flex-shrink: 0; }}
        .alert-content {{ flex: 1; }}
        .alert-title {{ font-weight: bold; margin-bottom: 4px; }}
        .alert-message {{ color: #333; margin-bottom: 4px; }}
        .alert-time {{ color: #999; font-size: 12px; }}
        .alert-details {{
          margin-top: 8px;
          padding: 8px;
          background: rgba(0,0,0,0.05);
          border-radius: 4px;
          font-size: 13px;
        }}
        .alert-actions {{ flex-shrink: 0; }}
        .error-message {{ color: red; margin-top: 16px; }}
        button {{
          padding: 6px 12px;
          background: #f44336;
          color: white;
          border: none;
          border-radius: 4px;
          cursor: pointer;
        }}
        @keyframes slideIn {{
          from {{ opacity: 0; transform: translateX(-20px); }}
          to {{ opacity: 1; transform: translateX(0); }}
        }}
      `}}
    </div>
  );
}};

export default GeofenceAlert;
'''
        return [{"path": "src/components/geospatial/GeofenceAlert.tsx", "content": code}]
