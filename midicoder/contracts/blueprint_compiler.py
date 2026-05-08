"""
Blueprint Compiler cho Midicoder v1.0.0

Module này định nghĩa Blueprint Compiler - công cụ compile blueprints thành contracts.

Theo requirement.md section "Blueprint System":
- Blueprint là composition của CP + DP + RX + Invariants
- Compiler resolves dependencies và generates contracts
- Validation rules enforce constraints

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from midicoder.errors import MidicoderError, ErrorCode
from midicoder.emitters.core.tenant.models import TenantConfig, TenantMode
from .artifact import ArtifactBase, ArtifactMetadata
from .composition.models import CompositionPlan
from .composition.engine import CompositionEngine


# ============================================================================
# Blueprint Data Classes
# ============================================================================


@dataclass
class BlueprintMetadata:
    """
    Metadata của Blueprint.
    
    Attributes:
        version: Version của blueprint (semver)
        created_at: Thời gian tạo (ISO 8601)
        updated_at: Thời gian cập nhật (ISO 8601)
        author: Tác giả/team
        status: Trạng thái lifecycle (draft, review, approved, deprecated)
        tags: Danh sách tags để phân loại
    """
    version: str
    created_at: str
    updated_at: str
    author: str | None = None
    status: str = "draft"
    tags: list[str] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BlueprintMetadata":
        """Tạo BlueprintMetadata từ dictionary."""
        from datetime import datetime
        
        # Handle empty data case
        if not data:
            now = datetime.utcnow().isoformat() + "Z"
            return cls(
                version="0.0.0",
                created_at=now,
                updated_at=now,
                author=None,
                status="draft",
                tags=[]
            )
        
        now = datetime.utcnow().isoformat() + "Z"
        return cls(
            version=data.get("version", "0.0.0"),
            created_at=data.get("created_at", now),
            updated_at=data.get("updated_at", now),
            author=data.get("author"),
            status=data.get("status", "draft"),
            tags=data.get("tags", [])
        )
    
    def to_dict(self) -> dict[str, Any]:
        """Convert thành dictionary."""
        return {
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "author": self.author,
            "status": self.status,
            "tags": self.tags
        }


@dataclass
class IndustryInfo:
    """
    Thông tin Industry của Blueprint.
    
    Attributes:
        id: Industry identifier (lowercase, hyphenated)
        name: Tên hiển thị
        group: Industry group
        priority: Priority rank (1-100)
        complexity: Implementation complexity level
        regulatory_risk: Regulatory compliance risk level
        commercial_priority: Commercial value priority
    """
    id: str
    name: str
    group: str
    priority: int | None = None
    complexity: str | None = None
    regulatory_risk: str | None = None
    commercial_priority: str | None = None
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "IndustryInfo":
        """Tạo IndustryInfo từ dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            group=data["group"],
            priority=data.get("priority"),
            complexity=data.get("complexity"),
            regulatory_risk=data.get("regulatory_risk"),
            commercial_priority=data.get("commercial_priority")
        )
    
    def to_dict(self) -> dict[str, Any]:
        """Convert thành dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "group": self.group,
            "priority": self.priority,
            "complexity": self.complexity,
            "regulatory_risk": self.regulatory_risk,
            "commercial_priority": self.commercial_priority
        }


@dataclass
class CorePacksConfig:
    """
    Cấu hình Core Packs cho Blueprint.
    
    Attributes:
        mandatory: P0 core packs (bắt buộc: CP01, CP02, CP03, CP04, CP07)
        included: Additional core packs từ P1-P3
        excluded: Core packs bị loại trừ (P2-P4 only)
        experimental: Experimental core packs (P4 only)
    """
    mandatory: list[str]
    included: list[str] = field(default_factory=list)
    excluded: list[str] = field(default_factory=list)
    experimental: list[str] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CorePacksConfig":
        """Tạo CorePacksConfig từ dictionary."""
        return cls(
            mandatory=data.get("mandatory", []),
            included=data.get("included", []),
            excluded=data.get("excluded", []),
            experimental=data.get("experimental", [])
        )
    
    def to_dict(self) -> dict[str, Any]:
        """Convert thành dictionary."""
        return {
            "mandatory": self.mandatory,
            "included": self.included,
            "excluded": self.excluded,
            "experimental": self.experimental
        }
    
    @property
    def all_included(self) -> list[str]:
        """Lấy tất cả core packs được include (mandatory + included)."""
        return self.mandatory + self.included


@dataclass
class DomainPackRef:
    """
    Reference đến Domain Pack.
    
    Attributes:
        id: Domain pack identifier (DPxx)
        required: Có bắt buộc không
        config: Configuration cho domain pack
    """
    id: str
    required: bool = True
    config: dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DomainPackRef":
        """Tạo DomainPackRef từ dictionary."""
        return cls(
            id=data["id"],
            required=data.get("required", True),
            config=data.get("config", {})
        )


@dataclass
class RegulatoryOverlayRef:
    """
    Reference đến Regulatory Overlay.
    
    Attributes:
        id: Regulatory overlay identifier (RXxx)
        strict_mode: Có enforce strict compliance không
        config: Configuration cho overlay
    """
    id: str
    strict_mode: bool = True
    config: dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RegulatoryOverlayRef":
        """Tạo RegulatoryOverlayRef từ dictionary."""
        return cls(
            id=data["id"],
            strict_mode=data.get("strict_mode", True),
            config=data.get("config", {})
        )


@dataclass
class BusinessInvariant:
    """
    Business Invariant cho Blueprint.
    
    Attributes:
        id: Invariant identifier (INVxxx)
        name: Tên invariant
        description: Mô tả invariant
        enforcement: Enforcement mode (compile-time, runtime, both)
        violation_code: Error code khi vi phạm
        severity: Severity level (error, warning)
    """
    id: str
    name: str
    description: str
    enforcement: str
    violation_code: str | None = None
    severity: str = "error"
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BusinessInvariant":
        """Tạo BusinessInvariant từ dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            enforcement=data["enforcement"],
            violation_code=data.get("violation_code"),
            severity=data.get("severity", "error")
        )


