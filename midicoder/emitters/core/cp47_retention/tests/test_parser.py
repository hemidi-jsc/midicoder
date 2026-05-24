# coding: utf-8
"""
Tests cho CP47 parser — Data Retention & Lifecycle Management.
"""

from __future__ import annotations

import pytest

from midicoder.emitters.core.cp47_retention.parser import (
    RetentionIR,
    parse_policies,
    parse_retention_config,
    parse_to_ir,
)


class TestParsePolicies:
    """Kiểm tra hàm parse_policies."""

    def test_parse_empty(self):
        """Test parse policies khi dict rỗng."""
        policies = parse_policies({})
        assert policies == []

    def test_parse_with_policies_key(self):
        """Test parse policies với key 'policies'."""
        data = {
            "policies": [
                {
                    "policy_id": "p1",
                    "entity_type": "Order",
                    "retention_days": 90,
                    "action": "archive",
                }
            ]
        }
        policies = parse_policies(data)
        assert len(policies) == 1
        assert policies[0]["policy_id"] == "p1"
        assert policies[0]["entity_type"] == "Order"

    def test_parse_with_retention_policies_key(self):
        """Test parse policies với key 'retention_policies'."""
        data = {
            "retention_policies": [
                {
                    "policy_id": "p1",
                    "entity_type": "Session",
                    "retention_days": 30,
                    "action": "purge",
                }
            ]
        }
        policies = parse_policies(data)
        assert len(policies) == 1
        assert policies[0]["action"] == "purge"

    def test_parse_multiple_policies(self):
        """Test parse nhiều policies cùng lúc."""
        data = {
            "policies": [
                {"policy_id": "p1", "entity_type": "Order", "retention_days": 365, "action": "archive"},
                {"policy_id": "p2", "entity_type": "Transaction", "retention_days": 730, "action": "archive_then_purge"},
                {"policy_id": "p3", "entity_type": "Session", "retention_days": 30, "action": "purge"},
            ]
        }
        policies = parse_policies(data)
        assert len(policies) == 3

    def test_parse_policy_defaults(self):
        """Test parse policy sử dụng các giá trị mặc định."""
        data = {"policies": [{"policy_id": "p1", "entity_type": "Record"}]}
        policies = parse_policies(data)
        assert policies[0]["retention_days"] == 365
        assert policies[0]["action"] == "archive"
        assert policies[0]["policy_type"] == "time_based"

    def test_parse_policy_with_id_fallback(self):
        """Test parse policy với key 'id' thay vì 'policy_id'."""
        data = {"policies": [{"id": "p1", "entity": "Order"}]}
        policies = parse_policies(data)
        assert policies[0]["policy_id"] == "p1"
        assert policies[0]["entity_type"] == "Order"


class TestParseRetentionConfig:
    """Kiểm tra hàm parse_retention_config."""

    def test_parse_defaults(self):
        """Test parse config với giá trị mặc định."""
        config = parse_retention_config({})
        assert config["enable_archival"] is True
        assert config["enable_purge"] is False
        assert config["enable_erasure"] is True
        assert config["enable_scheduler"] is True
        assert config["default_retention_days"] == 365
        assert config["batch_size"] == 1000

    def test_parse_custom_values(self):
        """Test parse config với các giá trị tùy chỉnh."""
        data = {
            "enable_archival": False,
            "enable_purge": True,
            "enable_erasure": False,
            "enable_scheduler": False,
            "default_retention_days": 180,
            "retention_config": {
                "batch_size": 500,
            },
        }
        config = parse_retention_config(data)
        assert config["enable_archival"] is False
        assert config["enable_purge"] is True
        assert config["enable_erasure"] is False
        assert config["enable_scheduler"] is False
        assert config["default_retention_days"] == 180
        assert config["batch_size"] == 500

    def test_parse_nested_config(self):
        """Test parse config từ nested retention_config."""
        data = {
            "retention_config": {
                "enable_purge": True,
                "batch_size": 2000,
            }
        }
        config = parse_retention_config(data)
        assert config["enable_purge"] is True
        assert config["batch_size"] == 2000

    def test_parse_config_key_fallback(self):
        """Test parse config từ nested config key."""
        data = {
            "config": {
                "enable_archival": False,
                "default_retention_days": 60,
            }
        }
        config = parse_retention_config(data)
        assert config["enable_archival"] is False
        assert config["default_retention_days"] == 60


