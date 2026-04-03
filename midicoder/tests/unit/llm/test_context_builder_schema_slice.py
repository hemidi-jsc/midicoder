from __future__ import annotations

from midicoder.llm.context_builder import slice_schema_for_targets


def test_slice_schema_for_targets_uses_expected_module_mapping() -> None:
    schema_tree = {
        "version": "v0",
        "modules": {
            "midicoder.dsl.schemas.info_model": {"name": "info"},
            "midicoder.dsl.schemas.command_model": {"name": "command"},
            "midicoder.dsl.schemas.guard_effect_model": {"name": "guard"},
            "midicoder.dsl.schemas.named_field_model": {"name": "named_field"},
            "midicoder.dsl.schemas.testing_model": {"name": "testing"},
            "midicoder.dsl.schemas.unused_model": {"name": "unused"},
        },
    }

    sliced = slice_schema_for_targets(
        schema_tree,
        ["meta/info.yaml", "app/commands.yaml", "testing/tests.yaml"],
    )

    assert set(sliced["modules"].keys()) == {
        "midicoder.dsl.schemas.info_model",
        "midicoder.dsl.schemas.command_model",
        "midicoder.dsl.schemas.guard_effect_model",
        "midicoder.dsl.schemas.named_field_model",
        "midicoder.dsl.schemas.testing_model",
    }


def test_slice_schema_for_targets_returns_full_schema_when_unknown_targets() -> None:
    schema_tree = {
        "version": "v0",
        "modules": {"midicoder.dsl.schemas.info_model": {"name": "info"}},
    }

    sliced = slice_schema_for_targets(schema_tree, ["unknown/file.yaml"])

    assert sliced == schema_tree

