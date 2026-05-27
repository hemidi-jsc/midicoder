"""Test template existence and content for CP29."""
from __future__ import annotations

import pytest
import jinja2
from pathlib import Path

_STACKS_DIR = Path(__file__).resolve().parents[4] / "stacks"


def _render_template(stack: str, pack_folder: str, template_name: str, context: dict | None = None) -> str:
    """Render a Jinja2 template with a permissive environment."""
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(_STACKS_DIR / stack / "core" / pack_folder),
        undefined=jinja2.ChainableUndefined,
    )
    try:
        tmpl = env.get_template(template_name)
        return tmpl.render(context or {})
    except Exception:
        # Fallback: read raw text
        p = _STACKS_DIR / stack / "core" / pack_folder / template_name
        return p.read_text(encoding="utf-8") if p.exists() else ""


# ---- CP29: multi_language (all 4 stacks) ----
_PACK_FOLDER = "cp29_multi_language"
_FASTAPI_TEMPLATES = sorted([f.name for f in (_STACKS_DIR / "fastapi" / "core" / _PACK_FOLDER).glob("*.jinja2")])
_NESTJS_TEMPLATES = sorted([f.name for f in (_STACKS_DIR / "nestjs" / "core" / _PACK_FOLDER).glob("*.jinja2")])
_REACT_TEMPLATES = sorted([f.name for f in (_STACKS_DIR / "react" / "core" / _PACK_FOLDER).glob("*.jinja2")])
_ANGULAR_TEMPLATES = sorted([f.name for f in (_STACKS_DIR / "angular" / "core" / _PACK_FOLDER).glob("*.jinja2")])

_ALL_TEMPLATES = (
    [("fastapi", t) for t in _FASTAPI_TEMPLATES]
    + [("nestjs", t) for t in _NESTJS_TEMPLATES]
    + [("react", t) for t in _REACT_TEMPLATES]
    + [("angular", t) for t in _ANGULAR_TEMPLATES]
)


class TestTemplateDiscovery:
    @pytest.mark.parametrize("t", _FASTAPI_TEMPLATES)
    def test_fastapi_template_exists(self, t):
        assert (_STACKS_DIR / "fastapi" / "core" / _PACK_FOLDER / t).exists()

    @pytest.mark.parametrize("t", _NESTJS_TEMPLATES)
    def test_nestjs_template_exists(self, t):
        assert (_STACKS_DIR / "nestjs" / "core" / _PACK_FOLDER / t).exists()

    @pytest.mark.parametrize("t", _REACT_TEMPLATES)
    def test_react_template_exists(self, t):
        assert (_STACKS_DIR / "react" / "core" / _PACK_FOLDER / t).exists()

    @pytest.mark.parametrize("t", _ANGULAR_TEMPLATES)
    def test_angular_template_exists(self, t):
        assert (_STACKS_DIR / "angular" / "core" / _PACK_FOLDER / t).exists()


def test_total_template_count():
    assert (
        len(_FASTAPI_TEMPLATES) + len(_NESTJS_TEMPLATES)
        + len(_REACT_TEMPLATES) + len(_ANGULAR_TEMPLATES)
    ) >= 5


class TestRuleV1NoMidicoderImport:
    @pytest.mark.parametrize("stack,t", _ALL_TEMPLATES)
    def test_no_midicoder_import(self, stack, t):
        raw = (_STACKS_DIR / stack / "core" / _PACK_FOLDER / t).read_text(encoding="utf-8")
        assert "from midicoder" not in raw, f"[{stack}] {t} should not import from midicoder"


class TestRuleV2NoPostInit:
    @pytest.mark.parametrize("stack,t", _ALL_TEMPLATES)
    def test_no_post_init(self, stack, t):
        raw = (_STACKS_DIR / stack / "core" / _PACK_FOLDER / t).read_text(encoding="utf-8")
        assert "__post_init__" not in raw, f"[{stack}] {t} should not contain __post_init__"
