# coding: utf-8
"""
Mô-đun recipes cho CP65 — Data Backup & Recovery.

Cung cấp các recipe để build BackupIR cho các use case phổ biến:
- database_backup_recipe: Daily full + hourly incremental database backup
- disaster_recovery_recipe: Full DR plan với RTO 15min, RPO 5min
- compliance_backup_recipe: SOX/HIPAA compliant với encryption, 7-year retention

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from midicoder.packs.cp65_backup_recovery.models import (
    BackupMonitor,
    BackupPolicy,
    BackupType,
    RecoveryPlan,
    RecoveryStep,
    RestorePoint,
    ScheduleType,
    StorageBackend,
)
from midicoder.packs.cp65_backup_recovery.parser import (
    BackupIR,
    parse_to_ir,
)


@dataclass
class RecipeOutput:
    """Kết quả từ recipe builder.

    Attributes:
        name: Tên recipe
        description: Mô tả recipe
        ir: BackupIR đã build
        raw_data: Raw DSL dict
    """
    name: str
    description: str
    ir: BackupIR
    raw_data: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Chuyển RecipeOutput sang dict."""
        return {
            "name": self.name,
            "description": self.description,
            "ir": self.ir.to_dict(),
            "raw_data": self.raw_data,
        }


def database_backup_recipe() -> RecipeOutput:
    """Recipe: Daily full + hourly incremental database backup với 30-day retention.

    - 2 backup policies: daily full, hourly incremental
    - 2 restore points: recent full và incremental
    - 1 recovery plan: database recovery (RTO 30min, RPO 15min)
    - 1 backup monitor: cảnh báo Slack + email

    Returns:
        RecipeOutput chứa BackupIR
    """
    data = {
        "backup_policies": [
            {
                "id": "db-full-daily",
                "name": "Database Full Backup (Daily)",
                "backup_type": "full",
                "target": "postgresql://db-primary:5432/production",
                "storage_backend": "s3",
                "schedule_type": "cron",
                "schedule_cron": "0 2 * * *",
                "retention_days": 30,
                "compression_enabled": True,
                "encryption_enabled": True,
                "max_backup_size_mb": 0,
                "parallel_workers": 4,
                "metadata": {"engine": "postgresql", "wal_mode": "true"},
            },
            {
                "id": "db-incremental-hourly",
                "name": "Database Incremental Backup (Hourly)",
                "backup_type": "incremental",
                "target": "postgresql://db-primary:5432/production",
                "storage_backend": "s3",
                "schedule_type": "cron",
                "schedule_cron": "0 * * * *",
                "retention_days": 7,
                "compression_enabled": True,
                "encryption_enabled": True,
                "max_backup_size_mb": 5120,
                "parallel_workers": 2,
                "metadata": {"engine": "postgresql", "wal_mode": "true"},
            },
        ],
        "restore_points": [
            {
                "id": "rp-full-001",
                "backup_policy_id": "db-full-daily",
                "timestamp": "2026-05-25T02:00:00Z",
                "size_bytes": 1073741824,
                "checksum": "sha256:abc123def456",
                "status": "completed",
                "storage_path": "s3://backup-bucket/db/full/2026-05-25.tar.gz",
                "metadata": {"records": 5000000, "tables": 42},
            },
            {
                "id": "rp-incr-001",
                "backup_policy_id": "db-incremental-hourly",
                "timestamp": "2026-05-25T14:00:00Z",
                "size_bytes": 104857600,
                "checksum": "sha256:789xyz012",
                "status": "completed",
                "storage_path": "s3://backup-bucket/db/incr/2026-05-25-14.tar.gz",
                "metadata": {"wal_start": "0/1000000", "wal_end": "0/100ABCD"},
            },
        ],
        "recovery_plans": [
            {
                "id": "db-recovery-plan",
                "name": "Database Disaster Recovery",
                "rto_minutes": 30,
                "rpo_minutes": 15,
                "priority": "critical",
                "steps": [
                    {
                        "id": "step-restore-full",
                        "order": 1,
                        "action": "restore_full_backup",
                        "target": "postgresql://db-replica:5432/production",
                        "timeout_minutes": 20,
                        "rollback_on_failure": False,
                        "dependencies": [],
                    },
                    {
                        "id": "step-apply-incremental",
                        "order": 2,
                        "action": "apply_incremental",
                        "target": "postgresql://db-replica:5432/production",
                        "timeout_minutes": 10,
                        "rollback_on_failure": True,
                        "dependencies": ["step-restore-full"],
                    },
                    {
                        "id": "step-verify-integrity",
                        "order": 3,
                        "action": "verify_integrity",
                        "target": "postgresql://db-replica:5432/production",
                        "timeout_minutes": 5,
                        "rollback_on_failure": False,
                        "dependencies": ["step-apply-incremental"],
                    },
                    {
                        "id": "step-promote-replica",
                        "order": 4,
                        "action": "promote_replica",
                        "target": "db-replica",
                        "timeout_minutes": 5,
                        "rollback_on_failure": True,
                        "dependencies": ["step-verify-integrity"],
                    },
                ],
                "auto_trigger": False,
                "notification_channels": ["slack:#incidents", "pagerduty"],
            }
        ],
        "monitors": [
            {
                "id": "db-backup-monitor",
                "policy_ids": ["db-full-daily", "db-incremental-hourly"],
                "alert_on_failure": True,
                "alert_on_lag_minutes": 15,
                "slack_webhook": "https://hooks.slack.com/services/T00/B00/XXX",
                "email_recipients": ["dba@example.com", "oncall@example.com"],
            }
        ],
        "default_retention_days": 30,
        "enable_encryption": True,
    }

    ir = parse_to_ir(data)

    return RecipeOutput(
        name="database_backup_recipe",
        description="Daily full + hourly incremental database backup với 30-day retention",
        ir=ir,
        raw_data=data,
    )


