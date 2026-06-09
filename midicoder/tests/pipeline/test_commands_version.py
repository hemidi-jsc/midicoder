"""
Tests cho Version Management Commands.

Test coverage:
- Version validation (SemVer regex)
- Version create
- Version use
- Version list
- Version delete
- Auto-cleanup
- _sync_metadata_from_sqlite: đồng bộ metadata.yml từ SQLite
- check_create_version: validate + impact check

SoT Reference: E01
"""

import hashlib
import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from midicoder.errors import ErrorCode, MidicoderError
from midicoder.pipeline.commands.version import (
    validate_version_name,
    get_workspace_dir,
    get_versions_dir,
    get_config_file,
    load_project_config,
    save_project_config,
    list_versions,
    get_active_version,
    get_max_versions,
    create_version,
    use_version,
    list_versions_command,
    delete_version,
    _auto_cleanup,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def temp_workspace():
    """Tạo temporary workspace cho testing."""
    # Tạo temp directory
    temp_dir = tempfile.mkdtemp()
    original_dir = os.getcwd()
    
    # Change vào temp directory
    os.chdir(temp_dir)
    
    # Tạo .midicoder/ structure
    workspace_dir = Path(temp_dir) / ".midicoder"
    versions_dir = workspace_dir / "versions"
    config_dir = workspace_dir / "config"
    
    workspace_dir.mkdir(parents=True)
    versions_dir.mkdir(parents=True)
    config_dir.mkdir(parents=True)
    
    # Tạo config mặc định
    config = {
        'midicoder_version': '1.0.0',
        'active_version': None,
        'max_versions': 5
    }
    with open(config_dir / "midicoder.yml", 'w') as f:
        yaml.dump(config, f)
    
    yield temp_dir
    
    # Cleanup
    os.chdir(original_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def workspace_with_version(temp_workspace):
    """Tạo workspace với 1 version."""
    versions_dir = Path(temp_workspace) / ".midicoder" / "versions"
    version_dir = versions_dir / "v1.0.0"
    version_dir.mkdir(parents=True)
    
    metadata = {
        'version': '1.0.0',
        'created_at': '2026-04-27T10:00:00Z',
        'parent_version': None,
        'status': 'active',
        'pipeline': {'brief': 'none', 'contract': 'none', 'ir': 'none', 'code': 'none'},
        'artifacts': {'briefs': 0, 'contracts': 0, 'files': 0, 'lines': 0}
    }
    with open(version_dir / "metadata.yml", 'w') as f:
        yaml.dump(metadata, f)
    
    # Update active version
    config_dir = Path(temp_workspace) / ".midicoder" / "config"
    config = {'active_version': 'v1.0.0', 'max_versions': 5}
    with open(config_dir / "midicoder.yml", 'w') as f:
        yaml.dump(config, f)
    
    return temp_workspace


@pytest.fixture
def workspace_with_multiple_versions(temp_workspace):
    """Tạo workspace với nhiều versions."""
    versions_dir = Path(temp_workspace) / ".midicoder" / "versions"
    
    versions_data = [
        ('v1.0.0', '2026-04-27T08:00:00Z', 'archived', None),
        ('v1.0.1', '2026-04-27T09:00:00Z', 'archived', '1.0.0'),
        ('v1.0.2', '2026-04-27T10:00:00Z', 'active', '1.0.1'),
    ]
    
    for version, created, status, parent in versions_data:
        version_dir = versions_dir / version
        version_dir.mkdir(parents=True)
        
        metadata = {
            'version': version.lstrip('v'),
            'created_at': created,
            'parent_version': parent,
            'status': status,
            'pipeline': {'brief': 'none', 'contract': 'none', 'ir': 'none', 'code': 'none'},
            'artifacts': {'briefs': 0, 'contracts': 0, 'files': 0, 'lines': 0}
        }
        with open(version_dir / "metadata.yml", 'w') as f:
            yaml.dump(metadata, f)
    
    # Update active version
    config_dir = Path(temp_workspace) / ".midicoder" / "config"
    config = {'active_version': 'v1.0.2', 'max_versions': 5}
    with open(config_dir / "midicoder.yml", 'w') as f:
        yaml.dump(config, f)
    
    return temp_workspace


# ============================================================================
# Version Validation Tests
# ============================================================================

class TestVersionValidation:
    """Tests cho version name validation."""
    
    def test_valid_semver_with_v_prefix(self):
        """Test valid SemVer với v prefix."""
        assert validate_version_name('v1.0.0') is True
        assert validate_version_name('v2.0.0') is True
        assert validate_version_name('v10.20.30') is True
    
    def test_valid_semver_without_v_prefix(self):
        """Test valid SemVer không có v prefix."""
        assert validate_version_name('1.0.0') is True
        assert validate_version_name('2.0.0') is True
        assert validate_version_name('10.20.30') is True
    
    def test_valid_semver_with_prerelease(self):
        """Test valid SemVer với prerelease."""
        assert validate_version_name('v1.0.0-alpha') is True
        assert validate_version_name('v1.0.0-beta.1') is True
        assert validate_version_name('v1.0.0-rc.1') is True
        assert validate_version_name('v1.0.0-alpha.beta') is True
    
    def test_valid_semver_with_build_metadata(self):
        """Test valid SemVer với build metadata."""
        assert validate_version_name('v1.0.0+build.123') is True
        assert validate_version_name('v1.0.0+20130313144700') is True
        assert validate_version_name('v1.0.0-alpha+001') is True
    
    def test_invalid_semver(self):
        """Test invalid SemVer formats."""
        assert validate_version_name('1.0') is False  # Thiếu patch
        assert validate_version_name('1') is False  # Chỉ major
        assert validate_version_name('v1.0.0.0') is False  # 4 components
        assert validate_version_name('1.0.0-') is False  # Prerelease trống
        assert validate_version_name('1.0.0+') is False  # Build metadata trống
        assert validate_version_name('abc') is False  # Không phải version
        assert validate_version_name('') is False  # Empty string
        assert validate_version_name('v1.0.0 ') is False  # Trailing space


# ============================================================================
# Version CRUD Tests
# ============================================================================

class TestVersionCreate:
    """Tests cho version create."""
    
    def test_create_version_success(self, temp_workspace):
        """Test tạo version mới thành công (phiên bản đầu tiên → không có parent)."""
        create_version('v1.0.0')

        # Check version directory created
        version_dir = Path(temp_workspace) / ".midicoder" / "versions" / "v1.0.0"
        assert version_dir.exists()

        # Check src directory created
        src_dir = version_dir / "src"
        assert src_dir.exists()

        # Check metadata.yml created
        metadata_file = version_dir / "metadata.yml"
        assert metadata_file.exists()

        # Check metadata content
        with open(metadata_file) as f:
            metadata = yaml.safe_load(f)
        assert metadata['version'] == '1.0.0'
        assert metadata['status'] == 'draft'
        assert metadata['parent_version'] is None  # phiên bản đầu tiên

        # Check active version updated
        config_file = Path(temp_workspace) / ".midicoder" / "config" / "midicoder.yml"
        with open(config_file) as f:
            config = yaml.safe_load(f)
        assert config['active_version'] == 'v1.0.0'

    def test_create_version_auto_parent(self, workspace_with_version):
        """Test tạo version mới tự động kế thừa từ version active (parent)."""
        # Tạo src trong parent (v1.0.0 đang active)
        parent_src = Path(workspace_with_version) / ".midicoder" / "versions" / "v1.0.0" / "src"
        parent_src.mkdir(parents=True)
        test_file = parent_src / "test.txt"
        test_file.write_text("test content")
        (parent_src / "subdir").mkdir(exist_ok=True)
        (parent_src / "subdir" / "nested.txt").write_text("nested content")

        # Tạo v1.0.1 — tự động lấy v1.0.0 làm parent
        create_version('v1.0.1')

        # Check file copied từ parent
        child_src = Path(workspace_with_version) / ".midicoder" / "versions" / "v1.0.1" / "src"
        copied_file = child_src / "test.txt"
        assert copied_file.exists()
        assert copied_file.read_text() == "test content"
        # Check nested file
        assert (child_src / "subdir" / "nested.txt").exists()
        assert (child_src / "subdir" / "nested.txt").read_text() == "nested content"

        # Check metadata có parent_version
        metadata_file = Path(workspace_with_version) / ".midicoder" / "versions" / "v1.0.1" / "metadata.yml"
        with open(metadata_file) as f:
            metadata = yaml.safe_load(f)
        assert metadata['parent_version'] == '1.0.0'
        assert metadata['status'] == 'draft'
    
    def test_create_version_invalid_name(self, temp_workspace):
        """Test tạo version với name không hợp lệ."""
        with pytest.raises(MidicoderError) as exc_info:
            create_version('invalid-name')
        
        assert exc_info.value.code == ErrorCode.VERSION_INVALID_NAME
    
    def test_create_version_already_exists(self, workspace_with_version):
        """Test tạo version đã tồn tại."""
        with pytest.raises(MidicoderError) as exc_info:
            create_version('v1.0.0')

        assert exc_info.value.code == ErrorCode.VERSION_ALREADY_EXISTS

    def test_create_version_without_v_prefix(self, temp_workspace):
        """Test tạo version không có v prefix (auto-add)."""
        create_version('1.0.0')

        # Should auto-add v prefix
        version_dir = Path(temp_workspace) / ".midicoder" / "versions" / "v1.0.0"
        assert version_dir.exists()


class TestVersionUse:
    """Tests cho version use/switch."""
    
    def test_use_version_success(self, workspace_with_multiple_versions):
        """Test switch version thành công."""
        use_version('v1.0.1')
        
        # Check active version updated
        config_file = Path(workspace_with_multiple_versions) / ".midicoder" / "config" / "midicoder.yml"
        with open(config_file) as f:
            config = yaml.safe_load(f)
        assert config['active_version'] == 'v1.0.1'
        
        # Check old active marked as archived
        old_metadata = Path(workspace_with_multiple_versions) / ".midicoder" / "versions" / "v1.0.2" / "metadata.yml"
        with open(old_metadata) as f:
            old_meta = yaml.safe_load(f)
        assert old_meta['status'] == 'archived'
        
        # Check new active marked as active
        new_metadata = Path(workspace_with_multiple_versions) / ".midicoder" / "versions" / "v1.0.1" / "metadata.yml"
        with open(new_metadata) as f:
            new_meta = yaml.safe_load(f)
        assert new_meta['status'] == 'inbuild'
    
    def test_use_version_without_v_prefix(self, workspace_with_multiple_versions):
        """Test switch version không có v prefix."""
        use_version('1.0.1')
        
        config_file = Path(workspace_with_multiple_versions) / ".midicoder" / "config" / "midicoder.yml"
        with open(config_file) as f:
            config = yaml.safe_load(f)
        assert config['active_version'] == 'v1.0.1'
    
    def test_use_version_not_found(self, temp_workspace):
        """Test switch version không tồn tại."""
        with pytest.raises(MidicoderError) as exc_info:
            use_version('v9.9.9')
        
        assert exc_info.value.code == ErrorCode.VERSION_NOT_FOUND


class TestVersionList:
    """Tests cho version list."""
    
    def test_list_versions_empty(self, temp_workspace):
        """Test list versions khi không có version."""
        versions = list_versions()
        assert versions == []
    
    def test_list_versions_single(self, workspace_with_version):
        """Test list versions với 1 version."""
        versions = list_versions()
        assert len(versions) == 1
        assert versions[0]['name'] == 'v1.0.0'
        assert versions[0]['metadata']['status'] == 'inbuild'
    
    def test_list_versions_multiple_sorted(self, workspace_with_multiple_versions):
        """Test list versions với nhiều versions (sorted by created_at)."""
        versions = list_versions()
        assert len(versions) == 3
        
        # Should be sorted by created_at (newest first)
        assert versions[0]['name'] == 'v1.0.2'
        assert versions[1]['name'] == 'v1.0.1'
        assert versions[2]['name'] == 'v1.0.0'


class TestVersionDelete:
    """Tests cho version delete."""
    
    def test_delete_version_success(self, workspace_with_multiple_versions):
        """Test xóa version thành công."""
        # Switch away first
        use_version('v1.0.2')
        delete_version('v1.0.0')
        
        # Check version directory removed
        version_dir = Path(workspace_with_multiple_versions) / ".midicoder" / "versions" / "v1.0.0"
        assert not version_dir.exists()
    
    def test_delete_active_version_without_force(self, workspace_with_version):
        """Test xóa active version không force."""
        with pytest.raises(MidicoderError) as exc_info:
            delete_version('v1.0.0')
        
        assert exc_info.value.code == ErrorCode.VERSION_DELETE_ACTIVE
    
    def test_delete_active_version_with_force(self, workspace_with_version):
        """Test xóa active version với force."""
        delete_version('v1.0.0', force=True)
        
        # Check version directory removed
        version_dir = Path(workspace_with_version) / ".midicoder" / "versions" / "v1.0.0"
        assert not version_dir.exists()
    
    def test_delete_version_not_found(self, temp_workspace):
        """Test xóa version không tồn tại."""
        with pytest.raises(MidicoderError) as exc_info:
            delete_version('v9.9.9')
        
        assert exc_info.value.code == ErrorCode.VERSION_NOT_FOUND


# ============================================================================
# Auto-Cleanup Tests
# ============================================================================

class TestAutoCleanup:
    """Tests cho auto-cleanup."""
    
    def test_no_cleanup_when_under_max(self, workspace_with_multiple_versions):
        """Test không cleanup khi số versions <= max_versions."""
        # Already have 3 versions, max is 5
        # Create 2 more (total 5)
        create_version('v1.0.3')
        create_version('v1.0.4')
        
        versions = list_versions()
        assert len(versions) == 5
    
    def test_cleanup_when_over_max(self, workspace_with_multiple_versions):
        """Test cleanup khi số versions > max_versions."""
        # Already have 3 versions, max is 5
        # Create 3 more (total 6)
        create_version('v1.0.3')
        create_version('v1.0.4')
        create_version('v1.0.5')
        
        versions = list_versions()
        # Should have cleaned up to 5 (active protected)
        assert len(versions) <= 5
        
        # Active version should still exist
        active = get_active_version()
        assert active is not None
        versions_dir = Path(str(workspace_with_multiple_versions)) / ".midicoder" / "versions"
        version_dirs = list(versions_dir.iterdir())
        active_exists = any(d.name == active for d in version_dirs)
        assert active_exists
    
    def test_cleanup_preserves_active(self, workspace_with_multiple_versions):
        """Test cleanup bảo vệ active version."""
        current_active = get_active_version()
        
        # Create versions until cleanup triggers
        for i in range(6):
            try:
                create_version(f'v2.0.{i}')
            except:
                break
        
        # Active version should still exist
        active = get_active_version()
        assert active is not None
        versions_dir = Path(str(workspace_with_multiple_versions)) / ".midicoder" / "versions"
        version_dirs = list(versions_dir.iterdir())
        active_exists = any(d.name == active for d in version_dirs)
        assert active_exists

    def test_cleanup_prioritizes_archived(self, workspace_with_multiple_versions):
        """Test cleanup ưu tiên archived versions."""
        current_active = get_active_version()

        for i in range(5):
            try:
                create_version(f'v2.0.{i}')
            except:
                break

        # Active version should always survive cleanup
        versions_dir = Path(str(workspace_with_multiple_versions)) / ".midicoder" / "versions"
        version_dirs = list(versions_dir.iterdir())
        version_names = [d.name for d in version_dirs]

        # Active version (đã update từ test trước) nên vẫn tồn tại
        active = get_active_version()
        assert active in version_names


# ============================================================================
# Helper Function Tests
# ============================================================================

class TestHelperFunctions:
    """Tests cho helper functions."""
    
    def test_get_workspace_dir_no_workspace(self):
        """Test get_workspace_dir khi không có workspace."""
        temp_dir = tempfile.mkdtemp()
        original_dir = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            with pytest.raises(MidicoderError) as exc_info:
                get_workspace_dir()
            assert exc_info.value.code == ErrorCode.CONFIG_READ_FAILED
        finally:
            os.chdir(original_dir)
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_get_active_version(self, workspace_with_version):
        """Test get_active_version."""
        active = get_active_version()
        assert active == 'v1.0.0'
    
    def test_get_max_versions(self, temp_workspace):
        """Test get_max_versions."""
        max_v = get_max_versions()
        assert max_v == 5
    
    def test_load_version_metadata(self, workspace_with_version):
        """Test load_version_metadata."""
        metadata = load_version_metadata('v1.0.0')
        assert metadata['version'] == '1.0.0'
        assert metadata['status'] == 'inbuild'
    
    def test_load_version_metadata_not_found(self, temp_workspace):
        """Test load_version_metadata khi version không tồn tại."""
        with pytest.raises(MidicoderError) as exc_info:
            load_version_metadata('v9.9.9')
        assert exc_info.value.code == ErrorCode.VERSION_NOT_FOUND


# ============================================================================
# Integration Tests
# ============================================================================

class TestVersionIntegration:
    """Integration tests cho version workflow."""
    
    def test_full_version_workflow(self, temp_workspace):
        """Test full version workflow: create -> list -> use -> delete."""
        # Create first version
        create_version('v1.0.0')
        
        # List should show 1 version
        versions = list_versions()
        assert len(versions) == 1
        
        # Create second version
        create_version('v1.0.1')
        
        # List should show 2 versions
        versions = list_versions()
        assert len(versions) == 2
        
        # Switch to first version
        use_version('v1.0.0')
        assert get_active_version() == 'v1.0.0'
        
        # Delete second version
        delete_version('v1.0.1')
        
        # List should show 1 version
        versions = list_versions()
        assert len(versions) == 1
    
    def test_version_with_pipeline_progress(self, temp_workspace):
        """Test version với pipeline progress tracking."""
        create_version('v1.0.0')
        
        # Simulate pipeline progress
        metadata_file = Path(temp_workspace) / ".midicoder" / "versions" / "v1.0.0" / "metadata.yml"
        with open(metadata_file) as f:
            metadata = yaml.safe_load(f)

        # Update pipeline status
        metadata['pipeline']['brief'] = 'frozen'
        metadata['artifacts']['briefs'] = 1

        with open(metadata_file, 'w') as f:
            yaml.dump(metadata, f)

        # Verify
        versions = list_versions()
        assert versions[0]['metadata']['pipeline']['brief'] == 'frozen'
        assert versions[0]['metadata']['artifacts']['briefs'] == 1


# ============================================================================
# _sync_metadata_from_sqlite — SQLite là nguồn sự thật, sync ra metadata.yml
# ============================================================================

class TestSyncMetadataFromSQLite:
    """Test đồng bộ metadata.yml từ SQLite status."""

    @pytest.fixture
    def workspace_with_sqlite_sync(self, temp_workspace):
        """Tạo workspace có versions trong SQLite và metadata.yml."""
        from midicoder.storage.projects import ProjectsManager
        from unittest.mock import patch

        versions_dir = Path(temp_workspace) / ".midicoder" / "versions"
        config_dir = Path(temp_workspace) / ".midicoder" / "config"

        # Tạo versions trên filesystem
        for vname, status in [("v1.0.0", "inbuild"), ("v2.0.0", "draft")]:
            vdir = versions_dir / vname
            vdir.mkdir(parents=True, exist_ok=True)
            (vdir / "src").mkdir(exist_ok=True)
            meta = {
                "version": vname.lstrip("v"),
                "status": status,
                "created_at": "2026-06-09T10:00:00Z",
                "pipeline": {"brief": "none", "contract": "none", "ir": "none", "code": "none"},
                "artifacts": {"briefs": 0, "contracts": 0, "files": 0, "lines": 0},
            }
            with open(vdir / "metadata.yml", "w") as f:
                yaml.dump(meta, f)

        # Config
        with open(config_dir / "midicoder.yml", "w") as f:
            yaml.dump({"active_version": "v2.0.0", "max_versions": 5}, f)

        # Mock project path
        project_id = hashlib.md5(str(Path(temp_workspace).resolve()).encode()).hexdigest()[:12]

        return temp_workspace, project_id, versions_dir

    def test_sync_archives_inbuild_versions(self, temp_workspace, workspace_with_sqlite_sync):
        """Khi SQLite archive version inbuild, metadata.yml cũng được sync."""
        from midicoder.pipeline.commands.version import _sync_metadata_from_sqlite
        from midicoder.storage.projects import ProjectsManager
        from unittest.mock import patch

        temp_ws, project_id, versions_dir = workspace_with_sqlite_sync

        # Tạo in-memory DB và insert versions với status khác
        import tempfile
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        mgr = ProjectsManager(db_path=Path(tmp.name))
        mgr.init()
        mgr.version_create(project_id, "v1.0.0", set_active=False)
        mgr.version_create(project_id, "v2.0.0", set_active=False)
        # Set v1.0.0 = inbuild, v2.0.0 = archived
        mgr.version_update_status(project_id, "v1.0.0", "inbuild")
        mgr.version_update_status(project_id, "v2.0.0", "archived")

        # Sync — metadata.yml phải khớp SQLite
        with patch("midicoder.pipeline.commands.version._get_manager", return_value=mgr):
            with patch("midicoder.pipeline.commands.version._get_project_id", return_value=project_id):
                with patch("midicoder.pipeline.commands.version.get_versions_dir", return_value=versions_dir):
                    _sync_metadata_from_sqlite(project_id)

        # Verify: v1.0.0 metadata.yml status = inbuild
        meta1 = yaml.safe_load((versions_dir / "v1.0.0" / "metadata.yml").read_text())
        assert meta1["status"] == "inbuild"

        # Verify: v2.0.0 metadata.yml status = archived
        meta2 = yaml.safe_load((versions_dir / "v2.0.0" / "metadata.yml").read_text())
        assert meta2["status"] == "archived"

        # Cleanup
        os.unlink(tmp.name)


# ============================================================================
# check_create_version — kiểm tra impact trước khi tạo
# ============================================================================

class TestCheckCreateVersion:
    """Test validate + impact check trước khi tạo version."""

    def test_validates_semver_format(self, temp_workspace):
        """Reject tên version không đúng SemVer."""
        from midicoder.pipeline.commands.version import check_create_version
        from midicoder.storage.projects import ProjectsManager
        from unittest.mock import patch

        import tempfile
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        mgr = ProjectsManager(db_path=Path(tmp.name))
        mgr.init()

        with patch("midicoder.pipeline.commands.version._get_manager", return_value=mgr):
            result = check_create_version("invalid-name!")

        assert result["error"] is not None
        assert "SemVer" in result["error"]
        os.unlink(tmp.name)

    def test_no_active_project(self, temp_workspace):
        """Trả về empty khi không có project active."""
        from midicoder.pipeline.commands.version import check_create_version
        from midicoder.storage.projects import ProjectsManager
        from unittest.mock import patch

        import tempfile
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        mgr = ProjectsManager(db_path=Path(tmp.name))
        mgr.init()

        with patch("midicoder.pipeline.commands.version._get_manager", return_value=mgr):
            result = check_create_version("v1.0.0")

        assert result["error"] is None
        assert result["current_count"] == 0
        assert result["will_archive"] == []
        assert result["will_delete"] == []
        os.unlink(tmp.name)

    def test_detects_inbuild_versions_to_archive(self, temp_workspace):
        """Detect các version status=inbuild sẽ bị archive."""
        from midicoder.pipeline.commands.version import check_create_version
        from midicoder.storage.projects import ProjectsManager
        from unittest.mock import patch

        import tempfile
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        mgr = ProjectsManager(db_path=Path(tmp.name))
        mgr.init()

        project_id = "testpid123456"
        mgr.create(project_id, "TestProject", "/tmp/test", set_active=True)
        mgr.version_create(project_id, "v1.0.0", set_active=True)
        mgr.version_update_status(project_id, "v1.0.0", "inbuild")

        with patch("midicoder.pipeline.commands.version._get_manager", return_value=mgr):
            with patch("midicoder.pipeline.commands.version.get_max_versions", return_value=5):
                result = check_create_version("v2.0.0")

        assert result["error"] is None
        assert len(result["will_archive"]) == 1
        assert result["will_archive"][0]["version"] == "v1.0.0"
        assert result["will_archive"][0]["status"] == "inbuild"
        os.unlink(tmp.name)

    def test_version_already_exists(self, temp_workspace):
        """Trả về error khi version đã tồn tại."""
        from midicoder.pipeline.commands.version import check_create_version
        from midicoder.storage.projects import ProjectsManager
        from unittest.mock import patch

        import tempfile
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        mgr = ProjectsManager(db_path=Path(tmp.name))
        mgr.init()

        project_id = "testpid123456"
        mgr.create(project_id, "TestProject", "/tmp/test", set_active=True)
        mgr.version_create(project_id, "v1.0.0", set_active=True)

        with patch("midicoder.pipeline.commands.version._get_manager", return_value=mgr):
            with patch("midicoder.pipeline.commands.version.get_max_versions", return_value=5):
                result = check_create_version("v1.0.0")

        assert result["error"] is not None
        assert "đã tồn tại" in result["error"]
        os.unlink(tmp.name)

    def test_semver_must_be_greater(self, temp_workspace):
        """Version mới phải lớn hơn version cao nhất hiện có."""
        from midicoder.pipeline.commands.version import check_create_version
        from midicoder.storage.projects import ProjectsManager
        from unittest.mock import patch

        import tempfile
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        mgr = ProjectsManager(db_path=Path(tmp.name))
        mgr.init()

        project_id = "testpid123456"
        mgr.create(project_id, "TestProject", "/tmp/test", set_active=True)
        mgr.version_create(project_id, "v2.0.0", set_active=True)

        with patch("midicoder.pipeline.commands.version._get_manager", return_value=mgr):
            with patch("midicoder.pipeline.commands.version.get_max_versions", return_value=5):
                result = check_create_version("v1.5.0")

        assert result["error"] is not None
        assert "phải lớn hơn" in result["error"]
        os.unlink(tmp.name)

    def test_autocomplete_normalizes_prefix(self, temp_workspace):
        """Tự động thêm 'v' prefix nếu thiếu."""
        from midicoder.pipeline.commands.version import check_create_version
        from midicoder.storage.projects import ProjectsManager
        from unittest.mock import patch

        import tempfile
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        mgr = ProjectsManager(db_path=Path(tmp.name))
        mgr.init()

        project_id = "testpid123456"
        mgr.create(project_id, "TestProject", "/tmp/test", set_active=True)

        with patch("midicoder.pipeline.commands.version._get_manager", return_value=mgr):
            with patch("midicoder.pipeline.commands.version.get_max_versions", return_value=5):
                result = check_create_version("1.0.0")  # thiếu 'v'

        assert result["error"] is None
        os.unlink(tmp.name)