# coding: utf-8
"""
Mô-đun recipes cho CP64 — API Contract Testing (Pact).

Cung cấp các recipe để build ContractIR cho các use case phổ biến:
- basic_contract_recipe: Basic consumer-driven contract cho REST API
- full_pact_flow_recipe: Full Pact flow với broker, auto-publish, provider verification
- multi_consumer_recipe: Multiple consumers đối với single provider

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from midicoder.packs.cp64_contract_testing.parser import (
    ContractIR,
    parse_to_ir,
)


@dataclass
class RecipeOutput:
    """Kết quả từ recipe builder.

    Attributes:
        name: Tên recipe
        description: Mô tả recipe
        ir: ContractIR đã build
        raw_data: Raw DSL dict
    """
    name: str
    description: str
    ir: ContractIR
    raw_data: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Chuyển RecipeOutput sang dict."""
        return {
            "name": self.name,
            "description": self.description,
            "ir": self.ir.to_dict(),
            "raw_data": self.raw_data,
        }


def basic_contract_recipe() -> RecipeOutput:
    """Recipe: Basic consumer-driven contract cho REST API.

    Thiết lập contract testing cơ bản giữa một consumer và một provider.
    Consumer định nghĩa các interactions (request/response) mà nó mong
    đợi từ provider. Pact sẽ mock provider trong consumer tests và
    verify contracts trong provider tests.

    Cấu hình:
    - 1 ConsumerSpec: OrderService (consumer) -> OrderAPI (provider)
    - 2 Interactions: GET /orders/{id} và POST /orders
    - Pact spec version: 2.0.0
    - Không có broker (file-based pact)

    Returns:
        RecipeOutput chứa ContractIR
    """
    data = {
        "consumer_specs": [
            {
                "id": "orders_consumer",
                "consumer_name": "OrderService",
                "provider_name": "OrderAPI",
                "pact_spec_version": "2.0.0",
                "interactions": [
                    {
                        "id": "get_order_by_id",
                        "description": "GET order by ID",
                        "provider_state": "order exists with id 123",
                        "request": {
                            "method": "GET",
                            "path": "/orders/123",
                            "headers": {"Content-Type": "application/json"},
                        },
                        "response": {
                            "status": 200,
                            "headers": {"Content-Type": "application/json"},
                            "body": {
                                "id": 123,
                                "status": "confirmed",
                                "total": 99.99,
                            },
                        },
                    },
                    {
                        "id": "create_order",
                        "description": "POST create new order",
                        "provider_state": "user has valid payment method",
                        "request": {
                            "method": "POST",
                            "path": "/orders",
                            "headers": {"Content-Type": "application/json"},
                            "body": {
                                "item_id": "prod-456",
                                "quantity": 2,
                            },
                        },
                        "response": {
                            "status": 201,
                            "headers": {"Content-Type": "application/json"},
                            "body": {
                                "id": 124,
                                "status": "pending",
                                "total": 49.99,
                            },
                        },
                    },
                ],
            }
        ],
        "default_pact_version": "2.0.0",
        "enable_auto_publish": False,
    }

    ir = parse_to_ir(data)

    return RecipeOutput(
        name="basic_contract_recipe",
        description="Basic consumer-driven contract — OrderService -> OrderAPI với 2 interactions",
        ir=ir,
        raw_data=data,
    )


def full_pact_flow_recipe() -> RecipeOutput:
    """Recipe: Full Pact flow với broker, auto-publish, provider verification.

    Thiết lập Pact flow hoàn chỉnh bao gồm:
    - Consumer defines contracts và publish lên Pact Broker
    - Provider verify contracts từ broker
    - Auto-publish verification results
    - Consumer version selectors để determine nào cần verify

    Cấu hình:
    - 1 ConsumerSpec: WebApp -> UserService
    - 1 ProviderVerifier: UserService verify contracts từ broker
    - 1 PactBrokerConfig: broker.pactflow.io
    - Auto-publish: bật
    - Consumer version selectors: chỉ verify major versions mới nhất

    Returns:
        RecipeOutput chứa ContractIR
    """
    data = {
        "consumer_specs": [
            {
                "id": "webapp_user_contract",
                "consumer_name": "WebApp",
                "provider_name": "UserService",
                "pact_spec_version": "2.0.0",
                "interactions": [
                    {
                        "id": "get_user_profile",
                        "description": "GET user profile by ID",
                        "provider_state": "user with id 42 exists",
                        "request": {
                            "method": "GET",
                            "path": "/users/42",
                            "headers": {"Content-Type": "application/json", "Authorization": "Bearer token123"},
                        },
                        "response": {
                            "status": 200,
                            "headers": {"Content-Type": "application/json"},
                            "body": {
                                "id": 42,
                                "email": "user@example.com",
                                "display_name": "John Doe",
                                "role": "admin",
                            },
                        },
                    },
                    {
                        "id": "update_user_profile",
                        "description": "PUT update user profile",
                        "provider_state": "user with id 42 exists",
                        "request": {
                            "method": "PUT",
                            "path": "/users/42",
                            "headers": {"Content-Type": "application/json"},
                            "body": {
                                "display_name": "Jane Doe",
                                "email": "jane@example.com",
                            },
                        },
                        "response": {
                            "status": 200,
                            "headers": {"Content-Type": "application/json"},
                            "body": {
                                "id": 42,
                                "email": "jane@example.com",
                                "display_name": "Jane Doe",
                                "role": "admin",
                            },
                        },
                    },
                ],
            }
        ],
        "provider_verifiers": [
            {
                "id": "user_service_verifier",
                "provider_name": "UserService",
                "pact_broker_url": "https://broker.pactflow.io",
                "publish_verification_results": True,
                "tags": ["main", "v1.0.0"],
                "consumer_version_selectors": [
                    {"consumer": "WebApp", "version": "latest", "main_branch": True},
                ],
            }
        ],
        "pact_broker_config": {
            "id": "pactflow_broker",
            "url": "https://broker.pactflow.io",
            "auth_token": "${PACT_BROKER_TOKEN}",
            "project": "my-org",
            "tags": ["production"],
            "auto_publish": True,
        },
        "default_pact_version": "2.0.0",
        "enable_auto_publish": True,
    }

    ir = parse_to_ir(data)

    return RecipeOutput(
        name="full_pact_flow_recipe",
        description="Full Pact flow — WebApp -> UserService với broker, auto-publish, provider verification",
        ir=ir,
        raw_data=data,
    )


