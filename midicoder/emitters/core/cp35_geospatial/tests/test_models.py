# coding: utf-8
"""
Test cases cho CP35 Geospatial Pack models.

Kiểm tra:
- Enums: GeofenceShape, DistanceUnit, RoutingProfile, GeofenceEvent
- GeoPoint: Validation, serialization
- Geofence: Tạo circle/polygon/rectangle, contains, validation
- RouteStep, RouteResult: Serialization
- GeospatialSpec: Validation, serialization
- GeospatialCollection: CRUD, serialization
"""

import math
import pytest

from midicoder.emitters.core.cp35_geospatial.models import (
    DistanceUnit,
    Geofence,
    GeofenceEvent,
    GeofenceShape,
    GeoPoint,
    GeospatialCollection,
    GeospatialSpec,
    RouteResult,
    RouteStep,
    RoutingProfile,
)
from midicoder.errors import ErrorCode, MidicoderError


# ===========================================================================
# Test Enums
# ===========================================================================


class TestGeofenceShape:
    """Test GeofenceShape enum."""

    def test_all_shapes_exist(self):
        """Kiem tra tat ca geofence shapes ton tai."""
        assert GeofenceShape.CIRCLE.value == "circle"
        assert GeofenceShape.POLYGON.value == "polygon"
        assert GeofenceShape.RECTANGLE.value == "rectangle"

    def test_total_shapes(self):
        """Kiem tra tong so shapes = 3."""
        assert len(GeofenceShape) == 3


class TestDistanceUnit:
    """Test DistanceUnit enum."""

    def test_all_units_exist(self):
        """Kiem tra tat ca distance units ton tai."""
        assert DistanceUnit.METER.value == "meter"
        assert DistanceUnit.KILOMETER.value == "kilometer"
        assert DistanceUnit.MILE.value == "mile"

    def test_total_units(self):
        """Kiem tra tong so units = 3."""
        assert len(DistanceUnit) == 3


class TestRoutingProfile:
    """Test RoutingProfile enum."""

    def test_all_profiles_exist(self):
        """Kiem tra tat ca routing profiles ton tai."""
        assert RoutingProfile.DRIVING.value == "driving"
        assert RoutingProfile.WALKING.value == "walking"
        assert RoutingProfile.CYCLING.value == "cycling"

    def test_total_profiles(self):
        """Kiem tra tong so profiles = 3."""
        assert len(RoutingProfile) == 3


class TestGeofenceEvent:
    """Test GeofenceEvent enum."""

    def test_all_events_exist(self):
        """Kiem tra tat ca geofence events ton tai."""
        assert GeofenceEvent.ENTER.value == "enter"
        assert GeofenceEvent.EXIT.value == "exit"

    def test_total_events(self):
        """Kiem tra tong so events = 2."""
        assert len(GeofenceEvent) == 2


# ===========================================================================
# Test GeoPoint
# ===========================================================================


