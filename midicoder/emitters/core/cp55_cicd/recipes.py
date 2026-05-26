# coding: utf-8
"""
Mô-đun recipes cho CP55 — CI/CD Pipeline Generator.

Cung cấp các recipe để build CIIR cho các use case phổ biến:
- github_actions_recipe: GitHub Actions workflow (build → test → lint → deploy)
- gitlab_ci_recipe: GitLab CI pipeline với các stages tương tự
- jenkins_recipe: Declarative Jenkinsfile stages
- full_cicd_recipe: Combined với Docker build, container scan, deploy

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from midicoder.emitters.core.cp55_cicd.models import (
    GitHubActionsWorkflow,
    GitLabCIPipeline,
    Jenkinsfile,
    PipelineConfig,
    PipelinePlatform,
    PipelineStage,
    PipelineStep,
    PipelineTrigger,
)
from midicoder.emitters.core.cp55_cicd.parser import (
    CIIR,
    parse_to_ir,
)


@dataclass
class RecipeOutput:
    """Kết quả từ recipe builder.

    Attributes:
        name: Tên recipe
        description: Mô tả recipe
        ir: CIIR đã build
        raw_data: Raw DSL dict
    """
    name: str
    description: str
    ir: CIIR
    raw_data: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Chuyển RecipeOutput sang dict."""
        return {
            "name": self.name,
            "description": self.description,
            "ir": self.ir.to_dict(),
            "raw_data": self.raw_data,
        }


def github_actions_recipe() -> RecipeOutput:
    """Recipe: GitHub Actions workflow — build → test → lint → deploy.

    Pipeline với các jobs:
    - lint: Kiểm tra code quality (flake8, black)
    - build: Build và install dependencies
    - test: Chạy test suite (unit + integration)
    - deploy: Deploy lên môi trường (chỉ trên main branch)

    Returns:
        RecipeOutput chứa CIIR
    """
    # Định nghĩa các steps
    lint_step = PipelineStep(
        step_id="lint_check",
        name="Kiểm tra code quality",
        image="python:3.12-slim",
        commands=[
            "pip install flake8 black isort",
            "flake8 midicoder/ --count --select=E9,F63,F7,F82 --show-source --statistics",
            "black --check --diff midicoder/",
            "isort --check-only --diff midicoder/",
        ],
        timeout_minutes=10,
    )

    build_step = PipelineStep(
        step_id="build_app",
        name="Build ứng dụng",
        image="python:3.12-slim",
        commands=[
            "python -m pip install --upgrade pip",
            "pip install -e \".[dev]\"",
            "python -m pytest --version",
        ],
        timeout_minutes=15,
    )

    test_step = PipelineStep(
        step_id="run_tests",
        name="Chạy test suite",
        image="python:3.12-slim",
        commands=[
            "pip install -e \".[test]\"",
            "python -m pytest tests/ -v --cov=midicoder --cov-report=xml",
            "python -m pytest tests/ -v --cov=midicoder --cov-report=html",
        ],
        env={"COVERAGE_FILE": ".coverage"},
        timeout_minutes=30,
        artifacts=["coverage.xml", "htmlcov/"],
    )

    deploy_step = PipelineStep(
        step_id="deploy_app",
        name="Deploy ứng dụng",
        image="python:3.12-slim",
        commands=[
            "echo 'Deploying to staging environment'",
            "pip install -e \".[deploy]\"",
            "python scripts/deploy.py --env staging",
        ],
        timeout_minutes=20,
    )

    # Định nghĩa các stages
    lint_stage = PipelineStage(
        stage_id="lint",
        name="Lint & Code Quality",
        steps=[lint_step],
        allow_failure=False,
    )

    build_stage = PipelineStage(
        stage_id="build",
        name="Build",
        steps=[build_step],
        allow_failure=False,
    )

    test_stage = PipelineStage(
        stage_id="test",
        name="Test",
        steps=[test_step],
        needs=["build"],
        allow_failure=False,
    )

    deploy_stage = PipelineStage(
        stage_id="deploy",
        name="Deploy",
        steps=[deploy_step],
        needs=["test"],
        allow_failure=False,
    )

    # Định nghĩa workflow
    workflow = GitHubActionsWorkflow(
        workflow_id="build_test_deploy",
        name="Build → Test → Deploy",
        filename="build-test-deploy.yml",
        triggers=[PipelineTrigger.PUSH, PipelineTrigger.PULL_REQUEST],
        jobs={
            "lint": lint_stage,
            "build": build_stage,
            "test": test_stage,
            "deploy": deploy_stage,
        },
    )

    # Pipeline config
    pipeline = PipelineConfig(
        pipeline_id="github_actions_main",
        name="GitHub Actions — Build/Test/Deploy",
        platform=PipelinePlatform.GITHUB_ACTIONS,
        triggers=[PipelineTrigger.PUSH, PipelineTrigger.PULL_REQUEST],
        branches=["main", "develop"],
        env_vars={"PYTHON_VERSION": "3.12"},
    )

    data = {
        "pipelines": [pipeline.to_dict()],
        "stages": [s.to_dict() for s in [lint_stage, build_stage, test_stage, deploy_stage]],
        "workflows": [workflow.to_dict()],
    }

    ir = parse_to_ir(data)

    return RecipeOutput(
        name="github_actions_recipe",
        description="GitHub Actions workflow — lint, build, test, deploy",
        ir=ir,
        raw_data=data,
    )


