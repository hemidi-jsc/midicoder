"""
Integration tests cho render_context — EU-0.1.

Kiem tra full flow:
DSL YAML → ProjectionNode → MIR metadata → FileContributionsLoader context dict
"""

import pytest
import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parents[2]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))


class TestDSLToMIRRenderContext:
    """Kiem tra render_context propagate tu DSL → MIR metadata."""

    def test_entity_render_context_in_mir_metadata(self, tmp_path):
        """Full flow: YAML entity co render_context → MIR.metadata.entities chua render_context."""
        dsl_dir = tmp_path / "dsl"
        dsl_dir.mkdir()
        (dsl_dir / "entities.yaml").write_text(
            """entities:
  - id: Product
    description: San pham
    fields:
      - name: name
        type: string
    render_context:
      sidebar_width: 280
      show_sku_in_list: true
      grid_columns: 4
""",
            encoding="utf-8",
        )
        (dsl_dir / "commands.yaml").write_text("commands: []\n", encoding="utf-8")
        (dsl_dir / "queries.yaml").write_text("queries: []\n", encoding="utf-8")

        from midicoder.dsl.loader import load_projection_tree

        tree = load_projection_tree(dsl_dir)
        assert len(tree.get_entities()) == 1

        # Kiem tra ProjectionNode co render_context
        entity_node = tree.get_entities()[0]
        assert entity_node.params.get("render_context") == {
            "sidebar_width": 280,
            "show_sku_in_list": True,
            "grid_columns": 4,
        }

    def test_command_render_context_in_projection_tree(self, tmp_path):
        """Full flow: YAML command co render_context → ProjectionNode.params chua render_context."""
        dsl_dir = tmp_path / "dsl"
        dsl_dir.mkdir()
        (dsl_dir / "entities.yaml").write_text("entities: []\n", encoding="utf-8")
        (dsl_dir / "commands.yaml").write_text(
            """commands:
  - id: CreateProduct
    description: Tao san pham
    input:
      - name: name
        type: string
    render_context:
      form_layout: vertical
      validation_mode: async
""",
            encoding="utf-8",
        )
        (dsl_dir / "queries.yaml").write_text("queries: []\n", encoding="utf-8")

        from midicoder.dsl.loader import load_projection_tree

        tree = load_projection_tree(dsl_dir)
        assert len(tree.get_commands()) == 1

        cmd_node = tree.get_commands()[0]
        assert cmd_node.params.get("render_context") == {
            "form_layout": "vertical",
            "validation_mode": "async",
        }

    def test_query_render_context_in_projection_tree(self, tmp_path):
        """Full flow: YAML query co render_context → ProjectionNode.params chua render_context."""
        dsl_dir = tmp_path / "dsl"
        dsl_dir.mkdir()
        (dsl_dir / "entities.yaml").write_text("entities: []\n", encoding="utf-8")
        (dsl_dir / "commands.yaml").write_text("commands: []\n", encoding="utf-8")
        (dsl_dir / "queries.yaml").write_text(
            """queries:
  - id: ListProducts
    description: Lay danh sach san pham
    render_context:
      pagination_size: 25
      sortable_columns:
        - name
        - price
""",
            encoding="utf-8",
        )

        from midicoder.dsl.loader import load_projection_tree

        tree = load_projection_tree(dsl_dir)
        assert len(tree.get_queries()) == 1

        query_node = tree.get_queries()[0]
        assert query_node.params.get("render_context") == {
            "pagination_size": 25,
            "sortable_columns": ["name", "price"],
        }

    def test_entity_without_render_context_defaults_to_empty(self, tmp_path):
        """Entity khong co render_context → default {} trong ProjectionNode.params."""
        dsl_dir = tmp_path / "dsl"
        dsl_dir.mkdir()
        (dsl_dir / "entities.yaml").write_text(
            """entities:
  - id: Product
    description: San pham
    fields:
      - name: name
        type: string
""",
            encoding="utf-8",
        )
        (dsl_dir / "commands.yaml").write_text("commands: []\n", encoding="utf-8")
        (dsl_dir / "queries.yaml").write_text("queries: []\n", encoding="utf-8")

        from midicoder.dsl.loader import load_projection_tree

        tree = load_projection_tree(dsl_dir)
        entity_node = tree.get_entities()[0]
        assert entity_node.params.get("render_context") == {}


