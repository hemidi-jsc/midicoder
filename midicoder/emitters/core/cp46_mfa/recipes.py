# coding: utf-8
"""
Mô-đun recipes cho CP46 — MFA & Advanced Authentication.

Cung cấp các recipe patterns để generate MFA với TOTP, SMS OTP,
WebAuthn/FIDO2, và biometric authentication.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass

from midicoder.emitters.core.cp46_mfa.models import (
    MFAMethod,
    MFAPriority,
)
from midicoder.emitters.core.cp46_mfa.parser import (
    MFAIR,
    MFARule,
)


@dataclass
class RecipeOutput:
    """Kết quả của recipe.

    Attributes:
        name: Tên recipe
        description: Mô tả recipe
        ir: MFAIR kết quả
    """
    name: str
    description: str
    ir: MFAIR


def basic_mfa_recipe() -> RecipeOutput:
    """Recipe: MFA cơ bản — TOTP bắt buộc, challenge 5 phút, max 5 attempts.

    Tạo MFA rule cho tất cả users với TOTP là phương thức duy nhất,
    bắt buộc xác thực. Phù hợp cho dev/prototyping.

    Returns:
        RecipeOutput với cấu hình MFA cơ bản
    """
    rules = [
        MFARule(
            rule_id="mfa_basic_all_users",
            role_id="all_users",
            method=MFAMethod.TOTP,
            priority=MFAPriority.REQUIRED,
            enabled=True,
            metadata={"recipe": "basic_mfa"},
        ),
    ]

    return RecipeOutput(
        name="basic_mfa",
        description="1 rule — TOTP bắt buộc cho tất cả users, challenge 5 phút, max 5 attempts",
        ir=MFAIR(
            rules=rules,
            enabled_methods=[MFAMethod.TOTP],
            default_method=MFAMethod.TOTP,
            default_priority=MFAPriority.REQUIRED,
            require_mfa=True,
            allow_backup=False,
            challenge_timeout=5,
            max_attempts=5,
            session_duration=1440,
            use_webauthn=False,
            use_biometric=False,
            use_sms_otp=False,
            use_totp=True,
        ),
    )


def full_mfa_recipe() -> RecipeOutput:
    """Recipe: MFA đầy đủ — TOTP, SMS OTP, WebAuthn, Biometric.

    Tạo 4 MFA rules: (1) admin yêu cầu WebAuthn, (2) staff dùng TOTP,
    (3) backup SMS OTP cho tất cả, (4) biometric cho mobile users.
    Multi-method với backup và priority.

    Returns:
        RecipeOutput với cấu hình MFA đầy đủ
    """
    rules = [
        MFARule(
            rule_id="mfa_full_admin_webauthn",
            role_id="admin",
            method=MFAMethod.WEBAUTHN_FIDO2,
            priority=MFAPriority.REQUIRED,
            enabled=True,
            metadata={"recipe": "full_mfa", "reason": "highest_security"},
        ),
        MFARule(
            rule_id="mfa_full_staff_totp",
            role_id="staff",
            method=MFAMethod.TOTP,
            priority=MFAPriority.REQUIRED,
            enabled=True,
            metadata={"recipe": "full_mfa", "reason": "standard_security"},
        ),
        MFARule(
            rule_id="mfa_full_backup_sms",
            role_id="all_users",
            method=MFAMethod.SMS_OTP,
            priority=MFAPriority.BACKUP,
            enabled=True,
            metadata={"recipe": "full_mfa", "reason": "backup_method"},
        ),
        MFARule(
            rule_id="mfa_full_mobile_biometric",
            role_id="mobile_users",
            method=MFAMethod.BIOMETRIC,
            priority=MFAPriority.OPTIONAL,
            enabled=True,
            metadata={"recipe": "full_mfa", "reason": "convenience"},
        ),
    ]

    return RecipeOutput(
        name="full_mfa",
        description="4 rules (WebAuthn cho admin, TOTP cho staff, SMS backup, Biometric cho mobile), multi-method với priority",
        ir=MFAIR(
            rules=rules,
            enabled_methods=[
                MFAMethod.TOTP,
                MFAMethod.SMS_OTP,
                MFAMethod.WEBAUTHN_FIDO2,
                MFAMethod.BIOMETRIC,
            ],
            default_method=MFAMethod.TOTP,
            default_priority=MFAPriority.REQUIRED,
            require_mfa=True,
            allow_backup=True,
            challenge_timeout=5,
            max_attempts=5,
            session_duration=1440,
            use_webauthn=True,
            use_biometric=True,
            use_sms_otp=True,
            use_totp=True,
        ),
    )


__all__ = [
    "RecipeOutput",
    "basic_mfa_recipe",
    "full_mfa_recipe",
]
