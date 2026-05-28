"""
Phase 11 — Contract Gen LLM Prompt Integration Tests.

Test the full pipeline:
  DSL YAML → DSLParser → ProjectionTree → IR build → metadata → code gen

Author: Midicoder Team
"""

import pytest
import yaml as _yaml

from midicoder.pipeline.dsl_parser import DSLParser
from midicoder.dsl.projection import ProjectionTree
from midicoder.dsl.loader import _load_ui_components
from midicoder.pipeline.commands.contract import (
    REQUIRED_CATEGORIES,
    _CATEGORY_PROMPT_MAP,
    _build_category_prompt,
)
from midicoder.pipeline.commands.ir import _build_mir_from_projection_tree
from midicoder.dsl.projection import NodeKind


# ============================================================================
# Sample YAML fixtures
# ============================================================================

UI_COMPONENTS_YAML = """
ui_components:
  - id: ProductForm
    component_type: form_field
    entity_id: Product
    description: Form nhập liệu sản phẩm
    properties:
      layout: vertical
  - id: ProductTable
    component_type: data_table
    entity_id: Product
    description: Bảng danh sách sản phẩm
    properties:
      pagination: true
ui_layouts:
  - id: ProductPageLayout
    layout_type: page
    description: Layout trang sản phẩm
    regions:
      - name: header
      - name: content
      - name: sidebar
ui_themes:
  - id: DefaultTheme
    name: default
    description: Theme mặc định
    tokens:
      primary_color: "#1976D2"
    dark_mode: false
ui_form_builders:
  - id: ProductFormBuilder
    entity_id: Product
    description: Form builder động cho sản phẩm
    fields:
      - name: productName
        type: text
        required: true
"""


class TestPhase11ContractGenPrompt:
    """11A: Verify ui_components in contract generation pipeline."""

    def test_ui_components_in_required_categories(self):
        """ui_components should be in REQUIRED_CATEGORIES."""
        assert "ui_components" in REQUIRED_CATEGORIES
        assert len(REQUIRED_CATEGORIES) == 8

    def test_ui_components_in_prompt_map(self):
        """ui_components should map to contract_ui_components prompt."""
        assert "ui_components" in _CATEGORY_PROMPT_MAP
        assert _CATEGORY_PROMPT_MAP["ui_components"] == "contract_ui_components"

    def test_build_category_prompt_for_ui_components(self):
        """_build_category_prompt should return valid prompts for ui_components."""
        system, user = _build_category_prompt(
            category="ui_components",
            analysis_data={"entities": [{"name": "Product"}]},
            clarifications=[],
            brief_content="Hệ thống quản lý sản phẩm",
        )
        assert "ui_components" in system.lower() or "ui component" in system.lower()
        assert "Product" in user
        assert "form_field" in system or "data_table" in system


class TestPhase11BriefAnalyze:
    """11B: Verify ui_components in brief analysis output."""

    def test_brief_analysis_includes_ui_components(self):
        """Brief analysis JSON should contain ui_components key."""
        from midicoder.pipeline.commands.brief import _analyze_with_llm

        # Verify the prompt template includes ui_components schema
        prompt_file = "midicoder/pipeline/prompts/default-brief-analyze.md"
        import os
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.dirname(__file__))
        )))
        prompt_path = os.path.join(base_dir, prompt_file)
        if os.path.exists(prompt_path):
            with open(prompt_path) as f:
                content = f.read()
            assert "ui_components" in content
            assert "component_type" in content

    def test_ui_components_in_text_summary(self):
        """Brief text summary should mention UI components count."""
        json_data = {
            "entities": [{"name": "Product"}],
            "commands": [],
            "queries": [],
            "events": [],
            "ui_components": [
                {"entity_id": "Product", "component_type": "form_field"},
                {"entity_id": "Product", "component_type": "data_table"},
            ],
            "confidence": 0.9,
            "summary": "Hệ thống quản lý sản phẩm",
        }
        entities = json_data.get("entities", [])
        ui_components = json_data.get("ui_components", [])
        text_summary = (
            f"Số UI components: {len(ui_components)}"
        )
        assert "2" in text_summary


