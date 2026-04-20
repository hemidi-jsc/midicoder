"""
MIR Builder cho Midicoder v1.0.0

Module này định nghĩa MIRBuilder - xây dựng MIR từ expanded CapabilityGraph.

Theo Rule 4 trong MIDICODER_STRATEGY.md:
- MIR là implementation truth, không phải pseudo text
- MIR phải chứa: ops, data flow, effect flow, transaction boundaries
- MIR target-agnostic, file-agnostic, patch-agnostic
- MIR là input bắt buộc cho emitter

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from typing import Any

from .expansion import ExpansionEngine, ExpansionReport
from .graph import CapabilityGraph, CapabilityInstance
from .artifact import ArtifactMetadata
from .mir import (
    MIR,
    MIROperation,
    MIRDataFlow,
    MIREffectFlow,
    MIRBoundary,
)


# ============================================================================
# MIR Builder
# ============================================================================


class MIRBuilder:
    """
    MIR Builder - Xây dựng MIR từ expanded CapabilityGraph.

    Theo Rule 4: MIR là implementation truth typed cho code generation.
    Builder này thực hiện:
    - Build operations từ core capability instances
    - Build data flows từ input/output references
    - Build effect flows từ events và side effects
    - Build boundaries từ transaction, auth, tenant scopes

    Attributes:
        _engine: ExpansionEngine để expand macros nếu cần
        _mir_counter: Counter để generate unique IDs cho MIR elements

    Example:
        builder = MIRBuilder()
        mir = builder.build_from_graph(graph, instance)
        assert mir.validate() == []  # Valid MIR
    """

    def __init__(self) -> None:
        """
        Khởi tạo MIRBuilder.

        Tạo expansion engine và reset counter.
        """
        # Expansion engine để expand macros nếu cần
        self._engine = ExpansionEngine()
        # Counter để generate unique IDs cho MIR elements
        self._mir_counter: int = 0

    def build_from_graph(
        self,
        graph: CapabilityGraph,
        instance: CapabilityInstance,
    ) -> MIR:
        """
        Build MIR từ expanded CapabilityGraph cho một capability instance.

        Đây là deterministic build, không dùng LLM.
        Quy trình:
        1. Expand macro instances thành core instances (nếu cần)
        2. Build operations từ core instances
        3. Build data flows
        4. Build effect flows
        5. Build boundaries
        6. Return MIR

        Args:
            graph: CapabilityGraph chứa instances và macros
            instance: CapabilityInstance cần build MIR

        Returns:
            MIR với đầy đủ ops, data flows, effect flows, boundaries
        """
        # Kiểm tra và expand nếu instance là macro
        expanded_instances = self._ensure_expanded(graph, instance)

        # Tạo MIR mới
        mir = MIR(
            ir_ref=f"Capability.{instance.id}",
            description=instance.description,
        )
        # Set metadata sau khi tạo (do ArtifactBase.metadata có init=False)
        object.__setattr__(mir, 'metadata', ArtifactMetadata.with_timestamp())

        # Build operations từ expanded instances
        self._build_operations(mir, expanded_instances, graph)

        # Build data flows
        self._build_data_flows(mir, expanded_instances)

        # Build effect flows
        self._build_effect_flows(mir, expanded_instances)

        # Build boundaries
        self._build_boundaries(mir, expanded_instances)

        return mir

    def _ensure_expanded(
        self,
        graph: CapabilityGraph,
        instance: CapabilityInstance,
    ) -> list[CapabilityInstance]:
        """
        Đảm bảo instances đã được expand thành core instances.

        Nếu instance là macro, expand thành core instances.
        Nếu instance đã là core, trả về list chứa chính nó.

        Args:
            graph: CapabilityGraph chứa macros
            instance: CapabilityInstance cần kiểm tra

        Returns:
            Danh sách core instances sau khi expand
        """
        # Kiểm tra instance có phải là macro không
        macro = graph.get_macro(instance.type)

        if macro is not None:
            # Instance là macro, cần expand
            # Add macro vào engine registry
            self._engine.register_macro(macro)

            # Expand
            report: ExpansionReport = self._engine.expand(graph, instance)

            # Get expanded core instances từ graph
            core_instances: list[CapabilityInstance] = []
            for core_id in report.final_core_instances:
                core_instance = graph.get_instance(core_id)
                if core_instance:
                    core_instances.append(core_instance)

            return core_instances

        # Instance đã là core, không cần expand
        return [instance]

    def _build_operations(
        self,
        mir: MIR,
        instances: list[CapabilityInstance],
        graph: CapabilityGraph,
    ) -> None:
        """
        Build MIROperation từ CapabilityInstances.

        Map core capability instances thành MIR operations.

        Args:
            mir: MIR target để add operations
            instances: Danh sách core capability instances
            graph: CapabilityGraph để lookup obligations
        """
        for instance in instances:
            # Tạo MIR operation từ capability instance
            op = MIROperation(
                op=instance.type,  # Core capability type → operation name
                params=instance.params,
                input_refs=[],  # Sẽ fill sau khi build data flows
                output_refs=[],  # Sẽ fill sau khi build data flows
                effect_refs=[],  # Sẽ fill sau khi build effect flows
                transaction_boundary=None,  # Sẽ fill sau khi build boundaries
                obligation_refs=instance.obligations,
            )

            # Add vào MIR
            mir.add_operation(op)

    def _build_data_flows(
        self,
        mir: MIR,
        instances: list[CapabilityInstance],
    ) -> None:
        """
        Build MIRDataFlow từ capability instances.

        Xác định data movement giữa operations dựa trên:
        - reads/writes của instances
        - params mapping giữa instances

        Args:
            mir: MIR target để add data flows
            instances: Danh sách core capability instances
        """
        # Build data flows dựa trên reads/writes relationships
        for i, instance in enumerate(instances):
            # Xác định output refs từ writes
            if instance.writes:
                op_index = i
                mir.ops[op_index].output_refs.extend(instance.writes)

            # Xác định input refs từ reads
            if instance.reads:
                op_index = i
                mir.ops[op_index].input_refs.extend(instance.reads)

            # Tạo data flow từ reads → params
            if instance.reads and instance.params:
                for read_entity in instance.reads:
                    self._mir_counter += 1
                    flow_id = f"flow_{self._mir_counter}"

                    # Tìm source operation (load_entity hoặc query_records)
                    source_op = self._find_source_op_for_read(instances, i, read_entity)

                    if source_op is not None:
                        flow = MIRDataFlow(
                            id=flow_id,
                            source_op=source_op,
                            source_field=f"{read_entity}.id",
                            target_op=instance.type,
                            target_field="id",
                        )
                        mir.add_data_flow(flow)

    def _find_source_op_for_read(
        self,
        instances: list[CapabilityInstance],
        target_index: int,
        entity: str,
    ) -> str | None:
        """
        Tìm source operation cung cấp data cho entity.

        Args:
            instances: Danh sách instances
            target_index: Index của target instance
            entity: Entity cần tìm source

        Returns:
            Operation name của source, None nếu không tìm thấy
        """
        # Tìm instances trước target có writes chứa entity
        for i in range(target_index):
            instance = instances[i]
            if entity in instance.writes:
                return instance.type

        return None

    def _build_effect_flows(
        self,
        mir: MIR,
        instances: list[CapabilityInstance],
    ) -> None:
        """
        Build MIREffectFlow từ capability instances.

        Xác định effect flows (events, notifications) từ:
        - publish_event operations
        - send_notification operations
        - emits của instances

        Args:
            mir: MIR target để add effect flows
            instances: Danh sách core capability instances
        """
        for i, instance in enumerate(instances):
            # Kiểm tra instance có emits không
            if instance.emits:
                # Find corresponding publish_event operation
                for j, other_instance in enumerate(instances):
                    if other_instance.type == "publish_event":
                        self._mir_counter += 1
                        effect_id = f"effect_{self._mir_counter}"

                        # Get event type from params
                        event_type = other_instance.params.get("event_type", "UnknownEvent")

                        effect = MIREffectFlow(
                            id=effect_id,
                            source_op=instance.type,
                            effect_type="event_publish",
                            target=event_type,
                            payload_fields=instance.emits,
                            async_=other_instance.params.get("async", True),
                        )
                        mir.add_effect_flow(effect)

                        # Add effect ref to operation
                        if j < len(mir.ops):
                            mir.ops[j].effect_refs.append(effect_id)

                        break

            # Kiểm tra instance là send_notification
            if instance.type == "send_notification":
                self._mir_counter += 1
                effect_id = f"effect_{self._mir_counter}"

                channel = instance.params.get("channel", "email")
                template = instance.params.get("template", "notification")

                effect = MIREffectFlow(
                    id=effect_id,
                    source_op=instance.type,
                    effect_type="notification",
                    target=template,
                    payload_fields=list(instance.params.get("data", {}).keys()),
                    async_=instance.params.get("async", True),
                )
                mir.add_effect_flow(effect)

    def _build_boundaries(
        self,
        mir: MIR,
        instances: list[CapabilityInstance],
    ) -> None:
        """
        Build MIRBoundary từ capability instances.

        Xác định boundaries:
        - Transaction boundaries từ begin/commit/rollback
        - Auth boundaries từ authorize_permission
        - Tenant boundaries từ enforce_tenant_scope

        Args:
            mir: MIR target để add boundaries
            instances: Danh sách core capability instances
        """
        # Build transaction boundaries
        self._build_transaction_boundaries(mir, instances)

        # Build auth boundaries
        self._build_auth_boundaries(mir, instances)

        # Build tenant boundaries
        self._build_tenant_boundaries(mir, instances)

    def _build_transaction_boundaries(
        self,
        mir: MIR,
        instances: list[CapabilityInstance],
    ) -> None:
        """
        Build transaction boundaries từ begin/commit/rollback operations.

        Args:
            mir: MIR target để add boundaries
            instances: Danh sách core capability instances
        """
        # Find begin_transaction operation
        begin_op = None
        begin_index = -1

        for i, instance in enumerate(instances):
            if instance.type == "begin_transaction":
                begin_op = instance
                begin_index = i
                break

        if begin_op is None:
            # No transaction boundary
            return

        # Create transaction boundary
        self._mir_counter += 1
        boundary_id = f"txn_{self._mir_counter}"

        # Find all operations trong transaction (between begin and commit)
        enclosing_ops: list[str] = ["begin_transaction"]
        commit_index = -1

        for i in range(begin_index + 1, len(instances)):
            instance = instances[i]
            if instance.type == "commit_transaction":
                commit_index = i
                enclosing_ops.append("commit_transaction")
                break
            elif instance.type != "rollback_transaction":
                enclosing_ops.append(instance.type)

        # Get transaction config from begin_transaction params
        config: dict[str, Any] = {
            "isolation": begin_op.params.get("isolation_level", "read_committed"),
        }

        boundary = MIRBoundary(
            id=boundary_id,
            boundary_type="transaction",
            enclosing_ops=enclosing_ops,
            config=config,
        )
        mir.add_boundary(boundary)

        # Set transaction_boundary ref trên các operations
        for i, instance in enumerate(instances):
            if i > begin_index and (commit_index == -1 or i < commit_index):
                if instance.type not in ["commit_transaction", "rollback_transaction"]:
                    if i < len(mir.ops):
                        mir.ops[i].transaction_boundary = boundary_id

    def _build_auth_boundaries(
        self,
        mir: MIR,
        instances: list[CapabilityInstance],
    ) -> None:
        """
        Build auth boundaries từ authorize_permission operations.

        Args:
            mir: MIR target để add boundaries
            instances: Danh sách core capability instances
        """
        for instance in instances:
            if instance.type == "authorize_permission":
                self._mir_counter += 1
                boundary_id = f"auth_{self._mir_counter}"

                permission = instance.params.get("permission", "unknown")

                boundary = MIRBoundary(
                    id=boundary_id,
                    boundary_type="auth",
                    enclosing_ops=[instance.type],
                    config={"permission": permission},
                    scope="permission_check",
                )
                mir.add_boundary(boundary)

    def _build_tenant_boundaries(
        self,
        mir: MIR,
        instances: list[CapabilityInstance],
    ) -> None:
        """
        Build tenant boundaries từ enforce_tenant_scope operations.

        Args:
            mir: MIR target để add boundaries
            instances: Danh sách core capability instances
        """
        for instance in instances:
            if instance.type == "enforce_tenant_scope":
                self._mir_counter += 1
                boundary_id = f"tenant_{self._mir_counter}"

                scope = instance.params.get("scope", "tenant_isolated")

                boundary = MIRBoundary(
                    id=boundary_id,
                    boundary_type="tenant",
                    enclosing_ops=[instance.type],
                    config={"scope": scope},
                    scope="tenant_isolation",
                )
                mir.add_boundary(boundary)