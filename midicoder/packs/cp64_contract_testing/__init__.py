"""
CP64: API Contract Testing (Pact) Module.

Module này cung cấp các components cho Consumer-Driven Contract Testing:
- models.py: Contract data models (ConsumerSpec, Interaction, RequestMatch,
  ResponseStub, ProviderVerifier, PactBrokerConfig)
- parser.py: DSL parser cho Contract DSL
- recipes.py: Pattern recipes (basic_contract, full_pact_flow, multi_consumer)
- fastapi.py: FastAPI emitter cho Contract Testing code
- nestjs.py: NestJS emitter cho Contract Testing code

Capabilities: consumer_driven_contract, provider_verification

Author: Midicoder Team
Version: 1.0.0
"""

from midicoder.packs.cp64_contract_testing.models import (
    ContractType,
    MatchRule,
    ConsumerSpec,
    Interaction,
    RequestMatch,
    ResponseStub,
    ProviderVerifier,
    PactBrokerConfig,
)
from midicoder.packs.cp64_contract_testing.parser import (
    ContractIR,
    parse_consumer_specs,
    parse_provider_verifiers,
    parse_to_ir,
)
from midicoder.packs.cp64_contract_testing.recipes import (
    RecipeOutput,
    basic_contract_recipe,
    full_pact_flow_recipe,
    multi_consumer_recipe,
)
from midicoder.packs.cp64_contract_testing.fastapi import (
    FastAPIContractEmitter,
    GeneratedFile,
)
from midicoder.packs.cp64_contract_testing.nestjs import (
    NestJSContractEmitter,
)

__all__ = [
    # Enums
    "ContractType",
    "MatchRule",
    # Models
    "ConsumerSpec",
    "Interaction",
    "RequestMatch",
    "ResponseStub",
    "ProviderVerifier",
    "PactBrokerConfig",
    # Parser
    "ContractIR",
    "parse_consumer_specs",
    "parse_provider_verifiers",
    "parse_to_ir",
    # Recipes
    "RecipeOutput",
    "basic_contract_recipe",
    "full_pact_flow_recipe",
    "multi_consumer_recipe",
    # FastAPI Emitter
    "FastAPIContractEmitter",
    "GeneratedFile",
    # NestJS Emitter
    "NestJSContractEmitter",
]