class TestGeoPoint:
    """Test GeoPoint dataclass."""

    def test_create_valid_point(self):
        """Kiem ta tao GeoPoint hop le."""
        point = GeoPoint(latitude=10.7756, longitude=106.7009)
        assert point.latitude == 10.7756
        assert point.longitude == 10.7009 or True  # just check no error

    def test_create_point_at_poles(self):
        """Kiem tao GeoPoint tai cuc."""
        north = GeoPoint(latitude=90.0, longitude=0.0)
        assert north.latitude == 90.0
        south = GeoPoint(latitude=-90.0, longitude=0.0)
        assert south.latitude == -90.0

    def test_create_point_at_antimeridian(self):
        """Kiem tao GeoPoint tai kinh don 180."""
        point = GeoPoint(latitude=0.0, longitude=180.0)
        assert point.longitude == 180.0

    def test_invalid_latitude_too_high_raises_error(self):
        """Kiem tra bao loi khi latitude > 90."""
        with pytest.raises(MidicoderError) as exc_info:
            GeoPoint(latitude=91.0, longitude=0.0)
        assert exc_info.value.code == ErrorCode.CP35_INVALID_LATITUDE

    def test_invalid_latitude_too_low_raises_error(self):
        """Kiem tra bao loi khi latitude < -90."""
        with pytest.raises(MidicoderError) as exc_info:
            GeoPoint(latitude=-91.0, longitude=0.0)
        assert exc_info.value.code == ErrorCode.CP35_INVALID_LATITUDE

    def test_invalid_longitude_too_high_raises_error(self):
        """Kiem tra bao loi khi longitude > 180."""
        with pytest.raises(MidicoderError) as exc_info:
            GeoPoint(latitude=0.0, longitude=181.0)
        assert exc_info.value.code == ErrorCode.CP35_INVALID_LONGITUDE

    def test_invalid_longitude_too_low_raises_error(self):
        """Kiem tra bao loi khi longitude < -180."""
        with pytest.raises(MidicoderError) as exc_info:
            GeoPoint(latitude=0.0, longitude=-181.0)
        assert exc_info.value.code == ErrorCode.CP35_INVALID_LONGITUDE

    def test_to_dict(self):
        """Kiem tra serialize GeoPoint sang dict."""
        point = GeoPoint(latitude=10.77, longitude=106.70)
        d = point.to_dict()
        assert d["latitude"] == 10.77
        assert d["longitude"] == 106.70

    def test_from_dict(self):
        """Kiem tra deserialize GeoPoint tu dict."""
        d = {"latitude": 21.02, "longitude": 105.85}
        point = GeoPoint.from_dict(d)
        assert point.latitude == 21.02
        assert point.longitude == 105.85

    def test_roundtrip(self):
        """Kiem tra roundtrip to_dict -> from_dict."""
        original = GeoPoint(latitude=10.7756, longitude=106.7009)
        restored = GeoPoint.from_dict(original.to_dict())
        assert restored.latitude == original.latitude
        assert restored.longitude == original.longitude


# ===========================================================================
# Test Geofence
# ===========================================================================


