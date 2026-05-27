# coding: utf-8
"""Tests cho CP62 — Mobile Backend (Push, Deep Link, Auth, OTA) models."""

import pytest
from midicoder.packs.cp62_mobile_backend.models import (
    DeepLinkAuth,
    DeepLinkRoute,
    DevicePlatform,
    DeviceRegistration,
    MobileAuthProvider,
    MobileAuthType,
    OTAPlatform,
    OTAUpdateConfig,
    PushNotificationConfig,
    PushPlatform,
)


# =============================================================================
# Enums
# =============================================================================

class TestPushPlatform:
    def test_enum_values(self):
        assert PushPlatform.FCM.value == "fcm"
        assert PushPlatform.APNS.value == "apns"
        assert PushPlatform.BOTH.value == "both"

    def test_enum_count(self):
        assert len(PushPlatform) == 3


class TestDeepLinkAuth:
    def test_enum_values(self):
        assert DeepLinkAuth.REQUIRED.value == "required"
        assert DeepLinkAuth.OPTIONAL.value == "optional"

    def test_enum_count(self):
        assert len(DeepLinkAuth) == 2


class TestMobileAuthType:
    def test_enum_values(self):
        assert MobileAuthType.APPLE.value == "apple"
        assert MobileAuthType.GOOGLE.value == "google"
        assert MobileAuthType.FACEBOOK.value == "facebook"

    def test_enum_count(self):
        assert len(MobileAuthType) == 3


class TestOTAPlatform:
    def test_enum_values(self):
        assert OTAPlatform.IOS.value == "ios"
        assert OTAPlatform.ANDROID.value == "android"
        assert OTAPlatform.BOTH.value == "both"

    def test_enum_count(self):
        assert len(OTAPlatform) == 3


class TestDevicePlatform:
    def test_enum_values(self):
        assert DevicePlatform.IOS.value == "ios"
        assert DevicePlatform.ANDROID.value == "android"

    def test_enum_count(self):
        assert len(DevicePlatform) == 2


# =============================================================================
# PushNotificationConfig
# =============================================================================

class TestPushNotificationConfig:
    def test_creation_with_defaults(self):
        pnc = PushNotificationConfig(id="pnc-1", platform=PushPlatform.FCM)
        assert pnc.sound is True
        assert pnc.badge is True
        assert pnc.data_payload is True

    def test_creation_with_all_fields(self):
        pnc = PushNotificationConfig(
            id="pnc-2", platform=PushPlatform.BOTH,
            server_key_ref="secret-ref", bundle_id="com.app.id",
            topic="notifications", sound=False, badge=False, data_payload=False,
        )
        assert pnc.bundle_id == "com.app.id"
        assert pnc.sound is False

    def test_to_dict(self):
        pnc = PushNotificationConfig(id="pnc-3", platform=PushPlatform.APNS)
        d = pnc.to_dict()
        assert d["platform"] == "apns"
        assert d["sound"] is True

    def test_from_dict(self):
        data = {
            "id": "pnc-4", "platform": "fcm",
            "server_key_ref": "k", "bundle_id": "com.test",
            "topic": "alerts", "sound": False,
        }
        pnc = PushNotificationConfig.from_dict(data)
        assert pnc.platform == PushPlatform.FCM
        assert pnc.sound is False

    def test_validation_error_empty_id(self):
        with pytest.raises(Exception):
            PushNotificationConfig(id="", platform=PushPlatform.FCM)

    def test_roundtrip(self):
        original = PushNotificationConfig(
            id="rt-pnc", platform=PushPlatform.BOTH,
            bundle_id="com.rt", topic="general", badge=False,
        )
        d = original.to_dict()
        restored = PushNotificationConfig.from_dict(d)
        assert restored.id == original.id
        assert restored.platform == original.platform
        assert restored.badge == original.badge


# =============================================================================
# DeepLinkRoute
# =============================================================================

