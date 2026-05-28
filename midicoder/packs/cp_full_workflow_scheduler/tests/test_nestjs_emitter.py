"""
Unit tests cho SchedulerNestJSEmitter.
"""

import pytest
from pathlib import Path
import tempfile

from midicoder.packs.cp_full_workflow_scheduler.nestjs import (
    SchedulerNestJSEmitter,
    GeneratedFile,
)


class TestSchedulerNestJSEmitter:
    """Test SchedulerNestJSEmitter."""

    def setup_method(self):
        """Setup test fixture với temporary template dir."""
        self.temp_dir = tempfile.mkdtemp()
        self.stack_dir = Path(self.temp_dir)
        self.template_dir = self.stack_dir / "cp31_scheduler"
        self.template_dir.mkdir()

        # Tạo template minimal
        (self.template_dir / "cron-parser.service.ts.jinja2").write_text(
            "// Cron Parser - {{ schedule_count }} schedules\n"
            "{% for s in schedules %}export const SCHEDULE_{{ s.schedule_id | upper }}\n{% endfor %}"
        )
        (self.template_dir / "calendar-engine.service.ts.jinja2").write_text(
            "// Calendar Engine - {{ 'has_calendar' if has_calendar else 'no_calendar' }}"
        )
        (self.template_dir / "scheduler.service.ts.jinja2").write_text(
            "// Scheduler Service"
        )
        (self.template_dir / "scheduler.controller.ts.jinja2").write_text(
            "// Scheduler Controller"
        )

        self.emitter = SchedulerNestJSEmitter(self.stack_dir)

    def test_emit_with_schedules(self):
        """Emit với schedules."""
        schedules = [
            {"schedule_id": "daily", "cron_expression": "0 0 * * *"},
        ]
        files = self.emitter.emit(schedules, self.temp_dir)
        assert len(files) == 4
        assert all(isinstance(f, GeneratedFile) for f in files)

    def test_emit_cron_parser_content(self):
        """Kiểm tra content của cron parser."""
        schedules = [
            {"schedule_id": "backup", "cron_expression": "0 2 * * *"},
        ]
        files = self.emitter.emit(schedules, self.temp_dir)
        cron_file = next(f for f in files if "cron-parser" in f.path)
        assert "SCHEDULE_BACKUP" in cron_file.content

    def test_emit_with_calendar_sets(self):
        """Emit với calendar sets."""
        calendar_sets = [
            {"calendar_set_id": "us", "name": "US Holidays", "exceptions": []}
        ]
        files = self.emitter.emit([], self.temp_dir, calendar_sets)
        cal_file = next(f for f in files if "calendar-engine" in f.path)
        assert "has_calendar" in cal_file.content

    def test_file_paths_correct(self):
        """Kiểm tra file paths."""
        files = self.emitter.emit([], self.temp_dir)
        paths = [f.path for f in files]
        assert "src/scheduler/cron-parser.service.ts" in paths
        assert "src/scheduler/calendar-engine.service.ts" in paths
        assert "src/scheduler/scheduler.service.ts" in paths
        assert "src/scheduler/scheduler.controller.ts" in paths
