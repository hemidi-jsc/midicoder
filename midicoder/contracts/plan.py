"""
Plan Contracts cho Midicoder v1.0.0

Module này định nghĩa các plan artifacts cho code generation và delivery:
- Surface Plan: Map capabilities → runtime surfaces (Rule 5)
- Target Plan: Map surfaces → runtime topology
- Patch Plan: Delivery plan cho code changes (Rule 13)

Theo Rule 5: Surface planning tách khỏi semantics
Theo Rule 13: Patch engine tồn tại nhưng không phải trái tim

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .artifact import ArtifactBase, ArtifactMetadata


# ============================================================================
# Surface Types
# ============================================================================


class SurfaceType(Enum):
    """
    Các loại runtime surfaces.
    
    Surfaces là nơi MIR materialize ra code.
    Theo Rule 5: Surface planning tách khỏi semantics.
    """
    HTTP_COMMAND_HANDLER = "http_command_handler"      # FastAPI/Flask handler
    HTTP_QUERY_HANDLER = "http_query_handler"          # GET handler
    APPLICATION_SERVICE = "application_service"        # Service layer method
    DOMAIN_SERVICE = "domain_service"                  # Domain service
    REPOSITORY = "repository"                          # Data access layer
    RESPONSE_SCHEMA = "response_schema"                # Pydantic response model
    REQUEST_SCHEMA = "request_schema"                  # Pydantic request model
    ENTITY_MODEL = "entity_model"                      # Domain entity
    VALUE_OBJECT = "value_object"                      # Value object
    EVENT_HANDLER = "event_handler"                    # Event subscriber
    WORKFLOW_ENGINE = "workflow_engine"                # Workflow state machine
    AUTH_MIDDLEWARE = "auth_middleware"                # Authentication middleware
    CACHE_LAYER = "cache_layer"                        # Cache implementation
    MESSAGE_PRODUCER = "message_producer"              # Event/message publisher
    MESSAGE_CONSUMER = "message_consumer"              # Event/message subscriber


# ============================================================================
# Surface
# ============================================================================


@dataclass
class Surface:
    """
    Surface đại diện cho một runtime artifact cần generate.
    
    Theo Rule 5: Surface planning chỉ trả lời:
    - Capability/MIR này cần materialize ra surface nào
    - Surface nào sở hữu symbol nào
    - Surface nào đi vào file/module nào
    
    Attributes:
        surface_type: Loại surface (từ SurfaceType enum)
        module: Module path (ví dụ: "orders.services")
        symbol: Symbol name trong module
        mir_ref: Reference vào source MIR
        dependencies: Danh sách surface dependencies
        config: Configuration cho surface
        
    Example:
        Surface(
            surface_type=SurfaceType.HTTP_COMMAND_HANDLER,
            module="orders.http",
            symbol="create_order",
            mir_ref="Command.CreateOrder",
            dependencies=["orders.services.CreateOrderService"],
        )
    """
    surface_type: str  # Use string for flexibility
    module: str
    symbol: str
    mir_ref: str
    dependencies: list[str] = field(default_factory=list)
    config: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "surface_type": self.surface_type,
            "module": self.module,
            "symbol": self.symbol,
            "mir_ref": self.mir_ref,
            "dependencies": self.dependencies,
            "config": self.config,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Surface":
        """Create from dictionary."""
        return cls(
            surface_type=data["surface_type"],
            module=data["module"],
            symbol=data["symbol"],
            mir_ref=data["mir_ref"],
            dependencies=data.get("dependencies", []),
            config=data.get("config", {}),
        )
    
    @property
    def fully_qualified_name(self) -> str:
        """Get fully qualified symbol name."""
        return f"{self.module}.{self.symbol}"


# ============================================================================
# Surface Plan
# ============================================================================


@dataclass
class SurfacePlan(ArtifactBase):
    """
    Surface Plan - Map MIR → Runtime Surfaces.
    
    Theo Rule 5: Surface planning tách khỏi semantics.
    Surface plan không chứa code text, không chứa patch operations.
    
    Attributes:
        mir_ref: Reference vào source MIR
        surfaces: Danh sách surfaces cần generate
        module_graph: Graph của module dependencies
        metadata: Artifact metadata
        
    Example:
        plan = SurfacePlan(
            mir_ref="Command.CreateOrder",
            surfaces=[
                Surface(
                    surface_type=SurfaceType.HTTP_COMMAND_HANDLER.value,
                    module="orders.http",
                    symbol="create_order",
                    mir_ref="Command.CreateOrder",
                ),
                Surface(
                    surface_type=SurfaceType.APPLICATION_SERVICE.value,
                    module="orders.services",
                    symbol="CreateOrderService",
                    mir_ref="Command.CreateOrder",
                ),
            ],
            metadata=ArtifactMetadata.with_timestamp(...),
        )
    """
    mir_ref: str = ""
    surfaces: list[Surface] = field(default_factory=list)
    module_graph: dict[str, list[str]] = field(default_factory=dict)
    
    # Cache mappings
    _surface_by_module_symbol: dict[str, Surface] = field(default_factory=dict, repr=False)
    
    @property
    def artifact_type(self) -> str:
        """Return artifact type."""
        return "surface_plan"
    
    def __post_init__(self) -> None:
        """Build cache mappings."""
        self._build_cache()
    
    def _build_cache(self) -> None:
        """Build cache mappings cho fast lookups."""
        self._surface_by_module_symbol = {
            s.fully_qualified_name: s for s in self.surfaces
        }
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.artifact_type,
            "version": "1.0.0",
            "metadata": self.metadata.to_dict(),
            "mir_ref": self.mir_ref,
            "surfaces": [s.to_dict() for s in self.surfaces],
            "module_graph": self.module_graph,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SurfacePlan":
        """Create from dictionary."""
        metadata = ArtifactMetadata.from_dict(data.get("metadata", {}))
        
        # Create instance without metadata (init=False)
        instance = cls(
            mir_ref=data["mir_ref"],
            surfaces=[Surface.from_dict(s) for s in data.get("surfaces", [])],
            module_graph=data.get("module_graph", {}),
        )
        # Set metadata after initialization
        object.__setattr__(instance, "metadata", metadata)
        return instance
    
    # =========================================================================
    # Surface Management
    # =========================================================================
    
    def add_surface(self, surface: Surface) -> None:
        """
        Thêm surface vào plan.
        
        Args:
            surface: Surface để thêm
        """
        self.surfaces.append(surface)
        self._surface_by_module_symbol[surface.fully_qualified_name] = surface
    
    def get_surface(self, module: str, symbol: str) -> Surface | None:
        """Lấy surface theo module và symbol."""
        return self._surface_by_module_symbol.get(f"{module}.{symbol}")
    
    def get_surfaces_by_type(self, surface_type: str) -> list[Surface]:
        """Lấy surfaces theo type."""
        return [s for s in self.surfaces if s.surface_type == surface_type]
    
    def get_surfaces_by_module(self, module: str) -> list[Surface]:
        """Lấy surfaces theo module."""
        return [s for s in self.surfaces if s.module == module]
    
    # =========================================================================
    # Validation
    # =========================================================================
    
    def validate(self) -> list[str]:
        """
        Validate surface plan.
        
        Returns:
            Danh sách error messages (rỗng nếu valid)
        """
        errors = super().validate()
        
        # Check mir_ref is set
        if not self.mir_ref:
            errors.append("SurfacePlan.mir_ref is required")
        
        # Check surfaces are not empty
        if not self.surfaces:
            errors.append("SurfacePlan must have at least one surface")
        
        # Check surface IDs are unique
        seen: set[str] = set()
        for surface in self.surfaces:
            fqdn = surface.fully_qualified_name
            if fqdn in seen:
                errors.append(f"Duplicate surface: {fqdn}")
            seen.add(fqdn)
        
        return errors


# ============================================================================
# Target Plan
# ============================================================================


@dataclass
class TargetPlan(ArtifactBase):
    """
    Target Plan - Map Surfaces → File/Module Topology.
    
    Target plan xác định runtime topology:
    - File paths
    - Package structure
    - Import paths
    
    Attributes:
        target_runtime: Runtime target (fastapi, django, etc.)
        base_path: Base path cho generated files
        surfaces: Danh sách surfaces với file mappings
        package_structure: Package structure
        metadata: Artifact metadata
    """
    target_runtime: str = ""
    base_path: str = ""
    surfaces: list[dict[str, Any]] = field(default_factory=list)
    package_structure: dict[str, Any] = field(default_factory=dict)
    
    @property
    def artifact_type(self) -> str:
        """Return artifact type."""
        return "target_plan"
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.artifact_type,
            "version": "1.0.0",
            "metadata": self.metadata.to_dict(),
            "target_runtime": self.target_runtime,
            "base_path": self.base_path,
            "surfaces": self.surfaces,
            "package_structure": self.package_structure,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TargetPlan":
        """Create from dictionary."""
        metadata = ArtifactMetadata.from_dict(data.get("metadata", {}))
        
        # Create instance without metadata (init=False)
        instance = cls(
            target_runtime=data["target_runtime"],
            base_path=data["base_path"],
            surfaces=data.get("surfaces", []),
            package_structure=data.get("package_structure", {}),
        )
        # Set metadata after initialization
        object.__setattr__(instance, "metadata", metadata)
        return instance
    
    def validate(self) -> list[str]:
        """Validate target plan."""
        errors = super().validate()
        
        if not self.target_runtime:
            errors.append("TargetPlan.target_runtime is required")
        
        if not self.base_path:
            errors.append("TargetPlan.base_path is required")
        
        return errors


# ============================================================================
# Patch Operation Types
# ============================================================================


class PatchOperationType(Enum):
    """Các loại patch operations."""
    CREATE_FILE = "create_file"       # Tạo file mới
    DELETE_FILE = "delete_file"       # Xóa file
    MODIFY_FILE = "modify_file"       # Sửa file
    RENAME_FILE = "rename_file"       # Đổi tên file
    CREATE_DIR = "create_directory"   # Tạo thư mục
    DELETE_DIR = "delete_directory"   # Xóa thư mục


# ============================================================================
# Patch Operation
# ============================================================================


@dataclass
class PatchOperation:
    """
    Patch Operation đại diện cho một file operation.
    
    Theo Rule 13: Patch engine chỉ gánh delivery, không gánh semantics.
    
    Attributes:
        op_type: Loại operation
        path: File/directory path
        content: Content (cho create/modify operations)
        old_path: Old path (cho rename)
        conditions: Pre-conditions cho patch
        rollback: Rollback operation
        
    Example:
        PatchOperation(
            op_type=PatchOperationType.CREATE_FILE,
            path="app/orders/http.py",
            content="def create_order(...):...",
        )
    """
    op_type: str  # Use string for flexibility
    path: str
    content: str | None = None
    old_path: str | None = None
    conditions: list[str] = field(default_factory=list)
    rollback: dict[str, Any] | None = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "op_type": self.op_type,
            "path": self.path,
            "content": self.content,
            "old_path": self.old_path,
            "conditions": self.conditions,
            "rollback": self.rollback,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PatchOperation":
        """Create from dictionary."""
        return cls(
            op_type=data["op_type"],
            path=data["path"],
            content=data.get("content"),
            old_path=data.get("old_path"),
            conditions=data.get("conditions", []),
            rollback=data.get("rollback"),
        )


# ============================================================================
# Patch Plan
# ============================================================================


@dataclass
class PatchPlan(ArtifactBase):
    """
    Patch Plan - Delivery Plan cho code changes.
    
    Theo Rule 13: Patch engine phải tồn tại nhưng không phải trái tim.
    Patch-plan là artifact cuối, chỉ gánh delivery.
    
    Attributes:
        mir_ref: Reference vào source MIR
        surface_plan_ref: Reference vào surface plan
        operations: Danh sách patch operations
        apply_order: Order của operations (dependency-ordered)
        conditions: Pre-conditions cho toàn patch
        rollback_plan: Rollback plan
        metadata: Artifact metadata
        
    Example:
        plan = PatchPlan(
            mir_ref="Command.CreateOrder",
            surface_plan_ref="surface_plan_create_order.json",
            operations=[
                PatchOperation(
                    op_type=PatchOperationType.CREATE_FILE,
                    path="app/orders/http.py",
                    content="...",
                ),
            ],
            metadata=ArtifactMetadata.with_timestamp(...),
        )
    """
    mir_ref: str = ""
    surface_plan_ref: str = ""
    operations: list[PatchOperation] = field(default_factory=list)
    apply_order: list[str] = field(default_factory=list)
    conditions: list[str] = field(default_factory=list)
    rollback_plan: list[dict[str, Any]] = field(default_factory=list)
    
    @property
    def artifact_type(self) -> str:
        """Return artifact type."""
        return "patch_plan"
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.artifact_type,
            "version": "1.0.0",
            "metadata": self.metadata.to_dict(),
            "mir_ref": self.mir_ref,
            "surface_plan_ref": self.surface_plan_ref,
            "operations": [op.to_dict() for op in self.operations],
            "apply_order": self.apply_order,
            "conditions": self.conditions,
            "rollback_plan": self.rollback_plan,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PatchPlan":
        """Create from dictionary."""
        metadata = ArtifactMetadata.from_dict(data.get("metadata", {}))
        
        # Create instance without metadata (init=False)
        instance = cls(
            mir_ref=data["mir_ref"],
            surface_plan_ref=data["surface_plan_ref"],
            operations=[
                PatchOperation.from_dict(op)
                for op in data.get("operations", [])
            ],
            apply_order=data.get("apply_order", []),
            conditions=data.get("conditions", []),
            rollback_plan=data.get("rollback_plan", []),
        )
        # Set metadata after initialization
        object.__setattr__(instance, "metadata", metadata)
        return instance
    
    # =========================================================================
    # Operation Management
    # =========================================================================
    
    def add_operation(self, operation: PatchOperation) -> None:
        """
        Thêm patch operation.
        
        Args:
            operation: Operation để thêm
        """
        self.operations.append(operation)
    
    def get_operations_by_type(self, op_type: str) -> list[PatchOperation]:
        """Lấy operations theo type."""
        return [op for op in self.operations if op.op_type == op_type]
    
    def get_operations_for_path(self, path: str) -> list[PatchOperation]:
        """Lấy operations cho path."""
        return [op for op in self.operations if op.path == path]
    
    # =========================================================================
    # Validation
    # =========================================================================
    
    def validate(self) -> list[str]:
        """
        Validate patch plan.
        
        Returns:
            Danh sách error messages (rỗng nếu valid)
        """
        errors = super().validate()
        
        # Check required refs
        if not self.mir_ref:
            errors.append("PatchPlan.mir_ref is required")
        
        if not self.surface_plan_ref:
            errors.append("PatchPlan.surface_plan_ref is required")
        
        # Check operations have valid paths
        for op in self.operations:
            if not op.path:
                errors.append(f"PatchOperation missing path: {op}")
        
        return errors