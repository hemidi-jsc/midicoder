# coding: utf-8
"""
Unit tests cho CP30 AI-Assisted Development Generator — models.

Kiểm tra:
- Enums: ReviewSeverity, ReviewCategory, SuggestionType, PromptCategory
- Dataclasses: ReviewPolicy, ReviewResult, SuggestionContext, SuggestionResult,
  PromptTemplate, AIAssistantConfig, AIAssistantCollection
- Validation: empty id, invalid severity, invalid category, duplicate ids
- Serialization: to_dict / from_dict
"""

from __future__ import annotations

from typing import Any

import pytest

from midicoder.emitters.core.cp30_ai_assisted.models import (
    AIAssistantCollection,
    AIAssistantConfig,
    PromptCategory,
    PromptTemplate,
    ReviewCategory,
    ReviewPolicy,
    ReviewResult,
    ReviewSeverity,
    SuggestionContext,
    SuggestionResult,
    SuggestionType,
)
from midicoder.errors import MidicoderError


# ===========================================================================
# Test Enums
# ===========================================================================


class TestReviewSeverity:
    """Kiểm tra enum ReviewSeverity."""

    def test_error_value(self) -> None:
        assert ReviewSeverity.ERROR.value == "error"

    def test_warning_value(self) -> None:
        assert ReviewSeverity.WARNING.value == "warning"

    def test_info_value(self) -> None:
        assert ReviewSeverity.INFO.value == "info"

    def test_all_members_count(self) -> None:
        assert len(ReviewSeverity) == 3


class TestReviewCategory:
    """Kiểm tra enum ReviewCategory."""

    def test_security_value(self) -> None:
        assert ReviewCategory.SECURITY.value == "security"

    def test_performance_value(self) -> None:
        assert ReviewCategory.PERFORMANCE.value == "performance"

    def test_style_value(self) -> None:
        assert ReviewCategory.STYLE.value == "style"

    def test_correctness_value(self) -> None:
        assert ReviewCategory.CORRECTNESS.value == "correctness"

    def test_all_members_count(self) -> None:
        assert len(ReviewCategory) == 4


class TestSuggestionType:
    """Kiểm tra enum SuggestionType."""

    def test_completion_value(self) -> None:
        assert SuggestionType.COMPLETION.value == "completion"

    def test_refactor_value(self) -> None:
        assert SuggestionType.REFACTOR.value == "refactor"

    def test_fix_value(self) -> None:
        assert SuggestionType.FIX.value == "fix"

    def test_explain_value(self) -> None:
        assert SuggestionType.EXPLAIN.value == "explain"

    def test_all_members_count(self) -> None:
        assert len(SuggestionType) == 4


class TestPromptCategory:
    """Kiểm tra enum PromptCategory."""

    def test_code_review_value(self) -> None:
        assert PromptCategory.CODE_REVIEW.value == "code_review"

    def test_code_suggestion_value(self) -> None:
        assert PromptCategory.CODE_SUGGESTION.value == "code_suggestion"

    def test_code_generation_value(self) -> None:
        assert PromptCategory.CODE_GENERATION.value == "code_generation"

    def test_documentation_value(self) -> None:
        assert PromptCategory.DOCUMENTATION.value == "documentation"

    def test_testing_value(self) -> None:
        assert PromptCategory.TESTING.value == "testing"

    def test_custom_value(self) -> None:
        assert PromptCategory.CUSTOM.value == "custom"

    def test_all_members_count(self) -> None:
        assert len(PromptCategory) == 6


# ===========================================================================
# Test ReviewPolicy
# ===========================================================================