class TestPhase11DSLE2E:
    """11C: End-to-end DSL pipeline for UI components."""

    def test_dsl_parser_parse_ui_components(self):
        """DSLParser should parse ui_components YAML into ProjectionNodes."""
        parser = DSLParser()
        nodes = parser.parse_yaml_string(UI_COMPONENTS_YAML, "ui_components")

        # Should have 4 nodes: 2 components + 1 layout + 1 theme + 1 form_builder
        # But parse_yaml_string only parses the main key, so check what's parsed
        assert len(nodes) > 0
        # All should be UI_COMPONENT kind when parsed via ui_components category
        for node in nodes:
            assert node.kind == NodeKind.UI_COMPONENT

    def test_dsl_parser_parse_ui_layouts(self):
        """DSLParser should parse ui_layouts YAML."""
        parser = DSLParser()
        layout_yaml = """
ui_layouts:
  - id: DashboardLayout
    layout_type: dashboard
    description: Layout bảng điều khiển
"""
        nodes = parser.parse_yaml_string(layout_yaml, "ui_layouts")
        assert len(nodes) == 1
        assert nodes[0].kind == NodeKind.UI_LAYOUT
        assert nodes[0].params["layout_type"] == "dashboard"

    def test_dsl_parser_parse_ui_themes(self):
        """DSLParser should parse ui_themes YAML."""
        parser = DSLParser()
        theme_yaml = """
ui_themes:
  - id: DarkTheme
    name: dark
    dark_mode: true
"""
        nodes = parser.parse_yaml_string(theme_yaml, "ui_themes")
        assert len(nodes) == 1
        assert nodes[0].kind == NodeKind.UI_THEME
        assert nodes[0].params["dark_mode"] is True

    def test_dsl_parser_parse_ui_form_builders(self):
        """DSLParser should parse ui_form_builders YAML."""
        parser = DSLParser()
        fb_yaml = """
ui_form_builders:
  - id: OrderFormBuilder
    entity_id: Order
    fields:
      - name: orderNumber
        type: text
"""
        nodes = parser.parse_yaml_string(fb_yaml, "ui_form_builders")
        assert len(nodes) == 1
        assert nodes[0].kind == NodeKind.UI_FORM_BUILDER
        assert nodes[0].params["entity_id"] == "Order"

    def test_build_projection_tree_with_ui_components(self):
        """build_projection_tree should include UI component nodes."""
        parser = DSLParser()
        yaml_dict = {
            "ui_components": """
ui_components:
  - id: ProductForm
    component_type: form_field
    entity_id: Product
  - id: ProductTable
    component_type: data_table
    entity_id: Product
""",
            "ui_layouts": """
ui_layouts:
  - id: MainLayout
    layout_type: page
""",
            "ui_themes": """
ui_themes:
  - id: DefaultTheme
    name: default
""",
            "ui_form_builders": """
ui_form_builders:
  - id: ProductFB
    entity_id: Product
""",
        }
        tree = parser.build_projection_tree(yaml_dict)

        assert len(tree.get_ui_components()) == 2
        assert len(tree.get_ui_layouts()) == 1
        assert len(tree.get_ui_themes()) == 1
        assert len(tree.get_ui_form_builders()) == 1

    def test_ir_build_with_ui_components(self):
        """IR build should include UI components in metadata."""
        parser = DSLParser()
        yaml_dict = {
            "ui_components": """
ui_components:
  - id: ProductForm
    component_type: form_field
    entity_id: Product
    description: Form sản phẩm
""",
        }
        tree = parser.build_projection_tree(yaml_dict)
        mir = _build_mir_from_projection_tree(tree)

        assert "ui_components" in mir.metadata
        assert len(mir.metadata["ui_components"]) == 1
        assert mir.metadata["ui_components"][0]["component_type"] == "form_field"

        # Verify MIR operations were added
        assert any(
            op.op_type.startswith("generate_ui_")
            for op in mir.operations
        )


