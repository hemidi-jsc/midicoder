# coding: utf-8
"""
Mô-đun models cho AI-Assisted Development Generator (CP30).

Định nghĩa các dataclass biểu diễn:
- ReviewSeverity: Enum mức độ nghiêm trọng của finding
- ReviewCategory: Enum loại review policy
- SuggestionType: Enum loại suggestion
- PromptCategory: Enum loại prompt template
- ReviewPolicy: Một policy cho AI code review
- ReviewResult: Kết quả từ 1 lần chạy AI review
- SuggestionContext: Bối cảnh cho AI suggestion
- SuggestionResult: Kết quả suggestion từ AI
- PromptTemplate: Template cho prompt AI với variables
- AIAssistantConfig: Cấu hình tổng thể cho AI assistant
- AIAssistantCollection: Collection chứa policies, templates, config

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# ===========================================================================
# Enums
# ===========================================================================


class ReviewSeverity(str, Enum):
    """Enum mức độ nghiêm trọng của finding."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

    __test__ = False  # Prevent pytest collection


class ReviewCategory(str, Enum):
    """Enum loại review policy."""
    SECURITY = "security"
    PERFORMANCE = "performance"
    STYLE = "style"
    CORRECTNESS = "correctness"

    __test__ = False  # Prevent pytest collection


class SuggestionType(str, Enum):
    """Enum loại suggestion."""
    COMPLETION = "completion"
    REFACTOR = "refactor"
    FIX = "fix"
    EXPLAIN = "explain"

    __test__ = False  # Prevent pytest collection


class PromptCategory(str, Enum):
    """Enum loại prompt template."""
    CODE_REVIEW = "code_review"
    CODE_SUGGESTION = "code_suggestion"
    CODE_GENERATION = "code_generation"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    CUSTOM = "custom"

    __test__ = False  # Prevent pytest collection


# ===========================================================================
# ReviewPolicy
# ===========================================================================


@dataclass
class ReviewPolicy:
    """
    Policy cho AI code review — định nghĩa quy tắc, mức độ và template.

    Attributes:
        id: Định danh duy nhất của policy
        name: Tên mô tả policy
        description: Mô tả chi tiết policy
        severity: Mức độ nghiêm trọng (error/warning/info)
        category: Loại policy (security/performance/style/correctness)
        enabled: Policy có được kích hoạt không
        prompt_template_ref: Tham chiếu đến prompt template ID
    """
    __test__ = False  # Prevent pytest collection

    id: str
    name: str = ""
    description: str = ""
    severity: ReviewSeverity = ReviewSeverity.INFO
    category: ReviewCategory = ReviewCategory.STYLE
    enabled: bool = True
    prompt_template_ref: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate policy sau khi khởi tạo."""
        if not self.id or not self.id.strip():
            EM.raise_error(ErrorCode.CP30_EMPTY_REVIEW_POLICY_ID, field="policy.id")
        if not self.severity:  # pragma: no cover
            EM.raise_error(ErrorCode.CP30_INVALID_SEVERITY, field="policy.severity")
        if not self.category:  # pragma: no cover
            EM.raise_error(ErrorCode.CP30_INVALID_CATEGORY, field="policy.category")


# ===========================================================================
# ReviewResult
# ===========================================================================


@dataclass
class ReviewResult:
    """
    Kết quả từ 1 lần chạy AI review.

    Attributes:
        finding_id: Định danh duy nhất của finding
        policy_id: ID của policy tạo ra finding này
        severity: Mức độ nghiêm trọng
        message: Mô tả chi tiết vấn đề
        line_range: Khoảng dòng code bị ảnh hưởng [start, end]
        suggestion: Gợi ý khắc phục
    """
    __test__ = False  # Prevent pytest collection

    finding_id: str
    policy_id: str
    severity: ReviewSeverity
    message: str
    line_range: list[int] = field(default_factory=list)
    suggestion: str = ""

    def __post_init__(self) -> None:
        """Validate review result sau khi khởi tạo."""
        if not self.finding_id or not self.finding_id.strip():
            EM.raise_error(ErrorCode.CP30_EMPTY_REVIEW_RESULT_ID, field="result.finding_id")


# ===========================================================================
# SuggestionContext
# ===========================================================================


@dataclass
class SuggestionContext:
    """
    Bối cảnh cho AI suggestion.

    Attributes:
        file_path: Đường dẫn file đang được phân tích
        language: Ngôn ngữ lập trình (python, typescript, ...)
        code_snippet: Đoạn code hiện tại
        cursor_position: Vị trí con trỏ (optional)
        intent: Ý định của developer (optional)
    """
    __test__ = False  # Prevent pytest collection

    file_path: str = ""
    language: str = "python"
    code_snippet: str = ""
    cursor_position: Optional[int] = None
    intent: str = ""


# ===========================================================================
# SuggestionResult
# ===========================================================================


@dataclass
class SuggestionResult:
    """
    Kết quả suggestion từ AI.

    Attributes:
        id: Định danh duy nhất của suggestion
        suggestion_type: Loại suggestion (completion/refactor/fix/explain)
        content: Nội dung suggestion
        confidence: Mức độ tin cậy (0.0 - 1.0)
        explanation: Giải thích lý do suggestion
    """
    __test__ = False  # Prevent pytest collection

    id: str
    suggestion_type: SuggestionType = SuggestionType.COMPLETION
    content: str = ""
    confidence: float = 0.0
    explanation: str = ""

    def __post_init__(self) -> None:
        """Validate suggestion result sau khi khởi tạo."""
        if not self.id or not self.id.strip():
            EM.raise_error(ErrorCode.CP30_EMPTY_SUGGESTION_RESULT_ID, field="result.id")
        if not self.suggestion_type:  # pragma: no cover
            EM.raise_error(ErrorCode.CP30_INVALID_SUGGESTION_TYPE, field="result.suggestion_type")


# ===========================================================================
# PromptTemplate
# ===========================================================================


@dataclass
class PromptTemplate:
    """
    Template cho prompt AI với variables.

    Attributes:
        id: Định danh duy nhất của template
        name: Tên mô tả template
        category: Loại template (code_review, code_suggestion, ...)
        content: Nội dung template với {{variable}} placeholders
        variables: Danh sách các variable được định nghĩa
        version: Version của template (semver)
        metadata: Metadata bổ sung
    """
    __test__ = False  # Prevent pytest collection

    id: str
    name: str = ""
    category: PromptCategory = PromptCategory.CUSTOM
    content: str = ""
    variables: dict[str, str] = field(default_factory=dict)
    version: str = "1.0.0"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate prompt template sau khi khởi tạo."""
        if not self.id or not self.id.strip():
            EM.raise_error(ErrorCode.CP30_EMPTY_TEMPLATE_ID, field="template.id")
        if not self.category:  # pragma: no cover
            EM.raise_error(ErrorCode.CP30_INVALID_PROMPT_CATEGORY, field="template.category")


