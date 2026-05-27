"""
PackResolver — Resolve packs từ TaxonomyRegistry.

Module này cung cấp khả năng:
- Query TaxonomyRegistry để lấy pack info
- Load pack.yml từ filesystem
- Extract capabilities_provided + templates mapping
- Validate pack status

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from industry.registry import TaxonomyRegistry, Pack
from midicoder.contracts.registry import CP_ID_TO_INTERNAL
from .models import PackResolution


class PackResolver:
    """
    Resolver cho packs — query taxonomy + load pack.yml.

    Trách nhiệm:
    - Resolve pack info từ TaxonomyRegistry
    - Load pack.yml từ filesystem
    - Validate pack status
    - Build PackResolution objects

    Attributes:
        registry: TaxonomyRegistry instance
        midicoder_root: Đường dẫn đến thư mục midicoder/
    """

    def __init__(
        self,
        registry: TaxonomyRegistry,
        midicoder_root: Path | None = None,
    ):
        """
        Khởi tạo PackResolver.

        Args:
            registry: TaxonomyRegistry đã load
            midicoder_root: Đường dẫn đến midicoder/ (default: auto-detect)
        """
        self.registry = registry
        if midicoder_root is None:
            # Auto-detect: đi lên từ file này
            self.midicoder_root = Path(__file__).resolve().parent.parent.parent
        else:
            self.midicoder_root = Path(midicoder_root)

    def resolve_pack(self, pack: Pack) -> PackResolution | None:
        """
        Resolve một pack thành PackResolution.

        Process:
        1. Lấy pack info từ registry
        2. Tìm và load pack.yml
        3. Extract capabilities_provided + templates
        4. Return PackResolution

        Args:
            pack: Pack object từ registry

        Returns:
            PackResolution hoặc None nếu không thể resolve
        """
        # Xác định directory và type based trên pack type
        pack_dir = self._find_pack_directory(pack)
        pack_yml_path = ""
        capabilities: list[str] = []
        templates: dict[str, str] = {}

        if pack_dir is not None:
            pack_yml_file = pack_dir / "pack.yml"
            if pack_yml_file.exists():
                pack_yml_path = str(pack_yml_file)
                data = self._load_pack_yml(pack_yml_file)
                capabilities = data.get("capabilities_provided", [])
                templates = data.get("templates", {})

        return PackResolution(
            pack_id=pack.id,
            pack_type=pack.pack_type,
            internal_id=pack.internal_id or self._generate_internal_id(pack),
            status=pack.status,
            capabilities_provided=capabilities,
            templates=templates,
            pack_yml_path=pack_yml_path,
        )

    def resolve_packs(self, packs: list[Pack]) -> dict[str, PackResolution]:
        """
        Resolve danh sách packs.

        Args:
            packs: Danh sách Pack objects

        Returns:
            Mapping: pack_id → PackResolution
        """
        result: dict[str, PackResolution] = {}
        for pack in packs:
            resolution = self.resolve_pack(pack)
            if resolution is not None:
                result[pack.id] = resolution
        return result

    def _find_pack_directory(self, pack: Pack) -> Path | None:
        """
        Tìm directory chứa pack code.

        Single-layer: tất cả packs nằm trong `midicoder/packs/{internal_id}/`

        Args:
            pack: Pack cần tìm

        Returns:
            Path đến pack directory hoặc None
        """
        packs_dir = self.midicoder_root / "packs"

        # Dùng internal_id làm directory name
        dir_name = pack.internal_id
        if dir_name is None:
            # Fallback: dùng single source mapping
            dir_name = CP_ID_TO_INTERNAL.get(pack.id, pack.id.lower())

        return packs_dir / dir_name

    def _load_pack_yml(self, path: Path) -> dict[str, Any]:
        """
        Load và parse pack.yml.

        Args:
            path: Đường dẫn đến pack.yml

        Returns:
            Parsed YAML data
        """
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def _generate_internal_id(self, pack: Pack) -> str:
        """
        Generate internal_id từ pack info.

        Args:
            pack: Pack cần generate

        Returns:
            Internal ID string
        """
        # Format: {type}{number}-{name-short}
        name_parts = pack.name.lower().split()
        short_name = "".join(name_parts[:2]) if name_parts else "unknown"

        if pack.pack_type == "core_pack":
            num = pack.id.replace("CP", "").zfill(2)
            return f"cp{num}-{short_name}"

        return f"{pack.pack_type}-{pack.id}"

    def _rx_id_to_dir_name(self, rx_id: str) -> str:
        """Map RX ID → directory name (deprecated, kept for backward compat)."""
        return rx_id.lower()