def disaster_recovery_recipe() -> RecipeOutput:
    """Recipe: Full DR plan với RTO 15min, RPO 5min, multi-step recovery.

    - 2 backup policies: full hourly, continuous WAL archiving
    - 2 restore points: recent snapshots
    - 1 recovery plan: DR với 6 bước, RTO 15min, RPO 5min
    - 1 backup monitor: cảnh báo tức thì

    Returns:
        RecipeOutput chứa BackupIR
    """
    data = {
        "backup_policies": [
            {
                "id": "dr-full-hourly",
                "name": "DR Full Backup (Hourly)",
                "backup_type": "full",
                "target": "postgresql://db-primary:5432/production",
                "storage_backend": "s3",
                "schedule_type": "cron",
                "schedule_cron": "0 * * * *",
                "retention_days": 14,
                "compression_enabled": True,
                "encryption_enabled": True,
                "max_backup_size_mb": 0,
                "parallel_workers": 8,
                "metadata": {"dr_enabled": True, "cross_region": True, "region": "us-east-1"},
            },
            {
                "id": "dr-wal-continuous",
                "name": "DR Continuous WAL Archiving",
                "backup_type": "point_in_time",
                "target": "postgresql://db-primary:5432/production",
                "storage_backend": "s3",
                "schedule_type": "event_triggered",
                "schedule_cron": "",
                "retention_days": 14,
                "compression_enabled": True,
                "encryption_enabled": True,
                "max_backup_size_mb": 0,
                "parallel_workers": 1,
                "metadata": {"wal_archive": True, "archive_timeout": 30},
            },
        ],
        "restore_points": [
            {
                "id": "dr-rp-full",
                "backup_policy_id": "dr-full-hourly",
                "timestamp": "2026-05-25T14:00:00Z",
                "size_bytes": 2147483648,
                "checksum": "sha256:drfull001",
                "status": "completed",
                "storage_path": "s3://dr-backup-bucket/full/2026-05-25-14.tar.gz",
                "metadata": {"region": "us-east-1", "replicated": True},
            },
            {
                "id": "dr-rp-wal",
                "backup_policy_id": "dr-wal-continuous",
                "timestamp": "2026-05-25T14:04:55Z",
                "size_bytes": 5242880,
                "checksum": "sha256:drwal001",
                "status": "completed",
                "storage_path": "s3://dr-backup-bucket/wal/0/5A000000",
                "metadata": {"wal_segment": "00000001000000000000005A"},
            },
        ],
        "recovery_plans": [
            {
                "id": "full-dr-plan",
                "name": "Full Disaster Recovery Plan",
                "rto_minutes": 15,
                "rpo_minutes": 5,
                "priority": "critical",
                "steps": [
                    {
                        "id": "dr-step-1-notify",
                        "order": 1,
                        "action": "notify_incident",
                        "target": "ops-team",
                        "timeout_minutes": 1,
                        "rollback_on_failure": False,
                        "dependencies": [],
                    },
                    {
                        "id": "dr-step-2-provision",
                        "order": 2,
                        "action": "provision_dr_instance",
                        "target": "us-west-2:db-dr-instance",
                        "timeout_minutes": 5,
                        "rollback_on_failure": True,
                        "dependencies": ["dr-step-1-notify"],
                    },
                    {
                        "id": "dr-step-3-restore-full",
                        "order": 3,
                        "action": "restore_full_backup",
                        "target": "us-west-2:db-dr-instance:5432",
                        "timeout_minutes": 10,
                        "rollback_on_failure": False,
                        "dependencies": ["dr-step-2-provision"],
                    },
                    {
                        "id": "dr-step-4-replay-wal",
                        "order": 4,
                        "action": "replay_wal_to_timestamp",
                        "target": "us-west-2:db-dr-instance:5432",
                        "timeout_minutes": 5,
                        "rollback_on_failure": True,
                        "dependencies": ["dr-step-3-restore-full"],
                    },
                    {
                        "id": "dr-step-5-verify",
                        "order": 5,
                        "action": "verify_data_integrity",
                        "target": "us-west-2:db-dr-instance:5432",
                        "timeout_minutes": 3,
                        "rollback_on_failure": False,
                        "dependencies": ["dr-step-4-replay-wal"],
                    },
                    {
                        "id": "dr-step-6-dns-switch",
                        "order": 6,
                        "action": "switch_dns_failover",
                        "target": "db.example.com",
                        "timeout_minutes": 2,
                        "rollback_on_failure": True,
                        "dependencies": ["dr-step-5-verify"],
                    },
                ],
                "auto_trigger": True,
                "notification_channels": [
                    "slack:#incidents",
                    "slack:#engineering",
                    "pagerduty",
                    "email:cto@example.com",
                ],
            }
        ],
        "monitors": [
            {
                "id": "dr-backup-monitor",
                "policy_ids": ["dr-full-hourly", "dr-wal-continuous"],
                "alert_on_failure": True,
                "alert_on_lag_minutes": 5,
                "slack_webhook": "https://hooks.slack.com/services/T00/B00/DR-ALERT",
                "email_recipients": ["dr-oncall@example.com", "cto@example.com"],
            }
        ],
        "default_retention_days": 14,
        "enable_encryption": True,
    }

    ir = parse_to_ir(data)

    return RecipeOutput(
        name="disaster_recovery_recipe",
        description="Full DR plan với RTO 15min, RPO 5min, multi-step recovery",
        ir=ir,
        raw_data=data,
    )


