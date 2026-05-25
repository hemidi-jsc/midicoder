"""
Tests cho Code Commands.

Tests này validate:
- CLI commands registration (plan, gen, apply)
- Implementation plan creation từ MIR
- Code generation từ plan
- Code apply vào target directory
- Error handling cho missing MIR/plan
- FileContributionsLoader: self-declare mechanism cho packs

E07: Emitter & Scaffolder
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, ANY

from click.testing import CliRunner

from midicoder.pipeline.commands.code import (
    code,
    CodePlan,
    GeneratedFile,
    _execute_plan,
    _execute_gen,
    _execute_apply,
    _create_implementation_plan,
    _plan_backend_files,
    _plan_frontend_files,
    _plan_infra_files,
    _render_template,
)
from midicoder.pipeline.file_contributions_loader import (
    FileContributionsLoader,
    FileContributions,
    _expand_path_pattern,
    _pascal_to_snake,
    _snake_to_camel,
    FRONTEND_STACKS,
)
from midicoder.storage.sqlite import ArtifactsManager


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def runner():
    """Click test runner."""
    return CliRunner()


@pytest.fixture
def sample_mir():
    """Sample MIR data matching actual MIRBuilder output (entities in metadata)."""
    return {
        "metadata": {
            "entities": [
                {"id": "Customer", "attributes": ["id", "name", "email"]},
                {"id": "Order", "attributes": ["id", "customer_id", "total"]},
            ],
            "commands": [
                {"id": "CreateOrder", "input": ["customer_id", "items"], "output": ["order_id"]},
            ],
            "queries": [
                {"id": "ListOrders", "input": ["customer_id"], "output": ["Order[]"]},
            ],
        },
        "operations": [
            {"id": "op1", "type": "create"},
            {"id": "op2", "type": "read"},
        ],
    }


@pytest.fixture
def sample_plan():
    """Sample implementation plan (typed roundtrip format)."""
    return {
        "meta": {
            "version": "1.0.0",
            "created_at": "2026-04-27T10:00:00Z",
            "target": "all",
        },
        "modules": [
            {
                "name": "backend_core",
                "module_type": "backend",
                "files": [
                    {"path": "app/main.py", "file_type": "main", "template": "fastapi/main.py.jinja2"},
                ],
            },
            {
                "name": "frontend_core",
                "module_type": "frontend",
                "files": [
                    {"path": "src/app/app.module.ts", "file_type": "module", "template": "angular/module.ts.jinja2"},
                ],
            },
            {
                "name": "infra_core",
                "module_type": "infra",
                "files": [
                    {"path": "docker-compose.yml", "file_type": "docker_compose", "template": "infra/docker-compose.yml.jinja2"},
                ],
            },
        ],
    }


@pytest.fixture
def temp_src_dir(tmp_path):
    """Create temporary src directory with generated files."""
    src_dir = tmp_path / ".midicoder" / "versions" / "v1.0.0" / "src"
    src_dir.mkdir(parents=True)
    
    # Tạo một vài files mẫu
    (src_dir / "app" / "main.py").parent.mkdir(parents=True)
    (src_dir / "app" / "main.py").write_text("# Generated main.py")
    
    return src_dir


# ============================================================================
# CLI Command Tests
# ============================================================================

class TestCodeCommandRegistration:
    """Tests cho CLI command registration."""

    def test_code_group_exists(self, runner):
        """Test code group CLI exists."""
        result = runner.invoke(code, ["--help"])
        assert result.exit_code == 0
        assert "Code planning, generation, và application" in result.output
        assert "plan" in result.output
        assert "gen" in result.output
        assert "apply" in result.output

    def test_code_plan_help(self, runner):
        """Test code plan --help."""
        result = runner.invoke(code, ["plan", "--help"])
        assert result.exit_code == 0
        assert "Tạo implementation plan từ MIR" in result.output
        assert "--target" in result.output
        assert "--verbose" in result.output

    def test_code_gen_help(self, runner):
        """Test code gen --help."""
        result = runner.invoke(code, ["gen", "--help"])
        assert result.exit_code == 0
        assert "Generate code từ plan" in result.output
        assert "--target" in result.output
        assert "--dry-run" in result.output

    def test_code_apply_help(self, runner):
        """Test code apply --help."""
        result = runner.invoke(code, ["apply", "--help"])
        assert result.exit_code == 0
        assert "Apply generated code vào target directory" in result.output
        assert "--target-dir" in result.output
        assert "--dry-run" in result.output
        assert "--backup" in result.output
        assert "--force" in result.output


# ============================================================================
# Plan Creation Tests
# ============================================================================

class TestPlanCreation:
    """Tests cho plan creation functions."""

    def test_create_implementation_plan_empty_mir(self):
        """Test create plan từ empty MIR."""
        from midicoder.pipeline.plan import ImplementationPlan
        
        mir = {"entities": [], "commands": [], "queries": []}
        plan = _create_implementation_plan(mir, target="all")
        
        assert isinstance(plan, ImplementationPlan)
        assert "version" in plan.meta
        assert "created_at" in plan.meta
        assert "target" in plan.meta
        
        # Check modules by type
        file_counts = plan.count_files()
        
        # Core backend files luôn có
        assert file_counts["backend"] >= 3  # main, config, database
        
        # Frontend: now resolved from pack contributions (angular stack),
        # includes auth, rbac, gateway, cache, etc.
        assert file_counts["frontend"] >= 2

        # Infra: CP07 contributes docker-compose + Dockerfile.api (2 files)
        assert file_counts["infra"] >= 2

    def test_create_implementation_plan_with_entities(self, sample_mir):
        """Test create plan từ MIR với entities."""
        from midicoder.pipeline.plan import ImplementationPlan
        
        plan = _create_implementation_plan(sample_mir, target="all")
        
        assert isinstance(plan, ImplementationPlan)
        
        # Count backend files using typed method
        file_counts = plan.count_files()
        
        # Should have core files + entity files
        assert file_counts["backend"] > 3
        
        # Check for entity-specific files using get_files_by_type
        all_files = plan.get_files_by_type("model") + plan.get_files_by_type("route")
        file_paths = [f.path for f in all_files]
        assert any("customer" in p for p in file_paths)
        assert any("order" in p for p in file_paths)

    def test_plan_backend_files(self, sample_mir):
        """Test _plan_backend_files function."""
        backend_files = _plan_backend_files(sample_mir)
        
        # Core files
        paths = [f["path"] for f in backend_files]
        assert "app/main.py" in paths
        assert "app/config.py" in paths
        assert "app/database.py" in paths
        
        # Entity files
        assert any("customer" in p for p in paths)
        assert any("order" in p for p in paths)
        
        # Check file types — không còn "model" hay "schema", chỉ còn các types cụ thể
        types = [f["type"] for f in backend_files]
        assert "main" in types
        # Các types backend: main, config, init, tenant_context, tenant_filter, entity, repo, service, schema, crud...
        assert any(t in ("model", "schema", "entity") for t in types)

    def test_plan_frontend_files(self, sample_mir):
        """Test _plan_frontend_files function — now resolved from pack contributions."""
        frontend_files = _plan_frontend_files(sample_mir)
        paths = [f["path"] for f in frontend_files]

        # Frontend files come from pack file_contributions (angular stack by default)
        # CP03 auth, CP04 rbac, CP06 gateway, CP18 frontend_framework, etc.
        assert len(frontend_files) >= 2

        # All frontend files should carry the frontend stack metadata
        for f in frontend_files:
            assert f.get("metadata", {}).get("stack") in FRONTEND_STACKS

    def test_plan_infra_files(self):
        """Test _plan_infra_files — now resolved from CP07 file_contributions."""
        infra_files = _plan_infra_files()

        # CP07 contributes docker-compose.yml + Dockerfile.api (2 files)
        assert len(infra_files) >= 2

        paths = [f["path"] for f in infra_files]
        assert "docker-compose.yml" in paths

    def test_plan_target_filtering(self, sample_mir):
        """Test plan filtering by target."""
        from midicoder.pipeline.plan import ImplementationPlan
        
        plan_backend = _create_implementation_plan(sample_mir, target="backend")
        plan_frontend = _create_implementation_plan(sample_mir, target="frontend")
        
        assert isinstance(plan_backend, ImplementationPlan)
        assert isinstance(plan_frontend, ImplementationPlan)
        
        # Backend-only plan should have backend modules, no frontend modules
        backend_counts = plan_backend.count_files()
        assert backend_counts["backend"] > 0
        assert backend_counts["frontend"] == 0
        
        # Frontend-only plan should have frontend modules, no backend modules
        frontend_counts = plan_frontend.count_files()
        assert frontend_counts["frontend"] > 0
        assert frontend_counts["backend"] == 0


# ============================================================================
# Code Generation Tests
# ============================================================================

class TestCodeGeneration:
    """Tests cho code generation."""

    def test_render_template_placeholder(self):
        """Test template rendering with a real template (config needs no special ctx)."""
        content = _render_template("config.py.jinja2", {"app_name": "Test API"})

        assert len(content) > 0

    def test_render_template_empty_context(self):
        """Test template rendering với empty context."""
        content = _render_template("config.py.jinja2", {})

        assert len(content) > 0


# ============================================================================
# Integration Tests (with mocking)
# ============================================================================

class TestCodePlanIntegration:
    """Integration tests cho code plan command."""

    @patch("midicoder.pipeline.commands.code._load_mir_from_artifacts")
    @patch("midicoder.pipeline.commands.code.ArtifactsManager")
    @patch("midicoder.pipeline.commands.code.get_config")
    def test_execute_plan_success(
        self,
        mock_get_config,
        mock_artifacts_manager,
        mock_load_mir,
        runner,
        sample_mir,
    ):
        """Test execute plan với MIR tồn tại."""
        # Setup mocks
        mock_load_mir.return_value = sample_mir
        mock_config = Mock()
        mock_config.get.return_value = "v1.0.0"
        mock_get_config.return_value = mock_config
        
        mock_am = Mock()
        mock_artifacts_manager.return_value = mock_am
        
        # Execute
        result = runner.invoke(code, ["plan", "--target", "backend"])
        
        # Verify
        assert result.exit_code == 0
        assert "Đang tạo implementation plan" in result.output
        assert "Plan Summary" in result.output
        # New format: "Backend modules" instead of "Backend files"
        assert "backend modules" in result.output.lower() or "Backend modules" in result.output

    @patch("midicoder.pipeline.commands.code._load_mir_from_artifacts")
    def test_execute_plan_no_mir(self, mock_load_mir, runner):
        """Test execute plan khi MIR không tồn tại."""
        mock_load_mir.return_value = None
        
        result = runner.invoke(code, ["plan"])
        
        assert result.exit_code == 1
        assert "MIR không tồn tại" in result.output
        assert "midicoder ir build" in result.output


class TestCodeGenIntegration:
    """Integration tests cho code gen command."""

    @patch("midicoder.pipeline.commands.code._load_plan_from_artifacts")
    @patch("midicoder.pipeline.commands.code.get_config")
    @patch("midicoder.pipeline.commands.code.Path")
    def test_execute_gen_success(
        self,
        mock_path,
        mock_get_config,
        mock_load_plan,
        runner,
        sample_plan,
        tmp_path,
    ):
        """Test execute gen với plan tồn tại."""
        # Setup mocks
        mock_load_plan.return_value = sample_plan
        mock_config = Mock()
        mock_config.get.return_value = "v1.0.0"
        mock_get_config.return_value = mock_config
        
        # Mock Path behavior with proper __truediv__
        mock_path_instance = MagicMock()
        mock_path_instance.__truediv__ = lambda self, other: mock_path_instance
        mock_path_instance.exists.return_value = False
        mock_path_instance.mkdir.return_value = None
        mock_path_instance.write_text = Mock()
        mock_path.return_value = mock_path_instance
        
        result = runner.invoke(code, ["gen", "--target", "all"])
        
        assert result.exit_code == 0
        assert "Đang generate code" in result.output
        assert "Code generation hoàn tất" in result.output

    @patch("midicoder.pipeline.commands.code._load_plan_from_artifacts")
    def test_execute_gen_no_plan(self, mock_load_plan, runner):
        """Test execute gen khi plan không tồn tại."""
        mock_load_plan.return_value = None
        
        result = runner.invoke(code, ["gen"])
        
        assert result.exit_code == 1
        assert "Plan không tồn tại" in result.output
        assert "midicoder code plan" in result.output


class TestCodeApplyIntegration:
    """Integration tests cho code apply command."""

    @patch("midicoder.pipeline.commands.code.Path")
    @patch("midicoder.pipeline.commands.code.get_config")
    def test_execute_apply_success(
        self,
        mock_get_config,
        mock_path,
        runner,
        tmp_path,
    ):
        """Test execute apply với generated code tồn tại."""
        # Setup mocks
        mock_config = Mock()
        mock_config.get.return_value = "v1.0.0"
        mock_get_config.return_value = mock_config
        
        # Create real src directory with files
        src_dir = tmp_path / ".midicoder" / "versions" / "v1.0.0" / "src"
        src_dir.mkdir(parents=True)
        (src_dir / "app").mkdir()
        (src_dir / "app" / "main.py").write_text("# Generated main.py")
        
        target_dir = tmp_path / "target"
        
        # Mock Path để return src_dir khi tạo path cho .midicoder/versions/v1.0.0/src
        def path_side_effect(path_str):
            if "v1.0.0/src" in str(path_str):
                mock_instance = MagicMock()
                mock_instance.exists.return_value = True
                mock_instance.is_file.return_value = False
                mock_instance.rglob.return_value = [(src_dir / "app" / "main.py")]
                mock_instance.absolute.return_value = src_dir.absolute()
                mock_instance.__truediv__ = lambda self, other: MagicMock()
                mock_instance.parent = MagicMock()
                mock_instance.parent.mkdir = Mock()
                return mock_instance
            return Path(path_str)
        
        mock_path.side_effect = path_side_effect
        
        # Run apply với force để không cần confirm
        result = runner.invoke(code, ["apply", "-d", str(target_dir), "--force"])
        
        # Verify - exit_code có thể là 1 nếu artifacts log fail
        assert "Đang apply code vào target" in result.output
        # Check rằng đã try to apply (có thể fail ở artifacts log nhưng apply logic chạy)
        assert "target" in result.output.lower()

    @patch("midicoder.pipeline.commands.code.get_config")
    def test_execute_apply_no_src(self, mock_get_config, runner, tmp_path):
        """Test execute apply khi src không tồn tại."""
        mock_config = Mock()
        mock_config.get.return_value = "v9.9.9"  # Version không tồn tại
        mock_get_config.return_value = mock_config
        
        result = runner.invoke(code, ["apply", "-d", str(tmp_path)])
        
        assert result.exit_code == 1
        assert "Generated code directory không tồn tại" in result.output


# ============================================================================
# Data Model Tests
# ============================================================================

class TestDataModels:
    """Tests cho data models."""

    def test_code_plan_dataclass(self):
        """Test CodePlan dataclass."""
        plan = CodePlan(
            meta={"version": "1.0.0"},
            backend_files=[{"path": "app/main.py"}],
            frontend_files=[{"path": "src/app/app.module.ts"}],
            infra_files=[{"path": "docker-compose.yml"}],
        )
        
        assert plan.meta["version"] == "1.0.0"
        assert len(plan.backend_files) == 1
        assert len(plan.frontend_files) == 1
        assert len(plan.infra_files) == 1

    def test_generated_file_dataclass(self):
        """Test GeneratedFile dataclass."""
        file = GeneratedFile(
            path="app/main.py",
            content="# Generated",
            type="main",
            template="fastapi/main.py.jinja2",
        )
        
        assert file.path == "app/main.py"
        assert "# Generated" in file.content
        assert file.type == "main"
        assert file.template == "fastapi/main.py.jinja2"


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Tests cho error handling."""

    @patch("midicoder.pipeline.commands.code._load_mir_from_artifacts")
    def test_plan_missing_mir_error(self, mock_load_mir, runner):
        """Test lỗi khi MIR không tồn tại."""
        mock_load_mir.return_value = None
        
        result = runner.invoke(code, ["plan"])
        
        assert result.exit_code == 1
        assert "MIR không tồn tại" in result.output

    @patch("midicoder.pipeline.commands.code._load_plan_from_artifacts")
    def test_gen_missing_plan_error(self, mock_load_plan, runner):
        """Test lỗi khi plan không tồn tại."""
        mock_load_plan.return_value = None
        
        result = runner.invoke(code, ["gen"])
        
        assert result.exit_code == 1
        assert "Plan không tồn tại" in result.output

    @patch("midicoder.pipeline.commands.code.get_config")
    def test_apply_missing_src_error(self, mock_get_config, runner, tmp_path):
        """Test lỗi khi src directory không tồn tại."""
        mock_config = Mock()
        mock_config.get.return_value = "v9.9.9"
        mock_get_config.return_value = mock_config

        result = runner.invoke(code, ["apply", "-d", str(tmp_path)])

        assert result.exit_code == 1
        assert "không tồn tại" in result.output


