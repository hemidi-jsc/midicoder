"""
Artifact Base Types cho Midicoder v1.0.0

Module này cung cấp các base types và utility functions cho tất cả artifacts.
Mọi artifact đều kế thừa từ ArtifactBase để đảm bảo:
- Metadata chuẩn (version, timestamps, provenance)
- Serialization/deserialization thống nhất
- Hash tính toán cho determinism
- Validation cơ bản

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, fields
from datetime import datetime
from pathlib import Path
from typing import Any, TypeVar

from typing_extensions import TypedDict


# ============================================================================
# Artifact Version
# ============================================================================


@dataclass
class ArtifactVersion:
    """
    Version information cho artifact.
    
    Attributes:
        major: Major version (breaking changes)
        minor: Minor version (new features)
        patch: Patch version (bug fixes)
        prerelease: Prerelease tag (alpha, beta, rc)
    
    Example:
        v = ArtifactVersion(major=1, minor=0, patch=0)
        str(v) -> "1.0.0"
    """
    major: int = 1
    minor: int = 0
    patch: int = 0
    prerelease: str | None = None
    
    def __str__(self) -> str:
        """Format version as string."""
        base = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            return f"{base}-{self.prerelease}"
        return base
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "major": self.major,
            "minor": self.minor,
            "patch": self.patch,
            "prerelease": self.prerelease,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ArtifactVersion":
        """Create from dictionary."""
        return cls(
            major=data.get("major", 1),
            minor=data.get("minor", 0),
            patch=data.get("patch", 0),
            prerelease=data.get("prerelease"),
        )


# ============================================================================
# Artifact Metadata
# ============================================================================


@dataclass
class ArtifactMetadata:
    """
    Metadata chuẩn cho tất cả artifacts.
    
    Cung cấp provenance, timestamps, và tracking information.
    
    Attributes:
        created_at: Thời điểm tạo artifact (ISO 8601)
        updated_at: Thời điểm cập nhật cuối (ISO 8601)
        author: Người tạo artifact
        organization: Tổ chức sở hữu artifact
        version: Version của artifact
        generated_by: Tool/process tạo artifact
        git_commit: Git commit hash (nếu có)
        description: Mô tả artifact
        tags: Danh sách tags
        source_files: Danh sách source files tham gia tạo artifact
    
    Example:
        metadata = ArtifactMetadata.with_timestamp(
            author="alice@example.com",
            description="Capability graph for e-commerce platform",
        )
    """
    created_at: str | None = None
    updated_at: str | None = None
    author: str | None = None
    organization: str | None = None
    version: str | None = None
    generated_by: str | None = None
    git_commit: str | None = None
    description: str | None = None
    tags: list[str] = field(default_factory=list)
    source_files: list[str] = field(default_factory=list)
    
    def __post_init__(self) -> None:
        """Validate và set default timestamps."""
        # Auto-set timestamps if not provided
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat() + "Z"
        if self.updated_at is None:
            self.updated_at = self.created_at
    
    @classmethod
    def with_timestamp(
        cls,
        author: str | None = None,
        organization: str | None = None,
        version: str | None = None,
        generated_by: str | None = None,
        git_commit: str | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
        source_files: list[str] | None = None,
    ) -> "ArtifactMetadata":
        """
        Tạo ArtifactMetadata với current timestamp.
        
        Args:
            author: Người tạo artifact
            organization: Tổ chức sở hữu
            version: Version string
            generated_by: Tool/process tạo artifact
            git_commit: Git commit hash
            description: Mô tả artifact
            tags: Danh sách tags
            source_files: Source files
            
        Returns:
            ArtifactMetadata với timestamps tự động
        """
        timestamp = datetime.utcnow().isoformat() + "Z"
        return cls(
            created_at=timestamp,
            updated_at=timestamp,
            author=author,
            organization=organization,
            version=version,
            generated_by=generated_by,
            git_commit=git_commit,
            description=description,
            tags=tags or [],
            source_files=source_files or [],
        )
    
    def update_timestamp(self) -> None:
        """Cập nhật updated_at timestamp."""
        self.updated_at = datetime.utcnow().isoformat() + "Z"
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "author": self.author,
            "organization": self.organization,
            "version": self.version,
            "generated_by": self.generated_by,
            "git_commit": self.git_commit,
            "description": self.description,
            "tags": self.tags,
            "source_files": self.source_files,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ArtifactMetadata":
        """Create from dictionary."""
        return cls(
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            author=data.get("author"),
            organization=data.get("organization"),
            version=data.get("version"),
            generated_by=data.get("generated_by"),
            git_commit=data.get("git_commit"),
            description=data.get("description"),
            tags=data.get("tags", []),
            source_files=data.get("source_files", []),
        )


# ============================================================================
# Base Artifact
# ============================================================================

T = TypeVar("T", bound="ArtifactBase")


@dataclass
class ArtifactBase:
    """
    Base class cho tất cả artifacts.
    
    Cung cấp:
    - Metadata management
    - JSON serialization/deserialization
    - Hash computation cho determinism
    - Validation cơ bản
    
    Subclasses cần implement:
    - artifact_type property
    - artifact_version property
    
    Note: metadata được đặt ở cuối để subclasses có thể define required fields trước.
    """
    # metadata phải ở cuối để subclasses có thể define required fields trước
    metadata: ArtifactMetadata = field(default_factory=ArtifactMetadata, init=False)
    
    def __post_init__(self) -> None:
        """Initialize metadata nếu chưa có."""
        if not hasattr(self, 'metadata') or self.metadata is None:
            object.__setattr__(self, 'metadata', ArtifactMetadata())
    
    @property
    def artifact_type(self) -> str:
        """
        Loại artifact.
        
        Overrides trong subclasses:
        - "capability_graph"
        - "mir"
        - "surface_plan"
        - "target_plan"
        - "patch_plan"
        - "validation_report"
        - "expansion_report"
        """
        raise NotImplementedError
    
    @property
    def artifact_version(self) -> ArtifactVersion:
        """Version của artifact schema."""
        return ArtifactVersion(major=1, minor=0, patch=0)
    
    def to_dict(self) -> dict[str, Any]:
        """
        Convert artifact to dictionary.
        
        Returns:
            Dictionary representation của artifact
        """
        result: dict[str, Any] = {
            "type": self.artifact_type,
            "version": str(self.artifact_version),
            "metadata": self.metadata.to_dict(),
        }
        
        # Add all dataclass fields except metadata
        for f in fields(self):
            if f.name != "metadata":
                value = getattr(self, f.name)
                if hasattr(value, "to_dict"):
                    result[f.name] = value.to_dict()
                elif isinstance(value, list):
                    result[f.name] = [
                        item.to_dict() if hasattr(item, "to_dict") else item
                        for item in value
                    ]
                else:
                    result[f.name] = value
        
        return result
    
    @classmethod
    def from_dict(cls: type[T], data: dict[str, Any]) -> T:
        """
        Create artifact from dictionary.
        
        Args:
            data: Dictionary representation
            
        Returns:
            Artifact instance
        """
        metadata = ArtifactMetadata.from_dict(data.get("metadata", {}))
        
        # Filter out metadata, type, version from data
        artifact_data = {
            k: v for k, v in data.items()
            if k not in ("type", "version", "metadata")
        }
        
        return cls(metadata=metadata, **artifact_data)
    
    def compute_hash(self) -> str:
        """
        Tính toán hash cho artifact.
        
        Hash được tính từ serialized content (không bao gồm timestamps).
        Đảm bảo same content → same hash.
        
        Returns:
            SHA-256 hash string (hex encoded)
        """
        # Serialize to deterministic JSON
        data = self.to_dict()
        
        # Remove timestamps from hash computation
        if "metadata" in data:
            data["metadata"].pop("created_at", None)
            data["metadata"].pop("updated_at", None)
        
        # Sort keys for deterministic output
        json_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
        
        return hashlib.sha256(json_str.encode("utf-8")).hexdigest()
    
    def validate(self) -> list[str]:
        """
        Validate artifact.
        
        Returns:
            Danh sách error messages (rỗng nếu valid)
        """
        errors: list[str] = []
        
        # Check metadata
        if not self.metadata:
            errors.append("Metadata is required")
        
        return errors


# ============================================================================
# Serialization Utilities
# ============================================================================


def write_artifact(
    artifact: ArtifactBase,
    path: Path | str,
    pretty: bool = True,
) -> None:
    """
    Viết artifact ra file JSON.
    
    Args:
        artifact: Artifact để viết
        path: Đường dẫn file
        pretty: Có format JSON đẹp không
        
    Raises:
        IOError: Nếu không thể write file
        ValueError: Nếu artifact không valid
    """
    # Validate trước khi write
    errors = artifact.validate()
    if errors:
        raise ValueError(f"Artifact validation failed: {'; '.join(errors)}")
    
    # Update timestamp
    artifact.metadata.update_timestamp()
    
    # Convert to dict
    data = artifact.to_dict()
    
    # Write to file
    path_obj = Path(path) if isinstance(path, str) else path
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path_obj, "w", encoding="utf-8") as f:
        if pretty:
            json.dump(data, f, indent=2, ensure_ascii=False)
        else:
            json.dump(data, f, ensure_ascii=False)


def read_artifact(path: Path | str) -> dict[str, Any]:
    """
    Đọc artifact từ file JSON.
    
    Args:
        path: Đường dẫn file
        
    Returns:
        Dictionary representation của artifact
        
    Raises:
        FileNotFoundError: Nếu file không tồn tại
        JSONDecodeError: Nếu file không phải JSON hợp lệ
    """
    path_obj = Path(path) if isinstance(path, str) else path
    
    if not path_obj.exists():
        raise FileNotFoundError(f"Artifact file not found: {path_obj}")
    
    with open(path_obj, "r", encoding="utf-8") as f:
        return json.load(f)


# ============================================================================
# Hash Utilities
# ============================================================================


def compute_content_hash(content: str | bytes) -> str:
    """
    Tính hash cho content.
    
    Args:
        content: Content string hoặc bytes
        
    Returns:
        SHA-256 hash (hex encoded)
    """
    if isinstance(content, str):
        content = content.encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def compute_file_hash(path: Path | str) -> str:
    """
    Tính hash cho file.
    
    Args:
        path: Đường dẫn file
        
    Returns:
        SHA-256 hash (hex encoded)
    """
    path_obj = Path(path) if isinstance(path, str) else path
    with open(path_obj, "rb") as f:
        return compute_content_hash(f.read())