# coding: utf-8
"""
Mô-đun providers cho CP11 File Storage.

Cung cấp:
- StorageProvider: ABC interface cho storage operations
- S3Provider: Implementation cho AWS S3 / MinIO
- LocalProvider: Implementation cho local filesystem
"""

from midicoder.emitters.core.file_storage.providers.base import StorageProvider
from midicoder.emitters.core.file_storage.providers.s3 import S3Provider
from midicoder.emitters.core.file_storage.providers.local import LocalProvider

__all__ = [
    "StorageProvider",
    "S3Provider",
    "LocalProvider",
]
