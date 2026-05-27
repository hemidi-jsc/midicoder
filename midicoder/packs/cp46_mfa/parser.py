# coding: utf-8
"""
Mô-đun parser cho CP46 — MFA & Advanced Authentication.

Parse DSL dict (từ contract YAML) sang MFAIR — Intermediate Representation
cho các MFA configurations, enrollment settings, challenge options,
và session management.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from midicoder.packs.cp46_mfa.models import (
    MFAMethod,
    MFAPriority,
    MFARule,
)


@dataclass
class MFAIR:
    """Intermediate Representation cho CP46.

    Gom tập tất cả cấu hình MFA từ DSL, bao gồm
    các rules, enrollment config, challenge options, và session settings.

    Attributes:
        rules: Danh sách MFA rules
        enabled_methods: Danh sách phương thức MFA được phép
        default_method: Phương thức MFA mặc định
        default_priority: Mức ưu tiên mặc định
        require_mfa: Bắt buộc xác thực MFA
        allow_backup: Cho phép phương thức dự phòng
        challenge_timeout: Timeout cho challenge (phút)
        max_attempts: Số lần thử tối đa
        session_duration: Thời lượng session (phút)
        use_webauthn: Có hỗ trợ WebAuthn không
        use_biometric: Có hỗ trợ biometric không
        use_sms_otp: Có hỗ trợ SMS OTP không
        use_totp: Có hỗ trợ TOTP không
    """
    rules: list[MFARule] = field(default_factory=list)
    enabled_methods: list[MFAMethod] = field(
        default_factory=lambda: [MFAMethod.TOTP, MFAMethod.SMS_OTP, MFAMethod.WEBAUTHN_FIDO2, MFAMethod.BIOMETRIC]
    )
    default_method: MFAMethod = MFAMethod.TOTP
    default_priority: MFAPriority = MFAPriority.REQUIRED
    require_mfa: bool = True
    allow_backup: bool = True
    challenge_timeout: int = 5
    max_attempts: int = 5
    session_duration: int = 1440
    use_webauthn: bool = True
    use_biometric: bool = True
    use_sms_otp: bool = True
    use_totp: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Chuyển MFAIR sang dict."""
        return {
            "rules": [r.to_dict() for r in self.rules],
            "enabled_methods": [m.value for m in self.enabled_methods],
            "default_method": self.default_method.value,
            "default_priority": self.default_priority.value,
            "require_mfa": self.require_mfa,
            "allow_backup": self.allow_backup,
            "challenge_timeout": self.challenge_timeout,
            "max_attempts": self.max_attempts,
            "session_duration": self.session_duration,
            "use_webauthn": self.use_webauthn,
            "use_biometric": self.use_biometric,
            "use_sms_otp": self.use_sms_otp,
            "use_totp": self.use_totp,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MFAIR":
        """Tạo MFAIR từ dict."""
        rules = [MFARule.from_dict(r) for r in data.get("rules", [])]
        methods_raw = data.get("enabled_methods", ["totp", "sms_otp", "webauthn_fido2", "biometric"])
        enabled_methods = [MFAMethod(m) for m in methods_raw]
        return cls(
            rules=rules,
            enabled_methods=enabled_methods,
            default_method=MFAMethod(data.get("default_method", "totp")),
            default_priority=MFAPriority(data.get("default_priority", "required")),
            require_mfa=data.get("require_mfa", True),
            allow_backup=data.get("allow_backup", True),
            challenge_timeout=data.get("challenge_timeout", 5),
            max_attempts=data.get("max_attempts", 5),
            session_duration=data.get("session_duration", 1440),
            use_webauthn=data.get("use_webauthn", True),
            use_biometric=data.get("use_biometric", True),
            use_sms_otp=data.get("use_sms_otp", True),
            use_totp=data.get("use_totp", True),
        )


def parse_mfa_rules(data: dict[str, Any]) -> list[MFARule]:
    """Parse danh sách MFA rules từ DSL dict.

    Args:
        data: DSL dict với key 'mfa_rules' hoặc 'rules'

    Returns:
        Danh sách MFARule
    """
    raw = data.get("mfa_rules", data.get("rules", []))
    rules = []
    for rule_data in raw:
        rules.append(MFARule(
            rule_id=rule_data.get("rule_id", rule_data.get("id", "")),
            user_id=rule_data.get("user_id", ""),
            role_id=rule_data.get("role_id", ""),
            method=MFAMethod(rule_data.get("method", "totp")),
            priority=MFAPriority(rule_data.get("priority", "required")),
            enabled=rule_data.get("enabled", True),
            metadata=rule_data.get("metadata", {}),
        ))
    return rules


def parse_mfa_config(data: dict[str, Any]) -> dict[str, Any]:
    """Parse cấu hình MFA từ DSL dict.

    Args:
        data: DSL dict với các config keys

    Returns:
        Dict chứa require_mfa, allow_backup, challenge_timeout,
        max_attempts, session_duration
    """
    return {
        "require_mfa": data.get("require_mfa", True),
        "allow_backup": data.get("allow_backup", True),
        "challenge_timeout": data.get("challenge_timeout", 5),
        "max_attempts": data.get("max_attempts", 5),
        "session_duration": data.get("session_duration", 1440),
        "default_method": data.get("default_method", "totp"),
        "default_priority": data.get("default_priority", "required"),
    }


def parse_methods_config(data: dict[str, Any]) -> dict[str, Any]:
    """Parse cấu hình methods từ DSL dict.

    Args:
        data: DSL dict với key 'methods'

    Returns:
        Dict chứa use_webauthn, use_biometric, use_sms_otp, use_totp
    """
    methods_raw = data.get("methods", {})
    if isinstance(methods_raw, dict):
        return {
            "use_webauthn": methods_raw.get("webauthn", methods_raw.get("webauthn_fido2", True)),
            "use_biometric": methods_raw.get("biometric", True),
            "use_sms_otp": methods_raw.get("sms_otp", True),
            "use_totp": methods_raw.get("totp", True),
        }
    # Default: all enabled
    return {
        "use_webauthn": True,
        "use_biometric": True,
        "use_sms_otp": True,
        "use_totp": True,
    }


def parse_enabled_methods(data: dict[str, Any]) -> list[MFAMethod]:
    """Parse danh sách enabled methods từ DSL dict.

    Args:
        data: DSL dict với key 'enabled_methods'

    Returns:
        Danh sách MFAMethod được phép
    """
    methods_raw = data.get("enabled_methods", None)
    if methods_raw is None:
        # Default: lấy từ methods config
        methods_config = parse_methods_config(data)
        result = []
        if methods_config["use_totp"]:
            result.append(MFAMethod.TOTP)
        if methods_config["use_sms_otp"]:
            result.append(MFAMethod.SMS_OTP)
        if methods_config["use_webauthn"]:
            result.append(MFAMethod.WEBAUTHN_FIDO2)
        if methods_config["use_biometric"]:
            result.append(MFAMethod.BIOMETRIC)
        return result if result else list(MFAMethod)

    # Explicit list provided
    return [MFAMethod(m) for m in methods_raw]


def parse_to_ir(data: dict[str, Any]) -> MFAIR:
    """Parse DSL dict thành MFAIR.

    Args:
        data: DSL dict với rules, config, methods, enabled_methods

    Returns:
        MFAIR gom tập tất cả parsed data
    """
    rules = parse_mfa_rules(data)
    config = parse_mfa_config(data)
    methods = parse_methods_config(data)
    enabled = parse_enabled_methods(data)

    return MFAIR(
        rules=rules,
        enabled_methods=enabled,
        default_method=MFAMethod(config["default_method"]),
        default_priority=MFAPriority(config["default_priority"]),
        require_mfa=config["require_mfa"],
        allow_backup=config["allow_backup"],
        challenge_timeout=config["challenge_timeout"],
        max_attempts=config["max_attempts"],
        session_duration=config["session_duration"],
        use_webauthn=methods["use_webauthn"],
        use_biometric=methods["use_biometric"],
        use_sms_otp=methods["use_sms_otp"],
        use_totp=methods["use_totp"],
    )


__all__ = [
    "MFAIR",
    "MFARule",
    "parse_mfa_rules",
    "parse_mfa_config",
    "parse_methods_config",
    "parse_enabled_methods",
    "parse_to_ir",
]
