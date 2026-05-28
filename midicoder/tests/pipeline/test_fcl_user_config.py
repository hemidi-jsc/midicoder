"""
Integration tests cho EU-0.2: FileContributionsLoader merge user config.

Verify rằng expand_* methods đúng cách merge user_config vào render_context.
"""

import pytest
from midicoder.pipeline.file_contributions_loader import (
    FileContributions,
    FileContributionsLoader,
    PerEntityFile,
    PerCommandFile,
    PerQueryFile,
    InfrastructureFile,
)


class TestExpandPerEntityUserConfig:
    """Test expand_per_entity với user config."""

    def test_without_user_config_returns_entity_rc(self):
        """Không có user_config -> render_context = entity RC (EU-0.1 behavior)."""
        fc = FileContributions(
            pack_id="CP01",
            pack_internal_id="cp_base_domain_model",
            per_entity=[PerEntityFile(
                path_pattern="app/models/{entity_snake}.py",
                file_type="model",
                template="entity.py.jinja2",
            )],
        )
        entities = [
            {"id": "Product", "render_context": {"sidebar_width": 300}}
        ]
        result = FileContributionsLoader.expand_per_entity(fc, entities)
        assert result[0]["context"]["render_context"] == {"sidebar_width": 300}

    def test_with_user_config_merges_defaults(self):
        """Có user_config -> merge defaults -> entity RC ghi đè."""
        fc = FileContributions(
            pack_id="CP01",
            pack_internal_id="cp_base_domain_model",
            per_entity=[PerEntityFile(
                path_pattern="app/models/{entity_snake}.py",
                file_type="model",
                template="entity.py.jinja2",
            )],
        )
        entities = [
            {"id": "Product", "render_context": {"sidebar_width": 999}}
        ]
        user_config = {
            "render": {
                "defaults": {"sidebar_width": 280, "grid": 4},
                "per_entity": {"Product": {"sidebar_width": 320}},
            }
        }
        result = FileContributionsLoader.expand_per_entity(fc, entities, user_config=user_config)
        rc = result[0]["context"]["render_context"]
        # sidebar_width: DSL RC (999) > per_entity (320) > defaults (280)
        assert rc["sidebar_width"] == 999
        # grid: chỉ có trong defaults, preserved
        assert rc["grid"] == 4

    def test_with_user_config_deep_merge(self):
        """Deep merge -- nested keys được preserve."""
        fc = FileContributions(
            pack_id="CP01",
            pack_internal_id="cp_base_domain_model",
            per_entity=[PerEntityFile(
                path_pattern="app/models/{entity_snake}.py",
                file_type="model",
                template="entity.py.jinja2",
            )],
        )
        entities = [
            {"id": "Product", "render_context": {}}
        ]
        user_config = {
            "render": {
                "defaults": {
                    "list_view": {"size": 20, "sortable": True, "filterable": True},
                },
                "per_entity": {
                    "Product": {"list_view": {"size": 25}},
                },
            }
        }
        result = FileContributionsLoader.expand_per_entity(fc, entities, user_config=user_config)
        rc = result[0]["context"]["render_context"]
        # deep merge: size=25 (per_entity), sortable=True (defaults), filterable=True (defaults)
        assert rc["list_view"]["size"] == 25
        assert rc["list_view"]["sortable"] is True
        assert rc["list_view"]["filterable"] is True


class TestExpandPerCommandUserConfig:
    """Test expand_per_command với user config."""

    def test_command_rc_merged_with_user_config(self):
        """Command render_context merge đúng với user config."""
        fc = FileContributions(
            pack_id="CP01",
            pack_internal_id="cp_base_domain_model",
            per_command=[PerCommandFile(
                path_pattern="app/commands/{command_snake}_handler.py",
                file_type="command",
                template="command_handler.py.jinja2",
            )],
        )
        commands = [
            {"id": "CreateOrder", "render_context": {"custom": True}}
        ]
        user_config = {
            "render": {
                "defaults": {"sidebar_width": 280},
                "per_entity": {"CreateOrder": {"sidebar_width": 400}},
            }
        }
        result = FileContributionsLoader.expand_per_command(fc, commands, user_config=user_config)
        rc = result[0]["context"]["render_context"]
        assert rc["custom"] is True  # DSL RC preserved
        assert rc["sidebar_width"] == 400  # per_entity applied


