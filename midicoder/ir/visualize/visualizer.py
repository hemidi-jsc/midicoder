"""IR visualizer for generating diagrams."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from .diagram.api import ApiDiagramGenerator
from .diagram.command import CommandGraphGenerator
from .diagram.entity import EntityDiagramGenerator
from .diagram.workflow import WorkflowDiagramGenerator
from .diagram.policy import PolicyDiagramGenerator
from .diagram.rules import RulesDiagramGenerator
from .diagram.scenario import ScenarioDiagramGenerator
from .diagram.base import MermaidRenderer
from .spec_map import VisualSpecRegistry

if TYPE_CHECKING:
    from ..schema.ir_schema import IR


class DiagramManifest:
    """Manifest of generated diagrams."""
    
    def __init__(self, visual_spec_meta: dict | None = None):
        """Initialize diagram manifest."""
        self.diagrams = []
        self.renderer = MermaidRenderer.renderer_metadata()
        self.visual_spec = visual_spec_meta or {}
    
    def add_diagrams(self, outputs: list) -> None:
        """Add diagram outputs to manifest.
        
        Args:
            outputs: List of DiagramOutput objects
        """
        for output in outputs:
            self.diagrams.append(output.to_dict())
    
    def to_dict(self) -> dict:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "diagrams": self.diagrams,
            "total": len(self.diagrams),
            "renderer": self.renderer,
            "visual_spec": self.visual_spec,
        }
    
    def write(self, path: Path) -> None:
        """Write manifest to file.
        
        Args:
            path: Path to manifest file
        """
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, sort_keys=True, ensure_ascii=False)
            f.write("\n")


def generate_diagrams(ir: IR, output_dir: Path, skip_diagrams: bool = False) -> DiagramManifest:
    """Generate all diagrams from IR."""
    if skip_diagrams:
        return DiagramManifest()
    
    spec_path = _resolve_visual_spec_path(output_dir)
    spec_registry = VisualSpecRegistry(spec_path)
    manifest = DiagramManifest(visual_spec_meta=spec_registry.metadata())
    
    print("[IR:DIAGRAMS] STEP workflow diagrams")
    workflow_outputs = generate_workflow_diagrams(ir, output_dir)
    manifest.add_diagrams(workflow_outputs)
    print(f"[IR:DIAGRAMS] STEP workflow diagrams | generated={len(workflow_outputs)}")
    
    print("[IR:DIAGRAMS] STEP entity relationship diagram")
    entity_outputs = generate_entity_diagram(ir, output_dir)
    manifest.add_diagrams(entity_outputs)
    print(f"[IR:DIAGRAMS] STEP entity relationship diagram | generated={len(entity_outputs)}")
    
    print("[IR:DIAGRAMS] STEP API map diagrams")
    api_outputs = generate_api_diagrams(ir, output_dir)
    manifest.add_diagrams(api_outputs)
    print(f"[IR:DIAGRAMS] STEP API map diagrams | generated={len(api_outputs)}")
    
    print("[IR:DIAGRAMS] STEP command graph")
    command_outputs = generate_command_graph(ir, output_dir)
    manifest.add_diagrams(command_outputs)
    print(f"[IR:DIAGRAMS] STEP command graph | generated={len(command_outputs)}")
    
    print("[IR:DIAGRAMS] STEP policy diagrams")
    policy_outputs = generate_policy_diagrams(ir, output_dir)
    manifest.add_diagrams(policy_outputs)
    print(f"[IR:DIAGRAMS] STEP policy diagrams | generated={len(policy_outputs)}")
    
    print("[IR:DIAGRAMS] STEP rules diagrams")
    rules_outputs = generate_rules_diagrams(ir, output_dir)
    manifest.add_diagrams(rules_outputs)
    print(f"[IR:DIAGRAMS] STEP rules diagrams | generated={len(rules_outputs)}")
    
    print("[IR:DIAGRAMS] STEP scenario diagrams")
    scenario_outputs = generate_scenario_diagrams(ir, output_dir)
    manifest.add_diagrams(scenario_outputs)
    print(f"[IR:DIAGRAMS] STEP scenario diagrams | generated={len(scenario_outputs)}")
    
    return manifest


def generate_workflow_diagrams(ir: IR, output_dir: Path) -> list:
    """Generate workflow state machine diagrams.
    
    Args:
        ir: IR object
        output_dir: Base output directory
        
    Returns:
        List of diagram outputs
    """
    workflows = ir.modules.workflow.workflows
    if not workflows:
        return []
    
    workflow_dir = output_dir / "workflows"
    generator = WorkflowDiagramGenerator(workflow_dir)
    
    return generator.generate(workflows)


def generate_entity_diagram(ir: IR, output_dir: Path) -> list:
    """Generate entity relationship diagram.
    
    Args:
        ir: IR object
        output_dir: Base output directory
        
    Returns:
        List of diagram outputs
    """
    domain = ir.modules.domain
    if not domain.entities and not domain.value_objects:
        return []
    
    entity_dir = output_dir / "entities"
    generator = EntityDiagramGenerator(entity_dir)
    
    return generator.generate(domain)


def generate_api_diagrams(ir: IR, output_dir: Path) -> list:
    """Generate API map diagrams.
    
    Args:
        ir: IR object
        output_dir: Base output directory
        
    Returns:
        List of diagram outputs
    """
    api = ir.modules.api
    application = ir.modules.application
    domain = ir.modules.domain
    
    if not api.http and not api.graphql:
        return []
    
    api_dir = output_dir / "api"
    generator = ApiDiagramGenerator(api_dir)
    
    return generator.generate(api, application, domain)


def generate_command_graph(ir: IR, output_dir: Path) -> list:
    """Generate command/application flow diagram."""
    application = ir.modules.application
    domain = ir.modules.domain
    
    if not application.commands:
        return []
    
    command_dir = output_dir / "commands"
    generator = CommandGraphGenerator(command_dir)
    
    return generator.generate(application, domain)


def generate_policy_diagrams(ir: IR, output_dir: Path) -> list:
    """Generate policy diagrams."""
    policy = ir.modules.policy
    if not policy or (not policy.access and not policy.business):
        return []
    policy_dir = output_dir / "policy"
    generator = PolicyDiagramGenerator(policy_dir)
    return generator.generate(policy)


def generate_rules_diagrams(ir: IR, output_dir: Path) -> list:
    """Generate rules diagrams."""
    rules = ir.modules.rules
    if not rules or not rules.rules:
        return []
    rules_dir = output_dir / "rules"
    generator = RulesDiagramGenerator(rules_dir)
    return generator.generate(rules)


def generate_scenario_diagrams(ir: IR, output_dir: Path) -> list:
    """Generate scenario diagrams."""
    scenarios = ir.modules.scenarios
    if not scenarios or not scenarios.scenarios:
        return []
    scenario_dir = output_dir / "scenarios"
    generator = ScenarioDiagramGenerator(scenario_dir)
    return generator.generate(scenarios)


def _resolve_visual_spec_path(output_dir: Path) -> Path | None:
    """Best-effort locate docs/specs/visual-ir-map.yml."""
    current = output_dir.resolve()
    for _ in range(5):
        candidate = current / "docs" / "specs" / "visual-ir-map.yml"
        if candidate.exists():
            return candidate
        if current.parent == current:
            break
        current = current.parent
    return None
