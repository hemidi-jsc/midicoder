# coding: utf-8
"""
Unit tests cho template discovery của CP24.

Kiểm tra:
- Templates tồn tại trong stack directories
- Không vi phạm Template Rule V1 (không có midicoder imports)
- Không vi phạm Template Rule V2 (không có __post_init__)

Author: Midicoder Team
Version: 1.0.0
"""

from pathlib import Path

import pytest
import jinja2

# Expected templates per stack
EXPECTED_TEMPLATES: dict[str, list[str]] = {
    "fastapi": [
        "pyproject_quality.toml.jinja2",
        "bandit.yaml.jinja2",
        "safety_policy.json.jinja2",
        "quality_gate.py.jinja2",
        "flake8.ini.jinja2",
        "isort.cfg.jinja2",
    ],
    "nestjs": [
        "eslintrc.json.jinja2",
        "prettierrc.jinja2",
        "quality_gate.ts.jinja2",
        "npmrc.jinja2",
        "tsconfig_strict.json.jinja2",
    ],
    "angular": [
        "eslintrc.json.jinja2",
        "prettierrc.jinja2",
        "quality_gate.ts.jinja2",
        "lockfile_lint.config.js.jinja2",
        "editorconfig.jinja2",
    ],
    "react": [
        "eslintrc.json.jinja2",
        "prettierrc.jinja2",
        "quality_gate.ts.jinja2",
        "lockfile_lint.config.js.jinja2",
        "editorconfig.jinja2",
    ],
}


def _get_stacks_dir() -> Path:
    """Lấy đường dẫn đến stacks directory."""
    return Path(__file__).parents[4] / "stacks"


class TestTemplateDiscovery:
    """Test cho template discovery."""

    @pytest.mark.parametrize("stack", list(EXPECTED_TEMPLATES.keys()))
    def test_templates_exist(self, stack: str) -> None:
        """Kiểm tra templates tồn tại trong stack directory."""
        stacks_dir = _get_stacks_dir()
        template_dir = stacks_dir / stack / "core" / "cp24_quality_security"

        assert template_dir.exists(), f"Template directory không tồn tại: {template_dir}"
        assert template_dir.is_dir(), f"Path không phải directory: {template_dir}"

        existing = {f.name for f in template_dir.iterdir() if f.is_file()}
        expected = set(EXPECTED_TEMPLATES[stack])

        missing = expected - existing
        assert not missing, f"Thiếu templates ở {stack}: {missing}"

    @pytest.mark.parametrize("stack", list(EXPECTED_TEMPLATES.keys()))
    def test_template_count(self, stack: str) -> None:
        """Kiểm tra số lượng templates đúng."""
        stacks_dir = _get_stacks_dir()
        template_dir = stacks_dir / stack / "core" / "cp24_quality_security"
        templates = [f for f in template_dir.iterdir() if f.is_file()]
        assert len(templates) == len(EXPECTED_TEMPLATES[stack])


class TestTemplateRuleV1:
    """Test cho Template Rule V1: Không có midicoder imports."""

    @pytest.mark.parametrize("stack", list(EXPECTED_TEMPLATES.keys()))
    def test_no_midicoder_imports(self, stack: str) -> None:
        """Kiểm tra không có 'from midicoder' hay '@midicoder' trong templates."""
        stacks_dir = _get_stacks_dir()
        template_dir = stacks_dir / stack / "core" / "cp24_quality_security"

        for template_file in template_dir.iterdir():
            if not template_file.is_file():
                continue
            content = template_file.read_text(encoding="utf-8")
            assert "from midicoder" not in content, (
                f"Template Rule V1 violation: 'from midicoder' found in {template_file.name}"
            )
            assert "import midicoder" not in content, (
                f"Template Rule V1 violation: 'import midicoder' found in {template_file.name}"
            )
            assert "@midicoder" not in content, (
                f"Template Rule V1 violation: '@midicoder' found in {template_file.name}"
            )


class TestTemplateRuleV2:
    """Test cho Template Rule V2: Không có __post_init__."""

    @pytest.mark.parametrize("stack", list(EXPECTED_TEMPLATES.keys()))
    def test_no_post_init(self, stack: str) -> None:
        """Kiểm tra không có '__post_init__' trong templates."""
        stacks_dir = _get_stacks_dir()
        template_dir = stacks_dir / stack / "core" / "cp24_quality_security"

        for template_file in template_dir.iterdir():
            if not template_file.is_file():
                continue
            content = template_file.read_text(encoding="utf-8")
            assert "__post_init__" not in content, (
                f"Template Rule V2 violation: '__post_init__' found in {template_file.name}"
            )


