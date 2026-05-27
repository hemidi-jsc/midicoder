# coding: utf-8
"""
Tests cho recipes.py (CP08).

Bao gồm:
- postgres_datasource recipe
- mysql_datasource recipe
- Recipe với read replicas
- Recipe column pattern definitions
"""

import pytest

from midicoder.packs.cp08_database.recipes import (
    postgres_datasource,
    mysql_datasource,
)
from midicoder.packs.cp08_database.models import (
    DatabaseEngine,
    Datasource,
    ReplicaConfig,
)


class TestPostgresRecipe:
    def test_postgres_default(self):
        ds = postgres_datasource()
        assert isinstance(ds, Datasource)
        assert ds.name == "primary"
        assert ds.engine == DatabaseEngine.POSTGRESQL
        assert ds.pool_size == 20
        assert ds.max_overflow == 40
        assert ds.ssl_enabled is True

    def test_postgres_custom_connection(self):
        ds = postgres_datasource(
            name="analytics",
            connection_string="postgresql+asyncpg://user:pass@host:5432/analytics",
        )
        assert ds.name == "analytics"
        assert "analytics" in ds.connection_string

    def test_postgres_with_replicas(self):
        ds = postgres_datasource(
            name="primary",
            connection_string="pg://primary",
            read_replicas=[
                {"name": "replica1", "connection_string": "pg://r1", "weight": 2},
                {"name": "replica2", "connection_string": "pg://r2", "weight": 1},
            ],
        )
        assert len(ds.read_replicas) == 2
        assert ds.read_replicas[0].weight == 2
        assert ds.read_replicas[1].name == "replica2"

    def test_postgres_no_replicas(self):
        ds = postgres_datasource()
        assert len(ds.read_replicas) == 0

    def test_postgres_ssl_disabled(self):
        ds = postgres_datasource(ssl_enabled=False)
        assert ds.ssl_enabled is False

    def test_postgres_to_dict_roundtrip(self):
        ds = postgres_datasource(name="test", connection_string="pg://db")
        d = ds.to_dict()
        assert d["engine"] == "postgresql"


class TestMySQLRecipe:
    def test_mysql_default(self):
        ds = mysql_datasource()
        assert isinstance(ds, Datasource)
        assert ds.engine == DatabaseEngine.MYSQL
        assert ds.pool_size == 20
        assert ds.ssl_enabled is False

    def test_mysql_custom(self):
        ds = mysql_datasource(
            name="read_replica",
            connection_string="mysql+aiomysql://user:pass@host:3306/reports",
            pool_size=30,
        )
        assert ds.name == "read_replica"
        assert ds.pool_size == 30

    def test_mysql_with_replicas(self):
        ds = mysql_datasource(
            name="primary",
            connection_string="mysql://primary",
            read_replicas=[
                {"name": "r1", "connection_string": "mysql://r1"},
            ],
        )
        assert len(ds.read_replicas) == 1

    def test_mysql_to_dict(self):
        ds = mysql_datasource()
        d = ds.to_dict()
        assert d["engine"] == "mysql"


class TestRecipeConsistency:
    """Verify recipe output is valid Datasource that can serialize."""

    def test_postgres_replica_is_replica_config(self):
        ds = postgres_datasource(
            read_replicas=[{"name": "r1", "connection_string": "pg://r1"}]
        )
        for r in ds.read_replicas:
            assert isinstance(r, ReplicaConfig)

    def test_mysql_full_roundtrip(self):
        ds = mysql_datasource(
            name="full",
            connection_string="mysql://host/db",
            pool_size=25,
            ssl_enabled=True,
            read_replicas=[
                {"name": "r1", "connection_string": "mysql://r1", "weight": 3}
            ],
        )
        d = ds.to_dict()
        assert d["pool_size"] == 25
        assert d["ssl_enabled"] is True
        assert d["engine"] == "mysql"
        assert len(d["read_replicas"]) == 1
        assert d["read_replicas"][0]["weight"] == 3
