"""
Tests cho CP64 Contract Testing Models.

Unit tests cho:
- ContractType enum
- MatchRule enum
- RequestMatch validation, to_dict, from_dict
- ResponseStub validation, to_dict, from_dict
- Interaction validation, to_dict, from_dict
- ConsumerSpec validation, to_dict, from_dict
- ProviderVerifier validation, to_dict, from_dict
- PactBrokerConfig validation, to_dict, from_dict

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from midicoder.packs.cp_backend_contract_testing.models import (
    ContractType,
    MatchRule,
    ConsumerSpec,
    Interaction,
    PactBrokerConfig,
    ProviderVerifier,
    RequestMatch,
    ResponseStub,
)
from midicoder.errors import ErrorCode, MidicoderError


# ===========================================================================
# Test ContractType
# ===========================================================================


class TestContractType:
    """Tests cho ContractType enum."""

    def test_consumer_driven_value(self):
        assert ContractType.CONSUMER_DRIVEN.value == "consumer_driven"

    def test_provider_verification_value(self):
        assert ContractType.PROVIDER_VERIFICATION.value == "provider_verification"

    def test_bidi_value(self):
        assert ContractType.BIDI.value == "bidi"

    def test_from_string_consumer_driven(self):
        assert ContractType("consumer_driven") == ContractType.CONSUMER_DRIVEN

    def test_from_string_provider_verification(self):
        assert ContractType("provider_verification") == ContractType.PROVIDER_VERIFICATION

    def test_from_string_bidi(self):
        assert ContractType("bidi") == ContractType.BIDI

    def test_from_string_invalid(self):
        with pytest.raises(ValueError):
            ContractType("invalid_type")


# ===========================================================================
# Test MatchRule
# ===========================================================================


class TestMatchRule:
    """Tests cho MatchRule enum."""

    def test_strict_value(self):
        assert MatchRule.STRICT.value == "strict"

    def test_equality_value(self):
        assert MatchRule.EQUALITY.value == "equality"

    def test_regex_value(self):
        assert MatchRule.REGEX.value == "regex"

    def test_type_value(self):
        assert MatchRule.TYPE.value == "type"

    def test_include_type_value(self):
        assert MatchRule.INCLUDE_TYPE.value == "include_type"

    def test_from_string_regex(self):
        assert MatchRule("regex") == MatchRule.REGEX

    def test_from_string_invalid(self):
        with pytest.raises(ValueError):
            MatchRule("invalid_rule")


# ===========================================================================
# Test RequestMatch
# ===========================================================================


class TestRequestMatch:
    """Tests cho RequestMatch."""

    def test_valid_request_match(self):
        rm = RequestMatch(
            method="GET",
            path="/orders/123",
            headers={"Content-Type": "application/json"},
            match_rules={"body.id": MatchRule.TYPE},
        )
        assert rm.method == "GET"
        assert rm.path == "/orders/123"
        assert rm.headers["Content-Type"] == "application/json"
        assert rm.body is None
        assert rm.query == {}
        assert len(rm.match_rules) == 1

    def test_with_body_and_query(self):
        rm = RequestMatch(
            method="POST",
            path="/orders",
            body={"item_id": "prod-1"},
            query={"page": "1"},
        )
        assert rm.body["item_id"] == "prod-1"
        assert rm.query["page"] == "1"

    def test_empty_method_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            RequestMatch(method="", path="/test")
        assert exc_info.value.code == ErrorCode.INVALID_INPUT

    def test_empty_path_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            RequestMatch(method="GET", path="")
        assert exc_info.value.code == ErrorCode.INVALID_INPUT

    def test_whitespace_method_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            RequestMatch(method="  ", path="/test")
        assert exc_info.value.code == ErrorCode.INVALID_INPUT

    def test_to_dict(self):
        rm = RequestMatch(
            method="PUT",
            path="/users/1",
            headers={"Content-Type": "application/json"},
            body={"name": "test"},
            query={"v": "2"},
            match_rules={"body.name": MatchRule.EQUALITY},
        )
        d = rm.to_dict()
        assert d["method"] == "PUT"
        assert d["path"] == "/users/1"
        assert d["body"]["name"] == "test"
        assert d["query"]["v"] == "2"
        assert d["match_rules"]["body.name"] == "equality"

    def test_from_dict(self):
        d = {
            "method": "DELETE",
            "path": "/orders/5",
            "headers": {"Authorization": "Bearer token"},
            "body": None,
            "query": {},
            "match_rules": {"body.status": "regex"},
        }
        rm = RequestMatch.from_dict(d)
        assert rm.method == "DELETE"
        assert rm.path == "/orders/5"
        assert rm.match_rules["body.status"] == MatchRule.REGEX

    def test_from_dict_defaults(self):
        rm = RequestMatch.from_dict({})
        assert rm.method == "GET"
        assert rm.path == "/"
        assert rm.headers == {}
        assert rm.body is None
        assert rm.query == {}
        assert rm.match_rules == {}

    def test_roundtrip(self):
        original = RequestMatch(
            method="PATCH",
            path="/products/42",
            headers={"If-Match": "etag-1"},
            body={"price": 19.99},
            query={"locale": "en"},
            match_rules={
                "body.price": MatchRule.TYPE,
                "headers.If-Match": MatchRule.STRICT,
            },
        )
        restored = RequestMatch.from_dict(original.to_dict())
        assert restored.method == original.method
        assert restored.path == original.path
        assert restored.headers == original.headers
        assert restored.body == original.body
        assert restored.query == original.query
        assert restored.match_rules == original.match_rules


# ===========================================================================
# Test ResponseStub
# ===========================================================================


class TestResponseStub:
    """Tests cho ResponseStub."""

    def test_valid_response_stub(self):
        rs = ResponseStub(
            status=200,
            headers={"Content-Type": "application/json"},
            body={"id": 1, "name": "test"},
        )
        assert rs.status == 200
        assert rs.body["id"] == 1

    def test_201_status(self):
        rs = ResponseStub(status=201, body={"created": True})
        assert rs.status == 201

    def test_404_status(self):
        rs = ResponseStub(status=404, body={"error": "not_found"})
        assert rs.status == 404

    def test_invalid_status_too_low(self):
        with pytest.raises(MidicoderError) as exc_info:
            ResponseStub(status=99)
        assert exc_info.value.code == ErrorCode.INVALID_INPUT

    def test_invalid_status_too_high(self):
        with pytest.raises(MidicoderError) as exc_info:
            ResponseStub(status=600)
        assert exc_info.value.code == ErrorCode.INVALID_INPUT

    def test_invalid_status_string(self):
        with pytest.raises(MidicoderError) as exc_info:
            ResponseStub(status="ok")  # type: ignore
        assert exc_info.value.code == ErrorCode.INVALID_INPUT

    def test_default_headers_and_body(self):
        rs = ResponseStub(status=200)
        assert rs.headers == {}
        assert rs.body is None
        assert rs.match_rules == {}

    def test_to_dict(self):
        rs = ResponseStub(
            status=201,
            headers={"Location": "/orders/1"},
            body={"id": 1},
            match_rules={"body.id": MatchRule.TYPE},
        )
        d = rs.to_dict()
        assert d["status"] == 201
        assert d["headers"]["Location"] == "/orders/1"
        assert d["match_rules"]["body.id"] == "type"

    def test_from_dict(self):
        d = {
            "status": 204,
            "headers": {},
            "body": None,
            "match_rules": {},
        }
        rs = ResponseStub.from_dict(d)
        assert rs.status == 204
        assert rs.headers == {}
        assert rs.body is None

    def test_from_dict_defaults(self):
        rs = ResponseStub.from_dict({})
        assert rs.status == 200
        assert rs.headers == {}
        assert rs.body is None

    def test_roundtrip(self):
        original = ResponseStub(
            status=200,
            headers={"Content-Type": "application/json"},
            body={"data": [1, 2, 3]},
            match_rules={"body.data": MatchRule.INCLUDE_TYPE},
        )
        restored = ResponseStub.from_dict(original.to_dict())
        assert restored.status == original.status
        assert restored.headers == original.headers
        assert restored.body == original.body
        assert restored.match_rules == original.match_rules


# ===========================================================================
# Test Interaction
# ===========================================================================


class TestInteraction:
    """Tests cho Interaction."""

    def test_valid_interaction(self):
        i = Interaction(
            id="get_order",
            description="GET order by ID",
            request=RequestMatch(method="GET", path="/orders/1"),
            response=ResponseStub(status=200, body={"id": 1}),
            provider_state="order exists",
        )
        assert i.id == "get_order"
        assert i.provider_state == "order exists"

    def test_empty_id_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            Interaction(
                id="",
                description="test",
                request=RequestMatch(method="GET", path="/"),
                response=ResponseStub(status=200),
            )
        assert exc_info.value.code == ErrorCode.INVALID_ID

    def test_whitespace_id_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            Interaction(
                id="  ",
                description="test",
                request=RequestMatch(method="GET", path="/"),
                response=ResponseStub(status=200),
            )
        assert exc_info.value.code == ErrorCode.INVALID_ID

    def test_default_provider_state(self):
        i = Interaction(
            id="test",
            description="test",
            request=RequestMatch(method="GET", path="/"),
            response=ResponseStub(status=200),
        )
        assert i.provider_state == ""

    def test_to_dict(self):
        i = Interaction(
            id="create_order",
            description="POST create order",
            request=RequestMatch(method="POST", path="/orders", body={"item": "a"}),
            response=ResponseStub(status=201, body={"id": 1}),
            provider_state="valid items",
        )
        d = i.to_dict()
        assert d["id"] == "create_order"
        assert d["description"] == "POST create order"
        assert d["request"]["method"] == "POST"
        assert d["response"]["status"] == 201
        assert d["provider_state"] == "valid items"

    def test_from_dict(self):
        d = {
            "id": "test_interaction",
            "description": "Test interaction",
            "request": {"method": "GET", "path": "/test"},
            "response": {"status": 200},
            "provider_state": "test state",
        }
        i = Interaction.from_dict(d)
        assert i.id == "test_interaction"
        assert i.request.method == "GET"
        assert i.response.status == 200

    def test_from_dict_description_default(self):
        d = {
            "id": "no_desc",
            "request": {"method": "GET", "path": "/"},
            "response": {"status": 200},
        }
        i = Interaction.from_dict(d)
        assert i.description == "no_desc"

    def test_roundtrip(self):
        original = Interaction(
            id="rt_test",
            description="Roundtrip test",
            request=RequestMatch(method="POST", path="/api", body={"k": "v"}),
            response=ResponseStub(status=201, body={"ok": True}),
            provider_state="ready",
        )
        restored = Interaction.from_dict(original.to_dict())
        assert restored.id == original.id
        assert restored.description == original.description
        assert restored.provider_state == original.provider_state
        assert restored.request.method == original.request.method
        assert restored.response.status == original.response.status


# ===========================================================================
# Test ConsumerSpec
# ===========================================================================


class TestConsumerSpec:
    """Tests cho ConsumerSpec."""

    def test_valid_consumer_spec(self):
        cs = ConsumerSpec(
            id="test_spec",
            consumer_name="WebApp",
            provider_name="UserService",
        )
        assert cs.id == "test_spec"
        assert cs.consumer_name == "WebApp"
        assert cs.provider_name == "UserService"
        assert cs.interactions == []
        assert cs.pact_spec_version == "2.0.0"
        assert cs.metadata == {}

    def test_with_interactions(self):
        cs = ConsumerSpec(
            id="spec_with_interaction",
            consumer_name="ConsumerA",
            provider_name="ProviderB",
            interactions=[
                Interaction(
                    id="i1",
                    description="Test",
                    request=RequestMatch(method="GET", path="/"),
                    response=ResponseStub(status=200),
                )
            ],
        )
        assert len(cs.interactions) == 1
        assert cs.interactions[0].id == "i1"

    def test_custom_pact_version(self):
        cs = ConsumerSpec(
            id="spec_v3",
            consumer_name="C",
            provider_name="P",
            pact_spec_version="3.0.0",
        )
        assert cs.pact_spec_version == "3.0.0"

    def test_empty_id_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            ConsumerSpec(id="", consumer_name="C", provider_name="P")
        assert exc_info.value.code == ErrorCode.INVALID_ID

    def test_empty_consumer_name_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            ConsumerSpec(id="test", consumer_name="", provider_name="P")
        assert exc_info.value.code == ErrorCode.INVALID_INPUT

    def test_empty_provider_name_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            ConsumerSpec(id="test", consumer_name="C", provider_name="")
        assert exc_info.value.code == ErrorCode.INVALID_INPUT

    def test_to_dict(self):
        cs = ConsumerSpec(
            id="dict_spec",
            consumer_name="ConsumerX",
            provider_name="ProviderY",
            pact_spec_version="2.0.0",
            interactions=[
                Interaction(
                    id="i1",
                    description="Interaction 1",
                    request=RequestMatch(method="GET", path="/test"),
                    response=ResponseStub(status=200),
                )
            ],
            metadata={"env": "test"},
        )
        d = cs.to_dict()
        assert d["id"] == "dict_spec"
        assert d["consumer_name"] == "ConsumerX"
        assert d["provider_name"] == "ProviderY"
        assert len(d["interactions"]) == 1
        assert d["metadata"]["env"] == "test"

    def test_from_dict(self):
        d = {
            "id": "from_dict_spec",
            "consumer_name": "Web",
            "provider_name": "API",
            "interactions": [
                {
                    "id": "i1",
                    "description": "Fetch data",
                    "request": {"method": "GET", "path": "/data"},
                    "response": {"status": 200},
                }
            ],
            "pact_spec_version": "2.0.0",
            "metadata": {},
        }
        cs = ConsumerSpec.from_dict(d)
        assert cs.id == "from_dict_spec"
        assert cs.consumer_name == "Web"
        assert len(cs.interactions) == 1

    def test_roundtrip(self):
        original = ConsumerSpec(
            id="rt_spec",
            consumer_name="ConsumerRT",
            provider_name="ProviderRT",
            pact_spec_version="2.1.0",
            interactions=[
                Interaction(
                    id="rt_int",
                    description="Roundtrip",
                    request=RequestMatch(method="POST", path="/api", body={"x": 1}),
                    response=ResponseStub(status=201, body={"id": 1}),
                    provider_state="ready",
                )
            ],
            metadata={"key": "value"},
        )
        restored = ConsumerSpec.from_dict(original.to_dict())
        assert restored.id == original.id
        assert restored.consumer_name == original.consumer_name
        assert restored.provider_name == original.provider_name
        assert restored.pact_spec_version == original.pact_spec_version
        assert len(restored.interactions) == len(original.interactions)
        assert restored.metadata == original.metadata


# ===========================================================================
# Test ProviderVerifier
# ===========================================================================


class TestProviderVerifier:
    """Tests cho ProviderVerifier."""

    def test_valid_provider_verifier(self):
        pv = ProviderVerifier(
            id="verifier_1",
            provider_name="UserService",
            pact_broker_url="https://broker.example.com",
        )
        assert pv.id == "verifier_1"
        assert pv.provider_name == "UserService"
        assert pv.publish_verification_results is False
        assert pv.tags == []
        assert pv.consumer_version_selectors == []

    def test_full_provider_verifier(self):
        pv = ProviderVerifier(
            id="full_verifier",
            provider_name="OrderService",
            pact_broker_url="https://broker.example.com",
            publish_verification_results=True,
            tags=["main", "v1.0"],
            consumer_version_selectors=[{"consumer": "WebApp", "version": "latest"}],
        )
        assert pv.publish_verification_results is True
        assert "main" in pv.tags
        assert len(pv.consumer_version_selectors) == 1

    def test_empty_id_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            ProviderVerifier(id="", provider_name="P")
        assert exc_info.value.code == ErrorCode.INVALID_ID

    def test_empty_provider_name_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            ProviderVerifier(id="test", provider_name="")
        assert exc_info.value.code == ErrorCode.INVALID_INPUT

    def test_to_dict(self):
        pv = ProviderVerifier(
            id="dict_verifier",
            provider_name="TestService",
            pact_broker_url="https://broker.test",
            publish_verification_results=True,
            tags=["production"],
            consumer_version_selectors=[{"consumer": "App", "version": "latest"}],
        )
        d = pv.to_dict()
        assert d["id"] == "dict_verifier"
        assert d["publish_verification_results"] is True
        assert d["tags"] == ["production"]
        assert len(d["consumer_version_selectors"]) == 1

    def test_from_dict(self):
        d = {
            "id": "from_dict_pv",
            "provider_name": "Svc",
            "pact_broker_url": "https://b.com",
            "publish_verification_results": True,
            "tags": ["dev"],
            "consumer_version_selectors": [],
        }
        pv = ProviderVerifier.from_dict(d)
        assert pv.id == "from_dict_pv"
        assert pv.publish_verification_results is True
        assert "dev" in pv.tags

    def test_from_dict_defaults(self):
        d = {"id": "minimal", "provider_name": "P"}
        pv = ProviderVerifier.from_dict(d)
        assert pv.pact_broker_url == ""
        assert pv.publish_verification_results is False
        assert pv.tags == []
        assert pv.consumer_version_selectors == []

    def test_roundtrip(self):
        original = ProviderVerifier(
            id="rt_pv",
            provider_name="RTService",
            pact_broker_url="https://rt.com",
            publish_verification_results=True,
            tags=["tag1", "tag2"],
            consumer_version_selectors=[{"consumer": "C", "main_branch": True}],
        )
        restored = ProviderVerifier.from_dict(original.to_dict())
        assert restored.id == original.id
        assert restored.provider_name == original.provider_name
        assert restored.pact_broker_url == original.pact_broker_url
        assert restored.publish_verification_results == original.publish_verification_results
        assert restored.tags == original.tags
        assert restored.consumer_version_selectors == original.consumer_version_selectors


# ===========================================================================
# Test PactBrokerConfig
# ===========================================================================


class TestPactBrokerConfig:
    """Tests cho PactBrokerConfig."""

    def test_valid_pact_broker_config(self):
        pbc = PactBrokerConfig(
            id="broker_1",
            url="https://broker.example.com",
            auth_token="secret-token",
        )
        assert pbc.id == "broker_1"
        assert pbc.url == "https://broker.example.com"
        assert pbc.auth_token == "secret-token"
        assert pbc.project == ""
        assert pbc.tags == []
        assert pbc.auto_publish is False

    def test_full_broker_config(self):
        pbc = PactBrokerConfig(
            id="full_broker",
            url="https://broker.example.com",
            auth_token="token",
            project="my-org",
            tags=["production"],
            auto_publish=True,
        )
        assert pbc.project == "my-org"
        assert pbc.auto_publish is True

    def test_empty_id_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            PactBrokerConfig(id="")
        assert exc_info.value.code == ErrorCode.INVALID_ID

    def test_whitespace_id_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            PactBrokerConfig(id="  ")
        assert exc_info.value.code == ErrorCode.INVALID_ID

    def test_to_dict(self):
        pbc = PactBrokerConfig(
            id="dict_broker",
            url="https://b.com",
            auth_token="tok",
            project="proj",
            tags=["tag1"],
            auto_publish=True,
        )
        d = pbc.to_dict()
        assert d["id"] == "dict_broker"
        assert d["url"] == "https://b.com"
        assert d["project"] == "proj"
        assert d["auto_publish"] is True

    def test_from_dict(self):
        d = {
            "id": "from_dict_broker",
            "url": "https://b.com",
            "auth_token": "t",
            "project": "p",
            "tags": ["t"],
            "auto_publish": True,
        }
        pbc = PactBrokerConfig.from_dict(d)
        assert pbc.id == "from_dict_broker"
        assert pbc.auto_publish is True

    def test_from_dict_defaults(self):
        d = {"id": "minimal_broker"}
        pbc = PactBrokerConfig.from_dict(d)
        assert pbc.url == ""
        assert pbc.auth_token == ""
        assert pbc.project == ""
        assert pbc.tags == []
        assert pbc.auto_publish is False

    def test_roundtrip(self):
        original = PactBrokerConfig(
            id="rt_broker",
            url="https://rt.com",
            auth_token="rt_token",
            project="rt_proj",
            tags=["rt"],
            auto_publish=True,
        )
        restored = PactBrokerConfig.from_dict(original.to_dict())
        assert restored.id == original.id
        assert restored.url == original.url
        assert restored.auth_token == original.auth_token
        assert restored.project == original.project
        assert restored.tags == original.tags
        assert restored.auto_publish == original.auto_publish
