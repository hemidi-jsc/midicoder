"""IR builder for Midicoder contracts DSL.

New implementation using pipeline architecture:
1. Load contracts
2. Schema validation
3. Lint
4. Build symbol table
5. Cross-reference checking
6. Normalize
7. Build IR
8. Write outputs
"""

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..diagnostics.error_codes import ErrorReporter
from ..diagnostics.logging import header, log, safe_print
from ..normalize.normalizer import Normalizer
from ..schema.ir_schema import (
    IR,
    ApiIR,
    ApplicationIR,
    CircuitBreakerPolicyIR,
    CommandIR,
    ConstraintIR,
    ContractTestCaseIR,
    ContractTestStepIR,
    CorsPolicyIR,
    DomainIR,
    EffectIR,
    EmailProviderIR,
    EntityIR,
    EnumIR,
    EnvironmentProfileIR,
    ErrorHandlerIR,
    ErrorIR,
    ErrorMapIR,
    EventIR,
    FieldIR,
    GuardIR,
    HttpApiIR,
    HttpRouteIR,
    IndexIR,
    IntegrationAuthIR,
    IntegrationsIR,
    IntegrationTargetIR,
    IRIndexes,
    IRMeta,
    IRModules,
    OAuth2ProviderIR,
    ObservabilityTargetIR,
    OpsIR,
    PersistenceColumnIR,
    PersistenceDatasourceIR,
    PersistenceIndexIR,
    PersistenceIR,
    PersistenceTableIR,
    PiiMaskingRuleIR,
    PolicyIR,
    ProjectionIR,
    QueryIR,
    RateLimitPolicyIR,
    RateLimitRuleIR,
    RefIR,
    ReliabilityPolicyIR,
    RestApiOperationIR,
    RetryPolicyIR,
    RulesIR,
    S3ResourceIR,
    ScenariosIR,
    SecretRefIR,
    SecurityBaselineIR,
    SignaturePolicyIR,
    SourceMetadata,
    StateIR,
    Stats,
    TestingIR,
    TimeoutPolicyIR,
    TransitionIR,
    ValueObjectIR,
    Warning,
    WebhookEndpointIR,
    WorkflowIR,
    WorkflowModuleIR,
)
from ..symbols.symbol_table import (
    SYMBOL_TYPE_COMMAND,
    SYMBOL_TYPE_ENTITY,
    SYMBOL_TYPE_ENUM,
    SYMBOL_TYPE_ERROR,
    SYMBOL_TYPE_EVENT,
    SYMBOL_TYPE_INTEGRATION,
    SYMBOL_TYPE_INTEGRATION_OPERATION,
    SYMBOL_TYPE_PERMISSION,
    SYMBOL_TYPE_PERSISTENCE_DATASOURCE,
    SYMBOL_TYPE_PERSISTENCE_TABLE,
    SYMBOL_TYPE_PROJECTION,
    SYMBOL_TYPE_QUERY,
    SYMBOL_TYPE_RELIABILITY_POLICY,
    SYMBOL_TYPE_ROLE,
    SYMBOL_TYPE_RULE,
    SYMBOL_TYPE_SCENARIO,
    SYMBOL_TYPE_SECRET,
    SYMBOL_TYPE_TEST_CASE,
    SYMBOL_TYPE_VALUE_OBJECT,
    SYMBOL_TYPE_WORKFLOW,
    SymbolTable,
)
from ..validation.cross_ref import CrossRefChecker
from ..validation.validator import Validator


def _load_schema_tree(root: Path) -> dict[str, Any]:
    """Load schema tree from package resources."""
    try:
        from importlib.resources import files

        schema_tree_path = Path(str(files("midicoder.dsl.schemas")) + "/tree_v0.yml")
    except Exception:
        # Fallback to relative path
        schema_tree_path = root / "midicoder" / "dsl" / "schemas" / "tree_v0.yml"

    if not schema_tree_path.exists():
        # Try another fallback
        schema_tree_path = (
            Path(__file__).parent.parent.parent / "dsl" / "schemas" / "tree_v0.yml"
        )

    if not schema_tree_path.exists():
        log(
            "schema",
            "warn",
            f"Schema tree not found at {schema_tree_path}, using empty schema",
        )
        return {}

    try:
        from ruamel.yaml import YAML

        yaml_loader = YAML(typ="safe")
        content = schema_tree_path.read_text(encoding="utf-8")
        data = yaml_loader.load(content)
        if not isinstance(data, dict):
            log("schema", "warn", "Schema tree is not a dict, using empty schema")
            return {}
        log("schema", "ok", f"Loaded schema tree from {schema_tree_path}")
        return data
    except Exception as e:
        log("schema", "warn", f"Failed to load schema tree: {e}, using empty schema")
        return {}


def build_ir(
    version: str,
    repo_root: str | None = None,
    skip_diagrams: bool = False,
    sort_collections: bool = True,
) -> None:
    """
    Build IR from contracts.

    Args:
        version: Version to build
        repo_root: Repository root (default: cwd)
        skip_diagrams: If True, skip diagram generation
        sort_collections: If True (default), sort collections by ID for deterministic output.
                         If False, preserve source order.

    Raises:
        FileNotFoundError: If contracts directory doesn't exist
        RuntimeError: If compilation fails
    """
    header(f"IR BUILD v{version}")

    root = Path(repo_root or os.getcwd())

    # Load schema tree for dynamic intent inference
    log("schema", "start", "Loading schema tree")
    schema_tree = _load_schema_tree(root)
    contracts_root = root / ".midicoder" / "versions" / version / "contracts"
    ir_root = root / ".midicoder" / "versions" / version / "irs"
    manifest_path = ir_root / "manifest.json"
    ir_path = ir_root / "ir.json"

    if not contracts_root.is_dir():
        raise FileNotFoundError(
            f"Contracts directory not found at {contracts_root}. "
            "Run 'midicoder contract gen' first."
        )

    # Initialize error reporter
    reporter = ErrorReporter()

    # Phase 1: Load contracts
    log("load", "start", "Loading contracts")
    validated_data = {}
    try:
        validated_data = _load_and_validate_contracts(contracts_root, reporter)
    except Exception as e:
        reporter.add_exception("load", str(contracts_root), e)

    if reporter.has_errors():
        _write_manifest_with_errors(
            manifest_path, version, contracts_root, root, reporter
        )
        _write_error_report(ir_root, reporter, contracts_root)
        _print_build_report(reporter, contracts_root)
        raise RuntimeError("IR build failed due to validation errors.")

    log("load", "ok", "Loaded and validated contracts", files=len(validated_data))

    # Phase 2: Build symbol table
    log("symbols", "start", "Building symbol table")
    symbol_table = _build_symbol_table(validated_data, reporter, contracts_root)

    if reporter.has_errors():
        _write_manifest_with_errors(
            manifest_path, version, contracts_root, root, reporter
        )
        _write_error_report(ir_root, reporter, contracts_root)
        _print_build_report(reporter, contracts_root)
        raise RuntimeError("IR build failed due to duplicate symbols.")

    stats = symbol_table.get_stats()
    total_symbols = sum(stats.values())
    log("symbols", "ok", "Built symbol table", total=total_symbols)

    # Phase 3: Cross-reference checking
    log("xref", "start", "Checking cross-references")
    _check_cross_references(validated_data, symbol_table, reporter)

    if reporter.has_errors():
        _write_manifest_with_errors(
            manifest_path, version, contracts_root, root, reporter
        )
        _write_error_report(ir_root, reporter, contracts_root)
        _print_build_report(reporter, contracts_root)
        raise RuntimeError("IR build failed due to unresolved references.")

    log("xref", "ok", "All cross-references resolved")

    # Phase 4: Normalize
    log("normalize", "start", "Normalizing contracts")
    normalizer = Normalizer(symbol_table)

    # Phase 5: Build IR
    log("ir", "start", "Building IR")
    ir = _build_ir_structure(
        validated_data,
        symbol_table,
        normalizer,
        version,
        contracts_root,
        sort_collections,
        schema_tree,
    )

    # Phase 5.5: Intent.module inference
    from ..analysis.intent import apply_intent_module

    apply_intent_module(ir, validated_data, normalizer, reporter, schema_tree)

    # Phase 5.6: Intent validation
    from ..analysis.intent import validate_intents

    validate_intents(ir, validated_data, normalizer, reporter)

    # Optional: intent statistics
    from ..analysis.intent import (
        compute_confidence_distribution,
        compute_intent_stats,
        compute_intent_summary,
    )

    ir.meta.intent = compute_intent_stats(ir)
    ir.meta.intent_summary = compute_intent_summary(ir)
    ir.meta.confidence_distribution = compute_confidence_distribution(ir)

    # Attach warnings to IR metadata
    ir.meta.warnings = _build_meta_warnings(reporter)

    if reporter.has_errors():
        _write_manifest_with_errors(
            manifest_path, version, contracts_root, root, reporter
        )
        _write_error_report(ir_root, reporter, contracts_root)
        _print_build_report(reporter, contracts_root)
        raise RuntimeError("IR build failed due to intent errors.")

    # Phase 6: Write outputs
    log("output", "start", "Writing IR")
    ir_root.mkdir(parents=True, exist_ok=True)
    _write_ir(ir, ir_path, symbol_table)

    log("output", "start", "Writing manifest")
    manifest = _build_manifest(version, contracts_root, ir_root, root, ir, reporter)
    _write_manifest(manifest, manifest_path)

    # Phase 7: Generate diagrams
    log("diagrams", "start", "Generating diagrams")
    diagram_manifest = None
    if not skip_diagrams:
        from ..visualize.visualizer import generate_diagrams

        diagrams_dir = ir_root / "diagrams_mermaid"
        diagram_manifest = generate_diagrams(ir, diagrams_dir, skip_diagrams)

        diagram_manifest_path = diagrams_dir / "manifest.json"
        diagram_manifest.write(diagram_manifest_path)
        log(
            "diagrams",
            "ok",
            "Generated diagrams",
            total=diagram_manifest.to_dict()["total"],
        )
    else:
        log("diagrams", "skip", "Skipping diagram generation")

    # Write lock file
    locks_root = root / ".midicoder" / "versions" / version / "locks"
    locks_root.mkdir(parents=True, exist_ok=True)
    _write_json(
        locks_root / "contracts.lock",
        {
            "version": version,
            "locked_at": _utc_now(),
            "ir": str(ir_path.relative_to(root)),
        },
    )

    # Write error/warning log (even on success, to capture warnings)
    if reporter.has_errors() or len(reporter.warnings) > 0 or len(reporter.infos) > 0:
        _write_error_report(ir_root, reporter, contracts_root)
        _print_build_report(reporter, contracts_root)

    # Print summary
    safe_print("")
    header("SUMMARY")
    summary_items = [
        ("Entities", ir.meta.stats.entities),
        ("Value Objects", ir.meta.stats.value_objects),
        ("Enums", ir.meta.stats.enums),
        ("Errors", ir.meta.stats.errors),
        ("Events", ir.meta.stats.events),
        ("Commands", ir.meta.stats.commands),
        ("Queries", ir.meta.stats.queries),
        ("Projections", ir.meta.stats.projections),
        ("Workflows", ir.meta.stats.workflows),
        ("Rules", ir.meta.stats.rules),
        ("Scenarios", ir.meta.stats.scenarios),
        ("HTTP Routes", ir.meta.stats.http_routes),
        ("GraphQL Types", ir.meta.stats.graphql_types),
        ("Roles", ir.meta.stats.roles),
        ("Permissions", ir.meta.stats.permissions),
        ("Policies", ir.meta.stats.policies),
        ("DataSources", ir.meta.stats.persistence_datasources),
        ("Tables", ir.meta.stats.persistence_tables),
        ("Integrations", ir.meta.stats.integrations),
        ("Ops", ir.meta.stats.integration_operations),
        ("Webhooks", ir.meta.stats.webhooks),
        ("Profiles", ir.meta.stats.profiles),
        ("Secrets", ir.meta.stats.secrets),
        ("Reliability", ir.meta.stats.reliability_policies),
        ("Observability", ir.meta.stats.observability_targets),
        ("Tests", ir.meta.stats.tests),
        ("Total Symbols", total_symbols),
        ("Warnings", len(reporter.warnings)),
        ("Info", len(reporter.infos)),
    ]
    for key, value in summary_items:
        safe_print(f"  {key:<15} {value}")
    safe_print("-" * 60)
    safe_print(f"IR built successfully at {ir_path.relative_to(root)}")


