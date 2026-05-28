# coding: utf-8
"""
Tests cho Core DB Models (CP08).

Bao gom:
- ColumnDef, Relationship, IndexDef
- DataModel, DataModelCollection
- Datasource, ReplicaConfig, DatabaseEngine
- Spatial types: SpatialColumn, SpatialIndex, SpatialType, SpatialIndexType
- Time-series: TimeSeriesModel, RetentionPolicy, TimeSeriesGranularity, RetentionPolicyType
- CQRS: ReadModel, ReadModelSource, RefreshStrategy
- Distributed TX: DistributedTransaction, TransactionParticipant, DistributedTxProtocol, ParticipantStatus
- JSONB: JSONBColumn, JSONBIndex, JSONBIndexType, JSONBValidationMode
- KPI-029 Tenant Isolation
- Validation (__post_init__)
- Error codes
"""

import pytest
from pathlib import Path

from midicoder.packs.cp_backend_database.models import (
    ColumnDef,
    ColumnType,
    DataModel,
    DataModelCollection,
    DatabaseEngine,
    Datasource,
    IndexDef,
    Relationship,
    RelationshipType,
    ReplicaConfig,
    # Spatial
    SpatialColumn,
    SpatialIndex,
    SpatialIndexType,
    SpatialType,
    # Time-series
    RetentionPolicy,
    RetentionPolicyType,
    TimeSeriesGranularity,
    TimeSeriesModel,
    # CQRS
    ReadModel,
    ReadModelSource,
    RefreshStrategy,
    # Distributed TX
    DistributedTransaction,
    DistributedTxProtocol,
    ParticipantStatus,
    TransactionParticipant,
    # JSONB
    JSONBColumn,
    JSONBIndex,
    JSONBIndexType,
    JSONBValidationMode,
)
from midicoder.errors import ErrorCode, MidicoderError


# ============================================================================
# ColumnDef
# ============================================================================


class TestColumnDef:
    def test_create_string_column(self):
        col = ColumnDef(name="email", column_type=ColumnType.STRING, max_length=255)
        assert col.name == "email"
        assert col.column_type == ColumnType.STRING
        assert col.max_length == 255
        assert col.required is False
        assert col.tenant_aware is False

    def test_create_required_column(self):
        col = ColumnDef(name="name", column_type=ColumnType.STRING, required=True)
        assert col.required is True

    def test_create_all_column_types(self):
        for ct in ColumnType:
            col = ColumnDef(name="test", column_type=ct)
            assert col.column_type == ct

    def test_create_tenant_aware_column(self):
        col = ColumnDef(name="tenant_id", column_type=ColumnType.STRING, tenant_aware=True)
        assert col.tenant_aware is True

    def test_to_dict_and_from_dict(self):
        original = ColumnDef(
            name="total",
            column_type=ColumnType.DECIMAL,
            precision=10,
            scale=2,
            required=True,
            tenant_aware=False,
        )
        d = original.to_dict()
        restored = ColumnDef.from_dict(d)
        assert restored.name == original.name
        assert restored.column_type == original.column_type
        assert restored.precision == original.precision
        assert restored.scale == original.scale
        assert restored.required == original.required

    def test_empty_name_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            ColumnDef(name="", column_type=ColumnType.STRING)
        assert exc_info.value.code == ErrorCode.MDC-BE01_EMPTY_NAME

    def test_negative_precision_clamped(self):
        col = ColumnDef(name="x", column_type=ColumnType.DECIMAL, precision=-1)
        assert col.precision == 10

    def test_negative_scale_clamped(self):
        col = ColumnDef(name="x", column_type=ColumnType.DECIMAL, scale=-5)
        assert col.scale == 0

    def test_array_column_type(self):
        col = ColumnDef(name="tags", column_type=ColumnType.ARRAY)
        assert col.column_type == ColumnType.ARRAY

    def test_bytes_column_type(self):
        col = ColumnDef(name="data", column_type=ColumnType.BYTES)
        assert col.column_type == ColumnType.BYTES

    def test_time_column_type(self):
        col = ColumnDef(name="started_at", column_type=ColumnType.TIME)
        assert col.column_type == ColumnType.TIME


# ============================================================================
# Relationship
# ============================================================================


