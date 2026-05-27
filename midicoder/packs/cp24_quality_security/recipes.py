# coding: utf-8
"""
Recipe module cho CP24 Code Quality & Security Scanner Generator.

Recipes cung cấp auto-generate quality profiles và security configs
khi không có DSL quality nodes explicit.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from midicoder.packs.cp24_quality_security.models import (
    AlertSeverity,
    DataQualityProfile,
    DataQualityRule,
    FormatterType,
    LinterType,
    QualityCheck,
    QualityCollection,
    QualityGateConfig,
    QualityProfile,
    QualityResult,
    QualityThreshold,
    SecurityScanConfig,
    SecurityTool,
    SeverityLevel,
    StackType,
)


# Mapping mặc định
DEFAULT_LINTER: dict[StackType, LinterType] = {
    StackType.FASTAPI: LinterType.RUFF,
    StackType.NESTJS: LinterType.ESLINT,
    StackType.ANGULAR: LinterType.ESLINT,
    StackType.REACT: LinterType.ESLINT,
}

DEFAULT_FORMATTER: dict[StackType, FormatterType] = {
    StackType.FASTAPI: FormatterType.BLACK,
    StackType.NESTJS: FormatterType.PRETTIER,
    StackType.ANGULAR: FormatterType.PRETTIER,
    StackType.REACT: FormatterType.PRETTIER,
}

DEFAULT_SECURITY_TOOLS: dict[StackType, list[SecurityTool]] = {
    StackType.FASTAPI: [SecurityTool.BANDIT, SecurityTool.SAFETY],
    StackType.NESTJS: [SecurityTool.NPM_AUDIT, SecurityTool.ESLINT_SECURITY],
    StackType.ANGULAR: [SecurityTool.ESLINT_SECURITY, SecurityTool.LOCKFILE_LINT],
    StackType.REACT: [SecurityTool.ESLINT_SECURITY, SecurityTool.LOCKFILE_LINT],
}


def generate_default_profiles(stack: StackType) -> QualityProfile:
    """
    Generate quality profile mặc định cho 1 stack.

    Args:
        stack: Stack target

    Returns:
        QualityProfile với cấu hình mặc định
    """
    return QualityProfile(
        name="standard",
        stack=stack,
        linter=DEFAULT_LINTER[stack],
        formatter=DEFAULT_FORMATTER[stack],
        min_score=80,
    )


def generate_strict_profiles(stack: StackType) -> QualityProfile:
    """
    Generate quality profile strict cho 1 stack.

    Args:
        stack: Stack target

    Returns:
        QualityProfile với cấu hình strict
    """
    return QualityProfile(
        name="strict",
        stack=stack,
        linter=DEFAULT_LINTER[stack],
        formatter=DEFAULT_FORMATTER[stack],
        min_score=95,
    )


def generate_security_config(stack: StackType) -> SecurityScanConfig:
    """
    Generate security scan config mặc định cho 1 stack.

    Args:
        stack: Stack target

    Returns:
        SecurityScanConfig với tools mặc định
    """
    return SecurityScanConfig(
        stack=stack,
        tools=list(DEFAULT_SECURITY_TOOLS[stack]),
        fail_on_severity=SeverityLevel.HIGH,
    )


def auto_generate_quality_collection(
    stacks: list[StackType] | None = None,
    profile_name: str = "standard",
    min_score: int = 80,
) -> QualityCollection:
    """
    Auto-generate toàn bộ quality collection cho các stacks được chỉ định.

    Đây là fallback khi không có DSL quality nodes explicit.

    Args:
        stacks: Danh sách stacks (default: tất cả 4 stacks)
        profile_name: Tên profile ("standard", "strict", "minimal")
        min_score: Score tối thiểu

    Returns:
        QualityCollection chứa profiles, security configs, gate config cho tất cả stacks
    """
    if stacks is None:
        stacks = list(StackType)

    collection = QualityCollection()

    for stack in stacks:
        # Generate quality profile
        profile = QualityProfile(
            name=profile_name,
            stack=stack,
            linter=DEFAULT_LINTER[stack],
            formatter=DEFAULT_FORMATTER[stack],
            min_score=min_score,
        )
        collection.add_profile(profile)

        # Generate security config
        sec_config = SecurityScanConfig(
            stack=stack,
            tools=list(DEFAULT_SECURITY_TOOLS[stack]),
            fail_on_severity=SeverityLevel.HIGH,
        )
        collection.add_security_config(sec_config)

    # Generate gate config
    collection.gate_config = QualityGateConfig(
        enabled=True,
        block_on_fail=True,
        report_path="reports/quality_gate.json",
        min_coverage=80,
    )

    return collection


__all__ = [
    "RecipeOutput",
    "auto_generate_quality_collection",
    "data_quality_recipe",
    "generate_default_profiles",
    "generate_security_config",
    "generate_strict_profiles",
]


# ===========================================================================
# RecipeOutput — dataclass kết quả recipe
# ===========================================================================


@dataclass
class RecipeOutput:
    """Kết quả từ recipe builder.

    Attributes:
        name: Tên recipe
        description: Mô tả recipe
        checks: Danh sách quality checks
        thresholds: Danh sách quality thresholds
        profile: Data quality profile
        raw_data: Raw DSL dict
    """
    __test__ = False  # Prevent pytest collection

    name: str
    description: str
    checks: list[QualityCheck]
    thresholds: list[QualityThreshold]
    profile: DataQualityProfile
    raw_data: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Chuyển RecipeOutput sang dict."""
        return {
            "name": self.name,
            "description": self.description,
            "checks": [c.to_dict() for c in self.checks],
            "thresholds": [t.to_dict() for t in self.thresholds],
            "profile": self.profile.to_dict(),
            "raw_data": self.raw_data,
        }


