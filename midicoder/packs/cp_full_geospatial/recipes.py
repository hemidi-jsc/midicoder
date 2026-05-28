# coding: utf-8
"""
Recipe module cho CP35 Geospatial Services.

Recipes cung cấp config sẵn dùng để map các use case phổ biến
thành GeospatialCollection vocabulary. Mỗi recipe trả về GeospatialCollection
với các GeospatialSpec đã được điền sẵn.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from midicoder.packs.cp_full_geospatial.models import (
    Geofence,
    GeofenceShape,
    GeospatialCollection,
    GeospatialSpec,
    GeoPoint,
    RoutingProfile,
)


# ===========================================================================
# Geofence Monitoring Recipe
# ===========================================================================


def geofence_monitoring_recipe(
    entity: str = "Device",
    geofence_name: str = "Default Geofence",
    shape: str = "circle",
    center_lat: float = 10.7769,
    center_lng: float = 106.7009,
    radius_m: float = 1000.0,
) -> GeospatialCollection:
    """
    Recipe tạo geospatial spec với geofence monitoring.

    Use case: Monitor enter/exit events khi entity di chuyển vào/ra khỏi
    vùng địa lý được định nghĩa.

    Args:
        entity: Entity source cần monitor
        geofence_name: Tên geofence
        shape: Hình dạng geofence (circle, polygon, rectangle)
        center_lat: Vĩ độ tâm (chỉ dùng cho circle)
        center_lng: Kinh độ tâm (chỉ dùng cho circle)
        radius_m: Bán kính tính bằng mét (chỉ dùng cho circle)

    Returns:
        GeospatialCollection với 1 geospatial spec có geofence config
    """
    collection = GeospatialCollection()

    # Parse shape
    try:
        fence_shape = GeofenceShape(shape)
    except ValueError:
        fence_shape = GeofenceShape.CIRCLE

    # Build geofence theo shape
    geofence = _build_geofence(
        name=geofence_name,
        shape=fence_shape,
        center_lat=center_lat,
        center_lng=center_lng,
        radius_m=radius_m,
    )

    collection.add(
        GeospatialSpec(
            id=f"{entity.lower()}_geofence",
            name=f"{entity} Geofence Monitoring",
            entity=entity,
            geofences=[geofence],
            routing_enabled=False,
            reverse_geocoding_enabled=False,
            notification_on_trigger=True,
            metadata={
                "recipe": "geofence_monitoring",
                "shape": shape,
            },
        )
    )

    return collection


# ===========================================================================
# Routing Service Recipe
# ===========================================================================


def routing_service_recipe(
    entity: str = "Location",
    profile: str = "driving",
) -> GeospatialCollection:
    """
    Recipe tạo geospatial spec với routing service.

    Use case: Tính toán đường đi giữa các điểm với profile di chuyển
    (driving, walking, cycling).

    Args:
        entity: Entity source cần tính route
        profile: Profile di chuyển (driving, walking, cycling)

    Returns:
        GeospatialCollection với 1 geospatial spec có routing enabled
    """
    collection = GeospatialCollection()

    # Parse profile
    try:
        routing_profile = RoutingProfile(profile)
    except ValueError:
        routing_profile = RoutingProfile.DRIVING

    collection.add(
        GeospatialSpec(
            id=f"{entity.lower()}_routing",
            name=f"{entity} Routing Service",
            entity=entity,
            geofences=[],
            routing_enabled=True,
            reverse_geocoding_enabled=False,
            notification_on_trigger=False,
            metadata={
                "recipe": "routing_service",
                "routing_profile": routing_profile.value,
            },
        )
    )

    return collection


# ===========================================================================
# Location Tracker Recipe (Full)
# ===========================================================================


def location_tracker_recipe(
    entity: str = "Asset",
    enable_geofencing: bool = True,
    enable_routing: bool = True,
    enable_reverse_geocoding: bool = True,
) -> GeospatialCollection:
    """
    Recipe tạo geospatial spec đầy đủ cho location tracking.

    Use case: Theo dõi vị trí thực tế của asset với đầy đủ tính năng:
    geofencing, routing, reverse geocoding.

    Args:
        entity: Entity source cần theo dõi
        enable_geofencing: Có bật geofencing không
        enable_routing: Có bật routing không
        enable_reverse_geocoding: Có bật reverse geocoding không

    Returns:
        GeospatialCollection với 1 geospatial spec đầy đủ features
    """
    collection = GeospatialCollection()

    geofences = []
    if enable_geofencing:
        geofences.append(
            _build_geofence(
                name=f"{entity} Default Zone",
                shape=GeofenceShape.CIRCLE,
                center_lat=10.7769,
                center_lng=106.7009,
                radius_m=5000.0,
            )
        )

    collection.add(
        GeospatialSpec(
            id=f"{entity.lower()}_tracker",
            name=f"{entity} Location Tracker",
            entity=entity,
            geofences=geofences,
            routing_enabled=enable_routing,
            reverse_geocoding_enabled=enable_reverse_geocoding,
            notification_on_trigger=enable_geofencing,
            metadata={
                "recipe": "location_tracker",
                "geofencing": enable_geofencing,
                "routing": enable_routing,
                "reverse_geocoding": enable_reverse_geocoding,
            },
        )
    )

    return collection


# ===========================================================================
# Helpers
# ===========================================================================


def _build_geofence(
    name: str,
    shape: GeofenceShape,
    center_lat: float,
    center_lng: float,
    radius_m: float,
) -> Geofence:
    """Xây dựng Geofence theo shape."""
    if shape == GeofenceShape.CIRCLE:
        return Geofence(
            name=name,
            shape=GeofenceShape.CIRCLE,
            center=GeoPoint(latitude=center_lat, longitude=center_lng),
            radius_m=radius_m,
        )
    elif shape == GeofenceShape.POLYGON:
        # Tạo polygon mặc định hình chữ nhật quanh center
        offset = radius_m / 111000.0  # xấp xỉ độ dài 1 độ
        return Geofence(
            name=name,
            shape=GeofenceShape.POLYGON,
            points=[
                GeoPoint(latitude=center_lat + offset, longitude=center_lng - offset),
                GeoPoint(latitude=center_lat + offset, longitude=center_lng + offset),
                GeoPoint(latitude=center_lat - offset, longitude=center_lng + offset),
                GeoPoint(latitude=center_lat - offset, longitude=center_lng - offset),
            ],
        )
    elif shape == GeofenceShape.RECTANGLE:
        offset = radius_m / 111000.0
        return Geofence(
            name=name,
            shape=GeofenceShape.RECTANGLE,
            min_lat=center_lat - offset,
            min_lng=center_lng - offset,
            max_lat=center_lat + offset,
            max_lng=center_lng + offset,
        )
    else:
        return Geofence(
            name=name,
            shape=GeofenceShape.CIRCLE,
            center=GeoPoint(latitude=center_lat, longitude=center_lng),
            radius_m=radius_m,
        )


__all__ = [
    "geofence_monitoring_recipe",
    "routing_service_recipe",
    "location_tracker_recipe",
]