class TestRelationship:
    def test_create_many_to_one(self):
        rel = Relationship(
            target_model="User",
            rel_type=RelationshipType.MANY_TO_ONE,
            foreign_key="user_id",
        )
        assert rel.target_model == "User"
        assert rel.rel_type == RelationshipType.MANY_TO_ONE
        assert rel.tenant_scoped is True

    def test_create_one_to_many(self):
        rel = Relationship(
            target_model="OrderItem",
            rel_type=RelationshipType.ONE_TO_MANY,
            back_ref="order",
        )
        assert rel.rel_type == RelationshipType.ONE_TO_MANY

    def test_m2m_auto_join_table(self):
        rel = Relationship(
            target_model="Tag",
            rel_type=RelationshipType.MANY_TO_MANY,
        )
        assert rel.join_table  # auto-generated

    def test_to_dict_and_from_dict(self):
        original = Relationship(
            target_model="Category",
            rel_type=RelationshipType.MANY_TO_MANY,
            join_table="product_category",
            tenant_scoped=True,
        )
        d = original.to_dict()
        restored = Relationship.from_dict(d)
        assert restored.target_model == original.target_model
        assert restored.join_table == original.join_table
        assert restored.tenant_scoped == original.tenant_scoped

    def test_empty_target_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            Relationship(target_model="", rel_type=RelationshipType.MANY_TO_ONE)
        assert exc_info.value.code == ErrorCode.MDC-BE01_EMPTY_NAME


# ============================================================================
# IndexDef
# ============================================================================


class TestIndexDef:
    def test_create_index(self):
        idx = IndexDef(name="idx_email", columns=["email"], unique=True)
        assert idx.unique is True

    def test_to_dict_and_from_dict(self):
        idx = IndexDef(name="idx_tenant", columns=["tenant_id"])
        d = idx.to_dict()
        restored = IndexDef.from_dict(d)
        assert restored.name == idx.name

    def test_empty_name_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            IndexDef(name="", columns=["col"])
        assert exc_info.value.code == ErrorCode.MDC-BE01_EMPTY_NAME


# ============================================================================
# DataModel
# ============================================================================


class TestDataModel:
    def test_create_simple_model(self):
        model = DataModel(
            id="User",
            table_name="users",
            columns=[ColumnDef(name="id", column_type=ColumnType.UUID, primary_key=True)],
        )
        assert model.id == "User"
        assert model.get_primary_key().name == "id"

    def test_tenant_model(self):
        model = DataModel(
            id="Order",
            table_name="orders",
            columns=[
                ColumnDef(name="id", column_type=ColumnType.UUID, primary_key=True),
                ColumnDef(name="tenant_id", column_type=ColumnType.STRING, tenant_aware=True),
            ],
            tenant_isolated=True,
        )
        assert model.has_tenant_column() is True
        assert model.tenant_isolated is True

    def test_no_tenant_column(self):
        model = DataModel(
            id="Config",
            table_name="configs",
            columns=[ColumnDef(name="id", column_type=ColumnType.UUID, primary_key=True)],
        )
        assert model.has_tenant_column() is False

    def test_duplicate_columns_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            DataModel(
                id="Test", table_name="test", columns=[
                    ColumnDef(name="id", column_type=ColumnType.UUID, primary_key=True),
                    ColumnDef(name="id", column_type=ColumnType.STRING),
                ]
            )
        assert exc_info.value.code == ErrorCode.MDC-BE01_DUPLICATE_COLUMN_NAME

    def test_missing_pk_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            DataModel(
                id="Test", table_name="test",
                columns=[ColumnDef(name="name", column_type=ColumnType.STRING)],
            )
        assert exc_info.value.code == ErrorCode.MDC-BE01_MISSING_PRIMARY_KEY

    def test_empty_id_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            DataModel(id="", table_name="test")
        assert exc_info.value.code == ErrorCode.MDC-BE01_EMPTY_NAME

    def test_empty_table_name_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            DataModel(id="Test", table_name="")
        assert exc_info.value.code == ErrorCode.MDC-BE01_EMPTY_NAME

    def test_to_dict_and_from_dict(self):
        original = DataModel(
            id="Order",
            table_name="orders",
            description="Orders table",
            columns=[ColumnDef(name="id", column_type=ColumnType.UUID, primary_key=True)],
            relationships=[Relationship(target_model="User", rel_type=RelationshipType.MANY_TO_ONE)],
            tenant_isolated=True,
        )
        d = original.to_dict()
        restored = DataModel.from_dict(d)
        assert restored.id == original.id
        assert restored.tenant_isolated == original.tenant_isolated
        assert len(restored.relationships) == 1

    def test_model_with_no_columns_no_pk_error(self):
        model = DataModel(id="Empty", table_name="empty")
        assert len(model.columns) == 0


