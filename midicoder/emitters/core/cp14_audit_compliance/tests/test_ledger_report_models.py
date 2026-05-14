# coding: utf-8
"""
Tests for CP14 ledger and report models.

Covers:
- LedgerEntry: hash computation, chain verification, serialization
- ImmutableLedgerConfig: defaults, validation, serialization
- ComplianceReportConfig: defaults, validation, serialization
- ReportSummary: fields, serialization
- LedgerStorageBackend, LedgerVerificationMode, ReportFormat, ReportScope, ComplianceStandard
"""

import pytest
from datetime import datetime, timezone

from midicoder.emitters.core.cp14_audit_compliance.models import (
    ComplianceReportConfig,
    ComplianceStandard,
    LedgerEntry,
    LedgerStorageBackend,
    LedgerVerificationMode,
    ImmutableLedgerConfig,
    ReportFormat,
    ReportScope,
    ReportSummary,
)


class TestLedgerStorageBackend:
    def test_all_variants(self):
        assert LedgerStorageBackend.DATABASE == "database"
        assert LedgerStorageBackend.BLOCKCHAIN == "blockchain"
        assert LedgerStorageBackend.APPEND_ONLY_STORE == "append_only_store"
        assert LedgerStorageBackend.SIGNED_CHAIN == "signed_chain"


class TestLedgerVerificationMode:
    def test_all_variants(self):
        assert LedgerVerificationMode.HASH_CHAIN == "hash_chain"
        assert LedgerVerificationMode.MERKLE_TREE == "merkle_tree"
        assert LedgerVerificationMode.DIGITAL_SIGNATURE == "digital_signature"
        assert LedgerVerificationMode.COMBINED == "combined"


class TestReportFormat:
    def test_all_variants(self):
        assert ReportFormat.PDF == "pdf"
        assert ReportFormat.CSV == "csv"
        assert ReportFormat.JSON == "json"
        assert ReportFormat.HTML == "html"
        assert ReportFormat.XLSX == "xlsx"


class TestReportScope:
    def test_all_variants(self):
        assert ReportScope.ALL == "all"
        assert ReportScope.ENTITY == "entity"
        assert ReportScope.ACTOR == "actor"
        assert ReportScope.TIME_RANGE == "time_range"
        assert ReportScope.TENANT == "tenant"
        assert ReportScope.ACTION == "action"


class TestComplianceStandard:
    def test_all_variants(self):
        assert ComplianceStandard.SOC2 == "soc2"
        assert ComplianceStandard.GDPR == "gdpr"
        assert ComplianceStandard.HIPAA == "hipaa"
        assert ComplianceStandard.PCI_DSS == "pci_dss"
        assert ComplianceStandard.ISO27001 == "iso27001"
        assert ComplianceStandard.SOX == "sox"
        assert ComplianceStandard.CUSTOM == "custom"


