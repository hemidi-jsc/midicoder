"""Phase 9G — Test PerUIComponentFile expansion end-to-end.

Verifies that the new per_ui_component expansion type correctly:
1. Parses from pack.yml
2. Expands entities × component_types into file plan dicts
3. Resolves path placeholders ({entity_pascal}, {entity_snake})
4. Injects entity + component_types into context
5. PackEmitterRouter dispatch() handles string component_type list
"""

import pytest
from pathlib import Path

from midicoder.pipeline.file_contributions_loader import (
    FileContributionsLoader,
    FileContributions,
    PerUIComponentFile,
)
from midicoder.packs.cp_full_ui_components.models import (
    ComponentSpec,
    ComponentType,
)

# ─── Test fixtures ───

SAMPLE_ENTITIES = [
    {
        "id": "User",
        "fields": [
            {"name": "email", "type": "str"},
            {"name": "password", "type": "str"},
            {"name": "display_name", "type": "str"},
        ],
    },
    {
        "id": "Order",
        "fields": [
            {"name": "customer_id", "type": "int"},
            {"name": "total_amount", "type": "float"},
            {"name": "status", "type": "str"},
        ],
    },
]


class TestPerUIComponentFileDataclass:
    """9G-1: PerUIComponentFile dataclass fields."""

    def test_create_minimal(self):
        puc = PerUIComponentFile(
            path_pattern="src/components/{entity_pascal}/Form{entity_pascal}.tsx",
            file_type="form_component",
            template="cp_full_ui_components/data-input/FormField.tsx.jinja2",
        )
        assert puc.stacks == []
        assert puc.pack_emitter is None
        assert puc.component_types == []
        assert puc.context_keys == []

    def test_create_full(self):
        puc = PerUIComponentFile(
            path_pattern="src/components/{entity_pascal}/Form{entity_pascal}.tsx",
            file_type="form_component",
            template="cp_full_ui_components/data-input/FormField.tsx.jinja2",
            stacks=["react"],
            pack_emitter="cp19.react",
            component_types=["form_field"],
            context_keys=["entity"],
        )
        assert puc.stacks == ["react"]
        assert puc.pack_emitter == "cp19.react"
        assert puc.component_types == ["form_field"]
        assert puc.context_keys == ["entity"]


