"""
Unit Tests cho Artifact Contracts.

Kiểm tra behavior của:
- ArtifactVersion class
- ArtifactMetadata class
- ArtifactBase class
- write_artifact() function
- read_artifact() function
- compute_content_hash() function
- compute_file_hash() function

Tests tuân thủ TDD, không mocks, bám sát SoT.

Author: Midicoder Team
Version: 1.0.0
"""

import json
import pytest
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from midicoder.contracts.artifact import (
    ArtifactVersion,
    ArtifactMetadata,
    ArtifactBase,
    write_artifact,
    read_artifact,
    compute_content_hash,
    compute_file_hash,
)


# ============================================================================
# ArtifactVersion Tests (12 tests)
# ============================================================================


class TestArtifactVersion:
    """Tests cho ArtifactVersion class."""

    def test_version_created_with_defaults(self):
        """Kiểm tra ArtifactVersion được tạo với default values."""
        version = ArtifactVersion()

        assert version.major == 1
        assert version.minor == 0
        assert version.patch == 0
        assert version.prerelease is None

    def test_version_created_with_custom_values(self):
        """Kiểm tra ArtifactVersion được tạo với custom values."""
        version = ArtifactVersion(major=2, minor=5, patch=10, prerelease="beta")

        assert version.major == 2
        assert version.minor == 5
        assert version.patch == 10
        assert version.prerelease == "beta"

    def test_version_str_without_prerelease(self):
        """Kiểm tra str(version) không có prerelease."""
        version = ArtifactVersion(major=1, minor=2, patch=3)

        assert str(version) == "1.2.3"

    def test_version_str_with_prerelease(self):
        """Kiểm tra str(version) có prerelease."""
        version = ArtifactVersion(major=1, minor=0, patch=0, prerelease="alpha")

        assert str(version) == "1.0.0-alpha"

    def test_version_str_with_rc_prerelease(self):
        """Kiểm tra str(version) với release candidate prerelease."""
        version = ArtifactVersion(major=0, minor=9, patch=5, prerelease="rc1")

        assert str(version) == "0.9.5-rc1"

    def test_version_to_dict(self):
        """Kiểm tra to_dict trả về dictionary đúng."""
        version = ArtifactVersion(major=1, minor=2, patch=3, prerelease="beta")
        version_dict = version.to_dict()

        assert version_dict == {
            "major": 1,
            "minor": 2,
            "patch": 3,
            "prerelease": "beta",
        }

    def test_version_to_dict_with_defaults(self):
        """Kiểm tra to_dict với default values."""
        version = ArtifactVersion()
        version_dict = version.to_dict()

        assert version_dict == {
            "major": 1,
            "minor": 0,
            "patch": 0,
            "prerelease": None,
        }

    def test_version_from_dict(self):
        """Kiểm tra from_dict tạo ArtifactVersion đúng."""
        version_data = {
            "major": 2,
            "minor": 5,
            "patch": 10,
            "prerelease": "alpha",
        }

        version = ArtifactVersion.from_dict(version_data)

        assert version.major == 2
        assert version.minor == 5
        assert version.patch == 10
        assert version.prerelease == "alpha"

    def test_version_from_dict_with_defaults(self):
        """Kiểm tra from_dict với missing fields dùng defaults."""
        version_data = {"major": 3}

        version = ArtifactVersion.from_dict(version_data)

        assert version.major == 3
        assert version.minor == 0
        assert version.patch == 0
        assert version.prerelease is None

    def test_version_roundtrip_preserves_state(self):
        """Kiểm tra roundtrip serialization giữ nguyên state."""
        original = ArtifactVersion(major=1, minor=0, patch=0, prerelease="rc1")

        version_dict = original.to_dict()
        reconstructed = ArtifactVersion.from_dict(version_dict)

        assert reconstructed.major == original.major
        assert reconstructed.minor == original.minor
        assert reconstructed.patch == original.patch
        assert reconstructed.prerelease == original.prerelease

    def test_version_edge_case_large_numbers(self):
        """Kiểm tra ArtifactVersion với số lớn."""
        version = ArtifactVersion(major=999, minor=999, patch=999)

        assert str(version) == "999.999.999"

    def test_version_edge_case_zero_values(self):
        """Kiểm tra ArtifactVersion với giá trị 0."""
        version = ArtifactVersion(major=0, minor=0, patch=0)

        assert str(version) == "0.0.0"


# ============================================================================
# ArtifactMetadata Tests (16 tests)
# ============================================================================


