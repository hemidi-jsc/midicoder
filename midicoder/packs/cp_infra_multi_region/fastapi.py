# coding: utf-8
"""
FastAPI Emitter cho I05: Multi-Region & Geo-Replication.

Module này render Jinja2 templates để sinh multi-region code
cho FastAPI stack, bao gồm region configuration, geo-routing middleware,
replication service, failover service, health check, data residency enforcement,
và region-aware API routes.

Tác giả: Midicoder Team
Version: 2.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.packs.cp_infra_multi_region.models import (
    GeoRegionEntry,
    GeoRoutingRule,
    RegionConfig,
    ReplicationPolicy,
)
from midicoder.packs.cp_infra_multi_region.parser import MultiRegionIR


__all__ = [
    "FastAPIMultiRegionEmitter",
    "GeneratedFile",
]


@dataclass
class GeneratedFile:
    """File đã generate.

    Attributes:
        path: Đường dẫn relative của file.
        content: Nội dung file.
    """
    path: str
    content: str


class FastAPIMultiRegionEmitter:
    """Emitter cho FastAPI stack — I05 Multi-Region & Geo-Replication.

    Render templates từ `stacks/fastapi/cp_infra_multi_region/`
    để sinh multi-region code cho FastAPI application.
    """

    def __init__(self, stack_dir: str | Path) -> None:
        """Khởi tạo emitter.

        Args:
            stack_dir: Đường dẫn đến `stacks/fastapi/`.
        """
        self.stack_dir = Path(stack_dir)
        self.template_dir = self.stack_dir / "cp_infra_multi_region"

        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)) if self.template_dir.exists() else None,
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def emit(self, ir: MultiRegionIR | None = None) -> MultiRegionIR:
        """Emit MultiRegionIR được pre-fill cho FastAPI.

        Nếu ir là None, tạo MultiRegionIR mặc định với:
        - 2 regions: us-east-1, eu-west-1
        - Async replication
        - Basic geo-routing

        Args:
            ir: MultiRegionIR hiện có (tùy chọn).

        Returns:
            MultiRegionIR đã được pre-fill cho FastAPI.
        """
        if ir is None:
            ir = MultiRegionIR()

        # Nếu chưa có regions, tạo mặc định
        if not ir.regions:
            primary = RegionConfig(
                id="us-east-1",
                name="US East (N. Virginia)",
                cloud_provider="aws",
                availability_zones=["us-east-1a", "us-east-1b", "us-east-1c"],
                primary=True,
                endpoint_url="https://api.us-east-1.example.com",
            )
            secondary = RegionConfig(
                id="eu-west-1",
                name="EU West (Ireland)",
                cloud_provider="aws",
                availability_zones=["eu-west-1a", "eu-west-1b", "eu-west-1c"],
                primary=False,
                endpoint_url="https://api.eu-west-1.example.com",
            )
            ir.regions.extend([primary, secondary])

        # Nếu chưa có replication policies, tạo mặc định (async)
        if not ir.replication_policies:
            ir.replication_policies.append(ReplicationPolicy(
                id="default-replication",
                name="Default async replication",
                mode="async",
                source_region="us-east-1",
                target_regions=["eu-west-1"],
                lag_threshold_ms=30000,
                conflict_resolution="source_wins",
                tables=[],
            ))

        # Nếu chưa có geo-routing rules, tạo mặc định
        if not ir.geo_routing_rules:
            ir.geo_routing_rules.append(GeoRoutingRule(
                id="geo-na",
                name="North America routing",
                strategy="latency",
                regions=[
                    GeoRegionEntry(region="us-east-1", weight=10),
                    GeoRegionEntry(region="eu-west-1", weight=1),
                ],
                fallback_region="eu-west-1",
                health_check_path="/health",
            ))
            ir.geo_routing_rules.append(GeoRoutingRule(
                id="geo-eu",
                name="Europe routing",
                strategy="geographic",
                regions=[
                    GeoRegionEntry(region="eu-west-1", weight=10),
                    GeoRegionEntry(region="us-east-1", weight=1),
                ],
                fallback_region="us-east-1",
                health_check_path="/health",
            ))

        return ir

    def render_files(self, ir: MultiRegionIR) -> list[GeneratedFile]:
        """Render tất cả FastAPI templates cho multi-region.

        Sinh 8 files:
        - app/config/region_config.py — region configuration constants
        - app/middleware/geo_routing_middleware.py — latency-based geo-routing middleware
        - app/services/replication_service.py — cross-region replication service
        - app/services/failover_service.py — automated failover service
        - app/services/region_health.py — per-region health check service
        - app/services/residency_enforcer.py — data residency enforcement service
        - app/api/region_router.py — region management API routes
        - app/dependencies.py — region-aware dependencies

        Args:
            ir: MultiRegionIR đã được pre-fill.

        Returns:
            Danh sách GeneratedFile.
        """
        context = self._build_context(ir)
        files: list[GeneratedFile] = []

        templates = [
            ("region_config.py.jinja2", "app/config/region_config.py"),
            ("geo_routing_middleware.py.jinja2", "app/middleware/geo_routing_middleware.py"),
            ("replication_service.py.jinja2", "app/services/replication_service.py"),
            ("failover_service.py.jinja2", "app/services/failover_service.py"),
            ("region_health.py.jinja2", "app/services/region_health.py"),
            ("residency_enforcer.py.jinja2", "app/services/residency_enforcer.py"),
            ("region_router.py.jinja2", "app/api/region_router.py"),
            ("dependencies.py.jinja2", "app/dependencies.py"),
        ]

        for template_name, output_path in templates:
            if self._template_exists(template_name):
                content = self._render(template_name, context)
                files.append(GeneratedFile(path=output_path, content=content))
            else:
                files.append(self._placeholder_python(output_path, template_name))

        return files

    def _build_context(self, ir: MultiRegionIR) -> dict[str, Any]:
        """Xây dựng template context từ MultiRegionIR."""
        return {
            "regions": [r.to_dict() for r in ir.regions],
            "replication_policies": [rp.to_dict() for rp in ir.replication_policies],
            "geo_routing_rules": [r.to_dict() for r in ir.geo_routing_rules],
            "failover_policies": [fp.to_dict() for fp in ir.failover_policies],
            "data_residency_rules": [dr.to_dict() for dr in ir.data_residency_rules],
            "health_checks": [hc.to_dict() for hc in ir.health_checks],
            "region_count": len(ir.regions),
            "has_replication": bool(ir.replication_policies),
            "replication_mode": ir.replication_policies[0].mode if ir.replication_policies else "async",
            "primary_region": ir.regions[0].id if ir.regions else "us-east-1",
        }

    def _template_exists(self, name: str) -> bool:
        """Kiểm tra template có tồn tại không."""
        return self.template_dir.exists() and (self.template_dir / name).exists()

    def _render(self, template_name: str, context: dict[str, Any]) -> str:
        """Render Jinja2 template.

        Args:
            template_name: Tên file template.
            context: Context dict cho template.

        Returns:
            Nội dung đã render.
        """
        template = self.env.get_template(template_name)
        return template.render(**context)

    def _placeholder_python(self, output_path: str, template_name: str) -> GeneratedFile:
        """Tạo placeholder Python code skeleton khi template không tìm thấy.

        Args:
            output_path: Đường dẫn output file.
            template_name: Tên template gốc.

        Returns:
            GeneratedFile với Python skeleton.
        """
        module_name = output_path.replace("/", ".").replace(".py", "")

        content = f'''# coding: utf-8
"""
Module placeholder cho CP28: Multi-Region & Geo-Replication.

File: {output_path}
Template: {template_name} (không tìm thấy — sử dụng skeleton mặc định)

Tác giả: Midicoder Team (auto-generated)
"""

from __future__ import annotations

# TODO: Implement {module_name}
# Template {template_name} không được tìm thấy trong template directory.
# Hãy tạo template hoặc implement manual.


__all__ = []
'''
        return GeneratedFile(path=output_path, content=content)
