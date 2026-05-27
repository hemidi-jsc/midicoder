# coding: utf-8
"""
Mô-đun models cho CP62 — Mobile Backend (FCM/APNs Push, Deep Linking, Mobile Auth, OTA).

Định nghĩa các dataclass biểu diễn:
- PushNotificationConfig: Cấu hình push notification (FCM/APNs)
- DeepLinkRoute: Route deep link với pattern matching
- MobileAuthProvider: OAuth2 mobile auth provider (Apple/Google/Facebook)
- OTAUpdateConfig: Cấu hình OTA update (forced update, rollout)
- DeviceRegistration: Đăng ký thiết bị mobile với push token

KPI-005: CP Obligations Coverage (>= 2 obligations cho CP62).

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# ===========================================================================
# Enums
# ===========================================================================


class PushPlatform(str, Enum):
    """Nền tảng push notification.

    - FCM: Firebase Cloud Messaging (Android)
    - APNS: Apple Push Notification Service (iOS)
    - BOTH: Cả FCM và APNs
    """
    FCM = "fcm"
    APNS = "apns"
    BOTH = "both"


class DeepLinkAuth(str, Enum):
    """Yêu cầu xác thực cho deep link.

    - REQUIRED: Bắt buộc phải đăng nhập
    - OPTIONAL: Không bắt buộc
    """
    REQUIRED = "required"
    OPTIONAL = "optional"


class MobileAuthType(str, Enum):
    """Loại mobile auth provider.

    - APPLE: Sign in with Apple
    - GOOGLE: Google Sign-In
    - FACEBOOK: Facebook Login
    """
    APPLE = "apple"
    GOOGLE = "google"
    FACEBOOK = "facebook"


class OTAPlatform(str, Enum):
    """Nền tảng OTA update.

    - IOS: iOS OTA update
    - ANDROID: Android OTA update
    - BOTH: Cả iOS và Android
    """
    IOS = "ios"
    ANDROID = "android"
    BOTH = "both"


class DevicePlatform(str, Enum):
    """Nền tảng thiết bị mobile.

    - IOS: iOS device
    - ANDROID: Android device
    """
    IOS = "ios"
    ANDROID = "android"


# ===========================================================================
# PushNotificationConfig
# ===========================================================================


@dataclass
class PushNotificationConfig:
    """Cấu hình push notification.

    Chứa thông tin cấu hình cho push notification service, bao gồm
    nền tảng (FCM/APNs), server key reference, bundle ID, topic,
    và các tùy chọn notification (sound, badge, data payload).

    Attributes:
        id: ID duy nhất của cấu hình push notification
        platform: Nền tảng push notification (fcm|apns|both)
        server_key_ref: Reference đến server key/secret trong secret store
        bundle_id: Bundle ID của ứng dụng (iOS) hoặc package name (Android)
        topic: Topic mặc định cho push notification
        sound: Có bật âm thanh notification không
        badge: Có hiển thị badge count không
        data_payload: Có hỗ trợ data payload (silent push) không
    """
    id: str
    platform: PushPlatform
    server_key_ref: str = ""
    bundle_id: str = ""
    topic: str = ""
    sound: bool = True
    badge: bool = True
    data_payload: bool = True

    def __post_init__(self) -> None:
        """Validate config sau khi khởi tạo."""
        if not self.id or not self.id.strip():
            raise EM.raise_error(
                ErrorCode.INVALID_PARAMETER,
                reason="PushNotificationConfig.id bắt buộc và không được để trống",
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển PushNotificationConfig sang dict."""
        return {
            "id": self.id,
            "platform": self.platform.value,
            "server_key_ref": self.server_key_ref,
            "bundle_id": self.bundle_id,
            "topic": self.topic,
            "sound": self.sound,
            "badge": self.badge,
            "data_payload": self.data_payload,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PushNotificationConfig":
        """Tạo PushNotificationConfig từ dict."""
        return cls(
            id=data["id"],
            platform=PushPlatform(data.get("platform", "both")),
            server_key_ref=data.get("server_key_ref", ""),
            bundle_id=data.get("bundle_id", ""),
            topic=data.get("topic", ""),
            sound=data.get("sound", True),
            badge=data.get("badge", True),
            data_payload=data.get("data_payload", True),
        )


# ===========================================================================
# DeepLinkRoute
# ===========================================================================


@dataclass
class DeepLinkRoute:
    """Route deep link.

    Định nghĩa một route deep link, bao gồm pattern path,
    target screen, yêu cầu xác thực, các tham số URL,
    và fallback behavior khi deep link không được xử lý.

    Attributes:
        id: ID duy nhất của deep link route
        path_pattern: Pattern của path (vd: "/product/{id}", "/order/{id}/status")
        target_screen: Tên screen/activity sẽ mở khi deep link được trigger
        auth_required: Có bắt buộc đăng nhập không
        params: Các tham số trong path pattern (vd: {"id": "string"})
        fallback_url: URL fallback khi ứng dụng không cài đặt hoặc deep link fail
        universal_link_enabled: Có bật Universal Link (iOS) / App Link (Android) không
    """
    id: str
    path_pattern: str
    target_screen: str
    auth_required: bool = False
    params: dict[str, str] = field(default_factory=dict)
    fallback_url: str = ""
    universal_link_enabled: bool = False

    def __post_init__(self) -> None:
        """Validate route sau khi khởi tạo."""
        if not self.id or not self.id.strip():
            raise EM.raise_error(
                ErrorCode.INVALID_PARAMETER,
                reason="DeepLinkRoute.id bắt buộc và không được để trống",
            )
        if not self.path_pattern or not self.path_pattern.strip():
            raise EM.raise_error(
                ErrorCode.INVALID_PARAMETER,
                reason="DeepLinkRoute.path_pattern bắt buộc và không được để trống",
            )
        if not self.target_screen or not self.target_screen.strip():
            raise EM.raise_error(
                ErrorCode.INVALID_PARAMETER,
                reason="DeepLinkRoute.target_screen bắt buộc và không được để trống",
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển DeepLinkRoute sang dict."""
        return {
            "id": self.id,
            "path_pattern": self.path_pattern,
            "target_screen": self.target_screen,
            "auth_required": self.auth_required,
            "params": self.params,
            "fallback_url": self.fallback_url,
            "universal_link_enabled": self.universal_link_enabled,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DeepLinkRoute":
        """Tạo DeepLinkRoute từ dict."""
        return cls(
            id=data["id"],
            path_pattern=data.get("path_pattern", ""),
            target_screen=data.get("target_screen", ""),
            auth_required=data.get("auth_required", False),
            params=data.get("params", {}),
            fallback_url=data.get("fallback_url", ""),
            universal_link_enabled=data.get("universal_link_enabled", False),
        )


# ===========================================================================
# MobileAuthProvider
# ===========================================================================


@dataclass
class MobileAuthProvider:
    """Mobile auth provider.

    Cấu hình OAuth2 provider cho mobile authentication, bao gồm
    loại provider (Apple/Google/Facebook), client credentials,
    redirect URI, và OAuth scopes.

    Attributes:
        id: ID duy nhất của auth provider
        type: Loại auth provider (apple|google|facebook)
        client_id_ref: Reference đến client ID trong secret store
        client_secret_ref: Reference đến client secret trong secret store
        redirect_uri: Redirect URI cho OAuth2 callback
        scopes: Danh sách OAuth scopes yêu cầu
    """
    id: str
    type: MobileAuthType
    client_id_ref: str = ""
    client_secret_ref: str = ""
    redirect_uri: str = ""
    scopes: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate auth provider sau khi khởi tạo."""
        if not self.id or not self.id.strip():
            raise EM.raise_error(
                ErrorCode.INVALID_PARAMETER,
                reason="MobileAuthProvider.id bắt buộc và không được để trống",
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển MobileAuthProvider sang dict."""
        return {
            "id": self.id,
            "type": self.type.value,
            "client_id_ref": self.client_id_ref,
            "client_secret_ref": "****",
            "redirect_uri": self.redirect_uri,
            "scopes": self.scopes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MobileAuthProvider":
        """Tạo MobileAuthProvider từ dict."""
        return cls(
            id=data["id"],
            type=MobileAuthType(data.get("type", "google")),
            client_id_ref=data.get("client_id_ref", ""),
            client_secret_ref=data.get("client_secret_ref", ""),
            redirect_uri=data.get("redirect_uri", ""),
            scopes=data.get("scopes", []),
        )


# ===========================================================================
# OTAUpdateConfig
# ===========================================================================


@dataclass
class OTAUpdateConfig:
    """Cấu hình OTA update.

    Định nghĩa cấu hình cho over-the-air update, bao gồm nền tảng mục tiêu,
    chế độ forced update, minimum version requirement, release notes,
    download URL, và rollout percentage.

    Attributes:
        id: ID duy nhất của OTA update config
        platform: Nền tảng mục tiêu (ios|android|both)
        forced_update: Có bắt buộc update không (ngăn dùng app nếu không update)
        minimum_version: Phiên bản tối thiểu yêu cầu (vd: "2.0.0")
        release_notes_url: URL đến release notes
        download_url: URL download bản cập nhật
        rollout_percentage: Phần trăm rollout (1-100, mặc định: 100)
    """
    id: str
    platform: OTAPlatform
    forced_update: bool = False
    minimum_version: str = ""
    release_notes_url: str = ""
    download_url: str = ""
    rollout_percentage: int = 100

    def __post_init__(self) -> None:
        """Validate OTA config sau khi khởi tạo."""
        if not self.id or not self.id.strip():
            raise EM.raise_error(
                ErrorCode.INVALID_PARAMETER,
                reason="OTAUpdateConfig.id bắt buộc và không được để trống",
            )
        if not (1 <= self.rollout_percentage <= 100):
            raise EM.raise_error(
                ErrorCode.INVALID_PARAMETER,
                reason=f"rollout_percentage phải từ 1-100, nhận được: {self.rollout_percentage}",
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển OTAUpdateConfig sang dict."""
        return {
            "id": self.id,
            "platform": self.platform.value,
            "forced_update": self.forced_update,
            "minimum_version": self.minimum_version,
            "release_notes_url": self.release_notes_url,
            "download_url": self.download_url,
            "rollout_percentage": self.rollout_percentage,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OTAUpdateConfig":
        """Tạo OTAUpdateConfig từ dict."""
        return cls(
            id=data["id"],
            platform=OTAPlatform(data.get("platform", "both")),
            forced_update=data.get("forced_update", False),
            minimum_version=data.get("minimum_version", ""),
            release_notes_url=data.get("release_notes_url", ""),
            download_url=data.get("download_url", ""),
            rollout_percentage=data.get("rollout_percentage", 100),
        )


# ===========================================================================
# DeviceRegistration
# ===========================================================================


@dataclass
class DeviceRegistration:
    """Đăng ký thiết bị mobile.

    Lưu thông tin thiết bị mobile đã đăng ký, bao gồm nền tảng,
    device token cho push notification, deep link handler,
    phiên bản OS/app, và thời gian last seen.

    Attributes:
        id: ID duy nhất của device registration
        platform: Nền tảng thiết bị (ios|android)
        device_token: Token push notification từ FCM/APNs
        push_enabled: Có bật push notification không
        deep_link_handler: Handler function cho deep link của thiết bị này
        last_seen: Thời gian last seen của thiết bị
        os_version: Phiên bản OS (vd: "iOS 17.0", "Android 14")
        app_version: Phiên bản ứng dụng (vd: "1.2.3")
    """
    id: str
    platform: DevicePlatform
    device_token: str = ""
    push_enabled: bool = True
    deep_link_handler: str = ""
    last_seen: datetime | None = None
    os_version: str = ""
    app_version: str = ""

    def __post_init__(self) -> None:
        """Validate device sau khi khởi tạo."""
        if not self.id or not self.id.strip():
            raise EM.raise_error(
                ErrorCode.INVALID_PARAMETER,
                reason="DeviceRegistration.id bắt buộc và không được để trống",
            )
        now = datetime.now(timezone.utc)
        if self.last_seen is None:
            self.last_seen = now

    def to_dict(self) -> dict[str, Any]:
        """Chuyển DeviceRegistration sang dict."""
        return {
            "id": self.id,
            "platform": self.platform.value,
            "device_token": self.device_token,
            "push_enabled": self.push_enabled,
            "deep_link_handler": self.deep_link_handler,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "os_version": self.os_version,
            "app_version": self.app_version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DeviceRegistration":
        """Tạo DeviceRegistration từ dict."""
        last_seen = None
        if data.get("last_seen"):
            try:
                last_seen = datetime.fromisoformat(data["last_seen"])
            except (ValueError, TypeError):
                pass
        return cls(
            id=data["id"],
            platform=DevicePlatform(data.get("platform", "android")),
            device_token=data.get("device_token", ""),
            push_enabled=data.get("push_enabled", True),
            deep_link_handler=data.get("deep_link_handler", ""),
            last_seen=last_seen,
            os_version=data.get("os_version", ""),
            app_version=data.get("app_version", ""),
        )