def _load_and_validate_contracts(
    contracts_root: Path, reporter: ErrorReporter
) -> dict[str, Any]:
    """Load and validate all contract files."""
    validator = Validator(reporter)
    validated_data = {}

    # Walk through all contract files
    for file_path in sorted(contracts_root.rglob("*.yaml")) + sorted(
        contracts_root.rglob("*.yml")
    ):
        relative_path = file_path.relative_to(contracts_root)

        # Skip hidden files and directories
        if any(part.startswith(".") for part in relative_path.parts):
            continue

        # Validate file
        data = validator.validate_file(file_path, contracts_root)
        if data is not None:
            validated_data[str(relative_path)] = data

    return validated_data


def _build_symbol_table(
    validated_data: dict[str, Any],
    reporter: ErrorReporter,
    contracts_root: Path,
) -> SymbolTable:
    """Build symbol table from validated contracts."""
    from midicoder.dsl.models import (
        AccessPolicyFile,
        CommandsFile,
        EntitiesFile,
        EnumsFile,
        ErrorsFile,
        EventsFile,
        IntegrationsFile,
        PersistenceModelFile,
        ProjectionsFile,
        QueriesFile,
        ReliabilityPoliciesFile,
        RulesFile,
        ScenariosFile,
        SecretsContractFile,
        TestingFile,
        ValueObjectsFile,
        WorkflowsFile,
    )

    symbol_table = SymbolTable()
    normalizer = Normalizer(symbol_table)

    for file_path, data in validated_data.items():
        # Register symbols based on file type
        if isinstance(data, EntitiesFile):
            for entity in data.entities:
                canonical_id = normalizer.normalize_id(entity.id)
                success = symbol_table.register(
                    SYMBOL_TYPE_ENTITY,
                    canonical_id,
                    file_path,
                    entity,
                )
                if not success:
                    from ..diagnostics.error_codes import E201

                    reporter.add_error(
                        stage="symbol_table",
                        code=E201,
                        file=file_path,
                        message=f"Duplicate entity ID: {entity.id}",
                    )

        elif isinstance(data, ValueObjectsFile):
            for vo in data.value_objects:
                canonical_id = normalizer.normalize_id(vo.id)
                success = symbol_table.register(
                    SYMBOL_TYPE_VALUE_OBJECT,
                    canonical_id,
                    file_path,
                    vo,
                )
                if not success:
                    from ..diagnostics.error_codes import E201

                    reporter.add_error(
                        stage="symbol_table",
                        code=E201,
                        file=file_path,
                        message=f"Duplicate value object ID: {vo.id}",
                    )

        elif isinstance(data, EnumsFile):
            for enum in data.enums:
                canonical_id = normalizer.normalize_id(enum.id)
                success = symbol_table.register(
                    SYMBOL_TYPE_ENUM,
                    canonical_id,
                    file_path,
                    enum,
                )
                if not success:
                    from ..diagnostics.error_codes import E201

                    reporter.add_error(
                        stage="symbol_table",
                        code=E201,
                        file=file_path,
                        message=f"Duplicate enum ID: {enum.id}",
                    )

        elif isinstance(data, ErrorsFile):
            for error in data.errors:
                canonical_id = normalizer.normalize_id(error.id)
                success = symbol_table.register(
                    SYMBOL_TYPE_ERROR,
                    canonical_id,
                    file_path,
                    error,
                )
                if not success:
                    from ..diagnostics.error_codes import E201

                    reporter.add_error(
                        stage="symbol_table",
                        code=E201,
                        file=file_path,
                        message=f"Duplicate error ID: {error.id}",
                    )

        elif isinstance(data, EventsFile):
            for event in data.events:
                canonical_id = normalizer.normalize_id(event.id)
                success = symbol_table.register(
                    SYMBOL_TYPE_EVENT,
                    canonical_id,
                    file_path,
                    event,
                )
                if not success:
                    from ..diagnostics.error_codes import E201

                    reporter.add_error(
                        stage="symbol_table",
                        code=E201,
                        file=file_path,
                        message=f"Duplicate event ID: {event.id}",
                    )

        elif isinstance(data, CommandsFile):
            for command in data.commands:
                canonical_id = normalizer.normalize_id(command.id)
                success = symbol_table.register(
                    SYMBOL_TYPE_COMMAND,
                    canonical_id,
                    file_path,
                    command,
                )
                if not success:
                    from ..diagnostics.error_codes import E201

                    reporter.add_error(
                        stage="symbol_table",
                        code=E201,
                        file=file_path,
                        message=f"Duplicate command ID: {command.id}",
                    )

        elif isinstance(data, QueriesFile):
            for query in data.queries:
                canonical_id = normalizer.normalize_id(query.id)
                success = symbol_table.register(
                    SYMBOL_TYPE_QUERY,
                    canonical_id,
                    file_path,
                    query,
                )
                if not success:
                    from ..diagnostics.error_codes import E201

                    reporter.add_error(
                        stage="symbol_table",
                        code=E201,
                        file=file_path,
                        message=f"Duplicate query ID: {query.id}",
                    )

        elif isinstance(data, WorkflowsFile):
            for workflow in data.workflows:
                canonical_id = normalizer.normalize_id(workflow.id)
                success = symbol_table.register(
                    SYMBOL_TYPE_WORKFLOW,
                    canonical_id,
                    file_path,
                    workflow,
                )
                if not success:
                    from ..diagnostics.error_codes import E201

                    reporter.add_error(
                        stage="symbol_table",
                        code=E201,
                        file=file_path,
                        message=f"Duplicate workflow ID: {workflow.id}",
                    )

        elif isinstance(data, ProjectionsFile):
            for projection in data.projections:
                canonical_id = normalizer.normalize_id(projection.id)
                success = symbol_table.register(
                    SYMBOL_TYPE_PROJECTION,
                    canonical_id,
                    file_path,
                    projection,
                )
                if not success:
                    from ..diagnostics.error_codes import E201

                    reporter.add_error(
                        stage="symbol_table",
                        code=E201,
                        file=file_path,
                        message=f"Duplicate projection ID: {projection.id}",
                    )

        elif isinstance(data, RulesFile):
            for rule in data.rules:
                canonical_id = normalizer.normalize_id(rule.id)
                success = symbol_table.register(
                    SYMBOL_TYPE_RULE,
                    canonical_id,
                    file_path,
                    rule,
                )
                if not success:
                    from ..diagnostics.error_codes import E201

                    reporter.add_error(
                        stage="symbol_table",
                        code=E201,
                        file=file_path,
                        message=f"Duplicate rule ID: {rule.id}",
                    )

        elif isinstance(data, AccessPolicyFile):
            for role in data.access.roles:
                canonical_id = normalizer.normalize_id(role.id)
                success = symbol_table.register(
                    SYMBOL_TYPE_ROLE,
                    canonical_id,
                    file_path,
                    role,
                )
                if not success:
                    from ..diagnostics.error_codes import E201

                    reporter.add_error(
                        stage="symbol_table",
                        code=E201,
                        file=file_path,
                        message=f"Duplicate role ID: {role.id}",
                    )
            for permission in data.access.permissions:
                canonical_id = normalizer.normalize_id(permission.id)
                success = symbol_table.register(
                    SYMBOL_TYPE_PERMISSION,
                    canonical_id,
                    file_path,
                    permission,
                )
                if not success:
                    from ..diagnostics.error_codes import E201

                    reporter.add_error(
                        stage="symbol_table",
                        code=E201,
                        file=file_path,
                        message=f"Duplicate permission ID: {permission.id}",
                    )

        elif isinstance(data, ScenariosFile):
            for scenario in data.scenarios:
                canonical_id = normalizer.normalize_id(scenario.id)
                success = symbol_table.register(
                    SYMBOL_TYPE_SCENARIO,
                    canonical_id,
                    file_path,
                    scenario,
                )
                if not success:
                    from ..diagnostics.error_codes import E201

                    reporter.add_error(
                        stage="symbol_table",
                        code=E201,
                        file=file_path,
                        message=f"Duplicate scenario ID: {scenario.id}",
                    )

        elif isinstance(data, PersistenceModelFile):
            for datasource in data.datasources:
                canonical_id = normalizer.normalize_id(datasource.id)
                success = symbol_table.register(
                    SYMBOL_TYPE_PERSISTENCE_DATASOURCE,
                    canonical_id,
                    file_path,
                    datasource,
                )
                if not success:
                    from ..diagnostics.error_codes import E201

                    reporter.add_error(
                        stage="symbol_table",
                        code=E201,
                        file=file_path,
                        message=f"Duplicate persistence datasource ID: {datasource.id}",
                    )
            for table in data.tables:
                canonical_id = normalizer.normalize_id(table.id)
                success = symbol_table.register(
                    SYMBOL_TYPE_PERSISTENCE_TABLE,
                    canonical_id,
                    file_path,
                    table,
                )
                if not success:
                    from ..diagnostics.error_codes import E201

                    reporter.add_error(
                        stage="symbol_table",
                        code=E201,
                        file=file_path,
                        message=f"Duplicate persistence table ID: {table.id}",
                    )

        elif isinstance(data, IntegrationsFile):
            for integration in data.integrations:
                canonical_id = normalizer.normalize_id(integration.id)
                success = symbol_table.register(
                    SYMBOL_TYPE_INTEGRATION,
                    canonical_id,
                    file_path,
                    integration,
                )
                if not success:
                    from ..diagnostics.error_codes import E201

                    reporter.add_error(
                        stage="symbol_table",
                        code=E201,
                        file=file_path,
                        message=f"Duplicate integration ID: {integration.id}",
                    )
            for operation in data.operations:
                canonical_id = normalizer.normalize_id(operation.id)
                success = symbol_table.register(
                    SYMBOL_TYPE_INTEGRATION_OPERATION,
                    canonical_id,
                    file_path,
                    operation,
                )
                if not success:
                    from ..diagnostics.error_codes import E201

                    reporter.add_error(
                        stage="symbol_table",
                        code=E201,
                        file=file_path,
                        message=f"Duplicate integration operation ID: {operation.id}",
                    )

        elif isinstance(data, ReliabilityPoliciesFile):
            for policy in data.reliability_policies:
                canonical_id = normalizer.normalize_id(policy.id)
                success = symbol_table.register(
                    SYMBOL_TYPE_RELIABILITY_POLICY,
                    canonical_id,
                    file_path,
                    policy,
                )
                if not success:
                    from ..diagnostics.error_codes import E201

                    reporter.add_error(
                        stage="symbol_table",
                        code=E201,
                        file=file_path,
                        message=f"Duplicate reliability policy ID: {policy.id}",
                    )

        elif isinstance(data, TestingFile):
            for test_case in data.tests:
                canonical_id = normalizer.normalize_id(test_case.id)
                success = symbol_table.register(
                    SYMBOL_TYPE_TEST_CASE,
                    canonical_id,
                    file_path,
                    test_case,
                )
                if not success:
                    from ..diagnostics.error_codes import E201

                    reporter.add_error(
                        stage="symbol_table",
                        code=E201,
                        file=file_path,
                        message=f"Duplicate test case ID: {test_case.id}",
                    )

        elif isinstance(data, SecretsContractFile):
            for secret in data.secrets:
                canonical_id = normalizer.normalize_id(secret.id)
                success = symbol_table.register(
                    SYMBOL_TYPE_SECRET,
                    canonical_id,
                    file_path,
                    secret,
                )
                if not success:
                    from ..diagnostics.error_codes import E201

                    reporter.add_error(
                        stage="symbol_table",
                        code=E201,
                        file=file_path,
                        message=f"Duplicate secret ID: {secret.id}",
                    )

    return symbol_table


