"""
Tests cho E00-T01: Chốt taxonomy CP/DP/RX.

Viết theo TDD, bám sát SoT:
- 30 Core Packs (CP01-CP30) across P0-P4
- 26 Domain Packs (DP01-DP26)
- 12 Regulatory Overlays (RX01-RX12)
- P0 mandatory: CP01, CP02, CP03, CP04, CP07

Không dùng mock, test với real data từ industry/taxonomy.yml.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from pathlib import Path

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
def taxonomy(taxonomy_path: Path) -> dict:
    """Load taxonomy.yml."""
    with open(taxonomy_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ============================================================================
# Test Core Packs (CP)
# ============================================================================


class TestCorePacks:
    """Tests cho Core Packs theo SoT."""

    def test_core_packs_total_count(self, taxonomy: dict) -> None:
        """Kiểm tra tổng số Core Packs là 30."""
        core_packs = taxonomy["core_packs"]
        assert len(core_packs) == 30, "Phải có đúng 30 Core Packs"

    def test_core_packs_ids(self, taxonomy: dict) -> None:
        """Kiểm tra tất cả CP IDs từ CP01 đến CP30 tồn tại."""
        core_packs = taxonomy["core_packs"]
        cp_ids = {cp["id"] for cp in core_packs}

        # Kiểm tra tất cả CP IDs từ CP01 đến CP30 đều tồn tại
        expected_ids = {f"CP{i:02d}" for i in range(1, 31)}
        assert cp_ids == expected_ids, f"CP IDs phải bao gồm CP01-CP30. Thiếu: {expected_ids - cp_ids}"

    def test_p0_mandatory_packs(self, taxonomy: dict) -> None:
        """Kiểm tra P0 mandatory packs theo SoT: CP01, CP02, CP03, CP04, CP07."""
        core_packs = taxonomy["core_packs"]
        p0_packs = [cp for cp in core_packs if cp["phase"] == "P0"]

        # Kiểm tra count
        assert len(p0_packs) == 5, "Phải có đúng 5 P0 packs"

        # Kiểm tra IDs bắt buộc theo SoT
        p0_ids = {cp["id"] for cp in p0_packs}
        expected_p0 = {"CP01", "CP02", "CP03", "CP04", "CP07"}
        assert p0_ids == expected_p0, f"P0 packs phải là {expected_p0}"

    def test_p1_packs_count(self, taxonomy: dict) -> None:
        """Kiểm tra số lượng P1 packs."""
        core_packs = taxonomy["core_packs"]
        p1_packs = [cp for cp in core_packs if cp["phase"] == "P1"]

        # Theo taxonomy.yml: CP05, CP06, CP08, CP09, CP10, CP11, CP12, CP13, CP14, CP15, CP23
        assert len(p1_packs) == 11, f"Phải có 11 P1 packs. Hiện có: {[p['id'] for p in p1_packs]}"

    def test_p2_packs_count(self, taxonomy: dict) -> None:
        """Kiểm tra số lượng P2 packs."""
        core_packs = taxonomy["core_packs"]
        p2_packs = [cp for cp in core_packs if cp["phase"] == "P2"]

        assert len(p2_packs) == 7, "Phải có 7 P2 packs"

    def test_p3_packs_count(self, taxonomy: dict) -> None:
        """Kiểm tra số lượng P3 packs."""
        core_packs = taxonomy["core_packs"]
        p3_packs = [cp for cp in core_packs if cp["phase"] == "P3"]

        assert len(p3_packs) == 3, "Phải có 3 P3 packs"

    def test_p4_packs_count(self, taxonomy: dict) -> None:
        """Kiểm tra số lượng P4 packs."""
        core_packs = taxonomy["core_packs"]
        p4_packs = [cp for cp in core_packs if cp["phase"] == "P4"]

        assert len(p4_packs) == 4, "Phải có 4 P4 packs"

    def test_cp01_domain_model(self, taxonomy: dict) -> None:
        """Kiểm tra CP01 là Domain Model DSL & IR Builder."""
        core_packs = taxonomy["core_packs"]
        cp01 = next((cp for cp in core_packs if cp["id"] == "CP01"), None)

        assert cp01 is not None, "CP01 phải tồn tại"
        assert "Domain Model" in cp01["name"], "CP01 phải là Domain Model"
        assert cp01["phase"] == "P0", "CP01 phải là P0"
        assert cp01["dependencies"] == [], "CP01 không có dependencies"

    def test_cp02_multi_tenant(self, taxonomy: dict) -> None:
        """Kiểm tra CP02 là Multi-Tenant Architecture."""
        core_packs = taxonomy["core_packs"]
        cp02 = next((cp for cp in core_packs if cp["id"] == "CP02"), None)

        assert cp02 is not None, "CP02 phải tồn tại"
        assert "Multi-Tenant" in cp02["name"], "CP02 phải là Multi-Tenant"
        assert cp02["phase"] == "P0", "CP02 phải là P0"
        assert "CP01" in cp02["dependencies"], "CP02 phụ thuộc CP01"

    def test_cp03_auth(self, taxonomy: dict) -> None:
        """Kiểm tra CP03 là Authentication & Authorization."""
        core_packs = taxonomy["core_packs"]
        cp03 = next((cp for cp in core_packs if cp["id"] == "CP03"), None)

        assert cp03 is not None, "CP03 phải tồn tại"
        assert "Authentication" in cp03["name"], "CP03 phải là Authentication"
        assert cp03["phase"] == "P0", "CP03 phải là P0"

    def test_cp04_rbac(self, taxonomy: dict) -> None:
        """Kiểm tra CP04 là RBAC & Policy Engine."""
        core_packs = taxonomy["core_packs"]
        cp04 = next((cp for cp in core_packs if cp["id"] == "CP04"), None)

        assert cp04 is not None, "CP04 phải tồn tại"
        assert "RBAC" in cp04["name"], "CP04 phải là RBAC"
        assert cp04["phase"] == "P0", "CP04 phải là P0"

    def test_cp07_iac(self, taxonomy: dict) -> None:
        """Kiểm tra CP07 là Infrastructure as Code."""
        core_packs = taxonomy["core_packs"]
        cp07 = next((cp for cp in core_packs if cp["id"] == "CP07"), None)

        assert cp07 is not None, "CP07 phải tồn tại"
        assert "Infrastructure" in cp07["name"], "CP07 phải là Infrastructure"
        assert cp07["phase"] == "P0", "CP07 phải là P0"

    def test_core_pack_required_fields(self, taxonomy: dict) -> None:
        """Kiểm tra tất cả Core Packs có required fields."""
        core_packs = taxonomy["core_packs"]
        required_fields = ["id", "name", "phase", "description", "dependencies"]

        for cp in core_packs:
            for field in required_fields:
                assert field in cp, f"Core Pack {cp['id']} thiếu field '{field}'"


# ============================================================================
# Test Domain Packs (DP)
# ============================================================================


class TestDomainPacks:
    """Tests cho Domain Packs theo SoT."""

    def test_domain_packs_total_count(self, taxonomy: dict) -> None:
        """Kiểm tra tổng số Domain Packs là 26."""
        domain_packs = taxonomy["domain_packs"]
        assert len(domain_packs) == 26, "Phải có đúng 26 Domain Packs"

    def test_domain_packs_ids(self, taxonomy: dict) -> None:
        """Kiểm tra tất cả DP IDs từ DP01 đến DP26."""
        domain_packs = taxonomy["domain_packs"]
        dp_ids = [dp["id"] for dp in domain_packs]

        expected_ids = [f"DP{i:02d}" for i in range(1, 27)]
        assert dp_ids == expected_ids, "DP IDs phải từ DP01 đến DP26"

    def test_dp01_commerce_core(self, taxonomy: dict) -> None:
        """Kiểm tra DP01 là Commerce Core."""
        domain_packs = taxonomy["domain_packs"]
        dp01 = next((dp for dp in domain_packs if dp["id"] == "DP01"), None)

        assert dp01 is not None, "DP01 phải tồn tại"
        assert "Commerce" in dp01["name"], "DP01 phải là Commerce"

    def test_dp11_banking_core(self, taxonomy: dict) -> None:
        """Kiểm tra DP11 là Banking Core."""
        domain_packs = taxonomy["domain_packs"]
        dp11 = next((dp for dp in domain_packs if dp["id"] == "DP11"), None)

        assert dp11 is not None, "DP11 phải tồn tại"
        assert "Banking" in dp11["name"], "DP11 phải là Banking"

    def test_dp16_exchange_trading(self, taxonomy: dict) -> None:
        """Kiểm tra DP16 là Exchange Trading."""
        domain_packs = taxonomy["domain_packs"]
        dp16 = next((dp for dp in domain_packs if dp["id"] == "DP16"), None)

        assert dp16 is not None, "DP16 phải tồn tại"
        assert "Exchange" in dp16["name"], "DP16 phải là Exchange"

    def test_domain_pack_required_fields(self, taxonomy: dict) -> None:
        """Kiểm tra tất cả Domain Packs có required fields."""
        domain_packs = taxonomy["domain_packs"]
        required_fields = ["id", "name", "category"]

        for dp in domain_packs:
            for field in required_fields:
                assert field in dp, f"Domain Pack {dp['id']} thiếu field '{field}'"


# ============================================================================
# Test Regulatory Overlays (RX)
# ============================================================================


class TestRegulatoryOverlays:
    """Tests cho Regulatory Overlays theo SoT."""

    def test_regulatory_overlays_total_count(self, taxonomy: dict) -> None:
        """Kiểm tra tổng số Regulatory Overlays là 12."""
        regulatory_overlays = taxonomy["regulatory_overlays"]
        assert len(regulatory_overlays) == 12, "Phải có đúng 12 Regulatory Overlays"

    def test_regulatory_overlays_ids(self, taxonomy: dict) -> None:
        """Kiểm tra tất cả RX IDs từ RX01 đến RX12."""
        regulatory_overlays = taxonomy["regulatory_overlays"]
        rx_ids = [rx["id"] for rx in regulatory_overlays]

        expected_ids = [f"RX{i:02d}" for i in range(1, 13)]
        assert rx_ids == expected_ids, "RX IDs phải từ RX01 đến RX12"

    def test_rx01_privacy_pii(self, taxonomy: dict) -> None:
        """Kiểm tra RX01 là Privacy & PII Protection (universal)."""
        regulatory_overlays = taxonomy["regulatory_overlays"]
        rx01 = next((rx for rx in regulatory_overlays if rx["id"] == "RX01"), None)

        assert rx01 is not None, "RX01 phải tồn tại"
        assert "Privacy" in rx01["name"], "RX01 phải là Privacy"
        # Universal được thể hiện qua industries_requiring: ["all"]
        assert "all" in rx01.get("industries_requiring", []), "RX01 phải áp dụng cho tất cả industries"

    def test_rx11_audit_evidence(self, taxonomy: dict) -> None:
        """Kiểm tra RX11 là Immutable Audit Evidence (universal)."""
        regulatory_overlays = taxonomy["regulatory_overlays"]
        rx11 = next((rx for rx in regulatory_overlays if rx["id"] == "RX11"), None)

        assert rx11 is not None, "RX11 phải tồn tại"
        assert "Audit" in rx11["name"], "RX11 phải là Audit"
        # Universal được thể hiện qua industries_requiring: ["all"]
        assert "all" in rx11.get("industries_requiring", []), "RX11 phải áp dụng cho tất cả industries"

    def test_universal_overlays(self, taxonomy: dict) -> None:
        """Kiểm tra universal overlays: RX01 và RX11."""
        regulatory_overlays = taxonomy["regulatory_overlays"]
        # Universal được thể hiện qua industries_requiring: ["all"]
        universal_overlays = [
            rx for rx in regulatory_overlays
            if "all" in rx.get("industries_requiring", [])
        ]

        assert len(universal_overlays) == 2, "Phải có đúng 2 universal overlays"
        universal_ids = {rx["id"] for rx in universal_overlays}
        assert universal_ids == {"RX01", "RX11"}, "Universal overlays phải là RX01 và RX11"

    def test_regulatory_overlay_required_fields(self, taxonomy: dict) -> None:
        """Kiểm tra tất cả Regulatory Overlays có required fields."""
        regulatory_overlays = taxonomy["regulatory_overlays"]
        required_fields = ["id", "name", "description"]

        for rx in regulatory_overlays:
            for field in required_fields:
                assert field in rx, f"Regulatory Overlay {rx['id']} thiếu field '{field}'"


# ============================================================================
# Test Dependencies
# ============================================================================


class TestDependencies:
    """Tests cho dependencies theo SoT."""

    def test_cp01_no_dependencies(self, taxonomy: dict) -> None:
        """Kiểm tra CP01 không có dependencies."""
        core_packs = taxonomy["core_packs"]
        cp01 = next((cp for cp in core_packs if cp["id"] == "CP01"), None)

        assert cp01["dependencies"] == [], "CP01 không nên có dependencies"

    def test_cp02_depends_on_cp01(self, taxonomy: dict) -> None:
        """Kiểm tra CP02 phụ thuộc CP01."""
        core_packs = taxonomy["core_packs"]
        cp02 = next((cp for cp in core_packs if cp["id"] == "CP02"), None)

        assert "CP01" in cp02["dependencies"], "CP02 phải phụ thuộc CP01"

    def test_cp03_depends_on_cp01_cp02(self, taxonomy: dict) -> None:
        """Kiểm tra CP03 phụ thuộc CP01 và CP02."""
        core_packs = taxonomy["core_packs"]
        cp03 = next((cp for cp in core_packs if cp["id"] == "CP03"), None)

        assert "CP01" in cp03["dependencies"], "CP03 phải phụ thuộc CP01"
        assert "CP02" in cp03["dependencies"], "CP03 phải phụ thuộc CP02"

    def test_cp04_depends_on_cp02_cp03(self, taxonomy: dict) -> None:
        """Kiểm tra CP04 phụ thuộc CP02 và CP03."""
        core_packs = taxonomy["core_packs"]
        cp04 = next((cp for cp in core_packs if cp["id"] == "CP04"), None)

        assert "CP02" in cp04["dependencies"], "CP04 phải phụ thuộc CP02"
        assert "CP03" in cp04["dependencies"], "CP04 phải phụ thuộc CP03"

    def test_no_circular_dependencies(self, taxonomy: dict) -> None:
        """Kiểm tra không có circular dependencies trong Core Packs."""
        core_packs = taxonomy["core_packs"]
        cp_map = {cp["id"]: cp["dependencies"] for cp in core_packs}

        # DFS để detect cycles
        def has_cycle(cp_id: str, visited: set, rec_stack: set) -> bool:
            visited.add(cp_id)
            rec_stack.add(cp_id)

            for dep in cp_map.get(cp_id, []):
                if dep not in visited:
                    if has_cycle(dep, visited, rec_stack):
                        return True
                elif dep in rec_stack:
                    return True

            rec_stack.remove(cp_id)
            return False

        visited = set()
        for cp_id in cp_map:
            if cp_id not in visited:
                assert not has_cycle(cp_id, visited, set()), f"Circular dependency detected from {cp_id}"