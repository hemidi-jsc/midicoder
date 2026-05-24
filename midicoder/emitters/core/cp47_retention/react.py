# coding: utf-8
"""
React Emitter cho CP47: Data Retention & Lifecycle Management.

Module này render Jinja2 templates để sinh retention lifecycle UI code
cho React stack, bao gồm Dashboard, Policy, Erasure, Progress,
useRetention hook, và RetentionProvider.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.emitters.core.cp47_retention.parser import RetentionIR
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


__all__ = [
    "ReactRetentionEmitter",
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


class ReactRetentionEmitter:
    """Emitter cho React stack — CP47 Data Retention & Lifecycle Management.

    Render templates từ `stacks/react/core/cp47_retention/`
    để sinh retention lifecycle UI code.
    """

    def __init__(self, stack_dir: str | Path) -> None:
        """Khởi tạo emitter.

        Args:
            stack_dir: Đường dẫn đến `stacks/react/core/`.

        Raises:
            MidicoderError: Nếu template directory không tồn tại.
        """
        self.stack_dir = Path(stack_dir)
        self.template_dir = self.stack_dir / "cp47_retention"

        if not self.template_dir.exists():
            raise EM.raise_error(
                ErrorCode.CP47_RETENTION_POLICY_NOT_FOUND,
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
        ir: RetentionIR,
        output_dir: str | Path,
    ) -> list[GeneratedFile]:
        """Emit retention lifecycle UI code cho React.

        Sinh 6 files:
        - RetentionDashboard.tsx
        - RetentionPolicy.tsx
        - RetentionErasure.tsx
        - RetentionProgress.tsx
        - useRetention.ts
        - RetentionProvider.tsx

        Args:
            ir: RetentionIR chứa policies và config.
            output_dir: Đường dẫn output directory.

        Returns:
            Danh sách GeneratedFile.
        """
        output_dir = Path(output_dir)
        context = self._build_context(ir)
        files: list[GeneratedFile] = []

        templates = [
            ("RetentionDashboard.tsx.jinja2", "src/components/retention/RetentionDashboard.tsx"),
            ("RetentionPolicy.tsx.jinja2", "src/components/retention/RetentionPolicy.tsx"),
            ("RetentionErasure.tsx.jinja2", "src/components/retention/RetentionErasure.tsx"),
            ("RetentionProgress.tsx.jinja2", "src/components/retention/RetentionProgress.tsx"),
            ("useRetention.ts.jinja2", "src/hooks/useRetention.ts"),
            ("RetentionProvider.tsx.jinja2", "src/providers/RetentionProvider.tsx"),
        ]

        for template_name, output_path in templates:
            if self._template_exists(template_name):
                content = self._render(template_name, context)
                files.append(GeneratedFile(path=output_path, content=content))

        return files

    def _build_context(self, ir: RetentionIR) -> dict[str, Any]:
        """Xây dựng template context từ RetentionIR."""
        return {
            "policies": ir.policies,
            "policy_count": len(ir.policies),
            "enable_archival": ir.enable_archival,
            "enable_purge": ir.enable_purge,
            "enable_erasure": ir.enable_erasure,
            "enable_scheduler": ir.enable_scheduler,
            "default_retention_days": ir.default_retention_days,
            "batch_size": ir.batch_size,
        }

    def _template_exists(self, name: str) -> bool:
        return (self.template_dir / name).exists()

    def _render(self, template_name: str, context: dict[str, Any]) -> str:
        try:
            template = self.env.get_template(template_name)
            return template.render(**context)
        except TemplateNotFound:
            raise EM.raise_error(
                ErrorCode.CP47_RETENTION_POLICY_NOT_FOUND,
                reason=f"Jinja2 template không tìm thấy: {template_name}",
            )
        except Exception as e:
            raise EM.raise_error(
                ErrorCode.CP47_RETENTION_SCAN_FAILED,
                reason=f"Render template thất bại {template_name}: {e}",
            )