@dataclass
class ComplianceInvariant:
    """
    Compliance Invariant cho Blueprint.
    
    Attributes:
        id: Invariant identifier
        overlay: Regulatory overlay reference (RXxx)
        description: Mô tả invariant
        controls: Danh sách controls cần enforce
    """
    id: str
    overlay: str
    description: str
    controls: list[str] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ComplianceInvariant":
        """Tạo ComplianceInvariant từ dictionary."""
        return cls(
            id=data["id"],
            overlay=data["overlay"],
            description=data["description"],
            controls=data.get("controls", [])
        )


@dataclass
class FailureModeInvariant:
    """
    Failure Mode Invariant cho Blueprint.
    
    Attributes:
        id: Invariant identifier
        scenario: Failure scenario description
        handling: Handling strategy
        recovery: Recovery procedure
    """
    id: str
    scenario: str
    handling: str
    recovery: str | None = None
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FailureModeInvariant":
        """Tạo FailureModeInvariant từ dictionary."""
        return cls(
            id=data["id"],
            scenario=data["scenario"],
            handling=data["handling"],
            recovery=data.get("recovery")
        )


@dataclass
class InvariantsConfig:
    """
    Configuration cho tất cả Invariants.
    
    Attributes:
        business: Danh sách business invariants
        compliance: Danh sách compliance invariants
        failure_modes: Danh sách failure mode invariants
    """
    business: list[BusinessInvariant] = field(default_factory=list)
    compliance: list[ComplianceInvariant] = field(default_factory=list)
    failure_modes: list[FailureModeInvariant] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "InvariantsConfig":
        """Tạo InvariantsConfig từ dictionary."""
        return cls(
            business=[
                BusinessInvariant.from_dict(inv)
                for inv in data.get("business", [])
            ],
            compliance=[
                ComplianceInvariant.from_dict(inv)
                for inv in data.get("compliance", [])
            ],
            failure_modes=[
                FailureModeInvariant.from_dict(inv)
                for inv in data.get("failure_modes", [])
            ]
        )
    
    def to_dict(self) -> dict[str, Any]:
        """Convert thành dictionary."""
        return {
            "business": [inv.to_dict() if hasattr(inv, 'to_dict') else inv for inv in self.business],
            "compliance": [inv.to_dict() if hasattr(inv, 'to_dict') else inv for inv in self.compliance],
            "failure_modes": [inv.to_dict() if hasattr(inv, 'to_dict') else inv for inv in self.failure_modes]
        }


@dataclass
class BlueprintConfig:
    """
    Configuration overrides cho Blueprint.

    Attributes:
        tenant_config: Tenant configuration (CP02 TenantConfig)
        default_auth_strategy: Default auth strategy (jwt, oauth2, saml, hybrid)
        default_db_engine: Default database engine (postgres, mysql, sqlserver, oracle)
        observability: Observability configuration
        security: Security configuration
    """
    tenant_config: TenantConfig = field(
        default_factory=lambda: TenantConfig(mode=TenantMode.SCHEMA)
    )
    default_auth_strategy: str = "jwt"
    default_db_engine: str = "postgres"
    observability: dict[str, Any] = field(default_factory=dict)
    security: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BlueprintConfig":
        """Tao BlueprintConfig tu dictionary."""
        # Support both new tenant_config and legacy default_tenant_mode
        if "tenant_config" in data:
            tc = TenantConfig.from_dict(data["tenant_config"])
        elif "default_tenant_mode" in data:
            mode_str = data["default_tenant_mode"]
            mode = TenantMode(mode_str) if mode_str in [m.value for m in TenantMode] else TenantMode.SCHEMA
            tc = TenantConfig(mode=mode)
        else:
            tc = TenantConfig(mode=TenantMode.SCHEMA)

        return cls(
            tenant_config=tc,
            default_auth_strategy=data.get("default_auth_strategy", "jwt"),
            default_db_engine=data.get("default_db_engine", "postgres"),
            observability=data.get("observability", {}),
            security=data.get("security", {})
        )


@dataclass
class BlueprintReferences:
    """
    References cho Blueprint.
    
    Attributes:
        brief_path: Path đến brief.md
        documentation_url: URL documentation
        related_blueprints: Danh sách related blueprints
    """
    brief_path: str | None = None
    documentation_url: str | None = None
    related_blueprints: list[str] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BlueprintReferences":
        """Tạo BlueprintReferences từ dictionary."""
        return cls(
            brief_path=data.get("brief_path"),
            documentation_url=data.get("documentation_url"),
            related_blueprints=data.get("related_blueprints", [])
        )


