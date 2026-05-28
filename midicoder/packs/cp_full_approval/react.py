# coding: utf-8
"""
React Emitter cho CP42: Approval Workflow Engine (Frontend).

Module này render Jinja2 templates để sinh approval workflow infrastructure
cho React stack, bao gồm:
- ApprovalDashboard.tsx: Component chính hiển thị bảng điều khiển phê duyệt
- ApprovalDetails.tsx: Chi tiết yêu cầu phê duyệt
- ApprovalHistory.tsx: Lịch sử phê duyệt
- NotificationBadge.tsx: Badge thông báo phê duyệt
- DelegationSettings.tsx: Cài đặt ủy quyền phê duyệt
- useApprovals.ts: Custom hook để quản lý trạng thái phê duyệt

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.packs.cp_full_approval.parser import ApprovalIR
from midicoder.errors import ErrorCode, MidicoderError, MidicoderErrorManager as EM


__all__ = [
    "ReactApprovalEmitter",
]


class ReactApprovalEmitter:
    """Emitter cho React stack — CP42 Approval Workflow Engine.

    Render templates từ `stacks/react/cp_full_approval/`
    để sinh approval workflow frontend components.

    Ví dụ:
        >>> emitter = ReactApprovalEmitter(stack_dir="/path/to/stacks/react/core")
        >>> ir = ApprovalIR(approval_requests=[...], approval_steps=[...])
        >>> files = emitter.emit(ir)
    """

    _TEMPLATE_MAP: dict[str, str] = {
        "ApprovalDashboard.tsx.jinja2": "src/approval/ApprovalDashboard.tsx",
        "ApprovalDetails.tsx.jinja2": "src/approval/ApprovalDetails.tsx",
        "ApprovalHistory.tsx.jinja2": "src/approval/ApprovalHistory.tsx",
        "NotificationBadge.tsx.jinja2": "src/approval/NotificationBadge.tsx",
        "DelegationSettings.tsx.jinja2": "src/approval/DelegationSettings.tsx",
        "useApprovals.ts.jinja2": "src/approval/hooks/useApprovals.ts",
    }

    def __init__(self, stack_dir: str | Path) -> None:
        """Khởi tạo emitter.

        Args:
            stack_dir: Đường dẫn đến `stacks/react/`.

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

    def emit(self, ir: ApprovalIR, context: dict[str, Any] | None = None) -> list[dict[str, str]]:
        """Emit approval workflow infrastructure cho React.

        Sinh 6 files:
        - ApprovalDashboard.tsx
        - ApprovalDetails.tsx
        - ApprovalHistory.tsx
        - NotificationBadge.tsx
        - DelegationSettings.tsx
        - useApprovals.ts

        Args:
            ir: ApprovalIR chứa approval requests, steps, rules.
            context: Context bổ sung (optional).

        Returns:
            List của {path, content} cho mỗi file.
        """
        extra_context = context or {}

        requests_list = [r.to_dict() for r in ir.requests]
        steps_list = [s.to_dict() for s in ir.steps]
        rules_list = [r.to_dict() for r in ir.escalation_rules]
        role_types = list({s.approver_role for s in ir.steps})

        template_context: dict[str, Any] = {
            "approval_requests": requests_list,
            "approval_steps": steps_list,
            "approval_rules": rules_list,
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
            **extra_context,
        }

        result: list[dict[str, str]] = []

        for template_name, output_path in self._TEMPLATE_MAP.items():
            if self._template_exists(template_name):
                content = self._render(template_name, template_context)
                result.append({"path": output_path, "content": content})

        return result

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
                reason=f"Template không tìm thấy: {template_name}",
            )
        except Exception as e:
            raise EM.raise_error(
                ErrorCode.MDC-F24_APPROVAL_REQUEST_NOT_FOUND,
                reason=f"Render thất bại {template_name}: {e}",
            )