def gitlab_ci_recipe() -> RecipeOutput:
    """Recipe: GitLab CI pipeline — similar stages cho GitLab CI.

    Pipeline với các stages:
    - lint: Code quality check
    - build: Build ứng dụng
    - test: Chạy tests
    - deploy: Deploy lên staging

    Returns:
        RecipeOutput chứa CIIR
    """
    # Định nghĩa các jobs (PipelineStep cho GitLab CI)
    lint_job = PipelineStep(
        step_id="lint_job",
        name="Lint code quality",
        image="python:3.12-slim",
        commands=[
            "pip install flake8 black",
            "flake8 midicoder/",
            "black --check midicoder/",
        ],
        timeout_minutes=10,
    )

    build_job = PipelineStep(
        step_id="build_job",
        name="Build ứng dụng",
        image="python:3.12-slim",
        commands=[
            "pip install -e \".[dev]\"",
            "python setup.py check",
        ],
        timeout_minutes=15,
    )

    test_job = PipelineStep(
        step_id="test_job",
        name="Chạy tests",
        image="python:3.12-slim",
        commands=[
            "pip install -e \".[test]\"",
            "python -m pytest tests/ -v --cov=midicoder",
        ],
        timeout_minutes=30,
        artifacts=["coverage.xml"],
    )

    deploy_job = PipelineStep(
        step_id="deploy_job",
        name="Deploy lên staging",
        image="python:3.12-slim",
        commands=[
            "echo 'Deploying to staging'",
            "python scripts/deploy.py --env staging",
        ],
        timeout_minutes=20,
    )

    # GitLab CI Pipeline
    gitlab_pipeline = GitLabCIPipeline(
        pipeline_id="gitlab_main_pipeline",
        stages=["lint", "build", "test", "deploy"],
        jobs={
            "lint": lint_job,
            "build": build_job,
            "test": test_job,
            "deploy": deploy_job,
        },
    )

    # Pipeline config
    pipeline = PipelineConfig(
        pipeline_id="gitlab_ci_main",
        name="GitLab CI — Build/Test/Deploy",
        platform=PipelinePlatform.GITLAB_CI,
        triggers=[PipelineTrigger.PUSH, PipelineTrigger.MERGE_REQUEST],
        branches=["main"],
        env_vars={"PYTHON_VERSION": "3.12"},
    )

    data = {
        "pipelines": [pipeline.to_dict()],
        "stages": [],
        "workflows": [gitlab_pipeline.to_dict()],
    }

    ir = parse_to_ir(data)

    return RecipeOutput(
        name="gitlab_ci_recipe",
        description="GitLab CI pipeline — lint, build, test, deploy",
        ir=ir,
        raw_data=data,
    )