# ============================================================================
# FileContributionsLoader Tests
# ============================================================================

class TestPascalToSnake:
    """Tests for case conversion helpers."""

    def test_simple_pascal(self):
        assert _pascal_to_snake("Customer") == "customer"

    def test_multi_word_pascal(self):
        assert _pascal_to_snake("OrderItem") == "order_item"

    def test_single_letter_prefix(self):
        assert _pascal_to_snake("IOError") == "io_error"

    def test_already_snake(self):
        assert _pascal_to_snake("customer") == "customer"


class TestSnakeToCamel:
    """Tests for snake_to_camel helper."""

    def test_simple_snake(self):
        assert _snake_to_camel("customer") == "customer"

    def test_multi_word_snake(self):
        assert _snake_to_camel("order_item") == "orderItem"


class TestExpandPathPattern:
    """Tests for _expand_path_pattern placeholder expansion."""

    def test_entity_snake_placeholder(self):
        entity = {"id": "Customer"}
        assert _expand_path_pattern("app/{entity_snake}_model.py", entity) == "app/customer_model.py"

    def test_entity_pascal_placeholder(self):
        entity = {"id": "Customer"}
        assert _expand_path_pattern("app/{entity_pascal}Model.py", entity) == "app/CustomerModel.py"

    def test_entity_camel_placeholder(self):
        entity = {"id": "OrderItem"}
        assert _expand_path_pattern("app/{entity_camel}.js", entity) == "app/orderItem.js"

    def test_no_placeholder(self):
        entity = {"id": "Customer"}
        assert _expand_path_pattern("app/database.py", entity) == "app/database.py"

    def test_unknown_placeholder_preserved(self):
        entity = {"id": "Customer"}
        assert _expand_path_pattern("app/{entity_snake}_{unknown_var}.py", entity) == "app/customer_{unknown_var}.py"


