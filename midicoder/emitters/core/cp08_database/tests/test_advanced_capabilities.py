# coding: utf-8
"""
Tests cho 5 advanced capabilities của CP08:
- spatial (PostGIS columns + indexes)
- time_series (partitioned models + retention)
- cqrs_read_model (materialized views + refresh strategies)
- distributed_transaction (Saga/2PC/Outbox)
- jsonb (JSONB columns + GIN indexes)

Both FastAPI (SQLAlchemy) và NestJS (TypeORM) emitters.
"""

import pytest
from pathlib import Path

from midicoder.emitters.core.cp08_database.models import (
    SpatialColumn,
    SpatialIndex,
    SpatialType,
    SpatialIndexType,
    TimeSeriesModel,
    RetentionPolicy,
    RetentionPolicyType,
    TimeSeriesGranularity,
    ReadModel,
    ReadModelSource,
    RefreshStrategy,
    DistributedTransaction,
    DistributedTxProtocol,
    TransactionParticipant,
    ParticipantStatus,
    JSONBColumn,
    JSONBIndex,
    JSONBIndexType,
    JSONBValidationMode,
    ColumnDef,
    ColumnType,
)
from midicoder.emitters.core.cp08_database.fastapi import SQLAlchemyEmitter
from midicoder.emitters.core.cp08_database.nestjs import TypeORMEmitter


# ============================================================================
# Spatial Tests
# ============================================================================


class TestSpatialFastAPI:
    def test_emit_spatial_columns(self):
        cols = [
            SpatialColumn(name="location", spatial_type=SpatialType.POINT, srid=4326),
            SpatialColumn(name="boundary", spatial_type=SpatialType.POLYGON, srid=3857),
            SpatialColumn(name="route", spatial_type=SpatialType.LINESTRING),
        ]
        emitter = SQLAlchemyEmitter()
        files = emitter.emit_spatial_columns(cols)
        assert "spatial/spatial_helpers.py" in files
        content = files["spatial/spatial_helpers.py"]
        assert "point" in content.lower()
        assert "polygon" in content.lower()
        assert "SRID=4326" in content
        assert "SRID=3857" in content
        assert "spatial_distance" in content
        assert "spatial_contains" in content

    def test_emit_spatial_index(self):
        indexes = [
            SpatialIndex(name="idx_location_gist", column="location", index_type=SpatialIndexType.GIST),
            SpatialIndex(name="idx_route_spgist", column="route", index_type=SpatialIndexType.SPGIST),
        ]
        emitter = SQLAlchemyEmitter()
        files = emitter.emit_spatial_index(indexes)
        assert "spatial/spatial_indexes.py" in files
        content = files["spatial/spatial_indexes.py"]
        assert "idx_location_gist" in content
        assert "gist" in content.lower()
        assert "create_spatial_indexes" in content

    def test_emit_spatial_with_default_srid(self):
        cols = [SpatialColumn(name="pos", spatial_type=SpatialType.GEOMETRY)]
        emitter = SQLAlchemyEmitter()
        files = emitter.emit_spatial_columns(cols)
        content = files["spatial/spatial_helpers.py"]
        assert "SRID=4326" in content  # default WGS84


class TestSpatialNestJS:
    def test_emit_spatial_decorators(self):
        cols = [
            SpatialColumn(name="location", spatial_type=SpatialType.POINT, srid=4326),
        ]
        emitter = TypeORMEmitter()
        files = emitter.emit_spatial_columns(cols)
        assert "spatial/spatial.decorators.ts" in files
        content = files["spatial/spatial.decorators.ts"]
        assert "SpatialColumn" in content
        assert "srid" in content.lower()
        assert "typeorm" in content.lower()

    def test_emit_spatial_indexes(self):
        indexes = [
            SpatialIndex(name="idx_loc", column="location", index_type=SpatialIndexType.GIN),
        ]
        emitter = TypeORMEmitter()
        files = emitter.emit_spatial_index(indexes)
        assert "spatial/spatial-indexes.ts" in files
        content = files["spatial/spatial-indexes.ts"]
        assert "MigrationInterface" in content
        assert "CREATE INDEX" in content