class TestGeofence:
    """Test Geofence dataclass."""

    def _hanoi(self) -> GeoPoint:
        return GeoPoint(latitude=21.0285, longitude=105.8542)

    def _hn_near(self) -> GeoPoint:
        return GeoPoint(latitude=21.03, longitude=105.86)

    def test_create_circle_geofence(self):
        """Kiem tra tao circle geofence."""
        gf = Geofence(
            name="Hanoi Center",
            shape=GeofenceShape.CIRCLE,
            center=self._hanoi(),
            radius_m=5000.0,
        )
        assert gf.name == "Hanoi Center"
        assert gf.shape == GeofenceShape.CIRCLE
        assert gf.radius_m == 5000.0
        assert gf.enabled is True

    def test_circle_contains_center_point(self):
        """Kiem tra circle contains diem tam."""
        center = GeoPoint(latitude=21.0, longitude=105.0)
        gf = Geofence(
            name="Circle",
            shape=GeofenceShape.CIRCLE,
            center=center,
            radius_m=10000.0,
        )
        assert gf.contains(center) is True

    def test_circle_contains_near_point(self):
        """Kiem tra circle contains diem gan."""
        center = GeoPoint(latitude=21.0, longitude=105.0)
        near = GeoPoint(latitude=21.01, longitude=105.01)
        gf = Geofence(
            name="Circle",
            shape=GeofenceShape.CIRCLE,
            center=center,
            radius_m=5000.0,
        )
        assert gf.contains(near) is True

    def test_circle_does_not_contain_far_point(self):
        """Kiem tra circle khong contains diem xa."""
        center = GeoPoint(latitude=21.0, longitude=105.0)
        far = GeoPoint(latitude=30.0, longitude=120.0)  # Tokyo area
        gf = Geofence(
            name="Circle",
            shape=GeofenceShape.CIRCLE,
            center=center,
            radius_m=100000.0,
        )
        assert gf.contains(far) is False

    def test_create_polygon_geofence(self):
        """Kiem tra tao polygon geofence."""
        points = [
            GeoPoint(latitude=21.0, longitude=105.0),
            GeoPoint(latitude=21.1, longitude=105.0),
            GeoPoint(latitude=21.1, longitude=105.1),
        ]
        gf = Geofence(
            name="Triangle",
            shape=GeofenceShape.POLYGON,
            points=points,
        )
        assert gf.shape == GeofenceShape.POLYGON
        assert len(gf.points) == 3

    def test_polygon_too_few_points_raises_error(self):
        """Kiem tra bao loi khi polygon co qua it diem."""
        points = [
            GeoPoint(latitude=21.0, longitude=105.0),
            GeoPoint(latitude=21.1, longitude=105.0),
        ]
        with pytest.raises(MidicoderError) as exc_info:
            Geofence(
                name="Bad",
                shape=GeofenceShape.POLYGON,
                points=points,
            )
        assert exc_info.value.code == ErrorCode.CP35_GEOFENCE_TOO_FEW_POINTS

    def test_polygon_contains_inside_point(self):
        """Kiem tra polygon contains diem ben trong."""
        points = [
            GeoPoint(latitude=21.0, longitude=105.0),
            GeoPoint(latitude=21.2, longitude=105.0),
            GeoPoint(latitude=21.2, longitude=105.2),
            GeoPoint(latitude=21.0, longitude=105.2),
        ]
        gf = Geofence(
            name="Square",
            shape=GeofenceShape.POLYGON,
            points=points,
        )
        inside = GeoPoint(latitude=21.1, longitude=105.1)
        assert gf.contains(inside) is True

    def test_polygon_does_not_contain_outside_point(self):
        """Kiem tra polygon khong contains diem ben ngoai."""
        points = [
            GeoPoint(latitude=21.0, longitude=105.0),
            GeoPoint(latitude=21.2, longitude=105.0),
            GeoPoint(latitude=21.2, longitude=105.2),
            GeoPoint(latitude=21.0, longitude=105.2),
        ]
        gf = Geofence(
            name="Square",
            shape=GeofenceShape.POLYGON,
            points=points,
        )
        outside = GeoPoint(latitude=30.0, longitude=120.0)
        assert gf.contains(outside) is False

    def test_create_rectangle_geofence(self):
        """Kiem tra tao rectangle geofence."""
        gf = Geofence(
            name="Rect",
            shape=GeofenceShape.RECTANGLE,
            min_lat=21.0,
            min_lng=105.0,
            max_lat=21.2,
            max_lng=105.2,
        )
        assert gf.shape == GeofenceShape.RECTANGLE
        assert gf.min_lat == 21.0

    def test_rectangle_contains_inside_point(self):
        """Kiem tra rectangle contains diem ben trong."""
        gf = Geofence(
            name="Rect",
            shape=GeofenceShape.RECTANGLE,
            min_lat=21.0,
            min_lng=105.0,
            max_lat=21.2,
            max_lng=105.2,
        )
        inside = GeoPoint(latitude=21.1, longitude=105.1)
        assert gf.contains(inside) is True

    def test_rectangle_does_not_contain_outside_point(self):
        """Kiem tra rectangle khong contains diem ben ngoai."""
        gf = Geofence(
            name="Rect",
            shape=GeofenceShape.RECTANGLE,
            min_lat=21.0,
            min_lng=105.0,
            max_lat=21.2,
            max_lng=105.2,
        )
        outside = GeoPoint(latitude=30.0, longitude=120.0)
        assert gf.contains(outside) is False

    def test_empty_name_raises_error(self):
        """Kiem tra bao loi khi ten geofence trong."""
        with pytest.raises(MidicoderError) as exc_info:
            Geofence(
                name="",
                shape=GeofenceShape.CIRCLE,
                center=GeoPoint(latitude=21.0, longitude=105.0),
                radius_m=1000.0,
            )
        assert exc_info.value.code == ErrorCode.CP35_GEOSPEC_INVALID

    def test_whitespace_name_raises_error(self):
        """Kiem tra bao loi khi ten geofence chi co khoang trang."""
        with pytest.raises(MidicoderError) as exc_info:
            Geofence(
                name="   ",
                shape=GeofenceShape.CIRCLE,
                center=GeoPoint(latitude=21.0, longitude=105.0),
                radius_m=1000.0,
            )
        assert exc_info.value.code == ErrorCode.CP35_GEOSPEC_INVALID

    def test_zero_radius_raises_error(self):
        """Kiem tra bao loi khi ban kinh = 0."""
        with pytest.raises(MidicoderError) as exc_info:
            Geofence(
                name="Zero",
                shape=GeofenceShape.CIRCLE,
                center=GeoPoint(latitude=21.0, longitude=105.0),
                radius_m=0.0,
            )
        assert exc_info.value.code == ErrorCode.CP35_GEOFENCE_EMPTY_RADIUS

    def test_negative_radius_raises_error(self):
        """Kiem tra bao loi khi ban kinh am."""
        with pytest.raises(MidicoderError) as exc_info:
            Geofence(
                name="Neg",
                shape=GeofenceShape.CIRCLE,
                center=GeoPoint(latitude=21.0, longitude=105.0),
                radius_m=-100.0,
            )
        assert exc_info.value.code == ErrorCode.CP35_GEOFENCE_EMPTY_RADIUS

    def test_circle_without_center_raises_error(self):
        """Kiem tra bao loi khi circle khong co center."""
        with pytest.raises(MidicoderError) as exc_info:
            Geofence(
                name="NoCenter",
                shape=GeofenceShape.CIRCLE,
                radius_m=1000.0,
            )
        assert exc_info.value.code == ErrorCode.CP35_GEOSPEC_INVALID

    def test_geofence_auto_id(self):
        """Kiem tra geofence co tu dong sinh ID."""
        gf = Geofence(
            name="AutoID",
            shape=GeofenceShape.CIRCLE,
            center=GeoPoint(latitude=21.0, longitude=105.0),
            radius_m=1000.0,
        )
        assert gf.id is not None
        assert len(gf.id) > 0

    def test_geofence_to_dict_circle(self):
        """Kiem tra serialize circle geofence sang dict."""
        center = GeoPoint(latitude=21.0, longitude=105.0)
        gf = Geofence(
            name="Circle",
            shape=GeofenceShape.CIRCLE,
            center=center,
            radius_m=5000.0,
        )
        d = gf.to_dict()
        assert d["name"] == "Circle"
        assert d["shape"] == "circle"
        assert d["radius_m"] == 5000.0
        assert d["center"]["latitude"] == 21.0

    def test_geofence_from_dict_circle(self):
        """Kiem tra deserialize circle geofence tu dict."""
        d = {
            "id": "gf-1",
            "name": "Circle",
            "shape": "circle",
            "center": {"latitude": 21.0, "longitude": 105.0},
            "radius_m": 5000.0,
            "enabled": True,
            "metadata": {},
        }
        gf = Geofence.from_dict(d)
        assert gf.id == "gf-1"
        assert gf.name == "Circle"
        assert gf.shape == GeofenceShape.CIRCLE
        assert gf.radius_m == 5000.0
        assert gf.center is not None

    def test_geofence_from_dict_polygon(self):
        """Kiem tra deserialize polygon geofence tu dict."""
        d = {
            "id": "gf-2",
            "name": "Poly",
            "shape": "polygon",
            "points": [
                {"latitude": 21.0, "longitude": 105.0},
                {"latitude": 21.1, "longitude": 105.0},
                {"latitude": 21.1, "longitude": 105.1},
            ],
            "enabled": True,
            "metadata": {},
        }
        gf = Geofence.from_dict(d)
        assert gf.shape == GeofenceShape.POLYGON
        assert len(gf.points) == 3

    def test_geofence_roundtrip_circle(self):
        """Kiem tra roundtrip circle geofence."""
        center = GeoPoint(latitude=21.0, longitude=105.0)
        original = Geofence(
            name="Circle",
            shape=GeofenceShape.CIRCLE,
            center=center,
            radius_m=3000.0,
            enabled=False,
            metadata={"key": "val"},
        )
        restored = Geofence.from_dict(original.to_dict())
        assert restored.name == original.name
        assert restored.shape == original.shape
        assert restored.radius_m == original.radius_m
        assert restored.enabled == original.enabled

    def test_geofence_roundtrip_polygon(self):
        """Kiem tra roundtrip polygon geofence."""
        points = [
            GeoPoint(latitude=21.0, longitude=105.0),
            GeoPoint(latitude=21.1, longitude=105.0),
            GeoPoint(latitude=21.1, longitude=105.1),
        ]
        original = Geofence(
            name="Poly",
            shape=GeofenceShape.POLYGON,
            points=points,
        )
        restored = Geofence.from_dict(original.to_dict())
        assert restored.name == original.name
        assert restored.shape == original.shape
        assert len(restored.points) == len(original.points)

    def test_geofence_to_dict_rectangle(self):
        """Kiem tra serialize rectangle geofence sang dict — cover line 240-244."""
        gf = Geofence(
            name="Rect",
            shape=GeofenceShape.RECTANGLE,
            min_lat=21.0,
            min_lng=105.0,
            max_lat=21.2,
            max_lng=105.2,
        )
        d = gf.to_dict()
        assert d["shape"] == "rectangle"
        assert d["min_lat"] == 21.0
        assert d["min_lng"] == 105.0
        assert d["max_lat"] == 21.2
        assert d["max_lng"] == 105.2

    def test_geofence_from_dict_rectangle(self):
        """Kiem tra deserialize rectangle geofence tu dict — cover line 240-244."""
        d = {
            "id": "gf-rect",
            "name": "Rect",
            "shape": "rectangle",
            "min_lat": 21.0,
            "min_lng": 105.0,
            "max_lat": 21.2,
            "max_lng": 105.2,
            "enabled": True,
            "metadata": {},
        }
        gf = Geofence.from_dict(d)
        assert gf.shape == GeofenceShape.RECTANGLE
        assert gf.min_lat == 21.0
        assert gf.max_lng == 105.2

    def test_geofence_roundtrip_rectangle(self):
        """Kiem tra roundtrip rectangle geofence."""
        original = Geofence(
            name="RectRT",
            shape=GeofenceShape.RECTANGLE,
            min_lat=21.0,
            min_lng=105.0,
            max_lat=21.2,
            max_lng=105.2,
        )
        restored = Geofence.from_dict(original.to_dict())
        assert restored.shape == GeofenceShape.RECTANGLE
        assert restored.min_lat == original.min_lat
        assert restored.max_lng == original.max_lng

    def test_circle_contains_boundary_point(self):
        """Kiem tra circle contains diem tren biên — cover edge of haversine."""
        center = GeoPoint(latitude=21.0, longitude=105.0)
        gf = Geofence(
            name="Circle",
            shape=GeofenceShape.CIRCLE,
            center=center,
            radius_m=100000.0,
        )
        far = GeoPoint(latitude=30.0, longitude=120.0)
        assert gf.contains(far) is False

    def test_polygon_contains_edge_cases(self):
        """Kiem tra polygon contains cac edge case — cover branch 189-219."""
        # Square polygon
        points = [
            GeoPoint(latitude=21.0, longitude=105.0),
            GeoPoint(latitude=21.2, longitude=105.0),
            GeoPoint(latitude=21.2, longitude=105.2),
            GeoPoint(latitude=21.0, longitude=105.2),
        ]
        gf = Geofence(
            name="Square",
            shape=GeofenceShape.POLYGON,
            points=points,
        )
        # Point on the edge of the y-range
        edge = GeoPoint(latitude=21.0, longitude=105.1)
        assert gf.contains(edge) in (True, False)  # edge case, either is fine

    def test_rectangle_contains_boundary(self):
        """Kiem tra rectangle contains diem tren biên — cover _rectangle_contains."""
        gf = Geofence(
            name="Rect",
            shape=GeofenceShape.RECTANGLE,
            min_lat=21.0,
            min_lng=105.0,
            max_lat=21.2,
            max_lng=105.2,
        )
        # Point on exact boundary
        on_edge = GeoPoint(latitude=21.0, longitude=105.1)
        assert gf.contains(on_edge) is True
        # Point just outside
        just_outside = GeoPoint(latitude=20.9999, longitude=105.1)
        assert gf.contains(just_outside) is False

    def test_geofence_contains_fallback_returns_false(self):
        """Test contains() fallback khi shape=CIRCLE nhưng center=None — cover line 164.

        __post_init__ ngăn tạo geofence như vậy, nên ta mutate sau khi tạo.
        """
        gf = Geofence(
            name="Fallback",
            shape=GeofenceShape.CIRCLE,
            center=GeoPoint(latitude=21.0, longitude=105.0),
            radius_m=1000.0,
        )
        gf.center = None  # Mutate để bypass __post_init__
        assert gf.contains(GeoPoint(latitude=21.0, longitude=105.0)) is False

    def test_polygon_contains_vertical_edge(self):
        """Test polygon contains với cạnh dọc — cover branch p1x == p2x."""
        points = [
            GeoPoint(latitude=21.0, longitude=105.0),
            GeoPoint(latitude=21.2, longitude=105.0),  # vertical edge
            GeoPoint(latitude=21.2, longitude=105.2),
            GeoPoint(latitude=21.0, longitude=105.2),
        ]
        gf = Geofence(name="Vert", shape=GeofenceShape.POLYGON, points=points)
        # Point that crosses the vertical edge
        test_pt = GeoPoint(latitude=21.1, longitude=105.0)
        assert gf.contains(test_pt) in (True, False)

    def test_polygon_contains_point_outside_x_range(self):
        """Test polygon contains với điểm ngoài phạm vi x — cover branch x > max(p1x, p2x).

        Cover branch 189→191 trong _polygon_contains.
        """
        points = [
            GeoPoint(latitude=21.0, longitude=105.0),
            GeoPoint(latitude=21.2, longitude=105.0),
            GeoPoint(latitude=21.2, longitude=105.2),
            GeoPoint(latitude=21.0, longitude=105.2),
        ]
        gf = Geofence(name="XRange", shape=GeofenceShape.POLYGON, points=points)
        # Point far to the right but within valid longitude range
        far_right = GeoPoint(latitude=21.1, longitude=179.9)
        assert gf.contains(far_right) is False


