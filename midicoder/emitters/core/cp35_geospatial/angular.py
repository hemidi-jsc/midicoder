# coding: utf-8
"""
Mô-đun Angular emitter cho Geospatial Pack (CP35).

Emit code Angular cho:
- MapViewerComponent: Hiển thị bản đồ với marker, polyline, geofence overlay
- GeofenceAlertComponent: Hiển thị cảnh báo geofence enter/exit events

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from pathlib import Path

from midicoder.emitters.core.cp35_geospatial.models import (
    Geofence,
    GeofenceShape,
    GeospatialCollection,
    GeospatialSpec,
    GeoPoint,
)
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


class AngularGeospatialEmitter:
    """Emitter sinh code Angular cho geospatial viewer components."""

    def emit(
        self, collection: GeospatialCollection, output_dir: Path | None = None
    ) -> list[dict[str, str]]:
        """
        Generate toàn bộ Angular components từ GeospatialCollection.

        Args:
            collection: GeospatialCollection chứa geospatial specs
            output_dir: Output directory (optional)

        Returns:
            List của {path, content} cho mỗi file
        """
        if not collection.reports:
            EM.raise_error(ErrorCode.CP35_COLLECTION_EMPTY, reason="Collection trống")

        result: list[dict[str, str]] = []
        result.extend(self.generate_map_viewer(collection))
        result.extend(self.generate_geofence_alert(collection))
        return result

    def generate_map_viewer(self, collection: GeospatialCollection) -> list[dict[str, str]]:
        """Sinh MapViewerComponent — bản đồ với marker, polyline, geofence."""

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

        # Build routing method block
        routing_block = '''  loadRoutes(): void {
    const sub = this.http.get<GeoRoute[]>("/api/geospatial/routes").subscribe({
      next: (data) => { this.routes = data; },
      error: (err) => { console.error("Failed to load routes:", err); },
    });
    this.subscriptions.add(sub);
  }

'''

        routing_load_call = "    this.loadRoutes();\n" if has_routing else ""

        ts_code = f'''// Map Viewer Component — Hiển thị bản đồ với marker, polyline, geofence overlay.
// CP35: Geospatial Services (Angular)
// Dùng @asymmetrik/ngx-leaflet
// Geofences định nghĩa: {gf_summary}
// Hỗ trợ routing: {"có" if has_routing else "không"}
// Hỗ trợ geofence: {"có" if has_geofence else "không"}

import {{ Component, OnInit, OnDestroy, Input }} from "@angular/core";
import {{ CommonModule }} from "@angular/common";
import {{ HttpClient }} from "@angular/common/http";
import {{ Subscription }} from "rxjs";
import {{ LeafletModule }} from "@asymmetrik/ngx-leaflet";
import {{
  leaflet,
  line,
  circle,
  polygon,
  marker,
  icon,
  LatLngTuple,
}} from "@asymmetrik/ngx-leaflet";

export interface GeoMarker {{
  position: LatLngTuple;
  label: string;
  popup: string;
}}

export interface GeoRoute {{
  name: string;
  positions: LatLngTuple[];
  color: string;
  weight: number;
}}

export interface GeoFenceZone {{
  id: string;
  name: string;
  shape: {shape_union};
  center?: {{ latitude: number; longitude: number }};
  radius_m?: number;
  points?: {{ latitude: number; longitude: number }}[];
}}

@Component({{
  selector: "app-map-viewer",
  standalone: true,
  imports: [CommonModule, LeafletModule],
  template: `
    <div class="map-viewer">
      <div class="map-header">
        <h2>Bản đồ Địa lý</h2>
        <div class="map-controls">
          <button (click)="zoomIn()">Zoom In</button>
          <button (click)="zoomOut()">Zoom Out</button>
          <button (click)="resetView()">Đặt lại</button>
        </div>
      </div>

      <div id="map" [style.height.px]="height" [style.width.%]="100">
        <div *ngIf="loading">Đang tải bản đồ...</div>
      </div>

      <div class="map-legend">
        <h3>Hướng dẫn</h3>
        <div *ngFor="let gf of geofences" class="legend-item">
          <span class="legend-shape" [class]="gf.shape"></span>
          {{ gf.name }} ({{ gf.shape }})
        </div>
        <div class="legend-item" *ngIf="hasRouting">
          <span class="legend-route"></span> Route (Polyline)
        </div>
      </div>

      <div *ngIf="error" class="error-message">
        {{ error }}
      </div>
    </div>
  `,
  styles: [`
    :host {{ display: block; padding: 20px; }}
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
    .map-legend {{ margin-top: 16px; padding: 12px; background: #f5f5f5; border-radius: 4px; }}
    .legend-item {{
      display: flex;
      align-items: center;
      gap: 8px;
      margin: 4px 0;
      font-size: 14px;
    }}
    .legend-shape.circle {{
      width: 12px;
      height: 12px;
      border-radius: 50%;
      background: rgba(255, 0, 0, 0.3);
      border: 2px solid red;
    }}
    .legend-shape.polygon {{
      width: 12px;
      height: 12px;
      background: rgba(0, 0, 255, 0.3);
      border: 2px solid blue;
      clip-path: polygon(50% 0%, 0% 100%, 100% 100%);
    }}
    .legend-shape.rectangle {{
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
  `]
}})
export class MapViewerComponent implements OnInit, OnDestroy {{
  @Input() center: [number, number] = [10.7769, 106.7009]; // TP. Hồ Chí Minh
  @Input() zoom: number = 13;
  @Input() height: number = 400;

  markers: GeoMarker[] = [];
  routes: GeoRoute[] = [];
  geofences: GeoFenceZone[] = [];

  loading = false;
  error: string = "";
  hasRouting = {has_routing};

  private subscriptions: Subscription = new Subscription();

  constructor(private http: HttpClient) {{}}

  ngOnInit(): void {{
    this.loadMapData();
    this.loadGeofences();
{routing_load_call}  }}

  ngOnDestroy(): void {{
    this.subscriptions.unsubscribe();
  }}

  loadMapData(): void {{
    this.loading = true;
    const sub = this.http.get<GeoMarker[]>("/api/geospatial/markers").subscribe({{
      next: (data) => {{
        this.markers = data;
        this.loading = false;
      }},
      error: (err) => {{
        this.loading = false;
        this.error = "Không thể tải dữ liệu bản đồ: " + err.message;
        console.error("Failed to load map data:", err);
      }},
    }});
    this.subscriptions.add(sub);
  }}

  loadGeofences(): void {{
    const sub = this.http.get<GeoFenceZone[]>("/api/geospatial/geofences").subscribe({{
      next: (data) => {{ this.geofences = data; }},
      error: (err) => {{ console.error("Failed to load geofences:", err); }},
    }});
    this.subscriptions.add(sub);
  }}

{routing_block}  zoomIn(): void {{
    console.log("Zoom in");
  }}

  zoomOut(): void {{
    console.log("Zoom out");
  }}

  resetView(): void {{
    this.center = [10.7769, 106.7009];
    this.zoom = 13;
  }}

  // Danh sách geofences đã định nghĩa
  GEOFENCE_NAMES = {str(geofence_names).replace("'", '"')};
  GEOFENCE_SHAPES = {str(unique_shapes).replace("'", '"')};
}}
'''
        return [{"path": "src/app/geospatial/map-viewer.component.ts", "content": ts_code}]

    def generate_geofence_alert(self, collection: GeospatialCollection) -> list[dict[str, str]]:
        """Sinh GeofenceAlertComponent — cảnh báo geofence enter/exit."""

        all_geofences: list[Geofence] = []
        for spec in collection.reports:
            all_geofences.extend(spec.geofences)

        geofence_names = [gf.name for gf in all_geofences]

        code = f'''// Geofence Alert Component — Hiển thị cảnh báo geofence enter/exit.
// CP35: Geospatial Services (Angular)
// Dùng DomSanitizer để render thông tin geofence trong iframe (nếu có).
// Cleanup Subscription khi component bị phá hủy.

import {{ Component, OnInit, OnDestroy, Input }} from "@angular/core";
import {{ CommonModule }} from "@angular/common";
import {{ HttpClient }} from "@angular/common/http";
import {{ Subscription, interval }} from "rxjs";
import {{ switchMap }} from "rxjs/operators";
import {{ DomSanitizer, SafeHtml }} from "@angular/platform-browser";

export interface GeofenceAlertData {{
  id: string;
  geofenceId: string;
  geofenceName: string;
  type: "enter" | "exit";
  message: string;
  timestamp: Date;
  location: {{ latitude: number; longitude: number }};
  details: SafeHtml | string;
}}

@Component({{
  selector: "app-geofence-alert",
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="geofence-alerts">
      <div class="alert-header">
        <h3>Cảnh báo Geofence ({{{{ alerts.length }}}})</h3>
        <button (click)="clearAll()">Xóa tất cả</button>
      </div>

      <div *ngIf="loading" class="loading">
        Đang tải cảnh báo...
      </div>

      <div *ngIf="!loading && alerts.length === 0" class="empty-state">
        Không có cảnh báo geofence.
      </div>

      <div
        *ngFor="let alert of alerts"
        class="alert-item"
        [class]="alert.type"
      >
        <div class="alert-icon">
          {{{{ alert.type === 'enter' ? '[Vào]' : '[Ra]' }}}}
        </div>
        <div class="alert-content">
          <div class="alert-title">
            {{{{ alert.type === 'enter' ? 'Vào khu vực' : 'Ra khỏi khu vực' }}}}:
            {{{{ alert.geofenceName }}}}
          </div>
          <div class="alert-message">
            {{{{ alert.message }}}}
          </div>
          <div class="alert-time">
            {{{{ alert.timestamp | date:'dd/MM/yyyy HH:mm:ss' }}}}
          </div>
          <div *ngIf="alert.details" class="alert-details" [innerHTML]="alert.details"></div>
        </div>
        <div class="alert-actions">
          <button (click)="dismissAlert(alert.id)">Đóng</button>
        </div>
      </div>

      <div *ngIf="error" class="error-message">
        {{{{ error }}}}
      </div>
    </div>
  `,
  styles: [`
    :host {{ display: block; padding: 20px; }}
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
    .alert-item.enter {{
      border-left: 4px solid #ff9800;
      background: #fff8e1;
    }}
    .alert-item.exit {{
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
  `]
}})
export class GeofenceAlertComponent implements OnInit, OnDestroy {{
  @Input() geofenceId: string = "";
  @Input() pollingInterval: number = 30000; // 30 giây

  alerts: GeofenceAlertData[] = [];
  loading = false;
  error: string = "";

  private subscriptions: Subscription = new Subscription();

  constructor(
    private http: HttpClient,
    private sanitizer: DomSanitizer
  ) {{}}

  ngOnInit(): void {{
    this.loadAlerts();
    this.startPolling();
  }}

  ngOnDestroy(): void {{
    this.subscriptions.unsubscribe();
  }}

  loadAlerts(): void {{
    this.loading = true;
    const url = this.geofenceId
      ? `/api/geospatial/geofences/${{{{this.geofenceId}}}}/alerts`
      : "/api/geospatial/alerts";

    const sub = this.http.get<any[]>(url).subscribe({{
      next: (data) => {{
        this.alerts = data.map((raw) => ({{
          ...raw,
          details: this.sanitizer.bypassSecurityTrustHtml(raw.details || ""),
        }}));
        this.loading = false;
      }},
      error: (err) => {{
        this.loading = false;
        this.error = "Không thể tải cảnh báo: " + err.message;
        console.error("Failed to load geofence alerts:", err);
      }},
    }});
    this.subscriptions.add(sub);
  }}

  startPolling(): void {{
    const pollSub = interval(this.pollingInterval).pipe(
      switchMap(() => this.http.get<any[]>(this.geofenceId
        ? `/api/geospatial/geofences/${{{{this.geofenceId}}}}/alerts`
        : "/api/geospatial/alerts"
      ))
    ).subscribe({{
      next: (data) => {{
        const newAlerts = data.map((raw) => ({{
          ...raw,
          details: this.sanitizer.bypassSecurityTrustHtml(raw.details || ""),
        }}));
        this.alerts = newAlerts;
      }},
      error: (err) => {{
        console.error("Polling geofence alerts failed:", err);
      }},
    }});
    this.subscriptions.add(pollSub);
  }}

  dismissAlert(alertId: string): void {{
    this.alerts = this.alerts.filter((a) => a.id !== alertId);
  }}

  clearAll(): void {{
    this.alerts = [];
  }}

  // Danh sách geofences đã định nghĩa
  KNOWN_GEOFENCES = {str(geofence_names).replace("'", '"')};
}}
'''
        return [{"path": "src/app/geospatial/geofence-alert.component.ts", "content": code}]
