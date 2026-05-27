"""
Tests cho CP65 Backup & Recovery Models.

Unit tests cho:
- BackupType enum
- StorageBackend enum
- ScheduleType enum
- BackupPolicy validation, to_dict, from_dict
- RestorePoint validation, to_dict, from_dict
- RecoveryStep validation, to_dict, from_dict
- RecoveryPlan validation, to_dict, from_dict
- BackupMonitor validation, to_dict, from_dict

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from midicoder.packs.cp65_backup_recovery.models import (
    BackupType,
    StorageBackend,
    ScheduleType,
    BackupPolicy,
    RestorePoint,
    RecoveryStep,
    RecoveryPlan,
    BackupMonitor,
)
from midicoder.errors import ErrorCode, MidicoderError


# ===========================================================================
# Test BackupType
# ===========================================================================


class TestBackupType:
    """Tests cho BackupType enum."""

    def test_full_value(self):
        assert BackupType.FULL.value == "full"

    def test_incremental_value(self):
        assert BackupType.INCREMENTAL.value == "incremental"

    def test_differential_value(self):
        assert BackupType.DIFFERENTIAL.value == "differential"

    def test_point_in_time_value(self):
        assert BackupType.POINT_IN_TIME.value == "point_in_time"

    def test_from_string_full(self):
        assert BackupType("full") == BackupType.FULL

    def test_from_string_incremental(self):
        assert BackupType("incremental") == BackupType.INCREMENTAL

    def test_from_string_invalid(self):
        with pytest.raises(ValueError):
            BackupType("invalid_type")


# ===========================================================================
# Test StorageBackend
# ===========================================================================


class TestStorageBackend:
    """Tests cho StorageBackend enum."""

    def test_local_value(self):
        assert StorageBackend.LOCAL.value == "local"

    def test_s3_value(self):
        assert StorageBackend.S3.value == "s3"

    def test_gcs_value(self):
        assert StorageBackend.GCS.value == "gcs"

    def test_azure_blob_value(self):
        assert StorageBackend.AZURE_BLOB.value == "azure_blob"

    def test_k8s_volume_value(self):
        assert StorageBackend.K8S_VOLUME.value == "k8s_volume"

    def test_from_string_s3(self):
        assert StorageBackend("s3") == StorageBackend.S3

    def test_from_string_invalid(self):
        with pytest.raises(ValueError):
            StorageBackend("invalid_backend")


# ===========================================================================
# Test ScheduleType
# ===========================================================================


class TestScheduleType:
    """Tests cho ScheduleType enum."""

    def test_cron_value(self):
        assert ScheduleType.CRON.value == "cron"

    def test_fixed_interval_value(self):
        assert ScheduleType.FIXED_INTERVAL.value == "fixed_interval"

    def test_on_demand_value(self):
        assert ScheduleType.ON_DEMAND.value == "on_demand"

    def test_event_triggered_value(self):
        assert ScheduleType.EVENT_TRIGGERED.value == "event_triggered"

    def test_from_string_cron(self):
        assert ScheduleType("cron") == ScheduleType.CRON

    def test_from_string_invalid(self):
        with pytest.raises(ValueError):
            ScheduleType("invalid_schedule")


# ===========================================================================
# Test RecoveryStep
# ===========================================================================


class TestRecoveryStep:
    """Tests cho RecoveryStep."""

    def test_valid_recovery_step(self):
        rs = RecoveryStep(
            id="step-001",
            order=1,
            action="restore_db",
            target="postgresql://db:5432/app",
        )
        assert rs.id == "step-001"
        assert rs.order == 1
        assert rs.action == "restore_db"
        assert rs.timeout_minutes == 30
        assert rs.rollback_on_failure is True
        assert rs.dependencies == []

    def test_full_recovery_step(self):
        rs = RecoveryStep(
            id="step-002",
            order=2,
            action="apply_patch",
            target="server-1",
            timeout_minutes=60,
            rollback_on_failure=False,
            dependencies=["step-001"],
        )
        assert rs.timeout_minutes == 60
        assert rs.rollback_on_failure is False
        assert "step-001" in rs.dependencies

    def test_empty_id_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            RecoveryStep(id="", order=1, action="test", target="t")
        assert exc_info.value.code == ErrorCode.INVALID_ID

    def test_whitespace_id_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            RecoveryStep(id="  ", order=1, action="test", target="t")
        assert exc_info.value.code == ErrorCode.INVALID_ID

    def test_empty_action_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            RecoveryStep(id="s1", order=1, action="", target="t")
        assert exc_info.value.code == ErrorCode.INVALID_INPUT

    def test_negative_order_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            RecoveryStep(id="s1", order=-1, action="test", target="t")
        assert exc_info.value.code == ErrorCode.INVALID_INPUT

    def test_zero_timeout_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            RecoveryStep(id="s1", order=1, action="test", target="t", timeout_minutes=0)
        assert exc_info.value.code == ErrorCode.INVALID_INPUT

    def test_to_dict(self):
        rs = RecoveryStep(
            id="step-dict",
            order=3,
            action="verify",
            target="db",
            timeout_minutes=15,
            rollback_on_failure=False,
            dependencies=["s1", "s2"],
        )
        d = rs.to_dict()
        assert d["id"] == "step-dict"
        assert d["order"] == 3
        assert d["timeout_minutes"] == 15
        assert d["rollback_on_failure"] is False
        assert d["dependencies"] == ["s1", "s2"]

    def test_from_dict(self):
        d = {
            "id": "from-dict",
            "order": 1,
            "action": "restore",
            "target": "db-host",
            "timeout_minutes": 45,
            "rollback_on_failure": True,
            "dependencies": ["prev-step"],
        }
        rs = RecoveryStep.from_dict(d)
        assert rs.id == "from-dict"
        assert rs.action == "restore"
        assert rs.timeout_minutes == 45

    def test_from_dict_defaults(self):
        d = {"id": "minimal", "order": 0, "action": "a", "target": "t"}
        rs = RecoveryStep.from_dict(d)
        assert rs.timeout_minutes == 30
        assert rs.rollback_on_failure is True
        assert rs.dependencies == []

    def test_roundtrip(self):
        original = RecoveryStep(
            id="rt-step",
            order=5,
            action="final_check",
            target="all-services",
            timeout_minutes=10,
            rollback_on_failure=False,
            dependencies=["dep1", "dep2"],
        )
        restored = RecoveryStep.from_dict(original.to_dict())
        assert restored.id == original.id
        assert restored.order == original.order
        assert restored.action == original.action
        assert restored.target == original.target
        assert restored.timeout_minutes == original.timeout_minutes
        assert restored.rollback_on_failure == original.rollback_on_failure
        assert restored.dependencies == original.dependencies


# ===========================================================================
# Test BackupPolicy
# ===========================================================================


class TestBackupPolicy:
    """Tests cho BackupPolicy."""

    def test_valid_backup_policy(self):
        bp = BackupPolicy(
            id="policy-001",
            name="Daily Full Backup",
            backup_type=BackupType.FULL,
            target="postgresql://db:5432/app",
            storage_backend=StorageBackend.S3,
        )
        assert bp.id == "policy-001"
        assert bp.name == "Daily Full Backup"
        assert bp.backup_type == BackupType.FULL
        assert bp.retention_days == 30
        assert bp.compression_enabled is True
        assert bp.encryption_enabled is False

    def test_full_backup_policy(self):
        bp = BackupPolicy(
            id="full-policy",
            name="Encrypted Backup",
            backup_type=BackupType.INCREMENTAL,
            target="/data/volume",
            storage_backend=StorageBackend.GCS,
            schedule_type=ScheduleType.FIXED_INTERVAL,
            retention_days=90,
            encryption_enabled=True,
            max_backup_size_mb=10240,
            parallel_workers=4,
            metadata={"region": "us-east-1"},
        )
        assert bp.retention_days == 90
        assert bp.encryption_enabled is True
        assert bp.metadata["region"] == "us-east-1"

    def test_empty_id_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            BackupPolicy(id="", name="test")
        assert exc_info.value.code == ErrorCode.INVALID_ID

    def test_whitespace_id_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            BackupPolicy(id="  ", name="test")
        assert exc_info.value.code == ErrorCode.INVALID_ID

    def test_empty_name_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            BackupPolicy(id="p1", name="")
        assert exc_info.value.code == ErrorCode.INVALID_INPUT

    def test_zero_retention_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            BackupPolicy(id="p1", name="test", retention_days=0)
        assert exc_info.value.code == ErrorCode.INVALID_INPUT

    def test_zero_workers_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            BackupPolicy(id="p1", name="test", parallel_workers=0)
        assert exc_info.value.code == ErrorCode.INVALID_INPUT

    def test_to_dict(self):
        bp = BackupPolicy(
            id="dict-policy",
            name="Test Policy",
            backup_type=BackupType.DIFFERENTIAL,
            target="db-target",
            storage_backend=StorageBackend.AZURE_BLOB,
            schedule_type=ScheduleType.EVENT_TRIGGERED,
            retention_days=60,
            encryption_enabled=True,
            metadata={"key": "value"},
        )
        d = bp.to_dict()
        assert d["id"] == "dict-policy"
        assert d["backup_type"] == "differential"
        assert d["storage_backend"] == "azure_blob"
        assert d["schedule_type"] == "event_triggered"
        assert d["encryption_enabled"] is True
        assert d["metadata"]["key"] == "value"

    def test_from_dict(self):
        d = {
            "id": "from-dict-pol",
            "name": "From Dict",
            "backup_type": "incremental",
            "target": "target",
            "storage_backend": "gcs",
            "schedule_type": "fixed_interval",
            "retention_days": 45,
            "encryption_enabled": True,
        }
        bp = BackupPolicy.from_dict(d)
        assert bp.id == "from-dict-pol"
        assert bp.backup_type == BackupType.INCREMENTAL
        assert bp.storage_backend == StorageBackend.GCS
        assert bp.retention_days == 45

    def test_from_dict_defaults(self):
        d = {"id": "minimal"}
        bp = BackupPolicy.from_dict(d)
        assert bp.name == "minimal"
        assert bp.backup_type == BackupType.FULL
        assert bp.storage_backend == StorageBackend.LOCAL
        assert bp.retention_days == 30

    def test_roundtrip(self):
        original = BackupPolicy(
            id="rt-policy",
            name="Roundtrip Policy",
            backup_type=BackupType.POINT_IN_TIME,
            target="pitr-target",
            storage_backend=StorageBackend.K8S_VOLUME,
            schedule_type=ScheduleType.CRON,
            schedule_cron="0 3 * * 0",
            retention_days=2555,
            compression_enabled=True,
            encryption_enabled=True,
            max_backup_size_mb=0,
            parallel_workers=8,
            metadata={"compliance": "HIPAA"},
        )
        restored = BackupPolicy.from_dict(original.to_dict())
        assert restored.id == original.id
        assert restored.name == original.name
        assert restored.backup_type == original.backup_type
        assert restored.storage_backend == original.storage_backend
        assert restored.retention_days == original.retention_days
        assert restored.metadata == original.metadata


# ===========================================================================
# Test RestorePoint
# ===========================================================================


class TestRestorePoint:
    """Tests cho RestorePoint."""

    def test_valid_restore_point(self):
        rp = RestorePoint(
            id="rp-001",
            backup_policy_id="policy-001",
            timestamp="2026-05-25T02:00:00Z",
            size_bytes=1073741824,
        )
        assert rp.id == "rp-001"
        assert rp.backup_policy_id == "policy-001"
        assert rp.status == "completed"
        assert rp.metadata == {}

    def test_full_restore_point(self):
        rp = RestorePoint(
            id="full-rp",
            backup_policy_id="pol-1",
            timestamp="2026-05-25T14:00:00Z",
            size_bytes=5368709120,
            checksum="sha256:abc123",
            status="completed",
            storage_path="s3://bucket/backup.tar.gz",
            metadata={"tables": 50},
        )
        assert rp.checksum == "sha256:abc123"
        assert rp.metadata["tables"] == 50

    def test_empty_id_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            RestorePoint(id="", backup_policy_id="p1")
        assert exc_info.value.code == ErrorCode.INVALID_ID

    def test_empty_policy_id_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            RestorePoint(id="rp1", backup_policy_id="")
        assert exc_info.value.code == ErrorCode.INVALID_INPUT

    def test_whitespace_policy_id_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            RestorePoint(id="rp1", backup_policy_id="  ")
        assert exc_info.value.code == ErrorCode.INVALID_INPUT

    def test_to_dict(self):
        rp = RestorePoint(
            id="dict-rp",
            backup_policy_id="pol-d",
            timestamp="2026-05-25T00:00:00Z",
            size_bytes=1000,
            checksum="sha256:test",
            status="in_progress",
            storage_path="/local/backup",
            metadata={"key": "val"},
        )
        d = rp.to_dict()
        assert d["id"] == "dict-rp"
        assert d["status"] == "in_progress"
        assert d["metadata"]["key"] == "val"

    def test_from_dict(self):
        d = {
            "id": "from-rp",
            "backup_policy_id": "fp1",
            "timestamp": "2026-01-01T00:00:00Z",
            "size_bytes": 500000,
            "checksum": "sha256:chk",
            "status": "failed",
            "storage_path": "s3://b/f",
        }
        rp = RestorePoint.from_dict(d)
        assert rp.id == "from-rp"
        assert rp.status == "failed"
        assert rp.size_bytes == 500000

    def test_from_dict_defaults(self):
        d = {"id": "min", "backup_policy_id": "bp1"}
        rp = RestorePoint.from_dict(d)
        assert rp.timestamp == ""
        assert rp.size_bytes == 0
        assert rp.status == "completed"

    def test_roundtrip(self):
        original = RestorePoint(
            id="rt-rp",
            backup_policy_id="rt-pol",
            timestamp="2026-05-25T12:00:00Z",
            size_bytes=2000000000,
            checksum="sha256:roundtrip",
            status="completed",
            storage_path="s3://rt/path",
            metadata={"test": True},
        )
        restored = RestorePoint.from_dict(original.to_dict())
        assert restored.id == original.id
        assert restored.backup_policy_id == original.backup_policy_id
        assert restored.timestamp == original.timestamp
        assert restored.checksum == original.checksum
        assert restored.metadata == original.metadata


# ===========================================================================
# Test RecoveryPlan
# ===========================================================================


class TestRecoveryPlan:
    """Tests cho RecoveryPlan."""

    def test_valid_recovery_plan(self):
        rp = RecoveryPlan(
            id="plan-001",
            name="Database Recovery",
            rto_minutes=30,
            rpo_minutes=15,
        )
        assert rp.id == "plan-001"
        assert rp.priority == "high"
        assert rp.steps == []
        assert rp.auto_trigger is False

    def test_full_recovery_plan(self):
        steps = [
            RecoveryStep(id="s1", order=1, action="restore", target="db"),
            RecoveryStep(id="s2", order=2, action="verify", target="db", dependencies=["s1"]),
        ]
        rp = RecoveryPlan(
            id="full-plan",
            name="Full DR Plan",
            rto_minutes=15,
            rpo_minutes=5,
            priority="critical",
            steps=steps,
            auto_trigger=True,
            notification_channels=["slack:#ops", "pagerduty"],
        )
        assert len(rp.steps) == 2
        assert rp.auto_trigger is True
        assert "slack:#ops" in rp.notification_channels

    def test_empty_id_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            RecoveryPlan(id="", name="test")
        assert exc_info.value.code == ErrorCode.INVALID_ID

    def test_empty_name_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            RecoveryPlan(id="p1", name="")
        assert exc_info.value.code == ErrorCode.INVALID_INPUT

    def test_zero_rto_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            RecoveryPlan(id="p1", name="test", rto_minutes=0)
        assert exc_info.value.code == ErrorCode.INVALID_INPUT

    def test_zero_rpo_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            RecoveryPlan(id="p1", name="test", rpo_minutes=0)
        assert exc_info.value.code == ErrorCode.INVALID_INPUT

    def test_invalid_priority_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            RecoveryPlan(id="p1", name="test", priority="urgent")
        assert exc_info.value.code == ErrorCode.INVALID_INPUT

    def test_valid_priority_low(self):
        rp = RecoveryPlan(id="p1", name="test", priority="low")
        assert rp.priority == "low"

    def test_valid_priority_critical(self):
        rp = RecoveryPlan(id="p1", name="test", priority="critical")
        assert rp.priority == "critical"

    def test_to_dict(self):
        steps = [RecoveryStep(id="s1", order=1, action="a", target="t")]
        rp = RecoveryPlan(
            id="dict-plan",
            name="Dict Plan",
            rto_minutes=60,
            priority="medium",
            steps=steps,
            notification_channels=["email:test@example.com"],
        )
        d = rp.to_dict()
        assert d["id"] == "dict-plan"
        assert len(d["steps"]) == 1
        assert d["steps"][0]["id"] == "s1"
        assert "email:test@example.com" in d["notification_channels"]

    def test_from_dict(self):
        d = {
            "id": "from-plan",
            "name": "From Dict Plan",
            "rto_minutes": 45,
            "rpo_minutes": 10,
            "priority": "critical",
            "steps": [
                {"id": "s1", "order": 1, "action": "restore", "target": "db"}
            ],
            "auto_trigger": True,
            "notification_channels": ["slack:#ops"],
        }
        rp = RecoveryPlan.from_dict(d)
        assert rp.id == "from-plan"
        assert len(rp.steps) == 1
        assert rp.steps[0].id == "s1"
        assert rp.auto_trigger is True

    def test_from_dict_defaults(self):
        d = {"id": "min", "name": "Min"}
        rp = RecoveryPlan.from_dict(d)
        assert rp.rto_minutes == 60
        assert rp.priority == "high"
        assert rp.steps == []

    def test_roundtrip(self):
        steps = [
            RecoveryStep(id="r1", order=1, action="restore", target="db"),
            RecoveryStep(id="r2", order=2, action="verify", target="db", dependencies=["r1"]),
        ]
        original = RecoveryPlan(
            id="rt-plan",
            name="RT Plan",
            rto_minutes=20,
            rpo_minutes=5,
            priority="critical",
            steps=steps,
            auto_trigger=True,
            notification_channels=["c1", "c2"],
        )
        restored = RecoveryPlan.from_dict(original.to_dict())
        assert restored.id == original.id
        assert restored.rto_minutes == original.rto_minutes
        assert len(restored.steps) == len(original.steps)
        assert restored.steps[0].id == original.steps[0].id
        assert restored.notification_channels == original.notification_channels


# ===========================================================================
# Test BackupMonitor
# ===========================================================================


class TestBackupMonitor:
    """Tests cho BackupMonitor."""

    def test_valid_backup_monitor(self):
        bm = BackupMonitor(
            id="monitor-001",
            policy_ids=["p1", "p2"],
        )
        assert bm.id == "monitor-001"
        assert bm.alert_on_failure is True
        assert bm.alert_on_lag_minutes == 60

    def test_full_backup_monitor(self):
        bm = BackupMonitor(
            id="full-monitor",
            policy_ids=["p1"],
            alert_on_failure=True,
            alert_on_lag_minutes=15,
            slack_webhook="https://hooks.slack.com/services/T/B/X",
            email_recipients=["a@example.com", "b@example.com"],
        )
        assert bm.alert_on_lag_minutes == 15
        assert len(bm.email_recipients) == 2

    def test_empty_id_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            BackupMonitor(id="")
        assert exc_info.value.code == ErrorCode.INVALID_ID

    def test_whitespace_id_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            BackupMonitor(id="  ")
        assert exc_info.value.code == ErrorCode.INVALID_ID

    def test_zero_lag_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            BackupMonitor(id="m1", alert_on_lag_minutes=0)
        assert exc_info.value.code == ErrorCode.INVALID_INPUT

    def test_to_dict(self):
        bm = BackupMonitor(
            id="dict-mon",
            policy_ids=["p1", "p2", "p3"],
            alert_on_failure=True,
            alert_on_lag_minutes=30,
            slack_webhook="https://hook.com/x",
            email_recipients=["admin@test.com"],
        )
        d = bm.to_dict()
        assert d["id"] == "dict-mon"
        assert len(d["policy_ids"]) == 3
        assert d["alert_on_lag_minutes"] == 30

    def test_from_dict(self):
        d = {
            "id": "from-mon",
            "policy_ids": ["a", "b"],
            "alert_on_failure": False,
            "alert_on_lag_minutes": 120,
            "slack_webhook": "https://s.com",
            "email_recipients": ["e@test.com"],
        }
        bm = BackupMonitor.from_dict(d)
        assert bm.id == "from-mon"
        assert bm.alert_on_failure is False
        assert bm.alert_on_lag_minutes == 120

    def test_from_dict_defaults(self):
        d = {"id": "min-mon"}
        bm = BackupMonitor.from_dict(d)
        assert bm.policy_ids == []
        assert bm.alert_on_failure is True
        assert bm.slack_webhook == ""

    def test_roundtrip(self):
        original = BackupMonitor(
            id="rt-mon",
            policy_ids=["x", "y"],
            alert_on_failure=True,
            alert_on_lag_minutes=45,
            slack_webhook="https://rt.com",
            email_recipients=["a@rt.com", "b@rt.com"],
        )
        restored = BackupMonitor.from_dict(original.to_dict())
        assert restored.id == original.id
        assert restored.policy_ids == original.policy_ids
        assert restored.alert_on_failure == original.alert_on_failure
        assert restored.slack_webhook == original.slack_webhook
        assert restored.email_recipients == original.email_recipients
