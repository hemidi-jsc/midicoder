# coding: utf-8
"""
Tests cho CP38 models: ImportJob, ExportJob, ETLMapping, ExtractConfig, TransformConfig,
LoadConfig, ETLStep, ETLJob, ImportError, BulkConfig + 5 enums.
"""

from __future__ import annotations

import pytest

from midicoder.errors import ErrorCode, MidicoderError


# ============================================================================
# Test Error Codes
# ============================================================================


class TestCP38ErrorCodes:
    """Tests cho CP38 error codes."""

    def test_cp38_invalid_import_file_exists(self):
        assert hasattr(ErrorCode, "CP38_INVALID_IMPORT_FILE")
        assert ErrorCode.CP38_INVALID_IMPORT_FILE == "MDC-CP38-001"

    def test_cp38_unsupported_format_exists(self):
        assert hasattr(ErrorCode, "CP38_UNSUPPORTED_FORMAT")
        assert ErrorCode.CP38_UNSUPPORTED_FORMAT == "MDC-CP38-002"

    def test_cp38_file_size_exceeded_exists(self):
        assert hasattr(ErrorCode, "CP38_FILE_SIZE_EXCEEDED")
        assert ErrorCode.CP38_FILE_SIZE_EXCEEDED == "MDC-CP38-003"

    def test_cp38_invalid_column_mapping_exists(self):
        assert hasattr(ErrorCode, "CP38_INVALID_COLUMN_MAPPING")
        assert ErrorCode.CP38_INVALID_COLUMN_MAPPING == "MDC-CP38-004"

    def test_cp38_duplicate_job_key_exists(self):
        assert hasattr(ErrorCode, "CP38_DUPLICATE_JOB_KEY")
        assert ErrorCode.CP38_DUPLICATE_JOB_KEY == "MDC-CP38-005"

    def test_cp38_job_not_found_exists(self):
        assert hasattr(ErrorCode, "CP38_JOB_NOT_FOUND")
        assert ErrorCode.CP38_JOB_NOT_FOUND == "MDC-CP38-006"

    def test_cp38_job_already_running_exists(self):
        assert hasattr(ErrorCode, "CP38_JOB_ALREADY_RUNNING")
        assert ErrorCode.CP38_JOB_ALREADY_RUNNING == "MDC-CP38-007"

    def test_cp38_invalid_etl_step_type_exists(self):
        assert hasattr(ErrorCode, "CP38_INVALID_ETL_STEP_TYPE")
        assert ErrorCode.CP38_INVALID_ETL_STEP_TYPE == "MDC-CP38-008"

    def test_cp38_etl_missing_extract_step_exists(self):
        assert hasattr(ErrorCode, "CP38_ETL_MISSING_EXTRACT_STEP")
        assert ErrorCode.CP38_ETL_MISSING_EXTRACT_STEP == "MDC-CP38-009"

    def test_cp38_etl_missing_load_step_exists(self):
        assert hasattr(ErrorCode, "CP38_ETL_MISSING_LOAD_STEP")
        assert ErrorCode.CP38_ETL_MISSING_LOAD_STEP == "MDC-CP38-010"

    def test_cp38_invalid_bulk_chunk_size_exists(self):
        assert hasattr(ErrorCode, "CP38_INVALID_BULK_CHUNK_SIZE")
        assert ErrorCode.CP38_INVALID_BULK_CHUNK_SIZE == "MDC-CP38-011"

    def test_cp38_invalid_transform_config_exists(self):
        assert hasattr(ErrorCode, "CP38_INVALID_TRANSFORM_CONFIG")
        assert ErrorCode.CP38_INVALID_TRANSFORM_CONFIG == "MDC-CP38-012"

    def test_cp38_invalid_export_format_exists(self):
        assert hasattr(ErrorCode, "CP38_INVALID_EXPORT_FORMAT")
        assert ErrorCode.CP38_INVALID_EXPORT_FORMAT == "MDC-CP38-013"

    def test_cp38_target_entity_not_found_exists(self):
        assert hasattr(ErrorCode, "CP38_TARGET_ENTITY_NOT_FOUND")
        assert ErrorCode.CP38_TARGET_ENTITY_NOT_FOUND == "MDC-CP38-014"

    def test_cp38_csv_parse_failed_exists(self):
        assert hasattr(ErrorCode, "CP38_CSV_PARSE_FAILED")
        assert ErrorCode.CP38_CSV_PARSE_FAILED == "MDC-CP38-015"

    def test_cp38_json_parse_failed_exists(self):
        assert hasattr(ErrorCode, "CP38_JSON_PARSE_FAILED")
        assert ErrorCode.CP38_JSON_PARSE_FAILED == "MDC-CP38-016"

    def test_cp38_template_not_found_exists(self):
        assert hasattr(ErrorCode, "CP38_TEMPLATE_NOT_FOUND")
        assert ErrorCode.CP38_TEMPLATE_NOT_FOUND == "MDC-CP38-017"

    def test_cp38_render_failed_exists(self):
        assert hasattr(ErrorCode, "CP38_RENDER_FAILED")
        assert ErrorCode.CP38_RENDER_FAILED == "MDC-CP38-018"


