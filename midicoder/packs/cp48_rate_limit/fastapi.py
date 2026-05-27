# coding: utf-8
"""
FastAPI emitter cho CP48 — API Rate Limiting & Quota Management.

Emit infrastructure files cho FastAPI:
- rate_limit_models.py
- rate_limit_middleware.py
- rate_limit_service.py
- rate_limit_router.py
- quota_service.py

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from jinja2 import TemplateNotFound

from midicoder.errors import ErrorCode, MidicoderError, MidicoderErrorManager as EM
from midicoder.packs.cp48_rate_limit.parser import RateLimitIR


@dataclass
class GeneratedFile:
    """File đã generate.

    Attributes:
        path: Đường dẫn output
        content: Nội dung file
    """
    path: str
    content: str


class FastAPIRateLimitEmitter:
    """Emitter cho FastAPI stack.

    Render Jinja2 templates từ stack directory và generate code cho FastAPI.

    Attributes:
        stack_dir: Đường dẫn đến template directory
    """

    def __init__(self, stack_dir: str | Path) -> None:
        """Khởi tạo emitter.

        Args:
            stack_dir: Đường dẫn đến template directory

        Raises:
            MidicoderError: Nếu template directory không tồn tại
        """
        self.stack_dir = Path(stack_dir)
        if not self.stack_dir.exists():
            raise EM.raise_error(
                ErrorCode.CP48_RATE_LIMIT_POLICY_NOT_FOUND,
                reason=f"Template directory không tồn tại: {self.stack_dir}",
            )

    def emit(self, ir: RateLimitIR, output_dir: str | Path) -> list[GeneratedFile]:
        """Emit tất cả files cho FastAPI.

        Args:
            ir: RateLimitIR chứa policies và quotas
            output_dir: Thư mục output

        Returns:
            Danh sách GeneratedFile
        """
        output_dir = Path(output_dir)
        files: list[GeneratedFile] = []

        templates = [
            ("rate_limit_models.py.jinja2", "app/rate_limit/models.py"),
            ("rate_limit_middleware.py.jinja2", "app/rate_limit/middleware.py"),
            ("rate_limit_service.py.jinja2", "app/rate_limit/service.py"),
            ("rate_limit_router.py.jinja2", "app/api/rate_limit_router.py"),
            ("quota_service.py.jinja2", "app/rate_limit/quota_service.py"),
        ]

        context = self._build_context(ir)

        for template_name, output_path in templates:
            try:
                content = self._render(template_name, context)
                files.append(GeneratedFile(
                    path=str(output_dir / output_path),
                    content=content,
                ))
            except Exception as e:
                if isinstance(e, MidicoderError):
                    raise
                raise EM.raise_error(
                    ErrorCode.CP48_RATE_LIMIT_POLICY_NOT_FOUND,
                    reason=f"Lỗi render template '{template_name}': {e}",
                )

        return files

    def _build_context(self, ir: RateLimitIR) -> dict[str, Any]:
        """Build context cho Jinja2 template.

        Args:
            ir: RateLimitIR

        Returns:
            Dict context
        """
        return {
            "policies": [p.to_dict() for p in ir.policies],
            "quotas": [q.to_dict() for q in ir.quotas],
            "has_policies": len(ir.policies) > 0,
            "has_quotas": len(ir.quotas) > 0,
        }

    def _render(self, template_name: str, context: dict[str, Any]) -> str:
        """Render Jinja2 template.

        Args:
            template_name: Tên template file
            context: Context dict

        Returns:
            Nội dung đã render

        Raises:
            MidicoderError: Nếu template không tìm thấy hoặc render lỗi
        """
        template_path = self.stack_dir / template_name

        if not template_path.exists():
            raise EM.raise_error(
                ErrorCode.CP48_RATE_LIMIT_POLICY_NOT_FOUND,
                reason=f"Template không tìm thấy: {template_path}",
            )

        try:
            from jinja2 import Template
            template = Template(template_path.read_text(encoding="utf-8"))
            return template.render(**context)
        except Exception as e:
            raise EM.raise_error(
                ErrorCode.CP48_RATE_LIMIT_POLICY_NOT_FOUND,
                reason=f"Lỗi render template '{template_name}': {e}",
            )


__all__ = [
    "FastAPIRateLimitEmitter",
    "GeneratedFile",
]
