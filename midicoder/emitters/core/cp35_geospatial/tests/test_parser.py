# coding: utf-8
"""
Test cases cho CP35 Geospatial Parser.

Kiểm tra:
- GeospatialParser: Parse YAML DSL hợp lệ
- Error handling: Invalid YAML, invalid shape, non-dict input
- Edge cases: Empty input, whitespace, comment-only
- parse_from_metadata: Parse dict từ MIR
- Roundtrip: parse → to_dict → from_dict
"""

import pytest

from midicoder.emitters.core.cp35_geospatial.parser import GeospatialParser
from midicoder.emitters.core.cp35_geospatial.models import (
    GeofenceShape,
    GeospatialCollection,
    GeospatialSpec,
    GeoPoint,
)
from midicoder.errors import ErrorCode, MidicoderError


class TestGeospatialParser:
    """Test GeospatialParser."""

    def setup_method(self):
        """Setup parser cho mỗi test."""
        self.parser = GeospatialParser()

    def test_parse_empty_string_returns_empty_collection(self):
        """Kiểm tra parse string rỗng trả về collection rỗng."""
        result = self.parser.parse("")
        assert isinstance(result, GeospatialCollection)
        assert len(result.reports) == 0

    def test_parse_whitespace_only_returns_empty_collection(self):
        """Kiểm tra parse whitespace trả về collection rỗng."""
        result = self.parser.parse("   \n\n  ")
        assert isinstance(result, GeospatialCollection)
        assert len(result.reports) == 0

    def test_parse_comment_only_returns_empty_collection(self):
        """Kiểm tra parse comment-only YAML trả về collection rỗng."""
        result = self.parser.parse("# Chỉ là comment\n# Không có data")
        assert isinstance(result, GeospatialCollection)
        assert len(result.reports) == 0

    def test_parse_single_geospatial_spec(self):
        """Kiểm tra parse 1 geospatial spec."""
        dsl = """
geospatial_specs:
  - id: geofence_monitor
    name: Geofence Monitor
    entity: Device
"""
        result = self.parser.parse(dsl)
        assert len(result.reports) == 1
        spec = result.reports[0]
        assert spec.id == "geofence_monitor"
        assert spec.name == "Geofence Monitor"
        assert spec.entity == "Device"
        assert spec.geofences == []
        assert spec.routing_enabled is False
        assert spec.reverse_geocoding_enabled is False
        assert spec.notification_on_trigger is False

    def test_parse_multiple_geospatial_specs(self):
        """Kiểm tra parse nhiều geospatial specs."""
        dsl = """
geospatial_specs:
  - id: monitor_1
    name: Monitor 1
    entity: Device
  - id: monitor_2
    name: Monitor 2
    entity: Vehicle
  - id: monitor_3
    name: Monitor 3
    entity: Person
"""
        result = self.parser.parse(dsl)
        assert len(result.reports) == 3
        assert result.reports[0].id == "monitor_1"
        assert result.reports[1].id == "monitor_2"
        assert result.reports[2].id == "monitor_3"

    def test_parse_spec_with_circle_geofence(self):
        """Kiểm tra parse spec có circle geofence."""
        dsl = """
geospatial_specs:
  - id: delivery_tracker
    name: Delivery Tracker
    entity: Vehicle
    geofences:
      - id: delivery_zone
        name: Delivery Zone
        shape: circle
        center:
          latitude: 10.7750
          longitude: 106.7000
        radius_m: 5000
"""
        result = self.parser.parse(dsl)
        spec = result.reports[0]
        assert len(spec.geofences) == 1
        fence = spec.geofences[0]
        assert fence.id == "delivery_zone"
        assert fence.name == "Delivery Zone"
        assert fence.shape == GeofenceShape.CIRCLE
        assert fence.center.latitude == 10.7750
        assert fence.center.longitude == 106.7000
        assert fence.radius_m == 5000

    def test_parse_spec_with_polygon_geofence(self):
        """Kiểm tra parse spec có polygon geofence."""
        dsl = """
geospatial_specs:
  - id: factory_monitor
    name: Factory Monitor
    entity: Device
    geofences:
      - id: factory_perimeter
        name: Factory Perimeter
        shape: polygon
        points:
          - latitude: 10.7769
            longitude: 106.7009
          - latitude: 10.7779
            longitude: 106.7009
          - latitude: 10.7779
            longitude: 106.7019
"""
        result = self.parser.parse(dsl)
        spec = result.reports[0]
        assert len(spec.geofences) == 1
        fence = spec.geofences[0]
        assert fence.shape == GeofenceShape.POLYGON
        assert len(fence.points) == 3
        assert fence.points[0].latitude == 10.7769
        assert fence.points[1].longitude == 106.7009
        assert fence.points[2].longitude == 106.7019

    def test_parse_spec_with_rectangle_geofence(self):
        """Kiểm tra parse spec có rectangle geofence."""
        dsl = """
geospatial_specs:
  - id: area_monitor
    name: Area Monitor
    entity: Device
    geofences:
      - id: bounding_box
        name: Bounding Box
        shape: rectangle
        min_lat: 10.7700
        min_lng: 106.6900
        max_lat: 10.7800
        max_lng: 106.7100
"""
        result = self.parser.parse(dsl)
        spec = result.reports[0]
        fence = spec.geofences[0]
        assert fence.shape == GeofenceShape.RECTANGLE
        assert fence.min_lat == 10.7700
        assert fence.min_lng == 106.6900
        assert fence.max_lat == 10.7800
        assert fence.max_lng == 106.7100

    def test_parse_spec_with_routing_enabled(self):
        """Kiểm tra parse spec có routing, reverse_geocoding, notification."""
        dsl = """
geospatial_specs:
  - id: full_monitor
    name: Full Monitor
    entity: Vehicle
    routing_enabled: true
    reverse_geocoding_enabled: true
    notification_on_trigger: true
"""
        result = self.parser.parse(dsl)
        spec = result.reports[0]
        assert spec.routing_enabled is True
        assert spec.reverse_geocoding_enabled is True
        assert spec.notification_on_trigger is True

    def test_parse_spec_with_multiple_geofences(self):
        """Kiểm tra parse spec có nhiều geofences (circle + polygon)."""
        dsl = """
geospatial_specs:
  - id: mixed_monitor
    name: Mixed Monitor
    entity: Device
    geofences:
      - id: zone_a
        name: Zone A
        shape: circle
        center:
          latitude: 10.7750
          longitude: 106.7000
        radius_m: 1000
      - id: zone_b
        name: Zone B
        shape: polygon
        points:
          - latitude: 10.7769
            longitude: 106.7009
          - latitude: 10.7779
            longitude: 106.7009
          - latitude: 10.7779
            longitude: 106.7019
"""
        result = self.parser.parse(dsl)
        spec = result.reports[0]
        assert len(spec.geofences) == 2
        assert spec.geofences[0].shape == GeofenceShape.CIRCLE
        assert spec.geofences[1].shape == GeofenceShape.POLYGON

    def test_parse_invalid_shape_raises_error(self):
        """Kiểm tra báo lỗi khi shape geofence không hợp lệ."""
        dsl = """
geospatial_specs:
  - id: bad_shape
    name: Bad
    entity: Device
    geofences:
      - id: f1
        name: F1
        shape: invalid_shape
"""
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse(dsl)
        assert exc_info.value.code == ErrorCode.CP35_INVALID_GEOFENCE_SHAPE

    def test_parse_invalid_yaml_raises_error(self):
        """Kiểm tra báo lỗi khi YAML không hợp lệ."""
        dsl = "{{{{invalid yaml}}}"
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse(dsl)
        assert exc_info.value.code == ErrorCode.CP35_PARSER_ERROR

    def test_parse_non_dict_yaml_raises_error(self):
        """Kiểm tra báo lỗi khi YAML không phải mapping."""
        dsl = "- just a list\n- not a mapping"
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse(dsl)
        assert exc_info.value.code == ErrorCode.CP35_PARSER_ERROR

    def test_parse_defaults(self):
        """Kiểm tra defaults khi thiếu fields."""
        dsl = """
geospatial_specs:
  - id: minimal
    name: Minimal
    entity: Device
"""
        result = self.parser.parse(dsl)
        spec = result.reports[0]
        assert spec.geofences == []
        assert spec.routing_enabled is False
        assert spec.reverse_geocoding_enabled is False
        assert spec.notification_on_trigger is False
        assert spec.metadata == {}

    def test_parse_geofence_enabled_default(self):
        """Kiểm tra geofence enabled mặc định là True."""
        dsl = """
geospatial_specs:
  - id: spec1
    name: Spec1
    entity: Device
    geofences:
      - id: f1
        name: F1
        shape: circle
        center:
          latitude: 10.0
          longitude: 106.0
        radius_m: 100
"""
        result = self.parser.parse(dsl)
        fence = result.reports[0].geofences[0]
        assert fence.enabled is True
        assert fence.metadata == {}


