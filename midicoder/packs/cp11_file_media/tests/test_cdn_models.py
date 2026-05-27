# coding: utf-8
"""
Test suite cho CP11 CDN Integration và PresignedURLPolicy models.

Kiểm tra:
- CDNIntegration: validation, to_dict/from_dict, get_cdn_url
- PresignedURLPolicy: validation, to_dict/from_dict
"""

import pytest
from midicoder.packs.cp11_file_media.models import (
    CDNIntegration,
    PresignedURLPolicy,
    FileStorageCollection,
)
from midicoder.errors import MidicoderError


class TestCDNIntegration:
    """Test CDNIntegration dataclass."""

    def test_default_values(self):
        cdn = CDNIntegration()
        assert cdn.name == "default"
        assert cdn.distribution_id is None
        assert cdn.domain is None
        assert cdn.signed_url is False
        assert cdn.default_ttl == 86400
        assert cdn.max_ttl == 31536000
        assert cdn.behavior_path == "/*"

    def test_full_config(self):
        cdn = CDNIntegration(
            name="prod",
            distribution_id="E1234567890",
            domain="d1234.cloudfront.net",
            origin_bucket="my-app-uploads",
            origin_access_identity="origin-access-identity/s3/cloudfront/E1234567890",
            signed_url=True,
            default_ttl=3600,
            max_ttl=86400,
        )
        assert cdn.name == "prod"
        assert cdn.distribution_id == "E1234567890"
        assert cdn.signed_url is True

    def test_empty_distribution_id_raises(self):
        with pytest.raises(MidicoderError):
            CDNIntegration(distribution_id="   ")

    def test_empty_domain_raises(self):
        with pytest.raises(MidicoderError):
            CDNIntegration(domain="   ")

    def test_negative_default_ttl_raises(self):
        with pytest.raises(MidicoderError):
            CDNIntegration(default_ttl=-1)

    def test_negative_max_ttl_raises(self):
        with pytest.raises(MidicoderError):
            CDNIntegration(max_ttl=-1)

    def test_default_ttl_greater_than_max_raises(self):
        with pytest.raises(MidicoderError):
            CDNIntegration(default_ttl=100000, max_ttl=1000)

    def test_get_cdn_url_with_domain(self):
        cdn = CDNIntegration(domain="d1234.cloudfront.net")
        assert cdn.get_cdn_url("uploads/doc.pdf") == "https://d1234.cloudfront.net/uploads/doc.pdf"

    def test_get_cdn_url_without_domain(self):
        cdn = CDNIntegration()
        assert cdn.get_cdn_url("uploads/doc.pdf") == ""

    def test_get_cdn_url_strips_leading_slash(self):
        cdn = CDNIntegration(domain="d1234.cloudfront.net")
        assert cdn.get_cdn_url("/uploads/doc.pdf") == "https://d1234.cloudfront.net/uploads/doc.pdf"

    def test_to_dict(self):
        cdn = CDNIntegration(
            name="prod",
            distribution_id="E1234567890",
            domain="d1234.cloudfront.net",
            signed_url=True,
        )
        d = cdn.to_dict()
        assert d["name"] == "prod"
        assert d["distribution_id"] == "E1234567890"
        assert d["domain"] == "d1234.cloudfront.net"
        assert d["signed_url"] is True
        assert d["default_ttl"] == 86400

    def test_from_dict(self):
        d = {
            "name": "test",
            "distribution_id": "E123",
            "domain": "d1234.cloudfront.net",
            "origin_bucket": "my-bucket",
            "signed_url": True,
            "default_ttl": 7200,
            "max_ttl": 86400,
            "behavior_path": "/assets/*",
        }
        cdn = CDNIntegration.from_dict(d)
        assert cdn.name == "test"
        assert cdn.distribution_id == "E123"
        assert cdn.domain == "d1234.cloudfront.net"
        assert cdn.signed_url is True
        assert cdn.default_ttl == 7200
        assert cdn.behavior_path == "/assets/*"

    def test_roundtrip(self):
        cdn = CDNIntegration(
            name="rt",
            distribution_id="E123",
            domain="d1234.cloudfront.net",
            origin_bucket="bucket",
            signed_url=True,
        )
        restored = CDNIntegration.from_dict(cdn.to_dict())
        assert restored.name == cdn.name
        assert restored.distribution_id == cdn.distribution_id
        assert restored.domain == cdn.domain
        assert restored.signed_url == cdn.signed_url


