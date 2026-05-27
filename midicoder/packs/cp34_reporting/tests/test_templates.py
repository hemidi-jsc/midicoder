"""Test template existence and content for CP34."""
from __future__ import annotations

import pytest
import jinja2
from pathlib import Path

_STACKS_DIR = Path(__file__).resolve().parents[4] / "stacks"
_PACK_FOLDER = "cp34_reporting"

# Discover templates dynamically
_STACK_TEMPLATES: dict[str, list[str]] = {}
for stack in ["fastapi", "nestjs", "react", "angular"]:
    stack_dir = _STACKS_DIR / stack / "core" / _PACK_FOLDER
    if stack_dir.exists():
        _STACK_TEMPLATES[stack] = sorted(f.name for f in stack_dir.glob("*.jinja2"))


def _render_template(stack: str, template_name: str, context: dict | None = None) -> str:
    """Render a Jinja2 template with a permissive environment."""
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(_STACKS_DIR / stack / "core" / _PACK_FOLDER),
        undefined=jinja2.ChainableUndefined,
    )
    try:
        tmpl = env.get_template(template_name)
        return tmpl.render(context or {})
    except Exception:
        p = _STACKS_DIR / stack / "core" / _PACK_FOLDER / template_name
        return p.read_text(encoding="utf-8") if p.exists() else ""


class TestTemplateDiscovery:
    @pytest.mark.parametrize("stack", list(_STACK_TEMPLATES.keys()))
    def test_stack_has_templates(self, stack):
        assert len(_STACK_TEMPLATES[stack]) > 0, f"{stack} should have templates"

    @pytest.mark.parametrize("stack", list(_STACK_TEMPLATES.keys()))
    def test_all_templates_exist(self, stack):
        for t in _STACK_TEMPLATES[stack]:
            assert (_STACKS_DIR / stack / "core" / _PACK_FOLDER / t).exists()


def test_total_template_count():
    total = sum(len(v) for v in _STACK_TEMPLATES.values())
    assert total >= 4, f"Expected at least 4 templates, got {total}"


class TestRuleV1NoMidicoderImport:
    @pytest.mark.parametrize("stack", list(_STACK_TEMPLATES.keys()))
    def test_no_midicoder_import(self, stack):
        for t in _STACK_TEMPLATES[stack]:
            raw = (_STACKS_DIR / stack / "core" / _PACK_FOLDER / t).read_text(encoding="utf-8")
            assert "from midicoder" not in raw, f"{stack}/{t} should not import from midicoder"


class TestRuleV2NoPostInit:
    @pytest.mark.parametrize("stack", list(_STACK_TEMPLATES.keys()))
    def test_no_post_init(self, stack):
        for t in _STACK_TEMPLATES[stack]:
            raw = (_STACKS_DIR / stack / "core" / _PACK_FOLDER / t).read_text(encoding="utf-8")
            assert "__post_init__" not in raw, f"{stack}/{t} should not contain __post_init__"
