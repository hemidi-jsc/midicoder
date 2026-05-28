# coding: utf-8
"""
Infrastructure Emitter cho I04: Environment & Secret Management.

Module này render Jinja2 templates để sinh infrastructure files
cho environment và secret management, bao gồm Vault policy,
Kubernetes Secret, và .env template.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.packs.cp_infra_env_secrets.parser import EnvIR
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


__all__ = [
    "EnvInfrastructureEmitter",
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


class EnvInfrastructureEmitter:
    """Emitter cho Infrastructure stack — I04 Environment & Secret Management.

    Render templates từ `stacks/infrastructure/cp_infra_env_secrets/`
    để sinh các file infrastructure: Vault policy, Vault setup,
    Kubernetes Secret, và .env template.
    """

    def __init__(self, stack_dir: str | Path) -> None:
        """Khởi tạo emitter.

        Args:
            stack_dir: Đường dẫn đến `stacks/infrastructure/`.

        Raises:
            MidicoderError: Nếu template directory không tồn tại.
        """
        self.stack_dir = Path(stack_dir)
        self.template_dir = self.stack_dir / "cp_infra_env_secrets"

        if not self.template_dir.exists():
            raise EM.raise_error(
                ErrorCode.MDC-I05_ENV_CONFIG_INVALID,
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
        ir: EnvIR,
        output_dir: str | Path,
    ) -> list[GeneratedFile]:
        """Emit infrastructure files cho environment & secret management.

        Sinh tối đa 4 files:
        - infra/vault-policy.hcl (Vault policy)
        - infra/vault-setup.sh (Vault setup script)
        - k8s/secret.yaml (Kubernetes Secret)
        - .env.template (Template biến môi trường)

        Args:
            ir: EnvIR chứa env configs, vault configs, KMS configs.
            output_dir: Đường dẫn output directory.

        Returns:
            Danh sách GeneratedFile.
        """
        output_dir = Path(output_dir)
        context = self._build_context(ir)
        files: list[GeneratedFile] = []

        templates = [
            ("vault-policy.hcl.jinja2", "infra/vault-policy.hcl"),
            ("vault-setup.sh.jinja2", "infra/vault-setup.sh"),
            ("k8s-secret.yaml.jinja2", "k8s/secret.yaml"),
            ("env-template.jinja2", ".env.template"),
        ]

        for template_name, output_path in templates:
            if self._template_exists(template_name):
                content = self._render(template_name, context)
                files.append(GeneratedFile(path=output_path, content=content))

        return files

    def _build_context(self, ir: EnvIR) -> dict[str, Any]:
        """Xây dựng template context từ EnvIR."""
        env_list = [e.to_dict() for e in ir.env_configs]
        secret_list = [s.to_dict() for s in ir.secret_configs]
        vault_list = [v.to_dict() for v in ir.vault_configs]
        kms_list = [k.to_dict() for k in ir.kms_configs]
        configmap_list = [c.to_dict() for c in ir.configmap_refs]

        # Gom tất cả variables
        all_variables: dict[str, str] = {}
        all_required: list[str] = []
        for e in ir.env_configs:
            all_variables.update(e.variables)
            all_required.extend(e.required_vars)

        return {
            "env_configs": env_list,
            "secret_configs": secret_list,
            "vault_configs": vault_list,
            "kms_configs": kms_list,
            "configmap_refs": configmap_list,
            "all_variables": all_variables,
            "all_required": list(dict.fromkeys(all_required)),
            "env_count": len(ir.env_configs),
            "secret_count": len(ir.secret_configs),
            "vault_count": len(ir.vault_configs),
            "kms_count": len(ir.kms_configs),
            "has_vault": bool(ir.vault_configs),
            "has_kms": bool(ir.kms_configs),
            "has_configmap": bool(ir.configmap_refs),
        }

    def _template_exists(self, name: str) -> bool:
        return (self.template_dir / name).exists()

    def _render(self, template_name: str, context: dict[str, Any]) -> str:
        try:
            template = self.env.get_template(template_name)
            return template.render(**context)
        except TemplateNotFound:
            raise EM.raise_error(
                ErrorCode.MDC-I05_ENV_CONFIG_INVALID,
                reason=f"Jinja2 template không tìm thấy: {template_name}",
            )
        except Exception as e:
            raise EM.raise_error(
                ErrorCode.GENERATION_FAILED,
                reason=f"Render template thất bại {template_name}: {e}",
            )
