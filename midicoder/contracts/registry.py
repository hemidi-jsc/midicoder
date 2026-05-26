"""
Pack Registry — Single source of truth cho CP_ID → internal_id mapping.

Module này là single source để resolve pack ID (vd: "CP02") thành
folder name (vd: "cp02_multi_tenant"). Tất cả consumer import từ đây,
không tự define mapping riêng.

Stack constants (BACKEND_STACKS, FRONTEND_STACKS, INFRA_STACK, ALL_STACKS)
cũng được định nghĩa ở đây để tránh duplicate.

Author: Midicoder Team
Version: 2.0.0
"""

from typing import Final

# ---------------------------------------------------------------------------
# Stack constants
# ---------------------------------------------------------------------------

BACKEND_STACKS: Final[set] = {"fastapi", "nestjs"}
"""Backend stacks: FastAPI và NestJS."""

FRONTEND_STACKS: Final[set] = {"angular", "react"}
"""Frontend stacks: Angular và React."""

INFRA_STACK: Final[str] = "infrastructure"
"""Infrastructure stack: files chung cho cả project."""

ALL_STACKS: Final[set] = BACKEND_STACKS | FRONTEND_STACKS | {INFRA_STACK}
"""Tất cả stack đã biết."""

# ---------------------------------------------------------------------------
# Pack ID → Internal folder name mapping
# ---------------------------------------------------------------------------

CP_ID_TO_INTERNAL: Final[dict[str, str]] = {
    "CP01": "cp01_domain_model",
    "CP02": "cp02_multi_tenant",
    "CP03": "cp03_auth",
    "CP04": "cp04_rbac",
    "CP05": "cp05_event_driven",
    "CP06": "cp06_api_gateway",
    "CP07": "cp07_iac",
    "CP08": "cp08_database",
    "CP09": "cp09_cache",
    "CP10": "cp10_search",
    "CP11": "cp11_file_media",
    "CP12": "cp12_notification",
    "CP13": "cp13_workflow_runtime",
    "CP14": "cp14_audit_compliance",
    "CP15": "cp15_observability",
    "CP16": "cp16_monitoring",
    "CP17": "cp17_bi_analytics",
    "CP18": "cp18_frontend_framework",
    "CP19": "cp19_ui_components",
    "CP20": "cp20_api_client",
    "CP21": "cp21_auth_ui",
    "CP22": "cp22_realtime_ui",
    "CP23": "cp23_testing_framework",
    "CP24": "cp24_quality_security",
    "CP25": "cp25_performance_testing",
    "CP26": "cp26_documentation",
    "CP27": "cp27_plugin_system",
    # CP28 removed — merged into CP27 (cp27_plugin_system)
    "CP29": "cp29_multi_language",
    "CP30": "cp30_ai_assisted",
    "CP31": "cp31_scheduler",
    "CP32": "cp32_state_machine",
    "CP33": "cp33_financial",
    "CP34": "cp34_reporting",
    "CP35": "cp35_geospatial",
    "CP36": "cp36_tenant_onboarding",
    "CP37": "cp37_feature_flags",
    "CP38": "cp38_data_etl",
    "CP39": "cp39_i18n_runtime",
    "CP40": "cp40_webhook",
    "CP41": "cp41_chat",
    "CP42": "cp42_approval",
    "CP43": "cp43_versioning",
    "CP44": "cp44_bulk_ops",
    "CP45": "cp45_payment",
    "CP46": "cp46_mfa",
    "CP47": "cp47_retention",
    "CP48": "cp48_rate_limit",
    "CP49": "cp49_consent",
    "CP50": "cp50_catalog",
    "CP51": "cp51_blueprint",
    "CP52": "cp52_invariant",
    "CP53": "cp53_domain_bridge",
    "CP54": "cp54_kubernetes",
    "CP55": "cp55_cicd",
    "CP56": "cp56_env_secrets",
    "CP57": "cp57_graphql_federation",
    "CP58": "cp58_encryption",
    "CP59": "cp59_tenant_billing",
    "CP60": "cp60_service_discovery",
    "CP61": "cp61_distributed_tracing",
    "CP62": "cp62_mobile_backend",
    "CP63": "cp63_recommendation",
}
"""Mapping từ pack ID (vd: "CP01") sang folder name (vd: "cp01_domain_model").

Đây là single source — file_contributions_loader.py và các consumer khác
import từ đây thay vì tự define mapping riêng.
"""

__all__ = [
    "BACKEND_STACKS",
    "FRONTEND_STACKS",
    "INFRA_STACK",
    "ALL_STACKS",
    "CP_ID_TO_INTERNAL",
]
