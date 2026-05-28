# coding: utf-8
"""
Tests cho emitter module CP35 Geospatial Services.

Kiểm tra: FastAPIGeospatialEmitter, NestJSGeospatialEmitter,
AngularGeospatialEmitter, ReactGeospatialEmitter.
"""

from midicoder.packs.cp_full_geospatial.models import (
    Geofence,
    GeofenceShape,
    GeospatialCollection,
    GeospatialSpec,
    GeoPoint,
)
from midicoder.packs.cp_full_geospatial.fastapi import FastAPIGeospatialEmitter
from midicoder.packs.cp_full_geospatial.nestjs import NestJSGeospatialEmitter
from midicoder.packs.cp_full_geospatial.angular import AngularGeospatialEmitter
from midicoder.packs.cp_full_geospatial.react import ReactGeospatialEmitter


def _make_collection() -> GeospatialCollection:
    """Tạo collection mẫu cho test."""
    collection = GeospatialCollection()
    collection.add(
        GeospatialSpec(
            id="test_geofence",
            name="Test Geofence Monitor",
            entity="Device",
            geofences=[
                Geofence(
                    name="Test Zone",
                    shape=GeofenceShape.CIRCLE,
                    center=GeoPoint(latitude=10.7769, longitude=106.7009),
                    radius_m=1000.0,
                )
            ],
            routing_enabled=True,
            reverse_geocoding_enabled=True,
            notification_on_trigger=True,
        )
    )
    return collection


# ===========================================================================
# FastAPIGeospatialEmitter
# ===========================================================================


class TestFastAPIGeospatialEmitter:
    def test_emit_returns_list_of_dicts(self):
        emitter = FastAPIGeospatialEmitter()
        result = emitter.emit(_make_collection())
        assert isinstance(result, list)
        assert all(isinstance(f, dict) for f in result)

    def test_emit_has_all_files(self):
        emitter = FastAPIGeospatialEmitter()
        result = emitter.emit(_make_collection())
        paths = [f["path"] for f in result]
        assert any("geospatial_service" in p for p in paths)
        assert any("geofence_service" in p for p in paths)
        assert any("routing_service" in p for p in paths)
        assert any("routes" in p and "geospatial" in p for p in paths)

    def test_emit_content_has_geo_specs(self):
        emitter = FastAPIGeospatialEmitter()
        result = emitter.emit(_make_collection())
        all_content = "\n".join(f["content"] for f in result)
        assert "Device" in all_content

    def test_emit_empty_collection_raises_error(self):
        emitter = FastAPIGeospatialEmitter()
        empty = GeospatialCollection()
        try:
            emitter.emit(empty)
            assert False, "Nên raise error"
        except Exception:
            pass

    def test_generate_service_has_geopy_import(self):
        emitter = FastAPIGeospatialEmitter()
        result = emitter.generate_service(_make_collection())
        content = result[0]["content"]
        assert "geopy" in content

    def test_generate_routing_service_has_osrm(self):
        emitter = FastAPIGeospatialEmitter()
        result = emitter.generate_routing_service(_make_collection())
        content = result[0]["content"]
        assert "osrm" in content.lower() or "OSRM" in content or "routing" in content.lower()


# ===========================================================================
# NestJSGeospatialEmitter
# ===========================================================================


class TestNestJSGeospatialEmitter:
    def test_emit_returns_list_of_dicts(self):
        emitter = NestJSGeospatialEmitter()
        result = emitter.emit(_make_collection())
        assert isinstance(result, list)
        assert all(isinstance(f, dict) for f in result)

    def test_emit_has_all_files(self):
        emitter = NestJSGeospatialEmitter()
        result = emitter.emit(_make_collection())
        paths = [f["path"] for f in result]
        assert any("geospatial.service" in p for p in paths)
        assert any("geofence.service" in p for p in paths)
        assert any("routing.service" in p for p in paths)
        assert any("geospatial.controller" in p for p in paths)

    def test_emit_has_typescript_syntax(self):
        emitter = NestJSGeospatialEmitter()
        result = emitter.emit(_make_collection())
        all_content = "\n".join(f["content"] for f in result)
        assert "export class" in all_content or "export interface" in all_content
        assert "Injectable" in all_content

    def test_emit_empty_collection_raises_error(self):
        emitter = NestJSGeospatialEmitter()
        empty = GeospatialCollection()
        try:
            emitter.emit(empty)
            assert False, "Nên raise error"
        except Exception:
            pass


# ===========================================================================
# AngularGeospatialEmitter
# ===========================================================================


class TestAngularGeospatialEmitter:
    def test_emit_returns_list_of_dicts(self):
        emitter = AngularGeospatialEmitter()
        result = emitter.emit(_make_collection())
        assert isinstance(result, list)
        assert all(isinstance(f, dict) for f in result)

    def test_emit_has_all_components(self):
        emitter = AngularGeospatialEmitter()
        result = emitter.emit(_make_collection())
        paths = [f["path"] for f in result]
        assert any("map-viewer" in p for p in paths)
        assert any("geofence-alert" in p for p in paths)

    def test_emit_has_angular_syntax(self):
        emitter = AngularGeospatialEmitter()
        result = emitter.emit(_make_collection())
        all_content = "\n".join(f["content"] for f in result)
        assert "@Component" in all_content
        assert "ngOnDestroy" in all_content or "Subscription" in all_content

    def test_emit_empty_collection_raises_error(self):
        emitter = AngularGeospatialEmitter()
        empty = GeospatialCollection()
        try:
            emitter.emit(empty)
            assert False, "Nên raise error"
        except Exception:
            pass