class TestFileContributionsLoaderRenderContext:
    """Kiem tra render_context inject vao context dict cua FileContributionsLoader."""

    def test_expand_per_entity_injects_render_context(self):
        """expand_per_entity() nen inject render_context vao context."""
        from midicoder.pipeline.file_contributions_loader import (
            FileContributions,
            FileContributionsLoader,
            PerEntityFile,
        )

        entity = {
            "id": "Product",
            "fields": [{"name": "name", "type": "string"}],
            "render_context": {"sidebar_width": 280, "grid_columns": 4},
        }

        entry = PerEntityFile(
            path_pattern="src/{entity_snake}/models.py",
            file_type="python",
            template="entity_model.py.jinja2",
            context_keys=[],
            pack_emitter="cp01_domain_model.fastapi",
            stacks=["fastapi"],
        )
        contributions = FileContributions(
            pack_id="CP01",
            pack_internal_id="cp01_domain_model",
            per_entity=[entry],
            per_command=[],
            per_query=[],
            per_ui_component=[],
            per_widget=[],
            infrastructure=[],
        )

        files = FileContributionsLoader.expand_per_entity(contributions, [entity])
        assert len(files) == 1
        ctx = files[0]["context"]
        assert "render_context" in ctx
        assert ctx["render_context"] == {"sidebar_width": 280, "grid_columns": 4}

    def test_expand_per_command_injects_render_context(self):
        """expand_per_command() nen inject render_context vao context."""
        from midicoder.pipeline.file_contributions_loader import (
            FileContributions,
            FileContributionsLoader,
            PerCommandFile,
        )

        command = {
            "id": "CreateProduct",
            "input": [{"name": "name", "type": "string"}],
            "render_context": {"form_layout": "vertical"},
        }

        entry = PerCommandFile(
            path_pattern="src/{command_snake}/command.py",
            file_type="python",
            template="command.py.jinja2",
            context_keys=[],
            pack_emitter="cp01_domain_model.fastapi",
            stacks=["fastapi"],
        )
        contributions = FileContributions(
            pack_id="CP01",
            pack_internal_id="cp01_domain_model",
            per_entity=[],
            per_command=[entry],
            per_query=[],
            per_ui_component=[],
            per_widget=[],
            infrastructure=[],
        )

        files = FileContributionsLoader.expand_per_command(contributions, [command])
        assert len(files) == 1
        ctx = files[0]["context"]
        assert "render_context" in ctx
        assert ctx["render_context"] == {"form_layout": "vertical"}

    def test_expand_per_query_injects_render_context(self):
        """expand_per_query() nen inject render_context vao context."""
        from midicoder.pipeline.file_contributions_loader import (
            FileContributions,
            FileContributionsLoader,
            PerQueryFile,
        )

        query = {
            "id": "ListProducts",
            "input": [],
            "render_context": {"pagination_size": 25},
        }

        entry = PerQueryFile(
            path_pattern="src/{query_snake}/query.py",
            file_type="python",
            template="query.py.jinja2",
            context_keys=[],
            pack_emitter="cp01_domain_model.fastapi",
            stacks=["fastapi"],
        )
        contributions = FileContributions(
            pack_id="CP01",
            pack_internal_id="cp01_domain_model",
            per_entity=[],
            per_command=[],
            per_query=[entry],
            per_ui_component=[],
            per_widget=[],
            infrastructure=[],
        )

        files = FileContributionsLoader.expand_per_query(contributions, [query])
        assert len(files) == 1
        ctx = files[0]["context"]
        assert "render_context" in ctx
        assert ctx["render_context"] == {"pagination_size": 25}

    def test_expand_infrastructure_has_empty_render_context(self):
        """expand_infrastructure() nen co render_context={} (default)."""
        from midicoder.pipeline.file_contributions_loader import (
            FileContributions,
            FileContributionsLoader,
            InfrastructureFile,
        )

        entry = InfrastructureFile(
            path="docker-compose.yml",
            file_type="yaml",
            template="docker-compose.yml.jinja2",
            context_keys=[],
            pack_emitter="cp07_iac.infrastructure",
            stacks=["infrastructure"],
        )
        contributions = FileContributions(
            pack_id="CP07",
            pack_internal_id="cp07_iac",
            per_entity=[],
            per_command=[],
            per_query=[],
            per_ui_component=[],
            per_widget=[],
            infrastructure=[entry],
        )

        files = FileContributionsLoader.expand_infrastructure(contributions, {})
        assert len(files) == 1
        ctx = files[0]["context"]
        assert "render_context" in ctx
        assert ctx["render_context"] == {}
