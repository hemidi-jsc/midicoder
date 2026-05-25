# coding: utf-8
"""
Test DSL loader functions P2-16a → P2-16i.

Tác giả: Midicoder CE Team
Version: 1.0.0
"""

from __future__ import annotations

import pytest
from pathlib import Path

from midicoder.dsl.projection import NodeKind
from midicoder.dsl.loader import (
    _load_plugins,
    _load_schedules,
    _load_financial,
    _load_reports,
    _load_etl,
    _load_localization,
    _load_versioning,
    _load_payment,
    _load_catalog,
    load_projection_tree,
    disable_yaml_caching,
    enable_yaml_caching,
)


def _write_yaml(tmp_path: Path, filename: str, content: str) -> Path:
    """Helper to write a YAML file and return its path."""
    p = tmp_path / filename
    p.write_text(content, encoding="utf-8")
    return p


# ===========================================================================
# P2-16a: _load_plugins
# ===========================================================================

class TestP2_16aLoadPlugins:
    """CP27: _load_plugins — load plugin slots/contracts/policies."""

    def test_load_plugin_slots(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "plugins.yaml", """
slots:
  - id: slot1
    name: OrderSlot
    entity_id: Order
    events: [order.created, order.updated]
""")
        nodes = _load_plugins(path)
        assert len(nodes) == 1
        assert nodes[0].kind == NodeKind.PLUGIN_SLOT
        assert nodes[0].params["entity_id"] == "Order"

    def test_load_plugin_contracts(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "plugins.yaml", """
contracts:
  - id: contract1
    slots: [slot1, slot2]
    dependencies: [dep1]
""")
        nodes = _load_plugins(path)
        assert len(nodes) == 1
        assert nodes[0].kind == NodeKind.PLUGIN_CONTRACT
        assert "slot1" in nodes[0].params["slots"]

    def test_load_plugin_policies(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "plugins.yaml", """
policies:
  - id: policy1
    policy_type: security
    rule: signed_only
    enforced: true
""")
        nodes = _load_plugins(path)
        assert len(nodes) == 1
        assert nodes[0].kind == NodeKind.PLUGIN_POLICY
        assert nodes[0].params["enforced"] is True

    def test_load_all_three_types(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "plugins.yaml", """
slots:
  - id: slot1
    name: TestSlot
contracts:
  - id: contract1
    slots: [slot1]
policies:
  - id: policy1
    policy_type: security
    rule: allow_all
""")
        nodes = _load_plugins(path)
        kinds = {n.kind for n in nodes}
        assert NodeKind.PLUGIN_SLOT in kinds
        assert NodeKind.PLUGIN_CONTRACT in kinds
        assert NodeKind.PLUGIN_POLICY in kinds
        assert len(nodes) == 3

    def test_empty_plugins(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "plugins.yaml", "{}")
        nodes = _load_plugins(path)
        assert len(nodes) == 0


# ===========================================================================
# P2-16b: _load_schedules
# ===========================================================================

class TestP2_16bLoadSchedules:
    """CP31: _load_schedules — load calendar schedules."""

    def test_load_calendar_schedule(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "schedules.yaml", """
schedules:
  - id: cal1
    calendar_type: academic
    workflow_id: wf1
    recurrence_rule: "0 9 * * 1-5"
""")
        nodes = _load_schedules(path)
        assert len(nodes) == 1
        assert nodes[0].kind == NodeKind.CALENDAR_SCHEDULE
        assert nodes[0].params["workflow_id"] == "wf1"

    def test_empty_schedules(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "schedules.yaml", "{}")
        nodes = _load_schedules(path)
        assert len(nodes) == 0


# ===========================================================================
# P2-16c: _load_financial
# ===========================================================================

