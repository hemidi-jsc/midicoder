# coding: utf-8
"""
CP49 — Consent & Preference Management Pack.

Public API barrel export.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from midicoder.emitters.core.cp49_consent.models import (
    CommChannel,
    CommunicationPreference,
    ConsentCategory,
    ConsentEngine,
    ConsentPolicy,
    ConsentPurpose,
    ConsentRecord,
    ConsentStatus,
    CookieCategory,
    CookiePreference,
    ErasureRequest,
    ErasureScope,
    ErasureStatus,
)
from midicoder.emitters.core.cp49_consent.parser import (
    ConsentIR,
    parse_comm_config,
    parse_consent_policies,
    parse_consent_records,
    parse_cookie_config,
    parse_erasure_config,
    parse_to_ir,
)
from midicoder.emitters.core.cp49_consent.recipes import (
    RecipeOutput,
    basic_consent_recipe,
    full_consent_recipe,
)
from midicoder.emitters.core.cp49_consent.fastapi import (
    FastAPIConsentEmitter,
)
from midicoder.emitters.core.cp49_consent.nestjs import (
    NestJSConsentEmitter,
)
from midicoder.emitters.core.cp49_consent.angular import (
    AngularConsentEmitter,
)
from midicoder.emitters.core.cp49_consent.react import (
    ReactConsentEmitter,
)

__all__ = [
    # Models - Enums
    "ConsentStatus",
    "ConsentPurpose",
    "ConsentCategory",
    "CookieCategory",
    "CommChannel",
    "ErasureStatus",
    "ErasureScope",
    # Models - Core
    "ConsentRecord",
    "ConsentPolicy",
    "CookiePreference",
    "CommunicationPreference",
    "ErasureRequest",
    # Models - Engine
    "ConsentEngine",
    # Parser
    "ConsentIR",
    "parse_consent_policies",
    "parse_consent_records",
    "parse_cookie_config",
    "parse_comm_config",
    "parse_erasure_config",
    "parse_to_ir",
    # Recipes
    "RecipeOutput",
    "basic_consent_recipe",
    "full_consent_recipe",
    # Emitters
    "FastAPIConsentEmitter",
    "NestJSConsentEmitter",
    "AngularConsentEmitter",
    "ReactConsentEmitter",
]
