# coding: utf-8
"""
CP30: AI-Assisted Development Generator.

Cung cấp:
- models: ReviewSeverity, ReviewCategory, SuggestionType, PromptCategory,
          ReviewPolicy, ReviewResult, SuggestionContext, SuggestionResult,
          PromptTemplate, AIAssistantConfig, AIAssistantCollection
- parser: AIAssistantParser
- recipes: auto_generate_ai_assistant_from_mir, generate_default_review_policies,
           generate_default_prompt_templates, generate_default_config

Author: Midicoder Team
Version: 1.0.0
"""

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
from midicoder.emitters.core.cp30_ai_assisted.parser import AIAssistantParser
from midicoder.emitters.core.cp30_ai_assisted.recipes import (
    auto_generate_ai_assistant_from_mir,
    generate_default_config,
    generate_default_prompt_templates,
    generate_default_review_policies,
)

__all__ = [
    "AIAssistantCollection",
    "AIAssistantConfig",
    "AIAssistantParser",
    "auto_generate_ai_assistant_from_mir",
    "generate_default_config",
    "generate_default_prompt_templates",
    "generate_default_review_policies",
    "PromptCategory",
    "PromptTemplate",
    "ReviewCategory",
    "ReviewPolicy",
    "ReviewResult",
    "ReviewSeverity",
    "SuggestionContext",
    "SuggestionResult",
    "SuggestionType",
]
