# coding: utf-8
"""
Test dependency extraction rules P2-15a → P2-15j.

Tác giả: Midicoder CE Team
Version: 1.0.0
"""

from __future__ import annotations

import pytest

from midicoder.dsl.dependencies import (
    DependencyBuilder,
    DependencyType,
)
from midicoder.dsl.projection import NodeKind, ProjectionNode, ProjectionTree


# ===========================================================================
# P2-15a: PLUGIN_SLOT dependency on entities
# ===========================================================================

class TestP2_15aPluginSlotDependencies:
    """CP27: PLUGIN_SLOT — depends on entities referenced in slot config."""

    def test_plugin_slot_with_entity_id(self) -> None:
        tree = ProjectionTree()
        tree.add_node(ProjectionNode(
            id="slot1", kind=NodeKind.PLUGIN_SLOT,
            params={"id": "slot1", "entity_id": "Customer"},
        ))
        graph = DependencyBuilder(tree=tree).build()
        deps = graph.get_dependencies("slot1")
        assert "Customer" in deps

    def test_plugin_slot_with_entities_list(self) -> None:
        tree = ProjectionTree()
        tree.add_node(ProjectionNode(
            id="slot1", kind=NodeKind.PLUGIN_SLOT,
            params={"id": "slot1", "entities": ["Customer", "Order"]},
        ))
        graph = DependencyBuilder(tree=tree).build()
        deps = graph.get_dependencies("slot1")
        assert "Customer" in deps
        assert "Order" in deps

    def test_plugin_slot_no_deps(self) -> None:
        tree = ProjectionTree()
        tree.add_node(ProjectionNode(
            id="slot1", kind=NodeKind.PLUGIN_SLOT,
            params={"id": "slot1"},
        ))
        graph = DependencyBuilder(tree=tree).build()
        deps = graph.get_dependencies("slot1")
        assert len(deps) == 0


# ===========================================================================
# P2-15b: CALENDAR_SCHEDULE dependency on WORKFLOW
# ===========================================================================

class TestP2_15bCalendarScheduleDependencies:
    """CP31: CALENDAR_SCHEDULE — depends on WORKFLOW (CP13)."""

    def test_calendar_with_workflow_id(self) -> None:
        tree = ProjectionTree()
        tree.add_node(ProjectionNode(
            id="cal1", kind=NodeKind.CALENDAR_SCHEDULE,
            params={"id": "cal1", "calendar_type": "academic", "workflow_id": "wf1"},
        ))
        graph = DependencyBuilder(tree=tree).build()
        deps = graph.get_dependencies("cal1")
        assert "wf1" in deps

    def test_calendar_with_workflow_field(self) -> None:
        tree = ProjectionTree()
        tree.add_node(ProjectionNode(
            id="cal1", kind=NodeKind.CALENDAR_SCHEDULE,
            params={"id": "cal1", "calendar_type": "academic", "workflow": "wf2"},
        ))
        graph = DependencyBuilder(tree=tree).build()
        deps = graph.get_dependencies("cal1")
        assert "wf2" in deps

    def test_calendar_no_workflow(self) -> None:
        tree = ProjectionTree()
        tree.add_node(ProjectionNode(
            id="cal1", kind=NodeKind.CALENDAR_SCHEDULE,
            params={"id": "cal1", "calendar_type": "academic"},
        ))
        graph = DependencyBuilder(tree=tree).build()
        deps = graph.get_dependencies("cal1")
        assert len(deps) == 0


# ===========================================================================
# P2-15c: Finance entities dependency
# ===========================================================================

class TestP2_15cFinanceDependencies:
    """CP33: GENERAL_LEDGER, FINANCIAL_INSTRUMENT, CURRENCY_EXCHANGE — depends on ENTITY."""

    def test_general_ledger_with_entity_id(self) -> None:
        tree = ProjectionTree()
        tree.add_node(ProjectionNode(
            id="ledger1", kind=NodeKind.GENERAL_LEDGER,
            params={"id": "ledger1", "entity_id": "Transaction"},
        ))
        graph = DependencyBuilder(tree=tree).build()
        deps = graph.get_dependencies("ledger1")
        assert "Transaction" in deps

    def test_financial_instrument_with_entities(self) -> None:
        tree = ProjectionTree()
        tree.add_node(ProjectionNode(
            id="fi1", kind=NodeKind.FINANCIAL_INSTRUMENT,
            params={"id": "fi1", "symbol": "AAPL", "type": "stock", "entities": ["Company"]},
        ))
        graph = DependencyBuilder(tree=tree).build()
        deps = graph.get_dependencies("fi1")
        assert "Company" in deps

    def test_currency_exchange_with_entity(self) -> None:
        tree = ProjectionTree()
        tree.add_node(ProjectionNode(
            id="fx1", kind=NodeKind.CURRENCY_EXCHANGE,
            params={"id": "fx1", "base_currency": "USD", "quote_currency": "EUR", "entity_id": "Rate"},
        ))
        graph = DependencyBuilder(tree=tree).build()
        deps = graph.get_dependencies("fx1")
        assert "Rate" in deps