class TestPresignedURLPolicy:
    """Test PresignedURLPolicy dataclass."""

    def test_default_values(self):
        p = PresignedURLPolicy()
        assert p.name == "default"
        assert p.expiration == 3600
        assert p.max_expiration == 604800
        assert p.allowed_operations == ["get_object"]
        assert p.use_cdn_signed_url is False

    def test_custom_values(self):
        p = PresignedURLPolicy(
            name="long_lived",
            expiration=7200,
            max_expiration=86400,
            allowed_operations=["get_object", "put_object"],
            use_cdn_signed_url=True,
        )
        assert p.expiration == 7200
        assert p.use_cdn_signed_url is True

    def test_zero_expiration_raises(self):
        with pytest.raises(MidicoderError):
            PresignedURLPolicy(expiration=0)

    def test_negative_expiration_raises(self):
        with pytest.raises(MidicoderError):
            PresignedURLPolicy(expiration=-100)

    def test_expiration_greater_than_max_raises(self):
        with pytest.raises(MidicoderError):
            PresignedURLPolicy(expiration=999999, max_expiration=100)

    def test_empty_allowed_operations_raises(self):
        with pytest.raises(MidicoderError):
            PresignedURLPolicy(allowed_operations=[])

    def test_to_dict(self):
        p = PresignedURLPolicy(
            name="cdn",
            expiration=1800,
            use_cdn_signed_url=True,
        )
        d = p.to_dict()
        assert d["name"] == "cdn"
        assert d["expiration"] == 1800
        assert d["use_cdn_signed_url"] is True

    def test_from_dict(self):
        d = {
            "name": "test",
            "expiration": 7200,
            "max_expiration": 172800,
            "allowed_operations": ["get_object", "put_object"],
            "use_cdn_signed_url": True,
        }
        p = PresignedURLPolicy.from_dict(d)
        assert p.name == "test"
        assert p.expiration == 7200
        assert p.max_expiration == 172800
        assert "put_object" in p.allowed_operations

    def test_roundtrip(self):
        p = PresignedURLPolicy(
            name="rt",
            expiration=5400,
            use_cdn_signed_url=True,
        )
        restored = PresignedURLPolicy.from_dict(p.to_dict())
        assert restored.name == p.name
        assert restored.expiration == p.expiration
        assert restored.use_cdn_signed_url == p.use_cdn_signed_url


class TestFileStorageCollectionWithCDN:
    """Test FileStorageCollection with CDN config."""

    def test_set_and_get_cdn_config(self):
        coll = FileStorageCollection()
        cdn = CDNIntegration(domain="d1234.cloudfront.net")
        coll.set_cdn_config(cdn)
        assert coll.cdn_config is cdn

    def test_has_cdn_true(self):
        coll = FileStorageCollection()
        coll.set_cdn_config(CDNIntegration(domain="d1234.cloudfront.net"))
        assert coll.has_cdn() is True

    def test_has_cdn_false_no_config(self):
        coll = FileStorageCollection()
        assert coll.has_cdn() is False

    def test_has_cdn_false_no_domain(self):
        coll = FileStorageCollection()
        coll.set_cdn_config(CDNIntegration())
        assert coll.has_cdn() is False

    def test_to_dict_includes_cdn(self):
        coll = FileStorageCollection()
        coll.set_cdn_config(CDNIntegration(domain="d1234.cloudfront.net", signed_url=True))
        coll.presigned_policy = PresignedURLPolicy(name="cdn", use_cdn_signed_url=True)
        d = coll.to_dict()
        assert "cdn_config" in d
        assert d["cdn_config"]["domain"] == "d1234.cloudfront.net"
        assert "presigned_policy" in d
        assert d["presigned_policy"]["use_cdn_signed_url"] is True

    def test_to_dict_excludes_none_cdn(self):
        coll = FileStorageCollection()
        d = coll.to_dict()
        assert "cdn_config" not in d
        assert "presigned_policy" not in d

    def test_from_dict_with_cdn(self):
        d = {
            "profiles": [],
            "policies": [],
            "transforms": [],
            "cdn_config": {
                "name": "prod",
                "distribution_id": "E123",
                "domain": "d1234.cloudfront.net",
                "signed_url": True,
            },
            "presigned_policy": {
                "name": "cdn",
                "expiration": 7200,
                "use_cdn_signed_url": True,
            },
        }
        coll = FileStorageCollection.from_dict(d)
        assert coll.cdn_config is not None
        assert coll.cdn_config.domain == "d1234.cloudfront.net"
        assert coll.presigned_policy is not None
        assert coll.presigned_policy.use_cdn_signed_url is True