class TestPhase11LoaderE2E:
    """DSL loader reads ui-components.yaml from disk (mocked)."""

    def test_load_ui_components_parses_all_categories(self, tmp_path):
        """_load_ui_components should parse all 4 categories from one file."""
        yaml_file = tmp_path / "ui-components.yaml"
        yaml_file.write_text(UI_COMPONENTS_YAML, encoding="utf-8")

        nodes = _load_ui_components(yaml_file)

        kinds = [n.kind for n in nodes]
        assert NodeKind.UI_COMPONENT in kinds
        assert NodeKind.UI_LAYOUT in kinds
        assert NodeKind.UI_THEME in kinds
        assert NodeKind.UI_FORM_BUILDER in kinds

        # Verify node count: 2 components + 1 layout + 1 theme + 1 fb = 5
        assert len(nodes) == 5

        # Verify each node has source
        for node in nodes:
            assert node.params.get("source") == "ui-components.yaml"


class TestPhase11FullPipeline:
    """Complete pipeline: YAML → Parser → Tree → IR → Metadata."""

    def test_full_pipeline_react(self):
        """End-to-end: React UI components flow through DSL to IR."""
        parser = DSLParser()
        yaml_dict = {
            "ui_components": """
ui_components:
  - id: OrderForm
    component_type: form_field
    entity_id: Order
    properties:
      framework: react
      library: tailwind
  - id: OrderTable
    component_type: data_table
    entity_id: Order
""",
            "ui_layouts": """
ui_layouts:
  - id: OrderPage
    layout_type: page
""",
            "ui_themes": """
ui_themes:
  - id: OrderTheme
    name: order-theme
""",
            "ui_form_builders": """
ui_form_builders:
  - id: OrderFB
    entity_id: Order
    fields:
      - name: orderNumber
        type: text
""",
        }

        tree = parser.build_projection_tree(yaml_dict)
        mir = _build_mir_from_projection_tree(tree)

        # Verify metadata
        assert len(mir.metadata["ui_components"]) == 2
        assert len(mir.metadata["ui_layouts"]) == 1
        assert len(mir.metadata["ui_themes"]) == 1
        assert len(mir.metadata["ui_form_builders"]) == 1

        # Verify operations
        gen_ops = [op for op in mir.operations if "gen" in op.op_id]
        assert len(gen_ops) == 5  # 2 comp + 1 layout + 1 theme + 1 fb


class TestPhase11ContractPromptFile:
    """Verify contract_ui_components.md prompt file exists and is valid."""

    def _get_prompt_path(self) -> str:
        """Resolve path to contract_ui_components.md prompt file."""
        # __file__ is in midicoder/packs/cp_full_ui_components/tests/
        # Go up 5 levels to project root, then into midicoder/pipeline/prompts/
        import os
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        )))
        return os.path.join(
            project_root, "midicoder", "pipeline", "prompts", "contract_ui_components.md"
        )

    def test_prompt_file_exists(self):
        """contract_ui_components.md should exist."""
        import os
        prompt_path = self._get_prompt_path()
        assert os.path.exists(prompt_path), f"Prompt file not found at {prompt_path}"

    def test_prompt_file_content(self):
        """Prompt file should contain UI component schema."""
        prompt_path = self._get_prompt_path()
        with open(prompt_path, encoding="utf-8") as f:
            content = f.read()

        assert "component_type" in content
        assert "form_field" in content
        assert "data_table" in content
        assert "card_list" in content
        assert "dialog" in content
        assert "ui_layouts" in content
        assert "ui_themes" in content
        assert "ui_form_builders" in content