class TestGeospatialParserFromMetadata:
    """Test parse_from_metadata."""

    def setup_method(self):
        self.parser = GeospatialParser()

    def test_parse_from_metadata_empty_dict(self):
        """Kiểm tra parse dict rỗng."""
        result = self.parser.parse_from_metadata({})
        assert isinstance(result, GeospatialCollection)
        assert len(result.reports) == 0

    def test_parse_from_metadata_with_specs(self):
        """Kiểm tra parse dict có geospatial specs."""
        data = {
            "geospatial_specs": [
                {
                    "id": "spec_1",
                    "name": "Spec 1",
                    "entity": "Device",
                    "routing_enabled": True,
                    "geofences": [
                        {
                            "id": "f1",
                            "name": "Zone 1",
                            "shape": "circle",
                            "center": {"latitude": 10.7750, "longitude": 106.7000},
                            "radius_m": 3000,
                        }
                    ],
                }
            ]
        }
        result = self.parser.parse_from_metadata(data)
        assert len(result.reports) == 1
        spec = result.reports[0]
        assert spec.id == "spec_1"
        assert spec.routing_enabled is True
        assert len(spec.geofences) == 1
        assert spec.geofences[0].radius_m == 3000

    def test_parse_from_metadata_non_dict_raises_error(self):
        """Kiểm tra parse non-dict báo lỗi."""
        with pytest.raises(MidicoderError):
            self.parser.parse_from_metadata("not a dict")

    def test_parse_from_metadata_multiple_specs(self):
        """Kiểm tra parse nhiều specs từ metadata."""
        data = {
            "geospatial_specs": [
                {"id": "a", "name": "A", "entity": "Device"},
                {"id": "b", "name": "B", "entity": "Vehicle"},
                {"id": "c", "name": "C", "entity": "Person"},
            ]
        }
        result = self.parser.parse_from_metadata(data)
        assert len(result.reports) == 3
        assert result.reports[0].id == "a"
        assert result.reports[2].id == "c"


