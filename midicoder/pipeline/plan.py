"""
Implementation Plan Module.

Module chứa typed data structures cho Implementation Plan trong Midicoder pipeline.
Plan là typed IR nằm giữa MIR và code generation, dùng để nhóm files theo modules
và xác định dependencies.

Theo SoT E07, plan được tạo từ MIR bằng `code plan` command và lưu vào SQLite
artifacts table dưới dạng JSON (artifact_type="plan").

Ví dụ sử dụng:
    # Tạo Implementation Plan
    plan = ImplementationPlan(
        meta={"version": "1.0.0", "target": "backend"}
    )
    
    # Thêm module backend
    backend_module = ModuleSpec(
        name="orders",
        module_type="backend",
        files=[
            FileSpec(
                path="app/models/order.py",
                file_type="model",
                template="fastapi/model.py.jinja2"
            )
        ]
    )
    plan.add_module(backend_module)
    
    # Serialize to JSON
    json_str = plan.to_json()
    
    # Save to SQLite
    artifacts_manager.create(
        artifact_id="plan-v1.0.0",
        artifact_type="plan",
        content=json_str
    )

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any


# ============================================================================
# FileSpec - File Specification
# ============================================================================


@dataclass
class FileSpec:
    """
    File Specification - Mô tả một file cần generate.
    
    FileSpec đại diện cho một file source code cần được generate từ template.
    Mỗi FileSpec chứa thông tin về đường dẫn, loại file, template dùng để render,
    và các dependencies với files khác.
    
    Theo SoT E07, FileSpec được dùng bởi emitter để xác định file nào cần generate
    và dùng template nào.
    
    Attributes:
        path: Đường dẫn file tương đối (ví dụ: app/models/order.py)
        file_type: Loại file (model, schema, route, service, component, etc.)
        template: Template name dùng để render (ví dụ: fastapi/model.py.jinja2)
        context: Template context (dict chứa entity, command, query data)
        dependencies: Danh sách file paths mà file này phụ thuộc
        metadata: Metadata bổ sung (optional)
    
    Ví dụ:
        spec = FileSpec(
            path="app/models/order.py",
            file_type="model",
            template="fastapi/model.py.jinja2",
            context={"entity": {"id": "Order", "name": "Đơn hàng"}},
            dependencies=["app/config.py"],
            metadata={"generated": True}
        )
    """
    
    path: str
    file_type: str
    template: str
    context: dict[str, Any] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """
        Chuyển FileSpec sang dictionary.
        
        Returns:
            Dictionary representation của FileSpec
        """
        return {
            "path": self.path,
            "file_type": self.file_type,
            "template": self.template,
            "context": self.context,
            "dependencies": self.dependencies,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FileSpec":
        """
        Tạo FileSpec từ dictionary.
        
        Args:
            data: Dictionary chứa file spec data
            
        Returns:
            FileSpec instance
        """
        return cls(
            path=data["path"],
            file_type=data["file_type"],
            template=data["template"],
            context=data.get("context", {}),
            dependencies=data.get("dependencies", []),
            metadata=data.get("metadata", {}),
        )


# ============================================================================
# ModuleSpec - Module Specification
# ============================================================================


@dataclass
class ModuleSpec:
    """
    Module Specification - Nhóm các files thuộc cùng module.
    
    ModuleSpec đại diện cho một module (ví dụ: orders, users, auth) chứa
    nhiều files liên quan. Module có dependencies với các modules khác.
    
    Theo SoT E07, modules được nhóm theo chức năng và có dependency graph
    để xác định thứ tự code generation.
    
    Attributes:
        name: Tên module (ví dụ: orders, users, auth)
        module_type: Loại module (backend, frontend, infra)
        files: Danh sách FileSpec thuộc module
        dependencies: Danh sách module names mà module này phụ thuộc
        metadata: Metadata bổ sung
    
    Ví dụ:
        module = ModuleSpec(
            name="orders",
            module_type="backend",
            files=[
                FileSpec(path="app/models/order.py", file_type="model", template="..."),
                FileSpec(path="app/routes/order.py", file_type="route", template="..."),
            ],
            dependencies=["auth", "users"],
            metadata={"priority": 1}
        )
    """
    
    name: str
    module_type: str
    files: list[FileSpec] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """
        Chuyển ModuleSpec sang dictionary.
        
        Returns:
            Dictionary representation của ModuleSpec
        """
        return {
            "name": self.name,
            "module_type": self.module_type,
            "files": [f.to_dict() for f in self.files],
            "dependencies": self.dependencies,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ModuleSpec":
        """
        Tạo ModuleSpec từ dictionary.
        
        Args:
            data: Dictionary chứa module spec data
            
        Returns:
            ModuleSpec instance
        """
        files = [FileSpec.from_dict(f) for f in data.get("files", [])]
        
        return cls(
            name=data["name"],
            module_type=data["module_type"],
            files=files,
            dependencies=data.get("dependencies", []),
            metadata=data.get("metadata", {}),
        )


# ============================================================================
# ImplementationPlan - Implementation Plan
# ============================================================================


@dataclass
class ImplementationPlan:
    """
    Implementation Plan - Kế hoạch code generation hoàn chỉnh.
    
    Plan là typed IR nằm giữa MIR và code generation. Plan nhóm files theo
    modules và xác định dependencies để emitter có thể generate code theo
    thứ tự đúng.
    
    Theo SoT E07, plan được tạo từ MIR bằng `code plan` command và lưu vào
    SQLite artifacts table dưới dạng JSON. Plan có deterministic hash để
    verify rằng cùng input (MIR) sẽ cho cùng output (Plan).
    
    Attributes:
        meta: Metadata (version, created_at, target, source_mir_hash)
        modules: Danh sách ModuleSpec (backend + frontend + infra)
        
    Methods:
        to_dict() → dict
        to_json(indent=2) → str
        from_dict(data) → ImplementationPlan
        from_json(json_str) → ImplementationPlan
        compute_hash() → str (SHA256 deterministic hash)
        get_files_by_type(file_type) → list[FileSpec]
        get_modules_by_type(module_type) → list[ModuleSpec]
        count_files() → dict[str, int]
        add_module(module) → None
    
    Ví dụ:
        plan = ImplementationPlan(
            meta={"version": "1.0.0", "target": "all"},
            modules=[
                ModuleSpec(name="orders", module_type="backend", files=[...]),
                ModuleSpec(name="frontend", module_type="frontend", files=[...]),
            ]
        )
        
        json_str = plan.to_json()
        plan_hash = plan.compute_hash()
    """
    
    meta: dict[str, Any] = field(default_factory=dict)
    modules: list[ModuleSpec] = field(default_factory=list)
    
    def add_module(self, module: ModuleSpec) -> None:
        """
        Thêm module vào plan.
        
        Args:
            module: ModuleSpec để thêm
        """
        self.modules.append(module)
    
    def to_dict(self) -> dict[str, Any]:
        """
        Chuyển ImplementationPlan sang dictionary.
        
        Returns:
            Dictionary representation của ImplementationPlan
        """
        return {
            "meta": self.meta,
            "modules": [m.to_dict() for m in self.modules],
        }
    
    def to_json(self, indent: int = 2) -> str:
        """
        Serialize ImplementationPlan sang JSON string.
        
        Args:
            indent: Số khoảng trắng cho indentation
            
        Returns:
            JSON string representation của ImplementationPlan
        """
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ImplementationPlan":
        """
        Tạo ImplementationPlan từ dictionary.
        
        Args:
            data: Dictionary chứa plan data
            
        Returns:
            ImplementationPlan instance
        """
        modules = [ModuleSpec.from_dict(m) for m in data.get("modules", [])]
        
        return cls(
            meta=data.get("meta", {}),
            modules=modules,
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> "ImplementationPlan":
        """
        Tạo ImplementationPlan từ JSON string.
        
        Args:
            json_str: JSON string chứa plan data
            
        Returns:
            ImplementationPlan instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def compute_hash(self) -> str:
        """
        Tính hash deterministic cho ImplementationPlan.
        
        Dùng cho verification và caching. Cùng plan → Cùng hash.
        Hash được tính bằng cách normalize JSON (sorted keys) rồi SHA256.
        
        Returns:
            SHA256 hash string của ImplementationPlan (64 hex characters)
        """
        # Normalize JSON cho determinism (sorted keys)
        normalized = json.dumps(self.to_dict(), sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    
    def get_files_by_type(self, file_type: str) -> list[FileSpec]:
        """
        Lọc files theo type từ tất cả modules.
        
        Args:
            file_type: Loại file để lọc (model, route, component, etc.)
            
        Returns:
            Danh sách FileSpec matching type
        """
        result = []
        for module in self.modules:
            for file_spec in module.files:
                if file_spec.file_type == file_type:
                    result.append(file_spec)
        return result
    
    def get_modules_by_type(self, module_type: str) -> list[ModuleSpec]:
        """
        Lọc modules theo type.
        
        Args:
            module_type: Loại module để lọc (backend, frontend, infra)
            
        Returns:
            Danh sách ModuleSpec matching type
        """
        return [m for m in self.modules if m.module_type == module_type]
    
    def count_files(self) -> dict[str, int]:
        """
        Đếm số files theo module_type.
        
        Returns:
            Dictionary {module_type: count}
        """
        counts: dict[str, int] = {}
        
        for module in self.modules:
            module_type = module.module_type
            if module_type not in counts:
                counts[module_type] = 0
            counts[module_type] += len(module.files)
        
        # Ensure all types are present
        for module_type in ["backend", "frontend", "infra"]:
            if module_type not in counts:
                counts[module_type] = 0
        
        return counts


# ============================================================================
# PlanBuilder - Fluent API cho Plan construction (optional, phase 2)
# ============================================================================


@dataclass
class PlanBuilder:
    """
    Plan Builder - Fluent API cho Implementation Plan construction.
    
    Cung cấp builder pattern để tạo Plan một cách declarative.
    Hữu ích cho plan generation từ MIR.
    
    Attributes:
        plan: ImplementationPlan đang build
    """
    
    plan: ImplementationPlan = field(default_factory=ImplementationPlan)
    
    def with_version(self, version: str) -> "PlanBuilder":
        """
        Set plan version.
        
        Args:
            version: Version string
            
        Returns:
            Self cho chaining
        """
        self.plan.meta["version"] = version
        return self
    
    def with_target(self, target: str) -> "PlanBuilder":
        """
        Set plan target.
        
        Args:
            target: Target (backend, frontend, all)
            
        Returns:
            Self cho chaining
        """
        self.plan.meta["target"] = target
        return self
    
    def add_module(
        self,
        name: str,
        module_type: str,
        files: list[FileSpec] | None = None,
        dependencies: list[str] | None = None
    ) -> "PlanBuilder":
        """
        Thêm module vào plan.
        
        Args:
            name: Module name
            module_type: Module type
            files: Danh sách FileSpec
            dependencies: Danh sách dependency module names
            
        Returns:
            Self cho chaining
        """
        self.plan.add_module(ModuleSpec(
            name=name,
            module_type=module_type,
            files=files or [],
            dependencies=dependencies or []
        ))
        return self
    
    def build(self) -> ImplementationPlan:
        """
        Build ImplementationPlan hoàn tất.
        
        Returns:
            ImplementationPlan instance
        """
        return self.plan