class TestArtifactMetadata:
    """Tests cho ArtifactMetadata class."""

    def test_metadata_created_with_auto_timestamps(self):
        """Kiểm tra ArtifactMetadata tự động tạo timestamps."""
        metadata = ArtifactMetadata()

        assert metadata.created_at is not None
        assert metadata.updated_at is not None
        assert metadata.created_at == metadata.updated_at

    def test_metadata_created_with_custom_timestamps(self):
        """Kiểm tra ArtifactMetadata với custom timestamps."""
        created = "2024-01-01T00:00:00Z"
        updated = "2024-01-02T00:00:00Z"
        metadata = ArtifactMetadata(created_at=created, updated_at=updated)

        assert metadata.created_at == created
        assert metadata.updated_at == updated

    def test_metadata_created_with_all_fields(self):
        """Kiểm tra ArtifactMetadata được tạo với tất cả fields."""
        metadata = ArtifactMetadata.with_timestamp(
            author="alice@example.com",
            organization="Midicoder Inc",
            version="1.0.0",
            generated_by="midicoder-cli",
            git_commit="abc123",
            description="Test artifact",
            tags=["test", "p0"],
            source_files=["contracts/test.yaml"],
        )

        assert metadata.author == "alice@example.com"
        assert metadata.organization == "Midicoder Inc"
        assert metadata.version == "1.0.0"
        assert metadata.generated_by == "midicoder-cli"
        assert metadata.git_commit == "abc123"
        assert metadata.description == "Test artifact"
        assert metadata.tags == ["test", "p0"]
        assert metadata.source_files == ["contracts/test.yaml"]

    def test_metadata_with_timestamp_sets_current_time(self):
        """Kiểm tra with_timestamp set current timestamp."""
        metadata = ArtifactMetadata.with_timestamp(author="test")

        # Parse timestamp để kiểm tra format
        created_dt = datetime.fromisoformat(metadata.created_at.replace("Z", "+00:00"))
        now = datetime.utcnow().replace(tzinfo=created_dt.tzinfo)

        # Timestamp phải gần hiện tại (trong 10 giây)
        diff = abs((now - created_dt).total_seconds())
        assert diff < 10

    def test_metadata_update_timestamp(self):
        """Kiểm tra update_timestamp cập nhật updated_at."""
        metadata = ArtifactMetadata.with_timestamp(author="test")
        old_updated_at = metadata.updated_at

        # Update timestamp
        metadata.update_timestamp()

        # updated_at phải thay đổi
        assert metadata.updated_at != old_updated_at
        assert metadata.updated_at is not None

    def test_metadata_to_dict_contains_all_fields(self):
        """Kiểm tra to_dict chứa tất cả fields."""
        metadata = ArtifactMetadata.with_timestamp(
            author="alice",
            organization="Org",
            version="1.0.0",
            tags=["tag1"],
            source_files=["file1.yaml"],
        )
        metadata_dict = metadata.to_dict()

        assert "created_at" in metadata_dict
        assert "updated_at" in metadata_dict
        assert metadata_dict["author"] == "alice"
        assert metadata_dict["organization"] == "Org"
        assert metadata_dict["version"] == "1.0.0"
        assert metadata_dict["tags"] == ["tag1"]
        assert metadata_dict["source_files"] == ["file1.yaml"]

    def test_metadata_to_dict_with_empty_lists(self):
        """Kiểm tra to_dict với empty lists."""
        metadata = ArtifactMetadata()
        metadata_dict = metadata.to_dict()

        assert metadata_dict["tags"] == []
        assert metadata_dict["source_files"] == []

    def test_metadata_from_dict(self):
        """Kiểm tra from_dict tạo ArtifactMetadata đúng."""
        metadata_data = {
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-02T00:00:00Z",
            "author": "alice",
            "organization": "Org",
            "version": "1.0.0",
            "generated_by": "cli",
            "git_commit": "abc123",
            "description": "Test",
            "tags": ["tag1", "tag2"],
            "source_files": ["file1.yaml", "file2.yaml"],
        }

        metadata = ArtifactMetadata.from_dict(metadata_data)

        assert metadata.created_at == "2024-01-01T00:00:00Z"
        assert metadata.author == "alice"
        assert metadata.tags == ["tag1", "tag2"]
        assert metadata.source_files == ["file1.yaml", "file2.yaml"]

    def test_metadata_from_dict_with_missing_fields(self):
        """Kiểm tra from_dict với missing fields."""
        metadata_data = {"author": "alice"}

        metadata = ArtifactMetadata.from_dict(metadata_data)

        assert metadata.author == "alice"
        # __post_init__ tự động set timestamps khi created_at là None
        assert metadata.created_at is not None
        assert metadata.updated_at == metadata.created_at
        assert metadata.organization is None
        assert metadata.tags == []
        assert metadata.source_files == []

    def test_metadata_roundtrip_preserves_state(self):
        """Kiểm tra roundtrip serialization giữ nguyên state."""
        original = ArtifactMetadata.with_timestamp(
            author="alice",
            organization="Org",
            version="1.0.0",
            tags=["test"],
            source_files=["test.yaml"],
        )

        metadata_dict = original.to_dict()
        reconstructed = ArtifactMetadata.from_dict(metadata_dict)

        assert reconstructed.author == original.author
        assert reconstructed.organization == original.organization
        assert reconstructed.version == original.version
        assert reconstructed.tags == original.tags
        assert reconstructed.source_files == original.source_files

    def test_metadata_tags_default_empty_list(self):
        """Kiểm tra tags mặc định là empty list."""
        metadata = ArtifactMetadata()

        assert metadata.tags == []
        assert isinstance(metadata.tags, list)

    def test_metadata_source_files_default_empty_list(self):
        """Kiểm tra source_files mặc định là empty list."""
        metadata = ArtifactMetadata()

        assert metadata.source_files == []
        assert isinstance(metadata.source_files, list)

    def test_metadata_with_special_characters(self):
        """Kiểm tra metadata với special characters."""
        metadata = ArtifactMetadata.with_timestamp(
            author="Alice <alice@example.com>",
            description="Test with special chars: @#$%",
            tags=["tag-with-dash", "tag_with_underscore"],
        )

        assert metadata.author == "Alice <alice@example.com>"
        assert "@#$%" in metadata.description

    def test_metadata_timestamp_format_iso8601(self):
        """Kiểm tra timestamp format ISO 8601."""
        metadata = ArtifactMetadata.with_timestamp()

        # ISO 8601 format: YYYY-MM-DDTHH:MM:SS
        assert "T" in metadata.created_at
        assert metadata.created_at.endswith("Z")

    def test_metadata_multiple_tags(self):
        """Kiểm tra metadata với nhiều tags."""
        tags = ["p0", "critical", "artifact", "test"]
        metadata = ArtifactMetadata.with_timestamp(tags=tags)

        assert metadata.tags == tags
        assert len(metadata.tags) == 4

    def test_metadata_multiple_source_files(self):
        """Kiểm tra metadata với nhiều source files."""
        files = [
            "contracts/entities.yaml",
            "contracts/commands.yaml",
            "contracts/queries.yaml",
        ]
        metadata = ArtifactMetadata.with_timestamp(source_files=files)

        assert metadata.source_files == files
        assert len(metadata.source_files) == 3


