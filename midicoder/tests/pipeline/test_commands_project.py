"""
Tests cho Project Management Commands.

Test coverage:
- init_workspace: tạo workspace structure + SQLite + YAML
- project_create: tạo project mới + register SQLite
- project_list: list projects
- project_activate: activate project + ConfigManager sync
- project_delete: xóa project khỏi registry
- get_techstacks, get_prompt_domains
"""

import hashlib
import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from midicoder.pipeline.commands.project import (
    init_workspace,
    project_create,
    project_list,
    project_get_active,
    project_activate,
    project_delete,
    get_techstacks,
    get_prompt_domains,
    _ensure_manager,
)
from midicoder.storage.projects import ProjectsManager


@pytest.fixture
def temp_project_dir():
    """Tạo temporary directory cho project."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def temp_projects_db():
    """ProjectsManager với DB tạm — yield (tmp_path, mgr)."""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    mgr = ProjectsManager(db_path=Path(tmp.name))
    mgr.init()
    yield Path(tmp.name), mgr
    # Cleanup
    try:
        os.unlink(tmp.name)
    except OSError:
        pass


# ============================================================================
# init_workspace
# ============================================================================

class TestInitWorkspace:
    """Test khởi tạo workspace structure."""

    def test_creates_directory_structure(self, temp_project_dir):
        """Kiểm tra tạo đúng thư mục con."""
        tech_stack = {
            "infrastructure": "infrastructure",
            "backend": "fastapi",
            "frontend": "angular",
            "ui_framework": "carbon",
        }
        result = init_workspace(temp_project_dir, tech_stack, "default")

        workspace = Path(temp_project_dir) / ".midicoder"
        assert (workspace / "config").is_dir()
        assert (workspace / "data").is_dir()
        assert (workspace / "versions").is_dir()
        assert (workspace / "runtime").is_dir()
        assert (workspace / "cache").is_dir()

    def test_creates_sqlite_databases(self, temp_project_dir):
        """Kiểm tra tạo đúng files SQLite."""
        tech_stack = {"infrastructure": "infrastructure", "backend": "fastapi", "frontend": "angular", "ui_framework": "carbon"}
        init_workspace(temp_project_dir, tech_stack, "default")

        data_dir = Path(temp_project_dir) / ".midicoder" / "data"
        assert (data_dir / "briefs.db").is_file()
        assert (data_dir / "artifacts.db").is_file()
        assert (data_dir / "provenance.db").is_file()
        assert (data_dir / "context.db").is_file()

    def test_creates_config_yaml(self, temp_project_dir):
        """Kiểm tra tạo file config YAML đúng."""
        tech_stack = {
            "infrastructure": "infrastructure",
            "backend": "fastapi",
            "frontend": "angular",
            "ui_framework": "carbon",
        }
        init_workspace(temp_project_dir, tech_stack, "ecommerce", max_versions=3)

        config_file = Path(temp_project_dir) / ".midicoder" / "config" / "midicoder.yml"
        assert config_file.is_file()

        data = yaml.safe_load(config_file.read_text())
        assert data["midicoder_version"] == "1.0.0"
        assert data["max_versions"] == 3
        assert data["tech_stack"]["backend"] == "fastapi"
        assert data["prompt_domain"] == "ecommerce"
        assert data["capabilities"]["enabled"] == []

    def test_returns_project_id(self, temp_project_dir):
        """Kiểm tra project_id được tính đúng từ path."""
        tech_stack = {"infrastructure": "infrastructure", "backend": "fastapi", "frontend": "angular", "ui_framework": "carbon"}
        result = init_workspace(temp_project_dir, tech_stack, "default")

        expected_id = hashlib.md5(str(Path(temp_project_dir).resolve()).encode()).hexdigest()[:12]
        assert result["project_id"] == expected_id
        assert result["workspace_dir"]
        assert result["config_file"]


# ============================================================================
# project_create
# ============================================================================

class TestProjectCreate:
    """Test tạo project mới + register SQLite."""

    def test_creates_new_project(self, temp_project_dir, temp_projects_db):
        """Tạo project mới hoàn toàn."""
        tmp_path, mgr = temp_projects_db
        with patch("midicoder.pipeline.commands.project._ensure_manager", return_value=mgr):
            with patch("midicoder.pipeline.commands.project._set_config_project_path"):
                result = project_create(
                    name="test-project",
                    path=temp_project_dir,
                    tech_stack={
                        "infrastructure": "infrastructure",
                        "backend": "fastapi",
                        "frontend": "angular",
                        "ui_framework": "carbon",
                    },
                    prompt_domain="default",
                )

        assert result["created"] is True
        assert result["project"]["name"] == "test-project"
        assert result["project"]["active"] == 1

    def test_existing_project_activates(self, temp_project_dir, temp_projects_db):
        """Project đã tồn tại theo path → activate thay vì tạo mới."""
        tmp_path, mgr = temp_projects_db
        project_id = hashlib.md5(str(Path(temp_project_dir).resolve()).encode()).hexdigest()[:12]

        # Pre-register project vào DB
        mgr.create(
            project_id=project_id,
            name="existing-project",
            path=str(Path(temp_project_dir).resolve()),
            set_active=True,
        )

        with patch("midicoder.pipeline.commands.project._ensure_manager", return_value=mgr):
            with patch("midicoder.pipeline.commands.project._set_config_project_path"):
                result = project_create(
                    name="test-project",
                    path=temp_project_dir,
                    tech_stack={"infrastructure": "infrastructure", "backend": "fastapi", "frontend": "angular", "ui_framework": "carbon"},
                    prompt_domain="default",
                )

        assert result["created"] is False
        assert result["already_exists"] is True
        assert result["project"]["name"] == "existing-project"

    def test_workspace_already_exists_not_midicoder(self, temp_project_dir, temp_projects_db):
        """Folder .midicoder tồn tại nhưng không phải Midicoder project → raise error."""
        tmp_path, mgr = temp_projects_db
        workspace = Path(temp_project_dir) / ".midicoder"
        workspace.mkdir(parents=True)

        with patch("midicoder.pipeline.commands.project._ensure_manager", return_value=mgr):
            with patch("midicoder.pipeline.commands.project._set_config_project_path"):
                with pytest.raises(Exception):
                    project_create(
                        name="test-project",
                        path=temp_project_dir,
                        tech_stack={"infrastructure": "infrastructure", "backend": "fastapi", "frontend": "angular", "ui_framework": "carbon"},
                        prompt_domain="default",
                    )


# ============================================================================
# project_list
# ============================================================================

class TestProjectList:
    """Test list projects."""

    def test_list_empty(self, temp_projects_db):
        """List trả về rỗng khi không có project."""
        tmp_path, mgr = temp_projects_db
        with patch("midicoder.pipeline.commands.project._ensure_manager", return_value=mgr):
            result = project_list()
        assert result["projects"] == []
        assert result["active"] is None

    def test_list_with_projects(self, temp_projects_db):
        """List trả về đúng số projects."""
        tmp_path, mgr = temp_projects_db
        mgr.create("pid1", "Project 1", "/path/to/1", set_active=True)
        mgr.create("pid2", "Project 2", "/path/to/2", set_active=False)

        with patch("midicoder.pipeline.commands.project._ensure_manager", return_value=mgr):
            result = project_list()
        assert len(result["projects"]) == 2
        assert result["active"]["name"] == "Project 1"


# ============================================================================
# project_activate
# ============================================================================

class TestProjectActivate:
    """Test activate project."""

    def test_activate_project(self, temp_projects_db):
        """Activate project và update ConfigManager."""
        tmp_path, mgr = temp_projects_db
        mgr.create("pid1", "P1", "/p1", set_active=True)
        mgr.create("pid2", "P2", "/p2", set_active=False)

        with patch("midicoder.pipeline.commands.project._ensure_manager", return_value=mgr):
            with patch("midicoder.pipeline.commands.project._set_config_project_path") as mock_set:
                result = project_activate("pid2")

        assert result["project"]["name"] == "P2"
        mock_set.assert_called_once_with("/p2")

    def test_activate_nonexistent(self, temp_projects_db):
        """Activate project không tồn tại → raise error."""
        tmp_path, mgr = temp_projects_db
        with patch("midicoder.pipeline.commands.project._ensure_manager", return_value=mgr):
            with pytest.raises(Exception):
                project_activate("nonexistent-id")


# ============================================================================
# project_delete
# ============================================================================

class TestProjectDelete:
    """Test xóa project."""

    def test_delete_inactive_project(self, temp_projects_db):
        """Xóa project không active."""
        tmp_path, mgr = temp_projects_db
        mgr.create("pid1", "P1", "/p1", set_active=True)
        mgr.create("pid2", "P2", "/p2", set_active=False)

        with patch("midicoder.pipeline.commands.project._ensure_manager", return_value=mgr):
            result = project_delete("pid2")
        assert result["name"] == "P2"
        assert mgr.get("pid2") is None

    def test_cannot_delete_active_when_multiple(self, temp_projects_db):
        """Không xóa project active khi còn nhiều projects."""
        tmp_path, mgr = temp_projects_db
        mgr.create("pid1", "P1", "/p1", set_active=True)
        mgr.create("pid2", "P2", "/p2", set_active=False)

        with patch("midicoder.pipeline.commands.project._ensure_manager", return_value=mgr):
            with pytest.raises(Exception):
                project_delete("pid1")

    def test_can_delete_active_when_only_one(self, temp_projects_db):
        """Cho phép xóa project active khi là project duy nhất."""
        tmp_path, mgr = temp_projects_db
        mgr.create("pid1", "P1", "/p1", set_active=True)

        with patch("midicoder.pipeline.commands.project._ensure_manager", return_value=mgr):
            result = project_delete("pid1")
        assert result["name"] == "P1"
        assert mgr.get("pid1") is None


# ============================================================================
# get_techstacks / get_prompt_domains
# ============================================================================

class TestTechstackMetadata:
    """Test metadata helper functions."""

    def test_get_techstacks_returns_categories(self):
        """Trả về đúng categories."""
        stacks = get_techstacks()
        assert "infrastructure" in stacks
        assert "backend" in stacks
        assert "frontend" in stacks
        assert "ui_framework" in stacks
        # Mỗi category có ít nhất 1 item
        for cat in stacks.values():
            assert len(cat) > 0

    def test_get_prompt_domains_has_default(self):
        """Luôn có domain 'default'."""
        domains = get_prompt_domains()
        assert any(d["value"] == "default" for d in domains)
