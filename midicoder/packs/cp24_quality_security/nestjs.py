# coding: utf-8
"""
Mô-đun NestJS emitter cho Code Quality & Security Scanner Generator (CP24).

Emit các file chất lượng và bảo mật cho NestJS:
- .eslintrc.json — ESLint config với security plugin
- .prettierrc — Prettier formatting config
- scripts/quality-gate.ts — Script chạy quality gate (eslint + npm audit)
- .npmrc — npm audit và engine-strict config
- tsconfig.strict.json — TypeScript strict mode config

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from midicoder.packs.cp24_quality_security.models import (
    LinterType,
    QualityCollection,
    SecurityTool,
    StackType,
)
from midicoder.pipeline.emitter import Emitter


class NestJSQualityEmitter:
    """
    Emitter sinh các file quality & security cho NestJS.

    Sinh ra:
    - .eslintrc.json — Cấu hình ESLint + security plugin
    - .prettierrc — Cấu hình Prettier
    - scripts/quality-gate.ts — Script standalone chạy quality gate
    - .npmrc — npm config (audit, fund, engine-strict)
    - tsconfig.strict.json — TypeScript strict compiler options
    """

    def __init__(self, stack_dir: str | Path) -> None:
        """
        Khởi tạo emitter.

        Args:
            stack_dir: Đường dẫn đến template directory
        """
        self.emitter = Emitter(stack="nestjs")
        self.stack_dir = Path(stack_dir)

    def generate(self, collection: QualityCollection) -> list[dict[str, str]]:
        """
        Generate toàn bộ quality & security files cho NestJS.

        Args:
            collection: QualityCollection từ parser

        Returns:
            Danh sách {path, content} cho mỗi file sinh ra
        """
        results: list[dict[str, str]] = []

        # Lấy profiles và security configs cho stack NestJS
        nestjs_profiles = collection.get_profiles_for_stack(StackType.NESTJS)
        nestjs_security = collection.get_security_for_stack(StackType.NESTJS)

        # Kiểm tra có dùng ESLint và npm-audit không
        use_eslint = False
        use_npm_audit = False
        for sec in nestjs_security:
            for tool in sec.tools:
                if tool == SecurityTool.ESLINT_SECURITY:  # type: ignore[attr-defined]
                    use_eslint = True
                if tool == SecurityTool.NPM_AUDIT:
                    use_npm_audit = True
            # Kiểm tra từ profiles
        for profile in nestjs_profiles:
            if profile.linter == LinterType.ESLINT:
                use_eslint = True

        # Nếu không có config cụ thể, mặc định sinh đầy đủ
        context: dict[str, Any] = {
            "collection": collection,
            "profiles": nestjs_profiles,
            "security_configs": nestjs_security,
            "use_eslint": use_eslint or not nestjs_security,
            "use_npm_audit": use_npm_audit or not nestjs_security,
        }

        # .eslintrc.json
        results.extend(self._generate_eslintrc(context))

        # .prettierrc
        results.extend(self._generate_prettierrc(context))

        # scripts/quality-gate.ts
        results.extend(self._generate_quality_gate(context))

        # .npmrc
        results.extend(self._generate_npmrc(context))

        # tsconfig.strict.json
        results.extend(self._generate_tsconfig_strict(context))

        return results

    def _generate_eslintrc(self, context: dict[str, Any]) -> list[dict[str, str]]:
        """Sinh .eslintrc.json."""
        try:
            content = self.emitter.render(
                "cp24_quality_security/eslintrc.json.jinja2",
                context,
            )
            return [{"path": ".eslintrc.json", "content": content}]
        except Exception:
            return []

    def _generate_prettierrc(self, context: dict[str, Any]) -> list[dict[str, str]]:
        """Sinh .prettierrc."""
        try:
            content = self.emitter.render(
                "cp24_quality_security/prettierrc.jinja2",
                context,
            )
            return [{"path": ".prettierrc", "content": content}]
        except Exception:
            return []

    def _generate_quality_gate(self, context: dict[str, Any]) -> list[dict[str, str]]:
        """Sinh scripts/quality-gate.ts."""
        try:
            content = self.emitter.render(
                "cp24_quality_security/quality_gate.ts.jinja2",
                context,
            )
            return [{"path": "scripts/quality-gate.ts", "content": content}]
        except Exception:
            return []

    def _generate_npmrc(self, context: dict[str, Any]) -> list[dict[str, str]]:
        """Sinh .npmrc."""
        try:
            content = self.emitter.render(
                "cp24_quality_security/npmrc.jinja2",
                context,
            )
            return [{"path": ".npmrc", "content": content}]
        except Exception:
            return []

    def _generate_tsconfig_strict(self, context: dict[str, Any]) -> list[dict[str, str]]:
        """Sinh tsconfig.strict.json."""
        try:
            content = self.emitter.render(
                "cp24_quality_security/tsconfig_strict.json.jinja2",
                context,
            )
            return [{"path": "tsconfig.strict.json", "content": content}]
        except Exception:
            return []