def jenkins_recipe() -> RecipeOutput:
    """Recipe: Declarative Jenkinsfile stages.

    Pipeline với các stages:
    - Setup: Chuẩn bị môi trường
    - Build: Build ứng dụng
    - Test: Chạy unit và integration tests
    - Quality: SonarQube scan
    - Deploy: Deploy lên staging/production

    Returns:
        RecipeOutput chứa CIIR
    """
    # Định nghĩa các stages cho Jenkins
    setup_stage = PipelineStage(
        stage_id="setup",
        name="Chuẩn bị môi trường",
        steps=[
            PipelineStep(
                step_id="checkout_code",
                name="Checkout code",
                image="",
                commands=["git checkout $BRANCH"],
                timeout_minutes=5,
            ),
            PipelineStep(
                step_id="install_deps",
                name="Install dependencies",
                image="",
                commands=["pip install -e \".[dev]\""],
                timeout_minutes=15,
            ),
        ],
        allow_failure=False,
    )

    build_stage = PipelineStage(
        stage_id="build",
        name="Build ứng dụng",
        steps=[
            PipelineStep(
                step_id="compile",
                name="Compile và build",
                image="",
                commands=[
                    "python setup.py build",
                    "python setup.py sdist bdist_wheel",
                ],
                timeout_minutes=15,
                artifacts=["dist/"],
            ),
        ],
        allow_failure=False,
    )

    test_stage = PipelineStage(
        stage_id="test",
        name="Chạy tests",
        steps=[
            PipelineStep(
                step_id="unit_tests",
                name="Unit tests",
                image="",
                commands=["python -m pytest tests/unit/ -v"],
                timeout_minutes=20,
            ),
            PipelineStep(
                step_id="integration_tests",
                name="Integration tests",
                image="",
                commands=["python -m pytest tests/integration/ -v"],
                timeout_minutes=30,
            ),
        ],
        allow_failure=False,
    )

    quality_stage = PipelineStage(
        stage_id="quality",
        name="SonarQube scan",
        steps=[
            PipelineStep(
                step_id="sonar_scan",
                name="SonarQube analysis",
                image="",
                commands=[
                    "sonar-scanner -Dsonar.projectKey=midicoder-ce",
                ],
                timeout_minutes=15,
            ),
        ],
        allow_failure=True,  # SonarQube fail không làm pipeline fail
    )

    deploy_stage = PipelineStage(
        stage_id="deploy",
        name="Deploy ứng dụng",
        steps=[
            PipelineStep(
                step_id="deploy_staging",
                name="Deploy lên staging",
                image="",
                commands=["python scripts/deploy.py --env staging"],
                timeout_minutes=20,
            ),
        ],
        allow_failure=False,
    )

    # Jenkinsfile
    jenkinsfile = Jenkinsfile(
        pipeline_id="jenkins_main_pipeline",
        agent="any",
        stages=[setup_stage, build_stage, test_stage, quality_stage, deploy_stage],
        post_actions={
            "always": [
                "archiveArtifacts artifacts: 'dist/**,coverage.xml', allowEmptyArchive: true",
                "echo 'Pipeline hoàn tất'",
            ],
            "success": ["echo 'Pipeline thành công'"],
            "failure": [
                "echo 'Pipeline thất bại'",
                "slackSend color: 'danger', message: 'Pipeline thất bại: $BUILD_NUMBER'",
            ],
        },
    )

    # Pipeline config
    pipeline = PipelineConfig(
        pipeline_id="jenkins_main",
        name="Jenkins — Full CI/CD",
        platform=PipelinePlatform.JENKINS,
        triggers=[PipelineTrigger.PUSH, PipelineTrigger.MANUAL],
        branches=["main", "develop"],
        env_vars={"SONAR_HOST": "http://sonarqube:9000"},
    )

    data = {
        "pipelines": [pipeline.to_dict()],
        "stages": [s.to_dict() for s in [setup_stage, build_stage, test_stage, quality_stage, deploy_stage]],
        "workflows": [jenkinsfile.to_dict()],
    }

    ir = parse_to_ir(data)

    return RecipeOutput(
        name="jenkins_recipe",
        description="Declarative Jenkinsfile — setup, build, test, quality, deploy",
        ir=ir,
        raw_data=data,
    )


