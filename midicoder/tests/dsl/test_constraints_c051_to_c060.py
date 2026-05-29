# coding: utf-8
"""
Test constraint validators C051–C060.

Tác giả: Midicoder CE Team
Version: 1.0.0
"""

from __future__ import annotations

import pytest

from midicoder.dsl.constraints import (
    APIVersionSemanticVersion,
    CalendarScheduleCronValid,
    ETLStepHasExtractAndLoad,
    GeofenceCoordinateRangeValid,
    PluginSlotIdUnique,
    ReportEntityReferenceExists,
    LocalizationLocaleBCP47,
    ConstraintLevel,
    ConstraintResult,
    get_registry,
)
from midicoder.dsl.metadata import ValidationContext
from midicoder.dsl.projection import NodeKind, ProjectionNode, ProjectionTree


def _ctx() -> ValidationContext:
    return ValidationContext(node_id="test")


def _entity(params: dict | None = None) -> ProjectionNode:
    """Helper để tạo ENTITY node với required fields."""
    p = {"id": "Customer", "fields": [{"name": "name", "type": "str"}]}
    if params:
        p.update(params)
    return ProjectionNode(id=p["id"], kind=NodeKind.ENTITY, params=p)


# ===========================================================================
# C051: PluginSlotIdUnique
# ===========================================================================

class TestC051PluginSlotIdUnique:
    """Test C051 — Plugin slot ID uniqueness."""

    def test_valid_unique_slot_ids(self) -> None:
        tree = ProjectionTree()
        tree.add_node(ProjectionNode(id="slot1", kind=NodeKind.PLUGIN_SLOT, params={"id": "slot1"}))
        tree.add_node(ProjectionNode(id="slot2", kind=NodeKind.PLUGIN_SLOT, params={"id": "slot2"}))

        constraint = PluginSlotIdUnique()
        results = constraint(tree.get_node("slot1"), tree, _ctx())

        assert len(results) == 0

    def test_non_plugin_slot_returns_empty(self) -> None:
        tree = ProjectionTree()
        node = _entity()

        constraint = PluginSlotIdUnique()
        results = constraint(node, tree, _ctx())

        assert len(results) == 0


# ===========================================================================
# C052: CalendarScheduleCronValid
# ===========================================================================

class TestC052CalendarScheduleCronValid:
    """Test C052 — Calendar schedule cron expression validity."""

    def test_valid_cron_expression(self) -> None:
        tree = ProjectionTree()
        node = ProjectionNode(
            id="cal1",
            kind=NodeKind.CALENDAR_SCHEDULE,
            params={"id": "cal1", "calendar_type": "academic", "recurrence_rule": "0 9 * * 1-5"},
        )

        constraint = CalendarScheduleCronValid()
        results = constraint(node, tree, _ctx())

        assert len(results) == 0

    def test_invalid_cron_too_few_fields(self) -> None:
        tree = ProjectionTree()
        node = ProjectionNode(
            id="cal1",
            kind=NodeKind.CALENDAR_SCHEDULE,
            params={"id": "cal1", "calendar_type": "academic", "recurrence_rule": "0 9 *"},
        )

        constraint = CalendarScheduleCronValid()
        results = constraint(node, tree, _ctx())

        assert len(results) == 1
        assert results[0].constraint_id == "C052"

    def test_no_cron_returns_empty(self) -> None:
        tree = ProjectionTree()
        node = ProjectionNode(
            id="cal1",
            kind=NodeKind.CALENDAR_SCHEDULE,
            params={"id": "cal1", "calendar_type": "academic"},
        )

        constraint = CalendarScheduleCronValid()
        results = constraint(node, tree, _ctx())

        assert len(results) == 0


# ===========================================================================
# C054: ReportEntityReferenceExists
# ===========================================================================

