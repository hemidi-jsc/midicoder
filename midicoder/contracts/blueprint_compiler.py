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
from .artifact import ArtifactBase, ArtifactMetadata


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
        return cls(
            version=data["version"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
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
        default_tenant_mode: Default tenant mode (database, schema, row, hybrid)
        default_auth_strategy: Default auth strategy (jwt, oauth2, saml, hybrid)
        default_db_engine: Default database engine (postgres, mysql, sqlserver, oracle)
        observability: Observability configuration
        security: Security configuration
    """
    default_tenant_mode: str = "schema"
    default_auth_strategy: str = "jwt"
    default_db_engine: str = "postgres"
    observability: dict[str, Any] = field(default_factory=dict)
    security: dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BlueprintConfig":
        """Tạo BlueprintConfig từ dictionary."""
        return cls(
            default_tenant_mode=data.get("default_tenant_mode", "schema"),
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
class CompiledBlueprint(ArtifactBase):
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
        metadata: Blueprint metadata
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
    metadata: BlueprintMetadata = field(default_factory=BlueprintMetadata)
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
    
    # Artifact metadata
    _artifact_metadata: ArtifactMetadata = field(default_factory=ArtifactMetadata, repr=False)
    
    @property
    def artifact_type(self) -> str:
        """Trả về artifact type."""
        return "compiled_blueprint"
    
    @property
    def metadata(self) -> ArtifactMetadata:
        """Get artifact metadata."""
        return self._artifact_metadata
    
    @metadata.setter
    def metadata(self, value: ArtifactMetadata) -> None:
        """Set artifact metadata."""
        self._artifact_metadata = value
    
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
        return cls(
            schema_version=data.get("schema_version", "industry-blueprint-v1"),
            metadata=BlueprintMetadata.from_dict(data.get("metadata", {})),
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
    
    def validate(self) -> list[str]:
        """
        Validate blueprint.
        
        Returns:
            Danh sách error messages (rỗng nếu valid)
        """
        errors = super().validate() if hasattr(super(), 'validate') else []
        
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
        if self.metadata.status == "approved":
            experimental_p4 = set(self.core_packs.experimental).intersection(p4_packs)
            if experimental_p4:
                has_experimental_tag = "experimental-feature" in self.metadata.tags
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
        
        # Load taxonomy
        if self.taxonomy_path.exists():
            with open(self.taxonomy_path, 'r', encoding='utf-8') as f:
                self.taxonomy = yaml.safe_load(f)
    
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
        return CompiledBlueprint(
            schema_version=data.get("$schema", "industry-blueprint-v1"),
            metadata=BlueprintMetadata.from_dict(data.get("metadata", {})),
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