# coding: utf-8
"""
Mô-đun FastAPI emitter cho Geospatial Pack (CP35).

Emit code FastAPI cho:
- GeospatialService: service chính (distance, geocoding)
- GeofenceService: service geofence (circle/polygon/rectangle)
- RoutingService: service routing (OSRM client + fallback)
- GeospatialRoutes: API endpoints

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from midicoder.packs.cp_full_geospatial.models import (
    GeospatialCollection,
    GeospatialSpec,
    GeofenceShape,
)
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


class FastAPIGeospatialEmitter:
    """
    Emitter sinh code FastAPI cho geospatial services.

    Methods:
        emit(): Generate toàn bộ files từ GeospatialCollection
        generate_service(): Sinh GeospatialService (distance, geocoding)
        generate_geofence_service(): Sinh GeofenceService (circle/polygon/rectangle)
        generate_routing_service(): Sinh RoutingService (OSRM + fallback)
        generate_routes(): Sinh API routes
    """

    def __init__(self, stack_dir: str | None = None) -> None:
        """
        Init emitter.

        Args:
            stack_dir: Đường dẫn đến stack template directory
        """
        self.stack_dir = Path(stack_dir) if stack_dir else None

    def emit(
        self, collection: GeospatialCollection, output_dir: Path | None = None
    ) -> list[dict[str, str]]:
        """
        Generate toàn bộ files FastAPI từ GeospatialCollection.

        Args:
            collection: GeospatialCollection chứa geospatial specs
            output_dir: Output directory (optional)

        Returns:
            List của {path, content} cho mỗi file
        """
        if not collection.reports:
            EM.raise_error(ErrorCode.MDC-F23_GEOSPEC_INVALID, reason="Collection trống")

        result: list[dict[str, str]] = []
        result.extend(self.generate_service(collection))
        result.extend(self.generate_geofence_service(collection))
        result.extend(self.generate_routing_service(collection))
        result.extend(self.generate_routes(collection))
        return result

    # -----------------------------------------------------------------------
    # GeospatialService
    # -----------------------------------------------------------------------

    def generate_service(self, collection: GeospatialCollection) -> list[dict[str, str]]:
        """Sinh GeospatialService class — distance, geocoding."""
        spec_ids = [s.id for s in collection.reports]
        has_reverse = any(s.reverse_geocoding_enabled for s in collection.reports)

        # Build spec registry block
        spec_lines: list[str] = []
        for spec in collection.reports:
            spec_lines.append(
                '    "%s": {"id": "%s", "entity": "%s", "reverse_geocoding": %s},'
                % (spec.id, spec.id, spec.entity, str(spec.reverse_geocoding_enabled))
            )
        specs_block = "\n".join(spec_lines)

        code = '"""Geospatial Service — Service tính toán khoảng cách và geocoding.\n\n'
        code += "CP35: Geospatial Services\n"
        code += "\n"
        code += "Cung cấp:\n"
        code += "- Tính khoảng cách giữa 2 điểm (geopy)\n"
        code += "- Reverse/forward geocoding (Nominatim)\n"
        code += "- Batch geocoding\n"
        code += '"""\n\n'
        code += "import logging\n"
        code += "import time\n"
        code += "from typing import Any, Dict, List, Optional\n"
        code += "from dataclasses import dataclass, field\n"
        code += "from enum import Enum\n\n"
        code += "from geopy.distance import geodesic\n"
        code += "from geopy.geocoders import Nominatim\n\n"
        code += "# Inline model definitions (Rule V1: no midicoder imports)\n\n"
        code += "@dataclass\n"
        code += "class GeoPoint:\n"
        code += '    """Điểm tọa độ địa lý (vĩ độ, kinh độ)."""\n'
        code += "    latitude: float  # -90..90\n"
        code += "    longitude: float  # -180..180\n\n"
        code += "    def to_dict(self) -> dict:\n"
        code += '        """Chuyển GeoPoint sang dict format."""\n'
        code += '        return {"latitude": self.latitude, "longitude": self.longitude}\n\n'
        code += "    @classmethod\n"
        code += "    def from_dict(cls, data: dict) -> \"GeoPoint\":\n"
        code += '        """Tạo GeoPoint từ dict."""\n'
        code += '        return cls(latitude=data["latitude"], longitude=data["longitude"])\n\n\n'
        code += "class DistanceUnit(str, Enum):\n"
        code += '    """Đơn vị đo khoảng cách."""\n'
        code += '    METER = "meter"\n'
        code += '    KILOMETER = "kilometer"\n'
        code += '    MILE = "mile"\n\n\n'
        code += "# Conversion factors (meters → target)\n"
        code += 'UNITS = {"meter": 1.0, "kilometer": 0.001, "mile": 0.000621371}\n\n\n'
        code += "logger = logging.getLogger(__name__)\n\n\n"
        code += "class GeospatialService:\n"
        code += '    """Service tính toán khoảng cách và geocoding.\n\n'
        code += "    Cung cấp các phương thức:\n"
        code += "    - calculate_distance: tính khoảng cách 2 điểm\n"
        code += "    - reverse_geocode: reverse geocoding từ tọa độ\n"
        code += "    - forward_geocode: forward geocoding từ địa chỉ\n"
        code += "    - batch_geocode: batch reverse geocoding\n"
        code += '    """\n\n'
        code += "    # Spec registry\n"
        code += "    SPECS: Dict[str, Dict[str, Any]] = {\n"
        code += specs_block + "\n"
        code += "    }\n\n"
        code += "    def __init__(self, user_agent: str = \"MidicoderCE/1.0\") -> None:\n"
        code += '        """Init geospatial service.\n\n'
        code += "        Args:\n"
        code += '            user_agent: User agent cho Nominatim\n'
        code += '        """\n'
        code += '        self._nominatim = Nominatim(user_agent=user_agent)\n\n'
        code += "    def calculate_distance(\n"
        code += '        self,\n'
        code += "        point1: GeoPoint,\n"
        code += "        point2: GeoPoint,\n"
        code += '        unit: str = "meter",\n'
        code += "    ) -> float:\n"
        code += '        """Tính khoảng cách giữa 2 điểm địa lý.\n\n'
        code += "        Args:\n"
        code += "            point1: Điểm đầu tiên\n"
        code += "            point2: Điểm thứ hai\n"
        code += "            unit: Đơn vị đo (meter, kilometer, mile)\n\n"
        code += "        Returns:\n"
        code += "            Khoảng cách tính theo đơn vị\n\n"
        code += "        Raises:\n"
        code += "            ValueError: Nếu đơn vị không hợp lệ\n"
        code += '        """\n'
        code += "        if unit not in UNITS:\n"
        code += '            raise ValueError(f"Đơn vị không hợp lệ: {unit}. Dùng: {list(UNITS.keys())}")\n\n'
        code += "        coords1 = (point1.latitude, point1.longitude)\n"
        code += "        coords2 = (point2.latitude, point2.longitude)\n"
        code += "        meters = geodesic(coords1, coords2).meters\n"
        code += "        return meters * UNITS[unit]\n\n"
        code += "    def reverse_geocode(\n"
        code += "        self,\n"
        code += "        latitude: float,\n"
        code += "        longitude: float,\n"
        code += "    ) -> str:\n"
        code += '        """Reverse geocoding — từ tọa độ sang địa chỉ.\n\n'
        code += "        Args:\n"
        code += "            latitude: Vĩ độ\n"
        code += "            longitude: Kinh độ\n\n"
        code += "        Returns:\n"
        code += "            Địa chỉ dạng string hoặc empty string nếu không tìm thấy\n"
        code += '        """\n'
        code += "        try:\n"
        code += "            location = self._nominatim.reverse((latitude, longitude), language=\"vi\")\n"
        code += "            return location.address if location else \"\"\n"
        code += "        except Exception as e:\n"
        code += '            logger.warning("Reverse geocode failed: %s", str(e))\n'
        code += '            return ""\n\n'
        code += "    def forward_geocode(self, address: str) -> GeoPoint | None:\n"
        code += '        """Forward geocoding — từ địa chỉ sang tọa độ.\n\n'
        code += "        Args:\n"
        code += "            address: Địa chỉ dạng string\n\n"
        code += "        Returns:\n"
        code += "            GeoPoint hoặc None nếu không tìm thấy\n"
        code += '        """\n'
        code += "        try:\n"
        code += "            location = self._nominatim.geocode(address, language=\"vi\")\n"
        code += "            if location:\n"
        code += "                return GeoPoint(latitude=location.latitude, longitude=location.longitude)\n"
        code += "            return None\n"
        code += "        except Exception as e:\n"
        code += '            logger.warning("Forward geocode failed: %s", str(e))\n'
        code += "            return None\n\n"
        code += "    def batch_geocode(\n"
        code += "        self,\n"
        code += "        points: List[GeoPoint],\n"
        code += "        delay: float = 1.0,\n"
        code += "    ) -> List[Dict[str, Any]]:\n"
        code += '        """Batch reverse geocoding — xử lý nhiều điểm.\n\n'
        code += "        Args:\n"
        code += "            points: Danh sách GeoPoint\n"
        code += "            delay: Thời gian chờ giữa các request (giây)\n\n"
        code += "        Returns:\n"
        code += "            Danh sách kết quả với tọa độ và địa chỉ\n"
        code += '        """\n'
        code += "        results: List[Dict[str, Any]] = []\n"
        code += "        for point in points:\n"
        code += "            address = self.reverse_geocode(point.latitude, point.longitude)\n"
        code += "            results.append({\n"
        code += '                "point": point.to_dict(),\n'
        code += '                "address": address,\n'
        code += '                "found": bool(address),\n'
        code += "            })\n"
        code += "            time.sleep(delay)\n"
        code += "        return results\n"

        return [{"path": "app/services/geospatial_service.py", "content": code}]

    # -----------------------------------------------------------------------
    # GeofenceService
    # -----------------------------------------------------------------------

    def generate_geofence_service(self, collection: GeospatialCollection) -> list[dict[str, str]]:
        """Sinh GeofenceService class — create/check/monitor geofences."""
        code = '"""Geofence Service — Service quản lý geofence và check point.\n\n'
        code += "CP35: Geospatial Services\n"
        code += "\n"
        code += "Cung cấp:\n"
        code += "- Tạo geofence (circle, polygon, rectangle)\n"
        code += "- Kiểm tra điểm có nằm trong geofence không\n"
        code += "- Monitor enter/exit events\n"
        code += "- Haversine cho circle, ray casting cho polygon, bounding box cho rectangle\n"
        code += '"""\n\n'
        code += "import logging\n"
        code += "import math\n"
        code += "import uuid\n"
        code += "from typing import Any, Dict, List, Optional\n"
        code += "from dataclasses import dataclass, field\n"
        code += "from datetime import datetime, timezone\n"
        code += "from enum import Enum\n\n\n"
        code += "# Inline model definitions (Rule V1: no midicoder imports)\n\n"
        code += "@dataclass\n"
        code += "class GeoPoint:\n"
        code += '    """Điểm tọa độ địa lý (vĩ độ, kinh độ)."""\n'
        code += "    latitude: float  # -90..90\n"
        code += "    longitude: float  # -180..180\n\n"
        code += "    def to_dict(self) -> dict:\n"
        code += '        """Chuyển GeoPoint sang dict format."""\n'
        code += '        return {"latitude": self.latitude, "longitude": self.longitude}\n\n'
        code += "    @classmethod\n"
        code += "    def from_dict(cls, data: dict) -> \"GeoPoint\":\n"
        code += '        """Tạo GeoPoint từ dict.\"\""\n'
        code += '        return cls(latitude=data["latitude"], longitude=data["longitude"])\n\n\n'
        code += "class GeofenceShape(str, Enum):\n"
        code += '    """Hình dạng của geofence.\"\""\n'
        code += '    CIRCLE = "circle"\n'
        code += '    POLYGON = "polygon"\n'
        code += '    RECTANGLE = "rectangle"\n\n\n'
        code += "class GeofenceEvent(str, Enum):\n"
        code += '    """Sự kiện geofence.\"\""\n'
        code += '    ENTER = "enter"\n'
        code += '    EXIT = "exit"\n\n\n'
        code += "@dataclass\n"
        code += "class Geofence:\n"
        code += '    """Geofence — vùng địa lý để monitor enter/exit events.\"""\n'
        code += "    id: str = field(default_factory=lambda: str(uuid.uuid4()))\n"
        code += '    name: str = ""\n'
        code += "    shape: GeofenceShape = GeofenceShape.CIRCLE\n"
        code += "    center: Optional[GeoPoint] = None\n"
        code += "    radius_m: float = 0.0\n"
        code += "    points: List[GeoPoint] = field(default_factory=list)\n"
        code += "    min_lat: float = -90.0\n"
        code += "    min_lng: float = -180.0\n"
        code += "    max_lat: float = 90.0\n"
        code += "    max_lng: float = 180.0\n"
        code += "    enabled: bool = True\n"
        code += "    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))\n"
        code += "    metadata: dict = field(default_factory=dict)\n\n"
        code += "    def to_dict(self) -> Dict[str, Any]:\n"
        code += '        """Chuyển geofence sang dict format.\"""\n'
        code += "        result: Dict[str, Any] = {\n"
        code += '            "id": self.id,\n'
        code += '            "name": self.name,\n'
        code += '            "shape": self.shape.value,\n'
        code += '            "enabled": self.enabled,\n'
        code += '            "created_at": self.created_at.isoformat(),\n'
        code += '            "metadata": self.metadata,\n'
        code += "        }\n"
        code += "        if self.shape == GeofenceShape.CIRCLE and self.center:\n"
        code += '            result["center"] = self.center.to_dict()\n'
        code += '            result["radius_m"] = self.radius_m\n'
        code += "        elif self.shape == GeofenceShape.POLYGON:\n"
        code += '            result["points"] = [p.to_dict() for p in self.points]\n'
        code += "        elif self.shape == GeofenceShape.RECTANGLE:\n"
        code += '            result["min_lat"] = self.min_lat\n'
        code += '            result["min_lng"] = self.min_lng\n'
        code += '            result["max_lat"] = self.max_lat\n'
        code += '            result["max_lng"] = self.max_lng\n'
        code += "        return result\n\n\n"
        code += "@dataclass\n"
        code += "class GeofenceMonitorEvent:\n"
        code += '    """Sự kiện monitor geofence.\"""\n'
        code += '    geofence_id: str = ""\n'
        code += '    event_type: str = "enter"\n'
        code += "    point: Optional[GeoPoint] = None\n"
        code += "    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))\n"
        code += "    metadata: dict = field(default_factory=dict)\n\n"
        code += "    def to_dict(self) -> Dict[str, Any]:\n"
        code += '        """Chuyển event sang dict format.\"""\n'
        code += "        result: Dict[str, Any] = {\n"
        code += '            "geofence_id": self.geofence_id,\n'
        code += '            "event_type": self.event_type,\n'
        code += '            "timestamp": self.timestamp.isoformat(),\n'
        code += '            "metadata": self.metadata,\n'
        code += "        }\n"
        code += "        if self.point:\n"
        code += '            result["point"] = self.point.to_dict()\n'
        code += "        return result\n\n\n"
        code += "logger = logging.getLogger(__name__)\n\n\n"
        code += "class GeofenceService:\n"
        code += '    """Service quản lý geofence và check point.\n\n'
        code += "    Cung cấp các phương thức:\n"
        code += "    - create_geofence: tạo geofence mới\n"
        code += "    - check_geofence: kiểm tra điểm có trong geofence\n"
        code += "    - monitor_point: monitor enter/exit events\n"
        code += "    - list_geofences: liệt kê tất cả geofences\n"
        code += "    - delete_geofence: xóa geofence\n"
        code += '    """\n\n'
        code += "    def __init__(self) -> None:\n"
        code += "        \"\"\"Init geofence service.\"\"\"\n"
        code += "        self._geofences: Dict[str, Geofence] = {}\n"
        code += "        self._history: Dict[str, List[bool]] = {}  # geofence_id -> list of last states\n\n"
        code += "    def create_geofence(\n"
        code += "        self,\n"
        code += '        name: str,\n'
        code += '        shape: str = "circle",\n'
        code += "        center: Optional[Dict[str, float]] = None,\n"
        code += "        radius_m: float = 0.0,\n"
        code += "        points: Optional[List[Dict[str, float]]] = None,\n"
        code += "        min_lat: float = -90.0,\n"
        code += "        min_lng: float = -180.0,\n"
        code += "        max_lat: float = 90.0,\n"
        code += "        max_lng: float = 180.0,\n"
        code += "        metadata: Optional[Dict[str, Any]] = None,\n"
        code += "    ) -> Geofence:\n"
        code += '        """Tạo geofence mới.\n\n'
        code += "        Args:\n"
        code += "            name: Tên geofence\n"
        code += "            shape: Hình dạng (circle, polygon, rectangle)\n"
        code += "            center: Tâm hình tròn (circle)\n"
        code += "            radius_m: Bán kính tính bằng mét (circle)\n"
        code += "            points: Danh sách điểm (polygon)\n"
        code += "            min_lat, min_lng, max_lat, max_lng: Boundary (rectangle)\n"
        code += "            metadata: Metadata mở rộng\n\n"
        code += "        Returns:\n"
        code += "            Geofence đã tạo\n\n"
        code += "        Raises:\n"
        code += "            ValueError: Nếu tham số không hợp lệ\n"
        code += "        \"\"\"\n"
        code += "        try:\n"
        code += "            gf_shape = GeofenceShape(shape)\n"
        code += "        except ValueError:\n"
        code += '            valid = [s.value for s in GeofenceShape]\n'
        code += '            raise ValueError(f"Shape không hợp lệ: {shape}. Dùng: {valid}")\n\n'
        code += "        gf = Geofence(\n"
        code += "            name=name,\n"
        code += "            shape=gf_shape,\n"
        code += "            metadata=metadata or {},\n"
        code += "        )\n\n"
        code += "        if gf_shape == GeofenceShape.CIRCLE:\n"
        code += '            if not center:\n'
        code += '                raise ValueError("Circle cần center")\n'
        code += "            gf.center = GeoPoint.from_dict(center)\n"
        code += "            gf.radius_m = radius_m\n"
        code += "            if radius_m <= 0:\n"
        code += '                raise ValueError("Bán kính phải > 0")\n'
        code += "        elif gf_shape == GeofenceShape.POLYGON:\n"
        code += '            if not points or len(points) < 3:\n'
        code += '                raise ValueError("Polygon cần ít nhất 3 điểm")\n'
        code += "            gf.points = [GeoPoint.from_dict(p) for p in points]\n"
        code += "        elif gf_shape == GeofenceShape.RECTANGLE:\n"
        code += "            gf.min_lat = min_lat\n"
        code += "            gf.min_lng = min_lng\n"
        code += "            gf.max_lat = max_lat\n"
        code += "            gf.max_lng = max_lng\n\n"
        code += "        self._geofences[gf.id] = gf\n"
        code += "        self._history[gf.id] = []\n"
        code += '        logger.info("Created geofence: %s (%s)", gf.id, name)\n'
        code += "        return gf\n\n"
        code += "    def check_geofence(\n"
        code += "        self,\n"
        code += "        geofence_id: str,\n"
        code += "        point: Dict[str, float],\n"
        code += "    ) -> Dict[str, Any]:\n"
        code += '        """Kiểm tra điểm có nằm trong geofence không.\n\n'
        code += "        Args:\n"
        code += "            geofence_id: ID của geofence\n"
        code += "            point: Điểm cần kiểm tra {latitude, longitude}\n\n"
        code += "        Returns:\n"
        code += "            Dict với is_inside (bool) và distance_m\n\n"
        code += "        Raises:\n"
        code += "            ValueError: Nếu geofence không tìm thấy\n"
        code += "        \"\"\"\n"
        code += "        gf = self._geofences.get(geofence_id)\n"
        code += "        if not gf:\n"
        code += '            raise ValueError(f"Geofence không tìm thấy: {geofence_id}")\n'
        code += "        gp = GeoPoint.from_dict(point)\n"
        code += "        is_inside = self._contains(gf, gp)\n"
        code += "        distance = self._nearest_distance(gf, gp)\n"
        code += "        return {\n"
        code += '            "geofence_id": geofence_id,\n'
        code += '            "is_inside": is_inside,\n'
        code += '            "distance_m": distance,\n'
        code += '            "shape": gf.shape.value,\n'
        code += "        }\n\n"
        code += "    def monitor_point(\n"
        code += "        self,\n"
        code += "        geofence_id: str,\n"
        code += "        point: Dict[str, float],\n"
        code += "    ) -> GeofenceMonitorEvent:\n"
        code += '        """Monitor điểm để phát hiện enter/exit event.\n\n'
        code += "        Args:\n"
        code += "            geofence_id: ID của geofence\n"
        code += "            point: Điểm cần monitor {latitude, longitude}\n\n"
        code += "        Returns:\n"
        code += "            GeofenceMonitorEvent với event type (enter/exit)\n"
        code += "        \"\"\"\n"
        code += "        gf = self._geofences.get(geofence_id)\n"
        code += "        if not gf:\n"
        code += '            raise ValueError(f"Geofence không tìm thấy: {geofence_id}")\n'
        code += "        gp = GeoPoint.from_dict(point)\n"
        code += "        is_inside = self._contains(gf, gp)\n\n"
        code += "        history = self._history.get(geofence_id, [])\n"
        code += "        event_type = GeofenceEvent.ENTER.value\n"
        code += "        if history:\n"
        code += "            last_state = history[-1]\n"
        code += "            if last_state and not is_inside:\n"
        code += "                event_type = GeofenceEvent.EXIT.value\n"
        code += "            elif last_state == is_inside:\n"
        code += "                event_type = \"none\"\n"
        code += "        history.append(is_inside)\n\n"
        code += "        event = GeofenceMonitorEvent(\n"
        code += "            geofence_id=geofence_id,\n"
        code += "            event_type=event_type,\n"
        code += "            point=gp,\n"
        code += "        )\n"
        code += '        logger.info("Geofence event: %s (%s)", event_type, geofence_id)\n'
        code += "        return event\n\n"
        code += "    def list_geofences(self) -> List[Dict[str, Any]]:\n"
        code += '        """Liệt kê tất cả geofences.\n\n'
        code += "        Returns:\n"
        code += "            Danh sách geofences dưới dạng dict\n"
        code += "        \"\"\"\n"
        code += "        return [gf.to_dict() for gf in self._geofences.values()]\n\n"
        code += "    def get_geofence(self, geofence_id: str) -> Optional[Dict[str, Any]]:\n"
        code += '        """Lấy thông tin một geofence.\n\n'
        code += "        Args:\n"
        code += "            geofence_id: ID của geofence\n\n"
        code += "        Returns:\n"
        code += "            Dict của geofence hoặc None\n"
        code += "        \"\"\"\n"
        code += "        gf = self._geofences.get(geofence_id)\n"
        code += "        return gf.to_dict() if gf else None\n\n"
        code += "    def delete_geofence(self, geofence_id: str) -> bool:\n"
        code += '        """Xóa geofence.\n\n'
        code += "        Args:\n"
        code += "            geofence_id: ID của geofence\n\n"
        code += "        Returns:\n"
        code += "            True nếu xóa thành công, False nếu không tìm thấy\n"
        code += "        \"\"\"\n"
        code += "        if geofence_id in self._geofences:\n"
        code += "            del self._geofences[geofence_id]\n"
        code += "            self._history.pop(geofence_id, None)\n"
        code += '            logger.info("Deleted geofence: %s", geofence_id)\n'
        code += "            return True\n"
        code += "        return False\n\n"
        code += "    # ---------------------------------------------------------------\n"
        code += "    # Internal: Contains check\n"
        code += "    # ---------------------------------------------------------------\n\n"
        code += "    def _contains(self, gf: Geofence, point: GeoPoint) -> bool:\n"
        code += '        """Kiểm tra điểm có trong geofence không (dispatch theo shape).\"""\n'
        code += "        if gf.shape == GeofenceShape.CIRCLE:\n"
        code += "            return self._circle_contains(gf, point)\n"
        code += "        elif gf.shape == GeofenceShape.POLYGON:\n"
        code += "            return self._polygon_contains(gf, point)\n"
        code += "        elif gf.shape == GeofenceShape.RECTANGLE:\n"
        code += "            return self._rectangle_contains(gf, point)\n"
        code += "        return False\n\n"
        code += "    def _circle_contains(self, gf: Geofence, point: GeoPoint) -> bool:\n"
        code += '        """Haversine distance check cho hình tròn.\n\n'
        code += "        Tính khoảng cách Haversine giữa tâm và điểm,\n"
        code += "        so sánh với bán kính.\n"
        code += "        \"\"\"\n"
        code += "        if not gf.center:\n"
        code += "            return False\n"
        code += "        R = 6371000.0  # Bán kính Trái Đất (mét)\n"
        code += "        lat1 = math.radians(gf.center.latitude)\n"
        code += "        lon1 = math.radians(gf.center.longitude)\n"
        code += "        lat2 = math.radians(point.latitude)\n"
        code += "        lon2 = math.radians(point.longitude)\n"
        code += "        dlat = lat2 - lat1\n"
        code += "        dlon = lon2 - lon1\n"
        code += "        a = (\n"
        code += "            math.sin(dlat / 2) ** 2\n"
        code += "            + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2\n"
        code += "        )\n"
        code += "        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))\n"
        code += "        distance = R * c\n"
        code += "        return distance <= gf.radius_m\n\n"
        code += "    def _polygon_contains(self, gf: Geofence, point: GeoPoint) -> bool:\n"
        code += '        """Ray casting algorithm cho point-in-polygon.\n\n'
        code += "        Dùng ray casting để kiểm tra điểm có nằm trong\n"
        code += "        đa giác kín hay không.\n"
        code += "        \"\"\"\n"
        code += "        n = len(gf.points)\n"
        code += "        if n < 3:\n"
        code += "            return False\n"
        code += "        inside = False\n"
        code += "        x, y = point.latitude, point.longitude\n"
        code += "        p1x, p1y = gf.points[0].latitude, gf.points[0].longitude\n"
        code += "        for i in range(1, n + 1):\n"
        code += "            p2x, p2y = gf.points[i % n].latitude, gf.points[i % n].longitude\n"
        code += "            if y > min(p1y, p2y):\n"
        code += "                if y <= max(p1y, p2y):\n"
        code += "                    if x <= max(p1x, p2x):\n"
        code += "                        if p1y != p2y:\n"
        code += "                            xints = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x\n"
        code += "                        if p1x == p2x or x <= xints:\n"
        code += "                            inside = not inside\n"
        code += "            p1x, p1y = p2x, p2y\n"
        code += "        return inside\n\n"
        code += "    def _rectangle_contains(self, gf: Geofence, point: GeoPoint) -> bool:\n"
        code += '        """Bounding box check cho rectangle.\n\n'
        code += "        Kiểm tra điểm có nằm trong hộp boundary hay không.\n"
        code += "        \"\"\"\n"
        code += "        return (\n"
        code += "            gf.min_lat <= point.latitude <= gf.max_lat\n"
        code += "            and gf.min_lng <= point.longitude <= gf.max_lng\n"
        code += "        )\n\n"
        code += "    def _nearest_distance(self, gf: Geofence, point: GeoPoint) -> float:\n"
        code += '        """Tính khoảng cách gần nhất từ điểm đến biên geofence (mét).\n\n'
        code += "        Returns:\n"
        code += "            Khoảng cách tính bằng mét. Trả về 0 nếu điểm nằm trong.\n"
        code += "        \"\"\"\n"
        code += "        R = 6371000.0\n"
        code += "        if gf.shape == GeofenceShape.CIRCLE and gf.center:\n"
        code += "            lat1 = math.radians(gf.center.latitude)\n"
        code += "            lon1 = math.radians(gf.center.longitude)\n"
        code += "            lat2 = math.radians(point.latitude)\n"
        code += "            lon2 = math.radians(point.longitude)\n"
        code += "            dlat = lat2 - lat1\n"
        code += "            dlon = lon2 - lon1\n"
        code += "            a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2\n"
        code += "            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))\n"
        code += "            return abs(R * c - gf.radius_m)\n"
        code += "        elif gf.shape == GeofenceShape.RECTANGLE:\n"
        code += "            if self._rectangle_contains(gf, point):\n"
        code += "                return 0.0\n"
        code += "            # Approximate: distance to nearest corner\n"
        code += "            corners = [\n"
        code += "                GeoPoint(gf.min_lat, gf.min_lng),\n"
        code += "                GeoPoint(gf.min_lat, gf.max_lng),\n"
        code += "                GeoPoint(gf.max_lat, gf.min_lng),\n"
        code += "                GeoPoint(gf.max_lat, gf.max_lng),\n"
        code += "            ]\n"
        code += "            min_d = float(\"inf\")\n"
        code += "            for corner in corners:\n"
        code += "                la1 = math.radians(corner.latitude)\n"
        code += "                lo1 = math.radians(corner.longitude)\n"
        code += "                la2 = math.radians(point.latitude)\n"
        code += "                lo2 = math.radians(point.longitude)\n"
        code += "                dlat = la2 - la1\n"
        code += "                dlon = lo2 - lo1\n"
        code += "                a = math.sin(dlat / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin(dlon / 2) ** 2\n"
        code += "                c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))\n"
        code += "                min_d = min(min_d, R * c)\n"
        code += "            return min_d\n"
        code += "        return 0.0\n"

        return [{"path": "app/services/geofence_service.py", "content": code}]

    # -----------------------------------------------------------------------
    # RoutingService
    # -----------------------------------------------------------------------

    def generate_routing_service(self, collection: GeospatialCollection) -> list[dict[str, str]]:
        """Sinh RoutingService class — OSRM client + fallback."""
        code = '"""Routing Service — Service tính route và distance matrix.\n\n'
        code += "CP35: Geospatial Services\n"
        code += "\n"
        code += "Cung cấp:\n"
        code += "- Tính route giữa 2 điểm (OSRM API)\n"
        code += "- Tính distance matrix cho nhiều điểm\n"
        code += "- Fallback sang straight-line distance khi OSRM không khả dụng\n"
        code += '"""\n\n'
        code += "import json\n"
        code += "import logging\n"
        code += "import math\n"
        code += "from typing import Any, Dict, List, Optional\n"
        code += "from dataclasses import dataclass, field\n"
        code += "from enum import Enum\n\n"
        code += "import requests\n\n\n"
        code += "# Inline model definitions (Rule V1: no midicoder imports)\n\n"
        code += "@dataclass\n"
        code += "class GeoPoint:\n"
        code += '    """Điểm tọa độ địa lý (vĩ độ, kinh độ).\"""\n'
        code += "    latitude: float  # -90..90\n"
        code += "    longitude: float  # -180..180\n\n"
        code += "    def to_dict(self) -> dict:\n"
        code += '        """Chuyển GeoPoint sang dict format.\"""\n'
        code += '        return {"latitude": self.latitude, "longitude": self.longitude}\n\n'
        code += "    @classmethod\n"
        code += "    def from_dict(cls, data: dict) -> \"GeoPoint\":\n"
        code += '        """Tạo GeoPoint từ dict.\"""\n'
        code += '        return cls(latitude=data["latitude"], longitude=data["longitude"])\n\n\n'
        code += "class RoutingProfile(str, Enum):\n"
        code += '    """Profile tính route.\"""\n'
        code += '    DRIVING = "driving"\n'
        code += '    WALKING = "walking"\n'
        code += '    CYCLING = "cycling"\n\n\n'
        code += "@dataclass\n"
        code += "class RouteStep:\n"
        code += '    """Một bước trong route.\"""\n'
        code += '    instruction: str = ""\n'
        code += "    distance_m: float = 0.0\n"
        code += "    duration_s: float = 0.0\n\n"
        code += "    def to_dict(self) -> Dict[str, Any]:\n"
        code += '        """Chuyển route step sang dict format.\"""\n'
        code += "        return {\n"
        code += '            "instruction": self.instruction,\n'
        code += '            "distance_m": self.distance_m,\n'
        code += '            "duration_s": self.duration_s,\n'
        code += "        }\n\n\n"
        code += "@dataclass\n"
        code += "class RouteResult:\n"
        code += '    """Kết quả tính route.\"""\n'
        code += "    origin: GeoPoint\n"
        code += "    destination: GeoPoint\n"
        code += "    distance_m: float = 0.0\n"
        code += "    duration_s: float = 0.0\n"
        code += "    geometry: List[GeoPoint] = field(default_factory=list)\n"
        code += "    steps: List[RouteStep] = field(default_factory=list)\n"
        code += '    profile: str = "driving"\n'
        code += "    used_osrm: bool = True\n\n"
        code += "    def to_dict(self) -> Dict[str, Any]:\n"
        code += '        """Chuyển route result sang dict format.\"""\n'
        code += "        return {\n"
        code += '            "origin": self.origin.to_dict(),\n'
        code += '            "destination": self.destination.to_dict(),\n'
        code += '            "distance_m": self.distance_m,\n'
        code += '            "duration_s": self.duration_s,\n'
        code += '            "geometry": [p.to_dict() for p in self.geometry],\n'
        code += '            "steps": [s.to_dict() for s in self.steps],\n'
        code += '            "profile": self.profile,\n'
        code += '            "used_osrm": self.used_osrm,\n'
        code += "        }\n\n\n"
        code += "logger = logging.getLogger(__name__)\n\n\n"
        code += "class RoutingService:\n"
        code += '    """Service tính route và distance matrix.\n\n'
        code += "    Dùng OSRM API để tính route thực tế và\n"
        code += "    fallback sang straight-line distance khi OSRM không khả dụng.\n"
        code += "    \"\"\"\n\n"
        code += '    OSRM_PROFILES: Dict[str, str] = {\n'
        code += '        "driving": "car",\n'
        code += '        "walking": "foot",\n'
        code += '        "cycling": "bike",\n'
        code += "    }\n\n"
        code += "    def __init__(\n"
        code += '        self, osrm_url: str = "http://localhost:5000"\n'
        code += "    ) -> None:\n"
        code += '        """Init routing service.\n\n'
        code += "        Args:\n"
        code += "            osrm_url: URL của OSRM server\n"
        code += "        \"\"\"\n"
        code += "        self._osrm_url = osrm_url\n\n"
        code += "    def calculate_route(\n"
        code += "        self,\n"
        code += "        origin: Dict[str, float],\n"
        code += "        destination: Dict[str, float],\n"
        code += '        profile: str = "driving",\n'
        code += "    ) -> RouteResult:\n"
        code += '        """Tính route giữa 2 điểm.\n\n'
        code += "        Args:\n"
        code += "            origin: Điểm xuất phát {latitude, longitude}\n"
        code += "            destination: Điểm đến {latitude, longitude}\n"
        code += "            profile: Profile di chuyển (driving, walking, cycling)\n\n"
        code += "        Returns:\n"
        code += "            RouteResult với distance, duration, geometry, steps\n"
        code += "        \"\"\"\n"
        code += "        origin_point = GeoPoint.from_dict(origin)\n"
        code += "        dest_point = GeoPoint.from_dict(destination)\n\n"
        code += "        osrm_profile = self.OSRM_PROFILES.get(profile, \"car\")\n"
        code += "        result = self._call_osrm(\n"
        code += "            origin_point, dest_point, osrm_profile\n"
        code += "        )\n\n"
        code += "        if result is None:\n"
        code += '            logger.warning("OSRM unavailable, using straight-line fallback")\n'
        code += "            result = self._fallback_straight_line(origin_point, dest_point, profile)\n\n"
        code += "        return result\n\n"
        code += "    def calculate_distance_matrix(\n"
        code += "        self,\n"
        code += "        points: List[Dict[str, float]],\n"
        code += '        profile: str = "driving",\n'
        code += "    ) -> Dict[str, Any]:\n"
        code += '        """Tính distance matrix cho nhiều điểm.\n\n'
        code += "        Args:\n"
        code += "            points: Danh sách điểm {latitude, longitude}\n"
        code += "            profile: Profile di chuyển\n\n"
        code += "        Returns:\n"
        code += "            Dict chứa distance và duration matrices\n"
        code += "        \"\"\"\n"
        code += "        geo_points = [GeoPoint.from_dict(p) for p in points]\n"
        code += "        n = len(geo_points)\n"
        code += "        osrm_profile = self.OSRM_PROFILES.get(profile, \"car\")\n\n"
        code += "        distances: List[List[float]] = [[0.0] * n for _ in range(n)]\n"
        code += "        durations: List[List[float]] = [[0.0] * n for _ in range(n)]\n\n"
        code += "        # Try OSRM table API\n"
        code += "        osrm_success = False\n"
        code += "        coords_str = \";\".join(\n"
        code += "            f\"{p.longitude},{p.latitude}\" for p in geo_points\n"
        code += "        )\n"
        code += "        try:\n"
        code += "            url = f\"{self._osrm_url}/table/{osrm_profile}/v1/table/{coords_str}\"\n"
        code += "            params = {\"annotations\": \"distance,duration\"}\n"
        code += "            resp = requests.get(url, params=params, timeout=10)\n"
        code += "            if resp.status_code == 200:\n"
        code += "                data = resp.json()\n"
        code += "                if \"durations\" in data and \"distances\" in data:\n"
        code += "                    durations = data[\"durations\"]\n"
        code += "                    distances_raw = data[\"distances\"]\n"
        code += "                    # OSRM returns seconds, convert to meters for distances\n"
        code += "                    distances = distances_raw\n"
        code += "                    osrm_success = True\n"
        code += "        except Exception as e:\n"
        code += '            logger.warning("OSRM table failed: %s", str(e))\n\n'
        code += "        # Fallback: Haversine for all pairs\n"
        code += "        if not osrm_success:\n"
        code += "            for i in range(n):\n"
        code += "                for j in range(n):\n"
        code += "                    if i != j:\n"
        code += "                        distances[i][j] = self._haversine(geo_points[i], geo_points[j])\n"
        code += "                        # Approximate duration (assumes 50 km/h driving)\n"
        code += "                        durations[i][j] = distances[i][j] / (50000.0 / 3600.0)\n\n"
        code += "        return {\n"
        code += '            "distances": distances,\n'
        code += '            "durations": durations,\n'
        code += '            "points": [p.to_dict() for p in geo_points],\n'
        code += '            "used_osrm": osrm_success,\n'
        code += "        }\n\n"
        code += "    # ---------------------------------------------------------------\n"
        code += "    # Internal: OSRM HTTP client\n"
        code += "    # ---------------------------------------------------------------\n\n"
        code += "    def _call_osrm(\n"
        code += "        self,\n"
        code += "        origin: GeoPoint,\n"
        code += "        destination: GeoPoint,\n"
        code += '        profile: str = "car",\n'
        code += "    ) -> Optional[RouteResult]:\n"
        code += '        """Gọi OSRM API để tính route.\n\n'
        code += "        Args:\n"
        code += "            origin: Điểm xuất phát\n"
        code += "            destination: Điểm đến\n"
        code += "            profile: OSRM profile (car, foot, bike)\n\n"
        code += "        Returns:\n"
        code += "            RouteResult hoặc None nếu thất bại\n"
        code += "        \"\"\"\n"
        code += "        coord_str = f\"{origin.longitude},{origin.latitude};{destination.longitude},{destination.latitude}\"\n"
        code += "        url = f\"{self._osrm_url}/route/{profile}/v1/route/{coord_str}\"\n"
        code += "        try:\n"
        code += "            resp = requests.get(url, timeout=10)\n"
        code += "            if resp.status_code != 200:\n"
        code += '                logger.warning("OSRM returned status %d", resp.status_code)\n'
        code += "                return None\n\n"
        code += "            data = resp.json()\n"
        code += "            if data.get(\"code\") != \"Ok\" or not data.get(\"routes\"):\n"
        code += '                logger.warning("OSRM no route found")\n'
        code += "                return None\n\n"
        code += "            route = data[\"routes\"][0]\n"
        code += "            # Parse geometry (encoded polyline)\n"
        code += "            geometry = self._decode_geometry(route.get(\"geometry\", \"\"))\n"
        code += "            # Parse steps\n"
        code += "            steps = self._parse_steps(route.get(\"legs\", [{}])[0].get(\"steps\", []))\n\n"
        code += "            return RouteResult(\n"
        code += "                origin=origin,\n"
        code += "                destination=destination,\n"
        code += '                distance_m=route.get("distance", 0.0),\n'
        code += '                duration_s=route.get("duration", 0.0),\n'
        code += "                geometry=geometry,\n"
        code += "                steps=steps,\n"
        code += '                profile=profile,\n'
        code += "                used_osrm=True,\n"
        code += "            )\n\n"
        code += "        except requests.RequestException as e:\n"
        code += '            logger.warning("OSRM request failed: %s", str(e))\n'
        code += "            return None\n"
        code += "        except (json.JSONDecodeError, KeyError, IndexError) as e:\n"
        code += '            logger.warning("OSRM parse error: %s", str(e))\n'
        code += "            return None\n\n"
        code += "    def _fallback_straight_line(\n"
        code += "        self,\n"
        code += "        origin: GeoPoint,\n"
        code += "        destination: GeoPoint,\n"
        code += '        profile: str = "driving",\n'
        code += "    ) -> RouteResult:\n"
        code += '        """Fallback khi OSRM không khả dụng — dùng Haversine.\n\n'
        code += "        Tính khoảng cách thẳng và ước lượng thời gian.\n"
        code += "        \"\"\"\n"
        code += "        distance = self._haversine(origin, destination)\n"
        code += "        # Approximate speed: 50 km/h driving, 5 km/h walking, 15 km/h cycling\n"
        code += "        speed_map = {\"driving\": 50000.0, \"walking\": 5000.0, \"cycling\": 15000.0}\n"
        code += "        speed = speed_map.get(profile, 50000.0) / 3600.0  # m/s\n"
        code += "        duration = distance / speed if speed > 0 else 0.0\n\n"
        code += "        return RouteResult(\n"
        code += "            origin=origin,\n"
        code += "            destination=destination,\n"
        code += "            distance_m=distance,\n"
        code += "            duration_s=duration,\n"
        code += "            geometry=[origin, destination],\n"
        code += "            steps=[RouteStep(\n"
        code += '                instruction=f"Di chuyển từ điểm xuất phát đến điểm đến ({distance:.0f}m)",\n'
        code += "                distance_m=distance,\n"
        code += "                duration_s=duration,\n"
        code += "            )],\n"
        code += "            profile=profile,\n"
        code += "            used_osrm=False,\n"
        code += "        )\n\n"
        code += "    def _haversine(self, p1: GeoPoint, p2: GeoPoint) -> float:\n"
        code += '        """Tính khoảng cách Haversine giữa 2 điểm (mét).\"""\n'
        code += "        R = 6371000.0\n"
        code += "        lat1 = math.radians(p1.latitude)\n"
        code += "        lon1 = math.radians(p1.longitude)\n"
        code += "        lat2 = math.radians(p2.latitude)\n"
        code += "        lon2 = math.radians(p2.longitude)\n"
        code += "        dlat = lat2 - lat1\n"
        code += "        dlon = lon2 - lon1\n"
        code += "        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2\n"
        code += "        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))\n"
        code += "        return R * c\n\n"
        code += "    def _decode_geometry(self, encoded: str) -> List[GeoPoint]:\n"
        code += '        """Decode polyline6 geometry từ OSRM.\n\n'
        code += "        Returns:\n"
        code += "            Danh sách GeoPoint từ encoded polyline\n"
        code += "        \"\"\"\n"
        code += "        if not encoded:\n"
        code += "            return []\n"
        code += "        coords: List[GeoPoint] = []\n"
        code += "        index = 0\n"
        code += "        lat = 0\n"
        code += "        lng = 0\n"
        code += "        while index < len(encoded):\n"
        code += "            b, lat_shift, lng_shift = None, None, None\n"
        code += "            result_shift = 0\n"
        code += "            result = 0\n"
        code += "            while True:\n"
        code += "                b = ord(encoded[index]) - 63\n"
        code += "                index += 1\n"
        code += "                result |= (b & 0x1f) << result_shift\n"
        code += "                result_shift += 5\n"
        code += "                if b < 0x20:\n"
        code += "                    break\n"
        code += "            lat += (~(result >> 1) if result & 1 else (result >> 1))\n"
        code += "            result = 0\n"
        code += "            result_shift = 0\n"
        code += "            while True:\n"
        code += "                b = ord(encoded[index]) - 63\n"
        code += "                index += 1\n"
        code += "                result |= (b & 0x1f) << result_shift\n"
        code += "                result_shift += 5\n"
        code += "                if b < 0x20:\n"
        code += "                    break\n"
        code += "            lng += (~(result >> 1) if result & 1 else (result >> 1))\n"
        code += "            coords.append(GeoPoint(latitude=lat / 1e5, longitude=lng / 1e5))\n"
        code += "        return coords\n\n"
        code += "    def _parse_steps(self, steps_data: List[Dict[str, Any]]) -> List[RouteStep]:\n"
        code += '        """Parse OSRM step data thành RouteStep list.\"""\n'
        code += "        steps: List[RouteStep] = []\n"
        code += "        for step in steps_data:\n"
        code += "            steps.append(RouteStep(\n"
        code += '                instruction=step.get("maneuver", {}).get("instruction", ""),\n'
        code += '                distance_m=step.get("distance", 0.0),\n'
        code += '                duration_s=step.get("duration", 0.0),\n'
        code += "            ))\n"
        code += "        return steps\n"

        return [{"path": "app/services/routing_service.py", "content": code}]

    # -----------------------------------------------------------------------
    # Routes
    # -----------------------------------------------------------------------

    def generate_routes(self, collection: GeospatialCollection) -> list[dict[str, str]]:
        """Sinh FastAPI API routes cho geospatial."""
        code = '"""Geospatial API Routes — Endpoints cho geospatial services.\n\n'
        code += "CP35: Geospatial Services\n"
        code += "\n"
        code += "Endpoints:\n"
        code += "- GET /api/geospatial/distance — tính khoảng cách 2 điểm\n"
        code += "- GET /api/geospatial/geofences — list geofences\n"
        code += "- POST /api/geospatial/geofences — tạo geofence\n"
        code += "- POST /api/geospatial/geofences/{id}/check — check point trong geofence\n"
        code += "- POST /api/geospatial/route — tính route\n"
        code += "- GET /api/geospatial/reverse-geocode — reverse geocoding\n"
        code += '"""\n\n'
        code += "from fastapi import APIRouter, Depends, HTTPException, Query\n"
        code += "from pydantic import BaseModel, Field\n"
        code += "from typing import Dict, List, Optional\n\n"
        code += "from app.services.geospatial_service import GeospatialService, GeoPoint as ServiceGeoPoint\n"
        code += "from app.services.geofence_service import GeofenceService\n"
        code += "from app.services.routing_service import RoutingService\n\n\n"
        code += "router = APIRouter(prefix=\"/api/geospatial\", tags=[\"geospatial\"])\n\n\n"
        code += "# ---------------------------------------------------------------------------\n"
        code += "# Pydantic schemas\n"
        code += "# ---------------------------------------------------------------------------\n\n"
        code += "class DistanceRequest(BaseModel):\n"
        code += '    """Request schema cho tính khoảng cách.\"""\n'
        code += '    lat1: float = Field(..., ge=-90, le=90, description="Vĩ độ điểm 1")\n'
        code += '    lon1: float = Field(..., ge=-180, le=180, description="Kinh độ điểm 1")\n'
        code += '    lat2: float = Field(..., ge=-90, le=90, description="Vĩ độ điểm 2")\n'
        code += '    lon2: float = Field(..., ge=-180, le=180, description="Kinh độ điểm 2")\n'
        code += '    unit: str = Field("meter", description="Đơn vị: meter, kilometer, mile")\n\n\n'
        code += "class DistanceResponse(BaseModel):\n"
        code += '    """Response schema cho khoảng cách.\"""\n'
        code += "    distance: float\n"
        code += '    unit: str\n\n\n'
        code += "class GeofenceCreateRequest(BaseModel):\n"
        code += '    """Request schema cho tạo geofence.\"""\n'
        code += '    name: str = Field(..., description="Tên geofence")\n'
        code += '    shape: str = Field("circle", description="Hình dạng: circle, polygon, rectangle")\n'
        code += '    center: Optional[Dict[str, float]] = Field(None, description="Tâm (circle)")\n'
        code += '    radius_m: float = Field(0.0, description="Bán kính (circle)")\n'
        code += '    points: Optional[List[Dict[str, float]]] = Field(None, description="Điểm (polygon)")\n'
        code += '    min_lat: float = Field(-90.0, description="Min vĩ độ (rectangle)")\n'
        code += '    min_lng: float = Field(-180.0, description="Min kinh độ (rectangle)")\n'
        code += '    max_lat: float = Field(90.0, description="Max vĩ độ (rectangle)")\n'
        code += '    max_lng: float = Field(180.0, description="Max kinh độ (rectangle)")\n'
        code += '    metadata: Optional[Dict] = Field(None, description="Metadata")\n\n\n'
        code += "class GeofenceCheckRequest(BaseModel):\n"
        code += '    """Request schema cho check point trong geofence.\"""\n'
        code += '    latitude: float = Field(..., description="Vĩ độ điểm")\n'
        code += '    longitude: float = Field(..., description="Kinh độ điểm")\n\n\n'
        code += "class GeofenceCheckResponse(BaseModel):\n"
        code += '    """Response schema cho check geofence.\"""\n'
        code += '    geofence_id: str\n'
        code += "    is_inside: bool\n"
        code += "    distance_m: float\n"
        code += '    shape: str\n\n\n'
        code += "class RouteRequest(BaseModel):\n"
        code += '    """Request schema cho tính route.\"""\n'
        code += '    origin_lat: float = Field(..., description="Vĩ độ điểm xuất phát")\n'
        code += '    origin_lon: float = Field(..., description="Kinh độ điểm xuất phát")\n'
        code += '    dest_lat: float = Field(..., description="Vĩ độ điểm đến")\n'
        code += '    dest_lon: float = Field(..., description="Kinh độ điểm đến")\n'
        code += '    profile: str = Field("driving", description="Profile: driving, walking, cycling")\n\n\n'
        code += "class ReverseGeocodeRequest(BaseModel):\n"
        code += '    """Request schema cho reverse geocoding.\"""\n'
        code += '    latitude: float = Field(..., description="Vĩ độ")\n'
        code += '    longitude: float = Field(..., description="Kinh độ")\n\n\n'
        code += "class ReverseGeocodeResponse(BaseModel):\n"
        code += '    """Response schema cho reverse geocoding.\"""\n'
        code += '    address: str\n'
        code += "    latitude: float\n"
        code += "    longitude: float\n\n\n"
        code += "# ---------------------------------------------------------------------------\n"
        code += "# Dependency injectors\n"
        code += "# ---------------------------------------------------------------------------\n\n"
        code += "_geospatial_service = GeospatialService()\n"
        code += "_geofence_service = GeofenceService()\n"
        code += "_routing_service = RoutingService()\n\n\n"
        code += "# ---------------------------------------------------------------------------\n"
        code += "# Endpoints\n"
        code += "# ---------------------------------------------------------------------------\n\n"
        code += "@router.get(\"/distance\", response_model=DistanceResponse)\n"
        code += "def calculate_distance(\n"
        code += '    lat1: float = Query(..., ge=-90, le=90, description="Vĩ độ điểm 1"),\n'
        code += '    lon1: float = Query(..., ge=-180, le=180, description="Kinh độ điểm 1"),\n'
        code += '    lat2: float = Query(..., ge=-90, le=90, description="Vĩ độ điểm 2"),\n'
        code += '    lon2: float = Query(..., ge=-180, le=180, description="Kinh độ điểm 2"),\n'
        code += '    unit: str = Query("meter", description="Đơn vị: meter, kilometer, mile"),\n'
        code += "):\n"
        code += '    """Tính khoảng cách giữa 2 điểm địa lý.\n\n'
        code += "    Args:\n"
        code += "        lat1, lon1: Tọa độ điểm 1\n"
        code += "        lat2, lon2: Tọa độ điểm 2\n"
        code += "        unit: Đơn vị đo\n\n"
        code += "    Returns:\n"
        code += "        Khoảng cách theo đơn vị\n"
        code += "    \"\"\"\n"
        code += "    point1 = ServiceGeoPoint(latitude=lat1, longitude=lon1)\n"
        code += "    point2 = ServiceGeoPoint(latitude=lat2, longitude=lon2)\n"
        code += "    distance = _geospatial_service.calculate_distance(point1, point2, unit)\n"
        code += "    return DistanceResponse(distance=distance, unit=unit)\n\n\n"
        code += "@router.get(\"/geofences\")\n"
        code += "def list_geofences():\n"
        code += '    """Liệt kê tất cả geofences.\n\n'
        code += "    Returns:\n"
        code += "        Danh sách geofences\n"
        code += "    \"\"\"\n"
        code += "    return _geofence_service.list_geofences()\n\n\n"
        code += "@router.post(\"/geofences\", status_code=201)\n"
        code += "def create_geofence(request: GeofenceCreateRequest):\n"
        code += '    """Tạo geofence mới.\n\n'
        code += "    Args:\n"
        code += "        request: Dữ liệu geofence\n\n"
        code += "    Returns:\n"
        code += "        Geofence đã tạo\n"
        code += "    \"\"\"\n"
        code += "    try:\n"
        code += "        gf = _geofence_service.create_geofence(\n"
        code += "            name=request.name,\n"
        code += "            shape=request.shape,\n"
        code += "            center=request.center,\n"
        code += "            radius_m=request.radius_m,\n"
        code += "            points=request.points,\n"
        code += "            min_lat=request.min_lat,\n"
        code += "            min_lng=request.min_lng,\n"
        code += "            max_lat=request.max_lat,\n"
        code += "            max_lng=request.max_lng,\n"
        code += "            metadata=request.metadata,\n"
        code += "        )\n"
        code += "        return gf.to_dict()\n"
        code += "    except ValueError as e:\n"
        code += '        raise HTTPException(status_code=400, detail=str(e))\n\n\n'
        code += "@router.post(\"/geofences/{geofence_id}/check\", response_model=GeofenceCheckResponse)\n"
        code += "def check_geofence(geofence_id: str, request: GeofenceCheckRequest):\n"
        code += '    """Kiểm tra điểm có nằm trong geofence không.\n\n'
        code += "    Args:\n"
        code += "        geofence_id: ID của geofence\n"
        code += "        request: Tọa độ điểm cần kiểm tra\n\n"
        code += "    Returns:\n"
        code += "        Kết quả kiểm tra (is_inside, distance)\n"
        code += "    \"\"\"\n"
        code += "    try:\n"
        code += '        result = _geofence_service.check_geofence(geofence_id, {"latitude": request.latitude, "longitude": request.longitude})\n'
        code += "        return GeofenceCheckResponse(**result)\n"
        code += "    except ValueError as e:\n"
        code += '        raise HTTPException(status_code=404, detail=str(e))\n\n\n'
        code += "@router.post(\"/route\")\n"
        code += "def calculate_route(request: RouteRequest):\n"
        code += '    """Tính route giữa 2 điểm.\n\n'
        code += "    Args:\n"
        code += "        request: Dữ liệu route (origin, destination, profile)\n\n"
        code += "    Returns:\n"
        code += "        RouteResult với distance, duration, geometry, steps\n"
        code += "    \"\"\"\n"
        code += "    origin = {\"latitude\": request.origin_lat, \"longitude\": request.origin_lon}\n"
        code += "    destination = {\"latitude\": request.dest_lat, \"longitude\": request.dest_lon}\n"
        code += "    result = _routing_service.calculate_route(origin, destination, request.profile)\n"
        code += "    return result.to_dict()\n\n\n"
        code += "@router.get(\"/reverse-geocode\", response_model=ReverseGeocodeResponse)\n"
        code += "def reverse_geocode(\n"
        code += '    latitude: float = Query(..., ge=-90, le=90, description="Vĩ độ"),\n'
        code += '    longitude: float = Query(..., ge=-180, le=180, description="Kinh độ"),\n'
        code += "):\n"
        code += '    """Reverse geocoding — từ tọa độ sang địa chỉ.\n\n'
        code += "    Args:\n"
        code += "        latitude: Vĩ độ\n"
        code += "        longitude: Kinh độ\n\n"
        code += "    Returns:\n"
        code += "        Địa chỉ và tọa độ\n"
        code += "    \"\"\"\n"
        code += "    address = _geospatial_service.reverse_geocode(latitude, longitude)\n"
        code += "    return ReverseGeocodeResponse(\n"
        code += "        address=address,\n"
        code += "        latitude=latitude,\n"
        code += "        longitude=longitude,\n"
        code += "    )\n"

        return [{"path": "app/routes/geospatial.py", "content": code}]