class TestExpandPerUIComponent:
    """9G-2: expand_per_ui_component() expands entities × component_types."""

    def _make_contributions(self, entries: list[dict]) -> FileContributions:
        """Helper to create FileContributions with per_ui_component entries."""
        from midicoder.pipeline.file_contributions_loader import _parse_per_ui_component
        parsed = [_parse_per_ui_component(e) for e in entries]
        return FileContributions(
            pack_id="CP19",
            pack_internal_id="cp_full_ui_components",
            per_ui_component=parsed,
        )

    def test_expand_single_entity_single_type(self):
        """User entity + form_field → 1 file."""
        contribs = self._make_contributions([{
            "path_pattern": "src/components/{entity_pascal}/Form{entity_pascal}.tsx",
            "file_type": "form_component",
            "template": "cp_full_ui_components/data-input/FormField.tsx.jinja2",
            "stacks": ["react"],
            "pack_emitter": "cp19.react",
            "component_types": ["form_field"],
            "context_keys": [],
        }])

        files = FileContributionsLoader.expand_per_ui_component(contribs, SAMPLE_ENTITIES)
        assert len(files) == 2  # User + Order

        user_file = [f for f in files if "User" in f["path"]][0]
        assert user_file["path"] == "src/components/User/FormUser.tsx"
        assert user_file["type"] == "form_component"
        assert user_file["context"]["entity"]["id"] == "User"
        assert user_file["context"]["components"] == ["form_field"]
        assert user_file["metadata"]["pack_emitter"] == "cp19.react"

        order_file = [f for f in files if "Order" in f["path"]][0]
        assert order_file["path"] == "src/components/Order/FormOrder.tsx"

    def test_expand_multiple_entities_multiple_types(self):
        """2 entities × 4 types = 8 files."""
        contribs = self._make_contributions([
            # Form
            {"path_pattern": "src/components/{entity_pascal}/Form{entity_pascal}.tsx",
             "file_type": "form_component", "template": "t1",
             "stacks": ["react"], "pack_emitter": "cp19.react",
             "component_types": ["form_field"], "context_keys": []},
            # Table
            {"path_pattern": "src/components/{entity_pascal}/Table{entity_pascal}.tsx",
             "file_type": "table_component", "template": "t2",
             "stacks": ["react"], "pack_emitter": "cp19.react",
             "component_types": ["data_table"], "context_keys": []},
            # Card List
            {"path_pattern": "src/components/{entity_pascal}/CardList{entity_pascal}.tsx",
             "file_type": "card_component", "template": "t3",
             "stacks": ["react"], "pack_emitter": "cp19.react",
             "component_types": ["card_list"], "context_keys": []},
            # Dialog
            {"path_pattern": "src/components/{entity_pascal}/Dialog{entity_pascal}.tsx",
             "file_type": "dialog_component", "template": "t4",
             "stacks": ["react"], "pack_emitter": "cp19.react",
             "component_types": ["dialog"], "context_keys": []},
        ])

        files = FileContributionsLoader.expand_per_ui_component(contribs, SAMPLE_ENTITIES)
        assert len(files) == 8  # 2 entities × 4 types

        # Verify paths
        paths = sorted([f["path"] for f in files])
        assert "src/components/Order/CardListOrder.tsx" in paths
        assert "src/components/Order/DialogOrder.tsx" in paths
        assert "src/components/Order/FormOrder.tsx" in paths
        assert "src/components/Order/TableOrder.tsx" in paths
        assert "src/components/User/CardListUser.tsx" in paths
        assert "src/components/User/DialogUser.tsx" in paths
        assert "src/components/User/FormUser.tsx" in paths
        assert "src/components/User/TableUser.tsx" in paths

    def test_expand_path_placeholders(self):
        """Verify {entity_snake}, {entity_camel} work in path patterns."""
        contribs = self._make_contributions([{
            "path_pattern": "src/components/{entity_snake}/{entity_snake}_form.tsx",
            "file_type": "form",
            "template": "t",
            "stacks": ["react"],
            "pack_emitter": "cp19.react",
            "component_types": ["form_field"],
            "context_keys": [],
        }])

        # Use entity with compound name
        entities = [{"id": "OrderItem", "fields": []}]
        files = FileContributionsLoader.expand_per_ui_component(contribs, entities)

        assert len(files) == 1
        # OrderItem → order_item (snake_case)
        assert files[0]["path"] == "src/components/order_item/order_item_form.tsx"

    def test_expand_empty_entities(self):
        """No entities → 0 files."""
        contribs = self._make_contributions([{
            "path_pattern": "src/components/{entity_pascal}/Form{entity_pascal}.tsx",
            "file_type": "form_component",
            "template": "t",
            "stacks": ["react"],
            "pack_emitter": "cp19.react",
            "component_types": ["form_field"],
            "context_keys": [],
        }])
        files = FileContributionsLoader.expand_per_ui_component(contribs, [])
        assert len(files) == 0

    def test_expand_injects_all_entities(self):
        """Context should contain all_entities for cross-reference."""
        contribs = self._make_contributions([{
            "path_pattern": "src/c/{entity_pascal}.tsx",
            "file_type": "f",
            "template": "t",
            "stacks": ["react"],
            "pack_emitter": "cp19.react",
            "component_types": ["form_field"],
            "context_keys": [],
        }])
        files = FileContributionsLoader.expand_per_ui_component(contribs, SAMPLE_ENTITIES)
        for f in files:
            assert "all_entities" in f["context"]
            assert len(f["context"]["all_entities"]) == 2

    def test_expand_angular_paths(self):
        """Angular-style path pattern with subdirs."""
        contribs = self._make_contributions([{
            "path_pattern": "src/app/shared/components/{entity_pascal}/form-{entity_snake}.component.ts",
            "file_type": "form_field_component",
            "template": "cp_full_ui_components/data-input/form-field.component.ts.jinja2",
            "stacks": ["angular"],
            "pack_emitter": "cp19.angular",
            "component_types": ["form_field"],
            "context_keys": [],
        }])
        files = FileContributionsLoader.expand_per_ui_component(contribs, SAMPLE_ENTITIES)
        paths = [f["path"] for f in files]
        assert "src/app/shared/components/User/form-user.component.ts" in paths
        assert "src/app/shared/components/Order/form-order.component.ts" in paths


