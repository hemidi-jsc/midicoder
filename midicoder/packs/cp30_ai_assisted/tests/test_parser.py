# coding: utf-8
"""
Test cases cho CP30 AIAssistantParser.

Kiểm tra:
- Parse YAML string thành AIAssistantCollection
- Parse dict metadata
- Parse từ MIR metadata
- Error handling: invalid YAML, invalid severity, invalid category
- Edge cases: empty input, severity/category parsing
"""

import pytest

from midicoder.packs.cp30_ai_assisted.models import (
    AIAssistantCollection,
    PromptCategory,
    ReviewCategory,
    ReviewSeverity,
)
from midicoder.packs.cp30_ai_assisted.parser import AIAssistantParser
from midicoder.errors import ErrorCode, MidicoderError


class TestAIAssistantParser:
    """Test AIAssistantParser.parse() method."""

    def setup_method(self):
        self.parser = AIAssistantParser()

    def test_parse_yaml_string_with_policies(self):
        """Kiểm tra parse YAML string có review policies."""
        yaml_str = """
review_policies:
  - id: security_scan
    name: Security Scan
    severity: error
    category: security
    enabled: true
    prompt_template_ref: tmpl_security
"""
        result = self.parser.parse(yaml_str)
        assert isinstance(result, AIAssistantCollection)
        assert len(result.review_policies) == 1
        assert result.review_policies[0].id == "security_scan"
        assert result.review_policies[0].severity == ReviewSeverity.ERROR
        assert result.review_policies[0].category == ReviewCategory.SECURITY

    def test_parse_dict_with_all_sections(self):
        """Kiểm tra parse dict có tất cả sections."""
        data = {
            "review_policies": [
                {"id": "p1", "severity": "warning", "category": "performance", "enabled": True}
            ],
            "prompt_templates": [
                {"id": "t1", "category": "code_review", "content": "Review {{code}}"}
            ],
            "config": {
                "id": "default",
                "enabled": True,
                "default_model": "gpt-4",
                "max_tokens": 4096,
            },
        }
        result = self.parser.parse(data)
        assert len(result.review_policies) == 1
        assert len(result.prompt_templates) == 1
        assert result.config is not None
        assert result.config.max_tokens == 4096

    def test_parse_empty_string_returns_empty_collection(self):
        """Kiểm tra parse string rỗng trả về collection rỗng."""
        result = self.parser.parse("")
        assert isinstance(result, AIAssistantCollection)
        assert len(result.review_policies) == 0
        assert len(result.prompt_templates) == 0
        assert result.config is None

    def test_parse_empty_dict_returns_empty_collection(self):
        """Kiểm tra parse dict rỗng trả về collection rỗng."""
        result = self.parser.parse({})
        assert isinstance(result, AIAssistantCollection)
        assert len(result.review_policies) == 0
        assert result.config is None

    def test_parse_invalid_yaml_raises_error(self):
        """Kiểm tra parse YAML không hợp lệ throw MidicoderError."""
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse("invalid: [yaml: }")
        assert exc_info.value.code == ErrorCode.CP30_DSL_PARSE_ERROR

    def test_parse_templates_section(self):
        """Kiểm tra parse chỉ section prompt templates."""
        yaml_str = """
prompt_templates:
  - id: tmpl_review
    name: Code Review
    category: code_review
    content: "Review this code: {{code}}"
    variables:
      code: Source code snippet
    version: 1.0.0
  - id: tmpl_test
    name: Test Generation
    category: testing
    content: "Generate tests for: {{code}}"
"""
        result = self.parser.parse(yaml_str)
        assert len(result.prompt_templates) == 2
        assert result.prompt_templates[0].id == "tmpl_review"
        assert result.prompt_templates[0].category == PromptCategory.CODE_REVIEW
        assert "code" in result.prompt_templates[0].variables

    def test_parse_config_section(self):
        """Kiểm tra parse section config."""
        yaml_str = """
config:
  id: production
  enabled: true
  default_model: claude-3
  max_tokens: 8192
  temperature: 0.5
  timeout_seconds: 60
  suggestions_enabled: true
"""
        result = self.parser.parse(yaml_str)
        assert result.config is not None
        assert result.config.id == "production"
        assert result.config.default_model == "claude-3"
        assert result.config.max_tokens == 8192
        assert result.config.temperature == 0.5