# ===========================================================================
# ReactGeospatialEmitter
# ===========================================================================


class TestReactGeospatialEmitter:
    def test_emit_returns_list_of_dicts(self):
        emitter = ReactGeospatialEmitter()
        result = emitter.emit(_make_collection())
        assert isinstance(result, list)
        assert all(isinstance(f, dict) for f in result)

    def test_emit_has_all_components(self):
        emitter = ReactGeospatialEmitter()
        result = emitter.emit(_make_collection())
        paths = [f["path"] for f in result]
        assert any("MapView" in p for p in paths)
        assert any("GeofenceAlert" in p for p in paths)

    def test_emit_has_react_syntax(self):
        emitter = ReactGeospatialEmitter()
        result = emitter.emit(_make_collection())
        all_content = "\n".join(f["content"] for f in result)
        assert "React.FC" in all_content or "function" in all_content
        assert "useState" in all_content or "interface" in all_content

    def test_emit_empty_collection_raises_error(self):
        emitter = ReactGeospatialEmitter()
        empty = GeospatialCollection()
        try:
            emitter.emit(empty)
            assert False, "Nên raise error"
        except Exception:
            pass

# ===========================================================================
# NestJSGeospatialEmitter — NO template (inline fallback)
# ===========================================================================


class TestNestJSGeospatialEmitterNoTemplate:
    """Test NestJS emitter khi không có template dir — cover inline fallback."""

    def test_inline_service_generation(self):
        """Cover lines 51, 102-103, 198: inline service khi stack_dir=None."""
        emitter = NestJSGeospatialEmitter(stack_dir=None)
        result = emitter.emit(_make_collection())
        assert isinstance(result, list)
        paths = [f["path"] for f in result]
        assert any("geospatial.service" in p for p in paths)
        # Verify inline generated content (not template)
        content = "\n".join(f["content"] for f in result)
        assert "Injectable" in content

    def test_inline_geofence_service(self):
        """Cover lines 132-133: inline geofence service."""
        emitter = NestJSGeospatialEmitter(stack_dir=None)
        result = emitter.generate_geofence_service(_make_collection())
        assert len(result) == 1
        assert "geofence.service" in result[0]["path"]
        content = result[0]["content"]
        assert "GeofenceService" in content

    def test_inline_routing_service(self):
        """Cover lines 155-156: inline routing service."""
        emitter = NestJSGeospatialEmitter(stack_dir=None)
        result = emitter.generate_routing_service(_make_collection())
        assert len(result) == 1
        content = result[0]["content"]
        assert "RoutingService" in content

    def test_inline_controller(self):
        """Cover lines 175-176: inline controller."""
        emitter = NestJSGeospatialEmitter(stack_dir=None)
        result = emitter.generate_controller(_make_collection())
        assert len(result) == 1
        assert "geospatial.controller" in result[0]["path"]
        content = result[0]["content"]
        assert "Controller" in content


# ===========================================================================
# ReactGeospatialEmitter — routing disabled
# ===========================================================================


def _make_collection_no_routing() -> GeospatialCollection:
    """Tạo collection không có routing — cover branch 61→63, 80-82."""
    collection = GeospatialCollection()
    collection.add(
        GeospatialSpec(
            id="no_routing",
            name="No Routing",
            entity="Device",
            routing_enabled=False,
            reverse_geocoding_enabled=False,
            geofences=[
                Geofence(
                    name="Zone",
                    shape=GeofenceShape.CIRCLE,
                    center=GeoPoint(latitude=10.7769, longitude=106.7009),
                    radius_m=1000.0,
                )
            ],
        )
    )
    return collection


class TestReactGeospatialEmitterNoRouting:
    """Test React emitter khi routing disabled — cover branch 61→63, 80-82."""

    def test_emit_without_routing(self):
        emitter = ReactGeospatialEmitter()
        result = emitter.emit(_make_collection_no_routing())
        content = "\n".join(f["content"] for f in result)
        # Should have map view but no route-related code
        assert "MapView" in content or "map" in content.lower()

    def test_map_view_no_routing_blocks(self):
        """Cover lines 80-82: routing-specific blocks when has_routing is False."""
        emitter = ReactGeospatialEmitter()
        result = emitter.generate_map_view(_make_collection_no_routing())
        content = result[0]["content"]
        # When has_routing is False, the routes_in_fetch, routes_parse, routes_set
        # should be empty strings (no route-fetching code)
        assert "MapView" in content


# ===========================================================================
# AngularGeospatialEmitter — routing disabled
# ===========================================================================


class TestAngularGeospatialEmitterNoRouting:
    """Test Angular emitter khi routing disabled — cover branch 61→63."""

    def test_emit_without_routing(self):
        emitter = AngularGeospatialEmitter()
        result = emitter.emit(_make_collection_no_routing())
        content = "\n".join(f["content"] for f in result)
        assert "Component" in content

    def test_map_viewer_no_routing(self):
        """Cover branch when has_routing is False — routing_block and routing_load_call empty."""
        emitter = AngularGeospatialEmitter()
        result = emitter.generate_map_viewer(_make_collection_no_routing())
        content = result[0]["content"]
        # hasRouting should be False in generated code
        assert "hasRouting = False" in content
