# coding: utf-8
"""
Test cases cho CP30 — kiểm tra template rendering.

Kiểm tra:
- Templates tồn tại và render được với context hợp lệ
- Template context có các keys cần thiết
"""

from pathlib import Path

import jinja2
import pytest

from midicoder.emitters.core.cp30_ai_assisted.parser import AIAssistantParser
from midicoder.emitters.core.cp30_ai_assisted.recipes import auto_generate_ai_assistant_from_mir

# ============================================================================
# Đường dẫn dự án
# ============================================================================

ROOT = Path(__file__).resolve().parents[5]  # midicoder-ce/

# ============================================================================
# Template directories và danh sách templates (cho Rule V1/V2)
# ============================================================================

STACK_DIRS = {
    "fastapi": ROOT / "midicoder" / "stacks" / "fastapi" / "core" / "cp30_ai_assisted",
    "nestjs": ROOT / "midicoder" / "stacks" / "nestjs" / "core" / "cp30_ai_assisted",
    "angular": ROOT / "midicoder" / "stacks" / "angular" / "core" / "cp30_ai_assisted",
    "react": ROOT / "midicoder" / "stacks" / "react" / "core" / "cp30_ai_assisted",
}

FASTAPI_TEMPLATES = [
    "__init__.py.jinja2",
    "ai_assistant.yaml.jinja2",
    "models.py.jinja2",
    "prompt_templates.py.jinja2",
    "registry.py.jinja2",
    "review_engine.py.jinja2",
    "suggestion_engine.py.jinja2",
]

NESTJS_TEMPLATES = [
    "ai-assistant.module.ts.jinja2",
    "models.ts.jinja2",
    "review.service.ts.jinja2",
    "suggestion.service.ts.jinja2",
    "templates.service.ts.jinja2",
]

ANGULAR_TEMPLATES = [
    "ai-assistant.module.ts.jinja2",
    "ai-suggestion-panel.component.ts.jinja2",
    "models.ts.jinja2",
    "review.service.ts.jinja2",
    "suggestion.service.ts.jinja2",
    "templates.service.ts.jinja2",
]

REACT_TEMPLATES = [
    "ai-assistant.ts.jinja2",
    "AISuggestionPanel.tsx.jinja2",
    "review.ts.jinja2",
    "suggestion.ts.jinja2",
    "templates.ts.jinja2",
    "types.ts.jinja2",
]

ALL_TEMPLATES = {
    "fastapi": FASTAPI_TEMPLATES,
    "nestjs": NESTJS_TEMPLATES,
    "angular": ANGULAR_TEMPLATES,
    "react": REACT_TEMPLATES,
}


def _render_template(stack: str, template_name: str) -> str:
    """Render template với context cơ bản sử dụng Jinja2 trực tiếp."""
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(STACK_DIRS[stack])),
        undefined=jinja2.ChainableUndefined,
    )
    # Context tối thiểu: các template CP30 dùng review_policies, prompt_templates, config
    ctx = {
        "review_policies": [],
        "prompt_templates": [],
        "config": {"enabled": True, "default_model": "gpt-4", "max_tokens": 2048},
    }
    template = env.get_template(template_name)
    return template.render(**ctx)