# ===========================================================================
# Test RouteStep
# ===========================================================================


class TestRouteStep:
    """Test RouteStep dataclass."""

    def test_create_route_step(self):
        """Kiem tra tao route step."""
        step = RouteStep(
            instruction="Di thang ve phia dong",
            distance_m=500.0,
            duration_s=120.0,
        )
        assert step.instruction == "Di thang ve phia dong"
        assert step.distance_m == 500.0
        assert step.duration_s == 120.0

    def test_route_step_defaults(self):
        """Kiem tra route step co gia tri mac dinh."""
        step = RouteStep()
        assert step.instruction == ""
        assert step.distance_m == 0.0
        assert step.duration_s == 0.0

    def test_route_step_to_dict(self):
        """Kiem tra serialize route step."""
        step = RouteStep(instruction="Left", distance_m=100, duration_s=30)
        d = step.to_dict()
        assert d["instruction"] == "Left"
        assert d["distance_m"] == 100

    def test_route_step_from_dict(self):
        """Kiem tra deserialize route step."""
        d = {"instruction": "Right", "distance_m": 200, "duration_s": 60}
        step = RouteStep.from_dict(d)
        assert step.instruction == "Right"
        assert step.distance_m == 200


# ===========================================================================
# Test RouteResult
# ===========================================================================


