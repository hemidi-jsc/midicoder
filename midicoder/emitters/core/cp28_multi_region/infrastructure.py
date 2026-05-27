# coding: utf-8
"""
Infrastructure Emitter cho CP28: Multi-Region & Geo-Replication.

Module này render Jinja2 templates để sinh infrastructure manifests
cho multi-region deployment, bao gồm Kubernetes multi-region deployment,
Route53 geo-routing, AWS failover Lambda, Terraform VPC peering,
và multi-cluster Kubernetes configuration.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.emitters.core.cp28_multi_region.models import (
    GeoRegionEntry,
    GeoRoutingRule,
    RegionConfig,
    ReplicationPolicy,
)
from midicoder.emitters.core.cp28_multi_region.parser import MultiRegionIR
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


__all__ = [
    "MultiRegionInfrastructureEmitter",
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


class MultiRegionInfrastructureEmitter:
    """Emitter cho infrastructure stack — CP28 Multi-Region & Geo-Replication.

    Render templates từ `stacks/infrastructure/core/cp28_multi_region/`
    để sinh infrastructure manifests cho multi-region deployment.
    """

    def __init__(self, stack_dir: str | Path) -> None:
        """Khởi tạo emitter.

        Args:
            stack_dir: Đường dẫn đến `stacks/infrastructure/core/`.

        Raises:
            MidicoderError: Nếu template directory không tồn tại.
        """
        self.stack_dir = Path(stack_dir)
        self.template_dir = self.stack_dir / "cp28_multi_region"

        if not self.template_dir.exists():
            raise EM.raise_error(
                ErrorCode.DSL_LOAD_FAILED,
                reason=f"Template directory không tìm thấy: {self.template_dir}",
            )

        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def emit(self, ir: MultiRegionIR | None = None) -> MultiRegionIR:
        """Emit MultiRegionIR được pre-fill cho infrastructure stack.

        Nếu ir là None, tạo MultiRegionIR mặc định với:
        - 2 regions: us-east-1, eu-west-1
        - Async replication
        - Basic geo-routing

        Args:
            ir: MultiRegionIR hiện có (tùy chọn).

        Returns:
            MultiRegionIR đã được pre-fill cho infrastructure.
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

    def render_manifests(self, ir: MultiRegionIR) -> list[GeneratedFile]:
        """Render infrastructure manifests cho multi-region deployment.

        Sinh 5 files:
        - multi-region/deployment-multi-region.yaml — K8s multi-region deployment
        - multi-region/route53-geo-routing.yaml — Route53 geo-routing records
        - multi-region/failover-lambda.py — AWS Lambda cho automated failover
        - multi-region/cross-region-vpc.tf — Terraform VPC peering
        - multi-region/multi-cluster-k8s.yaml — Multi-cluster K8s config

        Args:
            ir: MultiRegionIR đã được pre-fill.

        Returns:
            Danh sách GeneratedFile.
        """
        context = self._build_context(ir)
        files: list[GeneratedFile] = []

        templates = [
            ("deployment-multi-region.yaml.jinja2", "multi-region/deployment-multi-region.yaml", "yaml"),
            ("route53-geo-routing.yaml.jinja2", "multi-region/route53-geo-routing.yaml", "yaml"),
            ("failover-lambda.py.jinja2", "multi-region/failover-lambda.py", "python"),
            ("cross-region-vpc.tf.jinja2", "multi-region/cross-region-vpc.tf", "terraform"),
            ("multi-cluster-k8s.yaml.jinja2", "multi-region/multi-cluster-k8s.yaml", "yaml"),
        ]

        for template_name, output_path, lang in templates:
            if self._template_exists(template_name):
                content = self._render(template_name, context)
                files.append(GeneratedFile(path=output_path, content=content))
            else:
                files.append(self._placeholder(output_path, template_name, lang))

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
            "secondary_region": ir.regions[1].id if len(ir.regions) > 1 else "eu-west-1",
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

        Raises:
            MidicoderError: Nếu template không tìm thấy hoặc render thất bại.
        """
        try:
            template = self.env.get_template(template_name)
            return template.render(**context)
        except TemplateNotFound:
            raise EM.raise_error(
                ErrorCode.DSL_LOAD_FAILED,
                reason=f"Jinja2 template không tìm thấy: {template_name}",
            )
        except Exception as e:
            raise EM.raise_error(
                ErrorCode.DSL_LOAD_FAILED,
                reason=f"Render template thất bại {template_name}: {e}",
            )

    def _placeholder(self, output_path: str, template_name: str, lang: str) -> GeneratedFile:
        """Tạo placeholder file skeleton khi template không tìm thấy.

        Args:
            output_path: Đường dẫn output file.
            template_name: Tên template gốc.
            lang: Ngôn ngữ file (yaml, python, terraform).

        Returns:
            GeneratedFile với skeleton placeholder.
        """
        if lang == "yaml":
            content = f'''# CP28: Multi-Region & Geo-Replication
# File: {output_path}
# Template: {template_name} (không tìm thấy — sử dụng skeleton mặc định)

apiVersion: v1
kind: ConfigMap
metadata:
  name: multi-region-config
  labels:
    app: midicoder-ce
    cp: "28"
data:
  # TODO: Implement multi-region manifest
  # Template {template_name} không được tìm thấy.
'''
        elif lang == "python":
            content = f'''# coding: utf-8
"""
AWS Lambda cho CP28: Multi-Region & Geo-Replication.

File: {output_path}
Template: {template_name} (không tìm thấy — sử dụng skeleton mặc định)

Tác giả: Midicoder Team (auto-generated)
"""

from __future__ import annotations

import json
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def handler(event: dict, context: dict) -> dict:
    """AWS Lambda handler cho automated failover.

    TODO: Implement failover logic.
    Template {template_name} không được tìm thấy.
    """
    return {{
        "statusCode": 200,
        "body": json.dumps({{"message": "failover-placeholder"}}),
    }}
'''
        elif lang == "terraform":
            content = f'''# CP28: Multi-Region & Geo-Replication
# File: {output_path}
# Template: {template_name} (không tìm thấy — sử dụng skeleton mặc định)

# TODO: Implement cross-region VPC peering
# Template {template_name} không được tìm thấy.

resource "aws_vpc_peering_connection" "multi_region" {{
  vpc_id            = aws_vpc.primary.id
  peer_vpc_id       = aws_vpc.secondary.id
  peer_region       = "eu-west-1"
  auto_accept       = true

  tags = {{
    Name = "multi-region-vpc-peering"
    CP   = "28"
  }}
}}
'''
        else:
            content = f"# Placeholder: {output_path}\n# Template {template_name} không tìm thấy.\n"

        return GeneratedFile(path=output_path, content=content)
