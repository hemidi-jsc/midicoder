# coding: utf-8
"""
Mô-đun parser cho AI-Assisted Development Generator (CP30).

Parse DSL AI assistant nodes từ MIR metadata / Contract YAML thành AIAssistantCollection.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from typing import Any

import yaml

from midicoder.packs.cp_full_ai_assisted.models import (
    AIAssistantCollection,
    AIAssistantConfig,
    PromptCategory,
    PromptTemplate,
    ReviewCategory,
    ReviewPolicy,
    ReviewSeverity,
)
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


class AIAssistantParser:
    """
    Parser cho DSL AI assistant nodes.

    Parse YAML DSL hoặc dict metadata thành AIAssistantCollection.

    Ví dụ DSL:
        review_policies:
          - id: security_scan
            name: Security Scan
            severity: error
            category: security
            enabled: true
            prompt_template_ref: tmpl_code_review
        prompt_templates:
          - id: tmpl_code_review
            name: Code Review
            category: code_review
            content: "Review this code: {{code}}"
            variables: {code: "Source code snippet"}
        config:
          enabled: true
          default_model: gpt-4
          max_tokens: 4096
    """

    def parse(self, raw: str | dict[str, Any]) -> AIAssistantCollection:
        """
        Parse YAML string hoặc dict thành AIAssistantCollection.

        Args:
            raw: YAML string hoặc dict chứa AI assistant definitions

        Returns:
            AIAssistantCollection chứa review_policies, prompt_templates, config

        Raises:
            MidicoderError: Nếu parse thất bại
        """
        if isinstance(raw, str):
            if not raw or not raw.strip():
                return AIAssistantCollection()
            try:
                data = yaml.safe_load(raw)
            except yaml.YAMLError as e:
                EM.raise_error(
                    ErrorCode.MDC-F18_DSL_PARSE_ERROR,
                    message=f"Lỗi parse YAML AI assistant nodes: {e}",
                    error=str(e),
                )
            if data is None:
                return AIAssistantCollection()
        elif isinstance(raw, dict):
            data = raw
        else:
            return AIAssistantCollection()

        if not isinstance(data, dict):
            EM.raise_error(
                ErrorCode.MDC-F18_DSL_PARSE_ERROR,
                message="DSL AI assistant nodes phải là YAML mapping",
            )

        return self._parse_from_dict(data)

    def parse_from_metadata(self, metadata: dict[str, Any]) -> AIAssistantCollection:
        """
        Parse từ MIR metadata dict.

        MIR metadata có thể chứa các key 'review_policies', 'prompt_templates', 'config'.

        Args:
            metadata: MIR metadata dict

        Returns:
            AIAssistantCollection
        """
        if not metadata:
            return AIAssistantCollection()

        collection = AIAssistantCollection()

        # Parse review policies
        policies_data = metadata.get("review_policies", [])
        if isinstance(policies_data, list):
            for policy_data in policies_data:
                if isinstance(policy_data, dict):
                    policy = self._parse_policy(policy_data)
                    collection.add_review_policy(policy)
        else:  # pragma: no cover
            pass

        # Parse prompt templates
        templates_data = metadata.get("prompt_templates", [])
        if isinstance(templates_data, list):
            for template_data in templates_data:
                if isinstance(template_data, dict):
                    template = self._parse_template(template_data)
                    collection.add_prompt_template(template)
        else:  # pragma: no cover
            pass

        # Parse config
        config_data = metadata.get("config")
        if isinstance(config_data, dict):
            config = self._parse_config(config_data)
            collection.set_config(config)
        else:  # pragma: no cover
            pass

        return collection

    def _parse_from_dict(self, data: dict[str, Any]) -> AIAssistantCollection:
        """Parse từ dict đã load."""
        collection = AIAssistantCollection()

        # Parse review policies
        policies_data = data.get("review_policies", [])
        if isinstance(policies_data, list):
            for policy_data in policies_data:
                if isinstance(policy_data, dict):
                    policy = self._parse_policy(policy_data)
                    collection.add_review_policy(policy)
        else:  # pragma: no cover
            pass

        # Parse prompt templates
        templates_data = data.get("prompt_templates", [])
        if isinstance(templates_data, list):
            for template_data in templates_data:
                if isinstance(template_data, dict):
                    template = self._parse_template(template_data)
                    collection.add_prompt_template(template)
        else:  # pragma: no cover
            pass

        # Parse config
        config_data = data.get("config")
        if isinstance(config_data, dict):
            config = self._parse_config(config_data)
            collection.set_config(config)
        else:  # pragma: no cover
            pass

        return collection

    def _parse_severity(self, value: str) -> ReviewSeverity:
        """Parse severity string thành enum."""
        try:
            return ReviewSeverity(value)
        except ValueError:
            EM.raise_error(
                ErrorCode.MDC-F18_INVALID_SEVERITY,
                severity=value,
                valid=[s.value for s in ReviewSeverity],
            )

    def _parse_review_category(self, value: str) -> ReviewCategory:
        """Parse category string thành enum."""
        try:
            return ReviewCategory(value)
        except ValueError:
            EM.raise_error(
                ErrorCode.MDC-F18_INVALID_CATEGORY,
                category=value,
                valid=[c.value for c in ReviewCategory],
            )

    def _parse_prompt_category(self, value: str) -> PromptCategory:
        """Parse prompt category string thành enum."""
        try:
            return PromptCategory(value)
        except ValueError:
            EM.raise_error(
                ErrorCode.MDC-F18_INVALID_PROMPT_CATEGORY,
                category=value,
                valid=[c.value for c in PromptCategory],
            )

    def _parse_policy(self, data: dict[str, Any]) -> ReviewPolicy:
        """Parse review policy definition."""
        return ReviewPolicy(
            id=data.get("id", ""),
            name=data.get("name", data.get("id", "")),
            description=data.get("description", ""),
            severity=self._parse_severity(data.get("severity", "info")),
            category=self._parse_review_category(data.get("category", "style")),
            enabled=data.get("enabled", True),
            prompt_template_ref=data.get("prompt_template_ref"),
        )

    def _parse_template(self, data: dict[str, Any]) -> PromptTemplate:
        """Parse prompt template definition."""
        return PromptTemplate(
            id=data.get("id", ""),
            name=data.get("name", data.get("id", "")),
            category=self._parse_prompt_category(data.get("category", "custom")),
            content=data.get("content", ""),
            variables=data.get("variables", {}),
            version=data.get("version", "1.0.0"),
            metadata=data.get("metadata", {}),
        )

    def _parse_config(self, data: dict[str, Any]) -> AIAssistantConfig:
        """Parse AI assistant config definition."""
        return AIAssistantConfig(
            id=data.get("id", "default"),
            enabled=data.get("enabled", True),
            default_model=data.get("default_model", "gpt-4"),
            max_tokens=data.get("max_tokens", 4096),
            temperature=data.get("temperature", 0.7),
            timeout_seconds=data.get("timeout_seconds", 30),
            review_policies_enabled=data.get("review_policies_enabled", []),
            suggestions_enabled=data.get("suggestions_enabled", True),
            prompt_templates_path=data.get("prompt_templates_path", ""),
        )