# ============================================================================
# Test Enums
# ============================================================================


class TestCP38Enums:
    """Tests cho CP38 enums."""

    # ImportFormat
    def test_import_format_csv(self):
        from midicoder.packs.cp38_data_etl.models import ImportFormat
        assert ImportFormat.CSV.value == "csv"

    def test_import_format_json(self):
        from midicoder.packs.cp38_data_etl.models import ImportFormat
        assert ImportFormat.JSON.value == "json"

    # JobStatus
    def test_job_status_pending(self):
        from midicoder.packs.cp38_data_etl.models import JobStatus
        assert JobStatus.PENDING.value == "pending"

    def test_job_status_running(self):
        from midicoder.packs.cp38_data_etl.models import JobStatus
        assert JobStatus.RUNNING.value == "running"

    def test_job_status_completed(self):
        from midicoder.packs.cp38_data_etl.models import JobStatus
        assert JobStatus.COMPLETED.value == "completed"

    def test_job_status_failed(self):
        from midicoder.packs.cp38_data_etl.models import JobStatus
        assert JobStatus.FAILED.value == "failed"

    def test_job_status_cancelled(self):
        from midicoder.packs.cp38_data_etl.models import JobStatus
        assert JobStatus.CANCELLED.value == "cancelled"

    # TransformType
    def test_transform_type_map(self):
        from midicoder.packs.cp38_data_etl.models import TransformType
        assert TransformType.MAP.value == "map"

    def test_transform_type_filter(self):
        from midicoder.packs.cp38_data_etl.models import TransformType
        assert TransformType.FILTER.value == "filter"

    def test_transform_type_aggregate(self):
        from midicoder.packs.cp38_data_etl.models import TransformType
        assert TransformType.AGGREGATE.value == "aggregate"

    def test_transform_type_convert(self):
        from midicoder.packs.cp38_data_etl.models import TransformType
        assert TransformType.CONVERT.value == "convert"

    def test_transform_type_rename(self):
        from midicoder.packs.cp38_data_etl.models import TransformType
        assert TransformType.RENAME.value == "rename"

    # ExtractSource
    def test_extract_source_file(self):
        from midicoder.packs.cp38_data_etl.models import ExtractSource
        assert ExtractSource.FILE.value == "file"

    def test_extract_source_database(self):
        from midicoder.packs.cp38_data_etl.models import ExtractSource
        assert ExtractSource.DATABASE.value == "database"

    def test_extract_source_api(self):
        from midicoder.packs.cp38_data_etl.models import ExtractSource
        assert ExtractSource.API.value == "api"

    # LoadMode
    def test_load_mode_insert(self):
        from midicoder.packs.cp38_data_etl.models import LoadMode
        assert LoadMode.INSERT.value == "insert"

    def test_load_mode_update(self):
        from midicoder.packs.cp38_data_etl.models import LoadMode
        assert LoadMode.UPDATE.value == "update"

    def test_load_mode_upsert(self):
        from midicoder.packs.cp38_data_etl.models import LoadMode
        assert LoadMode.UPSERT.value == "upsert"

    def test_load_mode_delete(self):
        from midicoder.packs.cp38_data_etl.models import LoadMode
        assert LoadMode.DELETE.value == "delete"


# ============================================================================
# Test ImportJob
# ============================================================================


