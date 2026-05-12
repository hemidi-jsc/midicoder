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

        Thứ tự tìm:
        - core_pack → emitters/core/{internal_id}/
        - domain_pack → emitters/domain/{internal_id}/
        - regulatory_overlay → emitters/regulatory/{internal_id}/

        Args:
            pack: Pack cần tìm

        Returns:
            Path đến pack directory hoặc None
        """
        base_dir = self.midicoder_root / "emitters"

        if pack.pack_type == "core_pack":
            # Dùng internal_id làm directory name
            dir_name = pack.internal_id
            if dir_name is None:
                # Fallback: thử các tên phổ biến
                dir_name = self._cp_id_to_dir_name(pack.id)
            return base_dir / "core" / dir_name

        elif pack.pack_type == "domain_pack":
            dir_name = self._dp_id_to_dir_name(pack.id)
            return base_dir / "domain" / dir_name

        elif pack.pack_type == "regulatory_overlay":
            dir_name = self._rx_id_to_dir_name(pack.id)
            return base_dir / "regulatory" / dir_name

        return None

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
        elif pack.pack_type == "domain_pack":
            num = pack.id.replace("DP", "").zfill(2)
            return f"dp{num}-{short_name}"
        elif pack.pack_type == "regulatory_overlay":
            num = pack.id.replace("RX", "").zfill(2)
            return f"rx{num}-{short_name}"

        return f"{pack.pack_type}-{pack.id}"

    def _cp_id_to_dir_name(self, cp_id: str) -> str:
        """Map CP ID → directory name (snake_case internal_id, matches folder name verbatim)."""
        mapping = {
            "CP01": "cp01_domain_model",
            "CP02": "cp02_multi_tenant",
            "CP03": "cp03_auth",
            "CP04": "cp04_rbac",
            "CP05": "cp05_event_driven",
            "CP06": "cp06_api_gateway",
            "CP07": "cp07_iac",
            "CP08": "cp08_database",
            "CP09": "cp09_cache",
            "CP10": "cp10_search",
            "CP11": "cp11_file_media",
            "CP12": "cp12_notification",
            "CP13": "cp13_workflow_runtime",
            "CP14": "cp14_audit_compliance",
            "CP15": "cp15_observability",
            "CP16": "cp16_monitoring",
            "CP17": "cp17_bi_analytics",
            "CP18": "cp18_frontend_framework",
            "CP19": "cp19_ui_components",
            "CP20": "cp20_api_client",
            "CP51": "cp51_blueprint",
            "CP52": "cp52_invariant",
            "CP53": "cp53_domain_bridge",
        }
        return mapping.get(cp_id, cp_id.lower())

    def _dp_id_to_dir_name(self, dp_id: str) -> str:
        """Map DP ID → directory name."""
        mapping = {
            "DP01": "commerce",
            "DP02": "marketplace",
            "DP03": "travel",
            "DP04": "logistics",
            "DP05": "manufacturing",
            "DP11": "banking",
            "DP12": "payments",
        }
        return mapping.get(dp_id, dp_id.lower())

    def _rx_id_to_dir_name(self, rx_id: str) -> str:
        """Map RX ID → directory name."""
        mapping = {
            "RX01": "privacy",
            "RX02": "financial",
            "RX04": "clinical",
            "RX11": "audit",
        }
        return mapping.get(rx_id, rx_id.lower())