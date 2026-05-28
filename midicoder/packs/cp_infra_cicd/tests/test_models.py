# coding: utf-8
"""
Tests cho I03 — CI/CD Pipeline Generator models.

Phạm vi: toàn bộ enums (PipelinePlatform, PipelineTrigger) và dataclasses
(PipelineConfig, PipelineStep, PipelineStage, GitHubActionsWorkflow,
GitLabCIPipeline, Jenkinsfile).

Mỗi class được test: creation, to_dict, from_dict, defaults,
validation errors.
"""

import pytest
from midicoder.packs.cp_infra_cicd.models import (
    PipelinePlatform,
    PipelineTrigger,
    PipelineConfig,
    PipelineStep,
    PipelineStage,
    GitHubActionsWorkflow,
    GitLabCIPipeline,
    Jenkinsfile,
)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class TestPipelinePlatform:
    def test_enum_values(self):
        assert PipelinePlatform.GITHUB_ACTIONS.value == "github_actions"
        assert PipelinePlatform.GITLAB_CI.value == "gitlab_ci"
        assert PipelinePlatform.JENKINS.value == "jenkins"


class TestPipelineTrigger:
    def test_enum_values(self):
        assert PipelineTrigger.PUSH.value == "push"
        assert PipelineTrigger.PULL_REQUEST.value == "pull_request"
        assert PipelineTrigger.SCHEDULE.value == "schedule"
        assert PipelineTrigger.MANUAL.value == "manual"
        assert PipelineTrigger.RELEASE.value == "release"
        assert PipelineTrigger.TAG.value == "tag"


# ---------------------------------------------------------------------------
# PipelineConfig
# ---------------------------------------------------------------------------

class TestPipelineConfig:
    def test_defaults(self):
        pc = PipelineConfig(pipeline_id="pl-001")
        assert pc.name == "pl-001"  # auto-set from pipeline_id
        assert pc.platform == PipelinePlatform.GITHUB_ACTIONS
        assert pc.branches == ["main"]
        assert pc.triggers == []
        assert pc.env_vars == {}

    def test_creation(self):
        pc = PipelineConfig(
            pipeline_id="pl-002",
            name="CI Pipeline",
            platform=PipelinePlatform.GITLAB_CI,
            triggers=[PipelineTrigger.PUSH, PipelineTrigger.PULL_REQUEST],
            branches=["main", "develop"],
            env_vars={"NODE_ENV": "test"},
        )
        assert pc.platform == PipelinePlatform.GITLAB_CI
        assert len(pc.triggers) == 2
        assert pc.env_vars["NODE_ENV"] == "test"

    def test_to_dict(self):
        pc = PipelineConfig(
            pipeline_id="pl-001",
            name="Test",
            platform=PipelinePlatform.JENKINS,
            triggers=[PipelineTrigger.PUSH],
        )
        d = pc.to_dict()
        assert d["platform"] == "jenkins"
        assert d["triggers"] == ["push"]

    def test_from_dict(self):
        data = {
            "pipeline_id": "pl-003",
            "name": "From Dict",
            "platform": "gitlab_ci",
            "triggers": ["push", "schedule"],
            "branches": ["main"],
        }
        pc = PipelineConfig.from_dict(data)
        assert pc.platform == PipelinePlatform.GITLAB_CI
        assert len(pc.triggers) == 2
        assert pc.triggers[1] == PipelineTrigger.SCHEDULE

    def test_roundtrip(self):
        original = PipelineConfig(
            pipeline_id="pl-001",
            name="RT Pipeline",
            platform=PipelinePlatform.GITHUB_ACTIONS,
            triggers=[PipelineTrigger.PUSH, PipelineTrigger.TAG],
            branches=["main", "release"],
            env_vars={"KEY": "VALUE"},
        )
        restored = PipelineConfig.from_dict(original.to_dict())
        assert restored.pipeline_id == original.pipeline_id
        assert restored.platform == original.platform
        assert restored.env_vars == original.env_vars

    def test_empty_pipeline_id_raises(self):
        with pytest.raises(Exception):
            PipelineConfig(pipeline_id="")

    def test_name_defaults_to_pipeline_id(self):
        pc = PipelineConfig(pipeline_id="auto-name")
        assert pc.name == "auto-name"


# ---------------------------------------------------------------------------
# PipelineStep
# ---------------------------------------------------------------------------