class TestAIAssistantParserMetadata:
    """Test AIAssistantParser.parse_from_metadata() method."""

    def setup_method(self):
        self.parser = AIAssistantParser()

    def test_parse_from_metadata_with_all_sections(self):
        """Kiểm tra parse từ MIR metadata đầy đủ."""
        metadata = {
            "review_policies": [
                {"id": "p1", "name": "Test Policy", "severity": "error", "category": "security"}
            ],
            "prompt_templates": [
                {"id": "t1", "name": "Test Template", "category": "code_review", "content": "{{code}}"}
            ],
            "config": {"id": "default", "enabled": True},
        }
        result = self.parser.parse_from_metadata(metadata)
        assert isinstance(result, AIAssistantCollection)
        assert len(result.review_policies) == 1
        assert len(result.prompt_templates) == 1
        assert result.config is not None

    def test_parse_from_metadata_empty(self):
        """Kiểm tra parse metadata rỗng trả về collection rỗng."""
        result = self.parser.parse_from_metadata({})
        assert isinstance(result, AIAssistantCollection)
        assert len(result.review_policies) == 0
        assert result.config is None

    def test_parse_from_metadata_policies_only(self):
        """Kiểm tra parse metadata chỉ có policies."""
        metadata = {
            "review_policies": [
                {"id": "p1", "severity": "info", "category": "style"},
                {"id": "p2", "severity": "warning", "category": "correctness"},
            ]
        }
        result = self.parser.parse_from_metadata(metadata)
        assert len(result.review_policies) == 2
        assert result.review_policies[0].severity == ReviewSeverity.INFO
        assert result.review_policies[1].category == ReviewCategory.CORRECTNESS