# ===========================================================================
# P2-15d: Report dependencies on entities
# ===========================================================================

class TestP2_15dReportDependencies:
    """CP34: REPORT, DASHBOARD, EXPORT — depends on ENTITY."""

    def test_report_with_data_sources(self) -> None:
        tree = ProjectionTree()
        tree.add_node(ProjectionNode(
            id="r1", kind=NodeKind.REPORT,
            params={"id": "r1", "fields": [], "data_sources": ["Customer", "Order"]},
        ))
        graph = DependencyBuilder(tree=tree).build()
        deps = graph.get_dependencies("r1")
        assert "Customer" in deps
        assert "Order" in deps

    def test_dashboard_with_data_sources(self) -> None:
        tree = ProjectionTree()
        tree.add_node(ProjectionNode(
            id="d1", kind=NodeKind.DASHBOARD,
            params={"id": "d1", "widgets": [], "data_sources": ["Metric"]},
        ))
        graph = DependencyBuilder(tree=tree).build()
        deps = graph.get_dependencies("d1")
        assert "Metric" in deps

    def test_export_with_source_id(self) -> None:
        tree = ProjectionTree()
        tree.add_node(ProjectionNode(
            id="e1", kind=NodeKind.EXPORT,
            params={"id": "e1", "format": "csv", "source_id": "ReportA"},
        ))
        graph = DependencyBuilder(tree=tree).build()
        deps = graph.get_dependencies("e1")
        assert "ReportA" in deps


# ===========================================================================
# P2-15e: GEO_SEARCH_INDEX dependency on entity
# ===========================================================================

class TestP2_15eGeoSearchDependencies:
    """CP35: GEO_SEARCH_INDEX — depends on ENTITY with geofield."""

    def test_geo_search_with_entity_id(self) -> None:
        tree = ProjectionTree()
        tree.add_node(ProjectionNode(
            id="geo1", kind=NodeKind.GEO_SEARCH_INDEX,
            params={"id": "geo1", "entity_id": "Store"},
        ))
        graph = DependencyBuilder(tree=tree).build()
        deps = graph.get_dependencies("geo1")
        assert "Store" in deps

    def test_geo_search_no_entity(self) -> None:
        tree = ProjectionTree()
        tree.add_node(ProjectionNode(
            id="geo1", kind=NodeKind.GEO_SEARCH_INDEX,
            params={"id": "geo1"},
        ))
        graph = DependencyBuilder(tree=tree).build()
        deps = graph.get_dependencies("geo1")
        assert len(deps) == 0


# ===========================================================================
# P2-15f: ETL dependency on entities
# ===========================================================================

class TestP2_15fETLDpendencies:
    """CP38: DATA_MIGRATION, BATCH_JOB — depends on ENTITY."""

    def test_data_migration_with_schemas(self) -> None:
        tree = ProjectionTree()
        tree.add_node(ProjectionNode(
            id="m1", kind=NodeKind.DATA_MIGRATION,
            params={"id": "m1", "source_schema": "v1", "target_schema": "v2"},
        ))
        graph = DependencyBuilder(tree=tree).build()
        deps = graph.get_dependencies("m1")
        assert "v1" in deps
        assert "v2" in deps

    def test_batch_job_with_sources(self) -> None:
        tree = ProjectionTree()
        tree.add_node(ProjectionNode(
            id="b1", kind=NodeKind.BATCH_JOB,
            params={
                "id": "b1", "job_type": "aggregation",
                "input_sources": ["db1"], "output_destinations": ["db2"],
            },
        ))
        graph = DependencyBuilder(tree=tree).build()
        deps = graph.get_dependencies("b1")
        assert "db1" in deps
        assert "db2" in deps


# ===========================================================================
# P2-15g: Localization dependency on entity
# ===========================================================================

class TestP2_15gLocalizationDependencies:
    """CP39: LOCALIZATION — depends on ENTITY (translatable fields)."""

    def test_localization_with_entity_id(self) -> None:
        tree = ProjectionTree()
        tree.add_node(ProjectionNode(
            id="l1", kind=NodeKind.LOCALIZATION,
            params={"id": "l1", "entity_id": "Product", "locales": ["en", "vi"]},
        ))
        graph = DependencyBuilder(tree=tree).build()
        deps = graph.get_dependencies("l1")
        assert "Product" in deps

    def test_localization_no_entity(self) -> None:
        tree = ProjectionTree()
        tree.add_node(ProjectionNode(
            id="l1", kind=NodeKind.LOCALIZATION,
            params={"id": "l1", "entity_id": "", "locales": ["en"]},
        ))
        graph = DependencyBuilder(tree=tree).build()
        deps = graph.get_dependencies("l1")
        assert len(deps) == 0


# ===========================================================================
# P2-15h: API_VERSION dependency on entity
# ===========================================================================

