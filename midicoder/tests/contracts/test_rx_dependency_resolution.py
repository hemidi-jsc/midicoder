"""
Tests cho RX (Regulatory Overlay) Dependency Resolution.

Tuân thủ TDD, kiểm tra:
- Validate RX IDs hợp lệ (RX01-RX12)
- Validate universal overlays (RX01, RX11) cho tất cả blueprints
- Resolve RXs cho một industry cụ thể (industries_requiring)
- Validate obligations được enforce đúng

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
def rx_info_map(taxonomy: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """
    Tạo map từ RX ID → info (category, obligations, industries_requiring).
    
    Ví dụ:
        {
            "RX01": {
                "name": "Privacy & PII Protection",
                "category": "privacy",
                "obligations": ["pii_encryption_required", ...],
                "industries_requiring": ["all"],
                ...
            },
            ...
        }
    """
    rx_map: dict[str, dict[str, Any]] = {}
    for rx in taxonomy.get("regulatory_overlays", []):
        rx_map[rx["id"]] = {
            "name": rx.get("name", ""),
            "category": rx.get("category", ""),
            "obligations": rx.get("obligations", []),
            "industries_requiring": rx.get("industries_requiring", []),
            "description": rx.get("description", ""),
            "status": rx.get("status", "stable")
        }
    return rx_map


@pytest.fixture
def industry_to_rxs_map(rx_info_map: dict[str, dict[str, Any]]) -> dict[str, list[str]]:
    """
    Tạo map từ industry ID → list of RX IDs.
    
    Universal RXs (RX01, RX11) áp dụng cho tất cả industries.
    
    Ví dụ:
        {
            "ecommerce-d2c": ["RX01", "RX06", "RX10", "RX11"],
            "retail-banking": ["RX01", "RX02", "RX03", "RX11"],
            ...
        }
    """
    industry_map: dict[str, list[str]] = {}
    
    for rx_id, info in rx_info_map.items():
        industries_requiring = info.get("industries_requiring", [])
        
        # Universal RXs áp dụng cho tất cả industries
        if "all" in industries_requiring:
            # Thêm vào universal list (xử lý riêng)
            continue
        
        for industry in industries_requiring:
            if industry not in industry_map:
                industry_map[industry] = []
            industry_map[industry].append(rx_id)
    
    # Sort RX IDs cho mỗi industry để deterministic
    for industry in industry_map:
        industry_map[industry].sort()
    
    return industry_map


@pytest.fixture
def universal_rx_ids(rx_info_map: dict[str, dict[str, Any]]) -> set[str]:
    """
    Lấy danh sách universal RX IDs (áp dụng cho tất cả industries).
    
    Theo taxonomy: RX01, RX11
    """
    universal: set[str] = set()
    for rx_id, info in rx_info_map.items():
        if "all" in info.get("industries_requiring", []):
            universal.add(rx_id)
    return universal


# ============================================================================
# Test RX Info Map
# ============================================================================


class TestRXInfoMap:
    """Tests cho RX info map structure."""

    def test_rx01_privacy_exists(self, rx_info_map: dict[str, dict[str, Any]]) -> None:
        """Kiểm tra RX01 Privacy & PII Protection tồn tại."""
        assert "RX01" in rx_info_map, "RX01 phải tồn tại"
        assert rx_info_map["RX01"]["name"] == "Privacy & PII Protection"
        assert rx_info_map["RX01"]["category"] == "privacy"

    def test_rx01_is_universal(self, rx_info_map: dict[str, dict[str, Any]]) -> None:
        """Kiểm tra RX01 là universal overlay."""
        industries = rx_info_map["RX01"]["industries_requiring"]
        assert "all" in industries, "RX01 phải là universal overlay"

    def test_rx01_obligations(self, rx_info_map: dict[str, dict[str, Any]]) -> None:
        """Kiểm tra RX01 obligations."""
        obligations = rx_info_map["RX01"]["obligations"]
        assert "pii_encryption_required" in obligations
        assert "data_retention_policy_required" in obligations
        assert "consent_management_required" in obligations
        assert "right_to_erasure_support" in obligations

    def test_rx11_audit_exists(self, rx_info_map: dict[str, dict[str, Any]]) -> None:
        """Kiểm tra RX11 Immutable Audit Evidence tồn tại."""
        assert "RX11" in rx_info_map, "RX11 phải tồn tại"
        assert rx_info_map["RX11"]["name"] == "Immutable Audit Evidence"
        assert rx_info_map["RX11"]["category"] == "audit"

    def test_rx11_is_universal(self, rx_info_map: dict[str, dict[str, Any]]) -> None:
        """Kiểm tra RX11 là universal overlay."""
        industries = rx_info_map["RX11"]["industries_requiring"]
        assert "all" in industries, "RX11 phải là universal overlay"

    def test_rx_count_is_12(self, rx_info_map: dict[str, dict[str, Any]]) -> None:
        """Kiểm tra tổng số RXs là 12."""
        assert len(rx_info_map) == 12, f"Phải có 12 RXs, tìm thấy {len(rx_info_map)}"


# ============================================================================
# Test Universal RX Requirements
# ============================================================================


class TestUniversalRXRequirements:
    """Tests cho universal RX requirements."""

    def test_universal_rx_ids(self, universal_rx_ids: set[str]) -> None:
        """Kiểm tra universal RX IDs là RX01 và RX11."""
        assert universal_rx_ids == {"RX01", "RX11"}, f"Universal RXs phải là RX01, RX11. Tìm thấy: {universal_rx_ids}"

    def test_universal_count(self, universal_rx_ids: set[str]) -> None:
        """Kiểm tra số lượng universal RXs là 2."""
        assert len(universal_rx_ids) == 2, "Phải có đúng 2 universal RXs"


# ============================================================================
# Test RX Resolution for Industry
# ============================================================================


class TestRXResolutionForIndustry:
    """Tests cho RX resolution dựa vào industry."""

    def test_resolve_rxs_for_ecommerce_d2c(
        self,
        industry_to_rxs_map: dict[str, list[str]],
        universal_rx_ids: set[str],
    ) -> None:
        """
        Resolve RXs cho ecommerce-d2c.
        
        Expected: RX01 (universal), RX06 (Tax), RX10 (Consumer), RX11 (universal)
        """
        industry_rxs = industry_to_rxs_map.get("ecommerce-d2c", [])
        all_rxs = set(industry_rxs) | universal_rx_ids
        
        assert "RX01" in all_rxs, "ecommerce-d2c cần RX01 (universal)"
        assert "RX06" in all_rxs, "ecommerce-d2c cần RX06 (Tax)"
        assert "RX10" in all_rxs, "ecommerce-d2c cần RX10 (Consumer Protection)"
        assert "RX11" in all_rxs, "ecommerce-d2c cần RX11 (universal)"

    def test_resolve_rxs_for_retail_banking(
        self,
        industry_to_rxs_map: dict[str, list[str]],
        universal_rx_ids: set[str],
    ) -> None:
        """
        Resolve RXs cho retail-banking.
        
        Expected: RX01, RX02 (Financial), RX03 (AML), RX11
        """
        industry_rxs = industry_to_rxs_map.get("retail-banking", [])
        all_rxs = set(industry_rxs) | universal_rx_ids
        
        assert "RX01" in all_rxs, "retail-banking cần RX01"
        assert "RX02" in all_rxs, "retail-banking cần RX02 (Financial Integrity)"
        assert "RX03" in all_rxs, "retail-banking cần RX03 (AML)"
        assert "RX11" in all_rxs, "retail-banking cần RX11"

    def test_resolve_rxs_for_hospital_is(
        self,
        industry_to_rxs_map: dict[str, list[str]],
        universal_rx_ids: set[str],
    ) -> None:
        """
        Resolve RXs cho hospital-is.
        
        Expected: RX01, RX04 (HIPAA), RX11
        """
        industry_rxs = industry_to_rxs_map.get("hospital-is", [])
        all_rxs = set(industry_rxs) | universal_rx_ids
        
        assert "RX01" in all_rxs, "hospital-is cần RX01"
        assert "RX04" in all_rxs, "hospital-is cần RX04 (HIPAA)"
        assert "RX11" in all_rxs, "hospital-is cần RX11"

    def test_resolve_rxs_for_food_delivery(
        self,
        industry_to_rxs_map: dict[str, list[str]],
        universal_rx_ids: set[str],
    ) -> None:
        """
        Resolve RXs cho food-delivery.
        
        Expected: RX01, RX09 (Safety), RX10 (Consumer), RX11
        """
        industry_rxs = industry_to_rxs_map.get("food-delivery", [])
        all_rxs = set(industry_rxs) | universal_rx_ids
        
        assert "RX01" in all_rxs, "food-delivery cần RX01"
        assert "RX09" in all_rxs, "food-delivery cần RX09 (Safety)"
        assert "RX10" in all_rxs, "food-delivery cần RX10 (Consumer Protection)"
        assert "RX11" in all_rxs, "food-delivery cần RX11"


# ============================================================================
# Test RX Validation
# ============================================================================


class TestRXValidation:
    """Tests cho RX validation."""

    def test_validate_valid_rx_id(self, rx_info_map: dict[str, dict[str, Any]]) -> None:
        """Kiểm tra valid RX ID."""
        errors = self._validate_rx_id("RX01", rx_info_map)
        assert errors == [], f"RX01 nên valid, tìm thấy: {errors}"

    def test_validate_invalid_rx_id(self, rx_info_map: dict[str, dict[str, Any]]) -> None:
        """Kiểm tra invalid RX ID."""
        errors = self._validate_rx_id("RX99", rx_info_map)
        assert len(errors) > 0, "RX99 nên có error"
        assert "RX99" in errors[0]

    def test_validate_universal_rxs_required(
        self, universal_rx_ids: set[str], rx_info_map: dict[str, dict[str, Any]]
    ) -> None:
        """
        Kiểm tra universal RXs luôn được yêu cầu.
        
        Blueprint không include RX01 → Error
        """
        blueprint_rxs = {"RX02", "RX06"}  # Thiếu RX01, RX11
        errors = self._validate_universal_rxs(blueprint_rxs, universal_rx_ids)
        
        assert "RX01" in str(errors), "RX01 phải được báo là missing"
        assert "RX11" in str(errors), "RX11 phải được báo là missing"

    def test_validate_rxs_for_industry(
        self,
        rx_info_map: dict[str, dict[str, Any]],
        universal_rx_ids: set[str],
    ) -> None:
        """
        Kiểm tra RXs phù hợp với industry.
        
        ecommerce-d2c nên có: RX01, RX06, RX10, RX11
        """
        industry = "ecommerce-d2c"
        blueprint_rxs = {"RX01", "RX06", "RX10", "RX11"}
        
        # Get required RXs cho industry
        required_rxs = self._get_required_rxs_for_industry(
            industry, rx_info_map, universal_rx_ids
        )
        
        # Blueprint nên include tất cả required RXs
        missing = required_rxs - blueprint_rxs
        assert missing == set(), f"Thiếu RXs cho {industry}: {missing}"

    def _validate_rx_id(self, rx_id: str, rx_info_map: dict[str, dict[str, Any]]) -> list[str]:
        """Helper: Validate RX ID tồn tại."""
        errors: list[str] = []
        if rx_id not in rx_info_map:
            errors.append(f"Invalid RX ID: {rx_id}")
        return errors

    def _validate_universal_rxs(
        self, blueprint_rxs: set[str], universal_rx_ids: set[str]
    ) -> list[str]:
        """Helper: Validate universal RXs được include."""
        errors: list[str] = []
        
        for rx_id in universal_rx_ids:
            if rx_id not in blueprint_rxs:
                errors.append(f"Universal RX {rx_id} must be included in all blueprints")
        
        return errors

    def _get_required_rxs_for_industry(
        self,
        industry: str,
        rx_info_map: dict[str, dict[str, Any]],
        universal_rx_ids: set[str],
    ) -> set[str]:
        """Helper: Lấy required RXs cho industry."""
        required: set[str] = set(universal_rx_ids)
        
        for rx_id, info in rx_info_map.items():
            if rx_id in universal_rx_ids:
                continue
            
            industries_requiring = info.get("industries_requiring", [])
            if industry in industries_requiring:
                required.add(rx_id)
        
        return required


# ============================================================================
# Test RX Obligations
# ============================================================================


class TestRXObligations:
    """Tests cho RX obligations."""

    def test_rx02_obligations(self, rx_info_map: dict[str, dict[str, Any]]) -> None:
        """Kiểm tra RX02 Financial Integrity obligations."""
        obligations = rx_info_map["RX02"]["obligations"]
        assert "double_entry_required" in obligations
        assert "transaction_immutability" in obligations
        assert "reconciliation_mandatory" in obligations

    def test_rx04_obligations(self, rx_info_map: dict[str, dict[str, Any]]) -> None:
        """Kiểm tra RX04 HIPAA obligations."""
        obligations = rx_info_map["RX04"]["obligations"]
        assert "hipaa_compliance_required" in obligations
        assert "clinical_audit_trail" in obligations
        assert "phii_encryption_required" in obligations
        assert "minimum_necessary_access" in obligations

    def test_all_rxs_have_obligations(self, rx_info_map: dict[str, dict[str, Any]]) -> None:
        """Kiểm tra tất cả RXs đều có obligations."""
        for rx_id, info in rx_info_map.items():
            assert len(info.get("obligations", [])) > 0, f"{rx_id} phải có ít nhất 1 obligation"


# ============================================================================
# Test RX Category Grouping
# ============================================================================


class TestRXCategoryGrouping:
    """Tests cho RX category grouping."""

    def test_financial_category_rxs(self, rx_info_map: dict[str, dict[str, Any]]) -> None:
        """Kiểm tra financial category RXs."""
        financial_rxs = [
            rx_id for rx_id, info in rx_info_map.items()
            if info["category"] == "financial"
        ]
        assert "RX02" in financial_rxs  # Financial Integrity
        assert "RX03" in financial_rxs  # AML, KYC

    def test_healthcare_category_rx(self, rx_info_map: dict[str, dict[str, Any]]) -> None:
        """Kiểm tra healthcare category RX."""
        healthcare_rxs = [
            rx_id for rx_id, info in rx_info_map.items()
            if info["category"] == "healthcare"
        ]
        assert "RX04" in healthcare_rxs


# ============================================================================
# Test RX Integration with Blueprint
# ============================================================================


class TestRXIntegrationWithBlueprint:
    """Tests cho RX integration với Blueprint."""

    def test_blueprint_rx_ids_valid(self, rx_info_map: dict[str, dict[str, Any]]) -> None:
        """
        Kiểm tra RX IDs trong blueprint đều valid.
        
        Blueprint RXs: ["RX01", "RX06", "RX11"]
        """
        blueprint_rxs = ["RX01", "RX06", "RX11"]
        errors: list[str] = []
        
        for rx_id in blueprint_rxs:
            if rx_id not in rx_info_map:
                errors.append(f"Invalid RX ID: {rx_id}")
        
        assert errors == [], f"All blueprint RX IDs nên valid: {errors}"

    def test_blueprint_must_include_universal_rxs(
        self, universal_rx_ids: set[str]
    ) -> None:
        """
        Kiểm tra blueprint phải include universal RXs.
        
        Blueprint: ["RX02", "RX06"] - thiếu RX01, RX11
        """
        blueprint_rxs = {"RX02", "RX06"}
        missing_universal = universal_rx_ids - blueprint_rxs
        
        assert len(missing_universal) == 2, "Blueprint thiếu 2 universal RXs"
        assert "RX01" in missing_universal
        assert "RX11" in missing_universal

    def test_complete_blueprint_rxs_for_industry(
        self,
        rx_info_map: dict[str, dict[str, Any]],
        universal_rx_ids: set[str],
    ) -> None:
        """
        Kiểm tra complete RX set cho industry.
        
        marketplace-b2c: RX01 (universal), RX10 (Consumer), RX11 (universal)
        Note: marketplace-b2c không có RX06 trong taxonomy.yml
        """
        industry = "marketplace-b2c"
        required_rxs = self._get_required_rxs_for_industry(
            industry, rx_info_map, universal_rx_ids
        )
        
        # Marketplace-b2c cần: RX01, RX10 (Consumer), RX11
        # Theo taxonomy.yml: RX10 industries_requiring bao gồm marketplace-b2c
        expected = {"RX01", "RX10", "RX11"}
        assert required_rxs == expected, f"{industry} cần {expected}, tìm thấy {required_rxs}"

    def _get_required_rxs_for_industry(
        self,
        industry: str,
        rx_info_map: dict[str, dict[str, Any]],
        universal_rx_ids: set[str],
    ) -> set[str]:
        """Helper: Lấy required RXs cho industry."""
        required: set[str] = set(universal_rx_ids)
        
        for rx_id, info in rx_info_map.items():
            if rx_id in universal_rx_ids:
                continue
            
            industries_requiring = info.get("industries_requiring", [])
            if industry in industries_requiring:
                required.add(rx_id)
        
        return required