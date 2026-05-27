"""Test CP13 scheduler models — JobDefinition, JobInstance, SchedulePolicy, JobPriority."""

import pytest
from unittest import TestCase
from datetime import datetime
from unittest.mock import patch


class TestJobPriority(TestCase):
    """Kiểm tra enum JobPriority có đủ 4 giá trị."""

    def test_low_priority_exists(self):
        """JobPriority.LOW tồn tại."""
        from midicoder.packs.cp13_workflow_runtime.scheduler import JobPriority
        self.assertEqual(JobPriority.LOW.value, "low")

    def test_normal_priority_exists(self):
        """JobPriority.NORMAL tồn tại."""
        from midicoder.packs.cp13_workflow_runtime.scheduler import JobPriority
        self.assertEqual(JobPriority.NORMAL.value, "normal")

    def test_high_priority_exists(self):
        """JobPriority.HIGH tồn tại."""
        from midicoder.packs.cp13_workflow_runtime.scheduler import JobPriority
        self.assertEqual(JobPriority.HIGH.value, "high")

    def test_critical_priority_exists(self):
        """JobPriority.CRITICAL tồn tại."""
        from midicoder.packs.cp13_workflow_runtime.scheduler import JobPriority
        self.assertEqual(JobPriority.CRITICAL.value, "critical")


class TestSchedulePolicy(TestCase):
    """Kiểm tra SchedulePolicy với cron_expr và interval_seconds."""

    def test_cron_policy_creation(self):
        """Tạo SchedulePolicy với cron expression."""
        from midicoder.packs.cp13_workflow_runtime.scheduler import SchedulePolicy
        policy = SchedulePolicy(cron_expr="0 */5 * * * *")
        self.assertEqual(policy.cron_expr, "0 */5 * * * *")
        self.assertIsNone(policy.interval_seconds)
        self.assertEqual(policy.max_concurrent, 1)
        self.assertEqual(policy.timezone, "UTC")

    def test_interval_policy_creation(self):
        """Tạo SchedulePolicy với interval_seconds."""
        from midicoder.packs.cp13_workflow_runtime.scheduler import SchedulePolicy
        policy = SchedulePolicy(interval_seconds=300)
        self.assertEqual(policy.interval_seconds, 300)
        self.assertIsNone(policy.cron_expr)

    def test_policy_without_schedule_raises(self):
        """SchedulePolicy không có cron_expr cũng không có interval_seconds thì raise."""
        from midicoder.packs.cp13_workflow_runtime.scheduler import SchedulePolicy
        from midicoder.errors import ErrorCode
        with self.assertRaises(ValueError) as ctx:
            SchedulePolicy(cron_expr=None, interval_seconds=None)
        self.assertIn("MDC-CP13-007", str(ctx.exception))

    def test_policy_custom_max_concurrent(self):
        """SchedulePolicy có max_concurrent tùy chỉnh."""
        from midicoder.packs.cp13_workflow_runtime.scheduler import SchedulePolicy
        policy = SchedulePolicy(cron_expr="0 0 * * *", max_concurrent=5)
        self.assertEqual(policy.max_concurrent, 5)

    def test_policy_custom_timezone(self):
        """SchedulePolicy có timezone tùy chỉnh."""
        from midicoder.packs.cp13_workflow_runtime.scheduler import SchedulePolicy
        policy = SchedulePolicy(cron_expr="0 0 * * *", timezone="Asia/Ho_Chi_Minh")
        self.assertEqual(policy.timezone, "Asia/Ho_Chi_Minh")

    def test_policy_to_dict(self):
        """SchedulePolicy.to_dict() trả về dict đầy đủ."""
        from midicoder.packs.cp13_workflow_runtime.scheduler import SchedulePolicy
        policy = SchedulePolicy(cron_expr="*/10 * * * *", max_concurrent=3)
        d = policy.to_dict()
        self.assertEqual(d["cron_expr"], "*/10 * * * *")
        self.assertEqual(d["max_concurrent"], 3)

    def test_policy_from_dict(self):
        """SchedulePolicy.from_dict() tái tạo policy từ dict."""
        from midicoder.packs.cp13_workflow_runtime.scheduler import SchedulePolicy
        d = {"cron_expr": "0 0 * * *", "interval_seconds": None, "max_concurrent": 2, "timezone": "UTC"}
        policy = SchedulePolicy.from_dict(d)
        self.assertEqual(policy.cron_expr, "0 0 * * *")
        self.assertEqual(policy.max_concurrent, 2)