# ===========================================================================
# AIAssistantConfig
# ===========================================================================


@dataclass
class AIAssistantConfig:
    """
    Cấu hình tổng thể cho AI assistant.

    Attributes:
        id: Định danh config profile
        enabled: Có kích hoạt AI assistant không
        default_model: Model mặc định (string reference)
        max_tokens: Số token tối đa cho mỗi request
        temperature: Temperature cho LLM generation (0.0 - 2.0)
        timeout_seconds: Thời gian chờ tối đa (giây)
        review_policies_enabled: Danh sách policy IDs được kích hoạt
        suggestions_enabled: Có kích hoạt suggestions không
        prompt_templates_path: Đường dẫn đến thư mục templates
    """
    __test__ = False  # Prevent pytest collection

    id: str = "default"
    enabled: bool = True
    default_model: str = "gpt-4"
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout_seconds: int = 30
    review_policies_enabled: list[str] = field(default_factory=list)
    suggestions_enabled: bool = True
    prompt_templates_path: str = ""

    def __post_init__(self) -> None:
        """Validate config sau khi khởi tạo."""
        if not self.id or not self.id.strip():
            EM.raise_error(ErrorCode.CP30_EMPTY_CONFIG_ID, field="config.id")


# ===========================================================================
# AIAssistantCollection
# ===========================================================================