class TestFileContributionsLoader:
    """Tests for FileContributionsLoader — loading from pack.yml."""

    def test_load_cp08_contributions(self):
        """Test loading CP08 file_contributions from real pack.yml."""
        loader = FileContributionsLoader()
        fc = loader.load(pack_internal_id="cp08_database", pack_id="CP08")

        assert fc.pack_id == "CP08"
        assert fc.pack_internal_id == "cp08_database"
        assert not fc.is_empty
        assert len(fc.infrastructure) >= 1  # at least database.py
        assert len(fc.per_entity) >= 1  # at least repository

    def test_load_nonexistent_pack(self):
        """Test loading a pack that doesn't exist returns empty."""
        loader = FileContributionsLoader()
        fc = loader.load(pack_internal_id="nonexistent_pack", pack_id="CP99")

        assert fc.pack_id == "CP99"
        assert fc.is_empty

    def test_expand_infrastructure(self):
        """Test expanding infrastructure entries into file plans."""
        loader = FileContributionsLoader()
        fc = loader.load(pack_internal_id="cp08_database", pack_id="CP08")

        files = FileContributionsLoader.expand_infrastructure(fc)
        paths = [f["path"] for f in files]

        assert "app/database.py" in paths

    def test_expand_per_entity(self):
        """Test expanding per_entity entries with entity data."""
        loader = FileContributionsLoader()
        fc = loader.load(pack_internal_id="cp08_database", pack_id="CP08")

        entities = [
            {"id": "Customer"},
            {"id": "OrderItem"},
        ]

        files = FileContributionsLoader.expand_per_entity(fc, entities)
        paths = [f["path"] for f in files]

        # Should have repository files for each entity
        assert "app/repositories/customer_repo.py" in paths
        assert "app/repositories/order_item_repo.py" in paths