# ============================================================================
# DataModelCollection
# ============================================================================


class TestDataModelCollection:
    def test_add_and_count(self):
        collection = DataModelCollection()
        collection.add_model(DataModel(id="User", table_name="users", columns=[
            ColumnDef(name="id", column_type=ColumnType.UUID, primary_key=True)]))
        assert collection.total_count == 1

    def test_get_by_id(self):
        collection = DataModelCollection()
        m = DataModel(id="Product", table_name="products", columns=[
            ColumnDef(name="id", column_type=ColumnType.UUID, primary_key=True)])
        collection.add_model(m)
        assert collection.get_by_id("Product") is not None
        assert collection.get_by_id("Missing") is None

    def test_tenant_isolated_filter(self):
        collection = DataModelCollection()
        collection.add_model(DataModel(id="A", table_name="a", tenant_isolated=True, columns=[
            ColumnDef(name="id", column_type=ColumnType.UUID, primary_key=True)]))
        collection.add_model(DataModel(id="B", table_name="b", tenant_isolated=False, columns=[
            ColumnDef(name="id", column_type=ColumnType.UUID, primary_key=True)]))
        result = collection.tenant_isolated_models()
        assert len(result) == 1

    def test_duplicate_table_raises_error(self):
        collection = DataModelCollection()
        collection.add_model(DataModel(id="A", table_name="users", columns=[
            ColumnDef(name="id", column_type=ColumnType.UUID, primary_key=True)]))
        with pytest.raises(MidicoderError) as exc_info:
            collection.add_model(DataModel(id="B", table_name="users", columns=[
                ColumnDef(name="id", column_type=ColumnType.UUID, primary_key=True)]))
        assert exc_info.value.code == ErrorCode.MDC-BE01_DUPLICATE_TABLE_NAME

    def test_to_dict_and_from_dict(self):
        collection = DataModelCollection()
        collection.add_model(DataModel(id="M", table_name="m", columns=[
            ColumnDef(name="id", column_type=ColumnType.UUID, primary_key=True)]))
        d = collection.to_dict()
        restored = DataModelCollection.from_dict(d)
        assert restored.total_count == 1

    def test_get_primary_datasource(self):
        collection = DataModelCollection()
        ds = Datasource(name="primary", engine=DatabaseEngine.POSTGRESQL, connection_string="pg://db")
        collection.add_datasource(ds)
        assert collection.get_primary_datasource().name == "primary"


# ============================================================================
# ReplicaConfig & Datasource
# ============================================================================


class TestReplicaConfig:
    def test_create_replica(self):
        r = ReplicaConfig(name="r1", connection_string="pg://r1")
        assert r.weight == 1

    def test_to_dict_and_from_dict(self):
        r = ReplicaConfig(name="r1", connection_string="pg://r1", weight=3)
        d = r.to_dict()
        restored = ReplicaConfig.from_dict(d)
        assert restored.weight == 3

    def test_empty_name_raises_error(self):
        with pytest.raises(MidicoderError):
            ReplicaConfig(name="", connection_string="pg://db")

    def test_negative_weight_clamped(self):
        r = ReplicaConfig(name="r1", connection_string="pg://db", weight=-1)
        assert r.weight == 1


class TestDatasource:
    def test_create_datasource(self):
        ds = Datasource(name="primary", engine=DatabaseEngine.POSTGRESQL, connection_string="pg://db")
        assert ds.pool_size == 10
        assert ds.ssl_enabled is False

    def test_all_engines(self):
        for eng in DatabaseEngine:
            ds = Datasource(name="test", engine=eng, connection_string="conn://db")
            assert ds.engine == eng

    def test_to_dict_and_from_dict(self):
        original = Datasource(
            name="test", engine=DatabaseEngine.SQLSERVER, connection_string="mssql://db",
            pool_size=15, ssl_enabled=True,
        )
        d = original.to_dict()
        restored = Datasource.from_dict(d)
        assert restored.engine == original.engine

    def test_empty_name_raises_error(self):
        with pytest.raises(MidicoderError):
            Datasource(name="", engine=DatabaseEngine.POSTGRESQL, connection_string="pg://db")

    def test_empty_connection_raises_error(self):
        with pytest.raises(MidicoderError):
            Datasource(name="test", engine=DatabaseEngine.POSTGRESQL, connection_string="")