def _check_cross_references(
    validated_data: dict[str, Any],
    symbol_table: SymbolTable,
    reporter: ErrorReporter,
) -> None:
    """Check cross-references between contracts."""
    checker = CrossRefChecker(symbol_table, reporter)

    for file_path, data in validated_data.items():
        checker.check_file(data, file_path)


def _sort_ir_collections(
    domain_ir: DomainIR,
    application_ir: ApplicationIR,
    workflow_ir: WorkflowModuleIR,
    api_ir: ApiIR,
    persistence_ir: PersistenceIR,
    integrations_ir: IntegrationsIR,
    ops_ir: OpsIR,
    policy_ir: PolicyIR,
    rules_ir: RulesIR,
    scenarios_ir: ScenariosIR,
    testing_ir: TestingIR,
) -> None:
    """
    Sort all IR collections by ID for deterministic output.

    Sorts all collections in-place using case-insensitive sorting.
    This ensures that IR output is deterministic regardless of file order
    or declaration order within files.

    Args:
        domain_ir: Domain IR module
        application_ir: Application IR module
        workflow_ir: Workflow IR module
        api_ir: API IR module
        policy_ir: Policy IR module
        rules_ir: Rules IR module
        scenarios_ir: Scenarios IR module
    """
    # Sort domain collections
    domain_ir.entities.sort(key=lambda x: x.id.lower())
    domain_ir.value_objects.sort(key=lambda x: x.id.lower())
    domain_ir.enums.sort(key=lambda x: x.id.lower())
    domain_ir.errors.sort(key=lambda x: x.id.lower())
    domain_ir.events.sort(key=lambda x: x.id.lower())

    # Sort application collections
    application_ir.commands.sort(key=lambda x: x.id.lower())
    application_ir.queries.sort(key=lambda x: x.id.lower())
    application_ir.projections.sort(key=lambda x: x.id.lower())

    # Sort workflow collections
    workflow_ir.workflows.sort(key=lambda x: x.id.lower())

    # Sort API collections
    if api_ir.http:
        api_ir.http.routes.sort(key=lambda x: x.id.lower())

    if api_ir.graphql:
        api_ir.graphql.types.sort(key=lambda x: x.id.lower())
        api_ir.graphql.queries.sort(key=lambda x: x.id.lower())
        api_ir.graphql.mutations.sort(key=lambda x: x.id.lower())

    # Sort policy collections
    policy_ir.business.sort(key=lambda x: x.id.lower())
    if policy_ir.access:
        policy_ir.access.roles.sort(key=lambda x: x.id.lower())
        policy_ir.access.permissions.sort(key=lambda x: x.id.lower())

    # Sort rules and scenarios
    rules_ir.rules.sort(key=lambda x: x.id.lower())
    scenarios_ir.scenarios.sort(key=lambda x: x.id.lower())
    testing_ir.tests.sort(key=lambda x: x.id.lower())

    # Sort persistence and integration collections
    persistence_ir.datasources.sort(key=lambda x: x.id.lower())
    persistence_ir.tables.sort(key=lambda x: x.id.lower())
    integrations_ir.integrations.sort(key=lambda x: x.id.lower())
    integrations_ir.operations.sort(key=lambda x: x.id.lower())
    integrations_ir.webhooks.sort(key=lambda x: x.id.lower())
    integrations_ir.email_providers.sort(key=lambda x: x.id.lower())
    integrations_ir.oauth2_providers.sort(key=lambda x: x.id.lower())
    ops_ir.profiles.sort(key=lambda x: x.name.lower())
    ops_ir.secrets.sort(key=lambda x: x.id.lower())
    ops_ir.reliability_policies.sort(key=lambda x: x.id.lower())
    ops_ir.observability.sort(key=lambda x: x.ref.id.lower())