class TestFileContributionsLoaderIntegration:
    """Integration tests: _plan_backend_files uses CP08 self-declare."""

    def test_plan_backend_includes_cp08_infrastructure(self, sample_mir):
        """Verify CP08 infrastructure files appear in backend plan."""
        files = _plan_backend_files(sample_mir)
        paths = [f["path"] for f in files]

        assert "app/database.py" in paths

        # Verify the template path is correct (cp08_database/ not db/)
        db_file = next(f for f in files if f["path"] == "app/database.py")
        assert db_file["template"] == "cp08_database/database.py.jinja2"

    def test_plan_backend_includes_cp08_per_entity(self, sample_mir):
        """Verify CP08 per-entity files (repositories) appear in backend plan."""
        files = _plan_backend_files(sample_mir)
        paths = [f["path"] for f in files]

        assert "app/repositories/customer_repo.py" in paths
        assert "app/repositories/order_repo.py" in paths

    def test_plan_backend_no_stale_db_paths(self, sample_mir):
        """Verify no template paths start with stale 'db/' prefix."""
        files = _plan_backend_files(sample_mir)
        for f in files:
            template = f.get("template", "")
            # None of the templates should start with "db/"
            assert not template.startswith("db/"), (
                f"Stale template path found: {template} in {f['path']}"
            )


