# coding: utf-8
"""
Mô-đun models cho CP64 — API Contract Testing (Pact).

Định nghĩa các dataclass biểu diễn:
- ContractType: Loại contract testing (consumer_driven, provider_verification, bidi)
- MatchRule: Quy tắc matching cho request/response (strict, equality, regex, type, include_type)
- ConsumerSpec: Định nghĩa consumer-driven contract với interactions
- Interaction: Request/response interaction đơn lẻ
- RequestMatch: Match criteria cho request
- ResponseStub: Stub response cho mocked provider
- ProviderVerifier: Cấu hình provider verification
- PactBrokerConfig: Cấu hình Pact Broker

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# ===========================================================================
# Enums
# ===========================================================================


class ContractType(str, Enum):
    """Loại contract testing.

    - CONSUMER_DRIVEN: Consumer-driven contract — consumer định nghĩa expectations
    - PROVIDER_VERIFICATION: Provider verification — provider verify contracts từ consumers
    - BIDI: Bidirectional — cả consumer và provider cùng định nghĩa contracts
    """
    CONSUMER_DRIVEN = "consumer_driven"
    PROVIDER_VERIFICATION = "provider_verification"
    BIDI = "bidi"


class MatchRule(str, Enum):
    """Quy tắc matching cho request/response fields.

    - STRICT: Strict equality — phải match chính xác
    - EQUALITY: Equality matching — so sánh giá trị
    - REGEX: Regex matching — match theo regular expression
    - TYPE: Type matching — chỉ kiểm tra kiểu dữ liệu
    - INCLUDE_TYPE: Include type — value phải contain kiểu được chỉ định
    """
    STRICT = "strict"
    EQUALITY = "equality"
    REGEX = "regex"
    TYPE = "type"
    INCLUDE_TYPE = "include_type"


# ===========================================================================
# RequestMatch
# ===========================================================================


@dataclass
class RequestMatch:
    """Match criteria cho request trong contract interaction.

    Định nghĩa request mà consumer gửi đến provider, bao gồm HTTP method,
    path, headers, body, query parameters, và các match rules để
    xác định mức độ matching.

    Attributes:
        method: HTTP method (GET, POST, PUT, DELETE, PATCH)
        path: URL path của request
        headers: HTTP headers
        body: Request body (任意 dữ liệu)
        query: Query parameters
        match_rules: Các match rules cho từng field
    """
    method: str
    path: str
    headers: dict[str, str] = field(default_factory=dict)
    body: Any = None
    query: dict[str, str] = field(default_factory=dict)
    match_rules: dict[str, MatchRule] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate RequestMatch sau khi khởi tạo."""
        if not self.method or not self.method.strip():
            raise EM.raise_error(
                ErrorCode.INVALID_INPUT,
                reason="RequestMatch.method bắt buộc và không được để trống",
            )
        if not self.path or not self.path.strip():
            raise EM.raise_error(
                ErrorCode.INVALID_INPUT,
                reason="RequestMatch.path bắt buộc và không được để trống",
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển RequestMatch sang dict."""
        return {
            "method": self.method,
            "path": self.path,
            "headers": self.headers,
            "body": self.body,
            "query": self.query,
            "match_rules": {k: v.value for k, v in self.match_rules.items()},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RequestMatch":
        """Tạo RequestMatch từ dict."""
        raw_rules = data.get("match_rules", {})
        match_rules = {k: MatchRule(v) for k, v in raw_rules.items()} if raw_rules else {}
        return cls(
            method=data.get("method", "GET"),
            path=data.get("path", "/"),
            headers=data.get("headers", {}),
            body=data.get("body", None),
            query=data.get("query", {}),
            match_rules=match_rules,
        )


# ===========================================================================
# ResponseStub
# ===========================================================================


@dataclass
class ResponseStub:
    """Stub response cho mocked provider trong contract test.

    Định nghĩa response mà provider sẽ trả về khi consumer gửi request
    trong quá trình contract testing. Bao gồm HTTP status, headers,
    body, và các match rules.

    Attributes:
        status: HTTP status code
        headers: Response headers
        body: Response body (任意 dữ liệu)
        match_rules: Các match rules cho response validation
    """
    status: int
    headers: dict[str, str] = field(default_factory=dict)
    body: Any = None
    match_rules: dict[str, MatchRule] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate ResponseStub sau khi khởi tạo."""
        if not isinstance(self.status, int) or self.status < 100 or self.status > 599:
            raise EM.raise_error(
                ErrorCode.INVALID_INPUT,
                reason=f"ResponseStub.status phải là HTTP status code hợp lệ (100-599), nhận được: {self.status}",
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển ResponseStub sang dict."""
        return {
            "status": self.status,
            "headers": self.headers,
            "body": self.body,
            "match_rules": {k: v.value for k, v in self.match_rules.items()},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ResponseStub":
        """Tạo ResponseStub từ dict."""
        raw_rules = data.get("match_rules", {})
        match_rules = {k: MatchRule(v) for k, v in raw_rules.items()} if raw_rules else {}
        return cls(
            status=data.get("status", 200),
            headers=data.get("headers", {}),
            body=data.get("body", None),
            match_rules=match_rules,
        )


# ===========================================================================
# Interaction
# ===========================================================================


@dataclass
class Interaction:
    """Request/response interaction đơn lẻ trong contract.

    Định nghĩa một interaction giữa consumer và provider, bao gồm
    mô tả, request match criteria, response stub, và provider state.

    Attributes:
        id: ID duy nhất của interaction
        description: Mô tả interaction
        request: Request match criteria
        response: Response stub
        provider_state: Provider state trước khi interaction
    """
    id: str
    description: str
    request: RequestMatch
    response: ResponseStub
    provider_state: str = ""

    def __post_init__(self) -> None:
        """Validate Interaction sau khi khởi tạo."""
        if not self.id or not self.id.strip():
            raise EM.raise_error(
                ErrorCode.INVALID_ID,
                reason="Interaction.id bắt buộc và không được để trống",
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển Interaction sang dict."""
        return {
            "id": self.id,
            "description": self.description,
            "request": self.request.to_dict(),
            "response": self.response.to_dict(),
            "provider_state": self.provider_state,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Interaction":
        """Tạo Interaction từ dict."""
        return cls(
            id=data["id"],
            description=data.get("description", data["id"]),
            request=RequestMatch.from_dict(data.get("request", {})),
            response=ResponseStub.from_dict(data.get("response", {})),
            provider_state=data.get("provider_state", ""),
        )


# ===========================================================================
# ConsumerSpec
# ===========================================================================


@dataclass
class ConsumerSpec:
    """Định nghĩa consumer-driven contract với interactions.

    Mô tả contract giữa consumer và provider, bao gồm danh sách
    các interactions (request/response pairs) và metadata.

    Attributes:
        id: ID duy nhất của consumer spec
        consumer_name: Tên consumer service
        provider_name: Tên provider service
        interactions: Danh sách các interactions
        pact_spec_version: Phiên bản Pact specification
        metadata: Dữ liệu bổ sung
    """
    id: str
    consumer_name: str
    provider_name: str
    interactions: list[Interaction] = field(default_factory=list)
    pact_spec_version: str = "2.0.0"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate ConsumerSpec sau khi khởi tạo."""
        if not self.id or not self.id.strip():
            raise EM.raise_error(
                ErrorCode.INVALID_ID,
                reason="ConsumerSpec.id bắt buộc và không được để trống",
            )
        if not self.consumer_name or not self.consumer_name.strip():
            raise EM.raise_error(
                ErrorCode.INVALID_INPUT,
                reason="ConsumerSpec.consumer_name bắt buộc và không được để trống",
            )
        if not self.provider_name or not self.provider_name.strip():
            raise EM.raise_error(
                ErrorCode.INVALID_INPUT,
                reason="ConsumerSpec.provider_name bắt buộc và không được để trống",
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển ConsumerSpec sang dict."""
        return {
            "id": self.id,
            "consumer_name": self.consumer_name,
            "provider_name": self.provider_name,
            "interactions": [i.to_dict() for i in self.interactions],
            "pact_spec_version": self.pact_spec_version,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConsumerSpec":
        """Tạo ConsumerSpec từ dict."""
        raw_interactions = data.get("interactions", [])
        interactions = [Interaction.from_dict(i) for i in raw_interactions]
        return cls(
            id=data["id"],
            consumer_name=data.get("consumer_name", ""),
            provider_name=data.get("provider_name", ""),
            interactions=interactions,
            pact_spec_version=data.get("pact_spec_version", "2.0.0"),
            metadata=data.get("metadata", {}),
        )


# ===========================================================================
# ProviderVerifier
# ===========================================================================


@dataclass
class ProviderVerifier:
    """Cấu hình provider verification cho contract testing.

    Định nghĩa cách provider verify contracts từ các consumers,
    bao gồm Pact Broker URL, publish settings, tags, và consumer
    version selectors.

    Attributes:
        id: ID duy nhất của provider verifier
        provider_name: Tên provider service
        pact_broker_url: URL của Pact Broker
        publish_verification_results: Có publish kết quả verification không
        tags: Danh sách tags cho provider version
        consumer_version_selectors: Consumer version selectors để determine pacts
    """
    id: str
    provider_name: str
    pact_broker_url: str = ""
    publish_verification_results: bool = False
    tags: list[str] = field(default_factory=list)
    consumer_version_selectors: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate ProviderVerifier sau khi khởi tạo."""
        if not self.id or not self.id.strip():
            raise EM.raise_error(
                ErrorCode.INVALID_ID,
                reason="ProviderVerifier.id bắt buộc và không được để trống",
            )
        if not self.provider_name or not self.provider_name.strip():
            raise EM.raise_error(
                ErrorCode.INVALID_INPUT,
                reason="ProviderVerifier.provider_name bắt buộc và không được để trống",
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển ProviderVerifier sang dict."""
        return {
            "id": self.id,
            "provider_name": self.provider_name,
            "pact_broker_url": self.pact_broker_url,
            "publish_verification_results": self.publish_verification_results,
            "tags": self.tags,
            "consumer_version_selectors": self.consumer_version_selectors,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProviderVerifier":
        """Tạo ProviderVerifier từ dict."""
        return cls(
            id=data["id"],
            provider_name=data.get("provider_name", ""),
            pact_broker_url=data.get("pact_broker_url", ""),
            publish_verification_results=data.get("publish_verification_results", False),
            tags=data.get("tags", []),
            consumer_version_selectors=data.get("consumer_version_selectors", []),
        )


# ===========================================================================
# PactBrokerConfig
# ===========================================================================


@dataclass
class PactBrokerConfig:
    """Cấu hình Pact Broker cho contract sharing.

    Định nghĩa kết nối đến Pact Broker — nơi lưu trữ và chia sẻ
    contracts giữa consumers và providers.

    Attributes:
        id: ID duy nhất của broker config
        url: URL của Pact Broker
        auth_token: Authentication token cho broker
        project: Tên project trên broker
        tags: Danh sách tags cho contract versions
        auto_publish: Có tự động publish contracts không
    """
    id: str
    url: str = ""
    auth_token: str = ""
    project: str = ""
    tags: list[str] = field(default_factory=list)
    auto_publish: bool = False

    def __post_init__(self) -> None:
        """Validate PactBrokerConfig sau khi khởi tạo."""
        if not self.id or not self.id.strip():
            raise EM.raise_error(
                ErrorCode.INVALID_ID,
                reason="PactBrokerConfig.id bắt buộc và không được để trống",
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển PactBrokerConfig sang dict."""
        return {
            "id": self.id,
            "url": self.url,
            "auth_token": self.auth_token,
            "project": self.project,
            "tags": self.tags,
            "auto_publish": self.auto_publish,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PactBrokerConfig":
        """Tạo PactBrokerConfig từ dict."""
        return cls(
            id=data["id"],
            url=data.get("url", ""),
            auth_token=data.get("auth_token", ""),
            project=data.get("project", ""),
            tags=data.get("tags", []),
            auto_publish=data.get("auto_publish", False),
        )