# ============================================================================
# Spatial Types
# ============================================================================


class TestSpatialTypes:
    def test_spatial_column(self):
        sc = SpatialColumn(name="location", spatial_type=SpatialType.POINT, srid=4326)
        assert sc.srid == 4326

    def test_spatial_column_to_dict(self):
        sc = SpatialColumn(name="boundary", spatial_type=SpatialType.POLYGON)
        d = sc.to_dict()
        restored = SpatialColumn.from_dict(d)
        assert restored.spatial_type == SpatialType.POLYGON

    def test_spatial_index(self):
        si = SpatialIndex(name="idx_loc", column="location", index_type=SpatialIndexType.GIST)
        assert si.index_type == SpatialIndexType.GIST

    def test_spatial_index_to_dict(self):
        si = SpatialIndex(name="idx_loc", column="location", index_type=SpatialIndexType.BRIN)
        d = si.to_dict()
        restored = SpatialIndex.from_dict(d)
        assert restored.index_type == SpatialIndexType.BRIN

    def test_spatial_column_empty_name_raises_error(self):
        with pytest.raises(MidicoderError):
            SpatialColumn(name="", spatial_type=SpatialType.POINT)

    def test_spatial_index_empty_name_raises_error(self):
        with pytest.raises(MidicoderError):
            SpatialIndex(name="", column="loc")

    def test_all_spatial_types(self):
        for st in SpatialType:
            sc = SpatialColumn(name="test", spatial_type=st)
            assert sc.spatial_type == st

    def test_all_spatial_index_types(self):
        for sit in SpatialIndexType:
            si = SpatialIndex(name="idx", column="loc", index_type=sit)
            assert si.index_type == sit


# ============================================================================
# Time-Series
# ============================================================================


class TestTimeSeries:
    def test_retention_policy(self):
        rp = RetentionPolicy(name="metrics_90d", policy_type=RetentionPolicyType.TIME_BASED, threshold=7776000)
        assert rp.threshold == 7776000

    def test_retention_policy_to_dict(self):
        rp = RetentionPolicy(name="r1", policy_type=RetentionPolicyType.COUNT_BASED, threshold=10000)
        d = rp.to_dict()
        restored = RetentionPolicy.from_dict(d)
        assert restored.policy_type == RetentionPolicyType.COUNT_BASED

    def test_time_series_model(self):
        ts = TimeSeriesModel(
            id="cpu_metrics", table_name="cpu_metrics",
            timestamp_column="recorded_at",
            value_columns=["usage_percent"],
            grain_columns=["host"],
            granularity=TimeSeriesGranularity.MINUTE,
        )
        assert ts.granularity == TimeSeriesGranularity.MINUTE

    def test_time_series_model_with_retention(self):
        rp = RetentionPolicy(name="90d", policy_type=RetentionPolicyType.TIME_BASED, threshold=7776000)
        ts = TimeSeriesModel(
            id="metrics", table_name="metrics",
            timestamp_column="ts",
            value_columns=["val"],
            retention_policy=rp,
        )
        assert ts.retention_policy is not None

    def test_time_series_to_dict(self):
        ts = TimeSeriesModel(id="ts1", table_name="ts1", timestamp_column="ts", value_columns=["v"])
        d = ts.to_dict()
        restored = TimeSeriesModel.from_dict(d)
        assert restored.id == "ts1"

    def test_time_series_empty_id_raises_error(self):
        with pytest.raises(MidicoderError):
            TimeSeriesModel(id="", table_name="t", timestamp_column="ts")

    def test_all_granularities(self):
        for g in TimeSeriesGranularity:
            ts = TimeSeriesModel(id="t", table_name="t", timestamp_column="ts", granularity=g)
            assert ts.granularity == g

    def test_all_retention_types(self):
        for rt in RetentionPolicyType:
            rp = RetentionPolicy(name="r", policy_type=rt)
            assert rp.policy_type == rt


# ============================================================================
# CQRS Read Models
# ============================================================================