def compliance_backup_recipe() -> RecipeOutput:
    """Recipe: SOX/HIPAA compliant backup với encryption, 7-year retention, monitoring.

    - 3 backup policies: daily full, hourly incremental, weekly point-in-time
    - 1 restore point: compliance snapshot
    - 1 recovery plan: compliance recovery (audit trail)
    - 1 backup monitor: strict monitoring với multiple channels

    Returns:
        RecipeOutput chứa BackupIR
    """
    data = {
        "backup_policies": [
            {
                "id": "compliance-full-daily",
                "name": "Compliance Full Backup (Daily)",
                "backup_type": "full",
                "target": "postgresql://compliance-db:5432/audit",
                "storage_backend": "s3",
                "schedule_type": "cron",
                "schedule_cron": "0 1 * * *",
                "retention_days": 2555,
                "compression_enabled": True,
                "encryption_enabled": True,
                "max_backup_size_mb": 0,
                "parallel_workers": 4,
                "metadata": {
                    "compliance_framework": ["SOX", "HIPAA"],
                    "immutability": True,
                    "worm_enabled": True,
                    "audit_required": True,
                },
            },
            {
                "id": "compliance-incr-hourly",
                "name": "Compliance Incremental Backup (Hourly)",
                "backup_type": "incremental",
                "target": "postgresql://compliance-db:5432/audit",
                "storage_backend": "s3",
                "schedule_type": "cron",
                "schedule_cron": "0 * * * *",
                "retention_days": 2555,
                "compression_enabled": True,
                "encryption_enabled": True,
                "max_backup_size_mb": 0,
                "parallel_workers": 2,
                "metadata": {
                    "compliance_framework": ["SOX", "HIPAA"],
                    "immutability": True,
                },
            },
            {
                "id": "compliance-pit-weekly",
                "name": "Compliance Point-in-Time Backup (Weekly)",
                "backup_type": "point_in_time",
                "target": "postgresql://compliance-db:5432/audit",
                "storage_backend": "s3",
                "schedule_type": "cron",
                "schedule_cron": "0 0 * * 0",
                "retention_days": 2555,
                "compression_enabled": True,
                "encryption_enabled": True,
                "max_backup_size_mb": 0,
                "parallel_workers": 1,
                "metadata": {
                    "compliance_framework": ["SOX", "HIPAA"],
                    "immutability": True,
                    "legal_hold": True,
                },
            },
        ],
        "restore_points": [
            {
                "id": "compliance-rp-001",
                "backup_policy_id": "compliance-full-daily",
                "timestamp": "2026-05-25T01:00:00Z",
                "size_bytes": 5368709120,
                "checksum": "sha256:compliance001",
                "status": "completed",
                "storage_path": "s3://compliance-backup-bucket/immutable/full/2026-05-25.tar.gz",
                "metadata": {
                    "compliance_framework": ["SOX", "HIPAA"],
                    "legal_hold": True,
                    "tamper_proof": True,
                    "audit_hash": "sha256:audit001",
                },
            }
        ],
        "recovery_plans": [
            {
                "id": "compliance-recovery-plan",
                "name": "Compliance Data Recovery",
                "rto_minutes": 120,
                "rpo_minutes": 60,
                "priority": "high",
                "steps": [
                    {
                        "id": "comp-step-1-audit-log",
                        "order": 1,
                        "action": "log_recovery_audit",
                        "target": "audit-system",
                        "timeout_minutes": 1,
                        "rollback_on_failure": False,
                        "dependencies": [],
                    },
                    {
                        "id": "comp-step-2-restore",
                        "order": 2,
                        "action": "restore_compliance_backup",
                        "target": "postgresql://compliance-restore:5432/audit",
                        "timeout_minutes": 60,
                        "rollback_on_failure": False,
                        "dependencies": ["comp-step-1-audit-log"],
                    },
                    {
                        "id": "comp-step-3-verify",
                        "order": 3,
                        "action": "verify_checksum_and_integrity",
                        "target": "postgresql://compliance-restore:5432/audit",
                        "timeout_minutes": 30,
                        "rollback_on_failure": False,
                        "dependencies": ["comp-step-2-restore"],
                    },
                    {
                        "id": "comp-step-4-report",
                        "order": 4,
                        "action": "generate_recovery_report",
                        "target": "compliance-reports",
                        "timeout_minutes": 10,
                        "rollback_on_failure": False,
                        "dependencies": ["comp-step-3-verify"],
                    },
                ],
                "auto_trigger": False,
                "notification_channels": [
                    "slack:#compliance",
                    "email:compliance-officer@example.com",
                    "email:legal@example.com",
                ],
            }
        ],
        "monitors": [
            {
                "id": "compliance-backup-monitor",
                "policy_ids": [
                    "compliance-full-daily",
                    "compliance-incr-hourly",
                    "compliance-pit-weekly",
                ],
                "alert_on_failure": True,
                "alert_on_lag_minutes": 30,
                "slack_webhook": "https://hooks.slack.com/services/T00/B00/COMPLIANCE",
                "email_recipients": [
                    "compliance-officer@example.com",
                    "ciso@example.com",
                    "legal@example.com",
                ],
            }
        ],
        "default_retention_days": 2555,
        "enable_encryption": True,
    }

    ir = parse_to_ir(data)

    return RecipeOutput(
        name="compliance_backup_recipe",
        description="SOX/HIPAA compliant backup với encryption, 7-year retention, monitoring",
        ir=ir,
        raw_data=data,
    )


__all__ = [
    "RecipeOutput",
    "database_backup_recipe",
    "disaster_recovery_recipe",
    "compliance_backup_recipe",
]