class TestGeospatialParserRoundtrip:
    """Test roundtrip: parse → to_dict → from_dict."""

    def setup_method(self):
        self.parser = GeospatialParser()

    def test_roundtrip_single_spec_with_circle(self):
        """Kiểm tra roundtrip: parse YAML → to_dict → from_dict."""
        dsl = """
geospatial_specs:
  - id: rt_spec
    name: Roundtrip Spec
    entity: Vehicle
    routing_enabled: true
    reverse_geocoding_enabled: true
    notification_on_trigger: true
    geofences:
      - id: rt_fence
        name: Roundtrip Fence
        shape: circle
        center:
          latitude: 10.7750
          longitude: 106.7000
        radius_m: 5000
"""
        collection = self.parser.parse(dsl)
        assert len(collection.reports) == 1

        # to_dict
        data = collection.to_dict()
        assert "reports" in data
        assert len(data["reports"]) == 1

        # from_dict
        restored = GeospatialCollection.from_dict(data)
        assert len(restored.reports) == 1

        spec = restored.reports[0]
        assert spec.id == "rt_spec"
        assert spec.name == "Roundtrip Spec"
        assert spec.entity == "Vehicle"
        assert spec.routing_enabled is True
        assert spec.reverse_geocoding_enabled is True
        assert spec.notification_on_trigger is True
        assert len(spec.geofences) == 1
        assert spec.geofences[0].shape == GeofenceShape.CIRCLE
        assert spec.geofences[0].radius_m == 5000

    def test_roundtrip_polygon_geofence(self):
        """Kiểm tra roundtrip với polygon geofence."""
        dsl = """
geospatial_specs:
  - id: poly_rt
    name: Polygon RT
    entity: Device
    geofences:
      - id: poly_fence
        name: Polygon Fence
        shape: polygon
        points:
          - latitude: 10.7769
            longitude: 106.7009
          - latitude: 10.7779
            longitude: 106.7009
          - latitude: 10.7779
            longitude: 106.7019
"""
        collection = self.parser.parse(dsl)
        data = collection.to_dict()
        restored = GeospatialCollection.from_dict(data)

        fence = restored.reports[0].geofences[0]
        assert fence.shape == GeofenceShape.POLYGON
        assert len(fence.points) == 3
        assert fence.points[0].latitude == 10.7769

    def test_roundtrip_parse_from_metadata(self):
        """Kiểm tra roundtrip qua parse_from_metadata."""
        dsl = """
geospatial_specs:
  - id: meta_rt
    name: Meta RT
    entity: Device
    routing_enabled: true
    geofences:
      - id: f1
        name: F1
        shape: circle
        center:
          latitude: 10.0
          longitude: 106.0
        radius_m: 2000
"""
        collection = self.parser.parse(dsl)
        data = collection.to_dict()
        restored = self.parser.parse_from_metadata(data)

        assert len(restored.reports) == 1
        assert restored.reports[0].id == "meta_rt"
        assert restored.reports[0].routing_enabled is True

    def test_parse_from_metadata_non_list_specs_ignored(self):
        """Kiểm tra parse_from_metadata khi specs không phải list — cover line 100→105."""
        data = {
            "geospatial_specs": "not a list"
        }
        result = self.parser.parse_from_metadata(data)
        assert len(result.reports) == 0

    def test_parse_from_metadata_non_list_reports_ignored(self):
        """Kiểm tra parse_from_metadata khi reports không phải list."""
        data = {
            "reports": "also not a list"
        }
        result = self.parser.parse_from_metadata(data)
        assert len(result.reports) == 0

    def test_parse_from_metadata_uses_reports_fallback(self):
        """Kiểm tra parse_from_metadata fallback dùng key 'reports' — cover line 126→131."""
        data = {
            "reports": [
                {"id": "rb1", "name": "Report fallback", "entity": "Device"},
            ]
        }
        result = self.parser.parse_from_metadata(data)
        assert len(result.reports) == 1
        assert result.reports[0].id == "rb1"

    def test_parse_spec_with_rectangle_geofence(self):
        """Kiểm tra parse spec có rectangle geofence — cover line 215→221."""
        dsl = """
geospatial_specs:
  - id: rect_spec
    name: Rectangle Spec
    entity: Device
    geofences:
      - id: rect_f
        name: Rect Fence
        shape: rectangle
        min_lat: 21.0
        min_lng: 105.0
        max_lat: 21.2
        max_lng: 105.2
"""
        collection = self.parser.parse(dsl)
        assert len(collection.reports) == 1
        gf = collection.reports[0].geofences[0]
        assert gf.shape == GeofenceShape.RECTANGLE
        assert gf.min_lat == 21.0
        assert gf.max_lng == 105.2

    def test_parse_non_dict_spec_raises_error(self):
        """Kiểm tra parse non-dict spec báo lỗi — cover line 147."""
        with pytest.raises(MidicoderError):
            self.parser._parse_geospatial_spec("not a dict")

    def test_parse_non_dict_geofence_raises_error(self):
        """Kiểm tra parse non-dict geofence báo lỗi — cover line 185."""
        dsl = """
geospatial_specs:
  - id: bad_spec
    name: Bad
    entity: E
    geofences:
      - "not a dict"
"""
        with pytest.raises(MidicoderError):
            self.parser.parse(dsl)

    def test_parse_geofence_disabled(self):
        """Kiểm tra parse geofence có enabled=False — cover line 155→160."""
        dsl = """
geospatial_specs:
  - id: disabled_spec
    name: Disabled Spec
    entity: Device
    geofences:
      - id: f_disabled
        name: Disabled Fence
        shape: circle
        enabled: false
        center:
          latitude: 21.0
          longitude: 105.0
        radius_m: 1000
"""
        collection = self.parser.parse(dsl)
        gf = collection.reports[0].geofences[0]
        assert gf.enabled is False
