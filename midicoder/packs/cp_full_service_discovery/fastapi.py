# coding: utf-8
"""
FastAPI Emitter cho CP37: Feature Flags & Dynamic Config.

Module này render Jinja2 templates để sinh feature flag code
cho FastAPI stack, bao gồm models, schemas, services, routers,
storage backends, và evaluator.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.packs.cp_full_service_discovery.models import (
    ConfigScope,
    ConfigValueType,
    ConditionType,
    FlagVariantType,
)
from midicoder.packs.cp_full_service_discovery.parser import FeatureFlagIR
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


__all__ = [
    "FastAPIFeatureFlagEmitter",
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


class FastAPIFeatureFlagEmitter:
    """Emitter cho FastAPI stack — CP37 Feature Flags & Dynamic Config.

    Render templates từ `stacks/fastapi/cp_full_service_discovery/`
    để sinh feature flag code, bao gồm models, schemas, services,
    routers, storage backends, và evaluator engine.

    Ví dụ:
        >>> emitter = FastAPIFeatureFlagEmitter(stack_dir="/path/to/stacks/fastapi/core")
        >>> files = emitter.emit(ir, output_dir="/path/to/output")
    """

    def __init__(self, stack_dir: str | Path) -> None:
        """Khởi tạo emitter.

        Args:
            stack_dir: Đường dẫn đến `stacks/fastapi/`.

        Raises:
            MidicoderError: Nếu template directory không tồn tại (CP37_TEMPLATE_NOT_FOUND).
        """
        self.stack_dir = Path(stack_dir)
        self.template_dir = self.stack_dir / "cp_full_service_discovery"

        if not self.template_dir.exists():
            EM.raise_error(
                ErrorCode.MDC-F33_TEMPLATE_NOT_FOUND,
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
        """Emit feature flag code cho FastAPI.

        Sinh 15 files:
        - flag_model.py
        - flag_schema.py
        - flag_service.py
        - flag_router.py
        - ab_experiment_model.py
        - ab_experiment_service.py
        - ab_experiment_router.py
        - config_model.py
        - config_service.py
        - config_router.py
        - flag_store.py
        - redis_store.py
        - db_store.py
        - flag_evaluator.py
        - __init__.py

        Args:
            ir: FeatureFlagIR chứa flags, experiments, configs.
            output_dir: Đường dẫn output directory.

        Returns:
            Danh sách GeneratedFile.
        """
        output_dir = Path(output_dir)

        context = self._build_context(ir)

        files: list[GeneratedFile] = []

        # __init__.py
        if self._template_exists("__init__.py.jinja2"):
            content = self._render("__init__.py.jinja2", context)
            files.append(GeneratedFile(
                path="app/feature_flags/__init__.py",
                content=content,
            ))

        # flag_model.py
        if self._template_exists("flag_model.py.jinja2"):
            content = self._render("flag_model.py.jinja2", context)
            files.append(GeneratedFile(
                path="app/feature_flags/models/flag_model.py",
                content=content,
            ))

        # flag_schema.py
        if self._template_exists("flag_schema.py.jinja2"):
            content = self._render("flag_schema.py.jinja2", context)
            files.append(GeneratedFile(
                path="app/feature_flags/schemas/flag_schema.py",
                content=content,
            ))

        # flag_service.py
        if self._template_exists("flag_service.py.jinja2"):
            content = self._render("flag_service.py.jinja2", context)
            files.append(GeneratedFile(
                path="app/feature_flags/services/flag_service.py",
                content=content,
            ))

        # flag_router.py
        if self._template_exists("flag_router.py.jinja2"):
            content = self._render("flag_router.py.jinja2", context)
            files.append(GeneratedFile(
                path="app/feature_flags/routers/flag_router.py",
                content=content,
            ))

        # ab_experiment_model.py
        if self._template_exists("ab_experiment_model.py.jinja2"):
            content = self._render("ab_experiment_model.py.jinja2", context)
            files.append(GeneratedFile(
                path="app/feature_flags/models/ab_experiment_model.py",
                content=content,
            ))

        # experiment_service.py
        if self._template_exists("experiment_service.py.jinja2"):
            content = self._render("experiment_service.py.jinja2", context)
            files.append(GeneratedFile(
                path="app/feature_flags/services/experiment_service.py",
                content=content,
            ))

        # experiment_router.py
        if self._template_exists("experiment_router.py.jinja2"):
            content = self._render("experiment_router.py.jinja2", context)
            files.append(GeneratedFile(
                path="app/feature_flags/routers/experiment_router.py",
                content=content,
            ))

        # config_model.py
        if self._template_exists("config_model.py.jinja2"):
            content = self._render("config_model.py.jinja2", context)
            files.append(GeneratedFile(
                path="app/feature_flags/models/config_model.py",
                content=content,
            ))

        # config_service.py
        if self._template_exists("config_service.py.jinja2"):
            content = self._render("config_service.py.jinja2", context)
            files.append(GeneratedFile(
                path="app/feature_flags/services/config_service.py",
                content=content,
            ))

        # config_router.py
        if self._template_exists("config_router.py.jinja2"):
            content = self._render("config_router.py.jinja2", context)
            files.append(GeneratedFile(
                path="app/feature_flags/routers/config_router.py",
                content=content,
            ))

        # flag_store.py
        if self._template_exists("flag_store.py.jinja2"):
            content = self._render("flag_store.py.jinja2", context)
            files.append(GeneratedFile(
                path="app/feature_flags/stores/flag_store.py",
                content=content,
            ))

        # redis_store.py
        if self._template_exists("redis_store.py.jinja2"):
            content = self._render("redis_store.py.jinja2", context)
            files.append(GeneratedFile(
                path="app/feature_flags/stores/redis_store.py",
                content=content,
            ))

        # db_store.py
        if self._template_exists("db_store.py.jinja2"):
            content = self._render("db_store.py.jinja2", context)
            files.append(GeneratedFile(
                path="app/feature_flags/stores/db_store.py",
                content=content,
            ))

        # flag_evaluator.py
        if self._template_exists("flag_evaluator.py.jinja2"):
            content = self._render("flag_evaluator.py.jinja2", context)
            files.append(GeneratedFile(
                path="app/feature_flags/services/flag_evaluator.py",
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
                ErrorCode.MDC-F33_TEMPLATE_NOT_FOUND,
                template=template_name,
                reason=f"Jinja2 template không tìm thấy: {template_name}",
            )
        except Exception as e:
            raise EM.raise_error(
                ErrorCode.MDC-F33_RENDER_FAILED,
                template=template_name,
                reason=f"Render template thất bại {template_name}: {e}",
            )