def full_cicd_recipe() -> RecipeOutput:
    """Recipe: Combined CI/CD với Docker build + container scan + deploy.

    Recipe đầy đủ nhất với:
    - GitHub Actions workflow chính (lint, build, test, deploy)
    - Docker publish workflow riêng
    - Container security scan (Trivy)
    - Docker Compose CI environment

    Returns:
        RecipeOutput chứa CIIR
    """
    # === Main workflow stages ===
    lint_step = PipelineStep(
        step_id="lint_check",
        name="Lint & code quality",
        image="python:3.12-slim",
        commands=[
            "pip install flake8 black isort mypy",
            "flake8 midicoder/ --count --select=E9,F63,F7,F82 --show-source --statistics",
            "black --check --diff midicoder/",
            "isort --check-only --diff midicoder/",
            "mypy midicoder/ --ignore-missing-imports",
        ],
        timeout_minutes=10,
    )

    build_step = PipelineStep(
        step_id="build_app",
        name="Build ứng dụng",
        image="python:3.12-slim",
        commands=[
            "python -m pip install --upgrade pip",
            "pip install -e \".[dev]\"",
        ],
        timeout_minutes=15,
    )

    test_step = PipelineStep(
        step_id="run_tests",
        name="Chạy test suite",
        image="python:3.12-slim",
        commands=[
            "pip install -e \".[test]\"",
            "python -m pytest tests/ -v --cov=midicoder --cov-report=xml --junitxml=report.xml",
        ],
        env={"COVERAGE_FILE": ".coverage", "PYTEST_ADDOPTS": "-ra"},
        timeout_minutes=30,
        artifacts=["coverage.xml", "report.xml"],
    )

    docker_build_step = PipelineStep(
        step_id="docker_build",
        name="Build Docker image",
        image="",
        commands=[
            "docker build -t midicoder-ce:${{ github.sha }} .",
            "docker tag midicoder-ce:${{ github.sha }} midicoder-ce:latest",
        ],
        timeout_minutes=20,
    )

    container_scan_step = PipelineStep(
        step_id="container_scan",
        name="Container security scan (Trivy)",
        image="aquasec/trivy:latest",
        commands=[
            "trivy image --severity HIGH,CRITICAL --exit-code 1 midicoder-ce:${{ github.sha }}",
        ],
        timeout_minutes=15,
        env={"TRIVY_SEVERITY": "HIGH,CRITICAL"},
    )

    deploy_step = PipelineStep(
        step_id="deploy_app",
        name="Deploy ứng dụng",
        image="python:3.12-slim",
        commands=[
            "echo 'Deploying to staging environment'",
            "docker compose -f docker-compose.ci.yml up -d",
            "python scripts/health_check.py",
        ],
        timeout_minutes=20,
    )

    # === Định nghĩa stages ===
    lint_stage = PipelineStage(
        stage_id="lint",
        name="Lint & Code Quality",
        steps=[lint_step],
        allow_failure=False,
    )

    build_stage = PipelineStage(
        stage_id="build",
        name="Build",
        steps=[build_step],
        allow_failure=False,
    )

    test_stage = PipelineStage(
        stage_id="test",
        name="Test",
        steps=[test_step],
        needs=["build"],
        allow_failure=False,
    )

    docker_stage = PipelineStage(
        stage_id="docker",
        name="Docker Build & Scan",
        steps=[docker_build_step, container_scan_step],
        needs=["test"],
        allow_failure=False,
    )

    deploy_stage = PipelineStage(
        stage_id="deploy",
        name="Deploy",
        steps=[deploy_step],
        needs=["docker"],
        allow_failure=False,
    )

    # === Main workflow ===
    main_workflow = GitHubActionsWorkflow(
        workflow_id="build_test_deploy",
        name="Full CI/CD Pipeline",
        filename="build-test-deploy.yml",
        triggers=[PipelineTrigger.PUSH, PipelineTrigger.PULL_REQUEST],
        jobs={
            "lint": lint_stage,
            "build": build_stage,
            "test": test_stage,
            "docker": docker_stage,
            "deploy": deploy_stage,
        },
    )

    # === Docker publish workflow ===
    docker_publish_workflow = GitHubActionsWorkflow(
        workflow_id="docker_publish",
        name="Docker Image Publish",
        filename="docker-publish.yml",
        triggers=[PipelineTrigger.PUSH, PipelineTrigger.TAG],
        jobs={
            "publish": PipelineStage(
                stage_id="publish",
                name="Build & Publish Docker",
                steps=[
                    PipelineStep(
                        step_id="docker_login",
                        name="Login to registry",
                        image="",
                        commands=["echo ${{ secrets.REGISTRY_TOKEN }} | docker login -u ${{ secrets.REGISTRY_USER }} --password-stdin"],
                        timeout_minutes=5,
                    ),
                    PipelineStep(
                        step_id="docker_build_push",
                        name="Build and push",
                        image="",
                        commands=[
                            "docker buildx build --push -t registry.example.com/midicoder:${{ github.sha }} .",
                            "docker buildx build --push -t registry.example.com/midicoder:latest .",
                        ],
                        timeout_minutes=30,
                    ),
                ],
            ),
        },
    )

    # === Pipeline configs ===
    main_pipeline = PipelineConfig(
        pipeline_id="full_cicd_main",
        name="Full CI/CD Pipeline",
        platform=PipelinePlatform.GITHUB_ACTIONS,
        triggers=[PipelineTrigger.PUSH, PipelineTrigger.PULL_REQUEST],
        branches=["main", "develop", "release/*"],
        env_vars={
            "PYTHON_VERSION": "3.12",
            "DOCKER_REGISTRY": "registry.example.com",
            "TRIVY_SEVERITY": "HIGH,CRITICAL",
        },
    )

    docker_pipeline = PipelineConfig(
        pipeline_id="docker_publish_pipeline",
        name="Docker Publish Pipeline",
        platform=PipelinePlatform.GITHUB_ACTIONS,
        triggers=[PipelineTrigger.PUSH, PipelineTrigger.TAG],
        branches=["main"],
        env_vars={"DOCKER_REGISTRY": "registry.example.com"},
    )

    data = {
        "pipelines": [main_pipeline.to_dict(), docker_pipeline.to_dict()],
        "stages": [s.to_dict() for s in [lint_stage, build_stage, test_stage, docker_stage, deploy_stage]],
        "workflows": [main_workflow.to_dict(), docker_publish_workflow.to_dict()],
    }

    ir = parse_to_ir(data)

    return RecipeOutput(
        name="full_cicd_recipe",
        description="Full CI/CD — lint, build, test, Docker build, container scan, deploy",
        ir=ir,
        raw_data=data,
    )


__all__ = [
    "RecipeOutput",
    "github_actions_recipe",
    "gitlab_ci_recipe",
    "jenkins_recipe",
    "full_cicd_recipe",
]
