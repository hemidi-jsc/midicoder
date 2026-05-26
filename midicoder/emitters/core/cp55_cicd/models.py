# coding: utf-8
"""
Mô-đun models cho CP55 — CI/CD Pipeline Generator.

Định nghĩa các dataclass biểu diễn:
- PipelineConfig: Cấu hình pipeline tổng thể (platform, triggers, branches, env_vars)
- PipelineStage: Một stage trong pipeline (steps, needs, allow_failure)
- PipelineStep: Một bước cụ thể trong stage (image, commands, timeout, artifacts)
- GitHubActionsWorkflow: Workflow file cho GitHub Actions
- GitLabCIPipeline: Pipeline definition cho GitLab CI
- Jenkinsfile: Declarative Jenkinsfile stages

KPI-005: CP Obligations Coverage (>= 2 obligations cho CP55).

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# ===========================================================================
# Enums
# ===========================================================================


class PipelinePlatform(str, Enum):
    """Nền tảng CI/CD pipeline.

    - GITHUB_ACTIONS: GitHub Actions workflow
    - GITLAB_CI: GitLab CI/CD pipeline
    - JENKINS: Jenkins declarative pipeline
    """
    GITHUB_ACTIONS = "github_actions"
    GITLAB_CI = "gitlab_ci"
    JENKINS = "jenkins"


class PipelineTrigger(str, Enum):
    """Loại trigger cho pipeline.

    - PUSH: Kích hoạt khi push code
    - PULL_REQUEST: Kích hoạt khi tạo/update PR
    - SCHEDULE: Kích hoạt theo lịch (cron)
    - MANUAL: Kích hoạt thủ công
    - RELEASE: Kích hoạt khi tạo release
    - TAG: Kích hoạt khi push tag
    """
    PUSH = "push"
    PULL_REQUEST = "pull_request"
    SCHEDULE = "schedule"
    MANUAL = "manual"
    RELEASE = "release"
    TAG = "tag"


# ===========================================================================
# PipelineConfig
# ===========================================================================


@dataclass
class PipelineConfig:
    """Cấu hình pipeline tổng thể.

    Chứa thông tin cấu hình cho một CI/CD pipeline cụ thể, bao gồm
    nền tảng, triggers, branches scope, và biến môi trường.

    Attributes:
        pipeline_id: ID duy nhất của pipeline
        name: Tên pipeline (hiển thị)
        platform: Nền tảng CI/CD (github_actions, gitlab_ci, jenkins)
        triggers: Danh sách các trigger kích hoạt pipeline
        branches: Danh sách branches mà pipeline áp dụng
        env_vars: Biến môi trường cho pipeline
    """
    pipeline_id: str
    name: str = ""
    platform: PipelinePlatform = PipelinePlatform.GITHUB_ACTIONS
    triggers: list[PipelineTrigger] = field(default_factory=list)
    branches: list[str] = field(default_factory=list)
    env_vars: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate config sau khi khởi tạo."""
        if not self.pipeline_id or not self.pipeline_id.strip():
            raise EM.raise_error(
                ErrorCode.DSL_LOAD_FAILED,
                reason="pipeline_id bắt buộc và không được để trống",
            )

        if not self.name or not self.name.strip():
            self.name = self.pipeline_id

        if not self.branches:
            self.branches = ["main"]

    def to_dict(self) -> dict[str, Any]:
        """Chuyển PipelineConfig sang dict."""
        return {
            "pipeline_id": self.pipeline_id,
            "name": self.name,
            "platform": self.platform.value,
            "triggers": [t.value for t in self.triggers],
            "branches": self.branches,
            "env_vars": self.env_vars,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PipelineConfig":
        """Tạo PipelineConfig từ dict."""
        triggers = [PipelineTrigger(t) for t in data.get("triggers", ["push"])]
        return cls(
            pipeline_id=data["pipeline_id"],
            name=data.get("name", ""),
            platform=PipelinePlatform(data.get("platform", "github_actions")),
            triggers=triggers,
            branches=data.get("branches", ["main"]),
            env_vars=data.get("env_vars", {}),
        )


# ===========================================================================
# PipelineStep
# ===========================================================================


@dataclass
class PipelineStep:
    """Một bước cụ thể trong pipeline stage.

    Đại diện cho một bước thực thi, bao gồm container image,
    danh sách lệnh, biến môi trường, timeout, và artifacts.

    Attributes:
        step_id: ID duy nhất của bước
        name: Tên bước (hiển thị)
        image: Docker image để thực thi bước
        commands: Danh sách lệnh shell
        env: Biến môi trường cho bước này
        timeout_minutes: Thời gian tối đa (phút)
        artifacts: Danh sách artifact paths để lưu trữ
    """
    step_id: str
    name: str = ""
    image: str = ""
    commands: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    timeout_minutes: int = 30
    artifacts: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate step sau khi khởi tạo."""
        if not self.step_id or not self.step_id.strip():
            raise EM.raise_error(
                ErrorCode.DSL_LOAD_FAILED,
                reason="step_id bắt buộc và không được để trống",
            )

        if not self.name or not self.name.strip():
            self.name = self.step_id

        if self.timeout_minutes < 1:
            self.timeout_minutes = 30

        if not self.image:
            self.image = "ubuntu:latest"

    def to_dict(self) -> dict[str, Any]:
        """Chuyển PipelineStep sang dict."""
        return {
            "step_id": self.step_id,
            "name": self.name,
            "image": self.image,
            "commands": self.commands,
            "env": self.env,
            "timeout_minutes": self.timeout_minutes,
            "artifacts": self.artifacts,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PipelineStep":
        """Tạo PipelineStep từ dict."""
        return cls(
            step_id=data["step_id"],
            name=data.get("name", ""),
            image=data.get("image", ""),
            commands=data.get("commands", []),
            env=data.get("env", {}),
            timeout_minutes=data.get("timeout_minutes", 30),
            artifacts=data.get("artifacts", []),
        )


# ===========================================================================
# PipelineStage
# ===========================================================================


@dataclass
class PipelineStage:
    """Một stage trong pipeline.

    Nhóm các steps liên quan, có thể có dependencies (needs)
    và cấu hình failure handling.

    Attributes:
        stage_id: ID duy nhất của stage
        name: Tên stage (hiển thị)
        steps: Danh sách các bước trong stage
        needs: Danh sách stage IDs mà stage này phụ thuộc
        allow_failure: Có cho phép stage fail không
    """
    stage_id: str
    name: str = ""
    steps: list[PipelineStep] = field(default_factory=list)
    needs: list[str] = field(default_factory=list)
    allow_failure: bool = False

    def __post_init__(self) -> None:
        """Validate stage sau khi khởi tạo."""
        if not self.stage_id or not self.stage_id.strip():
            raise EM.raise_error(
                ErrorCode.DSL_LOAD_FAILED,
                reason="stage_id bắt buộc và không được để trống",
            )

        if not self.name or not self.name.strip():
            self.name = self.stage_id

    @property
    def total_timeout(self) -> int:
        """Trả về tổng timeout của tất cả steps trong stage (phút)."""
        return sum(s.timeout_minutes for s in self.steps)

    def to_dict(self) -> dict[str, Any]:
        """Chuyển PipelineStage sang dict."""
        return {
            "stage_id": self.stage_id,
            "name": self.name,
            "steps": [s.to_dict() for s in self.steps],
            "needs": self.needs,
            "allow_failure": self.allow_failure,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PipelineStage":
        """Tạo PipelineStage từ dict."""
        steps = [PipelineStep.from_dict(s) for s in data.get("steps", [])]
        return cls(
            stage_id=data["stage_id"],
            name=data.get("name", ""),
            steps=steps,
            needs=data.get("needs", []),
            allow_failure=data.get("allow_failure", False),
        )


# ===========================================================================
# GitHubActionsWorkflow
# ===========================================================================


@dataclass
class GitHubActionsWorkflow:
    """Workflow file cho GitHub Actions.

    Định nghĩa một workflow hoàn chỉnh bao gồm triggers
    và các jobs (tương ứng với stages).

    Attributes:
        workflow_id: ID duy nhất của workflow
        name: Tên workflow (hiển thị trong GitHub UI)
        filename: Tên file .yml trong .github/workflows/
        triggers: Danh sách triggers
        jobs: Từ điển job_id -> PipelineStage
    """
    workflow_id: str
    name: str = ""
    filename: str = ""
    triggers: list[PipelineTrigger] = field(default_factory=list)
    jobs: dict[str, PipelineStage] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate workflow sau khi khởi tạo."""
        if not self.workflow_id or not self.workflow_id.strip():
            raise EM.raise_error(
                ErrorCode.DSL_LOAD_FAILED,
                reason="workflow_id bắt buộc và không được để trống",
            )

        if not self.name or not self.name.strip():
            self.name = self.workflow_id

        if not self.filename or not self.filename.strip():
            self.filename = f"{self.workflow_id}.yml"

    @property
    def job_count(self) -> int:
        """Trả về số lượng jobs trong workflow."""
        return len(self.jobs)

    def to_dict(self) -> dict[str, Any]:
        """Chuyển GitHubActionsWorkflow sang dict."""
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "filename": self.filename,
            "triggers": [t.value for t in self.triggers],
            "jobs": {jid: stage.to_dict() for jid, stage in self.jobs.items()},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GitHubActionsWorkflow":
        """Tạo GitHubActionsWorkflow từ dict."""
        triggers = [PipelineTrigger(t) for t in data.get("triggers", ["push"])]
        jobs_data = data.get("jobs", {})
        jobs = {jid: PipelineStage.from_dict(sd) for jid, sd in jobs_data.items()}
        return cls(
            workflow_id=data["workflow_id"],
            name=data.get("name", ""),
            filename=data.get("filename", ""),
            triggers=triggers,
            jobs=jobs,
        )


# ===========================================================================
# GitLabCIPipeline
# ===========================================================================


@dataclass
class GitLabCIPipeline:
    """Pipeline definition cho GitLab CI.

    Định nghĩa stages và jobs theo format GitLab CI (.gitlab-ci.yml).

    Attributes:
        pipeline_id: ID duy nhất của pipeline
        stages: Danh sách stage IDs theo thứ tự thực thi
        jobs: Từ điển job_id -> PipelineStep
    """
    pipeline_id: str
    stages: list[str] = field(default_factory=list)
    jobs: dict[str, PipelineStep] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate GitLab CI pipeline sau khi khởi tạo."""
        if not self.pipeline_id or not self.pipeline_id.strip():
            raise EM.raise_error(
                ErrorCode.DSL_LOAD_FAILED,
                reason="pipeline_id bắt buộc và không được để trống",
            )

    @property
    def stage_count(self) -> int:
        """Trả về số lượng stages trong pipeline."""
        return len(self.stages)

    def to_dict(self) -> dict[str, Any]:
        """Chuyển GitLabCIPipeline sang dict."""
        return {
            "pipeline_id": self.pipeline_id,
            "stages": self.stages,
            "jobs": {jid: step.to_dict() for jid, step in self.jobs.items()},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GitLabCIPipeline":
        """Tạo GitLabCIPipeline từ dict."""
        jobs_data = data.get("jobs", {})
        jobs = {jid: PipelineStep.from_dict(sd) for jid, sd in jobs_data.items()}
        return cls(
            pipeline_id=data["pipeline_id"],
            stages=data.get("stages", []),
            jobs=jobs,
        )


# ===========================================================================
# Jenkinsfile
# ===========================================================================


@dataclass
class Jenkinsfile:
    """Declarative Jenkinsfile stages.

    Định nghĩa một declarative Jenkins pipeline bao gồm agent,
    các stages, và post-actions.

    Attributes:
        pipeline_id: ID duy nhất của pipeline
        agent: Agent type (any, docker, kubernetes, label)
        stages: Danh sách các stage
        post_actions: Danh sách post-action blocks (always, success, failure)
    """
    pipeline_id: str
    agent: str = "any"
    stages: list[PipelineStage] = field(default_factory=list)
    post_actions: dict[str, list[str]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate Jenkinsfile sau khi khởi tạo."""
        if not self.pipeline_id or not self.pipeline_id.strip():
            raise EM.raise_error(
                ErrorCode.DSL_LOAD_FAILED,
                reason="pipeline_id bắt buộc và không được để trống",
            )

        if not self.agent or not self.agent.strip():
            self.agent = "any"

        if not self.post_actions:
            self.post_actions = {
                "always": ["echo 'Pipeline hoàn tất'"],
                "success": ["echo 'Pipeline thành công'"],
                "failure": ["echo 'Pipeline thất bại'"],
            }

    @property
    def stage_count(self) -> int:
        """Trả về số lượng stages trong Jenkinsfile."""
        return len(self.stages)

    def to_dict(self) -> dict[str, Any]:
        """Chuyển Jenkinsfile sang dict."""
        return {
            "pipeline_id": self.pipeline_id,
            "agent": self.agent,
            "stages": [s.to_dict() for s in self.stages],
            "post_actions": self.post_actions,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Jenkinsfile":
        """Tạo Jenkinsfile từ dict."""
        stages = [PipelineStage.from_dict(s) for s in data.get("stages", [])]
        return cls(
            pipeline_id=data["pipeline_id"],
            agent=data.get("agent", "any"),
            stages=stages,
            post_actions=data.get(
                "post_actions",
                {
                    "always": ["echo 'Pipeline hoàn tất'"],
                    "success": ["echo 'Pipeline thành công'"],
                    "failure": ["echo 'Pipeline thất bại'"],
                },
            ),
        )