class TestImportJob:
    """Tests cho ImportJob model."""

    def test_import_job_creation(self):
        from midicoder.packs.cp38_data_etl.models import (
            ImportFormat,
            ImportJob,
            JobStatus,
        )

        job = ImportJob(
            job_key="import_users",
            target_entity="users",
            source_file="/data/users.csv",
            format=ImportFormat.CSV,
        )
        assert job.job_key == "import_users"
        assert job.target_entity == "users"
        assert job.source_file == "/data/users.csv"
        assert job.format == ImportFormat.CSV
        assert job.status == JobStatus.PENDING

    def test_import_job_empty_job_key_raises_error(self):
        from midicoder.packs.cp38_data_etl.models import ImportJob

        with pytest.raises(MidicoderError):
            ImportJob(job_key="", target_entity="users")

    def test_import_job_empty_target_entity_raises_error(self):
        from midicoder.packs.cp38_data_etl.models import ImportJob

        with pytest.raises(MidicoderError):
            ImportJob(job_key="test", target_entity="")

    def test_import_job_to_dict(self):
        from midicoder.packs.cp38_data_etl.models import ImportJob

        job = ImportJob(job_key="test_import", target_entity="products")
        d = job.to_dict()
        assert d["job_key"] == "test_import"
        assert d["target_entity"] == "products"
        assert d["format"] == "csv"
        assert d["status"] == "pending"

    def test_import_job_from_dict(self):
        from midicoder.packs.cp38_data_etl.models import (
            ImportFormat,
            ImportJob,
        )

        data = {
            "job_key": "restored_import",
            "target_entity": "orders",
            "format": "json",
            "status": "completed",
            "total_rows": 100,
        }
        job = ImportJob.from_dict(data)
        assert job.job_key == "restored_import"
        assert job.target_entity == "orders"
        assert job.format == ImportFormat.JSON

    def test_import_job_timestamps_auto_set(self):
        from midicoder.packs.cp38_data_etl.models import ImportJob

        job = ImportJob(job_key="ts_test", target_entity="users")
        assert job.created_at is not None

    def test_import_job_with_errors(self):
        from midicoder.packs.cp38_data_etl.models import (
            ImportError,
            ImportJob,
        )

        errors = [
            ImportError(row_number=1, column="email", error_message="invalid email"),
            ImportError(row_number=3, column="age", error_message="must be integer"),
        ]
        job = ImportJob(
            job_key="import_with_errors",
            target_entity="users",
            errors=errors,
        )
        assert len(job.errors) == 2
        assert job.errors[0].row_number == 1


# ============================================================================
# Test ExportJob
# ============================================================================


class TestExportJob:
    """Tests cho ExportJob model."""

    def test_export_job_creation(self):
        from midicoder.packs.cp38_data_etl.models import (
            ExportJob,
            ImportFormat,
        )

        job = ExportJob(
            job_key="export_orders",
            entity="orders",
            format=ImportFormat.CSV,
        )
        assert job.job_key == "export_orders"
        assert job.entity == "orders"
        assert job.format == ImportFormat.CSV

    def test_export_job_empty_job_key_raises_error(self):
        from midicoder.packs.cp38_data_etl.models import ExportJob

        with pytest.raises(MidicoderError):
            ExportJob(job_key="", entity="orders")

    def test_export_job_to_dict(self):
        from midicoder.packs.cp38_data_etl.models import ExportJob

        job = ExportJob(
            job_key="test_export",
            entity="products",
            filters={"status": "active"},
        )
        d = job.to_dict()
        assert d["job_key"] == "test_export"
        assert d["entity"] == "products"
        assert d["filters"]["status"] == "active"

    def test_export_job_from_dict(self):
        from midicoder.packs.cp38_data_etl.models import (
            ExportJob,
            ImportFormat,
        )

        data = {
            "job_key": "restored_export",
            "entity": "users",
            "format": "json",
            "total_rows": 50,
        }
        job = ExportJob.from_dict(data)
        assert job.job_key == "restored_export"
        assert job.entity == "users"
        assert job.format == ImportFormat.JSON


# ============================================================================
# Test ETLMapping
# ============================================================================


class TestETLMapping:
    """Tests cho ETLMapping model."""

    def test_etl_mapping_creation(self):
        from midicoder.packs.cp38_data_etl.models import (
            ETLMapping,
            TransformType,
        )

        m = ETLMapping(
            mapping_key="map_email",
            source_column="email_address",
            target_field="email",
            transform=TransformType.MAP,
        )
        assert m.mapping_key == "map_email"
        assert m.source_column == "email_address"
        assert m.target_field == "email"

    def test_etl_mapping_empty_mapping_key_raises_error(self):
        from midicoder.packs.cp38_data_etl.models import ETLMapping

        with pytest.raises(MidicoderError):
            ETLMapping(mapping_key="", source_column="a", target_field="b")

    def test_etl_mapping_empty_source_column_raises_error(self):
        from midicoder.packs.cp38_data_etl.models import ETLMapping

        with pytest.raises(MidicoderError):
            ETLMapping(mapping_key="m1", source_column="", target_field="b")

    def test_etl_mapping_empty_target_field_raises_error(self):
        from midicoder.packs.cp38_data_etl.models import ETLMapping

        with pytest.raises(MidicoderError):
            ETLMapping(mapping_key="m1", source_column="a", target_field="")

    def test_etl_mapping_to_dict(self):
        from midicoder.packs.cp38_data_etl.models import (
            ETLMapping,
            TransformType,
        )

        m = ETLMapping(
            mapping_key="m1",
            source_column="old_name",
            target_field="new_name",
            transform=TransformType.RENAME,
            params={"case": "upper"},
        )
        d = m.to_dict()
        assert d["mapping_key"] == "m1"
        assert d["transform"] == "rename"
        assert d["params"]["case"] == "upper"

    def test_etl_mapping_from_dict(self):
        from midicoder.packs.cp38_data_etl.models import (
            ETLMapping,
            TransformType,
        )

        data = {
            "mapping_key": "restored",
            "source_column": "src",
            "target_field": "tgt",
            "transform": "convert",
            "params": {},
        }
        m = ETLMapping.from_dict(data)
        assert m.mapping_key == "restored"
        assert m.transform is not None


