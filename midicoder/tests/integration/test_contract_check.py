from __future__ import annotations

from pathlib import Path

from midicoder.tests.conftest import assert_cli_success, run_cli, write_minimal_contracts


# Happy-path: với bộ contracts tối thiểu, lệnh `contract check` phải chạy thành công
def test_contract_check_with_minimal_contracts(tmp_workdir: Path) -> None:
    init_result = run_cli(["init"], tmp_workdir)
    assert_cli_success(init_result)

    version = "0.1.0"
    version_result = run_cli(["version", "create", version], tmp_workdir)
    assert_cli_success(version_result)

    write_minimal_contracts(tmp_workdir, version)

    check_result = run_cli(["contract", "check"], tmp_workdir)
    assert_cli_success(check_result)


# Negative-case 1: nếu thiếu file bắt buộc (errors.yaml) thì `contract check` phải fail
def test_contract_check_fails_on_missing_files(tmp_workdir: Path) -> None:
    init_result = run_cli(["init"], tmp_workdir)
    assert_cli_success(init_result)

    version = "0.1.0"
    version_result = run_cli(["version", "create", version], tmp_workdir)
    assert_cli_success(version_result)

    contracts_root = write_minimal_contracts(tmp_workdir, version)
    (contracts_root / "domain" / "errors.yaml").unlink()

    check_result = run_cli(["contract", "check"], tmp_workdir)
    assert check_result.returncode != 0


# Negative-case 2: nếu cấu trúc file không tuân theo schema (thiếu fields bắt buộc)
# thì `contract check` phải phát hiện lỗi và trả về mã lỗi khác 0
def test_contract_check_fails_on_invalid_schema(tmp_workdir: Path) -> None:
    init_result = run_cli(["init"], tmp_workdir)
    assert_cli_success(init_result)

    version = "0.1.0"
    version_result = run_cli(["version", "create", version], tmp_workdir)
    assert_cli_success(version_result)

    contracts_root = write_minimal_contracts(tmp_workdir, version)
    (contracts_root / "app" / "commands.yaml").write_text(
        """
commands:
  - id: CreateOrder
    fetches: []
""".lstrip(),
        encoding="utf-8",
    )

    check_result = run_cli(["contract", "check"], tmp_workdir)
    assert check_result.returncode != 0


def test_contract_check_flags_unknown_required_role(tmp_workdir: Path) -> None:
    init_result = run_cli(["init"], tmp_workdir)
    assert_cli_success(init_result)

    version = "0.1.0"
    version_result = run_cli(["version", "create", version], tmp_workdir)
    assert_cli_success(version_result)

    contracts_root = write_minimal_contracts(tmp_workdir, version)
    commands_path = contracts_root / "app" / "commands.yaml"
    commands_path.write_text(
        """
commands:
  - id: CreateOrder
    description: "create order"
    input:
      - name: order_id
        type: uuid
    fetches: []
    guards: []
    effects: []
    errors: []
    returns: []
    required_roles: ["finance_manager"]
""".lstrip(),
        encoding="utf-8",
    )
    policy_dir = contracts_root / "policy"
    policy_dir.mkdir(parents=True, exist_ok=True)
    (policy_dir / "rbac.yaml").write_text(
        """
access:
  roles:
    - id: admin
      description: "system admin"
  permissions: []
  bindings: []
""".lstrip(),
        encoding="utf-8",
    )

    check_result = run_cli(["contract", "check"], tmp_workdir)
    assert check_result.returncode != 0