class TestLedgerEntry:
    def test_create_defaults(self):
        entry = LedgerEntry(
            audit_trail_id="trail_1",
            sequence_number=1,
            data_hash="abc123",
        )
        assert entry.entry_id
        assert entry.timestamp
        assert entry.hash == ""
        assert entry.prev_hash == ""
        assert entry.signature == ""

    def test_compute_hash(self):
        entry = LedgerEntry(
            audit_trail_id="trail_1",
            sequence_number=1,
            data_hash="abc123",
            prev_hash="prev_hash_value",
        )
        h = entry.compute_hash()
        assert len(h) == 64  # SHA-256 hex
        assert h == entry.compute_hash()  # deterministic

    def test_compute_hash_deterministic(self):
        ts = datetime.now(timezone.utc)
        entry1 = LedgerEntry(
            audit_trail_id="trail_1",
            sequence_number=1,
            data_hash="abc123",
            prev_hash="prev_hash_value",
            timestamp=ts,
        )
        entry2 = LedgerEntry(
            audit_trail_id="trail_1",
            sequence_number=1,
            data_hash="abc123",
            prev_hash="prev_hash_value",
            timestamp=ts,
        )
        assert entry1.compute_hash() == entry2.compute_hash()

    def test_compute_hash_changes_with_prev_hash(self):
        entry1 = LedgerEntry(
            audit_trail_id="trail_1",
            sequence_number=1,
            data_hash="abc123",
            prev_hash="prev_hash_value",
        )
        entry2 = LedgerEntry(
            audit_trail_id="trail_1",
            sequence_number=1,
            data_hash="abc123",
            prev_hash="different_prev_hash",
        )
        assert entry1.compute_hash() != entry2.compute_hash()

    def test_verify_chain_empty_hash(self):
        entry = LedgerEntry(audit_trail_id="trail_1", sequence_number=0)
        assert entry.verify_chain() is True  # empty hash = OK

    def test_verify_chain_valid(self):
        entry = LedgerEntry(
            audit_trail_id="trail_1",
            sequence_number=1,
            data_hash="abc123",
            prev_hash="prev_hash_value",
        )
        entry.hash = entry.compute_hash()
        assert entry.verify_chain() is True

    def test_verify_chain_tampered(self):
        entry = LedgerEntry(
            audit_trail_id="trail_1",
            sequence_number=1,
            data_hash="abc123",
            prev_hash="prev_hash_value",
        )
        entry.hash = entry.compute_hash()
        entry.hash = "tampered_hash_value"
        assert entry.verify_chain() is False

    def test_to_dict(self):
        entry = LedgerEntry(
            entry_id="id_1",
            audit_trail_id="trail_1",
            sequence_number=5,
            hash="hash_value",
            prev_hash="prev_hash_value",
            data_hash="data_hash",
            signature="sig",
            metadata={"key": "value"},
        )
        d = entry.to_dict()
        assert d["entry_id"] == "id_1"
        assert d["audit_trail_id"] == "trail_1"
        assert d["sequence_number"] == 5
        assert d["hash"] == "hash_value"
        assert d["prev_hash"] == "prev_hash_value"
        assert d["signature"] == "sig"
        assert d["metadata"]["key"] == "value"

    def test_from_dict(self):
        data = {
            "entry_id": "id_1",
            "audit_trail_id": "trail_1",
            "sequence_number": 5,
            "hash": "hash_value",
            "prev_hash": "prev_hash_value",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data_hash": "data_hash",
            "signature": "sig",
            "metadata": {"key": "value"},
        }
        entry = LedgerEntry.from_dict(data)
        assert entry.entry_id == "id_1"
        assert entry.audit_trail_id == "trail_1"
        assert entry.sequence_number == 5
        assert entry.metadata == {"key": "value"}

    def test_negative_sequence_raises(self):
        with pytest.raises(Exception):
            LedgerEntry(sequence_number=-1)

    def test_zero_sequence_ok(self):
        entry = LedgerEntry(sequence_number=0)
        assert entry.sequence_number == 0

    def test_chain_linking(self):
        """Test that entries can form a valid chain."""
        entry1 = LedgerEntry(
            audit_trail_id="trail_1",
            sequence_number=0,
            data_hash="hash_1",
            prev_hash="",
        )
        entry1.hash = entry1.compute_hash()

        entry2 = LedgerEntry(
            audit_trail_id="trail_2",
            sequence_number=1,
            data_hash="hash_2",
            prev_hash=entry1.hash,
        )
        entry2.hash = entry2.compute_hash()

        assert entry1.verify_chain() is True
        assert entry2.verify_chain() is True

        # Tamper entry1 → entry2's chain should still verify (entry2 hash is correct)
        # but entry1.prev_hash change would change entry1.hash
        entry1.data_hash = "tampered"
        assert entry1.compute_hash() != entry1.hash  # new hash != stored hash


class TestImmutableLedgerConfig:
    def test_defaults(self):
        config = ImmutableLedgerConfig()
        assert config.enabled is True
        assert config.backend == LedgerStorageBackend.DATABASE
        assert config.verification_mode == LedgerVerificationMode.HASH_CHAIN
        assert config.batch_size == 100
        assert config.enable_merkle_root is False
        assert config.merkle_batch_size == 1000
        assert config.retention_days == 0
        assert config.sign_key_path == ""

    def test_batch_size_clamped(self):
        config = ImmutableLedgerConfig(batch_size=0)
        assert config.batch_size == 100

    def test_merkle_batch_size_clamped(self):
        config = ImmutableLedgerConfig(merkle_batch_size=-5)
        assert config.merkle_batch_size == 1000

    def test_retention_days_clamped(self):
        config = ImmutableLedgerConfig(retention_days=-1)
        assert config.retention_days == 0

    def test_to_dict(self):
        config = ImmutableLedgerConfig(
            backend=LedgerStorageBackend.BLOCKCHAIN,
            verification_mode=LedgerVerificationMode.COMBINED,
        )
        d = config.to_dict()
        assert d["backend"] == "blockchain"
        assert d["verification_mode"] == "combined"

    def test_from_dict(self):
        data = {
            "enabled": True,
            "backend": "blockchain",
            "verification_mode": "combined",
            "batch_size": 50,
            "enable_merkle_root": True,
            "merkle_batch_size": 500,
            "retention_days": 365,
            "sign_key_path": "/path/to/key",
            "description": "test config",
        }
        config = ImmutableLedgerConfig.from_dict(data)
        assert config.backend == LedgerStorageBackend.BLOCKCHAIN
        assert config.verification_mode == LedgerVerificationMode.COMBINED
        assert config.batch_size == 50
        assert config.enable_merkle_root is True
        assert config.sign_key_path == "/path/to/key"

    def test_all_backend_variants(self):
        for backend in LedgerStorageBackend:
            config = ImmutableLedgerConfig(backend=backend)
            assert config.backend == backend

    def test_all_verification_modes(self):
        for mode in LedgerVerificationMode:
            config = ImmutableLedgerConfig(verification_mode=mode)
            assert config.verification_mode == mode


