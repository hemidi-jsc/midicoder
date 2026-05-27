"""
Tests cho CP65 Backup Recipes.

Unit tests cho:
- database_backup_recipe
- disaster_recovery_recipe
- compliance_backup_recipe

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from midicoder.packs.cp65_backup_recovery.recipes import (
    RecipeOutput,
    database_backup_recipe,
    disaster_recovery_recipe,
    compliance_backup_recipe,
)
from midicoder.packs.cp65_backup_recovery.parser import BackupIR
from midicoder.packs.cp65_backup_recovery.models import (
    BackupType,
    StorageBackend,
    ScheduleType,
)


# ===========================================================================
# Test RecipeOutput
# ===========================================================================


class TestRecipeOutput:
    """Tests cho RecipeOutput dataclass."""

    def test_create(self):
        ir = BackupIR()
        ro = RecipeOutput(
            name="test",
            description="Test recipe",
            ir=ir,
            raw_data={},
        )
        assert ro.name == "test"
        assert ro.description == "Test recipe"
        assert isinstance(ro.ir, BackupIR)
        assert ro.raw_data == {}

    def test_to_dict(self):
        ir = BackupIR()
        ro = RecipeOutput(
            name="test",
            description="Test",
            ir=ir,
            raw_data={"key": "val"},
        )
        d = ro.to_dict()
        assert d["name"] == "test"
        assert d["description"] == "Test"
        assert isinstance(d["ir"], dict)
        assert d["raw_data"]["key"] == "val"


# ===========================================================================
# Test database_backup_recipe
# ===========================================================================


class TestDatabaseBackupRecipe:
    """Tests cho database_backup_recipe."""

    def test_returns_recipe_output(self):
        ro = database_backup_recipe()
        assert isinstance(ro, RecipeOutput)
        assert ro.name == "database_backup_recipe"
        assert "30-day retention" in ro.description

    def test_has_valid_ir(self):
        ro = database_backup_recipe()
        ir = ro.ir
        assert isinstance(ir, BackupIR)
        assert len(ir.backup_policies) == 2

    def test_full_backup_policy(self):
        ro = database_backup_recipe()
        full_policy = ro.ir.backup_policies[0]
        assert full_policy.id == "db-full-daily"
        assert full_policy.backup_type == BackupType.FULL
        assert full_policy.storage_backend == StorageBackend.S3
        assert full_policy.retention_days == 30
        assert full_policy.encryption_enabled is True

    def test_incremental_backup_policy(self):
        ro = database_backup_recipe()
        incr_policy = ro.ir.backup_policies[1]
        assert incr_policy.id == "db-incremental-hourly"
        assert incr_policy.backup_type == BackupType.INCREMENTAL
        assert incr_policy.retention_days == 7
        assert incr_policy.max_backup_size_mb == 5120

    def test_restore_points(self):
        ro = database_backup_recipe()
        assert len(ro.ir.restore_points) == 2
        assert ro.ir.restore_points[0].backup_policy_id == "db-full-daily"
        assert ro.ir.restore_points[1].backup_policy_id == "db-incremental-hourly"

    def test_recovery_plan(self):
        ro = database_backup_recipe()
        assert len(ro.ir.recovery_plans) == 1
        plan = ro.ir.recovery_plans[0]
        assert plan.id == "db-recovery-plan"
        assert plan.rto_minutes == 30
        assert plan.rpo_minutes == 15
        assert plan.priority == "critical"
        assert len(plan.steps) == 4

    def test_recovery_steps_dependencies(self):
        ro = database_backup_recipe()
        plan = ro.ir.recovery_plans[0]
        # Step 1 should have no dependencies
        assert plan.steps[0].dependencies == []
        # Step 2 should depend on step 1
        assert "step-restore-full" in plan.steps[1].dependencies

    def test_monitor(self):
        ro = database_backup_recipe()
        assert len(ro.ir.monitors) == 1
        mon = ro.ir.monitors[0]
        assert mon.id == "db-backup-monitor"
        assert len(mon.policy_ids) == 2
        assert mon.alert_on_failure is True
        assert mon.alert_on_lag_minutes == 15

    def test_encryption_enabled(self):
        ro = database_backup_recipe()
        assert ro.ir.enable_encryption is True

    def test_raw_data_populated(self):
        ro = database_backup_recipe()
        assert "backup_policies" in ro.raw_data
        assert "recovery_plans" in ro.raw_data
        assert len(ro.raw_data["backup_policies"]) == 2


# ===========================================================================
# Test disaster_recovery_recipe
# ===========================================================================


class TestDisasterRecoveryRecipe:
    """Tests cho disaster_recovery_recipe."""

    def test_returns_recipe_output(self):
        ro = disaster_recovery_recipe()
        assert isinstance(ro, RecipeOutput)
        assert ro.name == "disaster_recovery_recipe"
        assert "RTO 15min" in ro.description

    def test_has_valid_ir(self):
        ro = disaster_recovery_recipe()
        ir = ro.ir
        assert isinstance(ir, BackupIR)
        assert len(ir.backup_policies) == 2

    def test_full_backup_policy(self):
        ro = disaster_recovery_recipe()
        policy = ro.ir.backup_policies[0]
        assert policy.id == "dr-full-hourly"
        assert policy.backup_type == BackupType.FULL
        assert policy.parallel_workers == 8

    def test_wal_backup_policy(self):
        ro = disaster_recovery_recipe()
        wal_policy = ro.ir.backup_policies[1]
        assert wal_policy.id == "dr-wal-continuous"
        assert wal_policy.backup_type == BackupType.POINT_IN_TIME
        assert wal_policy.schedule_type == ScheduleType.EVENT_TRIGGERED

    def test_dr_recovery_plan(self):
        ro = disaster_recovery_recipe()
        plan = ro.ir.recovery_plans[0]
        assert plan.id == "full-dr-plan"
        assert plan.rto_minutes == 15
        assert plan.rpo_minutes == 5
        assert plan.priority == "critical"
        assert plan.auto_trigger is True
        assert len(plan.steps) == 6

    def test_dr_steps_order(self):
        ro = disaster_recovery_recipe()
        plan = ro.ir.recovery_plans[0]
        orders = [s.order for s in plan.steps]
        assert orders == [1, 2, 3, 4, 5, 6]

    def test_dr_notification_channels(self):
        ro = disaster_recovery_recipe()
        plan = ro.ir.recovery_plans[0]
        assert len(plan.notification_channels) >= 3
        assert "slack:#incidents" in plan.notification_channels

    def test_dr_monitor_strict(self):
        ro = disaster_recovery_recipe()
        mon = ro.ir.monitors[0]
        assert mon.alert_on_lag_minutes == 5

    def test_encryption_enabled(self):
        ro = disaster_recovery_recipe()
        assert ro.ir.enable_encryption is True

    def test_raw_data_populated(self):
        ro = disaster_recovery_recipe()
        assert "backup_policies" in ro.raw_data
        assert "recovery_plans" in ro.raw_data
        assert len(ro.raw_data["backup_policies"]) == 2


# ===========================================================================
# Test compliance_backup_recipe
# ===========================================================================


class TestComplianceBackupRecipe:
    """Tests cho compliance_backup_recipe."""

    def test_returns_recipe_output(self):
        ro = compliance_backup_recipe()
        assert isinstance(ro, RecipeOutput)
        assert ro.name == "compliance_backup_recipe"
        assert "7-year retention" in ro.description

    def test_has_valid_ir(self):
        ro = compliance_backup_recipe()
        ir = ro.ir
        assert isinstance(ir, BackupIR)
        assert len(ir.backup_policies) == 3

    def test_daily_full_policy(self):
        ro = compliance_backup_recipe()
        policy = ro.ir.backup_policies[0]
        assert policy.id == "compliance-full-daily"
        assert policy.backup_type == BackupType.FULL
        assert policy.retention_days == 2555  # ~7 years
        assert policy.encryption_enabled is True

    def test_hourly_incremental_policy(self):
        ro = compliance_backup_recipe()
        policy = ro.ir.backup_policies[1]
        assert policy.id == "compliance-incr-hourly"
        assert policy.backup_type == BackupType.INCREMENTAL
        assert policy.retention_days == 2555

    def test_weekly_pit_policy(self):
        ro = compliance_backup_recipe()
        policy = ro.ir.backup_policies[2]
        assert policy.id == "compliance-pit-weekly"
        assert policy.backup_type == BackupType.POINT_IN_TIME
        assert policy.retention_days == 2555

    def test_compliance_metadata(self):
        ro = compliance_backup_recipe()
        policy = ro.ir.backup_policies[0]
        assert "SOX" in policy.metadata.get("compliance_framework", [])
        assert "HIPAA" in policy.metadata.get("compliance_framework", [])
        assert policy.metadata.get("immutability") is True

    def test_compliance_recovery_plan(self):
        ro = compliance_backup_recipe()
        plan = ro.ir.recovery_plans[0]
        assert plan.id == "compliance-recovery-plan"
        assert plan.priority == "high"
        assert len(plan.steps) == 4

    def test_audit_log_step(self):
        ro = compliance_backup_recipe()
        plan = ro.ir.recovery_plans[0]
        first_step = plan.steps[0]
        assert first_step.action == "log_recovery_audit"
        assert first_step.order == 1

    def test_compliance_monitor(self):
        ro = compliance_backup_recipe()
        mon = ro.ir.monitors[0]
        assert len(mon.policy_ids) == 3
        assert len(mon.email_recipients) >= 2

    def test_7_year_retention(self):
        ro = compliance_backup_recipe()
        assert ro.ir.default_retention_days == 2555

    def test_encryption_enabled(self):
        ro = compliance_backup_recipe()
        assert ro.ir.enable_encryption is True

    def test_raw_data_populated(self):
        ro = compliance_backup_recipe()
        assert "backup_policies" in ro.raw_data
        assert len(ro.raw_data["backup_policies"]) == 3


# ===========================================================================
# Cross-recipe integration
# ===========================================================================


class TestRecipeIntegration:
    """Integration tests cho recipe ecosystem."""

    def test_all_recipes_return_valid_ir(self):
        """Tất cả recipes phải trả về valid BackupIR."""
        for recipe_fn in [database_backup_recipe, disaster_recovery_recipe, compliance_backup_recipe]:
            ro = recipe_fn()
            assert isinstance(ro, RecipeOutput)
            assert isinstance(ro.ir, BackupIR)
            assert ro.ir.backup_policies

    def test_recipes_can_be_serialized(self):
        """Tất cả recipes phải có thể serialize và deserialize."""
        for recipe_fn in [database_backup_recipe, disaster_recovery_recipe, compliance_backup_recipe]:
            ro = recipe_fn()
            d = ro.ir.to_dict()
            restored = BackupIR.from_dict(d)
            assert len(restored.backup_policies) == len(ro.ir.backup_policies)
            assert len(restored.recovery_plans) == len(ro.ir.recovery_plans)

    def test_database_recipe_has_monitor(self):
        """Database recipe phải có monitor."""
        assert database_backup_recipe().ir.monitors

    def test_dr_recipe_auto_trigger(self):
        """DR recipe phải có auto_trigger."""
        plan = disaster_recovery_recipe().ir.recovery_plans[0]
        assert plan.auto_trigger is True

    def test_compliance_recipe_long_retention(self):
        """Compliance recipe phải có retention > 2500 ngày."""
        for policy in compliance_backup_recipe().ir.backup_policies:
            assert policy.retention_days >= 2500

    def test_all_recipes_have_encryption(self):
        """Tất cả recipes phải bật encryption."""
        for recipe_fn in [database_backup_recipe, disaster_recovery_recipe, compliance_backup_recipe]:
            assert recipe_fn().ir.enable_encryption is True