class TestReviewPolicy:
    """Kiểm tra dataclass ReviewPolicy."""

    def test_create_valid_policy(self) -> None:
        policy = ReviewPolicy(
            id="security_scan",
            name="Security Scan",
            description="Scan security vulnerabilities",
            severity=ReviewSeverity.ERROR,
            category=ReviewCategory.SECURITY,
            enabled=True,
            prompt_template_ref="tmpl_security",
        )
        assert policy.id == "security_scan"
        assert policy.severity == ReviewSeverity.ERROR
        assert policy.category == ReviewCategory.SECURITY
        assert policy.enabled is True

    def test_default_values(self) -> None:
        policy = ReviewPolicy(id="test")
        assert policy.name == ""
        assert policy.description == ""
        assert policy.severity == ReviewSeverity.INFO
        assert policy.category == ReviewCategory.STYLE
        assert policy.enabled is True
        assert policy.prompt_template_ref is None

    def test_empty_id_raises_error(self) -> None:
        with pytest.raises(MidicoderError):
            ReviewPolicy(id="")

    def test_whitespace_id_raises_error(self) -> None:
        with pytest.raises(MidicoderError):
            ReviewPolicy(id="   ")


# ===========================================================================
# Test ReviewResult
# ===========================================================================


class TestReviewResult:
    """Kiểm tra dataclass ReviewResult."""

    def test_create_valid_result(self) -> None:
        result = ReviewResult(
            finding_id="finding_1",
            policy_id="security_scan",
            severity=ReviewSeverity.ERROR,
            message="Hardcoded API key found",
            line_range=[10, 12],
            suggestion="Use environment variable instead",
        )
        assert result.finding_id == "finding_1"
        assert result.line_range == [10, 12]
        assert result.suggestion == "Use environment variable instead"

    def test_default_values(self) -> None:
        result = ReviewResult(
            finding_id="f1",
            policy_id="p1",
            severity=ReviewSeverity.INFO,
            message="msg",
        )
        assert result.line_range == []
        assert result.suggestion == ""

    def test_empty_id_raises_error(self) -> None:
        with pytest.raises(MidicoderError):
            ReviewResult(
                finding_id="",
                policy_id="p1",
                severity=ReviewSeverity.INFO,
                message="msg",
            )


# ===========================================================================
# Test SuggestionContext
# ===========================================================================


class TestSuggestionContext:
    """Kiểm tra dataclass SuggestionContext."""

    def test_create_with_all_fields(self) -> None:
        ctx = SuggestionContext(
            file_path="src/main.py",
            language="python",
            code_snippet="def hello(): pass",
            cursor_position=15,
            intent="refactor",
        )
        assert ctx.file_path == "src/main.py"
        assert ctx.cursor_position == 15

    def test_default_values(self) -> None:
        ctx = SuggestionContext()
        assert ctx.file_path == ""
        assert ctx.language == "python"
        assert ctx.code_snippet == ""
        assert ctx.cursor_position is None
        assert ctx.intent == ""


# ===========================================================================
# Test SuggestionResult
# ===========================================================================


class TestSuggestionResult:
    """Kiểm tra dataclass SuggestionResult."""

    def test_create_valid_result(self) -> None:
        result = SuggestionResult(
            id="suggest_1",
            suggestion_type=SuggestionType.REFACTOR,
            content="Extract method",
            confidence=0.95,
            explanation="Function is too long",
        )
        assert result.suggestion_type == SuggestionType.REFACTOR
        assert result.confidence == 0.95

    def test_default_values(self) -> None:
        result = SuggestionResult(id="s1")
        assert result.suggestion_type == SuggestionType.COMPLETION
        assert result.content == ""
        assert result.confidence == 0.0

    def test_empty_id_raises_error(self) -> None:
        with pytest.raises(MidicoderError):
            SuggestionResult(id="")


# ===========================================================================
# Test PromptTemplate
# ===========================================================================


