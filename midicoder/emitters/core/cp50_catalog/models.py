# coding: utf-8
"""
Mô-đun models cho CP50 — Catalog & Taxonomy Engine.

Định nghĩa các dataclass biểu diễn:
- ProductStatus: Trạng thái sản phẩm (DRAFT, ACTIVE, INACTIVE, ARCHIVED)
- AttributeType: Loại thuộc tính (STRING, NUMBER, BOOLEAN, DATE, ENUM, COLOR)
- SortOrder: Thứ tự sắp xếp (ASC, DESC)
- Visibility: Chế độ hiển thị (PUBLIC, INTERNAL, RESTRICTED)
- CategoryLevel: Mức độ phân loại category (metadata only)
- Product: Sản phẩm trong catalog
- Category: Danh mục sản phẩm (hierarchical)
- ProductVariant: Biến thể của sản phẩm (màu sắc, kích cỡ, v.v.)
- AttributeDefinition: Định nghĩa thuộc tính của sản phẩm
- AttributeValue: Giá trị thuộc tính gán cho sản phẩm/variant
- CatalogEngine: Engine quản lý toàn bộ catalog, taxonomy, variant, attribute, và tìm kiếm

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# ===========================================================================
# Enums
# ===========================================================================


class ProductStatus(str, Enum):
    """Trạng thái vòng đời của sản phẩm.

    - DRAFT: Bản nháp, chưa công bố
    - ACTIVE: Đang hoạt động, hiển thị trên cửa hàng
    - INACTIVE: Tạm ngừng, không hiển thị nhưng vẫn lưu trữ
    - ARCHIVED: Đã lưu kho, không còn kinh doanh
    """
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class AttributeType(str, Enum):
    """Loại dữ liệu của thuộc tính sản phẩm.

    - STRING: Chuỗi ký tự
    - NUMBER: Số nguyên hoặc số thực
    - BOOLEAN: Đúng / Sai
    - DATE: Ngày tháng
    - ENUM: Danh sách giá trị cố định
    - COLOR: Mã màu (HEX, RGB)
    """
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    DATE = "date"
    ENUM = "enum"
    COLOR = "color"


class SortOrder(str, Enum):
    """Thứ tự sắp xếp kết quả.

    - ASC: Tăng dần
    - DESC: Giảm dần
    """
    ASC = "asc"
    DESC = "desc"


class Visibility(str, Enum):
    """Chế độ hiển thị của sản phẩm.

    - PUBLIC: Hiển thị công khai cho mọi người
    - INTERNAL: Chỉ nội bộ xem được
    - RESTRICTED: Chỉ người dùng được ủy quyền mới xem được
    """
    PUBLIC = "public"
    INTERNAL = "internal"
    RESTRICTED = "restricted"


class CategoryLevel(str, Enum):
    """Mức độ phân loại của danh mục (chỉ dùng cho metadata).

    - ROOT: Danh mục gốc
    - LEVEL_1: Cấp 1
    - LEVEL_2: Cấp 2
    - LEVEL_3: Cấp 3
    """
    ROOT = "root"
    LEVEL_1 = "level_1"
    LEVEL_2 = "level_2"
    LEVEL_3 = "level_3"


# ===========================================================================
# Helper: tự động tạo slug từ tên
# ===========================================================================


def _slugify(text: str) -> str:
    """Chuyển chuỗi thành slug thân thiện với URL.

    Quy trình:
    1. Chuyển sang chữ thường
    2. Chuẩn hóa Unicode (dấu → không dấu)
    3. Thay khoảng trắng và ký tự đặc biệt bằng dấu gạch ngang
    4. Loại bỏ ký tự không phải ASCII chữ/số/gạch ngang

    Args:
        text: Chuỗi đầu vào

    Returns:
        Chuỗi slug đã xử lý
    """
    text = text.lower().strip()
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


# ===========================================================================
# Product
# ===========================================================================


@dataclass
class Product:
    """Sản phẩm trong catalog.

    Đại diện cho một sản phẩm với đầy đủ thông tin giá cả, kích thước,
    hình ảnh, SEO, và thuộc tính mở rộng qua metadata.

    Attributes:
        product_id: ID duy nhất của sản phẩm
        name: Tên sản phẩm (hiển thị)
        slug: Đường dẫn URL thân thiện (tự động từ name)
        sku: Mã SKU duy nhất
        description: Mô tả chi tiết sản phẩm
        category_id: ID danh mục phân loại
        brand_id: ID thương hiệu
        price: Giá bán
        cost_price: Giá vốn
        compare_at_price: Giá so sánh (giá gốc/giá cũ)
        currency: Đơn vị tiền tệ (mặc định VND)
        weight: Khối lượng sản phẩm
        dimensions: Kích thước (length, width, height)
        status: Trạng thái vòng đời sản phẩm
        visibility: Chế độ hiển thị
        tags: Danh sách thẻ phân loại
        seo_metadata: Metadata cho SEO (title, description, keywords)
        images: Danh sách URL hình ảnh
        metadata: Dữ liệu bổ sung tùy chỉnh
        is_deleted: Cờ xóa mềm
        tenant_id: ID tenant sở hữu sản phẩm
        created_at: Thời điểm tạo
        updated_at: Thời điểm cập nhật cuối
        deleted_at: Thời điểm xóa mềm
    """
    product_id: str
    name: str
    slug: str = ""
    sku: str = ""
    description: str = ""
    category_id: str = ""
    brand_id: str = ""
    price: float = 0.0
    cost_price: float = 0.0
    compare_at_price: float = 0.0
    currency: str = "VND"
    weight: float = 0.0
    dimensions: dict[str, float] = field(default_factory=dict)
    status: ProductStatus = ProductStatus.DRAFT
    visibility: Visibility = Visibility.PUBLIC
    tags: list[str] = field(default_factory=list)
    seo_metadata: dict[str, str] = field(default_factory=dict)
    images: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    is_deleted: bool = False
    tenant_id: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate sản phẩm sau khi khởi tạo.

        - Kiểm tra product_id và name không để trống
        - Tự động đặt timestamp nếu chưa có
        - Tự động tạo slug từ name nếu chưa có
        """
        if not self.product_id or not self.product_id.strip():
            EM.raise_error(
                ErrorCode.CP50_PRODUCT_NOT_FOUND,
                reason="product_id bắt buộc và không được để trống",
            )

        if not self.name or not self.name.strip():
            EM.raise_error(
                ErrorCode.CP50_PRODUCT_NOT_FOUND,
                reason="name bắt buộc và không được để trống",
            )

        now = datetime.now(timezone.utc)
        if self.created_at is None:
            self.created_at = now
        if self.updated_at is None:
            self.updated_at = now

        # Tự động tạo slug từ name nếu chưa có
        if not self.slug or not self.slug.strip():
            self.slug = _slugify(self.name)

    def to_dict(self) -> dict[str, Any]:
        """Chuyển Product sang dict để xuất JSON."""
        return {
            "product_id": self.product_id,
            "name": self.name,
            "slug": self.slug,
            "sku": self.sku,
            "description": self.description,
            "category_id": self.category_id,
            "brand_id": self.brand_id,
            "price": self.price,
            "cost_price": self.cost_price,
            "compare_at_price": self.compare_at_price,
            "currency": self.currency,
            "weight": self.weight,
            "dimensions": self.dimensions,
            "status": self.status.value,
            "visibility": self.visibility.value,
            "tags": self.tags,
            "seo_metadata": self.seo_metadata,
            "images": self.images,
            "metadata": self.metadata,
            "is_deleted": self.is_deleted,
            "tenant_id": self.tenant_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Product":
        """Tạo Product từ dict nhập JSON."""
        return cls(
            product_id=data.get("product_id", ""),
            name=data.get("name", ""),
            slug=data.get("slug", ""),
            sku=data.get("sku", ""),
            description=data.get("description", ""),
            category_id=data.get("category_id", ""),
            brand_id=data.get("brand_id", ""),
            price=data.get("price", 0.0),
            cost_price=data.get("cost_price", 0.0),
            compare_at_price=data.get("compare_at_price", 0.0),
            currency=data.get("currency", "VND"),
            weight=data.get("weight", 0.0),
            dimensions=data.get("dimensions", {}),
            status=ProductStatus(data.get("status", "draft")),
            visibility=Visibility(data.get("visibility", "public")),
            tags=data.get("tags", []),
            seo_metadata=data.get("seo_metadata", {}),
            images=data.get("images", []),
            metadata=data.get("metadata", {}),
            is_deleted=data.get("is_deleted", False),
            tenant_id=data.get("tenant_id", ""),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
            deleted_at=datetime.fromisoformat(data["deleted_at"]) if data.get("deleted_at") else None,
        )


# ===========================================================================
# Category
# ===========================================================================


@dataclass
class Category:
    """Danh mục sản phẩm (hierarchical).

    Đại diện cho một danh mục có thể có parent_id để tạo cấu trúc cây.
    Giới hạn độ sâu tối đa là 4 cấp (ROOT + 3 levels).

    Attributes:
        category_id: ID duy nhất của danh mục
        name: Tên danh mục (hiển thị)
        slug: Đường dẫn URL thân thiện
        description: Mô tả danh mục
        parent_id: ID danh mục cha (None = cấp gốc)
        sort_order: Thứ tự sắp xếp trong cùng cấp
        icon: URL hoặc tên biểu tượng
        is_active: Có hoạt động không
        descendant_count: Số danh mục con (tất cả cấp)
        metadata: Dữ liệu bổ sung tùy chỉnh
        created_at: Thời điểm tạo
        updated_at: Thời điểm cập nhật cuối
    """
    category_id: str
    name: str
    slug: str = ""
    description: str = ""
    parent_id: str | None = None
    sort_order: int = 0
    icon: str = ""
    is_active: bool = True
    descendant_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate danh mục sau khi khởi tạo.

        - Kiểm tra category_id và name không để trống
        - Tự động tạo slug từ name nếu chưa có
        - Tự động đặt timestamp nếu chưa có
        """
        if not self.category_id or not self.category_id.strip():
            EM.raise_error(
                ErrorCode.CP50_CATEGORY_NOT_FOUND,
                reason="category_id bắt buộc và không được để trống",
            )

        if not self.name or not self.name.strip():
            EM.raise_error(
                ErrorCode.CP50_CATEGORY_NOT_FOUND,
                reason="name bắt buộc và không được để trống",
            )

        now = datetime.now(timezone.utc)
        if self.created_at is None:
            self.created_at = now
        if self.updated_at is None:
            self.updated_at = now

        # Tự động tạo slug từ name nếu chưa có
        if not self.slug or not self.slug.strip():
            self.slug = _slugify(self.name)

    def to_dict(self) -> dict[str, Any]:
        """Chuyển Category sang dict để xuất JSON."""
        return {
            "category_id": self.category_id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "parent_id": self.parent_id,
            "sort_order": self.sort_order,
            "icon": self.icon,
            "is_active": self.is_active,
            "descendant_count": self.descendant_count,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Category":
        """Tạo Category từ dict nhập JSON."""
        return cls(
            category_id=data.get("category_id", ""),
            name=data.get("name", ""),
            slug=data.get("slug", ""),
            description=data.get("description", ""),
            parent_id=data.get("parent_id", None),
            sort_order=data.get("sort_order", 0),
            icon=data.get("icon", ""),
            is_active=data.get("is_active", True),
            descendant_count=data.get("descendant_count", 0),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
        )


# ===========================================================================
# ProductVariant
# ===========================================================================


@dataclass
class ProductVariant:
    """Biến thể của sản phẩm.

    Đại diện cho một biến thể cụ thể của sản phẩm, ví dụ:
    áo phông màu đỏ kích thước L, hoặc điện thoại 256GB màu đen.

    Attributes:
        variant_id: ID duy nhất của biến thể
        product_id: ID sản phẩm mẹ
        sku: Mã SKU duy nhất của biến thể
        name: Tên biến thể (hiển thị)
        attribute_values: Giá trị thuộc tính (key → value)
        price: Giá bán biến thể
        cost_price: Giá vốn biến thể
        weight: Khối lượng biến thể
        barcode: Mã vạch (EAN, UPC)
        images: Danh sách URL hình ảnh biến thể
        is_active: Có hoạt động không
        sort_order: Thứ tự sắp xếp
        metadata: Dữ liệu bổ sung tùy chỉnh
        created_at: Thời điểm tạo
        updated_at: Thời điểm cập nhật cuối
    """
    variant_id: str
    product_id: str
    sku: str
    name: str = ""
    attribute_values: dict[str, str] = field(default_factory=dict)
    price: float = 0.0
    cost_price: float = 0.0
    weight: float = 0.0
    barcode: str = ""
    images: list[str] = field(default_factory=list)
    is_active: bool = True
    sort_order: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate biến thể sau khi khởi tạo.

        - Kiểm tra variant_id, product_id, sku không để trống
        - Tự động đặt timestamp nếu chưa có
        """
        if not self.variant_id or not self.variant_id.strip():
            EM.raise_error(
                ErrorCode.CP50_VARIANT_NOT_FOUND,
                reason="variant_id bắt buộc và không được để trống",
            )

        if not self.product_id or not self.product_id.strip():
            EM.raise_error(
                ErrorCode.CP50_PRODUCT_NOT_FOUND,
                reason="product_id bắt buộc cho biến thể sản phẩm",
            )

        if not self.sku or not self.sku.strip():
            EM.raise_error(
                ErrorCode.CP50_DUPLICATE_SKU,
                reason="sku bắt buộc và không được để trống cho biến thể",
            )

        now = datetime.now(timezone.utc)
        if self.created_at is None:
            self.created_at = now
        if self.updated_at is None:
            self.updated_at = now

    def to_dict(self) -> dict[str, Any]:
        """Chuyển ProductVariant sang dict để xuất JSON."""
        return {
            "variant_id": self.variant_id,
            "product_id": self.product_id,
            "sku": self.sku,
            "name": self.name,
            "attribute_values": self.attribute_values,
            "price": self.price,
            "cost_price": self.cost_price,
            "weight": self.weight,
            "barcode": self.barcode,
            "images": self.images,
            "is_active": self.is_active,
            "sort_order": self.sort_order,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProductVariant":
        """Tạo ProductVariant từ dict nhập JSON."""
        return cls(
            variant_id=data.get("variant_id", ""),
            product_id=data.get("product_id", ""),
            sku=data.get("sku", ""),
            name=data.get("name", ""),
            attribute_values=data.get("attribute_values", {}),
            price=data.get("price", 0.0),
            cost_price=data.get("cost_price", 0.0),
            weight=data.get("weight", 0.0),
            barcode=data.get("barcode", ""),
            images=data.get("images", []),
            is_active=data.get("is_active", True),
            sort_order=data.get("sort_order", 0),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
        )


# ===========================================================================
# AttributeDefinition
# ===========================================================================


@dataclass
class AttributeDefinition:
    """Định nghĩa thuộc tính của sản phẩm.

    Mô tả một thuộc tính có thể gán cho sản phẩm, bao gồm loại dữ liệu,
    quy tắc kiểm tra, và các tùy chọn (cho ENUM).

    Attributes:
        attribute_id: ID duy nhất của thuộc tính
        name: Tên hiển thị của thuộc tính
        key: Khóa máy đọc (tự động từ name)
        attribute_type: Loại dữ liệu (STRING, NUMBER, v.v.)
        is_required: Bắt buộc phải có giá trị
        validation_rules: Quy tắc kiểm tra (min, max, pattern)
        options: Danh sách giá trị cho ENUM
        unit: Đơn vị (kg, cm, ml, v.v.)
        is_searchable: Có thể tìm kiếm theo thuộc tính này
        is_filterable: Có thể lọc theo thuộc tính này
        is_visible: Hiển thị trên giao diện
        sort_order: Thứ tự sắp xếp
        metadata: Dữ liệu bổ sung tùy chỉnh
        created_at: Thời điểm tạo
        updated_at: Thời điểm cập nhật cuối
    """
    attribute_id: str
    name: str
    key: str = ""
    attribute_type: AttributeType = AttributeType.STRING
    is_required: bool = False
    validation_rules: dict[str, Any] = field(default_factory=dict)
    options: list[str] = field(default_factory=list)
    unit: str = ""
    is_searchable: bool = False
    is_filterable: bool = False
    is_visible: bool = True
    sort_order: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate định nghĩa thuộc tính sau khi khởi tạo.

        - Kiểm tra attribute_id và name không để trống
        - Tự động tạo key từ name nếu chưa có
        - Tự động đặt timestamp nếu chưa có
        """
        if not self.attribute_id or not self.attribute_id.strip():
            EM.raise_error(
                ErrorCode.CP50_ATTRIBUTE_NOT_FOUND,
                reason="attribute_id bắt buộc và không được để trống",
            )

        if not self.name or not self.name.strip():
            EM.raise_error(
                ErrorCode.CP50_ATTRIBUTE_NOT_FOUND,
                reason="name bắt buộc và không được để trống",
            )

        now = datetime.now(timezone.utc)
        if self.created_at is None:
            self.created_at = now
        if self.updated_at is None:
            self.updated_at = now

        # Tự động tạo key từ name nếu chưa có
        if not self.key or not self.key.strip():
            self.key = _slugify(self.name)

    def to_dict(self) -> dict[str, Any]:
        """Chuyển AttributeDefinition sang dict để xuất JSON."""
        return {
            "attribute_id": self.attribute_id,
            "name": self.name,
            "key": self.key,
            "attribute_type": self.attribute_type.value,
            "is_required": self.is_required,
            "validation_rules": self.validation_rules,
            "options": self.options,
            "unit": self.unit,
            "is_searchable": self.is_searchable,
            "is_filterable": self.is_filterable,
            "is_visible": self.is_visible,
            "sort_order": self.sort_order,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AttributeDefinition":
        """Tạo AttributeDefinition từ dict nhập JSON."""
        return cls(
            attribute_id=data.get("attribute_id", ""),
            name=data.get("name", ""),
            key=data.get("key", ""),
            attribute_type=AttributeType(data.get("attribute_type", "string")),
            is_required=data.get("is_required", False),
            validation_rules=data.get("validation_rules", {}),
            options=data.get("options", []),
            unit=data.get("unit", ""),
            is_searchable=data.get("is_searchable", False),
            is_filterable=data.get("is_filterable", False),
            is_visible=data.get("is_visible", True),
            sort_order=data.get("sort_order", 0),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
        )


# ===========================================================================
# AttributeValue
# ===========================================================================


@dataclass
class AttributeValue:
    """Giá trị thuộc tính gán cho sản phẩm hoặc biến thể.

    Liên kết một giá trị cụ thể với một thuộc tính đã định nghĩa,
    có thể gán ở cấp độ product hoặc variant.

    Attributes:
        attribute_value_id: ID duy nhất của giá trị thuộc tính
        attribute_id: ID thuộc tính định nghĩa
        product_id: ID sản phẩm (nếu gán ở cấp product)
        variant_id: ID biến thể (nếu gán ở cấp variant)
        value: Giá trị thực tế (str/int/float/bool/list)
    """
    attribute_value_id: str
    attribute_id: str
    product_id: str = ""
    variant_id: str = ""
    value: Any = None

    def __post_init__(self) -> None:
        """Validate giá trị thuộc tính sau khi khởi tạo.

        - Kiểm tra attribute_value_id và attribute_id không để trống
        """
        if not self.attribute_value_id or not self.attribute_value_id.strip():
            EM.raise_error(
                ErrorCode.CP50_ATTRIBUTE_NOT_FOUND,
                reason="attribute_value_id bắt buộc và không được để trống",
            )

        if not self.attribute_id or not self.attribute_id.strip():
            EM.raise_error(
                ErrorCode.CP50_ATTRIBUTE_NOT_FOUND,
                reason="attribute_id bắt buộc cho giá trị thuộc tính",
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển AttributeValue sang dict để xuất JSON."""
        return {
            "attribute_value_id": self.attribute_value_id,
            "attribute_id": self.attribute_id,
            "product_id": self.product_id,
            "variant_id": self.variant_id,
            "value": self.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AttributeValue":
        """Tạo AttributeValue từ dict nhập JSON."""
        return cls(
            attribute_value_id=data.get("attribute_value_id", ""),
            attribute_id=data.get("attribute_id", ""),
            product_id=data.get("product_id", ""),
            variant_id=data.get("variant_id", ""),
            value=data.get("value", None),
        )


# ===========================================================================
# CatalogEngine
# ===========================================================================


class CatalogEngine:
    """Engine quản lý toàn bộ catalog, taxonomy, variant, attribute, và tìm kiếm.

    In-memory engine cho quản lý catalog sản phẩm: CRUD sản phẩm,
    xây dựng cây danh mục, quản lý biến thể và thuộc tính, tìm kiếm
    với bộ lọc (faceted search).

    Workflow:
    1. Định nghĩa AttributeDefinition (kiểu thuộc tính)
    2. Tạo Category (cây phân loại)
    3. Tạo Product (gắn category, brand)
    4. Tạo ProductVariant (biến thể của product)
    5. Gán AttributeValue (thuộc tính cho product/variant)
    6. Tìm kiếm sản phẩm với filters và aggregations

    Attributes:
        products: Dict product_id → Product
        categories: Dict category_id → Category
        variants: Dict variant_id → ProductVariant
        attributes: Dict attribute_id → AttributeDefinition
        attribute_values: Danh sách AttributeValue
    """

    def __init__(self) -> None:
        """Khởi tạo CatalogEngine với các bộ sưu tập rỗng."""
        self.products: dict[str, Product] = {}
        self.categories: dict[str, Category] = {}
        self.variants: dict[str, ProductVariant] = {}
        self.attributes: dict[str, AttributeDefinition] = {}
        self.attribute_values: list[AttributeValue] = []
        self._product_counter = 0
        self._variant_counter = 0
        self._attr_value_counter = 0

    # ---------------------------------------------------------------------
    # Product CRUD
    # ---------------------------------------------------------------------

    def create_product(self, product: Product) -> Product:
        """Tạo sản phẩm mới trong catalog.

        Kiểm tra SKU trùng lặp (nếu có), sau đó lưu vào bộ sưu tập.

        Args:
            product: Đối tượng Product cần tạo

        Returns:
            Product đã tạo

        Raises:
            MidicoderError: Nếu SKU trùng lặp với sản phẩm khác (MDC-CP50-005)
        """
        now = datetime.now(timezone.utc)
        product.updated_at = now

        # Kiểm tra SKU trùng lặp
        if product.sku and product.sku.strip():
            for existing in self.products.values():
                if existing.sku == product.sku and not existing.is_deleted:
                    EM.raise_error(
                        ErrorCode.CP50_DUPLICATE_SKU,
                        sku=product.sku,
                        existing_product_id=existing.product_id,
                    )

        self.products[product.product_id] = product
        return product

    def update_product(self, product_id: str, **kwargs: Any) -> Product:
        """Cập nhật thông tin sản phẩm theo ID.

        Chấp nhận các trường cập nhật dưới dạng keyword arguments
        và ghi đè lên sản phẩm hiện có.

        Args:
            product_id: ID sản phẩm cần cập nhật
            **kwargs: Các trường cần cập nhật (name, price, status, v.v.)

        Returns:
            Product đã được cập nhật

        Raises:
            MidicoderError: Nếu product_id không tồn tại (MDC-CP50-001)
        """
        if product_id not in self.products:
            EM.raise_error(
                ErrorCode.CP50_PRODUCT_NOT_FOUND,
                product_id=product_id,
            )

        product = self.products[product_id]

        # Cập nhật các trường hợp lệ
        allowed_fields = {f.name for f in product.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        for key, value in kwargs.items():
            if key in allowed_fields:
                setattr(product, key, value)

        product.updated_at = datetime.now(timezone.utc)

        # Nếu name thay đổi, tái tạo slug nếu slug chưa được đặt thủ công
        if "name" in kwargs and "slug" not in kwargs:
            product.slug = _slugify(product.name)

        return product

    def delete_product(self, product_id: str) -> Product:
        """Xóa mềm sản phẩm (soft delete).

        Đặt is_deleted = True và ghi lại deleted_at, không xóa khỏi
        bộ sưu tập để có thể khôi phục sau này.

        Args:
            product_id: ID sản phẩm cần xóa

        Returns:
            Product đã được xóa mềm

        Raises:
            MidicoderError: Nếu product_id không tồn tại (MDC-CP50-001)
        """
        if product_id not in self.products:
            EM.raise_error(
                ErrorCode.CP50_PRODUCT_NOT_FOUND,
                product_id=product_id,
            )

        product = self.products[product_id]
        product.is_deleted = True
        product.deleted_at = datetime.now(timezone.utc)
        product.updated_at = product.deleted_at

        return product

    def get_product(self, product_id: str) -> Product:
        """Lấy sản phẩm theo ID.

        Args:
            product_id: ID sản phẩm cần lấy

        Returns:
            Product tìm thấy

        Raises:
            MidicoderError: Nếu product_id không tồn tại (MDC-CP50-001)
        """
        if product_id not in self.products:
            EM.raise_error(
                ErrorCode.CP50_PRODUCT_NOT_FOUND,
                product_id=product_id,
            )

        return self.products[product_id]

    def list_products(
        self,
        status: ProductStatus | None = None,
        category_id: str | None = None,
    ) -> list[Product]:
        """Liệt kê sản phẩm với bộ lọc tùy chọn.

        Lọc theo trạng thái và/hoặc danh mục, luôn loại bỏ sản phẩm
        đã bị xóa mềm.

        Args:
            status: Trạng thái cần lọc (None = tất cả)
            category_id: ID danh mục cần lọc (None = tất cả)

        Returns:
            Danh sách Product thỏa mãn điều kiện lọc
        """
        results: list[Product] = []
        for product in self.products.values():
            if product.is_deleted:
                continue
            if status is not None and product.status != status:
                continue
            if category_id is not None and product.category_id != category_id:
                continue
            results.append(product)
        return results

    def restore_product(self, product_id: str) -> Product:
        """Khôi phục sản phẩm đã bị xóa mềm.

        Đặt is_deleted = False, cleared deleted_at, và chuyển
        trạng thái về DRAFT để người dùng xem lại trước khi kích hoạt.

        Args:
            product_id: ID sản phẩm cần khôi phục

        Returns:
            Product đã được khôi phục

        Raises:
            MidicoderError: Nếu product_id không tồn tại hoặc không bị xóa (MDC-CP50-001)
        """
        if product_id not in self.products:
            EM.raise_error(
                ErrorCode.CP50_PRODUCT_NOT_FOUND,
                product_id=product_id,
            )

        product = self.products[product_id]
        if not product.is_deleted:
            EM.raise_error(
                ErrorCode.CP50_INVALID_PRODUCT_STATUS,
                reason="Sản phẩm chưa bị xóa, không cần khôi phục",
                current_status=product.status.value,
            )

        product.is_deleted = False
        product.deleted_at = None
        product.status = ProductStatus.DRAFT
        product.updated_at = datetime.now(timezone.utc)

        return product

    # ---------------------------------------------------------------------
    # Category
    # ---------------------------------------------------------------------

    def create_category(self, category: Category) -> Category:
        """Tạo danh mục mới trong taxonomy.

        Kiểm tra chu kỳ (cycle) nếu parent_id được chỉ định và
        kiểm tra độ sâu phân loại.

        Args:
            category: Đối tượng Category cần tạo

        Returns:
            Category đã tạo

        Raises:
            MidicoderError: Nếu parent_id tạo chu kỳ (MDC-CP50-007)
            MidicoderError: Nếu độ sâu phân loại vượt quá giới hạn (MDC-CP50-009)
        """
        now = datetime.now(timezone.utc)
        category.updated_at = now

        # Kiểm tra parent_id có tồn tại không
        if category.parent_id is not None:
            if category.parent_id not in self.categories:
                EM.raise_error(
                    ErrorCode.CP50_CATEGORY_NOT_FOUND,
                    category_id=category.parent_id,
                )

            # Kiểm tra chu kỳ: category không được là tổ tiên của parent
            ancestors = self.get_category_ancestors(category.parent_id)
            ancestor_ids = {c.category_id for c in ancestors}
            if category.category_id in ancestor_ids:
                EM.raise_error(
                    ErrorCode.CP50_CATEGORY_CYCLE_DETECTED,
                    category_id=category.category_id,
                    parent_id=category.parent_id,
                )

            # Kiểm tra độ sâu (tối đa 4 cấp: ROOT + 3)
            depth = len(ancestors) + 1  # +1 cho parent
            if depth > 3:
                EM.raise_error(
                    ErrorCode.CP50_CATEGORY_DEPTH_EXCEEDED,
                    category_id=category.category_id,
                    current_depth=depth,
                    max_depth=3,
                )

            # Cập nhật descendant_count của parent
            parent = self.categories[category.parent_id]
            parent.descendant_count += 1

        self.categories[category.category_id] = category
        return category

    def get_category_tree(self) -> list[Category]:
        """Xây dựng cây danh mục từ danh sách phẳng.

        Traversing tất cả categories và sắp xếp thành danh sách
        các nút gốc, mỗi nút có danh sách children lồng nhau.
        (Kết quả vẫn là list[Category] vì Category không có children field,
         nhưng các category con được trả về theo thứ tự BFS).

        Returns:
            Danh sách Category theo thứ tự cây (BFS)
        """
        if not self.categories:
            return []

        # Xây dựng ánh xạ parent_id → danh sách con
        children_map: dict[str | None, list[Category]] = {}
        for cat in self.categories.values():
            children_map.setdefault(cat.parent_id, []).append(cat)

        # Sắp xếp mỗi danh sách con theo sort_order
        for cat_list in children_map.values():
            cat_list.sort(key=lambda c: c.sort_order)

        # BFS từ các nút gốc
        tree: list[Category] = []
        queue: list[Category] = list(children_map.get(None, []))
        while queue:
            current = queue.pop(0)
            tree.append(current)
            for child in children_map.get(current.category_id, []):
                queue.append(child)

        return tree

    def get_category_ancestors(self, category_id: str) -> list[Category]:
        """Lấy danh sách tất cả tổ tiên của danh mục (từ gốc đến cha trực tiếp).

        Args:
            category_id: ID danh mục cần lấy tổ tiên

        Returns:
            Danh sách Category từ gốc đến cha trực tiếp

        Raises:
            MidicoderError: Nếu category_id không tồn tại (MDC-CP50-002)
        """
        if category_id not in self.categories:
            EM.raise_error(
                ErrorCode.CP50_CATEGORY_NOT_FOUND,
                category_id=category_id,
            )

        ancestors: list[Category] = []
        current = self.categories[category_id]
        while current.parent_id is not None:
            if current.parent_id not in self.categories:
                break
            parent = self.categories[current.parent_id]
            ancestors.append(parent)
            current = parent

        # Đảo ngược để từ gốc đến cha trực tiếp
        ancestors.reverse()
        return ancestors

    def get_category_descendants(self, category_id: str) -> list[Category]:
        """Lấy danh sách tất cả danh mục con (tất cả cấp) của một danh mục.

        Args:
            category_id: ID danh mục cần lấy con

        Returns:
            Danh sách Category con (BFS, bao gồm cả con của con)

        Raises:
            MidicoderError: Nếu category_id không tồn tại (MDC-CP50-002)
        """
        if category_id not in self.categories:
            EM.raise_error(
                ErrorCode.CP50_CATEGORY_NOT_FOUND,
                category_id=category_id,
            )

        descendants: list[Category] = []
        queue: list[str] = [category_id]

        while queue:
            current_id = queue.pop(0)
            for cat in self.categories.values():
                if cat.parent_id == current_id:
                    descendants.append(cat)
                    queue.append(cat.category_id)

        return descendants

    # ---------------------------------------------------------------------
    # Variant
    # ---------------------------------------------------------------------

    def create_variant(self, variant: ProductVariant) -> ProductVariant:
        """Tạo biến thể sản phẩm mới.

        Kiểm tra rằng product_id mẹ tồn tại và SKU không trùng
        với biến thể khác.

        Args:
            variant: Đối tượng ProductVariant cần tạo

        Returns:
            ProductVariant đã tạo

        Raises:
            MidicoderError: Nếu product_id mẹ không tồn tại (MDC-CP50-001)
            MidicoderError: Nếu SKU trùng lặp (MDC-CP50-005)
        """
        now = datetime.now(timezone.utc)
        variant.updated_at = now

        # Kiểm tra product_id mẹ tồn tại
        if variant.product_id not in self.products:
            EM.raise_error(
                ErrorCode.CP50_PRODUCT_NOT_FOUND,
                product_id=variant.product_id,
            )

        # Kiểm tra SKU trùng lặp trong variants
        for existing in self.variants.values():
            if existing.sku == variant.sku:
                EM.raise_error(
                    ErrorCode.CP50_DUPLICATE_SKU,
                    sku=variant.sku,
                    existing_variant_id=existing.variant_id,
                )

        self.variants[variant.variant_id] = variant
        return variant

    def list_variants_for_product(self, product_id: str) -> list[ProductVariant]:
        """Liệt kê tất cả biến thể của một sản phẩm.

        Sắp xếp theo sort_order tăng dần.

        Args:
            product_id: ID sản phẩm mẹ

        Returns:
            Danh sách ProductVariant thuộc sản phẩm
        """
        product_variants = [
            v for v in self.variants.values()
            if v.product_id == product_id
        ]
        product_variants.sort(key=lambda v: v.sort_order)
        return product_variants

    # ---------------------------------------------------------------------
    # Attribute
    # ---------------------------------------------------------------------

    def create_attribute_definition(self, attr: AttributeDefinition) -> AttributeDefinition:
        """Tạo định nghĩa thuộc tính mới.

        Args:
            attr: Đối tượng AttributeDefinition cần tạo

        Returns:
            AttributeDefinition đã tạo
        """
        now = datetime.now(timezone.utc)
        attr.updated_at = now
        self.attributes[attr.attribute_id] = attr
        return attr

    def set_attribute_value(
        self,
        product_id: str,
        attribute_id: str,
        value: Any,
        variant_id: str | None = None,
    ) -> AttributeValue:
        """Đặt hoặc cập nhật giá trị thuộc tính cho sản phẩm hoặc biến thể.

        Tự động tạo attribute_value_id mới và thêm vào bộ sưu tập.
        Nếu đã có giá trị cùng product_id + attribute_id (hoặc variant_id),
        sẽ ghi đè lên giá trị cũ.

        Args:
            product_id: ID sản phẩm cần gán thuộc tính
            attribute_id: ID thuộc tính định nghĩa
            value: Giá trị cần gán
            variant_id: ID biến thể (None = gán ở cấp product)

        Returns:
            AttributeValue đã tạo hoặc cập nhật

        Raises:
            MidicoderError: Nếu product_id không tồn tại (MDC-CP50-001)
            MidicoderError: Nếu attribute_id không tồn tại (MDC-CP50-004)
        """
        # Kiểm tra product_id tồn tại
        if product_id not in self.products:
            EM.raise_error(
                ErrorCode.CP50_PRODUCT_NOT_FOUND,
                product_id=product_id,
            )

        # Kiểm tra attribute_id tồn tại
        if attribute_id not in self.attributes:
            EM.raise_error(
                ErrorCode.CP50_ATTRIBUTE_NOT_FOUND,
                attribute_id=attribute_id,
            )

        # Tìm và ghi đè giá trị cũ nếu có
        for existing in self.attribute_values:
            if (existing.attribute_id == attribute_id
                    and existing.product_id == product_id
                    and existing.variant_id == (variant_id or "")):
                existing.value = value
                return existing

        # Tạo mới
        self._attr_value_counter += 1
        av_id = f"attr_val_{self._attr_value_counter}_{attribute_id}_{product_id}"

        attr_value = AttributeValue(
            attribute_value_id=av_id,
            attribute_id=attribute_id,
            product_id=product_id,
            variant_id=variant_id or "",
            value=value,
        )

        self.attribute_values.append(attr_value)
        return attr_value

    def get_product_attributes(self, product_id: str) -> dict[str, Any]:
        """Lấy tất cả giá trị thuộc tính của một sản phẩm.

        Trả về dict với key là attribute key (từ định nghĩa) và
        value là giá trị thực tế.

        Args:
            product_id: ID sản phẩm cần lấy thuộc tính

        Returns:
            Dict attribute_key → value

        Raises:
            MidicoderError: Nếu product_id không tồn tại (MDC-CP50-001)
        """
        if product_id not in self.products:
            EM.raise_error(
                ErrorCode.CP50_PRODUCT_NOT_FOUND,
                product_id=product_id,
            )

        result: dict[str, Any] = {}
        for av in self.attribute_values:
            if av.product_id == product_id and not av.variant_id:
                attr_def = self.attributes.get(av.attribute_id)
                if attr_def:
                    result[attr_def.key] = av.value
                else:
                    result[av.attribute_id] = av.value

        return result

    # ---------------------------------------------------------------------
    # Faceted Search
    # ---------------------------------------------------------------------

    def search_products(
        self,
        query: str,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Tìm kiếm sản phẩm với bộ lọc và aggregation.

        Tìm kiếm dựa trên query (tìm trong name, description, slug, tags)
        và lọc theo các điều kiện trong filters dict. Trả về kết quả kèm
        aggregations (đếm theo category, brand, status).

        Args:
            query: Chuỗi tìm kiếm (rỗng = lấy tất cả)
            filters: Dict bộ lọc, các khóa hỗ trợ:
                - status: ProductStatus.value
                - category_id: str
                - brand_id: str
                - min_price: float
                - max_price: float
                - visibility: Visibility.value
                - tags: list[str] (phải chứa ít nhất một)

        Returns:
            Dict với:
                - results: list[Product]
                - total: int (số lượng kết quả)
                - aggregations: dict (category_count, brand_count, status_count)
        """
        if not filters:
            filters = {}

        # Lọc ban đầu: loại bỏ sản phẩm đã xóa
        candidates = [p for p in self.products.values() if not p.is_deleted]

        # Áp dụng query: tìm trong name, description, slug, tags
        if query and query.strip():
            query_lower = query.lower().strip()
            filtered: list[Product] = []
            for p in candidates:
                searchable = (
                    p.name + " " + p.description + " " + p.slug
                    + " " + " ".join(p.tags)
                ).lower()
                if query_lower in searchable:
                    filtered.append(p)
            candidates = filtered

        # Áp dụng filters
        if "status" in filters:
            status_filter = ProductStatus(filters["status"])
            candidates = [p for p in candidates if p.status == status_filter]

        if "category_id" in filters:
            cat_id = filters["category_id"]
            candidates = [p for p in candidates if p.category_id == cat_id]

        if "brand_id" in filters:
            brand_id = filters["brand_id"]
            candidates = [p for p in candidates if p.brand_id == brand_id]

        if "min_price" in filters:
            min_price = filters["min_price"]
            candidates = [p for p in candidates if p.price >= min_price]

        if "max_price" in filters:
            max_price = filters["max_price"]
            candidates = [p for p in candidates if p.price <= max_price]

        if "visibility" in filters:
            vis_filter = Visibility(filters["visibility"])
            candidates = [p for p in candidates if p.visibility == vis_filter]

        if "tags" in filters:
            tag_filter = set(filters["tags"])
            candidates = [
                p for p in candidates
                if tag_filter & set(p.tags)
            ]

        # Tính aggregations
        category_count: dict[str, int] = {}
        brand_count: dict[str, int] = {}
        status_count: dict[str, int] = {}

        for p in candidates:
            # Theo category
            cat_key = p.category_id or "uncategorized"
            category_count[cat_key] = category_count.get(cat_key, 0) + 1

            # Theo brand
            brand_key = p.brand_id or "unbranded"
            brand_count[brand_key] = brand_count.get(brand_key, 0) + 1

            # Theo status
            status_count[p.status.value] = status_count.get(p.status.value, 0) + 1

        return {
            "results": candidates,
            "total": len(candidates),
            "aggregations": {
                "category_count": category_count,
                "brand_count": brand_count,
                "status_count": status_count,
            },
        }


# ===========================================================================
# Exports
# ===========================================================================

__all__ = [
    # Enums
    "ProductStatus",
    "AttributeType",
    "SortOrder",
    "Visibility",
    "CategoryLevel",
    # Dataclasses
    "Product",
    "Category",
    "ProductVariant",
    "AttributeDefinition",
    "AttributeValue",
    # Engine
    "CatalogEngine",
    # Helper
    "_slugify",
]