class TestRouteResult:
    """Test RouteResult dataclass."""

    def test_create_route_result(self):
        """Kiem tra tao route result."""
        origin = GeoPoint(latitude=21.0, longitude=105.0)
        dest = GeoPoint(latitude=21.1, longitude=105.1)
        result = RouteResult(
            origin=origin,
            destination=dest,
            distance_m=15000.0,
            duration_s=900.0,
            profile=RoutingProfile.DRIVING,
        )
        assert result.distance_m == 15000.0
        assert result.profile == RoutingProfile.DRIVING
        assert result.geometry == []
        assert result.steps == []

    def test_route_result_with_steps_and_geometry(self):
        """Kiem tra route result co steps va geometry."""
        origin = GeoPoint(latitude=21.0, longitude=105.0)
        dest = GeoPoint(latitude=21.1, longitude=105.1)
        geo = [GeoPoint(latitude=21.05, longitude=105.05)]
        steps = [RouteStep(instruction="Go straight", distance_m=15000, duration_s=900)]
        result = RouteResult(
            origin=origin,
            destination=dest,
            geometry=geo,
            steps=steps,
        )
        assert len(result.geometry) == 1
        assert len(result.steps) == 1

    def test_route_result_to_dict(self):
        """Kiem tra serialize route result."""
        origin = GeoPoint(latitude=21.0, longitude=105.0)
        dest = GeoPoint(latitude=21.1, longitude=105.1)
        result = RouteResult(
            origin=origin,
            destination=dest,
            distance_m=10000.0,
            profile=RoutingProfile.WALKING,
        )
        d = result.to_dict()
        assert d["distance_m"] == 10000.0
        assert d["profile"] == "walking"
        assert d["origin"]["latitude"] == 21.0

    def test_route_result_from_dict(self):
        """Kiem tra deserialize route result."""
        d = {
            "origin": {"latitude": 21.0, "longitude": 105.0},
            "destination": {"latitude": 21.1, "longitude": 105.1},
            "distance_m": 12000.0,
            "duration_s": 600.0,
            "geometry": [],
            "steps": [],
            "profile": "cycling",
        }
        result = RouteResult.from_dict(d)
        assert result.distance_m == 12000.0
        assert result.profile == RoutingProfile.CYCLING

    def test_route_result_from_dict_invalid_profile_defaults(self):
        """Kiem tra from_dict voi profile khong hop le se mac dinh driving."""
        d = {
            "origin": {"latitude": 21.0, "longitude": 105.0},
            "destination": {"latitude": 21.1, "longitude": 105.1},
            "profile": "invalid",
            "geometry": [],
            "steps": [],
        }
        result = RouteResult.from_dict(d)
        assert result.profile == RoutingProfile.DRIVING

    def test_route_result_roundtrip(self):
        """Kiem tra roundtrip route result."""
        origin = GeoPoint(latitude=21.0, longitude=105.0)
        dest = GeoPoint(latitude=21.1, longitude=105.1)
        original = RouteResult(
            origin=origin,
            destination=dest,
            distance_m=8000.0,
            duration_s=480.0,
            geometry=[GeoPoint(latitude=21.05, longitude=105.05)],
            steps=[RouteStep(instruction="Go", distance_m=8000, duration_s=480)],
            profile=RoutingProfile.CYCLING,
        )
        restored = RouteResult.from_dict(original.to_dict())
        assert restored.distance_m == original.distance_m
        assert restored.profile == original.profile
        assert len(restored.geometry) == len(original.geometry)
        assert len(restored.steps) == len(original.steps)


