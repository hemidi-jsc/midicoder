# coding: utf-8
"""
FastAPI Emitter cho CP64: API Contract Testing (Pact).

Module này render Jinja2 templates để sinh contract testing code
cho FastAPI stack, bao gồm contract service, consumer test,
provider verifier, và contract router.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.packs.cp_backend_contract_testing.parser import ContractIR
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


__all__ = [
    "FastAPIContractEmitter",
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


class FastAPIContractEmitter:
    """Emitter cho FastAPI stack — CP64 API Contract Testing (Pact).

    Render templates từ `stacks/fastapi/cp_backend_contract_testing/`
    để sinh contract testing code.
    """

    def __init__(self, stack_dir: str | Path) -> None:
        """Khởi tạo emitter.

        Args:
            stack_dir: Đường dẫn đến `stacks/fastapi/`.

        Raises:
            MidicoderError: Nếu template directory không tồn tại.
        """
        self.stack_dir = Path(stack_dir)
        self.template_dir = self.stack_dir / "cp_backend_contract_testing"

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
        """Emit contract testing code cho FastAPI.

        Sinh 4 files:
        - contract_service.py: Service chính quản lý contract lifecycle
        - pact_consumer_test.py: Consumer test với mocked provider
        - pact_provider_verifier.py: Provider verification script
        - contract_router.py: API endpoints cho contract status

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
            ("contract_service.py.jinja2", "app/services/contract_service.py"),
            ("pact_consumer_test.py.jinja2", "tests/contract/pact_consumer_test.py"),
            ("pact_provider_verifier.py.jinja2", "tests/contract/pact_provider_verifier.py"),
            ("contract_router.py.jinja2", "app/api/contract_router.py"),
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