# ===========================================================================
# Data Quality Recipe
# ===========================================================================


def data_quality_recipe() -> RecipeOutput:
    """Data quality profile với completeness, accuracy, freshness checks.

    Build sẵn các quality checks phổ biến:
    - completeness: kiểm tra % giá trị non-null trên các trường quan trọng
    - accuracy: kiểm tra giá trị nằm trong khoảng hợp lệ
    - freshness: kiểm tra độ cũ của dữ liệu
    - uniqueness: kiểm tra record trùng lặp
    - validity: kiểm tra định dạng email, phone, ...

    Returns:
        RecipeOutput chứa checks, thresholds, và profile
    """
    # --- Quality Checks ---
    checks: list[QualityCheck] = [
        QualityCheck(
            id="qc-users-email-completeness",
            name="User Email Completeness",
            target="users.email",
            rule=DataQualityRule.COMPLETENESS,
            threshold=0.98,
            description="Tỷ lệ user có email không được để trống >= 98%",
        ),
        QualityCheck(
            id="qc-users-age-accuracy",
            name="User Age Accuracy",
            target="users.age",
            rule=DataQualityRule.ACCURACY,
            threshold=0.95,
            metadata={"min_value": 0, "max_value": 150},
            description="Giá trị age nằm trong khoảng 0-150",
        ),
        QualityCheck(
            id="qc-orders-freshness",
            name="Orders Data Freshness",
            target="orders",
            rule=DataQualityRule.FRESHNESS,
            threshold=24.0,
            metadata={"unit": "hours"},
            description="Dữ liệu orders được cập nhật trong 24 giờ",
        ),
        QualityCheck(
            id="qc-users-email-uniqueness",
            name="User Email Uniqueness",
            target="users.email",
            rule=DataQualityRule.UNIQUENESS,
            threshold=1.0,
            description="Không có email trùng lặp trong bảng users",
        ),
        QualityCheck(
            id="qc-users-email-validity",
            name="User Email Validity",
            target="users.email",
            rule=DataQualityRule.VALIDITY,
            threshold=0.95,
            metadata={"pattern": r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"},
            description="Email phải khớp định dạng chuẩn",
        ),
        QualityCheck(
            id="qc-orders-users-consistency",
            name="Orders-Users Consistency",
            target="orders.user_id",
            rule=DataQualityRule.CONSISTENCY,
            threshold=0.99,
            metadata={"reference_table": "users.id"},
            description="Mọi user_id trong orders phải tồn tại trong users",
        ),
    ]

    # --- Thresholds ---
    thresholds: list[QualityThreshold] = [
        QualityThreshold(
            id="qt-email-completeness",
            check_id="qc-users-email-completeness",
            metric_name="completeness_pct",
            operator=">=",
            value=0.98,
            severity=AlertSeverity.CRITICAL,
        ),
        QualityThreshold(
            id="qt-age-accuracy",
            check_id="qc-users-age-accuracy",
            metric_name="accuracy_pct",
            operator=">=",
            value=0.95,
            severity=AlertSeverity.WARNING,
        ),
        QualityThreshold(
            id="qt-orders-freshness",
            check_id="qc-orders-freshness",
            metric_name="age_hours",
            operator="<=",
            value=24.0,
            severity=AlertSeverity.WARNING,
        ),
        QualityThreshold(
            id="qt-email-uniqueness",
            check_id="qc-users-email-uniqueness",
            metric_name="duplicate_count",
            operator="==",
            value=0.0,
            severity=AlertSeverity.CRITICAL,
        ),
        QualityThreshold(
            id="qt-email-validity",
            check_id="qc-users-email-validity",
            metric_name="validity_pct",
            operator=">=",
            value=0.95,
            severity=AlertSeverity.WARNING,
        ),
        QualityThreshold(
            id="qt-orders-consistency",
            check_id="qc-orders-users-consistency",
            metric_name="orphan_count",
            operator="==",
            value=0.0,
            severity=AlertSeverity.CRITICAL,
        ),
    ]

    # --- Profile ---
    profile = DataQualityProfile(
        id="dq-profile-default",
        name="Default Data Quality Profile",
        checks=[c.id for c in checks],
        schedule_cron="0 0 * * *",
        alert_on_failure=True,
        email_recipients=["data-team@company.com"],
        generate_report=True,
        report_format="json",
    )

    # --- Raw DSL ---
    raw_data: dict[str, Any] = {
        "checks": [c.to_dict() for c in checks],
        "thresholds": [t.to_dict() for t in thresholds],
        "profile": profile.to_dict(),
    }

    return RecipeOutput(
        name="data_quality_default",
        description="Default data quality profile với completeness, accuracy, freshness, uniqueness, validity, consistency checks",
        checks=checks,
        thresholds=thresholds,
        profile=profile,
        raw_data=raw_data,
    )