# ============================================================================
# Test ExtractConfig
# ============================================================================


class TestExtractConfig:
    """Tests cho ExtractConfig model."""

    def test_extract_config_creation(self):
        from midicoder.packs.cp38_data_etl.models import (
            ExtractConfig,
            ExtractSource,
        )

        c = ExtractConfig(
            source=ExtractSource.FILE,
            file_path="/data/input.csv",
            delimiter=",",
        )
        assert c.source == ExtractSource.FILE
        assert c.file_path == "/data/input.csv"

    def test_extract_config_to_dict(self):
        from midicoder.packs.cp38_data_etl.models import (
            ExtractConfig,
            ExtractSource,
        )

        c = ExtractConfig(
            source=ExtractSource.DATABASE,
            query="SELECT * FROM users",
            table="users",
        )
        d = c.to_dict()
        assert d["source"] == "database"
        assert d["query"] == "SELECT * FROM users"

    def test_extract_config_from_dict(self):
        from midicoder.packs.cp38_data_etl.models import (
            ExtractConfig,
            ExtractSource,
        )

        data = {
            "source": "api",
            "delimiter": "|",
        }
        c = ExtractConfig.from_dict(data)
        assert c.source == ExtractSource.API
        assert c.delimiter == "|"


# ============================================================================
# Test TransformConfig
# ============================================================================


class TestTransformConfig:
    """Tests cho TransformConfig model."""

    def test_transform_config_creation(self):
        from midicoder.packs.cp38_data_etl.models import (
            TransformConfig,
            TransformType,
        )

        c = TransformConfig(
            step_type=TransformType.MAP,
            params={"field": "status", "mapping": {"active": 1}},
        )
        assert c.step_type == TransformType.MAP

    def test_transform_config_to_dict(self):
        from midicoder.packs.cp38_data_etl.models import (
            TransformConfig,
            TransformType,
        )

        c = TransformConfig(step_type=TransformType.FILTER, params={"condition": "x > 0"})
        d = c.to_dict()
        assert d["step_type"] == "filter"
        assert d["params"]["condition"] == "x > 0"

    def test_transform_config_from_dict(self):
        from midicoder.packs.cp38_data_etl.models import (
            TransformConfig,
            TransformType,
        )

        data = {"step_type": "convert", "params": {"target_type": "int"}}
        c = TransformConfig.from_dict(data)
        assert c.step_type == TransformType.CONVERT


# ============================================================================
# Test LoadConfig
# ============================================================================


class TestLoadConfig:
    """Tests cho LoadConfig model."""

    def test_load_config_empty_target_entity_raises_error(self):
        from midicoder.packs.cp38_data_etl.models import LoadConfig

        with pytest.raises(MidicoderError):
            LoadConfig(target_entity="")

    def test_load_config_to_dict(self):
        from midicoder.packs.cp38_data_etl.models import (
            LoadConfig,
            LoadMode,
        )

        c = LoadConfig(
            target_entity="users",
            mode=LoadMode.UPSERT,
            upsert_key="user_id",
        )
        d = c.to_dict()
        assert d["target_entity"] == "users"
        assert d["mode"] == "upsert"
        assert d["upsert_key"] == "user_id"

    def test_load_config_from_dict(self):
        from midicoder.packs.cp38_data_etl.models import (
            LoadConfig,
            LoadMode,
        )

        data = {"target_entity": "orders", "mode": "delete"}
        c = LoadConfig.from_dict(data)
        assert c.target_entity == "orders"
        assert c.mode == LoadMode.DELETE


# ============================================================================
# Test ETLStep
# ============================================================================


class TestETLStep:
    """Tests cho ETLStep model."""

    def test_etl_step_empty_step_key_raises_error(self):
        from midicoder.packs.cp38_data_etl.models import ETLStep

        with pytest.raises(MidicoderError):
            ETLStep(step_key="", step_type="extract")

    def test_etl_step_to_dict(self):
        from midicoder.packs.cp38_data_etl.models import ETLStep

        s = ETLStep(
            step_key="extract_1",
            step_type="extract",
            config={"source": "file"},
            order=0,
        )
        d = s.to_dict()
        assert d["step_key"] == "extract_1"
        assert d["step_type"] == "extract"
        assert d["order"] == 0

    def test_etl_step_from_dict(self):
        from midicoder.packs.cp38_data_etl.models import ETLStep

        data = {
            "step_key": "load_1",
            "step_type": "load",
            "config": {"target": "users"},
            "order": 2,
        }
        s = ETLStep.from_dict(data)
        assert s.step_key == "load_1"
        assert s.step_type == "load"
        assert s.order == 2


