# coding: utf-8
"""
Mô-đun Angular emitter cho Code Quality & Security Scanner Generator (CP24).

Sinh ra các file cấu hình chất lượng code và bảo mật cho dự án Angular:
- .eslintrc.json — Cấu hình ESLint với TypeScript và security plugin
- .prettierrc — Cấu hình Prettier formatter
- scripts/quality-gate.ts — Runner script kiểm tra chất lượng code
- lockfile-lint.config.js — Cấu hình lockfile-lint cho npm packages
- .editorconfig — Quy tắc định dạng file chung

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from midicoder.pipeline.emitter import Emitter

from midicoder.packs.cp24_quality_security.models import (
    QualityCollection,
    SecurityScanConfig,
    SeverityLevel,
    StackType,
)


class AngularQualityEmitter:
    """
    Emitter sinh code quality & security cho Angular.

    Sinh ra:
    - .eslintrc.json — ESLint config với @typescript-eslint + security plugin
    - .prettierrc — Prettier config
    - scripts/quality-gate.ts — Quality gate runner (eslint + ng build + lockfile-lint)
    - lockfile-lint.config.js — Lockfile audit config
    - .editorconfig — Editor configuration
    """

    # Mapping giữa tên file output và template path
    _FILE_TEMPLATE_MAP: dict[str, str] = {
        ".eslintrc.json": "eslintrc.json.jinja2",
        ".prettierrc": "prettierrc.jinja2",
        "scripts/quality-gate.ts": "quality_gate.ts.jinja2",
        "lockfile-lint.config.js": "lockfile_lint.config.js.jinja2",
        ".editorconfig": "editorconfig.jinja2",
    }

    def __init__(self, stack_dir: str | Path) -> None:
        """
        Khởi tạo AngularQualityEmitter.

        Args:
            stack_dir: Đường dẫn đến thư mục stack Angular (dùng để xác định template dir).
        """
        self.emitter = Emitter(stack="angular")
        self.stack_dir = Path(stack_dir)

    def generate(
        self,
        collection: QualityCollection,
    ) -> list[dict[str, str]]:
        """
        Generate toàn bộ quality & security files cho Angular.

        Args:
            collection: QualityCollection chứa profiles, security configs, và gate config.

        Returns:
            Danh sách dict với 'path' và 'content' của từng file đã sinh.
        """
        results: list[dict[str, str]] = []

        # Lấy security config dành cho Angular
        angular_security = self._get_angular_security(collection)

        # Lấy gate config (mặc định nếu không có)
        gate_config = collection.gate_config

        # Xây dựng context chung cho tất cả templates
        context: dict[str, Any] = {
            "collection": collection,
            "security_config": angular_security,
            "gate_config": gate_config,
            "min_coverage": gate_config.min_coverage if gate_config else 80,
            "fail_on_severity": (
                angular_security.fail_on_severity.value
                if angular_security
                else "high"
            ),
        }

        # Sinh từng file theo mapping
        for output_path, template_name in self._FILE_TEMPLATE_MAP.items():
            result = self._render_file(template_name, context)
            if result:
                results.append(result)

        return results

    def _render_file(
        self,
        template_name: str,
        context: dict[str, Any],
    ) -> dict[str, str] | None:
        """
        Render một template và trả về dict chứa path và content.

        Args:
            template_name: Tên file template (ví dụ: eslintrc.json.jinja2).
            context: Context dict để render template.

        Returns:
            Dict với 'path' và 'content', hoặc None nếu render thất bại.
        """
        output_path = self._get_output_path(template_name)
        if not output_path:
            return None

        try:
            content = self.emitter.render(
                f"cp24_quality_security/{template_name}",
                context,
            )
            return {"path": output_path, "content": content}
        except Exception:
            return None

    def _get_output_path(self, template_name: str) -> str | None:
        """Tìm output path từ template name."""
        for output_path, name in self._FILE_TEMPLATE_MAP.items():
            if name == template_name:
                return output_path
        return None

    def _get_angular_security(
        self, collection: QualityCollection
    ) -> SecurityScanConfig | None:
        """Lọc security config dành cho Angular stack."""
        for config in collection.security_configs:
            if config.stack == StackType.ANGULAR:
                return config
        return None
