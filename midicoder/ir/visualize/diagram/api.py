"""API diagram generator."""

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
    from ...schema.ir_schema import ApiIR, HttpRouteIR, ApplicationIR, DomainIR


class ApiDiagramGenerator(DiagramGenerator):
    """Generator for API map diagrams using Mermaid."""

    def generate(
        self, api: ApiIR, application: ApplicationIR, domain: DomainIR
    ) -> list[DiagramOutput]:
        """Generate API map diagrams.

        Args:
            api: API IR object
            application: Application IR object
            domain: Domain IR object

        Returns:
            List of generated diagram outputs
        """
        outputs = []

        if api.http and api.http.routes:
            http_output = self._generate_http_api_diagram(
                api.http.routes, application, domain
            )
            if http_output:
                outputs.append(http_output)

        if api.graphql:
            graphql_output = self._generate_graphql_api_diagram(
                api.graphql, application, domain
            )
            if graphql_output:
                outputs.append(graphql_output)

        return outputs

    def _generate_http_api_diagram(
        self, routes: list[HttpRouteIR], application: ApplicationIR, domain: DomainIR
    ) -> DiagramOutput | None:
        """Generate HTTP API map diagram.

        Args:
            routes: List of HTTP routes
            application: Application IR object
            domain: Domain IR object

        Returns:
            Diagram output or None
        """
        mermaid_source = self._build_http_mermaid_source(routes, application, domain)

        output_path = self.output_dir / "http_api_map.mmd"

        assets = MermaidRenderer.render_to_file(mermaid_source, output_path, "mmd")

        # Build sources with full metadata
        sources = [
            create_source_metadata(
                id=route.id,
                type="HttpRoute",
                source=route.source if hasattr(route, "source") else None,
            )
            for route in routes
        ]

        return DiagramOutput(
            diagram_id="api_http_map",
            diagram_type="api",
            format="mmd",
            path=output_path,
            sources=sources,
            template="api.http.flow",
            assets=assets,
        )

    def _build_http_mermaid_source(
        self, routes: list[HttpRouteIR], application: ApplicationIR, domain: DomainIR
    ) -> str:
        """Build Mermaid flowchart source for HTTP API map.

        Args:
            routes: List of HTTP routes
            application: Application IR object
            domain: Domain IR object

        Returns:
            Mermaid source code
        """
        lines = [
            "---",
            "title: HTTP API Map",
            "---",
            "flowchart LR",
            "",
        ]

        command_map = {cmd.id: cmd for cmd in application.commands}
        query_map = {qry.id: qry for qry in application.queries}
        entity_map = {ent.id: ent for ent in domain.entities}

        # Define route nodes
        lines.append('    subgraph Routes["HTTP Routes"]')
        for route in routes:
            route_node = MermaidRenderer.sanitize_mermaid_id(f"route_{route.id}")
            route_label = MermaidRenderer.escape_mermaid_text(
                f"{route.method} {route.path}"
            )
            lines.append(f'        {route_node}["{route_label}"]')
        lines.append("    end")
        lines.append("")

        # Collect used commands and queries
        used_commands = set()
        used_queries = set()

        for route in routes:
            if route.command:
                used_commands.add(route.command.id)
            if route.query:
                used_queries.add(route.query.id)

        # Define command/query nodes
        if used_commands or used_queries:
            lines.append('    subgraph Operations["Commands/Queries"]')

            for cmd_id in used_commands:
                if cmd_id in command_map:
                    cmd_node = MermaidRenderer.sanitize_mermaid_id(f"cmd_{cmd_id}")
                    cmd_label = MermaidRenderer.escape_mermaid_text(cmd_id)
                    lines.append(f"        {cmd_node}(({cmd_label}))")

            for qry_id in used_queries:
                if qry_id in query_map:
                    qry_node = MermaidRenderer.sanitize_mermaid_id(f"qry_{qry_id}")
                    qry_label = MermaidRenderer.escape_mermaid_text(qry_id)
                    lines.append(f"        {qry_node}(({qry_label}))")

            lines.append("    end")
            lines.append("")

        # Collect used entities
        used_entities = set()

        for cmd_id in used_commands:
            if cmd_id in command_map:
                cmd = command_map[cmd_id]
                for fetch_ref in cmd.fetches:
                    if fetch_ref.type == "Entity":
                        used_entities.add(fetch_ref.id)

        for qry_id in used_queries:
            if qry_id in query_map:
                qry = query_map[qry_id]
                for read_ref in qry.reads:
                    if read_ref.type == "Entity":
                        used_entities.add(read_ref.id)

        # Define entity nodes
        if used_entities:
            lines.append("    subgraph Entities")
            for ent_id in used_entities:
                if ent_id in entity_map:
                    ent_node = MermaidRenderer.sanitize_mermaid_id(f"ent_{ent_id}")
                    ent_label = MermaidRenderer.escape_mermaid_text(ent_id)
                    lines.append(f'        {ent_node}[["{ent_label}"]]')
            lines.append("    end")
            lines.append("")

        # Define relationships
        for route in routes:
            route_node = MermaidRenderer.sanitize_mermaid_id(f"route_{route.id}")

            if route.command and route.command.id in command_map:
                cmd_node = MermaidRenderer.sanitize_mermaid_id(
                    f"cmd_{route.command.id}"
                )
                lines.append(f"    {route_node} -->|invokes| {cmd_node}")

                cmd = command_map[route.command.id]
                for fetch_ref in cmd.fetches:
                    if fetch_ref.type == "Entity" and fetch_ref.id in entity_map:
                        ent_node = MermaidRenderer.sanitize_mermaid_id(
                            f"ent_{fetch_ref.id}"
                        )
                        lines.append(f"    {cmd_node} -.->|fetches| {ent_node}")

            if route.query and route.query.id in query_map:
                qry_node = MermaidRenderer.sanitize_mermaid_id(f"qry_{route.query.id}")
                lines.append(f"    {route_node} -->|invokes| {qry_node}")

                qry = query_map[route.query.id]
                for read_ref in qry.reads:
                    if read_ref.type == "Entity" and read_ref.id in entity_map:
                        ent_node = MermaidRenderer.sanitize_mermaid_id(
                            f"ent_{read_ref.id}"
                        )
                        lines.append(f"    {qry_node} -.->|reads| {ent_node}")

        return "\n".join(lines)

    def _generate_graphql_api_diagram(
        self, graphql, application: ApplicationIR, domain: DomainIR
    ) -> DiagramOutput | None:
        """Generate GraphQL API map diagram.

        Args:
            graphql: GraphQL API IR object
            application: Application IR object
            domain: Domain IR object

        Returns:
            Diagram output or None
        """
        if not graphql.types and not graphql.queries and not graphql.mutations:
            return None

        lines = [
            "---",
            "title: GraphQL API Map",
            "---",
            "flowchart LR",
            "",
        ]

        # Define GraphQL types
        if graphql.types:
            lines.append('    subgraph Types["GraphQL Types"]')
            for gql_type in graphql.types:
                type_node = MermaidRenderer.sanitize_mermaid_id(f"type_{gql_type.id}")
                type_label = MermaidRenderer.escape_mermaid_text(gql_type.name)
                lines.append(f'        {type_node}["{type_label}"]')
            lines.append("    end")
            lines.append("")

        # Define operations
        if graphql.queries or graphql.mutations:
            lines.append("    subgraph Operations")

            for query in graphql.queries:
                query_node = MermaidRenderer.sanitize_mermaid_id(f"query_{query.id}")
                query_label = MermaidRenderer.escape_mermaid_text(query.name)
                lines.append(f"        {query_node}(({query_label}))")

            for mutation in graphql.mutations:
                mut_node = MermaidRenderer.sanitize_mermaid_id(f"mut_{mutation.id}")
                mut_label = MermaidRenderer.escape_mermaid_text(mutation.name)
                lines.append(f"        {mut_node}(({mut_label}))")

            lines.append("    end")
            lines.append("")

        mermaid_source = "\n".join(lines)

        output_path = self.output_dir / "graphql_api_map.mmd"

        assets = MermaidRenderer.render_to_file(mermaid_source, output_path, "mmd")

        # Build sources with full metadata
        sources = []

        for t in graphql.types:
            sources.append(
                create_source_metadata(
                    id=t.id,
                    type="GraphQLType",
                    source=t.source if hasattr(t, "source") else None,
                )
            )

        for q in graphql.queries:
            sources.append(
                create_source_metadata(
                    id=q.id,
                    type="GraphQLQuery",
                    source=q.source if hasattr(q, "source") else None,
                )
            )

        for m in graphql.mutations:
            sources.append(
                create_source_metadata(
                    id=m.id,
                    type="GraphQLMutation",
                    source=m.source if hasattr(m, "source") else None,
                )
            )

        return DiagramOutput(
            diagram_id="api_graphql_map",
            diagram_type="api",
            format="mmd",
            path=output_path,
            sources=sources,
            template="api.graphql.map",
            assets=assets,
        )
