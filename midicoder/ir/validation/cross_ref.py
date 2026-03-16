"""Cross-reference validation for DSL contracts."""

import os
from typing import Any

from midicoder.dsl.models import (
    AccessPolicyFile,
    CommandsFile,
    EntitiesFile,
    GraphQLApiFile,
    HttpApiFile,
    IntegrationsFile,
    ObservabilityFile,
    PersistenceModelFile,
    PoliciesFile,
    ProjectionsFile,
    QueriesFile,
    ReliabilityPoliciesFile,
    RulesFile,
    ScenariosFile,
    TestingFile,
    ValueObjectsFile,
    WorkflowsFile,
)

from ..diagnostics.error_codes import (
    E301,
    E302,
    E303,
    E304,
    E305,
    E306,
    E317,
    ErrorReporter,
)
from ..diagnostics.suggestions import (
    suggest_for_unresolved_entity,
    suggest_for_unresolved_error,
    suggest_for_unresolved_event,
    suggest_for_unresolved_type,
)
from ..normalize.normalizer import Normalizer
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
    SYMBOL_TYPE_ROLE,
    SYMBOL_TYPE_SCENARIO,
    SYMBOL_TYPE_SECRET,
    SYMBOL_TYPE_VALUE_OBJECT,
    SYMBOL_TYPE_WORKFLOW,
    SymbolTable,
)