# ============================================================================
# Time-Series Tests
# ============================================================================


class TestTimeSeriesFastAPI:
    def test_emit_time_series_model(self):
        model = TimeSeriesModel(
            id="SensorReading",
            table_name="sensor_readings",
            timestamp_column="recorded_at",
            granularity=TimeSeriesGranularity.SECOND,
            value_columns=["temperature", "humidity"],
            grain_columns=["host"],
        )
        emitter = SQLAlchemyEmitter()
        files = emitter.emit_time_series_model(model)
        key = list(files.keys())[0]
        assert "time_series/" in key
        content = files[key]
        assert "SensorReading" in content
        assert "recorded_at" in content
        assert "create_hypertable" in content

    def test_emit_time_series_with_retention(self):
        retention = RetentionPolicy(name="keep_90d", policy_type=RetentionPolicyType.TIME_BASED, threshold=90)
        model = TimeSeriesModel(
            id="Metrics",
            table_name="metrics",
            timestamp_column="ts",
            granularity=TimeSeriesGranularity.MINUTE,
            value_columns=["value"],
            retention_policy=retention,
        )
        emitter = SQLAlchemyEmitter()
        files = emitter.emit_time_series_model(model)
        content = list(files.values())[0]
        assert "time_based" in content
        assert "add_retention_policy" in content


class TestTimeSeriesNestJS:
    def test_emit_time_series_entity(self):
        model = TimeSeriesModel(
            id="Heartbeat",
            table_name="heartbeats",
            timestamp_column="event_time",
            granularity=TimeSeriesGranularity.HOUR,
            value_columns=["status"],
        )
        emitter = TypeORMEmitter()
        files = emitter.emit_time_series_model(model)
        key = list(files.keys())[0]
        assert "time_series/" in key
        content = files[key]
        assert "Heartbeat" in content
        assert "create_hypertable" in content


# ============================================================================
# CQRS Read Model Tests
# ============================================================================


class TestCQRSReadModelFastAPI:
    def test_emit_read_model_materialized_view(self):
        model = ReadModel(
            id="SalesSummary",
            table_name="sales_summary",
            source=ReadModelSource.MATERIALIZED_VIEW,
            refresh_strategy=RefreshStrategy.BATCH,
            source_models=["orders", "order_items", "products"],
            columns=[
                ColumnDef(name="total_amount", column_type=ColumnType.DECIMAL, required=True),
                ColumnDef(name="order_count", column_type=ColumnType.INTEGER, required=True),
            ],
        )
        emitter = SQLAlchemyEmitter()
        files = emitter.emit_read_model(model)
        key = list(files.keys())[0]
        assert "read_models/" in key
        content = files[key]
        assert "SalesSummary" in content
        assert "materialized_view" in content.lower()
        assert "batch" in content.lower()
        assert "last_refreshed_at" in content

    def test_emit_read_model_event_driven(self):
        model = ReadModel(
            id="UserProfile",
            table_name="user_profiles",
            source=ReadModelSource.DENORMALIZED_TABLE,
            refresh_strategy=RefreshStrategy.EVENT_DRIVEN,
            source_models=["users", "profiles"],
            columns=[ColumnDef(name="display_name", column_type=ColumnType.STRING, required=True)],
        )
        emitter = SQLAlchemyEmitter()
        files = emitter.emit_read_model(model)
        content = list(files.values())[0]
        assert "event_driven" in content.lower()


class TestCQRSReadModelNestJS:
    def test_emit_read_model_entity(self):
        model = ReadModel(
            id="DashboardStats",
            table_name="dashboard_stats",
            source=ReadModelSource.CACHED_COMPUTATION,
            refresh_strategy=RefreshStrategy.LAZY,
            source_models=["stats"],
            columns=[ColumnDef(name="value", column_type=ColumnType.DECIMAL, required=True)],
        )
        emitter = TypeORMEmitter()
        files = emitter.emit_read_model(model)
        key = list(files.keys())[0]
        assert "read_models/" in key
        content = files[key]
        assert "DashboardStats" in content
        assert "lazy" in content.lower()


