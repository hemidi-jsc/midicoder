# coding: utf-8
"""
FastAPI Emitter cho CP59: Tenant Billing & Invoicing.

Module này render Jinja2 templates để sinh billing & invoicing code
cho FastAPI stack, bao gồm models, schemas, service, router,
webhook handler, và invoice generator.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.packs.cp_full_tenant_billing.parser import BillingIR
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


__all__ = [
    "FastAPITenantBillingEmitter",
    "GeneratedFile",
]


@dataclass
class GeneratedFile:
    """File đã generate.

    Attributes:
        path: Duong dan relative cua file.
        content: Noi dung file.
    """
    path: str
    content: str


class FastAPITenantBillingEmitter:
    """Emitter cho FastAPI stack — CP59 Tenant Billing & Invoicing.

    Render templates tu `stacks/fastapi/cp_full_tenant_billing/`
    de sinh billing & invoicing code.
    """

    def __init__(self, stack_dir: str | Path) -> None:
        """Khoi tao emitter.

        Args:
            stack_dir: Duong dan den `stacks/fastapi/`.

        Raises:
            MidicoderError: Neu template directory khong ton tai.
        """
        self.stack_dir = Path(stack_dir)
        self.template_dir = self.stack_dir / "cp_full_tenant_billing"

        if not self.template_dir.exists():
            raise EM.raise_error(
                ErrorCode.MDC-F34_BILLING_PLAN_NOT_FOUND,
                reason=f"Template directory khong tim thay: {self.template_dir}",
            )

        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def emit(
        self,
        ir: BillingIR,
        output_dir: str | Path,
    ) -> list[GeneratedFile]:
        """Emit billing & invoicing code cho FastAPI.

        Sinh 6 files:
        - billing_models.py
        - billing_schemas.py
        - billing_service.py
        - billing_router.py
        - invoice_generator.py
        - billing_events.py

        Args:
            ir: BillingIR chua plans, cycles, invoices, meters, gateways.
            output_dir: Duong dan output directory.

        Returns:
            Danh sach GeneratedFile.
        """
        output_dir = Path(output_dir)
        context = self._build_context(ir)
        files: list[GeneratedFile] = []

        templates = [
            ("billing_models.py.jinja2", "app/models/billing_models.py"),
            ("billing_schemas.py.jinja2", "app/schemas/billing_schemas.py"),
            ("billing_service.py.jinja2", "app/services/billing_service.py"),
            ("billing_router.py.jinja2", "app/api/billing_router.py"),
            ("invoice_generator.py.jinja2", "app/services/invoice_generator.py"),
            ("billing_events.py.jinja2", "app/services/billing_events.py"),
        ]

        for template_name, output_path in templates:
            if self._template_exists(template_name):
                content = self._render(template_name, context)
                files.append(GeneratedFile(path=output_path, content=content))

        return files

    def _build_context(self, ir: BillingIR) -> dict[str, Any]:
        """Xay dung template context tu BillingIR."""
        plans_list = [p.to_dict() for p in ir.plans]
        cycles_list = [c.to_dict() for c in ir.cycles]
        invoices_list = [i.to_dict() for i in ir.invoice_configs]
        meters_list = [m.to_dict() for m in ir.meters]
        gateways_list = [g.to_dict() for g in ir.gateways]
        return {
            "plans": plans_list,
            "cycles": cycles_list,
            "invoice_configs": invoices_list,
            "meters": meters_list,
            "gateways": gateways_list,
            "plan_count": len(ir.plans),
            "cycle_count": len(ir.cycles),
            "invoice_count": len(ir.invoice_configs),
            "meter_count": len(ir.meters),
            "gateway_count": len(ir.gateways),
        }

    def _template_exists(self, name: str) -> bool:
        return (self.template_dir / name).exists()

    def _render(self, template_name: str, context: dict[str, Any]) -> str:
        try:
            template = self.env.get_template(template_name)
            return template.render(**context)
        except TemplateNotFound:
            raise EM.raise_error(
                ErrorCode.MDC-F34_BILLING_PLAN_NOT_FOUND,
                reason=f"Jinja2 template khong tim thay: {template_name}",
            )
        except Exception as e:
            raise EM.raise_error(
                ErrorCode.MDC-F34_BILLING_GATEWAY_TIMEOUT,
                reason=f"Render template that bai {template_name}: {e}",
            )