class TestPipelineStep:
    def test_defaults(self):
        ps = PipelineStep(step_id="step-001")
        assert ps.name == "step-001"
        assert ps.image == "ubuntu:latest"
        assert ps.timeout_minutes == 30
        assert ps.commands == []
        assert ps.artifacts == []

    def test_creation(self):
        ps = PipelineStep(
            step_id="step-002",
            name="Build",
            image="node:20",
            commands=["npm install", "npm run build"],
            env={"CI": "true"},
            timeout_minutes=15,
            artifacts=["dist/**"],
        )
        assert ps.image == "node:20"
        assert len(ps.commands) == 2
        assert ps.timeout_minutes == 15

    def test_to_dict(self):
        ps = PipelineStep(step_id="s1", name="Test", image="python:3.12", commands=["pytest"])
        d = ps.to_dict()
        assert d["image"] == "python:3.12"
        assert d["commands"] == ["pytest"]

    def test_from_dict(self):
        data = {
            "step_id": "s2",
            "name": "Deploy",
            "image": "alpine:3.19",
            "commands": ["sh deploy.sh"],
            "timeout_minutes": 10,
        }
        ps = PipelineStep.from_dict(data)
        assert ps.image == "alpine:3.19"
        assert ps.timeout_minutes == 10

    def test_roundtrip(self):
        original = PipelineStep(
            step_id="step-001",
            name="Lint",
            image="node:20",
            commands=["npm run lint"],
            env={"NODE_ENV": "ci"},
            artifacts=["reports/**"],
        )
        restored = PipelineStep.from_dict(original.to_dict())
        assert restored.commands == original.commands
        assert restored.artifacts == original.artifacts

    def test_empty_step_id_raises(self):
        with pytest.raises(Exception):
            PipelineStep(step_id="")

    def test_negative_timeout_defaults_to_30(self):
        ps = PipelineStep(step_id="s", timeout_minutes=-1)
        assert ps.timeout_minutes == 30

    def test_zero_timeout_defaults_to_30(self):
        ps = PipelineStep(step_id="s", timeout_minutes=0)
        assert ps.timeout_minutes == 30


# ---------------------------------------------------------------------------
# PipelineStage
# ---------------------------------------------------------------------------

class TestPipelineStage:
    def test_defaults(self):
        ps = PipelineStage(stage_id="stage-001")
        assert ps.name == "stage-001"
        assert ps.steps == []
        assert ps.needs == []
        assert ps.allow_failure is False

    def test_creation(self):
        ps = PipelineStage(
            stage_id="stage-002",
            name="Build Stage",
            steps=[
                PipelineStep(step_id="s1", name="Install"),
                PipelineStep(step_id="s2", name="Build"),
            ],
            needs=["setup-stage"],
            allow_failure=True,
        )
        assert len(ps.steps) == 2
        assert ps.allow_failure is True

    def test_total_timeout(self):
        ps = PipelineStage(
            stage_id="stage-001",
            steps=[
                PipelineStep(step_id="s1", timeout_minutes=10),
                PipelineStep(step_id="s2", timeout_minutes=20),
            ],
        )
        assert ps.total_timeout == 30

    def test_total_timeout_empty(self):
        ps = PipelineStage(stage_id="empty")
        assert ps.total_timeout == 0

    def test_to_dict(self):
        ps = PipelineStage(
            stage_id="s1",
            name="Test",
            steps=[PipelineStep(step_id="st1", name="Run")],
            needs=["build"],
        )
        d = ps.to_dict()
        assert len(d["steps"]) == 1
        assert d["needs"] == ["build"]

    def test_from_dict(self):
        data = {
            "stage_id": "s2",
            "name": "Deploy",
            "steps": [
                {"step_id": "st1", "name": "Push", "image": "docker:latest"}
            ],
            "needs": ["test"],
            "allow_failure": True,
        }
        ps = PipelineStage.from_dict(data)
        assert len(ps.steps) == 1
        assert ps.allow_failure is True

    def test_roundtrip(self):
        original = PipelineStage(
            stage_id="stage-001",
            name="CI",
            steps=[
                PipelineStep(step_id="s1", name="A", timeout_minutes=5),
                PipelineStep(step_id="s2", name="B", timeout_minutes=10),
            ],
            needs=["prev"],
        )
        restored = PipelineStage.from_dict(original.to_dict())
        assert len(restored.steps) == 2
        assert restored.total_timeout == 15

    def test_empty_stage_id_raises(self):
        with pytest.raises(Exception):
            PipelineStage(stage_id="")


# ---------------------------------------------------------------------------
# GitHubActionsWorkflow
# ---------------------------------------------------------------------------

class TestGitHubActionsWorkflow:
    def test_defaults(self):
        gw = GitHubActionsWorkflow(workflow_id="wf-001")
        assert gw.name == "wf-001"
        assert gw.filename == "wf-001.yml"
        assert gw.job_count == 0

    def test_creation(self):
        stage = PipelineStage(stage_id="build", name="Build")
        gw = GitHubActionsWorkflow(
            workflow_id="wf-002",
            name="CI Workflow",
            filename="ci.yml",
            triggers=[PipelineTrigger.PUSH, PipelineTrigger.PULL_REQUEST],
            jobs={"build": stage},
        )
        assert gw.job_count == 1
        assert gw.filename == "ci.yml"

    def test_to_dict(self):
        gw = GitHubActionsWorkflow(
            workflow_id="wf-001",
            triggers=[PipelineTrigger.PUSH],
            jobs={"build": PipelineStage(stage_id="b", name="Build")},
        )
        d = gw.to_dict()
        assert d["triggers"] == ["push"]
        assert "build" in d["jobs"]

    def test_from_dict(self):
        data = {
            "workflow_id": "wf-003",
            "name": "Actions",
            "filename": "actions.yml",
            "triggers": ["push", "manual"],
            "jobs": {
                "lint": {"stage_id": "lint", "name": "Lint"}
            },
        }
        gw = GitHubActionsWorkflow.from_dict(data)
        assert len(gw.triggers) == 2
        assert len(gw.jobs) == 1
        assert gw.filename == "actions.yml"

    def test_roundtrip(self):
        original = GitHubActionsWorkflow(
            workflow_id="wf-001",
            name="Test",
            filename="test.yml",
            triggers=[PipelineTrigger.PUSH],
            jobs={"deploy": PipelineStage(stage_id="d", name="Deploy")},
        )
        restored = GitHubActionsWorkflow.from_dict(original.to_dict())
        assert restored.workflow_id == original.workflow_id
        assert len(restored.jobs) == 1

    def test_empty_workflow_id_raises(self):
        with pytest.raises(Exception):
            GitHubActionsWorkflow(workflow_id="")

    def test_filename_defaults(self):
        gw = GitHubActionsWorkflow(workflow_id="my-wf")
        assert gw.filename == "my-wf.yml"