# ============================================================================
# Test ETLJob
# ============================================================================


class TestETLJob:
    """Tests cho ETLJob model."""

    def test_etl_job_creation(self):
        from midicoder.packs.cp38_data_etl.models import (
            ETLJob,
            ETLStep,
        )

        steps = [
            ETLStep(step_key="ext", step_type="extract", order=0),
            ETLStep(step_key="load", step_type="load", order=1),
        ]
        job = ETLJob(job_key="migrate_1", steps=steps)
        assert job.job_key == "migrate_1"
        assert len(job.steps) == 2

    def test_etl_job_missing_extract_step_raises_error(self):
        from midicoder.packs.cp38_data_etl.models import (
            ETLJob,
            ETLStep,
        )

        steps = [ETLStep(step_key="load", step_type="load", order=0)]
        with pytest.raises(MidicoderError):
            ETLJob(job_key="bad", steps=steps)

    def test_etl_job_missing_load_step_raises_error(self):
        from midicoder.packs.cp38_data_etl.models import (
            ETLJob,
            ETLStep,
        )

        steps = [ETLStep(step_key="ext", step_type="extract", order=0)]
        with pytest.raises(MidicoderError):
            ETLJob(job_key="bad", steps=steps)

    def test_etl_job_to_dict(self):
        from midicoder.packs.cp38_data_etl.models import (
            ETLJob,
            ETLStep,
        )

        steps = [
            ETLStep(step_key="ext", step_type="extract", order=0),
            ETLStep(step_key="load", step_type="load", order=1),
        ]
        job = ETLJob(job_key="dict_job", steps=steps)
        d = job.to_dict()
        assert d["job_key"] == "dict_job"
        assert len(d["steps"]) == 2

    def test_etl_job_from_dict(self):
        from midicoder.packs.cp38_data_etl.models import ETLJob

        data = {
            "job_key": "restored_etl",
            "steps": [
                {"step_key": "e", "step_type": "extract", "order": 0},
                {"step_key": "l", "step_type": "load", "order": 1},
            ],
            "status": "running",
        }
        job = ETLJob.from_dict(data)
        assert job.job_key == "restored_etl"
        assert len(job.steps) == 2


# ============================================================================
# Test ImportError
# ============================================================================


class TestImportError:
    """Tests cho ImportError model."""

    def test_import_error_creation(self):
        from midicoder.packs.cp38_data_etl.models import ImportError

        err = ImportError(
            row_number=5,
            column="email",
            error_message="invalid format",
        )
        assert err.row_number == 5
        assert err.column == "email"
        assert err.error_message == "invalid format"

    def test_import_error_to_dict(self):
        from midicoder.packs.cp38_data_etl.models import ImportError

        err = ImportError(row_number=10, column="age", error_message="not a number")
        d = err.to_dict()
        assert d["row_number"] == 10
        assert d["column"] == "age"

    def test_import_error_from_dict(self):
        from midicoder.packs.cp38_data_etl.models import ImportError

        data = {"row_number": 20, "column": "phone", "error_message": "bad format"}
        err = ImportError.from_dict(data)
        assert err.row_number == 20
        assert err.error_message == "bad format"


# ============================================================================
# Test BulkConfig
# ============================================================================


class TestBulkConfig:
    """Tests cho BulkConfig model."""

    def test_bulk_config_chunk_size_zero_raises_error(self):
        from midicoder.packs.cp38_data_etl.models import BulkConfig

        with pytest.raises(MidicoderError):
            BulkConfig(chunk_size=0)

    def test_bulk_config_chunk_size_negative_raises_error(self):
        from midicoder.packs.cp38_data_etl.models import BulkConfig

        with pytest.raises(MidicoderError):
            BulkConfig(chunk_size=-1)

    def test_bulk_config_to_dict(self):
        from midicoder.packs.cp38_data_etl.models import BulkConfig

        c = BulkConfig(chunk_size=500, max_retries=5, rollback_threshold=0.05)
        d = c.to_dict()
        assert d["chunk_size"] == 500
        assert d["max_retries"] == 5
        assert d["rollback_threshold"] == 0.05

    def test_bulk_config_from_dict(self):
        from midicoder.packs.cp38_data_etl.models import BulkConfig

        data = {"chunk_size": 2000, "max_retries": 1, "rollback_threshold": 0.2}
        c = BulkConfig.from_dict(data)
        assert c.chunk_size == 2000
        assert c.max_retries == 1

    def test_bulk_config_defaults(self):
        from midicoder.packs.cp38_data_etl.models import BulkConfig

        c = BulkConfig()
        assert c.chunk_size == 1000
        assert c.max_retries == 3
        assert c.rollback_threshold == 0.1


