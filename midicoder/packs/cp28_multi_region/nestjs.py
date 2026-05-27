# coding: utf-8
"""
NestJS Emitter cho CP28: Multi-Region & Geo-Replication.

Module này render Jinja2 templates để sinh multi-region code
cho NestJS stack, bao gồm region module, region config service,
geo-routing interceptor, replication service, failover service,
health service, và data residency guard.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.packs.cp28_multi_region.models import (
    GeoRegionEntry,
    GeoRoutingRule,
    RegionConfig,
    ReplicationPolicy,
)
from midicoder.packs.cp28_multi_region.parser import MultiRegionIR


__all__ = [
    "NestJSMultiRegionEmitter",
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


class NestJSMultiRegionEmitter:
    """Emitter cho NestJS stack — CP28 Multi-Region & Geo-Replication.

    Render templates từ `stacks/nestjs/cp28_multi_region/`
    để sinh multi-region code cho NestJS application.
    """

    def __init__(self, stack_dir: str | Path) -> None:
        """Khởi tạo emitter.

        Args:
            stack_dir: Đường dẫn đến `stacks/nestjs/`.
        """
        self.stack_dir = Path(stack_dir)
        self.template_dir = self.stack_dir / "cp28_multi_region"

        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)) if self.template_dir.exists() else None,
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def emit(self, ir: MultiRegionIR | None = None) -> MultiRegionIR:
        """Emit MultiRegionIR được pre-fill cho NestJS.

        Nếu ir là None, tạo MultiRegionIR mặc định với:
        - 2 regions: us-east-1, eu-west-1
        - Async replication
        - Basic geo-routing

        Args:
            ir: MultiRegionIR hiện có (tùy chọn).

        Returns:
            MultiRegionIR đã được pre-fill cho NestJS.
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
        """Render tất cả NestJS templates cho multi-region.

        Sinh 7 files:
        - src/region/region.module.ts
        - src/region/services/region-config.service.ts
        - src/region/services/geo-routing.interceptor.ts
        - src/region/services/replication.service.ts
        - src/region/services/failover.service.ts
        - src/region/services/health.service.ts
        - src/region/guards/residency.guard.ts

        Args:
            ir: MultiRegionIR đã được pre-fill.

        Returns:
            Danh sách GeneratedFile.
        """
        context = self._build_context(ir)
        files: list[GeneratedFile] = []

        templates = [
            ("region_module.ts.jinja2", "src/region/region.module.ts"),
            ("region_config_service.ts.jinja2", "src/region/services/region-config.service.ts"),
            ("geo_routing_interceptor.ts.jinja2", "src/region/services/geo-routing.interceptor.ts"),
            ("replication_service.ts.jinja2", "src/region/services/replication.service.ts"),
            ("failover_service.ts.jinja2", "src/region/services/failover.service.ts"),
            ("health_service.ts.jinja2", "src/region/services/health.service.ts"),
            ("residency_guard.ts.jinja2", "src/region/guards/residency.guard.ts"),
        ]

        for template_name, output_path in templates:
            if self._template_exists(template_name):
                content = self._render(template_name, context)
                files.append(GeneratedFile(path=output_path, content=content))
            else:
                files.append(self._placeholder_typescript(output_path, template_name))

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

    def _placeholder_typescript(self, output_path: str, template_name: str) -> GeneratedFile:
        """Tạo placeholder TypeScript skeleton khi template không tìm thấy.

        Args:
            output_path: Đường dẫn output file.
            template_name: Tên template gốc.

        Returns:
            GeneratedFile với TypeScript skeleton.
        """
        # Extract class name from file name
        class_name = output_path.split("/")[-1].replace(".ts", "").replace("-", ".")
        # Convert dot-separated to PascalCase
        parts = class_name.split(".")
        class_name = "".join(p.capitalize() for p in parts)

        content = f'''/**
 * Placeholder cho CP28: Multi-Region & Geo-Replication.
 *
 * File: {output_path}
 * Template: {template_name} (không tìm thấy — sử dụng skeleton mặc định)
 *
 * @author Midicoder Team (auto-generated)
 */

// TODO: Implement {class_name}
// Template {template_name} không được tìm thấy trong template directory.
// Hãy tạo template hoặc implement manual.

export class {class_name} {{
  // Implement logic tại đây
}}
'''
        return GeneratedFile(path=output_path, content=content)
