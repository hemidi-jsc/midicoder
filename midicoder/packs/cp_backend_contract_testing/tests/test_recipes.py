"""
Tests cho CP64 Contract Recipes.

Unit tests cho:
- basic_contract_recipe
- full_pact_flow_recipe
- multi_consumer_recipe

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from midicoder.packs.cp_backend_contract_testing.recipes import (
    RecipeOutput,
    basic_contract_recipe,
    full_pact_flow_recipe,
    multi_consumer_recipe,
)
from midicoder.packs.cp_backend_contract_testing.parser import ContractIR


# ===========================================================================
# Test RecipeOutput
# ===========================================================================


class TestRecipeOutput:
    """Tests cho RecipeOutput dataclass."""

    def test_create(self):
        ir = ContractIR()
        ro = RecipeOutput(
            name="test",
            description="Test recipe",
            ir=ir,
            raw_data={},
        )
        assert ro.name == "test"
        assert ro.description == "Test recipe"
        assert isinstance(ro.ir, ContractIR)
        assert ro.raw_data == {}

    def test_to_dict(self):
        ir = ContractIR()
        ro = RecipeOutput(
            name="test",
            description="Test",
            ir=ir,
            raw_data={"key": "val"},
        )
        d = ro.to_dict()
        assert d["name"] == "test"
        assert d["description"] == "Test"
        assert isinstance(d["ir"], dict)
        assert d["raw_data"]["key"] == "val"


# ===========================================================================
# Test basic_contract_recipe
# ===========================================================================


class TestBasicContractRecipe:
    """Tests cho basic_contract_recipe."""

    def test_returns_recipe_output(self):
        ro = basic_contract_recipe()
        assert isinstance(ro, RecipeOutput)
        assert ro.name == "basic_contract_recipe"
        assert "consumer-driven contract" in ro.description

    def test_has_valid_ir(self):
        ro = basic_contract_recipe()
        ir = ro.ir
        assert isinstance(ir, ContractIR)
        assert len(ir.consumer_specs) == 1

    def test_consumer_spec(self):
        ro = basic_contract_recipe()
        spec = ro.ir.consumer_specs[0]
        assert spec.id == "orders_consumer"
        assert spec.consumer_name == "OrderService"
        assert spec.provider_name == "OrderAPI"
        assert spec.pact_spec_version == "2.0.0"

    def test_interactions(self):
        ro = basic_contract_recipe()
        spec = ro.ir.consumer_specs[0]
        assert len(spec.interactions) == 2

        get_int = spec.interactions[0]
        assert get_int.id == "get_order_by_id"
        assert get_int.request.method == "GET"
        assert get_int.response.status == 200

        post_int = spec.interactions[1]
        assert post_int.id == "create_order"
        assert post_int.request.method == "POST"
        assert post_int.response.status == 201

    def test_no_provider_verifiers(self):
        ro = basic_contract_recipe()
        assert ro.ir.provider_verifiers == []

    def test_no_broker(self):
        ro = basic_contract_recipe()
        assert ro.ir.pact_broker_config is None

    def test_no_auto_publish(self):
        ro = basic_contract_recipe()
        assert ro.ir.enable_auto_publish is False

    def test_raw_data_populated(self):
        ro = basic_contract_recipe()
        assert "consumer_specs" in ro.raw_data
        assert len(ro.raw_data["consumer_specs"]) == 1


# ===========================================================================
# Test full_pact_flow_recipe
# ===========================================================================


class TestFullPactFlowRecipe:
    """Tests cho full_pact_flow_recipe."""

    def test_returns_recipe_output(self):
        ro = full_pact_flow_recipe()
        assert isinstance(ro, RecipeOutput)
        assert ro.name == "full_pact_flow_recipe"

    def test_has_valid_ir(self):
        ro = full_pact_flow_recipe()
        ir = ro.ir
        assert isinstance(ir, ContractIR)
        assert len(ir.consumer_specs) >= 1

    def test_consumer_spec(self):
        ro = full_pact_flow_recipe()
        spec = ro.ir.consumer_specs[0]
        assert spec.consumer_name == "WebApp"
        assert spec.provider_name == "UserService"

    def test_has_provider_verifier(self):
        ro = full_pact_flow_recipe()
        assert len(ro.ir.provider_verifiers) == 1
        pv = ro.ir.provider_verifiers[0]
        assert pv.provider_name == "UserService"
        assert pv.publish_verification_results is True

    def test_has_pact_broker(self):
        ro = full_pact_flow_recipe()
        broker = ro.ir.pact_broker_config
        assert broker is not None
        assert "broker.pactflow.io" in broker.url
        assert broker.auto_publish is True

    def test_auto_publish_enabled(self):
        ro = full_pact_flow_recipe()
        assert ro.ir.enable_auto_publish is True

    def test_consumer_version_selectors(self):
        ro = full_pact_flow_recipe()
        pv = ro.ir.provider_verifiers[0]
        assert len(pv.consumer_version_selectors) == 1
        assert pv.consumer_version_selectors[0]["consumer"] == "WebApp"

    def test_interactions_have_provider_state(self):
        ro = full_pact_flow_recipe()
        spec = ro.ir.consumer_specs[0]
        for interaction in spec.interactions:
            assert interaction.provider_state  # không rỗng


# ===========================================================================
# Test multi_consumer_recipe
# ===========================================================================


class TestMultiConsumerRecipe:
    """Tests cho multi_consumer_recipe."""

    def test_returns_recipe_output(self):
        ro = multi_consumer_recipe()
        assert isinstance(ro, RecipeOutput)
        assert ro.name == "multi_consumer_recipe"

    def test_multiple_consumer_specs(self):
        ro = multi_consumer_recipe()
        assert len(ro.ir.consumer_specs) == 3

    def test_different_consumers(self):
        ro = multi_consumer_recipe()
        names = {s.consumer_name for s in ro.ir.consumer_specs}
        assert "WebApp" in names
        assert "MobileApp" in names
        assert "AdminDashboard" in names

    def test_same_provider(self):
        ro = multi_consumer_recipe()
        for spec in ro.ir.consumer_specs:
            assert spec.provider_name == "PaymentService"

    def test_has_provider_verifier(self):
        ro = multi_consumer_recipe()
        assert len(ro.ir.provider_verifiers) == 1
        pv = ro.ir.provider_verifiers[0]
        assert pv.provider_name == "PaymentService"

    def test_multiple_consumer_version_selectors(self):
        ro = multi_consumer_recipe()
        pv = ro.ir.provider_verifiers[0]
        assert len(pv.consumer_version_selectors) == 3

    def test_has_pact_broker(self):
        ro = multi_consumer_recipe()
        broker = ro.ir.pact_broker_config
        assert broker is not None
        assert broker.auto_publish is True

    def test_auto_publish_enabled(self):
        ro = multi_consumer_recipe()
        assert ro.ir.enable_auto_publish is True

    def test_each_consumer_has_interactions(self):
        ro = multi_consumer_recipe()
        for spec in ro.ir.consumer_specs:
            assert len(spec.interactions) >= 1

    def test_different_interaction_ids(self):
        ro = multi_consumer_recipe()
        all_ids = []
        for spec in ro.ir.consumer_specs:
            for interaction in spec.interactions:
                all_ids.append(interaction.id)
        assert len(all_ids) == len(set(all_ids))  # tất cả IDs khác nhau


# ===========================================================================
# Cross-recipe integration
# ===========================================================================


class TestRecipeIntegration:
    """Integration tests cho recipe ecosystem."""

    def test_all_recipes_return_valid_ir(self):
        """Tất cả recipes phải trả về valid ContractIR."""
        for recipe_fn in [basic_contract_recipe, full_pact_flow_recipe, multi_consumer_recipe]:
            ro = recipe_fn()
            assert isinstance(ro, RecipeOutput)
            assert isinstance(ro.ir, ContractIR)
            assert ro.ir.consumer_specs

    def test_recipes_can_be_serialized(self):
        """Tất cả recipes phải có thể serialize và deserialize."""
        for recipe_fn in [basic_contract_recipe, full_pact_flow_recipe, multi_consumer_recipe]:
            ro = recipe_fn()
            d = ro.ir.to_dict()
            restored = ContractIR.from_dict(d)
            assert len(restored.consumer_specs) == len(ro.ir.consumer_specs)

    def test_full_and_multi_have_broker(self):
        """Full và multi recipe phải có Pact Broker."""
        assert full_pact_flow_recipe().ir.pact_broker_config is not None
        assert multi_consumer_recipe().ir.pact_broker_config is not None

    def test_basic_has_no_broker(self):
        """Basic recipe không cần broker (file-based)."""
        assert basic_contract_recipe().ir.pact_broker_config is None
