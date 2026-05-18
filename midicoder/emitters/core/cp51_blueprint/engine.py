"""
CompositionEngine — Orchestrate full composition flow.

Module này chứa logic chính của CP51:
- Topological emit order (CP→DP→RX, phase P0→P4, dependency-aware)
- Pack resolution (query taxonomy + load pack.yml)
- Template mapping (MIR op_type → template path)
- Stack binding (stack name → stack templates)
- Template existence validation

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from industry.registry import TaxonomyRegistry, Pack

if TYPE_CHECKING:
    from typing import Any as CompiledBlueprint  # type: ignore  # blueprint_compiler removed
from .models import (
    CompositionPlan,
    CompositionNode,
    PackResolution,
    TemplateBinding,
    StackBinding,
)
from .resolver import PackResolver


# Mapping mặc định từ target_profiles → stacks
# Scope: chỉ AWS + Local/on-premise (không hỗ trợ GCP/Azure)
PROFILE_TO_STACKS: dict[str, list[str]] = {
    "local": ["fastapi", "angular"],
    "aws": ["fastapi", "angular"],
    "on-premise": ["fastapi", "angular"],
}

# Default stacks khi không có target_profiles
DEFAULT_STACKS = ["fastapi", "nestjs", "angular", "react"]

# Phase order mapping
PHASE_ORDER: dict[str, int] = {"P0": 0, "P1": 1, "P2": 2, "P3": 3, "P4": 4}


class CompositionEngine:
    """
    Engine chính cho composition — orchestrate toàn bộ flow.

    Trách nhiệm:
    - Build topological emit order
    - Resolve tất cả packs
    - Build template mapping
    - Build stack bindings
    - Validate templates exist

    Attributes:
        registry: TaxonomyRegistry
        resolver: PackResolver
    """

    def __init__(self, registry: TaxonomyRegistry, midicoder_root: Path | None = None):
        """
        Khởi tạo CompositionEngine.

        Args:
            registry: TaxonomyRegistry đã load
            midicoder_root: Đường dẫn đến midicoder/
        """
        self.registry = registry
        self.resolver = PackResolver(registry, midicoder_root)

    def compose(
        self,
        blueprint: CompiledBlueprint,
        mir_operations: list[str] | None = None,
        target_stacks: list[str] | None = None,
    ) -> CompositionPlan:
        """
        Compose blueprint thành CompositionPlan hoàn chỉnh.

        Process:
        1. Validate blueprint
        2. Resolve tất cả packs từ blueprint
        3. Build topological emit order (CP→DP→RX, phase-aware)
        4. Resolve pack details (capabilities, templates)
        5. Build template mapping (op_type → template)
        6. Build stack bindings
        7. Validate templates exist
        8. Return CompositionPlan

        Args:
            blueprint: CompiledBlueprint đã validate
            mir_operations: Danh sách MIR op_types (tùy chọn)
            target_stacks: Danh sách target stacks (default: từ blueprint hoặc DEFAULT_STACKS)

        Returns:
            CompositionPlan hoàn chỉnh
        """
        # Tạo plan với blueprint id duy nhất
        blueprint_id = self._generate_blueprint_id(blueprint)
        plan = CompositionPlan(blueprint_id=blueprint_id)

        # Step 1: Validate blueprint
        blueprint_errors = blueprint.validate()
        for error in blueprint_errors:
            plan.add_validation_error(f"Blueprint validation: {error}")

        # Step 2: Gather tất cả packs từ blueprint
        all_packs = self._gather_blueprint_packs(blueprint)

        # Step 3: Resolve pack details
        plan.pack_resolution = self.resolver.resolve_packs(all_packs)

        # Step 4: Build topological emit order
        plan.emit_order = self._build_emit_order(all_packs, plan.pack_resolution)

        # Step 5: Build template mapping từ MIR operations
        if mir_operations:
            plan.template_mapping = self._build_template_mapping(mir_operations, plan.pack_resolution)

        # Step 6: Determine target stacks
        stacks = target_stacks or self._determine_stacks(blueprint)

        # Step 7: Build stack bindings
        plan.stack_bindings = self._build_stack_bindings(stacks, plan.template_mapping)

        # Step 8: Validate templates exist
        self._validate_templates_exist(plan)

        # Step 9: Validate pack status warnings
        self._validate_pack_status(plan)

        return plan

    def _gather_blueprint_packs(self, blueprint: CompiledBlueprint) -> list[Pack]:
        """
        Lấy tất cả packs từ blueprint (CPs + DPs + RXs).

        Args:
            blueprint: CompiledBlueprint

        Returns:
            Danh sách Pack objects
        """
        packs: list[Pack] = []

        # Core Packs (mandatory + included)
        cp_ids = blueprint.core_packs.all_included
        for cp_id in cp_ids:
            pack = self.registry.get_pack(cp_id)
            if pack is not None:
                packs.append(pack)

        # Domain Packs
        for dp_ref in blueprint.domain_packs:
            pack = self.registry.get_pack(dp_ref.id)
            if pack is not None:
                packs.append(pack)

        # Regulatory Overlays
        for rx_ref in blueprint.regulatory_overlays:
            pack = self.registry.get_pack(rx_ref.id)
            if pack is not None:
                packs.append(pack)

        return packs

    def _build_emit_order(
        self,
        packs: list[Pack],
        resolutions: dict[str, PackResolution],
    ) -> list[CompositionNode]:
        """
        Build topological emit order.

        Thứ tự:
        1. Core Packs trước (P0 → P1 → P2 → P3 → P4)
        2. Domain Packs sau (theo thứ tự trong blueprint)
        3. Regulatory Overlays cuối (theo thứ tự trong blueprint)

        Trong mỗi nhóm, sort theo phase order + dependency order.

        Args:
            packs: Danh sách tất cả packs
            resolutions: Pack resolutions

        Returns:
            Danh sách CompositionNode theo emit order
        """
        nodes: list[CompositionNode] = []
        order_counter = 0

        # Chia packs theo type
        core_packs = [p for p in packs if p.pack_type == "core_pack"]
        domain_packs = [p for p in packs if p.pack_type == "domain_pack"]
        rx_packs = [p for p in packs if p.pack_type == "regulatory_overlay"]

        # Sort CPs theo phase + CP number (deterministic)
        core_packs.sort(key=lambda p: (
            PHASE_ORDER.get(p.phase or "P0", 0),
            int(p.id[2:]) if p.id[2:].isdigit() else 0
        ))

        # Emit Core Packs
        for pack in core_packs:
            order_counter += 1
            deps = self._get_pack_dependencies(pack, resolutions)
            nodes.append(CompositionNode(
                pack_id=pack.id,
                pack_type=pack.pack_type,
                emit_order=order_counter,
                phase=pack.phase or "P0",
                dependencies=deps,
            ))

        # Emit Domain Packs
        for pack in domain_packs:
            order_counter += 1
            deps = self._get_pack_dependencies(pack, resolutions)
            nodes.append(CompositionNode(
                pack_id=pack.id,
                pack_type=pack.pack_type,
                emit_order=order_counter,
                phase=pack.phase or "P1",
                dependencies=deps,
            ))

        # Emit Regulatory Overlays
        for pack in rx_packs:
            order_counter += 1
            deps = self._get_pack_dependencies(pack, resolutions)
            nodes.append(CompositionNode(
                pack_id=pack.id,
                pack_type=pack.pack_type,
                emit_order=order_counter,
                phase=pack.phase or "P1",
                dependencies=deps,
            ))

        return nodes

    def _get_pack_dependencies(self, pack: Pack, resolutions: dict[str, PackResolution]) -> list[str]:
        """
        Lấy dependencies của pack (chỉ những deps có trong resolutions).

        Args:
            pack: Pack cần lấy dependencies
            resolutions: Pack resolutions

        Returns:
            Danh sách dependency pack IDs
        """
        deps = pack.depends_on or []
        # Chỉ giữ lại những deps có trong resolutions
        return [d for d in deps if d in resolutions]

    def _build_template_mapping(
        self,
        mir_operations: list[str],
        resolutions: dict[str, PackResolution],
    ) -> dict[str, TemplateBinding]:
        """
        Build mapping từ MIR op_type → TemplateBinding.

        Process:
        1. Query registry cho packs cung cấp op_type
        2. Load pack.yml → get templates mapping
        3. Build TemplateBinding

        Args:
            mir_operations: Danh sách MIR op_types
            resolutions: Pack resolutions

        Returns:
            Mapping: op_type → TemplateBinding
        """
        mapping: dict[str, TemplateBinding] = {}

        # Tìm packs cho các operations
        relevant_packs = self.registry.resolve_packs_for_operations(mir_operations)

        for pack in relevant_packs:
            if pack.id not in resolutions:
                continue

            resolution = resolutions[pack.id]
            # Lấy capabilities từ taxonomy raw data
            caps = pack.raw.get("capabilities_provided", [])

            for cap in caps:
                if cap in mir_operations and cap not in mapping:
                    # Template path mặc định (sẽ được refine bởi pack.yml)
                    template_path = resolution.templates.get(cap, f"{pack.internal_id}/template.jinja2")
                    mapping[cap] = TemplateBinding(
                        op_type=cap,
                        pack_id=pack.id,
                        template_path=template_path,
                        stack="fastapi",  # Default stack
                    )

        return mapping

    def _build_stack_bindings(
        self,
        stacks: list[str],
        template_mapping: dict[str, TemplateBinding],
    ) -> dict[str, StackBinding]:
        """
        Build stack bindings cho các target stacks.

        Args:
            stacks: Danh sách stack names
            template_mapping: Template bindings

        Returns:
            Mapping: stack_name → StackBinding
        """
        bindings: dict[str, StackBinding] = {}

        for stack in stacks:
            # Lọc templates cho stack này
            stack_templates = [
                t for t in template_mapping.values() if t.stack == stack
            ]
            # Nếu không có stack-specific templates, dùng tất cả
            if not stack_templates:
                stack_templates = list(template_mapping.values())

            bindings[stack] = StackBinding(
                stack_name=stack,
                templates=stack_templates,
                stack_dir=f"midicoder/stacks/{stack}/",
            )

        return bindings

    def _validate_templates_exist(self, plan: CompositionPlan) -> None:
        """
        Validate template files tồn tại trên filesystem.

        Scan tất cả template paths trong template_mapping và stack_bindings.
        Nếu missing → thêm warning vào plan.

        Args:
            plan: CompositionPlan cần validate
        """
        stacks_root = Path(__file__).resolve().parent.parent.parent / "stacks"

        checked_paths: set[str] = set()

        # Kiểm tra templates trong template_mapping
        for binding in plan.template_mapping.values():
            path_key = f"{binding.stack}/{binding.template_path}"
            if path_key in checked_paths:
                continue
            checked_paths.add(path_key)

            # Tìm template trong core hoặc domain
            template_path = stacks_root / binding.stack / "core" / binding.template_path
            if not template_path.exists():
                template_path = stacks_root / binding.stack / "domain" / binding.template_path

            if not template_path.exists():
                plan.add_warning(
                    f"Template không tồn tại: {binding.template_path} "
                    f"(stack={binding.stack}, pack={binding.pack_id})"
                )

        # Kiểm tra templates trong stack bindings
        for stack_binding in plan.stack_bindings.values():
            for binding in stack_binding.templates:
                path_key = f"{binding.stack}/{binding.template_path}"
                if path_key in checked_paths:
                    continue
                checked_paths.add(path_key)

                template_path = stacks_root / binding.stack / "core" / binding.template_path
                if not template_path.exists():
                    template_path = stacks_root / binding.stack / "domain" / binding.template_path

                if not template_path.exists():
                    plan.add_warning(
                        f"Template không tồn tại: {binding.template_path} "
                        f"(stack={binding.stack})"
                    )

    def _validate_pack_status(self, plan: CompositionPlan) -> None:
        """
        Validate pack status — warn nếu có pack planned hoặc deprecated.

        Args:
            plan: CompositionPlan cần validate
        """
        for pack_id, resolution in plan.pack_resolution.items():
            if resolution.status == "planned":
                plan.add_warning(f"Pack {pack_id} đang ở trạng thái 'planned'")
            elif resolution.status == "deprecated":
                plan.add_warning(f"Pack {pack_id} đang ở trạng thái 'deprecated'")

    def _determine_stacks(self, blueprint: CompiledBlueprint) -> list[str]:
        """
        Xác định target stacks từ blueprint.

        Args:
            blueprint: CompiledBlueprint

        Returns:
            Danh sách stack names
        """
        # Nếu blueprint có target_profiles, map sang stacks
        if blueprint.target_profiles:
            stacks: list[str] = []
            for profile in blueprint.target_profiles:
                profile_stacks = PROFILE_TO_STACKS.get(profile, DEFAULT_STACKS)
                for s in profile_stacks:
                    if s not in stacks:
                        stacks.append(s)
            return stacks

        return DEFAULT_STACKS.copy()

    def _generate_blueprint_id(self, blueprint: CompiledBlueprint) -> str:
        """
        Generate unique blueprint ID.

        Args:
            blueprint: CompiledBlueprint

        Returns:
            Unique blueprint ID string
        """
        # Dùng industry id + timestamp để tạo unique ID
        industry_id = blueprint.industry.id or "unknown"
        version = blueprint.metadata.version or "0.0.0"
        return f"blueprint-{industry_id}-{version}"
