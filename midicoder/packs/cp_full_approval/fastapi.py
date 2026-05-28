# coding: utf-8
"""
FastAPI Emitter cho CP42: Approval Workflow Engine.

Module này render Jinja2 templates để sinh approval workflow code
cho FastAPI stack, bao gồm models, schemas, service, router,
event handler, escalation worker, và delegation service.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.packs.cp_full_approval.parser import ApprovalIR
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


__all__ = [
    "FastAPIApprovalEmitter",
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


class FastAPIApprovalEmitter:
    """Emitter cho FastAPI stack — CP42 Approval Workflow Engine.

    Render templates từ `stacks/fastapi/cp_full_approval/`
    để sinh approval workflow code.

    Ví dụ:
        >>> emitter = FastAPIApprovalEmitter(stack_dir="/path/to/stacks/fastapi/core")
        >>> files = emitter.emit(ir, output_dir="/path/to/output")
    """

    def __init__(self, stack_dir: str | Path) -> None:
        """Khởi tạo emitter.

        Args:
            stack_dir: Đường dẫn đến `stacks/fastapi/`.

        Raises:
            MidicoderError: Nếu template directory không tồn tại.
        """
        self.stack_dir = Path(stack_dir)
        self.template_dir = self.stack_dir  # stack_dir đã là .../cp_full_approval

        if not self.template_dir.exists():
            EM.raise_error(
                ErrorCode.MDC-F24_APPROVAL_REQUEST_NOT_FOUND,
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
        ir: ApprovalIR,
        output_dir: str | Path,
    ) -> list[GeneratedFile]:
        """Emit approval workflow code cho FastAPI.

        Sinh 7 files:
        - approval_models.py
        - approval_schemas.py
        - approval_service.py
        - approval_router.py
        - approval_event_handler.py
        - approval_escalation_worker.py
        - approval_delegation_service.py

        Args:
            ir: ApprovalIR chứa approval requests, steps, rules.
            output_dir: Đường dẫn output directory.

        Returns:
            Danh sách GeneratedFile.
        """
        output_dir = Path(output_dir)

        context = self._build_context(ir)

        files: list[GeneratedFile] = []

        templates = [
            ("approval_models.py.jinja2", "app/models/approval_models.py"),
            ("approval_schemas.py.jinja2", "app/schemas/approval_schemas.py"),
            ("approval_service.py.jinja2", "app/services/approval_service.py"),
            ("approval_router.py.jinja2", "app/api/approval_router.py"),
            ("approval_event_handler.py.jinja2", "app/events/approval_event_handler.py"),
            ("approval_escalation_worker.py.jinja2", "app/workers/approval_escalation_worker.py"),
            ("approval_delegation_service.py.jinja2", "app/services/approval_delegation_service.py"),
        ]

        for template_name, output_path in templates:
            if self._template_exists(template_name):
                content = self._render(template_name, context)
                files.append(GeneratedFile(path=output_path, content=content))

        return files

    def _build_context(self, ir: ApprovalIR) -> dict[str, Any]:
        """Xây dựng template context từ ApprovalIR.

        Args:
            ir: ApprovalIR input.

        Returns:
            Dict context cho Jinja2.
        """
        requests_list = [r.to_dict() for r in ir.requests]
        steps_list = [s.to_dict() for s in ir.steps]
        rules_list = [r.to_dict() for r in ir.escalation_rules]

        # Role types unique list
        role_types = list({s.approver_role for s in ir.steps})

        return {
            "approval_requests": requests_list,
            "approval_requests_list": requests_list,
            "approval_steps": steps_list,
            "approval_steps_list": steps_list,
            "approval_rules": rules_list,
            "approval_rules_list": rules_list,
            "approval_roles": role_types,
            "role_types": role_types,
            "request_count": len(ir.requests),
            "step_count": len(ir.steps),
            "rule_count": len(ir.escalation_rules),
            "use_delegation": len(ir.delegations) > 0,
            "escalation_timeout": ir.escalation_rules[0].trigger_after_minutes if ir.escalation_rules else 60,
            "use_websocket": ir.use_events,
            "use_events": ir.use_events,
            "notification_config": ir.notification_config,
        }

    def _template_exists(self, name: str) -> bool:
        """Kiểm tra template có tồn tại không.

        Args:
            name: Tên template file.

        Returns:
            True nếu tồn tại.
        """
        return (self.template_dir / name).exists()

    def _render(self, template_name: str, context: dict[str, Any]) -> str:
        """Render một template.

        Args:
            template_name: Tên template file.
            context: Template context.

        Returns:
            Rendered string.

        Raises:
            MidicoderError: Nếu template không tìm thấy hoặc render lỗi.
        """
        try:
            template = self.env.get_template(template_name)
            return template.render(**context)
        except TemplateNotFound:
            raise EM.raise_error(
                ErrorCode.MDC-F24_APPROVAL_REQUEST_NOT_FOUND,
                reason=f"Jinja2 template không tìm thấy: {template_name}",
            )
        except Exception as e:
            raise EM.raise_error(
                ErrorCode.MDC-F24_APPROVAL_REQUEST_NOT_FOUND,
                reason=f"Render template thất bại {template_name}: {e}",
            )
