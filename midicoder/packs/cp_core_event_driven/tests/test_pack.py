"""Tests for pack.yml manifest and __init__.py exports."""

from __future__ import annotations

from pathlib import Path

import yaml


class TestPackYAML:
    def test_pack_yml_exists(self):
        pack_path = Path("midicoder/packs/cp_core_event_driven/pack.yml")
        assert pack_path.exists()

    def test_pack_yml_has_correct_id(self):
        pack_path = Path("midicoder/packs/cp_core_event_driven/pack.yml")
        with open(pack_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data["pack"]["id"] == "CP05"

    def test_pack_yml_has_correct_name(self):
        pack_path = Path("midicoder/packs/cp_core_event_driven/pack.yml")
        with open(pack_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert "Event-Driven" in data["pack"]["name"]

    def test_pack_yml_capabilities_provided(self):
        pack_path = Path("midicoder/packs/cp_core_event_driven/pack.yml")
        with open(pack_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        caps = data["pack"]["capabilities_provided"]
        assert "publish_event" in caps
        assert "subscribe_event" in caps
        assert "event_outbox" in caps
        assert "event_sourcing" in caps
        assert "transport_abstraction" in caps
        assert "dead_letter_queue" in caps

    def test_pack_yml_status_is_stable(self):
        pack_path = Path("midicoder/packs/cp_core_event_driven/pack.yml")
        with open(pack_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data["pack"]["status"] == "stable"

    def test_pack_yml_error_codes_prefix(self):
        pack_path = Path("midicoder/packs/cp_core_event_driven/pack.yml")
        with open(pack_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data["pack"]["error_codes"]["prefix"] == "MDC-CP05"

    def test_pack_yml_definitions_count_updated(self):
        pack_path = Path("midicoder/packs/cp_core_event_driven/pack.yml")
        with open(pack_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data["pack"]["definitions_count"] >= 10

    def test_pack_yml_no_frontend_integration(self):
        pack_path = Path("midicoder/packs/cp_core_event_driven/pack.yml")
        with open(pack_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert "frontend_integration" not in data["pack"]

    def test_pack_yml_infrastructure_files(self):
        pack_path = Path("midicoder/packs/cp_core_event_driven/pack.yml")
        with open(pack_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        infra = data["pack"]["file_contributions"]["infrastructure"]
        assert len(infra) >= 10

    def test_pack_yml_templates_exist(self):
        pack_path = Path("midicoder/packs/cp_core_event_driven/pack.yml")
        with open(pack_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        stacks_base = Path("midicoder/stacks")
        for fc in data["pack"]["file_contributions"]["infrastructure"]:
            for stack in fc.get("stacks", []):
                template = fc["template"]
                template_path = stacks_base / stack / "core" / template
                assert template_path.exists(), f"Missing template: {template_path}"


class TestInitExports:
    def test_import_all_models(self):
        from midicoder.packs.cp_core_event_driven import (
            CQRSProjection,
            DeliveryGuarantee,
            DLQConfig,
            DLQPolicy,
            EventDefinition,
            EventSchemaVersion,
            EventStoreBackend,
            EventStoreConfig,
            EventStream,
            IdempotencyStrategy,
            IdempotentConsumer,
            MaterializationStrategy,
            OutboxEntry,
            RetryPolicy,
            RetryStrategy,
            SchemaEvolutionPolicy,
            SnapshotStrategy,
            TransportConfig,
            TransportType,
        )
        assert EventDefinition is not None
        assert OutboxEntry is not None
        assert TransportConfig is not None
        assert DLQConfig is not None
        assert EventStoreConfig is not None
        assert RetryPolicy is not None
        assert IdempotentConsumer is not None
        assert EventSchemaVersion is not None
        assert EventStream is not None
        assert CQRSProjection is not None

    def test_import_parser(self):
        from midicoder.packs.cp_core_event_driven import EventParser
        assert EventParser is not None

    def test_import_emitters(self):
        from midicoder.packs.cp_core_event_driven import (
            FastAPIEventEmitter,
            NestJSEventEmitter,
        )
        assert FastAPIEventEmitter is not None
        assert NestJSEventEmitter is not None

    def test_all_exports_defined(self):
        import midicoder.packs.cp_core_event_driven as cp05

        for name in cp05.__all__:
            assert hasattr(cp05, name), f"Missing export: {name}"
