# coding: utf-8
"""
NestJS Emitter cho I02: Kubernetes & Cloud Native Deployment.

Module này render Jinja2 templates để sinh Kubernetes manifest files
được pre-fill cho NestJS application (port 3000, health check /health, etc.).

Tác giả: Midicoder Team
Version: 2.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.packs.cp_infra_kubernetes.models import (
    K8sDeployment,
    K8sEnvVar,
    K8sPort,
    K8sResources,
    K8sService,
)
from midicoder.packs.cp_infra_kubernetes.parser import K8sIR


__all__ = [
    "NestJSK8sEmitter",
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


class NestJSK8sEmitter:
    """Emitter cho NestJS stack — I02 Kubernetes.

    Tạo K8sIR với các giá trị mặc định phù hợp cho NestJS app:
    - Port 3000
    - Health check /health
    - Resource defaults phù hợp cho Node.js/NestJS
    """

    def __init__(self, stack_dir: str | Path) -> None:
        """Khởi tạo emitter.

        Args:
            stack_dir: Đường dẫn đến `stacks/infrastructure/`.
        """
        self.stack_dir = Path(stack_dir)

    def emit(
        self,
        ir: K8sIR | None = None,
        output_dir: str | Path | None = None,
    ) -> K8sIR:
        """Emit K8sIR được pre-fill cho NestJS.

        Nếu ir đã có deployment, cập nhật với NestJS defaults.
        Nếu không, tạo deployment mặc định.

        Args:
            ir: K8sIR hiện có (tùy chọn).
            output_dir: Đường dẫn output (dùng cho tương lai).

        Returns:
            K8sIR đã được pre-fill cho NestJS.
        """
        if ir is None:
            ir = K8sIR()

        # Nếu chưa có deployment, tạo mặc định
        if not ir.deployments:
            deployment = K8sDeployment(
                id="nestjs-deployment",
                name="nestjs-app",
                replicas=2,
                image="nestjs-app:latest",
                ports=[K8sPort(container_port=3000, protocol="TCP", name="http")],
                resources=K8sResources(cpu="500m", memory="512Mi"),
                strategy="RollingUpdate",
                labels={"app": "nestjs-app"},
                env=[
                    K8sEnvVar(name="APP_HOST", value="0.0.0.0"),
                    K8sEnvVar(name="APP_PORT", value="3000"),
                    K8sEnvVar(name="NODE_ENV", value="production"),
                ],
                volume_mounts=[],
            )
            ir.deployments.append(deployment)
        else:
            # Cập nhật deployment đầu tiên với NestJS defaults
            dep = ir.deployments[0]
            if not dep.ports:
                dep.ports = [K8sPort(container_port=3000, protocol="TCP", name="http")]
            if not dep.labels:
                dep.labels = {"app": dep.name}

        # Nếu chưa có service, tạo mặc định
        if not ir.services:
            selector = ir.deployments[0].labels if ir.deployments[0].labels else {"app": "nestjs-app"}
            service = K8sService(
                id="nestjs-service",
                name="nestjs-app",
                type="ClusterIP",
                ports=[K8sPort(container_port=80, protocol="TCP", name="http")],
                selector=selector,
            )
            ir.services.append(service)

        return ir

    def render_manifests(self, ir: K8sIR) -> list[GeneratedFile]:
        """Render Kubernetes manifests từ K8sIR.

        Args:
            ir: K8sIR đã được pre-fill.

        Returns:
            Danh sách GeneratedFile.
        """
        files: list[GeneratedFile] = []

        # Render deployment manifest
        if ir.deployments:
            content = self._render_deployment(ir.deployments[0])
            files.append(GeneratedFile(path="k8s/deployment.yaml", content=content))

        # Render service manifest
        if ir.services:
            content = self._render_service(ir.services[0])
            files.append(GeneratedFile(path="k8s/service.yaml", content=content))

        return files

    def _render_deployment(self, deployment: K8sDeployment) -> str:
        """Render deployment manifest YAML."""
        ports_yaml = ""
        for p in deployment.ports:
            ports_yaml += f"            - containerPort: {p.container_port}\n"
            ports_yaml += f"              protocol: {p.protocol}\n"

        env_yaml = ""
        for e in deployment.env:
            env_yaml += f"            - name: {e.name}\n"
            if e.value is not None:
                env_yaml += f"              value: \"{e.value}\"\n"

        return f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {deployment.name}
  labels:
    app: {deployment.labels.get('app', deployment.name)}
spec:
  replicas: {deployment.replicas}
  strategy:
    type: {deployment.strategy}
  selector:
    matchLabels:
      app: {deployment.labels.get('app', deployment.name)}
  template:
    metadata:
      labels:
        app: {deployment.labels.get('app', deployment.name)}
    spec:
      containers:
        - name: {deployment.name}
          image: {deployment.image}
          ports:
{ports_yaml.rstrip()}
          resources:
            limits:
              cpu: {deployment.resources.cpu}
              memory: {deployment.resources.memory}
            requests:
              cpu: {deployment.resources.cpu}
              memory: {deployment.resources.memory}
          livenessProbe:
            httpGet:
              path: /health
              port: {deployment.ports[0].container_port if deployment.ports else 3000}
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /health
              port: {deployment.ports[0].container_port if deployment.ports else 3000}
            initialDelaySeconds: 5
            periodSeconds: 5
          env:
{env_yaml.rstrip()}
"""

    def _render_service(self, service: K8sService) -> str:
        """Render service manifest YAML."""
        selector_yaml = ""
        for k, v in service.selector.items():
            selector_yaml += f"    {k}: {v}\n"

        ports_yaml = ""
        for p in service.ports:
            ports_yaml += f"  - port: {p.container_port}\n"
            ports_yaml += f"    targetPort: {p.container_port}\n"
            ports_yaml += f"    protocol: {p.protocol}\n"

        return f"""apiVersion: v1
kind: Service
metadata:
  name: {service.name}
spec:
  type: {service.type}
  selector:
{selector_yaml.rstrip()}
  ports:
{ports_yaml.rstrip()}
"""
