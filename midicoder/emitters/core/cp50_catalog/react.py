# coding: utf-8
"""
React Emitter cho CP50: Catalog & Taxonomy Engine (Frontend).

Module này render Jinja2 templates để sinh catalog management infrastructure
cho React stack, bao gồm:
- ProductList.tsx: Component hiển thị danh sách sản phẩm
- ProductDetail.tsx: Component chi tiết sản phẩm
- CategoryTree.tsx: Component cây phân loại danh mục
- FacetFilter.tsx: Component bộ lọc theo thuộc tính
- useCatalog.ts: Custom hook để quản lý trạng thái catalog
- useFacetedSearch.ts: Custom hook cho tìm kiếm có bộ lọc

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.emitters.core.cp50_catalog.parser import CatalogIR
from midicoder.errors import ErrorCode, MidicoderError, MidicoderErrorManager as EM


__all__ = [
    "ReactCatalogEmitter",
]


class ReactCatalogEmitter:
    """Emitter cho React stack — CP50 Catalog & Taxonomy Engine.

    Render templates từ `stacks/react/core/cp50_catalog/`
    để sinh catalog management frontend components.

    Ví dụ:
        >>> emitter = ReactCatalogEmitter(stack_dir="/path/to/stacks/react/core")
        >>> ir = CatalogIR(products=[...], categories=[...])
        >>> files = emitter.emit(ir)
    """

    _TEMPLATE_MAP: dict[str, str] = {
        "ProductList.tsx.jinja2": "src/catalog/ProductList.tsx",
        "ProductDetail.tsx.jinja2": "src/catalog/ProductDetail.tsx",
        "CategoryTree.tsx.jinja2": "src/catalog/CategoryTree.tsx",
        "FacetFilter.tsx.jinja2": "src/catalog/FacetFilter.tsx",
        "useCatalog.ts.jinja2": "src/catalog/hooks/useCatalog.ts",
        "useFacetedSearch.ts.jinja2": "src/catalog/hooks/useFacetedSearch.ts",
    }

    def __init__(self, stack_dir: str | Path) -> None:
        """Khởi tạo emitter.

        Args:
            stack_dir: Đường dẫn đến `stacks/react/core/`.

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

    def emit(self, ir: CatalogIR, context: dict[str, Any] | None = None) -> list[dict[str, str]]:
        """Emit catalog management infrastructure cho React.

        Sinh 6 files:
        - ProductList.tsx
        - ProductDetail.tsx
        - CategoryTree.tsx
        - FacetFilter.tsx
        - useCatalog.ts
        - useFacetedSearch.ts

        Args:
            ir: CatalogIR chứa sản phẩm, danh mục, biến thể, thuộc tính.
            context: Context bổ sung (optional).

        Returns:
            List của {path, content} cho mỗi file.
        """
        extra_context = context or {}

        products_list = [p.to_dict() for p in ir.products]
        categories_list = [c.to_dict() for c in ir.categories]
        variants_list = [v.to_dict() for v in ir.variants]
        attributes_list = [a.to_dict() for a in ir.attributes]
        attribute_values_list = [av.to_dict() for av in ir.attribute_values]

        template_context: dict[str, Any] = {
            "products": products_list,
            "products_list": products_list,
            "categories": categories_list,
            "categories_list": categories_list,
            "variants": variants_list,
            "variants_list": variants_list,
            "attributes": attributes_list,
            "attributes_list": attributes_list,
            "attribute_values": attribute_values_list,
            "attribute_values_list": attribute_values_list,
            "use_search": ir.use_search,
            "use_audit": ir.use_audit,
            "product_count": len(ir.products),
            "category_count": len(ir.categories),
            "variant_count": len(ir.variants),
            "attribute_count": len(ir.attributes),
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
                ErrorCode.CP50_PRODUCT_NOT_FOUND,
                reason=f"Template không tìm thấy: {template_name}",
            )
        except Exception as e:
            raise EM.raise_error(
                ErrorCode.CP50_PRODUCT_NOT_FOUND,
                reason=f"Render thất bại {template_name}: {e}",
            )