class TestDeepLinkRoute:
    def test_creation_with_defaults(self):
        dlr = DeepLinkRoute(id="dlr-1", path_pattern="/home", target_screen="HomeScreen")
        assert dlr.auth_required is False
        assert dlr.params == {}
        assert dlr.universal_link_enabled is False

    def test_creation_with_all_fields(self):
        dlr = DeepLinkRoute(
            id="dlr-2", path_pattern="/product/{id}",
            target_screen="ProductDetail", auth_required=True,
            params={"id": "string"}, fallback_url="https://example.com",
            universal_link_enabled=True,
        )
        assert dlr.auth_required is True
        assert dlr.params == {"id": "string"}

    def test_to_dict(self):
        dlr = DeepLinkRoute(id="dlr-3", path_pattern="/order/{id}", target_screen="OrderView")
        d = dlr.to_dict()
        assert d["path_pattern"] == "/order/{id}"
        assert d["universal_link_enabled"] is False

    def test_from_dict(self):
        data = {
            "id": "dlr-4", "path_pattern": "/user/{uid}",
            "target_screen": "UserProfile", "auth_required": True,
            "params": {"uid": "string"}, "universal_link_enabled": True,
        }
        dlr = DeepLinkRoute.from_dict(data)
        assert dlr.auth_required is True
        assert dlr.universal_link_enabled is True

    def test_validation_error_empty_id(self):
        with pytest.raises(Exception):
            DeepLinkRoute(id="", path_pattern="/p", target_screen="S")

    def test_validation_error_empty_path_pattern(self):
        with pytest.raises(Exception):
            DeepLinkRoute(id="dlr-5", path_pattern="", target_screen="S")

    def test_validation_error_empty_target_screen(self):
        with pytest.raises(Exception):
            DeepLinkRoute(id="dlr-6", path_pattern="/p", target_screen="")

    def test_roundtrip(self):
        original = DeepLinkRoute(
            id="rt-dlr", path_pattern="/item/{id}", target_screen="ItemDetail",
            auth_required=True, params={"id": "int"},
        )
        d = original.to_dict()
        restored = DeepLinkRoute.from_dict(d)
        assert restored.id == original.id
        assert restored.path_pattern == original.path_pattern
        assert restored.target_screen == original.target_screen
        assert restored.params == original.params


# =============================================================================
# MobileAuthProvider
# =============================================================================

class TestMobileAuthProvider:
    def test_creation_with_defaults(self):
        map_ = MobileAuthProvider(id="map-1", type=MobileAuthType.GOOGLE)
        assert map_.scopes == []

    def test_creation_with_all_fields(self):
        map_ = MobileAuthProvider(
            id="map-2", type=MobileAuthType.APPLE,
            client_id_ref="client-123", client_secret_ref="secret-ref",
            redirect_uri="https://app/callback",
            scopes=["email", "name"],
        )
        assert map_.scopes == ["email", "name"]
        assert map_.redirect_uri == "https://app/callback"

    def test_to_dict_masks_secret(self):
        map_ = MobileAuthProvider(
            id="map-3", type=MobileAuthType.FACEBOOK,
            client_secret_ref="my_secret_key",
        )
        d = map_.to_dict()
        assert d["client_secret_ref"] == "****"
        assert d["type"] == "facebook"

    def test_from_dict(self):
        data = {
            "id": "map-4", "type": "apple",
            "client_id_ref": "ref", "redirect_uri": "https://cb",
            "scopes": ["openid"],
        }
        map_ = MobileAuthProvider.from_dict(data)
        assert map_.type == MobileAuthType.APPLE
        assert "openid" in map_.scopes

    def test_validation_error_empty_id(self):
        with pytest.raises(Exception):
            MobileAuthProvider(id="", type=MobileAuthType.GOOGLE)

    def test_roundtrip(self):
        original = MobileAuthProvider(
            id="rt-map", type=MobileAuthType.GOOGLE,
            redirect_uri="https://rt", scopes=["profile"],
        )
        d = original.to_dict()
        restored = MobileAuthProvider.from_dict(d)
        assert restored.id == original.id
        assert restored.type == original.type
        assert restored.redirect_uri == original.redirect_uri


# =============================================================================
# OTAUpdateConfig
# =============================================================================

