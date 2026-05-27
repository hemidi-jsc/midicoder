# coding: utf-8
"""
Mô-đun parser cho CP55 — CI/CD Pipeline Generator.

Parse DSL dict (từ contract YAML) sang CIIR — Intermediate Representation
cho CI/CD pipeline configurations, stages, workflows.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from midicoder.packs.cp55_cicd.models import (
    GitHubActionsWorkflow,
    GitLabCIPipeline,
    Jenkinsfile,
    PipelineConfig,
    PipelineStage,
    PipelineStep,
    PipelineTrigger,
)


@dataclass
class CIIR:
    """Intermediate Representation cho CP55.

    Gom tập tất cả cấu hình CI/CD pipeline từ DSL, bao gồm
    pipeline configs, stages, và workflows.

    Attributes:
        pipelines: Danh sách pipeline configurations
        stages: Danh sách các stage definitions
        workflows: Danh sách workflow definitions
    """
    pipelines: list[PipelineConfig] = field(default_factory=list)
    stages: list[PipelineStage] = field(default_factory=list)
    workflows: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Chuyển CIIR sang dict."""
        return {
            "pipelines": [p.to_dict() for p in self.pipelines],
            "stages": [s.to_dict() for s in self.stages],
            "workflows": self.workflows,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CIIR":
        """Tạo CIIR từ dict."""
        pipelines = [PipelineConfig.from_dict(p) for p in data.get("pipelines", [])]
        stages = [PipelineStage.from_dict(s) for s in data.get("stages", [])]
        workflows = data.get("workflows", [])
        return cls(
            pipelines=pipelines,
            stages=stages,
            workflows=workflows,
        )


def parse_pipelines(data: dict[str, Any]) -> list[PipelineConfig]:
    """Parse danh sách pipeline configurations từ DSL dict.

    Args:
        data: DSL dict với key 'pipelines' hoặc 'ci_pipelines'

    Returns:
        Danh sách PipelineConfig
    """
    raw = data.get("pipelines", data.get("ci_pipelines", []))
    pipelines = []
    for p_data in raw:
        triggers_raw = p_data.get("triggers", ["push"])
        triggers = [PipelineTrigger(t) for t in triggers_raw]
        pipelines.append(PipelineConfig(
            pipeline_id=p_data.get("pipeline_id", p_data.get("id", "")),
            name=p_data.get("name", ""),
            platform=p_data.get("platform", "github_actions"),
            triggers=triggers,
            branches=p_data.get("branches", ["main"]),
            env_vars=p_data.get("env_vars", {}),
        ))
    return pipelines


def parse_stages(data: dict[str, Any]) -> list[PipelineStage]:
    """Parse danh sách stages từ DSL dict.

    Args:
        data: DSL dict với key 'stages' hoặc 'pipeline_stages'

    Returns:
        Danh sách PipelineStage
    """
    raw = data.get("stages", data.get("pipeline_stages", []))
    stages = []
    for s_data in raw:
        steps_raw = s_data.get("steps", [])
        steps = []
        for step_data in steps_raw:
            steps.append(PipelineStep(
                step_id=step_data.get("step_id", step_data.get("id", "")),
                name=step_data.get("name", ""),
                image=step_data.get("image", ""),
                commands=step_data.get("commands", []),
                env=step_data.get("env", {}),
                timeout_minutes=step_data.get("timeout_minutes", 30),
                artifacts=step_data.get("artifacts", []),
            ))
        stages.append(PipelineStage(
            stage_id=s_data.get("stage_id", s_data.get("id", "")),
            name=s_data.get("name", ""),
            steps=steps,
            needs=s_data.get("needs", []),
            allow_failure=s_data.get("allow_failure", False),
        ))
    return stages


def parse_workflows(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Parse danh sách workflow definitions từ DSL dict.

    Args:
        data: DSL dict với key 'workflows'

    Returns:
        Danh sách workflow definition dicts
    """
    return data.get("workflows", [])


def parse_to_ir(data: dict[str, Any]) -> CIIR:
    """Parse DSL dict thành CIIR.

    Args:
        data: DSL dict với pipelines, stages, workflows

    Returns:
        CIIR gom tập tất cả parsed data
    """
    pipelines = parse_pipelines(data)
    stages = parse_stages(data)
    workflows = parse_workflows(data)

    return CIIR(
        pipelines=pipelines,
        stages=stages,
        workflows=workflows,
    )


__all__ = [
    "CIIR",
    "parse_pipelines",
    "parse_stages",
    "parse_workflows",
    "parse_to_ir",
]