# ============================================================================
# Test Schema Evolution Error Codes
# ============================================================================


class TestCP38SchemaErrorCodes:
    """Tests cho CP38 schema evolution error codes."""

    def test_cp38_schema_not_found_exists(self):
        assert hasattr(ErrorCode, "CP38_SCHEMA_NOT_FOUND")
        assert ErrorCode.CP38_SCHEMA_NOT_FOUND == "MDC-CP38-019"

    def test_cp38_duplicate_schema_id_exists(self):
        assert hasattr(ErrorCode, "CP38_DUPLICATE_SCHEMA_ID")
        assert ErrorCode.CP38_DUPLICATE_SCHEMA_ID == "MDC-CP38-020"

    def test_cp38_invalid_schema_format_exists(self):
        assert hasattr(ErrorCode, "CP38_INVALID_SCHEMA_FORMAT")
        assert ErrorCode.CP38_INVALID_SCHEMA_FORMAT == "MDC-CP38-021"

    def test_cp38_incompatible_schema_exists(self):
        assert hasattr(ErrorCode, "CP38_INCOMPATIBLE_SCHEMA")
        assert ErrorCode.CP38_INCOMPATIBLE_SCHEMA == "MDC-CP38-022"

    def test_cp38_schema_registry_unavailable_exists(self):
        assert hasattr(ErrorCode, "CP38_SCHEMA_REGISTRY_UNAVAILABLE")
        assert ErrorCode.CP38_SCHEMA_REGISTRY_UNAVAILABLE == "MDC-CP38-023"


# ============================================================================
# Test Schema Format & Compatibility Enums
# ============================================================================


class TestSchemaEvolutionEnums:
    """Tests cho Schema Evolution enums."""

    # SchemaFormat
    def test_schema_format_avro(self):
        from midicoder.packs.cp38_data_etl.models import SchemaFormat
        assert SchemaFormat.AVRO.value == "avro"

    def test_schema_format_protobuf(self):
        from midicoder.packs.cp38_data_etl.models import SchemaFormat
        assert SchemaFormat.PROTOBUF.value == "protobuf"

    def test_schema_format_json_schema(self):
        from midicoder.packs.cp38_data_etl.models import SchemaFormat
        assert SchemaFormat.JSON_SCHEMA.value == "json_schema"

    def test_schema_format_sql(self):
        from midicoder.packs.cp38_data_etl.models import SchemaFormat
        assert SchemaFormat.SQL.value == "sql"

    # CompatibilityMode
    def test_compatibility_mode_backward(self):
        from midicoder.packs.cp38_data_etl.models import CompatibilityMode
        assert CompatibilityMode.BACKWARD.value == "backward"

    def test_compatibility_mode_forward(self):
        from midicoder.packs.cp38_data_etl.models import CompatibilityMode
        assert CompatibilityMode.FORWARD.value == "forward"

    def test_compatibility_mode_backward_forward(self):
        from midicoder.packs.cp38_data_etl.models import CompatibilityMode
        assert CompatibilityMode.BACKWARD_FORWARD.value == "backward_forward"

    def test_compatibility_mode_full(self):
        from midicoder.packs.cp38_data_etl.models import CompatibilityMode
        assert CompatibilityMode.FULL.value == "full"

    def test_compatibility_mode_none(self):
        from midicoder.packs.cp38_data_etl.models import CompatibilityMode
        assert CompatibilityMode.NONE.value == "none"


# ============================================================================
# Test SchemaDefinition
# ============================================================================


