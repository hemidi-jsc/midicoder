"""
Pack Registry — Single source of truth for pack ID → internal_id mapping (taxonomy-v2).

Module này là single source để resolve pack ID (vd: "F01") sang
folder name (vd: "cp_full_auth"). Tất cả consumer import từ đây,
không tự define mapping riêng.

Taxonomy v2: 52 packs tổ chức theo 6 tier (BASE, INFRA, CORE, BACKEND,
FRONTEND, FULL) — thay thế taxonomy v1 (65 packs CP01→CP65).

Stack constants (BACKEND_STACKS, FRONTEND_STACKS, INFRA_STACK, ALL_STACKS)
cũng được định nghĩa ở đây để tránh duplicate.

Author: Midicoder Team
Version: 3.0.0 (taxonomy-v2)
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
# Pack ID → Internal folder name mapping (taxonomy-v2)
# ---------------------------------------------------------------------------

ID_TO_INTERNAL: Final[dict[str, str]] = {
    # BASE
    "B01": "cp_base_domain_model",

    # INFRA
    "I01": "cp_infra_iac",
    "I02": "cp_infra_kubernetes",
    "I03": "cp_infra_cicd",
    "I04": "cp_infra_env_secrets",
    "I05": "cp_infra_multi_region",

    # CORE
    "C01": "cp_core_multi_tenant",
    "C02": "cp_core_event_driven",
    "C03": "cp_core_observability",

    # BACKEND
    "BE01": "cp_backend_database",
    "BE02": "cp_backend_cache",
    "BE03": "cp_backend_api_client",
    "BE04": "cp_backend_graphql_federation",
    "BE05": "cp_backend_encryption",
    "BE06": "cp_backend_contract_testing",

    # FRONTEND
    "FE01": "cp_frontend_auth_ui",
    "FE02": "cp_frontend_realtime_ui",

    # FULL
    "F01": "cp_full_auth",
    "F02": "cp_full_rbac",
    "F03": "cp_full_api_gateway",
    "F04": "cp_full_file_media",
    "F05": "cp_full_frontend_framework",
    "F07": "cp_full_ui_components",
    "F08": "cp_full_notification",
    "F09": "cp_full_testing_framework",
    "F10": "cp_full_quality_security",
    "F11": "cp_full_documentation",
    "F12": "cp_full_plugin_system",
    "F13": "cp_full_ai_assisted",
    "F14": "cp_full_audit_compliance",
    "F15": "cp_full_monitoring",
    "F16": "cp_full_state_machine",
    "F17": "cp_full_financial",
    "F18": "cp_full_reporting",
    "F19": "cp_full_geospatial",
    "F20": "cp_full_workflow_scheduler",
    "F21": "cp_full_tenant_onboarding",
    "F22": "cp_full_search",
    "F23": "cp_full_i18n",
    "F24": "cp_full_webhook",
    "F25": "cp_full_chat",
    "F26": "cp_full_approval",
    "F27": "cp_full_versioning",
    "F28": "cp_full_bulk_etl",
    "F29": "cp_full_payment",
    "F30": "cp_full_mfa",
    "F31": "cp_full_data_lifecycle",
    "F32": "cp_full_rate_limit",
    "F33": "cp_full_consent",
    "F34": "cp_full_catalog",
    "F35": "cp_full_service_discovery",
    "F36": "cp_full_tenant_billing",
}
"""Mapping từ pack ID (vd: "F01") sang folder name (vd: "cp_full_auth").

Taxonomy v2: 52 packs trong 6 tier. Đây là single source — file_contributions_loader.py
và các consumer khác import từ đây thay vì tự define mapping riêng.
"""

# ---------------------------------------------------------------------------
# Reverse mapping: internal folder name → Pack ID
# ---------------------------------------------------------------------------

INTERNAL_TO_ID: Final[dict[str, str]] = {v: k for k, v in ID_TO_INTERNAL.items()}
"""Reverse mapping từ folder name (vd: "cp_full_auth") sang pack ID (vd: "F01")."""

# ---------------------------------------------------------------------------
# All pack IDs
# ---------------------------------------------------------------------------

ALL_PACK_IDS: Final[list[str]] = list(ID_TO_INTERNAL.keys())
"""Tất cả pack IDs theo taxonomy-v2 (trình tự theo tier)."""

# ---------------------------------------------------------------------------
# Backwards compatibility alias (deprecated — keep until all consumers migrate)
# ---------------------------------------------------------------------------

CP_ID_TO_INTERNAL = ID_TO_INTERNAL
"""Alias cho backwards compatibility — dùng ID_TO_INTERNAL mới trong code mới."""

__all__ = [
    "BACKEND_STACKS",
    "FRONTEND_STACKS",
    "INFRA_STACK",
    "ALL_STACKS",
    "ID_TO_INTERNAL",
    "INTERNAL_TO_ID",
    "ALL_PACK_IDS",
    "CP_ID_TO_INTERNAL",
]
