# coding: utf-8
"""
NestJS Emitter cho CP37: Feature Flags & Dynamic Config.

Module này render Jinja2 templates để sinh feature flag code
cho NestJS stack, bao gồm entities, DTOs, services, controllers,
storage service, và module.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.packs.cp37_feature_flags.models import (
    ConfigScope,
    ConfigValueType,
    ConditionType,
    FlagVariantType,
)
from midicoder.packs.cp37_feature_flags.parser import FeatureFlagIR
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


__all__ = [
    "NestJSFeatureFlagEmitter",
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


class NestJSFeatureFlagEmitter:
    """Emitter cho NestJS stack — CP37 Feature Flags & Dynamic Config.

    Render templates từ `stacks/nestjs/cp37_feature_flags/`
    để sinh feature flag code, bao gồm entities, DTOs, services,
    controllers, storage service, và NestJS module.

    Ví dụ:
        >>> emitter = NestJSFeatureFlagEmitter(stack_dir="/path/to/stacks/nestjs/core")
        >>> files = emitter.emit(ir, output_dir="/path/to/output")
    """

    def __init__(self, stack_dir: str | Path) -> None:
        """Khởi tạo emitter.

        Args:
            stack_dir: Đường dẫn đến `stacks/nestjs/`.

        Raises:
            MidicoderError: Nếu template directory không tồn tại (CP37_TEMPLATE_NOT_FOUND).
        """
        self.stack_dir = Path(stack_dir)
        self.template_dir = self.stack_dir / "cp37_feature_flags"

        if not self.template_dir.exists():
            EM.raise_error(
                ErrorCode.CP37_TEMPLATE_NOT_FOUND,
                template=str(self.template_dir),
                message=f"Template directory không tìm thấy: {self.template_dir}"
            )

        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def emit(
        self,
        ir: FeatureFlagIR,
        output_dir: str | Path,
    ) -> list[GeneratedFile]:
        """Emit feature flag code cho NestJS.

        Sinh 14 files:
        - flag.entity.ts
        - flag-dto.ts
        - flag.service.ts
        - flag.controller.ts
        - experiment.entity.ts
        - experiment-dto.ts
        - experiment.service.ts
        - experiment.controller.ts
        - config.entity.ts
        - config-dto.ts
        - config.service.ts
        - config.controller.ts
        - flag-store.service.ts
        - feature-flags.module.ts

        Args:
            ir: FeatureFlagIR chứa flags, experiments, configs.
            output_dir: Đường dẫn output directory.

        Returns:
            Danh sách GeneratedFile.
        """
        output_dir = Path(output_dir)

        context = self._build_context(ir)

        files: list[GeneratedFile] = []

        # flag.entity.ts
        if self._template_exists("flag.entity.ts.jinja2"):
            content = self._render("flag.entity.ts.jinja2", context)
            files.append(GeneratedFile(
                path="src/feature-flags/entities/flag.entity.ts",
                content=content,
            ))

        # flag.dto.ts
        if self._template_exists("flag.dto.ts.jinja2"):
            content = self._render("flag.dto.ts.jinja2", context)
            files.append(GeneratedFile(
                path="src/feature-flags/dtos/flag-dto.ts",
                content=content,
            ))

        # flag.service.ts
        if self._template_exists("flag.service.ts.jinja2"):
            content = self._render("flag.service.ts.jinja2", context)
            files.append(GeneratedFile(
                path="src/feature-flags/services/flag.service.ts",
                content=content,
            ))

        # flag.controller.ts
        if self._template_exists("flag.controller.ts.jinja2"):
            content = self._render("flag.controller.ts.jinja2", context)
            files.append(GeneratedFile(
                path="src/feature-flags/controllers/flag.controller.ts",
                content=content,
            ))

        # experiment.entity.ts
        if self._template_exists("experiment.entity.ts.jinja2"):
            content = self._render("experiment.entity.ts.jinja2", context)
            files.append(GeneratedFile(
                path="src/feature-flags/entities/experiment.entity.ts",
                content=content,
            ))

        # experiment.dto.ts
        if self._template_exists("experiment.dto.ts.jinja2"):
            content = self._render("experiment.dto.ts.jinja2", context)
            files.append(GeneratedFile(
                path="src/feature-flags/dtos/experiment-dto.ts",
                content=content,
            ))

        # experiment.service.ts
        if self._template_exists("experiment.service.ts.jinja2"):
            content = self._render("experiment.service.ts.jinja2", context)
            files.append(GeneratedFile(
                path="src/feature-flags/services/experiment.service.ts",
                content=content,
            ))

        # experiment.controller.ts
        if self._template_exists("experiment.controller.ts.jinja2"):
            content = self._render("experiment.controller.ts.jinja2", context)
            files.append(GeneratedFile(
                path="src/feature-flags/controllers/experiment.controller.ts",
                content=content,
            ))

        # config.entity.ts
        if self._template_exists("config.entity.ts.jinja2"):
            content = self._render("config.entity.ts.jinja2", context)
            files.append(GeneratedFile(
                path="src/feature-flags/entities/config.entity.ts",
                content=content,
            ))

        # config.dto.ts
        if self._template_exists("config.dto.ts.jinja2"):
            content = self._render("config.dto.ts.jinja2", context)
            files.append(GeneratedFile(
                path="src/feature-flags/dtos/config-dto.ts",
                content=content,
            ))

        # config.service.ts
        if self._template_exists("config.service.ts.jinja2"):
            content = self._render("config.service.ts.jinja2", context)
            files.append(GeneratedFile(
                path="src/feature-flags/services/config.service.ts",
                content=content,
            ))

        # config.controller.ts
        if self._template_exists("config.controller.ts.jinja2"):
            content = self._render("config.controller.ts.jinja2", context)
            files.append(GeneratedFile(
                path="src/feature-flags/controllers/config.controller.ts",
                content=content,
            ))

        # flag-sync.gateway.ts
        if self._template_exists("flag-sync.gateway.ts.jinja2"):
            content = self._render("flag-sync.gateway.ts.jinja2", context)
            files.append(GeneratedFile(
                path="src/feature-flags/gateways/flag-sync.gateway.ts",
                content=content,
            ))

        # feature-flags.module.ts
        if self._template_exists("feature-flags.module.ts.jinja2"):
            content = self._render("feature-flags.module.ts.jinja2", context)
            files.append(GeneratedFile(
                path="src/feature-flags/feature-flags.module.ts",
                content=content,
            ))

        return files

    def _build_context(self, ir: FeatureFlagIR) -> dict[str, Any]:
        """Xây dựng template context từ FeatureFlagIR.

        Args:
            ir: FeatureFlagIR input.

        Returns:
            Dict context cho Jinja2.
        """
        flags_list = [f.to_dict() for f in ir.flags]
        experiments_list = [e.to_dict() for e in ir.experiments]
        configs_list = [c.to_dict() for c in ir.configs]

        return {
            # Data từ IR
            "flags": flags_list,
            "experiments": experiments_list,
            "configs": configs_list,
            "flag_count": len(ir.flags),
            "experiment_count": len(ir.experiments),
            "config_count": len(ir.configs),
            # Enum values để template reference
            "flag_variant_types": [
                FlagVariantType.BOOLEAN.value,
                FlagVariantType.PERCENTAGE.value,
                FlagVariantType.TARGETED.value,
            ],
            "condition_types": [
                ConditionType.ROLE.value,
                ConditionType.ATTRIBUTE.value,
                ConditionType.TENANT.value,
                ConditionType.SEGMENT.value,
            ],
            "config_scopes": [
                ConfigScope.GLOBAL.value,
                ConfigScope.TENANT.value,
                ConfigScope.ENVIRONMENT.value,
            ],
            "config_value_types": [
                ConfigValueType.STRING.value,
                ConfigValueType.NUMBER.value,
                ConfigValueType.BOOLEAN.value,
                ConfigValueType.JSON.value,
                ConfigValueType.ARRAY.value,
            ],
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
                ErrorCode.CP37_TEMPLATE_NOT_FOUND,
                template=template_name,
                reason=f"Jinja2 template không tìm thấy: {template_name}",
            )
        except Exception as e:
            raise EM.raise_error(
                ErrorCode.CP37_RENDER_FAILED,
                template=template_name,
                reason=f"Render template thất bại {template_name}: {e}",
            )
