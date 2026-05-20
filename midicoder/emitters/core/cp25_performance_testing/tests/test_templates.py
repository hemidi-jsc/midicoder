# coding: utf-8
"""
Unit tests cho template discovery của CP25.

Author: Midicoder Team
Version: 1.0.0
"""

from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent


class TestTemplateDiscovery:
    """Test template discovery cho CP25."""

    def test_fastapi_templates_exist(self) -> None:
        """Kiểm tra templates FastAPI tồn tại."""
        templates_dir = PROJECT_ROOT / "stacks" / "fastapi" / "core" / "cp25_performance_testing"
        assert templates_dir.exists()

        expected = [
            "locustfile.py.jinja2",
            "locust.conf.jinja2",
            "perf_test_entity.py.jinja2",
            "perf_baseline.py.jinja2",
        ]
        for t in expected:
            assert (templates_dir / t).exists(), f"Template {t} không tồn tại"

    def test_nestjs_templates_exist(self) -> None:
        """Kiểm tra templates NestJS tồn tại."""
        templates_dir = PROJECT_ROOT / "stacks" / "nestjs" / "core" / "cp25_performance_testing"
        assert templates_dir.exists()

        expected = [
            "artillery.yml.jinja2",
            "perf_baseline.spec.ts.jinja2",
        ]
        for t in expected:
            assert (templates_dir / t).exists(), f"Template {t} không tồn tại"

    def test_angular_templates_exist(self) -> None:
        """Kiểm tra templates Angular tồn tại."""
        templates_dir = PROJECT_ROOT / "stacks" / "angular" / "core" / "cp25_performance_testing"
        assert templates_dir.exists()

        expected = [
            "lighthouserc.js.jinja2",
            "web_vitals.spec.ts.jinja2",
            "lighthouse_ci.js.jinja2",
        ]
        for t in expected:
            assert (templates_dir / t).exists(), f"Template {t} không tồn tại"

    def test_react_templates_exist(self) -> None:
        """Kiểm tra templates React tồn tại."""
        templates_dir = PROJECT_ROOT / "stacks" / "react" / "core" / "cp25_performance_testing"
        assert templates_dir.exists()

        expected = [
            "lighthouserc.js.jinja2",
            "web_vitals.test.tsx.jinja2",
            "lighthouse_ci.js.jinja2",
        ]
        for t in expected:
            assert (templates_dir / t).exists(), f"Template {t} không tồn tại"

    def test_pack_yml_exists(self) -> None:
        """Kiểm tra pack.yml tồn tại."""
        pack_dir = PROJECT_ROOT / "emitters" / "core" / "cp25_performance_testing"
        assert (pack_dir / "pack.yml").exists()

    def test_pack_yml_content(self) -> None:
        """Kiểm tra nội dung pack.yml."""
        import yaml

        pack_dir = PROJECT_ROOT / "emitters" / "core" / "cp25_performance_testing"
        with open(pack_dir / "pack.yml") as f:
            data = yaml.safe_load(f)

        assert data["pack"]["id"] == "CP25"
        assert data["pack"]["internal_id"] == "cp25_performance_testing"
        assert "perf_test_run" in data["pack"]["capabilities_provided"]
        assert "load_scenario" in data["pack"]["capabilities_provided"]
        assert "baseline_compare" in data["pack"]["capabilities_provided"]