# ---------------------------------------------------------------------------
# GitLabCIPipeline
# ---------------------------------------------------------------------------

class TestGitLabCIPipeline:
    def test_defaults(self):
        gl = GitLabCIPipeline(pipeline_id="gl-001")
        assert gl.stages == []
        assert gl.stage_count == 0

    def test_creation(self):
        gl = GitLabCIPipeline(
            pipeline_id="gl-002",
            stages=["build", "test", "deploy"],
            jobs={
                "build-job": PipelineStep(step_id="b", name="Build"),
                "test-job": PipelineStep(step_id="t", name="Test"),
            },
        )
        assert gl.stage_count == 3
        assert len(gl.jobs) == 2

    def test_to_dict(self):
        gl = GitLabCIPipeline(
            pipeline_id="gl-001",
            stages=["build", "test"],
            jobs={"j1": PipelineStep(step_id="s", name="Step")},
        )
        d = gl.to_dict()
        assert d["stages"] == ["build", "test"]
        assert "j1" in d["jobs"]

    def test_from_dict(self):
        data = {
            "pipeline_id": "gl-003",
            "stages": ["compile"],
            "jobs": {
                "c1": {"step_id": "c", "name": "Compile"}
            },
        }
        gl = GitLabCIPipeline.from_dict(data)
        assert gl.stage_count == 1
        assert "c1" in gl.jobs

    def test_roundtrip(self):
        original = GitLabCIPipeline(
            pipeline_id="gl-001",
            stages=["build", "test"],
            jobs={"bj": PipelineStep(step_id="bs", name="Build Step")},
        )
        restored = GitLabCIPipeline.from_dict(original.to_dict())
        assert restored.pipeline_id == original.pipeline_id
        assert len(restored.stages) == 2

    def test_empty_pipeline_id_raises(self):
        with pytest.raises(Exception):
            GitLabCIPipeline(pipeline_id="")


# ---------------------------------------------------------------------------
# Jenkinsfile
# ---------------------------------------------------------------------------

class TestJenkinsfile:
    def test_defaults(self):
        jf = Jenkinsfile(pipeline_id="jk-001")
        assert jf.agent == "any"
        assert jf.stage_count == 0
        assert "always" in jf.post_actions
        assert "success" in jf.post_actions
        assert "failure" in jf.post_actions

    def test_creation(self):
        jf = Jenkinsfile(
            pipeline_id="jk-002",
            agent="docker",
            stages=[
                PipelineStage(stage_id="build", name="Build"),
                PipelineStage(stage_id="test", name="Test"),
            ],
            post_actions={"always": ["echo done"]},
        )
        assert jf.agent == "docker"
        assert jf.stage_count == 2
        assert jf.post_actions == {"always": ["echo done"]}

    def test_to_dict(self):
        jf = Jenkinsfile(
            pipeline_id="jk-001",
            agent="kubernetes",
            stages=[PipelineStage(stage_id="s1", name="Step")],
        )
        d = jf.to_dict()
        assert d["agent"] == "kubernetes"
        assert len(d["stages"]) == 1

    def test_from_dict(self):
        data = {
            "pipeline_id": "jk-003",
            "agent": "label",
            "stages": [
                {"stage_id": "build", "name": "Build"}
            ],
        }
        jf = Jenkinsfile.from_dict(data)
        assert jf.agent == "label"
        assert len(jf.stages) == 1

    def test_roundtrip(self):
        original = Jenkinsfile(
            pipeline_id="jk-001",
            agent="docker",
            stages=[
                PipelineStage(stage_id="s1", name="A"),
                PipelineStage(stage_id="s2", name="B"),
            ],
            post_actions={"always": ["clean"]},
        )
        restored = Jenkinsfile.from_dict(original.to_dict())
        assert restored.agent == "docker"
        assert len(restored.stages) == 2
        assert restored.post_actions == {"always": ["clean"]}

    def test_empty_pipeline_id_raises(self):
        with pytest.raises(Exception):
            Jenkinsfile(pipeline_id="")

    def test_empty_agent_defaults(self):
        jf = Jenkinsfile(pipeline_id="jk-001", agent="")
        assert jf.agent == "any"
