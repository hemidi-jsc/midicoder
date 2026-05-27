# coding: utf-8
"""
Tests cho recipe module CP35 Geospatial Services.

Kiểm tra: geofence_monitoring_recipe, routing_service_recipe, location_tracker_recipe.
"""

from midicoder.packs.cp35_geospatial.recipes import (
    geofence_monitoring_recipe,
    routing_service_recipe,
    location_tracker_recipe,
)
from midicoder.packs.cp35_geospatial.models import (
    GeofenceShape,
    GeospatialCollection,
)


# ===========================================================================
# geofence_monitoring_recipe
# ===========================================================================


class TestGeofenceMonitoringRecipe:
    def test_returns_collection(self):
        result = geofence_monitoring_recipe()
        assert isinstance(result, GeospatialCollection)

    def test_has_one_spec(self):
        result = geofence_monitoring_recipe()
        assert len(result.reports) == 1

    def test_default_entity(self):
        result = geofence_monitoring_recipe()
        assert result.reports[0].entity == "Device"

    def test_custom_entity(self):
        result = geofence_monitoring_recipe(entity="Vehicle")
        assert result.reports[0].entity == "Vehicle"

    def test_default_shape_is_circle(self):
        result = geofence_monitoring_recipe()
        assert result.reports[0].geofences[0].shape == GeofenceShape.CIRCLE

    def test_custom_shape_polygon(self):
        result = geofence_monitoring_recipe(shape="polygon")
        assert result.reports[0].geofences[0].shape == GeofenceShape.POLYGON

    def test_custom_shape_rectangle(self):
        result = geofence_monitoring_recipe(shape="rectangle")
        assert result.reports[0].geofences[0].shape == GeofenceShape.RECTANGLE

    def test_invalid_shape_defaults_to_circle(self):
        result = geofence_monitoring_recipe(shape="invalid")
        assert result.reports[0].geofences[0].shape == GeofenceShape.CIRCLE

    def test_has_geofence(self):
        result = geofence_monitoring_recipe()
        assert len(result.reports[0].geofences) == 1

    def test_notification_enabled(self):
        result = geofence_monitoring_recipe()
        assert result.reports[0].notification_on_trigger is True

    def test_routing_disabled(self):
        result = geofence_monitoring_recipe()
        assert result.reports[0].routing_enabled is False


# ===========================================================================
# routing_service_recipe
# ===========================================================================


class TestRoutingServiceRecipe:
    def test_returns_collection(self):
        result = routing_service_recipe()
        assert isinstance(result, GeospatialCollection)

    def test_has_one_spec(self):
        result = routing_service_recipe()
        assert len(result.reports) == 1

    def test_default_entity(self):
        result = routing_service_recipe()
        assert result.reports[0].entity == "Location"

    def test_routing_enabled(self):
        result = routing_service_recipe()
        assert result.reports[0].routing_enabled is True

    def test_custom_profile(self):
        result = routing_service_recipe(profile="walking")
        assert result.reports[0].metadata["routing_profile"] == "walking"

    def test_invalid_profile_defaults_to_driving(self):
        result = routing_service_recipe(profile="invalid")
        assert result.reports[0].metadata["routing_profile"] == "driving"


# ===========================================================================
# location_tracker_recipe
# ===========================================================================


class TestLocationTrackerRecipe:
    def test_returns_collection(self):
        result = location_tracker_recipe()
        assert isinstance(result, GeospatialCollection)

    def test_has_one_spec(self):
        result = location_tracker_recipe()
        assert len(result.reports) == 1

    def test_default_entity(self):
        result = location_tracker_recipe()
        assert result.reports[0].entity == "Asset"

    def test_all_features_enabled_by_default(self):
        result = location_tracker_recipe()
        assert result.reports[0].routing_enabled is True
        assert result.reports[0].reverse_geocoding_enabled is True
        assert len(result.reports[0].geofences) > 0

    def test_geofencing_disabled(self):
        result = location_tracker_recipe(enable_geofencing=False)
        assert len(result.reports[0].geofences) == 0

    def test_routing_disabled(self):
        result = location_tracker_recipe(enable_routing=False)
        assert result.reports[0].routing_enabled is False

    def test_reverse_geocoding_disabled(self):
        result = location_tracker_recipe(enable_reverse_geocoding=False)
        assert result.reports[0].reverse_geocoding_enabled is False

    def test_metadata_contains_flags(self):
        result = location_tracker_recipe(enable_geofencing=False, enable_routing=True)
        meta = result.reports[0].metadata
        assert meta["geofencing"] is False
        assert meta["routing"] is True
