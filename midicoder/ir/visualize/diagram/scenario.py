"""Scenario visualization generator."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .base import (
    DiagramGenerator,
    DiagramOutput,
    MermaidRenderer,
    create_source_metadata,
)

if TYPE_CHECKING:
    from ...schema.ir_schema import ScenariosIR, ScenarioIR, ScenarioStepIR


class ScenarioDiagramGenerator(DiagramGenerator):
    """Generate sequence diagrams for scenarios."""

    def generate(self, scenarios_ir: ScenariosIR) -> list[DiagramOutput]:
        outputs = []
        for scenario in scenarios_ir.scenarios[:10]:
            output = self._generate_scenario_diagram(scenario)
            if output:
                outputs.append(output)
        return outputs

    def _generate_scenario_diagram(self, scenario: ScenarioIR) -> DiagramOutput | None:
        lifelines = list(dict.fromkeys((scenario.actors or []) + ["System"]))
        if not lifelines:
            lifelines = ["User", "System"]

        lines = [
            "---",
            f"title: Scenario {MermaidRenderer.escape_mermaid_text(scenario.id)}",
            "---",
            "sequenceDiagram",
            "",
        ]

        for actor in lifelines:
            safe = MermaidRenderer.sanitize_mermaid_id(actor or "Actor")
            label = MermaidRenderer.escape_mermaid_text(actor or "Actor")
            lines.append(f"    participant {safe} as {label}")
        lines.append("")

        primary = MermaidRenderer.sanitize_mermaid_id(lifelines[0])
        system = MermaidRenderer.sanitize_mermaid_id("System")

        for idx, step in enumerate(scenario.steps[:20]):
            sender, receiver = self._resolve_participants(step, primary, system)
            label = self._build_step_label(step, idx)
            lines.append(f"    {sender}->{receiver}: {label}")

        mermaid_source = "\n".join(lines)
        output_path = self.output_dir / f"scenario_{scenario.id}.mmd"
        assets = MermaidRenderer.render_to_file(mermaid_source, output_path, "mmd")

        sources = [
            create_source_metadata(
                id=scenario.id,
                type="Scenario",
                source=scenario.source if hasattr(scenario, "source") else None,
            )
        ]

        return DiagramOutput(
            diagram_id=f"scenario_{scenario.id}",
            diagram_type="scenario",
            format="mmd",
            path=output_path,
            sources=sources,
            template="scenario.sequence",
            assets=assets,
        )

    def _resolve_participants(
        self, step: ScenarioStepIR, primary: str, system: str
    ) -> tuple[str, str]:
        if step.type in {"command", "query"}:
            return primary, system
        if step.type == "event":
            return system, primary
        if step.type == "assertion":
            return primary, primary
        return primary, system

    def _build_step_label(self, step: ScenarioStepIR, idx: int) -> str:
        ref = getattr(step.ref, "id", None) if step.ref else None
        meta = step.type or "step"
        label = f"{meta}: {ref or f'step_{idx}'}"
        return MermaidRenderer.escape_mermaid_text(label)
