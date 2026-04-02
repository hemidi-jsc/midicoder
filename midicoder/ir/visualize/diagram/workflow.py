"""Workflow diagram generator."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from .base import (
    DiagramGenerator,
    DiagramOutput,
    MermaidRenderer,
    create_source_metadata,
)

if TYPE_CHECKING:
    from ...schema.ir_schema import WorkflowIR, StateIR, TransitionIR


class WorkflowDiagramGenerator(DiagramGenerator):
    """Generator for workflow state machine diagrams using Mermaid."""

    def generate(self, workflows: list[WorkflowIR]) -> list[DiagramOutput]:
        """Generate workflow diagrams.

        Args:
            workflows: List of workflow IR objects

        Returns:
            List of generated diagram outputs
        """
        outputs = []

        for workflow in workflows:
            output = self._generate_workflow_diagram(workflow)
            if output:
                outputs.append(output)

        return outputs

    def _generate_workflow_diagram(self, workflow: WorkflowIR) -> DiagramOutput | None:
        """Generate diagram for a single workflow.

        Args:
            workflow: Workflow IR object

        Returns:
            Diagram output or None if generation failed
        """
        mermaid_source = self._build_mermaid_source(workflow)

        output_path = self.output_dir / f"{workflow.id}.mmd"

        assets = MermaidRenderer.render_to_file(mermaid_source, output_path, "mmd")

        return DiagramOutput(
            diagram_id=f"workflow_{workflow.id}",
            diagram_type="workflow",
            format="mmd",
            path=output_path,
            sources=[
                create_source_metadata(
                    id=workflow.id,
                    type="Workflow",
                    source=workflow.source if hasattr(workflow, "source") else None,
                )
            ],
            template="workflow.stateDiagram",
            assets=assets,
        )

    def _build_mermaid_source(self, workflow: WorkflowIR) -> str:
        """Build Mermaid stateDiagram source for workflow.

        Args:
            workflow: Workflow IR object

        Returns:
            Mermaid source code
        """
        lines = [
            "---",
            f"title: {self._yaml_quote(workflow.id)}",
            "---",
            "stateDiagram-v2",
            "",
        ]

        # Map state IDs to sanitized node IDs
        state_nodes = {}
        for state in workflow.states:
            node_id = MermaidRenderer.sanitize_mermaid_id(state.id)
            state_nodes[state.id] = node_id

        # Define initial state
        if workflow.initial_state:
            initial_node = state_nodes.get(workflow.initial_state)
            if initial_node:
                lines.append(f"    [*] --> {initial_node}")
                lines.append("")

        # Define state labels and descriptions
        for state in workflow.states:
            node_id = state_nodes[state.id]

            # Set state label with description if available
            if state.description:
                label = MermaidRenderer.escape_mermaid_text(state.id)
                desc = MermaidRenderer.escape_mermaid_text(state.description[:50])
                combined = f"{label} - {desc}"
                lines.append(f"    {node_id} : {combined}")
            elif state.id != node_id:
                label = MermaidRenderer.escape_mermaid_text(state.id)
                lines.append(f"    {node_id} : {label}")

        lines.append("")

        # Define transitions
        for transition in workflow.transitions:
            from_node = state_nodes.get(transition.from_state)
            to_node = state_nodes.get(transition.to_state)

            if not from_node or not to_node:
                continue

            label = self._build_transition_label_mermaid(transition)

            if label:
                lines.append(f"    {from_node} --> {to_node} : {label}")
            else:
                lines.append(f"    {from_node} --> {to_node}")

        lines.append("")

        # Mark terminal states
        for state in workflow.states:
            if self._is_terminal_state(state):
                node_id = state_nodes[state.id]
                lines.append(f"    {node_id} --> [*]")

        # Add error handlers as comments (notes are not reliable in stateDiagram-v2)
        if workflow.error_handlers:
            lines.append("")
            lines.append("    %% Error Handlers:")
            for handler in workflow.error_handlers[:5]:
                if handler.error:
                    error_text = f"{handler.error.id} -> {handler.transition_to if handler.transition_to else handler.action}"
                    lines.append(f"    %% - {error_text}")
            if len(workflow.error_handlers) > 5:
                lines.append(f"    %% ... ({len(workflow.error_handlers) - 5} more)")

        return "\n".join(lines)

    def _is_terminal_state(self, state: StateIR) -> bool:
        """Check if state is terminal.

        Args:
            state: State IR object

        Returns:
            True if terminal state
        """
        if (
            "final" in state.id.lower()
            or "end" in state.id.lower()
            or "terminal" in state.id.lower()
        ):
            return True

        return False

    def _get_state_color(self, state: StateIR) -> str:
        """Get fill color for state node.

        Args:
            state: State IR object

        Returns:
            Color name
        """
        if self._is_terminal_state(state):
            return "lightcoral"

        if state.id.lower() == "initial" or "initial" in state.id.lower():
            return "lightgreen"

        if "error" in state.id.lower() or "failed" in state.id.lower():
            return "pink"

        if "processing" in state.id.lower() or "active" in state.id.lower():
            return "lightyellow"

        return "lightblue"

    def _build_transition_label_mermaid(self, transition: TransitionIR) -> str:
        """Build label for transition edge in Mermaid format.

        Args:
            transition: Transition IR object

        Returns:
            Label text
        """
        event_parts = []

        if transition.on_command:
            event_parts.append(f"cmd_{transition.on_command.id}")

        if transition.on_event:
            event_parts.append(f"evt_{transition.on_event.id}")

        event_token = "_".join(
            MermaidRenderer.sanitize_mermaid_id(part) for part in event_parts
        )

        guard_text = ""
        if transition.guards:
            guard_ids = [
                MermaidRenderer.sanitize_mermaid_id(g.id) for g in transition.guards
            ]
            if len(guard_ids) <= 2:
                guard_token = "_and_".join(guard_ids)
            else:
                guard_token = f"{len(guard_ids)}_guards"
            guard_text = f" [{guard_token}]"

        effect_text = ""
        if transition.effects:
            effect_ids = [
                MermaidRenderer.sanitize_mermaid_id(e.id) for e in transition.effects
            ]
            if len(effect_ids) <= 2:
                effect_token = "_and_".join(effect_ids)
            else:
                effect_token = f"{len(effect_ids)}_effects"
            effect_text = f" / {effect_token}"

        if not event_token and not guard_text and not effect_text:
            return ""

        if not event_token:
            event_token = "transition"

        label = f"{event_token}{guard_text}{effect_text}"

        return MermaidRenderer.escape_mermaid_text(label)

    def _yaml_quote(self, text: str) -> str:
        """Quote text for YAML front matter."""
        safe = text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        return f'"{safe}"'