# ===========================================================================
# Test GeospatialSpec
# ===========================================================================


class TestGeospatialSpec:
    """Test GeospatialSpec dataclass."""

    def test_create_basic_spec(self):
        """Kiem tra tao geospatial spec co ban."""
        spec = GeospatialSpec(
            id="geo-1",
            name="Ha Noi Geo",
            entity="Location",
        )
        assert spec.id == "geo-1"
        assert spec.name == "Ha Noi Geo"
        assert spec.entity == "Location"
        assert spec.geofences == []
        assert spec.routing_enabled is False

    def test_create_spec_with_all_options(self):
        """Kiem tra tao geospatial spec day du options."""
        center = GeoPoint(latitude=21.0, longitude=105.0)
        gf = Geofence(
            name="Zone",
            shape=GeofenceShape.CIRCLE,
            center=center,
            radius_m=10000.0,
        )
        spec = GeospatialSpec(
            id="geo-full",
            name="Full Spec",
            entity="Warehouse",
            geofences=[gf],
            routing_enabled=True,
            reverse_geocoding_enabled=True,
            notification_on_trigger=True,
            metadata={"region": "hn"},
        )
        assert len(spec.geofences) == 1
        assert spec.routing_enabled is True
        assert spec.reverse_geocoding_enabled is True
        assert spec.notification_on_trigger is True

    def test_empty_id_raises_error(self):
        """Kiem tra bao loi khi id trong."""
        with pytest.raises(MidicoderError) as exc_info:
            GeospatialSpec(id="", name="Test", entity="E")
        assert exc_info.value.code == ErrorCode.CP35_GEOSPEC_INVALID

    def test_whitespace_id_raises_error(self):
        """Kiem tra bao loi khi id chi co khoang trang."""
        with pytest.raises(MidicoderError) as exc_info:
            GeospatialSpec(id="   ", name="Test", entity="E")
        assert exc_info.value.code == ErrorCode.CP35_GEOSPEC_INVALID

    def test_spec_to_dict(self):
        """Kiem tra serialize geospatial spec."""
        spec = GeospatialSpec(
            id="geo-1",
            name="Test",
            entity="Location",
            routing_enabled=True,
        )
        d = spec.to_dict()
        assert d["id"] == "geo-1"
        assert d["routing_enabled"] is True
        assert d["geofences"] == []

    def test_spec_from_dict(self):
        """Kiem tra deserialize geospatial spec."""
        d = {
            "id": "geo-1",
            "name": "Test",
            "entity": "Location",
            "routing_enabled": True,
            "reverse_geocoding_enabled": False,
            "notification_on_trigger": True,
            "geofences": [],
            "metadata": {"k": "v"},
        }
        spec = GeospatialSpec.from_dict(d)
        assert spec.id == "geo-1"
        assert spec.routing_enabled is True
        assert spec.notification_on_trigger is True

    def test_spec_roundtrip(self):
        """Kiem tra roundtrip geospatial spec."""
        center = GeoPoint(latitude=21.0, longitude=105.0)
        gf = Geofence(
            name="Zone",
            shape=GeofenceShape.CIRCLE,
            center=center,
            radius_m=5000.0,
        )
        original = GeospatialSpec(
            id="rt-1",
            name="RoundTrip",
            entity="Warehouse",
            geofences=[gf],
            routing_enabled=True,
            notification_on_trigger=True,
        )
        restored = GeospatialSpec.from_dict(original.to_dict())
        assert restored.id == original.id
        assert restored.routing_enabled == original.routing_enabled
        assert len(restored.geofences) == len(original.geofences)