# ============================================================================
# ArtifactBase Tests (10 tests)
# ============================================================================


class TestArtifactBase:
    """Tests cho ArtifactBase class."""

    def test_base_class_cannot_be_instantiated_directly_for_type(self):
        """Kiểm tra ArtifactBase.artifact_type raise NotImplementedError."""
        # Tạo instance nhưng artifact_type phải raise NotImplementedError
        artifact = object.__new__(ArtifactBase)
        artifact.metadata = ArtifactMetadata()

        with pytest.raises(NotImplementedError):
            _ = artifact.artifact_type

    def test_base_class_has_default_version(self):
        """Kiểm tra ArtifactBase có default version."""
        artifact = object.__new__(ArtifactBase)
        artifact.metadata = ArtifactMetadata()

        version = artifact.artifact_version
        assert version.major == 1
        assert version.minor == 0
        assert version.patch == 0

    def test_base_class_auto_initializes_metadata(self):
        """Kiểm tra ArtifactBase tự động initialize metadata."""
        artifact = object.__new__(ArtifactBase)
        # __post_init__ sẽ được gọi
        ArtifactBase.__post_init__(artifact)

        assert artifact.metadata is not None
        assert isinstance(artifact.metadata, ArtifactMetadata)

    def test_to_dict_includes_type_and_version(self):
        """Kiểm tra to_dict bao gồm type và version."""

        class TestArtifact(ArtifactBase):
            @property
            def artifact_type(self) -> str:
                return "test_artifact"

        artifact = TestArtifact()
        artifact_dict = artifact.to_dict()

        assert artifact_dict["type"] == "test_artifact"
        assert artifact_dict["version"] == "1.0.0"
        assert "metadata" in artifact_dict

    def test_to_dict_includes_metadata(self):
        """Kiểm tra to_dict bao gồm metadata."""

        class TestArtifact(ArtifactBase):
            @property
            def artifact_type(self) -> str:
                return "test_artifact"

        artifact = TestArtifact()
        artifact.metadata = ArtifactMetadata.with_timestamp(author="test")
        artifact_dict = artifact.to_dict()

        assert artifact_dict["metadata"]["author"] == "test"

    def test_compute_hash_excludes_timestamps(self):
        """Kiểm tra compute_hash không bao gồm timestamps."""

        class TestArtifact(ArtifactBase):
            @property
            def artifact_type(self) -> str:
                return "test_artifact"

        artifact1 = TestArtifact()
        artifact1.metadata = ArtifactMetadata.with_timestamp(author="test")

        artifact2 = TestArtifact()
        artifact2.metadata = ArtifactMetadata.with_timestamp(author="test")

        # Hash phải giống nhau mặc dù timestamps khác nhau
        hash1 = artifact1.compute_hash()
        hash2 = artifact2.compute_hash()

        assert hash1 == hash2

    def test_compute_hash_is_deterministic(self):
        """Kiểm tra compute_hash là deterministic."""

        class TestArtifact(ArtifactBase):
            @property
            def artifact_type(self) -> str:
                return "test_artifact"

        artifact = TestArtifact()

        # Tính hash nhiều lần phải ra kết quả giống nhau
        hash1 = artifact.compute_hash()
        hash2 = artifact.compute_hash()
        hash3 = artifact.compute_hash()

        assert hash1 == hash2 == hash3

    def test_compute_hash_returns_sha256_format(self):
        """Kiểm tra compute_hash trả về SHA-256 format."""

        class TestArtifact(ArtifactBase):
            @property
            def artifact_type(self) -> str:
                return "test_artifact"

        artifact = TestArtifact()
        hash_value = artifact.compute_hash()

        # SHA-256 hash là 64 hex characters
        assert len(hash_value) == 64
        assert all(c in "0123456789abcdef" for c in hash_value)

    def test_validate_returns_empty_list_when_valid(self):
        """Kiểm tra validate trả về empty list khi valid."""

        class TestArtifact(ArtifactBase):
            @property
            def artifact_type(self) -> str:
                return "test_artifact"

        artifact = TestArtifact()

        errors = artifact.validate()

        assert errors == []

    def test_validate_returns_errors_when_metadata_missing(self):
        """Kiểm tra validate trả về errors khi metadata missing."""

        class TestArtifact(ArtifactBase):
            @property
            def artifact_type(self) -> str:
                return "test_artifact"

        artifact = TestArtifact()
        artifact.metadata = None  # type: ignore

        errors = artifact.validate()

        assert len(errors) > 0
        assert any("Metadata" in err for err in errors)