class TestP2_16cLoadFinancial:
    """CP33: _load_financial — load ledgers, instruments, exchange, tax, subledgers."""

    def test_load_ledgers(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "financial.yaml", """
ledgers:
  - id: ledger1
    currency: USD
    entity_id: Transaction
""")
        nodes = _load_financial(path)
        assert len(nodes) == 1
        assert nodes[0].kind == NodeKind.GENERAL_LEDGER

    def test_load_instruments(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "financial.yaml", """
instruments:
  - id: fi1
    symbol: AAPL
    type: stock
""")
        nodes = _load_financial(path)
        assert len(nodes) == 1
        assert nodes[0].kind == NodeKind.FINANCIAL_INSTRUMENT
        assert nodes[0].params["symbol"] == "AAPL"

    def test_load_currency_exchanges(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "financial.yaml", """
currency_exchanges:
  - id: fx1
    base_currency: USD
    quote_currency: EUR
    exchange_rate: 1.1
""")
        nodes = _load_financial(path)
        assert len(nodes) == 1
        assert nodes[0].kind == NodeKind.CURRENCY_EXCHANGE

    def test_load_tax_rules(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "financial.yaml", """
tax_rules:
  - id: tax1
    tax_type: vat
    rate: 10
    jurisdiction: VN
""")
        nodes = _load_financial(path)
        assert len(nodes) == 1
        assert nodes[0].kind == NodeKind.TAX_RULE

    def test_load_subledgers(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "financial.yaml", """
subledgers:
  - id: sub1
    ledger_type: accounts_receivable
    parent_ledger_id: ledger1
""")
        nodes = _load_financial(path)
        assert len(nodes) == 1
        assert nodes[0].kind == NodeKind.SUBLEDGER

    def test_load_all_finance_types(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "financial.yaml", """
ledgers:
  - id: ledger1
    currency: USD
instruments:
  - id: fi1
    symbol: AAPL
    type: stock
currency_exchanges:
  - id: fx1
    base_currency: USD
    quote_currency: EUR
tax_rules:
  - id: tax1
    tax_type: vat
    rate: 10
    jurisdiction: VN
subledgers:
  - id: sub1
    ledger_type: accounts_receivable
""")
        nodes = _load_financial(path)
        assert len(nodes) == 5


# ===========================================================================
# P2-16d: _load_reports
# ===========================================================================

class TestP2_16dLoadReports:
    """CP34: _load_reports — load reports, dashboards, exports, scheduled reports."""

    def test_load_reports(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "reports.yaml", """
reports:
  - id: r1
    data_sources: [Customer]
    fields: []
""")
        nodes = _load_reports(path)
        assert len(nodes) == 1
        assert nodes[0].kind == NodeKind.REPORT

    def test_load_dashboards(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "reports.yaml", """
dashboards:
  - id: d1
    widgets: []
""")
        nodes = _load_reports(path)
        assert len(nodes) == 1
        assert nodes[0].kind == NodeKind.DASHBOARD

    def test_load_exports(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "reports.yaml", """
exports:
  - id: e1
    format: csv
    source_id: r1
""")
        nodes = _load_reports(path)
        assert len(nodes) == 1
        assert nodes[0].kind == NodeKind.EXPORT

    def test_load_scheduled_reports(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "reports.yaml", """
scheduled_reports:
  - id: sr1
    report_id: r1
    frequency: daily
""")
        nodes = _load_reports(path)
        assert len(nodes) == 1
        assert nodes[0].kind == NodeKind.SCHEDULED_REPORT

    def test_load_all_report_types(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "reports.yaml", """
reports:
  - id: r1
    data_sources: [Customer]
    fields: []
dashboards:
  - id: d1
    widgets: []
exports:
  - id: e1
    format: csv
    source_id: r1
scheduled_reports:
  - id: sr1
    report_id: r1
    frequency: daily
""")
        nodes = _load_reports(path)
        assert len(nodes) == 4


# ===========================================================================
# P2-16e: _load_etl
# ===========================================================================

class TestP2_16eLoadETL:
    """CP38: _load_etl — load data migrations and batch jobs."""

    def test_load_data_migrations(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "etl.yaml", """
migrations:
  - id: m1
    source_schema: v1
    target_schema: v2
""")
        nodes = _load_etl(path)
        assert len(nodes) == 1
        assert nodes[0].kind == NodeKind.DATA_MIGRATION

    def test_load_batch_jobs(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "etl.yaml", """
batch_jobs:
  - id: b1
    job_type: aggregation
""")
        nodes = _load_etl(path)
        assert len(nodes) == 1
        assert nodes[0].kind == NodeKind.BATCH_JOB

    def test_load_both(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "etl.yaml", """
migrations:
  - id: m1
    source_schema: v1
    target_schema: v2
batch_jobs:
  - id: b1
    job_type: aggregation
""")
        nodes = _load_etl(path)
        assert len(nodes) == 2