class TestPromptTemplate:
    """Kiểm tra dataclass PromptTemplate."""

    def test_create_valid_template(self) -> None:
        tmpl = PromptTemplate(
            id="tmpl_review",
            name="Code Review",
            category=PromptCategory.CODE_REVIEW,
            content="Review {{code}}",
            variables={"code": "Source code"},
            version="1.0.0",
        )
        assert tmpl.id == "tmpl_review"
        assert tmpl.category == PromptCategory.CODE_REVIEW
        assert "code" in tmpl.variables

    def test_default_values(self) -> None:
        tmpl = PromptTemplate(id="t1")
        assert tmpl.name == ""
        assert tmpl.category == PromptCategory.CUSTOM
        assert tmpl.content == ""
        assert tmpl.version == "1.0.0"

    def test_empty_id_raises_error(self) -> None:
        with pytest.raises(MidicoderError):
            PromptTemplate(id="")


# ===========================================================================
# Test AIAssistantConfig
# ===========================================================================


class TestAIAssistantConfig:
    """Kiểm tra dataclass AIAssistantConfig."""

    def test_create_valid_config(self) -> None:
        cfg = AIAssistantConfig(
            id="production",
            enabled=True,
            default_model="claude-3",
            max_tokens=8192,
            temperature=0.5,
            timeout_seconds=60,
        )
        assert cfg.id == "production"
        assert cfg.default_model == "claude-3"
        assert cfg.max_tokens == 8192

    def test_default_values(self) -> None:
        cfg = AIAssistantConfig()
        assert cfg.id == "default"
        assert cfg.enabled is True
        assert cfg.default_model == "gpt-4"
        assert cfg.max_tokens == 4096
        assert cfg.temperature == 0.7
        assert cfg.suggestions_enabled is True

    def test_empty_id_raises_error(self) -> None:
        with pytest.raises(MidicoderError):
            AIAssistantConfig(id="")


# ===========================================================================
# Test AIAssistantCollection
# ===========================================================================