class TestCQRSReadModel:
    def test_read_model(self):
        rm = ReadModel(
            id="order_view", table_name="order_view",
            source=ReadModelSource.MATERIALIZED_VIEW,
            source_models=["Order", "OrderItem"],
            refresh_strategy=RefreshStrategy.EVENT_DRIVEN,
        )
        assert rm.source == ReadModelSource.MATERIALIZED_VIEW

    def test_read_model_to_dict(self):
        rm = ReadModel(
            id="rm1", table_name="rm1",
            source=ReadModelSource.DENORMALIZED_TABLE,
            refresh_strategy=RefreshStrategy.BATCH,
            refresh_interval_seconds=600,
        )
        d = rm.to_dict()
        restored = ReadModel.from_dict(d)
        assert restored.refresh_strategy == RefreshStrategy.BATCH

    def test_read_model_empty_id_raises_error(self):
        with pytest.raises(MidicoderError):
            ReadModel(id="", table_name="t", source=ReadModelSource.SEARCH_INDEX)

    def test_all_read_model_sources(self):
        for s in ReadModelSource:
            rm = ReadModel(id="r", table_name="r", source=s)
            assert rm.source == s

    def test_all_refresh_strategies(self):
        for rs in RefreshStrategy:
            rm = ReadModel(id="r", table_name="r", source=ReadModelSource.MATERIALIZED_VIEW, refresh_strategy=rs)
            assert rm.refresh_strategy == rs


# ============================================================================
# Distributed Transactions
# ============================================================================


class TestDistributedTransaction:
    def test_transaction_participant(self):
        tp = TransactionParticipant(datasource_name="primary", role="coordinator", timeout_seconds=60)
        assert tp.can_compensate is True

    def test_participant_to_dict(self):
        tp = TransactionParticipant(datasource_name="ds1", role="participant")
        d = tp.to_dict()
        restored = TransactionParticipant.from_dict(d)
        assert restored.role == "participant"

    def test_distributed_transaction(self):
        dt = DistributedTransaction(
            id="order_tx", protocol=DistributedTxProtocol.SAGA,
            coordinator_datasource="primary",
            participants=[TransactionParticipant(datasource_name="payments", role="participant")],
        )
        assert dt.protocol == DistributedTxProtocol.SAGA

    def test_distributed_tx_to_dict(self):
        dt = DistributedTransaction(
            id="tx1", protocol=DistributedTxProtocol.TWO_PHASE_COMMIT,
            coordinator_datasource="primary",
            retry_count=5,
        )
        d = dt.to_dict()
        restored = DistributedTransaction.from_dict(d)
        assert restored.retry_count == 5

    def test_distributed_tx_empty_id_raises_error(self):
        with pytest.raises(MidicoderError):
            DistributedTransaction(id="", protocol=DistributedTxProtocol.OUTBOX, coordinator_datasource="ds")

    def test_all_protocols(self):
        for p in DistributedTxProtocol:
            dt = DistributedTransaction(id="t", protocol=p, coordinator_datasource="primary")
            assert dt.protocol == p

    def test_all_participant_statuses(self):
        for ps in ParticipantStatus:
            assert ps.value  # enum exists


# ============================================================================
# JSONB
# ============================================================================


class TestJSONB:
    def test_jsonb_column(self):
        jc = JSONBColumn(name="metadata", validation_mode=JSONBValidationMode.SCHEMA, json_schema='{}')
        assert jc.required is False

    def test_jsonb_column_to_dict(self):
        jc = JSONBColumn(
            name="data", validation_mode=JSONBValidationMode.CHECK_CONSTRAINT,
            check_expression="data->>'status' IN ('active')",
        )
        d = jc.to_dict()
        restored = JSONBColumn.from_dict(d)
        assert restored.validation_mode == JSONBValidationMode.CHECK_CONSTRAINT

    def test_jsonb_index(self):
        ji = JSONBIndex(name="idx_meta", column="metadata", index_type=JSONBIndexType.GIN)
        assert ji.index_type == JSONBIndexType.GIN

    def test_jsonb_index_to_dict(self):
        ji = JSONBIndex(name="idx_p", column="data", index_type=JSONBIndexType.GIN_PATH_OPS, path="{customer}")
        d = ji.to_dict()
        restored = JSONBIndex.from_dict(d)
        assert restored.path == "{customer}"

    def test_jsonb_column_empty_name_raises_error(self):
        with pytest.raises(MidicoderError):
            JSONBColumn(name="")

    def test_all_jsonb_index_types(self):
        for jt in JSONBIndexType:
            ji = JSONBIndex(name="i", column="c", index_type=jt)
            assert ji.index_type == jt

    def test_all_jsonb_validation_modes(self):
        for vm in JSONBValidationMode:
            jc = JSONBColumn(name="d", validation_mode=vm)
            assert jc.validation_mode == vm