class TestC054ReportEntityReferenceExists:
    """Test C054 — Report entity reference must exist."""

    def test_valid_reference(self) -> None:
        tree = ProjectionTree()
        tree.add_node(_entity())
        node = ProjectionNode(
            id="r1",
            kind=NodeKind.REPORT,
            params={"id": "r1", "fields": [], "data_sources": ["Customer"]},
        )

        constraint = ReportEntityReferenceExists()
        results = constraint(node, tree, _ctx())

        assert len(results) == 0

    def test_nonexistent_reference_fails(self) -> None:
        tree = ProjectionTree()
        node = ProjectionNode(
            id="r1",
            kind=NodeKind.REPORT,
            params={"id": "r1", "fields": [], "data_sources": ["NonExistent"]},
        )

        constraint = ReportEntityReferenceExists()
        results = constraint(node, tree, _ctx())

        assert len(results) == 1
        assert results[0].constraint_id == "C054"

    def test_scheduled_report_with_invalid_report_id(self) -> None:
        tree = ProjectionTree()
        node = ProjectionNode(
            id="sr1",
            kind=NodeKind.SCHEDULED_REPORT,
            params={"id": "sr1", "frequency": "daily", "report_id": "missing_report"},
        )

        constraint = ReportEntityReferenceExists()
        results = constraint(node, tree, _ctx())

        assert len(results) == 1


# ===========================================================================
# C055: GeofenceCoordinateRangeValid
# ===========================================================================

class TestC055GeofenceCoordinateRangeValid:
    """Test C055 — Geofence coordinate range validity."""

    def test_valid_coordinates(self) -> None:
        tree = ProjectionTree()
        node = ProjectionNode(
            id="geo1",
            kind=NodeKind.GEO_SEARCH_INDEX,
            params={
                "id": "geo1",
                "geofences": [{"latitude": 40.7128, "longitude": -74.0060}],
            },
        )

        constraint = GeofenceCoordinateRangeValid()
        results = constraint(node, tree, _ctx())

        assert len(results) == 0

    def test_invalid_latitude(self) -> None:
        tree = ProjectionTree()
        node = ProjectionNode(
            id="geo1",
            kind=NodeKind.GEO_SEARCH_INDEX,
            params={
                "id": "geo1",
                "geofences": [{"latitude": 100, "longitude": 0}],
            },
        )

        constraint = GeofenceCoordinateRangeValid()
        results = constraint(node, tree, _ctx())

        assert len(results) == 1
        assert "Latitude" in results[0].message

    def test_invalid_longitude(self) -> None:
        tree = ProjectionTree()
        node = ProjectionNode(
            id="geo1",
            kind=NodeKind.GEO_SEARCH_INDEX,
            params={
                "id": "geo1",
                "geofences": [{"latitude": 0, "longitude": 200}],
            },
        )

        constraint = GeofenceCoordinateRangeValid()
        results = constraint(node, tree, _ctx())

        assert len(results) == 1
        assert "Longitude" in results[0].message


# ===========================================================================
# C056: ETLStepHasExtractAndLoad
# ===========================================================================

class TestC056ETLStepHasExtractAndLoad:
    """Test C056 — ETL step must have extract + load."""

    def test_valid_etl_with_both_steps(self) -> None:
        tree = ProjectionTree()
        node = ProjectionNode(
            id="etl1",
            kind=NodeKind.DATA_MIGRATION,
            params={
                "id": "etl1",
                "source_schema": "v1",
                "target_schema": "v2",
                "steps": [
                    {"type": "extract", "source": "db1"},
                    {"type": "transform"},
                    {"type": "load", "target": "db2"},
                ],
            },
        )

        constraint = ETLStepHasExtractAndLoad()
        results = constraint(node, tree, _ctx())

        assert len(results) == 0

    def test_missing_extract_step(self) -> None:
        tree = ProjectionTree()
        node = ProjectionNode(
            id="etl1",
            kind=NodeKind.DATA_MIGRATION,
            params={
                "id": "etl1",
                "source_schema": "v1",
                "target_schema": "v2",
                "steps": [
                    {"type": "transform"},
                    {"type": "load", "target": "db2"},
                ],
            },
        )

        constraint = ETLStepHasExtractAndLoad()
        results = constraint(node, tree, _ctx())

        assert len(results) == 1
        assert "extract" in results[0].message

    def test_batch_job_also_validated(self) -> None:
        tree = ProjectionTree()
        node = ProjectionNode(
            id="batch1",
            kind=NodeKind.BATCH_JOB,
            params={
                "id": "batch1",
                "job_type": "aggregation",
                "steps": [
                    {"type": "extract"},
                ],
            },
        )

        constraint = ETLStepHasExtractAndLoad()
        results = constraint(node, tree, _ctx())

        assert len(results) == 1
        assert "load" in results[0].message