class TestTemplateContent:
    """Test cho nội dung templates."""

    def test_fastapi_quality_gate_has_main_block(self) -> None:
        """Kiểm tra quality gate script có main block."""
        stacks_dir = _get_stacks_dir()
        tpl = stacks_dir / "fastapi" / "core" / "cp24_quality_security" / "quality_gate.py.jinja2"
        if tpl.exists():
            content = tpl.read_text(encoding="utf-8")
            assert "if __name__" in content or "main" in content

    def test_nestjs_eslintrc_has_security_plugin(self) -> None:
        """Kiểm tra NestJS eslintrc có security plugin."""
        stacks_dir = _get_stacks_dir()
        tpl = stacks_dir / "nestjs" / "core" / "cp24_quality_security" / "eslintrc.json.jinja2"
        if tpl.exists():
            content = tpl.read_text(encoding="utf-8")
            assert "security" in content

    def test_react_eslintrc_has_react_plugin(self) -> None:
        """Kiểm tra React eslintrc có react plugin."""
        stacks_dir = _get_stacks_dir()
        tpl = stacks_dir / "react" / "core" / "cp24_quality_security" / "eslintrc.json.jinja2"
        if tpl.exists():
            content = tpl.read_text(encoding="utf-8")
            assert "react" in content.lower()

# ===========================================================================
# Dữ liệu và helper cho Rule V1/V2 (P2-17) — kiểm tra output đã render
# ===========================================================================

def _render_template(stack: str, template_name: str) -> str:
    """Render template với context cơ bản; fallback đọc raw nếu render lỗi."""
    template_path = _get_stacks_dir() / stack / "core" / "cp24_quality_security"
    try:
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(template_path)),
            undefined=jinja2.ChainableUndefined,
        )
        ctx = {
            "profile": {"exclude": []},
            "rule_overrides": {},
            "collection": None,
            "lint_config": {},
            "security_rules": [],
        }
        template = env.get_template(template_name)
        return template.render(**ctx)
    except Exception:
        # Fallback: đọc nội dung raw nếu Jinja2 parse lỗi (undefined vars / JS syntax)
        raw_file = template_path / template_name
        if raw_file.exists():
            return raw_file.read_text(encoding="utf-8")
        raise


# ===========================================================================
# Test Rule V1 & V2 (P2-17) — kiểm tra output đã render
# ===========================================================================

class TestRuleV1NoMidicoderImportRendered:
    """Rule V1: Output render của template KHÔNG chứa 'from midicoder'."""

    def test_fastapi_no_midicoder_import(self) -> None:
        """FastAPI templates không chứa 'from midicoder' trong output."""
        for template in EXPECTED_TEMPLATES["fastapi"]:
            result = _render_template("fastapi", template)
            assert "from midicoder" not in result, f"Rule V1 vi phạm: {template}"
            assert "import midicoder" not in result, f"Rule V1 vi phạm: {template}"

    def test_nestjs_no_midicoder_import(self) -> None:
        """NestJS templates không chứa 'from midicoder' trong output."""
        for template in EXPECTED_TEMPLATES["nestjs"]:
            result = _render_template("nestjs", template)
            assert "from midicoder" not in result, f"Rule V1 vi phạm: {template}"
            assert "import midicoder" not in result, f"Rule V1 vi phạm: {template}"

    def test_angular_no_midicoder_import(self) -> None:
        """Angular templates không chứa 'from midicoder' trong output."""
        for template in EXPECTED_TEMPLATES["angular"]:
            result = _render_template("angular", template)
            assert "from midicoder" not in result, f"Rule V1 vi phạm: {template}"
            assert "import midicoder" not in result, f"Rule V1 vi phạm: {template}"

    def test_react_no_midicoder_import(self) -> None:
        """React templates không chứa 'from midicoder' trong output."""
        for template in EXPECTED_TEMPLATES["react"]:
            result = _render_template("react", template)
            assert "from midicoder" not in result, f"Rule V1 vi phạm: {template}"
            assert "import midicoder" not in result, f"Rule V1 vi phạm: {template}"


class TestRuleV2NoPostInitRendered:
    """Rule V2: Output render của template KHÔNG chứa '__post_init__'."""

    def test_fastapi_no_post_init(self) -> None:
        """FastAPI templates không chứa __post_init__ trong output."""
        for template in EXPECTED_TEMPLATES["fastapi"]:
            result = _render_template("fastapi", template)
            assert "__post_init__" not in result, f"Rule V2 vi phạm: {template}"

    def test_nestjs_no_post_init(self) -> None:
        """NestJS templates không chứa __post_init__ trong output."""
        for template in EXPECTED_TEMPLATES["nestjs"]:
            result = _render_template("nestjs", template)
            assert "__post_init__" not in result, f"Rule V2 vi phạm: {template}"

    def test_angular_no_post_init(self) -> None:
        """Angular templates không chứa __post_init__ trong output."""
        for template in EXPECTED_TEMPLATES["angular"]:
            result = _render_template("angular", template)
            assert "__post_init__" not in result, f"Rule V2 vi phạm: {template}"

    def test_react_no_post_init(self) -> None:
        """React templates không chứa __post_init__ trong output."""
        for template in EXPECTED_TEMPLATES["react"]:
            result = _render_template("react", template)
            assert "__post_init__" not in result, f"Rule V2 vi phạm: {template}"