def _build_ir_structure(
    validated_data: dict[str, Any],
    symbol_table: SymbolTable,
    normalizer: Normalizer,
    version: str,
    contracts_root: Path,
    sort_collections: bool = True,
    schema_tree: dict[str, Any] | None = None,
) -> IR:
    """
    Build the IR structure from validated and normalized contracts.

    Args:
        validated_data: Validated contract data
        symbol_table: Symbol table
        normalizer: Normalizer instance
        version: Version string
        contracts_root: Root path for contracts
        sort_collections: If True, sort all collections by ID for deterministic output
        schema_tree: Schema tree for dynamic intent inference

    Returns:
        Complete IR structure
    """
    from midicoder.dsl.models import (
        AccessPolicyFile,
        CommandsFile,
        EntitiesFile,
        EnumsFile,
        ErrorsFile,
        EventsFile,
        GraphQLApiFile,
        HttpApiFile,
        IntegrationsFile,
        ObservabilityFile,
        PersistenceModelFile,
        PoliciesFile,
        ProfilesFile,
        ProjectionsFile,
        QueriesFile,
        ReliabilityPoliciesFile,
        RulesFile,
        ScenariosFile,
        SecretsContractFile,
        SecurityBaselineFile,
        TestingFile,
        ValueObjectsFile,
        WorkflowsFile,
    )

    # Initialize IR modules
    domain_ir = DomainIR()
    application_ir = ApplicationIR()
    workflow_ir = WorkflowModuleIR()
    api_ir = ApiIR()
    persistence_ir = PersistenceIR()
    integrations_ir = IntegrationsIR()
    ops_ir = OpsIR()
    testing_ir = TestingIR()

    # Initialize IR types
    policy_ir = PolicyIR()
    rules_ir = RulesIR()
    scenarios_ir = ScenariosIR()

    # Build IR from each file
    for file_path, data in validated_data.items():
        file_checksum = _compute_file_checksum(contracts_root / file_path)

        if isinstance(data, EntitiesFile):
            for idx, entity in enumerate(data.entities):
                if not _is_canonical_symbol_owner(
                    symbol_table, SYMBOL_TYPE_ENTITY, entity.id, file_path, normalizer
                ):
                    continue
                entity_ir = _build_entity_ir(
                    entity, file_path, file_checksum, normalizer, idx
                )
                domain_ir.entities.append(entity_ir)

        elif isinstance(data, ValueObjectsFile):
            for idx, vo in enumerate(data.value_objects):
                if not _is_canonical_symbol_owner(
                    symbol_table, SYMBOL_TYPE_VALUE_OBJECT, vo.id, file_path, normalizer
                ):
                    continue
                vo_ir = _build_value_object_ir(
                    vo, file_path, file_checksum, normalizer, idx
                )
                domain_ir.value_objects.append(vo_ir)

        elif isinstance(data, EnumsFile):
            for idx, enum in enumerate(data.enums):
                if not _is_canonical_symbol_owner(
                    symbol_table, SYMBOL_TYPE_ENUM, enum.id, file_path, normalizer
                ):
                    continue
                enum_ir = _build_enum_ir(
                    enum, file_path, file_checksum, normalizer, idx
                )
                domain_ir.enums.append(enum_ir)

        elif isinstance(data, ErrorsFile):
            for idx, error in enumerate(data.errors):
                if not _is_canonical_symbol_owner(
                    symbol_table, SYMBOL_TYPE_ERROR, error.id, file_path, normalizer
                ):
                    continue
                error_ir = _build_error_ir(
                    error, file_path, file_checksum, normalizer, idx
                )
                domain_ir.errors.append(error_ir)

        elif isinstance(data, EventsFile):
            for idx, event in enumerate(data.events):
                if not _is_canonical_symbol_owner(
                    symbol_table, SYMBOL_TYPE_EVENT, event.id, file_path, normalizer
                ):
                    continue
                event_ir = _build_event_ir(
                    event, file_path, file_checksum, normalizer, idx
                )
                domain_ir.events.append(event_ir)

        elif isinstance(data, CommandsFile):
            for idx, command in enumerate(data.commands):
                if not _is_canonical_symbol_owner(
                    symbol_table, SYMBOL_TYPE_COMMAND, command.id, file_path, normalizer
                ):
                    continue
                command_ir = _build_command_ir(
                    command, file_path, file_checksum, normalizer, idx
                )
                application_ir.commands.append(command_ir)

        elif isinstance(data, QueriesFile):
            for idx, query in enumerate(data.queries):
                if not _is_canonical_symbol_owner(
                    symbol_table, SYMBOL_TYPE_QUERY, query.id, file_path, normalizer
                ):
                    continue
                query_ir = _build_query_ir(
                    query, file_path, file_checksum, normalizer, idx
                )
                application_ir.queries.append(query_ir)

        elif isinstance(data, WorkflowsFile):
            for idx, workflow in enumerate(data.workflows):
                if not _is_canonical_symbol_owner(
                    symbol_table,
                    SYMBOL_TYPE_WORKFLOW,
                    workflow.id,
                    file_path,
                    normalizer,
                ):
                    continue
                workflow_ir_item = _build_workflow_ir(
                    workflow, file_path, file_checksum, normalizer, idx
                )
                workflow_ir.workflows.append(workflow_ir_item)

        elif isinstance(data, ProjectionsFile):
            for idx, projection in enumerate(data.projections):
                if not _is_canonical_symbol_owner(
                    symbol_table,
                    SYMBOL_TYPE_PROJECTION,
                    projection.id,
                    file_path,
                    normalizer,
                ):
                    continue
                projection_ir = _build_projection_ir(
                    projection, file_path, file_checksum, normalizer, idx
                )
                application_ir.projections.append(projection_ir)

        elif isinstance(data, HttpApiFile):
            for idx, route in enumerate(data.routes):
                route_ir = _build_http_route_ir(
                    route, file_path, file_checksum, normalizer, idx
                )
                if api_ir.http is None:
                    api_ir.http = HttpApiIR()
                api_ir.http.routes.append(route_ir)

        elif isinstance(data, GraphQLApiFile):
            # Build GraphQL API
            if api_ir.graphql is None:
                from ..schema.ir_schema import GraphQLApiIR

                api_ir.graphql = GraphQLApiIR()

            # Build GraphQL types
            for idx, gql_type in enumerate(data.api.types):
                type_ir = _build_graphql_type_ir(
                    gql_type, file_path, file_checksum, normalizer, idx
                )
                api_ir.graphql.types.append(type_ir)

            # Build GraphQL queries
            for idx, gql_query in enumerate(data.api.queries):
                query_ir = _build_graphql_operation_ir(
                    gql_query, "query", file_path, file_checksum, normalizer, idx
                )
                api_ir.graphql.queries.append(query_ir)

            # Build GraphQL mutations
            for idx, gql_mutation in enumerate(data.api.mutations):
                mutation_ir = _build_graphql_operation_ir(
                    gql_mutation, "mutation", file_path, file_checksum, normalizer, idx
                )
                api_ir.graphql.mutations.append(mutation_ir)

        elif isinstance(data, AccessPolicyFile):
            # Build Access Policy
            if policy_ir.access is None:
                policy_ir.access = _build_access_policy_ir(
                    data, file_path, file_checksum, normalizer
                )

        elif isinstance(data, PoliciesFile):
            # Build Business Policies
            for idx, policy in enumerate(data.policies):
                business_policy_ir = _build_business_policy_ir(
                    policy, file_path, file_checksum, normalizer, idx
                )
                policy_ir.business.append(business_policy_ir)

        elif isinstance(data, RulesFile):
            # Build Rules
            for idx, rule in enumerate(data.rules):
                if not _is_canonical_symbol_owner(
                    symbol_table, SYMBOL_TYPE_RULE, rule.id, file_path, normalizer
                ):
                    continue
                rule_ir = _build_rule_ir(
                    rule, file_path, file_checksum, normalizer, idx
                )
                rules_ir.rules.append(rule_ir)

        elif isinstance(data, ScenariosFile):
            # Build Scenarios
            for idx, scenario in enumerate(data.scenarios):
                if not _is_canonical_symbol_owner(
                    symbol_table,
                    SYMBOL_TYPE_SCENARIO,
                    scenario.id,
                    file_path,
                    normalizer,
                ):
                    continue
                scenario_ir = _build_scenario_ir(
                    scenario, file_path, file_checksum, normalizer, idx
                )
                scenarios_ir.scenarios.append(scenario_ir)

        elif isinstance(data, PersistenceModelFile):
            for idx, datasource in enumerate(data.datasources):
                if not _is_canonical_symbol_owner(
                    symbol_table,
                    SYMBOL_TYPE_PERSISTENCE_DATASOURCE,
                    datasource.id,
                    file_path,
                    normalizer,
                ):
                    continue
                persistence_ir.datasources.append(
                    _build_persistence_datasource_ir(
                        datasource, file_path, file_checksum, normalizer, idx
                    )
                )
            for idx, table in enumerate(data.tables):
                if not _is_canonical_symbol_owner(
                    symbol_table,
                    SYMBOL_TYPE_PERSISTENCE_TABLE,
                    table.id,
                    file_path,
                    normalizer,
                ):
                    continue
                persistence_ir.tables.append(
                    _build_persistence_table_ir(
                        table, file_path, file_checksum, normalizer, idx
                    )
                )

        elif isinstance(data, IntegrationsFile):
            for idx, integration in enumerate(data.integrations):
                if not _is_canonical_symbol_owner(
                    symbol_table,
                    SYMBOL_TYPE_INTEGRATION,
                    integration.id,
                    file_path,
                    normalizer,
                ):
                    continue
                integrations_ir.integrations.append(
                    _build_integration_target_ir(
                        integration, file_path, file_checksum, normalizer, idx
                    )
                )
            for idx, operation in enumerate(data.operations):
                if not _is_canonical_symbol_owner(
                    symbol_table,
                    SYMBOL_TYPE_INTEGRATION_OPERATION,
                    operation.id,
                    file_path,
                    normalizer,
                ):
                    continue
                integrations_ir.operations.append(
                    _build_rest_api_operation_ir(
                        operation, file_path, file_checksum, normalizer, idx
                    )
                )
            for idx, s3_resource in enumerate(data.s3_resources):
                integrations_ir.s3_resources.append(
                    _build_s3_resource_ir(
                        s3_resource, file_path, file_checksum, normalizer, idx
                    )
                )
            for idx, oauth2 in enumerate(data.oauth2_providers):
                integrations_ir.oauth2_providers.append(
                    _build_oauth2_provider_ir(
                        oauth2, file_path, file_checksum, normalizer, idx
                    )
                )
            for idx, webhook in enumerate(data.webhooks):
                integrations_ir.webhooks.append(
                    _build_webhook_endpoint_ir(
                        webhook, file_path, file_checksum, normalizer, idx
                    )
                )
            for idx, email_provider in enumerate(data.email_providers):
                integrations_ir.email_providers.append(
                    _build_email_provider_ir(
                        email_provider, file_path, file_checksum, normalizer, idx
                    )
                )

        elif isinstance(data, ProfilesFile):
            for idx, profile in enumerate(data.profiles):
                ops_ir.profiles.append(
                    _build_profile_ir(
                        profile, file_path, file_checksum, normalizer, idx
                    )
                )

        elif isinstance(data, SecretsContractFile):
            for idx, secret in enumerate(data.secrets):
                ops_ir.secrets.append(
                    _build_secret_ref_ir(
                        secret, file_path, file_checksum, normalizer, idx
                    )
                )

        elif isinstance(data, SecurityBaselineFile):
            ops_ir.security = _build_security_baseline_ir(
                data.security,
                file_path,
                file_checksum,
                normalizer,
            )

        elif isinstance(data, ReliabilityPoliciesFile):
            for idx, policy in enumerate(data.reliability_policies):
                if not _is_canonical_symbol_owner(
                    symbol_table,
                    SYMBOL_TYPE_RELIABILITY_POLICY,
                    policy.id,
                    file_path,
                    normalizer,
                ):
                    continue
                ops_ir.reliability_policies.append(
                    _build_reliability_policy_ir(
                        policy, file_path, file_checksum, normalizer, idx
                    )
                )

        elif isinstance(data, ObservabilityFile):
            for idx, target in enumerate(data.observability):
                ops_ir.observability.append(
                    _build_observability_target_ir(
                        target, file_path, file_checksum, normalizer, idx
                    )
                )

        elif isinstance(data, TestingFile):
            for idx, test_case in enumerate(data.tests):
                if not _is_canonical_symbol_owner(
                    symbol_table,
                    SYMBOL_TYPE_TEST_CASE,
                    test_case.id,
                    file_path,
                    normalizer,
                ):
                    continue
                testing_ir.tests.append(
                    _build_contract_test_case_ir(
                        test_case, file_path, file_checksum, normalizer, idx
                    )
                )

    # Sort all collections by ID for deterministic output (if enabled)
    if sort_collections:
        _sort_ir_collections(
            domain_ir,
            application_ir,
            workflow_ir,
            api_ir,
            persistence_ir,
            integrations_ir,
            ops_ir,
            policy_ir,
            rules_ir,
            scenarios_ir,
            testing_ir,
        )

    # Build indexes
    indexes = _build_indexes(symbol_table, normalizer)

    # Build stats
    stats = Stats(
        entities=len(domain_ir.entities),
        value_objects=len(domain_ir.value_objects),
        enums=len(domain_ir.enums),
        errors=len(domain_ir.errors),
        events=len(domain_ir.events),
        commands=len(application_ir.commands),
        queries=len(application_ir.queries),
        projections=len(application_ir.projections),
        workflows=len(workflow_ir.workflows),
        rules=len(rules_ir.rules),
        scenarios=len(scenarios_ir.scenarios),
        http_routes=len(api_ir.http.routes) if api_ir.http else 0,
        graphql_types=len(api_ir.graphql.types) if api_ir.graphql else 0,
        roles=len(policy_ir.access.roles) if policy_ir.access else 0,
        permissions=len(policy_ir.access.permissions) if policy_ir.access else 0,
        policies=len(policy_ir.business),
        persistence_datasources=len(persistence_ir.datasources),
        persistence_tables=len(persistence_ir.tables),
        integrations=len(integrations_ir.integrations),
        integration_operations=len(integrations_ir.operations),
        webhooks=len(integrations_ir.webhooks),
        email_providers=len(integrations_ir.email_providers),
        oauth2_providers=len(integrations_ir.oauth2_providers),
        profiles=len(ops_ir.profiles),
        secrets=len(ops_ir.secrets),
        reliability_policies=len(ops_ir.reliability_policies),
        observability_targets=len(ops_ir.observability),
        tests=len(testing_ir.tests),
    )

    # Build metadata
    meta = IRMeta(stats=stats)

    # Build modules
    modules = IRModules(
        domain=domain_ir,
        application=application_ir,
        workflow=workflow_ir,
        api=api_ir,
        persistence=persistence_ir,
        integrations=integrations_ir,
        ops=ops_ir,
        policy=policy_ir,
        rules=rules_ir,
        scenarios=scenarios_ir,
        testing=testing_ir,
    )

    # Build top-level IR
    ir = IR(
        version=version,
        schema_version="2.0.0",
        generated_at=_utc_now(),
        modules=modules,
        indexes=indexes,
        meta=meta,
    )

    # Phase: Intent.kind inference
    from ..analysis.intent import apply_intent_kind

    apply_intent_kind(ir, validated_data, normalizer, schema_tree)

    return ir


def _is_canonical_symbol_owner(
    symbol_table: SymbolTable,
    symbol_type: str,
    raw_id: Any,
    source_file: str,
    normalizer: Normalizer,
) -> bool:
    """
    Check whether this file is the canonical owner of a symbol.

    When multiple files define the same symbol ID, symbol table conflict
    resolution selects one canonical source. IR materialization must follow
    that source to avoid duplicated IR nodes.
    """
    try:
        canonical_id = normalizer.normalize_id(str(raw_id))
    except Exception:
        # If ID normalization fails unexpectedly, keep current behavior.
        return True

    resolved = symbol_table.resolve(symbol_type, canonical_id)
    if resolved is None:
        return True
    return resolved.source_file == source_file


def _build_entity_ir(
    entity: Any,
    file: str,
    checksum: str,
    normalizer: Normalizer,
    source_order: int = 0,
) -> EntityIR:
    """Build EntityIR from Entity model."""
    from ..diagnostics.line_info_cache import get_line_info

    # Get line information
    line_info = get_line_info(file, entity.id)

    return EntityIR(
        id=normalizer.normalize_id(entity.id),
        description=entity.description,
        fields=[_build_field_ir(f) for f in entity.fields],
        primary_key=entity.primary_key,
        indexes=[_build_index_ir(idx) for idx in entity.indexes],
        constraints=[_build_constraint_ir(c) for c in entity.constraints],
        tags=entity.tags,
        tenant_scope=entity.tenant_scope,
        source_ref=entity.source,
        source=SourceMetadata(
            file=file,
            checksum=checksum,
            line_start=line_info.get("start"),
            line_end=line_info.get("end"),
            source_order=source_order,
        ),
        hash=normalizer.compute_hash(entity.model_dump()),
        intent=None,
    )


def _build_value_object_ir(
    vo: Any,
    file: str,
    checksum: str,
    normalizer: Normalizer,
    source_order: int = 0,
) -> ValueObjectIR:
    """Build ValueObjectIR from ValueObject model."""
    from ..diagnostics.line_info_cache import get_line_info

    # Get line information
    line_info = get_line_info(file, vo.id)

    return ValueObjectIR(
        id=normalizer.normalize_id(vo.id),
        description=vo.description,
        fields=[_build_field_ir(f) for f in vo.fields],
        tags=vo.tags,
        category=vo.category,
        source_ref=vo.source,
        source=SourceMetadata(
            file=file,
            checksum=checksum,
            line_start=line_info.get("start"),
            line_end=line_info.get("end"),
            source_order=source_order,
        ),
        hash=normalizer.compute_hash(vo.model_dump()),
        intent=None,
    )


def _build_enum_ir(
    enum: Any,
    file: str,
    checksum: str,
    normalizer: Normalizer,
    source_order: int = 0,
) -> EnumIR:
    """Build EnumIR from EnumDef model."""
    from ..diagnostics.line_info_cache import get_line_info

    line_info = get_line_info(file, enum.id)

    return EnumIR(
        id=normalizer.normalize_id(enum.id),
        description=enum.description,
        values=enum.values,
        value_labels=enum.value_labels,
        tags=enum.tags,
        source_ref=enum.source,
        source=SourceMetadata(
            file=file,
            checksum=checksum,
            line_start=line_info.get("start"),
            line_end=line_info.get("end"),
            source_order=source_order,
        ),
        hash=normalizer.compute_hash(enum.model_dump()),
        intent=None,
    )