class TestJobDefinition(TestCase):
    """Kiểm tra JobDefinition model."""

    def test_job_definition_creation(self):
        """Tạo JobDefinition hợp lệ."""
        from midicoder.packs.cp13_workflow_runtime.scheduler import JobDefinition, SchedulePolicy, JobPriority
        job = JobDefinition(
            job_id="cleanup_sessions",
            name="Xóa session cũ",
            task_type="session_cleanup",
            schedule=SchedulePolicy(cron_expr="0 2 * * *"),
        )
        self.assertEqual(job.job_id, "cleanup_sessions")
        self.assertEqual(job.priority, JobPriority.NORMAL)
        self.assertEqual(job.retry_count, 3)
        self.assertEqual(job.timeout_seconds, 3600)
        self.assertTrue(job.enabled)

    def test_job_definition_empty_id_raises(self):
        """JobDefinition với job_id rỗng thì raise."""
        from midicoder.packs.cp13_workflow_runtime.scheduler import JobDefinition, SchedulePolicy
        with self.assertRaises(ValueError) as ctx:
            JobDefinition(
                job_id="",
                name="Test",
                task_type="test",
                schedule=SchedulePolicy(cron_expr="0 * * * *"),
            )
        self.assertIn("MDC-CP13-002", str(ctx.exception))

    def test_job_definition_empty_task_type_raises(self):
        """JobDefinition với task_type rỗng thì raise."""
        from midicoder.packs.cp13_workflow_runtime.scheduler import JobDefinition, SchedulePolicy
        with self.assertRaises(ValueError) as ctx:
            JobDefinition(
                job_id="test_job",
                name="Test",
                task_type="",
                schedule=SchedulePolicy(cron_expr="0 * * * *"),
            )
        self.assertIn("MDC-CP13-001", str(ctx.exception))

    def test_job_definition_with_all_fields(self):
        """JobDefinition với đầy đủ tùy chọn."""
        from midicoder.packs.cp13_workflow_runtime.scheduler import JobDefinition, SchedulePolicy, JobPriority
        job = JobDefinition(
            job_id="send_report",
            name="Gửi báo cáo hàng ngày",
            task_type="email_report",
            schedule=SchedulePolicy(cron_expr="0 8 * * *", timezone="Asia/Ho_Chi_Minh"),
            priority=JobPriority.HIGH,
            retry_count=5,
            timeout_seconds=1800,
            enabled=True,
            metadata={"department": "finance"},
        )
        self.assertEqual(job.priority, JobPriority.HIGH)
        self.assertEqual(job.retry_count, 5)
        self.assertEqual(job.metadata["department"], "finance")

    def test_job_definition_to_dict(self):
        """JobDefinition.to_dict() trả về dict đầy đủ."""
        from midicoder.packs.cp13_workflow_runtime.scheduler import JobDefinition, SchedulePolicy
        job = JobDefinition(
            job_id="test_job",
            name="Test Job",
            task_type="test_task",
            schedule=SchedulePolicy(interval_seconds=60),
        )
        d = job.to_dict()
        self.assertEqual(d["job_id"], "test_job")
        self.assertEqual(d["name"], "Test Job")

    def test_job_definition_from_dict(self):
        """JobDefinition.from_dict() tái tạo từ dict."""
        from midicoder.packs.cp13_workflow_runtime.scheduler import JobDefinition
        d = {
            "job_id": "import_data",
            "name": "Import dữ liệu",
            "task_type": "data_import",
            "schedule": {"cron_expr": "0 3 * * *", "interval_seconds": None, "max_concurrent": 1, "timezone": "UTC"},
            "priority": "normal",
            "retry_count": 2,
            "timeout_seconds": 7200,
            "enabled": True,
            "metadata": {},
        }
        job = JobDefinition.from_dict(d)
        self.assertEqual(job.job_id, "import_data")
        self.assertEqual(job.schedule.cron_expr, "0 3 * * *")