@dataclass
class AIAssistantCollection:
    """
    Collection chứa tất cả review policies, prompt templates, và config.

    Dùng làm output của AIAssistantParser và input cho template renderer.

    Attributes:
        review_policies: Danh sách review policies
        prompt_templates: Danh sách prompt templates
        config: Cấu hình AI assistant
    """
    __test__ = False  # Prevent pytest collection

    review_policies: list[ReviewPolicy] = field(default_factory=list)
    prompt_templates: list[PromptTemplate] = field(default_factory=list)
    config: Optional[AIAssistantConfig] = None

    def add_review_policy(self, policy: ReviewPolicy) -> None:
        """Thêm review policy vào collection."""
        if self.get_review_policy_by_id(policy.id):
            EM.raise_error(
                ErrorCode.CP30_DUPLICATE_REVIEW_POLICY_ID,
                id=policy.id,
                reason="Duplicate review policy ID"
            )
        self.review_policies.append(policy)

    def add_prompt_template(self, template: PromptTemplate) -> None:
        """Thêm prompt template vào collection."""
        if self.get_template_by_id(template.id):
            EM.raise_error(
                ErrorCode.CP30_DUPLICATE_TEMPLATE_ID,
                id=template.id,
                reason="Duplicate template ID"
            )
        self.prompt_templates.append(template)

    def set_config(self, config: AIAssistantConfig) -> None:
        """Đặt cấu hình AI assistant."""
        self.config = config

    def get_review_policy_by_id(self, policy_id: str) -> Optional[ReviewPolicy]:
        """Tìm review policy theo ID."""
        for policy in self.review_policies:
            if policy.id == policy_id:
                return policy
        return None

    def get_template_by_id(self, template_id: str) -> Optional[PromptTemplate]:
        """Tìm prompt template theo ID."""
        for template in self.prompt_templates:
            if template.id == template_id:
                return template
        return None

    def get_policies_by_category(self, category: ReviewCategory) -> list[ReviewPolicy]:
        """Lấy danh sách policies theo category."""
        return [p for p in self.review_policies if p.category == category]

    def get_templates_by_category(self, category: PromptCategory) -> list[PromptTemplate]:
        """Lấy danh sách templates theo category."""
        return [t for t in self.prompt_templates if t.category == category]

    def get_enabled_policies(self) -> list[ReviewPolicy]:
        """Lấy danh sách policies đang enabled."""
        return [p for p in self.review_policies if p.enabled]

    def has_duplicate_policies(self) -> bool:
        """Kiểm tra có policy ID trùng lặp không."""
        seen: set[str] = set()
        for policy in self.review_policies:
            if policy.id in seen:
                return True
            seen.add(policy.id)
        return False

    def has_duplicate_templates(self) -> bool:
        """Kiểm tra có template ID trùng lặp không."""
        seen: set[str] = set()
        for template in self.prompt_templates:
            if template.id in seen:
                return True
            seen.add(template.id)
        return False

    def to_dict(self) -> dict[str, Any]:
        """Chuyển collection sang dict format."""
        return {
            "review_policies": [
                {
                    "id": p.id,
                    "name": p.name,
                    "description": p.description,
                    "severity": p.severity.value,
                    "category": p.category.value,
                    "enabled": p.enabled,
                    "prompt_template_ref": p.prompt_template_ref,
                }
                for p in self.review_policies
            ],
            "prompt_templates": [
                {
                    "id": t.id,
                    "name": t.name,
                    "category": t.category.value,
                    "content": t.content,
                    "variables": t.variables,
                    "version": t.version,
                    "metadata": t.metadata,
                }
                for t in self.prompt_templates
            ],
            "config": {
                "id": self.config.id,
                "enabled": self.config.enabled,
                "default_model": self.config.default_model,
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature,
                "timeout_seconds": self.config.timeout_seconds,
                "review_policies_enabled": self.config.review_policies_enabled,
                "suggestions_enabled": self.config.suggestions_enabled,
                "prompt_templates_path": self.config.prompt_templates_path,
            } if self.config else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AIAssistantCollection":
        """Tạo AIAssistantCollection từ dict."""
        collection = cls()

        for policy_data in data.get("review_policies", []):
            policy = ReviewPolicy(
                id=policy_data["id"],
                name=policy_data.get("name", ""),
                description=policy_data.get("description", ""),
                severity=ReviewSeverity(policy_data.get("severity", "info")),
                category=ReviewCategory(policy_data.get("category", "style")),
                enabled=policy_data.get("enabled", True),
                prompt_template_ref=policy_data.get("prompt_template_ref"),
            )
            collection.add_review_policy(policy)

        for template_data in data.get("prompt_templates", []):
            template = PromptTemplate(
                id=template_data["id"],
                name=template_data.get("name", ""),
                category=PromptCategory(template_data.get("category", "custom")),
                content=template_data.get("content", ""),
                variables=template_data.get("variables", {}),
                version=template_data.get("version", "1.0.0"),
                metadata=template_data.get("metadata", {}),
            )
            collection.add_prompt_template(template)

        config_data = data.get("config")
        if config_data:
            config = AIAssistantConfig(
                id=config_data.get("id", "default"),
                enabled=config_data.get("enabled", True),
                default_model=config_data.get("default_model", "gpt-4"),
                max_tokens=config_data.get("max_tokens", 4096),
                temperature=config_data.get("temperature", 0.7),
                timeout_seconds=config_data.get("timeout_seconds", 30),
                review_policies_enabled=config_data.get("review_policies_enabled", []),
                suggestions_enabled=config_data.get("suggestions_enabled", True),
                prompt_templates_path=config_data.get("prompt_templates_path", ""),
            )
            collection.set_config(config)

        return collection