class TestResolveAllPerUIComponent:
    """9G-3: resolve_all_per_ui_component() loads from disk + deduplicates."""

    def test_loads_cp19_per_ui_component(self):
        """Loader reads CP19 pack.yml per_ui_component section."""
        loader = FileContributionsLoader()
        fc = loader.load("cp_full_ui_components", "CP19", stack="react")

        assert len(fc.per_ui_component) > 0
        assert any(
            e.path_pattern.endswith("Form{entity_pascal}.tsx")
            for e in fc.per_ui_component
        )

    def test_resolve_returns_files_per_entity(self):
        """resolve_all_per_ui_component returns files for each entity."""
        loader = FileContributionsLoader()
        files = loader.resolve_all_per_ui_component("react", SAMPLE_ENTITIES)

        # Should have 4 types × 2 entities = 8 files
        assert len(files) >= 8

        # All should have react stack
        for f in files:
            assert "react" in str(f.get("metadata", {}).get("stacks", "")) or \
                   f.get("metadata", {}).get("pack_emitter", "").startswith("cp19.react")

    def test_deduplication(self):
        """Same path from multiple packs → only 1 file."""
        # CP19 is the only pack with per_ui_component, but test dedup logic
        loader = FileContributionsLoader()
        files = loader.resolve_all_per_ui_component("react", SAMPLE_ENTITIES)
        paths = [f["path"] for f in files]
        assert len(paths) == len(set(paths))  # no duplicates

    def test_angular_stack(self):
        """Angular stack resolves with angular paths."""
        loader = FileContributionsLoader()
        files = loader.resolve_all_per_ui_component("angular", SAMPLE_ENTITIES)

        assert len(files) > 0
        # Angular paths should end with .component.ts
        angular_files = [f for f in files if f["path"].endswith(".component.ts")]
        assert len(angular_files) > 0


class TestPackEmitterRouterDispatch:
    """9G-4: dispatch() handles string component_type list from per_ui_component expansion."""

    def test_dispatch_with_string_component_types(self):
        """context['components'] = ['form_field'] + context['entity'] → generates form."""
        from midicoder.pipeline.pack_emitter_router import PackEmitterRouter

        entity = {
            "id": "TestEntity",
            "fields": [
                {"name": "name", "type": "str"},
                {"name": "age", "type": "int"},
            ],
        }
        file_spec = {
            "path": "src/components/TestEntity/FormTestEntity.tsx",
            "type": "form_component",
            "template": "cp_full_ui_components/data-input/FormField.tsx.jinja2",
            "context": {
                "entity": entity,
                "components": ["form_field"],  # ← string list from per_ui_component
                "all_entities": [entity],
            },
            "metadata": {"pack_emitter": "cp19.react", "stack": "react"},
        }

        results = PackEmitterRouter.dispatch("cp19.react", file_spec, "react")
        assert len(results) >= 1
        assert "content" in results[0]
        # Content should be non-empty TypeScript/JSX
        content = results[0]["content"]
        assert len(content) > 100  # real generated content
        assert "TestEntity" in content or "testEntity" in content or "form" in content.lower()

    def test_dispatch_with_multiple_component_types(self):
        """context['components'] = ['form_field', 'data_table'] → generates both."""
        from midicoder.pipeline.pack_emitter_router import PackEmitterRouter

        entity = {
            "id": "TestEntity",
            "fields": [
                {"name": "name", "type": "str"},
                {"name": "count", "type": "int"},
            ],
        }
        file_spec = {
            "path": "src/components/TestEntity/FormTestEntity.tsx",
            "type": "ui_component",
            "template": "cp_full_ui_components/data-input/FormField.tsx.jinja2",
            "context": {
                "entity": entity,
                "components": ["form_field", "data_table"],
                "all_entities": [entity],
            },
            "metadata": {"pack_emitter": "cp19.react", "stack": "react"},
        }

        results = PackEmitterRouter.dispatch("cp19.react", file_spec, "react")
        assert len(results) >= 2  # form_field + data_table

    def test_dispatch_with_dict_components(self):
        """context['components'] = [dict] → uses ComponentSpec.from_dict."""
        from midicoder.pipeline.pack_emitter_router import PackEmitterRouter

        entity = {
            "id": "TestEntity",
            "fields": [{"name": "name", "type": "str"}],
        }
        comp_dict = {
            "component_type": "form_field",
            "entity_id": "TestEntity",
            "fields": [{"name": "name", "binding_path": "name", "field_type": "text"}],
        }
        file_spec = {
            "path": "src/components/TestEntity/FormTestEntity.tsx",
            "type": "ui_component",
            "template": "cp_full_ui_components/data-input/FormField.tsx.jinja2",
            "context": {
                "entity": entity,
                "components": [comp_dict],  # ← dict list
            },
            "metadata": {"pack_emitter": "cp19.react", "stack": "react"},
        }

        results = PackEmitterRouter.dispatch("cp19.react", file_spec, "react")
        assert len(results) >= 1


