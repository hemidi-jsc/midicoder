"""
InvariantRegistry: Singleton quản lý đăng ký và query invariants.

Registry lưu trữ tất cả InvariantDefinition đã được đăng ký,
hỗ trợ query theo category, overlay, domain và blueprint.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .models import InvariantCategory, InvariantDefinition

if TYPE_CHECKING:
    from typing import Any as CompiledBlueprint  # type: ignore  # blueprint_compiler removed


class InvariantRegistry:
    """
    Singleton registry cho tất cả InvariantDefinition.

    Cung cấp API để:
    - Đăng ký invariant mới
    - Query invariant theo id, category, overlay, domain
    - Lấy invariants cho một blueprint cụ thể

    Usage:
        registry = InvariantRegistry()
        registry.register(invariant_def)
        inv = registry.get("INV-BIZ-001")
        biz_invs = registry.get_by_category(InvariantCategory.BUSINESS)
    """

    _instance: InvariantRegistry | None = None

    def __new__(cls) -> InvariantRegistry:
        """Singleton pattern: trả về instance duy nhất."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._invariants: dict[str, InvariantDefinition] = {}
            cls._instance._domain_invariants: dict[str, list[InvariantDefinition]] = {}
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """
        Reset registry (dùng cho testing).

        Xóa tất cả invariants đã đăng ký.
        """
        cls._instance = None

    def register(self, invariant: InvariantDefinition) -> None:
        """
        Đăng ký invariant vào registry.

        Args:
            invariant: InvariantDefinition cần đăng ký

        Raises:
            ValueError: Nếu invariant id đã tồn tại
        """
        if invariant.id in self._invariants:
            raise ValueError(f"Invariant '{invariant.id}' đã tồn tại trong registry")
        self._invariants[invariant.id] = invariant

        # Index theo domain nếu có
        if invariant.domain:
            if invariant.domain not in self._domain_invariants:
                self._domain_invariants[invariant.domain] = []
            self._domain_invariants[invariant.domain].append(invariant)

    def get(self, invariant_id: str) -> InvariantDefinition:
        """
        Lấy invariant theo id.

        Args:
            invariant_id: ID của invariant

        Returns:
            InvariantDefinition

        Raises:
            KeyError: Nếu invariant không tồn tại
        """
        if invariant_id not in self._invariants:
            raise KeyError(f"Invariant '{invariant_id}' không tồn tại trong registry")
        return self._invariants[invariant_id]

    def is_registered(self, invariant_id: str) -> bool:
        """
        Kiểm tra invariant có được đăng ký không.

        Args:
            invariant_id: ID của invariant

        Returns:
            True nếu đã đăng ký, False nếu chưa
        """
        return invariant_id in self._invariants

    def get_by_category(self, category: InvariantCategory) -> list[InvariantDefinition]:
        """
        Lấy tất cả invariants theo category.

        Args:
            category: InvariantCategory cần lọc

        Returns:
            Danh sách InvariantDefinition thuộc category
        """
        return [
            inv for inv in self._invariants.values()
            if inv.category == category
        ]

    def get_by_overlay(self, rx_id: str) -> list[InvariantDefinition]:
        """
        Lấy tất cả invariants thuộc regulatory overlay.

        Args:
            rx_id: Regulatory overlay ID (RX01-RX12)

        Returns:
            Danh sách InvariantDefinition thuộc overlay
        """
        return [
            inv for inv in self._invariants.values()
            if inv.overlay == rx_id
        ]

    def get_by_domain(self, dp_id: str) -> list[InvariantDefinition]:
        """
        Lấy tất cả invariants thuộc domain pack.

        Args:
            dp_id: Domain pack ID (DP01-DP26)

        Returns:
            Danh sách InvariantDefinition thuộc domain
        """
        return self._domain_invariants.get(dp_id, [])

    def get_for_blueprint(self, blueprint: CompiledBlueprint) -> list[InvariantDefinition]:
        """
        Lấy tất cả invariants liên quan đến blueprint.

        Invariants được trả về bao gồm:
        1. Invariants trong blueprint invariants config
        2. Invariants từ regulatory overlays của blueprint
        3. Invariants từ domain packs của blueprint

        Args:
            blueprint: CompiledBlueprint cần lấy invariants

        Returns:
            Danh sách InvariantDefinition liên quan
        """
        result: dict[str, InvariantDefinition] = {}

        # 1. Invariants từ blueprint config
        if hasattr(blueprint, 'invariants'):
            for biz_inv in blueprint.invariants.business:
                inv_id = biz_inv if isinstance(biz_inv, str) else biz_inv.get("id", "")
                if inv_id and inv_id in self._invariants:
                    result[inv_id] = self._invariants[inv_id]

            for comp_inv in blueprint.invariants.compliance:
                inv_id = comp_inv if isinstance(comp_inv, str) else comp_inv.get("id", "")
                if inv_id and inv_id in self._invariants:
                    result[inv_id] = self._invariants[inv_id]

            for fm_inv in blueprint.invariants.failure_modes:
                inv_id = fm_inv if isinstance(fm_inv, str) else fm_inv.get("id", "")
                if inv_id and inv_id in self._invariants:
                    result[inv_id] = self._invariants[inv_id]

        # 2. Invariants từ regulatory overlays
        if hasattr(blueprint, 'regulatory_overlays'):
            for rx in blueprint.regulatory_overlays:
                rx_id = rx if isinstance(rx, str) else rx.get("id", "")
                for inv in self.get_by_overlay(rx_id):
                    result[inv.id] = inv

        # 3. Invariants từ domain packs
        if hasattr(blueprint, 'domain_packs'):
            for dp in blueprint.domain_packs:
                dp_id = dp if isinstance(dp, str) else dp.get("id", "")
                for inv in self.get_by_domain(dp_id):
                    result[inv.id] = inv

        return list(result.values())

    def get_all(self) -> list[InvariantDefinition]:
        """
        Lấy tất cả invariants đã đăng ký.

        Returns:
            Danh sách tất cả InvariantDefinition
        """
        return list(self._invariants.values())

    @property
    def count(self) -> int:
        """Số lượng invariants đã đăng ký."""
        return len(self._invariants)

    def to_dict(self) -> dict[str, Any]:
        """
        Chuyển toàn bộ registry sang dict.

        Returns:
            Dictionary với tất cả invariants
        """
        return {
            inv_id: inv.to_dict()
            for inv_id, inv in self._invariants.items()
        }