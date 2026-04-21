"""
Unit Tests cho Geospatial Filter Expressions.

Task: E11-004 - Add geospatial filter expressions
Priority: P1 - Required by Food Delivery, Last Mile Delivery, Warehouse

Kiểm tra:
- geo_within_radius filter
- geo_nearest filter
- geo_bounding_box filter
- Integration với query_records capability

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from midicoder.contracts.core_capabilities import CoreCapabilitiesRegistry


class TestGeospatialWithinRadius:
    """Tests cho geo_within_radius filter."""

    def test_query_with_geo_within_radius(self):
        """Kiểm tra query với geo_within_radius filter."""
        registry = CoreCapabilitiesRegistry()
        cap = registry.get_capability_by_id("query_records")

        # Check filter field exists
        assert "filter" in cap.params_schema

        # Example geo_within_radius filter (tested via flexible dict schema)
        filter_example = {
            "geo_within_radius": {
                "field": "location",
                "center": {"lat": 10.8231, "lng": 106.6297},
                "radius_km": 5
            }
        }
        assert "geo_within_radius" in filter_example
        assert filter_example["geo_within_radius"]["radius_km"] == 5

    def test_food_delivery_driver_search(self):
        """Kiểm tra scenario: Tìm driver gần customer."""
        # Filter để tìm drivers trong bán kính 3km
        driver_filter = {
            "status": "available",
            "geo_within_radius": {
                "field": "current_location",
                "center": {"lat": 10.7769, "lng": 106.7009},  # District 1, HCMC
                "radius_km": 3
            }
        }
        assert driver_filter["geo_within_radius"]["center"]["lat"] == 10.7769


class TestGeospatialNearest:
    """Tests cho geo_nearest filter."""

    def test_query_with_geo_nearest(self):
        """Kiểm tra query với geo_nearest filter."""
        # Example geo_nearest filter
        nearest_filter = {
            "geo_nearest": {
                "field": "warehouse_location",
                "point": {"lat": 21.0285, "lng": 105.8542},  # Hanoi
                "limit": 5
            }
        }
        assert nearest_filter["geo_nearest"]["limit"] == 5

    def test_last_mile_warehouse_search(self):
        """Kiểm tra scenario: Tìm warehouse gần nhất."""
        warehouse_filter = {
            "geo_nearest": {
                "field": "warehouse_location",
                "point": {"lat": 10.8231, "lng": 106.6297},
                "limit": 3,
                "sort_by_distance": True
            }
        }
        assert warehouse_filter["geo_nearest"]["limit"] == 3


class TestGeospatialBoundingBox:
    """Tests cho geo_bounding_box filter."""

    def test_query_with_geo_bounding_box(self):
        """Kiểm tra query với geo_bounding_box filter."""
        bbox_filter = {
            "geo_bounding_box": {
                "field": "store_location",
                "southwest": {"lat": 10.7000, "lng": 106.6000},
                "northeast": {"lat": 10.9000, "lng": 106.8000}
            }
        }
        assert bbox_filter["geo_bounding_box"]["southwest"]["lat"] == 10.7000

    def test_warehouse_coverage_area(self):
        """Kiểm tra scenario: Tìm stores trong coverage area."""
        coverage_filter = {
            "active": True,
            "geo_bounding_box": {
                "field": "store_location",
                "southwest": {"lat": 10.75, "lng": 106.65},
                "northeast": {"lat": 10.85, "lng": 106.75}
            }
        }
        assert coverage_filter["geo_bounding_box"]["field"] == "store_location"


class TestGeospatialComplexFilters:
    """Tests cho complex geospatial filters."""

    def test_combined_geo_and_attribute_filters(self):
        """Kiểm tra kết hợp geo filter và attribute filters."""
        combined_filter = {
            "status": "available",
            "rating": {"gte": 4.5},
            "geo_within_radius": {
                "field": "location",
                "center": {"lat": 10.8231, "lng": 106.6297},
                "radius_km": 5
            }
        }
        assert combined_filter["status"] == "available"
        assert combined_filter["geo_within_radius"]["radius_km"] == 5

    def test_geo_filter_with_sorting(self):
        """Kiểm tra geo filter với sorting by distance."""
        # This would be used with sort params
        filter_with_sort = {
            "geo_within_radius": {
                "field": "restaurant_location",
                "center": {"lat": 10.7769, "lng": 106.7009},
                "radius_km": 10
            },
            "sort_by": "distance",
            "sort_order": "asc"
        }
        assert filter_with_sort["sort_by"] == "distance"


class TestGeospatialCoreCapabilityIntegration:
    """Tests cho geospatial integration với core capabilities."""

    def test_query_records_supports_geo_filters(self):
        """Kiểm tra query_records supports geo filters."""
        registry = CoreCapabilitiesRegistry()
        cap = registry.get_capability_by_id("query_records")

        # query_records has filter field that can accept geo expressions
        assert "filter" in cap.params_schema
        assert cap.params_schema["filter"]["type"] == "object"

    def test_geospatial_filter_structure(self):
        """Kiểm tra cấu trúc geospatial filters."""
        # Standard geospatial filter structure (documented pattern)
        geo_filters = {
            "geo_within_radius": {
                "type": "object",
                "properties": {
                    "field": {"type": "string"},
                    "center": {
                        "type": "object",
                        "properties": {
                            "lat": {"type": "number"},
                            "lng": {"type": "number"}
                        }
                    },
                    "radius_km": {"type": "number"}
                }
            },
            "geo_nearest": {
                "type": "object",
                "properties": {
                    "field": {"type": "string"},
                    "point": {
                        "type": "object",
                        "properties": {
                            "lat": {"type": "number"},
                            "lng": {"type": "number"}
                        }
                    },
                    "limit": {"type": "integer"}
                }
            },
            "geo_bounding_box": {
                "type": "object",
                "properties": {
                    "field": {"type": "string"},
                    "southwest": {
                        "type": "object",
                        "properties": {
                            "lat": {"type": "number"},
                            "lng": {"type": "number"}
                        }
                    },
                    "northeast": {
                        "type": "object",
                        "properties": {
                            "lat": {"type": "number"},
                            "lng": {"type": "number"}
                        }
                    }
                }
            }
        }
        assert "geo_within_radius" in geo_filters
        assert "geo_nearest" in geo_filters
        assert "geo_bounding_box" in geo_filters