def _build_error_ir(
    error: Any,
    file: str,
    checksum: str,
    normalizer: Normalizer,
    source_order: int = 0,
) -> ErrorIR:
    """Build ErrorIR from ErrorDef model."""
    from ..diagnostics.line_info_cache import get_line_info

    line_info = get_line_info(file, error.id)

    return ErrorIR(
        id=normalizer.normalize_id(error.id),
        description=error.description,
        fields=[],
        category=error.category,
        http_status=error.http_status,
        code=error.code,
        tags=error.tags,
        source_ref=error.source,
        source=SourceMetadata(
            file=file,
            checksum=checksum,
            line_start=line_info.get("start"),
            line_end=line_info.get("end"),
            source_order=source_order,
        ),
        hash=normalizer.compute_hash(error.model_dump()),
    )


def _build_event_ir(
    event: Any,
    file: str,
    checksum: str,
    normalizer: Normalizer,
    source_order: int = 0,
) -> EventIR:
    """Build EventIR from EventDef model."""
    from ..diagnostics.line_info_cache import get_line_info

    line_info = get_line_info(file, event.id)

    return EventIR(
        id=normalizer.normalize_id(event.id),
        description=event.description,
        fields=[_build_field_ir(f) for f in event.payload],
        kind=event.kind,
        tags=event.tags,
        source_ref=event.source,
        source=SourceMetadata(
            file=file,
            checksum=checksum,
            line_start=line_info.get("start"),
            line_end=line_info.get("end"),
            source_order=source_order,
        ),
        hash=normalizer.compute_hash(event.model_dump()),
        intent=None,
    )


def _build_command_ir(
    command: Any,
    file: str,
    checksum: str,
    normalizer: Normalizer,
    source_order: int = 0,
) -> CommandIR:
    """Build CommandIR from Command model."""
    from ..diagnostics.line_info_cache import get_line_info

    line_info = get_line_info(file, command.id)

    return CommandIR(
        id=normalizer.normalize_id(command.id),
        description=command.description,
        input=[_build_field_ir(f) for f in command.input],
        returns=[_build_field_ir(f) for f in command.returns],
        fetches=[
            _build_typed_ref(ref, normalizer, "Entity") for ref in command.fetches
        ],
        guards=[_build_guard_ir(g) for g in command.guards],
        effects=[_build_effect_ir(e) for e in command.effects],
        errors=[_build_typed_ref(ref, normalizer, "Error") for ref in command.errors],
        emits=[_build_typed_ref(ref, normalizer, "Event") for ref in command.emits],
        category=command.category,
        required_roles=list(getattr(command, "required_roles", []) or []),
        required_permissions=list(getattr(command, "required_permissions", []) or []),
        writes_to=list(getattr(command, "writes_to", []) or []),
        datasource=getattr(command, "datasource", None),
        transaction=command.transaction,
        tenant_scope=command.tenant_scope,
        tags=command.tags,
        source_ref=command.source,
        source=SourceMetadata(
            file=file,
            checksum=checksum,
            line_start=line_info.get("start"),
            line_end=line_info.get("end"),
            source_order=source_order,
        ),
        hash=normalizer.compute_hash(command.model_dump()),
        intent=None,
    )


def _build_query_ir(
    query: Any,
    file: str,
    checksum: str,
    normalizer: Normalizer,
    source_order: int = 0,
) -> QueryIR:
    """Build QueryIR from Query model."""
    from ..diagnostics.line_info_cache import get_line_info

    line_info = get_line_info(file, query.id)

    return QueryIR(
        id=normalizer.normalize_id(query.id),
        description=query.description,
        input=[_build_field_ir(f) for f in query.input],
        returns=[_build_field_ir(f) for f in query.returns],
        reads=[_build_typed_ref(ref, normalizer, "Entity") for ref in query.reads],
        filters=query.filters,
        pagination=query.pagination,
        category=query.category,
        required_roles=list(getattr(query, "required_roles", []) or []),
        required_permissions=list(getattr(query, "required_permissions", []) or []),
        reads_from=list(getattr(query, "reads_from", []) or []),
        datasource=getattr(query, "datasource", None),
        tags=query.tags,
        source_ref=query.source,
        source=SourceMetadata(
            file=file,
            checksum=checksum,
            line_start=line_info.get("start"),
            line_end=line_info.get("end"),
            source_order=source_order,
        ),
        hash=normalizer.compute_hash(query.model_dump()),
        intent=None,
    )


def _build_workflow_ir(
    workflow: Any,
    file: str,
    checksum: str,
    normalizer: Normalizer,
    source_order: int = 0,
) -> WorkflowIR:
    """Build WorkflowIR from Workflow model."""
    from ..diagnostics.line_info_cache import get_line_info

    line_info = get_line_info(file, workflow.id)

    return WorkflowIR(
        id=normalizer.normalize_id(workflow.id),
        description=workflow.description,
        entity=_build_typed_ref(workflow.entity, normalizer, "Entity"),
        states=[_build_state_ir(s) for s in workflow.states],
        transitions=[_build_transition_ir(t, normalizer) for t in workflow.transitions],
        initial_state=workflow.initial_state,
        error_handlers=[
            _build_error_handler_ir(h, normalizer) for h in workflow.error_handlers
        ],
        required_roles=list(getattr(workflow, "required_roles", []) or []),
        required_permissions=list(getattr(workflow, "required_permissions", []) or []),
        scenarios=list(getattr(workflow, "scenarios", []) or []),
        tags=workflow.tags,
        source_ref=workflow.source,
        source=SourceMetadata(
            file=file,
            checksum=checksum,
            line_start=line_info.get("start"),
            line_end=line_info.get("end"),
            source_order=source_order,
        ),
        hash=normalizer.compute_hash(workflow.model_dump()),
        intent=None,
    )


def _build_http_route_ir(
    route: Any,
    file: str,
    checksum: str,
    normalizer: Normalizer,
    source_order: int = 0,
) -> HttpRouteIR:
    """Build HttpRouteIR from HttpRoute model."""
    from ..diagnostics.line_info_cache import get_line_info

    route_id = f"{route.method.lower()}_{route.path.replace('/', '_').replace('{', '').replace('}', '').strip('_')}"
    line_info = get_line_info(file, route_id)

    # If not found by generated ID, try to get from path
    if not line_info.get("start"):
        line_info = get_line_info(file, route.path)

    command_ref: RefIR | None = None
    query_ref: RefIR | None = None

    if route.command:
        command_candidate, query_candidate = _resolve_http_route_ref(
            route.command, normalizer, preferred_type="command"
        )
        command_ref = command_candidate or command_ref
        query_ref = query_candidate or query_ref

    if route.query:
        command_candidate, query_candidate = _resolve_http_route_ref(
            route.query, normalizer, preferred_type="query"
        )
        # Keep earlier assignments from the corresponding field if already set.
        command_ref = command_ref or command_candidate
        query_ref = query_ref or query_candidate

    return HttpRouteIR(
        id=normalizer.normalize_id(route_id),
        method=route.method,
        path=route.path,
        command=command_ref,
        query=query_ref,
        description=route.description,
        auth=route.auth,
        request_schema=(
            [_build_field_ir(f) for f in route.request_schema]
            if route.request_schema
            else []
        ),
        response_schema=(
            [_build_field_ir(f) for f in route.response_schema]
            if route.response_schema
            else None
        ),
        deprecated=route.deprecated,
        tags=route.tags,
        source_ref=route.source,
        source=SourceMetadata(
            file=file,
            checksum=checksum,
            line_start=line_info.get("start"),
            line_end=line_info.get("end"),
            source_order=source_order,
        ),
        hash=normalizer.compute_hash(route.model_dump()),
    )


def _extract_ref_id(ref: Any) -> str:
    if isinstance(ref, str):
        if ":" in ref:
            return ref.split(":", 1)[1].strip()
        return ref
    if isinstance(ref, dict):
        return ref.get("id", "")
    if isinstance(ref, list) and len(ref) >= 2:
        return str(ref[1])
    return str(ref)


def _resolve_http_route_ref(
    ref: Any,
    normalizer: Normalizer,
    preferred_type: str,
) -> tuple[RefIR | None, RefIR | None]:
    """
    Resolve an HTTP route reference against both command/query symbol spaces.

    Returns:
        (command_ref, query_ref)
    """
    ref_id = normalizer.normalize_id(_extract_ref_id(ref))
    is_command = bool(normalizer.symbols.resolve(SYMBOL_TYPE_COMMAND, ref_id))
    is_query = bool(normalizer.symbols.resolve(SYMBOL_TYPE_QUERY, ref_id))

    if preferred_type == "command":
        if is_command:
            return _build_typed_ref(ref, normalizer, "Command"), None
        if is_query:
            return None, _build_typed_ref(ref, normalizer, "Query")
        return _build_typed_ref(ref, normalizer, "Command"), None

    if preferred_type == "query":
        if is_query:
            return None, _build_typed_ref(ref, normalizer, "Query")
        if is_command:
            return _build_typed_ref(ref, normalizer, "Command"), None
        return None, _build_typed_ref(ref, normalizer, "Query")

    return None, None


def _build_graphql_type_ir(
    gql_type: Any,
    file: str,
    checksum: str,
    normalizer: Normalizer,
    source_order: int = 0,
) -> Any:
    """Build GraphQLTypeIR from GraphQLType model."""
    from ..diagnostics.line_info_cache import get_line_info

    line_info = get_line_info(file, gql_type.name)

    from ..schema.ir_schema import GraphQLFieldIR, GraphQLTypeIR

    fields = []
    for field in gql_type.fields:
        fields.append(
            GraphQLFieldIR(
                name=field.name,
                type=field.type,
                args=[_build_field_ir(arg) for arg in getattr(field, "args", [])],
                description=field.description,
            )
        )

    return GraphQLTypeIR(
        id=normalizer.normalize_id(gql_type.name),
        name=gql_type.name,
        kind=gql_type.kind or "object",
        fields=fields,
        description=gql_type.description,
        tags=[],
        source_ref=None,
        source=SourceMetadata(
            file=file,
            checksum=checksum,
            line_start=line_info.get("start"),
            line_end=line_info.get("end"),
            source_order=source_order,
        ),
        hash=normalizer.compute_hash(gql_type.model_dump()),
    )


def _build_graphql_operation_ir(
    operation: Any,
    operation_type: str,
    file: str,
    checksum: str,
    normalizer: Normalizer,
    source_order: int = 0,
) -> Any:
    """Build GraphQLOperationIR from GraphQLField model."""
    from ..diagnostics.line_info_cache import get_line_info

    line_info = get_line_info(file, operation.name)

    from ..schema.ir_schema import GraphQLOperationIR

    command_ref = None
    query_ref = None

    resolver = getattr(operation, "resolver", "")
    if resolver:
        resolver = resolver.strip()
        if resolver.startswith("Command:"):
            command_ref = _build_typed_ref(resolver, normalizer, "Command")
        elif resolver.startswith("Query:"):
            query_ref = _build_typed_ref(resolver, normalizer, "Query")
        else:
            if operation_type == "mutation":
                command_ref = _build_typed_ref(resolver, normalizer, "Command")
            elif operation_type == "query":
                query_ref = _build_typed_ref(resolver, normalizer, "Query")

    returns_type = None
    if operation.returns:
        if len(operation.returns) == 1:
            returns_type = operation.returns[0].type
        else:
            returns_type = "Multiple"

    return GraphQLOperationIR(
        id=normalizer.normalize_id(operation.name),
        name=operation.name,
        type=operation_type,
        args=[_build_field_ir(arg) for arg in operation.args],
        returns=[_build_field_ir(f) for f in operation.returns],
        returns_type=returns_type,
        command=command_ref,
        query=query_ref,
        description=operation.description,
        tags=[],
        source_ref=None,
        source=SourceMetadata(
            file=file,
            checksum=checksum,
            line_start=line_info.get("start"),
            line_end=line_info.get("end"),
            source_order=source_order,
        ),
        hash=normalizer.compute_hash(operation.model_dump()),
    )


