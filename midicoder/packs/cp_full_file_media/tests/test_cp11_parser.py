# coding: utf-8
"""
Test suite cho CP11 parser (FileStorageParser).

Test coverage cho:
- FileStorageParser.parse() từ YAML string
- FileStorageParser.parse_from_metadata() từ dict
- Error handling (MDC-CP11-007)

CP11: File Storage & Media Processing Generator
"""

import pytest

from midicoder.errors import ErrorCode, MidicoderError


class TestFileStorageParser:
    """Test FileStorageParser."""

    def test_parse_yaml_string(self):
        """Parse YAML string thành FileStorageCollection."""
        from midicoder.packs.cp_full_file_media.parser import FileStorageParser
        from midicoder.packs.cp_full_file_media.models import StorageBackend, TransformType

        yaml_str = """
profiles:
  - name: primary-s3
    backend_type: s3
    bucket: my-bucket
    region: us-east-1
policies:
  - name: images
    allowed_content_types: [image/jpeg, image/png]
    max_file_size: 10485760
    allowed_extensions: [jpg, jpeg, png]
transforms:
  - name: thumbnail-100
    transform_type: thumbnail
    width: 100
    height: 100
"""
        parser = FileStorageParser()
        collection = parser.parse(yaml_str)

        assert collection.total_count == 1
        assert collection.profiles[0].backend_type == StorageBackend.S3
        assert len(collection.policies) == 1
        assert len(collection.transforms) == 1
        assert collection.transforms[0].transform_type == TransformType.THUMBNAIL

    def test_parse_from_metadata(self):
        """Parse từ MIR metadata dict."""
        from midicoder.packs.cp_full_file_media.parser import FileStorageParser
        from midicoder.packs.cp_full_file_media.models import StorageBackend

        metadata = {
            "profiles": [
                {
                    "name": "local-dev",
                    "backend_type": "local",
                }
            ],
            "policies": [
                {
                    "name": "docs",
                    "allowed_content_types": ["application/pdf"],
                    "max_file_size": 5242880,
                    "allowed_extensions": ["pdf"],
                }
            ],
            "transforms": [],
        }

        parser = FileStorageParser()
        collection = parser.parse_from_metadata(metadata)

        assert collection.total_count == 1
        assert collection.profiles[0].backend_type == StorageBackend.LOCAL
        assert len(collection.policies) == 1

    def test_parse_empty_metadata(self):
        """Parse metadata rỗng → collection rỗng."""
        from midicoder.packs.cp_full_file_media.parser import FileStorageParser

        parser = FileStorageParser()
        collection = parser.parse_from_metadata({})

        assert collection.total_count == 0
        assert len(collection.policies) == 0
        assert len(collection.transforms) == 0

    def test_parse_invalid_yaml_raises_error(self):
        """YAML không hợp lệ → MDC-CP11-007."""
        from midicoder.packs.cp_full_file_media.parser import FileStorageParser

        parser = FileStorageParser()
        with pytest.raises(MidicoderError) as exc_info:
            parser.parse("{{invalid yaml")
        assert exc_info.value.code == ErrorCode.MDC-F35_DSL_PARSE_ERROR

    def test_parse_yaml_not_dict_raises_error(self):
        """YAML không phải dict → MDC-CP11-007."""
        from midicoder.packs.cp_full_file_media.parser import FileStorageParser

        parser = FileStorageParser()
        with pytest.raises(MidicoderError) as exc_info:
            parser.parse("- just a list")
        assert exc_info.value.code == ErrorCode.MDC-F35_DSL_PARSE_ERROR

    def test_parse_skips_invalid_profiles(self):
        """Profile invalid được skip (không throw)."""
        from midicoder.packs.cp_full_file_media.parser import FileStorageParser

        metadata = {
            "profiles": [
                {"name": "valid", "backend_type": "s3", "bucket": "b1"},
                {"name": "", "backend_type": "s3", "bucket": "b2"},  # invalid
            ],
            "policies": [],
            "transforms": [],
        }

        parser = FileStorageParser()
        collection = parser.parse_from_metadata(metadata)

        # Chỉ có 1 profile valid
        assert collection.total_count == 1

    def test_parse_full_collection(self):
        """Parse đầy đủ profiles, policies, transforms."""
        from midicoder.packs.cp_full_file_media.parser import FileStorageParser

        yaml_str = """
profiles:
  - name: s3-primary
    backend_type: s3
    bucket: primary-bucket
    region: us-east-1
    tenant_isolation: true
  - name: s3-media
    backend_type: s3
    bucket: media-bucket
    region: ap-southeast-1
policies:
  - name: images
    allowed_content_types: [image/jpeg, image/png, image/webp]
    max_file_size: 10485760
    allowed_extensions: [jpg, jpeg, png, webp]
    default_storage_profile: s3-media
  - name: videos
    allowed_content_types: [video/mp4, video/webm]
    max_file_size: 104857600
    allowed_extensions: [mp4, webm]
    default_storage_profile: s3-media
transforms:
  - name: thumb-small
    transform_type: thumbnail
    width: 100
    height: 100
    quality: 80
  - name: resize-large
    transform_type: resize
    width: 1920
    height: 1080
    quality: 90
  - name: transcode-mp4
    transform_type: transcode
    format: mp4
    quality: 85
"""
        parser = FileStorageParser()
        collection = parser.parse(yaml_str)

        assert collection.total_count == 2
        assert len(collection.policies) == 2
        assert len(collection.transforms) == 3

        # Validate policy has validate_upload method
        policy = collection.policies[0]
        assert policy.name == "images"
        assert "image/jpeg" in policy.allowed_content_types
