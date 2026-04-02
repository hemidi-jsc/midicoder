"""Rules visualization generator."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .base import (
    DiagramGenerator,
    DiagramOutput,
    MermaidRenderer,
    create_source_metadata,
)

if TYPE_CHECKING:
    from ...schema.ir_schema import RuleIR, RulesIR


class RulesDiagramGenerator(DiagramGenerator):
    """Generate decision-table inspired diagrams for rules."""

    def generate(self, rules_ir: RulesIR) -> list[DiagramOutput]:
        if not rules_ir.rules:
            return []
        output = self._generate_rules_flow(rules_ir.rules)
        return [output] if output else []

    def _generate_rules_flow(self, rules: list[RuleIR]) -> DiagramOutput | None:
        lines = [
            "---",
            "title: Decision Rules Overview",
            "---",
            "flowchart LR",
            "",
        ]

        limited_rules = rules[:8]
        for rule in limited_rules:
            rule_node = MermaidRenderer.sanitize_mermaid_id(f"rule_{rule.id}")
            label = MermaidRenderer.escape_mermaid_text(
                f"{rule.id}\\nseverity: {rule.severity or 'n/a'}"
            )
            lines.append(f'    {rule_node}["{label}"]')

            for idx, row in enumerate(rule.table[:4]):
                row_node = MermaidRenderer.sanitize_mermaid_id(f"{rule.id}_row_{idx}")
                conditions = ", ".join(
                    f"{k}={v}" for k, v in list(row.conditions.items())[:2]
                )
                cond_label = MermaidRenderer.escape_mermaid_text(
                    conditions[:50] or "any"
                )
                result_node = MermaidRenderer.sanitize_mermaid_id(
                    f"{rule.id}_result_{idx}"
                )
                result_label = MermaidRenderer.escape_mermaid_text(str(row.result))[:40]

                lines.append(f'    {row_node}{{"{cond_label}"}}')
                lines.append(f'    {result_node}(("{result_label}"))')
                lines.append(f"    {rule_node} -->|row {idx + 1}| {row_node}")
                lines.append(f"    {row_node} --> {result_node}")

        mermaid_source = "\n".join(lines)
        output_path = self.output_dir / "rules_overview.mmd"
        assets = MermaidRenderer.render_to_file(mermaid_source, output_path, "mmd")

        sources = [
            create_source_metadata(
                id=rule.id,
                type="Rule",
                source=rule.source if hasattr(rule, "source") else None,
            )
            for rule in limited_rules
        ]

        return DiagramOutput(
            diagram_id="rules_overview",
            diagram_type="rules",
            format="mmd",
            path=output_path,
            sources=sources,
            template="rules.decision.table",
            assets=assets,
        )
