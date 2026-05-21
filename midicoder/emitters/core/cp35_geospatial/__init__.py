# coding: utf-8
"""
CP35: Geospatial Services.

Cung cấp:
- models: GeospatialSpec, Geofence, GeoPoint, GeospatialCollection, RouteResult, RouteStep
- enums: GeofenceShape, DistanceUnit, RoutingProfile, GeofenceEvent
- parser: GeospatialParser
- fastapi: FastAPIGeospatialEmitter (backend)
- nestjs: NestJSGeospatialEmitter (backend)
- angular: AngularGeospatialEmitter (frontend viewer)
- react: ReactGeospatialEmitter (frontend viewer)
- recipes: geospatial recipes cho CP51 composition
"""

from midicoder.emitters.core.cp35_geospatial.models import (
    DistanceUnit,
    Geofence,
    GeofenceEvent,
    GeofenceShape,
    GeospatialCollection,
    GeospatialSpec,
    GeoPoint,
    RouteResult,
    RouteStep,
    RoutingProfile,
)
from midicoder.emitters.core.cp35_geospatial.parser import GeospatialParser
from midicoder.emitters.core.cp35_geospatial.angular import AngularGeospatialEmitter
from midicoder.emitters.core.cp35_geospatial.react import ReactGeospatialEmitter

__all__ = [
    "AngularGeospatialEmitter",
    "DistanceUnit",
    "Geofence",
    "GeofenceEvent",
    "GeofenceShape",
    "GeospatialCollection",
    "GeospatialParser",
    "GeospatialSpec",
    "GeoPoint",
    "ReactGeospatialEmitter",
    "RouteResult",
    "RouteStep",
    "RoutingProfile",
]