# ===========================================================================
# P2-16f: _load_localization
# ===========================================================================

class TestP2_16fLoadLocalization:
    """CP39: _load_localization — load localization specs."""

    def test_load_localization(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "localization.yaml", """
localizations:
  - id: l1
    entity_id: Product
    locales: [en, vi-VN]
""")
        nodes = _load_localization(path)
        assert len(nodes) == 1
        assert nodes[0].kind == NodeKind.LOCALIZATION
        assert "vi-VN" in nodes[0].params["locales"]

    def test_empty_localization(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "localization.yaml", "{}")
        nodes = _load_localization(path)
        assert len(nodes) == 0


# ===========================================================================
# P2-16g: _load_versioning
# ===========================================================================

class TestP2_16gLoadVersioning:
    """CP43: _load_versioning — load API versions, deprecation notices, pagination specs."""

    def test_load_api_versions(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "versioning.yaml", """
api_versions:
  - id: av1
    version: "1.0.0"
    api_id: api1
""")
        nodes = _load_versioning(path)
        assert len(nodes) == 1
        assert nodes[0].kind == NodeKind.API_VERSION

    def test_load_deprecation_notices(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "versioning.yaml", """
deprecation_notices:
  - id: dep1
    api_version_id: av1
    reason: superseded
""")
        nodes = _load_versioning(path)
        assert len(nodes) == 1
        assert nodes[0].kind == NodeKind.DEPRECATION_NOTICE

    def test_load_pagination_specs(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "versioning.yaml", """
pagination_specs:
  - id: ps1
    page_size: 20
""")
        nodes = _load_versioning(path)
        assert len(nodes) == 1
        assert nodes[0].kind == NodeKind.PAGINATION_SPEC

    def test_load_all_versioning_types(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "versioning.yaml", """
api_versions:
  - id: av1
    version: "1.0.0"
    api_id: api1
deprecation_notices:
  - id: dep1
    api_version_id: av1
    reason: superseded
pagination_specs:
  - id: ps1
    page_size: 20
""")
        nodes = _load_versioning(path)
        assert len(nodes) == 3


# ===========================================================================
# P2-16h: _load_payment
# ===========================================================================

class TestP2_16hLoadPayment:
    """CP45: _load_payment — load payment gateways."""

    def test_load_payment_gateway(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "payment.yaml", """
payment_gateways:
  - id: pg1
    provider: stripe
    currencies: [USD, EUR]
    webhook_url: https://example.com/hook
""")
        nodes = _load_payment(path)
        assert len(nodes) == 1
        assert nodes[0].kind == NodeKind.PAYMENT_GATEWAY
        assert "EUR" in nodes[0].params["currencies"]

    def test_empty_payment(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "payment.yaml", "{}")
        nodes = _load_payment(path)
        assert len(nodes) == 0


# ===========================================================================
# P2-16i: _load_catalog
# ===========================================================================

class TestP2_16iLoadCatalog:
    """CP50: _load_catalog — load product catalogs and faceted search indexes."""

    def test_load_product_catalog(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "catalog.yaml", """
catalogs:
  - id: cat1
    entity_id: Product
    inventory_tracking: true
""")
        nodes = _load_catalog(path)
        assert len(nodes) == 1
        assert nodes[0].kind == NodeKind.PRODUCT_CATALOG

    def test_load_faceted_search(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "catalog.yaml", """
faceted_search:
  - id: fs1
    entity_id: Product
    facets: [color, size]
""")
        nodes = _load_catalog(path)
        assert len(nodes) == 1
        assert nodes[0].kind == NodeKind.FACETED_SEARCH_INDEX

    def test_load_both(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path, "catalog.yaml", """
catalogs:
  - id: cat1
    entity_id: Product
faceted_search:
  - id: fs1
    entity_id: Product
    facets: [color]
""")
        nodes = _load_catalog(path)
        assert len(nodes) == 2


# ===========================================================================
# P2-16j: Integration — load_projection_tree calls new loaders
# ===========================================================================

