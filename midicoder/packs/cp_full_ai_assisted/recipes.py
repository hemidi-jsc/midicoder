# coding: utf-8
"""
Recipe module cho CP30 AI-Assisted Development Generator.

Recipes cung cấp auto-generate review policies, prompt templates, và config
từ MIR metadata (entities, commands) khi không có DSL AI assistant nodes explicit.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from midicoder.packs.cp_full_ai_assisted.models import (
    AIAssistantCollection,
    AIAssistantConfig,
    PromptCategory,
    PromptTemplate,
    ReviewCategory,
    ReviewPolicy,
    ReviewSeverity,
)


# ===========================================================================
# Sinh default review policies
# ===========================================================================


def generate_default_review_policies() -> list[ReviewPolicy]:
    """
    Sinh danh sách các review policies mặc định.

    Tạo ra các policies cho:
    - Security: kiểm tra hardcoded secret, SQL injection, XSS
    - Performance: kiểm tra N+1 query, loop inefficiency
    - Style: kiểm tra naming convention, line length
    - Correctness: kiểm tra type safety, unused import

    Returns:
        Danh sách các ReviewPolicy đã sinh ra
    """
    policies: list[ReviewPolicy] = []

    # Policy 1: Hardcoded secret detection (Security, Error)
    policies.append(ReviewPolicy(
        id="policy_hardcoded_secret",
        name="Hardcoded Secret Detection",
        description="Phát hiện bí mật được hardcode trong mã nguồn (API key, password, token)",
        severity=ReviewSeverity.ERROR,
        category=ReviewCategory.SECURITY,
        enabled=True,
        prompt_template_ref="tmpl_security_review",
    ))

    # Policy 2: SQL injection check (Security, Error)
    policies.append(ReviewPolicy(
        id="policy_sql_injection",
        name="SQL Injection Check",
        description="Phát hiện tiềm năng injection trong truy vấn SQL",
        severity=ReviewSeverity.ERROR,
        category=ReviewCategory.SECURITY,
        enabled=True,
        prompt_template_ref="tmpl_security_review",
    ))

    # Policy 3: Performance anti-pattern (Performance, Warning)
    policies.append(ReviewPolicy(
        id="policy_performance_anti_pattern",
        name="Performance Anti-Pattern",
        description="Phát hiện anti-pattern hiệu suất (N+1 query, vòng lặp không tối ưu)",
        severity=ReviewSeverity.WARNING,
        category=ReviewCategory.PERFORMANCE,
        enabled=True,
        prompt_template_ref="tmpl_performance_review",
    ))

    # Policy 4: Style enforcement (Style, Info)
    policies.append(ReviewPolicy(
        id="policy_style_enforcement",
        name="Style Enforcement",
        description="Kiểm tra tuấn thủ naming convention và code style",
        severity=ReviewSeverity.INFO,
        category=ReviewCategory.STYLE,
        enabled=True,
        prompt_template_ref="tmpl_style_review",
    ))

    # Policy 5: Type safety check (Correctness, Warning)
    policies.append(ReviewPolicy(
        id="policy_type_safety",
        name="Type Safety Check",
        description="Kiểm tra type annotation và type safety",
        severity=ReviewSeverity.WARNING,
        category=ReviewCategory.CORRECTNESS,
        enabled=True,
        prompt_template_ref="tmpl_correctness_review",
    ))

    # Policy 6: Unused import detection (Correctness, Info)
    policies.append(ReviewPolicy(
        id="policy_unused_import",
        name="Unused Import Detection",
        description="Phát hiện import không được sử dụng",
        severity=ReviewSeverity.INFO,
        category=ReviewCategory.CORRECTNESS,
        enabled=True,
        prompt_template_ref="tmpl_correctness_review",
    ))

    return policies


# ===========================================================================
# Sinh default prompt templates
# ===========================================================================


def generate_default_prompt_templates() -> list[PromptTemplate]:
    """
    Sinh danh sách prompt templates mặc định cho các use cases phổ biến.

    Tạo ra templates cho:
    - Code review (security, performance, style, correctness)
    - Code suggestion (completion, refactor, fix)
    - Documentation generation
    - Test generation

    Returns:
        Danh sách các PromptTemplate đã sinh ra
    """
    templates: list[PromptTemplate] = []

    # Template 1: Security review
    templates.append(PromptTemplate(
        id="tmpl_security_review",
        name="Security Code Review",
        category=PromptCategory.CODE_REVIEW,
        content=(
            "Bạn là chuyên gia bảo mật phần mềm. Hãy phân tích đoạn mã sau "
            "và phát hiện các lỗ hổng bảo mật tiềm ẩn như: hardcoded secret, "
            "SQL injection, XSS, CSRF, auth bypass.\n\n"
            "Đoạn mã:\n```\n{{code}}\n```\n\n"
            "Trả về danh sách findings với format:\n"
            "- **Finding**: [mô tả]\n"
            "- **Severity**: [error/warning/info]\n"
            "- **Line**: [dòng bị ảnh hưởng]\n"
            "- **Fix**: [gợi ý khắc phục]"
        ),
        variables={
            "code": "Đoạn mã cần phân tích bảo mật",
        },
        version="1.0.0",
        metadata={"max_tokens": 2048, "temperature": 0.3},
    ))

    # Template 2: Performance review
    templates.append(PromptTemplate(
        id="tmpl_performance_review",
        name="Performance Code Review",
        category=PromptCategory.CODE_REVIEW,
        content=(
            "Bạn là chuyên gia tối ưu hiệu suất phần mềm. Hãy phân tích đoạn mã sau "
            "và phát hiện các anti-pattern hiệu suất như: N+1 query, vòng lặp không tối ưu, "
            "memory leak, blocking I/O.\n\n"
            "Đoạn mã:\n```\n{{code}}\n```\n\n"
            "Trả về danh sách findings với gợi ý cải thiện hiệu suất."
        ),
        variables={
            "code": "Đoạn mã cần phân tích hiệu suất",
        },
        version="1.0.0",
        metadata={"max_tokens": 2048, "temperature": 0.3},
    ))

    # Template 3: Style review
    templates.append(PromptTemplate(
        id="tmpl_style_review",
        name="Style Code Review",
        category=PromptCategory.CODE_REVIEW,
        content=(
            "Bạn là chuyên gia code quality. Hãy phân tích đoạn mã sau "
            "và phát hiện các vấn đề về code style như: naming convention, "
            "line length, function length, magic numbers.\n\n"
            "Đoạn mã:\n```\n{{code}}\n```\n\n"
            "Ngôn ngữ: {{language}}\n\n"
            "Trả về danh sách findings với gợi ý cải thiện code style."
        ),
        variables={
            "code": "Đoạn mã cần phân tích style",
            "language": "Ngôn ngữ lập trình",
        },
        version="1.0.0",
        metadata={"max_tokens": 1024, "temperature": 0.2},
    ))

    # Template 4: Correctness review
    templates.append(PromptTemplate(
        id="tmpl_correctness_review",
        name="Correctness Code Review",
        category=PromptCategory.CODE_REVIEW,
        content=(
            "Bạn là chuyên gia code correctness. Hãy phân tích đoạn mã sau "
            "và phát hiện các vấn đề như: type safety, unused imports, "
            "potential null reference, error handling missing.\n\n"
            "Đoạn mã:\n```\n{{code}}\n```\n\n"
            "Trả về danh sách findings với gợi ý khắc phục."
        ),
        variables={
            "code": "Đoạn mã cần phân tích correctness",
        },
        version="1.0.0",
        metadata={"max_tokens": 2048, "temperature": 0.3},
    ))

    # Template 5: Code completion suggestion
    templates.append(PromptTemplate(
        id="tmpl_code_completion",
        name="Code Completion Suggestion",
        category=PromptCategory.CODE_SUGGESTION,
        content=(
            "Bạn là trợ lý lập trình. Hãy gợi ý code completion cho đoạn mã sau "
            "tại vị trí con trỏ.\n\n"
            "Đoạn mã:\n```\n{{code}}\n```\n\n"
            "Ngôn ngữ: {{language}}\n"
            "Vị trí con trỏ: dòng {{cursor_line}}, cột {{cursor_column}}\n\n"
            "Trả về code completion phù hợp với ngữ cảnh."
        ),
        variables={
            "code": "Đoạn mã hiện tại",
            "language": "Ngôn ngữ lập trình",
            "cursor_line": "Số dòng con trỏ",
            "cursor_column": "Số cột con trỏ",
        },
        version="1.0.0",
        metadata={"max_tokens": 512, "temperature": 0.1},
    ))

    # Template 6: Refactor suggestion
    templates.append(PromptTemplate(
        id="tmpl_refactor_suggestion",
        name="Refactor Suggestion",
        category=PromptCategory.CODE_SUGGESTION,
        content=(
            "Bạn là chuyên gia refactoring. Hãy phân tích đoạn mã sau "
            "và gợi ý các cải tiến về cấu trúc mã, design pattern, clean code.\n\n"
            "Đoạn mã:\n```\n{{code}}\n```\n\n"
            "Ngôn ngữ: {{language}}\n\n"
            "Trả về danh sách gợi ý refactoring với code before/after."
        ),
        variables={
            "code": "Đoạn mã cần refactoring",
            "language": "Ngôn ngữ lập trình",
        },
        version="1.0.0",
        metadata={"max_tokens": 2048, "temperature": 0.4},
    ))

    # Template 7: Documentation generation
    templates.append(PromptTemplate(
        id="tmpl_doc_generation",
        name="Documentation Generation",
        category=PromptCategory.DOCUMENTATION,
        content=(
            "Bạn là chuyên gia viết tài liệu kỹ thuật. Hãy tạo documentation "
            "cho đoạn mã sau dưới dạng docstring/comment.\n\n"
            "Đoạn mã:\n```\n{{code}}\n```\n\n"
            "Ngôn ngữ: {{language}}\n"
            "Format documentation: {{doc_format}}\n\n"
            "Trả về documentation đầy đủ với mô tả tham số, giá trị trả về, và exception."
        ),
        variables={
            "code": "Đoạn mã cần tạo tài liệu",
            "language": "Ngôn ngữ lập trình",
            "doc_format": "Format documentation (Google/NumPy/Sphinx/JSDoc)",
        },
        version="1.0.0",
        metadata={"max_tokens": 1024, "temperature": 0.2},
    ))

    # Template 8: Test generation
    templates.append(PromptTemplate(
        id="tmpl_test_generation",
        name="Test Generation",
        category=PromptCategory.TESTING,
        content=(
            "Bạn là chuyên gia viết test. Hãy tạo unit test cho đoạn mã sau.\n\n"
            "Đoạn mã:\n```\n{{code}}\n```\n\n"
            "Ngôn ngữ: {{language}}\n"
            "Framework test: {{test_framework}}\n\n"
            "Trả về unit test đầy đủ với các trường hợp: success, edge case, error."
        ),
        variables={
            "code": "Đoạn mã cần viết test",
            "language": "Ngôn ngữ lập trình",
            "test_framework": "Framework test (pytest/Jest/JUnit)",
        },
        version="1.0.0",
        metadata={"max_tokens": 2048, "temperature": 0.3},
    ))

    return templates


# ===========================================================================
# Sinh default config
# ===========================================================================


def generate_default_config() -> AIAssistantConfig:
    """
    Sinh cấu hình AI assistant mặc định.

    Returns:
        AIAssistantConfig với các giá trị mặc định
    """
    return AIAssistantConfig(
        id="default",
        enabled=True,
        default_model="gpt-4",
        max_tokens=4096,
        temperature=0.7,
        timeout_seconds=30,
        review_policies_enabled=[
            "policy_hardcoded_secret",
            "policy_sql_injection",
            "policy_performance_anti_pattern",
            "policy_type_safety",
        ],
        suggestions_enabled=True,
        prompt_templates_path="ai_assistant/templates/",
    )


# ===========================================================================
# Master recipe: auto-generate AIAssistantCollection từ MIR metadata
# ===========================================================================


def auto_generate_ai_assistant_from_mir(metadata: dict) -> AIAssistantCollection:
    """
    Auto-generate toàn bộ AIAssistantCollection từ MIR metadata.

    Đây là fallback khi không có DSL AI assistant nodes explicit.
    Hàm này sinh ra:
    - Default review policies (security, performance, style, correctness)
    - Default prompt templates (review, suggestion, doc, test)
    - Default config

    Args:
        metadata: MIR metadata dict, chứa các keys:
            - "entities": list[dict] — danh sách entity metadata
            - "commands": list[dict] — danh sách command metadata

    Returns:
        AIAssistantCollection chứa review_policies, prompt_templates, config
    """
    collection = AIAssistantCollection()

    # Bước 1: sinh các review policies mặc định
    policies = generate_default_review_policies()
    for policy in policies:
        collection.add_review_policy(policy)

    # Bước 2: sinh các prompt templates mặc định
    templates = generate_default_prompt_templates()
    for template in templates:
        collection.add_prompt_template(template)

    # Bước 3: sinh config mặc định
    config = generate_default_config()
    collection.set_config(config)

    return collection


__all__ = [
    "auto_generate_ai_assistant_from_mir",
    "generate_default_review_policies",
    "generate_default_prompt_templates",
    "generate_default_config",
]
