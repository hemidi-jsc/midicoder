# coding: utf-8
"""
Infrastructure Emitter cho CP55: CI/CD Pipeline Generator.

Module này render Jinja2 templates để sinh CI/CD pipeline files,
bao gồm GitHub Actions workflows, GitLab CI, Jenkinsfile,
và Docker Compose CI environment.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.emitters.core.cp55_cicd.parser import CIIR
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


__all__ = [
    "CICDInfrastructureEmitter",
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


class CICDInfrastructureEmitter:
    """Emitter cho Infrastructure stack — CP55 CI/CD Pipeline Generator.

    Render templates từ `stacks/infrastructure/core/cp55_cicd/`
    để sinh CI/CD pipeline files.
    """

    def __init__(self, stack_dir: str | Path) -> None:
        """Khởi tạo emitter.

        Args:
            stack_dir: Đường dẫn đến `stacks/infrastructure/core/`.

        Raises:
            MidicoderError: Nếu template directory không tồn tại.
        """
        self.stack_dir = Path(stack_dir)
        self.template_dir = self.stack_dir / "cp55_cicd"

        if not self.template_dir.exists():
            raise EM.raise_error(
                ErrorCode.DSL_LOAD_FAILED,
                reason=f"Template directory không tìm thấy: {self.template_dir}",
            )

        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=False,  # CI/CD files không cần HTML escaping
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def emit(
        self,
        ir: CIIR,
        output_dir: str | Path,
    ) -> list[GeneratedFile]:
        """Emit CI/CD pipeline files.

        Sinh các files:
        - .github/workflows/build-test-deploy.yml
        - .github/workflows/docker-publish.yml
        - .gitlab-ci.yml
        - Jenkinsfile
        - docker-compose.ci.yml

        Args:
            ir: CIIR chứa pipeline configs và settings.
            output_dir: Đường dẫn output directory.

        Returns:
            Danh sách GeneratedFile.
        """
        output_dir = Path(output_dir)
        context = self._build_context(ir)
        files: list[GeneratedFile] = []

        templates = [
            ("github-actions/build-test-deploy.yml.jinja2", ".github/workflows/build-test-deploy.yml"),
            ("github-actions/docker-publish.yml.jinja2", ".github/workflows/docker-publish.yml"),
            ("gitlab-ci.yml.jinja2", ".gitlab-ci.yml"),
            ("Jenkinsfile.jinja2", "Jenkinsfile"),
            ("docker-compose.ci.yml.jinja2", "docker-compose.ci.yml"),
        ]

        for template_name, output_path in templates:
            if self._template_exists(template_name):
                content = self._render(template_name, context)
                files.append(GeneratedFile(path=output_path, content=content))

        return files

    @staticmethod
    def _build_context(ir: CIIR) -> dict[str, Any]:
        """Xây dựng template context từ CIIR.

        Args:
            ir: CIIR đã parse.

        Returns:
            Template context dict.
        """
        pipelines_list = [p.to_dict() for p in ir.pipelines]
        stages_list = [s.to_dict() for s in ir.stages]
        return {
            "pipelines": pipelines_list,
            "stages": stages_list,
            "workflows": ir.workflows,
            "pipeline_count": len(ir.pipelines),
            "stage_count": len(ir.stages),
            "workflow_count": len(ir.workflows),
        }

    def _template_exists(self, name: str) -> bool:
        """Kiểm tra template có tồn tại không.

        Args:
            name: Tên template file.

        Returns:
            True nếu template tồn tại.
        """
        return (self.template_dir / name).exists()

    def _render(self, template_name: str, context: dict[str, Any]) -> str:
        """Render một Jinja2 template.

        Args:
            template_name: Tên template file.
            context: Template context.

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