class TestEndToEnd:
    """9G-5: Full end-to-end: pack.yml → loader → expand → dispatch → content."""

    def test_react_full_pipeline(self):
        """Load CP19 pack.yml → expand for entities → dispatch → verify content."""
        from midicoder.pipeline.pack_emitter_router import PackEmitterRouter

        loader = FileContributionsLoader()
        files = loader.resolve_all_per_ui_component("react", SAMPLE_ENTITIES)

        for f in files:
            # Inject ui_framework
            f.setdefault("context", {})["ui_framework"] = "antd"

            pack_emitter = f.get("metadata", {}).get("pack_emitter")
            if not pack_emitter:
                continue
            if not pack_emitter.startswith("cp19."):
                continue

            results = PackEmitterRouter.dispatch(pack_emitter, f, "react")
            assert len(results) >= 1, f"No results for {f['path']}"
            for r in results:
                assert "content" in r
                assert len(r["content"]) > 50, f"Empty content for {r['path']}"

    def test_angular_full_pipeline(self):
        """Load CP19 pack.yml → expand for entities → dispatch → verify content."""
        from midicoder.pipeline.pack_emitter_router import PackEmitterRouter

        loader = FileContributionsLoader()
        files = loader.resolve_all_per_ui_component("angular", SAMPLE_ENTITIES)

        for f in files:
            f.setdefault("context", {})["ui_framework"] = "material"

            pack_emitter = f.get("metadata", {}).get("pack_emitter")
            if not pack_emitter:
                continue
            if not pack_emitter.startswith("cp19."):
                continue

            results = PackEmitterRouter.dispatch(pack_emitter, f, "angular")
            assert len(results) >= 1, f"No results for {f['path']}"
            for r in results:
                assert "content" in r
                assert len(r["content"]) > 50, f"Empty content for {r['path']}"


class TestFileContributionsIsNotEmpty:
    """9G-6: FileContributions.is_empty includes per_ui_component."""

    def test_empty_without_per_ui_component(self):
        fc = FileContributions(pack_id="X", pack_internal_id="x")
        assert fc.is_empty is True

    def test_not_empty_with_per_ui_component(self):
        from midicoder.pipeline.file_contributions_loader import _parse_per_ui_component
        parsed = [_parse_per_ui_component({
            "path_pattern": "src/c/{entity_pascal}.tsx",
            "file_type": "f",
            "template": "t",
            "stacks": ["react"],
        })]
        fc = FileContributions(
            pack_id="CP19",
            pack_internal_id="cp_full_ui_components",
            per_ui_component=parsed,
        )
        assert fc.is_empty is False