class TestAIAssistantCollection:
    """Kiểm tra dataclass AIAssistantCollection."""

    def test_add_and_get_policy(self) -> None:
        collection = AIAssistantCollection()
        policy = ReviewPolicy(id="p1", name="Test")
        collection.add_review_policy(policy)
        assert collection.get_review_policy_by_id("p1") is policy
        assert collection.get_review_policy_by_id("nonexistent") is None

    def test_add_and_get_template(self) -> None:
        collection = AIAssistantCollection()
        tmpl = PromptTemplate(id="t1", name="Test")
        collection.add_prompt_template(tmpl)
        assert collection.get_template_by_id("t1") is tmpl

    def test_set_config(self) -> None:
        collection = AIAssistantCollection()
        cfg = AIAssistantConfig(id="default")
        collection.set_config(cfg)
        assert collection.config is cfg

    def test_duplicate_policy_raises_error(self) -> None:
        collection = AIAssistantCollection()
        collection.add_review_policy(ReviewPolicy(id="p1"))
        with pytest.raises(MidicoderError):
            collection.add_review_policy(ReviewPolicy(id="p1"))

    def test_duplicate_template_raises_error(self) -> None:
        collection = AIAssistantCollection()
        collection.add_prompt_template(PromptTemplate(id="t1"))
        with pytest.raises(MidicoderError):
            collection.add_prompt_template(PromptTemplate(id="t1"))

    def test_get_policies_by_category(self) -> None:
        collection = AIAssistantCollection()
        collection.add_review_policy(ReviewPolicy(id="p1", category=ReviewCategory.SECURITY))
        collection.add_review_policy(ReviewPolicy(id="p2", category=ReviewCategory.STYLE))
        collection.add_review_policy(ReviewPolicy(id="p3", category=ReviewCategory.SECURITY))

        security = collection.get_policies_by_category(ReviewCategory.SECURITY)
        assert len(security) == 2

    def test_get_templates_by_category(self) -> None:
        collection = AIAssistantCollection()
        collection.add_prompt_template(PromptTemplate(id="t1", category=PromptCategory.CODE_REVIEW))
        collection.add_prompt_template(PromptTemplate(id="t2", category=PromptCategory.TESTING))

        reviews = collection.get_templates_by_category(PromptCategory.CODE_REVIEW)
        assert len(reviews) == 1

    def test_get_enabled_policies(self) -> None:
        collection = AIAssistantCollection()
        collection.add_review_policy(ReviewPolicy(id="p1", enabled=True))
        collection.add_review_policy(ReviewPolicy(id="p2", enabled=False))
        collection.add_review_policy(ReviewPolicy(id="p3", enabled=True))

        enabled = collection.get_enabled_policies()
        assert len(enabled) == 2

    def test_has_duplicate_policies(self) -> None:
        collection = AIAssistantCollection()
        collection.review_policies.append(ReviewPolicy(id="p1"))
        collection.review_policies.append(ReviewPolicy(id="p2"))
        assert collection.has_duplicate_policies() is False

        collection.review_policies.append(ReviewPolicy(id="p1"))
        assert collection.has_duplicate_policies() is True

    def test_has_duplicate_templates(self) -> None:
        collection = AIAssistantCollection()
        collection.prompt_templates.append(PromptTemplate(id="t1"))
        collection.prompt_templates.append(PromptTemplate(id="t1"))
        assert collection.has_duplicate_templates() is True

    def test_to_dict(self) -> None:
        collection = AIAssistantCollection()
        collection.add_review_policy(ReviewPolicy(id="p1", name="Test", severity=ReviewSeverity.ERROR, category=ReviewCategory.SECURITY))
        collection.add_prompt_template(PromptTemplate(id="t1", name="Tmpl", category=PromptCategory.CODE_REVIEW, content="test {{code}}"))
        collection.set_config(AIAssistantConfig(id="default", enabled=True))

        d = collection.to_dict()
        assert "review_policies" in d
        assert "prompt_templates" in d
        assert "config" in d
        assert len(d["review_policies"]) == 1
        assert d["review_policies"][0]["id"] == "p1"
        assert d["config"]["enabled"] is True

    def test_from_dict(self) -> None:
        data: dict[str, Any] = {
            "review_policies": [
                {
                    "id": "p1",
                    "name": "Test",
                    "description": "Desc",
                    "severity": "error",
                    "category": "security",
                    "enabled": True,
                    "prompt_template_ref": "t1",
                }
            ],
            "prompt_templates": [
                {
                    "id": "t1",
                    "name": "Tmpl",
                    "category": "code_review",
                    "content": "test {{code}}",
                    "variables": {"code": "Source"},
                    "version": "1.0.0",
                    "metadata": {},
                }
            ],
            "config": {
                "id": "default",
                "enabled": True,
                "default_model": "gpt-4",
                "max_tokens": 4096,
                "temperature": 0.7,
                "timeout_seconds": 30,
                "review_policies_enabled": ["p1"],
                "suggestions_enabled": True,
                "prompt_templates_path": "",
            },
        }
        collection = AIAssistantCollection.from_dict(data)
        assert len(collection.review_policies) == 1
        assert len(collection.prompt_templates) == 1
        assert collection.config is not None
        assert collection.review_policies[0].severity == ReviewSeverity.ERROR
        assert collection.prompt_templates[0].category == PromptCategory.CODE_REVIEW

    def test_roundtrip_serialization(self) -> None:
        original = AIAssistantCollection()
        original.add_review_policy(ReviewPolicy(id="p1", category=ReviewCategory.SECURITY, severity=ReviewSeverity.ERROR))
        original.add_prompt_template(PromptTemplate(id="t1", category=PromptCategory.TESTING))
        original.set_config(AIAssistantConfig(id="prod", enabled=False))

        d = original.to_dict()
        restored = AIAssistantCollection.from_dict(d)

        assert len(restored.review_policies) == 1
        assert len(restored.prompt_templates) == 1
        assert restored.config is not None
        assert restored.config.enabled is False
        assert restored.review_policies[0].category == ReviewCategory.SECURITY

    def test_empty_collection(self) -> None:
        collection = AIAssistantCollection()
        assert len(collection.review_policies) == 0
        assert len(collection.prompt_templates) == 0
        assert collection.config is None
        assert collection.has_duplicate_policies() is False
        assert collection.has_duplicate_templates() is False
