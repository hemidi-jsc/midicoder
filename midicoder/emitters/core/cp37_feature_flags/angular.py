# coding: utf-8
"""
Angular Emitter cho CP37: Feature Flags & Dynamic Config (Frontend).

Module này render Jinja2 templates để sinh feature flag infrastructure
cho Angular stack, bao gồm:
- feature-flag.service.ts: Injectable service quản lý feature flags
- feature-flag.directive.ts: Structural directive *featureFlag cho conditional rendering
- ab-experiment.service.ts: Injectable service quản lý A/B experiments
- dynamic-config.service.ts: Injectable service quản lý dynamic configs
- feature-flags.module.ts: NgModule đóng gói toàn bộ feature flag infrastructure

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.emitters.core.cp37_feature_flags.models import (
    ABExperiment,
    ABVariant,
    ConfigScope,
    ConfigValueType,
    DynamicConfig,
    FeatureFlag,
    FlagVariantType,
)
from midicoder.emitters.core.cp37_feature_flags.parser import FeatureFlagIR
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


__all__ = [
    "AngularFeatureFlagEmitter",
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


class AngularFeatureFlagEmitter:
    """Emitter cho Angular stack — CP37 Feature Flags & Dynamic Config.

    Render templates từ `stacks/angular/core/cp37_feature_flags/`
    để sinh feature flag infrastructure cho Angular.

    Ví dụ:
        >>> emitter = AngularFeatureFlagEmitter(stack_dir="/path/to/stacks/angular/core")
        >>> ir = FeatureFlagIR(flags=[...], experiments=[...], configs=[...])
        >>> files = emitter.emit(ir)
    """

    # Mapping template name -> output path (khớp với file thực tế trong stacks/angular/core/cp37_feature_flags/)
    _TEMPLATE_MAP: dict[str, str] = {
        "flag-provider.service.ts.jinja2": "src/app/core/feature-flags/flag-provider.service.ts",
        "flag-directive.ts.jinja2": "src/app/core/feature-flags/flag-directive.ts",
        "flag-interceptor.ts.jinja2": "src/app/core/feature-flags/flag-interceptor.ts",
        "config.service.ts.jinja2": "src/app/core/feature-flags/config.service.ts",
        "flag-sync.service.ts.jinja2": "src/app/core/feature-flags/flag-sync.service.ts",
    }

    def __init__(self, stack_dir: str | Path) -> None:
        """Khởi tạo emitter.

        Args:
            stack_dir: Đường dẫn đến `stacks/angular/core/`.

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

    def emit(self, ir: FeatureFlagIR, context: dict[str, Any] | None = None) -> list[dict[str, str]]:
        """Emit feature flag infrastructure cho Angular.

        Sinh 5 files:
        - feature-flag.service.ts
        - feature-flag.directive.ts
        - ab-experiment.service.ts
        - dynamic-config.service.ts
        - feature-flags.module.ts

        Args:
            ir: FeatureFlagIR chứa flags, experiments, configs.
            context: Context bổ sung (optional), vd: ui_framework.

        Returns:
            List của {path, content} cho mỗi file.
        """
        extra_context = context or {}

        # Xây dựng context từ FeatureFlagIR
        flags_list = []
        for f in ir.flags:
            flag_dict: dict[str, Any] = {
                "flag_key": f.flag_key,
                "name": f.name,
                "description": f.description,
                "variant_type": f.variant_type.value,
                "default_enabled": f.default_enabled,
                "percentage": f.percentage,
                "is_active": f.is_active,
                "environments": f.environments,
            }
            # Thêm targeting rules summary
            if f.targeting_rules:
                flag_dict["targeting_rules"] = [
                    {
                        "rule_id": r.rule_id,
                        "condition_type": r.condition_type.value,
                        "condition": r.condition,
                        "value": r.value,
                        "priority": r.priority,
                    }
                    for r in f.targeting_rules
                ]
            flags_list.append(flag_dict)

        # Xây dựng experiments list
        experiments_list = []
        for exp in ir.experiments:
            variants_list = []
            for v in exp.variants:
                variants_list.append({
                    "variant_key": v.variant_key,
                    "name": v.name,
                    "weight": v.weight,
                    "metadata": v.metadata,
                })
            exp_dict: dict[str, Any] = {
                "experiment_key": exp.experiment_key,
                "name": exp.name,
                "description": exp.description,
                "variants": variants_list,
                "is_active": exp.is_active,
                "is_running": exp.is_running,
                "traffic_percentage": exp.traffic_percentage,
                "success_metric": exp.success_metric,
            }
            experiments_list.append(exp_dict)

        # Xây dựng configs list
        configs_list = []
        for c in ir.configs:
            configs_list.append({
                "config_key": c.config_key,
                "value": c.value,
                "value_type": c.value_type.value,
                "scope": c.scope.value,
                "tenant_id": c.tenant_id,
                "environment": c.environment,
                "is_encrypted": c.is_encrypted,
            })

        # Flag keys flat list cho TypeScript union type
        flag_keys = [f.flag_key for f in ir.flags]

        # Experiment keys flat list
        experiment_keys = [e.experiment_key for e in ir.experiments]

        # Config keys flat list
        config_keys = [c.config_key for c in ir.configs]

        # Các loại variant type được sử dụng
        variant_types_used = list({f.variant_type.value for f in ir.flags})

        # Các loại config value type được sử dụng
        config_value_types_used = list({c.value_type.value for c in ir.configs})

        # Các scope được sử dụng
        scopes_used = list({c.scope.value for c in ir.configs})

        # Has targeting rules
        has_targeting = any(f.targeting_rules for f in ir.flags)

        # Has percentage flags
        has_percentage = any(
            f.variant_type == FlagVariantType.PERCENTAGE for f in ir.flags
        )

        # Has tenant overrides
        has_tenant_overrides = any(f.tenant_overrides for f in ir.flags)

        template_context: dict[str, Any] = {
            # Flags
            "flags": flags_list,
            "flag_count": len(ir.flags),
            "flag_keys": flag_keys,
            "variant_types": variant_types_used,
            "has_targeting": has_targeting,
            "has_percentage": has_percentage,
            "has_tenant_overrides": has_tenant_overrides,
            # Experiments
            "experiments": experiments_list,
            "experiment_count": len(ir.experiments),
            "experiment_keys": experiment_keys,
            # Configs
            "configs": configs_list,
            "config_count": len(ir.configs),
            "config_keys": config_keys,
            "config_value_types": config_value_types_used,
            "scopes_used": scopes_used,
            # Extra context
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
                ErrorCode.CP37_TEMPLATE_NOT_FOUND,
                template=template_name,
                reason=f"Template không tìm thấy: {template_name}",
            )
        except Exception as e:
            raise EM.raise_error(
                ErrorCode.CP37_RENDER_FAILED,
                template=template_name,
                reason=f"Render thất bại {template_name}: {e}",
            )
