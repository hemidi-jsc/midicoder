"""
Unit Tests cho Stream Connection Core Capability.

Task: E11-001 - Add stream_connection core capability
Priority: P0 - Required by Food Delivery, Exchange Trading, Telehealth

Kiểm tra:
- stream_connection capability được thêm vào registry
- Protocol enum: websocket, sse, grpc_stream
- Auth mode enum: none, token, sig_v4
- Default obligations: connection_auth_required, heartbeat_required, reconnect_policy_required
- Params schema đầy đủ (endpoint, subscription, heartbeat_interval, reconnect_policy, auth_mode)
- Access patterns đúng (network access, streaming effects)
- Serialization/deserialization hoạt động đúng

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from midicoder.contracts.core_capabilities import (
    CoreCapabilitiesRegistry,
    StreamingCoreCapabilities,
)
from midicoder.contracts.graph import CoreCapability


class TestStreamingCoreCapabilities:
    """Tests cho Streaming Core Capabilities."""

    def test_stream_connection_exists(self):
        """Kiểm tra stream_connection capability tồn tại."""
        registry = CoreCapabilitiesRegistry()
        cap = registry.get_capability_by_id("stream_connection")

        assert cap is not None
        assert cap.id == "stream_connection"
        assert cap.name == "Stream Connection"
        assert "protocol" in cap.params_schema
        assert "endpoint" in cap.params_schema
        assert "subscription" in cap.params_schema

    def test_stream_connection_protocol_enum(self):
        """Kiểm tra protocol enum của stream_connection."""
        registry = CoreCapabilitiesRegistry()
        cap = registry.get_capability_by_id("stream_connection")

        protocol_enum = cap.params_schema["protocol"]["enum"]
        assert "websocket" in protocol_enum
        assert "sse" in protocol_enum
        assert "grpc_stream" in protocol_enum

    def test_stream_connection_auth_mode_enum(self):
        """Kiểm tra auth_mode enum của stream_connection."""
        registry = CoreCapabilitiesRegistry()
        cap = registry.get_capability_by_id("stream_connection")

        auth_mode_enum = cap.params_schema["auth_mode"]["enum"]
        assert "none" in auth_mode_enum
        assert "token" in auth_mode_enum
        assert "sig_v4" in auth_mode_enum

    def test_stream_connection_required_fields(self):
        """Kiểm tra các required fields của stream_connection."""
        registry = CoreCapabilitiesRegistry()
        cap = registry.get_capability_by_id("stream_connection")

        # Kiểm tra required fields
        assert cap.params_schema["protocol"]["required"] is True
        assert cap.params_schema["endpoint"]["required"] is True
        assert cap.params_schema["subscription"]["required"] is True

    def test_stream_connection_heartbeat_params(self):
        """Kiểm tra heartbeat params của stream_connection."""
        registry = CoreCapabilitiesRegistry()
        cap = registry.get_capability_by_id("stream_connection")

        assert "heartbeat_interval" in cap.params_schema
        assert cap.params_schema["heartbeat_interval"]["type"] == "integer"

    def test_stream_connection_reconnect_policy(self):
        """Kiểm tra reconnect_policy của stream_connection."""
        registry = CoreCapabilitiesRegistry()
        cap = registry.get_capability_by_id("stream_connection")

        assert "reconnect_policy" in cap.params_schema
        assert cap.params_schema["reconnect_policy"]["type"] == "object"

    def test_stream_connection_default_obligations(self):
        """Kiểm tra default obligations của stream_connection."""
        registry = CoreCapabilitiesRegistry()
        cap = registry.get_capability_by_id("stream_connection")

        assert "connection_auth_required" in cap.default_obligations
        assert "heartbeat_required" in cap.default_obligations
        assert "reconnect_policy_required" in cap.default_obligations

    def test_stream_connection_access_patterns(self):
        """Kiểm tra access patterns của stream_connection."""
        registry = CoreCapabilitiesRegistry()
        cap = registry.get_capability_by_id("stream_connection")

        # Kiểm tra network access
        assert "network" in cap.write_access
        # Kiểm tra streaming effects
        assert "stream_connected" in cap.effects or "stream_opened" in cap.effects

    def test_stream_connection_description(self):
        """Kiểm tra description của stream_connection."""
        registry = CoreCapabilitiesRegistry()
        cap = registry.get_capability_by_id("stream_connection")

        assert cap.description is not None
        assert "stream" in cap.description.lower()
        assert "websocket" in cap.description.lower() or "sse" in cap.description.lower()


class TestStreamingCoreCapabilitiesCategory:
    """Tests cho StreamingCoreCapabilities category class."""

    def test_streaming_category_exists(self):
        """Kiểm tra StreamingCoreCapabilities category tồn tại."""
        registry = CoreCapabilitiesRegistry()

        assert registry.streaming is not None
        assert hasattr(registry.streaming, "STREAM_CONNECTION")


class TestCoreCapabilitiesRegistryWithStreaming:
    """Tests cho CoreCapabilitiesRegistry sau khi thêm streaming."""

    def test_get_all_capabilities_returns_17(self):
        """Kiểm tra registry trả về đúng 17 capabilities (16 + 1 streaming)."""
        capabilities = CoreCapabilitiesRegistry.get_all_capabilities()

        assert len(capabilities) == 17

    def test_stream_connection_in_registry(self):
        """Kiểm tra stream_connection có trong registry."""
        ids = CoreCapabilitiesRegistry.get_capability_ids()

        assert "stream_connection" in ids

    def test_get_statistics_updated(self):
        """Kiểm tra statistics được cập nhật với streaming category."""
        stats = CoreCapabilitiesRegistry.get_statistics()

        assert stats["total"] == 17
        assert "streaming" in stats["by_category"]
        assert stats["by_category"]["streaming"] == 1

    def test_all_17_capabilities_present(self):
        """Kiểm tra tất cả 17 core capabilities đều có mặt."""
        expected_ids = [
            # Authorization & Security (3)
            "authorize_permission",
            "enforce_tenant_scope",
            "validate_input",
            # Data Operations (5)
            "create_record",
            "update_record",
            "delete_record",
            "query_records",
            "load_entity",
            # Transaction Management (3)
            "begin_transaction",
            "commit_transaction",
            "rollback_transaction",
            # Event & Integration (3)
            "publish_event",
            "call_external_service",
            "send_notification",
            # Audit & Observability (2)
            "write_audit_log",
            "record_metric",
            # Streaming (1) - NEW
            "stream_connection",
        ]

        ids = CoreCapabilitiesRegistry.get_capability_ids()

        for expected_id in expected_ids:
            assert expected_id in ids, f"Missing capability: {expected_id}"


class TestStreamConnectionSerialization:
    """Tests cho serialization của stream_connection."""

    def test_to_dict_contains_required_fields(self):
        """Kiểm tra to_dict chứa các fields bắt buộc."""
        registry = CoreCapabilitiesRegistry()
        cap = registry.get_capability_by_id("stream_connection")
        cap_dict = cap.to_dict()

        assert "id" in cap_dict
        assert cap_dict["id"] == "stream_connection"
        assert "name" in cap_dict
        assert "description" in cap_dict
        assert "params_schema" in cap_dict
        assert "default_obligations" in cap_dict
        assert "read_access" in cap_dict
        assert "write_access" in cap_dict
        assert "effects" in cap_dict

    def test_from_dict_creates_stream_connection(self):
        """Kiểm tra from_dict tạo stream_connection đúng."""
        cap_data = {
            "id": "stream_connection",
            "name": "Stream Connection",
            "description": "Quản lý kết nối streaming real-time",
            "params_schema": {
                "protocol": {
                    "type": "string",
                    "required": True,
                    "enum": ["websocket", "sse", "grpc_stream"]
                },
                "endpoint": {"type": "string", "required": True},
                "subscription": {"type": "string", "required": True},
                "heartbeat_interval": {"type": "integer", "required": False},
                "reconnect_policy": {"type": "object", "required": False},
                "auth_mode": {
                    "type": "string",
                    "required": False,
                    "enum": ["none", "token", "sig_v4"]
                }
            },
            "default_obligations": [
                "connection_auth_required",
                "heartbeat_required",
                "reconnect_policy_required"
            ],
            "read_access": [],
            "write_access": ["network"],
            "effects": ["stream_connected"]
        }

        cap = CoreCapability.from_dict(cap_data)

        assert cap.id == "stream_connection"
        assert cap.name == "Stream Connection"
        assert "websocket" in cap.params_schema["protocol"]["enum"]
        assert "connection_auth_required" in cap.default_obligations

    def test_roundtrip_serialization(self):
        """Kiểm tra serialization roundtrip cho stream_connection."""
        registry = CoreCapabilitiesRegistry()
        cap = registry.get_capability_by_id("stream_connection")

        cap_dict = cap.to_dict()
        reconstructed = CoreCapability.from_dict(cap_dict)

        assert reconstructed.id == cap.id
        assert reconstructed.name == cap.name
        assert reconstructed.description == cap.description
        assert reconstructed.params_schema == cap.params_schema
        assert reconstructed.default_obligations == cap.default_obligations
        assert reconstructed.read_access == cap.read_access
        assert reconstructed.write_access == cap.write_access
        assert reconstructed.effects == cap.effects


class TestStreamConnectionUseCases:
    """Tests cho use cases của stream_connection theo GAP analysis."""

    def test_food_delivery_tracking_scenario(self):
        """
        Kiểm tra scenario: Food Delivery - Real-time order tracking.
        
        Khách hàng cần theo dõi đơn hàng theo thời gian thực qua WebSocket.
        """
        registry = CoreCapabilitiesRegistry()
        cap = registry.get_capability_by_id("stream_connection")

        # Đảm bảo capability hỗ trợ websocket cho tracking
        assert "websocket" in cap.params_schema["protocol"]["enum"]
        # Đảm bảo có heartbeat để giữ kết nối sống
        assert "heartbeat_interval" in cap.params_schema
        # Đảm bảo có reconnect policy cho mobile networks
        assert "reconnect_policy" in cap.params_schema

    def test_exchange_trading_scenario(self):
        """
        Kiểm tra scenario: Exchange Trading - Real-time market data.
        
        Trader cần nhận market data theo thời gian thực qua SSE/WebSocket.
        """
        registry = CoreCapabilitiesRegistry()
        cap = registry.get_capability_by_id("stream_connection")

        # Đảm bảo capability hỗ trợ cả websocket và sse
        assert "websocket" in cap.params_schema["protocol"]["enum"]
        assert "sse" in cap.params_schema["protocol"]["enum"]
        # Đảm bảo có subscription support cho market data channels
        assert "subscription" in cap.params_schema

    def test_telehealth_video_scenario(self):
        """
        Kiểm tra scenario: Telehealth - Real-time video consultation.
        
        Bác sĩ và bệnh nhân cần video call theo thời gian thực.
        """
        registry = CoreCapabilitiesRegistry()
        cap = registry.get_capability_by_id("stream_connection")

        # Đảm bảo capability hỗ trợ authentication (token cho patient data)
        assert "auth_mode" in cap.params_schema
        assert "token" in cap.params_schema["auth_mode"]["enum"]
        # Đảm bảo có connection management
        assert "connection_auth_required" in cap.default_obligations

    def test_reconnect_policy_structure(self):
        """
        Kiểm tra cấu trúc reconnect_policy cho mobile/unstable networks.
        """
        registry = CoreCapabilitiesRegistry()
        cap = registry.get_capability_by_id("stream_connection")

        reconnect_schema = cap.params_schema["reconnect_policy"]
        assert reconnect_schema["type"] == "object"
        # Reconnect policy phải có properties cho cấu hình
        assert "properties" in reconnect_schema