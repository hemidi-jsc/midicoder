# coding: utf-8
"""
Tests cho CP38 recipes: csv_import_recipe, json_import_recipe, data_migrate_recipe,
etl_pipeline_recipe, bulk_export_recipe.
"""

from __future__ import annotations

from midicoder.packs.cp38_data_etl.parser import ETLIR
from midicoder.packs.cp38_data_etl.recipes import (
    RecipeOutput,
    bulk_export_recipe,
    csv_import_recipe,
    data_migrate_recipe,
    etl_pipeline_recipe,
    json_import_recipe,
)


class TestCSVImportRecipe:
    """Tests cho csv_import_recipe."""

    def test_returns_recipe_output(self):
        result = csv_import_recipe("users", "/data/users.csv")
        assert isinstance(result, RecipeOutput)

    def test_has_one_import_job(self):
        result = csv_import_recipe("users", "/data/users.csv")
        assert isinstance(result.ir, ETLIR)
        assert len(result.ir.import_jobs) == 1

    def test_job_format_is_csv(self):
        from midicoder.packs.cp38_data_etl.models import ImportFormat

        result = csv_import_recipe("users", "/data/users.csv")
        assert result.ir.import_jobs[0].format == ImportFormat.CSV

    def test_correct_name_and_description(self):
        result = csv_import_recipe("products", "/data/products.csv")
        assert result.name == "csv_import"
        assert "/data/products.csv" in result.description
        assert "products" in result.description

    def test_job_target_entity(self):
        result = csv_import_recipe("orders", "/data/orders.csv")
        assert result.ir.import_jobs[0].target_entity == "orders"


class TestJSONImportRecipe:
    """Tests cho json_import_recipe."""

    def test_returns_recipe_output(self):
        result = json_import_recipe("users", "/data/users.json")
        assert isinstance(result, RecipeOutput)

    def test_has_one_import_job(self):
        result = json_import_recipe("users", "/data/users.json")
        assert isinstance(result.ir, ETLIR)
        assert len(result.ir.import_jobs) == 1

    def test_job_format_is_json(self):
        from midicoder.packs.cp38_data_etl.models import ImportFormat

        result = json_import_recipe("users", "/data/users.json")
        assert result.ir.import_jobs[0].format == ImportFormat.JSON

    def test_correct_name_and_description(self):
        result = json_import_recipe("products", "/data/products.json")
        assert result.name == "json_import"
        assert "/data/products.json" in result.description


class TestDataMigrateRecipe:
    """Tests cho data_migrate_recipe."""

    def test_has_etl_job_with_extract_transform_load_steps(self):
        from midicoder.packs.cp38_data_etl.models import (
            ETLMapping,
            ExtractSource,
        )

        result = data_migrate_recipe(
            source=ExtractSource.FILE,
            target="users",
            mappings=[
                ETLMapping(mapping_key="m1", source_column="email", target_field="email"),
            ],
        )
        assert isinstance(result, RecipeOutput)
        assert len(result.ir.etl_jobs) == 1
        steps = result.ir.etl_jobs[0].steps
        step_types = [s.step_type for s in steps]
        assert "extract" in step_types
        assert "load" in step_types

    def test_has_transform_step_when_mappings_provided(self):
        from midicoder.packs.cp38_data_etl.models import (
            ETLMapping,
            ExtractSource,
        )

        result = data_migrate_recipe(
            source=ExtractSource.DATABASE,
            target="orders",
            mappings=[
                ETLMapping(mapping_key="m1", source_column="status", target_field="state"),
                ETLMapping(mapping_key="m2", source_column="total", target_field="amount"),
            ],
        )
        steps = result.ir.etl_jobs[0].steps
        step_types = [s.step_type for s in steps]
        assert "transform" in step_types

    def test_correct_name_and_description(self):
        from midicoder.packs.cp38_data_etl.models import ExtractSource

        result = data_migrate_recipe(
            source=ExtractSource.API,
            target="products",
            mappings=[],
        )
        assert result.name == "data_migrate"
        assert "products" in result.description

    def test_no_transform_step_when_no_mappings(self):
        from midicoder.packs.cp38_data_etl.models import ExtractSource

        result = data_migrate_recipe(
            source=ExtractSource.FILE,
            target="users",
            mappings=[],
        )
        steps = result.ir.etl_jobs[0].steps
        step_types = [s.step_type for s in steps]
        assert "transform" not in step_types


class TestETLPipelineRecipe:
    """Tests cho etl_pipeline_recipe."""

    def test_creates_pipeline_from_pre_built_steps(self):
        from midicoder.packs.cp38_data_etl.models import ETLStep

        steps = [
            ETLStep(step_key="ext", step_type="extract", order=0),
            ETLStep(step_key="trf", step_type="transform", order=1),
            ETLStep(step_key="ldr", step_type="load", order=2),
        ]
        result = etl_pipeline_recipe(steps=steps, job_key="custom_pipeline")
        assert isinstance(result, RecipeOutput)
        assert len(result.ir.etl_jobs) == 1
        assert result.ir.etl_jobs[0].job_key == "custom_pipeline"
        assert len(result.ir.etl_jobs[0].steps) == 3

    def test_correct_name(self):
        from midicoder.packs.cp38_data_etl.models import ETLStep

        steps = [
            ETLStep(step_key="e", step_type="extract", order=0),
            ETLStep(step_key="l", step_type="load", order=1),
        ]
        result = etl_pipeline_recipe(steps=steps)
        assert result.name == "etl_pipeline"


class TestBulkExportRecipe:
    """Tests cho bulk_export_recipe."""

    def test_has_export_job(self):
        result = bulk_export_recipe("orders")
        assert isinstance(result, RecipeOutput)
        assert len(result.ir.export_jobs) == 1

    def test_correct_format_csv(self):
        from midicoder.packs.cp38_data_etl.models import ImportFormat

        result = bulk_export_recipe("users", fmt=ImportFormat.CSV)
        assert result.ir.export_jobs[0].format == ImportFormat.CSV

    def test_correct_format_json(self):
        from midicoder.packs.cp38_data_etl.models import ImportFormat

        result = bulk_export_recipe("products", fmt=ImportFormat.JSON)
        assert result.ir.export_jobs[0].format == ImportFormat.JSON

    def test_has_bulk_config(self):
        result = bulk_export_recipe("orders")
        assert result.ir.bulk_config is not None

    def test_correct_name_and_description(self):
        result = bulk_export_recipe("users")
        assert result.name == "bulk_export"
        assert "users" in result.description
