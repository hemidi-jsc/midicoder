# coding: utf-8
"""
Mô-đun S3 storage provider cho CP11 File Storage.

Implement StorageProvider bằng AWS S3 (hoặc MinIO/S3-compatible) qua boto3.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

# Lazy import — boto3 là runtime dependency của generated code, không phải của Midicoder
# import boto3
# from boto3.s3.transfer import TransferConfig
# from botocore.exceptions import ClientError, NoCredentialsError

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM
from midicoder.emitters.core.file_storage.providers.base import StorageProvider

logger = logging.getLogger(__name__)


class S3Provider(StorageProvider):
    """
    Provider implement StorageProvider bằng AWS S3 / MinIO qua boto3.

    Hỗ trợ:
        - Upload/download/xóa object
        - Presigned URL với thời hạn tùy chỉnh
        - Liệt kê files theo prefix
        - Tenant isolation (KPI-029) qua tenant_prefix trong key

    Ví dụ:
        provider = S3Provider(
            bucket="my-bucket",
            region="ap-southeast-1",
            endpoint_url="https://minio.example.com",
            tenant_prefix="tenants/{tenant_id}/",
        )
        result = provider.upload(b"data", "files/doc.pdf", "application/pdf")
    """

    def __init__(
        self,
        bucket: str,
        region: str = "us-east-1",
        endpoint_url: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
        tenant_prefix: str | None = None,
    ) -> None:
        """
        Khởi tạo S3Provider.

        Args:
            bucket: Tên S3 bucket
            region: AWS region (mặc định "us-east-1")
            endpoint_url: Custom endpoint cho MinIO/S3-compatible (tùy chọn)
            access_key: AWS access key ID (tùy chọn, ưu tiên dùng môi trường)
            secret_key: AWS secret access key (tùy chọn, ưu tiên dùng môi trường)
            tenant_prefix: Tiền tố tenant cho key để enforce tenant isolation (KPI-029)
        """
        self._bucket = bucket
        self._region = region
        self._endpoint_url = endpoint_url
        self._access_key = access_key
        self._secret_key = secret_key
        self._tenant_prefix = tenant_prefix.rstrip("/") + "/" if tenant_prefix else ""
        self._client: Any = None

    def _get_client(self) -> Any:
        """
        Tạo (hoặc tái sử dụng) boto3 S3 client — lazy initialization.

        Returns:
            boto3 S3 client đã cấu hình

        Raises:
            MidicoderError: Nếu không thể tạo client do thiếu credentials
        """
        if self._client is not None:
            return self._client

        # Lazy import boto3 — chỉ load khi thực sự cần
        import boto3
        from botocore.exceptions import ClientError, NoCredentialsError

        try:
            kwargs: dict[str, Any] = {
                "service_name": "s3",
                "region_name": self._region,
            }

            if self._endpoint_url:
                kwargs["endpoint_url"] = self._endpoint_url

            if self._access_key and self._secret_key:
                kwargs["aws_access_key_id"] = self._access_key
                kwargs["aws_secret_access_key"] = self._secret_key

            self._client = boto3.client(**kwargs)
            return self._client

        except NoCredentialsError:
            EM.raise_error(
                ErrorCode.CP11_PROVIDER_NOT_FOUND,
                provider="s3",
                detail="Không tìm thấy AWS credentials — thiết lập môi trường hoặc truyền access_key/secret_key",
            )
        except Exception as e:
            EM.raise_error(
                ErrorCode.CP11_PROVIDER_NOT_FOUND,
                provider="s3",
                detail=f"Không thể tạo S3 client: {e}",
            )

    def _build_key(self, key: str, tenant_id: str | None = None) -> str:
        """
        Xây dựng key thực tế trong S3 — KPI-029: thêm tenant prefix nếu cấu hình.

        Args:
            key: Key gốc của file
            tenant_id: Tenant identifier (chưa dùng trực tiếp, prefix đã được set tại init)

        Returns:
            Key hoàn chỉnh với tenant prefix (nếu có) và key gốc
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
        Upload dữ liệu bytes lên S3 bucket.

        Sử dụng TransferConfig để tối ưu hóa upload cho file lớn
        (multipart threshold 8MB, max 10 concurrent tasks).

        Args:
            file_bytes: Nội dung file dưới dạng bytes
            key: Khóa (path) của file trong S3 bucket
            content_type: MIME type của file
            tenant_id: Tenant identifier cho tenant isolation (KPI-029)

        Returns:
            Dict chứa:
                - key (str): Key thực tế trong S3
                - url (str): URL public của object (s3://bucket/key)
                - size (int): Kích thước file (bytes)

        Raises:
            MidicoderError: Nếu content_type không hợp lệ hoặc upload thất bại
        """
        from io import BytesIO

        from boto3.s3.transfer import TransferConfig
        from botocore.exceptions import ClientError

        # Validate content_type
        if not content_type or not content_type.strip():
            EM.raise_error(
                ErrorCode.CP11_INVALID_CONTENT_TYPE,
                key=key,
                detail="Content type không được để trống",
            )

        full_key = self._build_key(key, tenant_id)
        client = self._get_client()

        try:
            transfer_config = TransferConfig(
                multipart_threshold=8 * 1024 * 1024,
                max_concurrency=10,
            )

            client.put_object(
                Bucket=self._bucket,
                Key=full_key,
                Body=BytesIO(file_bytes),
                ContentType=content_type,
                ContentLength=len(file_bytes),
                Config=transfer_config,
            )

            url = f"s3://{self._bucket}/{full_key}"

            return {
                "key": full_key,
                "url": url,
                "size": len(file_bytes),
            }

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            EM.raise_error(
                ErrorCode.CP11_PROVIDER_NOT_FOUND,
                provider="s3",
                operation="upload",
                key=full_key,
                error_code=error_code,
                detail=f"S3 upload thất bại: {e}",
            )

    def download(
        self,
        key: str,
        tenant_id: str | None = None,
    ) -> bytes:
        """
        Tải xuống nội dung file từ S3 bucket.

        Args:
            key: Khóa (path) của file trong S3 bucket
            tenant_id: Tenant identifier cho tenant isolation (KPI-029)

        Returns:
            Nội dung file dưới dạng bytes

        Raises:
            MidicoderError: Nếu file không tồn tại (404) hoặc download thất bại
        """
        full_key = self._build_key(key, tenant_id)
        client = self._get_client()

        from botocore.exceptions import ClientError

        try:
            response = client.get_object(Bucket=self._bucket, Key=full_key)
            return response["Body"].read()

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "NoSuchKey":
                EM.raise_error(
                    ErrorCode.CP11_PROVIDER_NOT_FOUND,
                    provider="s3",
                    operation="download",
                    key=full_key,
                    detail=f"File không tồn tại trong S3: {full_key}",
                )
            EM.raise_error(
                ErrorCode.CP11_PROVIDER_NOT_FOUND,
                provider="s3",
                operation="download",
                key=full_key,
                error_code=error_code,
                detail=f"S3 download thất bại: {e}",
            )

    def delete(
        self,
        key: str,
        tenant_id: str | None = None,
    ) -> bool:
        """
        Xóa object khỏi S3 bucket.

        Args:
            key: Khóa (path) của object cần xóa
            tenant_id: Tenant identifier cho tenant isolation (KPI-029)

        Returns:
            True nếu xóa thành công, False nếu object không tồn tại

        Raises:
            MidicoderError: Nếu xóa thất bại do lỗi hệ thống
        """
        full_key = self._build_key(key, tenant_id)
        client = self._get_client()

        from botocore.exceptions import ClientError

        try:
            client.delete_object(Bucket=self._bucket, Key=full_key)
            return True

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "NoSuchKey":
                return False
            EM.raise_error(
                ErrorCode.CP11_PROVIDER_NOT_FOUND,
                provider="s3",
                operation="delete",
                key=full_key,
                error_code=error_code,
                detail=f"S3 delete thất bại: {e}",
            )

    def get_presigned_url(
        self,
        key: str,
        expiration: int = 3600,
        tenant_id: str | None = None,
    ) -> str:
        """
        Tạo presigned URL để truy cập tạm thời object trong S3.

        Args:
            key: Khóa (path) của file trong S3 bucket
            expiration: Thời gian sống của URL (giây), mặc định 3600s = 1 giờ
            tenant_id: Tenant identifier cho tenant isolation (KPI-029)

        Returns:
            Presigned URL string để GET object trong khoảng expiration

        Raises:
            MidicoderError: Nếu tạo presigned URL thất bại
        """
        full_key = self._build_key(key, tenant_id)
        client = self._get_client()

        from botocore.exceptions import ClientError

        try:
            url = client.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": self._bucket,
                    "Key": full_key,
                },
                ExpiresIn=expiration,
            )
            return url

        except ClientError as e:
            EM.raise_error(
                ErrorCode.CP11_PROVIDER_NOT_FOUND,
                provider="s3",
                operation="get_presigned_url",
                key=full_key,
                detail=f"Không thể tạo presigned URL: {e}",
            )

    def list_files(
        self,
        prefix: str,
        tenant_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Liệt kê các objects trong S3 bucket theo prefix.

        Sử dụng list_objects_v2 với pagination để lấy tất cả objects.
        Trả về danh sách với thông tin key, size, last_modified cho mỗi object.

        Args:
            prefix: Tiền tố để lọc objects (ví dụ: "uploads/2024/")
            tenant_id: Tenant identifier cho tenant isolation (KPI-029)

        Returns:
            Danh sách dict, mỗi dict chứa:
                - key (str): Key của object
                - size (int): Kích thước object (bytes)
                - last_modified (str): Thời gian sửa đổi (ISO 8601 UTC)

        Raises:
            MidicoderError: Nếu list_objects thất bại
        """
        full_prefix = self._build_key(prefix, tenant_id)
        client = self._get_client()
        files: list[dict[str, Any]] = []

        from botocore.exceptions import ClientError

        try:
            paginator = client.get_paginator("list_objects_v2")
            page_iterator = paginator.paginate(
                Bucket=self._bucket,
                Prefix=full_prefix,
            )

            for page in page_iterator:
                contents = page.get("Contents", [])
                for obj in contents:
                    last_modified = obj.get("LastModified", datetime.now(timezone.utc))

                    # Chuyển datetime sang ISO 8601 string nếu cần
                    if isinstance(last_modified, datetime):
                        last_modified_str = last_modified.strftime("%Y-%m-%dT%H:%M:%SZ")
                    else:
                        last_modified_str = str(last_modified)

                    # Loại bỏ tenant prefix từ key trả về để user thấy key gốc
                    display_key = obj["Key"]
                    if self._tenant_prefix and display_key.startswith(self._tenant_prefix):
                        display_key = display_key[len(self._tenant_prefix):]

                    files.append({
                        "key": display_key,
                        "size": obj.get("Size", 0),
                        "last_modified": last_modified_str,
                    })

            return files

        except ClientError as e:
            EM.raise_error(
                ErrorCode.CP11_PROVIDER_NOT_FOUND,
                provider="s3",
                operation="list_files",
                prefix=full_prefix,
                detail=f"S3 list_files thất bại: {e}",
            )