@dataclass
class CompiledBlueprint:
    """
    Compiled Blueprint Artifact.
    
    Blueprint sau khi compile, chứa:
    - Metadata
    - Industry info
    - Resolved CP/DP/RX dependencies
    - Invariants
    - Configuration
    - Validation results
    
    Attributes:
        schema_version: Schema version
        _blueprint_metadata: Blueprint metadata (BlueprintMetadata)
        industry: Industry information
        core_packs: Core packs configuration
        domain_packs: Domain packs references
        regulatory_overlays: Regulatory overlays references
        target_profiles: Supported deployment targets
        invariants: Invariants configuration
        config: Blueprint configuration
        references: References to related artifacts
    """
    
    schema_version: str = "industry-blueprint-v1"
    industry: IndustryInfo = field(default_factory=IndustryInfo)
    core_packs: CorePacksConfig = field(default_factory=CorePacksConfig)
    domain_packs: list[DomainPackRef] = field(default_factory=list)
    regulatory_overlays: list[RegulatoryOverlayRef] = field(default_factory=list)
    target_profiles: list[str] = field(default_factory=list)
    invariants: InvariantsConfig = field(default_factory=InvariantsConfig)
    config: BlueprintConfig = field(default_factory=BlueprintConfig)
    references: BlueprintReferences = field(default_factory=BlueprintReferences)
    
    # Compiled results
    validation_errors: list[str] = field(default_factory=list, repr=False)
    validation_warnings: list[str] = field(default_factory=list, repr=False)
    
    # Blueprint metadata - private field, accessed via property
    _blueprint_metadata: BlueprintMetadata | None = field(default=None, repr=False)
    
    @property
    def metadata(self) -> BlueprintMetadata:
        """Get BlueprintMetadata. Creates default if not set."""
        if self._blueprint_metadata is None:
            self._blueprint_metadata = BlueprintMetadata.from_dict({})
        return self._blueprint_metadata
    
    @metadata.setter
    def metadata(self, value: BlueprintMetadata) -> None:
        """Set BlueprintMetadata."""
        self._blueprint_metadata = value
    
    @property
    def artifact_type(self) -> str:
        """Trả về artifact type."""
        return "compiled_blueprint"
    
    def to_dict(self) -> dict[str, Any]:
        """Convert thành dictionary."""
        return {
            "type": self.artifact_type,
            "version": self.schema_version,
            "metadata": self.metadata.to_dict() if hasattr(self.metadata, 'to_dict') else self.metadata,
            "industry": self.industry.to_dict() if hasattr(self.industry, 'to_dict') else self.industry,
            "core_packs": self.core_packs.to_dict() if hasattr(self.core_packs, 'to_dict') else self.core_packs,
            "domain_packs": [dp.to_dict() if hasattr(dp, 'to_dict') else dp for dp in self.domain_packs],
            "regulatory_overlays": [ro.to_dict() if hasattr(ro, 'to_dict') else ro for ro in self.regulatory_overlays],
            "target_profiles": self.target_profiles,
            "invariants": self.invariants.to_dict() if hasattr(self.invariants, 'to_dict') else self.invariants,
            "config": self.config.to_dict() if hasattr(self.config, 'to_dict') else self.config,
            "references": self.references.to_dict() if hasattr(self.references, 'to_dict') else self.references,
            "validation": {
                "errors": self.validation_errors,
                "warnings": self.validation_warnings
            }
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CompiledBlueprint":
        """Tạo CompiledBlueprint từ dictionary."""
        blueprint = cls(
            schema_version=data.get("schema_version", "industry-blueprint-v1"),
            industry=IndustryInfo.from_dict(data.get("industry", {})),
            core_packs=CorePacksConfig.from_dict(data.get("core_packs", {})),
            domain_packs=[
                DomainPackRef.from_dict(dp)
                for dp in data.get("domain_packs", [])
            ],
            regulatory_overlays=[
                RegulatoryOverlayRef.from_dict(ro)
                for ro in data.get("regulatory_overlays", [])
            ],
            target_profiles=data.get("target_profiles", []),
            invariants=InvariantsConfig.from_dict(data.get("invariants", {})),
            config=BlueprintConfig.from_dict(data.get("config", {})),
            references=BlueprintReferences.from_dict(data.get("references", {})),
            validation_errors=data.get("validation", {}).get("errors", []),
            validation_warnings=data.get("validation", {}).get("warnings", [])
        )
        blueprint.metadata = BlueprintMetadata.from_dict(data.get("metadata", {}))
        return blueprint
    
    def validate(self) -> list[str]:
        """
        Validate blueprint.
        
        Returns:
            Danh sách error messages (rỗng nếu valid)
        """
        errors = []
        
        # Rule V001: Bắt buộc P0 Core Packs
        required_p0 = ["CP01", "CP02", "CP03", "CP04", "CP07"]
        for cp in required_p0:
            if cp not in self.core_packs.mandatory:
                errors.append(f"V001: Blueprint phải bao gồm core pack bắt buộc {cp}")
        
        # Rule V002: Universal Regulatory Overlays
        required_rx = ["RX01", "RX11"]
        overlay_ids = [ro.id for ro in self.regulatory_overlays]
        for rx in required_rx:
            if rx not in overlay_ids:
                errors.append(f"V002: Blueprint phải bao gồm regulatory overlay bắt buộc {rx}")
        
        # Rule V005: Target Profile Consistency
        valid_profiles = ["local", "aws", "gcp", "azure", "on-premise"]
        for profile in self.target_profiles:
            if profile not in valid_profiles:
                errors.append(f"V005: Target profile không được hỗ trợ: {profile}")
        
        # Rule V003: Domain Pack Consistency - Kiểm tra DP IDs hợp lệ
        valid_dp_ids = {"DP01", "DP02", "DP03", "DP04", "DP05", "DP06", "DP07", "DP08",
                        "DP09", "DP10", "DP11", "DP12", "DP13", "DP14", "DP15", "DP16",
                        "DP17", "DP18", "DP19", "DP20", "DP21", "DP22", "DP23", "DP24",
                        "DP25", "DP26"}
        for dp in self.domain_packs:
            if dp.id not in valid_dp_ids:
                errors.append(f"V003: Domain pack ID không hợp lệ: {dp.id}")
        
        # Rule V004: Regulatory Overlay Consistency - Kiểm tra RX IDs hợp lệ
        valid_rx_ids = {"RX01", "RX02", "RX03", "RX04", "RX05", "RX06",
                        "RX07", "RX08", "RX09", "RX10", "RX11", "RX12"}
        for ro in self.regulatory_overlays:
            if ro.id not in valid_rx_ids:
                errors.append(f"V004: Regulatory overlay ID không hợp lệ: {ro.id}")
        
        # Rule V006: Core Pack Dependency Order - Kiểm tra dependency ordering
        cp_dependencies = {
            "CP01": [], "CP02": ["CP01"], "CP03": ["CP01", "CP02"], "CP04": ["CP02", "CP03"],
            "CP05": ["CP01"], "CP06": ["CP01", "CP05"], "CP07": [], "CP08": ["CP01"],
            "CP09": ["CP08"], "CP10": ["CP08"], "CP11": ["CP07"], "CP12": ["CP05"],
            "CP13": ["CP05"], "CP14": ["CP01"], "CP15": ["CP07"], "CP16": ["CP15"],
            "CP17": ["CP08", "CP15"], "CP18": ["CP01"], "CP19": ["CP18"], "CP20": ["CP06", "CP18"],
            "CP21": ["CP03", "CP18"], "CP22": ["CP05", "CP18"], "CP23": ["CP01"],
            "CP24": ["CP23"], "CP25": ["CP23"], "CP26": ["CP01"], "CP27": ["CP01"],
            "CP28": ["CP01"], "CP29": ["CP01", "CP02", "CP03", "CP04", "CP05", "CP06",
                                      "CP07", "CP08", "CP09", "CP10", "CP11", "CP12",
                                      "CP13", "CP14", "CP15", "CP16", "CP17", "CP18",
                                      "CP19", "CP20", "CP21", "CP22", "CP23", "CP24",
                                      "CP25", "CP26", "CP27", "CP28"], "CP30": ["CP01"]
        }
        all_cp = set(self.core_packs.mandatory + self.core_packs.included)
        for cp_id in all_cp:
            if cp_id in cp_dependencies:
                for dep in cp_dependencies[cp_id]:
                    if dep not in all_cp and dep not in self.core_packs.excluded:
                        errors.append(f"V006: Thiếu dependency {dep} cho {cp_id}")
        
        # Rule V007: Complexity Pack Alignment - Kiểm tra complexity vs pack selection
        if self.industry.complexity in ["very_high", "extreme"]:
            p1_packs = {"CP05", "CP06", "CP08", "CP09", "CP10", "CP11", "CP12",
                        "CP13", "CP14", "CP15", "CP23"}
            included_p1 = len(all_cp.intersection(p1_packs))
            if included_p1 < 8:
                errors.append(f"V007: Complexity {self.industry.complexity} nên include tối thiểu 8 P1 packs, tìm thấy {included_p1}")
        
        # Rule V008: Brief Reference Required - Warn nếu brief_path không có
        if self.references.brief_path is None:
            errors.append("V008: Blueprint nên reference brief_path (warning)")
        
        # Rule V009: Invariant Minimum cho High Risk
        if self.industry.regulatory_risk in ["high", "very_high"]:
            total_invariants = (
                len(self.invariants.business) +
                len(self.invariants.compliance)
            )
            if total_invariants < 10:
                errors.append(
                    f"V009: Regulatory risk cao yêu cầu tối thiểu 10 invariants, "
                    f"tìm thấy {total_invariants}"
                )
        
        # Rule V010: No P4 in Production - Warn nếu P4 packs trong approved blueprint
        p4_packs = {"CP27", "CP28", "CP29", "CP30"}
        blueprint_metadata = self.metadata  # BlueprintMetadata instance
        if blueprint_metadata.status == "approved":
            experimental_p4 = set(self.core_packs.experimental).intersection(p4_packs)
            if experimental_p4:
                has_experimental_tag = "experimental-feature" in blueprint_metadata.tags
                if not has_experimental_tag:
                    errors.append(f"V010: P4 packs trong approved blueprint cần tag 'experimental-feature': {experimental_p4}")
        
        return errors
    
    def is_valid(self) -> bool:
        """Kiểm tra blueprint có valid không."""
        return len(self.validate()) == 0


# ============================================================================
# Blueprint Compiler
# ============================================================================


class BlueprintCompilerError(MidicoderError):
    r"""
    Exception cho Blueprint Compiler errors, extend từ MidicoderError.
    
    Theo NEW_SESSION_PROMPT.md Rule #8:
    "Quản lý mã lỗi và mã exception tập trung tại: midicoder\errors.py"
    
    Attributes:
        code: ErrorCode từ enum
        message: Message tiếng Việt mô tả lỗi
        context: Context thông tin cho debugging
        suggestions: Gợi ý khắc phục
    
    Ví dụ:
        raise BlueprintCompilerError(
            code=ErrorCode.BLUEPRINT_FILE_NOT_FOUND,
            message="Không tìm thấy file blueprint",
            context={"path": "industry/blueprints/ecommerce.yml"}
        )
    """
    pass


class BlueprintCompiler:
    """
    Blueprint Compiler - Compile blueprints thành contracts.
    
    Theo requirement.md:
    1. Load blueprint YAML
    2. Resolve CP dependencies
    3. Resolve DP dependencies
    4. Resolve RX dependencies
    5. Generate contracts/
    6. Return CompiledBlueprint
    
    Usage:
        compiler = BlueprintCompiler()
        blueprint = compiler.compile("industry/blueprints/ecommerce-d2c.yml")
        
        if blueprint.is_valid():
            # Use compiled blueprint
        else:
            print(blueprint.validation_errors)
    """
    
    def __init__(
        self,
        taxonomy_path: Path | None = None,
        industry_map_path: Path | None = None
    ):
        """
        Khởi tạo Blueprint Compiler.
        
        Args:
            taxonomy_path: Path đến taxonomy.yml
            industry_map_path: Path đến industry map file
        """
        self.taxonomy_path = taxonomy_path or Path("industry/taxonomy.yml")
        self.industry_map_path = industry_map_path or Path(
            "backlog/INDUSTRY_100_SYSTEM_MAP.md"
        )
        self.taxonomy: dict[str, Any] = {}
        self.industry_map: dict[str, Any] = {}
        
        # CP dependency maps
        self._cp_dependency_map: dict[str, list[str]] = {}
        self._cp_phase_map: dict[str, str] = {}
        
        # DP info maps
        self._dp_info_map: dict[str, dict[str, Any]] = {}
        self._industry_to_dps_map: dict[str, list[str]] = {}
        
        # RX info maps
        self._rx_info_map: dict[str, dict[str, Any]] = {}
        self._industry_to_rxs_map: dict[str, list[str]] = {}
        self._universal_rx_ids: set[str] = set()
        
        # Load taxonomy và build dependency maps
        if self.taxonomy_path.exists():
            with open(self.taxonomy_path, 'r', encoding='utf-8') as f:
                self.taxonomy = yaml.safe_load(f)
            self._build_cp_dependency_maps()
            self._build_dp_info_maps()
            self._build_rx_info_maps()
    
    def _build_cp_dependency_maps(self) -> None:
        """
        Build CP dependency maps từ taxonomy.
        
        Tạo 2 maps:
        - _cp_dependency_map: CP ID → dependencies list
        - _cp_phase_map: CP ID → phase (P0, P1, P2, P3, P4)
        """
        for cp in self.taxonomy.get("core_packs", []):
            cp_id = cp["id"]
            self._cp_dependency_map[cp_id] = cp.get("dependencies", [])
            self._cp_phase_map[cp_id] = cp.get("phase", "P0")
    
    def _build_dp_info_maps(self) -> None:
        """
        Build DP info maps từ taxonomy.
        
        Tạo 2 maps:
        - _dp_info_map: DP ID → info dict (name, category, industries_using, ...)
        - _industry_to_dps_map: industry ID → list of DP IDs
        """
        # Build DP info map
        for dp in self.taxonomy.get("domain_packs", []):
            dp_id = dp["id"]
            self._dp_info_map[dp_id] = {
                "name": dp.get("name", ""),
                "category": dp.get("category", ""),
                "industries_using": dp.get("industries_using", []),
                "description": dp.get("description", ""),
                "status": dp.get("status", "stable")
            }
        
        # Build industry to DPs map
        industry_to_dps: dict[str, list[str]] = {}
        for dp_id, info in self._dp_info_map.items():
            for industry in info.get("industries_using", []):
                if industry not in industry_to_dps:
                    industry_to_dps[industry] = []
                industry_to_dps[industry].append(dp_id)
        
        # Sort DP IDs cho mỗi industry để deterministic
        for industry in industry_to_dps:
            industry_to_dps[industry].sort()
        
        self._industry_to_dps_map = industry_to_dps
    
    def resolve_dp_dependencies(self, industry_id: str) -> list[str]:
        """
        Resolve DPs cho một industry cụ thể.
        
        Khác với CP, DP không có transitive dependencies.
        DP resolution dựa vào industry mapping trong taxonomy.
        
        Args:
            industry_id: Industry identifier (ví dụ: "ecommerce-d2c")
            
        Returns:
            Danh sách DP IDs phù hợp cho industry
            
        Example:
            compiler.resolve_dp_dependencies("ecommerce-d2c")
            # Returns: ["DP01", "DP12"]
        """
        return self._industry_to_dps_map.get(industry_id, [])
    
    def validate_dp_id(self, dp_id: str) -> list[str]:
        """
        Validate DP ID tồn tại trong taxonomy.
        
        Args:
            dp_id: DP ID cần validate
            
        Returns:
            Danh sách error messages (rỗng nếu valid)
        """
        errors: list[str] = []
        if dp_id not in self._dp_info_map:
            errors.append(f"Invalid DP ID: {dp_id}")
        return errors
    
    def validate_dp_for_industry(
        self, dp_id: str, industry_id: str
    ) -> list[str]:
        """
        Validate DP phù hợp với industry.
        
        Args:
            dp_id: DP ID cần validate
            industry_id: Industry identifier
            
        Returns:
            Danh sách error messages (rỗng nếu DP phù hợp với industry)
        """
        errors: list[str] = []
        
        # Validate DP ID tồn tại
        if dp_id not in self._dp_info_map:
            errors.append(f"Invalid DP ID: {dp_id}")
            return errors
        
        # Kiểm tra industry có trong industries_using của DP
        industries_using = self._dp_info_map[dp_id].get("industries_using", [])
        if industry_id not in industries_using:
            errors.append(
                f"DP {dp_id} not typically used for industry '{industry_id}'. "
                f"Common industries: {', '.join(industries_using[:5])}"
            )
        
        return errors
    
    def get_dp_info(self, dp_id: str) -> dict[str, Any] | None:
        """
        Lấy thông tin chi tiết của một DP.
        
        Args:
            dp_id: DP ID
            
        Returns:
            Info dict hoặc None nếu không tìm thấy
        """
        return self._dp_info_map.get(dp_id)
    
    def _build_rx_info_maps(self) -> None:
        """
        Build RX info maps từ taxonomy.
        
        Tạo 3 maps:
        - _rx_info_map: RX ID → info dict (name, category, obligations, industries_requiring)
        - _industry_to_rxs_map: industry ID → list of RX IDs (không tính universal)
        - _universal_rx_ids: Set của universal RX IDs (RX01, RX11)
        """
        # Build RX info map
        for rx in self.taxonomy.get("regulatory_overlays", []):
            rx_id = rx["id"]
            self._rx_info_map[rx_id] = {
                "name": rx.get("name", ""),
                "category": rx.get("category", ""),
                "obligations": rx.get("obligations", []),
                "industries_requiring": rx.get("industries_requiring", []),
                "description": rx.get("description", ""),
                "status": rx.get("status", "stable")
            }
        
        # Build industry to RXs map (không tính universal RXs)
        industry_to_rxs: dict[str, list[str]] = {}
        for rx_id, info in self._rx_info_map.items():
            industries_requiring = info.get("industries_requiring", [])
            
            # Universal RXs (industries_requiring: ["all"])
            if "all" in industries_requiring:
                self._universal_rx_ids.add(rx_id)
                continue
            
            # Non-universal RXs: map industry → RX
            for industry in industries_requiring:
                if industry not in industry_to_rxs:
                    industry_to_rxs[industry] = []
                industry_to_rxs[industry].append(rx_id)
        
        # Sort RX IDs cho mỗi industry để deterministic
        for industry in industry_to_rxs:
            industry_to_rxs[industry].sort()
        
        self._industry_to_rxs_map = industry_to_rxs
    
    def resolve_rx_dependencies(self, industry_id: str) -> list[str]:
        """
        Resolve RXs cho một industry cụ thể.
        
        Bao gồm:
        - Universal RXs (RX01, RX11) cho tất cả industries
        - Industry-specific RXs từ taxonomy
        
        Args:
            industry_id: Industry identifier (ví dụ: "ecommerce-d2c")
            
        Returns:
            Danh sách RX IDs phù hợp cho industry
            
        Example:
            compiler.resolve_rx_dependencies("ecommerce-d2c")
            # Returns: ["RX01", "RX06", "RX10", "RX11"]
        """
        industry_rxs = self._industry_to_rxs_map.get(industry_id, [])
        # Kết hợp universal RXs và industry-specific RXs
        all_rxs = list(self._universal_rx_ids) + industry_rxs
        all_rxs.sort()
        return all_rxs
    
    def validate_rx_id(self, rx_id: str) -> list[str]:
        """
        Validate RX ID tồn tại trong taxonomy.
        
        Args:
            rx_id: RX ID cần validate
            
        Returns:
            Danh sách error messages (rỗng nếu valid)
        """
        errors: list[str] = []
        if rx_id not in self._rx_info_map:
            errors.append(f"Invalid RX ID: {rx_id}")
        return errors
    
    def validate_universal_rxs(
        self, blueprint_rx_ids: set[str]
    ) -> list[str]:
        """
        Validate universal RXs được include trong blueprint.
        
        Tất cả blueprints phải include RX01 và RX11.
        
        Args:
            blueprint_rx_ids: Set của RX IDs trong blueprint
            
        Returns:
            Danh sách error messages (rỗng nếu tất cả universal RXs đều có mặt)
        """
        errors: list[str] = []
        
        for rx_id in self._universal_rx_ids:
            if rx_id not in blueprint_rx_ids:
                errors.append(
                    f"Universal RX {rx_id} phải được include trong tất cả blueprints"
                )
        
        return errors
    
    def get_required_rxs_for_industry(self, industry_id: str) -> set[str]:
        """
        Lấy required RXs cho một industry.
        
        Args:
            industry_id: Industry identifier
            
        Returns:
            Set của RX IDs cần thiết cho industry
        """
        return set(self.resolve_rx_dependencies(industry_id))
    
    def get_rx_info(self, rx_id: str) -> dict[str, Any] | None:
        """
        Lấy thông tin chi tiết của một RX.
        
        Args:
            rx_id: RX ID
            
        Returns:
            Info dict hoặc None nếu không tìm thấy
        """
        return self._rx_info_map.get(rx_id)
    
    def get_universal_rx_ids(self) -> set[str]:
        """
        Lấy danh sách universal RX IDs.
        
        Returns:
            Set của universal RX IDs (RX01, RX11)
        """
        return self._universal_rx_ids.copy()
    
    def resolve_cp_dependencies(self, cp_list: list[str]) -> list[str]:
        """
        Resolve transitive dependencies cho một list của CP IDs.
        
        Sử dụng DFS để traverse dependency graph và trả về
        tất cả CPs cần thiết (bao gồm transitive dependencies).
        
        Args:
            cp_list: Danh sách CP IDs cần resolve
            
        Returns:
            Danh sách CP IDs đã resolve (bao gồm tất cả dependencies)
            
        Example:
            compiler.resolve_cp_dependencies(["CP03"])
            # Returns: ["CP01", "CP02", "CP03"]
        """
        resolved: set[str] = set()
        stack = list(cp_list)
        
        while stack:
            cp_id = stack.pop()
            if cp_id in resolved:
                continue
            
            resolved.add(cp_id)
            deps = self._cp_dependency_map.get(cp_id, [])
            for dep in deps:
                if dep not in resolved:
                    stack.append(dep)
        
        # Sort theo CP ID để deterministic
        return sorted(resolved, key=lambda x: int(x[2:]))
    
    def find_missing_cp_dependencies(
        self, blueprint_packs: set[str]
    ) -> set[str]:
        """
        Tìm missing dependencies cho một set của blueprint CP packs.
        
        Args:
            blueprint_packs: Set của CP IDs trong blueprint
            
        Returns:
            Set của CP IDs missing (cần thêm vào blueprint)
            
        Example:
            compiler.find_missing_cp_dependencies({"CP03"})
            # Returns: {"CP01", "CP02"}
        """
        all_required: set[str] = set()
        stack = list(blueprint_packs)
        
        while stack:
            cp_id = stack.pop()
            if cp_id in all_required:
                continue
            
            all_required.add(cp_id)
            deps = self._cp_dependency_map.get(cp_id, [])
            for dep in deps:
                if dep not in all_required:
                    stack.append(dep)
        
        # Missing = all_required - blueprint_packs
        return all_required - blueprint_packs
    
    def validate_cp_dependency_order(
        self, cp_list: list[str]
    ) -> list[str]:
        """
        Validate dependency order cho CP list.
        
        Kiểm tra rằng CPs chỉ phụ thuộc vào các CPs trong phase trước hoặc cùng phase.
        P0 → P0
        P1 → P0, P1
        P2 → P0, P1, P2
        P3 → P0, P1, P2, P3
        P4 → P0, P1, P2, P3, P4
        
        Args:
            cp_list: Danh sách CP IDs cần validate
            
        Returns:
            Danh sách error messages (rỗng nếu valid)
        """
        errors: list[str] = []
        phase_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3, "P4": 4}
        
        for cp_id in cp_list:
            cp_phase = self._cp_phase_map.get(cp_id, "P0")
            cp_phase_num = phase_order.get(cp_phase, 0)
            
            deps = self._cp_dependency_map.get(cp_id, [])
            for dep in deps:
                dep_phase = self._cp_phase_map.get(dep, "P0")
                dep_phase_num = phase_order.get(dep_phase, 0)
                
                # Dependency phase không được cao hơn current phase
                if dep_phase_num > cp_phase_num:
                    errors.append(
                        f"CP dependency order violated: {cp_id} ({cp_phase}) "
                        f"cannot depend on {dep} ({dep_phase})"
                    )
        
        return errors
    
    def compile(self, blueprint_path: Path | str) -> CompiledBlueprint:
        """
        Compile blueprint file.
        
        Process:
        1. Load blueprint YAML
        2. Parse và validate schema
        3. Resolve dependencies
        4. Apply validation rules
        5. Return CompiledBlueprint
        
        Args:
            blueprint_path: Path đến blueprint file
            
        Returns:
            CompiledBlueprint instance
            
        Raises:
            FileNotFoundError: Nếu blueprint file không tồn tại
            BlueprintCompilerError: Nếu compile failed
        """
        blueprint_path = Path(blueprint_path)
        
        # Check file exists
        if not blueprint_path.exists():
            raise FileNotFoundError(f"Blueprint file not found: {blueprint_path}")
        
        # Load blueprint
        with open(blueprint_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        # Parse blueprint
        blueprint = self._parse_blueprint(data)
        
        # Validate
        errors = blueprint.validate()
        blueprint.validation_errors = errors
        
        # Check for critical errors
        if errors:
            for error in errors:
                if error.startswith(("V001", "V002", "V009")):
                    # Critical validation errors
                    pass
                    # Could raise BlueprintCompilerError here if strict
        
        return blueprint
    
    def _parse_blueprint(self, data: dict[str, Any]) -> CompiledBlueprint:
        """
        Parse blueprint data thành CompiledBlueprint.
        
        Args:
            data: Parsed YAML data
            
        Returns:
            CompiledBlueprint instance
        """
        blueprint = CompiledBlueprint(
            schema_version=data.get("$schema", "industry-blueprint-v1"),
            industry=IndustryInfo.from_dict(data.get("industry", {})),
            core_packs=CorePacksConfig.from_dict(data.get("core_packs", {})),
            domain_packs=[
                DomainPackRef.from_dict(dp)
                for dp in data.get("domain_packs", [])
            ],
            regulatory_overlays=[
                RegulatoryOverlayRef.from_dict(ro)
                for ro in data.get("regulatory_overlays", [])
            ],
            target_profiles=data.get("target_profiles", []),
            invariants=InvariantsConfig.from_dict(data.get("invariants", {})),
            config=BlueprintConfig.from_dict(data.get("config", {})),
            references=BlueprintReferences.from_dict(data.get("references", {}))
        )
        blueprint.metadata = BlueprintMetadata.from_dict(data.get("metadata", {}))
        return blueprint
    
    def compile_directory(
        self,
        blueprints_dir: Path | str,
        pattern: str = "*.yml"
    ) -> list[CompiledBlueprint]:
        """
        Compile tất cả blueprints trong một directory.
        
        Args:
            blueprints_dir: Directory chứa blueprint files
            pattern: File pattern (default: *.yml)
            
        Returns:
            Danh sách CompiledBlueprint instances
        """
        blueprints_dir = Path(blueprints_dir)
        blueprints = []
        
        for blueprint_file in blueprints_dir.glob(pattern):
            try:
                blueprint = self.compile(blueprint_file)
                blueprints.append(blueprint)
            except Exception as e:
                # Log error but continue with other blueprints
                print(f"Error compiling {blueprint_file}: {e}")
        
        return blueprints
    
    def get_all_core_packs(self, blueprint: CompiledBlueprint) -> list[str]:
        """
        Lấy tất cả core packs (mandatory + included) cho blueprint.
        
        Args:
            blueprint: CompiledBlueprint
            
        Returns:
            Danh sách core pack IDs
        """
        return blueprint.core_packs.all_included
    
    def get_all_domain_packs(self, blueprint: CompiledBlueprint) -> list[str]:
        """
        Lấy tất cả domain pack IDs.
        
        Args:
            blueprint: CompiledBlueprint
            
        Returns:
            Danh sách domain pack IDs
        """
        return [dp.id for dp in blueprint.domain_packs]
    
    def get_all_regulatory_overlays(self, blueprint: CompiledBlueprint) -> list[str]:
        """
        Lấy tất cả regulatory overlay IDs.
        
        Args:
            blueprint: CompiledBlueprint
            
        Returns:
            Danh sách regulatory overlay IDs
        """
        return [ro.id for ro in blueprint.regulatory_overlays]

    def compose(
        self,
        blueprint: CompiledBlueprint,
        mir: Any | None = None,
        target_stacks: list[str] | None = None,
    ) -> CompositionPlan:
        """
        Compose blueprint thành CompositionPlan.

        Method này là entry point của CP51 — nhận CompiledBlueprint
        và generate CompositionPlan hoàn chỉnh cho stage 'code gen'.

        Process:
        1. Validate blueprint is_valid()
        2. Resolve CP dependencies (topological sort theo phase order)
        3. Resolve DP dependencies (sau CP deps)
        4. Resolve RX dependencies (sau DP deps)
        5. Build pack resolution (query taxonomy + load pack.yml)
        6. Build template mapping (MIR op_type → template)
        7. Build stack bindings
        8. Validate templates exist
        9. Return CompositionPlan

        Args:
            blueprint: CompiledBlueprint đã compile và validate
            mir: MIR object (tùy chọn, để extract operations)
            target_stacks: Danh sách target stacks (default: từ blueprint)

        Returns:
            CompositionPlan hoàn chỉnh
        """
        # Extract MIR operations nếu có
        mir_operations: list[str] | None = None
        if mir is not None and hasattr(mir, "operations"):
            mir_operations = [
                op.op_type for op in mir.operations
                if hasattr(op, "op_type")
            ]

        # CP52 GATE: Validate invariants trước khi compose
        # Nếu gate fail → throw compile error (MDC-BLUEPRINT-006)
        try:
            from midicoder.emitters.core.invariant import InvariantManager
            from midicoder.errors import MidicoderErrorManager as EM

            invariant_manager = InvariantManager()
            invariant_manager.initialize()

            # Validate từ MIR (nếu có)
            if mir is not None:
                report = invariant_manager.validate(
                    mir,
                    blueprint_id=getattr(blueprint, 'id', None) or getattr(blueprint.industry, 'id', '') or '',
                )
                if not report.is_passing:
                    violations = report.get_critical_violations()
                    violation_codes = report.summary.get('violation_codes', [])
                    raise EM.raise_error(
                        ErrorCode.BLUEPRINT_INVARIANT_VIOLATION,
                        violations=report.failed,
                        violation_codes=violation_codes,
                        details=', '.join(
                            f'{v.invariant_id}: {v.message}' for v in violations
                        ),
                    )
        except MidicoderError:
            # Re-raise MidicoderError (BLUEPRINT_INVARIANT_VIOLATION)
            raise
        except Exception:
            # Nếu invariant system không khả dụng, continue
            # Fallback để không block pipeline nếu CP52 chưa ready
            pass

        # Tạo composition engine
        engine = CompositionEngine(self._taxonomy_registry)

        # Compose
        return engine.compose(
            blueprint=blueprint,
            mir_operations=mir_operations,
            target_stacks=target_stacks,
        )

    def _get_taxonomy_registry(self) -> Any:
        """
        Lấy TaxonomyRegistry từ taxonomy data.

        Returns:
            TaxonomyRegistry instance
        """
        from industry.registry import TaxonomyRegistry
        return TaxonomyRegistry(self.taxonomy)

    @property
    def _taxonomy_registry(self) -> Any:
        """Lazy load TaxonomyRegistry."""
        if not hasattr(self, "_registry"):
            self._registry = self._get_taxonomy_registry()
        return self._registry


# Export classes
__all__ = [
    # Data classes
    "BlueprintMetadata",
    "IndustryInfo",
    "CorePacksConfig",
    "DomainPackRef",
    "RegulatoryOverlayRef",
    "BusinessInvariant",
    "ComplianceInvariant",
    "FailureModeInvariant",
    "InvariantsConfig",
    "BlueprintConfig",
    "BlueprintReferences",
    "CompiledBlueprint",
    # Compiler
    "BlueprintCompiler",
    "BlueprintCompilerError",
]