def _build_projection_ir(
    projection: Any,
    file: str,
    checksum: str,
    normalizer: Normalizer,
    source_order: int = 0,
) -> ProjectionIR:
    """Build ProjectionIR from Projection model."""
    from ..diagnostics.line_info_cache import get_line_info

    line_info = get_line_info(file, projection.id)

    return ProjectionIR(
        id=normalizer.normalize_id(projection.id),
        description=projection.description,
        source_events=[
            _build_typed_ref(ref, normalizer, "Event")
            for ref in projection.source_events
        ],
        fields=[_build_field_ir(f) for f in projection.fields],
        storage=projection.storage,
        storage_kind=getattr(projection, "storage_kind", None),
        storage_ref=getattr(projection, "storage_ref", None),
        tags=projection.tags,
        source_ref=projection.source,
        source=SourceMetadata(
            file=file,
            checksum=checksum,
            line_start=line_info.get("start"),
            line_end=line_info.get("end"),
            source_order=source_order,
        ),
        hash=normalizer.compute_hash(projection.model_dump()),
        intent=None,
    )


def _build_access_policy_ir(
    data: Any, file: str, checksum: str, normalizer: Normalizer
) -> Any:
    """Build AccessPolicyIR from AccessPolicyFile."""
    from ..diagnostics.line_info_cache import get_line_info
    from ..schema.ir_schema import AccessPolicyIR, BindingIR, PermissionIR, RoleIR

    access = data.access

    roles = []
    for role in access.roles:
        line_info = get_line_info(file, role.id)
        roles.append(
            RoleIR(
                id=normalizer.normalize_id(role.id),
                description=role.description,
                tags=[],
                source_ref=None,
                source=SourceMetadata(
                    file=file,
                    checksum=checksum,
                    line_start=line_info.get("start"),
                    line_end=line_info.get("end"),
                ),
                hash=normalizer.compute_hash(role.model_dump()),
            )
        )

    permissions = []
    for perm in access.permissions:
        line_info = get_line_info(file, perm.id)
        permissions.append(
            PermissionIR(
                id=normalizer.normalize_id(perm.id),
                description=perm.description,
                resource=perm.resource,
                actions=[perm.action],
                tags=[],
                source_ref=None,
                source=SourceMetadata(
                    file=file,
                    checksum=checksum,
                    line_start=line_info.get("start"),
                    line_end=line_info.get("end"),
                ),
                hash=normalizer.compute_hash(perm.model_dump()),
            )
        )

    bindings = []
    for binding in access.bindings:
        bindings.append(
            BindingIR(
                role=binding.role,
                permissions=binding.permissions,
                scope=None,
            )
        )

    return AccessPolicyIR(
        roles=roles,
        permissions=permissions,
        bindings=bindings,
    )


def _build_business_policy_ir(
    policy: Any,
    file: str,
    checksum: str,
    normalizer: Normalizer,
    source_order: int = 0,
) -> Any:
    """Build BusinessPolicyIR from Policy model."""
    from ..diagnostics.line_info_cache import get_line_info
    from ..schema.ir_schema import BusinessPolicyIR, PolicyConditionIR, PolicyEffectIR

    line_info = get_line_info(file, policy.id)

    conditions = []
    for cond in policy.conditions:
        conditions.append(
            PolicyConditionIR(
                field=cond.field,
                operator=cond.op,
                value=cond.value,
            )
        )

    effects = []
    for effect in policy.effects:
        effects.append(
            PolicyEffectIR(
                type=effect.type,
                target=effect.target if hasattr(effect, "target") else None,
                params=effect.params if hasattr(effect, "params") else {},
            )
        )

    return BusinessPolicyIR(
        id=normalizer.normalize_id(policy.id),
        description=policy.description,
        conditions=conditions,
        effects=effects,
        tags=policy.tags if hasattr(policy, "tags") else [],
        scope=policy.scope if hasattr(policy, "scope") else None,
        source_ref=policy.source if hasattr(policy, "source") else None,
        source=SourceMetadata(
            file=file,
            checksum=checksum,
            line_start=line_info.get("start"),
            line_end=line_info.get("end"),
            source_order=source_order,
        ),
        hash=normalizer.compute_hash(policy.model_dump()),
    )


def _build_rule_ir(
    rule: Any,
    file: str,
    checksum: str,
    normalizer: Normalizer,
    source_order: int = 0,
) -> Any:
    """Build RuleIR from Rule model."""
    from ..diagnostics.line_info_cache import get_line_info
    from ..schema.ir_schema import RuleIR, RuleRowIR

    line_info = get_line_info(file, rule.id)

    table = []
    for row in rule.rows:  # 'rows' not 'table' in schema
        table.append(
            RuleRowIR(
                conditions=row.when,  # 'when' not 'conditions'
                result=row.then,  # 'then' not 'result'
            )
        )

    return RuleIR(
        id=normalizer.normalize_id(rule.id),
        description=rule.description,
        table=table,
        default_result=None,  # Not in current schema
        tags=rule.tags,
        applies_to=rule.applies_to,
        applies_to_scenario=getattr(rule, "applies_to_scenario", None),
        inputs=rule.inputs,
        outputs=rule.outputs,
        severity=rule.severity,
        source_ref=rule.source,
        source=SourceMetadata(
            file=file,
            checksum=checksum,
            line_start=line_info.get("start"),
            line_end=line_info.get("end"),
            source_order=source_order,
        ),
        hash=normalizer.compute_hash(rule.model_dump()),
    )


def _build_scenario_ir(
    scenario: Any,
    file: str,
    checksum: str,
    normalizer: Normalizer,
    source_order: int = 0,
) -> Any:
    """Build ScenarioIR from Scenario model."""
    from ..diagnostics.line_info_cache import get_line_info

    line_info = get_line_info(file, scenario.id)

    from ..schema.ir_schema import ScenarioIR, ScenarioStepIR

    steps = []
    for step in scenario.steps:
        step_ref = None
        if hasattr(step, "ref") and step.ref:
            default_type = None
            if step.type == "command":
                default_type = "Command"
            elif step.type == "query":
                default_type = "Query"
            elif step.type == "event":
                default_type = "Event"
            if default_type:
                step_ref = _build_typed_ref(step.ref, normalizer, default_type)
            else:
                step_ref = _build_ref_ir(normalizer.normalize_ref(step.ref))

        steps.append(
            ScenarioStepIR(
                type=step.type,
                ref=step_ref,
                input=step.input if hasattr(step, "input") else {},
                expect=step.expect if hasattr(step, "expect") else {},
                description=step.description if hasattr(step, "description") else None,
            )
        )

    raw_actor_roles = list(getattr(scenario, "actor_roles", []) or [])
    if not raw_actor_roles:
        # Backward compatibility: older contracts stored role IDs in actors.
        raw_actor_roles = list(getattr(scenario, "actors", []) or [])

    return ScenarioIR(
        id=normalizer.normalize_id(scenario.id),
        description=scenario.description,
        actors=scenario.actors if hasattr(scenario, "actors") else [],
        preconditions=(
            scenario.preconditions if hasattr(scenario, "preconditions") else []
        ),
        steps=steps,
        postconditions=(
            scenario.postconditions if hasattr(scenario, "postconditions") else []
        ),
        tags=scenario.tags if hasattr(scenario, "tags") else [],
        source_ref=scenario.source if hasattr(scenario, "source") else None,
        source=SourceMetadata(
            file=file,
            checksum=checksum,
            line_start=line_info.get("start"),
            line_end=line_info.get("end"),
            source_order=source_order,
        ),
        hash=normalizer.compute_hash(scenario.model_dump()),
        actor_roles=[
            _build_typed_ref(role_ref, normalizer, "Role")
            for role_ref in raw_actor_roles
            if str(role_ref).strip()
        ],
    )


def _build_timeout_policy_ir(value: Any | None) -> TimeoutPolicyIR | None:
    if value is None:
        return None
    return TimeoutPolicyIR(
        connect_ms=getattr(value, "connect_ms", None),
        read_ms=getattr(value, "read_ms", None),
        total_ms=getattr(value, "total_ms", None),
    )


def _build_retry_policy_ir(value: Any | None) -> RetryPolicyIR | None:
    if value is None:
        return None
    return RetryPolicyIR(
        max_attempts=getattr(value, "max_attempts", 1),
        backoff_ms=getattr(value, "backoff_ms", 0),
        max_backoff_ms=getattr(value, "max_backoff_ms", None),
        jitter=getattr(value, "jitter", False),
    )


def _build_rate_limit_policy_ir(value: Any | None) -> RateLimitPolicyIR | None:
    if value is None:
        return None
    return RateLimitPolicyIR(
        requests=getattr(value, "requests"),
        per_seconds=getattr(value, "per_seconds"),
    )


def _build_circuit_breaker_policy_ir(
    value: Any | None,
) -> CircuitBreakerPolicyIR | None:
    if value is None:
        return None
    return CircuitBreakerPolicyIR(
        failure_threshold=getattr(value, "failure_threshold"),
        recovery_timeout_seconds=getattr(value, "recovery_timeout_seconds"),
    )


def _build_persistence_datasource_ir(
    datasource: Any,
    file: str,
    checksum: str,
    normalizer: Normalizer,
    source_order: int = 0,
) -> PersistenceDatasourceIR:
    from ..diagnostics.line_info_cache import get_line_info

    line_info = get_line_info(file, datasource.id)
    integration_ref = getattr(datasource, "integration_id", None)
    return PersistenceDatasourceIR(
        id=normalizer.normalize_id(datasource.id),
        engine=datasource.engine,
        connector=datasource.connector,
        database=datasource.database,
        host=datasource.host,
        port=datasource.port,
        db_schema=getattr(datasource, "db_schema", None),
        default=datasource.default,
        options=datasource.options,
        integration=(
            _build_typed_ref(integration_ref, normalizer, "Integration")
            if integration_ref
            else None
        ),
        source=SourceMetadata(
            file=file,
            checksum=checksum,
            line_start=line_info.get("start"),
            line_end=line_info.get("end"),
            source_order=source_order,
        ),
        hash=normalizer.compute_hash(datasource.model_dump()),
    )


def _build_persistence_table_ir(
    table: Any,
    file: str,
    checksum: str,
    normalizer: Normalizer,
    source_order: int = 0,
) -> PersistenceTableIR:
    from ..diagnostics.line_info_cache import get_line_info

    line_info = get_line_info(file, table.id)
    return PersistenceTableIR(
        id=normalizer.normalize_id(table.id),
        description=table.description,
        datasource=table.datasource,
        operation=(
            _build_typed_ref(table.operation_id, normalizer, "IntegrationOperation")
            if getattr(table, "operation_id", None)
            else None
        ),
        columns=[
            PersistenceColumnIR(
                name=c.name,
                type=c.type,
                required=c.required,
                description=c.description,
                constraints=c.constraints,
            )
            for c in table.columns
        ],
        indexes=[
            PersistenceIndexIR(
                name=i.name,
                columns=i.columns,
                unique=i.unique,
            )
            for i in table.indexes
        ],
        tags=table.tags,
        source=SourceMetadata(
            file=file,
            checksum=checksum,
            line_start=line_info.get("start"),
            line_end=line_info.get("end"),
            source_order=source_order,
        ),
        hash=normalizer.compute_hash(table.model_dump()),
    )