class TestComplianceReportConfig:
    def test_defaults(self):
        config = ComplianceReportConfig()
        assert config.report_format == ReportFormat.PDF
        assert config.standard == ComplianceStandard.SOC2
        assert config.scope == ReportScope.ALL
        assert config.include_evidence is True
        assert config.include_ledger_verification is True
        assert config.auto_generate is False

    def test_cron_sets_auto_generate(self):
        config = ComplianceReportConfig(schedule_cron="0 0 1 * *")
        assert config.auto_generate is True

    def test_to_dict(self):
        config = ComplianceReportConfig(
            standard=ComplianceStandard.GDPR,
            report_format=ReportFormat.CSV,
        )
        d = config.to_dict()
        assert d["standard"] == "gdpr"
        assert d["report_format"] == "csv"

    def test_from_dict(self):
        data = {
            "report_format": "xlsx",
            "standard": "hipaa",
            "scope": "entity",
            "scope_filter": "Patient",
            "auto_generate": True,
            "schedule_cron": "0 0 * * *",
            "recipients": ["admin@example.com"],
        }
        config = ComplianceReportConfig.from_dict(data)
        assert config.report_format == ReportFormat.XLSX
        assert config.standard == ComplianceStandard.HIPAA
        assert config.scope == ReportScope.ENTITY
        assert config.scope_filter == "Patient"
        assert config.recipients == ["admin@example.com"]

    def test_all_formats(self):
        for fmt in ReportFormat:
            config = ComplianceReportConfig(report_format=fmt)
            assert config.report_format == fmt

    def test_all_standards(self):
        for std in ComplianceStandard:
            config = ComplianceReportConfig(standard=std)
            assert config.standard == std

    def test_all_scopes(self):
        for scope in ReportScope:
            config = ComplianceReportConfig(scope=scope)
            assert config.scope == scope


class TestReportSummary:
    def test_defaults(self):
        summary = ReportSummary()
        assert summary.total_events == 0
        assert summary.events_by_action == {}
        assert summary.ledger_verified is True
        assert summary.ledger_breaks == 0
        assert summary.generated_at

    def test_populated(self):
        summary = ReportSummary(
            total_events=100,
            events_by_action={"CREATE": 50, "UPDATE": 30, "DELETE": 20},
            events_by_entity={"Order": 60, "Customer": 40},
            violations_count=2,
            violations=[{"control": "c1", "detail": "missing evidence"}],
            ledger_verified=False,
            ledger_breaks=1,
            period_start="2024-01-01",
            period_end="2024-12-31",
        )
        assert summary.total_events == 100
        assert summary.ledger_verified is False

    def test_to_dict(self):
        summary = ReportSummary(
            total_events=50,
            violations_count=3,
            ledger_verified=False,
        )
        d = summary.to_dict()
        assert d["total_events"] == 50
        assert d["violations_count"] == 3
        assert d["ledger_verified"] is False

    def test_from_dict(self):
        data = {
            "total_events": 200,
            "events_by_action": {"CREATE": 100, "DELETE": 100},
            "violations_count": 5,
            "violations": [{"control": "c1", "detail": "violation 1"}],
            "ledger_verified": False,
            "ledger_breaks": 2,
            "period_start": "2024-01-01",
            "period_end": "2024-12-31",
            "generated_at": "2024-12-31T23:59:59Z",
        }
        summary = ReportSummary.from_dict(data)
        assert summary.total_events == 200
        assert summary.violations_count == 5
        assert summary.ledger_verified is False
        assert summary.ledger_breaks == 2

    def test_roundtrip(self):
        original = ReportSummary(
            total_events=75,
            events_by_entity={"Order": 75},
            violations=[{"control": "sox_immutable", "detail": "test"}],
            period_start="2024-01-01",
            period_end="2024-12-31",
        )
        d = original.to_dict()
        restored = ReportSummary.from_dict(d)
        assert restored.total_events == original.total_events
        assert restored.events_by_entity == original.events_by_entity
        assert restored.violations == original.violations
        assert restored.period_start == original.period_start
