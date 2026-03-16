from __future__ import annotations

from midicoder.dsl.schemas.observability_model import ObservabilityTarget
from midicoder.dsl.schemas.reliability_model import ReliabilityPolicy
from midicoder.dsl.schemas.scenario_model import Scenario, ScenarioStep
from midicoder.dsl.schemas.testing_model import ContractTestCase, ContractTestStep
from midicoder.ir.builder.builder import (
    _build_contract_test_case_ir,
    _build_observability_target_ir,
    _build_reliability_policy_ir,
    _build_scenario_ir,
)
from midicoder.ir.normalize.normalizer import Normalizer
from midicoder.ir.symbols.symbol_table import SymbolTable


def _normalizer() -> Normalizer:
    return Normalizer(SymbolTable())


def test_reliability_ir_supports_integration_operation_target() -> None:
    policy = ReliabilityPolicy(
        id="RetryCharge",
        target_kind="integration_operation",
        target_ref="IntegrationOperation:ChargeCustomer",
    )

    ir = _build_reliability_policy_ir(policy, "policy/reliability.yaml", "abc", _normalizer())

    assert ir.target_ref.type == "IntegrationOperation"
    assert ir.target_ref.id == "charge_customer"


def test_observability_ir_supports_persistence_targets() -> None:
    table_target = ObservabilityTarget(kind="persistence.table", ref="PersistenceTable:orders")
    datasource_target = ObservabilityTarget(
        kind="persistence.datasource",
        ref="PersistenceDatasource:main_db",
    )

    table_ir = _build_observability_target_ir(table_target, "ops/observability.yaml", "abc", _normalizer())
    datasource_ir = _build_observability_target_ir(
        datasource_target,
        "ops/observability.yaml",
        "abc",
        _normalizer(),
    )

    assert table_ir.ref.type == "PersistenceTable"
    assert table_ir.ref.id == "orders"
    assert datasource_ir.ref.type == "PersistenceDatasource"
    assert datasource_ir.ref.id == "main_db"


def test_scenario_ir_emits_actor_roles_typed_refs() -> None:
    scenario = Scenario(
        id="CheckoutHappyPath",
        actors=["legacy_actor"],
        actor_roles=["Role:tenant_admin", "support_agent"],
        steps=[ScenarioStep(type="command", ref="CreateOrder")],
    )

    ir = _build_scenario_ir(scenario, "scenarios/scenarios.yaml", "abc", _normalizer())

    assert [ref.type for ref in ir.actor_roles] == ["Role", "Role"]
    assert [ref.id for ref in ir.actor_roles] == ["tenant_admin", "support_agent"]


def test_scenario_model_backfills_actor_roles_from_legacy_actors() -> None:
    scenario = Scenario(
        id="LegacyScenario",
        actors=["tenant_admin"],
        steps=[ScenarioStep(type="command", ref="CreateOrder")],
    )
    assert scenario.actor_roles == ["tenant_admin"]


def test_scenario_ir_prioritizes_actor_roles_over_legacy_actors() -> None:
    scenario = Scenario(
        id="PriorityScenario",
        actors=["legacy_actor"],
        actor_roles=["Role:billing_admin"],
        steps=[ScenarioStep(type="command", ref="CreateOrder")],
    )

    ir = _build_scenario_ir(scenario, "scenarios/scenarios.yaml", "abc", _normalizer())

    assert [ref.id for ref in ir.actor_roles] == ["billing_admin"]


def test_contract_test_case_ir_emits_scenario_typed_ref() -> None:
    test_case = ContractTestCase(
        id="order_happy_path",
        kind="integration",
        scenario="Scenario:CheckoutHappyPath",
        steps=[ContractTestStep(type="command", ref="CreateOrder")],
    )

    ir = _build_contract_test_case_ir(test_case, "testing/tests.yaml", "abc", _normalizer())

    assert ir.scenario is not None
    assert ir.scenario.type == "Scenario"
    assert ir.scenario.id == "checkout_happy_path"