class TestParseToIR:
    """Kiểm tra hàm parse_to_ir."""

    def test_parse_empty(self):
        """Test parse_to_ir với dict rỗng."""
        ir = parse_to_ir({})
        assert ir.policies == []
        assert ir.enable_archival is True
        assert ir.enable_purge is False
        assert ir.enable_erasure is True
        assert ir.enable_scheduler is True
        assert ir.default_retention_days == 365
        assert ir.batch_size == 1000

    def test_parse_full(self):
        """Test parse_to_ir với dữ liệu đầy đủ."""
        data = {
            "policies": [
                {"policy_id": "p1", "entity_type": "Order", "retention_days": 365, "action": "archive"},
                {"policy_id": "p2", "entity_type": "Transaction", "retention_days": 730, "action": "purge"},
            ],
            "enable_archival": True,
            "enable_purge": True,
            "enable_erasure": True,
            "enable_scheduler": True,
            "default_retention_days": 365,
            "retention_config": {
                "batch_size": 500,
            },
        }
        ir = parse_to_ir(data)
        assert len(ir.policies) == 2
        assert ir.enable_archival is True
        assert ir.enable_purge is True
        assert ir.enable_erasure is True
        assert ir.enable_scheduler is True
        assert ir.default_retention_days == 365
        assert ir.batch_size == 500


class TestRetentionIR:
    """Kiểm tra class RetentionIR."""

    def test_create_default(self):
        """Test tạo RetentionIR với giá trị mặc định."""
        ir = RetentionIR()
        assert ir.policies == []
        assert ir.enable_archival is True
        assert ir.enable_purge is False
        assert ir.enable_erasure is True
        assert ir.enable_scheduler is True
        assert ir.default_retention_days == 365
        assert ir.batch_size == 1000

    def test_to_dict(self):
        """Test chuyển RetentionIR sang dict."""
        ir = RetentionIR(
            enable_archival=False,
            enable_purge=True,
            enable_erasure=False,
            enable_scheduler=False,
            default_retention_days=180,
            batch_size=500,
        )
        d = ir.to_dict()
        assert d["enable_archival"] is False
        assert d["enable_purge"] is True
        assert d["enable_erasure"] is False
        assert d["enable_scheduler"] is False
        assert d["default_retention_days"] == 180
        assert d["batch_size"] == 500

    def test_from_dict(self):
        """Test tạo RetentionIR từ dict."""
        data = {
            "policies": [{"policy_id": "p1", "entity_type": "Order", "retention_days": 90, "action": "archive"}],
            "enable_archival": True,
            "enable_purge": True,
            "enable_erasure": False,
            "enable_scheduler": True,
            "default_retention_days": 90,
            "batch_size": 2000,
        }
        ir = RetentionIR.from_dict(data)
        assert len(ir.policies) == 1
        assert ir.enable_archival is True
        assert ir.enable_purge is True
        assert ir.enable_erasure is False
        assert ir.enable_scheduler is True
        assert ir.default_retention_days == 90
        assert ir.batch_size == 2000

    def test_roundtrip(self):
        """Test serialization và deserialization (to_dict -> from_dict)."""
        ir = RetentionIR(
            policies=[{"policy_id": "p1", "entity_type": "Order", "retention_days": 90, "action": "archive"}],
            enable_archival=True,
            enable_purge=True,
            enable_erasure=False,
            enable_scheduler=True,
            default_retention_days=90,
            batch_size=500,
        )
        restored = RetentionIR.from_dict(ir.to_dict())
        assert restored.policies == ir.policies
        assert restored.enable_archival == ir.enable_archival
        assert restored.enable_purge == ir.enable_purge
        assert restored.enable_erasure == ir.enable_erasure
        assert restored.enable_scheduler == ir.enable_scheduler
        assert restored.default_retention_days == ir.default_retention_days
        assert restored.batch_size == ir.batch_size

    def test_from_dict_with_partial_data(self):
        """Test tạo RetentionIR từ dict không đầy đủ."""
        data = {"enable_purge": True, "batch_size": 200}
        ir = RetentionIR.from_dict(data)
        assert ir.policies == []
        assert ir.enable_archival is True  # mặc định
        assert ir.enable_purge is True
        assert ir.enable_erasure is True  # mặc định
        assert ir.enable_scheduler is True  # mặc định
        assert ir.default_retention_days == 365  # mặc định
        assert ir.batch_size == 200
