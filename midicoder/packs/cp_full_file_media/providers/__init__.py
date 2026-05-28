# coding: utf-8
"""
Mô-đun providers cho CP11 File Storage.

Cung cấp:
- StorageProvider: ABC interface cho storage operations
- S3Provider: Implementation cho AWS S3 / MinIO
- LocalProvider: Implementation cho local filesystem
"""

from midicoder.packs.cp_full_file_media.providers.base import StorageProvider
from midicoder.packs.cp_full_file_media.providers.s3 import S3Provider
from midicoder.packs.cp_full_file_media.providers.local import LocalProvider

__all__ = [
    "StorageProvider",
    "S3Provider",
    "LocalProvider",
]