class TestJobInstance(TestCase):
    """Kiểm tra JobInstance model."""

    def test_job_instance_creation(self):
        """Tạo JobInstance với status pending."""
        from midicoder.packs.cp13_workflow_runtime.scheduler import JobInstance
        inst = JobInstance(instance_id="inst-001", job_id="cleanup_sessions")
        self.assertEqual(inst.instance_id, "inst-001")
        self.assertEqual(inst.status, "pending")
        self.assertIsNone(inst.started_at)
        self.assertIsNone(inst.completed_at)
        self.assertEqual(inst.retries, 0)

    def test_job_instance_empty_id_raises(self):
        """JobInstance với instance_id rỗng thì raise."""
        from midicoder.packs.cp13_workflow_runtime.scheduler import JobInstance
        with self.assertRaises(ValueError) as ctx:
            JobInstance(instance_id="", job_id="test")
        self.assertIn("MDC-CP13-002", str(ctx.exception))

    def test_job_instance_empty_job_id_raises(self):
        """JobInstance với job_id rỗng thì raise."""
        from midicoder.packs.cp13_workflow_runtime.scheduler import JobInstance
        with self.assertRaises(ValueError) as ctx:
            JobInstance(instance_id="inst-001", job_id="")
        self.assertIn("MDC-CP13-002", str(ctx.exception))

    def test_mark_running(self):
        """JobInstance.mark_running() set status và started_at."""
        from midicoder.packs.cp13_workflow_runtime.scheduler import JobInstance
        inst = JobInstance(instance_id="inst-001", job_id="test")
        inst.mark_running()
        self.assertEqual(inst.status, "running")
        self.assertIsNotNone(inst.started_at)

    def test_mark_completed(self):
        """JobInstance.mark_completed() set status, completed_at, result."""
        from midicoder.packs.cp13_workflow_runtime.scheduler import JobInstance
        inst = JobInstance(instance_id="inst-001", job_id="test")
        inst.mark_completed(result={"rows_deleted": 150})
        self.assertEqual(inst.status, "completed")
        self.assertIsNotNone(inst.completed_at)
        self.assertEqual(inst.result["rows_deleted"], 150)

    def test_mark_failed(self):
        """JobInstance.mark_failed() set status và error."""
        from midicoder.packs.cp13_workflow_runtime.scheduler import JobInstance
        inst = JobInstance(instance_id="inst-001", job_id="test")
        inst.mark_failed(error="Connection timeout")
        self.assertEqual(inst.status, "failed")
        self.assertEqual(inst.error, "Connection timeout")

    def test_mark_failed_increments_retries(self):
        """JobInstance.mark_failed() tăng retry count."""
        from midicoder.packs.cp13_workflow_runtime.scheduler import JobInstance
        inst = JobInstance(instance_id="inst-001", job_id="test")
        inst.mark_failed(error="timeout")
        inst.mark_failed(error="timeout again")
        self.assertEqual(inst.retries, 2)

    def test_job_instance_to_dict(self):
        """JobInstance.to_dict() trả về dict đầy đủ."""
        from midicoder.packs.cp13_workflow_runtime.scheduler import JobInstance
        inst = JobInstance(instance_id="inst-001", job_id="test")
        inst.mark_completed(result={"ok": True})
        d = inst.to_dict()
        self.assertEqual(d["instance_id"], "inst-001")
        self.assertEqual(d["status"], "completed")
        self.assertEqual(d["result"]["ok"], True)

    def test_job_instance_cancelled_status(self):
        """JobInstance có thể được tạo với status cancelled."""
        from midicoder.packs.cp13_workflow_runtime.scheduler import JobInstance
        inst = JobInstance(instance_id="inst-002", job_id="test")
        inst.status = "cancelled"
        self.assertEqual(inst.status, "cancelled")
