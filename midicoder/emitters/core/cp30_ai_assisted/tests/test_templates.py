# coding: utf-8
"""
Test cases cho CP30 — kiểm tra template rendering.

Kiểm tra:
- Templates tồn tại và render được với context hợp lệ
- Template context có các keys cần thiết
"""

import pytest

from midicoder.emitters.core.cp30_ai_assisted.parser import AIAssistantParser
from midicoder.emitters.core.cp30_ai_assisted.recipes import auto_generate_ai_assistant_from_mir


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
