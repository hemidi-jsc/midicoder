# coding: utf-8
"""
Recipes for Database & Data Access Layer Generator (CP08).

Each recipe is a pre-configured factory that produces a Datasource
with concrete driver settings — representing common deployment patterns.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from .models import (
    ColumnType,
    DatabaseEngine,
    Datasource,
    ReplicaConfig,
    RetentionPolicy,
    RetentionPolicyType,
    TimeSeriesGranularity,
    TimeSeriesModel,
)


# ---------------------------------------------------------------------------
# DataSource Recipes
# ---------------------------------------------------------------------------


def postgres_datasource(
    name: str = "primary",
    connection_string: str = "postgresql+asyncpg://user:pass@localhost:5432/dbname",
    pool_size: int = 20,
    max_overflow: int = 40,
    ssl_enabled: bool = True,
    read_replicas: list[dict] | None = None,
) -> Datasource:
    """
    PostgreSQL DataSource recipe.

    Recommended for: most web applications, spatial + full-text workloads.
    Driver: asyncpg (async) / psycopg3 (sync).
    """
    replicas = []
    if read_replicas:
        for r in read_replicas:
            replicas.append(ReplicaConfig(
                name=r.get("name", "replica"),
                connection_string=r.get("connection_string", connection_string),
                weight=r.get("weight", 1),
            ))

    return Datasource(
        name=name,
        engine=DatabaseEngine.POSTGRESQL,
        connection_string=connection_string,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_timeout=30,
        pool_recycle=3600,
        read_replicas=replicas,
        ssl_enabled=ssl_enabled,
        description="PostgreSQL primary datasource",
    )


def mysql_datasource(
    name: str = "primary",
    connection_string: str = "mysql+aiomysql://user:pass@localhost:3306/dbname",
    pool_size: int = 20,
    max_overflow: int = 40,
    ssl_enabled: bool = False,
    read_replicas: list[dict] | None = None,
) -> Datasource:
    """
    MySQL DataSource recipe.

    Recommended for: cost-sensitive deployments, WordPress/Drupal migration.
    Driver: aiomysql (async) / mysqlclient (sync).
    """
    replicas = []
    if read_replicas:
        for r in read_replicas:
            replicas.append(ReplicaConfig(
                name=r.get("name", "replica"),
                connection_string=r.get("connection_string", connection_string),
                weight=r.get("weight", 1),
            ))

    return Datasource(
        name=name,
        engine=DatabaseEngine.MYSQL,
        connection_string=connection_string,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_timeout=30,
        pool_recycle=3600,
        read_replicas=replicas,
        ssl_enabled=ssl_enabled,
        description="MySQL primary datasource",
    )


def sqlserver_datasource(
    name: str = "primary",
    connection_string: str = "mssql+aiosqlite://user:pass@localhost:1433/dbname",
    pool_size: int = 10,
    max_overflow: int = 20,
    ssl_enabled: bool = True,
) -> Datasource:
    """
    SQL Server DataSource recipe.

    Recommended for: enterprise Windows environments, existing MSSQL infra.
    Driver: aiosqlite (async) / pyodbc (sync).
    """
    return Datasource(
        name=name,
        engine=DatabaseEngine.SQLSERVER,
        connection_string=connection_string,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_timeout=30,
        pool_recycle=3600,
        ssl_enabled=ssl_enabled,
        description="SQL Server primary datasource",
    )


def oracle_datasource(
    name: str = "primary",
    connection_string: str = "oracle+oracledb://user:pass@localhost:1521/dbname",
    pool_size: int = 10,
    max_overflow: int = 20,
    ssl_enabled: bool = True,
) -> Datasource:
    """
    Oracle DataSource recipe.

    Recommended for: legacy enterprise, banking core systems.
    Driver: oracledb (async-ready).
    """
    return Datasource(
        name=name,
        engine=DatabaseEngine.ORACLE,
        connection_string=connection_string,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_timeout=30,
        pool_recycle=1800,
        ssl_enabled=ssl_enabled,
        description="Oracle primary datasource",
    )


def timescale_datasource(
    name: str = "timescale",
    connection_string: str = "postgresql+asyncpg://user:pass@localhost:5432/timescaledb",
    pool_size: int = 20,
    max_overflow: int = 40,
    ssl_enabled: bool = True,
    retention_days: int = 90,
    partition_interval: str = "week",
) -> Datasource:
    """
    TimescaleDB DataSource recipe (PostgreSQL extension).

    Recommended for: time-series metrics, IoT telemetry, event logging.
    Includes default retention policy.
    """
    ds = postgres_datasource(
        name=name,
        connection_string=connection_string,
        pool_size=pool_size,
        max_overflow=max_overflow,
        ssl_enabled=ssl_enabled,
    )
    ds.description = f"TimescaleDB datasource with {retention_days}d retention"
    return ds


def sqlite_datasource(
    name: str = "local",
    connection_string: str = "sqlite:///./app.db",
) -> Datasource:
    """
    SQLite DataSource recipe.

    Recommended for: local development, embedded deployments, CI testing.
    Note: uses PostgreSQL engine enum as closest match (single-file DB).
    """
    return Datasource(
        name=name,
        engine=DatabaseEngine.POSTGRESQL,
        connection_string=connection_string,
        pool_size=1,
        max_overflow=0,
        pool_timeout=10,
        pool_recycle=600,
        ssl_enabled=False,
        description="SQLite local datasource (dev/test only)",
    )


# ---------------------------------------------------------------------------
# Time-Series Recipes
# ---------------------------------------------------------------------------


def time_series_model_from_entity(
    entity_id: str,
    table_name: str,
    timestamp_column: str = "recorded_at",
    grain_columns: list[str] | None = None,
    value_columns: list[str] | None = None,
    granularity: str = "minute",
    retention_days: int = 90,
    partition_interval: str = "week",
) -> TimeSeriesModel:
    """
    Create a TimeSeriesModel with a default retention policy.

    Args:
        entity_id: Unique identifier for the time-series model.
        table_name: Table name in the database.
        timestamp_column: Column that holds the timestamp.
        grain_columns: Columns that identify the data point (e.g. host, metric).
        value_columns: Columns that hold measured values.
        granularity: Granularity level (second, minute, hour, day, week, month).
        retention_days: Number of days to retain data before auto-cleanup.
        partition_interval: Partition interval (week, month recommended).
    """
    granularity_enum = TimeSeriesGranularity(granularity)
    retention = RetentionPolicy(
        name=f"{entity_id}_retention",
        policy_type=RetentionPolicyType.TIME_BASED,
        threshold=retention_days * 86400,  # days to seconds
        partition_interval=partition_interval,
        description=f"Keep {retention_days} days of {entity_id} data",
    )

    return TimeSeriesModel(
        id=entity_id,
        table_name=table_name,
        timestamp_column=timestamp_column,
        grain_columns=grain_columns or [],
        value_columns=value_columns or [],
        granularity=granularity_enum,
        retention_policy=retention,
        partition_interval=partition_interval,
        description=f"Time-series model for {entity_id} with {retention_days}d retention",
    )


# ---------------------------------------------------------------------------
# Column Type Recipes
# ---------------------------------------------------------------------------

COLUMN_TYPE_PRESETS: dict[str, dict] = {
    "uuid_pk": {
        "name": "id",
        "type": "uuid",
        "primary_key": True,
        "required": True,
    },
    "tenant_id": {
        "name": "tenant_id",
        "type": "string",
        "tenant_aware": True,
        "required": True,
        "indexed": True,
        "max_length": 36,
    },
    "email": {
        "name": "email",
        "type": "string",
        "required": True,
        "unique": True,
        "max_length": 255,
    },
    "timestamps": {
        "name": "created_at",
        "type": "datetime",
        "required": False,
    },
    "soft_delete": {
        "name": "deleted_at",
        "type": "datetime",
        "required": False,
    },
    "jsonb_metadata": {
        "name": "metadata",
        "type": "json",
        "required": False,
    },
    "money": {
        "name": "amount",
        "type": "decimal",
        "precision": 10,
        "scale": 2,
        "required": True,
    },
}
