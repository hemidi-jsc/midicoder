"""
Models cho CP51: Blueprint Composition Engine.

Cung cấp các data classes để biểu diễn CompositionPlan —
kế hoạch thi công chi tiết cho stage 'code gen'.

Các model chính:
- CompositionNode: Node trong emit order (pack + thứ tự + dependencies)
- PackResolution: Kết quả resolve một pack (capabilities, templates)
- TemplateBinding: Binding giữa MIR op_type và template path
- StackBinding: Binding giữa stack name và templates
- CompositionPlan: Kế hoạch composition hoàn chỉnh

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# ============================================================================
# Composition Models
# ============================================================================


@dataclass
class CompositionNode:
    """
    Node trong emit order của CompositionPlan.

    Mỗi node đại diện cho một pack cần emit, với thông tin
    về thứ tự emit và dependencies.

    Attributes:
        pack_id: ID của pack (CP01, DP01, RX01)
        pack_type: Loại pack (core_pack, domain_pack, regulatory_overlay)
        emit_order: Thứ tự emit (1-based, nhỏ hơn = emit trước)
        phase: Phase của pack (P0, P1, P2, P3, P4)
        dependencies: Danh sách pack IDs phải emit trước pack này
    """

    pack_id: str
    pack_type: str
    emit_order: int
    phase: str
    dependencies: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize thành dictionary."""
        return {
            "pack_id": self.pack_id,
            "pack_type": self.pack_type,
            "emit_order": self.emit_order,
            "phase": self.phase,
            "dependencies": self.dependencies,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CompositionNode:
        """Tạo CompositionNode từ dictionary."""
        return cls(
            pack_id=data["pack_id"],
            pack_type=data["pack_type"],
            emit_order=data["emit_order"],
            phase=data["phase"],
            dependencies=data.get("dependencies", []),
        )


@dataclass
class PackResolution:
    """
    Kết quả resolve một pack từ TaxonomyRegistry.

    Chứa thông tin chi tiết về pack đã được resolve,
    bao gồm capabilities_provided và templates mapping.

    Attributes:
        pack_id: ID của pack
        pack_type: Loại pack
        internal_id: Internal ID (vd: cp1-domain-model)
        status: Trạng thái pack (stable, developing, planned)
        capabilities_provided: Danh sách capabilities của pack
        templates: Mapping capability → template path
        pack_yml_path: Đường dẫn đến pack.yml
    """

    pack_id: str
    pack_type: str
    internal_id: str
    status: str
    capabilities_provided: list[str] = field(default_factory=list)
    templates: dict[str, str] = field(default_factory=dict)
    pack_yml_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize thành dictionary."""
        return {
            "pack_id": self.pack_id,
            "pack_type": self.pack_type,
            "internal_id": self.internal_id,
            "status": self.status,
            "capabilities_provided": self.capabilities_provided,
            "templates": self.templates,
            "pack_yml_path": self.pack_yml_path,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PackResolution:
        """Tạo PackResolution từ dictionary."""
        return cls(
            pack_id=data["pack_id"],
            pack_type=data["pack_type"],
            internal_id=data["internal_id"],
            status=data["status"],
            capabilities_provided=data.get("capabilities_provided", []),
            templates=data.get("templates", {}),
            pack_yml_path=data.get("pack_yml_path", ""),
        )


@dataclass
class TemplateBinding:
    """
    Binding giữa MIR operation type và template path.

    Mỗi binding nối một MIR op_type với template cụ thể
    trong stack cụ thể.

    Attributes:
        op_type: MIR operation type (vd: create_record, query_records)
        pack_id: Pack cung cấp template (vd: CP08)
        template_path: Đường dẫn template (vd: fastapi/model.py.jinja2)
        stack: Stack name (fastapi, nestjs, angular, react)
    """

    op_type: str
    pack_id: str
    template_path: str
    stack: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize thành dictionary."""
        return {
            "op_type": self.op_type,
            "pack_id": self.pack_id,
            "template_path": self.template_path,
            "stack": self.stack,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TemplateBinding:
        """Tạo TemplateBinding từ dictionary."""
        return cls(
            op_type=data["op_type"],
            pack_id=data["pack_id"],
            template_path=data["template_path"],
            stack=data["stack"],
        )


@dataclass
class StackBinding:
    """
    Binding giữa stack name và danh sách templates.

    Mỗi stack binding chứa tất cả templates cần render
    cho stack cụ thể.

    Attributes:
        stack_name: Tên stack (fastapi, nestjs, angular, react)
        templates: Danh sách template bindings cho stack này
        stack_dir: Đường dẫn đến stack directory
    """

    stack_name: str
    templates: list[TemplateBinding] = field(default_factory=list)
    stack_dir: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize thành dictionary."""
        return {
            "stack_name": self.stack_name,
            "templates": [t.to_dict() for t in self.templates],
            "stack_dir": self.stack_dir,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StackBinding:
        """Tạo StackBinding từ dictionary."""
        return cls(
            stack_name=data["stack_name"],
            templates=[
                TemplateBinding.from_dict(t) for t in data.get("templates", [])
            ],
            stack_dir=data.get("stack_dir", ""),
        )


@dataclass
class CompositionPlan:
    """
    Kế hoạch composition hoàn chỉnh cho Blueprint.

    CompositionPlan là output của CP51 — chứa đầy đủ thông tin
    cần thiết cho stage 'code gen' để emit source code:
    - Emit order (topological sort của packs)
    - Pack resolution (capabilities, templates)
    - Template mapping (MIR op_type → template)
    - Stack bindings (stack-specific templates)
    - Validation results

    Attributes:
        blueprint_id: ID của CompiledBlueprint reference
        schema_version: Version của composition plan schema
        emit_order: Danh sách nodes theo thứ tự emit (topological)
        pack_resolution: Mapping pack ID → PackResolution
        template_mapping: Mapping MIR op_type → TemplateBinding
        stack_bindings: Mapping stack name → StackBinding
        validation_errors: Danh sách validation errors
        validation_warnings: Danh sách validation warnings
    """

    blueprint_id: str
    schema_version: str = "composition-plan-v1"
    emit_order: list[CompositionNode] = field(default_factory=list)
    pack_resolution: dict[str, PackResolution] = field(default_factory=dict)
    template_mapping: dict[str, TemplateBinding] = field(default_factory=dict)
    stack_bindings: dict[str, StackBinding] = field(default_factory=dict)
    validation_errors: list[str] = field(default_factory=list)
    validation_warnings: list[str] = field(default_factory=list)

    def add_validation_error(self, error: str) -> None:
        """
        Thêm validation error vào plan.

        Args:
            error: Thông báo lỗi
        """
        self.validation_errors.append(error)

    def add_warning(self, warning: str) -> None:
        """
        Thêm warning vào plan.

        Args:
            warning: Thông báo warning
        """
        self.validation_warnings.append(warning)

    def is_valid(self) -> bool:
        """
        Kiểm tra plan có valid không (không có validation errors).

        Returns:
            True nếu không có validation errors
        """
        return len(self.validation_errors) == 0

    def to_dict(self) -> dict[str, Any]:
        """Serialize thành dictionary."""
        return {
            "blueprint_id": self.blueprint_id,
            "schema_version": self.schema_version,
            "emit_order": [node.to_dict() for node in self.emit_order],
            "pack_resolution": {
                k: v.to_dict() for k, v in self.pack_resolution.items()
            },
            "template_mapping": {
                k: v.to_dict() for k, v in self.template_mapping.items()
            },
            "stack_bindings": {
                k: v.to_dict() for k, v in self.stack_bindings.items()
            },
            "validation_errors": self.validation_errors,
            "validation_warnings": self.validation_warnings,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CompositionPlan:
        """Tạo CompositionPlan từ dictionary."""
        emit_order = [
            CompositionNode.from_dict(n) for n in data.get("emit_order", [])
        ]
        pack_resolution = {
            k: PackResolution.from_dict(v)
            for k, v in data.get("pack_resolution", {}).items()
        }
        template_mapping = {
            k: TemplateBinding.from_dict(v)
            for k, v in data.get("template_mapping", {}).items()
        }
        stack_bindings = {
            k: StackBinding.from_dict(v)
            for k, v in data.get("stack_bindings", {}).items()
        }

        return cls(
            blueprint_id=data["blueprint_id"],
            schema_version=data.get("schema_version", "composition-plan-v1"),
            emit_order=emit_order,
            pack_resolution=pack_resolution,
            template_mapping=template_mapping,
            stack_bindings=stack_bindings,
            validation_errors=data.get("validation_errors", []),
            validation_warnings=data.get("validation_warnings", []),
        )


__all__ = [
    "CompositionNode",
    "PackResolution",
    "TemplateBinding",
    "StackBinding",
    "CompositionPlan",
]