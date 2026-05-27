# coding: utf-8
"""
Test cases cho CP30 AI-Assisted Development Generator recipes.

Kiểm tra:
- auto_generate_ai_assistant_from_mir
- generate_default_review_policies
- generate_default_prompt_templates
- generate_default_config
"""

import pytest

from midicoder.packs.cp30_ai_assisted.recipes import (
    auto_generate_ai_assistant_from_mir,
    generate_default_config,
    generate_default_prompt_templates,
    generate_default_review_policies,
)
from midicoder.packs.cp30_ai_assisted.models import (
    AIAssistantCollection,
    AIAssistantConfig,
    PromptCategory,
    PromptTemplate,
    ReviewCategory,
    ReviewPolicy,
    ReviewSeverity,
)


class TestAutoGenerateAiAssistantFromMir:
    """Test auto_generate_ai_assistant_from_mir (master recipe)."""

    def test_generate_from_empty_metadata_returns_collection(self):
        """Kiểm tra metadata rỗng trả về AIAssistantCollection hợp lệ."""
        collection = auto_generate_ai_assistant_from_mir({})

        assert isinstance(collection, AIAssistantCollection)
        assert len(collection.review_policies) > 0
        assert len(collection.prompt_templates) > 0
        assert collection.config is not None

    def test_generate_has_review_policies(self):
        """Kiểm tra collection có review policies."""
        collection = auto_generate_ai_assistant_from_mir({})

        policy_ids = [p.id for p in collection.review_policies]
        assert "policy_hardcoded_secret" in policy_ids
        assert "policy_sql_injection" in policy_ids
        assert "policy_performance_anti_pattern" in policy_ids
        assert "policy_style_enforcement" in policy_ids
        assert "policy_type_safety" in policy_ids
        assert "policy_unused_import" in policy_ids

    def test_generate_has_prompt_templates(self):
        """Kiểm tra collection có prompt templates."""
        collection = auto_generate_ai_assistant_from_mir({})

        template_ids = [t.id for t in collection.prompt_templates]
        assert "tmpl_security_review" in template_ids
        assert "tmpl_performance_review" in template_ids
        assert "tmpl_code_completion" in template_ids
        assert "tmpl_doc_generation" in template_ids
        assert "tmpl_test_generation" in template_ids

    def test_generate_has_config(self):
        """Kiểm tra collection có config."""
        collection = auto_generate_ai_assistant_from_mir({})
        assert collection.config is not None
        assert collection.config.enabled is True
        assert collection.config.suggestions_enabled is True

    def test_generate_from_metadata_with_entities(self):
        """Kiểm tra metadata có entities sinh ra collection đầy đủ."""
        metadata = {
            "entities": [
                {"id": "User", "fields": [{"name": "email"}]},
            ],
            "commands": [{"id": "CreateUser"}],
        }

        collection = auto_generate_ai_assistant_from_mir(metadata)
        assert isinstance(collection, AIAssistantCollection)
        assert len(collection.review_policies) > 0
        assert len(collection.prompt_templates) > 0


class TestGenerateDefaultReviewPolicies:
    """Test generate_default_review_policies recipe."""

    def test_generate_six_policies(self):
        """Kiểm tra sinh ra 6 review policies mặc định."""
        policies = generate_default_review_policies()
        assert len(policies) == 6

    def test_security_policies_are_error_severity(self):
        """Kiểm tra security policies có severity là error."""
        policies = generate_default_review_policies()
        security_policies = [p for p in policies if p.category == ReviewCategory.SECURITY]
        for policy in security_policies:
            assert policy.severity == ReviewSeverity.ERROR

    def test_performance_policy_is_warning(self):
        """Kiểm tra performance policy có severity là warning."""
        policies = generate_default_review_policies()
        perf = [p for p in policies if p.category == ReviewCategory.PERFORMANCE]
        assert len(perf) == 1
        assert perf[0].severity == ReviewSeverity.WARNING

    def test_style_policy_is_info(self):
        """Kiểm tra style policy có severity là info."""
        policies = generate_default_review_policies()
        style = [p for p in policies if p.category == ReviewCategory.STYLE]
        assert len(style) == 1
        assert style[0].severity == ReviewSeverity.INFO

    def test_all_policies_enabled(self):
        """Kiểm tra tất cả policies đều được enabled."""
        policies = generate_default_review_policies()
        for policy in policies:
            assert policy.enabled is True

    def test_policies_have_template_refs(self):
        """Kiểm tra policies có prompt_template_ref."""
        policies = generate_default_review_policies()
        for policy in policies:
            assert policy.prompt_template_ref is not None

    def test_policy_categories_covered(self):
        """Kiểm tra tất cả categories được cover."""
        policies = generate_default_review_policies()
        categories = {p.category for p in policies}
        assert ReviewCategory.SECURITY in categories
        assert ReviewCategory.PERFORMANCE in categories
        assert ReviewCategory.STYLE in categories
        assert ReviewCategory.CORRECTNESS in categories


class TestGenerateDefaultPromptTemplates:
    """Test generate_default_prompt_templates recipe."""

    def test_generate_eight_templates(self):
        """Kiểm tra sinh ra 8 prompt templates mặc định."""
        templates = generate_default_prompt_templates()
        assert len(templates) == 8

    def test_templates_have_content(self):
        """Kiểm tra templates có content không rỗng."""
        templates = generate_default_prompt_templates()
        for template in templates:
            assert template.content != ""

    def test_templates_have_variables(self):
        """Kiểm tra templates có variables."""
        templates = generate_default_prompt_templates()
        for template in templates:
            assert len(template.variables) > 0

    def test_templates_cover_categories(self):
        """Kiểm tra templates cover nhiều categories."""
        templates = generate_default_prompt_templates()
        categories = {t.category for t in templates}
        assert PromptCategory.CODE_REVIEW in categories
        assert PromptCategory.CODE_SUGGESTION in categories
        assert PromptCategory.DOCUMENTATION in categories
        assert PromptCategory.TESTING in categories

    def test_templates_have_metadata(self):
        """Kiểm tra templates có metadata."""
        templates = generate_default_prompt_templates()
        for template in templates:
            assert "max_tokens" in template.metadata
            assert "temperature" in template.metadata

    def test_security_review_template(self):
        """Kiểm tra security review template."""
        templates = generate_default_prompt_templates()
        security = [t for t in templates if t.id == "tmpl_security_review"]
        assert len(security) == 1
        assert security[0].category == PromptCategory.CODE_REVIEW
        assert "code" in security[0].variables


class TestGenerateDefaultConfig:
    """Test generate_default_config recipe."""

    def test_generate_valid_config(self):
        """Kiểm tra sinh ra config hợp lệ."""
        config = generate_default_config()
        assert isinstance(config, AIAssistantConfig)
        assert config.id == "default"
        assert config.enabled is True
        assert config.suggestions_enabled is True

    def test_config_has_enabled_policies(self):
        """Kiểm tra config có review_policies_enabled."""
        config = generate_default_config()
        assert len(config.review_policies_enabled) > 0
        assert "policy_hardcoded_secret" in config.review_policies_enabled

    def test_config_has_template_path(self):
        """Kiểm tra config có prompt_templates_path."""
        config = generate_default_config()
        assert config.prompt_templates_path == "ai_assistant/templates/"
