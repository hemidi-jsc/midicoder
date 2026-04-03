from __future__ import annotations

from midicoder.contract.registry import (
    CONTRACT_FILE_REGISTRY,
    get_dependencies,
    get_file_meta,
    get_schema_modules,
    list_by_layer,
    validate_registry,
)


def test_registry_loads_all_current_files() -> None:
    # Current scope: 26 file types from existing DSL surface.
    assert len(CONTRACT_FILE_REGISTRY) == 26


def test_registry_validation_has_no_errors() -> None:
    assert validate_registry() == []


def test_registry_query_by_layer() -> None:
    layer_one_files = {meta.file_id for meta in list_by_layer(1)}
    assert layer_one_files == {
        "meta/info.yaml",
        "meta/profiles.yaml",
        "meta/secrets.yaml",
        "glossary.yaml",
    }


def test_registry_dependencies_and_schema_modules() -> None:
    assert get_dependencies("testing/tests.yaml") == (
        "scenarios/scenarios.yaml",
        "rules/rules.yaml",
        "policy/policies.yaml",
        "policy/reliability.yaml",
    )
    assert get_schema_modules("api/http.yaml") == (
        "midicoder.dsl.schemas.http_api_model",
        "midicoder.dsl.schemas.named_field_model",
    )
    assert get_file_meta("unknown/file.yaml") is None
