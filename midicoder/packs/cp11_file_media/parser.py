# coding: utf-8
"""
File Storage Parser - Parse MIR metadata thành FileStorageCollection.

Module này chứa FileStorageParser để parse storage config từ MIR metadata
và từ YAML string thành FileStorageCollection.

Hỗ trợ:
- Parse profiles, policies, transforms
- Parse CDN config (AWS CloudFront)
- Parse PresignedURLPolicy

Author: Midicoder Team
Version: 1.1.0
"""

from __future__ import annotations

from typing import Any

import yaml

from midicoder.packs.cp11_file_media.models import (
    StorageProfile,
    UploadPolicy,
    MediaTransform,
    CDNIntegration,
    PresignedURLPolicy,
    FileStorageCollection,
    StorageBackend,
    TransformType,
    _BACKEND_MAP,
    _TRANSFORM_MAP,
)


class FileStorageParser:
    """
    Parser để convert MIR metadata và YAML string thành FileStorageCollection.

    Support:
    - Parse từ MIR metadata (dict)
    - Parse từ YAML string
    - Validation và error throwing
    - Parse CDN config (CloudFront)
    - Parse PresignedURLPolicy
    """

    def parse(self, raw: str) -> FileStorageCollection:
        """
        Parse YAML string thành FileStorageCollection.

        Args:
            raw: YAML string chứa storage profiles, policies, transforms,
                 cdn_config, presigned_policy

        Returns:
            FileStorageCollection đầy đủ

        Raises:
            MidicoderError: Nếu YAML không hợp lệ (MDC-CP11-007)
        """
        from midicoder.errors import ErrorCode, MidicoderErrorManager as EM

        try:
            data = yaml.safe_load(raw)
        except yaml.YAMLError as e:
            EM.raise_error(
                ErrorCode.CP11_DSL_PARSE_ERROR,
                detail=f"Parse YAML thất bại: {e}",
            )

        if not isinstance(data, dict):
            EM.raise_error(
                ErrorCode.CP11_DSL_PARSE_ERROR,
                detail="YAML phải là dict",
            )

        return self.parse_from_metadata(data)

    def parse_from_metadata(self, metadata: dict[str, Any]) -> FileStorageCollection:
        """
        Parse storage config từ MIR metadata.

        Args:
            metadata: Dict chứa profiles, policies, transforms, cdn_config, presigned_policy

        Returns:
            FileStorageCollection đầy đủ
        """
        collection = FileStorageCollection()

        # Parse profiles
        for profile_data in metadata.get("profiles", []):
            try:
                collection.add_profile(self._parse_profile(profile_data))
            except Exception:
                continue

        # Parse policies
        for policy_data in metadata.get("policies", []):
            try:
                collection.add_policy(self._parse_policy(policy_data))
            except Exception:
                continue

        # Parse transforms
        for transform_data in metadata.get("transforms", []):
            try:
                collection.add_transform(self._parse_transform(transform_data))
            except Exception:
                continue

        # Parse CDN config (CloudFront)
        cdn_data = metadata.get("cdn_config")
        if cdn_data and isinstance(cdn_data, dict):
            try:
                collection.set_cdn_config(self._parse_cdn_config(cdn_data))
            except Exception:
                pass

        # Parse presigned URL policy
        presigned_data = metadata.get("presigned_policy")
        if presigned_data and isinstance(presigned_data, dict):
            try:
                collection.presigned_policy = self._parse_presigned_policy(presigned_data)
            except Exception:
                pass

        return collection

    def _parse_profile(self, data: dict[str, Any]) -> StorageProfile:
        """Parse một storage profile."""
        from midicoder.errors import ErrorCode, MidicoderErrorManager as EM

        profile_name = data.get("name", "")
        if not profile_name:
            EM.raise_error(
                ErrorCode.CP11_EMPTY_PROFILE_NAME,
                detail="Profile name không được để trống",
            )

        backend_str = data.get("backend_type", "s3")
        backend = _BACKEND_MAP.get(backend_str)
        if backend is None:
            EM.raise_error(
                ErrorCode.CP11_INVALID_BACKEND_TYPE,
                profile_name=profile_name,
                backend_type=backend_str,
            )

        return StorageProfile(
            name=profile_name,
            backend_type=backend,
            bucket=data.get("bucket"),
            region=data.get("region", "us-east-1"),
            endpoint_url=data.get("endpoint_url"),
            access_key=data.get("access_key"),
            secret_key=data.get("secret_key"),
            tenant_isolation=data.get("tenant_isolation", True),
            description=data.get("description", ""),
        )

    def _parse_policy(self, data: dict[str, Any]) -> UploadPolicy:
        """Parse một upload policy."""
        return UploadPolicy(
            name=data.get("name", ""),
            allowed_content_types=data.get("allowed_content_types", []),
            max_file_size=data.get("max_file_size", 10 * 1024 * 1024),
            allowed_extensions=data.get("allowed_extensions", []),
            default_storage_profile=data.get("default_storage_profile", ""),
            description=data.get("description", ""),
        )

    def _parse_transform(self, data: dict[str, Any]) -> MediaTransform:
        """Parse một media transform."""
        transform_str = data.get("transform_type", "resize")
        transform_type = _TRANSFORM_MAP.get(transform_str, TransformType.RESIZE)
        return MediaTransform(
            name=data.get("name", ""),
            transform_type=transform_type,
            width=data.get("width"),
            height=data.get("height"),
            format=data.get("format"),
            quality=data.get("quality", 80),
            description=data.get("description", ""),
        )

    def _parse_cdn_config(self, data: dict[str, Any]) -> CDNIntegration:
        """Parse CDN config (AWS CloudFront)."""
        return CDNIntegration(
            name=data.get("name", "default"),
            distribution_id=data.get("distribution_id"),
            domain=data.get("domain"),
            origin_bucket=data.get("origin_bucket"),
            origin_access_identity=data.get("origin_access_identity"),
            signed_url=data.get("signed_url", False),
            default_ttl=data.get("default_ttl", 86400),
            max_ttl=data.get("max_ttl", 31536000),
            behavior_path=data.get("behavior_path", "/*"),
            description=data.get("description", ""),
        )

    def _parse_presigned_policy(self, data: dict[str, Any]) -> PresignedURLPolicy:
        """Parse presigned URL policy."""
        return PresignedURLPolicy(
            name=data.get("name", "default"),
            expiration=data.get("expiration", 3600),
            max_expiration=data.get("max_expiration", 604800),
            allowed_operations=data.get("allowed_operations", ["get_object"]),
            use_cdn_signed_url=data.get("use_cdn_signed_url", False),
        )
