# coding: utf-8
"""
Mô-đun models cho Geospatial Pack (CP35).

Định nghĩa các dataclass biểu diễn:
- GeoPoint: Điểm tọa độ địa lý (vĩ độ, kinh độ)
- Geofence: Vùng địa lý để monitor enter/exit events
- RouteStep: Một bước trong route
- RouteResult: Kết quả tính route
- GeospatialSpec: Spec cho geospatial service — parse từ DSL YAML
- GeospatialCollection: Collection chứa danh sách geospatial specs
- Enums: GeofenceShape, DistanceUnit, RoutingProfile, GeofenceEvent

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, List, Optional

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# ===========================================================================
# Enums
# ===========================================================================


class GeofenceShape(str, Enum):
    """Shape của geofence."""
    CIRCLE = "circle"
    POLYGON = "polygon"
    RECTANGLE = "rectangle"


class DistanceUnit(str, Enum):
    """Đơn vị đo khoảng cách."""
    METER = "meter"
    KILOMETER = "kilometer"
    MILE = "mile"


class RoutingProfile(str, Enum):
    """Profile tính route."""
    DRIVING = "driving"
    WALKING = "walking"
    CYCLING = "cycling"


class GeofenceEvent(str, Enum):
    """Sự kiện geofence."""
    ENTER = "enter"
    EXIT = "exit"


# ===========================================================================
# GeoPoint
# ===========================================================================


@dataclass
class GeoPoint:
    """Điểm tọa độ địa lý (vĩ độ, kinh độ).

    Attributes:
        latitude: Vĩ độ, khoảng -90 đến 90
        longitude: Kinh độ, khoảng -180 đến 180
    """
    latitude: float  # -90..90
    longitude: float  # -180..180

    def __post_init__(self) -> None:
        """Validate tọa độ sau khi khởi tạo."""
        if not -90 <= self.latitude <= 90:
            EM.raise_error(ErrorCode.CP35_INVALID_LATITUDE, value=self.latitude)
        if not -180 <= self.longitude <= 180:
            EM.raise_error(ErrorCode.CP35_INVALID_LONGITUDE, value=self.longitude)

    def to_dict(self) -> dict:
        """Chuyển GeoPoint sang dict format."""
        return {"latitude": self.latitude, "longitude": self.longitude}

    @classmethod
    def from_dict(cls, data: dict) -> "GeoPoint":
        """Tạo GeoPoint từ dict."""
        return cls(latitude=data["latitude"], longitude=data["longitude"])


# ===========================================================================
# Geofence
# ===========================================================================


@dataclass
class Geofence:
    """Geofence — vùng địa lý để monitor enter/exit events.

    Attributes:
        id: Định danh duy nhất
        name: Tên geofence
        shape: Hình dạng (circle, polygon, rectangle)
        center: Tâm hình tròn (chỉ dùng cho shape=CIRCLE)
        radius_m: Bán kính tính bằng mét (chỉ dùng cho shape=CIRCLE)
        points: Danh sách điểm (chỉ dùng cho shape=POLYGON)
        min_lat, min_lng, max_lat, max_lng: Boundary (chỉ dùng cho shape=RECTANGLE)
        enabled: Có kích hoạt không
        metadata: Metadata mở rộng
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    shape: GeofenceShape = GeofenceShape.CIRCLE
    # Circle: center + radius
    center: Optional[GeoPoint] = None
    radius_m: float = 0.0
    # Polygon: list of points (closed)
    points: List[GeoPoint] = field(default_factory=list)
    # Rectangle: min/max bounds
    min_lat: float = -90.0
    min_lng: float = -180.0
    max_lat: float = 90.0
    max_lng: float = 180.0
    enabled: bool = True
    metadata: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate geofence sau khi khởi tạo."""
        if not self.name or not self.name.strip():
            EM.raise_error(
                ErrorCode.CP35_GEOSPEC_INVALID,
                reason="name không được để trống",
            )
        if self.shape == GeofenceShape.CIRCLE:
            if self.center is None:
                EM.raise_error(
                    ErrorCode.CP35_GEOSPEC_INVALID,
                    reason="circle cần center",
                )
            if self.radius_m <= 0:
                EM.raise_error(
                    ErrorCode.CP35_GEOFENCE_EMPTY_RADIUS,
                    radius=self.radius_m,
                )
        elif self.shape == GeofenceShape.POLYGON:
            if len(self.points) < 3:
                EM.raise_error(
                    ErrorCode.CP35_GEOFENCE_TOO_FEW_POINTS,
                    count=len(self.points),
                )

    def contains(self, point: GeoPoint) -> bool:
        """Kiểm tra điểm có nằm trong geofence không."""
        if self.shape == GeofenceShape.CIRCLE and self.center:
            return self._circle_contains(point)
        elif self.shape == GeofenceShape.POLYGON:
            return self._polygon_contains(point)
        elif self.shape == GeofenceShape.RECTANGLE:
            return self._rectangle_contains(point)
        return False

    def _circle_contains(self, point: GeoPoint) -> bool:
        """Haversine distance check cho hình tròn."""
        R = 6371000.0  # Earth radius in meters
        lat1, lon1 = math.radians(self.center.latitude), math.radians(self.center.longitude)
        lat2, lon2 = math.radians(point.latitude), math.radians(point.longitude)
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c
        return distance <= self.radius_m

    def _polygon_contains(self, point: GeoPoint) -> bool:
        """Ray casting algorithm for point-in-polygon."""
        n = len(self.points)
        inside = False
        x, y = point.latitude, point.longitude
        p1x, p1y = self.points[0].latitude, self.points[0].longitude
        for i in range(1, n + 1):
            p2x, p2y = self.points[i % n].latitude, self.points[i % n].longitude
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xints = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xints:
                            inside = not inside
            p1x, p1y = p2x, p2y
        return inside

    def _rectangle_contains(self, point: GeoPoint) -> bool:
        """Kiểm tra điểm có nằm trong rectangle bounds không."""
        return (self.min_lat <= point.latitude <= self.max_lat and
                self.min_lng <= point.longitude <= self.max_lng)

    def to_dict(self) -> dict[str, Any]:
        """Chuyển geofence sang dict format."""
        result: dict[str, Any] = {
            "id": self.id,
            "name": self.name,
            "shape": self.shape.value,
            "enabled": self.enabled,
            "metadata": self.metadata,
        }
        if self.shape == GeofenceShape.CIRCLE and self.center:
            result["center"] = self.center.to_dict()
            result["radius_m"] = self.radius_m
        elif self.shape == GeofenceShape.POLYGON:
            result["points"] = [p.to_dict() for p in self.points]
        elif self.shape == GeofenceShape.RECTANGLE:
            result["min_lat"] = self.min_lat
            result["min_lng"] = self.min_lng
            result["max_lat"] = self.max_lat
            result["max_lng"] = self.max_lng
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Geofence":
        """Tạo Geofence từ dict."""
        shape = GeofenceShape(data.get("shape", "circle"))
        kwargs: dict[str, Any] = {
            "id": data.get("id", str(uuid.uuid4())),
            "name": data.get("name", ""),
            "shape": shape,
            "enabled": data.get("enabled", True),
            "metadata": data.get("metadata", {}),
        }
        if shape == GeofenceShape.CIRCLE:
            center_data = data.get("center", {})
            kwargs["center"] = GeoPoint.from_dict(center_data) if center_data else None
            kwargs["radius_m"] = data.get("radius_m", 0.0)
        elif shape == GeofenceShape.POLYGON:
            points_data = data.get("points", [])
            kwargs["points"] = [GeoPoint.from_dict(p) for p in points_data]
        elif shape == GeofenceShape.RECTANGLE:
            kwargs["min_lat"] = data.get("min_lat", -90.0)
            kwargs["min_lng"] = data.get("min_lng", -180.0)
            kwargs["max_lat"] = data.get("max_lat", 90.0)
            kwargs["max_lng"] = data.get("max_lng", 180.0)
        return cls(**kwargs)


# ===========================================================================
# RouteStep
# ===========================================================================


@dataclass
class RouteStep:
    """Một bước trong route.

    Attributes:
        instruction: Hướng dẫn di chuyển
        distance_m: Khoảng cách tính bằng mét
        duration_s: Thời gian ước tính tính bằng giây
    """
    instruction: str = ""
    distance_m: float = 0.0
    duration_s: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Chuyển route step sang dict format."""
        return {
            "instruction": self.instruction,
            "distance_m": self.distance_m,
            "duration_s": self.duration_s,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RouteStep":
        """Tạo RouteStep từ dict."""
        return cls(
            instruction=data.get("instruction", ""),
            distance_m=data.get("distance_m", 0.0),
            duration_s=data.get("duration_s", 0.0),
        )


# ===========================================================================
# RouteResult
# ===========================================================================


@dataclass
class RouteResult:
    """Kết quả tính route.

    Attributes:
        origin: Điểm xuất phát
        destination: Điểm đến
        distance_m: Tổng khoảng cách tính bằng mét
        duration_s: Tổng thời gian ước tính tính bằng giây
        geometry: Danh sách các điểm tọa độ trên route
        steps: Danh sách các bước hướng dẫn
        profile: Profile di chuyển (driving, walking, cycling)
    """
    origin: GeoPoint
    destination: GeoPoint
    distance_m: float = 0.0
    duration_s: float = 0.0
    geometry: List[GeoPoint] = field(default_factory=list)
    steps: List[RouteStep] = field(default_factory=list)
    profile: RoutingProfile = RoutingProfile.DRIVING

    def to_dict(self) -> dict[str, Any]:
        """Chuyển route result sang dict format."""
        return {
            "origin": self.origin.to_dict(),
            "destination": self.destination.to_dict(),
            "distance_m": self.distance_m,
            "duration_s": self.duration_s,
            "geometry": [p.to_dict() for p in self.geometry],
            "steps": [s.to_dict() for s in self.steps],
            "profile": self.profile.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RouteResult":
        """Tạo RouteResult từ dict."""
        profile_str = data.get("profile", "driving")
        try:
            profile = RoutingProfile(profile_str)
        except ValueError:
            profile = RoutingProfile.DRIVING

        return cls(
            origin=GeoPoint.from_dict(data["origin"]),
            destination=GeoPoint.from_dict(data["destination"]),
            distance_m=data.get("distance_m", 0.0),
            duration_s=data.get("duration_s", 0.0),
            geometry=[GeoPoint.from_dict(p) for p in data.get("geometry", [])],
            steps=[RouteStep.from_dict(s) for s in data.get("steps", [])],
            profile=profile,
        )


# ===========================================================================
# GeospatialSpec
# ===========================================================================


@dataclass
class GeospatialSpec:
    """Spec cho geospatial service — parse từ DSL YAML.

    Attributes:
        id: Định danh duy nhất của spec
        name: Tên hiển thị
        entity: Entity source (link CP01)
        geofences: Danh sách geofence definitions
        routing_enabled: Có bật routing không
        reverse_geocoding_enabled: Có bật reverse geocoding không
        notification_on_trigger: Có thông báo khi trigger event không
        metadata: Metadata mở rộng
    """
    id: str
    name: str = ""
    entity: str = ""
    geofences: List[Geofence] = field(default_factory=list)
    routing_enabled: bool = False
    reverse_geocoding_enabled: bool = False
    notification_on_trigger: bool = False
    metadata: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate geospatial spec sau khi khởi tạo."""
        if not self.id or not self.id.strip():
            EM.raise_error(
                ErrorCode.CP35_GEOSPEC_INVALID,
                reason="id không được để trống",
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển geospatial spec sang dict format."""
        return {
            "id": self.id,
            "name": self.name,
            "entity": self.entity,
            "geofences": [g.to_dict() for g in self.geofences],
            "routing_enabled": self.routing_enabled,
            "reverse_geocoding_enabled": self.reverse_geocoding_enabled,
            "notification_on_trigger": self.notification_on_trigger,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GeospatialSpec":
        """Tạo GeospatialSpec từ dict."""
        geofences_data = data.get("geofences", [])
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            entity=data.get("entity", ""),
            geofences=[Geofence.from_dict(g) for g in geofences_data],
            routing_enabled=data.get("routing_enabled", False),
            reverse_geocoding_enabled=data.get("reverse_geocoding_enabled", False),
            notification_on_trigger=data.get("notification_on_trigger", False),
            metadata=data.get("metadata", {}),
        )


# ===========================================================================
# GeospatialCollection
# ===========================================================================


@dataclass
class GeospatialCollection:
    """Collection chứa danh sách geospatial specs.

    Dùng làm output của GeospatialParser và input cho Stack Emitters.

    Attributes:
        reports: Danh sách GeospatialSpec
    """
    reports: List[GeospatialSpec] = field(default_factory=list)

    def add(self, spec: GeospatialSpec) -> None:
        """Thêm geospatial spec vào collection."""
        if self.get_by_id(spec.id):
            EM.raise_error(ErrorCode.DSL_DUPLICATE_NODE_ID, id=spec.id, kind="geospatial")
        self.reports.append(spec)

    def get_by_id(self, spec_id: str) -> Optional[GeospatialSpec]:
        """Tìm geospatial spec theo ID."""
        for spec in self.reports:
            if spec.id == spec_id:
                return spec
        return None

    def to_dict(self) -> dict[str, Any]:
        """Chuyển collection sang dict format."""
        return {
            "reports": [r.to_dict() for r in self.reports],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GeospatialCollection":
        """Tạo GeospatialCollection từ dict."""
        result = cls()
        result.reports = [GeospatialSpec.from_dict(r) for r in data.get("reports", [])]
        return result
