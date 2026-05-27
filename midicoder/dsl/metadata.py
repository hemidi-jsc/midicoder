"""
DSL v1 Metadata Module

Metadata classes for documentation, provenance, and introspection.
Mirrors the ModelMeta pattern from existing DSL v0 schemas.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Version:
    """
    Version information for DSL components.
    
    Attributes:
        major: Major version number
        minor: Minor version number
        patch: Patch version number
        prerelease: Prerelease tag (e.g., "alpha", "beta")
        build_metadata: Build metadata (e.g., git commit)
    """
    major: int = 1
    minor: int = 0
    patch: int = 0
    prerelease: Optional[str] = None
    build_metadata: Optional[str] = None
    
    def __str__(self) -> str:
        """Return version string."""
        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            version += f"-{self.prerelease}"
        if self.build_metadata:
            version += f"+{self.build_metadata}"
        return version
    
    @classmethod
    def parse(cls, version_str: str) -> "Version":
        """
        Parse version string into Version object.
        
        Args:
            version_str: Version string (e.g., "1.0.0", "2.0.0-beta+abc123")
            
        Returns:
            Version object
        """
        # Remove build metadata
        build_metadata = None
        if "+" in version_str:
            version_str, build_metadata = version_str.split("+", 1)
        
        # Remove prerelease
        prerelease = None
        if "-" in version_str:
            version_str, prerelease = version_str.split("-", 1)
        
        # Parse major.minor.patch
        parts = version_str.split(".")
        major = int(parts[0]) if len(parts) > 0 else 0
        minor = int(parts[1]) if len(parts) > 1 else 0
        patch = int(parts[2]) if len(parts) > 2 else 0
        
        return cls(major=major, minor=minor, patch=patch, 
                   prerelease=prerelease, build_metadata=build_metadata)


@dataclass
class SourceLocation:
    """
    Source code location for DSL components.
    
    Used for error reporting and debugging.
    
    Attributes:
        file: Source file path
        line: Line number (1-indexed)
        column: Column number (1-indexed)
        package: Package name
        module: Module name
    """
    file: Optional[str] = None
    line: Optional[int] = None
    column: Optional[int] = None
    package: Optional[str] = None
    module: Optional[str] = None
    
    def __str__(self) -> str:
        """Return location string."""
        parts = []
        if self.file:
            parts.append(self.file)
        if self.line:
            parts.append(f":{self.line}")
        if self.column:
            parts.append(f":{self.column}")
        return "".join(parts) if parts else "<unknown>"


@dataclass
class ComponentMeta:
    """
    Metadata for a DSL component (entity, command, query, etc.).
    
    Provides component-level metadata including source location,
    version tracking, and component relationships.
    
    Attributes:
        name: Component name
        version: Component version
        source: Source location
        dependencies: List of dependency names
        dependents: List of components that depend on this one
        deprecated: Whether this component is deprecated
        deprecation_note: Note explaining deprecation
    """
    name: str
    version: Optional[str] = None
    source: Optional[SourceLocation] = None
    dependencies: list[str] = field(default_factory=list)
    dependents: list[str] = field(default_factory=list)
    deprecated: bool = False
    deprecation_note: Optional[str] = None
    
    def __post_init__(self) -> None:
        """Validate component metadata."""
        if not self.name:
            raise ValueError("ComponentMeta.name is required")


@dataclass
class NodeMeta:
    """
    Metadata for a DSL node (entity, command, query, etc.).
    
    Provides documentation, usage context, and relationship information
    for better IDE support and automated tooling.
    
    Attributes:
        kind: Node type identifier (e.g., "domain.entity", "app.command")
        usage_en: English description of node's purpose and usage
        usage_vi: Vietnamese description (optional, for localization)
        included_by: List of node kinds that can reference this node
        includes: List of node kinds this node can reference
        real_world_examples: Concrete examples for documentation
        visualizers: Tools that can visualize this node type
    """
    kind: str
    usage_en: str
    usage_vi: Optional[str] = None
    included_by: list[str] = field(default_factory=list)
    includes: list[str] = field(default_factory=list)
    real_world_examples: list[str] = field(default_factory=list)
    visualizers: list[str] = field(default_factory=list)
    
    def __post_init__(self) -> None:
        """Validate metadata after initialization."""
        if not self.kind:
            raise ValueError("NodeMeta.kind is required")
        if not self.usage_en:
            raise ValueError("NodeMeta.usage_en is required")


@dataclass
class ManifestMetadata:
    """
    Provenance metadata for a Manifest.
    
    Tracks authorship, creation time, and generation context
    for audit and reproducibility purposes.
    
    Attributes:
        author: Name or email of the author
        organization: Organization name
        created_at: ISO timestamp of creation
        updated_at: ISO timestamp of last update
        version: Manifest version string
        generated_by: Tool/process that generated this manifest
        git_commit: Git commit hash (if applicable)
        description: Human-readable description
        tags: List of tags for categorization
    """
    author: Optional[str] = None
    organization: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    version: Optional[str] = None
    generated_by: Optional[str] = None
    git_commit: Optional[str] = None
    description: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    
    def __post_init__(self) -> None:
        """Set auto-generated fields if not provided."""
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat() + "Z"
        if self.updated_at is None:
            self.updated_at = self.created_at
    
    @classmethod
    def with_timestamp(cls, **kwargs) -> "ManifestMetadata":
        """
        Create metadata with current timestamp.
        
        Args:
            **kwargs: Additional keyword arguments
            
        Returns:
            ManifestMetadata instance
        """
        now = datetime.utcnow().isoformat() + "Z"
        return cls(
            created_at=now,
            updated_at=now,
            **kwargs
        )


@dataclass
class ArtifactSpec:
    """
    Specification for an expected artifact.
    
    Describes what artifacts should be produced by the code generation
    process for this manifest.
    
    Attributes:
        name: Artifact name (e.g., "api_server", "database_schema")
        type: Artifact type (e.g., "code", "config", "schema", "test")
        path: Output path pattern
        description: Human-readable description
        required: Whether this artifact is required
        template: Template name to use for generation (if applicable)
    """
    name: str
    type: str
    path: str
    description: Optional[str] = None
    required: bool = True
    template: Optional[str] = None
    
    def __post_init__(self) -> None:
        """Validate artifact spec."""
        if not self.name:
            raise ValueError("ArtifactSpec.name is required")
        if not self.type:
            raise ValueError("ArtifactSpec.type is required")
        if not self.path:
            raise ValueError("ArtifactSpec.path is required")


@dataclass
class DependencySpec:
    """
    Dependency specification for external packages or internal packs.
    
    Attributes:
        name: Dependency name
        version: Version constraint (e.g., ">=1.0.0", "^2.0")
        optional: Whether this dependency is optional
        source: Source repository or package manager
        description: Human-readable description
    """
    name: str
    version: Optional[str] = None
    optional: bool = False
    source: Optional[str] = None
    description: Optional[str] = None
    
    def __post_init__(self) -> None:
        """Validate dependency spec."""
        if not self.name:
            raise ValueError("DependencySpec.name is required")


@dataclass
class CategoryInfo:
    """
    Category information for a node.
    
    Provides categorization context for nodes like commands, queries, errors.
    
    Attributes:
        category: Category identifier (e.g., "billing.charge")
        description: Category description
        parent_category: Parent category (if hierarchical)
    """
    category: str
    description: Optional[str] = None
    parent_category: Optional[str] = None


@dataclass
class ValidationContext:
    """
    Context for validation operations.
    
    Tracks the current validation state and accumulated results.
    
    Attributes:
        node_id: ID of the node being validated
        parent_id: ID of the parent node (if applicable)
        depth: Current depth in the validation tree
        visited: Set of visited node IDs (for cycle detection)
        errors: Accumulated validation errors
        warnings: Accumulated validation warnings
    """
    node_id: str
    parent_id: Optional[str] = None
    depth: int = 0
    visited: set[str] = field(default_factory=set)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    
    def error(self, message: str) -> None:
        """Add an error to the context."""
        self.errors.append(f"[{self.node_id}] {message}")
    
    def warning(self, message: str) -> None:
        """Add a warning to the context."""
        self.warnings.append(f"[{self.node_id}] {message}")
    
    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0
    
    def is_valid(self) -> bool:
        """Check if validation passed."""
        return not self.has_errors()
    
    def copy_with_node(self, node_id: str) -> "ValidationContext":
        """
        Create a copy of this context for a child node.
        
        Args:
            node_id: ID of the child node
            
        Returns:
            New ValidationContext for the child
        """
        return ValidationContext(
            node_id=node_id,
            parent_id=self.node_id,
            depth=self.depth + 1,
            visited=self.visited.copy(),
        )