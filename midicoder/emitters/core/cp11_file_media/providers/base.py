# coding: utf-8
"""
Mô-đun Abstract Base Class cho storage providers của CP11 File Storage.

Định nghĩa interface chung mà mọi storage provider (S3, Local, ...)
phải implement — đảm bảo tính nhất quán khi đổi backend.

Scope: chỉ AWS (S3) + Local (filesystem). Không hỗ trợ GCP/Azure.
"""

from __future__ import annotations

import abc
from typing import Any


class StorageProvider(abc.ABC):
    """
    Abstract Base Class cho tất cả storage providers.

    Mọi provider phải implement các phương thức:
        - upload: Upload dữ liệu bytes lên storage backend
        - download: Tải xuống dữ liệu từ storage backend
        - delete: Xóa file khỏi storage backend
        - get_presigned_url: Tạo URL truy cập tạm thời cho file
        - list_files: Liệt kê files trong storage backend

    Ví dụ:
        provider = S3Provider(bucket="my-bucket", region="us-east-1")
        result = provider.upload(b"content", "files/hello.txt", "text/plain")
        print(result["url"])  # URL đã upload
    """

    @abc.abstractmethod
    def upload(
        self,
        file_bytes: bytes,
        key: str,
        content_type: str,
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Upload dữ liệu bytes lên storage backend.

        Args:
            file_bytes: Nội dung file dưới dạng bytes
            key: Khóa (path) của file trong storage backend
            content_type: MIME type của file (ví dụ: "text/plain", "image/png")
            tenant_id: Tenant identifier cho tenant isolation (KPI-029)

        Returns:
            Dict chứa thông tin file đã upload:
                - key (str): Khóa thực tế trong storage
                - url (str): URL truy cập file
                - size (int): Kích thước file (bytes)

        Raises:
            MidicoderError: Nếu upload thất bại hoặc vi phạm policy
        """
        ...

    @abc.abstractmethod
    def download(
        self,
        key: str,
        tenant_id: str | None = None,
    ) -> bytes:
        """
        Tải xuống dữ liệu file từ storage backend.

        Args:
            key: Khóa (path) của file trong storage backend
            tenant_id: Tenant identifier cho tenant isolation (KPI-029)

        Returns:
            Nội dung file dưới dạng bytes

        Raises:
            MidicoderError: Nếu file không tồn tại hoặc download thất bại
        """
        ...

    @abc.abstractmethod
    def delete(
        self,
        key: str,
        tenant_id: str | None = None,
    ) -> bool:
        """
        Xóa file khỏi storage backend.

        Args:
            key: Khóa (path) của file cần xóa
            tenant_id: Tenant identifier cho tenant isolation (KPI-029)

        Returns:
            True nếu xóa thành công, False nếu file không tồn tại

        Raises:
            MidicoderError: Nếu xóa thất bại do lỗi hệ thống
        """
        ...

    @abc.abstractmethod
    def get_presigned_url(
        self,
        key: str,
        expiration: int = 3600,
        tenant_id: str | None = None,
    ) -> str:
        """
        Tạo URL truy cập tạm thời (presigned) cho file.

        Args:
            key: Khóa (path) của file trong storage backend
            expiration: Thời gian sống của URL (giây), mặc định 3600s = 1 giờ
            tenant_id: Tenant identifier cho tenant isolation (KPI-029)

        Returns:
            URL string để truy cập file trong khoảng thời gian expiration

        Raises:
            MidicoderError: Nếu tạo URL thất bại
        """
        ...

    @abc.abstractmethod
    def list_files(
        self,
        prefix: str,
        tenant_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Liệt kê các files trong storage backend theo prefix.

        Args:
            prefix: Tiền tố để lọc files (ví dụ: "uploads/2024/")
            tenant_id: Tenant identifier cho tenant isolation (KPI-029)

        Returns:
            Danh sách dict, mỗi dict chứa:
                - key (str): Khóa của file
                - size (int): Kích thước file (bytes)
                - last_modified (str): Thời gian sửa đổi cuối cùng (ISO 8601)

        Raises:
            MidicoderError: Nếu liệt kê thất bại
        """
        ...
