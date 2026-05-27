# coding: utf-8
"""
Tests cho CP47 models — Data Retention & Lifecycle Management.

Bao phủ:
- TestCP47ErrorCodes: 10 error codes
- TestRetentionAction: 4 hành động
- TestRetentionPolicyType: 3 loại
- TestRetentionPolicyStatus: 3 trạng thái
- TestArchiveStatus: 4 trạng thái (state machine)
- TestErasureStatus: 5 trạng thái
- TestRetentionPolicy: tạo, validate, is_active, is_unlimited, to_dict, from_dict
- TestArchivedRecord: tạo, validate, is_restorable, to_dict, from_dict
- TestErasureRequest: tạo, validate, completion_percentage, is_in_progress, to_dict, from_dict
- TestRetentionEngine: toàn bộ engine methods

Tổng: ~110 tests
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone

from midicoder.packs.cp47_retention.models import (
    ArchiveStatus,
    ArchivedRecord,
    ErasureRequest,
    ErasureStatus,
    RetentionAction,
    RetentionEngine,
    RetentionPolicy,
    RetentionPolicyStatus,
    RetentionPolicyType,
)
from midicoder.errors import ErrorCode, MidicoderError


# ===========================================================================
# Error Codes
# ===========================================================================


class TestCP47ErrorCodes:
    """Test 10 error codes của CP47."""

    def test_retention_policy_not_found_code(self):
        assert ErrorCode.CP47_RETENTION_POLICY_NOT_FOUND.value == "MDC-CP47-001"

    def test_retention_days_invalid_code(self):
        assert ErrorCode.CP47_RETENTION_DAYS_INVALID.value == "MDC-CP47-002"

    def test_archive_failed_code(self):
        assert ErrorCode.CP47_ARCHIVE_FAILED.value == "MDC-CP47-003"

    def test_purge_not_allowed_code(self):
        assert ErrorCode.CP47_PURGE_NOT_ALLOWED.value == "MDC-CP47-004"

    def test_erasure_request_not_found_code(self):
        assert ErrorCode.CP47_ERASURE_REQUEST_NOT_FOUND.value == "MDC-CP47-005"

    def test_erasure_in_progress_code(self):
        assert ErrorCode.CP47_ERASURE_IN_PROGRESS.value == "MDC-CP47-006"

    def test_cold_storage_unavailable_code(self):
        assert ErrorCode.CP47_COLD_STORAGE_UNAVAILABLE.value == "MDC-CP47-007"

    def test_retention_scan_failed_code(self):
        assert ErrorCode.CP47_RETENTION_SCAN_FAILED.value == "MDC-CP47-008"

    def test_exemption_already_exists_code(self):
        assert ErrorCode.CP47_EXEMPTION_ALREADY_EXISTS.value == "MDC-CP47-009"

    def test_restore_failed_code(self):
        assert ErrorCode.CP47_RESTORE_FAILED.value == "MDC-CP47-010"


# ===========================================================================
# Enums
# ===========================================================================


class TestRetentionAction:
    def test_archive(self):
        assert RetentionAction.ARCHIVE.value == "archive"

    def test_purge(self):
        assert RetentionAction.PURGE.value == "purge"

    def test_anonymize(self):
        assert RetentionAction.ANONYMIZE.value == "anonymize"

    def test_archive_then_purge(self):
        assert RetentionAction.ARCHIVE_THEN_PURGE.value == "archive_then_purge"


class TestRetentionPolicyType:
    def test_time_based(self):
        assert RetentionPolicyType.TIME_BASED.value == "time_based"

    def test_event_based(self):
        assert RetentionPolicyType.EVENT_BASED.value == "event_based"

    def test_status_based(self):
        assert RetentionPolicyType.STATUS_BASED.value == "status_based"


class TestRetentionPolicyStatus:
    def test_active(self):
        assert RetentionPolicyStatus.ACTIVE.value == "active"

    def test_paused(self):
        assert RetentionPolicyStatus.PAUSED.value == "paused"

    def test_expired(self):
        assert RetentionPolicyStatus.EXPIRED.value == "expired"


class TestArchiveStatus:
    def test_pending(self):
        assert ArchiveStatus.PENDING.value == "pending"

    def test_archiving(self):
        assert ArchiveStatus.ARCHIVING.value == "archiving"

    def test_archived(self):
        assert ArchiveStatus.ARCHIVED.value == "archived"

    def test_failed(self):
        assert ArchiveStatus.FAILED.value == "failed"


class TestErasureStatus:
    def test_pending(self):
        assert ErasureStatus.PENDING.value == "pending"

    def test_processing(self):
        assert ErasureStatus.PROCESSING.value == "processing"

    def test_completed(self):
        assert ErasureStatus.COMPLETED.value == "completed"

    def test_failed(self):
        assert ErasureStatus.FAILED.value == "failed"

    def test_partially_completed(self):
        assert ErasureStatus.PARTIALLY_COMPLETED.value == "partially_completed"


# ===========================================================================
# RetentionPolicy
# ===========================================================================


class TestRetentionPolicy:
    def test_create_valid_policy(self):
        policy = RetentionPolicy(
            policy_id="policy_001",
            entity_type="Order",
            retention_days=90,
        )
        assert policy.policy_id == "policy_001"
        assert policy.entity_type == "Order"
        assert policy.retention_days == 90
        assert policy.action == RetentionAction.ARCHIVE
        assert policy.status == RetentionPolicyStatus.ACTIVE
        assert policy.is_active is True

    def test_empty_policy_id_raises_error(self):
        with pytest.raises(MidicoderError):
            RetentionPolicy(policy_id="", entity_type="Order")

    def test_whitespace_only_policy_id_raises_error(self):
        with pytest.raises(MidicoderError):
            RetentionPolicy(policy_id="   ", entity_type="Order")

    def test_empty_entity_type_raises_error(self):
        with pytest.raises(MidicoderError):
            RetentionPolicy(policy_id="p1", entity_type="")

    def test_negative_retention_days_raises_error(self):
        with pytest.raises(MidicoderError):
            RetentionPolicy(policy_id="p1", entity_type="Order", retention_days=-1)

    def test_zero_retention_days_is_unlimited(self):
        policy = RetentionPolicy(policy_id="p1", entity_type="Order", retention_days=0)
        assert policy.is_unlimited is True

    def test_positive_retention_days_is_not_unlimited(self):
        policy = RetentionPolicy(policy_id="p1", entity_type="Order", retention_days=365)
        assert policy.is_unlimited is False

    def test_is_active_when_active(self):
        policy = RetentionPolicy(
            policy_id="p1", entity_type="Order",
            status=RetentionPolicyStatus.ACTIVE,
        )
        assert policy.is_active is True

    def test_is_active_when_paused(self):
        policy = RetentionPolicy(
            policy_id="p1", entity_type="Order",
            status=RetentionPolicyStatus.PAUSED,
        )
        assert policy.is_active is False

    def test_is_active_when_expired(self):
        policy = RetentionPolicy(
            policy_id="p1", entity_type="Order",
            status=RetentionPolicyStatus.EXPIRED,
        )
        assert policy.is_active is False

    def test_to_dict(self):
        policy = RetentionPolicy(
            policy_id="p1",
            entity_type="User",
            retention_days=180,
            action=RetentionAction.PURGE,
            policy_type=RetentionPolicyType.EVENT_BASED,
            created_by="admin",
            tenant_id="tenant_1",
            description="Chính sách xóa user",
        )
        d = policy.to_dict()
        assert d["policy_id"] == "p1"
        assert d["entity_type"] == "User"
        assert d["retention_days"] == 180
        assert d["action"] == "purge"
        assert d["policy_type"] == "event_based"
        assert d["created_by"] == "admin"
        assert d["tenant_id"] == "tenant_1"

    def test_from_dict(self):
        data = {
            "policy_id": "p_from",
            "entity_type": "Transaction",
            "retention_days": 730,
            "action": "anonymize",
            "policy_type": "status_based",
            "status": "paused",
        }
        policy = RetentionPolicy.from_dict(data)
        assert policy.policy_id == "p_from"
        assert policy.action == RetentionAction.ANONYMIZE
        assert policy.policy_type == RetentionPolicyType.STATUS_BASED
        assert policy.status == RetentionPolicyStatus.PAUSED

    def test_roundtrip(self):
        policy = RetentionPolicy(
            policy_id="rt_policy",
            entity_type="Log",
            retention_days=30,
            action=RetentionAction.ARCHIVE_THEN_PURGE,
            description="Roundtrip test",
            created_by="tester",
        )
        restored = RetentionPolicy.from_dict(policy.to_dict())
        assert restored.policy_id == policy.policy_id
        assert restored.entity_type == policy.entity_type
        assert restored.retention_days == policy.retention_days
        assert restored.action == policy.action
        assert restored.description == policy.description
        assert restored.created_by == policy.created_by


# ===========================================================================
# ArchivedRecord
# ===========================================================================


class TestArchivedRecord:
    def test_create_valid_archive(self):
        record = ArchivedRecord(
            archive_id="arc_001",
            original_entity_type="Order",
            original_entity_id="order_123",
        )
        assert record.archive_id == "arc_001"
        assert record.original_entity_type == "Order"
        assert record.original_entity_id == "order_123"
        assert record.archive_reason == "retention_exceeded"
        assert record.archive_status == ArchiveStatus.PENDING
        assert record.archived_at is not None

    def test_empty_archive_id_raises_error(self):
        with pytest.raises(MidicoderError):
            ArchivedRecord(archive_id="", original_entity_type="Order", original_entity_id="o1")

    def test_whitespace_archive_id_raises_error(self):
        with pytest.raises(MidicoderError):
            ArchivedRecord(archive_id="  ", original_entity_type="Order", original_entity_id="o1")

    def test_empty_entity_type_raises_error(self):
        with pytest.raises(MidicoderError):
            ArchivedRecord(archive_id="a1", original_entity_type="", original_entity_id="o1")

    def test_empty_entity_id_raises_error(self):
        with pytest.raises(MidicoderError):
            ArchivedRecord(archive_id="a1", original_entity_type="Order", original_entity_id="")

    def test_is_restorable_when_archived(self):
        record = ArchivedRecord(
            archive_id="a1", original_entity_type="Order",
            original_entity_id="o1", archive_status=ArchiveStatus.ARCHIVED,
        )
        assert record.is_restorable is True

    def test_is_restorable_when_pending(self):
        record = ArchivedRecord(
            archive_id="a1", original_entity_type="Order",
            original_entity_id="o1", archive_status=ArchiveStatus.PENDING,
        )
        assert record.is_restorable is False

    def test_is_restorable_when_failed(self):
        record = ArchivedRecord(
            archive_id="a1", original_entity_type="Order",
            original_entity_id="o1", archive_status=ArchiveStatus.FAILED,
        )
        assert record.is_restorable is False

    def test_is_restorable_after_restore(self):
        record = ArchivedRecord(
            archive_id="a1", original_entity_type="Order",
            original_entity_id="o1", archive_status=ArchiveStatus.ARCHIVED,
            restored_at=datetime.now(timezone.utc),
        )
        assert record.is_restorable is False

    def test_to_dict(self):
        record = ArchivedRecord(
            archive_id="arc_001",
            original_entity_type="User",
            original_entity_id="user_456",
            archive_reason="manual",
            archive_status=ArchiveStatus.ARCHIVED,
            cold_storage_location="cold://users/user_456",
            tenant_id="tenant_1",
        )
        d = record.to_dict()
        assert d["archive_id"] == "arc_001"
        assert d["archive_status"] == "archived"
        assert d["cold_storage_location"] == "cold://users/user_456"
        assert d["archive_reason"] == "manual"
        assert d["tenant_id"] == "tenant_1"

    def test_from_dict(self):
        data = {
            "archive_id": "arc_from",
            "original_entity_type": "Log",
            "original_entity_id": "log_789",
            "archive_status": "archived",
            "cold_storage_location": "cold://logs/log_789",
        }
        record = ArchivedRecord.from_dict(data)
        assert record.archive_id == "arc_from"
        assert record.archive_status == ArchiveStatus.ARCHIVED
        assert record.cold_storage_location == "cold://logs/log_789"

    def test_roundtrip(self):
        record = ArchivedRecord(
            archive_id="arc_rt",
            original_entity_type="Transaction",
            original_entity_id="tx_001",
            archive_reason="retention_exceeded",
            data_snapshot={"amount": 1000, "currency": "VND"},
            archive_status=ArchiveStatus.ARCHIVED,
            cold_storage_location="cold://tx/tx_001",
        )
        restored = ArchivedRecord.from_dict(record.to_dict())
        assert restored.archive_id == record.archive_id
        assert restored.original_entity_type == record.original_entity_type
        assert restored.original_entity_id == record.original_entity_id
        assert restored.archive_status == record.archive_status
        assert restored.cold_storage_location == record.cold_storage_location


# ===========================================================================
# ErasureRequest
# ===========================================================================


class TestErasureRequest:
    def test_create_valid_erasure(self):
        req = ErasureRequest(
            request_id="erase_001",
            subject_id="user_abc",
        )
        assert req.request_id == "erase_001"
        assert req.subject_id == "user_abc"
        assert req.request_reason == "gdpr_right_to_erasure"
        assert req.erasure_status == ErasureStatus.PENDING
        assert req.requested_at is not None

    def test_empty_request_id_raises_error(self):
        with pytest.raises(MidicoderError):
            ErasureRequest(request_id="", subject_id="user_abc")

    def test_whitespace_request_id_raises_error(self):
        with pytest.raises(MidicoderError):
            ErasureRequest(request_id="  ", subject_id="user_abc")

    def test_empty_subject_id_raises_error(self):
        with pytest.raises(MidicoderError):
            ErasureRequest(request_id="e1", subject_id="")

    def test_completion_percentage_zero_when_no_entities(self):
        req = ErasureRequest(request_id="e1", subject_id="u1")
        assert req.completion_percentage == 0.0

    def test_completion_percentage_fully_completed(self):
        req = ErasureRequest(
            request_id="e1", subject_id="u1",
            entities_found=[{"type": "A"}, {"type": "B"}],
            entities_erased=[{"type": "A"}, {"type": "B"}],
        )
        assert req.completion_percentage == 100.0

    def test_completion_percentage_partial(self):
        req = ErasureRequest(
            request_id="e1", subject_id="u1",
            entities_found=[{"type": "A"}, {"type": "B"}, {"type": "C"}],
            entities_erased=[{"type": "A"}],
        )
        assert req.completion_percentage == pytest.approx(33.33333333333333)

    def test_is_in_progress_when_pending(self):
        req = ErasureRequest(
            request_id="e1", subject_id="u1",
            erasure_status=ErasureStatus.PENDING,
        )
        assert req.is_in_progress is True

    def test_is_in_progress_when_processing(self):
        req = ErasureRequest(
            request_id="e1", subject_id="u1",
            erasure_status=ErasureStatus.PROCESSING,
        )
        assert req.is_in_progress is True

    def test_is_in_progress_when_completed(self):
        req = ErasureRequest(
            request_id="e1", subject_id="u1",
            erasure_status=ErasureStatus.COMPLETED,
        )
        assert req.is_in_progress is False

    def test_is_in_progress_when_failed(self):
        req = ErasureRequest(
            request_id="e1", subject_id="u1",
            erasure_status=ErasureStatus.FAILED,
        )
        assert req.is_in_progress is False

    def test_to_dict(self):
        req = ErasureRequest(
            request_id="erase_001",
            subject_id="user_123",
            request_reason="account_closure",
            erasure_status=ErasureStatus.PROCESSING,
            requested_by="admin",
            tenant_id="tenant_1",
        )
        d = req.to_dict()
        assert d["request_id"] == "erase_001"
        assert d["subject_id"] == "user_123"
        assert d["erasure_status"] == "processing"
        assert d["requested_by"] == "admin"
        assert d["request_reason"] == "account_closure"

    def test_from_dict(self):
        data = {
            "request_id": "erase_from",
            "subject_id": "user_xyz",
            "erasure_status": "completed",
            "request_reason": "gdpr_right_to_erasure",
        }
        req = ErasureRequest.from_dict(data)
        assert req.request_id == "erase_from"
        assert req.subject_id == "user_xyz"
        assert req.erasure_status == ErasureStatus.COMPLETED

    def test_roundtrip(self):
        req = ErasureRequest(
            request_id="erase_rt",
            subject_id="subject_001",
            request_reason="manual",
            entities_found=[{"type": "Order", "id": "o1"}],
            entities_erased=[{"type": "Order", "id": "o1"}],
            entities_failed=[],
            erasure_status=ErasureStatus.PARTIALLY_COMPLETED,
            requested_by="gdpr_admin",
        )
        restored = ErasureRequest.from_dict(req.to_dict())
        assert restored.request_id == req.request_id
        assert restored.subject_id == req.subject_id
        assert restored.erasure_status == req.erasure_status
        assert restored.requested_by == req.requested_by
        assert restored.entities_found == req.entities_found


# ===========================================================================
# RetentionEngine
# ===========================================================================


class TestRetentionEngine:
    def test_create_engine(self):
        engine = RetentionEngine()
        assert engine.policies == {}
        assert engine.archives == {}
        assert engine.erasures == {}
        assert engine.exemptions == {}

    # -- Policy Management --
    def test_register_policy(self):
        engine = RetentionEngine()
        policy = RetentionPolicy(policy_id="p1", entity_type="Order")
        result = engine.register_policy(policy)
        assert result.policy_id == "p1"
        assert "p1" in engine.policies

    def test_get_policy(self):
        engine = RetentionEngine()
        policy = RetentionPolicy(policy_id="p1", entity_type="User")
        engine.register_policy(policy)
        result = engine.get_policy("p1")
        assert result.entity_type == "User"

    def test_get_policy_not_found(self):
        engine = RetentionEngine()
        with pytest.raises(MidicoderError):
            engine.get_policy("nonexistent")

    def test_pause_policy(self):
        engine = RetentionEngine()
        policy = RetentionPolicy(policy_id="p1", entity_type="Order")
        engine.register_policy(policy)
        result = engine.pause_policy("p1")
        assert result.status == RetentionPolicyStatus.PAUSED
        assert result.is_active is False

    def test_pause_policy_not_found(self):
        engine = RetentionEngine()
        with pytest.raises(MidicoderError):
            engine.pause_policy("nonexistent")

    def test_get_policy_for_entity(self):
        engine = RetentionEngine()
        engine.register_policy(RetentionPolicy(policy_id="p1", entity_type="Order"))
        result = engine.get_policy_for_entity("Order")
        assert result.policy_id == "p1"

    def test_get_policy_for_entity_no_match(self):
        engine = RetentionEngine()
        engine.register_policy(RetentionPolicy(policy_id="p1", entity_type="Order"))
        result = engine.get_policy_for_entity("User")
        assert result is None

    def test_get_policy_for_entity_ignores_paused(self):
        engine = RetentionEngine()
        policy = RetentionPolicy(
            policy_id="p1", entity_type="Order",
            status=RetentionPolicyStatus.PAUSED,
        )
        engine.register_policy(policy)
        result = engine.get_policy_for_entity("Order")
        assert result is None

    def test_get_active_policies(self):
        engine = RetentionEngine()
        engine.register_policy(RetentionPolicy(policy_id="p1", entity_type="Order"))
        engine.register_policy(RetentionPolicy(policy_id="p2", entity_type="User"))
        paused = RetentionPolicy(policy_id="p3", entity_type="Log", status=RetentionPolicyStatus.PAUSED)
        engine.register_policy(paused)
        active = engine.get_active_policies()
        assert len(active) == 2

    def test_get_active_policies_empty(self):
        engine = RetentionEngine()
        active = engine.get_active_policies()
        assert len(active) == 0

    # -- Exemption Management --
    def test_add_exemption(self):
        engine = RetentionEngine()
        engine.add_exemption("entity_001", "legal_hold")
        assert "entity_001" in engine.exemptions
        assert engine.exemptions["entity_001"] == "legal_hold"

    def test_add_exemption_duplicate_raises_error(self):
        engine = RetentionEngine()
        engine.add_exemption("entity_001", "legal_hold")
        with pytest.raises(MidicoderError):
            engine.add_exemption("entity_001", "compliance")

    def test_get_exemption(self):
        engine = RetentionEngine()
        engine.add_exemption("entity_001", "audit_trail")
        assert engine.exemptions["entity_001"] == "audit_trail"

    def test_remove_exemption(self):
        engine = RetentionEngine()
        engine.add_exemption("entity_001", "manual")
        result = engine.remove_exemption("entity_001")
        assert result == "manual"
        assert "entity_001" not in engine.exemptions

    def test_remove_exemption_not_found(self):
        engine = RetentionEngine()
        with pytest.raises(MidicoderError):
            engine.remove_exemption("nonexistent")

    def test_is_exempted_true(self):
        engine = RetentionEngine()
        engine.add_exemption("entity_001", "legal_hold")
        assert engine.is_exempted("entity_001") is True

    def test_is_exempted_false(self):
        engine = RetentionEngine()
        assert engine.is_exempted("entity_001") is False

    # -- Archive Operations --
    def test_archive_record(self):
        engine = RetentionEngine()
        record = engine.archive_record(
            entity_type="Order",
            entity_id="order_123",
            data_snapshot={"id": "order_123", "amount": 50000},
            reason="retention_exceeded",
        )
        assert record.archive_id == "arc-order-order_123"
        assert record.archive_status == ArchiveStatus.ARCHIVED
        assert record.cold_storage_location == "cold://Order/order_123"
        assert record.original_entity_type == "Order"

    def test_archive_record_default_reason(self):
        engine = RetentionEngine()
        record = engine.archive_record(
            entity_type="User",
            entity_id="user_001",
            data_snapshot={"name": "Test"},
        )
        assert record.archive_reason == "retention_exceeded"

    def test_get_archive(self):
        engine = RetentionEngine()
        engine.archive_record("Order", "o1", {}, reason="manual")
        result = engine.get_archive("arc-order-o1")
        assert result.original_entity_id == "o1"

    def test_get_archive_not_found(self):
        engine = RetentionEngine()
        with pytest.raises(MidicoderError):
            engine.get_archive("nonexistent")

    def test_restore_record_success(self):
        engine = RetentionEngine()
        engine.archive_record("Order", "o1", {})
        result = engine.restore_record("arc-order-o1")
        assert result.restored_at is not None
        assert result.is_restorable is False

    def test_restore_record_not_found(self):
        engine = RetentionEngine()
        with pytest.raises(MidicoderError):
            engine.restore_record("nonexistent")

    def test_restore_record_not_restorable(self):
        engine = RetentionEngine()
        engine.archive_record("Order", "o1", {})
        archive = engine.archives["arc-order-o1"]
        archive.archive_status = ArchiveStatus.FAILED
        with pytest.raises(MidicoderError):
            engine.restore_record("arc-order-o1")

    # -- Erasure Operations --
    def test_create_erasure_request(self):
        engine = RetentionEngine()
        req = engine.create_erasure_request(
            subject_id="user_abc",
            reason="gdpr_right_to_erasure",
            requested_by="admin",
        )
        assert req.subject_id == "user_abc"
        assert req.request_reason == "gdpr_right_to_erasure"
        assert req.requested_by == "admin"
        assert req.request_id.startswith("erase-user_abc")
        assert req.request_id in engine.erasures

    def test_create_erasure_request_default_reason(self):
        engine = RetentionEngine()
        req = engine.create_erasure_request(subject_id="user_123")
        assert req.request_reason == "gdpr_right_to_erasure"

    def test_create_erasure_duplicate_in_progress_fails(self):
        engine = RetentionEngine()
        engine.create_erasure_request(subject_id="user_dup")
        with pytest.raises(MidicoderError):
            engine.create_erasure_request(subject_id="user_dup")

    def test_create_erasure_after_completed_is_allowed(self):
        engine = RetentionEngine()
        req = engine.create_erasure_request(subject_id="user_done")
        engine.complete_erasure(req.request_id, ErasureStatus.COMPLETED)
        new_req = engine.create_erasure_request(subject_id="user_done")
        # request có thể trùng ID nếu tạo trong cùng 1 giây, nhưng status sẽ khác
        assert new_req.erasure_status == ErasureStatus.PENDING
        assert req.erasure_status == ErasureStatus.COMPLETED

    def test_get_erasure_request(self):
        engine = RetentionEngine()
        req = engine.create_erasure_request(subject_id="user_get")
        result = engine.get_erasure_request(req.request_id)
        assert result.subject_id == "user_get"

    def test_get_erasure_request_not_found(self):
        engine = RetentionEngine()
        with pytest.raises(MidicoderError):
            engine.get_erasure_request("nonexistent")

    def test_complete_erasure(self):
        engine = RetentionEngine()
        req = engine.create_erasure_request(subject_id="user_complete")
        result = engine.complete_erasure(req.request_id)
        assert result.erasure_status == ErasureStatus.COMPLETED
        assert result.completed_at is not None

    def test_complete_erasure_with_failed_status(self):
        engine = RetentionEngine()
        req = engine.create_erasure_request(subject_id="user_fail")
        result = engine.complete_erasure(req.request_id, ErasureStatus.FAILED)
        assert result.erasure_status == ErasureStatus.FAILED

    def test_complete_erasure_not_found(self):
        engine = RetentionEngine()
        with pytest.raises(MidicoderError):
            engine.complete_erasure("nonexistent")

    # -- Scan Operations --
    def test_scan_expiring_records_with_policies(self):
        engine = RetentionEngine()
        engine.register_policy(RetentionPolicy(policy_id="p1", entity_type="Order", retention_days=90))
        engine.register_policy(RetentionPolicy(policy_id="p2", entity_type="User", retention_days=180))
        expiring = engine.scan_expiring_records()
        assert len(expiring) == 2
        types = {e["entity_type"] for e in expiring}
        assert "Order" in types
        assert "User" in types

    def test_scan_expiring_records_skips_unlimited(self):
        engine = RetentionEngine()
        engine.register_policy(RetentionPolicy(policy_id="p1", entity_type="Log", retention_days=0))
        engine.register_policy(RetentionPolicy(policy_id="p2", entity_type="Order", retention_days=30))
        expiring = engine.scan_expiring_records()
        assert len(expiring) == 1
        assert expiring[0]["entity_type"] == "Order"

    def test_scan_expiring_records_skips_paused(self):
        engine = RetentionEngine()
        paused = RetentionPolicy(
            policy_id="p1", entity_type="Log",
            status=RetentionPolicyStatus.PAUSED,
        )
        engine.register_policy(paused)
        engine.register_policy(RetentionPolicy(policy_id="p2", entity_type="Order", retention_days=30))
        expiring = engine.scan_expiring_records()
        assert len(expiring) == 1

    def test_scan_expiring_records_with_custom_time(self):
        engine = RetentionEngine()
        engine.register_policy(RetentionPolicy(policy_id="p1", entity_type="Order", retention_days=90))
        custom_time = datetime(2026, 5, 24, 12, 0, 0, tzinfo=timezone.utc)
        expiring = engine.scan_expiring_records(current_time=custom_time)
        assert len(expiring) == 1

    def test_scan_expiring_records_empty(self):
        engine = RetentionEngine()
        expiring = engine.scan_expiring_records()
        assert len(expiring) == 0

    def test_scan_expiring_records_contains_policy_info(self):
        engine = RetentionEngine()
        engine.register_policy(RetentionPolicy(
            policy_id="p1", entity_type="Order",
            retention_days=90, action=RetentionAction.PURGE,
        ))
        expiring = engine.scan_expiring_records()
        assert expiring[0]["action"] == "purge"
        assert expiring[0]["retention_days"] == 90

    # -- Statistics --
    def test_get_user_total_archived(self):
        engine = RetentionEngine()
        engine.archive_record("Order", "o1", {})
        engine.archive_record("User", "u1", {})
        pending = ArchivedRecord(
            archive_id="arc-pending",
            original_entity_type="Log",
            original_entity_id="l1",
            archive_status=ArchiveStatus.PENDING,
        )
        engine.archives["arc-pending"] = pending
        total = engine.get_user_total_archived()
        assert total == 2

    def test_get_user_total_archived_empty(self):
        engine = RetentionEngine()
        total = engine.get_user_total_archived()
        assert total == 0

    def test_get_user_total_erased(self):
        engine = RetentionEngine()
        req1 = engine.create_erasure_request(subject_id="u1")
        engine.complete_erasure(req1.request_id, ErasureStatus.COMPLETED)
        req2 = engine.create_erasure_request(subject_id="u2")
        engine.complete_erasure(req2.request_id, ErasureStatus.PARTIALLY_COMPLETED)
        req3 = engine.create_erasure_request(subject_id="u3")
        engine.complete_erasure(req3.request_id, ErasureStatus.FAILED)
        total = engine.get_user_total_erased()
        assert total == 2

    def test_get_user_total_erased_empty(self):
        engine = RetentionEngine()
        total = engine.get_user_total_erased()
        assert total == 0
