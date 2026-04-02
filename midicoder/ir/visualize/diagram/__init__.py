"""Diagram generation module for IR visualization using Mermaid.

This module generates Mermaid diagrams for visualizing IR structures:
- Workflow diagrams (stateDiagram-v2)
- Entity relationship diagrams (erDiagram)
- API maps (flowchart)
- Application flows (commands/queries/guards/effects)
- Policy access matrices
- Decision rule overviews
- Scenario sequences
- Intent summaries

All diagrams are generated as .mmd (Mermaid) files which can be:
- Viewed directly in GitHub/GitLab
- Previewed in VS Code with Mermaid extension
- Generated as Mermaid source (.mmd) for Markdown embedding

No external dependencies required for basic functionality!
"""

from .api import ApiDiagramGenerator
from .base import DiagramGenerator, DiagramOutput, MermaidRenderer
from .command import CommandGraphGenerator
from .entity import EntityDiagramGenerator
from .policy import PolicyDiagramGenerator
from .rules import RulesDiagramGenerator
from .scenario import ScenarioDiagramGenerator
from .workflow import WorkflowDiagramGenerator

__all__ = [
    "DiagramGenerator",
    "DiagramOutput",
    "MermaidRenderer",
    "WorkflowDiagramGenerator",
    "EntityDiagramGenerator",
    "ApiDiagramGenerator",
    "CommandGraphGenerator",
    "PolicyDiagramGenerator",
    "RulesDiagramGenerator",
    "ScenarioDiagramGenerator",
]
