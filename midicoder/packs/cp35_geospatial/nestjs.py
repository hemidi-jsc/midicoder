# coding: utf-8
"""
Mô-đun NestJS emitter cho Geospatial Pack (CP35).

Emit code NestJS cho:
- GeospatialService: tính toán khoảng cách, reverse geocoding
- GeofenceService: quản lý geofence và check enter/exit
- RoutingService: tính route qua OSRM API
- GeospatialController: API controller

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.packs.cp35_geospatial.models import GeospatialCollection
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


class NestJSGeospatialEmitter:
    """
    Emitter sinh code NestJS cho geospatial services.

    Methods:
        emit(): Generate toàn bộ files từ GeospatialCollection
        generate_service(): Sinh GeospatialService
        generate_geofence_service(): Sinh GeofenceService
        generate_routing_service(): Sinh RoutingService
        generate_controller(): Sinh GeospatialController
    """

    def __init__(self, stack_dir: str | None = None) -> None:
        """
        Init emitter.

        Args:
            stack_dir: Đường dẫn đến stack template directory
        """
        self.stack_dir = Path(stack_dir) if stack_dir else None
        self.template_dir = (
            self.stack_dir / "cp35_geospatial" if self.stack_dir else None
        )

        if self.template_dir and self.template_dir.exists():
            self._env = Environment(
                loader=FileSystemLoader(str(self.template_dir)),
                autoescape=True,
                trim_blocks=True,
                lstrip_blocks=True,
            )
        else:
            self._env = None

    def emit(
        self, collection: GeospatialCollection
    ) -> list[dict[str, str]]:
        """
        Generate toàn bộ files NestJS từ GeospatialCollection.

        Args:
            collection: GeospatialCollection chứa geospatial specs

        Returns:
            List của {path, content} cho mỗi file
        """
        if not collection.reports:
            EM.raise_error(
                ErrorCode.CP35_GEOSPEC_INVALID,
                reason="Collection trống",
            )

        result: list[dict[str, str]] = []
        result.extend(self.generate_service(collection))
        result.extend(self.generate_geofence_service(collection))
        result.extend(self.generate_routing_service(collection))
        result.extend(self.generate_controller(collection))
        return result

    def generate_service(
        self, collection: GeospatialCollection
    ) -> list[dict[str, str]]:
        """Sinh GeospatialService class."""
        has_reverse_geocoding = any(
            spec.reverse_geocoding_enabled for spec in collection.reports
        )
        spec_ids = [spec.id for spec in collection.reports]

        context = {
            "collection": collection,
            "spec_ids": spec_ids,
            "has_reverse_geocoding": has_reverse_geocoding,
            "spec_count": len(collection.reports),
        }

        if self._template_exists("geospatial.service.ts.jinja2"):
            content = self._render("geospatial.service.ts.jinja2", context)
            return [{"path": "src/geospatial/geospatial.service.ts", "content": content}]

        # Fallback: inline generation khi không có template
        return [
            {
                "path": "src/geospatial/geospatial.service.ts",
                "content": self._build_service_inline(collection),
            }
        ]

    def generate_geofence_service(
        self, collection: GeospatialCollection
    ) -> list[dict[str, str]]:
        """Sinh GeofenceService class."""
        all_shapes = set()
        all_geofences = []
        for spec in collection.reports:
            for gf in spec.geofences:
                all_shapes.add(gf.shape.value)
                all_geofences.append(gf)

        context = {
            "collection": collection,
            "all_geofences": all_geofences,
            "all_shapes": list(all_shapes),
            "geofence_count": len(all_geofences),
        }

        if self._template_exists("geofence.service.ts.jinja2"):
            content = self._render("geofence.service.ts.jinja2", context)
            return [{"path": "src/geospatial/geofence.service.ts", "content": content}]

        return [
            {
                "path": "src/geospatial/geofence.service.ts",
                "content": self._build_geofence_service_inline(collection),
            }
        ]

    def generate_routing_service(
        self, collection: GeospatialCollection
    ) -> list[dict[str, str]]:
        """Sinh RoutingService class."""
        has_routing = any(spec.routing_enabled for spec in collection.reports)

        context = {
            "collection": collection,
            "has_routing": has_routing,
            "spec_count": len(collection.reports),
        }

        if self._template_exists("routing.service.ts.jinja2"):
            content = self._render("routing.service.ts.jinja2", context)
            return [{"path": "src/geospatial/routing.service.ts", "content": content}]

        return [
            {
                "path": "src/geospatial/routing.service.ts",
                "content": self._build_routing_service_inline(collection),
            }
        ]

    def generate_controller(
        self, collection: GeospatialCollection
    ) -> list[dict[str, str]]:
        """Sinh GeospatialController class."""
        context = {
            "collection": collection,
            "spec_count": len(collection.reports),
        }

        if self._template_exists("geospatial.controller.ts.jinja2"):
            content = self._render("geospatial.controller.ts.jinja2", context)
            return [
                {
                    "path": "src/geospatial/geospatial.controller.ts",
                    "content": content,
                }
            ]

        return [
            {
                "path": "src/geospatial/geospatial.controller.ts",
                "content": self._build_controller_inline(collection),
            }
        ]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _template_exists(self, name: str) -> bool:
        """Kiểm tra template có tồn tại không."""
        if self.template_dir is None:
            return False
        return (self.template_dir / name).exists()

    def _render(self, template_name: str, context: dict[str, Any]) -> str:
        """Render một Jinja2 template."""
        if self._env is None:
            raise EM.raise_error(
                ErrorCode.CP35_GEOSPEC_INVALID,
                reason="Jinja2 environment chưa được khởi tạo",
            )
        try:
            template = self._env.get_template(template_name)
            return template.render(**context)
        except TemplateNotFound:
            return ""
        except Exception as e:
            EM.raise_error(
                ErrorCode.CP35_GEOSPEC_INVALID,
                reason=f"Lỗi render template {template_name}: {e}",
            )

    # ------------------------------------------------------------------
    # Inline fallback generators (khi không có Jinja2 templates)
    # ------------------------------------------------------------------

    def _build_service_inline(self, collection: GeospatialCollection) -> str:
        """Build GeospatialService inline khi không có template."""
        has_reverse_geocoding = any(
            spec.reverse_geocoding_enabled for spec in collection.reports
        )

        code = "// Geospatial Service — Service tính toán địa lý.\n"
        code += "// Dùng @turf/turf cho geometry operations.\n\n"
        code += 'import { Injectable } from "@nestjs/common";\n'
        code += 'import * as turf from "@turf/turf";\n\n'
        code += "export class GeoPoint {\n"
        code += "  latitude: number;\n"
        code += "  longitude: number;\n"
        code += "  constructor(lat: number, lng: number) {\n"
        code += "    this.latitude = lat;\n"
        code += "    this.longitude = lng;\n"
        code += "  }\n"
        code += "}\n\n"
        code += "export interface GeospatialService {\n"
        code += "  calculateDistance(p1: GeoPoint, p2: GeoPoint, unit?: string): number;\n"
        code += "  reverseGeocode(lat: number, lng: number): Promise<string>;\n"
        code += "}\n\n"
        code += "@Injectable()\n"
        code += "export class GeospatialService {\n\n"
        code += "  // Haversine distance giữa 2 điểm tọa độ.\n"
        code += "  calculateDistance(p1: GeoPoint, p2: GeoPoint, unit: string = \"kilometers\"): number {\n"
        code += '    const pt1 = turf.point([p1.longitude, p1.latitude]);\n'
        code += '    const pt2 = turf.point([p2.longitude, p2.latitude]);\n'
        code += "    return turf.distance(pt1, pt2, { units: unit as any });\n"
        code += "  }\n\n"
        code += "  // Reverse geocoding — tra cứu địa chỉ từ tọa độ.\n"
        if has_reverse_geocoding:
            code += '  async reverseGeocode(lat: number, lng: number): Promise<string> {\n'
            code += '    const url = `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}`;\n'
            code += "    const resp = await fetch(url, {\n"
            code += '      headers: { "Accept-Language": "vi" },\n'
            code += "    });\n"
            code += '    const data = await resp.json() as { display_name: string };\n'
            code += "    return data.display_name || `(${lat}, ${lng})`;\n"
            code += "  }\n"
        else:
            code += "  // Reverse geocoding chưa được kích hoạt.\n"
            code += '  async reverseGeocode(lat: number, lng: number): Promise<string> {\n'
            code += '    throw new Error("Reverse geocoding không được kích hoạt");\n'
            code += "  }\n"
        code += "}\n"
        return code

    def _build_geofence_service_inline(self, collection: GeospatialCollection) -> str:
        """Build GeofenceService inline khi không có template."""
        all_geofences = []
        for spec in collection.reports:
            all_geofences.extend(spec.geofences)

        code = "// Geofence Service — Quản lý geofence và check enter/exit.\n"
        code += "// Hỗ trợ: Circle, Polygon, Rectangle.\n\n"
        code += 'import { Injectable } from "@nestjs/common";\n'
        code += 'import * as turf from "@turf/turf";\n\n'
        code += "export enum GeofenceShape {\n"
        code += '  CIRCLE = "circle",\n'
        code += '  POLYGON = "polygon",\n'
        code += '  RECTANGLE = "rectangle",\n'
        code += "}\n\n"
        code += "export interface GeoPoint {\n"
        code += "  latitude: number;\n"
        code += "  longitude: number;\n"
        code += "}\n\n"
        code += "export interface Geofence {\n"
        code += "  id: string;\n"
        code += "  name: string;\n"
        code += "  shape: GeofenceShape;\n"
        code += "  center?: GeoPoint;\n"
        code += "  radius_m?: number;\n"
        code += "  points?: GeoPoint[];\n"
        code += "  min_lat?: number;\n"
        code += "  min_lng?: number;\n"
        code += "  max_lat?: number;\n"
        code += "  max_lng?: number;\n"
        code += "  enabled: boolean;\n"
        code += "  metadata?: Record<string, any>;\n"
        code += "}\n\n"
        code += "export interface GeofenceCheckResult {\n"
        code += "  geofence_id: string;\n"
        code += "  inside: boolean;\n"
        code += "  event: string;\n"
        code += "}\n\n"
        code += "@Injectable()\n"
        code += "export class GeofenceService {\n"
        code += '  private readonly geofences: Map<string, Geofence> = new Map();\n\n'
        code += "  // Tạo geofence mới.\n"
        code += "  createGeofence(geofence: Geofence): void {\n"
        code += "    this.geofences.set(geofence.id, geofence);\n"
        code += "  }\n\n"
        code += "  // Kiểm tra điểm có nằm trong geofence không.\n"
        code += "  checkGeofence(geofence: Geofence, point: GeoPoint): boolean {\n"
        code += "    switch (geofence.shape) {\n"
        code += '      case GeofenceShape.CIRCLE:\n'
        code += "        return this._checkCircle(geofence, point);\n"
        code += '      case GeofenceShape.POLYGON:\n'
        code += "        return this._checkPolygon(geofence, point);\n"
        code += '      case GeofenceShape.RECTANGLE:\n'
        code += "        return this._checkRectangle(geofence, point);\n"
        code += "      default:\n"
        code += "        return false;\n"
        code += "    }\n"
        code += "  }\n\n"
        code += "  // Monitor điểm — trả về danh sách geofences chứa điểm.\n"
        code += "  monitorPoint(point: GeoPoint): GeofenceCheckResult[] {\n"
        code += "    const results: GeofenceCheckResult[] = [];\n"
        code += "    for (const [id, gf] of this.geofences) {\n"
        code += "      if (!gf.enabled) continue;\n"
        code += "      const inside = this.checkGeofence(gf, point);\n"
        code += "      results.push({\n"
        code += "        geofence_id: id,\n"
        code += "        inside,\n"
        code += '        event: inside ? "enter" : "exit",\n'
        code += "      });\n"
        code += "    }\n"
        code += "    return results;\n"
        code += "  }\n\n"
        code += "  // Liệt kê tất cả geofences.\n"
        code += "  listGeofences(): Geofence[] {\n"
        code += "    return Array.from(this.geofences.values());\n"
        code += "  }\n\n"
        code += "  // Circle: dùng turf.distance() để kiểm tra.\n"
        code += "  private _checkCircle(geofence: Geofence, point: GeoPoint): boolean {\n"
        code += "    if (!geofence.center || geofence.radius_m == null) return false;\n"
        code += "    const center = turf.point([geofence.center.longitude, geofence.center.latitude]);\n"
        code += "    const pt = turf.point([point.longitude, point.latitude]);\n"
        code += '    const dist = turf.distance(center, pt, { units: "meters" });\n'
        code += "    return dist <= geofence.radius_m;\n"
        code += "  }\n\n"
        code += "  // Polygon: dùng turf.booleanPointInPolygon().\n"
        code += "  private _checkPolygon(geofence: Geofence, point: GeoPoint): boolean {\n"
        code += "    if (!geofence.points || geofence.points.length < 3) return false;\n"
        code += "    const coords = geofence.points.map((p) => [p.longitude, p.latitude] as [number, number]);\n"
        code += "    // Đóng polygon: thêm điểm đầu vào cuối.\n"
        code += "    coords.push(coords[0]);\n"
        code += "    const polygon = turf.polygon([coords]);\n"
        code += "    const pt = turf.point([point.longitude, point.latitude]);\n"
        code += "    return turf.booleanPointInPolygon(pt, polygon);\n"
        code += "  }\n\n"
        code += "  // Rectangle: so sánh tọa độ min/max.\n"
        code += "  private _checkRectangle(geofence: Geofence, point: GeoPoint): boolean {\n"
        code += "    return (\n"
        code += "      point.latitude >= (geofence.min_lat ?? -90) &&\n"
        code += "      point.latitude <= (geofence.max_lat ?? 90) &&\n"
        code += "      point.longitude >= (geofence.min_lng ?? -180) &&\n"
        code += "      point.longitude <= (geofence.max_lng ?? 180)\n"
        code += "    );\n"
        code += "  }\n"
        code += "}\n"
        return code

    def _build_routing_service_inline(self, collection: GeospatialCollection) -> str:
        """Build RoutingService inline khi không có template."""
        code = "// Routing Service — Tính route qua OSRM API.\n\n"
        code += 'import { Injectable } from "@nestjs/common";\n'
        code += 'import fetch from "node-fetch";\n\n'
        code += "export interface RouteStep {\n"
        code += "  instruction: string;\n"
        code += "  distance_m: number;\n"
        code += "  duration_s: number;\n"
        code += "}\n\n"
        code += "export interface RouteResult {\n"
        code += "  origin: { latitude: number; longitude: number };\n"
        code += "  destination: { latitude: number; longitude: number };\n"
        code += "  distance_m: number;\n"
        code += "  duration_s: number;\n"
        code += "  geometry: { latitude: number; longitude: number }[];\n"
        code += "  steps: RouteStep[];\n"
        code += '  profile: "driving" | "walking" | "cycling";\n'
        code += "}\n\n"
        code += "export interface GeoPoint {\n"
        code += "  latitude: number;\n"
        code += "  longitude: number;\n"
        code += "}\n\n"
        code += "@Injectable()\n"
        code += "export class RoutingService {\n"
        code += '  private readonly osrmEndpoint: string;\n\n'
        code += "  constructor() {\n"
        code += '    this.osrmEndpoint =\n'
        code += '      process.env.OSRM_ENDPOINT || "https://router.project-osrm.org";\n'
        code += "  }\n\n"
        code += '  /**\n'
        code += "   * Tính route từ điểm A đến điểm B.\n"
        code += "   *\n"
        code += '   * @param origin Điểm xuất phát\n'
        code += "   * @param destination Điểm đến\n"
        code += '   * @param profile Profile di chuyển (mặc định: "driving")\n'
        code += "   */\n"
        code += "  async calculateRoute(\n"
        code += "    origin: GeoPoint,\n"
        code += "    destination: GeoPoint,\n"
        code += '    profile: string = "driving",\n'
        code += "  ): Promise<RouteResult> {\n"
        code += "    try {\n"
        code += "      const url = `${this.osrmEndpoint}/route/v1/${profile}/`;\n"
        code += "      const coordStr = `${origin.longitude},${origin.latitude};${destination.longitude},${destination.latitude}`;\n"
        code += "      const resp = await fetch(`${url}${coordStr}?overview=full&geometries=geojson`);\n"
        code += "      const data = await resp.json();\n"
        code += "      if (!data.routes || data.routes.length === 0) {\n"
        code += "        return this._fallbackRoute(origin, destination, profile);\n"
        code += "      }\n"
        code += "      const route = data.routes[0];\n"
        code += "      return {\n"
        code += "        origin: { latitude: origin.latitude, longitude: origin.longitude },\n"
        code += "        destination: { latitude: destination.latitude, longitude: destination.longitude },\n"
        code += "        distance_m: route.distance,\n"
        code += "        duration_s: route.duration,\n"
        code += "        geometry: (route.geometry.coordinates || []).map(\n"
        code += "          (c: [number, number]) => ({ latitude: c[1], longitude: c[0] }),\n"
        code += "        ),\n"
        code += "        steps: [],\n"
        code += "        profile: profile as any,\n"
        code += "      };\n"
        code += "    } catch {\n"
        code += "      return this._fallbackRoute(origin, destination, profile);\n"
        code += "    }\n"
        code += "  }\n\n"
        code += "  // Tính distance matrix cho nhiều điểm.\n"
        code += "  async calculateDistanceMatrix(\n"
        code += "    origins: GeoPoint[],\n"
        code += "    destinations: GeoPoint[],\n"
        code += '    profile: string = "driving",\n'
        code += "  ): Promise<{ distances: number[][]; durations: number[][] }> {\n"
        code += "    const originStr = origins.map((p) => `${p.longitude},${p.latitude}`).join(";");\n"
        code += "    const destStr = destinations.map((p) => `${p.longitude},${p.latitude}`).join(";");\n"
        code += "    const url = `${this.osrmEndpoint}/table/v1/${profile}/${originStr}:${destStr}`;\n"
        code += "    const resp = await fetch(url);\n"
        code += "    const data = await resp.json();\n"
        code += "    return {\n"
        code += "      distances: data.durations || [],\n"
        code += "      durations: data.durations || [],\n"
        code += "    };\n"
        code += "  }\n\n"
        code += "  // Fallback: straight-line khi OSRM unavailable.\n"
        code += "  private _fallbackRoute(\n"
        code += "    origin: GeoPoint,\n"
        code += "    destination: GeoPoint,\n"
        code += "    profile: string,\n"
        code += "  ): RouteResult {\n"
        code += "    const R = 6371000;\n"
        code += "    const dLat = ((destination.latitude - origin.latitude) * Math.PI) / 180;\n"
        code += "    const dLon = ((destination.longitude - origin.longitude) * Math.PI) / 180;\n"
        code += "    const a =\n"
        code += "      Math.sin(dLat / 2) ** 2 +\n"
        code += "      Math.cos((origin.latitude * Math.PI) / 180) *\n"
        code += "        Math.cos((destination.latitude * Math.PI) / 180) *\n"
        code += "        Math.sin(dLon / 2) ** 2;\n"
        code += "    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));\n"
        code += "    const distance = R * c;\n"
        code += "    const speed = profile === \"walking\" ? 1.4 : profile === \"cycling\" ? 5.5 : 15;\n"
        code += "    return {\n"
        code += "      origin: { latitude: origin.latitude, longitude: origin.longitude },\n"
        code += "      destination: { latitude: destination.latitude, longitude: destination.longitude },\n"
        code += "      distance_m: distance,\n"
        code += "      duration_s: distance / speed,\n"
        code += "      geometry: [origin, destination],\n"
        code += "      steps: [{ instruction: \"Đi thẳng\", distance_m: distance, duration_s: distance / speed }],\n"
        code += "      profile: profile as any,\n"
        code += "    };\n"
        code += "  }\n"
        code += "}\n"
        return code

    def _build_controller_inline(self, collection: GeospatialCollection) -> str:
        """Build GeospatialController inline khi không có template."""
        code = "// Geospatial Controller — API endpoints cho geospatial services.\n\n"
        code += 'import {\n'
        code += '  Controller,\n'
        code += '  Get,\n'
        code += '  Post,\n'
        code += '  Body,\n'
        code += '  Param,\n'
        code += '  Query,\n'
        code += '} from "@nestjs/common";\n'
        code += 'import { GeospatialService, GeoPoint } from "./geospatial.service";\n'
        code += 'import { GeofenceService, Geofence, GeofenceShape } from "./geofence.service";\n'
        code += 'import { RoutingService } from "./routing.service";\n\n'
        code += '@Controller("api/geospatial")\n'
        code += "export class GeospatialController {\n"
        code += "  constructor(\n"
        code += "    private readonly geoService: GeospatialService,\n"
        code += "    private readonly geofenceService: GeofenceService,\n"
        code += "    private readonly routingService: RoutingService,\n"
        code += "  ) {}\n\n"
        code += "  // Tính khoảng cách giữa 2 điểm tọa độ.\n"
        code += '  @Get("distance")\n'
        code += "  calculateDistance(\n"
        code += '    @Query("lat1") lat1: number,\n'
        code += '    @Query("lng1") lng1: number,\n'
        code += '    @Query("lat2") lat2: number,\n'
        code += '    @Query("lng2") lng2: number,\n'
        code += '    @Query("unit") unit: string = "kilometers",\n'
        code += "  ) {\n"
        code += "    const p1 = new GeoPoint(lat1, lng1);\n"
        code += "    const p2 = new GeoPoint(lat2, lng2);\n"
        code += "    return { distance: this.geoService.calculateDistance(p1, p2, unit), unit };\n"
        code += "  }\n\n"
        code += "  // Liệt kê tất cả geofences.\n"
        code += '  @Get("geofences")\n'
        code += "  listGeofences() {\n"
        code += "    return this.geofenceService.listGeofences();\n"
        code += "  }\n\n"
        code += "  // Tạo geofence mới.\n"
        code += '  @Post("geofences")\n'
        code += "  createGeofence(@Body() body: Geofence) {\n"
        code += "    this.geofenceService.createGeofence(body);\n"
        code += "    return { id: body.id, name: body.name, shape: body.shape };\n"
        code += "  }\n\n"
        code += "  // Kiểm tra điểm có nằm trong geofence không.\n"
        code += '  @Post("geofences/:id/check")\n'
        code += "  checkGeofence(\n"
        code += '    @Param("id") id: string,\n'
        code += "    @Body() body: { latitude: number; longitude: number },\n"
        code += "  ) {\n"
        code += "    const geofences = this.geofenceService.listGeofences();\n"
        code += "    const gf = geofences.find((g) => g.id === id);\n"
        code += "    if (!gf) {\n"
        code += "      throw new Error(`Geofence ${id} không tìm thấy`);\n"
        code += "    }\n"
        code += "    const point = { latitude: body.latitude, longitude: body.longitude };\n"
        code += "    const inside = this.geofenceService.checkGeofence(gf, point);\n"
        code += '    return { geofence_id: id, inside, event: inside ? "enter" : "exit" };\n'
        code += "  }\n\n"
        code += "  // Tính route từ điểm A đến điểm B.\n"
        code += '  @Post("route")\n'
        code += "  async calculateRoute(\n"
        code += "    @Body()\n"
        code += "    body: {\n"
        code += "      origin: { latitude: number; longitude: number };\n"
        code += "      destination: { latitude: number; longitude: number };\n"
        code += "      profile?: string;\n"
        code += "    },\n"
        code += "  ) {\n"
        code += '    const route = await this.routingService.calculateRoute(body.origin, body.destination, body.profile || "driving");\n'
        code += "    return route;\n"
        code += "  }\n\n"
        code += "  // Reverse geocoding — tra cứu địa chỉ từ tọa độ.\n"
        code += '  @Get("reverse-geocode")\n'
        code += "  async reverseGeocode(@Query(\"lat\") lat: number, @Query(\"lng\") lng: number) {\n"
        code += "    const address = await this.geoService.reverseGeocode(lat, lng);\n"
        code += "    return { latitude: lat, longitude: lng, address };\n"
        code += "  }\n"
        code += "}\n"
        return code
