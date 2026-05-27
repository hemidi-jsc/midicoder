# coding: utf-8
"""
Infrastructure Emitter cho CP65: Data Backup & Recovery.

Module này render Jinja2 templates để sinh Kubernetes infrastructure files
cho backup và recovery, bao gồm CronJob cho scheduled backup,
VolumeSnapshot cho storage, và S3 lifecycle policy.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.packs.cp65_backup_recovery.parser import BackupIR
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


__all__ = [
    "BackupInfrastructureEmitter",
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


class BackupInfrastructureEmitter:
    """Emitter cho infrastructure stack — CP65 Data Backup & Recovery.

    Render templates từ `stacks/infrastructure/cp65_backup_recovery/`
    để sinh Kubernetes CronJob, VolumeSnapshot, và S3 lifecycle manifests.
    """

    def __init__(self, stack_dir: str | Path) -> None:
        """Khởi tạo emitter.

        Args:
            stack_dir: Đường dẫn đến `stacks/infrastructure/`.

        Raises:
            MidicoderError: Nếu template directory không tồn tại.
        """
        self.stack_dir = Path(stack_dir)
        self.template_dir = self.stack_dir / "cp65_backup_recovery"

        if not self.template_dir.exists():
            raise EM.raise_error(
                ErrorCode.DSL_LOAD_FAILED,
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
        ir: BackupIR,
        output_dir: str | Path,
    ) -> list[GeneratedFile]:
        """Emit Kubernetes infrastructure files cho backup & recovery.

        Sinh các files dựa trên resources có trong BackupIR:
        - k8s/backup-cronjob.yaml (nếu có backup policies với cron schedule)
        - k8s/volume-snapshot.yaml (nếu có policies dùng k8s_volume)
        - k8s/backup-s3-lifecycle.yaml (nếu có policies dùng S3/GCS/Azure)

        Args:
            ir: BackupIR chứa backup policies và recovery plans.
            output_dir: Đường dẫn output directory.

        Returns:
            Danh sách GeneratedFile.
        """
        output_dir = Path(output_dir)
        context = self._build_context(ir)
        files: list[GeneratedFile] = []

        templates = [
            ("k8s/backup-cronjob.yaml.jinja2", "k8s/backup-cronjob.yaml"),
            ("k8s/volume-snapshot.yaml.jinja2", "k8s/volume-snapshot.yaml"),
            ("k8s/backup-s3-lifecycle.yaml.jinja2", "k8s/backup-s3-lifecycle.yaml"),
        ]

        for template_name, output_path in templates:
            if self._template_exists(template_name):
                content = self._render(template_name, context)
                files.append(GeneratedFile(path=output_path, content=content))

        return files

    def _build_context(self, ir: BackupIR) -> dict[str, Any]:
        """Xây dựng template context từ BackupIR."""
        return {
            "backup_policies": [p.to_dict() for p in ir.backup_policies],
            "restore_points": [r.to_dict() for r in ir.restore_points],
            "recovery_plans": [p.to_dict() for p in ir.recovery_plans],
            "monitors": [m.to_dict() for m in ir.monitors],
            "policy_count": len(ir.backup_policies),
            "restore_point_count": len(ir.restore_points),
            "recovery_plan_count": len(ir.recovery_plans),
            "monitor_count": len(ir.monitors),
            "default_retention_days": ir.default_retention_days,
            "enable_encryption": ir.enable_encryption,
        }

    def _template_exists(self, name: str) -> bool:
        """Kiểm tra template có tồn tại không."""
        return (self.template_dir / name).exists()

    def _render(self, template_name: str, context: dict[str, Any]) -> str:
        """Render Jinja2 template.

        Args:
            template_name: Tên file template.
            context: Context dict cho template.

        Returns:
            Nội dung đã render.

        Raises:
            MidicoderError: Nếu template không tìm thấy hoặc render thất bại.
        """
        try:
            template = self.env.get_template(template_name)
            return template.render(**context)
        except TemplateNotFound:
            raise EM.raise_error(
                ErrorCode.DSL_LOAD_FAILED,
                reason=f"Jinja2 template không tìm thấy: {template_name}",
            )
        except Exception as e:
            raise EM.raise_error(
                ErrorCode.DSL_LOAD_FAILED,
                reason=f"Render template thất bại {template_name}: {e}",
            )
