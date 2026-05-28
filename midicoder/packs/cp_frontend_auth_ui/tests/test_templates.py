"""Test template existence and content for CP21."""
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


# ---- CP21: auth_ui (frontend only: react, angular) ----
_PACK_FOLDER = "cp_frontend_auth_ui"
_REACT_TEMPLATES = sorted([f.name for f in (_STACKS_DIR / "react" / "core" / _PACK_FOLDER).glob("*.jinja2")])
_ANGULAR_TEMPLATES = sorted([f.name for f in (_STACKS_DIR / "angular" / "core" / _PACK_FOLDER).glob("*.jinja2")])


class TestTemplateDiscovery:
    @pytest.mark.parametrize("t", _REACT_TEMPLATES)
    def test_react_template_exists(self, t):
        assert (_STACKS_DIR / "react" / "core" / _PACK_FOLDER / t).exists()

    @pytest.mark.parametrize("t", _ANGULAR_TEMPLATES)
    def test_angular_template_exists(self, t):
        assert (_STACKS_DIR / "angular" / "core" / _PACK_FOLDER / t).exists()


def test_total_template_count():
    assert len(_REACT_TEMPLATES) + len(_ANGULAR_TEMPLATES) >= 10


class TestRuleV1NoMidicoderImport:
    @pytest.mark.parametrize("t", _REACT_TEMPLATES + _ANGULAR_TEMPLATES)
    def test_no_midicoder_import(self, t):
        stack = "react" if (_STACKS_DIR / "react" / "core" / _PACK_FOLDER / t).exists() else "angular"
        raw = (_STACKS_DIR / stack / "core" / _PACK_FOLDER / t).read_text(encoding="utf-8")
        assert "from midicoder" not in raw, f"{t} should not import from midicoder"


class TestRuleV2NoPostInit:
    @pytest.mark.parametrize("t", _REACT_TEMPLATES + _ANGULAR_TEMPLATES)
    def test_no_post_init(self, t):
        stack = "react" if (_STACKS_DIR / "react" / "core" / _PACK_FOLDER / t).exists() else "angular"
        raw = (_STACKS_DIR / stack / "core" / _PACK_FOLDER / t).read_text(encoding="utf-8")
        assert "__post_init__" not in raw, f"{t} should not contain __post_init__"