class TestP2_15hAPIVersionDependencies:
    """CP43: API_VERSION — depends on ENTITY."""

    def test_api_version_with_api_id(self) -> None:
        tree = ProjectionTree()
        tree.add_node(ProjectionNode(
            id="av1", kind=NodeKind.API_VERSION,
            params={"id": "av1", "version": "1.0.0", "api_id": "api1"},
        ))
        graph = DependencyBuilder(tree=tree).build()
        deps = graph.get_dependencies("av1")
        assert "api1" in deps

    def test_api_version_with_entities(self) -> None:
        tree = ProjectionTree()
        tree.add_node(ProjectionNode(
            id="av1", kind=NodeKind.API_VERSION,
            params={"id": "av1", "version": "2.0.0", "api_id": "api1", "entities": ["Customer"]},
        ))
        graph = DependencyBuilder(tree=tree).build()
        deps = graph.get_dependencies("av1")
        assert "api1" in deps
        assert "Customer" in deps


# ===========================================================================
# P2-15i: PAYMENT_GATEWAY dependency on Currency/Webhook
# ===========================================================================

class TestP2_15iPaymentGatewayDependencies:
    """CP45: PAYMENT_GATEWAY — depends on CP33 (Currency), CP40 (Webhook)."""

    def test_payment_gateway_with_currencies(self) -> None:
        tree = ProjectionTree()
        tree.add_node(ProjectionNode(
            id="pg1", kind=NodeKind.PAYMENT_GATEWAY,
            params={"id": "pg1", "provider": "stripe", "currencies": ["USD", "EUR"]},
        ))
        graph = DependencyBuilder(tree=tree).build()
        deps = graph.get_dependencies("pg1")
        assert "USD" in deps
        assert "EUR" in deps

    def test_payment_gateway_with_webhook(self) -> None:
        tree = ProjectionTree()
        tree.add_node(ProjectionNode(
            id="pg1", kind=NodeKind.PAYMENT_GATEWAY,
            params={"id": "pg1", "provider": "stripe", "webhook_id": "wh1"},
        ))
        graph = DependencyBuilder(tree=tree).build()
        deps = graph.get_dependencies("pg1")
        assert "wh1" in deps


# ===========================================================================
# P2-15j: PRODUCT_CATALOG dependency on CP08/CP10
# ===========================================================================

class TestP2_15jCatalogDependencies:
    """CP50: PRODUCT_CATALOG, FACETED_SEARCH_INDEX — depends on CP08, CP10."""

    def test_product_catalog_with_string_products(self) -> None:
        tree = ProjectionTree()
        tree.add_node(ProjectionNode(
            id="cat1", kind=NodeKind.PRODUCT_CATALOG,
            params={"id": "cat1", "products": ["prod1", "prod2"]},
        ))
        graph = DependencyBuilder(tree=tree).build()
        deps = graph.get_dependencies("cat1")
        assert "prod1" in deps
        assert "prod2" in deps

    def test_product_catalog_with_entity_id(self) -> None:
        tree = ProjectionTree()
        tree.add_node(ProjectionNode(
            id="cat1", kind=NodeKind.PRODUCT_CATALOG,
            params={"id": "cat1", "entity_id": "Product"},
        ))
        graph = DependencyBuilder(tree=tree).build()
        deps = graph.get_dependencies("cat1")
        assert "Product" in deps

    def test_product_catalog_with_search_index(self) -> None:
        tree = ProjectionTree()
        tree.add_node(ProjectionNode(
            id="cat1", kind=NodeKind.PRODUCT_CATALOG,
            params={"id": "cat1", "search_index_id": "search1"},
        ))
        graph = DependencyBuilder(tree=tree).build()
        deps = graph.get_dependencies("cat1")
        assert "search1" in deps

    def test_product_catalog_skips_dict_products(self) -> None:
        """Products as dicts (with sku/category) should not create edges."""
        tree = ProjectionTree()
        tree.add_node(ProjectionNode(
            id="cat1", kind=NodeKind.PRODUCT_CATALOG,
            params={"id": "cat1", "products": [
                {"sku": "ABC-001", "category": "electronics"},
            ]},
        ))
        graph = DependencyBuilder(tree=tree).build()
        deps = graph.get_dependencies("cat1")
        assert len(deps) == 0


# ===========================================================================
# Integration: New dependency types are registered
# ===========================================================================

class TestP2_15DependencyTypes:
    """Test 10 dependency types mới đều tồn tại trong DependencyType enum."""

    def test_all_new_dependency_types_exist(self) -> None:
        expected = {
            "PLUGIN_SLOT_DEPENDENCY",
            "CALENDAR_WORKFLOW_DEPENDENCY",
            "FINANCE_ENTITY_DEPENDENCY",
            "REPORT_ENTITY_DEPENDENCY",
            "GEO_ENTITY_DEPENDENCY",
            "ETL_ENTITY_DEPENDENCY",
            "LOCALIZATION_ENTITY_DEPENDENCY",
            "API_VERSION_ENTITY_DEPENDENCY",
            "PAYMENT_ENTITY_DEPENDENCY",
            "CATALOG_ENTITY_DEPENDENCY",
        }
        actual = {e.name for e in DependencyType}
        assert expected.issubset(actual), f"Missing: {expected - actual}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
