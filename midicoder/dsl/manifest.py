"""
DSL v1 Manifest Module

Central manifest for defining a Midicoder project's composition.
Single-pack architecture — all capability packs are CP*.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from .metadata import (
    ArtifactSpec,
    DependencySpec,
    ManifestMetadata,
)


class TargetProfile(Enum):
    """
    Target deployment profile for code generation.

    Determines which templates and configurations to use.
    """
    PROTO = "proto"        # Prototype - minimal setup
    MVP = "mvp"            # Minimum Viable Product
    STARTUP = "startup"    # Startup - scaled for growth
    ENTERPRISE = "enterprise"  # Enterprise - full compliance


class StrictMode(Enum):
    """
    Strictness level for validation and enforcement.
    """
    LENIENT = "lenient"    # Allow missing optional fields
    NORMAL = "normal"      # Standard validation
    STRICT = "strict"      # Enforce all constraints


@dataclass
class TargetConfig:
    """
    Target-specific configuration.

    Overrides and customizations for a specific deployment target.

    Attributes:
        name: Target identifier (e.g., "prod", "staging", "dev")
        environment: Environment name
        config: Target-specific configuration overrides
    """
    name: str
    environment: str
    config: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("TargetConfig.name is required")
        if not self.environment:
            raise ValueError("TargetConfig.environment is required")


@dataclass
class IntegrationSpec:
    """
    External integration specification.

    Describes external services this project integrates with.

    Attributes:
        name: Integration name
        type: Integration type (e.g., "payment", "email", "sms")
        provider: Provider name (e.g., "stripe", "sendgrid")
        auth_type: Authentication type (api_key, oauth2, etc.)
        config: Integration-specific configuration
        required: Whether this integration is required
    """
    name: str
    type: str
    provider: str
    auth_type: str
    config: dict[str, Any] = field(default_factory=dict)
    required: bool = True

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("IntegrationSpec.name is required")
        if not self.type:
            raise ValueError("IntegrationSpec.type is required")
        if not self.provider:
            raise ValueError("IntegrationSpec.provider is required")


@dataclass
class CapabilityPack:
    """
    Capability pack specification.

    References a CP (Capability Pack) from Midicoder library.

    Attributes:
        name: Capability pack identifier (e.g., "CP01", "CP02")
        version: Version constraint (optional)
        config: Pack-specific configuration
    """
    name: str
    version: Optional[str] = None
    config: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("CapabilityPack.name is required")
        if not self.name.startswith("CP"):
            raise ValueError(
                f"Capability pack name must start with 'CP': {self.name}"
            )


@dataclass
class Manifest:
    """
    Root manifest for a Midicoder project.

    Defines the complete composition of a project including:
    - Target profile and strictness level
    - Capability packs (CP*)
    - External integrations
    - Dependencies
    - Expected artifacts

    Example:
        manifest = Manifest(
            version="v1.0.0",
            target_profile=TargetProfile.MVP,
            strict_mode=StrictMode.NORMAL,
            capabilities=[
                CapabilityPack(name="CP01"),
                CapabilityPack(name="CP02"),
            ],
            metadata=ManifestMetadata.with_timestamp(
                author="alice@example.com",
                description="Platform MVP",
            ),
        )
    """
    # ========================================================================
    # Core Fields
    # ========================================================================
    version: str
    target_profile: TargetProfile
    strict_mode: StrictMode = StrictMode.NORMAL

    # ========================================================================
    # Capabilities
    # ========================================================================
    capabilities: list[CapabilityPack] = field(default_factory=list)

    # ========================================================================
    # Metadata
    # ========================================================================
    metadata: ManifestMetadata = field(default_factory=ManifestMetadata)

    # ========================================================================
    # Dependencies
    # ========================================================================
    dependencies: list[DependencySpec] = field(default_factory=list)

    # ========================================================================
    # Integrations
    # ========================================================================
    integrations: list[IntegrationSpec] = field(default_factory=list)

    # ========================================================================
    # Artifacts
    # ========================================================================
    expected_artifacts: list[ArtifactSpec] = field(default_factory=list)

    # ========================================================================
    # Targets
    # ========================================================================
    targets: list[TargetConfig] = field(default_factory=list)

    # ========================================================================
    # Additional Config
    # ========================================================================
    config: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate manifest after initialization."""
        if not self.version:
            raise ValueError("Manifest.version is required")

        # Auto-set metadata timestamps if not provided
        if self.metadata.created_at is None:
            self.metadata = ManifestMetadata.with_timestamp(
                author=self.metadata.author,
                organization=self.metadata.organization,
                version=self.metadata.version,
                generated_by=self.metadata.generated_by,
                git_commit=self.metadata.git_commit,
                description=self.metadata.description,
                tags=self.metadata.tags,
            )

    @classmethod
    def new(
        cls,
        version: str,
        target_profile: TargetProfile,
        **kwargs
    ) -> "Manifest":
        """
        Create a new manifest with auto-generated metadata.

        Args:
            version: Manifest version string
            target_profile: Target deployment profile
            **kwargs: Additional keyword arguments

        Returns:
            New Manifest instance
        """
        return cls(
            version=version,
            target_profile=target_profile,
            metadata=ManifestMetadata.with_timestamp(),
            **kwargs
        )

    def get_capability_names(self) -> list[str]:
        """Get list of capability pack names."""
        return [cp.name for cp in self.capabilities]

    def has_capability(self, name: str) -> bool:
        """Check if a capability pack is included."""
        return any(cp.name == name for cp in self.capabilities)

    def get_artifact_paths(self) -> list[str]:
        """Get list of expected artifact paths."""
        return [art.path for art in self.expected_artifacts]

    def is_strict(self) -> bool:
        """Check if strict mode is enabled."""
        return self.strict_mode == StrictMode.STRICT


# Alias for backward compatibility and explicit naming
DSLManifest = Manifest