class TestP2_16jLoadProjectionTreeIntegration:
    """Test load_projection_tree() calls all new loader functions."""

    def test_load_plugins_from_directory(self, tmp_path: Path) -> None:
        _write_yaml(tmp_path, "plugins.yaml", """
slots:
  - id: slot1
    name: TestSlot
""")
        tree = load_projection_tree(tmp_path)
        assert tree.get_node("slot1") is not None

    def test_load_schedules_from_directory(self, tmp_path: Path) -> None:
        _write_yaml(tmp_path, "schedules.yaml", """
schedules:
  - id: cal1
    calendar_type: academic
""")
        tree = load_projection_tree(tmp_path)
        assert tree.get_node("cal1") is not None

    def test_load_financial_from_directory(self, tmp_path: Path) -> None:
        _write_yaml(tmp_path, "financial.yaml", """
ledgers:
  - id: ledger1
    currency: USD
""")
        tree = load_projection_tree(tmp_path)
        assert tree.get_node("ledger1") is not None

    def test_load_reports_from_directory(self, tmp_path: Path) -> None:
        _write_yaml(tmp_path, "reports.yaml", """
reports:
  - id: r1
    data_sources: [Customer]
    fields: []
""")
        tree = load_projection_tree(tmp_path)
        assert tree.get_node("r1") is not None

    def test_load_etl_from_directory(self, tmp_path: Path) -> None:
        _write_yaml(tmp_path, "etl.yaml", """
migrations:
  - id: m1
    source_schema: v1
    target_schema: v2
""")
        tree = load_projection_tree(tmp_path)
        assert tree.get_node("m1") is not None

    def test_load_localization_from_directory(self, tmp_path: Path) -> None:
        _write_yaml(tmp_path, "localization.yaml", """
localizations:
  - id: l1
    entity_id: Product
    locales: [en]
""")
        tree = load_projection_tree(tmp_path)
        assert tree.get_node("l1") is not None

    def test_load_versioning_from_directory(self, tmp_path: Path) -> None:
        _write_yaml(tmp_path, "versioning.yaml", """
api_versions:
  - id: av1
    version: "1.0.0"
    api_id: api1
""")
        tree = load_projection_tree(tmp_path)
        assert tree.get_node("av1") is not None

    def test_load_payment_from_directory(self, tmp_path: Path) -> None:
        _write_yaml(tmp_path, "payment.yaml", """
payment_gateways:
  - id: pg1
    provider: stripe
""")
        tree = load_projection_tree(tmp_path)
        assert tree.get_node("pg1") is not None

    def test_load_catalog_from_directory(self, tmp_path: Path) -> None:
        _write_yaml(tmp_path, "catalog.yaml", """
catalogs:
  - id: cat1
    entity_id: Product
""")
        tree = load_projection_tree(tmp_path)
        assert tree.get_node("cat1") is not None

    def test_load_all_new_loaders_together(self, tmp_path: Path) -> None:
        """Test all 9 new loaders work together in one tree."""
        _write_yaml(tmp_path, "plugins.yaml", """
slots:
  - id: slot1
    name: TestSlot
""")
        _write_yaml(tmp_path, "schedules.yaml", """
schedules:
  - id: cal1
    calendar_type: academic
""")
        _write_yaml(tmp_path, "financial.yaml", """
ledgers:
  - id: ledger1
    currency: USD
""")
        _write_yaml(tmp_path, "reports.yaml", """
reports:
  - id: r1
    data_sources: [Customer]
    fields: []
""")
        _write_yaml(tmp_path, "etl.yaml", """
migrations:
  - id: m1
    source_schema: v1
    target_schema: v2
""")
        _write_yaml(tmp_path, "localization.yaml", """
localizations:
  - id: l1
    entity_id: Product
    locales: [en]
""")
        _write_yaml(tmp_path, "versioning.yaml", """
api_versions:
  - id: av1
    version: "1.0.0"
    api_id: api1
""")
        _write_yaml(tmp_path, "payment.yaml", """
payment_gateways:
  - id: pg1
    provider: stripe
""")
        _write_yaml(tmp_path, "catalog.yaml", """
catalogs:
  - id: cat1
    entity_id: Product
""")
        tree = load_projection_tree(tmp_path)
        expected_ids = {"slot1", "cal1", "ledger1", "r1", "m1", "l1", "av1", "pg1", "cat1"}
        actual_ids = set(tree.nodes.keys())
        assert expected_ids.issubset(actual_ids), f"Missing: {expected_ids - actual_ids}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
