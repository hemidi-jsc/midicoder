"""Schema validation and linting for DSL contracts."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import midicoder.dsl.models as dsl_models
from pydantic import BaseModel, ValidationError

from midicoder.dsl import loader
from ..diagnostics.line_tracker import get_nested_line_number
from midicoder.dsl.catalogs import (
    AUTH_TYPE_CATALOG,
    AWS_SERVICE_CATALOG,
    AZURE_SERVICE_CATALOG,
    COMMAND_CATEGORY_CATALOG,
    CLOUD_PROVIDER_CATALOG,
    CONSTRAINT_TYPE_CATALOG,
    EMAIL_TRANSPORT_CATALOG,
    EFFECT_CATALOG,
    ENVIRONMENT_CATALOG,
    ERROR_CATEGORY_CATALOG,
    EVENT_KIND_CATALOG,
    GUARD_CATALOG,
    HTTP_METHOD_CATALOG,
    INTEGRATION_TYPE_CATALOG,
    PERSISTENCE_ENGINE_CATALOG,
    QUERY_CATEGORY_CATALOG,
    RELIABILITY_TARGET_KIND_CATALOG,
    TENANT_SCOPE_CATALOG,
    TEST_KIND_CATALOG,
    TEST_FRAMEWORK_CATALOG,
    VALUE_OBJECT_CATEGORY_CATALOG,
    WEBHOOK_SIGNATURE_ALG_CATALOG,
    GCP_SERVICE_CATALOG,
)
from midicoder.dsl.models import (
    CommandsFile,
    EntitiesFile,
    EnumsFile,
    ErrorsFile,
    EventsFile,
    HttpApiFile,
    IntegrationsFile,
    ObservabilityFile,
    PersistenceModelFile,
    ProfilesFile,
    QueriesFile,
    ReliabilityPoliciesFile,
    RulesFile,
    SecretsContractFile,
    SecurityBaselineFile,
    TestingFile,
    ValueObjectsFile,
    WorkflowsFile,
)

from ..diagnostics.error_codes import (
    E101,
    E102,
    E103,
    E201,
    E202,
    E203,
    E204,
    E205,
    E206,
    E207,
    E208,
    E209,
    E211,
    E212,
    ErrorReporter,
)


@dataclass(frozen=True)
class FileModelSpec:
    """Runtime schema descriptor for dynamic contract-file inference."""

    model_cls: type[BaseModel]
    required_root_fields: frozenset[str]
    all_root_fields: frozenset[str]


class Validator:
    """Validates DSL contracts (schema + lint)."""

    def __init__(self, reporter: ErrorReporter) -> None:
        self.reporter = reporter
        self._raw_yaml_cache: dict[str, Any] = {}
        self._file_model_specs = self._build_file_model_specs()

    def validate_file(self, file_path: Path, contracts_root: Path) -> Any | None:
        """
        Validate a single contract file.

        Returns:
            Parsed and validated data, or None if validation failed.
        """
        relative_path = str(file_path.relative_to(contracts_root))

        try:
            # Load raw YAML first (preserves line numbers from ruamel.yaml)
            raw_yaml = loader.load_yaml(file_path)
            self._raw_yaml_cache[relative_path] = raw_yaml

            # Store in global line info cache for use in IR builder
            from ..diagnostics.line_info_cache import store_raw_yaml

            store_raw_yaml(relative_path, raw_yaml)

            # Infer contract schema dynamically from file content, then validate.
            data = self._validate_with_inferred_schema(raw_yaml)
            if data is None:
                # Unknown/unmanaged YAML file: skip instead of hard-failing.
                return None

            # Run lint checks
            self._lint_file(data, relative_path, file_path)

            return data

        except ValidationError as e:
            # Schema validation error
            self._handle_validation_error(e, relative_path, file_path)
            return None
        except Exception as e:
            # Other errors (YAML syntax, IO, etc.)
            self.reporter.add_exception("schema", relative_path, e)
            return None

    def _build_file_model_specs(self) -> list[FileModelSpec]:
        """Discover all DSL `*File` schemas for runtime content-based inference."""
        specs: list[FileModelSpec] = []
        for _, value in vars(dsl_models).items():
            if not isinstance(value, type):
                continue
            if not issubclass(value, BaseModel) or value is BaseModel:
                continue
            if not value.__name__.endswith("File"):
                continue

            model_fields = getattr(value, "model_fields", {}) or {}
            all_fields = frozenset(model_fields.keys())
            if not all_fields:
                continue

            required_fields = frozenset(
                name for name, field in model_fields.items() if field.is_required()
            )
            specs.append(
                FileModelSpec(
                    model_cls=value,
                    required_root_fields=required_fields,
                    all_root_fields=all_fields,
                )
            )

        specs.sort(
            key=lambda spec: (
                -len(spec.required_root_fields),
                -len(spec.all_root_fields),
                spec.model_cls.__name__,
            )
        )
        return specs

    def _select_candidate_specs(self, raw_yaml: Any) -> list[FileModelSpec]:
        """Select likely schema candidates from YAML root keys."""
        if not isinstance(raw_yaml, dict):
            return []

        yaml_keys = set(raw_yaml.keys())
        if not yaml_keys:
            return []

        exact_required = [
            spec
            for spec in self._file_model_specs
            if spec.required_root_fields
            and spec.required_root_fields.issubset(yaml_keys)
        ]
        if exact_required:
            return exact_required

        overlap_required = [
            spec
            for spec in self._file_model_specs
            if spec.required_root_fields.intersection(yaml_keys)
        ]
        if overlap_required:
            return overlap_required

        return []

    def _preprocess_for_model(self, model_cls: type[BaseModel], payload: Any) -> Any:
        """
        Apply schema-specific normalization before model validation.

        Kept minimal and isolated so file inference stays data-driven.
        """
        if model_cls is HttpApiFile:
            return self._normalize_http_routes(payload)
        return payload

    def _validate_with_inferred_schema(self, raw_yaml: Any) -> Any | None:
        """
        Validate file content by inferring schema from DSL models.

        Returns:
            Validated Pydantic object if matched; None if file is not recognized.
        Raises:
            ValidationError: if candidates are recognized but all validations fail.
        """
        candidate_specs = self._select_candidate_specs(raw_yaml)
        if not candidate_specs:
            return None

        first_error: ValidationError | None = None
        for spec in candidate_specs:
            payload = deepcopy(raw_yaml)
            payload = self._preprocess_for_model(spec.model_cls, payload)
            try:
                return spec.model_cls.model_validate(payload)
            except ValidationError as exc:
                if first_error is None:
                    first_error = exc

        if first_error is not None:
            raise first_error

        return None

    def _normalize_http_routes(self, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        routes = data.get("routes")
        if not isinstance(routes, list):
            return data
        for route in routes:
            if not isinstance(route, dict):
                continue
            # Normalize empty strings to None-equivalent by dropping keys so
            # HttpRoute validator can evaluate XOR(command, query) correctly.
            command_value = route.get("command")
            if isinstance(command_value, str) and not command_value.strip():
                route.pop("command", None)
            query_value = route.get("query")
            if isinstance(query_value, str) and not query_value.strip():
                route.pop("query", None)

            # Legacy compatibility: accept "action" as command alias only when
            # route does not already provide command/query.
            if "command" not in route and "query" not in route:
                action_value = route.get("action")
                if isinstance(action_value, str) and action_value.strip():
                    route["command"] = action_value.strip()
        return data

    def _handle_validation_error(
        self, error: ValidationError, file: str, file_path: Path
    ) -> None:
        """Handle Pydantic validation errors."""
        for err in error.errors():
            loc = ".".join(str(x) for x in err["loc"])
            msg = err["msg"]
            err_type = err["type"]

            # Map Pydantic error types to our codes
            if "missing" in err_type:
                code = E101
            elif "type_error" in err_type:
                code = E102
            elif "extra_forbidden" in err_type:
                code = E103
            else:
                code = E102  # Default to invalid type

            # Try to extract line number from raw YAML
            line_number = None
            if file in self._raw_yaml_cache:
                raw_yaml = self._raw_yaml_cache[file]
                line_number = get_nested_line_number(raw_yaml, loc)

            self.reporter.add_error(
                stage="schema",
                code=code,
                file=file,
                message=f"{msg} at {loc}",
                path=loc,
                line=line_number,
            )

    def _lint_file(self, data: Any, file: str, file_path: Path) -> None:
        """Run lint checks on validated data."""
        if isinstance(data, EntitiesFile):
            self._lint_entities(data, file)
        elif isinstance(data, ValueObjectsFile):
            self._lint_value_objects(data, file)
        elif isinstance(data, EnumsFile):
            self._lint_enums(data, file)
        elif isinstance(data, ErrorsFile):
            self._lint_errors(data, file)
        elif isinstance(data, EventsFile):
            self._lint_events(data, file)
        elif isinstance(data, CommandsFile):
            self._lint_commands(data, file)
        elif isinstance(data, QueriesFile):
            self._lint_queries(data, file)
        elif isinstance(data, WorkflowsFile):
            self._lint_workflows(data, file)
        elif isinstance(data, HttpApiFile):
            self._lint_http_api(data, file)
        elif isinstance(data, PersistenceModelFile):
            self._lint_persistence(data, file)
        elif isinstance(data, IntegrationsFile):
            self._lint_integrations(data, file)
        elif isinstance(data, ProfilesFile):
            self._lint_profiles(data, file)
        elif isinstance(data, SecretsContractFile):
            self._lint_secrets_contract(data, file)
        elif isinstance(data, ReliabilityPoliciesFile):
            self._lint_reliability(data, file)
        elif isinstance(data, ObservabilityFile):
            self._lint_observability(data, file)
        elif isinstance(data, TestingFile):
            self._lint_testing(data, file)
        elif isinstance(data, SecurityBaselineFile):
            self._lint_security_baseline(data, file)

    def _lint_entities(self, data: EntitiesFile, file: str) -> None:
        """Lint entity definitions."""
        seen_ids = set()

        for idx, entity in enumerate(data.entities):
            path = f"entities[{idx}]"
            line = self._get_line_for_path(file, path)

            # Check duplicate IDs
            if entity.id in seen_ids:
                self.reporter.add_error(
                    stage="lint",
                    code=E201,
                    file=file,
                    message=f"Duplicate entity ID: {entity.id}",
                    path=path,
                    line=line,
                )
            seen_ids.add(entity.id)

            # Check field names unique
            self._check_field_names_unique(entity.fields, file, f"{path}.fields")

            # Check primary_key exists in fields
            if entity.primary_key:
                field_names = {f.name for f in entity.fields}
                if entity.primary_key not in field_names:
                    pk_line = self._get_line_for_path(file, f"{path}.primary_key")
                    self.reporter.add_error(
                        stage="lint",
                        code=E203,
                        file=file,
                        message=f"Primary key '{entity.primary_key}' not found in fields",
                        path=f"{path}.primary_key",
                        line=pk_line,
                    )

            # Check indexes reference valid fields
            field_names = {f.name for f in entity.fields}
            for idx_idx, index in enumerate(entity.indexes):
                for field_name in index.fields:
                    if field_name not in field_names:
                        index_line = self._get_line_for_path(
                            file, f"{path}.indexes[{idx_idx}]"
                        )
                        self.reporter.add_error(
                            stage="lint",
                            code=E204,
                            file=file,
                            message=f"Index field '{field_name}' not found in entity fields",
                            path=f"{path}.indexes[{idx_idx}]",
                            line=index_line,
                        )

            # Check constraints reference valid fields
            for const_idx, constraint in enumerate(entity.constraints):
                # Check constraint type
                if constraint.type not in CONSTRAINT_TYPE_CATALOG:
                    self.reporter.add_error(
                        stage="lint",
                        code=E212,
                        file=file,
                        message=f"Invalid constraint type: {constraint.type}. Must be one of: {CONSTRAINT_TYPE_CATALOG}",
                        path=f"{path}.constraints[{const_idx}].type",
                    )

                for field_name in constraint.fields:
                    if field_name not in field_names:
                        self.reporter.add_error(
                            stage="lint",
                            code=E205,
                            file=file,
                            message=f"Constraint field '{field_name}' not found in entity fields",
                            path=f"{path}.constraints[{const_idx}]",
                        )

            # Check tenant_scope if present
            if entity.tenant_scope and entity.tenant_scope not in TENANT_SCOPE_CATALOG:
                self.reporter.add_error(
                    stage="lint",
                    code=E211,
                    file=file,
                    message=f"Invalid tenant_scope: {entity.tenant_scope}. Must be one of: {TENANT_SCOPE_CATALOG}",
                    path=f"{path}.tenant_scope",
                )

    def _lint_value_objects(self, data: ValueObjectsFile, file: str) -> None:
        """Lint value object definitions."""
        seen_ids = set()

        for idx, vo in enumerate(data.value_objects):
            path = f"value_objects[{idx}]"

            # Check duplicate IDs
            if vo.id in seen_ids:
                self.reporter.add_error(
                    stage="lint",
                    code=E201,
                    file=file,
                    message=f"Duplicate value object ID: {vo.id}",
                    path=path,
                )
            seen_ids.add(vo.id)

            # Check field names unique
            self._check_field_names_unique(vo.fields, file, f"{path}.fields")

            # Check category if present
            if vo.category and vo.category not in VALUE_OBJECT_CATEGORY_CATALOG:
                self.reporter.add_error(
                    stage="lint",
                    code=E206,
                    file=file,
                    message=f"Invalid category: {vo.category}. Must be one of: {VALUE_OBJECT_CATEGORY_CATALOG}",
                    path=f"{path}.category",
                )

    def _lint_enums(self, data: EnumsFile, file: str) -> None:
        """Lint enum definitions."""
        seen_ids = set()

        for idx, enum in enumerate(data.enums):
            path = f"enums[{idx}]"

            # Check duplicate IDs
            if enum.id in seen_ids:
                self.reporter.add_error(
                    stage="lint",
                    code=E201,
                    file=file,
                    message=f"Duplicate enum ID: {enum.id}",
                    path=path,
                )
            seen_ids.add(enum.id)

            # Check values non-empty and unique
            if not enum.values:
                self.reporter.add_error(
                    stage="lint",
                    code=E102,
                    file=file,
                    message=f"Enum '{enum.id}' has no values",
                    path=f"{path}.values",
                )
            else:
                seen_values = set()
                for value in enum.values:
                    if value in seen_values:
                        self.reporter.add_error(
                            stage="lint",
                            code=E201,
                            file=file,
                            message=f"Duplicate enum value: {value}",
                            path=f"{path}.values",
                        )
                    seen_values.add(value)

    def _lint_errors(self, data: ErrorsFile, file: str) -> None:
        """Lint error definitions."""
        seen_ids = set()

        for idx, error in enumerate(data.errors):
            path = f"errors[{idx}]"

            # Check duplicate IDs
            if error.id in seen_ids:
                self.reporter.add_error(
                    stage="lint",
                    code=E201,
                    file=file,
                    message=f"Duplicate error ID: {error.id}",
                    path=path,
                )
            seen_ids.add(error.id)

            # Check category if present
            if error.category and error.category not in ERROR_CATEGORY_CATALOG:
                self.reporter.add_error(
                    stage="lint",
                    code=E206,
                    file=file,
                    message=f"Invalid category: {error.category}. Must be one of: {ERROR_CATEGORY_CATALOG}",
                    path=f"{path}.category",
                )

    def _lint_events(self, data: EventsFile, file: str) -> None:
        """Lint event definitions."""
        seen_ids = set()

        for idx, event in enumerate(data.events):
            path = f"events[{idx}]"

            # Check duplicate IDs
            if event.id in seen_ids:
                self.reporter.add_error(
                    stage="lint",
                    code=E201,
                    file=file,
                    message=f"Duplicate event ID: {event.id}",
                    path=path,
                )
            seen_ids.add(event.id)

            # Check kind if present
            if event.kind and event.kind not in EVENT_KIND_CATALOG:
                self.reporter.add_error(
                    stage="lint",
                    code=E206,
                    file=file,
                    message=f"Invalid kind: {event.kind}. Must be one of: {EVENT_KIND_CATALOG}",
                    path=f"{path}.kind",
                )

    def _lint_commands(self, data: CommandsFile, file: str) -> None:
        """Lint command definitions."""
        seen_ids = set()

        for idx, command in enumerate(data.commands):
            path = f"commands[{idx}]"

            # Check duplicate IDs
            if command.id in seen_ids:
                self.reporter.add_error(
                    stage="lint",
                    code=E201,
                    file=file,
                    message=f"Duplicate command ID: {command.id}",
                    path=path,
                )
            seen_ids.add(command.id)

            # Check field names unique in input and returns
            self._check_field_names_unique(command.input, file, f"{path}.input")
            self._check_field_names_unique(command.returns, file, f"{path}.returns")

            # Check category if present
            if command.category and command.category not in COMMAND_CATEGORY_CATALOG:
                self.reporter.add_error(
                    stage="lint",
                    code=E206,
                    file=file,
                    message=f"Invalid category: {command.category}. Must be one of: {COMMAND_CATEGORY_CATALOG}",
                    path=f"{path}.category",
                )

            # Check tenant_scope if present
            if (
                command.tenant_scope
                and command.tenant_scope not in TENANT_SCOPE_CATALOG
            ):
                self.reporter.add_error(
                    stage="lint",
                    code=E211,
                    file=file,
                    message=f"Invalid tenant_scope: {command.tenant_scope}. Must be one of: {TENANT_SCOPE_CATALOG}",
                    path=f"{path}.tenant_scope",
                )

            # Check guards have valid IDs
            for guard_idx, guard in enumerate(command.guards):
                if guard.id not in GUARD_CATALOG:
                    self.reporter.add_error(
                        stage="lint",
                        code=E207,
                        file=file,
                        message=f"Invalid guard ID: {guard.id}. Must be one of: {GUARD_CATALOG}",
                        path=f"{path}.guards[{guard_idx}]",
                        severity="warning",  # Warning, not error
                    )

            # Check effects have valid IDs
            for effect_idx, effect in enumerate(command.effects):
                if effect.id not in EFFECT_CATALOG:
                    self.reporter.add_error(
                        stage="lint",
                        code=E208,
                        file=file,
                        message=f"Invalid effect ID: {effect.id}. Must be one of: {EFFECT_CATALOG}",
                        path=f"{path}.effects[{effect_idx}]",
                        severity="warning",  # Warning, not error
                    )

    def _lint_queries(self, data: QueriesFile, file: str) -> None:
        """Lint query definitions."""
        seen_ids = set()

        for idx, query in enumerate(data.queries):
            path = f"queries[{idx}]"

            # Check duplicate IDs
            if query.id in seen_ids:
                self.reporter.add_error(
                    stage="lint",
                    code=E201,
                    file=file,
                    message=f"Duplicate query ID: {query.id}",
                    path=path,
                )
            seen_ids.add(query.id)

            # Check field names unique in input and returns
            self._check_field_names_unique(query.input, file, f"{path}.input")
            self._check_field_names_unique(query.returns, file, f"{path}.returns")

            # Check category if present
            if query.category and query.category not in QUERY_CATEGORY_CATALOG:
                self.reporter.add_error(
                    stage="lint",
                    code=E206,
                    file=file,
                    message=f"Invalid category: {query.category}. Must be one of: {QUERY_CATEGORY_CATALOG}",
                    path=f"{path}.category",
                )

    def _lint_workflows(self, data: WorkflowsFile, file: str) -> None:
        """Lint workflow definitions."""
        seen_ids = set()

        for idx, workflow in enumerate(data.workflows):
            path = f"workflows[{idx}]"

            # Check duplicate IDs
            if workflow.id in seen_ids:
                self.reporter.add_error(
                    stage="lint",
                    code=E201,
                    file=file,
                    message=f"Duplicate workflow ID: {workflow.id}",
                    path=path,
                )
            seen_ids.add(workflow.id)

            # Check state IDs unique
            state_ids = set()
            for state_idx, state in enumerate(workflow.states):
                if state.id in state_ids:
                    self.reporter.add_error(
                        stage="lint",
                        code=E201,
                        file=file,
                        message=f"Duplicate state ID: {state.id}",
                        path=f"{path}.states[{state_idx}]",
                    )
                state_ids.add(state.id)

            # Check initial_state exists
            if workflow.initial_state not in state_ids:
                self.reporter.add_error(
                    stage="lint",
                    code=E209,
                    file=file,
                    message=f"Initial state '{workflow.initial_state}' not found in states",
                    path=f"{path}.initial_state",
                )

            # Check transitions reference valid states
            for trans_idx, transition in enumerate(workflow.transitions):
                if transition.from_state not in state_ids:
                    self.reporter.add_error(
                        stage="lint",
                        code=E209,
                        file=file,
                        message=f"Transition from_state '{transition.from_state}' not found in states",
                        path=f"{path}.transitions[{trans_idx}].from_state",
                    )

                if transition.to_state not in state_ids:
                    self.reporter.add_error(
                        stage="lint",
                        code=E209,
                        file=file,
                        message=f"Transition to_state '{transition.to_state}' not found in states",
                        path=f"{path}.transitions[{trans_idx}].to_state",
                    )

    def _lint_http_api(self, data: HttpApiFile, file: str) -> None:
        """Lint HTTP API definitions."""
        seen_paths = set()

        for idx, route in enumerate(data.routes):
            path = f"routes[{idx}]"

            # Check method valid
            if route.method not in HTTP_METHOD_CATALOG:
                self.reporter.add_error(
                    stage="lint",
                    code=E206,
                    file=file,
                    message=f"Invalid HTTP method: {route.method}. Must be one of: {HTTP_METHOD_CATALOG}",
                    path=f"{path}.method",
                )

            # Check path format
            if not route.path.startswith("/"):
                self.reporter.add_error(
                    stage="lint",
                    code=E102,
                    file=file,
                    message=f"Route path must start with '/': {route.path}",
                    path=f"{path}.path",
                )

            # Check duplicate routes (method + path)
            route_key = f"{route.method} {route.path}"
            if route_key in seen_paths:
                self.reporter.add_error(
                    stage="lint",
                    code=E201,
                    file=file,
                    message=f"Duplicate route: {route_key}",
                    path=path,
                )
            seen_paths.add(route_key)

    def _lint_persistence(self, data: PersistenceModelFile, file: str) -> None:
        seen_ds: set[str] = set()
        for idx, ds in enumerate(data.datasources):
            path = f"datasources[{idx}]"
            if ds.id in seen_ds:
                self.reporter.add_error(
                    stage="lint",
                    code=E201,
                    file=file,
                    message=f"Duplicate datasource id: {ds.id}",
                    path=f"{path}.id",
                )
            seen_ds.add(ds.id)
            if ds.engine not in PERSISTENCE_ENGINE_CATALOG:
                self.reporter.add_error(
                    stage="lint",
                    code=E206,
                    file=file,
                    message=f"Invalid persistence engine: {ds.engine}",
                    path=f"{path}.engine",
                )

        table_columns: dict[str, set[str]] = {}
        for t_idx, table in enumerate(data.tables):
            t_path = f"tables[{t_idx}]"
            if table.datasource and table.datasource not in seen_ds:
                self.reporter.add_error(
                    stage="lint",
                    code=E203,
                    file=file,
                    message=f"Unknown datasource: {table.datasource}",
                    path=f"{t_path}.datasource",
                )
            elif not table.datasource and seen_ds:
                self.reporter.add_error(
                    stage="lint",
                    code=E101,
                    file=file,
                    message="datasource is required when datasources are declared",
                    path=f"{t_path}.datasource",
                )
            cols: set[str] = set()
            for c_idx, col in enumerate(table.columns):
                c_path = f"{t_path}.columns[{c_idx}]"
                if col.name in cols:
                    self.reporter.add_error(
                        stage="lint",
                        code=E202,
                        file=file,
                        message=f"Duplicate column name: {col.name}",
                        path=f"{c_path}.name",
                    )
                cols.add(col.name)
            table_columns[table.id] = cols
            for i_idx, index in enumerate(table.indexes):
                i_path = f"{t_path}.indexes[{i_idx}]"
                for col_name in index.columns:
                    if col_name not in cols:
                        self.reporter.add_error(
                            stage="lint",
                            code=E204,
                            file=file,
                            message=f"Index column '{col_name}' not found in table '{table.id}'",
                            path=f"{i_path}.columns",
                        )

        for t_idx, table in enumerate(data.tables):
            t_path = f"tables[{t_idx}]"
            for c_idx, col in enumerate(table.columns):
                fk = col.constraints.get("foreign_key")
                if not isinstance(fk, dict):
                    continue
                ref_table = fk.get("table")
                ref_col = fk.get("column")
                if ref_table not in table_columns:
                    self.reporter.add_error(
                        stage="lint",
                        code=E205,
                        file=file,
                        message=f"foreign_key table '{ref_table}' not found",
                        path=f"{t_path}.columns[{c_idx}].constraints.foreign_key.table",
                    )
                elif ref_col not in table_columns.get(ref_table, set()):
                    self.reporter.add_error(
                        stage="lint",
                        code=E205,
                        file=file,
                        message=f"foreign_key column '{ref_col}' not found on '{ref_table}'",
                        path=f"{t_path}.columns[{c_idx}].constraints.foreign_key.column",
                    )

    def _lint_integrations(self, data: IntegrationsFile, file: str) -> None:
        integration_ids: set[str] = set()
        for idx, integration in enumerate(data.integrations):
            path = f"integrations[{idx}]"
            if integration.id in integration_ids:
                self.reporter.add_error(
                    stage="lint",
                    code=E201,
                    file=file,
                    message=f"Duplicate integration id: {integration.id}",
                    path=f"{path}.id",
                )
            integration_ids.add(integration.id)
            if integration.type not in INTEGRATION_TYPE_CATALOG:
                self.reporter.add_error(
                    stage="lint",
                    code=E206,
                    file=file,
                    message=f"Invalid integration type: {integration.type}",
                    path=f"{path}.type",
                )
            if (
                integration.provider
                and integration.provider not in CLOUD_PROVIDER_CATALOG
            ):
                self.reporter.add_error(
                    stage="lint",
                    code=E206,
                    file=file,
                    message=f"Invalid cloud provider: {integration.provider}",
                    path=f"{path}.provider",
                )
            if (
                integration.provider == "aws"
                and integration.service
                and integration.service not in AWS_SERVICE_CATALOG
            ):
                self.reporter.add_error(
                    stage="lint",
                    code=E206,
                    file=file,
                    message=f"Invalid AWS service: {integration.service}",
                    path=f"{path}.service",
                )
            if (
                integration.provider == "gcp"
                and integration.service
                and integration.service not in GCP_SERVICE_CATALOG
            ):
                self.reporter.add_error(
                    stage="lint",
                    code=E206,
                    file=file,
                    message=f"Invalid GCP service: {integration.service}",
                    path=f"{path}.service",
                )
            if (
                integration.provider == "azure"
                and integration.service
                and integration.service not in AZURE_SERVICE_CATALOG
            ):
                self.reporter.add_error(
                    stage="lint",
                    code=E206,
                    file=file,
                    message=f"Invalid Azure service: {integration.service}",
                    path=f"{path}.service",
                )
            if integration.auth and integration.auth.type not in AUTH_TYPE_CATALOG:
                self.reporter.add_error(
                    stage="lint",
                    code=E206,
                    file=file,
                    message=f"Invalid auth type: {integration.auth.type}",
                    path=f"{path}.auth.type",
                )

        for idx, operation in enumerate(data.operations):
            if operation.integration_id not in integration_ids:
                self.reporter.add_error(
                    stage="lint",
                    code=E203,
                    file=file,
                    message=f"Unknown integration reference: {operation.integration_id}",
                    path=f"operations[{idx}].integration_id",
                )

        for idx, webhook in enumerate(data.webhooks):
            if (
                webhook.signature
                and webhook.signature.alg not in WEBHOOK_SIGNATURE_ALG_CATALOG
            ):
                self.reporter.add_error(
                    stage="lint",
                    code=E206,
                    file=file,
                    message=f"Invalid webhook signature algorithm: {webhook.signature.alg}",
                    path=f"webhooks[{idx}].signature.alg",
                )

        for idx, provider in enumerate(data.email_providers):
            if provider.transport not in EMAIL_TRANSPORT_CATALOG:
                self.reporter.add_error(
                    stage="lint",
                    code=E206,
                    file=file,
                    message=f"Invalid email transport: {provider.transport}",
                    path=f"email_providers[{idx}].transport",
                )

    def _lint_profiles(self, data: ProfilesFile, file: str) -> None:
        names: set[str] = set()
        for idx, profile in enumerate(data.profiles):
            path = f"profiles[{idx}]"
            if profile.name in names:
                self.reporter.add_error(
                    stage="lint",
                    code=E201,
                    file=file,
                    message=f"Duplicate profile name: {profile.name}",
                    path=f"{path}.name",
                )
            names.add(profile.name)
            if profile.name not in ENVIRONMENT_CATALOG:
                self.reporter.add_error(
                    stage="lint",
                    code=E206,
                    file=file,
                    message=f"Unknown environment profile: {profile.name}",
                    path=f"{path}.name",
                )

    def _lint_secrets_contract(self, data: SecretsContractFile, file: str) -> None:
        ids: set[str] = set()
        from midicoder.dsl.catalogs import SECRET_PROVIDER_CATALOG

        for idx, secret in enumerate(data.secrets):
            path = f"secrets[{idx}]"
            if secret.id in ids:
                self.reporter.add_error(
                    stage="lint",
                    code=E201,
                    file=file,
                    message=f"Duplicate secret id: {secret.id}",
                    path=f"{path}.id",
                )
            ids.add(secret.id)
            if secret.provider not in SECRET_PROVIDER_CATALOG:
                self.reporter.add_error(
                    stage="lint",
                    code=E206,
                    file=file,
                    message=f"Invalid secret provider: {secret.provider}",
                    path=f"{path}.provider",
                )

    def _lint_reliability(self, data: ReliabilityPoliciesFile, file: str) -> None:
        ids: set[str] = set()
        for idx, policy in enumerate(data.reliability_policies):
            path = f"reliability_policies[{idx}]"
            if policy.id in ids:
                self.reporter.add_error(
                    stage="lint",
                    code=E201,
                    file=file,
                    message=f"Duplicate reliability policy id: {policy.id}",
                    path=f"{path}.id",
                )
            ids.add(policy.id)
            if policy.target_kind not in RELIABILITY_TARGET_KIND_CATALOG:
                self.reporter.add_error(
                    stage="lint",
                    code=E206,
                    file=file,
                    message=f"Invalid reliability target_kind: {policy.target_kind}",
                    path=f"{path}.target_kind",
                )

    def _lint_observability(self, data: ObservabilityFile, file: str) -> None:
        for idx, target in enumerate(data.observability):
            if not target.kind:
                self.reporter.add_error(
                    stage="lint",
                    code=E102,
                    file=file,
                    message="observability target kind is required",
                    path=f"observability[{idx}].kind",
                )

    def _lint_testing(self, data: TestingFile, file: str) -> None:
        ids: set[str] = set()
        for idx, test in enumerate(data.tests):
            path = f"tests[{idx}]"
            if test.id in ids:
                self.reporter.add_error(
                    stage="lint",
                    code=E201,
                    file=file,
                    message=f"Duplicate test id: {test.id}",
                    path=f"{path}.id",
                )
            ids.add(test.id)
            if test.kind not in TEST_KIND_CATALOG:
                self.reporter.add_error(
                    stage="lint",
                    code=E206,
                    file=file,
                    message=f"Invalid test kind: {test.kind}",
                    path=f"{path}.kind",
                )
            if test.framework and test.framework not in TEST_FRAMEWORK_CATALOG:
                self.reporter.add_error(
                    stage="lint",
                    code=E206,
                    file=file,
                    message=f"Invalid test framework: {test.framework}",
                    path=f"{path}.framework",
                )
            if test.framework in {"pytest", "jest"} and test.kind != "unit":
                self.reporter.add_error(
                    stage="lint",
                    code=E206,
                    file=file,
                    message=f"{test.framework} is restricted to unit tests for coverage",
                    path=f"{path}.kind",
                )
            if test.framework == "selenium" and test.kind != "e2e":
                self.reporter.add_error(
                    stage="lint",
                    code=E206,
                    file=file,
                    message="selenium should be used for e2e tests",
                    path=f"{path}.kind",
                )

    def _lint_security_baseline(self, data: SecurityBaselineFile, file: str) -> None:
        for idx, rule in enumerate(data.security.rate_limits):
            if rule.requests <= 0 or rule.per_seconds <= 0:
                self.reporter.add_error(
                    stage="lint",
                    code=E102,
                    file=file,
                    message="rate limit values must be positive",
                    path=f"security.rate_limits[{idx}]",
                )

    def _check_field_names_unique(self, fields: list, file: str, path: str) -> None:
        """Check that field names are unique."""
        seen_names = set()
        for idx, field in enumerate(fields):
            if field.name in seen_names:
                line_number = self._get_line_for_path(file, f"{path}[{idx}]")
                self.reporter.add_error(
                    stage="lint",
                    code=E202,
                    file=file,
                    message=f"Duplicate field name: {field.name}",
                    path=f"{path}[{idx}]",
                    line=line_number,
                )
            seen_names.add(field.name)

    def _get_line_for_path(self, file: str, path: str) -> int | None:
        """Get line number for a specific path in the file."""
        if file in self._raw_yaml_cache:
            raw_yaml = self._raw_yaml_cache[file]
            return get_nested_line_number(raw_yaml, path)
        return None
