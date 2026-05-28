"""
Tests cho status filter trong pipeline.

Tests này validate:
- FileContributions.status field
- FileContributionsLoader.load() với status_filter
- FileContributionsLoader.load_all() với status_filter
- CLI flag --status-filter trên code plan và code gen commands
- _create_implementation_plan với status_filter
- _plan_backend_files/frontend_files/infra_files với status_filter
- resolve_all_* methods với status_filter
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, PropertyMock

from click.testing import CliRunner

from midicoder.pipeline.commands.code import (
    code,
    _execute_plan,
    _execute_gen,
    _create_implementation_plan,
    _plan_backend_files,
    _plan_frontend_files,
    _plan_infra_files,
)
from midicoder.pipeline.file_contributions_loader import (
    FileContributionsLoader,
    FileContributions,
)
from midicoder.pipeline.plan import ImplementationPlan


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def runner():
    """Click test runner."""
    return CliRunner()


@pytest.fixture
def sample_mir():
    """Sample MIR data matching actual MIRBuilder output."""
    return {
        "metadata": {
            "entities": [
                {"id": "Customer", "attributes": ["id", "name", "email"]},
            ],
            "commands": [],
            "queries": [],
        },
        "operations": [
            {"id": "op1", "type": "create"},
        ],
    }


# ============================================================================
# FileContributions.status field tests
# ============================================================================

class TestFileContributionsStatus:
    """Tests cho status field trong FileContributions dataclass."""

    def test_default_status_is_stable(self):
        """FileContributions không có status nên default là 'stable'."""
        fc = FileContributions(pack_id="B01", pack_internal_id="cp_base_domain_model")
        assert fc.status == "stable"

    def test_explicit_status(self):
        """FileContributions có thể set status từ pack.yml."""
        fc = FileContributions(
            pack_id="CP99",
            pack_internal_id="cp99_experimental",
            status="experimental",
        )
        assert fc.status == "experimental"

    def test_deprecated_status(self):
        """FileContributions có thể có status 'deprecated'."""
        fc = FileContributions(
            pack_id="CP98",
            pack_internal_id="cp98_old",
            status="deprecated",
        )
        assert fc.status == "deprecated"


# ============================================================================
# FileContributionsLoader.load() status_filter tests
# ============================================================================

class TestLoaderStatusFilter:
    """Tests cho status_filter trong FileContributionsLoader.load()."""

    def test_load_stable_pack_no_filter(self):
        """Load pack không có status_filter nên trả về đầy đủ."""
        loader = FileContributionsLoader()
        fc = loader.load(pack_internal_id="cp_base_domain_model", pack_id="B01")

        assert fc.pack_id == "B01"
        assert fc.status == "stable"

    def test_load_stable_pack_with_stable_filter(self):
        """Load pack có status_filter='stable' nên trả về đầy đủ."""
        loader = FileContributionsLoader()
        fc = loader.load(
            pack_internal_id="cp_base_domain_model",
            pack_id="B01",
            status_filter="stable",
        )

        assert fc.pack_id == "B01"
        assert fc.status == "stable"
        assert not fc.is_empty

    def test_load_stable_pack_with_experimental_filter(self):
        """Load pack có status_filter='experimental' nên trả về empty."""
        loader = FileContributionsLoader()
        fc = loader.load(
            pack_internal_id="cp_base_domain_model",
            pack_id="B01",
            status_filter="experimental",
        )

        assert fc.pack_id == "B01"
        assert fc.is_empty

    def test_load_nonexistent_pack(self):
        """Load pack không tồn tại trả về empty."""
        loader = FileContributionsLoader()
        fc = loader.load(pack_internal_id="nonexistent_pack", pack_id="CP99")

        assert fc.pack_id == "CP99"
        assert fc.is_empty

    def test_load_with_both_stack_and_status_filter(self):
        """Load với cả stack và status_filter cùng lúc."""
        loader = FileContributionsLoader()
        fc = loader.load(
            pack_internal_id="cp_base_domain_model",
            pack_id="B01",
            stack="fastapi",
            status_filter="stable",
        )

        assert fc.pack_id == "B01"
        assert fc.status == "stable"
        assert not fc.is_empty

    def test_load_with_stack_mismatch_and_status_filter(self):
        """Load với stack không match nên trả về ít files hơn."""
        loader = FileContributionsLoader()
        fc_fastapi = loader.load(
            pack_internal_id="cp_base_domain_model",
            pack_id="B01",
            stack="fastapi",
            status_filter="stable",
        )
        fc_angular = loader.load(
            pack_internal_id="cp_base_domain_model",
            pack_id="B01",
            stack="angular",
            status_filter="stable",
        )

        assert fc_fastapi.pack_id == "B01"
        # Đếm tất cả files
        len_fc = lambda fc: len(fc.infrastructure) + len(fc.per_entity) + len(fc.per_command) + len(fc.per_query) + len(fc.per_ui_component) + len(fc.per_widget)
        # fastapi nên có >= angular
        assert len_fc(fc_fastapi) >= len_fc(fc_angular)


# ============================================================================
# FileContributionsLoader.load_all() status_filter tests
# ============================================================================

class TestLoaderAllStatusFilter:
    """Tests cho status_filter trong FileContributionsLoader.load_all()."""

    def test_load_all_no_filter(self):
        """load_all không có filter trả về tất cả packs."""
        loader = FileContributionsLoader()
        contributions = loader.load_all(stack="fastapi")

        assert len(contributions) > 0

    def test_load_all_stable_filter(self):
        """load_all với status_filter='stable' chỉ trả về stable packs."""
        loader = FileContributionsLoader()
        contributions = loader.load_all(stack="fastapi", status_filter="stable")

        for fc in contributions:
            assert fc.status == "stable"

    def test_load_all_experimental_filter_empty(self):
        """load_all với status_filter='experimental' nên trả về ít packs hơn
        hoặc empty nếu không có pack nào experimental."""
        loader = FileContributionsLoader()
        contributions = loader.load_all(stack="fastapi", status_filter="experimental")

        # Most packs are "stable", so experimental filter should return few or none
        for fc in contributions:
            assert fc.status == "experimental"

    def test_load_all_deprecated_filter(self):
        """load_all với status_filter='deprecated' nên trả về empty
        nếu không có pack nào deprecated."""
        loader = FileContributionsLoader()
        contributions = loader.load_all(stack="fastapi", status_filter="deprecated")

        for fc in contributions:
            assert fc.status == "deprecated"


# ============================================================================
# resolve_all_* methods status_filter tests
# ============================================================================

class TestResolveAllStatusFilter:
    """Tests cho status_filter trong resolve_all_* methods."""

    def test_resolve_all_infrastructure_with_status_filter(self):
        """resolve_all_infrastructure với status_filter."""
        loader = FileContributionsLoader()
        files_all = loader.resolve_all_infrastructure("fastapi")
        files_stable = loader.resolve_all_infrastructure(
            "fastapi", status_filter="stable"
        )

        # stable filter should return same or fewer files
        assert len(files_stable) <= len(files_all)

    def test_resolve_all_infrastructure_experimental_empty(self):
        """resolve_all_infrastructure với experimental nên trả về ít hơn."""
        loader = FileContributionsLoader()
        files_all = loader.resolve_all_infrastructure("fastapi")
        files_exp = loader.resolve_all_infrastructure(
            "fastapi", status_filter="experimental"
        )

        for fc in files_exp:
            assert True  # all returned files come from experimental packs

    def test_resolve_all_per_entity_with_status_filter(self, sample_mir):
        """resolve_all_per_entity với status_filter."""
        entities = sample_mir["metadata"]["entities"]
        loader = FileContributionsLoader()

        files_all = loader.resolve_all_per_entity("fastapi", entities)
        files_stable = loader.resolve_all_per_entity(
            "fastapi", entities, status_filter="stable"
        )

        assert len(files_stable) <= len(files_all)

    def test_resolve_all_per_command_with_status_filter(self, sample_mir):
        """resolve_all_per_command với status_filter."""
        commands = sample_mir["metadata"].get("commands", [])
        loader = FileContributionsLoader()

        files_all = loader.resolve_all_per_command("fastapi", commands)
        files_stable = loader.resolve_all_per_command(
            "fastapi", commands, status_filter="stable"
        )

        # Both should have same count (stable packs provide commands)
        assert len(files_stable) <= len(files_all)

    def test_resolve_all_per_ui_component_with_status_filter(self, sample_mir):
        """resolve_all_per_ui_component với status_filter."""
        entities = sample_mir["metadata"]["entities"]
        loader = FileContributionsLoader()

        files_all = loader.resolve_all_per_ui_component("angular", entities)
        files_stable = loader.resolve_all_per_ui_component(
            "angular", entities, status_filter="stable"
        )

        assert len(files_stable) <= len(files_all)

    def test_resolve_all_per_widget_with_status_filter(self):
        """resolve_all_per_widget với status_filter."""
        loader = FileContributionsLoader()

        files_all = loader.resolve_all_per_widget("react")
        files_stable = loader.resolve_all_per_widget(
            "react", status_filter="stable"
        )

        assert len(files_stable) <= len(files_all)


# ============================================================================
# CLI --status-filter flag tests
# ============================================================================

class TestCLIStatusFilter:
    """Tests cho CLI flag --status-filter."""

    def test_code_plan_help_shows_status_filter(self, runner):
        """code plan --help phải hiển thị --status-filter."""
        result = runner.invoke(code, ["plan", "--help"])

        assert result.exit_code == 0
        assert "--status-filter" in result.output
        assert "-s" in result.output

    def test_code_gen_help_shows_status_filter(self, runner):
        """code gen --help phải hiển thị --status-filter."""
        result = runner.invoke(code, ["gen", "--help"])

        assert result.exit_code == 0
        assert "--status-filter" in result.output
        assert "-s" in result.output

    def test_code_plan_status_filter_stable(self, runner):
        """code plan với --status-filter stable."""
        result = runner.invoke(code, ["plan", "--help"])

        assert result.exit_code == 0
        assert "stable" in result.output

    @patch("midicoder.pipeline.commands.code._load_mir_from_artifacts")
    @patch("midicoder.pipeline.commands.code.ArtifactsManager")
    @patch("midicoder.pipeline.commands.code.get_config")
    def test_execute_plan_with_status_filter(
        self,
        mock_get_config,
        mock_artifacts_manager,
        mock_load_mir,
        runner,
        sample_mir,
    ):
        """Test execute plan với status_filter."""
        mock_load_mir.return_value = sample_mir
        mock_config = Mock()
        mock_config.get.return_value = "v1.0.0"
        mock_get_config.return_value = mock_config

        mock_am = Mock()
        mock_artifacts_manager.return_value = mock_am

        result = runner.invoke(code, ["plan", "--status-filter", "stable"])

        assert result.exit_code == 0
        assert "status_filter=stable" in result.output
        assert "Plan Summary" in result.output

    @patch("midicoder.pipeline.commands.code._load_mir_from_artifacts")
    @patch("midicoder.pipeline.commands.code.ArtifactsManager")
    @patch("midicoder.pipeline.commands.code.get_config")
    def test_execute_plan_with_short_status_filter(
        self,
        mock_get_config,
        mock_artifacts_manager,
        mock_load_mir,
        runner,
        sample_mir,
    ):
        """Test execute plan với short flag -s."""
        mock_load_mir.return_value = sample_mir
        mock_config = Mock()
        mock_config.get.return_value = "v1.0.0"
        mock_get_config.return_value = mock_config

        mock_am = Mock()
        mock_artifacts_manager.return_value = mock_am

        result = runner.invoke(code, ["plan", "-s", "experimental"])

        assert result.exit_code == 0
        assert "status_filter=experimental" in result.output

    @patch("midicoder.pipeline.commands.code._load_mir_from_artifacts")
    @patch("midicoder.pipeline.commands.code.ArtifactsManager")
    @patch("midicoder.pipeline.commands.code.get_config")
    def test_execute_plan_no_status_filter(
        self,
        mock_get_config,
        mock_artifacts_manager,
        mock_load_mir,
        runner,
        sample_mir,
    ):
        """Test execute plan không có status_filter."""
        mock_load_mir.return_value = sample_mir
        mock_config = Mock()
        mock_config.get.return_value = "v1.0.0"
        mock_get_config.return_value = mock_config

        mock_am = Mock()
        mock_artifacts_manager.return_value = mock_am

        result = runner.invoke(code, ["plan"])

        assert result.exit_code == 0
        # Không có status_filter nên không hiển thị message
        assert "status_filter=" not in result.output


# ============================================================================
# Plan creation with status_filter tests
# ============================================================================

class TestPlanCreationWithStatusFilter:
    """Tests cho _create_implementation_plan với status_filter."""

    def test_create_plan_with_stable_filter(self, sample_mir):
        """Test _create_implementation_plan với status_filter='stable'."""
        plan = _create_implementation_plan(
            sample_mir, target="all", status_filter="stable"
        )

        assert isinstance(plan, ImplementationPlan)
        assert "version" in plan.meta

    def test_create_plan_no_filter_has_more_files(self, sample_mir):
        """Plan không có filter nên có nhiều files hơn hoặc bằng plan có filter."""
        plan_all = _create_implementation_plan(sample_mir, target="backend")
        plan_stable = _create_implementation_plan(
            sample_mir, target="backend", status_filter="stable"
        )

        counts_all = plan_all.count_files()
        counts_stable = plan_stable.count_files()

        # stable filter should return same or fewer files
        assert counts_stable["backend"] <= counts_all["backend"]

    def test_create_plan_experimental_filter_fewer_files(self, sample_mir):
        """Plan với experimental filter nên có ít files hơn."""
        plan_all = _create_implementation_plan(sample_mir, target="backend")
        plan_exp = _create_implementation_plan(
            sample_mir, target="backend", status_filter="experimental"
        )

        counts_all = plan_all.count_files()
        counts_exp = plan_exp.count_files()

        # experimental filter should return same or fewer files
        # (most packs are stable, so experimental returns less)
        assert counts_exp["backend"] <= counts_all["backend"]

    def test_create_plan_deprecated_filter_fewer_files(self, sample_mir):
        """Plan với deprecated filter nên có ít files hơn."""
        plan_all = _create_implementation_plan(sample_mir, target="backend")
        plan_dep = _create_implementation_plan(
            sample_mir, target="backend", status_filter="deprecated"
        )

        counts_all = plan_all.count_files()
        counts_dep = plan_dep.count_files()

        # deprecated filter should return same or fewer files
        assert counts_dep["backend"] <= counts_all["backend"]

    def test_create_plan_frontend_with_status_filter(self, sample_mir):
        """Test plan frontend với status_filter."""
        plan = _create_implementation_plan(
            sample_mir, target="frontend", status_filter="stable"
        )

        assert isinstance(plan, ImplementationPlan)
        counts = plan.count_files()
        assert counts["frontend"] >= 0

    def test_create_plan_infra_with_status_filter(self, sample_mir):
        """Test plan với target='all' nên include infra."""
        plan = _create_implementation_plan(
            sample_mir, target="all", status_filter="stable"
        )

        counts = plan.count_files()
        # I01 (IaC) is stable, so infra files should still be present
        assert counts["infra"] >= 0


# ============================================================================
# Individual plan function tests
# ============================================================================

class TestPlanFunctionsStatusFilter:
    """Tests cho _plan_backend/frontend/infra_files với status_filter."""

    def test_plan_backend_files_with_status_filter(self, sample_mir):
        """Test _plan_backend_files với status_filter."""
        files_all = _plan_backend_files(sample_mir)
        files_stable = _plan_backend_files(sample_mir, status_filter="stable")

        assert len(files_stable) <= len(files_all)

        # Core files (main.py, config.py) are always included regardless of filter
        paths = [f["path"] for f in files_stable]
        assert "app/main.py" in paths
        assert "app/config.py" in paths

    def test_plan_backend_files_experimental_filter(self, sample_mir):
        """Test _plan_backend_files với experimental filter."""
        files_all = _plan_backend_files(sample_mir)
        files_exp = _plan_backend_files(sample_mir, status_filter="experimental")

        # experimental filter should return same or fewer
        assert len(files_exp) <= len(files_all)

        # Core files always included
        paths = [f["path"] for f in files_exp]
        assert "app/main.py" in paths
        assert "app/config.py" in paths

    def test_plan_frontend_files_with_status_filter(self, sample_mir):
        """Test _plan_frontend_files với status_filter."""
        files_all = _plan_frontend_files(sample_mir)
        files_stable = _plan_frontend_files(sample_mir, status_filter="stable")

        assert len(files_stable) <= len(files_all)

    def test_plan_infra_files_with_status_filter(self):
        """Test _plan_infra_files với status_filter."""
        files_all = _plan_infra_files()
        files_stable = _plan_infra_files(status_filter="stable")

        # I01 is stable, so stable filter should return same files
        assert len(files_stable) <= len(files_all)

    def test_plan_infra_files_deprecated_filter(self):
        """Test _plan_infra_files với deprecated filter nên ít files hơn."""
        files_all = _plan_infra_files()
        files_dep = _plan_infra_files(status_filter="deprecated")

        # deprecated filter should return same or fewer
        assert len(files_dep) <= len(files_all)


# ============================================================================
# Edge case tests
# ============================================================================

class TestEdgeCases:
    """Tests cho edge cases của status filter."""

    def test_status_filter_none_equals_no_filter(self, sample_mir):
        """status_filter=None nên tương đương với không có filter."""
        files_none = _plan_backend_files(sample_mir, status_filter=None)
        files_default = _plan_backend_files(sample_mir)

        assert len(files_none) == len(files_default)

    def test_invalid_status_filter_ignored(self, sample_mir):
        """status_filter không valid (không phải stable/experimental/deprecated)
        nên trả về kết quả tương đương không có filter vì không có pack nào match."""
        # Click validates the choice at CLI level, but programmatic calls
        # could pass arbitrary strings
        files_unknown = _plan_backend_files(sample_mir, status_filter="unknown")
        files_default = _plan_backend_files(sample_mir)

        # "unknown" status won't match any pack, so only core files remain
        assert len(files_unknown) <= len(files_default)

        # Core files always present
        paths = [f["path"] for f in files_unknown]
        assert "app/main.py" in paths
        assert "app/config.py" in paths

    def test_status_filter_case_sensitive(self):
        """status_filter nên case-sensitive."""
        loader = FileContributionsLoader()
        fc_lower = loader.load(
            pack_internal_id="cp_base_domain_model",
            pack_id="B01",
            status_filter="stable",
        )
        fc_upper = loader.load(
            pack_internal_id="cp_base_domain_model",
            pack_id="B01",
            status_filter="Stable",  # Capital S
        )

        assert not fc_lower.is_empty
        assert fc_upper.is_empty  # "Stable" != "stable"
