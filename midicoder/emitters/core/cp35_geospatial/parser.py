# coding: utf-8
"""
Mô-đun parser cho Geospatial Pack (CP35).

Parse YAML DSL thành GeospatialCollection chứa:
- GeospatialSpec: Spec cho geospatial service (entity, geofences, routing, reverse geocoding)

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from typing import Any

import yaml

from midicoder.emitters.core.cp35_geospatial.models import (
    Geofence,
    GeofenceShape,
    GeospatialCollection,
    GeospatialSpec,
    GeoPoint,
)
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


class GeospatialParser:
    """
    Parser cho DSL geospatial spec.

    Parse YAML DSL thành GeospatialCollection.

    Ví dụ DSL:
        geospatial_specs:
          - id: "geofence_monitor"
            name: "Geofence Monitor"
            entity: "Device"
            routing_enabled: true
            reverse_geocoding_enabled: true
            notification_on_trigger: true
            geofences:
              - id: "factory_perimeter"
                name: "Factory Perimeter"
                shape: "polygon"
                points:
                  - latitude: 10.7769
                    longitude: 106.7009
                  - latitude: 10.7779
                    longitude: 106.7009
                  - latitude: 10.7779
                    longitude: 106.7019
              - id: "delivery_zone"
                name: "Delivery Zone"
                shape: "circle"
                center:
                  latitude: 10.7750
                  longitude: 106.7000
                radius_m: 5000
    """

    def parse(self, raw: str) -> GeospatialCollection:
        """
        Parse YAML DSL string thành GeospatialCollection.

        Args:
            raw: YAML string chứa danh sách geospatial specs

        Returns:
            GeospatialCollection chứa geospatial specs

        Raises:
            MidicoderError: Nếu YAML không hợp lệ hoặc parse thất bại
        """
        if not raw or not raw.strip():
            return GeospatialCollection()

        # Parse YAML
        try:
            data = yaml.safe_load(raw)
        except yaml.YAMLError as e:
            EM.raise_error(
                ErrorCode.CP35_PARSER_ERROR,
                error=str(e),
            )

        # YAML comment-only hoặc null → treat as empty collection
        if data is None:
            return GeospatialCollection()
        if not isinstance(data, dict):
            EM.raise_error(
                ErrorCode.CP35_PARSER_ERROR,
                error="DSL geospatial spec phải là YAML mapping",
            )

        collection = GeospatialCollection()

        # Parse geospatial_specs
        raw_specs = data.get("geospatial_specs", [])
        if isinstance(raw_specs, list):
            for spec_data in raw_specs:
                spec = self._parse_geospatial_spec(spec_data)
                collection.add(spec)

        return collection

    def parse_from_metadata(self, data: dict[str, Any]) -> GeospatialCollection:
        """
        Parse dict từ MIR metadata thành GeospatialCollection.

        Args:
            data: Dict chứa geospatial specs từ MIR metadata

        Returns:
            GeospatialCollection chứa geospatial specs
        """
        if not isinstance(data, dict):
            EM.raise_error(
                ErrorCode.CP35_PARSER_ERROR,
                error="Geospatial metadata phải là dict",
            )

        collection = GeospatialCollection()
        raw_specs = data.get("geospatial_specs", data.get("reports", []))

        if isinstance(raw_specs, list):
            for spec_data in raw_specs:
                spec = self._parse_geospatial_spec(spec_data)
                collection.add(spec)

        return collection

    def _parse_geospatial_spec(self, data: dict[str, Any]) -> GeospatialSpec:
        """
        Parse dict thành GeospatialSpec.

        Args:
            data: Dict chứa thông tin geospatial spec

        Returns:
            GeospatialSpec instance

        Raises:
            MidicoderError: Nếu dữ liệu không hợp lệ
        """
        if not isinstance(data, dict):
            EM.raise_error(
                ErrorCode.CP35_PARSER_ERROR,
                error="Geospatial spec phải là YAML mapping",
            )

        # Parse geofences
        geofences = []
        raw_geofences = data.get("geofences", [])
        if isinstance(raw_geofences, list):
            for fence_data in raw_geofences:
                fence = self._parse_geofence(fence_data)
                geofences.append(fence)

        return GeospatialSpec(
            id=data.get("id", ""),
            name=data.get("name", ""),
            entity=data.get("entity", ""),
            geofences=geofences,
            routing_enabled=data.get("routing_enabled", False),
            reverse_geocoding_enabled=data.get("reverse_geocoding_enabled", False),
            notification_on_trigger=data.get("notification_on_trigger", False),
            metadata=data.get("metadata", {}),
        )

    def _parse_geofence(self, data: dict[str, Any]) -> Geofence:
        """
        Parse dict thành Geofence.

        Args:
            data: Dict chứa thông tin geofence

        Returns:
            Geofence instance

        Raises:
            MidicoderError: Nếu shape không hợp lệ hoặc dữ liệu thiếu
        """
        if not isinstance(data, dict):
            EM.raise_error(
                ErrorCode.CP35_PARSER_ERROR,
                error="Geofence phải là YAML mapping",
            )

        # Parse shape
        shape_str = data.get("shape", "circle")
        try:
            shape = GeofenceShape(shape_str)
        except ValueError:
            EM.raise_error(
                ErrorCode.CP35_INVALID_GEOFENCE_SHAPE,
                shape=shape_str,
            )

        kwargs: dict[str, Any] = {
            "id": data.get("id", ""),
            "name": data.get("name", ""),
            "shape": shape,
            "enabled": data.get("enabled", True),
            "metadata": data.get("metadata", {}),
        }

        if shape == GeofenceShape.CIRCLE:
            center_data = data.get("center", {})
            kwargs["center"] = self._parse_geo_point(center_data) if center_data else None
            kwargs["radius_m"] = data.get("radius_m", 0.0)
        elif shape == GeofenceShape.POLYGON:
            points_data = data.get("points", [])
            kwargs["points"] = [self._parse_geo_point(p) for p in points_data]
        elif shape == GeofenceShape.RECTANGLE:
            kwargs["min_lat"] = data.get("min_lat", -90.0)
            kwargs["min_lng"] = data.get("min_lng", -180.0)
            kwargs["max_lat"] = data.get("max_lat", 90.0)
            kwargs["max_lng"] = data.get("max_lng", 180.0)

        return Geofence(**kwargs)

    def _parse_geo_point(self, data: dict[str, Any]) -> GeoPoint:
        """
        Parse dict thành GeoPoint.

        Args:
            data: Dict chứa latitude, longitude

        Returns:
            GeoPoint instance
        """
        return GeoPoint(
            latitude=data.get("latitude", 0.0),
            longitude=data.get("longitude", 0.0),
        )
