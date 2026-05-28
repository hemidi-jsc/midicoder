# coding: utf-8
"""
Infrastructure Emitter cho I02: Kubernetes & Cloud Native Deployment.

Module này render Jinja2 templates để sinh Kubernetes manifest files
cho infrastructure stack, bao gồm deployment, service, ingress, HPA,
configmap, secret, PVC, và Helm Chart.yaml.

Tác giả: Midicoder Team
Version: 2.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.packs.cp_infra_kubernetes.parser import K8sIR
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


__all__ = [
    "K8sInfrastructureEmitter",
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


class K8sInfrastructureEmitter:
    """Emitter cho infrastructure stack — CP54 Kubernetes & Cloud Native.

    Render templates từ `stacks/infrastructure/cp_infra_kubernetes/`
    để sinh Kubernetes manifest files và Helm Chart.yaml.
    """

    def __init__(self, stack_dir: str | Path) -> None:
        """Khởi tạo emitter.

        Args:
            stack_dir: Đường dẫn đến `stacks/infrastructure/`.

        Raises:
            MidicoderError: Nếu template directory không tồn tại.
        """
        self.stack_dir = Path(stack_dir)
        self.template_dir = self.stack_dir / "cp_infra_kubernetes"

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

    def emit(
        self,
        ir: K8sIR,
        output_dir: str | Path,
    ) -> list[GeneratedFile]:
        """Emit Kubernetes manifest files.

        Sinh các files dựa trên resources có trong K8sIR:
        - k8s/deployment.yaml (nếu có deployments)
        - k8s/service.yaml (nếu có services)
        - k8s/ingress.yaml (nếu có ingresses)
        - k8s/hpa.yaml (nếu có hpas)
        - k8s/configmap.yaml (nếu có configmaps)
        - k8s/secret.yaml (nếu có secrets)
        - k8s/pvc.yaml (nếu có pvcs)
        - helm/Chart.yaml (luôn sinh)

        Args:
            ir: K8sIR chứa Kubernetes resources.
            output_dir: Đường dẫn output directory.

        Returns:
            Danh sách GeneratedFile.
        """
        output_dir = Path(output_dir)
        context = self._build_context(ir)
        files: list[GeneratedFile] = []

        templates = [
            ("k8s/deployment.yaml.jinja2", "k8s/deployment.yaml", "deployments"),
            ("k8s/service.yaml.jinja2", "k8s/service.yaml", "services"),
            ("k8s/ingress.yaml.jinja2", "k8s/ingress.yaml", "ingresses"),
            ("k8s/hpa.yaml.jinja2", "k8s/hpa.yaml", "hpas"),
            ("k8s/configmap.yaml.jinja2", "k8s/configmap.yaml", "configmaps"),
            ("k8s/secret.yaml.jinja2", "k8s/secret.yaml", "secrets"),
            ("k8s/pvc.yaml.jinja2", "k8s/pvc.yaml", "pvcs"),
            ("helm/Chart.yaml.jinja2", "helm/Chart.yaml", None),
        ]

        for template_name, output_path, resource_key in templates:
            # Bỏ template nếu không có resource tương ứng
            if resource_key and not context.get(resource_key):
                continue
            if self._template_exists(template_name):
                content = self._render(template_name, context)
                files.append(GeneratedFile(path=output_path, content=content))

        return files

    def _build_context(self, ir: K8sIR) -> dict[str, Any]:
        """Xây dựng template context từ K8sIR."""
        return {
            "deployments": [d.to_dict() for d in ir.deployments],
            "services": [s.to_dict() for s in ir.services],
            "ingresses": [i.to_dict() for i in ir.ingresses],
            "hpas": [h.to_dict() for h in ir.hpas],
            "configmaps": [c.to_dict() for c in ir.configmaps],
            "secrets": [s.to_dict() for s in ir.secrets],
            "pvcs": [p.to_dict() for p in ir.pvcs],
            "deployment_count": len(ir.deployments),
            "service_count": len(ir.services),
            "ingress_count": len(ir.ingresses),
            "hpa_count": len(ir.hpas),
            "configmap_count": len(ir.configmaps),
            "secret_count": len(ir.secrets),
            "pvc_count": len(ir.pvcs),
        }

    def _template_exists(self, name: str) -> bool:
        """Kiểm tra template có tồn tại không."""
        return (self.template_dir / name).exists()

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
