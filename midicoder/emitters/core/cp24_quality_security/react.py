# coding: utf-8
"""
Mô-đun React emitter cho Code Quality & Security Scanner Generator (CP24).

Emit các file quality/security cho React:
- .eslintrc.json — ESLint config với security plugin
- .prettierrc — Prettier config
- scripts/quality-gate.ts — Quality gate runner (eslint, npm audit, lockfile-lint)
- lockfile-lint.config.js — Lockfile lint config
- .editorconfig — Editor config

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from midicoder.pipeline.emitter import Emitter

from midicoder.emitters.core.cp24_quality_security.models import (
    QualityCollection,
    StackType,
)


class ReactQualityEmitter:
    """
    Emitter sinh code quality & security cho React.

    Sinh ra:
    - .eslintrc.json — ESLint config (react, react-hooks, security, prettier)
    - .prettierrc — Prettier formatting rules
    - scripts/quality-gate.ts — TypeScript quality gate runner
    - lockfile-lint.config.js — Lockfile dependency audit config
    - .editorconfig — Editor code style config
    """

    def __init__(self, stack_dir: str | Path) -> None:
        """
        Khởi tạo ReactQualityEmitter.

        Args:
            stack_dir: Đường dẫn đến stack directory (dùng để xác định template root).
        """
        self.emitter = Emitter(stack="react")
        self.stack_dir = Path(stack_dir)

    def generate(self, collection: QualityCollection) -> list[dict[str, str]]:
        """
        Generate toàn bộ quality/security config files cho React.

        Process:
        1. Sinh .eslintrc.json
        2. Sinh .prettierrc
        3. Sinh scripts/quality-gate.ts
        4. Sinh lockfile-lint.config.js
        5. Sinh .editorconfig

        Args:
            collection: QualityCollection chứa profiles và security configs.

        Returns:
            Danh sách dict với key 'path' và 'content' cho từng file đã generate.
        """
        results: list[dict[str, str]] = []

        results.extend(self._generate_eslintrc(collection))
        results.extend(self._generate_prettierrc(collection))
        results.extend(self._generate_quality_gate(collection))
        results.extend(self._generate_lockfile_lint(collection))
        results.extend(self._generate_editorconfig(collection))

        return results

    # ------------------------------------------------------------------
    # Nhóm phương thức render từng file
    # ------------------------------------------------------------------

    def _generate_eslintrc(self, collection: QualityCollection) -> list[dict[str, str]]:
        """Sinh .eslintrc.json — cấu hình ESLint với security rules."""
        try:
            # Lấy các rule overrides từ collection
            rule_overrides: dict[str, Any] = {}
            for profile in collection.get_profiles_for_stack(StackType.REACT):
                rule_overrides.update(profile.rules)

            security_rules: list[dict[str, Any]] = []
            for config in collection.get_security_for_stack(StackType.REACT):
                for rule in config.rules:
                    security_rules.append(rule.to_dict())

            content = self.emitter.render(
                "cp24_quality_security/eslintrc.json.jinja2",
                {
                    "collection": collection,
                    "rule_overrides": rule_overrides,
                    "security_rules": security_rules,
                },
            )
            return [{"path": ".eslintrc.json", "content": content}]
        except Exception:
            return []

    def _generate_prettierrc(self, collection: QualityCollection) -> list[dict[str, str]]:
        """Sinh .prettierrc — cấu hình Prettier formatting."""
        try:
            content = self.emitter.render(
                "cp24_quality_security/prettierrc.jinja2",
                {"collection": collection},
            )
            return [{"path": ".prettierrc", "content": content}]
        except Exception:
            return []

    def _generate_quality_gate(self, collection: QualityCollection) -> list[dict[str, str]]:
        """Sinh scripts/quality-gate.ts — chất lượng gate runner."""
        try:
            # Lấy cấu hình quality gate
            gate_config = collection.gate_config
            min_coverage = gate_config.min_coverage if gate_config else 80
            block_on_fail = gate_config.block_on_fail if gate_config else True

            content = self.emitter.render(
                "cp24_quality_security/quality_gate.ts.jinja2",
                {
                    "collection": collection,
                    "min_coverage": min_coverage,
                    "block_on_fail": block_on_fail,
                },
            )
            return [{"path": "scripts/quality-gate.ts", "content": content}]
        except Exception:
            return []

    def _generate_lockfile_lint(self, collection: QualityCollection) -> list[dict[str, str]]:
        """Sinh lockfile-lint.config.js — kiểm tra lockfile dependencies."""
        try:
            content = self.emitter.render(
                "cp24_quality_security/lockfile_lint.config.js.jinja2",
                {"collection": collection},
            )
            return [{"path": "lockfile-lint.config.js", "content": content}]
        except Exception:
            return []

    def _generate_editorconfig(self, collection: QualityCollection) -> list[dict[str, str]]:
        """Sinh .editorconfig — cấu hình editor code style."""
        try:
            content = self.emitter.render(
                "cp24_quality_security/editorconfig.jinja2",
                {"collection": collection},
            )
            return [{"path": ".editorconfig", "content": content}]
        except Exception:
            return []