# ============================================================================
# write_artifact Tests (8 tests)
# ============================================================================


class TestWriteArtifact:
    """Tests cho write_artifact function."""

    def test_write_artifact_creates_file(self):
        """Kiểm tra write_artifact tạo file."""

        class TestArtifact(ArtifactBase):
            @property
            def artifact_type(self) -> str:
                return "test_artifact"

        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test_artifact.json"
            artifact = TestArtifact()
            write_artifact(artifact, path)

            assert path.exists()

    def test_write_artifact_creates_parent_directories(self):
        """Kiểm tra write_artifact tạo parent directories."""

        class TestArtifact(ArtifactBase):
            @property
            def artifact_type(self) -> str:
                return "test_artifact"

        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "subdir" / "nested" / "test_artifact.json"
            artifact = TestArtifact()
            write_artifact(artifact, path)

            assert path.exists()
            assert path.parent.exists()

    def test_write_artifact_writes_valid_json(self):
        """Kiểm tra write_artifact viết valid JSON."""

        class TestArtifact(ArtifactBase):
            @property
            def artifact_type(self) -> str:
                return "test_artifact"

        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test_artifact.json"
            artifact = TestArtifact()
            write_artifact(artifact, path)

            with open(path, "r") as f:
                data = json.load(f)

            assert "type" in data
            assert "version" in data
            assert "metadata" in data

    def test_write_artifact_pretty_format(self):
        """Kiểm tra write_artifact với pretty format."""

        class TestArtifact(ArtifactBase):
            @property
            def artifact_type(self) -> str:
                return "test_artifact"

        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test_artifact.json"
            artifact = TestArtifact()
            write_artifact(artifact, path, pretty=True)

            with open(path, "r") as f:
                content = f.read()

            # Pretty format có indentation
            assert "  " in content

    def test_write_artifact_compact_format(self):
        """Kiểm tra write_artifact với compact format."""

        class TestArtifact(ArtifactBase):
            @property
            def artifact_type(self) -> str:
                return "test_artifact"

        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test_artifact.json"
            artifact = TestArtifact()
            write_artifact(artifact, path, pretty=False)

            with open(path, "r") as f:
                content = f.read()

            # Compact format không có newlines hay indentation
            assert "\n" not in content
            assert "  " not in content

    def test_write_artifact_raises_on_invalid_artifact(self):
        """Kiểm tra write_artifact raise ValueError khi artifact không valid."""

        class InvalidArtifact(ArtifactBase):
            @property
            def artifact_type(self) -> str:
                return "invalid_artifact"

            def validate(self) -> list[str]:
                return ["Custom validation error"]

        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "invalid.json"
            artifact = InvalidArtifact()

            with pytest.raises(ValueError) as exc_info:
                write_artifact(artifact, path)

            assert "validation failed" in str(exc_info.value).lower()

    def test_write_artifact_updates_timestamp(self):
        """Kiểm tra write_artifact cập nhật timestamp."""

        class TestArtifact(ArtifactBase):
            @property
            def artifact_type(self) -> str:
                return "test_artifact"

        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test_artifact.json"
            artifact = TestArtifact()
            old_timestamp = artifact.metadata.updated_at

            write_artifact(artifact, path)

            # Timestamp phải được cập nhật
            assert artifact.metadata.updated_at != old_timestamp

    def test_write_artifact_with_string_path(self):
        """Kiểm tra write_artifact với string path."""

        class TestArtifact(ArtifactBase):
            @property
            def artifact_type(self) -> str:
                return "test_artifact"

        with TemporaryDirectory() as tmpdir:
            path = str(Path(tmpdir) / "test_artifact.json")
            artifact = TestArtifact()
            write_artifact(artifact, path)

            assert Path(path).exists()


