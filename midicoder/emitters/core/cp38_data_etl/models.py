# coding: utf-8
"""
Mô-đun models cho CP38 — Data Import/Export/ETL.

Định nghĩa các dataclass biểu diễn:
- ImportJob: Job import dữ liệu từ file CSV/JSON vào entity
- ExportJob: Job export dữ liệu từ entity ra file
- ETLMapping: Ánh xạ cột source sang field target với transform
- ExtractConfig: Cấu hình extract dữ liệu từ source
- TransformConfig: Cấu hình transform step
- LoadConfig: Cấu hình load dữ liệu vào target
- ETLStep: Một bước trong ETL pipeline (extract/transform/load)
- ETLJob: Job ETL hoàn chỉnh với nhiều steps
- ImportError: Lỗi gặp phải trong quá trình import
- BulkConfig: Cấu hình cho bulk operation

KPI-005: CP Obligations Coverage (>= 2 obligations cho CP38).

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# ===========================================================================
# Enums
# ===========================================================================


class ImportFormat(str, Enum):
    """Định dạng file import.

    - CSV: File CSV với delimiter
    - JSON: File JSON (array of objects)
    """
    CSV = "csv"
    JSON = "json"


class JobStatus(str, Enum):
    """Trạng thái của import/export/ETL job.

    - PENDING: Đang chờ chạy
    - RUNNING: Đang chạy
    - COMPLETED: Đã hoàn thành
    - FAILED: Đã thất bại
    - CANCELLED: Đã bị hủy
    """
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TransformType(str, Enum):
    """Loại transform trong ETL mapping.

    - MAP: Ánh xạ giá trị (vd: "active" -> 1)
    - FILTER: Lọc dữ liệu theo điều kiện
    - AGGREGATE: Tổng hợp dữ liệu (sum, count, avg)
    - CONVERT: Chuyển đổi kiểu dữ liệu
    - RENAME: Đổi tên cột/field
    """
    MAP = "map"
    FILTER = "filter"
    AGGREGATE = "aggregate"
    CONVERT = "convert"
    RENAME = "rename"


class ExtractSource(str, Enum):
    """Nguồn dữ liệu cho extract step.

    - FILE: File trên hệ thống
    - DATABASE: CSDL (SQL query)
    - API: REST API endpoint
    """
    FILE = "file"
    DATABASE = "database"
    API = "api"


class LoadMode(str, Enum):
    """Chế độ load dữ liệu vào target.

    - INSERT: Chỉ chèn mới
    - UPDATE: Chỉ cập nhật bản ghi có sẵn
    - UPSERT: Chèn mới hoặc cập nhật nếu đã tồn tại
    - DELETE: Xóa bản ghi theo key
    """
    INSERT = "insert"
    UPDATE = "update"
    UPSERT = "upsert"
    DELETE = "delete"


# ===========================================================================
# ImportError
# ===========================================================================


@dataclass
class ImportError:
    """Lỗi gặp phải trong quá trình import một hàng.

    Attributes:
        row_number: Số thứ tự hàng (1-indexed)
        column: Tên cột/giá trị gặp lỗi
        error_message: Mô tả chi tiết lỗi
    """
    row_number: int
    column: str = ""
    error_message: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Chuyển ImportError sang dict."""
        return {
            "row_number": self.row_number,
            "column": self.column,
            "error_message": self.error_message,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ImportError":
        """Tạo ImportError từ dict."""
        return cls(
            row_number=data.get("row_number", 0),
            column=data.get("column", ""),
            error_message=data.get("error_message", ""),
        )


# ===========================================================================
# Import Job
# ===========================================================================


@dataclass
class ImportJob:
    """Job import dữ liệu từ file vào entity.

    Theo dõi toàn bộ quá trình import, bao gồm số lượng hàng
    thành công, thất bại, bị bỏ qua, và danh sách lỗi chi tiết.

    Attributes:
        job_key: Identifier duy nhất cho job
        target_entity: Entity đích nhận dữ liệu import
        source_file: Đường dẫn file nguồn (optional)
        format: Định dạng file (csv/json)
        status: Trạng thái hiện tại của job
        total_rows: Tổng số hàng trong file
        success_rows: Số hàng import thành công
        failed_rows: Số hàng import thất bại
        skipped_rows: Số hàng bị bỏ qua
        errors: Danh sách lỗi chi tiết theo từng hàng
        tenant_id: Tenant ID cho multi-tenant scope
        started_at: Thời điểm bắt đầu chạy job
        completed_at: Thời điểm hoàn thành job
        created_at: Thời điểm tạo job
    """
    job_key: str
    target_entity: str
    source_file: str | None = None
    format: ImportFormat = ImportFormat.CSV
    status: JobStatus = JobStatus.PENDING
    total_rows: int = 0
    success_rows: int = 0
    failed_rows: int = 0
    skipped_rows: int = 0
    errors: list[ImportError] = field(default_factory=list)
    tenant_id: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate import job sau khi khởi tạo."""
        if not self.job_key or not self.job_key.strip():
            EM.raise_error(
                ErrorCode.CP38_DUPLICATE_JOB_KEY,
                job_key=self.job_key,
                message="Job key không được để trống"
            )
        if not self.target_entity or not self.target_entity.strip():
            EM.raise_error(
                ErrorCode.CP38_TARGET_ENTITY_NOT_FOUND,
                message="Target entity không được để trống"
            )
        # Validate: total_rows >= success + failed + skipped
        if self.total_rows < self.success_rows + self.failed_rows + self.skipped_rows:
            EM.raise_error(
                ErrorCode.CP38_INVALID_COLUMN_MAPPING,
                detail=f"total_rows ({self.total_rows}) phải >= success_rows ({self.success_rows}) + failed_rows ({self.failed_rows}) + skipped_rows ({self.skipped_rows})",
                message="Tổng số hàng phải lớn hơn hoặc bằng tổng các hàng con"
            )

        now = datetime.now(timezone.utc)
        if self.created_at is None:
            self.created_at = now

    def to_dict(self) -> dict[str, Any]:
        """Chuyển ImportJob sang dict."""
        return {
            "job_key": self.job_key,
            "target_entity": self.target_entity,
            "source_file": self.source_file,
            "format": self.format.value,
            "status": self.status.value,
            "total_rows": self.total_rows,
            "success_rows": self.success_rows,
            "failed_rows": self.failed_rows,
            "skipped_rows": self.skipped_rows,
            "errors": [e.to_dict() for e in self.errors],
            "tenant_id": self.tenant_id,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ImportJob":
        """Tạo ImportJob từ dict."""
        errors_data = data.get("errors", [])
        errors = [ImportError.from_dict(e) for e in errors_data]
        return cls(
            job_key=data.get("job_key", ""),
            target_entity=data.get("target_entity", ""),
            source_file=data.get("source_file"),
            format=ImportFormat(data.get("format", "csv")),
            status=JobStatus(data.get("status", "pending")),
            total_rows=data.get("total_rows", 0),
            success_rows=data.get("success_rows", 0),
            failed_rows=data.get("failed_rows", 0),
            skipped_rows=data.get("skipped_rows", 0),
            errors=errors,
            tenant_id=data.get("tenant_id"),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
        )


# ===========================================================================
# Export Job
# ===========================================================================


@dataclass
class ExportJob:
    """Job export dữ liệu từ entity ra file.

    Attributes:
        job_key: Identifier duy nhất cho job
        entity: Entity nguồn cần export
        format: Định dạng file output (csv/json)
        filters: Bộ lọc dữ liệu (dict key-value)
        status: Trạng thái hiện tại của job
        output_path: Đường dẫn file output
        total_rows: Tổng số hàng đã export
        tenant_id: Tenant ID cho multi-tenant scope
        created_at: Thời điểm tạo job
    """
    job_key: str
    entity: str
    format: ImportFormat = ImportFormat.CSV
    filters: dict[str, Any] = field(default_factory=dict)
    status: JobStatus = JobStatus.PENDING
    output_path: str | None = None
    total_rows: int = 0
    tenant_id: str | None = None
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate export job sau khi khởi tạo."""
        if not self.job_key or not self.job_key.strip():
            EM.raise_error(
                ErrorCode.CP38_DUPLICATE_JOB_KEY,
                job_key=self.job_key,
                message="Job key không được để trống"
            )
        # Validate: format phải là csv hoặc json
        if self.format not in (ImportFormat.CSV, ImportFormat.JSON):
            EM.raise_error(
                ErrorCode.CP38_INVALID_EXPORT_FORMAT,
                message=f"Format export phải là csv hoặc json, nhận được: {self.format}"
            )

        now = datetime.now(timezone.utc)
        if self.created_at is None:
            self.created_at = now

    def to_dict(self) -> dict[str, Any]:
        """Chuyển ExportJob sang dict."""
        return {
            "job_key": self.job_key,
            "entity": self.entity,
            "format": self.format.value,
            "filters": self.filters,
            "status": self.status.value,
            "output_path": self.output_path,
            "total_rows": self.total_rows,
            "tenant_id": self.tenant_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExportJob":
        """Tạo ExportJob từ dict."""
        return cls(
            job_key=data.get("job_key", ""),
            entity=data.get("entity", ""),
            format=ImportFormat(data.get("format", "csv")),
            filters=data.get("filters", {}),
            status=JobStatus(data.get("status", "pending")),
            output_path=data.get("output_path"),
            total_rows=data.get("total_rows", 0),
            tenant_id=data.get("tenant_id"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
        )


# ===========================================================================
# ETL Mapping
# ===========================================================================


@dataclass
class ETLMapping:
    """Ánh xạ cột source sang field target với transform.

    Attributes:
        mapping_key: Identifier duy nhất cho mapping này
        source_column: Tên cột trong dữ liệu nguồn
        target_field: Tên field trong entity đích
        transform: Loại transform (map/filter/aggregate/convert/rename)
        params: Tham số chi tiết cho transform
    """
    mapping_key: str
    source_column: str
    target_field: str
    transform: TransformType | None = None
    params: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate ETL mapping sau khi khởi tạo."""
        if not self.mapping_key or not self.mapping_key.strip():
            EM.raise_error(
                ErrorCode.CP38_INVALID_COLUMN_MAPPING,
                detail="mapping_key",
                message="Mapping key không được để trống"
            )
        if not self.source_column or not self.source_column.strip():
            EM.raise_error(
                ErrorCode.CP38_INVALID_COLUMN_MAPPING,
                detail="source_column",
                message="Source column không được để trống"
            )
        if not self.target_field or not self.target_field.strip():
            EM.raise_error(
                ErrorCode.CP38_INVALID_COLUMN_MAPPING,
                detail="target_field",
                message="Target field không được để trống"
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển ETLMapping sang dict."""
        return {
            "mapping_key": self.mapping_key,
            "source_column": self.source_column,
            "target_field": self.target_field,
            "transform": self.transform.value if self.transform else None,
            "params": self.params,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ETLMapping":
        """Tạo ETLMapping từ dict."""
        transform_value = data.get("transform")
        transform = TransformType(transform_value) if transform_value else None
        return cls(
            mapping_key=data.get("mapping_key", ""),
            source_column=data.get("source_column", ""),
            target_field=data.get("target_field", ""),
            transform=transform,
            params=data.get("params", {}),
        )


# ===========================================================================
# Extract Config
# ===========================================================================


@dataclass
class ExtractConfig:
    """Cấu hình extract dữ liệu từ source.

    Attributes:
        source: Nguồn dữ liệu (file/database/api)
        file_path: Đường dẫn file (khi source=file)
        query: SQL query (khi source=database)
        table: Tên bảng (khi source=database)
        delimiter: Ký tự phân cách (khi source=file, format=csv)
    """
    source: ExtractSource
    file_path: str | None = None
    query: str | None = None
    table: str | None = None
    delimiter: str = ","

    def __post_init__(self) -> None:
        """Validate extract config sau khi khởi tạo."""
        if not self.source:
            EM.raise_error(
                ErrorCode.CP38_INVALID_ETL_STEP_TYPE,
                step_type="extract",
                message="Source phải được chỉ định"
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển ExtractConfig sang dict."""
        return {
            "source": self.source.value,
            "file_path": self.file_path,
            "query": self.query,
            "table": self.table,
            "delimiter": self.delimiter,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExtractConfig":
        """Tạo ExtractConfig từ dict."""
        return cls(
            source=ExtractSource(data.get("source", "file")),
            file_path=data.get("file_path"),
            query=data.get("query"),
            table=data.get("table"),
            delimiter=data.get("delimiter", ","),
        )


# ===========================================================================
# Transform Config
# ===========================================================================


@dataclass
class TransformConfig:
    """Cấu hình transform step trong ETL.

    Attributes:
        step_type: Loại transform
        params: Tham số chi tiết cho transform
    """
    step_type: TransformType
    params: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate transform config sau khi khởi tạo."""
        if not self.step_type or self.step_type not in TransformType:
            EM.raise_error(
                ErrorCode.CP38_INVALID_TRANSFORM_CONFIG,
                message=f"Step type không hợp lệ: {self.step_type}"
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển TransformConfig sang dict."""
        return {
            "step_type": self.step_type.value,
            "params": self.params,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TransformConfig":
        """Tạo TransformConfig từ dict."""
        return cls(
            step_type=TransformType(data.get("step_type", "map")),
            params=data.get("params", {}),
        )


# ===========================================================================
# Load Config
# ===========================================================================


@dataclass
class LoadConfig:
    """Cấu hình load dữ liệu vào target entity.

    Attributes:
        target_entity: Entity đích nhận dữ liệu
        mode: Chế độ load (insert/update/upsert/delete)
        upsert_key: Field dùng để xác định bản ghi khi upsert
    """
    target_entity: str
    mode: LoadMode = LoadMode.INSERT
    upsert_key: str | None = None

    def __post_init__(self) -> None:
        """Validate load config sau khi khởi tạo."""
        if not self.target_entity or not self.target_entity.strip():
            EM.raise_error(
                ErrorCode.CP38_TARGET_ENTITY_NOT_FOUND,
                message="Target entity không được để trống"
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển LoadConfig sang dict."""
        return {
            "target_entity": self.target_entity,
            "mode": self.mode.value,
            "upsert_key": self.upsert_key,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LoadConfig":
        """Tạo LoadConfig từ dict."""
        return cls(
            target_entity=data.get("target_entity", ""),
            mode=LoadMode(data.get("mode", "insert")),
            upsert_key=data.get("upsert_key"),
        )


# ===========================================================================
# ETL Step
# ===========================================================================


@dataclass
class ETLStep:
    """Một bước trong ETL pipeline.

    Bước có thể là extract, transform, hoặc load. Mỗi bước có
    config riêng và thứ tự thực thi (order).

    Attributes:
        step_key: Identifier duy nhất cho step
        step_type: Loại step (extract/transform/load hoặc TransformType)
        config: Cấu hình chi tiết cho step
        order: Thứ tự thực thi (0 = đầu tiên)
    """
    step_key: str
    step_type: str  # "extract", "load", hoặc TransformType
    config: dict[str, Any] = field(default_factory=dict)
    order: int = 0

    def __post_init__(self) -> None:
        """Validate ETL step sau khi khởi tạo."""
        if not self.step_key or not self.step_key.strip():
            EM.raise_error(
                ErrorCode.CP38_INVALID_ETL_STEP_TYPE,
                step_type=self.step_type,
                message="Step key không được để trống"
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển ETLStep sang dict."""
        return {
            "step_key": self.step_key,
            "step_type": self.step_type,
            "config": self.config,
            "order": self.order,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ETLStep":
        """Tạo ETLStep từ dict."""
        return cls(
            step_key=data.get("step_key", ""),
            step_type=data.get("step_type", "extract"),
            config=data.get("config", {}),
            order=data.get("order", 0),
        )


# ===========================================================================
# ETL Job
# ===========================================================================


@dataclass
class ETLJob:
    """Job ETL hoàn chỉnh với nhiều steps.

    ETL pipeline bao gồm ít nhất 1 extract step và 1 load step,
    có thể có nhiều transform steps ở giữa.

    Attributes:
        job_key: Identifier duy nhất cho job
        steps: Danh sách ETL steps theo thứ tự
        status: Trạng thái hiện tại của job
        total_rows_processed: Tổng số hàng đã xử lý
        created_at: Thời điểm tạo job
    """
    job_key: str
    steps: list[ETLStep] = field(default_factory=list)
    status: JobStatus = JobStatus.PENDING
    total_rows_processed: int = 0
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate ETL job sau khi khởi tạo."""
        if not self.job_key or not self.job_key.strip():
            EM.raise_error(
                ErrorCode.CP38_DUPLICATE_JOB_KEY,
                job_key=self.job_key,
                message="Job key không được để trống"
            )

        # Validate: phải có ít nhất 1 extract step
        has_extract = any(s.step_type == "extract" for s in self.steps)
        if not has_extract:
            EM.raise_error(
                ErrorCode.CP38_ETL_MISSING_EXTRACT_STEP,
                message="ETL pipeline phải có ít nhất 1 extract step"
            )

        # Validate: phải có ít nhất 1 load step
        has_load = any(s.step_type == "load" for s in self.steps)
        if not has_load:
            EM.raise_error(
                ErrorCode.CP38_ETL_MISSING_LOAD_STEP,
                message="ETL pipeline phải có ít nhất 1 load step"
            )

        now = datetime.now(timezone.utc)
        if self.created_at is None:
            self.created_at = now

    def to_dict(self) -> dict[str, Any]:
        """Chuyển ETLJob sang dict."""
        return {
            "job_key": self.job_key,
            "steps": [s.to_dict() for s in self.steps],
            "status": self.status.value,
            "total_rows_processed": self.total_rows_processed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ETLJob":
        """Tạo ETLJob từ dict."""
        steps_data = data.get("steps", [])
        steps = [ETLStep.from_dict(s) for s in steps_data]
        return cls(
            job_key=data.get("job_key", ""),
            steps=steps,
            status=JobStatus(data.get("status", "pending")),
            total_rows_processed=data.get("total_rows_processed", 0),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
        )


# ===========================================================================
# Bulk Config
# ===========================================================================


@dataclass
class BulkConfig:
    """Cấu hình cho bulk operation (import/export với số lượng lớn).

    Attributes:
        chunk_size: Số bản ghi xử lý mỗi lần (mặc định 1000)
        max_retries: Số lần thử lại tối đa khi lỗi (mặc định 3)
        rollback_threshold: Tỷ lệ lỗi cho phép trước khi rollback (mặc định 0.1 = 10%)
    """
    chunk_size: int = 1000
    max_retries: int = 3
    rollback_threshold: float = 0.1

    def __post_init__(self) -> None:
        """Validate bulk config sau khi khởi tạo."""
        if self.chunk_size <= 0:
            EM.raise_error(
                ErrorCode.CP38_INVALID_BULK_CHUNK_SIZE,
                message=f"Chunk size phải lớn hơn 0, nhận được: {self.chunk_size}"
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển BulkConfig sang dict."""
        return {
            "chunk_size": self.chunk_size,
            "max_retries": self.max_retries,
            "rollback_threshold": self.rollback_threshold,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BulkConfig":
        """Tạo BulkConfig từ dict."""
        return cls(
            chunk_size=data.get("chunk_size", 1000),
            max_retries=data.get("max_retries", 3),
            rollback_threshold=data.get("rollback_threshold", 0.1),
        )


# ===========================================================================
# Exports
# ===========================================================================

__all__ = [
    # Enums
    "ImportFormat",
    "JobStatus",
    "TransformType",
    "ExtractSource",
    "LoadMode",
    # Import/Export Jobs
    "ImportJob",
    "ExportJob",
    "ImportError",
    # ETL
    "ETLMapping",
    "ExtractConfig",
    "TransformConfig",
    "LoadConfig",
    "ETLStep",
    "ETLJob",
    # Bulk
    "BulkConfig",
]