class TestOTAUpdateConfig:
    def test_creation_with_defaults(self):
        ota = OTAUpdateConfig(id="ota-1", platform=OTAPlatform.IOS)
        assert ota.forced_update is False
        assert ota.rollout_percentage == 100

    def test_creation_with_all_fields(self):
        ota = OTAUpdateConfig(
            id="ota-2", platform=OTAPlatform.ANDROID,
            forced_update=True, minimum_version="2.0.0",
            release_notes_url="https://notes.com",
            download_url="https://dl.com/app.apk",
            rollout_percentage=50,
        )
        assert ota.forced_update is True
        assert ota.rollout_percentage == 50

    def test_to_dict(self):
        ota = OTAUpdateConfig(id="ota-3", platform=OTAPlatform.BOTH, forced_update=True)
        d = ota.to_dict()
        assert d["platform"] == "both"
        assert d["forced_update"] is True

    def test_from_dict(self):
        data = {
            "id": "ota-4", "platform": "ios", "forced_update": False,
            "minimum_version": "1.5.0", "rollout_percentage": 25,
        }
        ota = OTAUpdateConfig.from_dict(data)
        assert ota.platform == OTAPlatform.IOS
        assert ota.rollout_percentage == 25

    def test_validation_error_empty_id(self):
        with pytest.raises(Exception):
            OTAUpdateConfig(id="", platform=OTAPlatform.IOS)

    def test_validation_error_rollout_zero(self):
        with pytest.raises(Exception):
            OTAUpdateConfig(id="ota-5", platform=OTAPlatform.IOS, rollout_percentage=0)

    def test_validation_error_rollout_over_100(self):
        with pytest.raises(Exception):
            OTAUpdateConfig(id="ota-6", platform=OTAPlatform.IOS, rollout_percentage=101)

    def test_roundtrip(self):
        original = OTAUpdateConfig(
            id="rt-ota", platform=OTAPlatform.ANDROID,
            forced_update=True, rollout_percentage=75,
        )
        d = original.to_dict()
        restored = OTAUpdateConfig.from_dict(d)
        assert restored.id == original.id
        assert restored.platform == original.platform
        assert restored.forced_update == original.forced_update
        assert restored.rollout_percentage == original.rollout_percentage


# =============================================================================
# DeviceRegistration
# =============================================================================

class TestDeviceRegistration:
    def test_creation_with_defaults(self):
        dr = DeviceRegistration(id="dr-1", platform=DevicePlatform.IOS)
        assert dr.push_enabled is True
        assert dr.last_seen is not None

    def test_creation_with_all_fields(self):
        dr = DeviceRegistration(
            id="dr-2", platform=DevicePlatform.ANDROID,
            device_token="fcm_token_123", push_enabled=False,
            deep_link_handler="handleDeepLink",
            os_version="Android 14", app_version="3.0.0",
        )
        assert dr.device_token == "fcm_token_123"
        assert dr.push_enabled is False

    def test_to_dict(self):
        dr = DeviceRegistration(id="dr-3", platform=DevicePlatform.IOS, device_token="token")
        d = dr.to_dict()
        assert d["platform"] == "ios"
        assert d["device_token"] == "token"

    def test_from_dict(self):
        data = {
            "id": "dr-4", "platform": "android",
            "device_token": "tok", "push_enabled": False,
            "os_version": "Android 13", "app_version": "2.1.0",
        }
        dr = DeviceRegistration.from_dict(data)
        assert dr.platform == DevicePlatform.ANDROID
        assert dr.push_enabled is False
        assert dr.os_version == "Android 13"

    def test_validation_error_empty_id(self):
        with pytest.raises(Exception):
            DeviceRegistration(id="", platform=DevicePlatform.IOS)

    def test_roundtrip(self):
        original = DeviceRegistration(
            id="rt-dr", platform=DevicePlatform.IOS,
            device_token="rt-token", push_enabled=True,
            app_version="1.0.0",
        )
        d = original.to_dict()
        restored = DeviceRegistration.from_dict(d)
        assert restored.id == original.id
        assert restored.platform == original.platform
        assert restored.push_enabled == original.push_enabled
