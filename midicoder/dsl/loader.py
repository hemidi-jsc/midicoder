from __future__ import annotations

from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

from midicoder.dsl.models import (
    AccessPolicyFile,
    CommandsFile,
    EntitiesFile,
    EnumsFile,
    ErrorsFile,
    EventsFile,
    GlossaryFile,
    GraphQLApiFile,
    HttpApiFile,
    InfoFile,
    IntegrationsFile,
    ObservabilityFile,
    PersistenceModelFile,
    PoliciesFile,
    ProfilesFile,
    ProjectionsFile,
    QueriesFile,
    ReliabilityPoliciesFile,
    RulesFile,
    ScenariosFile,
    SecretsContractFile,
    SecurityBaselineFile,
    TestingFile,
    ValueObjectsFile,
    WorkflowsFile,
)

yaml = YAML(typ="rt")


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.load(handle)


def load_entities(path: Path) -> EntitiesFile:
    data = load_yaml(path)
    return EntitiesFile.model_validate(data)


def load_value_objects(path: Path) -> ValueObjectsFile:
    data = load_yaml(path)
    return ValueObjectsFile.model_validate(data)


def load_enums(path: Path) -> EnumsFile:
    data = load_yaml(path)
    return EnumsFile.model_validate(data)


def load_errors(path: Path) -> ErrorsFile:
    data = load_yaml(path)
    return ErrorsFile.model_validate(data)


def load_events(path: Path) -> EventsFile:
    data = load_yaml(path)
    return EventsFile.model_validate(data)


def load_commands(path: Path) -> CommandsFile:
    data = load_yaml(path)
    return CommandsFile.model_validate(data)


def load_http(path: Path) -> HttpApiFile:
    data = load_yaml(path)
    return HttpApiFile.model_validate(data)


def load_rules(path: Path) -> RulesFile:
    data = load_yaml(path)
    return RulesFile.model_validate(data)


def load_info(path: Path) -> InfoFile:
    data = load_yaml(path)
    return InfoFile.model_validate(data)


def load_glossary(path: Path) -> GlossaryFile:
    data = load_yaml(path)
    return GlossaryFile.model_validate(data)


def load_queries(path: Path) -> QueriesFile:
    data = load_yaml(path)
    return QueriesFile.model_validate(data)


def load_workflows(path: Path) -> WorkflowsFile:
    data = load_yaml(path)
    return WorkflowsFile.model_validate(data)


def load_scenarios(path: Path) -> ScenariosFile:
    data = load_yaml(path)
    return ScenariosFile.model_validate(data)


def load_projections(path: Path) -> ProjectionsFile:
    data = load_yaml(path)
    return ProjectionsFile.model_validate(data)


def load_policies(path: Path) -> PoliciesFile:
    data = load_yaml(path)
    return PoliciesFile.model_validate(data)


def load_access_policy(path: Path) -> AccessPolicyFile:
    data = load_yaml(path)
    return AccessPolicyFile.model_validate(data)


def load_graphql(path: Path) -> GraphQLApiFile:
    data = load_yaml(path)
    return GraphQLApiFile.model_validate(data)


def load_persistence(path: Path) -> PersistenceModelFile:
    data = load_yaml(path)
    return PersistenceModelFile.model_validate(data)


def load_integrations(path: Path) -> IntegrationsFile:
    data = load_yaml(path)
    return IntegrationsFile.model_validate(data)


def load_profiles(path: Path) -> ProfilesFile:
    data = load_yaml(path)
    return ProfilesFile.model_validate(data)


def load_secrets_contract(path: Path) -> SecretsContractFile:
    data = load_yaml(path)
    return SecretsContractFile.model_validate(data)


def load_security_baseline(path: Path) -> SecurityBaselineFile:
    data = load_yaml(path)
    return SecurityBaselineFile.model_validate(data)


def load_reliability(path: Path) -> ReliabilityPoliciesFile:
    data = load_yaml(path)
    return ReliabilityPoliciesFile.model_validate(data)


def load_observability(path: Path) -> ObservabilityFile:
    data = load_yaml(path)
    return ObservabilityFile.model_validate(data)


def load_testing(path: Path) -> TestingFile:
    data = load_yaml(path)
    return TestingFile.model_validate(data)
