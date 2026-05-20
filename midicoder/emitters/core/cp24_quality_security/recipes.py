# coding: utf-8
"""
Recipe module cho CP24 Code Quality & Security Scanner Generator.

Recipes cung cấp auto-generate quality profiles và security configs
khi không có DSL quality nodes explicit.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from midicoder.emitters.core.cp24_quality_security.models import (
    FormatterType,
    LinterType,
    QualityCollection,
    QualityGateConfig,
    QualityProfile,
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
    "generate_default_profiles",
    "generate_strict_profiles",
    "generate_security_config",
    "auto_generate_quality_collection",
]
