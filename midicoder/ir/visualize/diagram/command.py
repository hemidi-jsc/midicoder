"""Command graph diagram generator."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .base import (
    DiagramGenerator,
    DiagramOutput,
    MermaidRenderer,
    create_source_metadata,
)

if TYPE_CHECKING:
    from ...schema.ir_schema import ApplicationIR, CommandIR, DomainIR, QueryIR


class CommandGraphGenerator(DiagramGenerator):
    """Generator for application flow diagrams using Mermaid."""

    def generate(
        self, application: ApplicationIR, domain: DomainIR
    ) -> list[DiagramOutput]:
        if not application.commands:
            return []

        mermaid_source = self._build_mermaid_source(application, domain)
        output_path = self.output_dir / "application_flow.mmd"
        assets = MermaidRenderer.render_to_file(mermaid_source, output_path, "mmd")

        sources = [
            create_source_metadata(
                id=cmd.id,
                type="Command",
                source=cmd.source if hasattr(cmd, "source") else None,
            )
            for cmd in application.commands
        ]
        sources.extend(
            create_source_metadata(
                id=qry.id,
                type="Query",
                source=qry.source if hasattr(qry, "source") else None,
            )
            for qry in application.queries
        )

        return [
            DiagramOutput(
                diagram_id="application_flow",
                diagram_type="command",
                format="mmd",
                path=output_path,
                sources=sources,
                template="application.flow.lanes",
                assets=assets,
            )
        ]

    def _build_mermaid_source(
        self, application: ApplicationIR, domain: DomainIR
    ) -> str:
        lines = [
            "---",
            "title: Application Flow",
            "---",
            "flowchart LR",
            "",
        ]

        event_map = {evt.id: evt for evt in domain.events}
        entity_map = {ent.id: ent for ent in domain.entities}

        lines.append("    subgraph Commands")
        for command in application.commands:
            cmd_node = MermaidRenderer.sanitize_mermaid_id(f"cmd_{command.id}")
            label = self._build_command_label_mermaid(command)
            lines.append(f'        {cmd_node}["{label}"]:::intent-controller')
        lines.append("    end")
        lines.append("")

        if application.queries:
            lines.append("    subgraph Queries")
            for query in application.queries:
                qry_node = MermaidRenderer.sanitize_mermaid_id(f"qry_{query.id}")
                label = self._build_query_label_mermaid(query)
                lines.append(f'        {qry_node}["{label}"]:::intent-controller')
            lines.append("    end")
            lines.append("")

        guard_defs = {}
        effect_defs = {}
        for command in application.commands:
            for guard in command.guards:
                guard_defs.setdefault(guard.id, guard)
            for effect in command.effects:
                effect_defs.setdefault(effect.id, effect)

        guard_nodes = {}
        if guard_defs:
            lines.append("    subgraph Guards")
            for guard_id in guard_defs:
                node_id = MermaidRenderer.sanitize_mermaid_id(f"guard_{guard_id}")
                guard_nodes[guard_id] = node_id
                lines.append(
                    f'        {node_id}(("{MermaidRenderer.escape_mermaid_text(guard_id)}"))'
                )
            lines.append("    end")
            lines.append("")

        effect_nodes = {}
        if effect_defs:
            lines.append("    subgraph Effects")
            for effect_id in effect_defs:
                node_id = MermaidRenderer.sanitize_mermaid_id(f"effect_{effect_id}")
                effect_nodes[effect_id] = node_id
                lines.append(
                    f'        {node_id}(("{MermaidRenderer.escape_mermaid_text(effect_id)}"))'
                )
            lines.append("    end")
            lines.append("")

        emitted_events = set()
        for command in application.commands:
            for emit_ref in command.emits:
                if emit_ref.type == "Event":
                    emitted_events.add(emit_ref.id)

        if emitted_events:
            lines.append("    subgraph Events")
            for evt_id in emitted_events:
                if evt_id in event_map:
                    evt_node = MermaidRenderer.sanitize_mermaid_id(f"evt_{evt_id}")
                    evt_label = MermaidRenderer.escape_mermaid_text(evt_id)
                    lines.append(f"        {evt_node}({evt_label})")
            lines.append("    end")
            lines.append("")

        used_entities = set()
        for command in application.commands:
            for ref in command.fetches:
                if ref.type == "Entity":
                    used_entities.add(ref.id)
        for query in application.queries:
            for ref in query.reads:
                if ref.type == "Entity":
                    used_entities.add(ref.id)

        if used_entities:
            lines.append("    subgraph Domain")
            for ent_id in sorted(used_entities):
                if ent_id in entity_map:
                    node_id = MermaidRenderer.sanitize_mermaid_id(f"ent_{ent_id}")
                    label = MermaidRenderer.escape_mermaid_text(ent_id)
                    lines.append(f'        {node_id}[["{label}"]]')
            lines.append("    end")
            lines.append("")

        for command in application.commands:
            cmd_node = MermaidRenderer.sanitize_mermaid_id(f"cmd_{command.id}")
            for guard in command.guards:
                guard_node = guard_nodes.get(guard.id)
                if guard_node:
                    lines.append(f"    {guard_node} -->|guard| {cmd_node}")
            for effect in command.effects:
                effect_node = effect_nodes.get(effect.id)
                if effect_node:
                    lines.append(f"    {cmd_node} -->|effect| {effect_node}")
            for fetch_ref in command.fetches:
                if fetch_ref.type == "Entity" and fetch_ref.id in entity_map:
                    ent_node = MermaidRenderer.sanitize_mermaid_id(
                        f"ent_{fetch_ref.id}"
                    )
                    lines.append(f"    {cmd_node} -.->|fetches| {ent_node}")
            for emit_ref in command.emits:
                if emit_ref.type == "Event" and emit_ref.id in event_map:
                    evt_node = MermaidRenderer.sanitize_mermaid_id(f"evt_{emit_ref.id}")
                    lines.append(f"    {cmd_node} -->|emits| {evt_node}")

        for query in application.queries:
            qry_node = MermaidRenderer.sanitize_mermaid_id(f"qry_{query.id}")
            for read_ref in query.reads:
                if read_ref.type == "Entity" and read_ref.id in entity_map:
                    ent_node = MermaidRenderer.sanitize_mermaid_id(f"ent_{read_ref.id}")
                    lines.append(f"    {qry_node} -.->|reads| {ent_node}")

        return "\n".join(lines)

    def _build_command_label_mermaid(self, command: CommandIR) -> str:
        parts = [command.id]
        if command.intent and command.intent.module:
            parts.append(f"module: {command.intent.module}")
        if command.guards:
            parts.append(f"guards: {len(command.guards)}")
        if command.effects:
            parts.append(f"effects: {len(command.effects)}")
        if command.emits:
            parts.append(f"emits: {len(command.emits)}")
        label = "\\n".join(parts)
        return MermaidRenderer.escape_mermaid_text(label)

    def _build_query_label_mermaid(self, query: QueryIR) -> str:
        parts = [query.id]
        if query.intent and query.intent.module:
            parts.append(f"module: {query.intent.module}")
        if query.reads:
            parts.append(f"reads: {len(query.reads)}")
        label = "\\n".join(parts)
        return MermaidRenderer.escape_mermaid_text(label)
