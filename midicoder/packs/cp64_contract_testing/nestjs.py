# coding: utf-8
"""
NestJS Emitter cho CP64: API Contract Testing (Pact).

Module này render Jinja2 templates để sinh contract testing code
cho NestJS stack, bao gồm contract module, consumer service,
provider service, và contract controller.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.packs.cp64_contract_testing.parser import ContractIR
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


__all__ = [
    "NestJSContractEmitter",
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


class NestJSContractEmitter:
    """Emitter cho NestJS stack — CP64 API Contract Testing (Pact).

    Render templates từ `stacks/nestjs/cp64_contract_testing/`
    để sinh contract testing code với NestJS modules, services,
    và controllers.
    """

    def __init__(self, stack_dir: str | Path) -> None:
        """Khởi tạo emitter.

        Args:
            stack_dir: Đường dẫn đến `stacks/nestjs/`.

        Raises:
            MidicoderError: Nếu template directory không tồn tại.
        """
        self.stack_dir = Path(stack_dir)
        self.template_dir = self.stack_dir / "cp64_contract_testing"

        if not self.template_dir.exists():
            raise EM.raise_error(
                ErrorCode.INVALID_CONFIG,
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
        ir: ContractIR,
        output_dir: str | Path,
    ) -> list[GeneratedFile]:
        """Emit contract testing code cho NestJS.

        Sinh 4 files:
        - contract.module.ts: NestJS module với providers
        - pact-consumer.service.ts: Consumer test service
        - pact-provider.service.ts: Provider verification service
        - contract.controller.ts: REST controller endpoints

        Args:
            ir: ContractIR chứa consumer specs và provider verifiers.
            output_dir: Đường dẫn output directory.

        Returns:
            Danh sách GeneratedFile.
        """
        output_dir = Path(output_dir)
        context = self._build_context(ir)
        files: list[GeneratedFile] = []

        templates = [
            ("contract.module.ts.jinja2", "src/contract/contract.module.ts"),
            ("pact-consumer.service.ts.jinja2", "src/contract/pact-consumer.service.ts"),
            ("pact-provider.service.ts.jinja2", "src/contract/pact-provider.service.ts"),
            ("contract.controller.ts.jinja2", "src/contract/contract.controller.ts"),
        ]

        for template_name, output_path in templates:
            if self._template_exists(template_name):
                content = self._render(template_name, context)
                files.append(GeneratedFile(path=output_path, content=content))

        return files

    def _build_context(self, ir: ContractIR) -> dict[str, Any]:
        """Xây dựng template context từ ContractIR."""
        consumer_specs_list = [c.to_dict() for c in ir.consumer_specs]
        provider_verifiers_list = [p.to_dict() for p in ir.provider_verifiers]
        broker_dict = ir.pact_broker_config.to_dict() if ir.pact_broker_config else None
        return {
            "consumer_specs": consumer_specs_list,
            "provider_verifiers": provider_verifiers_list,
            "pact_broker": broker_dict,
            "spec_count": len(ir.consumer_specs),
            "verifier_count": len(ir.provider_verifiers),
            "default_pact_version": ir.default_pact_version,
            "enable_auto_publish": ir.enable_auto_publish,
        }

    def _template_exists(self, name: str) -> bool:
        return (self.template_dir / name).exists()

    def _render(self, template_name: str, context: dict[str, Any]) -> str:
        try:
            template = self.env.get_template(template_name)
            return template.render(**context)
        except TemplateNotFound:
            raise EM.raise_error(
                ErrorCode.INVALID_CONFIG,
                reason=f"Jinja2 template không tìm thấy: {template_name}",
            )
        except Exception as e:
            raise EM.raise_error(
                ErrorCode.INVALID_CONFIG,
                reason=f"Render template thất bại {template_name}: {e}",
            )