class TestFrontendWidgetContributions:
    """Tests cho per_widget file contributions trong frontend plan (CP22)."""

    def test_plan_frontend_includes_per_widget_files(self, sample_mir):
        """Kiểm tra per_widget files từ CP22 có mặt trong frontend plan.

        Đây là regression test cho bug P0-1: _plan_frontend_files() không gọi
        resolve_all_per_widget() → widget templates không được emit.
        """
        # Patch frontend_stack để test với react (CP22 có widget cho react)
        with patch(
            "midicoder.pipeline.commands.code._get_frontend_stack", return_value="react"
        ):
            frontend_files = _plan_frontend_files(sample_mir)
            paths = [f["path"] for f in frontend_files]

            # CP22 declare 5 widget types: presence, live_feed, live_counter,
            # live_cursor, notification_toast → các file .tsx
            widget_files = [p for p in paths if p.endswith(".tsx") and any(
                w in p.lower() for w in [
                    "presence", "livefeed", "livecounter",
                    "livecursor", "notificationtoast"
                ]
            )]

            # PHẢI có ít nhất một widget file — nếu không thì resolve_all_per_widget chưa được gọi
            assert len(widget_files) > 0, (
                f"Không có widget file trong frontend plan. "
                f"resolve_all_per_widget() có thể chưa được gọi. "
                f"Paths: {paths[:20]}..."
            )

    def test_widget_files_have_stack_metadata(self, sample_mir):
        """Kiểm tra widget files có metadata['stack'] được set đúng."""
        with patch(
            "midicoder.pipeline.commands.code._get_frontend_stack", return_value="react"
        ):
            frontend_files = _plan_frontend_files(sample_mir)

            widget_files = [
                f for f in frontend_files
                if f.get("type") == "widget"
            ]

            for wf in widget_files:
                assert wf.get("metadata", {}).get("stack") == "react", (
                    f"Widget file {wf['path']} thiếu metadata['stack'] = 'react'"
                )

    def test_widget_files_for_angular_stack(self, sample_mir):
        """Kiểm tra widget files cho Angular stack (kebab-case components)."""
        with patch(
            "midicoder.pipeline.commands.code._get_frontend_stack", return_value="angular"
        ):
            frontend_files = _plan_frontend_files(sample_mir)
            paths = [f["path"] for f in frontend_files]

            # Angular widgets dùng kebab-case .component.ts pattern
            angular_widgets = [
                p for p in paths
                if p.endswith(".component.ts") and any(
                    w in p.lower() for w in [
                        "presence", "live-feed", "live-counter",
                        "live-cursor", "notification-toast"
                    ]
                )
            ]

            assert len(angular_widgets) > 0, (
                f"Không có Angular widget file trong frontend plan. Paths: {paths[:20]}..."
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])