def _build_integration_target_ir(
    integration: Any,
    file: str,
    checksum: str,
    normalizer: Normalizer,
    source_order: int = 0,
) -> IntegrationTargetIR:
    from ..diagnostics.line_info_cache import get_line_info

    line_info = get_line_info(file, integration.id)
    auth_ir = None
    if integration.auth:
        auth_ir = IntegrationAuthIR(
            type=integration.auth.type,
            secret_ref=integration.auth.secret_ref,
            key_name=integration.auth.key_name,
            token_prefix=integration.auth.token_prefix,
            options=integration.auth.options,
        )
    return IntegrationTargetIR(
        id=normalizer.normalize_id(integration.id),
        type=integration.type,
        provider=getattr(integration, "provider", None),
        service=getattr(integration, "service", None),
        base_url=integration.base_url,
        auth=auth_ir,
        timeouts=_build_timeout_policy_ir(integration.timeouts),
        retry=_build_retry_policy_ir(integration.retry),
        rate_limit=_build_rate_limit_policy_ir(integration.rate_limit),
        circuit_breaker=_build_circuit_breaker_policy_ir(integration.circuit_breaker),
        headers=integration.headers,
        tags=integration.tags,
        source=SourceMetadata(
            file=file,
            checksum=checksum,
            line_start=line_info.get("start"),
            line_end=line_info.get("end"),
            source_order=source_order,
        ),
        hash=normalizer.compute_hash(integration.model_dump()),
    )


def _build_rest_api_operation_ir(
    operation: Any,
    file: str,
    checksum: str,
    normalizer: Normalizer,
    source_order: int = 0,
) -> RestApiOperationIR:
    from ..diagnostics.line_info_cache import get_line_info

    line_info = get_line_info(file, operation.id)
    return RestApiOperationIR(
        id=normalizer.normalize_id(operation.id),
        integration_id=_build_typed_ref(
            operation.integration_id, normalizer, "Integration"
        ),
        method=operation.method,
        path=operation.path,
        request_schema=[_build_field_ir(f) for f in operation.request_schema],
        response_schema=[_build_field_ir(f) for f in operation.response_schema],
        error_mapping=[
            ErrorMapIR(
                source_code=err.source_code,
                target_error=_build_typed_ref(err.target_error, normalizer, "Error"),
            )
            for err in operation.error_mapping
        ],
        source=SourceMetadata(
            file=file,
            checksum=checksum,
            line_start=line_info.get("start"),
            line_end=line_info.get("end"),
            source_order=source_order,
        ),
        hash=normalizer.compute_hash(operation.model_dump()),
    )


def _build_s3_resource_ir(
    resource: Any,
    file: str,
    checksum: str,
    normalizer: Normalizer,
    source_order: int = 0,
) -> S3ResourceIR:
    return S3ResourceIR(
        integration_id=_build_typed_ref(
            resource.integration_id, normalizer, "Integration"
        ),
        bucket=resource.bucket,
        region=resource.region,
        operations=resource.operations,
        path_template=resource.path_template,
        encryption=resource.encryption,
        source=SourceMetadata(file=file, checksum=checksum, source_order=source_order),
        hash=normalizer.compute_hash(resource.model_dump()),
    )


def _build_email_provider_ir(
    provider: Any,
    file: str,
    checksum: str,
    normalizer: Normalizer,
    source_order: int = 0,
) -> EmailProviderIR:
    return EmailProviderIR(
        id=normalizer.normalize_id(provider.id),
        transport=provider.transport,
        host=provider.host,
        port=provider.port,
        username_secret=provider.username_secret,
        password_secret=provider.password_secret,
        from_email=provider.from_email,
        from_name=provider.from_name,
        source=SourceMetadata(file=file, checksum=checksum, source_order=source_order),
        hash=normalizer.compute_hash(provider.model_dump()),
    )


def _build_oauth2_provider_ir(
    provider: Any,
    file: str,
    checksum: str,
    normalizer: Normalizer,
    source_order: int = 0,
) -> OAuth2ProviderIR:
    return OAuth2ProviderIR(
        id=normalizer.normalize_id(provider.id),
        issuer=provider.issuer,
        audience=provider.audience,
        jwks_url=provider.jwks_url,
        introspection_url=provider.introspection_url,
        client_id_secret=provider.client_id_secret,
        client_secret_secret=provider.client_secret_secret,
        scopes=provider.scopes,
        source=SourceMetadata(file=file, checksum=checksum, source_order=source_order),
        hash=normalizer.compute_hash(provider.model_dump()),
    )


def _build_webhook_endpoint_ir(
    webhook: Any,
    file: str,
    checksum: str,
    normalizer: Normalizer,
    source_order: int = 0,
) -> WebhookEndpointIR:
    signature = None
    if webhook.signature:
        signature = SignaturePolicyIR(
            alg=webhook.signature.alg,
            secret_ref=webhook.signature.secret_ref,
            header_name=webhook.signature.header_name,
        )
    return WebhookEndpointIR(
        id=normalizer.normalize_id(webhook.id),
        direction=webhook.direction,
        url_or_path=webhook.url_or_path,
        method=webhook.method,
        signature=signature,
        retries=_build_retry_policy_ir(webhook.retries),
        events=webhook.events,
        source=SourceMetadata(file=file, checksum=checksum, source_order=source_order),
        hash=normalizer.compute_hash(webhook.model_dump()),
    )


def _build_profile_ir(
    profile: Any,
    file: str,
    checksum: str,
    normalizer: Normalizer,
    source_order: int = 0,
) -> EnvironmentProfileIR:
    return EnvironmentProfileIR(
        name=profile.name,
        overrides=profile.overrides,
        tags=profile.tags,
        source=SourceMetadata(file=file, checksum=checksum, source_order=source_order),
        hash=normalizer.compute_hash(profile.model_dump()),
    )


def _build_secret_ref_ir(
    secret: Any,
    file: str,
    checksum: str,
    normalizer: Normalizer,
    source_order: int = 0,
) -> SecretRefIR:
    return SecretRefIR(
        id=normalizer.normalize_id(secret.id),
        provider=secret.provider,
        key=secret.key,
        description=secret.description,
        required=secret.required,
        tags=secret.tags,
        source=SourceMetadata(file=file, checksum=checksum, source_order=source_order),
        hash=normalizer.compute_hash(secret.model_dump()),
    )


def _build_security_baseline_ir(
    security: Any,
    file: str,
    checksum: str,
    normalizer: Normalizer,
) -> SecurityBaselineIR:
    cors = None
    if security.cors:
        cors = CorsPolicyIR(
            allowed_origins=security.cors.allowed_origins,
            allowed_methods=security.cors.allowed_methods,
            allowed_headers=security.cors.allowed_headers,
            allow_credentials=security.cors.allow_credentials,
        )
    return SecurityBaselineIR(
        auth_required=security.auth_required,
        authz_required=security.authz_required,
        cors=cors,
        rate_limits=[
            RateLimitRuleIR(
                id=r.id,
                requests=r.requests,
                per_seconds=r.per_seconds,
                scope=r.scope,
            )
            for r in security.rate_limits
        ],
        pii_masking=[
            PiiMaskingRuleIR(field=p.field, strategy=p.strategy)
            for p in security.pii_masking
        ],
        webhook_signature_required=security.webhook_signature_required,
        source=SourceMetadata(file=file, checksum=checksum),
        hash=normalizer.compute_hash(security.model_dump()),
    )


def _build_reliability_policy_ir(
    policy: Any,
    file: str,
    checksum: str,
    normalizer: Normalizer,
    source_order: int = 0,
) -> ReliabilityPolicyIR:
    target_type_map = {
        "command": "Command",
        "workflow": "Workflow",
        "integration": "Integration",
        "integration_operation": "IntegrationOperation",
    }
    return ReliabilityPolicyIR(
        id=normalizer.normalize_id(policy.id),
        target_kind=policy.target_kind,
        target_ref=_build_typed_ref(
            policy.target_ref,
            normalizer,
            target_type_map.get(policy.target_kind, "Unknown"),
        ),
        timeout=_build_timeout_policy_ir(policy.timeout),
        retry=_build_retry_policy_ir(policy.retry),
        circuit_breaker=_build_circuit_breaker_policy_ir(policy.circuit_breaker),
        idempotency_key_field=policy.idempotency_key_field,
        tags=policy.tags,
        source=SourceMetadata(file=file, checksum=checksum, source_order=source_order),
        hash=normalizer.compute_hash(policy.model_dump()),
    )


def _build_observability_target_ir(
    target: Any,
    file: str,
    checksum: str,
    normalizer: Normalizer,
    source_order: int = 0,
) -> ObservabilityTargetIR:
    target_type_map = {
        "command": "Command",
        "workflow": "Workflow",
        "integration": "Integration",
        "integration_operation": "IntegrationOperation",
        "persistence.table": "PersistenceTable",
        "persistence.datasource": "PersistenceDatasource",
    }
    return ObservabilityTargetIR(
        kind=target.kind,
        ref=_build_typed_ref(
            target.ref, normalizer, target_type_map.get(target.kind, "Unknown")
        ),
        log_fields=target.log_fields,
        metrics=target.metrics,
        trace_enabled=target.trace_enabled,
        alert_rules=target.alert_rules,
        source=SourceMetadata(file=file, checksum=checksum, source_order=source_order),
        hash=normalizer.compute_hash(target.model_dump()),
    )


def _build_contract_test_case_ir(
    test_case: Any,
    file: str,
    checksum: str,
    normalizer: Normalizer,
    source_order: int = 0,
) -> ContractTestCaseIR:
    step_type_map = {
        "command": "Command",
        "query": "Query",
        "event": "Event",
    }
    steps: list[ContractTestStepIR] = []
    for step in test_case.steps:
        ref = None
        if getattr(step, "ref", None):
            ref = _build_typed_ref(
                step.ref, normalizer, step_type_map.get(step.type, "Unknown")
            )
        steps.append(
            ContractTestStepIR(
                type=step.type,
                ref=ref,
                input=step.input,
                expect=step.expect,
            )
        )
    scenario_ref_raw = getattr(test_case, "scenario", None) or getattr(
        test_case, "scenario_id", None
    )
    scenario_ref = (
        _build_typed_ref(scenario_ref_raw, normalizer, "Scenario")
        if scenario_ref_raw
        else None
    )

    return ContractTestCaseIR(
        id=normalizer.normalize_id(test_case.id),
        kind=test_case.kind,
        framework=getattr(test_case, "framework", None),
        description=test_case.description,
        tags=test_case.tags,
        steps=steps,
        source=SourceMetadata(file=file, checksum=checksum, source_order=source_order),
        hash=normalizer.compute_hash(test_case.model_dump()),
        scenario=scenario_ref,
    )


def _build_field_ir(field: Any) -> FieldIR:
    """Build FieldIR from NamedField model."""
    return FieldIR(
        name=field.name,
        type=field.type,
        required=field.required,
        description=field.description,
        default=field.default,
        metadata=field.metadata if hasattr(field, "metadata") else {},
        constraints=field.constraints if hasattr(field, "constraints") else {},
        source_ref=field.source if hasattr(field, "source") else None,
        introduced_in=field.introduced_in if hasattr(field, "introduced_in") else None,
        deprecated_in=field.deprecated_in if hasattr(field, "deprecated_in") else None,
        replaced_by=field.replaced_by if hasattr(field, "replaced_by") else None,
        status=field.status if hasattr(field, "status") else None,
    )


