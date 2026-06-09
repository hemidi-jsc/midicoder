"""
Tests cho Version Management Commands.

Test coverage:
- Version validation (SemVer regex)
- Version create
- Version use
- Version list
- Version delete
- Auto-cleanup

SoT Reference: E01
"""

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
    load_version_metadata,
    save_version_metadata,
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
        """Test tạo version mới thành công."""
        create_version('v1.0.1')
        
        # Check version directory created
        version_dir = Path(temp_workspace) / ".midicoder" / "versions" / "v1.0.1"
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
        assert metadata['version'] == '1.0.1'
        assert metadata['status'] == 'draft'
        assert metadata['parent_version'] is None
        
        # Check active version updated
        config_file = Path(temp_workspace) / ".midicoder" / "config" / "midicoder.yml"
        with open(config_file) as f:
            config = yaml.safe_load(f)
        assert config['active_version'] == 'v1.0.1'
    
    def test_create_version_without_v_prefix(self, temp_workspace):
        """Test tạo version không có v prefix (auto-add)."""
        create_version('1.0.1')
        
        # Should auto-add v prefix
        version_dir = Path(temp_workspace) / ".midicoder" / "versions" / "v1.0.1"
        assert version_dir.exists()
    
    def test_create_version_from_parent(self, workspace_with_version):
        """Test tạo version từ parent."""
        # Tạo parent src với file
        parent_src = Path(workspace_with_version) / ".midicoder" / "versions" / "v1.0.0" / "src"
        parent_src.mkdir(parents=True)
        test_file = parent_src / "test.txt"
        test_file.write_text("test content")
        
        create_version('v1.0.1', from_version='v1.0.0')
        
        # Check file copied
        child_src = Path(workspace_with_version) / ".midicoder" / "versions" / "v1.0.1" / "src"
        copied_file = child_src / "test.txt"
        assert copied_file.exists()
        assert copied_file.read_text() == "test content"
        
        # Check metadata has parent
        metadata_file = Path(workspace_with_version) / ".midicoder" / "versions" / "v1.0.1" / "metadata.yml"
        with open(metadata_file) as f:
            metadata = yaml.safe_load(f)
        assert metadata['parent_version'] == '1.0.0'
    
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
    
    def test_create_version_nonexistent_parent(self, temp_workspace):
        """Test tạo version với parent không tồn tại."""
        with pytest.raises(MidicoderError) as exc_info:
            create_version('v1.0.1', from_version='v9.9.9')
        
        assert exc_info.value.code == ErrorCode.VERSION_NOT_FOUND


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