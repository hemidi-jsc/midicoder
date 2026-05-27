"""
Tests cho CP65 Backup Parser.

Unit tests cho:
- BackupIR dataclass (to_dict, from_dict)
- parse_backup_policies
- parse_restore_points
- parse_recovery_plans
- parse_monitors
- parse_to_ir

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from midicoder.packs.cp65_backup_recovery.parser import (
    BackupIR,
    parse_backup_policies,
    parse_restore_points,
    parse_recovery_plans,
    parse_monitors,
    parse_to_ir,
)
from midicoder.packs.cp65_backup_recovery.models import (
    BackupMonitor,
    BackupPolicy,
    BackupType,
    RecoveryPlan,
    RecoveryStep,
    RestorePoint,
    StorageBackend,
)


# ===========================================================================
# Test BackupIR
# ===========================================================================


class TestBackupIR:
    """Tests cho BackupIR."""

    def test_default_values(self):
        ir = BackupIR()
        assert ir.backup_policies == []
        assert ir.restore_points == []
        assert ir.recovery_plans == []
        assert ir.monitors == []
        assert ir.default_retention_days == 30
        assert ir.enable_encryption is False

    def test_with_backup_policies(self):
        policy = BackupPolicy(id="p1", name="Policy 1")
        ir = BackupIR(backup_policies=[policy])
        assert len(ir.backup_policies) == 1
        assert ir.backup_policies[0].id == "p1"

    def test_with_restore_points(self):
        rp = RestorePoint(id="rp1", backup_policy_id="p1")
        ir = BackupIR(restore_points=[rp])
        assert len(ir.restore_points) == 1
        assert ir.restore_points[0].id == "rp1"

    def test_with_recovery_plans(self):
        plan = RecoveryPlan(id="plan1", name="DR Plan")
        ir = BackupIR(recovery_plans=[plan])
        assert len(ir.recovery_plans) == 1
        assert ir.recovery_plans[0].id == "plan1"

    def test_with_monitors(self):
        mon = BackupMonitor(id="mon1", policy_ids=["p1"])
        ir = BackupIR(monitors=[mon])
        assert len(ir.monitors) == 1
        assert ir.monitors[0].id == "mon1"

    def test_custom_settings(self):
        ir = BackupIR(default_retention_days=90, enable_encryption=True)
        assert ir.default_retention_days == 90
        assert ir.enable_encryption is True

    def test_to_dict_empty(self):
        ir = BackupIR()
        d = ir.to_dict()
        assert d["backup_policies"] == []
        assert d["restore_points"] == []
        assert d["recovery_plans"] == []
        assert d["monitors"] == []
        assert d["default_retention_days"] == 30
        assert d["enable_encryption"] is False

    def test_to_dict_full(self):
        policy = BackupPolicy(id="p1", name="P1")
        rp = RestorePoint(id="rp1", backup_policy_id="p1")
        plan = RecoveryPlan(id="plan1", name="Plan1")
        mon = BackupMonitor(id="mon1")
        ir = BackupIR(
            backup_policies=[policy],
            restore_points=[rp],
            recovery_plans=[plan],
            monitors=[mon],
            default_retention_days=60,
            enable_encryption=True,
        )
        d = ir.to_dict()
        assert len(d["backup_policies"]) == 1
        assert len(d["restore_points"]) == 1
        assert len(d["recovery_plans"]) == 1
        assert len(d["monitors"]) == 1
        assert d["default_retention_days"] == 60
        assert d["enable_encryption"] is True

    def test_from_dict_empty(self):
        ir = BackupIR.from_dict({})
        assert ir.backup_policies == []
        assert ir.restore_points == []
        assert ir.recovery_plans == []
        assert ir.monitors == []
        assert ir.default_retention_days == 30
        assert ir.enable_encryption is False

    def test_from_dict_full(self):
        d = {
            "backup_policies": [
                {
                    "id": "p1",
                    "name": "Full Backup",
                    "backup_type": "full",
                    "storage_backend": "s3",
                    "retention_days": 30,
                }
            ],
            "restore_points": [
                {
                    "id": "rp1",
                    "backup_policy_id": "p1",
                    "timestamp": "2026-05-25T02:00:00Z",
                    "size_bytes": 1073741824,
                }
            ],
            "recovery_plans": [
                {
                    "id": "plan1",
                    "name": "DR Plan",
                    "rto_minutes": 15,
                    "priority": "critical",
                    "steps": [
                        {
                            "id": "s1",
                            "order": 1,
                            "action": "restore",
                            "target": "db",
                        }
                    ],
                }
            ],
            "monitors": [
                {
                    "id": "mon1",
                    "policy_ids": ["p1"],
                    "alert_on_failure": True,
                }
            ],
            "default_retention_days": 45,
            "enable_encryption": True,
        }
        ir = BackupIR.from_dict(d)
        assert len(ir.backup_policies) == 1
        assert ir.backup_policies[0].id == "p1"
        assert len(ir.restore_points) == 1
        assert len(ir.recovery_plans) == 1
        assert len(ir.recovery_plans[0].steps) == 1
        assert len(ir.monitors) == 1
        assert ir.default_retention_days == 45
        assert ir.enable_encryption is True

    def test_roundtrip(self):
        steps = [RecoveryStep(id="s1", order=1, action="restore", target="db")]
        original = BackupIR(
            backup_policies=[
                BackupPolicy(
                    id="rt-pol",
                    name="RT Policy",
                    backup_type=BackupType.INCREMENTAL,
                    storage_backend=StorageBackend.GCS,
                    retention_days=90,
                )
            ],
            restore_points=[
                RestorePoint(
                    id="rt-rp",
                    backup_policy_id="rt-pol",
                    timestamp="2026-05-25T12:00:00Z",
                    size_bytes=500000000,
                )
            ],
            recovery_plans=[
                RecoveryPlan(
                    id="rt-plan",
                    name="RT Plan",
                    rto_minutes=30,
                    rpo_minutes=10,
                    steps=steps,
                )
            ],
            monitors=[
                BackupMonitor(id="rt-mon", policy_ids=["rt-pol"])
            ],
            default_retention_days=90,
            enable_encryption=True,
        )
        restored = BackupIR.from_dict(original.to_dict())
        assert len(restored.backup_policies) == len(original.backup_policies)
        assert restored.backup_policies[0].id == original.backup_policies[0].id
        assert restored.backup_policies[0].backup_type == original.backup_policies[0].backup_type
        assert len(restored.restore_points) == len(original.restore_points)
        assert len(restored.recovery_plans) == len(original.recovery_plans)
        assert restored.recovery_plans[0].steps[0].id == original.recovery_plans[0].steps[0].id
        assert len(restored.monitors) == len(original.monitors)
        assert restored.default_retention_days == original.default_retention_days
        assert restored.enable_encryption == original.enable_encryption


# ===========================================================================
# Test parse_backup_policies
# ===========================================================================


class TestParseBackupPolicies:
    """Tests cho parse_backup_policies()."""

    def test_parse_backup_policies_key(self):
        data = {
            "backup_policies": [
                {
                    "id": "p1",
                    "name": "Daily Full",
                    "backup_type": "full",
                    "storage_backend": "s3",
                }
            ]
        }
        policies = parse_backup_policies(data)
        assert len(policies) == 1
        assert policies[0].id == "p1"
        assert policies[0].backup_type == BackupType.FULL

    def test_parse_empty(self):
        data = {}
        policies = parse_backup_policies(data)
        assert policies == []

    def test_parse_multiple(self):
        data = {
            "backup_policies": [
                {"id": "a", "name": "A", "backup_type": "full"},
                {"id": "b", "name": "B", "backup_type": "incremental"},
                {"id": "c", "name": "C", "backup_type": "differential"},
            ]
        }
        policies = parse_backup_policies(data)
        assert len(policies) == 3
        assert all(isinstance(p, BackupPolicy) for p in policies)


# ===========================================================================
# Test parse_restore_points
# ===========================================================================


class TestParseRestorePoints:
    """Tests cho parse_restore_points()."""

    def test_parse_restore_points_key(self):
        data = {
            "restore_points": [
                {
                    "id": "rp1",
                    "backup_policy_id": "p1",
                    "timestamp": "2026-05-25T02:00:00Z",
                }
            ]
        }
        rps = parse_restore_points(data)
        assert len(rps) == 1
        assert rps[0].id == "rp1"
        assert rps[0].backup_policy_id == "p1"

    def test_parse_empty(self):
        data = {}
        rps = parse_restore_points(data)
        assert rps == []

    def test_parse_multiple(self):
        data = {
            "restore_points": [
                {"id": "r1", "backup_policy_id": "p1"},
                {"id": "r2", "backup_policy_id": "p1"},
            ]
        }
        rps = parse_restore_points(data)
        assert len(rps) == 2
        assert all(isinstance(r, RestorePoint) for r in rps)


# ===========================================================================
# Test parse_recovery_plans
# ===========================================================================


class TestParseRecoveryPlans:
    """Tests cho parse_recovery_plans()."""

    def test_parse_recovery_plans_key(self):
        data = {
            "recovery_plans": [
                {
                    "id": "plan1",
                    "name": "DR Plan",
                    "rto_minutes": 15,
                    "steps": [
                        {"id": "s1", "order": 1, "action": "restore", "target": "db"}
                    ],
                }
            ]
        }
        plans = parse_recovery_plans(data)
        assert len(plans) == 1
        assert plans[0].id == "plan1"
        assert len(plans[0].steps) == 1

    def test_parse_empty(self):
        data = {}
        plans = parse_recovery_plans(data)
        assert plans == []

    def test_parse_multiple(self):
        data = {
            "recovery_plans": [
                {"id": "p1", "name": "Plan A", "steps": []},
                {"id": "p2", "name": "Plan B", "steps": []},
            ]
        }
        plans = parse_recovery_plans(data)
        assert len(plans) == 2
        assert all(isinstance(p, RecoveryPlan) for p in plans)


# ===========================================================================
# Test parse_monitors
# ===========================================================================


class TestParseMonitors:
    """Tests cho parse_monitors()."""

    def test_parse_monitors_key(self):
        data = {
            "monitors": [
                {
                    "id": "mon1",
                    "policy_ids": ["p1", "p2"],
                    "alert_on_failure": True,
                }
            ]
        }
        mons = parse_monitors(data)
        assert len(mons) == 1
        assert mons[0].id == "mon1"
        assert len(mons[0].policy_ids) == 2

    def test_parse_empty(self):
        data = {}
        mons = parse_monitors(data)
        assert mons == []

    def test_parse_multiple(self):
        data = {
            "monitors": [
                {"id": "m1", "policy_ids": ["a"]},
                {"id": "m2", "policy_ids": ["b"]},
            ]
        }
        mons = parse_monitors(data)
        assert len(mons) == 2
        assert all(isinstance(m, BackupMonitor) for m in mons)


# ===========================================================================
# Test parse_to_ir
# ===========================================================================


class TestParseToIR:
    """Tests cho parse_to_ir()."""

    def test_parse_minimal(self):
        data = {}
        ir = parse_to_ir(data)
        assert isinstance(ir, BackupIR)
        assert ir.backup_policies == []
        assert ir.restore_points == []
        assert ir.recovery_plans == []
        assert ir.monitors == []
        assert ir.default_retention_days == 30
        assert ir.enable_encryption is False

    def test_parse_full(self):
        data = {
            "backup_policies": [
                {
                    "id": "p1",
                    "name": "Full Backup",
                    "backup_type": "full",
                    "storage_backend": "s3",
                    "retention_days": 30,
                }
            ],
            "restore_points": [
                {
                    "id": "rp1",
                    "backup_policy_id": "p1",
                    "timestamp": "2026-05-25T02:00:00Z",
                }
            ],
            "recovery_plans": [
                {
                    "id": "plan1",
                    "name": "DR Plan",
                    "rto_minutes": 15,
                    "priority": "critical",
                    "steps": [
                        {
                            "id": "s1",
                            "order": 1,
                            "action": "restore",
                            "target": "db",
                        }
                    ],
                }
            ],
            "monitors": [
                {
                    "id": "mon1",
                    "policy_ids": ["p1"],
                    "alert_on_failure": True,
                }
            ],
            "default_retention_days": 60,
            "enable_encryption": True,
        }
        ir = parse_to_ir(data)
        assert len(ir.backup_policies) == 1
        assert len(ir.restore_points) == 1
        assert len(ir.recovery_plans) == 1
        assert len(ir.monitors) == 1
        assert ir.default_retention_days == 60
        assert ir.enable_encryption is True

    def test_parse_only_policies(self):
        data = {
            "backup_policies": [
                {"id": "p1", "name": "A"},
                {"id": "p2", "name": "B"},
            ]
        }
        ir = parse_to_ir(data)
        assert len(ir.backup_policies) == 2
        assert ir.restore_points == []
        assert ir.recovery_plans == []
        assert ir.monitors == []

    def test_parse_with_steps(self):
        data = {
            "recovery_plans": [
                {
                    "id": "plan1",
                    "name": "Multi-step Plan",
                    "steps": [
                        {"id": "s1", "order": 1, "action": "restore", "target": "db"},
                        {"id": "s2", "order": 2, "action": "verify", "target": "db", "dependencies": ["s1"]},
                    ],
                }
            ]
        }
        ir = parse_to_ir(data)
        plan = ir.recovery_plans[0]
        assert len(plan.steps) == 2
        assert plan.steps[1].dependencies == ["s1"]