def _build_index_ir(index: Any) -> IndexIR:
    """Build IndexIR from Index model."""
    return IndexIR(
        name=index.name,
        fields=index.fields,
        unique=index.unique,
    )


def _build_constraint_ir(constraint: Any) -> ConstraintIR:
    """Build ConstraintIR from Constraint model."""
    return ConstraintIR(
        type=constraint.type,
        fields=constraint.fields,
        ref=constraint.ref,
    )


def _build_guard_ir(guard: Any) -> GuardIR:
    """Build GuardIR from GuardRef model."""
    return GuardIR(
        id=guard.id,
        params=guard.params if hasattr(guard, "params") else {},
    )


def _build_effect_ir(effect: Any) -> EffectIR:
    """Build EffectIR from EffectRef model."""
    return EffectIR(
        id=effect.id,
        params=effect.params if hasattr(effect, "params") else {},
    )


def _build_ref_ir(ref_dict: dict[str, str]) -> RefIR:
    """Build RefIR from normalized reference dict."""
    return RefIR(
        type=ref_dict.get("type", "Unknown"),
        id=ref_dict.get("id", ""),
    )


def _build_typed_ref(ref: Any, normalizer: Normalizer, default_type: str) -> RefIR:
    """Build RefIR with fallback type when ref does not declare one."""
    ref_dict = normalizer.normalize_ref(ref)
    if not ref_dict.get("type") or ref_dict.get("type") == "Unknown":
        ref_dict["type"] = default_type
    return _build_ref_ir(ref_dict)


def _build_state_ir(state: Any) -> StateIR:
    """Build StateIR from WorkflowState model."""
    return StateIR(
        id=state.id,
        description=state.description,
        kind=state.kind,
    )


def _build_transition_ir(transition: Any, normalizer: Normalizer) -> TransitionIR:
    """Build TransitionIR from WorkflowTransition model."""
    return TransitionIR(
        from_state=transition.from_state,
        to_state=transition.to_state,
        on_command=(
            _build_typed_ref(transition.on_command, normalizer, "Command")
            if transition.on_command
            else None
        ),
        on_event=(
            _build_typed_ref(transition.on_event, normalizer, "Event")
            if transition.on_event
            else None
        ),
        guards=[_build_guard_ir(g) for g in transition.guards],
        effects=[_build_effect_ir(e) for e in transition.effects],
        description=getattr(transition, "description", None),
    )


def _build_error_handler_ir(handler: Any, normalizer: Normalizer) -> ErrorHandlerIR:
    """Build ErrorHandlerIR from WorkflowErrorHandler model."""
    return ErrorHandlerIR(
        error=_build_typed_ref(handler.error, normalizer, "Error"),
        action=handler.action,
        transition_to=handler.transition_to,
    )


def _build_indexes(symbol_table: SymbolTable, normalizer: Normalizer) -> IRIndexes:
    """Build IR indexes from symbol table."""
    from ..schema.ir_schema import SymbolIndex

    symbols_index = {}
    for (sym_type, sym_id), symbol in symbol_table.get_all_symbols().items():
        if sym_type not in symbols_index:
            symbols_index[sym_type] = {}

        symbols_index[sym_type][sym_id] = SymbolIndex(
            id=sym_id,
            type=sym_type,
            source_file=symbol.source_file,
            hash=_compute_symbol_hash(symbol, normalizer),
        )

    return IRIndexes(symbols=symbols_index, refs=[])


def _compute_symbol_hash(symbol: Any, normalizer: Normalizer) -> str:
    data = getattr(symbol, "data", None)
    if hasattr(data, "model_dump"):
        payload = data.model_dump()
    elif isinstance(data, dict):
        payload = data
    else:
        payload = str(data)
    try:
        return normalizer.compute_hash(payload)
    except TypeError:
        return hashlib.sha256(str(payload).encode("utf-8")).hexdigest()


def _compute_file_checksum(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def _write_ir(ir: IR, ir_path: Path, symbol_table: SymbolTable) -> None:
    """Write full IR with intent metadata to JSON file."""
    ir_dict = _build_ir_output(ir)
    _write_json(ir_path, ir_dict)


def _build_ir_output(ir: IR) -> dict[str, Any]:
    """Build full IR output with intent confidence labels and summary metadata."""
    ir_dict = ir.to_dict()

    _convert_intent_confidence_labels(ir_dict)

    meta = ir_dict.get("meta")
    if isinstance(meta, dict):
        # Remove internal-only intent stats from output schema
        meta.pop("intent", None)
        warnings = meta.get("warnings")
        if isinstance(warnings, list):
            cleaned: list[dict[str, Any]] = []
            for item in warnings:
                if isinstance(item, dict):
                    entry = {
                        "code": item.get("code"),
                        "message": item.get("message"),
                        "file": item.get("file"),
                        "line": item.get("line"),
                    }
                    # Drop keys with None to keep output compact
                    cleaned.append({k: v for k, v in entry.items() if v is not None})
            meta["warnings"] = cleaned

    return ir_dict


def _convert_intent_confidence_labels(node: Any) -> None:
    from ..analysis.intent import confidence_label

    if isinstance(node, dict):
        intent = node.get("intent")
        if isinstance(intent, dict):
            confidence = intent.get("confidence")
            if isinstance(confidence, (int, float)):
                intent["confidence"] = confidence_label(float(confidence))
            alternatives = intent.get("alternatives")
            if isinstance(alternatives, list):
                for alt in alternatives:
                    if isinstance(alt, dict):
                        alt_confidence = alt.get("confidence")
                        if isinstance(alt_confidence, (int, float)):
                            alt["confidence"] = confidence_label(float(alt_confidence))

        for value in node.values():
            _convert_intent_confidence_labels(value)
        return

    if isinstance(node, list):
        for item in node:
            _convert_intent_confidence_labels(item)


def _build_meta_warnings(reporter: ErrorReporter) -> list[Warning]:
    warnings: list[Warning] = []
    for item in reporter.warnings:
        warnings.append(
            Warning(
                stage=item.stage,
                code=item.code,
                file=item.file,
                message=item.message,
                line=item.line,
            )
        )
    return warnings


def _write_manifest(manifest: dict[str, Any], manifest_path: Path) -> None:
    """Write manifest to JSON file."""
    _write_json(manifest_path, manifest)


def _write_manifest_with_errors(
    manifest_path: Path,
    version: str,
    contracts_root: Path,
    root: Path,
    reporter: ErrorReporter,
) -> None:
    """Write manifest with error information."""
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    manifest = {
        "version": version,
        "generated_at": _utc_now(),
        "status": "failed",
        "contracts_root": str(contracts_root.relative_to(root)),
        "errors": reporter.to_dict()["errors"],
        "warnings": reporter.to_dict()["warnings"],
        "infos": reporter.to_dict().get("infos", []),
    }

    _write_json(manifest_path, manifest)


def _write_error_report(
    ir_root: Path,
    reporter: ErrorReporter,
    contracts_root: Path,
) -> None:
    """
    Write error report to log file.

    Errors, warnings, and info are written to errors.log in the IR output directory.
    File is appended with timestamp separator to preserve history.

    Args:
        ir_root: IR output directory
        reporter: Error reporter with collected errors/warnings
        contracts_root: Contract root path for context
    """
    error_log = ir_root / "errors.log"

    # Create directory if needed
    ir_root.mkdir(parents=True, exist_ok=True)

    # Prepare report content
    report_content = _format_build_report(reporter, contracts_root)

    # Append to file (or create if doesn't exist)
    mode = "a" if error_log.exists() else "w"
    with open(error_log, mode, encoding="utf-8") as f:
        f.write(report_content)


def _format_build_report(
    reporter: ErrorReporter,
    contracts_root: Path,
) -> str:
    """Format the full build report for console/file output."""
    timestamp = _utc_now()
    separator = "=" * 80
    report_lines = [
        "",
        separator,
        f"Build Report - {timestamp}",
        separator,
        "",
        reporter.format_report(
            show_warnings=True,
            show_context=True,
            contracts_root=str(contracts_root),
            show_infos=True,
        ),
        "",
    ]
    return "\n".join(report_lines)


def _print_build_report(
    reporter: ErrorReporter,
    contracts_root: Path,
) -> None:
    """Print build report to console."""
    safe_print(_format_build_report(reporter, contracts_root))


def _build_manifest(
    version: str,
    contracts_root: Path,
    ir_root: Path,
    root: Path,
    ir: IR,
    reporter: ErrorReporter,
) -> dict[str, Any]:
    """
    Build manifest data.

    Manifest includes metadata about the build, including input files,
    output files, statistics, and checksums for incremental rebuild detection.
    """
    # Collect input files with checksums (sorted for determinism)
    input_files = []
    for file_path in sorted(contracts_root.rglob("*.yaml")) + sorted(
        contracts_root.rglob("*.yml")
    ):
        # Skip hidden files and directories
        if any(part.startswith(".") for part in file_path.parts):
            continue

        input_files.append(
            {
                "path": str(file_path.relative_to(contracts_root)),
                "checksum": _compute_file_checksum(file_path),
            }
        )

    # Compute IR checksum (will be computed after IR is written)
    ir_path = ir_root / "ir.json"
    ir_checksum = None
    if ir_path.exists():
        ir_checksum = _compute_file_checksum(ir_path)

    return {
        "version": version,
        "generated_at": _utc_now(),
        "status": "success",
        "contracts_root": str(contracts_root.relative_to(root)),
        "ir_root": str(ir_root.relative_to(root)),
        "input_files": input_files,
        "ir_checksum": ir_checksum,
        "outputs": {
            "ir": str((ir_root / "ir.json").relative_to(root)),
            "manifest": str((ir_root / "manifest.json").relative_to(root)),
        },
        "stats": {
            "entities": ir.meta.stats.entities,
            "value_objects": ir.meta.stats.value_objects,
            "enums": ir.meta.stats.enums,
            "errors": ir.meta.stats.errors,
            "events": ir.meta.stats.events,
            "commands": ir.meta.stats.commands,
            "queries": ir.meta.stats.queries,
            "projections": ir.meta.stats.projections,
            "workflows": ir.meta.stats.workflows,
            "rules": ir.meta.stats.rules,
            "scenarios": ir.meta.stats.scenarios,
            "http_routes": ir.meta.stats.http_routes,
            "graphql_types": ir.meta.stats.graphql_types,
            "roles": ir.meta.stats.roles,
            "permissions": ir.meta.stats.permissions,
            "policies": ir.meta.stats.policies,
            "persistence_datasources": ir.meta.stats.persistence_datasources,
            "persistence_tables": ir.meta.stats.persistence_tables,
            "integrations": ir.meta.stats.integrations,
            "integration_operations": ir.meta.stats.integration_operations,
            "webhooks": ir.meta.stats.webhooks,
            "email_providers": ir.meta.stats.email_providers,
            "oauth2_providers": ir.meta.stats.oauth2_providers,
            "profiles": ir.meta.stats.profiles,
            "secrets": ir.meta.stats.secrets,
            "reliability_policies": ir.meta.stats.reliability_policies,
            "observability_targets": ir.meta.stats.observability_targets,
            "tests": ir.meta.stats.tests,
        },
        "warnings": reporter.to_dict()["warnings"],
        "infos": reporter.to_dict().get("infos", []),
    }


def _write_json(path: Path, payload: Any) -> None:
    """Write JSON to file."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True, ensure_ascii=False)
        f.write("\n")


def _utc_now() -> str:
    """Get current UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()