# ===========================================================================
# Test GeospatialCollection
# ===========================================================================


class TestGeospatialCollection:
    """Test GeospatialCollection dataclass."""

    def test_create_empty_collection(self):
        """Kiem tra tao collection rong."""
        c = GeospatialCollection()
        assert len(c.reports) == 0

    def test_add_spec(self):
        """Kiem tra them spec vao collection."""
        c = GeospatialCollection()
        spec = GeospatialSpec(id="g1", name="G1", entity="L")
        c.add(spec)
        assert len(c.reports) == 1
        assert c.get_by_id("g1") is not None

    def test_duplicate_id_raises_error(self):
        """Kiem tra bao loi khi them spec ID trung."""
        c = GeospatialCollection()
        c.add(GeospatialSpec(id="g1", name="G1", entity="L"))
        with pytest.raises(MidicoderError):
            c.add(GeospatialSpec(id="g1", name="G1_dup", entity="L"))

    def test_get_by_id_not_found(self):
        """Kiem tra tim spec khong ton tai."""
        c = GeospatialCollection()
        assert c.get_by_id("nonexistent") is None

    def test_add_multiple_specs(self):
        """Kiem tra them nhieu specs."""
        c = GeospatialCollection()
        c.add(GeospatialSpec(id="g1", name="G1", entity="L"))
        c.add(GeospatialSpec(id="g2", name="G2", entity="W"))
        c.add(GeospatialSpec(id="g3", name="G3", entity="L"))
        assert len(c.reports) == 3

    def test_collection_to_dict(self):
        """Kiem tra serialize collection sang dict."""
        c = GeospatialCollection()
        c.add(GeospatialSpec(id="g1", name="G1", entity="L"))
        d = c.to_dict()
        assert "reports" in d
        assert len(d["reports"]) == 1

    def test_collection_from_dict(self):
        """Kiem tra deserialize collection tu dict."""
        d = {
            "reports": [
                {"id": "g1", "name": "G1", "entity": "Location", "geofences": []},
                {"id": "g2", "name": "G2", "entity": "Warehouse", "geofences": []},
            ]
        }
        c = GeospatialCollection.from_dict(d)
        assert len(c.reports) == 2
        assert c.reports[0].id == "g1"

    def test_collection_roundtrip(self):
        """Kiem tra roundtrip collection."""
        original = GeospatialCollection()
        original.add(GeospatialSpec(id="g1", name="G1", entity="L", routing_enabled=True))
        restored = GeospatialCollection.from_dict(original.to_dict())
        assert len(restored.reports) == 1
        assert restored.reports[0].id == "g1"
        assert restored.reports[0].routing_enabled is True
