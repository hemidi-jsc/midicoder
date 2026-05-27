# coding: utf-8
"""
NestJS Emitter cho CP63: Search & Recommendation Engine.

Module này render Jinja2 templates để sinh recommendation code
cho NestJS stack, bao gồm recommendation module, cached recommendations
service, A/B test routing service, và recommendation controller.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.packs.cp63_recommendation.parser import RecommendationIR
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


__all__ = [
    "NestJSRecommendationEmitter",
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


class NestJSRecommendationEmitter:
    """Emitter cho NestJS stack — CP63 Search & Recommendation Engine.

    Render templates từ `stacks/nestjs/cp63_recommendation/`
    để sinh recommendation engine code với NestJS modules, services,
    cached recommendations, và A/B test routing.
    """

    def __init__(self, stack_dir: str | Path) -> None:
        """Khởi tạo emitter.

        Args:
            stack_dir: Đường dẫn đến `stacks/nestjs/`.

        Raises:
            MidicoderError: Nếu template directory không tồn tại.
        """
        self.stack_dir = Path(stack_dir)
        self.template_dir = self.stack_dir / "cp63_recommendation"

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
        ir: RecommendationIR,
        output_dir: str | Path,
    ) -> list[GeneratedFile]:
        """Emit recommendation engine code cho NestJS.

        Sinh 4 files:
        - recommendation.module.ts: NestJS module với providers
        - recommendation.service.ts: Cached recommendation service
        - ab-test-routing.service.ts: A/B test routing service
        - recommendation.controller.ts: REST controller endpoints

        Args:
            ir: RecommendationIR chứa recommendation configs.
            output_dir: Đường dẫn output directory.

        Returns:
            Danh sách GeneratedFile.
        """
        output_dir = Path(output_dir)
        context = self._build_context(ir)
        files: list[GeneratedFile] = []

        templates = [
            ("recommendation.module.ts.jinja2", "src/recommendation/recommendation.module.ts"),
            ("recommendation.service.ts.jinja2", "src/recommendation/recommendation.service.ts"),
            ("ab-test-routing.service.ts.jinja2", "src/recommendation/ab-test-routing.service.ts"),
            ("recommendation.controller.ts.jinja2", "src/recommendation/recommendation.controller.ts"),
        ]

        for template_name, output_path in templates:
            if self._template_exists(template_name):
                content = self._render(template_name, context)
                files.append(GeneratedFile(path=output_path, content=content))

        return files

    def _build_context(self, ir: RecommendationIR) -> dict[str, Any]:
        """Xây dựng template context từ RecommendationIR."""
        configs_list = [c.to_dict() for c in ir.configs]
        embeddings_list = [e.to_dict() for e in ir.embeddings]
        preferences_list = [p.to_dict() for p in ir.preferences]
        ab_tests_list = [a.to_dict() for a in ir.ab_tests]
        return {
            "configs": configs_list,
            "embeddings": embeddings_list,
            "preferences": preferences_list,
            "ab_tests": ab_tests_list,
            "config_count": len(ir.configs),
            "embedding_count": len(ir.embeddings),
            "default_algorithm": ir.default_algorithm.value,
            "default_top_k": ir.default_top_k,
            "enable_cache": ir.enable_cache,
            "enable_ab_testing": ir.enable_ab_testing,
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