# ============================================================================
# read_artifact Tests (6 tests)
# ============================================================================


class TestReadArtifact:
    """Tests cho read_artifact function."""

    def test_read_artifact_returns_dict(self):
        """Kiểm tra read_artifact trả về dictionary."""
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test_artifact.json"
            test_data = {"type": "test", "version": "1.0.0", "metadata": {}}
            with open(path, "w") as f:
                json.dump(test_data, f)

            result = read_artifact(path)

            assert isinstance(result, dict)
            assert result["type"] == "test"

    def test_read_artifact_raises_on_missing_file(self):
        """Kiểm tra read_artifact raise FileNotFoundError khi file không tồn tại."""
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "nonexistent.json"

            with pytest.raises(FileNotFoundError):
                read_artifact(path)

    def test_read_artifact_raises_on_invalid_json(self):
        """Kiểm tra read_artifact raise JSONDecodeError khi JSON không hợp lệ."""
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "invalid.json"
            with open(path, "w") as f:
                f.write("not valid json {")

            with pytest.raises(json.JSONDecodeError):
                read_artifact(path)

    def test_read_artifact_with_string_path(self):
        """Kiểm tra read_artifact với string path."""
        with TemporaryDirectory() as tmpdir:
            path = str(Path(tmpdir) / "test_artifact.json")
            test_data = {"type": "test", "metadata": {}}
            with open(path, "w") as f:
                json.dump(test_data, f)

            result = read_artifact(path)

            assert result["type"] == "test"

    def test_read_artifact_preserves_nested_structure(self):
        """Kiểm tra read_artifact giữ nguyên nested structure."""
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test_artifact.json"
            test_data = {
                "type": "test",
                "metadata": {"author": "alice"},
                "nested": {"key": "value"},
                "list": [1, 2, 3],
            }
            with open(path, "w") as f:
                json.dump(test_data, f)

            result = read_artifact(path)

            assert result["nested"]["key"] == "value"
            assert result["list"] == [1, 2, 3]

    def test_read_artifact_with_unicode(self):
        """Kiểm tra read_artifact với unicode characters."""
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test_artifact.json"
            test_data = {"description": "Test with unicode: 你好世界 🌍"}
            with open(path, "w", encoding="utf-8") as f:
                json.dump(test_data, f, ensure_ascii=False)

            result = read_artifact(path)

            assert result["description"] == "Test with unicode: 你好世界 🌍"


