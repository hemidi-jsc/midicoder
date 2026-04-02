"""Policy visualization generators."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .base import (
    DiagramGenerator,
    DiagramOutput,
    MermaidRenderer,
    create_source_metadata,
)

if TYPE_CHECKING:
    from ...schema.ir_schema import PolicyIR, AccessPolicyIR, BusinessPolicyIR


class PolicyDiagramGenerator(DiagramGenerator):
    """Generate access and business policy diagrams."""

    def generate(self, policy: PolicyIR) -> list[DiagramOutput]:
        outputs: list[DiagramOutput] = []
        if policy.access and (policy.access.roles or policy.access.permissions):
            access_output = self._generate_access_diagram(policy.access)
            if access_output:
                outputs.append(access_output)
        if policy.business:
            business_output = self._generate_business_diagram(policy.business)
            if business_output:
                outputs.append(business_output)
        return outputs

    def _generate_access_diagram(self, access: AccessPolicyIR) -> DiagramOutput | None:
        lines = [
            "---",
            "title: Access Policy Matrix",
            "---",
            "classDiagram",
            "",
        ]

        role_nodes = {}
        for role in access.roles:
            node_id = MermaidRenderer.sanitize_mermaid_id(f"role_{role.id}")
            role_nodes[role.id] = node_id
            lines.append(f"    class {node_id}{{")
            lines.append(
                f"        +Role {MermaidRenderer.escape_mermaid_text(role.id)}"
            )
            if role.description:
                lines.append(
                    f"        {MermaidRenderer.escape_mermaid_text(role.description[:60])}"
                )
            lines.append("    }")

        permission_nodes = {}
        for perm in access.permissions:
            node_id = MermaidRenderer.sanitize_mermaid_id(f"perm_{perm.id}")
            permission_nodes[perm.id] = node_id
            actions = ", ".join(perm.actions[:4]) if perm.actions else ""
            lines.append(f"    class {node_id}{{")
            lines.append(
                f"        +Perm {MermaidRenderer.escape_mermaid_text(perm.id)}"
            )
            lines.append(
                f"        resource: {MermaidRenderer.escape_mermaid_text(perm.resource)}"
            )
            if actions:
                lines.append(
                    f"        actions: {MermaidRenderer.escape_mermaid_text(actions)}"
                )
            lines.append("    }")

        resource_nodes = {}
        for perm in access.permissions:
            res = perm.resource
            if res not in resource_nodes:
                node_id = MermaidRenderer.sanitize_mermaid_id(f"res_{res}")
                resource_nodes[res] = node_id
                lines.append(f"    class {node_id}{{")
                lines.append(
                    f"        +Resource {MermaidRenderer.escape_mermaid_text(res)}"
                )
                lines.append("    }")
            lines.append(
                f"    {permission_nodes[perm.id]} --> {resource_nodes[res]} : grants"
            )

        for binding in access.bindings:
            role_node = role_nodes.get(binding.role)
            if not role_node:
                continue
            for perm_id in binding.permissions:
                perm_node = permission_nodes.get(perm_id)
                if not perm_node:
                    continue
                scope = binding.scope or ""
                scope_label = (
                    f" : {MermaidRenderer.escape_mermaid_text(scope)}" if scope else ""
                )
                lines.append(f"    {role_node} --> {perm_node}{scope_label}")

        if len(lines) <= 4:
            return None

        mermaid_source = "\n".join(lines)
        output_path = self.output_dir / "access_policy.mmd"
        assets = MermaidRenderer.render_to_file(mermaid_source, output_path, "mmd")

        sources = []
        for role in access.roles:
            sources.append(
                create_source_metadata(
                    id=role.id,
                    type="Role",
                    source=role.source if hasattr(role, "source") else None,
                )
            )
        for perm in access.permissions:
            sources.append(
                create_source_metadata(
                    id=perm.id,
                    type="Permission",
                    source=perm.source if hasattr(perm, "source") else None,
                )
            )

        return DiagramOutput(
            diagram_id="policy_access_matrix",
            diagram_type="policy",
            format="mmd",
            path=output_path,
            sources=sources,
            template="policy.access.matrix",
            assets=assets,
        )

    def _generate_business_diagram(
        self, policies: list[BusinessPolicyIR]
    ) -> DiagramOutput | None:
        if not policies:
            return None

        lines = [
            "---",
            "title: Business Policy Graph",
            "---",
            "flowchart LR",
            "",
        ]

        for policy in policies[:20]:
            policy_node = MermaidRenderer.sanitize_mermaid_id(f"policy_{policy.id}")
            label = MermaidRenderer.escape_mermaid_text(policy.id)
            scope = f"\\nscope: {policy.scope}" if policy.scope else ""
            lines.append(f'    {policy_node}["{label}{scope}"]')

            for idx, condition in enumerate(policy.conditions[:4]):
                cond_node = MermaidRenderer.sanitize_mermaid_id(
                    f"{policy.id}_cond_{idx}"
                )
                cond_text = f"{condition.field} {condition.operator} {condition.value}"
                cond_label = MermaidRenderer.escape_mermaid_text(cond_text[:40])
                lines.append(f'    {cond_node}{{"{cond_label}"}}')
                lines.append(f"    {policy_node} --> {cond_node}")

            for idx, effect in enumerate(policy.effects[:4]):
                effect_node = MermaidRenderer.sanitize_mermaid_id(
                    f"{policy.id}_effect_{idx}"
                )
                target = effect.target or ""
                eff_text = f"{effect.type} {target}"
                eff_label = MermaidRenderer.escape_mermaid_text(eff_text[:40])
                lines.append(f'    {effect_node}(("{eff_label}"))')
                lines.append(f"    {policy_node} --> {effect_node}")

        mermaid_source = "\n".join(lines)
        output_path = self.output_dir / "business_policy.mmd"
        assets = MermaidRenderer.render_to_file(mermaid_source, output_path, "mmd")

        sources = [
            create_source_metadata(
                id=policy.id,
                type="BusinessPolicy",
                source=policy.source if hasattr(policy, "source") else None,
            )
            for policy in policies
        ]

        return DiagramOutput(
            diagram_id="policy_business_graph",
            diagram_type="policy",
            format="mmd",
            path=output_path,
            sources=sources,
            template="policy.business.flow",
            assets=assets,
        )
