"""Contract file registry as the single source of truth."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ContractFileMeta:
    """Metadata for one contract file type."""

    file_id: str
    layer: int
    dependencies: tuple[str, ...]
    output_provides: tuple[str, ...]
    schema_modules: tuple[str, ...]


_REGISTRY_DATA: tuple[ContractFileMeta, ...] = (
    ContractFileMeta(
        file_id="meta/info.yaml",
        layer=1,
        dependencies=(),
        output_provides=("project_metadata",),
        schema_modules=("midicoder.dsl.schemas.info_model",),
    ),
    ContractFileMeta(
        file_id="meta/profiles.yaml",
        layer=1,
        dependencies=("meta/info.yaml",),
        output_provides=("environment_profiles",),
        schema_modules=("midicoder.dsl.schemas.profiles_model",),
    ),
    ContractFileMeta(
        file_id="meta/secrets.yaml",
        layer=1,
        dependencies=("meta/info.yaml", "meta/profiles.yaml"),
        output_provides=("secret_references",),
        schema_modules=("midicoder.dsl.schemas.secrets_contract_model",),
    ),
    ContractFileMeta(
        file_id="glossary.yaml",
        layer=1,
        dependencies=("meta/info.yaml",),
        output_provides=("canonical_terms",),
        schema_modules=("midicoder.dsl.schemas.glossary_model",),
    ),
    ContractFileMeta(
        file_id="domain/entities.yaml",
        layer=2,
        dependencies=("glossary.yaml",),
        output_provides=("entity_catalog",),
        schema_modules=(
            "midicoder.dsl.schemas.entity_model",
            "midicoder.dsl.schemas.named_field_model",
        ),
    ),
    ContractFileMeta(
        file_id="domain/value_objects.yaml",
        layer=2,
        dependencies=("glossary.yaml",),
        output_provides=("value_object_catalog",),
        schema_modules=(
            "midicoder.dsl.schemas.value_object_model",
            "midicoder.dsl.schemas.named_field_model",
        ),
    ),
    ContractFileMeta(
        file_id="domain/enums.yaml",
        layer=2,
        dependencies=("glossary.yaml",),
        output_provides=("enum_catalog",),
        schema_modules=("midicoder.dsl.schemas.enum_model",),
    ),
    ContractFileMeta(
        file_id="domain/errors.yaml",
        layer=2,
        dependencies=("glossary.yaml",),
        output_provides=("error_catalog",),
        schema_modules=("midicoder.dsl.schemas.error_model",),
    ),
    ContractFileMeta(
        file_id="domain/events.yaml",
        layer=2,
        dependencies=(
            "glossary.yaml",
            "domain/entities.yaml",
            "domain/value_objects.yaml",
            "domain/enums.yaml",
        ),
        output_provides=("event_catalog",),
        schema_modules=(
            "midicoder.dsl.schemas.event_model",
            "midicoder.dsl.schemas.named_field_model",
        ),
    ),
    ContractFileMeta(
        file_id="app/commands.yaml",
        layer=3,
        dependencies=(
            "glossary.yaml",
            "domain/entities.yaml",
            "domain/value_objects.yaml",
            "domain/enums.yaml",
            "domain/errors.yaml",
        ),
        output_provides=("command_contracts",),
        schema_modules=(
            "midicoder.dsl.schemas.command_model",
            "midicoder.dsl.schemas.named_field_model",
            "midicoder.dsl.schemas.guard_effect_model",
        ),
    ),
    ContractFileMeta(
        file_id="app/queries.yaml",
        layer=3,
        dependencies=(
            "glossary.yaml",
            "domain/entities.yaml",
            "domain/value_objects.yaml",
            "domain/enums.yaml",
        ),
        output_provides=("query_contracts",),
        schema_modules=(
            "midicoder.dsl.schemas.query_model",
            "midicoder.dsl.schemas.named_field_model",
        ),
    ),
    ContractFileMeta(
        file_id="app/projections.yaml",
        layer=3,
        dependencies=("app/queries.yaml", "domain/events.yaml", "domain/entities.yaml"),
        output_provides=("projection_contracts",),
        schema_modules=(
            "midicoder.dsl.schemas.projection_model",
            "midicoder.dsl.schemas.named_field_model",
        ),
    ),
    ContractFileMeta(
        file_id="rules/rules.yaml",
        layer=3,
        dependencies=(
            "glossary.yaml",
            "domain/entities.yaml",
            "domain/value_objects.yaml",
            "domain/enums.yaml",
        ),
        output_provides=("business_rules",),
        schema_modules=("midicoder.dsl.schemas.rule_model",),
    ),
    ContractFileMeta(
        file_id="workflows/workflows.yaml",
        layer=3,
        dependencies=(
            "app/commands.yaml",
            "app/queries.yaml",
            "rules/rules.yaml",
            "domain/events.yaml",
        ),
        output_provides=("workflow_contracts",),
        schema_modules=(
            "midicoder.dsl.schemas.workflow_model",
            "midicoder.dsl.schemas.guard_effect_model",
        ),
    ),
    ContractFileMeta(
        file_id="persistence/model.yaml",
        layer=5,
        dependencies=(
            "domain/entities.yaml",
            "domain/value_objects.yaml",
            "domain/enums.yaml",
        ),
        output_provides=("persistence_model",),
        schema_modules=("midicoder.dsl.schemas.persistence_model",),
    ),
    ContractFileMeta(
        file_id="api/http.yaml",
        layer=6,
        dependencies=("app/commands.yaml", "app/queries.yaml", "domain/errors.yaml"),
        output_provides=("http_api_contracts",),
        schema_modules=(
            "midicoder.dsl.schemas.http_api_model",
            "midicoder.dsl.schemas.named_field_model",
        ),
    ),
    ContractFileMeta(
        file_id="api/graphql.yaml",
        layer=6,
        dependencies=("domain/entities.yaml", "app/queries.yaml", "app/commands.yaml"),
        output_provides=("graphql_api_contracts",),
        schema_modules=(
            "midicoder.dsl.schemas.graphql_api_model",
            "midicoder.dsl.schemas.named_field_model",
        ),
    ),
    ContractFileMeta(
        file_id="integrations/integrations.yaml",
        layer=6,
        dependencies=("app/commands.yaml", "domain/events.yaml"),
        output_provides=("integration_contracts",),
        schema_modules=(
            "midicoder.dsl.schemas.integration_model",
            "midicoder.dsl.schemas.named_field_model",
        ),
    ),
    ContractFileMeta(
        file_id="policy/policies.yaml",
        layer=7,
        dependencies=("rules/rules.yaml",),
        output_provides=("policy_rules",),
        schema_modules=("midicoder.dsl.schemas.policy_model",),
    ),
    ContractFileMeta(
        file_id="policy/rbac.yaml",
        layer=7,
        dependencies=("glossary.yaml", "domain/entities.yaml"),
        output_provides=("rbac_policies",),
        schema_modules=("midicoder.dsl.schemas.access_policy_model",),
    ),
    ContractFileMeta(
        file_id="policy/permissions_map.yaml",
        layer=7,
        dependencies=("policy/rbac.yaml", "policy/policies.yaml"),
        output_provides=("permission_mappings",),
        schema_modules=("midicoder.dsl.schemas.access_policy_model",),
    ),
    ContractFileMeta(
        file_id="policy/security.yaml",
        layer=7,
        dependencies=("policy/policies.yaml",),
        output_provides=("security_baseline",),
        schema_modules=("midicoder.dsl.schemas.security_baseline_model",),
    ),
    ContractFileMeta(
        file_id="policy/reliability.yaml",
        layer=7,
        dependencies=("workflows/workflows.yaml", "integrations/integrations.yaml"),
        output_provides=("reliability_policies",),
        schema_modules=("midicoder.dsl.schemas.reliability_model",),
    ),
    ContractFileMeta(
        file_id="ops/observability.yaml",
        layer=5,
        dependencies=(
            "api/http.yaml",
            "workflows/workflows.yaml",
            "integrations/integrations.yaml",
            "policy/reliability.yaml",
        ),
        output_provides=("observability_contracts",),
        schema_modules=("midicoder.dsl.schemas.observability_model",),
    ),
    ContractFileMeta(
        file_id="scenarios/scenarios.yaml",
        layer=9,
        dependencies=(
            "app/commands.yaml",
            "app/queries.yaml",
            "workflows/workflows.yaml",
            "api/http.yaml",
        ),
        output_provides=("scenario_definitions",),
        schema_modules=("midicoder.dsl.schemas.scenario_model",),
    ),
    ContractFileMeta(
        file_id="testing/tests.yaml",
        layer=9,
        dependencies=(
            "scenarios/scenarios.yaml",
            "rules/rules.yaml",
            "policy/policies.yaml",
            "policy/reliability.yaml",
        ),
        output_provides=("test_contracts",),
        schema_modules=("midicoder.dsl.schemas.testing_model",),
    ),
)

CONTRACT_FILE_REGISTRY: dict[str, ContractFileMeta] = {
    meta.file_id: meta for meta in _REGISTRY_DATA
}


def get_file_meta(file_id: str) -> ContractFileMeta | None:
    """Return metadata for one file, or None when unknown."""
    return CONTRACT_FILE_REGISTRY.get(file_id)


def list_files() -> list[str]:
    """Return all known contract file IDs."""
    return list(CONTRACT_FILE_REGISTRY.keys())


def list_by_layer(layer: int) -> list[ContractFileMeta]:
    """Return file metadata entries for a given layer."""
    return [meta for meta in _REGISTRY_DATA if meta.layer == layer]


def get_dependencies(file_id: str) -> tuple[str, ...]:
    """Return dependency file IDs for one file."""
    meta = get_file_meta(file_id)
    return meta.dependencies if meta else ()


def get_schema_modules(file_id: str) -> tuple[str, ...]:
    """Return schema module list for one file."""
    meta = get_file_meta(file_id)
    return meta.schema_modules if meta else ()


def validate_registry() -> list[str]:
    """Validate registry integrity and return a list of errors."""
    errors: list[str] = []
    known_file_ids = set(CONTRACT_FILE_REGISTRY.keys())

    if len(CONTRACT_FILE_REGISTRY) != len(_REGISTRY_DATA):
        errors.append("duplicate_file_id: registry keys collapsed from source data")

    for meta in _REGISTRY_DATA:
        if not meta.file_id:
            errors.append("invalid_file_id: empty")

        if meta.layer < 1 or meta.layer > 9:
            errors.append(f"invalid_layer:{meta.file_id}:{meta.layer}")

        dep_set: set[str] = set()
        for dep in meta.dependencies:
            if dep == meta.file_id:
                errors.append(f"self_dependency:{meta.file_id}")
            if dep in dep_set:
                errors.append(f"duplicate_dependency:{meta.file_id}:{dep}")
            dep_set.add(dep)
            if dep not in known_file_ids:
                errors.append(f"missing_dependency:{meta.file_id}:{dep}")

        output_set: set[str] = set()
        for output in meta.output_provides:
            if output in output_set:
                errors.append(f"duplicate_output:{meta.file_id}:{output}")
            output_set.add(output)

        module_set: set[str] = set()
        for module_name in meta.schema_modules:
            if module_name in module_set:
                errors.append(f"duplicate_schema_module:{meta.file_id}:{module_name}")
            module_set.add(module_name)

    return errors


def assert_valid_registry() -> None:
    """Raise ValueError when registry integrity checks fail."""
    errors = validate_registry()
    if errors:
        raise ValueError("; ".join(errors))


assert_valid_registry()