class CrossRefChecker:
    """Checks cross-references between contract objects."""
    
    def __init__(self, symbol_table: SymbolTable, reporter: ErrorReporter) -> None:
        self.symbols = symbol_table
        self.reporter = reporter
        self.normalizer = Normalizer(symbol_table)
        strict_raw = os.getenv("STRICT_CROSS_REF", "").strip().lower()
        if not strict_raw:
            strict_raw = os.getenv("MIDICODER_STRICT_CROSS_REF", "").strip().lower()
        self.strict_cross_ref = strict_raw in {"1", "true", "yes", "on"}

    def _warning_severity(self) -> str:
        return "error" if self.strict_cross_ref else "warning"
    
    def check_file(self, data: Any, file: str) -> None:
        """Check cross-references in a validated file."""
        if isinstance(data, EntitiesFile):
            self._check_entities(data, file)
        elif isinstance(data, ValueObjectsFile):
            self._check_value_objects(data, file)
        elif isinstance(data, CommandsFile):
            self._check_commands(data, file)
        elif isinstance(data, QueriesFile):
            self._check_queries(data, file)
        elif isinstance(data, WorkflowsFile):
            self._check_workflows(data, file)
        elif isinstance(data, HttpApiFile):
            self._check_http_api(data, file)
        elif isinstance(data, GraphQLApiFile):
            self._check_graphql_api(data, file)
        elif isinstance(data, AccessPolicyFile):
            self._check_access_policy(data, file)
        elif isinstance(data, RulesFile):
            self._check_rules(data, file)
        elif isinstance(data, ScenariosFile):
            self._check_scenarios(data, file)
        elif isinstance(data, PoliciesFile):
            self._check_policies(data, file)
        elif isinstance(data, ProjectionsFile):
            self._check_projections(data, file)
        elif isinstance(data, PersistenceModelFile):
            self._check_persistence(data, file)
        elif isinstance(data, IntegrationsFile):
            self._check_integrations(data, file)
        elif isinstance(data, ReliabilityPoliciesFile):
            self._check_reliability(data, file)
        elif isinstance(data, ObservabilityFile):
            self._check_observability(data, file)
        elif isinstance(data, TestingFile):
            self._check_testing(data, file)
    
    def _check_entities(self, data: EntitiesFile, file: str) -> None:
        """Check field type references in entities."""
        for idx, entity in enumerate(data.entities):
            path = f"entities[{idx}]"
            self._check_field_types(entity.fields, file, f"{path}.fields")
    
    def _check_value_objects(self, data: ValueObjectsFile, file: str) -> None:
        """Check field type references in value objects."""
        for idx, vo in enumerate(data.value_objects):
            path = f"value_objects[{idx}]"
            self._check_field_types(vo.fields, file, f"{path}.fields")
    
    def _check_field_types(self, fields: list, file: str, base_path: str) -> None:
        """
        Check that field types with references (Entity:xxx, Enum:xxx) are valid.
        
        Supports formats:
        - Entity:user_id
        - ValueObject:address
        - Enum:status
        """
        for idx, field in enumerate(fields):
            field_path = f"{base_path}[{idx}]"
            field_type = field.type
            
            # Check if type contains a reference (Type:id format)
            if ':' in field_type:
                parts = field_type.split(':', 1)
                if len(parts) == 2:
                    ref_type, ref_id = parts
                    
                    # Map type names to symbol types
                    type_map = {
                        'Entity': SYMBOL_TYPE_ENTITY,
                        'ValueObject': SYMBOL_TYPE_VALUE_OBJECT,
                        'Enum': SYMBOL_TYPE_ENUM,
                        'Integration': SYMBOL_TYPE_INTEGRATION,
                        'IntegrationOperation': SYMBOL_TYPE_INTEGRATION_OPERATION,
                        'Role': SYMBOL_TYPE_ROLE,
                        'Permission': SYMBOL_TYPE_PERMISSION,
                        'Scenario': SYMBOL_TYPE_SCENARIO,
                        'PersistenceTable': SYMBOL_TYPE_PERSISTENCE_TABLE,
                        'PersistenceDatasource': SYMBOL_TYPE_PERSISTENCE_DATASOURCE,
                    }
                    
                    if ref_type in type_map:
                        symbol_type = type_map[ref_type]
                        ref_id_normalized = self._normalize_id(ref_id)

                        if not self.symbols.resolve(symbol_type, ref_id_normalized):
                            # Generate suggestion
                            suggestion = suggest_for_unresolved_type(
                                ref_type,
                                ref_id_normalized,
                                self.symbols,
                            )
                            
                            self.reporter.add_error(
                                stage="cross_ref",
                                code=E317,
                                file=file,
                                message=f"Field '{field.name}' references unknown {ref_type} '{ref_id}'",
                                path=f"{field_path}.type",
                                context={"suggestion": suggestion} if suggestion else {},
                            )
    
    def _check_commands(self, data: CommandsFile, file: str) -> None:
        """Check cross-references in commands."""
        for idx, command in enumerate(data.commands):
            path = f"commands[{idx}]"
            
            # Check field types in input and returns
            self._check_field_types(command.input, file, f"{path}.input")
            self._check_field_types(command.returns, file, f"{path}.returns")
            
            # Check fetches → Entity
            for fetch_idx, fetch_ref in enumerate(command.fetches):
                entity_id_raw, entity_id = self._extract_id_pair(fetch_ref)
                if not self.symbols.resolve(SYMBOL_TYPE_ENTITY, entity_id):
                    suggestion = suggest_for_unresolved_entity(entity_id, self.symbols)
                    
                    self.reporter.add_error(
                        stage="cross_ref",
                        code=E301,
                        file=file,
                        message=f"Command '{command.id}' references unknown entity '{entity_id_raw}'",
                        path=f"{path}.fetches[{fetch_idx}]",
                        context={"suggestion": suggestion} if suggestion else {},
                    )

            # Check RBAC links
            for role_idx, role_ref in enumerate(getattr(command, "required_roles", []) or []):
                role_raw, role_id = self._extract_id_pair(role_ref)
                if not self.symbols.resolve(SYMBOL_TYPE_ROLE, role_id):
                    self.reporter.add_error(
                        stage="cross_ref",
                        code=E305,
                        file=file,
                        message=f"Command '{command.id}' references unknown role '{role_raw}'",
                        path=f"{path}.required_roles[{role_idx}]",
                    )
            for perm_idx, perm_ref in enumerate(getattr(command, "required_permissions", []) or []):
                perm_raw, perm_id = self._extract_id_pair(perm_ref)
                if not self.symbols.resolve(SYMBOL_TYPE_PERMISSION, perm_id):
                    self.reporter.add_error(
                        stage="cross_ref",
                        code=E305,
                        file=file,
                        message=f"Command '{command.id}' references unknown permission '{perm_raw}'",
                        path=f"{path}.required_permissions[{perm_idx}]",
                    )

            # Check persistence links
            for table_idx, table_ref in enumerate(getattr(command, "writes_to", []) or []):
                table_raw, table_id = self._extract_id_pair(table_ref)
                if not self.symbols.resolve(SYMBOL_TYPE_PERSISTENCE_TABLE, table_id):
                    self.reporter.add_error(
                        stage="cross_ref",
                        code=E306,
                        file=file,
                        message=f"Command '{command.id}' references unknown persistence table '{table_raw}'",
                        path=f"{path}.writes_to[{table_idx}]",
                    )
            datasource_ref = getattr(command, "datasource", None)
            if datasource_ref:
                ds_raw, ds_id = self._extract_id_pair(datasource_ref)
                if not self.symbols.resolve(SYMBOL_TYPE_PERSISTENCE_DATASOURCE, ds_id):
                    self.reporter.add_error(
                        stage="cross_ref",
                        code=E306,
                        file=file,
                        message=f"Command '{command.id}' references unknown datasource '{ds_raw}'",
                        path=f"{path}.datasource",
                    )
            
            # Check errors → Error
            for error_idx, error_ref in enumerate(command.errors):
                error_id_raw, error_id = self._extract_id_pair(error_ref)
                if not self.symbols.resolve(SYMBOL_TYPE_ERROR, error_id):
                    suggestion = suggest_for_unresolved_error(error_id, self.symbols)
                    
                    self.reporter.add_error(
                        stage="cross_ref",
                        code=E303,
                        file=file,
                        message=f"Command '{command.id}' references unknown error '{error_id_raw}'",
                        path=f"{path}.errors[{error_idx}]",
                        context={"suggestion": suggestion} if suggestion else {},
                    )
            
            # Check emits → Event (if specified)
            for emit_idx, emit_ref in enumerate(command.emits):
                event_id_raw, event_id = self._extract_id_pair(emit_ref)
                if not self.symbols.resolve(SYMBOL_TYPE_EVENT, event_id):
                    suggestion = suggest_for_unresolved_event(event_id, self.symbols)
                    
                    # Warning only - events might be implicit from effects
                    self.reporter.add_error(
                        stage="cross_ref",
                        code=E304,
                        file=file,
                        message=f"Command '{command.id}' emits unknown event '{event_id_raw}'",
                        path=f"{path}.emits[{emit_idx}]",
                        severity=self._warning_severity(),
                        context={"suggestion": suggestion} if suggestion else {},
                    )

            for effect_idx, effect in enumerate(command.effects):
                if effect.id == "emit.event":
                    params = effect.params or {}
                    event_ref = params.get("event")
                    if event_ref:
                        event_raw, event_id = self._extract_id_pair(event_ref)
                        if not self.symbols.resolve(SYMBOL_TYPE_EVENT, event_id):
                            self.reporter.add_error(
                                stage="cross_ref",
                                code=E304,
                                file=file,
                                message=f"Command '{command.id}' emit.event references unknown event '{event_raw}'",
                                path=f"{path}.effects[{effect_idx}].params.event",
                            )
                if effect.id != "call.integration":
                    continue
                params = effect.params or {}
                target = (
                    params.get("target")
                    or params.get("integration")
                    or params.get("service")
                )
                operation_id = params.get("operation_id")

                if target:
                    target_raw, target_id = self._extract_id_pair(target)
                    if not self.symbols.resolve(SYMBOL_TYPE_INTEGRATION, target_id):
                        self.reporter.add_error(
                            stage="cross_ref",
                            code=E306,
                            file=file,
                            message=f"Command '{command.id}' references unknown integration '{target_raw}'",
                            path=f"{path}.effects[{effect_idx}].params.target",
                        )

                if operation_id:
                    op_raw, op_id = self._extract_id_pair(operation_id)
                    if not self.symbols.resolve(SYMBOL_TYPE_INTEGRATION_OPERATION, op_id):
                        self.reporter.add_error(
                            stage="cross_ref",
                            code=E306,
                            file=file,
                            message=f"Command '{command.id}' references unknown integration operation '{op_raw}'",
                            path=f"{path}.effects[{effect_idx}].params.operation_id",
                        )

            for guard_idx, guard in enumerate(command.guards):
                params = guard.params or {}
                if guard.id == "auth.role":
                    role_ref = params.get("role")
                    if role_ref:
                        role_raw, role_id = self._extract_id_pair(role_ref)
                        if not self.symbols.resolve(SYMBOL_TYPE_ROLE, role_id):
                            self.reporter.add_error(
                                stage="cross_ref",
                                code=E305,
                                file=file,
                                message=f"Command '{command.id}' auth.role references unknown role '{role_raw}'",
                                path=f"{path}.guards[{guard_idx}].params.role",
                            )
                elif guard.id == "auth.permission":
                    perm_ref = params.get("permission")
                    if perm_ref:
                        perm_raw, perm_id = self._extract_id_pair(perm_ref)
                        if not self.symbols.resolve(SYMBOL_TYPE_PERMISSION, perm_id):
                            self.reporter.add_error(
                                stage="cross_ref",
                                code=E305,
                                file=file,
                                message=f"Command '{command.id}' auth.permission references unknown permission '{perm_raw}'",
                                path=f"{path}.guards[{guard_idx}].params.permission",
                            )
    
    def _check_queries(self, data: QueriesFile, file: str) -> None:
        """Check cross-references in queries."""
        for idx, query in enumerate(data.queries):
            path = f"queries[{idx}]"
            
            # Check field types in input and returns
            self._check_field_types(query.input, file, f"{path}.input")
            self._check_field_types(query.returns, file, f"{path}.returns")
            
            # Check reads → Entity
            for read_idx, read_ref in enumerate(query.reads):
                entity_id_raw, entity_id = self._extract_id_pair(read_ref)
                if not self.symbols.resolve(SYMBOL_TYPE_ENTITY, entity_id):
                    self.reporter.add_error(
                        stage="cross_ref",
                        code=E301,
                        file=file,
                        message=f"Query '{query.id}' references unknown entity '{entity_id_raw}'",
                        path=f"{path}.reads[{read_idx}]",
                    )

            for role_idx, role_ref in enumerate(getattr(query, "required_roles", []) or []):
                role_raw, role_id = self._extract_id_pair(role_ref)
                if not self.symbols.resolve(SYMBOL_TYPE_ROLE, role_id):
                    self.reporter.add_error(
                        stage="cross_ref",
                        code=E305,
                        file=file,
                        message=f"Query '{query.id}' references unknown role '{role_raw}'",
                        path=f"{path}.required_roles[{role_idx}]",
                    )
            for perm_idx, perm_ref in enumerate(getattr(query, "required_permissions", []) or []):
                perm_raw, perm_id = self._extract_id_pair(perm_ref)
                if not self.symbols.resolve(SYMBOL_TYPE_PERMISSION, perm_id):
                    self.reporter.add_error(
                        stage="cross_ref",
                        code=E305,
                        file=file,
                        message=f"Query '{query.id}' references unknown permission '{perm_raw}'",
                        path=f"{path}.required_permissions[{perm_idx}]",
                    )
            for table_idx, table_ref in enumerate(getattr(query, "reads_from", []) or []):
                table_raw, table_id = self._extract_id_pair(table_ref)
                if not self.symbols.resolve(SYMBOL_TYPE_PERSISTENCE_TABLE, table_id):
                    self.reporter.add_error(
                        stage="cross_ref",
                        code=E306,
                        file=file,
                        message=f"Query '{query.id}' references unknown persistence table '{table_raw}'",
                        path=f"{path}.reads_from[{table_idx}]",
                    )
            datasource_ref = getattr(query, "datasource", None)
            if datasource_ref:
                ds_raw, ds_id = self._extract_id_pair(datasource_ref)
                if not self.symbols.resolve(SYMBOL_TYPE_PERSISTENCE_DATASOURCE, ds_id):
                    self.reporter.add_error(
                        stage="cross_ref",
                        code=E306,
                        file=file,
                        message=f"Query '{query.id}' references unknown datasource '{ds_raw}'",
                        path=f"{path}.datasource",
                    )
    
    def _check_workflows(self, data: WorkflowsFile, file: str) -> None:
        """Check cross-references in workflows."""
        for idx, workflow in enumerate(data.workflows):
            path = f"workflows[{idx}]"
            
            # Check entity → Entity
            entity_id_raw, entity_id = self._extract_id_pair(workflow.entity)
            if not self.symbols.resolve(SYMBOL_TYPE_ENTITY, entity_id):
                self.reporter.add_error(
                    stage="cross_ref",
                    code=E301,
                    file=file,
                    message=f"Workflow '{workflow.id}' references unknown entity '{entity_id_raw}'",
                    path=f"{path}.entity",
                )
            for scenario_idx, scenario_ref in enumerate(getattr(workflow, "scenarios", []) or []):
                scenario_raw, scenario_id = self._extract_id_pair(scenario_ref)
                if not self.symbols.resolve(SYMBOL_TYPE_SCENARIO, scenario_id):
                    self.reporter.add_error(
                        stage="cross_ref",
                        code=E302,
                        file=file,
                        message=f"Workflow '{workflow.id}' references unknown scenario '{scenario_raw}'",
                        path=f"{path}.scenarios[{scenario_idx}]",
                        severity=self._warning_severity(),
                    )

            for role_idx, role_ref in enumerate(getattr(workflow, "required_roles", []) or []):
                role_raw, role_id = self._extract_id_pair(role_ref)
                if not self.symbols.resolve(SYMBOL_TYPE_ROLE, role_id):
                    self.reporter.add_error(
                        stage="cross_ref",
                        code=E305,
                        file=file,
                        message=f"Workflow '{workflow.id}' references unknown role '{role_raw}'",
                        path=f"{path}.required_roles[{role_idx}]",
                    )
            for perm_idx, perm_ref in enumerate(getattr(workflow, "required_permissions", []) or []):
                perm_raw, perm_id = self._extract_id_pair(perm_ref)
                if not self.symbols.resolve(SYMBOL_TYPE_PERMISSION, perm_id):
                    self.reporter.add_error(
                        stage="cross_ref",
                        code=E305,
                        file=file,
                        message=f"Workflow '{workflow.id}' references unknown permission '{perm_raw}'",
                        path=f"{path}.required_permissions[{perm_idx}]",
                    )
            
            # Check transitions
            for trans_idx, transition in enumerate(workflow.transitions):
                trans_path = f"{path}.transitions[{trans_idx}]"
                
                # Check on_command → Command
                if transition.on_command:
                    cmd_id_raw, cmd_id = self._extract_id_pair(transition.on_command)
                    if not self.symbols.resolve(SYMBOL_TYPE_COMMAND, cmd_id):
                        self.reporter.add_error(
                            stage="cross_ref",
                            code=E302,
                            file=file,
                            message=f"Workflow '{workflow.id}' transition references unknown command '{cmd_id_raw}'",
                            path=f"{trans_path}.on_command",
                        )
                
                # Check on_event → Event
                if transition.on_event:
                    event_id_raw, event_id = self._extract_id_pair(transition.on_event)
                    if not self.symbols.resolve(SYMBOL_TYPE_EVENT, event_id):
                        self.reporter.add_error(
                            stage="cross_ref",
                            code=E304,
                            file=file,
                            message=f"Workflow '{workflow.id}' transition references unknown event '{event_id_raw}'",
                            path=f"{trans_path}.on_event",
                        )

                for guard_idx, guard in enumerate(transition.guards):
                    params = guard.params or {}
                    if guard.id == "auth.role":
                        role_ref = params.get("role")
                        if role_ref:
                            role_raw, role_id = self._extract_id_pair(role_ref)
                            if not self.symbols.resolve(SYMBOL_TYPE_ROLE, role_id):
                                self.reporter.add_error(
                                    stage="cross_ref",
                                    code=E305,
                                    file=file,
                                    message=f"Workflow '{workflow.id}' guard references unknown role '{role_raw}'",
                                    path=f"{trans_path}.guards[{guard_idx}].params.role",
                                )
                    elif guard.id == "auth.permission":
                        perm_ref = params.get("permission")
                        if perm_ref:
                            perm_raw, perm_id = self._extract_id_pair(perm_ref)
                            if not self.symbols.resolve(SYMBOL_TYPE_PERMISSION, perm_id):
                                self.reporter.add_error(
                                    stage="cross_ref",
                                    code=E305,
                                    file=file,
                                    message=f"Workflow '{workflow.id}' guard references unknown permission '{perm_raw}'",
                                    path=f"{trans_path}.guards[{guard_idx}].params.permission",
                                )

                for effect_idx, effect in enumerate(transition.effects):
                    params = effect.params or {}
                    if effect.id == "emit.event":
                        event_ref = params.get("event")
                        if event_ref:
                            event_raw, event_id = self._extract_id_pair(event_ref)
                            if not self.symbols.resolve(SYMBOL_TYPE_EVENT, event_id):
                                self.reporter.add_error(
                                    stage="cross_ref",
                                    code=E304,
                                    file=file,
                                    message=f"Workflow '{workflow.id}' emit.event references unknown event '{event_raw}'",
                                    path=f"{trans_path}.effects[{effect_idx}].params.event",
                                )
                    elif effect.id == "call.integration":
                        target = (
                            params.get("target")
                            or params.get("integration")
                            or params.get("service")
                        )
                        operation_id = params.get("operation_id")
                        if target:
                            target_raw, target_id = self._extract_id_pair(target)
                            if not self.symbols.resolve(SYMBOL_TYPE_INTEGRATION, target_id):
                                self.reporter.add_error(
                                    stage="cross_ref",
                                    code=E306,
                                    file=file,
                                    message=f"Workflow '{workflow.id}' references unknown integration '{target_raw}'",
                                    path=f"{trans_path}.effects[{effect_idx}].params.target",
                                )
                        if operation_id:
                            op_raw, op_id = self._extract_id_pair(operation_id)
                            if not self.symbols.resolve(SYMBOL_TYPE_INTEGRATION_OPERATION, op_id):
                                self.reporter.add_error(
                                    stage="cross_ref",
                                    code=E306,
                                    file=file,
                                    message=f"Workflow '{workflow.id}' references unknown integration operation '{op_raw}'",
                                    path=f"{trans_path}.effects[{effect_idx}].params.operation_id",
                                )
            
            # Check error_handlers
            for handler_idx, handler in enumerate(workflow.error_handlers):
                error_id_raw, error_id = self._extract_id_pair(handler.error)
                if not self.symbols.resolve(SYMBOL_TYPE_ERROR, error_id):
                    self.reporter.add_error(
                        stage="cross_ref",
                        code=E303,
                        file=file,
                        message=f"Workflow '{workflow.id}' error handler references unknown error '{error_id_raw}'",
                        path=f"{path}.error_handlers[{handler_idx}].error",
                    )
    
    def _check_http_api(self, data: HttpApiFile, file: str) -> None:
        """Check cross-references in HTTP API."""
        for idx, route in enumerate(data.routes):
            path = f"routes[{idx}]"

            cmd_id_raw = ""
            cmd_id = ""
            if route.command:
                cmd_id_raw, cmd_id = self._extract_id_pair(route.command)

            query_id_raw = ""
            query_id = ""
            if route.query:
                query_id_raw, query_id = self._extract_id_pair(route.query)

            # Check query -> Query (fallback to Command when needed)
            if query_id and not self._resolve_command_or_query(query_id):
                self.reporter.add_error(
                    stage="cross_ref",
                    code=E306,
                    file=file,
                    message=f"Route '{route.method} {route.path}' references unknown query/command '{query_id_raw}'",
                    path=f"{path}.query",
                )

            # Check command -> Command (fallback to Query when needed)
            if cmd_id and not self._resolve_command_or_query(cmd_id):
                self.reporter.add_error(
                    stage="cross_ref",
                    code=E302,
                    file=file,
                    message=f"Route '{route.method} {route.path}' references unknown command/query '{cmd_id_raw}'",
                    path=f"{path}.command",
                )

            auth_raw = (route.auth or "").strip()
            if auth_raw:
                segments = [
                    segment.strip()
                    for part in auth_raw.split("|")
                    for segment in part.split(",")
                    if segment.strip()
                ]
                for segment in segments:
                    lowered = segment.lower()
                    if lowered.startswith("role:"):
                        role_raw = segment.split(":", 1)[1].strip()
                        _, role_id = self._extract_id_pair(role_raw)
                        if not self.symbols.resolve(SYMBOL_TYPE_ROLE, role_id):
                            self.reporter.add_error(
                                stage="cross_ref",
                                code=E305,
                                file=file,
                                message=f"Route '{route.method} {route.path}' auth references unknown role '{role_raw}'",
                                path=f"{path}.auth",
                            )
                    elif lowered.startswith("permission:"):
                        perm_raw = segment.split(":", 1)[1].strip()
                        _, perm_id = self._extract_id_pair(perm_raw)
                        if not self.symbols.resolve(SYMBOL_TYPE_PERMISSION, perm_id):
                            self.reporter.add_error(
                                stage="cross_ref",
                                code=E305,
                                file=file,
                                message=f"Route '{route.method} {route.path}' auth references unknown permission '{perm_raw}'",
                                path=f"{path}.auth",
                            )
    
    def _check_rules(self, data: RulesFile, file: str) -> None:
        """Check cross-references in rules."""
        for idx, rule in enumerate(data.rules):
            path = f"rules[{idx}]"
            
            if hasattr(rule, 'applies_to') and rule.applies_to:
                target_kind = "command"
                target_ref = rule.applies_to
                if ":" in str(rule.applies_to):
                    target_kind, target_ref = [part.strip() for part in str(rule.applies_to).split(":", 1)]
                target_raw, target_id = self._extract_id_pair(target_ref)
                symbol_type = {
                    "command": SYMBOL_TYPE_COMMAND,
                    "query": SYMBOL_TYPE_QUERY,
                    "workflow": SYMBOL_TYPE_WORKFLOW,
                }.get(target_kind)
                if symbol_type is None:
                    self.reporter.add_error(
                        stage="cross_ref",
                        code=E302,
                        file=file,
                        message=f"Rule '{rule.id}' applies_to has unsupported kind '{target_kind}'",
                        path=f"{path}.applies_to",
                        severity=self._warning_severity(),
                    )
                elif not self.symbols.resolve(symbol_type, target_id):
                    self.reporter.add_error(
                        stage="cross_ref",
                        code=E302,
                        file=file,
                        message=f"Rule '{rule.id}' applies_to unknown {target_kind} '{target_raw}'",
                        path=f"{path}.applies_to",
                        severity=self._warning_severity(),
                    )
            scenario_ref = getattr(rule, "applies_to_scenario", None)
            if scenario_ref:
                scenario_raw, scenario_id = self._extract_id_pair(scenario_ref)
                if not self.symbols.resolve(SYMBOL_TYPE_SCENARIO, scenario_id):
                    self.reporter.add_error(
                        stage="cross_ref",
                        code=E302,
                        file=file,
                        message=f"Rule '{rule.id}' applies_to_scenario unknown scenario '{scenario_raw}'",
                        path=f"{path}.applies_to_scenario",
                        severity=self._warning_severity(),
                    )
    
    def _check_scenarios(self, data: ScenariosFile, file: str) -> None:
        """Check cross-references in scenarios."""
        for idx, scenario in enumerate(data.scenarios):
            path = f"scenarios[{idx}]"

            actor_refs = list(getattr(scenario, "actor_roles", []) or [])
            using_legacy_actors = False
            if not actor_refs:
                actor_refs = list(getattr(scenario, "actors", []) or [])
                using_legacy_actors = bool(actor_refs)

            if using_legacy_actors:
                self.reporter.add_error(
                    stage="cross_ref",
                    code=E305,
                    file=file,
                    message=f"Scenario '{scenario.id}' still uses legacy actors[]; migrate to actor_roles[]",
                    path=f"{path}.actors",
                    severity=self._warning_severity(),
                )

            for actor_idx, actor_ref in enumerate(actor_refs):
                actor_raw, actor_id = self._extract_id_pair(actor_ref)
                if not self.symbols.resolve(SYMBOL_TYPE_ROLE, actor_id):
                    self.reporter.add_error(
                        stage="cross_ref",
                        code=E305,
                        file=file,
                                message=f"Scenario '{scenario.id}' actor references unknown role '{actor_raw}'",
                                path=(
                                    f"{path}.actor_roles[{actor_idx}]"
                                    if not using_legacy_actors
                                    else f"{path}.actors[{actor_idx}]"
                                ),
                                severity=self._warning_severity(),
                            )
            
            # Check steps
            for step_idx, step in enumerate(scenario.steps):
                step_path = f"{path}.steps[{step_idx}]"
                
                # Depending on step type, check appropriate references
                if hasattr(step, 'ref') and step.ref:
                    ref_id_raw, ref_id = self._extract_id_pair(step.ref)
                    
                    # Try to resolve as Command first, then Query, then Event
                    if step.type == "command":
                        if not self.symbols.resolve(SYMBOL_TYPE_COMMAND, ref_id):
                            self.reporter.add_error(
                                stage="cross_ref",
                                code=E302,
                                file=file,
                                message=f"Scenario '{scenario.id}' step references unknown command '{ref_id_raw}'",
                                path=f"{step_path}.ref",
                                severity=self._warning_severity(),
                            )
                    elif step.type == "query":
                        if not self.symbols.resolve(SYMBOL_TYPE_QUERY, ref_id):
                            self.reporter.add_error(
                                stage="cross_ref",
                                code=E306,
                                file=file,
                                message=f"Scenario '{scenario.id}' step references unknown query '{ref_id_raw}'",
                                path=f"{step_path}.ref",
                                severity=self._warning_severity(),
                            )
                    elif step.type == "event":
                        if not self.symbols.resolve(SYMBOL_TYPE_EVENT, ref_id):
                            self.reporter.add_error(
                                stage="cross_ref",
                                code=E304,
                                file=file,
                                message=f"Scenario '{scenario.id}' step references unknown event '{ref_id_raw}'",
                                path=f"{step_path}.ref",
                                severity=self._warning_severity(),
                            )

    def _check_projections(self, data: ProjectionsFile, file: str) -> None:
        """Check cross-references in projections."""
        for idx, projection in enumerate(data.projections):
            path = f"projections[{idx}]"
            self._check_field_types(projection.fields, file, f"{path}.fields")

            for event_idx, event_ref in enumerate(projection.source_events):
                event_raw, event_id = self._extract_id_pair(event_ref)
                if not self.symbols.resolve(SYMBOL_TYPE_EVENT, event_id):
                    self.reporter.add_error(
                        stage="cross_ref",
                        code=E304,
                        file=file,
                        message=f"Projection '{projection.id}' references unknown event '{event_raw}'",
                        path=f"{path}.source_events[{event_idx}]",
                    )

            storage_ref = getattr(projection, "storage_ref", None) or getattr(projection, "storage", None)
            if storage_ref:
                storage_raw, storage_id = self._extract_id_pair(storage_ref)
                if not self.symbols.resolve(SYMBOL_TYPE_PERSISTENCE_TABLE, storage_id):
                    self.reporter.add_error(
                        stage="cross_ref",
                        code=E306,
                        file=file,
                        message=f"Projection '{projection.id}' references unknown persistence table '{storage_raw}'",
                        path=f"{path}.storage_ref" if getattr(projection, "storage_ref", None) else f"{path}.storage",
                    )
    
    def _check_graphql_api(self, data: GraphQLApiFile, file: str) -> None:
        """Check cross-references in GraphQL API."""
        # Check GraphQL queries
        for idx, gql_query in enumerate(data.api.queries):
            path = f"api.queries[{idx}]"
            
            # Check resolver references
            if hasattr(gql_query, 'resolver') and gql_query.resolver:
                resolver = gql_query.resolver
                
                if resolver.startswith('Command:'):
                    cmd_id_raw = resolver.split(':', 1)[1]
                    cmd_id = self._normalize_id(cmd_id_raw)
                    if not self.symbols.resolve(SYMBOL_TYPE_COMMAND, cmd_id):
                        self.reporter.add_error(
                            stage="cross_ref",
                            code=E302,
                            file=file,
                            message=f"GraphQL query '{gql_query.name}' resolver references unknown command '{cmd_id_raw}'",
                            path=f"{path}.resolver",
                        )
                elif resolver.startswith('Query:'):
                    query_id_raw = resolver.split(':', 1)[1]
                    query_id = self._normalize_id(query_id_raw)
                    if not self.symbols.resolve(SYMBOL_TYPE_QUERY, query_id):
                        self.reporter.add_error(
                            stage="cross_ref",
                            code=E306,
                            file=file,
                            message=f"GraphQL query '{gql_query.name}' resolver references unknown query '{query_id_raw}'",
                            path=f"{path}.resolver",
                        )
        
        # Check GraphQL mutations
        for idx, gql_mutation in enumerate(data.api.mutations):
            path = f"api.mutations[{idx}]"
            
            # Check resolver references
            if hasattr(gql_mutation, 'resolver') and gql_mutation.resolver:
                resolver = gql_mutation.resolver
                
                if resolver.startswith('Command:'):
                    cmd_id_raw = resolver.split(':', 1)[1]
                    cmd_id = self._normalize_id(cmd_id_raw)
                    if not self.symbols.resolve(SYMBOL_TYPE_COMMAND, cmd_id):
                        self.reporter.add_error(
                            stage="cross_ref",
                            code=E302,
                            file=file,
                            message=f"GraphQL mutation '{gql_mutation.name}' resolver references unknown command '{cmd_id_raw}'",
                            path=f"{path}.resolver",
                        )
        
        # Check GraphQL types - validate field types reference known entities
        for idx, gql_type in enumerate(data.api.types):
            path = f"api.types[{idx}]"
            
            for field_idx, field in enumerate(gql_type.fields):
                field_path = f"{path}.fields[{field_idx}]"
                
                # Check if field type references an entity
                field_type = field.type
                
                # Remove array/optional wrappers
                if field_type.startswith('Array['):
                    field_type = field_type[6:-1]
                if field_type.startswith('Optional['):
                    field_type = field_type[9:-1]
                
                # Check if it's an entity reference
                if ':' in field_type:
                    ref_type, ref_id = field_type.split(':', 1)
                    if ref_type == 'Entity':
                        ref_id_normalized = self._normalize_id(ref_id)
                        if not self.symbols.resolve(SYMBOL_TYPE_ENTITY, ref_id_normalized):
                            self.reporter.add_error(
                                stage="cross_ref",
                                code=E301,
                                file=file,
                                message=f"GraphQL type '{gql_type.name}' field '{field.name}' references unknown entity '{ref_id}'",
                                path=f"{field_path}.type",
                                severity=self._warning_severity(),
                            )
    
    def _check_access_policy(self, data: AccessPolicyFile, file: str) -> None:
        """Check cross-references in access policy."""
        # Build maps of roles and permissions for validation
        role_ids = {role.id for role in data.access.roles}
        permission_ids = {perm.id for perm in data.access.permissions}
        
        # Check bindings reference valid roles and permissions
        for idx, binding in enumerate(data.access.bindings):
            path = f"access.bindings[{idx}]"
            
            # Check role exists
            if binding.role not in role_ids:
                self.reporter.add_error(
                    stage="cross_ref",
                    code=E305,
                    file=file,
                    message=f"Binding references unknown role '{binding.role}'",
                    path=f"{path}.role",
                )
            
            # Check permissions exist
            for perm_idx, perm_id in enumerate(binding.permissions):
                if perm_id not in permission_ids:
                    self.reporter.add_error(
                        stage="cross_ref",
                        code=E305,
                        file=file,
                        message=f"Binding references unknown permission '{perm_id}'",
                        path=f"{path}.permissions[{perm_idx}]",
                    )
        
        # Check permission resources reference valid domain symbols/resources.
        for idx, perm in enumerate(data.access.permissions):
            path = f"access.permissions[{idx}]"

            if not perm.resource or ":" not in perm.resource:
                continue

            resource_kind, resource_ref = [segment.strip() for segment in perm.resource.split(":", 1)]
            lowered_kind = resource_kind.lower()
            symbol_type = {
                "entity": SYMBOL_TYPE_ENTITY,
                "command": SYMBOL_TYPE_COMMAND,
                "query": SYMBOL_TYPE_QUERY,
                "projection": SYMBOL_TYPE_PROJECTION,
            }.get(lowered_kind)

            if symbol_type is None:
                # `api:*` and `document:*` are namespaced resources, not symbol refs.
                if lowered_kind not in {"api", "document"}:
                    self.reporter.add_error(
                        stage="cross_ref",
                        code=E301,
                        file=file,
                        message=f"Permission '{perm.id}' uses unsupported resource kind '{resource_kind}'",
                        path=f"{path}.resource",
                    )
                continue

            ref_id = self._normalize_id(resource_ref)
            if not self.symbols.resolve(symbol_type, ref_id):
                self.reporter.add_error(
                    stage="cross_ref",
                    code=E301,
                    file=file,
                    message=f"Permission '{perm.id}' resource references unknown target '{resource_ref}'",
                    path=f"{path}.resource",
                    severity=self._warning_severity(),
                )
    
    def _check_policies(self, data: PoliciesFile, file: str) -> None:
        """Check cross-references in business policies."""
        # Business policies might reference entities, commands, etc.
        for idx, policy in enumerate(data.policies):
            path = f"policies[{idx}]"
            
            # Check if policy has any entity/command references in conditions
            for cond_idx, condition in enumerate(policy.conditions):
                cond_path = f"{path}.conditions[{cond_idx}]"
                
                # Check if field references an entity field
                if hasattr(condition, 'field') and condition.field:
                    field_ref = condition.field
                    
                    # Format: Entity:entity_id.field_name
                    if ':' in field_ref and '.' in field_ref:
                        entity_part, field_name = field_ref.split('.', 1)
                        if ':' in entity_part:
                            ref_type, ref_id = entity_part.split(':', 1)
                            if ref_type == 'Entity':
                                ref_id_normalized = self._normalize_id(ref_id)
                                if not self.symbols.resolve(SYMBOL_TYPE_ENTITY, ref_id_normalized):
                                    self.reporter.add_error(
                                        stage="cross_ref",
                                        code=E301,
                                        file=file,
                                        message=f"Policy '{policy.id}' condition references unknown entity '{ref_id}'",
                                        path=f"{cond_path}.field",
                                        severity=self._warning_severity(),
                                    )

    def _check_persistence(self, data: PersistenceModelFile, file: str) -> None:
        datasource_ids = {self._normalize_id(ds.id) for ds in data.datasources}
        for idx, datasource in enumerate(data.datasources):
            integration_ref = getattr(datasource, "integration_id", None)
            if not integration_ref:
                continue
            raw_id, integration_id = self._extract_id_pair(integration_ref)
            if not self.symbols.resolve(SYMBOL_TYPE_INTEGRATION, integration_id):
                self.reporter.add_error(
                    stage="cross_ref",
                    code=E306,
                    file=file,
                    message=f"Datasource '{datasource.id}' references unknown integration '{raw_id}'",
                    path=f"datasources[{idx}].integration_id",
                )
        for idx, table in enumerate(data.tables):
            if not table.datasource:
                pass
            else:
                raw_id, datasource_id = self._extract_id_pair(table.datasource)
                if datasource_id not in datasource_ids:
                    self.reporter.add_error(
                        stage="cross_ref",
                        code=E306,
                        file=file,
                        message=f"Table '{table.id}' references unknown datasource '{raw_id}'",
                        path=f"tables[{idx}].datasource",
                    )
            operation_ref = getattr(table, "operation_id", None)
            if operation_ref:
                op_raw, op_id = self._extract_id_pair(operation_ref)
                if not self.symbols.resolve(SYMBOL_TYPE_INTEGRATION_OPERATION, op_id):
                    self.reporter.add_error(
                        stage="cross_ref",
                        code=E306,
                        file=file,
                        message=f"Table '{table.id}' references unknown integration operation '{op_raw}'",
                        path=f"tables[{idx}].operation_id",
                    )

    def _check_integrations(self, data: IntegrationsFile, file: str) -> None:
        integration_ids = {self._normalize_id(i.id) for i in data.integrations}
        operation_ids = {self._normalize_id(op.id) for op in data.operations}
        for idx, operation in enumerate(data.operations):
            raw_id, integration_id = self._extract_id_pair(operation.integration_id)
            if integration_id not in integration_ids:
                self.reporter.add_error(
                    stage="cross_ref",
                    code=E306,
                    file=file,
                    message=f"Operation '{operation.id}' references unknown integration '{raw_id}'",
                    path=f"operations[{idx}].integration_id",
                )
        for idx, s3_resource in enumerate(data.s3_resources):
            raw_id, integration_id = self._extract_id_pair(s3_resource.integration_id)
            if integration_id not in integration_ids:
                self.reporter.add_error(
                    stage="cross_ref",
                    code=E306,
                    file=file,
                    message=f"S3 resource references unknown integration '{raw_id}'",
                    path=f"s3_resources[{idx}].integration_id",
                )
            for op_idx, operation_ref in enumerate(s3_resource.operations):
                op_raw, op_id = self._extract_id_pair(operation_ref)
                if op_id not in operation_ids:
                    self.reporter.add_error(
                        stage="cross_ref",
                        code=E306,
                        file=file,
                        message=f"S3 resource references unknown integration operation '{op_raw}'",
                        path=f"s3_resources[{idx}].operations[{op_idx}]",
                    )

        for idx, integration in enumerate(data.integrations):
            auth = integration.auth
            if not auth or not auth.secret_ref:
                continue
            secret_raw, secret_id = self._extract_id_pair(auth.secret_ref)
            if not self.symbols.resolve(SYMBOL_TYPE_SECRET, secret_id):
                self.reporter.add_error(
                    stage="cross_ref",
                    code=E306,
                    file=file,
                    message=f"Integration '{integration.id}' references unknown secret '{secret_raw}'",
                    path=f"integrations[{idx}].auth.secret_ref",
                )

        for idx, webhook in enumerate(data.webhooks):
            signature = webhook.signature
            if not signature or not signature.secret_ref:
                continue
            secret_raw, secret_id = self._extract_id_pair(signature.secret_ref)
            if not self.symbols.resolve(SYMBOL_TYPE_SECRET, secret_id):
                self.reporter.add_error(
                    stage="cross_ref",
                    code=E306,
                    file=file,
                    message=f"Webhook '{webhook.id}' references unknown secret '{secret_raw}'",
                    path=f"webhooks[{idx}].signature.secret_ref",
                )

        for idx, provider in enumerate(data.email_providers):
            for key in ("username_secret", "password_secret"):
                secret_ref = getattr(provider, key)
                if not secret_ref:
                    continue
                secret_raw, secret_id = self._extract_id_pair(secret_ref)
                if not self.symbols.resolve(SYMBOL_TYPE_SECRET, secret_id):
                    self.reporter.add_error(
                        stage="cross_ref",
                        code=E306,
                        file=file,
                        message=f"Email provider '{provider.id}' references unknown secret '{secret_raw}'",
                        path=f"email_providers[{idx}].{key}",
                    )

        for idx, provider in enumerate(data.oauth2_providers):
            for key in ("client_id_secret", "client_secret_secret"):
                secret_ref = getattr(provider, key)
                if not secret_ref:
                    continue
                secret_raw, secret_id = self._extract_id_pair(secret_ref)
                if not self.symbols.resolve(SYMBOL_TYPE_SECRET, secret_id):
                    self.reporter.add_error(
                        stage="cross_ref",
                        code=E306,
                        file=file,
                        message=f"OAuth2 provider '{provider.id}' references unknown secret '{secret_raw}'",
                        path=f"oauth2_providers[{idx}].{key}",
                    )

    def _check_reliability(self, data: ReliabilityPoliciesFile, file: str) -> None:
        for idx, policy in enumerate(data.reliability_policies):
            raw_id, ref_id = self._extract_id_pair(policy.target_ref)
            if policy.target_kind == "command":
                if not self.symbols.resolve(SYMBOL_TYPE_COMMAND, ref_id):
                    self.reporter.add_error(
                        stage="cross_ref",
                        code=E302,
                        file=file,
                        message=f"Reliability policy '{policy.id}' references unknown command '{raw_id}'",
                        path=f"reliability_policies[{idx}].target_ref",
                    )
            elif policy.target_kind == "workflow":
                if not self.symbols.resolve(SYMBOL_TYPE_WORKFLOW, ref_id):
                    self.reporter.add_error(
                        stage="cross_ref",
                        code=E302,
                        file=file,
                        message=f"Reliability policy '{policy.id}' references unknown workflow '{raw_id}'",
                        path=f"reliability_policies[{idx}].target_ref",
                    )
            elif policy.target_kind == "integration":
                if not self.symbols.resolve(SYMBOL_TYPE_INTEGRATION, ref_id):
                    self.reporter.add_error(
                        stage="cross_ref",
                        code=E306,
                        file=file,
                        message=f"Reliability policy '{policy.id}' references unknown integration '{raw_id}'",
                        path=f"reliability_policies[{idx}].target_ref",
                    )
            elif policy.target_kind == "integration_operation":
                if not self.symbols.resolve(SYMBOL_TYPE_INTEGRATION_OPERATION, ref_id):
                    self.reporter.add_error(
                        stage="cross_ref",
                        code=E306,
                        file=file,
                        message=f"Reliability policy '{policy.id}' references unknown integration operation '{raw_id}'",
                        path=f"reliability_policies[{idx}].target_ref",
                    )

    def _check_observability(self, data: ObservabilityFile, file: str) -> None:
        for idx, target in enumerate(data.observability):
            raw_id, ref_id = self._extract_id_pair(target.ref)
            if target.kind == "command":
                if not self.symbols.resolve(SYMBOL_TYPE_COMMAND, ref_id):
                    self.reporter.add_error(
                        stage="cross_ref",
                        code=E302,
                        file=file,
                        message=f"Observability target references unknown command '{raw_id}'",
                        path=f"observability[{idx}].ref",
                    )
            elif target.kind == "workflow":
                if not self.symbols.resolve(SYMBOL_TYPE_WORKFLOW, ref_id):
                    self.reporter.add_error(
                        stage="cross_ref",
                        code=E302,
                        file=file,
                        message=f"Observability target references unknown workflow '{raw_id}'",
                        path=f"observability[{idx}].ref",
                    )
            elif target.kind == "integration":
                if not self.symbols.resolve(SYMBOL_TYPE_INTEGRATION, ref_id):
                    self.reporter.add_error(
                        stage="cross_ref",
                        code=E306,
                        file=file,
                        message=f"Observability target references unknown integration '{raw_id}'",
                        path=f"observability[{idx}].ref",
                    )
            elif target.kind == "integration_operation":
                if not self.symbols.resolve(SYMBOL_TYPE_INTEGRATION_OPERATION, ref_id):
                    self.reporter.add_error(
                        stage="cross_ref",
                        code=E306,
                        file=file,
                        message=f"Observability target references unknown integration operation '{raw_id}'",
                        path=f"observability[{idx}].ref",
                    )
            elif target.kind == "persistence.table":
                if not self.symbols.resolve(SYMBOL_TYPE_PERSISTENCE_TABLE, ref_id):
                    self.reporter.add_error(
                        stage="cross_ref",
                        code=E306,
                        file=file,
                        message=f"Observability target references unknown persistence table '{raw_id}'",
                        path=f"observability[{idx}].ref",
                    )
            elif target.kind == "persistence.datasource":
                if not self.symbols.resolve(SYMBOL_TYPE_PERSISTENCE_DATASOURCE, ref_id):
                    self.reporter.add_error(
                        stage="cross_ref",
                        code=E306,
                        file=file,
                        message=f"Observability target references unknown persistence datasource '{raw_id}'",
                        path=f"observability[{idx}].ref",
                    )

    def _check_testing(self, data: TestingFile, file: str) -> None:
        for test_idx, test_case in enumerate(data.tests):
            scenario_ref = getattr(test_case, "scenario", None) or getattr(test_case, "scenario_id", None)
            if scenario_ref:
                raw_id, scenario_id = self._extract_id_pair(scenario_ref)
                if not self.symbols.resolve(SYMBOL_TYPE_SCENARIO, scenario_id):
                    self.reporter.add_error(
                        stage="cross_ref",
                        code=E306,
                        file=file,
                        message=f"Test case '{test_case.id}' references unknown scenario '{raw_id}'",
                        path=f"tests[{test_idx}].scenario",
                    )
            for step_idx, step in enumerate(test_case.steps):
                raw_id, ref_id = self._extract_id_pair(step.ref)
                step_path = f"tests[{test_idx}].steps[{step_idx}].ref"
                if step.type == "command":
                    if not self.symbols.resolve(SYMBOL_TYPE_COMMAND, ref_id):
                        self.reporter.add_error(
                            stage="cross_ref",
                            code=E302,
                            file=file,
                            message=f"Test step references unknown command '{raw_id}'",
                            path=step_path,
                        )
                elif step.type == "query":
                    if not self.symbols.resolve(SYMBOL_TYPE_QUERY, ref_id):
                        self.reporter.add_error(
                            stage="cross_ref",
                            code=E306,
                            file=file,
                            message=f"Test step references unknown query '{raw_id}'",
                            path=step_path,
                        )
                elif step.type == "event":
                    if not self.symbols.resolve(SYMBOL_TYPE_EVENT, ref_id):
                        self.reporter.add_error(
                            stage="cross_ref",
                            code=E304,
                            file=file,
                            message=f"Test step references unknown event '{raw_id}'",
                            path=step_path,
                        )
    
    def _extract_id(self, ref: Any) -> str:
        """
        Extract ID from a reference.
        
        Handles:
        - Simple string: "entity_id"
        - Type:ID format: "Entity:user"
        - Dict format: {"type": "Entity", "id": "user"}
        """
        if isinstance(ref, str):
            # Check if it's Type:ID format
            if ":" in ref:
                return ref.split(":", 1)[1].strip()
            return ref
        elif isinstance(ref, dict):
            return ref.get("id", "")
        return str(ref)

    def _extract_id_pair(self, ref: Any) -> tuple[str, str]:
        raw_id = self._extract_id(ref)
        return raw_id, self._normalize_id(raw_id)

    def _normalize_id(self, raw_id: str) -> str:
        if raw_id is None:
            return ""
        try:
            return self.normalizer.normalize_id(raw_id)
        except Exception:
            return raw_id

    def _resolve_command_or_query(self, ref_id: str) -> bool:
        return bool(
            self.symbols.resolve(SYMBOL_TYPE_COMMAND, ref_id)
            or self.symbols.resolve(SYMBOL_TYPE_QUERY, ref_id)
        )
