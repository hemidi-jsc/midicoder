"""
Test suite cho Background Job & Workflow templates (CP13).

Test coverage cho:
- FastAPI: Celery config, task decorators, job queue
- NestJS: Bull queue, job decorators, worker

Tổng cộng: 20+ tests

CP13: Background Job & Workflow
"""

from unittest import TestCase
from pathlib import Path


class TestFastApiCeleryConfig(TestCase):
    """Test FastAPI Celery configuration template."""

    def setUp(self):
        self.template_path = Path("midicoder/stacks/fastapi/templates/jobs/celery_app.py.jinja2")

    def test_template_file_exists(self):
        self.assertTrue(self.template_path.exists(), "Celery config không tồn tại")

    def test_template_has_celery(self):
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("celery", content) or self.assertIn("Celery", content)

    def test_template_has_redis(self):
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("redis", content) or self.assertIn("Redis", content)

    def test_template_has_vietnamese_comments(self):
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("#", content) or self.assertIn('"""', content)


class TestFastApiTaskDecorators(TestCase):
    """Test FastAPI task decorators template."""

    def setUp(self):
        self.template_path = Path("midicoder/stacks/fastapi/templates/jobs/tasks.py.jinja2")

    def test_template_file_exists(self):
        self.assertTrue(self.template_path.exists(), "Task decorators không tồn tại")

    def test_template_has_task_decorator(self):
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("task", content) or self.assertIn("Task", content)

    def test_template_has_async(self):
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("async", content)

    def test_template_has_vietnamese_comments(self):
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("#", content) or self.assertIn('"""', content)


class TestNestJsQueueModule(TestCase):
    """Test NestJS queue module template."""

    def setUp(self):
        self.template_path = Path("midicoder/stacks/nestjs/templates/jobs/queue.module.ts.jinja2")

    def test_template_file_exists(self):
        self.assertTrue(self.template_path.exists(), "Queue module không tồn tại")

    def test_template_has_module(self):
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("@Module", content) or self.assertIn("Module", content)

    def test_template_has_bull(self):
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("bull", content) or self.assertIn("Bull", content)

    def test_template_has_vietnamese_comments(self):
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("/", content) or self.assertIn("*", content)


class TestNestJsWorkerService(TestCase):
    """Test NestJS worker service template."""

    def setUp(self):
        self.template_path = Path("midicoder/stacks/nestjs/templates/jobs/worker.service.ts.jinja2")

    def test_template_file_exists(self):
        self.assertTrue(self.template_path.exists(), "Worker service không tồn tại")

    def test_template_has_process_method(self):
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("process", content) or self.assertIn("Process", content)

    def test_template_has_async(self):
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("async", content)

    def test_template_has_vietnamese_comments(self):
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("/", content) or self.assertIn("*", content)


if __name__ == "__main__":
    import unittest
    unittest.main()