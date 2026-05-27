# coding: utf-8
"""
Mô-đun Local filesystem storage provider cho CP11 File Storage.

Implement StorageProvider bằng local disk — dùng pathlib.Path cho
tất cả file operations, tự động tạo thư mục khi cần.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM
from midicoder.packs.cp11_file_media.providers.base import StorageProvider

logger = logging.getLogger(__name__)


class LocalProvider(StorageProvider):
    """
    Provider implement StorageProvider bằng local filesystem.

    Sử dụng pathlib.Path cho tất cả file operations:
        - Tự động tạo thư mục cha khi upload
        - Resolve path để tránh path traversal
        - Trả về file:// URL cho presigned URL

    Ví dụ:
        provider = LocalProvider(base_path="/data/storage")
        result = provider.upload(b"hello", "files/hello.txt", "text/plain")
        content = provider.download("files/hello.txt")
    """

    def __init__(
        self,
        base_path: str,
        tenant_prefix: str | None = None,
    ) -> None:
        """
        Khởi tạo LocalProvider.

        Args:
            base_path: Thư mục gốc để lưu trữ files (sẽ tạo nếu chưa tồn tại)
            tenant_prefix: Tiền tố tenant subdirectory cho tenant isolation (KPI-029)
        """
        self._base_path = Path(os.path.abspath(base_path))
        self._tenant_prefix = tenant_prefix.rstrip("/") + "/" if tenant_prefix else ""

        # Tạo thư mục base nếu chưa tồn tại
        self._base_path.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, key: str, tenant_id: str | None = None) -> Path:
        """
        Resolve key thành absolute path trên local filesystem.

        Thêm tenant prefix nếu có, rồi resolve để ngăn chặn path traversal
        (ví dụ: key chứa "../" sẽ bị giới hạn trong base_path).

        Args:
            key: Khóa (path) của file
            tenant_id: Tenant identifier cho tenant isolation (KPI-029)

        Returns:
            Path absolute dẫn đến file trong base_path

        Raises:
            MidicoderError: Nếu resolved path thoát khỏi base_path (path traversal)
        """
        # Thêm tenant prefix
        full_key = self._build_key(key, tenant_id)

        # Resolve để xử lý ../ và relative path
        resolved = (self._base_path / full_key).resolve()

        # Kiểm tra path traversal: resolved path phải nằm trong base_path
        try:
            resolved.relative_to(self._base_path.resolve())
        except ValueError:
            EM.raise_error(
                ErrorCode.CP11_INVALID_CONTENT_TYPE,
                key=key,
                detail=f"Path traversal bị chặn: resolved path {resolved} thoát khỏi base_path {self._base_path}",
            )

        return resolved

    def _build_key(self, key: str, tenant_id: str | None = None) -> str:
        """
        Xây dựng key thực tế với tenant prefix (KPI-029).

        Args:
            key: Key gốc của file
            tenant_id: Tenant identifier

        Returns:
            Key hoàn chỉnh với tenant prefix (nếu có)
        """
        if self._tenant_prefix:
            return f"{self._tenant_prefix}{key}"
        return key

    def upload(
        self,
        file_bytes: bytes,
        key: str,
        content_type: str,
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Ghi dữ liệu bytes vào file trên local disk.

        Tự động tạo các thư mục cha nếu chưa tồn tại.

        Args:
            file_bytes: Nội dung file dưới dạng bytes
            key: Khóa (path) của file trong base_path
            content_type: MIME type của file (lưu cho metadata, không enforce)
            tenant_id: Tenant identifier cho tenant isolation (KPI-029)

        Returns:
            Dict chứa:
                - key (str): Key thực tế của file
                - url (str): file:// URL của file
                - size (int): Kích thước file (bytes)

        Raises:
            MidicoderError: Nếu content_type rỗng hoặc write thất bại
        """
        # Validate content_type
        if not content_type or not content_type.strip():
            EM.raise_error(
                ErrorCode.CP11_INVALID_CONTENT_TYPE,
                key=key,
                detail="Content type không được để trống",
            )

        full_key = self._build_key(key, tenant_id)
        file_path = self._resolve_path(key, tenant_id)

        try:
            # Tạo thư mục cha nếu chưa tồn tại
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Ghi bytes vào file
            file_path.write_bytes(file_bytes)

            url = f"file://{quote(str(file_path))}"

            return {
                "key": full_key,
                "url": url,
                "size": len(file_bytes),
            }

        except OSError as e:
            EM.raise_error(
                ErrorCode.CP11_PROVIDER_NOT_FOUND,
                provider="local",
                operation="upload",
                key=full_key,
                path=str(file_path),
                detail=f"Không thể ghi file: {e}",
            )

    def download(
        self,
        key: str,
        tenant_id: str | None = None,
    ) -> bytes:
        """
        Đọc nội dung file từ local disk.

        Args:
            key: Khóa (path) của file trong base_path
            tenant_id: Tenant identifier cho tenant isolation (KPI-029)

        Returns:
            Nội dung file dưới dạng bytes

        Raises:
            MidicoderError: Nếu file không tồn tại hoặc đọc thất bại
        """
        file_path = self._resolve_path(key, tenant_id)

        if not file_path.exists():
            EM.raise_error(
                ErrorCode.CP11_PROVIDER_NOT_FOUND,
                provider="local",
                operation="download",
                key=key,
                path=str(file_path),
                detail=f"File không tồn tại: {file_path}",
            )

        if not file_path.is_file():
            EM.raise_error(
                ErrorCode.CP11_PROVIDER_NOT_FOUND,
                provider="local",
                operation="download",
                key=key,
                path=str(file_path),
                detail=f"Path không phải là file: {file_path}",
            )

        try:
            return file_path.read_bytes()

        except OSError as e:
            EM.raise_error(
                ErrorCode.CP11_PROVIDER_NOT_FOUND,
                provider="local",
                operation="download",
                key=key,
                path=str(file_path),
                detail=f"Không thể đọc file: {e}",
            )

    def delete(
        self,
        key: str,
        tenant_id: str | None = None,
    ) -> bool:
        """
        Xóa file khỏi local disk.

        Args:
            key: Khóa (path) của file cần xóa
            tenant_id: Tenant identifier cho tenant isolation (KPI-029)

        Returns:
            True nếu xóa thành công, False nếu file không tồn tại

        Raises:
            MidicoderError: Nếu xóa thất bại do lỗi hệ thống
        """
        file_path = self._resolve_path(key, tenant_id)

        if not file_path.exists():
            return False

        if not file_path.is_file():
            EM.raise_error(
                ErrorCode.CP11_PROVIDER_NOT_FOUND,
                provider="local",
                operation="delete",
                key=key,
                path=str(file_path),
                detail=f"Path không phải là file: {file_path}",
            )

        try:
            file_path.unlink()
            return True

        except OSError as e:
            EM.raise_error(
                ErrorCode.CP11_PROVIDER_NOT_FOUND,
                provider="local",
                operation="delete",
                key=key,
                path=str(file_path),
                detail=f"Không thể xóa file: {e}",
            )

    def get_presigned_url(
        self,
        key: str,
        expiration: int = 3600,
        tenant_id: str | None = None,
    ) -> str:
        """
        Trả về file:// URL cho file trên local disk.

        Lưu ý: URL file:// không có cơ chế expiration như presigned URL
        của S3 — tham số expiration được lưu để tương thích interface
        nhưng không enforce trên local filesystem.

        Args:
            key: Khóa (path) của file trong base_path
            expiration: Thời gian sống (giây) — không enforce trên local
            tenant_id: Tenant identifier cho tenant isolation (KPI-029)

        Returns:
            file:// URL của file (đã URL-encode path)

        Raises:
            MidicoderError: Nếu file không tồn tại
        """
        file_path = self._resolve_path(key, tenant_id)

        if not file_path.exists():
            EM.raise_error(
                ErrorCode.CP11_PROVIDER_NOT_FOUND,
                provider="local",
                operation="get_presigned_url",
                key=key,
                path=str(file_path),
                detail=f"File không tồn tại: {file_path}",
            )

        return f"file://{quote(str(file_path))}"

    def list_files(
        self,
        prefix: str,
        tenant_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Liệt kê các files trong local disk theo prefix.

        Walk từ thư mục prefix và thu thập thông tin cho từng file.
        Không trả về directory, chỉ trả về regular files.

        Args:
            prefix: Tiền tố path để lọc files (ví dụ: "uploads/2024/")
            tenant_id: Tenant identifier cho tenant isolation (KPI-029)

        Returns:
            Danh sách dict, mỗi dict chứa:
                - key (str): Key của file (tương đối với base_path)
                - size (int): Kích thước file (bytes)
                - last_modified (str): Thời gian sửa đổi (ISO 8601 UTC)

        Raises:
            MidicoderError: Nếu prefix directory không tồn tại hoặc walk thất bại
        """
        full_prefix = self._build_key(prefix, tenant_id)
        prefix_path = (self._base_path / full_prefix).resolve()

        # Kiểm tra path traversal
        try:
            prefix_path.relative_to(self._base_path.resolve())
        except ValueError:
            EM.raise_error(
                ErrorCode.CP11_INVALID_CONTENT_TYPE,
                prefix=prefix,
                detail=f"Path traversal bị chặn: prefix {prefix_path} thoát khỏi base_path",
            )

        if not prefix_path.exists():
            return []

        files: list[dict[str, Any]] = []

        try:
            # Nếu prefix là file thì trả về luôn
            if prefix_path.is_file():
                stat = prefix_path.stat()
                last_modified = datetime.fromtimestamp(
                    stat.st_mtime, tz=timezone.utc
                ).strftime("%Y-%m-%dT%H:%M:%SZ")

                relative = prefix_path.relative_to(self._base_path)
                display_key = str(relative).replace("\\", "/")
                if self._tenant_prefix and display_key.startswith(self._tenant_prefix):
                    display_key = display_key[len(self._tenant_prefix):]

                files.append({
                    "key": display_key,
                    "size": stat.st_size,
                    "last_modified": last_modified,
                })
                return files

            # Walk directory và thu thập files
            for file_path in prefix_path.rglob("*"):
                if not file_path.is_file():
                    continue

                stat = file_path.stat()
                last_modified = datetime.fromtimestamp(
                    stat.st_mtime, tz=timezone.utc
                ).strftime("%Y-%m-%dT%H:%M:%SZ")

                relative = file_path.relative_to(self._base_path)
                display_key = str(relative).replace("\\", "/")
                if self._tenant_prefix and display_key.startswith(self._tenant_prefix):
                    display_key = display_key[len(self._tenant_prefix):]

                files.append({
                    "key": display_key,
                    "size": stat.st_size,
                    "last_modified": last_modified,
                })

            return files

        except OSError as e:
            EM.raise_error(
                ErrorCode.CP11_PROVIDER_NOT_FOUND,
                provider="local",
                operation="list_files",
                prefix=str(prefix_path),
                detail=f"Không thể quét directory: {e}",
            )
