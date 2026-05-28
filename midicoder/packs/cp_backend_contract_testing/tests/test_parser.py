"""
Tests cho CP64 Contract Parser.

Unit tests cho:
- ContractIR dataclass (to_dict, from_dict)
- parse_consumer_specs
- parse_provider_verifiers
- parse_to_ir

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from midicoder.packs.cp_backend_contract_testing.parser import (
    ContractIR,
    parse_consumer_specs,
    parse_provider_verifiers,
    parse_to_ir,
)
from midicoder.packs.cp_backend_contract_testing.models import (
    ConsumerSpec,
    Interaction,
    PactBrokerConfig,
    ProviderVerifier,
    RequestMatch,
    ResponseStub,
)


# ===========================================================================
# Test ContractIR
# ===========================================================================


class TestContractIR:
    """Tests cho ContractIR."""

    def test_default_values(self):
        ir = ContractIR()
        assert ir.consumer_specs == []
        assert ir.provider_verifiers == []
        assert ir.pact_broker_config is None
        assert ir.default_pact_version == "2.0.0"
        assert ir.enable_auto_publish is False

    def test_with_consumer_specs(self):
        spec = ConsumerSpec(
            id="s1",
            consumer_name="Web",
            provider_name="API",
            interactions=[
                Interaction(
                    id="i1",
                    description="test",
                    request=RequestMatch(method="GET", path="/"),
                    response=ResponseStub(status=200),
                )
            ],
        )
        ir = ContractIR(consumer_specs=[spec])
        assert len(ir.consumer_specs) == 1
        assert ir.consumer_specs[0].id == "s1"

    def test_with_provider_verifiers(self):
        pv = ProviderVerifier(
            id="pv1",
            provider_name="API",
            pact_broker_url="https://b.com",
        )
        ir = ContractIR(provider_verifiers=[pv])
        assert len(ir.provider_verifiers) == 1
        assert ir.provider_verifiers[0].provider_name == "API"

    def test_with_pact_broker_config(self):
        pbc = PactBrokerConfig(id="b1", url="https://b.com", auto_publish=True)
        ir = ContractIR(pact_broker_config=pbc)
        assert ir.pact_broker_config is not None
        assert ir.pact_broker_config.url == "https://b.com"

    def test_custom_pact_version(self):
        ir = ContractIR(default_pact_version="3.0.0", enable_auto_publish=True)
        assert ir.default_pact_version == "3.0.0"
        assert ir.enable_auto_publish is True

    def test_to_dict_empty(self):
        ir = ContractIR()
        d = ir.to_dict()
        assert d["consumer_specs"] == []
        assert d["provider_verifiers"] == []
        assert "pact_broker_config" not in d
        assert d["default_pact_version"] == "2.0.0"
        assert d["enable_auto_publish"] is False

    def test_to_dict_with_broker(self):
        pbc = PactBrokerConfig(id="b1", url="https://b.com")
        ir = ContractIR(pact_broker_config=pbc)
        d = ir.to_dict()
        assert d["pact_broker_config"]["id"] == "b1"
        assert d["pact_broker_config"]["url"] == "https://b.com"

    def test_to_dict_full(self):
        spec = ConsumerSpec(id="s1", consumer_name="C", provider_name="P")
        pv = ProviderVerifier(id="pv1", provider_name="P")
        pbc = PactBrokerConfig(id="b1", url="https://b.com")
        ir = ContractIR(
            consumer_specs=[spec],
            provider_verifiers=[pv],
            pact_broker_config=pbc,
            default_pact_version="2.1.0",
            enable_auto_publish=True,
        )
        d = ir.to_dict()
        assert len(d["consumer_specs"]) == 1
        assert len(d["provider_verifiers"]) == 1
        assert d["pact_broker_config"]["id"] == "b1"
        assert d["default_pact_version"] == "2.1.0"
        assert d["enable_auto_publish"] is True

    def test_from_dict_empty(self):
        ir = ContractIR.from_dict({})
        assert ir.consumer_specs == []
        assert ir.provider_verifiers == []
        assert ir.pact_broker_config is None
        assert ir.default_pact_version == "2.0.0"
        assert ir.enable_auto_publish is False

    def test_from_dict_full(self):
        d = {
            "consumer_specs": [
                {
                    "id": "s1",
                    "consumer_name": "Web",
                    "provider_name": "API",
                    "interactions": [
                        {
                            "id": "i1",
                            "description": "Get data",
                            "request": {"method": "GET", "path": "/data"},
                            "response": {"status": 200, "body": {"key": "val"}},
                        }
                    ],
                }
            ],
            "provider_verifiers": [
                {
                    "id": "pv1",
                    "provider_name": "API",
                    "pact_broker_url": "https://b.com",
                    "publish_verification_results": True,
                }
            ],
            "pact_broker_config": {
                "id": "b1",
                "url": "https://b.com",
                "auto_publish": True,
            },
            "default_pact_version": "2.1.0",
            "enable_auto_publish": True,
        }
        ir = ContractIR.from_dict(d)
        assert len(ir.consumer_specs) == 1
        assert ir.consumer_specs[0].consumer_name == "Web"
        assert len(ir.consumer_specs[0].interactions) == 1
        assert len(ir.provider_verifiers) == 1
        assert ir.provider_verifiers[0].publish_verification_results is True
        assert ir.pact_broker_config is not None
        assert ir.pact_broker_config.auto_publish is True
        assert ir.default_pact_version == "2.1.0"
        assert ir.enable_auto_publish is True

    def test_roundtrip(self):
        original = ContractIR(
            consumer_specs=[
                ConsumerSpec(
                    id="rt",
                    consumer_name="RTConsumer",
                    provider_name="RTProvider",
                    interactions=[
                        Interaction(
                            id="rt_int",
                            description="RT",
                            request=RequestMatch(method="POST", path="/api", body={"x": 1}),
                            response=ResponseStub(status=201),
                        )
                    ],
                )
            ],
            provider_verifiers=[
                ProviderVerifier(id="rt_pv", provider_name="RTProvider")
            ],
            pact_broker_config=PactBrokerConfig(id="rt_b", url="https://rt.com"),
            default_pact_version="2.1.0",
            enable_auto_publish=True,
        )
        restored = ContractIR.from_dict(original.to_dict())
        assert len(restored.consumer_specs) == len(original.consumer_specs)
        assert restored.consumer_specs[0].id == original.consumer_specs[0].id
        assert len(restored.provider_verifiers) == len(original.provider_verifiers)
        assert restored.pact_broker_config is not None
        assert restored.pact_broker_config.url == original.pact_broker_config.url
        assert restored.default_pact_version == original.default_pact_version
        assert restored.enable_auto_publish == original.enable_auto_publish


# ===========================================================================
# Test parse_consumer_specs
# ===========================================================================


class TestParseConsumerSpecs:
    """Tests cho parse_consumer_specs()."""

    def test_parse_consumer_specs_key(self):
        data = {
            "consumer_specs": [
                {
                    "id": "s1",
                    "consumer_name": "C1",
                    "provider_name": "P1",
                }
            ]
        }
        specs = parse_consumer_specs(data)
        assert len(specs) == 1
        assert specs[0].id == "s1"
        assert specs[0].consumer_name == "C1"

    def test_parse_contracts_key(self):
        data = {
            "contracts": [
                {
                    "id": "s2",
                    "consumer_name": "C2",
                    "provider_name": "P2",
                }
            ]
        }
        specs = parse_consumer_specs(data)
        assert len(specs) == 1
        assert specs[0].id == "s2"

    def test_parse_empty(self):
        data = {}
        specs = parse_consumer_specs(data)
        assert specs == []

    def test_parse_multiple_specs(self):
        data = {
            "consumer_specs": [
                {"id": "a", "consumer_name": "A", "provider_name": "P"},
                {"id": "b", "consumer_name": "B", "provider_name": "P"},
                {"id": "c", "consumer_name": "C", "provider_name": "P"},
            ]
        }
        specs = parse_consumer_specs(data)
        assert len(specs) == 3
        assert all(isinstance(s, ConsumerSpec) for s in specs)

    def test_parse_with_interactions(self):
        data = {
            "consumer_specs": [
                {
                    "id": "s1",
                    "consumer_name": "C",
                    "provider_name": "P",
                    "interactions": [
                        {
                            "id": "i1",
                            "description": "Fetch",
                            "request": {"method": "GET", "path": "/items"},
                            "response": {"status": 200, "body": []},
                        }
                    ],
                }
            ]
        }
        specs = parse_consumer_specs(data)
        assert len(specs[0].interactions) == 1
        assert specs[0].interactions[0].id == "i1"


# ===========================================================================
# Test parse_provider_verifiers
# ===========================================================================


class TestParseProviderVerifiers:
    """Tests cho parse_provider_verifiers()."""

    def test_parse_provider_verifiers_key(self):
        data = {
            "provider_verifiers": [
                {
                    "id": "pv1",
                    "provider_name": "API",
                    "pact_broker_url": "https://b.com",
                }
            ]
        }
        pvs = parse_provider_verifiers(data)
        assert len(pvs) == 1
        assert pvs[0].id == "pv1"
        assert pvs[0].pact_broker_url == "https://b.com"

    def test_parse_verifiers_key(self):
        data = {
            "verifiers": [
                {
                    "id": "v1",
                    "provider_name": "Svc",
                }
            ]
        }
        pvs = parse_provider_verifiers(data)
        assert len(pvs) == 1
        assert pvs[0].id == "v1"

    def test_parse_empty(self):
        data = {}
        pvs = parse_provider_verifiers(data)
        assert pvs == []

    def test_parse_multiple_verifiers(self):
        data = {
            "provider_verifiers": [
                {"id": "x", "provider_name": "X"},
                {"id": "y", "provider_name": "Y"},
            ]
        }
        pvs = parse_provider_verifiers(data)
        assert len(pvs) == 2
        assert all(isinstance(p, ProviderVerifier) for p in pvs)


# ===========================================================================
# Test parse_to_ir
# ===========================================================================


class TestParseToIR:
    """Tests cho parse_to_ir()."""

    def test_parse_minimal(self):
        data = {}
        ir = parse_to_ir(data)
        assert isinstance(ir, ContractIR)
        assert ir.consumer_specs == []
        assert ir.provider_verifiers == []
        assert ir.pact_broker_config is None
        assert ir.default_pact_version == "2.0.0"
        assert ir.enable_auto_publish is False

    def test_parse_full(self):
        data = {
            "consumer_specs": [
                {
                    "id": "cs1",
                    "consumer_name": "WebApp",
                    "provider_name": "API",
                    "interactions": [
                        {
                            "id": "i1",
                            "description": "GET /users",
                            "request": {"method": "GET", "path": "/users"},
                            "response": {"status": 200, "body": []},
                        }
                    ],
                }
            ],
            "provider_verifiers": [
                {
                    "id": "pv1",
                    "provider_name": "API",
                    "pact_broker_url": "https://b.com",
                    "publish_verification_results": True,
                    "tags": ["main"],
                }
            ],
            "pact_broker_config": {
                "id": "b1",
                "url": "https://b.com",
                "auth_token": "tok",
                "auto_publish": True,
            },
            "default_pact_version": "2.1.0",
            "enable_auto_publish": True,
        }
        ir = parse_to_ir(data)
        assert len(ir.consumer_specs) == 1
        assert ir.consumer_specs[0].consumer_name == "WebApp"
        assert len(ir.consumer_specs[0].interactions) == 1
        assert len(ir.provider_verifiers) == 1
        assert ir.provider_verifiers[0].publish_verification_results is True
        assert ir.pact_broker_config is not None
        assert ir.pact_broker_config.auto_publish is True
        assert ir.default_pact_version == "2.1.0"
        assert ir.enable_auto_publish is True

    def test_parse_with_contracts_alias(self):
        data = {
            "contracts": [
                {"id": "c1", "consumer_name": "C", "provider_name": "P"}
            ],
            "verifiers": [
                {"id": "v1", "provider_name": "P"}
            ],
        }
        ir = parse_to_ir(data)
        assert len(ir.consumer_specs) == 1
        assert len(ir.provider_verifiers) == 1

    def test_parse_no_broker(self):
        data = {
            "consumer_specs": [
                {"id": "s1", "consumer_name": "C", "provider_name": "P"}
            ]
        }
        ir = parse_to_ir(data)
        assert ir.pact_broker_config is None

    def test_parse_multiple_consumers_single_provider(self):
        data = {
            "consumer_specs": [
                {"id": "a", "consumer_name": "WebApp", "provider_name": "PaymentService"},
                {"id": "b", "consumer_name": "MobileApp", "provider_name": "PaymentService"},
                {"id": "c", "consumer_name": "Admin", "provider_name": "PaymentService"},
            ],
            "provider_verifiers": [
                {
                    "id": "pv1",
                    "provider_name": "PaymentService",
                    "consumer_version_selectors": [
                        {"consumer": "WebApp", "version": "latest"},
                        {"consumer": "MobileApp", "version": "latest"},
                    ],
                }
            ],
        }
        ir = parse_to_ir(data)
        assert len(ir.consumer_specs) == 3
        assert all(s.provider_name == "PaymentService" for s in ir.consumer_specs)
        assert len(ir.provider_verifiers[0].consumer_version_selectors) == 2
