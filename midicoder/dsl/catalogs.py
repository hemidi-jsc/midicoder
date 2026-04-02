"""Central catalogs for DSL schema.

This module re-exports catalog constants defined in the individual
`midicoder.dsl.schemas.*_model` modules so that other parts of the
system can rely on a single import location.
"""

from __future__ import annotations

from .schemas.access_policy_model import PERMISSION_ACTION_CATALOG
from .schemas.command_model import (
    COMMAND_CATEGORY_CATALOG,
    TENANT_SCOPE_CATALOG as COMMAND_TENANT_SCOPE_CATALOG,
)
from .schemas.entity_model import (
    CONSTRAINT_TYPE_CATALOG,
    TENANT_SCOPE_CATALOG as ENTITY_TENANT_SCOPE_CATALOG,
)
from .schemas.error_model import ERROR_CATEGORY_CATALOG
from .schemas.event_model import EVENT_KIND_CATALOG
from .schemas.glossary_model import GLOSSARY_CATEGORY_CATALOG
from .schemas.graphql_api_model import GRAPHQL_TYPE_KIND_CATALOG
from .schemas.guard_effect_model import EFFECT_CATALOG, GUARD_CATALOG
from .schemas.http_api_model import HTTP_METHOD_CATALOG
from .schemas.integration_model import (
    AUTH_TYPE_CATALOG,
    AWS_SERVICE_CATALOG,
    AZURE_SERVICE_CATALOG,
    CLOUD_PROVIDER_CATALOG,
    EMAIL_TRANSPORT_CATALOG,
    GCP_SERVICE_CATALOG,
    INTEGRATION_TYPE_CATALOG,
    WEBHOOK_SIGNATURE_ALG_CATALOG,
)
from .schemas.named_field_model import (
    COMPOSITE_TYPE_CATALOG,
    REF_TYPE_PREFIXES,
    SCALAR_TYPE_CATALOG,
)
from .schemas.observability_model import OBSERVABILITY_KIND_CATALOG
from .schemas.persistence_model import (
    PERSISTENCE_CONNECTOR_CATALOG,
    PERSISTENCE_CONSTRAINT_KEY_CATALOG,
    PERSISTENCE_ENGINE_CATALOG,
)
from .schemas.policy_model import POLICY_EFFECT_TYPE_CATALOG, POLICY_OPERATOR_CATALOG
from .schemas.profiles_model import ENVIRONMENT_CATALOG
from .schemas.query_model import QUERY_CATEGORY_CATALOG
from .schemas.reliability_model import RELIABILITY_TARGET_KIND_CATALOG
from .schemas.rule_model import RULE_SEVERITY_CATALOG
from .schemas.secrets_contract_model import SECRET_PROVIDER_CATALOG
from .schemas.scenario_model import SCENARIO_STEP_TYPE_CATALOG
from .schemas.testing_model import (
    CONTRACT_TEST_STEP_TYPE_CATALOG,
    TEST_FRAMEWORK_CATALOG,
    TEST_KIND_CATALOG,
)
from .schemas.value_object_model import VALUE_OBJECT_CATEGORY_CATALOG
from .schemas.workflow_model import WORKFLOW_STATE_KIND_CATALOG

TENANT_SCOPE_CATALOG = ENTITY_TENANT_SCOPE_CATALOG | COMMAND_TENANT_SCOPE_CATALOG

__all__ = [
    # shared field/type catalogs
    "SCALAR_TYPE_CATALOG",
    "COMPOSITE_TYPE_CATALOG",
    "REF_TYPE_PREFIXES",
    # meta catalogs
    "GLOSSARY_CATEGORY_CATALOG",
    # domain catalogs
    "CONSTRAINT_TYPE_CATALOG",
    "TENANT_SCOPE_CATALOG",
    "VALUE_OBJECT_CATEGORY_CATALOG",
    "ERROR_CATEGORY_CATALOG",
    "EVENT_KIND_CATALOG",
    # application catalogs
    "COMMAND_CATEGORY_CATALOG",
    "QUERY_CATEGORY_CATALOG",
    # rules and policy catalogs
    "RULE_SEVERITY_CATALOG",
    "POLICY_OPERATOR_CATALOG",
    "POLICY_EFFECT_TYPE_CATALOG",
    # access control catalogs
    "PERMISSION_ACTION_CATALOG",
    # workflow catalogs
    "WORKFLOW_STATE_KIND_CATALOG",
    # api catalogs
    "HTTP_METHOD_CATALOG",
    "GRAPHQL_TYPE_KIND_CATALOG",
    # scenario catalogs
    "SCENARIO_STEP_TYPE_CATALOG",
    # guard/effect catalogs
    "GUARD_CATALOG",
    "EFFECT_CATALOG",
    # environment/secrets/reliability/testing catalogs
    "ENVIRONMENT_CATALOG",
    "SECRET_PROVIDER_CATALOG",
    "RELIABILITY_TARGET_KIND_CATALOG",
    "TEST_KIND_CATALOG",
    "TEST_FRAMEWORK_CATALOG",
    "CONTRACT_TEST_STEP_TYPE_CATALOG",
    "OBSERVABILITY_KIND_CATALOG",
    # persistence catalogs
    "PERSISTENCE_ENGINE_CATALOG",
    "PERSISTENCE_CONNECTOR_CATALOG",
    "PERSISTENCE_CONSTRAINT_KEY_CATALOG",
    # integration catalogs
    "INTEGRATION_TYPE_CATALOG",
    "CLOUD_PROVIDER_CATALOG",
    "AWS_SERVICE_CATALOG",
    "GCP_SERVICE_CATALOG",
    "AZURE_SERVICE_CATALOG",
    "AUTH_TYPE_CATALOG",
    "WEBHOOK_SIGNATURE_ALG_CATALOG",
    "EMAIL_TRANSPORT_CATALOG",
]