def test_contract_check_requires_typed_secret_refs(tmp_workdir: Path) -> None:
    init_result = run_cli(["init"], tmp_workdir)
    assert_cli_success(init_result)

    version = "0.1.0"
    version_result = run_cli(["version", "create", version], tmp_workdir)
    assert_cli_success(version_result)

    contracts_root = write_minimal_contracts(tmp_workdir, version)

    secrets_dir = contracts_root / "secrets"
    secrets_dir.mkdir(parents=True, exist_ok=True)
    (secrets_dir / "secrets.yaml").write_text(
        """
secrets:
  - id: BillingApiKey
    provider: env
    key: BILLING_API_KEY
""".lstrip(),
        encoding="utf-8",
    )

    integrations_dir = contracts_root / "integrations"
    integrations_dir.mkdir(parents=True, exist_ok=True)
    integrations_file = integrations_dir / "integrations.yaml"
    integrations_file.write_text(
        """
integrations:
  - id: BillingGateway
    type: rest_api
    provider: aws
    service: lambda
    auth:
      type: api_key
      secret_ref: BillingApiKey
operations:
  - id: ChargeCustomer
    integration_id: BillingGateway
    method: POST
    path: /charge
""".lstrip(),
        encoding="utf-8",
    )

    bad_result = run_cli(["contract", "check"], tmp_workdir)
    assert bad_result.returncode != 0
    combined_output = f"{bad_result.stdout}\n{bad_result.stderr}"
    assert "typed format 'Secret:<id>'" in combined_output

    integrations_file.write_text(
        """
integrations:
  - id: BillingGateway
    type: rest_api
    provider: aws
    service: lambda
    auth:
      type: api_key
      secret_ref: Secret:BillingApiKey
operations:
  - id: ChargeCustomer
    integration_id: BillingGateway
    method: POST
    path: /charge
""".lstrip(),
        encoding="utf-8",
    )

    good_result = run_cli(["contract", "check"], tmp_workdir)
    assert_cli_success(good_result)


def test_contract_check_flags_unknown_workflow_scenario(tmp_workdir: Path) -> None:
    init_result = run_cli(["init"], tmp_workdir)
    assert_cli_success(init_result)

    version = "0.1.0"
    version_result = run_cli(["version", "create", version], tmp_workdir)
    assert_cli_success(version_result)

    contracts_root = write_minimal_contracts(tmp_workdir, version)
    workflow_dir = contracts_root / "workflows"
    workflow_dir.mkdir(parents=True, exist_ok=True)
    (workflow_dir / "workflows.yaml").write_text(
        """
workflows:
  - id: OrderFlow
    entity: Order
    states:
      - id: start
    transitions:
      - from_state: start
        to_state: start
        on_command: CreateOrder
        guards: []
        effects: []
    initial_state: start
    error_handlers: []
    scenarios: ["DemoScenario"]
""".lstrip(),
        encoding="utf-8",
    )

    check_result = run_cli(["contract", "check"], tmp_workdir)
    assert check_result.returncode != 0
    assert "scenarios references unknown scenario" in (check_result.stdout + check_result.stderr)


def test_contract_check_flags_unknown_rule_scenario(tmp_workdir: Path) -> None:
    init_result = run_cli(["init"], tmp_workdir)
    assert_cli_success(init_result)

    version = "0.1.0"
    version_result = run_cli(["version", "create", version], tmp_workdir)
    assert_cli_success(version_result)

    contracts_root = write_minimal_contracts(tmp_workdir, version)
    scenarios_dir = contracts_root / "scenarios"
    scenarios_dir.mkdir(parents=True, exist_ok=True)
    (scenarios_dir / "scenarios.yaml").write_text(
        """
scenarios:
  - id: CheckoutHappyPath
    steps: []
""".lstrip(),
        encoding="utf-8",
    )

    (contracts_root / "rules" / "rules.yaml").write_text(
        """
rules:
  - id: RuleCreateOrder
    applies_to: CreateOrder
    applies_to_scenario: DemoScenario
    rows: []
""".lstrip(),
        encoding="utf-8",
    )

    check_result = run_cli(["contract", "check"], tmp_workdir)
    assert check_result.returncode != 0
    assert "applies_to_scenario references unknown scenario" in (check_result.stdout + check_result.stderr)


def test_contract_check_flags_invalid_persistence_links(tmp_workdir: Path) -> None:
    init_result = run_cli(["init"], tmp_workdir)
    assert_cli_success(init_result)

    version = "0.1.0"
    version_result = run_cli(["version", "create", version], tmp_workdir)
    assert_cli_success(version_result)

    contracts_root = write_minimal_contracts(tmp_workdir, version)
    persistence_dir = contracts_root / "persistence"
    persistence_dir.mkdir(parents=True, exist_ok=True)
    (persistence_dir / "model.yaml").write_text(
        """
datasources:
  - id: main_db
    engine: postgres
    integration_id: Integration:UnknownIntegration
tables:
  - id: orders_projection
    datasource: main_db
    operation_id: IntegrationOperation:MissingOp
    columns:
      - name: id
        type: uuid
""".lstrip(),
        encoding="utf-8",
    )

    check_result = run_cli(["contract", "check"], tmp_workdir)
    assert check_result.returncode != 0
    combined_output = check_result.stdout + check_result.stderr
    assert "integration_id references unknown integration" in combined_output
    assert "operation_id references unknown integration operation" in combined_output