class TestSchemaDefinition:
    """Tests cho SchemaDefinition model."""

    def test_schema_definition_creation(self):
        from midicoder.packs.cp38_data_etl.models import (
            SchemaDefinition,
            SchemaFormat,
        )

        s = SchemaDefinition(
            id="schema_users_v1",
            name="users_schema",
            format=SchemaFormat.AVRO,
            version="1.0.0",
            subject="users-value",
            schema_content='{"type": "record", "name": "User"}',
        )
        assert s.id == "schema_users_v1"
        assert s.name == "users_schema"
        assert s.format == SchemaFormat.AVRO
        assert s.version == "1.0.0"
        assert s.subject == "users-value"

    def test_schema_definition_defaults(self):
        from midicoder.packs.cp38_data_etl.models import (
            SchemaDefinition,
            SchemaFormat,
        )

        s = SchemaDefinition(
            id="schema_test",
            name="test_schema",
            format=SchemaFormat.JSON_SCHEMA,
        )
        assert s.version == "1.0.0"
        assert s.subject == ""
        assert s.schema_content == ""
        assert s.properties == {}

    def test_schema_definition_empty_id_raises_error(self):
        from midicoder.packs.cp38_data_etl.models import (
            SchemaDefinition,
            SchemaFormat,
        )

        with pytest.raises(MidicoderError):
            SchemaDefinition(
                id="",
                name="test_schema",
                format=SchemaFormat.AVRO,
            )

    def test_schema_definition_empty_name_raises_error(self):
        from midicoder.packs.cp38_data_etl.models import (
            SchemaDefinition,
            SchemaFormat,
        )

        with pytest.raises(MidicoderError):
            SchemaDefinition(
                id="schema_test",
                name="",
                format=SchemaFormat.AVRO,
            )

    def test_schema_definition_to_dict(self):
        from midicoder.packs.cp38_data_etl.models import (
            SchemaDefinition,
            SchemaFormat,
        )

        s = SchemaDefinition(
            id="schema_orders",
            name="orders_schema",
            format=SchemaFormat.PROTOBUF,
            version="2.1.0",
            subject="orders-value",
            schema_content="syntax = 'proto3';",
            properties={"auto_register": True},
        )
        d = s.to_dict()
        assert d["id"] == "schema_orders"
        assert d["name"] == "orders_schema"
        assert d["format"] == "protobuf"
        assert d["version"] == "2.1.0"
        assert d["properties"]["auto_register"] is True

    def test_schema_definition_from_dict(self):
        from midicoder.packs.cp38_data_etl.models import (
            SchemaDefinition,
            SchemaFormat,
        )

        data = {
            "id": "restored_schema",
            "name": "restored_name",
            "format": "sql",
            "version": "3.0.0",
            "subject": "restored-value",
            "schema_content": "CREATE TABLE t (id INT);",
            "properties": {"key": "value"},
        }
        s = SchemaDefinition.from_dict(data)
        assert s.id == "restored_schema"
        assert s.format == SchemaFormat.SQL
        assert s.version == "3.0.0"
        assert s.properties == {"key": "value"}


# ============================================================================
# Test SchemaRegistryConfig
# ============================================================================


class TestSchemaRegistryConfig:
    """Tests cho SchemaRegistryConfig model."""

    def test_schema_registry_config_creation(self):
        from midicoder.packs.cp38_data_etl.models import (
            CompatibilityMode,
            SchemaFormat,
            SchemaRegistryConfig,
        )

        c = SchemaRegistryConfig(
            id="registry_prod",
            name="Production Registry",
            url="http://localhost:8081",
            format=SchemaFormat.AVRO,
            compatibility_mode=CompatibilityMode.BACKWARD,
        )
        assert c.id == "registry_prod"
        assert c.name == "Production Registry"
        assert c.url == "http://localhost:8081"
        assert c.format == SchemaFormat.AVRO
        assert c.compatibility_mode == CompatibilityMode.BACKWARD

    def test_schema_registry_config_defaults(self):
        from midicoder.packs.cp38_data_etl.models import (
            CompatibilityMode,
            SchemaFormat,
            SchemaRegistryConfig,
        )

        c = SchemaRegistryConfig(
            id="reg_test",
            name="Test Registry",
        )
        assert c.url == ""
        assert c.format == SchemaFormat.AVRO
        assert c.compatibility_mode == CompatibilityMode.BACKWARD
        assert c.auth_enabled is False
        assert c.schema_lookup_max_size == 1000

    def test_schema_registry_config_with_auth(self):
        from midicoder.packs.cp38_data_etl.models import SchemaRegistryConfig

        c = SchemaRegistryConfig(
            id="reg_auth",
            name="Auth Registry",
            auth_enabled=True,
            auth_basic_user="admin",
            auth_basic_password="secret",
        )
        assert c.auth_enabled is True
        assert c.auth_basic_user == "admin"
        assert c.auth_basic_password == "secret"

    def test_schema_registry_config_empty_id_raises_error(self):
        from midicoder.packs.cp38_data_etl.models import SchemaRegistryConfig

        with pytest.raises(MidicoderError):
            SchemaRegistryConfig(id="", name="test")

    def test_schema_registry_config_empty_name_raises_error(self):
        from midicoder.packs.cp38_data_etl.models import SchemaRegistryConfig

        with pytest.raises(MidicoderError):
            SchemaRegistryConfig(id="reg_test", name="")

    def test_schema_registry_config_invalid_lookup_size_raises_error(self):
        from midicoder.packs.cp38_data_etl.models import SchemaRegistryConfig

        with pytest.raises(MidicoderError):
            SchemaRegistryConfig(
                id="reg_test",
                name="test",
                schema_lookup_max_size=0,
            )

    def test_schema_registry_config_to_dict(self):
        from midicoder.packs.cp38_data_etl.models import (
            CompatibilityMode,
            SchemaFormat,
            SchemaRegistryConfig,
        )

        c = SchemaRegistryConfig(
            id="reg_dict",
            name="Dict Registry",
            url="http://registry:8081",
            format=SchemaFormat.PROTOBUF,
            compatibility_mode=CompatibilityMode.FULL,
            auth_enabled=True,
            auth_basic_user="user",
            auth_basic_password="pass",
            schema_lookup_max_size=500,
        )
        d = c.to_dict()
        assert d["id"] == "reg_dict"
        assert d["format"] == "protobuf"
        assert d["compatibility_mode"] == "full"
        assert d["auth_enabled"] is True
        assert d["schema_lookup_max_size"] == 500

    def test_schema_registry_config_from_dict(self):
        from midicoder.packs.cp38_data_etl.models import (
            CompatibilityMode,
            SchemaFormat,
            SchemaRegistryConfig,
        )

        data = {
            "id": "restored_reg",
            "name": "Restored Registry",
            "url": "http://localhost:9092",
            "format": "json_schema",
            "compatibility_mode": "forward",
            "auth_enabled": False,
            "auth_basic_user": "",
            "auth_basic_password": "",
            "schema_lookup_max_size": 2000,
        }
        c = SchemaRegistryConfig.from_dict(data)
        assert c.id == "restored_reg"
        assert c.format == SchemaFormat.JSON_SCHEMA
        assert c.compatibility_mode == CompatibilityMode.FORWARD
        assert c.schema_lookup_max_size == 2000


