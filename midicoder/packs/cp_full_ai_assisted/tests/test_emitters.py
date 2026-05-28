# coding: utf-8
"""
Emitter tests cho CP30 AI-Assisted Development Generator.

Kiểm tra:
- FastAPI emitter: render đúng 7 templates (__init__.py, models.py, review_engine.py,
  suggestion_engine.py, prompt_templates.py, registry.py, ai_assistant.yaml)
- NestJS emitter: render đúng 5 templates (models.ts, ai-assistant.module.ts,
  review.service.ts, suggestion.service.ts, templates.service.ts)
- Angular emitter: render đúng 6 templates (có thêm ai-suggestion-panel.component.ts)
- React emitter: render đúng 6 templates (có thêm AISuggestionPanel.tsx, ai-assistant.ts)
- Review policies: verify 6 policies (hardcoded_secret, sql_injection,
  performance_anti_pattern, style, type_safety, unused_import) có mặt trong context
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from midicoder.packs.cp_full_ai_assisted.recipes import (
    auto_generate_ai_assistant_from_mir,
    generate_default_review_policies,
    generate_default_prompt_templates,
    generate_default_config,
)
from midicoder.pipeline.emitter import Emitter


# ===========================================================================
# Context mẫu cho tất cả test
# ===========================================================================


def _make_context() -> dict[str, Any]:
    """Tạo context mẫu cho AI assistant emit."""
    collection = auto_generate_ai_assistant_from_mir({
        "entities": [
            {"id": "Customer", "fields": [{"id": "name"}, {"id": "email"}]},
            {"id": "Order", "fields": [{"id": "total"}, {"id": "status"}]},
        ],
        "commands": [
            {"id": "CreateOrder", "input": [{"name": "customer_id"}]},
        ],
    })

    config = collection.config or generate_default_config()
    policies = collection.review_policies
    templates = collection.prompt_templates

    return {
        "entities": [
            {"id": "Customer", "fields": [{"id": "name"}, {"id": "email"}]},
            {"id": "Order", "fields": [{"id": "total"}, {"id": "status"}]},
        ],
        "commands": [{"id": "CreateOrder", "input": [{"name": "customer_id"}]}],
        "queries": [],
        "policies": [],
        "ai_assistant_config": {
            "id": config.id,
            "enabled": config.enabled,
            "default_model": config.default_model,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
        },
        "review_policies": [
            {
                "id": p.id,
                "name": p.name,
                "severity": p.severity.value,
                "category": p.category.value,
                "enabled": p.enabled,
            }
            for p in policies
        ],
        "prompt_templates": [
            {
                "id": t.id,
                "name": t.name,
                "category": t.category.value,
                "variables": t.variables,
            }
            for t in templates
        ],
    }


# Template lists per stack (theo templates có thật)
FASTAPI_TEMPLATES = [
    "__init__.py.jinja2",
    "models.py.jinja2",
    "review_engine.py.jinja2",
    "suggestion_engine.py.jinja2",
    "prompt_templates.py.jinja2",
    "registry.py.jinja2",
    "ai_assistant.yaml.jinja2",
]

NESTJS_TEMPLATES = [
    "models.ts.jinja2",
    "ai-assistant.module.ts.jinja2",
    "review.service.ts.jinja2",
    "suggestion.service.ts.jinja2",
    "templates.service.ts.jinja2",
]

ANGULAR_TEMPLATES = [
    "models.ts.jinja2",
    "ai-assistant.module.ts.jinja2",
    "review.service.ts.jinja2",
    "suggestion.service.ts.jinja2",
    "templates.service.ts.jinja2",
    "ai-suggestion-panel.component.ts.jinja2",
]

REACT_TEMPLATES = [
    "types.ts.jinja2",
    "ai-assistant.ts.jinja2",
    "review.ts.jinja2",
    "suggestion.ts.jinja2",
    "templates.ts.jinja2",
    "AISuggestionPanel.tsx.jinja2",
]


# ===========================================================================
# Test FastAPI Emitter
# ===========================================================================


class TestFastAPIEmitter:
    """Kiểm tra FastAPI emitter render đúng 7 templates."""

    def test_emit_all_7_templates(self, tmp_path: Path) -> None:
        """FastAPI render được cả 7 templates."""
        emitter = Emitter(stack="fastapi")
        context = _make_context()
        for tmpl in FASTAPI_TEMPLATES:
            content = emitter.render(f"cp_full_ai_assisted/{tmpl}", context)
            assert len(content) > 0, f"Template {tmpl} render rỗng"

    def test_render_init_file(self, tmp_path: Path) -> None:
        """__init__.py chứa AI assistant export."""
        emitter = Emitter(stack="fastapi")
        content = emitter.render("cp_full_ai_assisted/__init__.py.jinja2", _make_context())
        assert "ai" in content.lower() or "assistant" in content.lower() or "__all__" in content

    def test_render_models_file(self, tmp_path: Path) -> None:
        """models.py chứa AI data models."""
        emitter = Emitter(stack="fastapi")
        content = emitter.render("cp_full_ai_assisted/models.py.jinja2", _make_context())
        assert "class" in content or "model" in content.lower() or "pydantic" in content.lower()

    def test_render_review_engine(self, tmp_path: Path) -> None:
        """review_engine.py chứa review logic."""
        emitter = Emitter(stack="fastapi")
        content = emitter.render("cp_full_ai_assisted/review_engine.py.jinja2", _make_context())
        assert "review" in content.lower()

    def test_render_suggestion_engine(self, tmp_path: Path) -> None:
        """suggestion_engine.py chứa suggestion logic."""
        emitter = Emitter(stack="fastapi")
        content = emitter.render("cp_full_ai_assisted/suggestion_engine.py.jinja2", _make_context())
        assert "suggestion" in content.lower() or "suggest" in content.lower()

    def test_render_prompt_templates(self, tmp_path: Path) -> None:
        """prompt_templates.py chứa prompt template definitions."""
        emitter = Emitter(stack="fastapi")
        content = emitter.render("cp_full_ai_assisted/prompt_templates.py.jinja2", _make_context())
        assert "prompt" in content.lower() or "template" in content.lower()

    def test_render_registry_file(self, tmp_path: Path) -> None:
        """registry.py chứa AI assistant registry."""
        emitter = Emitter(stack="fastapi")
        content = emitter.render("cp_full_ai_assisted/registry.py.jinja2", _make_context())
        assert "registry" in content.lower() or "register" in content.lower()

    def test_render_yaml_config(self, tmp_path: Path) -> None:
        """ai_assistant.yaml chứa YAML config."""
        emitter = Emitter(stack="fastapi")
        content = emitter.render("cp_full_ai_assisted/ai_assistant.yaml.jinja2", _make_context())
        assert "model" in content.lower() or "gpt" in content.lower() or "enabled" in content.lower()


# ===========================================================================
# Test NestJS Emitter
# ===========================================================================


class TestNestJSEmitter:
    """Kiểm tra NestJS emitter render đúng 5 templates."""

    def test_emit_all_5_templates(self, tmp_path: Path) -> None:
        """NestJS render được cả 5 templates."""
        emitter = Emitter(stack="nestjs")
        context = _make_context()
        for tmpl in NESTJS_TEMPLATES:
            content = emitter.render(f"cp_full_ai_assisted/{tmpl}", context)
            assert len(content) > 0, f"Template {tmpl} render rỗng"

    def test_render_module_file(self, tmp_path: Path) -> None:
        """ai-assistant.module.ts chứa @Module."""
        emitter = Emitter(stack="nestjs")
        content = emitter.render("cp_full_ai_assisted/ai-assistant.module.ts.jinja2", _make_context())
        assert "@Module" in content or "Module" in content

    def test_render_review_service(self, tmp_path: Path) -> None:
        """review.service.ts chứa @Injectable review service."""
        emitter = Emitter(stack="nestjs")
        content = emitter.render("cp_full_ai_assisted/review.service.ts.jinja2", _make_context())
        assert "review" in content.lower() or "@Injectable" in content

    def test_render_suggestion_service(self, tmp_path: Path) -> None:
        """suggestion.service.ts chứa suggestion service."""
        emitter = Emitter(stack="nestjs")
        content = emitter.render("cp_full_ai_assisted/suggestion.service.ts.jinja2", _make_context())
        assert "suggestion" in content.lower() or "suggest" in content.lower()

    def test_render_templates_service(self, tmp_path: Path) -> None:
        """templates.service.ts chứa template management."""
        emitter = Emitter(stack="nestjs")
        content = emitter.render("cp_full_ai_assisted/templates.service.ts.jinja2", _make_context())
        assert "template" in content.lower()


# ===========================================================================
# Test Angular Emitter
# ===========================================================================


class TestAngularEmitter:
    """Kiểm tra Angular emitter render đúng 6 templates."""

    def test_emit_all_6_templates(self, tmp_path: Path) -> None:
        """Angular render được cả 6 templates."""
        emitter = Emitter(stack="angular")
        context = _make_context()
        for tmpl in ANGULAR_TEMPLATES:
            content = emitter.render(f"cp_full_ai_assisted/{tmpl}", context)
            assert len(content) > 0, f"Template {tmpl} render rỗng"

    def test_render_module_file(self, tmp_path: Path) -> None:
        """ai-assistant.module.ts chứa @NgModule."""
        emitter = Emitter(stack="angular")
        content = emitter.render("cp_full_ai_assisted/ai-assistant.module.ts.jinja2", _make_context())
        assert "@NgModule" in content or "NgModule" in content

    def test_render_suggestion_panel(self, tmp_path: Path) -> None:
        """ai-suggestion-panel.component.ts chứa @Component."""
        emitter = Emitter(stack="angular")
        content = emitter.render("cp_full_ai_assisted/ai-suggestion-panel.component.ts.jinja2", _make_context())
        assert "@Component" in content or "Component" in content

    def test_render_review_service(self, tmp_path: Path) -> None:
        """review.service.ts chứa review service."""
        emitter = Emitter(stack="angular")
        content = emitter.render("cp_full_ai_assisted/review.service.ts.jinja2", _make_context())
        assert "review" in content.lower()


# ===========================================================================
# Test React Emitter
# ===========================================================================


class TestReactEmitter:
    """Kiểm tra React emitter render đúng 6 templates."""

    def test_emit_all_6_templates(self, tmp_path: Path) -> None:
        """React render được cả 6 templates."""
        emitter = Emitter(stack="react")
        context = _make_context()
        for tmpl in REACT_TEMPLATES:
            content = emitter.render(f"cp_full_ai_assisted/{tmpl}", context)
            assert len(content) > 0, f"Template {tmpl} render rỗng"

    def test_render_types_file(self, tmp_path: Path) -> None:
        """types.ts chứa TypeScript type definitions."""
        emitter = Emitter(stack="react")
        content = emitter.render("cp_full_ai_assisted/types.ts.jinja2", _make_context())
        assert "interface" in content or "type" in content.lower()

    def test_render_ai_assistant_file(self, tmp_path: Path) -> None:
        """ai-assistant.ts chứa AI assistant hook/utility."""
        emitter = Emitter(stack="react")
        content = emitter.render("cp_full_ai_assisted/ai-assistant.ts.jinja2", _make_context())
        assert "ai" in content.lower() or "assistant" in content.lower()

    def test_render_suggestion_panel(self, tmp_path: Path) -> None:
        """AISuggestionPanel.tsx chứa React component."""
        emitter = Emitter(stack="react")
        content = emitter.render("cp_full_ai_assisted/AISuggestionPanel.tsx.jinja2", _make_context())
        assert "function" in content.lower() or "component" in content.lower() or "export" in content.lower()


# ===========================================================================
# Test Review Policies
# ===========================================================================


class TestReviewPolicies:
    """Kiểm tra 6 review policies có mặt trong emitted context."""

    def test_policy_hardcoded_secret(self, tmp_path: Path) -> None:
        """Policy: hardcoded_secret detection."""
        policies = generate_default_review_policies()
        ids = [p.id for p in policies]
        assert "policy_hardcoded_secret" in ids

    def test_policy_sql_injection(self, tmp_path: Path) -> None:
        """Policy: SQL injection check."""
        policies = generate_default_review_policies()
        ids = [p.id for p in policies]
        assert "policy_sql_injection" in ids

    def test_policy_performance_anti_pattern(self, tmp_path: Path) -> None:
        """Policy: performance anti-pattern."""
        policies = generate_default_review_policies()
        ids = [p.id for p in policies]
        assert "policy_performance_anti_pattern" in ids

    def test_policy_style(self, tmp_path: Path) -> None:
        """Policy: style enforcement."""
        policies = generate_default_review_policies()
        ids = [p.id for p in policies]
        assert "policy_style_enforcement" in ids

    def test_policy_type_safety(self, tmp_path: Path) -> None:
        """Policy: type safety check."""
        policies = generate_default_review_policies()
        ids = [p.id for p in policies]
        assert "policy_type_safety" in ids

    def test_policy_unused_import(self, tmp_path: Path) -> None:
        """Policy: unused import detection."""
        policies = generate_default_review_policies()
        ids = [p.id for p in policies]
        assert "policy_unused_import" in ids

    def test_total_six_policies(self, tmp_path: Path) -> None:
        """Tổng cộng đúng 6 policies."""
        policies = generate_default_review_policies()
        assert len(policies) == 6

    def test_context_has_review_policies(self, tmp_path: Path) -> None:
        """Context có review_policies key với 6 entries."""
        context = _make_context()
        assert "review_policies" in context
        assert len(context["review_policies"]) == 6

    def test_policies_have_categories(self, tmp_path: Path) -> None:
        """Policies có đầy đủ categories: SECURITY, PERFORMANCE, STYLE, CORRECTNESS."""
        policies = generate_default_review_policies()
        categories = {p.category.value for p in policies}
        assert "security" in categories
        assert "performance" in categories
        assert "style" in categories
        assert "correctness" in categories

    def test_default_config_has_review_policies_enabled(self, tmp_path: Path) -> None:
        """Default config có 4 review policies enabled."""
        config = generate_default_config()
        assert len(config.review_policies_enabled) >= 4


# ===========================================================================
# Test Prompt Templates
# ===========================================================================


class TestPromptTemplates:
    """Kiểm tra prompt templates trong emitted context."""

    def test_has_security_template(self, tmp_path: Path) -> None:
        """Template: security review."""
        templates = generate_default_prompt_templates()
        ids = [t.id for t in templates]
        assert "tmpl_security_review" in ids

    def test_has_performance_template(self, tmp_path: Path) -> None:
        """Template: performance review."""
        templates = generate_default_prompt_templates()
        ids = [t.id for t in templates]
        assert "tmpl_performance_review" in ids

    def test_has_style_template(self, tmp_path: Path) -> None:
        """Template: style review."""
        templates = generate_default_prompt_templates()
        ids = [t.id for t in templates]
        assert "tmpl_style_review" in ids

    def test_has_test_generation_template(self, tmp_path: Path) -> None:
        """Template: test generation."""
        templates = generate_default_prompt_templates()
        ids = [t.id for t in templates]
        assert "tmpl_test_generation" in ids


# ===========================================================================
# Test Error Boundary
# ===========================================================================


class TestErrorBoundary:
    """Kiểm tra error boundary."""

    def test_emitter_raises_error_for_missing_template(self, tmp_path: Path) -> None:
        """Emitter raise error khi template không tồn tại."""
        emitter = Emitter(stack="fastapi")
        with pytest.raises(Exception):
            emitter.render("cp_full_ai_assisted/nonexistent.py.jinja2", _make_context())

    def test_auto_generate_with_none_metadata(self, tmp_path: Path) -> None:
        """auto_generate_ai_assistant_from_mir xử lý None metadata không crash."""
        collection = auto_generate_ai_assistant_from_mir(None)
        # Với None metadata, recipe vẫn sinh default policies/templates
        assert collection is not None