# ============================================================================
# compute_content_hash Tests (6 tests)
# ============================================================================


class TestComputeContentHash:
    """Tests cho compute_content_hash function."""

    def test_compute_content_hash_string(self):
        """Kiểm tra compute_content_hash với string input."""
        content = "test content"
        hash_value = compute_content_hash(content)

        assert len(hash_value) == 64
        assert isinstance(hash_value, str)

    def test_compute_content_hash_bytes(self):
        """Kiểm tra compute_content_hash với bytes input."""
        content = b"test content"
        hash_value = compute_content_hash(content)

        assert len(hash_value) == 64
        assert isinstance(hash_value, str)

    def test_compute_content_hash_empty_string(self):
        """Kiểm tra compute_content_hash với empty string."""
        content = ""
        hash_value = compute_content_hash(content)

        assert len(hash_value) == 64
        # Empty string có hash cụ thể
        assert hash_value == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    def test_compute_content_hash_deterministic(self):
        """Kiểm tra compute_content_hash là deterministic."""
        content = "test content"

        hash1 = compute_content_hash(content)
        hash2 = compute_content_hash(content)
        hash3 = compute_content_hash(content)

        assert hash1 == hash2 == hash3

    def test_compute_content_hash_different_content_different_hash(self):
        """Kiểm tra content khác nhau có hash khác nhau."""
        content1 = "test content 1"
        content2 = "test content 2"

        hash1 = compute_content_hash(content1)
        hash2 = compute_content_hash(content2)

        assert hash1 != hash2

    def test_compute_content_hash_unicode(self):
        """Kiểm tra compute_content_hash với unicode content."""
        content = "你好世界 🌍"
        hash_value = compute_content_hash(content)

        assert len(hash_value) == 64


# ============================================================================
# compute_file_hash Tests (6 tests)
# ============================================================================


class TestComputeFileHash:
    """Tests cho compute_file_hash function."""

    def test_compute_file_hash_returns_hash(self):
        """Kiểm tra compute_file_hash trả về hash."""
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.txt"
            with open(path, "w") as f:
                f.write("test content")

            hash_value = compute_file_hash(path)

            assert len(hash_value) == 64
            assert isinstance(hash_value, str)

    def test_compute_file_hash_with_string_path(self):
        """Kiểm tra compute_file_hash với string path."""
        with TemporaryDirectory() as tmpdir:
            path = str(Path(tmpdir) / "test.txt")
            with open(path, "w") as f:
                f.write("test content")

            hash_value = compute_file_hash(path)

            assert len(hash_value) == 64

    def test_compute_file_hash_different_files_different_hash(self):
        """Kiểm tra files khác nhau có hash khác nhau."""
        with TemporaryDirectory() as tmpdir:
            path1 = Path(tmpdir) / "file1.txt"
            path2 = Path(tmpdir) / "file2.txt"
            with open(path1, "w") as f:
                f.write("content 1")
            with open(path2, "w") as f:
                f.write("content 2")

            hash1 = compute_file_hash(path1)
            hash2 = compute_file_hash(path2)

            assert hash1 != hash2

    def test_compute_file_hash_same_content_same_hash(self):
        """Kiểm tra files có content giống nhau có hash giống nhau."""
        with TemporaryDirectory() as tmpdir:
            path1 = Path(tmpdir) / "file1.txt"
            path2 = Path(tmpdir) / "file2.txt"
            with open(path1, "w") as f:
                f.write("same content")
            with open(path2, "w") as f:
                f.write("same content")

            hash1 = compute_file_hash(path1)
            hash2 = compute_file_hash(path2)

            assert hash1 == hash2

    def test_compute_file_hash_binary_file(self):
        """Kiểm tra compute_file_hash với binary file."""
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.bin"
            with open(path, "wb") as f:
                f.write(b"\x00\x01\x02\x03")

            hash_value = compute_file_hash(path)

            assert len(hash_value) == 64

    def test_compute_file_hash_empty_file(self):
        """Kiểm tra compute_file_hash với empty file."""
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "empty.txt"
            with open(path, "w") as f:
                pass  # Create empty file

            hash_value = compute_file_hash(path)

            # Empty file có hash cụ thể
            assert hash_value == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"