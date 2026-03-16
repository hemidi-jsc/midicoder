"""Aggregated DSL models.

This module re-exports the individual schema models defined in
`midicoder.dsl.schemas.*_model` for backwards compatibility.
"""

from __future__ import annotations

from .schemas.access_policy_model import AccessPolicy, AccessPolicyFile, Binding, Permission, Role
from .schemas.command_model import Command, CommandsFile
from .schemas.entity_model import EntitiesFile, Entity
from .schemas.enum_model import EnumDef, EnumsFile
from .schemas.error_model import ErrorDef, ErrorsFile
from .schemas.event_model import EventDef, EventsFile
from .schemas.glossary_model import Glossary, GlossaryFile, GlossaryTerm
from .schemas.graphql_api_model import GraphQLApi, GraphQLApiFile, GraphQLField, GraphQLType
from .schemas.guard_effect_model import EffectRef, GuardRef, IntegrationCallParams
from .schemas.http_api_model import HttpApiFile, HttpRoute
from .schemas.info_model import InfoFile, ProjectInfo
from .schemas.integration_model import (
    CircuitBreakerPolicy,
    EmailProvider,
    ErrorMap,
    IntegrationAuth,
    IntegrationTarget,
    IntegrationsFile,
    OAuth2Provider,
    RateLimitPolicy,
    RestApiOperation,
    RetryPolicy,
    S3Resource,
    SignaturePolicy,
    TimeoutPolicy,
    WebhookEndpoint,
)
from .schemas.named_field_model import NamedField
from .schemas.observability_model import ObservabilityFile, ObservabilityTarget
from .schemas.persistence_model import (
    PersistenceColumn,
    PersistenceDatasource,
    PersistenceIndex,
    PersistenceModelFile,
    PersistenceTable,
)
from .schemas.policy_model import PoliciesFile, Policy, PolicyCondition, PolicyEffect
from .schemas.projection_model import Projection, ProjectionsFile
from .schemas.query_model import QueriesFile, Query
from .schemas.profiles_model import EnvironmentProfile, ProfilesFile
from .schemas.reliability_model import (
    CircuitBreakerConfig,
    ReliabilityPoliciesFile,
    ReliabilityPolicy,
    RetryConfig,
    TimeoutConfig,
)
from .schemas.rule_model import Rule, RuleRow, RulesFile
from .schemas.scenario_model import Scenario, ScenarioStep, ScenariosFile
from .schemas.secrets_contract_model import SecretRef, SecretsContractFile
from .schemas.security_baseline_model import (
    CorsPolicy,
    PiiMaskingRule,
    RateLimitRule,
    SecurityBaseline,
    SecurityBaselineFile,
)
from .schemas.testing_model import ContractTestCase, ContractTestStep, TestingFile
from .schemas.value_object_model import ValueObject, ValueObjectsFile
from .schemas.workflow_model import Workflow, WorkflowErrorHandler, WorkflowState, WorkflowTransition, WorkflowsFile

__all__ = [
    "NamedField",
    "Entity",
    "EntitiesFile",
    "ValueObject",
    "ValueObjectsFile",
    "EnumDef",
    "EnumsFile",
    "ErrorDef",
    "ErrorsFile",
    "EventDef",
    "EventsFile",
    "GuardRef",
    "EffectRef",
    "IntegrationCallParams",
    "Command",
    "CommandsFile",
    "Query",
    "QueriesFile",
    "Projection",
    "ProjectionsFile",
    "HttpRoute",
    "HttpApiFile",
    "GraphQLType",
    "GraphQLField",
    "GraphQLApi",
    "GraphQLApiFile",
    "RuleRow",
    "Rule",
    "RulesFile",
    "WorkflowState",
    "WorkflowTransition",
    "WorkflowErrorHandler",
    "Workflow",
    "WorkflowsFile",
    "PolicyCondition",
    "PolicyEffect",
    "Policy",
    "PoliciesFile",
    "Role",
    "Permission",
    "Binding",
    "AccessPolicy",
    "AccessPolicyFile",
    "ScenarioStep",
    "Scenario",
    "ScenariosFile",
    "Glossary",
    "GlossaryFile",
    "GlossaryTerm",
    "InfoFile", 
    "ProjectInfo",
    "PersistenceDatasource",
    "PersistenceColumn",
    "PersistenceIndex",
    "PersistenceTable",
    "PersistenceModelFile",
    "IntegrationAuth",
    "TimeoutPolicy",
    "RetryPolicy",
    "RateLimitPolicy",
    "CircuitBreakerPolicy",
    "IntegrationTarget",
    "ErrorMap",
    "RestApiOperation",
    "S3Resource",
    "EmailProvider",
    "OAuth2Provider",
    "SignaturePolicy",
    "WebhookEndpoint",
    "IntegrationsFile",
    "EnvironmentProfile",
    "ProfilesFile",
    "SecretRef",
    "SecretsContractFile",
    "CorsPolicy",
    "RateLimitRule",
    "PiiMaskingRule",
    "SecurityBaseline",
    "SecurityBaselineFile",
    "TimeoutConfig",
    "RetryConfig",
    "CircuitBreakerConfig",
    "ReliabilityPolicy",
    "ReliabilityPoliciesFile",
    "ObservabilityTarget",
    "ObservabilityFile",
    "ContractTestStep",
    "ContractTestCase",
    "TestingFile",
]
