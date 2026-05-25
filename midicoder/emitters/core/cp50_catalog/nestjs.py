# coding: utf-8
"""
NestJS Emitter cho CP50: Catalog & Taxonomy Engine.

Module này render Jinja2 templates để sinh catalog management code
cho NestJS stack, bao gồm entity, DTO, các service (product,
category, attribute), catalog controller, và catalog module.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.emitters.core.cp50_catalog.parser import CatalogIR
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


__all__ = [
    "NestJSCatalogEmitter",
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


class NestJSCatalogEmitter:
    """Emitter cho NestJS stack — CP50 Catalog & Taxonomy Engine.

    Render templates từ `stacks/nestjs/core/cp50_catalog/`
    để sinh catalog management code.

    Ví dụ:
        >>> emitter = NestJSCatalogEmitter(stack_dir="/path/to/stacks/nestjs/core")
        >>> files = emitter.emit(ir, output_dir="/path/to/output")
    """

    def __init__(self, stack_dir: str | Path) -> None:
        """Khởi tạo emitter.

        Args:
            stack_dir: Đường dẫn đến `stacks/nestjs/core/`.

        Raises:
            MidicoderError: Nếu template directory không tồn tại.
        """
        self.stack_dir = Path(stack_dir)
        self.template_dir = self.stack_dir  # stack_dir đã là .../cp50_catalog

        if not self.template_dir.exists():
            EM.raise_error(
                ErrorCode.CP50_PRODUCT_NOT_FOUND,
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
        ir: CatalogIR,
        output_dir: str | Path,
    ) -> list[GeneratedFile]:
        """Emit catalog management code cho NestJS.

        Sinh 7 files:
        - catalog.entity.ts
        - catalog.dto.ts
        - product.service.ts
        - category.service.ts
        - attribute.service.ts
        - catalog.controller.ts
        - catalog.module.ts

        Args:
            ir: CatalogIR chứa products, categories, variants, attributes.
            output_dir: Đường dẫn output directory.

        Returns:
            Danh sách GeneratedFile.
        """
        output_dir = Path(output_dir)

        context = self._build_context(ir)

        files: list[GeneratedFile] = []

        templates = [
            ("catalog.entity.ts.jinja2", "src/catalog/catalog.entity.ts"),
            ("catalog.dto.ts.jinja2", "src/catalog/catalog.dto.ts"),
            ("product.service.ts.jinja2", "src/catalog/product.service.ts"),
            ("category.service.ts.jinja2", "src/catalog/category.service.ts"),
            ("attribute.service.ts.jinja2", "src/catalog/attribute.service.ts"),
            ("catalog.controller.ts.jinja2", "src/catalog/catalog.controller.ts"),
            ("catalog.module.ts.jinja2", "src/catalog/catalog.module.ts"),
        ]

        for template_name, output_path in templates:
            if self._template_exists(template_name):
                content = self._render(template_name, context)
                files.append(GeneratedFile(path=output_path, content=content))

        return files

    def _build_context(self, ir: CatalogIR) -> dict[str, Any]:
        """Xây dựng template context từ CatalogIR.

        Args:
            ir: CatalogIR input.

        Returns:
            Dict context cho Jinja2.
        """
        products_list = [p.to_dict() for p in ir.products]
        categories_list = [c.to_dict() for c in ir.categories]
        variants_list = [v.to_dict() for v in ir.variants]
        attributes_list = [a.to_dict() for a in ir.attributes]
        attribute_values_list = [av.to_dict() for av in ir.attribute_values]

        return {
            "products": products_list,
            "categories": categories_list,
            "variants": variants_list,
            "attributes": attributes_list,
            "attribute_values": attribute_values_list,
            "use_search": ir.use_search,
            "use_audit": ir.use_audit,
            "product_count": len(ir.products),
            "category_count": len(ir.categories),
            "variant_count": len(ir.variants),
            "attribute_count": len(ir.attributes),
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
                ErrorCode.CP50_PRODUCT_NOT_FOUND,
                reason=f"Jinja2 template không tìm thấy: {template_name}",
            )
        except Exception as e:
            raise EM.raise_error(
                ErrorCode.CP50_PRODUCT_NOT_FOUND,
                reason=f"Render template thất bại {template_name}: {e}",
            )
