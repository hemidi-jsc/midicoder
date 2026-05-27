"""
Pack Emitter Router.

Routes FileSpecs to pack-specific emitters instead of raw Jinja2.
This is the dispatch layer between pipeline's code gen and structured
pack emitters (e.g., CP01 EntityEmitter, VOEmitter).

Usage in code.py:
    if pack_emitter := file_spec.metadata.get("pack_emitter"):
        files = PackEmitterRouter.dispatch(pack_emitter, file_spec, stack)
    else:
        # raw Jinja2 fallback
        content = Emitter.render(template, context)

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

from .config import get_config


# ---------------------------------------------------------------------------
# Registry: pack_emitter key → (module_path, class_name, parser_key | None)
#
# parser_key is an optional hint telling the router which parser to use
# to convert the raw MIR dict into a structured dataclass before passing
# it to the emitter.
# ---------------------------------------------------------------------------

EMITTER_REGISTRY: dict[str, tuple[str, str, str | None]] = {
    # CP01 – Entity (FastAPI)
    "cp01.entity.fastapi": (
        "midicoder.emitters.core.cp01_domain_model.entity_fastapi",
        "FastAPIEntityEmitter",
        "cp01_entity",
    ),
    # CP01 – Entity (NestJS)
    "cp01.entity.nestjs": (
        "midicoder.emitters.core.cp01_domain_model.entity_nestjs",
        "NestJSEntityEmitter",
        "cp01_entity",
    ),
    # CP01 – Value Object (FastAPI)
    "cp01.vo.fastapi": (
        "midicoder.emitters.core.cp01_domain_model.vo_fastapi",
        "FastAPIValueObjectEmitter",
        None,  # VO emitters accept raw dicts
    ),
    # CP01 – Value Object (NestJS)
    "cp01.vo.nestjs": (
        "midicoder.emitters.core.cp01_domain_model.vo_nestjs",
        "NestJSValueObjectEmitter",
        None,
    ),
    # CP03 – Auth (FastAPI)
    "cp03.auth.fastapi": (
        "midicoder.emitters.core.cp03_auth.fastapi",
        "FastAPIAuthEmitter",
        "cp03_auth",
    ),
    # CP03 – Auth (NestJS)
    "cp03.auth.nestjs": (
        "midicoder.emitters.core.cp03_auth.nestjs",
        "NestJSEmitter",
        "cp03_auth",
    ),
    # CP03 – Auth (Angular)
    "cp03.auth.angular": (
        "midicoder.emitters.core.cp03_auth.angular",
        "AngularEmitter",
        "cp03_auth",
    ),
    # CP03 – Auth (React)
    "cp03.auth.react": (
        "midicoder.emitters.core.cp03_auth.react",
        "ReactEmitter",
        "cp03_auth",
    ),
    # CP04 – RBAC (FastAPI)
    "cp04.rbac.fastapi": (
        "midicoder.emitters.core.cp04_rbac.fastapi",
        "FastAPIRBACEmitter",
        None,
    ),
    # CP04 – RBAC (NestJS)
    "cp04.rbac.nestjs": (
        "midicoder.emitters.core.cp04_rbac.nestjs",
        "NestJSRBACEmitter",
        None,
    ),
    # CP04 – RBAC (Angular)
    "cp04.rbac.angular": (
        "midicoder.emitters.core.cp04_rbac.angular",
        "AngularRBACEmitter",
        None,
    ),
    # CP04 – RBAC (React)
    "cp04.rbac.react": (
        "midicoder.emitters.core.cp04_rbac.react",
        "ReactRBACEmitter",
        None,
    ),
    # CP07 – Docker Compose (already used, kept for reference)
    "cp07.docker": (
        "midicoder.emitters.core.cp07_iac.docker",
        "DockerComposeGenerator",
        None,
    ),
    # CP08 – Database (FastAPI)
    "cp08.database.fastapi": (
        "midicoder.emitters.core.cp08_database.fastapi",
        "SQLAlchemyEmitter",
        "cp08_database",
    ),
    # CP08 – Database (NestJS)
    "cp08.database.nestjs": (
        "midicoder.emitters.core.cp08_database.nestjs",
        "TypeORMEmitter",
        "cp08_database",
    ),
    # CP10 – Search (FastAPI)
    "cp10.search.fastapi": (
        "midicoder.emitters.core.cp10_search.fastapi",
        "FastAPISearchEmitter",
        "cp10_search",
    ),
    # CP10 – Search (NestJS)
    "cp10.search.nestjs": (
        "midicoder.emitters.core.cp10_search.nestjs",
        "NestJSSearchEmitter",
        "cp10_search",
    ),
    # CP10 – Search (Angular)
    "cp10.search.angular": (
        "midicoder.emitters.core.cp10_search.angular",
        "AngularEmitter",
        "cp10_search",
    ),
    # CP10 – Search (React)
    "cp10.search.react": (
        "midicoder.emitters.core.cp10_search.react",
        "ReactEmitter",
        "cp10_search",
    ),
    # CP05 – Event (FastAPI)
    "cp05.event.fastapi": (
        "midicoder.emitters.core.cp05_event_driven.fastapi",
        "FastAPIEventEmitter",
        "cp05_event",
    ),
    # CP05 – Event (NestJS)
    "cp05.event.nestjs": (
        "midicoder.emitters.core.cp05_event_driven.nestjs",
        "NestJSEventEmitter",
        "cp05_event",
    ),
    # CP06 – API Gateway (FastAPI)
    "cp06.gateway.fastapi": (
        "midicoder.emitters.core.cp06_api_gateway.fastapi",
        "FastAPIGatewayEmitter",
        "cp06_gateway",
    ),
    # CP06 – API Gateway (NestJS)
    "cp06.gateway.nestjs": (
        "midicoder.emitters.core.cp06_api_gateway.nestjs",
        "NestJSGatewayEmitter",
        "cp06_gateway",
    ),
    # CP06 – API Gateway (Angular)
    "cp06.gateway.angular": (
        "midicoder.emitters.core.cp06_api_gateway.angular",
        "AngularGatewayEmitter",
        "cp06_gateway",
    ),
    # CP06 – API Gateway (React)
    "cp06.gateway.react": (
        "midicoder.emitters.core.cp06_api_gateway.react",
        "ReactGatewayEmitter",
        "cp06_gateway",
    ),
    # CP09 – Cache (FastAPI)
    "cp09.cache.fastapi": (
        "midicoder.emitters.core.cp09_cache.fastapi",
        "FastAPICacheEmitter",
        "cp09_cache",
    ),
    # CP09 – Cache (NestJS)
    "cp09.cache.nestjs": (
        "midicoder.emitters.core.cp09_cache.nestjs",
        "NestJSCacheEmitter",
        "cp09_cache",
    ),
    # CP09 – Cache (Angular)
    "cp09.cache.angular": (
        "midicoder.emitters.core.cp09_cache.angular",
        "AngularEmitter",
        "cp09_cache",
    ),
    # CP09 – Cache (React)
    "cp09.cache.react": (
        "midicoder.emitters.core.cp09_cache.react",
        "ReactEmitter",
        "cp09_cache",
    ),
    # CP18 – Frontend Framework (Angular)
    "cp18.frontend.angular": (
        "midicoder.emitters.core.cp18_frontend_framework.angular",
        "AngularComponentEmitter",
        "cp18_frontend",
    ),
    # CP18 – Frontend Framework (React)
    "cp18.frontend.react": (
        "midicoder.emitters.core.cp18_frontend_framework.react",
        "ReactComponentEmitter",
        "cp18_frontend",
    ),
    # CP18 – Frontend Framework (FastAPI backend config)
    "cp18.frontend.fastapi": (
        "midicoder.emitters.core.cp18_frontend_framework.fastapi",
        "FastAPIFrontendEmitter",
        "cp18_frontend",
    ),
    # CP18 – Frontend Framework (NestJS backend config)
    "cp18.frontend.nestjs": (
        "midicoder.emitters.core.cp18_frontend_framework.nestjs",
        "NestJSFrontendEmitter",
        "cp18_frontend",
    ),
    # CP19 – UI Components (Angular)
    "cp19.angular": (
        "midicoder.emitters.core.cp19_ui_components.angular",
        "AngularUIEmitter",
        "cp19_ui_components",
    ),
    # CP19 – UI Components (React)
    "cp19.react": (
        "midicoder.emitters.core.cp19_ui_components.react",
        "ReactUIEmitter",
        "cp19_ui_components",
    ),
    # CP19 – UI Components (FastAPI)
    "cp19.fastapi": (
        "midicoder.emitters.core.cp19_ui_components.fastapi",
        "FastAPIUIEmitter",
        "cp19_ui_components",
    ),
    # CP19 – UI Components (NestJS)
    "cp19.nestjs": (
        "midicoder.emitters.core.cp19_ui_components.nestjs",
        "NestJSUIEmitter",
        "cp19_ui_components",
    ),
    # CP21 – Authentication UI (React)
    "cp21.react": (
        "midicoder.emitters.core.cp21_auth_ui.react",
        "ReactAuthUIEmitter",
        None,
    ),
    # CP21 – Authentication UI (Angular)
    "cp21.angular": (
        "midicoder.emitters.core.cp21_auth_ui.angular",
        "AngularAuthUIEmitter",
        None,
    ),
    # CP22 – Real-time UI (React)
    "cp22.react": (
        "midicoder.emitters.core.cp22_realtime_ui.react",
        "RealtimeComponentEmitter",
        "cp22_realtime",
    ),
    # CP22 – Real-time UI (Angular)
    "cp22.angular": (
        "midicoder.emitters.core.cp22_realtime_ui.angular",
        "AngularRealtimeEmitter",
        "cp22_realtime",
    ),
    # CP24 – Quality & Security (FastAPI)
    "cp24.quality.fastapi": (
        "midicoder.emitters.core.cp24_quality_security.fastapi",
        "FastAPIQualityEmitter",
        "cp24_quality",
    ),
    # CP24 – Quality & Security (NestJS)
    "cp24.quality.nestjs": (
        "midicoder.emitters.core.cp24_quality_security.nestjs",
        "NestJSQualityEmitter",
        "cp24_quality",
    ),
    # CP24 – Quality & Security (Angular)
    "cp24.quality.angular": (
        "midicoder.emitters.core.cp24_quality_security.angular",
        "AngularQualityEmitter",
        "cp24_quality",
    ),
    # CP24 – Quality & Security (React)
    "cp24.quality.react": (
        "midicoder.emitters.core.cp24_quality_security.react",
        "ReactQualityEmitter",
        "cp24_quality",
    ),
    # CP34 – Report & Document (FastAPI)
    "cp34.report.fastapi": (
        "midicoder.emitters.core.cp34_reporting.fastapi",
        "FastAPIReportEmitter",
        "cp34_report",
    ),
    # CP34 – Report & Document (NestJS)
    "cp34.report.nestjs": (
        "midicoder.emitters.core.cp34_reporting.nestjs",
        "NestJSReportEmitter",
        "cp34_report",
    ),
    # CP34 – Report & Document (Angular)
    "cp34.report.angular": (
        "midicoder.emitters.core.cp34_reporting.angular",
        "AngularReportEmitter",
        "cp34_report",
    ),
    # CP34 – Report & Document (React)
    "cp34.report.react": (
        "midicoder.emitters.core.cp34_reporting.react",
        "ReactReportEmitter",
        "cp34_report",
    ),
    # CP35 – Geospatial Services (FastAPI)
    "cp35.geospatial.fastapi": (
        "midicoder.emitters.core.cp35_geospatial.fastapi",
        "FastAPIGeospatialEmitter",
        "cp35_geospatial",
    ),
    # CP35 – Geospatial Services (NestJS)
    "cp35.geospatial.nestjs": (
        "midicoder.emitters.core.cp35_geospatial.nestjs",
        "NestJSGeospatialEmitter",
        "cp35_geospatial",
    ),
    # CP35 – Geospatial Services (Angular)
    "cp35.geospatial.angular": (
        "midicoder.emitters.core.cp35_geospatial.angular",
        "AngularGeospatialEmitter",
        "cp35_geospatial",
    ),
    # CP35 – Geospatial Services (React)
    "cp35.geospatial.react": (
        "midicoder.emitters.core.cp35_geospatial.react",
        "ReactGeospatialEmitter",
        "cp35_geospatial",
    ),
    # CP43 – Versioning & History (FastAPI)
    "cp43.versioning.fastapi": (
        "midicoder.emitters.core.cp43_versioning.fastapi",
        "FastAPIVersioningEmitter",
        None,
    ),
    # CP43 – Versioning & History (NestJS)
    "cp43.versioning.nestjs": (
        "midicoder.emitters.core.cp43_versioning.nestjs",
        "NestJSVersioningEmitter",
        None,
    ),
    # CP43 – Versioning & History (Angular)
    "cp43.versioning.angular": (
        "midicoder.emitters.core.cp43_versioning.angular",
        "AngularVersioningEmitter",
        None,
    ),
    # CP43 – Versioning & History (React)
    "cp43.versioning.react": (
        "midicoder.emitters.core.cp43_versioning.react",
        "ReactVersioningEmitter",
        None,
    ),
    # CP33 – Financial Engine (FastAPI)
    "cp33.financial.fastapi": (
        "midicoder.emitters.core.cp33_financial.fastapi",
        "FinancialFastAPIEmitter",
        "cp33_financial",
    ),
    # CP33 – Financial Engine (NestJS)
    "cp33.financial.nestjs": (
        "midicoder.emitters.core.cp33_financial.nestjs",
        "FinancialNestJSEmitter",
        "cp33_financial",
    ),
    # CP33 – Financial Engine (Angular)
    "cp33.financial.angular": (
        "midicoder.emitters.core.cp33_financial.angular",
        "FinancialAngularEmitter",
        "cp33_financial",
    ),
    # CP33 – Financial Engine (React)
    "cp33.financial.react": (
        "midicoder.emitters.core.cp33_financial.react",
        "FinancialReactEmitter",
        "cp33_financial",
    ),
    # CP36 – Tenant Onboarding (FastAPI)
    "cp36.onboarding.fastapi": (
        "midicoder.emitters.core.cp36_tenant_onboarding.fastapi",
        "TenantOnboardingFastAPIEmitter",
        "cp36_onboarding",
    ),
    # CP36 – Tenant Onboarding (NestJS)
    "cp36.onboarding.nestjs": (
        "midicoder.emitters.core.cp36_tenant_onboarding.nestjs",
        "TenantOnboardingNestJSEmitter",
        "cp36_onboarding",
    ),
    # CP36 – Tenant Onboarding (Angular)
    "cp36.onboarding.angular": (
        "midicoder.emitters.core.cp36_tenant_onboarding.angular",
        "TenantOnboardingAngularEmitter",
        "cp36_onboarding",
    ),
    # CP36 – Tenant Onboarding (React)
    "cp36.onboarding.react": (
        "midicoder.emitters.core.cp36_tenant_onboarding.react",
        "TenantOnboardingReactEmitter",
        "cp36_onboarding",
    ),
    # CP37 – Feature Flags (FastAPI)
    "cp37.feature_flags.fastapi": (
        "midicoder.emitters.core.cp37_feature_flags.fastapi",
        "FastAPIFeatureFlagEmitter",
        "cp37_feature_flags",
    ),
    # CP37 – Feature Flags (NestJS)
    "cp37.feature_flags.nestjs": (
        "midicoder.emitters.core.cp37_feature_flags.nestjs",
        "NestJSFeatureFlagEmitter",
        "cp37_feature_flags",
    ),
    # CP37 – Feature Flags (Angular)
    "cp37.feature_flags.angular": (
        "midicoder.emitters.core.cp37_feature_flags.angular",
        "AngularFeatureFlagEmitter",
        "cp37_feature_flags",
    ),
    # CP37 – Feature Flags (React)
    "cp37.feature_flags.react": (
        "midicoder.emitters.core.cp37_feature_flags.react",
        "ReactFeatureFlagEmitter",
        "cp37_feature_flags",
    ),
    # CP44 – Bulk Operations (FastAPI)
    "cp44.bulk_ops.fastapi": (
        "midicoder.emitters.core.cp44_bulk_ops.fastapi",
        "FastAPIBulkOpsEmitter",
        "cp44_bulk_ops",
    ),
    # CP44 – Bulk Operations (NestJS)
    "cp44.bulk_ops.nestjs": (
        "midicoder.emitters.core.cp44_bulk_ops.nestjs",
        "NestJSBulkOpsEmitter",
        "cp44_bulk_ops",
    ),
    # CP44 – Bulk Operations (Angular)
    "cp44.bulk_ops.angular": (
        "midicoder.emitters.core.cp44_bulk_ops.angular",
        "AngularBulkOpsEmitter",
        "cp44_bulk_ops",
    ),
    # CP44 – Bulk Operations (React)
    "cp44.bulk_ops.react": (
        "midicoder.emitters.core.cp44_bulk_ops.react",
        "ReactBulkOpsEmitter",
        "cp44_bulk_ops",
    ),
    # CP45 – Payment (FastAPI)
    "cp45.payment.fastapi": (
        "midicoder.emitters.core.cp45_payment.fastapi",
        "FastAPIPaymentEmitter",
        "cp45_payment",
    ),
    # CP45 – Payment (NestJS)
    "cp45.payment.nestjs": (
        "midicoder.emitters.core.cp45_payment.nestjs",
        "NestJSPaymentEmitter",
        "cp45_payment",
    ),
    # CP45 – Payment (Angular)
    "cp45.payment.angular": (
        "midicoder.emitters.core.cp45_payment.angular",
        "AngularPaymentEmitter",
        "cp45_payment",
    ),
    # CP45 – Payment (React)
    "cp45.payment.react": (
        "midicoder.emitters.core.cp45_payment.react",
        "ReactPaymentEmitter",
        "cp45_payment",
    ),
    # CP58 – Data Encryption (FastAPI)
    "cp58.encryption.fastapi": (
        "midicoder.emitters.core.cp58_encryption.fastapi",
        "FastAPIEncryptionEmitter",
        "cp58_encryption",
    ),
    # CP58 – Data Encryption (NestJS)
    "cp58.encryption.nestjs": (
        "midicoder.emitters.core.cp58_encryption.nestjs",
        "NestJSEncryptionEmitter",
        "cp58_encryption",
    ),
    # CP59 – Tenant Billing (FastAPI)
    "cp59.billing.fastapi": (
        "midicoder.emitters.core.cp59_tenant_billing.fastapi",
        "FastAPITenantBillingEmitter",
        "cp59_tenant_billing",
    ),
    # CP59 – Tenant Billing (NestJS)
    "cp59.billing.nestjs": (
        "midicoder.emitters.core.cp59_tenant_billing.nestjs",
        "NestJSTenantBillingEmitter",
        "cp59_tenant_billing",
    ),
    # CP46 – MFA (FastAPI)
    "cp46.mfa.fastapi": (
        "midicoder.emitters.core.cp46_mfa.fastapi",
        "FastAPIMFAEmitter",
        "cp46_mfa",
    ),
    # CP46 – MFA (NestJS)
    "cp46.mfa.nestjs": (
        "midicoder.emitters.core.cp46_mfa.nestjs",
        "NestJSMFAEmitter",
        "cp46_mfa",
    ),
    # CP46 – MFA (Angular)
    "cp46.mfa.angular": (
        "midicoder.emitters.core.cp46_mfa.angular",
        "AngularMFAEmitter",
        "cp46_mfa",
    ),
    # CP46 – MFA (React)
    "cp46.mfa.react": (
        "midicoder.emitters.core.cp46_mfa.react",
        "ReactMFAEmitter",
        "cp46_mfa",
    ),
    # CP48 – Rate Limit (FastAPI)
    "cp48.rate_limit.fastapi": (
        "midicoder.emitters.core.cp48_rate_limit.fastapi",
        "FastAPIRateLimitEmitter",
        "cp48_rate_limit",
    ),
    # CP48 – Rate Limit (NestJS)
    "cp48.rate_limit.nestjs": (
        "midicoder.emitters.core.cp48_rate_limit.nestjs",
        "NestJSRateLimitEmitter",
        "cp48_rate_limit",
    ),
    # CP48 – Rate Limit (Angular)
    "cp48.rate_limit.angular": (
        "midicoder.emitters.core.cp48_rate_limit.angular",
        "AngularRateLimitEmitter",
        "cp48_rate_limit",
    ),
    # CP48 – Rate Limit (React)
    "cp48.rate_limit.react": (
        "midicoder.emitters.core.cp48_rate_limit.react",
        "ReactRateLimitEmitter",
        "cp48_rate_limit",
    ),
    # CP49 – Consent (FastAPI)
    "cp49.consent.fastapi": (
        "midicoder.emitters.core.cp49_consent.fastapi",
        "FastAPIConsentEmitter",
        "cp49_consent",
    ),
    # CP49 – Consent (NestJS)
    "cp49.consent.nestjs": (
        "midicoder.emitters.core.cp49_consent.nestjs",
        "NestJSConsentEmitter",
        "cp49_consent",
    ),
    # CP49 – Consent (Angular)
    "cp49.consent.angular": (
        "midicoder.emitters.core.cp49_consent.angular",
        "AngularConsentEmitter",
        "cp49_consent",
    ),
    # CP49 – Consent (React)
    "cp49.consent.react": (
        "midicoder.emitters.core.cp49_consent.react",
        "ReactConsentEmitter",
        "cp49_consent",
    ),
    # CP50 – Catalog (FastAPI)
    "cp50.catalog.fastapi": (
        "midicoder.emitters.core.cp50_catalog.fastapi",
        "FastAPICatalogEmitter",
        "cp50_catalog",
    ),
    # CP50 – Catalog (NestJS)
    "cp50.catalog.nestjs": (
        "midicoder.emitters.core.cp50_catalog.nestjs",
        "NestJSCatalogEmitter",
        "cp50_catalog",
    ),
    # CP50 – Catalog (Angular)
    "cp50.catalog.angular": (
        "midicoder.emitters.core.cp50_catalog.angular",
        "AngularCatalogEmitter",
        "cp50_catalog",
    ),
    # CP12 – Notification (FastAPI)
    "cp12.notification.fastapi": (
        "midicoder.emitters.core.cp12_notification.fastapi",
        "FastAPINotificationEmitter",
        "cp12_notification",
    ),
    # CP12 – Notification (NestJS)
    "cp12.notification.nestjs": (
        "midicoder.emitters.core.cp12_notification.nestjs",
        "NestJSNotificationEmitter",
        "cp12_notification",
    ),
    # CP12 – Notification (Angular)
    "cp12.notification.angular": (
        "midicoder.emitters.core.cp12_notification.angular",
        "AngularNotificationEmitter",
        "cp12_notification",
    ),
    # CP12 – Notification (React)
    "cp12.notification.react": (
        "midicoder.emitters.core.cp12_notification.react",
        "ReactNotificationEmitter",
        "cp12_notification",
    ),
    # CP13 – Workflow (FastAPI)
    "cp13.workflow.fastapi": (
        "midicoder.emitters.core.cp13_workflow_runtime.fastapi",
        "WorkflowFastAPIEmitter",
        None,
    ),
    # CP13 – Workflow (NestJS)
    "cp13.workflow.nestjs": (
        "midicoder.emitters.core.cp13_workflow_runtime.nestjs",
        "WorkflowNestJSEmitter",
        None,
    ),
    # CP14 – Audit Compliance (FastAPI)
    "cp14.audit_compliance.fastapi": (
        "midicoder.emitters.core.cp14_audit_compliance.fastapi",
        "FastAPIAuditComplianceEmitter",
        "cp14_audit_compliance",
    ),
    # CP14 – Audit Compliance (NestJS)
    "cp14.audit_compliance.nestjs": (
        "midicoder.emitters.core.cp14_audit_compliance.nestjs",
        "NestJSAuditComplianceEmitter",
        "cp14_audit_compliance",
    ),
    # CP14 – Audit Compliance (Angular)
    "cp14.audit_compliance.angular": (
        "midicoder.emitters.core.cp14_audit_compliance.angular",
        "AngularAuditComplianceEmitter",
        "cp14_audit_compliance",
    ),
    # CP14 – Audit Compliance (React)
    "cp14.audit_compliance.react": (
        "midicoder.emitters.core.cp14_audit_compliance.react",
        "ReactAuditComplianceEmitter",
        "cp14_audit_compliance",
    ),
    # CP15 – Observability (FastAPI)
    "cp15.observability.fastapi": (
        "midicoder.emitters.core.cp15_observability.fastapi",
        "FastAPIObservabilityEmitter",
        "cp15_observability",
    ),
    # CP15 – Observability (NestJS)
    "cp15.observability.nestjs": (
        "midicoder.emitters.core.cp15_observability.nestjs",
        "NestJSObservabilityEmitter",
        "cp15_observability",
    ),
    # CP15 – Observability (Angular)
    "cp15.observability.angular": (
        "midicoder.emitters.core.cp15_observability.angular",
        "AngularObservabilityEmitter",
        "cp15_observability",
    ),
    # CP15 – Observability (React)
    "cp15.observability.react": (
        "midicoder.emitters.core.cp15_observability.react",
        "ReactObservabilityEmitter",
        "cp15_observability",
    ),
    # CP40 – Webhook (FastAPI)
    "cp40.webhook.fastapi": (
        "midicoder.emitters.core.cp40_webhook.fastapi",
        "FastAPIWebhookEmitter",
        "cp40_webhook",
    ),
    # CP40 – Webhook (NestJS)
    "cp40.webhook.nestjs": (
        "midicoder.emitters.core.cp40_webhook.nestjs",
        "NestJSWebhookEmitter",
        "cp40_webhook",
    ),
    # CP40 – Webhook (Angular)
    "cp40.webhook.angular": (
        "midicoder.emitters.core.cp40_webhook.angular",
        "AngularWebhookEmitter",
        "cp40_webhook",
    ),
    # CP40 – Webhook (React)
    "cp40.webhook.react": (
        "midicoder.emitters.core.cp40_webhook.react",
        "ReactWebhookEmitter",
        "cp40_webhook",
    ),
    # CP42 – Approval (FastAPI)
    "cp42.approval.fastapi": (
        "midicoder.emitters.core.cp42_approval.fastapi",
        "FastAPIApprovalEmitter",
        "cp42_approval",
    ),
    # CP42 – Approval (NestJS)
    "cp42.approval.nestjs": (
        "midicoder.emitters.core.cp42_approval.nestjs",
        "NestJSApprovalEmitter",
        "cp42_approval",
    ),
    # CP42 – Approval (Angular)
    "cp42.approval.angular": (
        "midicoder.emitters.core.cp42_approval.angular",
        "AngularApprovalEmitter",
        "cp42_approval",
    ),
    # CP42 – Approval (React)
    "cp42.approval.react": (
        "midicoder.emitters.core.cp42_approval.react",
        "ReactApprovalEmitter",
        "cp42_approval",
    ),
    # CP47 – Retention (FastAPI)
    "cp47.retention.fastapi": (
        "midicoder.emitters.core.cp47_retention.fastapi",
        "FastAPIRetentionEmitter",
        "cp47_retention",
    ),
    # CP47 – Retention (NestJS)
    "cp47.retention.nestjs": (
        "midicoder.emitters.core.cp47_retention.nestjs",
        "NestJSRetentionEmitter",
        "cp47_retention",
    ),
    # CP47 – Retention (Angular)
    "cp47.retention.angular": (
        "midicoder.emitters.core.cp47_retention.angular",
        "AngularRetentionEmitter",
        "cp47_retention",
    ),
    # CP47 – Retention (React)
    "cp47.retention.react": (
        "midicoder.emitters.core.cp47_retention.react",
        "ReactRetentionEmitter",
        "cp47_retention",
    ),
    # CP56 – Environment & Secrets (FastAPI)
    "cp56.env_secrets.fastapi": (
        "midicoder.emitters.core.cp56_env_secrets.fastapi",
        "FastAPIEnvEmitter",
        "cp56_env_secrets",
    ),
    # CP56 – Environment & Secrets (NestJS)
    "cp56.env_secrets.nestjs": (
        "midicoder.emitters.core.cp56_env_secrets.nestjs",
        "NestJSSEnvEmitter",
        "cp56_env_secrets",
    ),
    # CP56 – Environment & Secrets (Infrastructure)
    "cp56.env_secrets.infrastructure": (
        "midicoder.emitters.core.cp56_env_secrets.infrastructure",
        "EnvInfrastructureEmitter",
        "cp56_env_secrets",
    ),
    # CP54 – Kubernetes (Infrastructure)
    "cp54.kubernetes.infrastructure": (
        "midicoder.emitters.core.cp54_kubernetes.infrastructure",
        "K8sInfrastructureEmitter",
        "cp54_kubernetes",
    ),
    # CP54 – Kubernetes (FastAPI)
    "cp54.kubernetes.fastapi": (
        "midicoder.emitters.core.cp54_kubernetes.fastapi",
        "FastAPIK8sEmitter",
        "cp54_kubernetes",
    ),
    # CP54 – Kubernetes (NestJS)
    "cp54.kubernetes.nestjs": (
        "midicoder.emitters.core.cp54_kubernetes.nestjs",
        "NestJSK8sEmitter",
        "cp54_kubernetes",
    ),
    # CP55 – CI/CD Pipeline (Infrastructure)
    "cp55.cicd.infrastructure": (
        "midicoder.emitters.core.cp55_cicd.infrastructure",
        "CICDInfrastructureEmitter",
        "cp55_cicd",
    ),
    # CP61 – Distributed Tracing (FastAPI)
    "cp61.distributed_tracing.fastapi": (
        "midicoder.emitters.core.cp61_distributed_tracing.fastapi",
        "FastAPITracingEmitter",
        "cp61_distributed_tracing",
    ),
    # CP61 – Distributed Tracing (NestJS)
    "cp61.distributed_tracing.nestjs": (
        "midicoder.emitters.core.cp61_distributed_tracing.nestjs",
        "NestJSTracingEmitter",
        "cp61_distributed_tracing",
    ),
    # CP57 – GraphQL Schema Federation (FastAPI)
    "cp57.graphql_federation.fastapi": (
        "midicoder.emitters.core.cp57_graphql_federation.fastapi",
        "FastAPIFederationEmitter",
        "cp57_graphql_federation",
    ),
    # CP57 – GraphQL Schema Federation (NestJS)
    "cp57.graphql_federation.nestjs": (
        "midicoder.emitters.core.cp57_graphql_federation.nestjs",
        "NestJSFederationEmitter",
        "cp57_graphql_federation",
    ),
    # CP60 – Service Discovery (FastAPI)
    "cp60.service_discovery.fastapi": (
        "midicoder.emitters.core.cp60_service_discovery.fastapi",
        "FastAPIServiceDiscoveryEmitter",
        "cp60_service_discovery",
    ),
    # CP60 – Service Discovery (NestJS)
    "cp60.service_discovery.nestjs": (
        "midicoder.emitters.core.cp60_service_discovery.nestjs",
        "NestJSServiceDiscoveryEmitter",
        "cp60_service_discovery",
    ),
    # CP62 – Mobile Backend (FastAPI)
    "cp62.mobile_backend.fastapi": (
        "midicoder.emitters.core.cp62_mobile_backend.fastapi",
        "FastAPIMobileBackendEmitter",
        "cp62_mobile_backend",
    ),
    # CP62 – Mobile Backend (NestJS)
    "cp62.mobile_backend.nestjs": (
        "midicoder.emitters.core.cp62_mobile_backend.nestjs",
        "NestJSMobileBackendEmitter",
        "cp62_mobile_backend",
    ),
    # CP63 – Recommendation (FastAPI)
    "cp63.recommendation.fastapi": (
        "midicoder.emitters.core.cp63_recommendation.fastapi",
        "FastAPIRecommendationEmitter",
        "cp63_recommendation",
    ),
    # CP63 – Recommendation (NestJS)
    "cp63.recommendation.nestjs": (
        "midicoder.emitters.core.cp63_recommendation.nestjs",
        "NestJSRecommendationEmitter",
        "cp63_recommendation",
    ),
    # CP28 — Multi-Region (FastAPI)
    "cp28.multi_region.fastapi": (
        "midicoder.emitters.core.cp28_multi_region.fastapi",
        "FastAPIMultiRegionEmitter",
        "cp28_multi_region",
    ),
    # CP28 — Multi-Region (NestJS)
    "cp28.multi_region.nestjs": (
        "midicoder.emitters.core.cp28_multi_region.nestjs",
        "NestJSMultiRegionEmitter",
        "cp28_multi_region",
    ),
    # CP28 — Multi-Region (Infrastructure)
    "cp28.multi_region.infrastructure": (
        "midicoder.emitters.core.cp28_multi_region.infrastructure",
        "MultiRegionInfrastructureEmitter",
        "cp28_multi_region",
    ),
    # CP64 — API Contract Testing (FastAPI)
    "cp64.contract.fastapi": (
        "midicoder.emitters.core.cp64_contract_testing.fastapi",
        "FastAPIContractEmitter",
        "cp64_contract_testing",
    ),
    # CP64 — API Contract Testing (NestJS)
    "cp64.contract.nestjs": (
        "midicoder.emitters.core.cp64_contract_testing.nestjs",
        "NestJSContractEmitter",
        "cp64_contract_testing",
    ),
    # CP65 — Data Backup & Recovery (FastAPI)
    "cp65.backup.fastapi": (
        "midicoder.emitters.core.cp65_backup_recovery.fastapi",
        "FastAPIBackupEmitter",
        "cp65_backup_recovery",
    ),
    # CP65 — Data Backup & Recovery (NestJS)
    "cp65.backup.nestjs": (
        "midicoder.emitters.core.cp65_backup_recovery.nestjs",
        "NestJSBackupEmitter",
        "cp65_backup_recovery",
    ),
    # CP65 — Data Backup & Recovery (Infrastructure)
    "cp65.backup.infrastructure": (
        "midicoder.emitters.core.cp65_backup_recovery.infrastructure",
        "BackupInfrastructureEmitter",
        "cp65_backup_recovery",
    ),
}


# ---------------------------------------------------------------------------
# Parser registry: parser_key → callable(raw_dict) → dataclass
# ---------------------------------------------------------------------------

def _parse_entity_dict(raw: dict[str, Any]) -> Any:
    """Parse a raw entity dict from MIR metadata into a CP01 Entity dataclass."""
    from midicoder.emitters.core.cp01_domain_model.entity_parser import EntityParser
    parser = EntityParser()

    # EntityParser expects a YAML-like dict with "entities" key.
    # MIR metadata stores entities as a flat list of dicts, so wrap it.
    import yaml
    yaml_safe = {
        "entities": [raw],
    }
    yaml_str = yaml.dump(yaml_safe)
    entities = parser.parse(yaml_str)
    return entities[0] if entities else None


def _parse_database_dict(raw: dict[str, Any]) -> Any:
    """Parse a raw database dict from MIR metadata into a CP08 DataModelCollection."""
    from midicoder.emitters.core.cp08_database.parser import DBParser
    parser = DBParser()
    return parser.parse_from_metadata(raw)


def _parse_auth_dict(raw: dict[str, Any]) -> Any:
    """Parse a raw auth dict from MIR metadata into a CP03 AuthIR dataclass."""
    from midicoder.emitters.core.cp03_auth.parser import AuthParser
    import yaml

    # AuthParser expects a file path, but we have raw dict — create a minimal
    # YAML structure and use the internal parse methods.
    yaml_safe = raw if "authentication" in raw else {
        "authentication": {"providers": raw.get("providers", [])},
    }
    yaml_str = yaml.dump(yaml_safe)

    # Use a temp file for AuthParser
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False, encoding="utf-8") as f:
        f.write(yaml_str)
        f.flush()
        parser = AuthParser(f.name)
        auth_ir = parser.parse()
    import os
    os.unlink(f.name)
    return auth_ir


def _parse_search_dict(raw: dict[str, Any]) -> Any:
    """Parse raw MIR metadata into a CP10 SearchCollection."""
    from midicoder.emitters.core.cp10_search.parser import SearchParser
    parser = SearchParser()
    return parser.parse_from_metadata(raw)


def _parse_event_dict(raw: dict[str, Any]) -> Any:
    """Parse raw event dict from MIR metadata into a CP05 EventDefinition list."""
    from midicoder.emitters.core.cp05_event_driven.parser import EventParser
    parser = EventParser()
    # MIR metadata stores events as a list of dicts — pass directly
    if isinstance(raw, list):
        return parser.parse(raw)
    # If it's a single dict, wrap in list
    return parser.parse([raw])


def _parse_cache_dict(raw: dict[str, Any]) -> Any:
    """Parse raw MIR metadata into a CP09 CacheCollection."""
    from midicoder.emitters.core.cp09_cache.parser import CacheParser
    parser = CacheParser()
    return parser.parse_from_metadata(raw)


def _parse_gateway_dict(raw: dict[str, Any]) -> Any:
    """Parse raw MIR metadata into a CP06 RouteCollection."""
    from midicoder.emitters.core.cp06_api_gateway.route_parser import RouteParser
    parser = RouteParser()
    return parser.parse_from_metadata(
        routes_data=raw.get("routes"),
        graphql_data=raw.get("graphql"),
        webhooks_data=raw.get("webhooks"),
    )


def _parse_frontend_dict(raw: dict[str, Any]) -> Any:
    """Parse raw frontend dict from DSL/MIR into CP18 FrontendApp dataclass."""
    from midicoder.emitters.core.cp18_frontend_framework.parser import FrontendFrameworkParser
    import yaml

    # FrontendFrameworkParser expects a YAML string — serialize the raw dict
    yaml_str = yaml.dump(raw)
    parser = FrontendFrameworkParser()
    result = parser.parse(yaml_str)
    return result.get("frontend_app")


def _parse_ui_component_dict(raw: dict[str, Any]) -> Any:
    """Parse raw UI component dict from DSL/MIR into CP19 ComponentSpec list."""
    from midicoder.emitters.core.cp19_ui_components.models import ComponentSpec

    # raw can be a single dict or a list of dicts
    if isinstance(raw, list):
        return [ComponentSpec.from_dict(item) for item in raw if isinstance(item, dict)]
    elif isinstance(raw, dict):
        # If it has a "components" key, unwrap it
        if "components" in raw:
            return [ComponentSpec.from_dict(item) for item in raw["components"]]
        # Otherwise treat as single ComponentSpec
        return [ComponentSpec.from_dict(raw)]
    return []


def _parse_realtime_dict(raw: dict[str, Any]) -> Any:
    """Parse raw realtime events dict from CP05/MIR into CP22 ChannelSpec list."""
    from midicoder.emitters.core.cp22_realtime_ui.parser import RealtimeParser
    parser = RealtimeParser()
    # raw can be list of event dicts, or a dict with 'events' key
    if isinstance(raw, list):
        return parser.parse(raw)
    elif isinstance(raw, dict):
        events = raw.get("events", raw.get("channels", []))
        return parser.parse(events) if events else []
    return []


def _parse_quality_dict(raw: dict[str, Any]) -> Any:
    """Parse raw quality config dict from DSL/MIR into CP24 QualityCollection."""
    from midicoder.emitters.core.cp24_quality_security.parser import QualityProfileParser
    parser = QualityProfileParser()
    return parser.parse_from_metadata(raw)


def _parse_report_dict(raw: dict[str, Any]) -> Any:
    """Parse raw report dict from DSL/MIR into CP34 ReportCollection."""
    from midicoder.emitters.core.cp34_reporting.parser import ReportParser
    parser = ReportParser()
    return parser.parse_from_metadata(raw)


def _parse_geospatial_dict(raw: dict[str, Any]) -> Any:
    """Parse raw geospatial dict from DSL/MIR into CP35 GeospatialCollection."""
    from midicoder.emitters.core.cp35_geospatial.parser import GeospatialParser
    parser = GeospatialParser()
    return parser.parse_from_metadata(raw)


def _parse_financial_dict(raw: dict[str, Any]) -> Any:
    """Parse raw financial dict from DSL/MIR into CP33 FinancialIR — qua FinancialParser."""
    from midicoder.emitters.core.cp33_financial.parser import FinancialParser
    return FinancialParser.parse_to_ir(raw) if isinstance(raw, dict) else []


def _parse_onboarding_dict(raw: dict[str, Any]) -> Any:
    """Parse raw onboarding dict from DSL/MIR into CP36 OnboardingIR."""
    from midicoder.emitters.core.cp36_tenant_onboarding.parser import parse_onboarding_dsl
    return parse_onboarding_dsl(raw)


def _parse_feature_flag_dict(raw: dict[str, Any]) -> Any:
    """Parse raw feature flag dict from DSL/MIR into CP37 FeatureFlagIR."""
    from midicoder.emitters.core.cp37_feature_flags.parser import FeatureFlagIR
    return FeatureFlagIR.from_dict(raw) if isinstance(raw, dict) else []


def _parse_bulk_ops_dict(raw: dict[str, Any]) -> Any:
    """Parse raw bulk ops dict from DSL/MIR into CP44 BulkIR."""
    from midicoder.emitters.core.cp44_bulk_ops.parser import BulkIR
    return BulkIR.from_dict(raw) if isinstance(raw, dict) else []


def _parse_payment_dict(raw: dict[str, Any]) -> Any:
    """Parse raw payment dict from DSL/MIR into CP45 PaymentIR."""
    from midicoder.emitters.core.cp45_payment.parser import PaymentIR
    return PaymentIR.from_dict(raw) if isinstance(raw, dict) else []


def _parse_tenant_billing_dict(raw: dict[str, Any]) -> Any:
    """Parse raw tenant billing dict from DSL/MIR into CP59 BillingIR."""
    from midicoder.emitters.core.cp59_tenant_billing.parser import BillingIR
    return BillingIR.from_dict(raw) if isinstance(raw, dict) else []


def _parse_mfa_dict(raw: dict[str, Any]) -> Any:
    """Parse raw mfa dict from DSL/MIR into CP46 MFAIR."""
    from midicoder.emitters.core.cp46_mfa.parser import MFAIR
    return MFAIR.from_dict(raw) if isinstance(raw, dict) else []


def _parse_rate_limit_dict(raw: dict[str, Any]) -> Any:
    """Parse raw rate limit dict from DSL/MIR into CP48 RateLimitIR — qua RateLimitParser."""
    from midicoder.emitters.core.cp48_rate_limit.parser import RateLimitParser
    return RateLimitParser.parse_to_ir(raw) if isinstance(raw, dict) else []


def _parse_consent_dict(raw: dict[str, Any]) -> Any:
    """Parse raw consent dict from DSL/MIR into CP49 ConsentIR."""
    from midicoder.emitters.core.cp49_consent.parser import ConsentIR
    return ConsentIR.from_dict(raw) if isinstance(raw, dict) else []


def _parse_notification_dict(raw: dict[str, Any]) -> Any:
    """Parse raw notification dict from DSL/MIR into CP12 Notification list."""
    from midicoder.emitters.core.cp12_notification.parser import (
        parse_channels,
        parse_notifications,
        parse_providers,
    )
    return {
        "notifications": parse_notifications(raw) if isinstance(raw, dict) else [],
        "providers": parse_providers(raw) if isinstance(raw, dict) else [],
        "channels": parse_channels(raw) if isinstance(raw, dict) else {},
        "webhooks": raw.get("webhooks", []) if isinstance(raw, dict) else [],
    }


def _parse_audit_dict(raw: dict[str, Any]) -> Any:
    """Parse raw audit dict from DSL/MIR into CP14 AuditComplianceCollection."""
    from midicoder.emitters.core.cp14_audit_compliance.parser import (
        AuditComplianceParser,
    )
    import yaml
    parser = AuditComplianceParser()
    yaml_str = yaml.dump(raw) if isinstance(raw, dict) else raw
    return parser.parse(yaml_str) if yaml_str else {}


def _parse_observability_dict(raw: dict[str, Any]) -> Any:
    """Parse raw observability dict from DSL/MIR into CP15 Observability dict."""
    from midicoder.emitters.core.cp15_observability.parser import ObservabilityParser
    parser = ObservabilityParser()
    if isinstance(raw, dict):
        import yaml
        yaml_str = yaml.dump(raw)
        return parser.parse(yaml_str)
    return {}


def _parse_webhook_dict(raw: dict[str, Any]) -> Any:
    """Parse raw webhook dict from DSL/MIR into CP40 WebhookIR."""
    from midicoder.emitters.core.cp40_webhook.parser import WebhookIR
    return WebhookIR.from_dict(raw) if isinstance(raw, dict) else []


def _parse_approval_dict(raw: dict[str, Any]) -> Any:
    """Parse raw approval dict from DSL/MIR into CP42 ApprovalIR."""
    from midicoder.emitters.core.cp42_approval.parser import ApprovalIR
    return ApprovalIR.from_dict(raw) if isinstance(raw, dict) else []


def _parse_retention_dict(raw: dict[str, Any]) -> Any:
    """Parse raw retention dict from DSL/MIR into CP47 RetentionIR."""
    from midicoder.emitters.core.cp47_retention.parser import RetentionIR
    return RetentionIR.from_dict(raw) if isinstance(raw, dict) else []


def _parse_catalog_dict(raw: dict[str, Any]) -> Any:
    """Parse raw catalog dict from DSL/MIR into CP50 CatalogIR."""
    from midicoder.emitters.core.cp50_catalog.parser import CatalogIR
    return CatalogIR.from_dict(raw) if isinstance(raw, dict) else []


def _parse_env_secrets_dict(raw: dict[str, Any]) -> Any:
    """Parse raw env secrets dict from DSL/MIR into CP56 EnvIR."""
    from midicoder.emitters.core.cp56_env_secrets.parser import EnvIR
    return EnvIR.from_dict(raw) if isinstance(raw, dict) else []


def _parse_kubernetes_dict(raw: dict[str, Any]) -> Any:
    """Parse raw kubernetes dict from DSL/MIR into CP54 K8sIR."""
    from midicoder.emitters.core.cp54_kubernetes.parser import K8sIR
    return K8sIR.from_dict(raw) if isinstance(raw, dict) else []


def _parse_cicd_dict(raw: dict[str, Any]) -> Any:
    """Parse raw CI/CD dict from DSL/MIR into CP55 CIIR."""
    from midicoder.emitters.core.cp55_cicd.parser import CIIR
    return CIIR.from_dict(raw) if isinstance(raw, dict) else []


def _parse_encryption_dict(raw: dict[str, Any]) -> Any:
    """Parse raw encryption dict from DSL/MIR into CP58 EncryptionIR."""
    from midicoder.emitters.core.cp58_encryption.parser import EncryptionIR
    return EncryptionIR.from_dict(raw) if isinstance(raw, dict) else []


def _parse_distributed_tracing_dict(raw: dict[str, Any]) -> Any:
    """Parse raw distributed tracing dict from DSL/MIR into CP61 TracingIR."""
    from midicoder.emitters.core.cp61_distributed_tracing.parser import TracingIR
    return TracingIR.from_dict(raw) if isinstance(raw, dict) else []


def _parse_graphql_federation_dict(raw: dict[str, Any]) -> Any:
    """Parse raw GraphQL Federation dict from DSL/MIR into CP57 GraphQLIR."""
    from midicoder.emitters.core.cp57_graphql_federation.parser import GraphQLIR
    return GraphQLIR.from_dict(raw) if isinstance(raw, dict) else []


def _parse_service_discovery_dict(raw: dict[str, Any]) -> Any:
    """Parse raw service discovery dict from DSL/MIR into CP60 ServiceDiscoveryIR."""
    from midicoder.emitters.core.cp60_service_discovery.parser import ServiceDiscoveryIR
    return ServiceDiscoveryIR.from_dict(raw) if isinstance(raw, dict) else []


def _parse_recommendation_dict(raw: dict[str, Any]) -> Any:
    """Parse raw recommendation dict from DSL/MIR into CP63 RecommendationIR."""
    from midicoder.emitters.core.cp63_recommendation.parser import RecommendationIR
    return RecommendationIR.from_dict(raw) if isinstance(raw, dict) else []


def _parse_multi_region_dict(raw: dict[str, Any]) -> Any:
    """Parse raw multi-region dict from DSL/MIR into CP28 MultiRegionIR."""
    from midicoder.emitters.core.cp28_multi_region.parser import MultiRegionIR
    return MultiRegionIR.from_dict(raw) if isinstance(raw, dict) else []


def _parse_contract_testing_dict(raw: dict[str, Any]) -> Any:
    """Parse raw contract testing dict from DSL/MIR into CP64 ContractIR."""
    from midicoder.emitters.core.cp64_contract_testing.parser import ContractIR
    return ContractIR.from_dict(raw) if isinstance(raw, dict) else []


def _parse_backup_recovery_dict(raw: dict[str, Any]) -> Any:
    """Parse raw backup recovery dict from DSL/MIR into CP65 BackupIR."""
    from midicoder.emitters.core.cp65_backup_recovery.parser import BackupIR
    return BackupIR.from_dict(raw) if isinstance(raw, dict) else []


PARSER_REGISTRY: dict[str, Any] = {
    "cp01_entity": _parse_entity_dict,
    "cp08_database": _parse_database_dict,
    "cp03_auth": _parse_auth_dict,
    "cp10_search": _parse_search_dict,
    "cp05_event": _parse_event_dict,
    "cp09_cache": _parse_cache_dict,
    "cp06_gateway": _parse_gateway_dict,
    "cp18_frontend": _parse_frontend_dict,
    "cp19_ui_components": _parse_ui_component_dict,
    "cp22_realtime": _parse_realtime_dict,
    "cp24_quality": _parse_quality_dict,
    "cp34_report": _parse_report_dict,
    "cp35_geospatial": _parse_geospatial_dict,
    "cp33_financial": _parse_financial_dict,
    "cp36_onboarding": _parse_onboarding_dict,
    "cp37_feature_flags": _parse_feature_flag_dict,
    "cp44_bulk_ops": _parse_bulk_ops_dict,
    "cp45_payment": _parse_payment_dict,
    "cp59_tenant_billing": _parse_tenant_billing_dict,
    "cp46_mfa": _parse_mfa_dict,
    "cp48_rate_limit": _parse_rate_limit_dict,
    "cp49_consent": _parse_consent_dict,
    "cp50_catalog": _parse_catalog_dict,
    "cp12_notification": _parse_notification_dict,
    "cp14_audit_compliance": _parse_audit_dict,
    "cp15_observability": _parse_observability_dict,
    "cp40_webhook": _parse_webhook_dict,
    "cp42_approval": _parse_approval_dict,
    "cp47_retention": _parse_retention_dict,
    "cp54_kubernetes": _parse_kubernetes_dict,
    "cp55_cicd": _parse_cicd_dict,
    "cp56_env_secrets": _parse_env_secrets_dict,
    "cp58_encryption": _parse_encryption_dict,
    "cp61_distributed_tracing": _parse_distributed_tracing_dict,
    "cp57_graphql_federation": _parse_graphql_federation_dict,
    "cp60_service_discovery": _parse_service_discovery_dict,
    "cp63_recommendation": _parse_recommendation_dict,
    "cp28_multi_region": _parse_multi_region_dict,
    "cp64_contract_testing": _parse_contract_testing_dict,
    "cp65_backup_recovery": _parse_backup_recovery_dict,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


class PackEmitterRouter:
    """
    Dispatches FileSpecs to pack-specific emitters.

    The router resolves the stack-specific emitter class, instantiates it
    with the correct template directory, and calls its ``emit()`` method.
    If a parser key is registered, raw MIR dicts are converted to typed
    dataclasses before dispatch.
    """

    @staticmethod
    def dispatch(
        pack_emitter: str,
        file_spec: dict[str, Any],
        stack: str,
    ) -> list[dict[str, str]]:
        """
        Dispatch a single FileSpec to the appropriate pack emitter.

        Args:
            pack_emitter: Key in EMITTER_REGISTRY (e.g. "cp01.entity.fastapi")
            file_spec: FileSpec as dict (path, context, template, …)
            stack: Stack name ("fastapi", "nestjs", …)

        Returns:
            List of ``{"path": ..., "content": ...}`` — one entry per
            generated file.  Multi-file emitters (e.g. command emitter)
            may return more than one entry.
        """
        if pack_emitter not in EMITTER_REGISTRY:
            raise KeyError(
                f"Unknown pack_emitter '{pack_emitter}'. "
                f"Available: {list(EMITTER_REGISTRY.keys())}"
            )

        module_path, class_name, parser_key = EMITTER_REGISTRY[pack_emitter]

        # Resolve template directory
        stack_dir = _resolve_stack_dir(stack)

        # Import and instantiate emitter
        mod = importlib.import_module(module_path)
        emitter_cls = getattr(mod, class_name)

        # CP19 emitters accept (ui_framework=...) not (stack_dir=...)
        if pack_emitter.startswith("cp19.") or pack_emitter.startswith("cp22."):
            emitter = emitter_cls()
        else:
            emitter = emitter_cls(stack_dir=stack_dir)

        # Get raw data from FileSpec context
        context = file_spec.get("context", {})
        file_path = file_spec.get("path", "")
        file_type = file_spec.get("file_type", file_spec.get("type", ""))

        # Parse raw dict → dataclass if parser registered
        entity_data = context.get("entity")
        vo_data = context.get("vo")

        # ── CP19: UI Component emitter (must be FIRST — uses raw entity dict) ──
        if parser_key == "cp19_ui_components" or pack_emitter.startswith("cp19."):
            # --- UI Component emitter dispatch ---
            # CP19 emitters take (list[ComponentSpec], output_dir) and return
            # list[GeneratedFile] with path/content attributes.
            try:
                from midicoder.emitters.core.cp19_ui_components.models import ComponentSpec

                entity = context.get("entity")
                components = []

                # Case 1: components is a list of strings (component_type names) from per_ui_component expansion
                components_raw = context.get("components")
                if isinstance(components_raw, list) and components_raw and isinstance(components_raw[0], str):
                    if entity:
                        type_to_factory = {
                            "form_field": ComponentSpec.generate_form,
                            "data_table": ComponentSpec.generate_table,
                            "card_list": ComponentSpec.generate_card_list,
                            "dialog": ComponentSpec.generate_dialog,
                        }
                        for ct in components_raw:
                            factory = type_to_factory.get(ct)
                            if factory:
                                try:
                                    components.append(factory(entity))
                                except Exception:
                                    pass

                # Case 2: components is a list of dicts (explicit ComponentSpec from MIR)
                elif components_raw:
                    components = _parse_ui_component_dict(components_raw)

                # Case 3: fallback — ui_components key
                elif context.get("ui_components"):
                    components = _parse_ui_component_dict(context["ui_components"])

                # Case 4: single entity, no components — generate all 4 types
                elif entity and not components:
                    components = [
                        ComponentSpec.generate_form(entity),
                        ComponentSpec.generate_table(entity),
                        ComponentSpec.generate_card_list(entity),
                        ComponentSpec.generate_dialog(entity),
                    ]

                import tempfile
                with tempfile.TemporaryDirectory() as tmp:
                    output_dir = Path(tmp)
                    generated = emitter.generate(components, output_dir)
                    results = []
                    for gf in generated:
                        if hasattr(gf, "content"):
                            content = gf.content
                        elif hasattr(gf, "path") and gf.path.exists():
                            content = gf.path.read_text(encoding="utf-8")
                        else:
                            continue
                        rel = str(getattr(gf, "path", Path(file_path)))
                        if tmp in rel:
                            try:
                                rel = str(Path(rel).relative_to(tmp))
                            except ValueError:
                                pass
                        results.append({"path": rel, "content": content})
                    return results if results else _fallback_placeholder(
                        file_path, "UI Component emitter produced no files"
                    )
            except Exception as exc:
                return _fallback_placeholder(file_path, str(exc))

        elif entity_data and parser_key and parser_key in PARSER_REGISTRY:
            entity = PARSER_REGISTRY[parser_key](entity_data)
            if entity is None:
                return _fallback_placeholder(file_path, "Failed to parse entity dict")

            # Collect all entities for relationship resolution
            all_entities_raw = context.get("all_entities", [])
            all_entities = []
            for raw_e in all_entities_raw:
                parsed = PARSER_REGISTRY[parser_key](raw_e)
                if parsed:
                    all_entities.append(parsed)

            # --- Entity emitter dispatch ---
            # Entity emitters return a single string (the model code)
            try:
                if file_type in ("model", "schema"):
                    content = emitter.emit(entity, all_entities)
                else:
                    # repository, route — entity emitter only produces model code
                    # for model/schema types; fall through for others
                    return _fallback_placeholder(
                        file_path,
                        f"Entity emitter does not produce '{file_type}' files; "
                        f"use raw Jinja2 instead",
                    )
                return [{"path": file_path, "content": content}]
            except Exception as exc:
                return _fallback_placeholder(file_path, str(exc))

        elif vo_data:
            # --- Value Object emitter dispatch ---
            # VO emitters accept raw dicts directly
            try:
                content = emitter.render_value_object(vo_data)
                return [{"path": file_path, "content": content}]
            except Exception as exc:
                return _fallback_placeholder(file_path, str(exc))

        elif parser_key == "cp10_search" or pack_emitter.startswith("cp10."):
            # --- Search emitter dispatch ---
            # Search emitters take (SearchCollection, output_dir) and return
            # list[GeneratedFile] with path/content attributes.
            try:
                collection = PARSER_REGISTRY["cp10_search"](context)
                import tempfile
                with tempfile.TemporaryDirectory() as tmp:
                    output_dir = Path(tmp)
                    generated = emitter.emit(collection, output_dir)
                    results = []
                    for gf in generated:
                        # GeneratedFile can have .content str or need file read
                        if hasattr(gf, "content"):
                            content = gf.content
                        elif hasattr(gf, "path") and gf.path.exists():
                            content = gf.path.read_text(encoding="utf-8")
                        else:
                            continue
                        # Build relative path from output_dir
                        rel = str(getattr(gf, "path", Path(file_path)))
                        if tmp in rel:
                            try:
                                rel = str(Path(rel).relative_to(tmp))
                            except ValueError:
                                pass
                        results.append({"path": rel, "content": content})
                    return results if results else _fallback_placeholder(
                        file_path, "Search emitter produced no files"
                    )
            except Exception as exc:
                return _fallback_placeholder(file_path, str(exc))

        elif parser_key == "cp06_gateway" or pack_emitter.startswith("cp06."):
            # --- Gateway emitter dispatch ---
            # Gateway emitters take (RouteCollection) via generate() and return
            # dict[file_path, content].
            try:
                collection = PARSER_REGISTRY["cp06_gateway"](context)
                if hasattr(emitter, "generate"):
                    result = emitter.generate(collection)
                    if isinstance(result, dict):
                        return [{"path": k, "content": v} for k, v in result.items()]
                    elif isinstance(result, list):
                        return result
                return _fallback_placeholder(
                    file_path, "Gateway emitter returned unexpected type"
                )
            except Exception as exc:
                return _fallback_placeholder(file_path, str(exc))

        elif hasattr(emitter, "emit"):
            # Generic dispatch — emitter.emit(entity, all_entities) or
            # emitter.emit(command, output_dir) — try to call emit()
            try:
                if entity_data:
                    result = emitter.emit(entity_data, context.get("all_entities", []))
                else:
                    # Some emitters take (data, output_dir) — pass empty
                    result = emitter.emit(None, Path("."))
                if isinstance(result, str):
                    return [{"path": file_path, "content": result}]
                elif isinstance(result, dict):
                    return [{"path": k, "content": v} for k, v in result.items()]
                else:
                    return _fallback_placeholder(
                        file_path, f"Emitter returned unexpected type {type(result)}"
                    )
            except Exception as exc:
                return _fallback_placeholder(file_path, str(exc))

        else:
            return _fallback_placeholder(
                file_path,
                f"Cannot dispatch '{pack_emitter}' — no matching data in context",
            )


def _resolve_stack_dir(stack: str) -> Path:
    """
    Resolve the absolute template directory for a given stack.

    Mirrors the resolution logic in pipeline/emitter.py:
    ``package_dir / "stacks" / stack / "core"``
    """
    package_dir = Path(__file__).resolve().parent.parent  # midicoder/
    new_dir = package_dir / "stacks" / stack / "core"
    old_dir = package_dir / "stacks" / stack / "templates"

    if new_dir.exists():
        return new_dir
    elif old_dir.exists():
        return old_dir
    else:
        # Create empty dir so Jinja2 doesn't crash
        new_dir.mkdir(parents=True, exist_ok=True)
        return new_dir


def _fallback_placeholder(
    file_path: str, reason: str
) -> list[dict[str, str]]:
    """Return a single-file result with a placeholder / error comment."""
    content = (
        f"# Placeholder — pack emitter dispatch failed\n"
        f"# Reason: {reason}\n"
        f"# File: {file_path}\n"
        f"pass\n"
    )
    return [{"path": file_path, "content": content}]