class TestAIAssistantParserSeverity:
    """Test severity và category parsing."""

    def setup_method(self):
        self.parser = AIAssistantParser()

    def test_parse_all_severity_levels(self):
        """Kiểm tra parse tất cả severity levels."""
        yaml_str = """
review_policies:
  - id: p_error
    severity: error
    category: security
  - id: p_warning
    severity: warning
    category: performance
  - id: p_info
    severity: info
    category: style
"""
        result = self.parser.parse(yaml_str)
        assert len(result.review_policies) == 3
        assert result.review_policies[0].severity == ReviewSeverity.ERROR
        assert result.review_policies[1].severity == ReviewSeverity.WARNING
        assert result.review_policies[2].severity == ReviewSeverity.INFO

    def test_parse_all_review_categories(self):
        """Kiểm tra parse tất cả review categories."""
        yaml_str = """
review_policies:
  - id: p_sec
    severity: error
    category: security
  - id: p_perf
    severity: warning
    category: performance
  - id: p_style
    severity: info
    category: style
  - id: p_corr
    severity: warning
    category: correctness
"""
        result = self.parser.parse(yaml_str)
        assert len(result.review_policies) == 4
        assert result.review_policies[0].category == ReviewCategory.SECURITY
        assert result.review_policies[1].category == ReviewCategory.PERFORMANCE
        assert result.review_policies[2].category == ReviewCategory.STYLE
        assert result.review_policies[3].category == ReviewCategory.CORRECTNESS

    def test_parse_all_prompt_categories(self):
        """Kiểm tra parse tất cả prompt categories."""
        yaml_str = """
prompt_templates:
  - id: t1
    category: code_review
    content: test
  - id: t2
    category: code_suggestion
    content: test
  - id: t3
    category: code_generation
    content: test
  - id: t4
    category: documentation
    content: test
  - id: t5
    category: testing
    content: test
  - id: t6
    category: custom
    content: test
"""
        result = self.parser.parse(yaml_str)
        assert len(result.prompt_templates) == 6
        assert result.prompt_templates[0].category == PromptCategory.CODE_REVIEW
        assert result.prompt_templates[3].category == PromptCategory.DOCUMENTATION
        assert result.prompt_templates[5].category == PromptCategory.CUSTOM

    def test_parse_non_string_non_dict_returns_empty(self):
        """Kiểm tra parse input không phải string/dict trả về collection rỗng."""
        result = self.parser.parse([])
        assert isinstance(result, AIAssistantCollection)
        assert len(result.review_policies) == 0

    def test_parse_yaml_resolving_to_none_returns_empty(self):
        """Kiểm tra parse YAML string giải ra None trả về collection rỗng."""
        result = self.parser.parse("null")
        assert isinstance(result, AIAssistantCollection)
        assert len(result.review_policies) == 0

    def test_parse_yaml_resolving_to_list_raises_error(self):
        """Kiểm tra parse YAML string giải ra list throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse("- item1")
        assert exc_info.value.code == ErrorCode.CP30_DSL_PARSE_ERROR

    def test_parse_from_metadata_with_none(self):
        """Kiểm tra parse metadata None trả về collection rỗng."""
        result = self.parser.parse_from_metadata(None)
        assert isinstance(result, AIAssistantCollection)
        assert len(result.review_policies) == 0

    def test_parse_with_invalid_severity_raises_error(self):
        """Kiểm tra parse severity không hợp lệ throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse({"review_policies": [{"id": "p1", "severity": "invalid", "category": "security"}]})
        assert exc_info.value.code == ErrorCode.CP30_INVALID_SEVERITY

    def test_parse_with_invalid_category_raises_error(self):
        """Kiểm tra parse category không hợp lệ throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse({"review_policies": [{"id": "p1", "severity": "error", "category": "invalid"}]})
        assert exc_info.value.code == ErrorCode.CP30_INVALID_CATEGORY

    def test_parse_with_invalid_prompt_category_raises_error(self):
        """Kiểm tra parse prompt category không hợp lệ throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse({"prompt_templates": [{"id": "t1", "category": "invalid", "content": "test"}]})
        assert exc_info.value.code == ErrorCode.CP30_INVALID_PROMPT_CATEGORY

    def test_parse_from_metadata_skips_non_dict_entries(self):
        """Kiểm tra parse metadata bỏ qua entries không phải dict."""
        metadata = {
            "review_policies": ["not_a_dict", {"id": "p1", "severity": "error", "category": "security"}],
            "prompt_templates": [42, {"id": "t1", "category": "custom", "content": "test"}],
            "config": "not_a_dict",
        }
        result = self.parser.parse_from_metadata(metadata)
        assert len(result.review_policies) == 1
        assert len(result.prompt_templates) == 1
        assert result.config is None

    def test_parse_from_metadata_with_manifests_key(self):
        """Kiểm tra parse metadata có manifests key (backward compat)."""
        metadata = {
            "review_policies": [{"id": "p1", "severity": "error", "category": "security"}],
            "manifests": [{"id": "m1", "name": "Test"}],
        }
        result = self.parser.parse_from_metadata(metadata)
        assert len(result.review_policies) == 1

    def test_parse_yaml_with_manifests_key(self):
        """Kiểm tra parse YAML có manifests key (backward compat)."""
        yaml_str = """
manifests:
  - id: m1
    name: Test
"""
        result = self.parser.parse(yaml_str)
        assert isinstance(result, AIAssistantCollection)

    def test_parse_from_metadata_with_empty_strings(self):
        """Kiểm tra parse metadata có empty string list values."""
        metadata = {
            "review_policies": [],
            "prompt_templates": [],
        }
        result = self.parser.parse_from_metadata(metadata)
        assert len(result.review_policies) == 0
        assert len(result.prompt_templates) == 0

    def test_parse_yaml_with_empty_sections(self):
        """Kiểm tra parse YAML có empty sections."""
        yaml_str = """
review_policies: []
prompt_templates: []
"""
        result = self.parser.parse(yaml_str)
        assert len(result.review_policies) == 0
        assert len(result.prompt_templates) == 0

    def test_parse_config_with_all_fields(self):
        """Kiểm tra parse config đầy đủ fields."""
        yaml_str = """
config:
  id: prod
  enabled: true
  default_model: gpt-4
  max_tokens: 8192
  temperature: 0.3
  timeout_seconds: 60
  review_policies_enabled: [p1, p2]
  suggestions_enabled: true
  prompt_templates_path: /tmp/tmpl
"""
        result = self.parser.parse(yaml_str)
        assert result.config is not None
        assert result.config.id == "prod"
        assert result.config.default_model == "gpt-4"
        assert result.config.max_tokens == 8192
        assert result.config.review_policies_enabled == ["p1", "p2"]
        assert result.config.prompt_templates_path == "/tmp/tmpl"
