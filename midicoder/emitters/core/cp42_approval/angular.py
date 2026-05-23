# coding: utf-8
"""
Angular Emitter cho CP42: Approval Workflow Engine (Frontend).

Module này render Jinja2 templates để sinh approval workflow infrastructure
cho Angular stack, bao gồm:
- approval-dashboard.component.ts: Component chính hiển thị bảng điều khiển phê duyệt
- approval-details.component.ts: Chi tiết yêu cầu phê duyệt
- approval-history.component.ts: Lịch sử phê duyệt
- approval.service.ts: Injectable service gọi API phê duyệt
- approval.store.ts: Store quản lý trạng thái phê duyệt
- approval-types.ts: Định nghĩa kiểu TypeScript

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.emitters.core.cp42_approval.parser import ApprovalIR
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


__all__ = [
    "AngularApprovalEmitter",
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


class AngularApprovalEmitter:
    """Emitter cho Angular stack — CP42 Approval Workflow Engine.

    Render templates từ `stacks/angular/core/cp42_approval/`
    để sinh approval workflow infrastructure cho Angular.

    Ví dụ:
        >>> emitter = AngularApprovalEmitter(stack_dir="/path/to/stacks/angular/core")
        >>> ir = ApprovalIR(approval_requests=[...], approval_steps=[...])
        >>> files = emitter.emit(ir)
    """

    _TEMPLATE_MAP: dict[str, str] = {
        "approval-dashboard.component.ts.jinja2": "src/approval/approval-dashboard.component.ts",
        "approval-details.component.ts.jinja2": "src/approval/approval-details.component.ts",
        "approval-history.component.ts.jinja2": "src/approval/approval-history.component.ts",
        "approval.service.ts.jinja2": "src/approval/approval.service.ts",
        "approval.store.ts.jinja2": "src/approval/approval.store.ts",
        "approval-types.ts.jinja2": "src/approval/approval-types.ts",
    }

    def __init__(self, stack_dir: str | Path) -> None:
        """Khởi tạo emitter.

        Args:
            stack_dir: Đường dẫn đến `stacks/angular/core/`.

        Raises:
            MidicoderError: Nếu template directory không tồn tại.
        """
        self.stack_dir = Path(stack_dir)
        self.template_dir = self.stack_dir  # stack_dir đã là .../cp42_approval

        if not self.template_dir.exists():
            EM.raise_error(
                ErrorCode.CP42_APPROVAL_REQUEST_NOT_FOUND,
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
        """Emit approval workflow infrastructure cho Angular.

        Sinh 6 files:
        - approval-dashboard.component.ts
        - approval-details.component.ts
        - approval-history.component.ts
        - approval.service.ts
        - approval.store.ts
        - approval-types.ts

        Args:
            ir: ApprovalIR chứa approval requests, steps, rules.
            output_dir: Đường dẫn output directory.

        Returns:
            Danh sách GeneratedFile.
        """
        output_dir = Path(output_dir)

        context = self._build_context(ir)

        files: list[GeneratedFile] = []

        for template_name, output_path in self._TEMPLATE_MAP.items():
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
            "notification_config": ir.notification_config if ir.notification_config else {
                "emailEnabled": True,
                "pushEnabled": False,
                "notifyOnStepAssigned": True,
                "notifyOnDeadlineApproaching": True,
                "deadlineWarningHours": 24,
                "notifyOnEscalation": True,
                "notifyOnDelegation": True,
                "webSocketUrl": "ws://localhost:8080/ws/approvals",
            },
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
                ErrorCode.CP42_APPROVAL_REQUEST_NOT_FOUND,
                reason=f"Jinja2 template không tìm thấy: {template_name}",
            )
        except Exception as e:
            raise EM.raise_error(
                ErrorCode.CP42_APPROVAL_REQUEST_NOT_FOUND,
                reason=f"Render template thất bại {template_name}: {e}",
            )