# ============================================================================
# Test SchemaEvolutionRule
# ============================================================================


class TestSchemaEvolutionRule:
    """Tests cho SchemaEvolutionRule model."""

    def test_schema_evolution_rule_creation(self):
        from midicoder.packs.cp38_data_etl.models import SchemaEvolutionRule

        r = SchemaEvolutionRule(
            id="rule_users",
            schema_id="schema_users_v1",
            allowed_operations=["add_field", "add_enum_value"],
            auto_evolve=False,
            require_approval=True,
            notification_channels=["slack", "email"],
        )
        assert r.id == "rule_users"
        assert r.schema_id == "schema_users_v1"
        assert len(r.allowed_operations) == 2
        assert r.auto_evolve is False
        assert r.require_approval is True

    def test_schema_evolution_rule_defaults(self):
        from midicoder.packs.cp38_data_etl.models import SchemaEvolutionRule

        r = SchemaEvolutionRule(
            id="rule_default",
            schema_id="schema_test",
        )
        assert r.allowed_operations == []
        assert r.auto_evolve is False
        assert r.require_approval is True
        assert r.notification_channels == []

    def test_schema_evolution_rule_auto_evolve(self):
        from midicoder.packs.cp38_data_etl.models import SchemaEvolutionRule

        r = SchemaEvolutionRule(
            id="rule_auto",
            schema_id="schema_auto",
            allowed_operations=["add_field", "remove_field", "change_type", "add_enum_value"],
            auto_evolve=True,
            require_approval=False,
        )
        assert r.auto_evolve is True
        assert r.require_approval is False
        assert len(r.allowed_operations) == 4

    def test_schema_evolution_rule_empty_id_raises_error(self):
        from midicoder.packs.cp38_data_etl.models import SchemaEvolutionRule

        with pytest.raises(MidicoderError):
            SchemaEvolutionRule(id="", schema_id="schema_test")

    def test_schema_evolution_rule_empty_schema_id_raises_error(self):
        from midicoder.packs.cp38_data_etl.models import SchemaEvolutionRule

        with pytest.raises(MidicoderError):
            SchemaEvolutionRule(id="rule_test", schema_id="")

    def test_schema_evolution_rule_to_dict(self):
        from midicoder.packs.cp38_data_etl.models import SchemaEvolutionRule

        r = SchemaEvolutionRule(
            id="rule_dict",
            schema_id="schema_dict",
            allowed_operations=["add_field"],
            auto_evolve=True,
            require_approval=False,
            notification_channels=["slack"],
        )
        d = r.to_dict()
        assert d["id"] == "rule_dict"
        assert d["schema_id"] == "schema_dict"
        assert d["allowed_operations"] == ["add_field"]
        assert d["auto_evolve"] is True
        assert d["notification_channels"] == ["slack"]

    def test_schema_evolution_rule_from_dict(self):
        from midicoder.packs.cp38_data_etl.models import SchemaEvolutionRule

        data = {
            "id": "restored_rule",
            "schema_id": "restored_schema",
            "allowed_operations": ["add_field", "remove_field"],
            "auto_evolve": True,
            "require_approval": False,
            "notification_channels": ["email", "pagerduty"],
        }
        r = SchemaEvolutionRule.from_dict(data)
        assert r.id == "restored_rule"
        assert r.schema_id == "restored_schema"
        assert len(r.allowed_operations) == 2
        assert r.auto_evolve is True
        assert len(r.notification_channels) == 2