class TestExpandPerQueryUserConfig:
    """Test expand_per_query với user config."""

    def test_query_rc_merged_with_user_config(self):
        """Query render_context merge đúng với user config."""
        fc = FileContributions(
            pack_id="CP01",
            pack_internal_id="cp_base_domain_model",
            per_query=[PerQueryFile(
                path_pattern="app/queries/{query_snake}_handler.py",
                file_type="query",
                template="query_handler.py.jinja2",
            )],
        )
        queries = [
            {"id": "ListProducts", "render_context": {"page_size": 50}}
        ]
        user_config = {
            "render": {
                "defaults": {"grid": 4},
            }
        }
        result = FileContributionsLoader.expand_per_query(fc, queries, user_config=user_config)
        rc = result[0]["context"]["render_context"]
        assert rc["page_size"] == 50  # DSL RC preserved
        assert rc["grid"] == 4  # defaults applied


class TestExpandInfrastructureUserConfig:
    """Test expand_infrastructure với user config."""

    def test_infrastructure_uses_infrastructure_overrides(self):
        """Infrastructure inject render.infrastructure vào context."""
        fc = FileContributions(
            pack_id="CP07",
            pack_internal_id="cp_infra_iac",
            infrastructure=[InfrastructureFile(
                path="docker-compose.yml",
                file_type="docker_compose",
                template="docker-compose.yml.jinja2",
            )],
        )
        user_config = {
            "render": {
                "infrastructure": {
                    "docker_compose": {"api_replicas": 3, "postgres_image": "postgres:16"},
                }
            }
        }
        result = FileContributionsLoader.expand_infrastructure(fc, user_config=user_config)
        rc = result[0]["context"]["render_context"]
        assert rc == {"docker_compose": {"api_replicas": 3, "postgres_image": "postgres:16"}}

    def test_infrastructure_empty_without_user_config(self):
        """Không có user_config -> render_context = {}."""
        fc = FileContributions(
            pack_id="CP07",
            pack_internal_id="cp_infra_iac",
            infrastructure=[InfrastructureFile(
                path="docker-compose.yml",
                file_type="docker_compose",
                template="docker-compose.yml.jinja2",
            )],
        )
        result = FileContributionsLoader.expand_infrastructure(fc)
        assert result[0]["context"]["render_context"] == {}


class TestFullPriorityChain:
    """Test full priority chain: defaults -> per_entity -> DSL RC."""

    def test_multiple_entities_different_configs(self):
        """Nhiều entity, mỗi entity có config khác nhau."""
        fc = FileContributions(
            pack_id="CP01",
            pack_internal_id="cp_base_domain_model",
            per_entity=[PerEntityFile(
                path_pattern="app/models/{entity_snake}.py",
                file_type="model",
                template="entity.py.jinja2",
            )],
        )
        entities = [
            {"id": "Product", "render_context": {"custom": "product_dsl"}},
            {"id": "Order", "render_context": {"custom": "order_dsl"}},
            {"id": "User", "render_context": {}},
        ]
        user_config = {
            "render": {
                "defaults": {"sidebar_width": 280, "grid": 4},
                "per_entity": {
                    "Product": {"sidebar_width": 320},
                    "Order": {"sidebar_width": 400, "extra": "order_config"},
                },
            }
        }
        result = FileContributionsLoader.expand_per_entity(fc, entities, user_config=user_config)

        # Product: DSL RC + per_entity + defaults
        assert result[0]["context"]["render_context"]["custom"] == "product_dsl"
        assert result[0]["context"]["render_context"]["sidebar_width"] == 320
        assert result[0]["context"]["render_context"]["grid"] == 4

        # Order: DSL RC + per_entity + defaults
        assert result[1]["context"]["render_context"]["custom"] == "order_dsl"
        assert result[1]["context"]["render_context"]["sidebar_width"] == 400
        assert result[1]["context"]["render_context"]["extra"] == "order_config"
        assert result[1]["context"]["render_context"]["grid"] == 4

        # User: chỉ có defaults (không trong per_entity)
        assert result[2]["context"]["render_context"]["sidebar_width"] == 280
        assert result[2]["context"]["render_context"]["grid"] == 4