def multi_consumer_recipe() -> RecipeOutput:
    """Recipe: Multiple consumers đối với single provider.

    Thiết lập contract testing với nhiều consumers cùng phụ thuộc
    vào một provider duy nhất. Provider verification sẽ verify
    contracts từ tất cả consumers để đảm bảo backward compatibility.

    Cấu hình:
    - 3 ConsumerSpecs: WebApp, MobileApp, AdminDashboard -> PaymentService
    - 1 ProviderVerifier: PaymentService verify tất cả contracts
    - Pact Broker: broker.pactflow.io
    - Auto-publish: bật

    Returns:
        RecipeOutput chứa ContractIR
    """
    data = {
        "consumer_specs": [
            {
                "id": "webapp_payment_contract",
                "consumer_name": "WebApp",
                "provider_name": "PaymentService",
                "pact_spec_version": "2.0.0",
                "interactions": [
                    {
                        "id": "web_charge_payment",
                        "description": "POST charge payment (web)",
                        "provider_state": "valid card on file",
                        "request": {
                            "method": "POST",
                            "path": "/payments/charge",
                            "headers": {"Content-Type": "application/json"},
                            "body": {
                                "amount": 100.00,
                                "currency": "USD",
                                "card_token": "tok_123",
                            },
                        },
                        "response": {
                            "status": 200,
                            "headers": {"Content-Type": "application/json"},
                            "body": {
                                "payment_id": "pay_abc",
                                "status": "succeeded",
                                "amount": 100.00,
                            },
                        },
                    },
                ],
            },
            {
                "id": "mobile_payment_contract",
                "consumer_name": "MobileApp",
                "provider_name": "PaymentService",
                "pact_spec_version": "2.0.0",
                "interactions": [
                    {
                        "id": "mobile_refund_payment",
                        "description": "POST refund payment (mobile)",
                        "provider_state": "payment exists and is succeeded",
                        "request": {
                            "method": "POST",
                            "path": "/payments/refund",
                            "headers": {"Content-Type": "application/json"},
                            "body": {
                                "payment_id": "pay_abc",
                                "amount": 50.00,
                                "reason": "customer_request",
                            },
                        },
                        "response": {
                            "status": 200,
                            "headers": {"Content-Type": "application/json"},
                            "body": {
                                "refund_id": "ref_123",
                                "status": "pending",
                                "amount": 50.00,
                            },
                        },
                    },
                ],
            },
            {
                "id": "admin_payment_contract",
                "consumer_name": "AdminDashboard",
                "provider_name": "PaymentService",
                "pact_spec_version": "2.0.0",
                "interactions": [
                    {
                        "id": "admin_list_payments",
                        "description": "GET list payments (admin)",
                        "provider_state": "multiple payments exist",
                        "request": {
                            "method": "GET",
                            "path": "/payments",
                            "query": {"status": "succeeded", "page": "1"},
                        },
                        "response": {
                            "status": 200,
                            "headers": {"Content-Type": "application/json"},
                            "body": {
                                "payments": [
                                    {"payment_id": "pay_abc", "status": "succeeded", "amount": 100.00},
                                    {"payment_id": "pay_def", "status": "succeeded", "amount": 250.00},
                                ],
                                "total": 2,
                            },
                        },
                    },
                ],
            },
        ],
        "provider_verifiers": [
            {
                "id": "payment_service_verifier",
                "provider_name": "PaymentService",
                "pact_broker_url": "https://broker.pactflow.io",
                "publish_verification_results": True,
                "tags": ["main", "v2.0.0"],
                "consumer_version_selectors": [
                    {"consumer": "WebApp", "version": "latest", "main_branch": True},
                    {"consumer": "MobileApp", "version": "latest", "main_branch": True},
                    {"consumer": "AdminDashboard", "version": "latest", "main_branch": True},
                ],
            }
        ],
        "pact_broker_config": {
            "id": "pactflow_broker",
            "url": "https://broker.pactflow.io",
            "auth_token": "${PACT_BROKER_TOKEN}",
            "project": "my-org",
            "tags": ["production"],
            "auto_publish": True,
        },
        "default_pact_version": "2.0.0",
        "enable_auto_publish": True,
    }

    ir = parse_to_ir(data)

    return RecipeOutput(
        name="multi_consumer_recipe",
        description="Multi-consumer — WebApp, MobileApp, AdminDashboard -> PaymentService với unified verification",
        ir=ir,
        raw_data=data,
    )


__all__ = [
    "RecipeOutput",
    "basic_contract_recipe",
    "full_pact_flow_recipe",
    "multi_consumer_recipe",
]