# ============================================================================
# Distributed Transaction Tests
# ============================================================================


class TestDistributedTransactionFastAPI:
    def test_emit_saga_transaction(self):
        tx = DistributedTransaction(
            id="order-payment",
            protocol=DistributedTxProtocol.SAGA,
            coordinator_datasource="order_db",
            timeout_seconds=30,
            participants=[
                TransactionParticipant(datasource_name="order_db", role="create_order", can_compensate=True),
                TransactionParticipant(datasource_name="payment_db", role="charge_payment", can_compensate=True),
            ],
        )
        emitter = SQLAlchemyEmitter()
        files = emitter.emit_distributed_transaction(tx)
        key = list(files.keys())[0]
        assert "transactions/" in key
        content = files[key]
        assert "Saga" in content
        assert "CREATE_ORDER" in content
        assert "CHARGE_PAYMENT" in content
        assert "compensate" in content

    def test_emit_2pc_transaction(self):
        tx = DistributedTransaction(
            id="fund-transfer",
            protocol=DistributedTxProtocol.TWO_PHASE_COMMIT,
            coordinator_datasource="core_db",
            timeout_seconds=5,
            participants=[
                TransactionParticipant(datasource_name="core_db", role="debit_account", can_compensate=False),
                TransactionParticipant(datasource_name="core_db", role="credit_account", can_compensate=False),
            ],
        )
        emitter = SQLAlchemyEmitter()
        files = emitter.emit_distributed_transaction(tx)
        content = list(files.values())[0]
        assert "Coordinator" in content
        assert "prepare" in content
        assert "commit" in content
        assert "abort" in content

    def test_emit_outbox_transaction(self):
        tx = DistributedTransaction(
            id="order-notification",
            protocol=DistributedTxProtocol.OUTBOX,
            coordinator_datasource="order_db",
            timeout_seconds=10,
            participants=[
                TransactionParticipant(datasource_name="order_db", role="create_order", can_compensate=False),
            ],
        )
        emitter = SQLAlchemyEmitter()
        files = emitter.emit_distributed_transaction(tx)
        content = list(files.values())[0]
        assert "Outbox" in content
        assert "aggregate_type" in content
        assert "published" in content


class TestDistributedTransactionNestJS:
    def test_emit_saga_service(self):
        tx = DistributedTransaction(
            id="checkout-flow",
            protocol=DistributedTxProtocol.SAGA,
            coordinator_datasource="inventory",
            timeout_seconds=30,
            participants=[
                TransactionParticipant(datasource_name="inventory", role="reserve_stock", can_compensate=True),
                TransactionParticipant(datasource_name="payment", role="process_payment", can_compensate=True),
            ],
        )
        emitter = TypeORMEmitter()
        files = emitter.emit_distributed_transaction(tx)
        key = list(files.keys())[0]
        assert "transactions/" in key
        content = files[key]
        assert "Saga" in content
        assert "RESERVE_STOCK" in content
        assert "compensate" in content

    def test_emit_2pc_coordinator(self):
        tx = DistributedTransaction(
            id="account-sync",
            protocol=DistributedTxProtocol.TWO_PHASE_COMMIT,
            coordinator_datasource="profile_db",
            timeout_seconds=10,
            participants=[
                TransactionParticipant(datasource_name="profile_db", role="update_profile", can_compensate=False),
            ],
        )
        emitter = TypeORMEmitter()
        files = emitter.emit_distributed_transaction(tx)
        content = list(files.values())[0]
        assert "Coordinator" in content
        assert "prepare" in content


# ============================================================================
# JSONB Tests
# ============================================================================


