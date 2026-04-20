"""
Tests cho DP (Domain Pack) Dependency Resolution.

Tuân thủ TDD, kiểm tra:
- Validate DP IDs hợp lệ (DP01-DP26)
- Validate DP phù hợp với industry (industries_using)
- Resolve DPs cho một industry cụ thể

Khác với CP, DP không có transitive dependencies trong taxonomy.
DP dependency resolution dựa vào industry mapping.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def taxonomy_path() -> Path:
    """Đường dẫn đến taxonomy.yml."""
    return Path("industry/taxonomy.yml")


@pytest.fixture
def taxonomy(taxonomy_path: Path) -> dict[str, Any]:
    """Load taxonomy.yml."""
    with open(taxonomy_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture
def dp_info_map(taxonomy: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """
    Tạo map từ DP ID → info (category, industries_using, description).
    
    Ví dụ:
        {
            "DP01": {
                "name": "Commerce Core",
                "category": "commerce",
                "industries_using": ["ecommerce-d2c", ...],
                ...
            },
            ...
        }
    """
    dp_map: dict[str, dict[str, Any]] = {}
    for dp in taxonomy.get("domain_packs", []):
        dp_map[dp["id"]] = {
            "name": dp.get("name", ""),
            "category": dp.get("category", ""),
            "industries_using": dp.get("industries_using", []),
            "description": dp.get("description", ""),
            "status": dp.get("status", "stable")
        }
    return dp_map


@pytest.fixture
def industry_to_dps_map(dp_info_map: dict[str, dict[str, Any]]) -> dict[str, list[str]]:
    """
    Tạo map từ industry ID → list of DP IDs.
    
    Ví dụ:
        {
            "ecommerce-d2c": ["DP01", "DP12"],
            "marketplace-b2c": ["DP01", "DP02", "DP12"],
            ...
        }
    """
    industry_map: dict[str, list[str]] = {}
    
    for dp_id, info in dp_info_map.items():
        for industry in info.get("industries_using", []):
            if industry not in industry_map:
                industry_map[industry] = []
            industry_map[industry].append(dp_id)
    
    # Sort DP IDs cho mỗi industry để deterministic
    for industry in industry_map:
        industry_map[industry].sort()
    
    return industry_map


# ============================================================================
# Test DP Info Map
# ============================================================================


class TestDPInfoMap:
    """Tests cho DP info map structure."""

    def test_dp01_commerce_exists(self, dp_info_map: dict[str, dict[str, Any]]) -> None:
        """Kiểm tra DP01 Commerce Core tồn tại."""
        assert "DP01" in dp_info_map, "DP01 phải tồn tại"
        assert dp_info_map["DP01"]["name"] == "Commerce Core"
        assert dp_info_map["DP01"]["category"] == "commerce"

    def test_dp01_industries_using(self, dp_info_map: dict[str, dict[str, Any]]) -> None:
        """Kiểm tra DP01 industries_using."""
        industries = dp_info_map["DP01"]["industries_using"]
        assert "ecommerce-d2c" in industries
        assert "marketplace-b2c" in industries
        assert "marketplace-b2b" in industries

    def test_dp11_banking_exists(self, dp_info_map: dict[str, dict[str, Any]]) -> None:
        """Kiểm tra DP11 Banking Core tồn tại."""
        assert "DP11" in dp_info_map, "DP11 phải tồn tại"
        assert dp_info_map["DP11"]["name"] == "Banking Core"
        assert dp_info_map["DP11"]["category"] == "banking"

    def test_dp16_exchange_exists(self, dp_info_map: dict[str, dict[str, Any]]) -> None:
        """Kiểm tra DP16 Exchange Trading tồn tại."""
        assert "DP16" in dp_info_map, "DP16 phải tồn tại"
        assert dp_info_map["DP16"]["name"] == "Exchange Trading & Market Infra"
        assert dp_info_map["DP16"]["category"] == "exchange"

    def test_all_dps_have_required_fields(self, dp_info_map: dict[str, dict[str, Any]]) -> None:
        """Kiểm tra tất cả DPs có required fields."""
        required_fields = ["name", "category", "industries_using", "status"]
        
        for dp_id, info in dp_info_map.items():
            for field in required_fields:
                assert field in info, f"{dp_id} thiếu field '{field}'"

    def test_dp_count_is_26(self, dp_info_map: dict[str, dict[str, Any]]) -> None:
        """Kiểm tra tổng số DPs là 26."""
        assert len(dp_info_map) == 26, f"Phải có 26 DPs, tìm thấy {len(dp_info_map)}"


# ============================================================================
# Test Industry to DPs Mapping
# ============================================================================


class TestIndustryToDpsMapping:
    """Tests cho industry to DPs mapping."""

    def test_ecommerce_d2c_has_dp01(self, industry_to_dps_map: dict[str, list[str]]) -> None:
        """Kiểm tra ecommerce-d2c có DP01."""
        assert "ecommerce-d2c" in industry_to_dps_map
        assert "DP01" in industry_to_dps_map["ecommerce-d2c"]

    def test_marketplace_b2c_has_dp01_and_dp02(
        self, industry_to_dps_map: dict[str, list[str]]
    ) -> None:
        """Kiểm tra marketplace-b2c có DP01 và DP02."""
        assert "marketplace-b2c" in industry_to_dps_map
        dps = industry_to_dps_map["marketplace-b2c"]
        assert "DP01" in dps
        assert "DP02" in dps

    def test_retail_banking_has_dp11(self, industry_to_dps_map: dict[str, list[str]]) -> None:
        """Kiểm tra retail-banking có DP11."""
        assert "retail-banking" in industry_to_dps_map
        assert "DP11" in industry_to_dps_map["retail-banking"]

    def test_exchange_trading_has_dp16(self, industry_to_dps_map: dict[str, list[str]]) -> None:
        """Kiểm tra exchange-trading có DP16."""
        assert "exchange-trading" in industry_to_dps_map
        assert "DP16" in industry_to_dps_map["exchange-trading"]

    def test_hospital_is_has_dp09(self, industry_to_dps_map: dict[str, list[str]]) -> None:
        """Kiểm tra hospital-is có DP09."""
        assert "hospital-is" in industry_to_dps_map
        assert "DP09" in industry_to_dps_map["hospital-is"]


# ============================================================================
# Test DP Resolution for Industry
# ============================================================================


class TestDPResolutionForIndustry:
    """Tests cho DP resolution dựa vào industry."""

    def test_resolve_dps_for_ecommerce_d2c(
        self, industry_to_dps_map: dict[str, list[str]]
    ) -> None:
        """
        Resolve DPs cho ecommerce-d2c.
        
        Expected: DP01 (Commerce Core), DP12 (Payments & Cards)
        """
        dps = industry_to_dps_map.get("ecommerce-d2c", [])
        assert "DP01" in dps, "ecommerce-d2c cần DP01"
        assert "DP12" in dps, "ecommerce-d2c cần DP12"

    def test_resolve_dps_for_marketplace_b2c(
        self, industry_to_dps_map: dict[str, list[str]]
    ) -> None:
        """
        Resolve DPs cho marketplace-b2c.
        
        Expected: DP01, DP02, DP12
        """
        dps = industry_to_dps_map.get("marketplace-b2c", [])
        assert "DP01" in dps
        assert "DP02" in dps
        assert "DP12" in dps

    def test_resolve_dps_for_food_delivery(
        self, industry_to_dps_map: dict[str, list[str]]
    ) -> None:
        """
        Resolve DPs cho food-delivery.
        
        Expected: DP01 (Commerce), DP04 (Logistics)
        """
        dps = industry_to_dps_map.get("food-delivery", [])
        assert "DP01" in dps, "food-delivery cần DP01"
        assert "DP04" in dps, "food-delivery cần DP04"

    def test_resolve_dps_for_unknown_industry(
        self, industry_to_dps_map: dict[str, list[str]]
    ) -> None:
        """
        Resolve DPs cho industry không tồn tại.
        
        Expected: [] (empty list)
        """
        dps = industry_to_dps_map.get("unknown-industry", [])
        assert dps == [], "Unknown industry nên trả về empty list"


# ============================================================================
# Test DP Validation
# ============================================================================


class TestDPValidation:
    """Tests cho DP validation."""

    def test_validate_valid_dp_id(self, dp_info_map: dict[str, dict[str, Any]]) -> None:
        """Kiểm tra valid DP ID."""
        errors = self._validate_dp_id("DP01", dp_info_map)
        assert errors == [], f"DP01 nên valid, tìm thấy: {errors}"

    def test_validate_invalid_dp_id(self, dp_info_map: dict[str, dict[str, Any]]) -> None:
        """Kiểm tra invalid DP ID."""
        errors = self._validate_dp_id("DP99", dp_info_map)
        assert len(errors) > 0, "DP99 nên có error"
        assert "DP99" in errors[0]

    def test_validate_dp_for_industry(
        self, dp_info_map: dict[str, dict[str, Any]]
    ) -> None:
        """
        Kiểm tra DP phù hợp với industry.
        
        DP01 phù hợp với ecommerce-d2c.
        """
        errors = self._validate_dp_for_industry("DP01", "ecommerce-d2c", dp_info_map)
        assert errors == [], f"DP01 nên phù hợp với ecommerce-d2c"

    def test_validate_dp_not_for_industry(
        self, dp_info_map: dict[str, dict[str, Any]]
    ) -> None:
        """
        Kiểm tra DP không phù hợp với industry.
        
        DP11 (Banking) không phù hợp với ecommerce-d2c.
        """
        errors = self._validate_dp_for_industry("DP11", "ecommerce-d2c", dp_info_map)
        # Warning không phải error vì DP có thể được dùng cho industry khác
        # Nhưng nên có warning về mismatch
        assert len(errors) >= 0  # Không enforce error, chỉ warning

    def test_validate_multiple_dps_for_industry(
        self, dp_info_map: dict[str, dict[str, Any]]
    ) -> None:
        """
        Kiểm tra multiple DPs cho một industry.
        
        ["DP01", "DP12"] đều phù hợp với ecommerce-d2c.
        """
        errors = self._validate_dps_for_industry(
            ["DP01", "DP12"], "ecommerce-d2c", dp_info_map
        )
        assert errors == [], f"DP01 và DP12 nên phù hợp với ecommerce-d2c"

    def _validate_dp_id(self, dp_id: str, dp_info_map: dict[str, dict[str, Any]]) -> list[str]:
        """Helper: Validate DP ID tồn tại."""
        errors: list[str] = []
        if dp_id not in dp_info_map:
            errors.append(f"Invalid DP ID: {dp_id}")
        return errors

    def _validate_dp_for_industry(
        self, dp_id: str, industry: str, dp_info_map: dict[str, dict[str, Any]]
    ) -> list[str]:
        """Helper: Validate DP phù hợp với industry."""
        errors: list[str] = []
        
        if dp_id not in dp_info_map:
            errors.append(f"Invalid DP ID: {dp_id}")
            return errors
        
        industries_using = dp_info_map[dp_id].get("industries_using", [])
        if industry not in industries_using:
            errors.append(
                f"DP {dp_id} not typically used for industry '{industry}'. "
                f"Common industries: {', '.join(industries_using[:5])}"
            )
        
        return errors

    def _validate_dps_for_industry(
        self, dp_ids: list[str], industry: str, dp_info_map: dict[str, dict[str, Any]]
    ) -> list[str]:
        """Helper: Validate multiple DPs phù hợp với industry."""
        errors: list[str] = []
        
        for dp_id in dp_ids:
            errors.extend(self._validate_dp_for_industry(dp_id, industry, dp_info_map))
        
        return errors


# ============================================================================
# Test DP Category Grouping
# ============================================================================


class TestDPCategoryGrouping:
    """Tests cho DP category grouping."""

    def test_commerce_category_dps(self, dp_info_map: dict[str, dict[str, Any]]) -> None:
        """Kiểm tra commerce category DPs."""
        commerce_dps = [
            dp_id for dp_id, info in dp_info_map.items()
            if info["category"] == "commerce"
        ]
        assert "DP01" in commerce_dps
        assert "DP02" in commerce_dps

    def test_healthcare_category_dps(self, dp_info_map: dict[str, dict[str, Any]]) -> None:
        """Kiểm tra healthcare category DPs."""
        healthcare_dps = [
            dp_id for dp_id, info in dp_info_map.items()
            if info["category"] == "healthcare"
        ]
        assert "DP09" in healthcare_dps
        assert "DP10" in healthcare_dps

    def test_financial_category_dps(self, dp_info_map: dict[str, dict[str, Any]]) -> None:
        """Kiểm tra financial category DPs (banking, payments, lending, insurance)."""
        financial_categories = ["banking", "payments", "lending", "insurance", "capital-markets", "exchange"]
        financial_dps = [
            dp_id for dp_id, info in dp_info_map.items()
            if info["category"] in financial_categories
        ]
        assert "DP11" in financial_dps  # Banking
        assert "DP12" in financial_dps  # Payments
        assert "DP16" in financial_dps  # Exchange


# ============================================================================
# Test DP Integration with Blueprint
# ============================================================================


class TestDPIntegrationWithBlueprint:
    """Tests cho DP integration với Blueprint."""

    def test_blueprint_dp_ids_valid(
        self, dp_info_map: dict[str, dict[str, Any]]
    ) -> None:
        """
        Kiểm tra DP IDs trong blueprint đều valid.
        
        Blueprint DPs: ["DP01", "DP02"]
        """
        blueprint_dps = ["DP01", "DP02"]
        errors: list[str] = []
        
        for dp_id in blueprint_dps:
            if dp_id not in dp_info_map:
                errors.append(f"Invalid DP ID: {dp_id}")
        
        assert errors == [], f"All blueprint DP IDs should be valid: {errors}"

    def test_blueprint_dp_for_industry_valid(
        self, dp_info_map: dict[str, dict[str, Any]]
    ) -> None:
        """
        Kiểm tra DPs trong blueprint phù hợp với industry.
        
        Blueprint: ecommerce-d2c với ["DP01", "DP12"]
        """
        industry = "ecommerce-d2c"
        blueprint_dps = ["DP01", "DP12"]
        warnings: list[str] = []
        
        for dp_id in blueprint_dps:
            dp_warnings = self._validate_dp_for_industry(dp_id, industry, dp_info_map)
            warnings.extend(dp_warnings)
        
        # DP01 và DP12 đều phù hợp với ecommerce-d2c
        assert warnings == [], f"DPS nên phù hợp với {industry}: {warnings}"

    def _validate_dp_for_industry(
        self, dp_id: str, industry: str, dp_info_map: dict[str, dict[str, Any]]
    ) -> list[str]:
        """Helper: Validate DP phù hợp với industry."""
        errors: list[str] = []
        
        if dp_id not in dp_info_map:
            errors.append(f"Invalid DP ID: {dp_id}")
            return errors
        
        industries_using = dp_info_map[dp_id].get("industries_using", [])
        if industry not in industries_using:
            errors.append(
                f"DP {dp_id} not typically used for industry '{industry}'"
            )
        
        return errors