# ===========================================================================
# C057: LocalizationLocaleBCP47
# ===========================================================================

class TestC057LocalizationLocaleBCP47:
    """Test C057 — Localization locale code BCP 47 format."""

    def test_valid_locales(self) -> None:
        tree = ProjectionTree()
        node = ProjectionNode(
            id="l10n1",
            kind=NodeKind.LOCALIZATION,
            params={"id": "l10n1", "entity_id": "Product", "locales": ["en", "en-US", "zh-Hant-TW", "vi-VN"]},
        )

        constraint = LocalizationLocaleBCP47()
        results = constraint(node, tree, _ctx())

        assert len(results) == 0

    def test_invalid_locale_fails(self) -> None:
        tree = ProjectionTree()
        node = ProjectionNode(
            id="l10n1",
            kind=NodeKind.LOCALIZATION,
            params={"id": "l10n1", "entity_id": "Product", "locales": ["en", "invalid-locale", "zh-Hant-TW"]},
        )

        constraint = LocalizationLocaleBCP47()
        results = constraint(node, tree, _ctx())

        assert len(results) == 1
        assert results[0].constraint_id == "C057"
        assert "BCP 47" in results[0].message

    def test_single_char_locale_fails(self) -> None:
        tree = ProjectionTree()
        node = ProjectionNode(
            id="l10n1",
            kind=NodeKind.LOCALIZATION,
            params={"id": "l10n1", "entity_id": "Product", "locales": ["x"]},
        )

        constraint = LocalizationLocaleBCP47()
        results = constraint(node, tree, _ctx())

        assert len(results) == 1


# ===========================================================================
# C058: APIVersionSemanticVersion
# ===========================================================================

class TestC058APIVersionSemanticVersion:
    """Test C058 — API version semantic versioning."""

    def test_valid_semver(self) -> None:
        tree = ProjectionTree()
        node = ProjectionNode(
            id="v1",
            kind=NodeKind.API_VERSION,
            params={"id": "v1", "version": "1.0.0", "api_id": "api1"},
        )

        constraint = APIVersionSemanticVersion()
        results = constraint(node, tree, _ctx())

        assert len(results) == 0

    def test_valid_semver_with_prerelease(self) -> None:
        tree = ProjectionTree()
        node = ProjectionNode(
            id="v1",
            kind=NodeKind.API_VERSION,
            params={"id": "v1", "version": "2.1.0-beta.1", "api_id": "api1"},
        )

        constraint = APIVersionSemanticVersion()
        results = constraint(node, tree, _ctx())

        assert len(results) == 0

    def test_invalid_version_fails(self) -> None:
        tree = ProjectionTree()
        node = ProjectionNode(
            id="v1",
            kind=NodeKind.API_VERSION,
            params={"id": "v1", "version": "v1.0", "api_id": "api1"},
        )

        constraint = APIVersionSemanticVersion()
        results = constraint(node, tree, _ctx())

        assert len(results) == 1
        assert results[0].constraint_id == "C058"


# ===========================================================================
# Integration: Registry includes all C051-C060
# ===========================================================================

class TestC051ToC060Registry:
    """Test tất cả 10 constraints đều được đăng ký trong default_registry."""

    def test_all_constraints_registered(self) -> None:
        registry = get_registry()
        all_ids = {c.id for c in registry.get_all()}

        expected = {"C051", "C052", "C054", "C055", "C056", "C057", "C058"}
        assert expected.issubset(all_ids), f"Missing constraints: {expected - all_ids}"

    def test_all_constraints_are_error_level(self) -> None:
        registry = get_registry()
        for c in registry.get_all():
            if c.id in {"C051", "C052", "C054", "C055", "C056", "C057", "C058"}:
                assert c.level == ConstraintLevel.ERROR, f"{c.id} should be ERROR level"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
