# coding: utf-8
"""
Mô-đun parser cho CP49 — Consent & Preference Management.

Parse DSL dict (từ contract YAML) sang ConsentIR — Intermediate Representation
cho các chính sách consent, bản ghi consent, cấu hình cookie, sở thích truyền thông.

Lưu ý: gdpr_erasure delegate đến CP47 (Data Retention & Lifecycle Management).

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from midicoder.emitters.core.cp49_consent.models import (
    ConsentCategory,
    ConsentPolicy,
    ConsentPurpose,
    ConsentRecord,
    ConsentStatus,
    CookieCategory,
    CookiePreference,
    CommChannel,
    CommunicationPreference,
)


@dataclass
class ConsentIR:
    """Intermediate Representation cho CP49.

    Gom tập tất cả cấu hình quản lý consent từ DSL, bao gồm
    các chính sách consent, bản ghi consent, cấu hình cookie,
    và sở thích truyền thông.

    Lưu ý: gdpr_erasure delegate đến CP47 (Data Retention & Lifecycle Management).

    Attributes:
        policies: Danh sách chính sách consent
        consents: Danh sách bản ghi consent
        cookie_categories: Danh sách danh mục cookie
        comm_channels: Danh sách kênh truyền thông
        use_audit: Có sử dụng tích hợp audit (CP14) không
        use_retention: Có sử dụng tích hợp retention (CP47) không
    """
    policies: list[ConsentPolicy] = field(default_factory=list)
    consents: list[ConsentRecord] = field(default_factory=list)
    cookie_categories: list[str] = field(default_factory=list)
    comm_channels: list[str] = field(default_factory=list)
    use_audit: bool = True
    use_retention: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Chuyển ConsentIR sang dict."""
        return {
            "policies": [p.to_dict() for p in self.policies],
            "consents": [c.to_dict() for c in self.consents],
            "cookie_categories": self.cookie_categories,
            "comm_channels": self.comm_channels,
            "use_audit": self.use_audit,
            "use_retention": self.use_retention,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConsentIR":
        """Tạo ConsentIR từ dict."""
        policies = [ConsentPolicy.from_dict(p) for p in data.get("policies", [])]
        consents = [ConsentRecord.from_dict(c) for c in data.get("consents", [])]
        return cls(
            policies=policies,
            consents=consents,
            cookie_categories=data.get("cookie_categories", []),
            comm_channels=data.get("comm_channels", []),
            use_audit=data.get("use_audit", True),
            use_retention=data.get("use_retention", True),
        )


def parse_consent_policies(data: dict[str, Any]) -> list[ConsentPolicy]:
    """Parse danh sách chính sách consent từ DSL dict.

    Args:
        data: DSL dict với key 'consent_policies' hoặc 'policies'

    Returns:
        Danh sách ConsentPolicy
    """
    raw = data.get("consent_policies", data.get("policies", []))
    policies = []
    for pol in raw:
        policies.append(ConsentPolicy(
            policy_id=pol.get("policy_id", pol.get("id", "")),
            tenant_id=pol.get("tenant_id", pol.get("tenant", "")),
            purpose=ConsentPurpose(pol.get("purpose", "essential")),
            category=ConsentCategory(pol.get("category", "necessary")),
            is_mandatory=pol.get("is_mandatory", False),
            description=pol.get("description", ""),
            expiry_days=pol.get("expiry_days", 365),
            renewal_reminder_days=pol.get("renewal_reminder_days", 30),
        ))
    return policies


def parse_consent_records(data: dict[str, Any]) -> list[ConsentRecord]:
    """Parse danh sách bản ghi consent từ DSL dict.

    Args:
        data: DSL dict với key 'consent_records' hoặc 'consents'

    Returns:
        Danh sách ConsentRecord
    """
    raw = data.get("consent_records", data.get("consents", []))
    records = []
    for rec in raw:
        records.append(ConsentRecord(
            record_id=rec.get("record_id", rec.get("id", "")),
            user_id=rec.get("user_id", rec.get("user", "")),
            tenant_id=rec.get("tenant_id", rec.get("tenant", "")),
            purpose=ConsentPurpose(rec.get("purpose", "essential")),
            category=ConsentCategory(rec.get("category", "necessary")),
            status=ConsentStatus(rec.get("status", "active")),
            ip_address=rec.get("ip_address", ""),
            user_agent=rec.get("user_agent", ""),
            metadata=rec.get("metadata", {}),
        ))
    return records


def parse_cookie_config(data: dict[str, Any]) -> list[str]:
    """Parse cấu hình cookie từ DSL dict.

    Args:
        data: DSL dict với key 'cookie_config' hoặc 'cookies'

    Returns:
        Danh sách danh mục cookie được kích hoạt
    """
    raw = data.get("cookie_config", data.get("cookies", {}))

    if isinstance(raw, list):
        return raw

    if isinstance(raw, dict):
        categories = []
        for cat_name in raw:
            if cat_name in {c.value for c in CookieCategory}:
                categories.append(cat_name)
        return categories

    return []


def parse_comm_config(data: dict[str, Any]) -> list[str]:
    """Parse cấu hình sở thích truyền thông từ DSL dict.

    Args:
        data: DSL dict với key 'communication_preferences' hoặc 'comm_config'

    Returns:
        Danh sách kênh truyền thông được kích hoạt
    """
    raw = data.get("communication_preferences", data.get("comm_config", {}))

    if isinstance(raw, list):
        return raw

    if isinstance(raw, dict):
        channels = []
        for ch_name in raw:
            if ch_name in {c.value for c in CommChannel}:
                channels.append(ch_name)
        return channels

    return []


def parse_to_ir(data: dict[str, Any]) -> ConsentIR:
    """Parse DSL dict thành ConsentIR.

    Gom tập tất cả các thành phần: policies, records, cookie config,
    comm config, và các flags tích hợp audit/retention.

    Lưu ý: gdpr_erasure delegate đến CP47 (Data Retention & Lifecycle Management).

    Args:
        data: DSL dict với consent_policies, consent_records, cookie_config,
            communication_preferences

    Returns:
        ConsentIR gom tập tất cả parsed data
    """
    policies = parse_consent_policies(data)
    consents = parse_consent_records(data)
    cookie_categories = parse_cookie_config(data)
    comm_channels = parse_comm_config(data)

    return ConsentIR(
        policies=policies,
        consents=consents,
        cookie_categories=cookie_categories,
        comm_channels=comm_channels,
        use_audit=data.get("use_audit", True),
        use_retention=data.get("use_retention", True),
    )


__all__ = [
    "ConsentIR",
    "parse_consent_policies",
    "parse_consent_records",
    "parse_cookie_config",
    "parse_comm_config",
    "parse_to_ir",
]