class TestJSONBFastAPI:
    def test_emit_jsonb_columns(self):
        cols = [
            JSONBColumn(name="attributes", validation_mode=JSONBValidationMode.SCHEMA),
            JSONBColumn(name="metadata", validation_mode=JSONBValidationMode.NONE),
        ]
        emitter = SQLAlchemyEmitter()
        files = emitter.emit_jsonb_columns(cols)
        assert "jsonb/jsonb_helpers.py" in files
        content = files["jsonb/jsonb_helpers.py"]
        assert "attributes" in content
        assert "metadata" in content
        assert "jsonb_path_query" in content
        assert "jsonb_contains" in content

    def test_emit_jsonb_with_schema_validation(self):
        cols = [JSONBColumn(name="settings", validation_mode=JSONBValidationMode.CHECK_CONSTRAINT)]
        emitter = SQLAlchemyEmitter()
        files = emitter.emit_jsonb_columns(cols)
        content = files["jsonb/jsonb_helpers.py"]
        assert "settings" in content


class TestJSONBNestJS:
    def test_emit_jsonb_decorators(self):
        cols = [
            JSONBColumn(name="data", validation_mode=JSONBValidationMode.SCHEMA),
        ]
        emitter = TypeORMEmitter()
        files = emitter.emit_jsonb_columns(cols)
        assert "jsonb/jsonb.decorators.ts" in files
        content = files["jsonb/jsonb.decorators.ts"]
        assert "JsonbColumn" in content
        assert "JsonbGinIndex" in content
        assert "typeorm" in content.lower()


# ============================================================================
# Integration Tests — All 5 Capabilities
# ============================================================================


class TestAdvancedCapabilityIntegration:
    def test_all_spatial_types_emit(self):
        cols = [SpatialColumn(name=f"col_{t.name}", spatial_type=t) for t in SpatialType]
        fa = SQLAlchemyEmitter()
        nj = TypeORMEmitter()
        fa_files = fa.emit_spatial_columns(cols)
        nj_files = nj.emit_spatial_columns(cols)
        assert len(fa_files) > 0
        assert len(nj_files) > 0

    def test_all_retention_types_emit(self):
        for rt in RetentionPolicyType:
            retention = RetentionPolicy(name=f"ret_{rt.value}", policy_type=rt, threshold=30)
            model = TimeSeriesModel(
                id="Test", table_name="test",
                timestamp_column="ts",
                granularity=TimeSeriesGranularity.DAY,
                value_columns=["v"],
                retention_policy=retention,
            )
            fa = SQLAlchemyEmitter()
            files = fa.emit_time_series_model(model)
            assert len(files) > 0

    def test_all_refresh_strategies_emit(self):
        for rs in RefreshStrategy:
            model = ReadModel(
                id="RM", table_name="rm",
                source=ReadModelSource.MATERIALIZED_VIEW,
                refresh_strategy=rs,
                source_models=["t"],
                columns=[ColumnDef(name="v", column_type=ColumnType.STRING)],
            )
            fa = SQLAlchemyEmitter()
            files = fa.emit_read_model(model)
            assert len(files) > 0

    def test_all_tx_protocols_emit(self):
        for protocol in DistributedTxProtocol:
            tx = DistributedTransaction(
                id=f"tx_{protocol.name}",
                protocol=protocol,
                coordinator_datasource="db",
                timeout_seconds=5,
                participants=[TransactionParticipant(datasource_name="db", role="step1", can_compensate=protocol != DistributedTxProtocol.TWO_PHASE_COMMIT)],
            )
            fa = SQLAlchemyEmitter()
            files = fa.emit_distributed_transaction(tx)
            assert len(files) > 0

    def test_all_jsonb_validation_modes_emit(self):
        for vm in JSONBValidationMode:
            cols = [JSONBColumn(name="j", validation_mode=vm)]
            fa = SQLAlchemyEmitter()
            files = fa.emit_jsonb_columns(cols)
            assert len(files) > 0