class TestTemplateContext:
    """Kiểm tra context cho template rendering."""

    def test_collection_provides_review_policies_context(self):
        """Kiểm tra collection cung cấp context cho review policies."""
        collection = auto_generate_ai_assistant_from_mir({})
        d = collection.to_dict()

        assert "review_policies" in d
        for policy in d["review_policies"]:
            assert "id" in policy
            assert "name" in policy
            assert "severity" in policy
            assert "category" in policy

    def test_collection_provides_prompt_templates_context(self):
        """Kiểm tra collection cung cấp context cho prompt templates."""
        collection = auto_generate_ai_assistant_from_mir({})
        d = collection.to_dict()

        assert "prompt_templates" in d
        for template in d["prompt_templates"]:
            assert "id" in template
            assert "name" in template
            assert "category" in template
            assert "content" in template

    def test_collection_provides_config_context(self):
        """Kiểm tra collection cung cấp context cho config."""
        collection = auto_generate_ai_assistant_from_mir({})
        d = collection.to_dict()

        assert "config" in d
        assert d["config"] is not None
        assert "enabled" in d["config"]
        assert "default_model" in d["config"]
        assert "max_tokens" in d["config"]

    def test_parser_provides_context_for_all_severities(self):
        """Kiểm tra parser render context có đủ severities."""
        parser = AIAssistantParser()
        data = {
            "review_policies": [
                {"id": "p1", "severity": "error", "category": "security"},
                {"id": "p2", "severity": "warning", "category": "performance"},
                {"id": "p3", "severity": "info", "category": "style"},
            ]
        }
        collection = parser.parse(data)
        d = collection.to_dict()

        severities = {p["severity"] for p in d["review_policies"]}
        assert "error" in severities
        assert "warning" in severities
        assert "info" in severities


# ===========================================================================
# Test Rule V1 & V2 (P2-17)
# ===========================================================================

class TestRuleV1NoMidicoderImport:
    """Rule V1: Output của template KHÔNG chứa 'from midicoder'."""

    def test_fastapi_no_midicoder_import(self) -> None:
        """FastAPI templates không chứa 'from midicoder' trong output."""
        for template in FASTAPI_TEMPLATES:
            result = _render_template("fastapi", template)
            assert "from midicoder" not in result, f"Rule V1 vi phạm: {template}"
            assert "import midicoder" not in result, f"Rule V1 vi phạm: {template}"

    def test_nestjs_no_midicoder_import(self) -> None:
        """NestJS templates không chứa 'from midicoder' trong output."""
        for template in NESTJS_TEMPLATES:
            result = _render_template("nestjs", template)
            assert "from midicoder" not in result, f"Rule V1 vi phạm: {template}"
            assert "import midicoder" not in result, f"Rule V1 vi phạm: {template}"

    def test_angular_no_midicoder_import(self) -> None:
        """Angular templates không chứa 'from midicoder' trong output."""
        for template in ANGULAR_TEMPLATES:
            result = _render_template("angular", template)
            assert "from midicoder" not in result, f"Rule V1 vi phạm: {template}"
            assert "import midicoder" not in result, f"Rule V1 vi phạm: {template}"

    def test_react_no_midicoder_import(self) -> None:
        """React templates không chứa 'from midicoder' trong output."""
        for template in REACT_TEMPLATES:
            result = _render_template("react", template)
            assert "from midicoder" not in result, f"Rule V1 vi phạm: {template}"
            assert "import midicoder" not in result, f"Rule V1 vi phạm: {template}"


class TestRuleV2NoPostInit:
    """Rule V2: Output của template KHÔNG chứa '__post_init__'."""

    def test_fastapi_no_post_init(self) -> None:
        """FastAPI templates không chứa __post_init__ trong output."""
        for template in FASTAPI_TEMPLATES:
            result = _render_template("fastapi", template)
            assert "__post_init__" not in result, f"Rule V2 vi phạm: {template}"

    def test_nestjs_no_post_init(self) -> None:
        """NestJS templates không chứa __post_init__ trong output."""
        for template in NESTJS_TEMPLATES:
            result = _render_template("nestjs", template)
            assert "__post_init__" not in result, f"Rule V2 vi phạm: {template}"

    def test_angular_no_post_init(self) -> None:
        """Angular templates không chứa __post_init__ trong output."""
        for template in ANGULAR_TEMPLATES:
            result = _render_template("angular", template)
            assert "__post_init__" not in result, f"Rule V2 vi phạm: {template}"

    def test_react_no_post_init(self) -> None:
        """React templates không chứa __post_init__ trong output."""
        for template in REACT_TEMPLATES:
            result = _render_template("react", template)
            assert "__post_init__" not in result, f"Rule V2 vi phạm: {template}"
