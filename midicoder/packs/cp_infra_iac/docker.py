"""
Docker Compose Generator — Generate Docker Compose từ MIR.

Module này cung cấp DockerComposeGenerator class để:
- Load MIR từ SQLite artifacts table
- Extract infrastructure requirements từ MIR operations
- Render Docker Compose template (Jinja2)
- Write docker-compose.yml vào output directory

Theo SoT E18, Docker Compose bao gồm:
- Backend (FastAPI/NestJS)
- Frontend (Angular/React)
- Database (PostgreSQL)
- Cache (Redis)
- Graph DB (Neo4j)

Services chỉ được include nếu được detect trong MIR (option B).

Sử dụng:
    from midicoder.packs.cp_infra_iac.docker import DockerComposeGenerator

    generator = DockerComposeGenerator()
    config = generator.extract_infrastructure(mir)
    compose_content = generator.render_template(config)
    generator.write_compose(compose_content, output_path)

Author: Midicoder Team
Version: 2.0.0
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import jinja2

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM
from midicoder.storage.sqlite import ArtifactsManager


# ============================================================================
# DockerComposeGenerator
# ============================================================================


class DockerComposeGenerator:
    """
    Docker Compose Generator từ MIR.

    Generator này:
    1. Load MIR từ SQLite artifacts
    2. Extract infrastructure requirements từ operations và metadata
    3. Render Docker Compose template với Jinja2
    4. Write docker-compose.yml vào output path

    Detection rules cho services:
    - Backend: operations với op_type chứa "api", "handler", "controller", "service"
    - Frontend: operations với op_type chứa "ui", "view", "component", "page"
    - PostgreSQL: operations với op_type chứa "db", "repository", "persist", "crud"
    - Redis: operations với obligation_refs chứa "cache"
    - Neo4j: operations với op_type chứa "graph", "knowledge", "relationship"

    Attributes:
        template_path: Path đến Docker Compose template

    Ví dụ:
        generator = DockerComposeGenerator()
        config = generator.extract_infrastructure(mir)
        compose_content = generator.render_template(config)
        generator.write_compose(compose_content, output_path)
    """

    def __init__(self, template_path: str | None = None) -> None:
        """
        Initialize DockerComposeGenerator.

        Args:
            template_path: Custom template path (optional)
        """
        # Template path mặc định
        if template_path:
            self.template_path = Path(template_path)
        else:
            self.template_path = (
                Path(__file__).parent.parent.parent / "stacks" / "infrastructure" / "docker-compose.j2"
            )

    def load_mir_from_sqlite(self, version: str = "v1.0.0") -> "MIR":
        """
        Load MIR từ SQLite artifacts table.

        Load MIR JSON từ artifacts table với artifact_type="mir".
        Nếu có multiple MIR artifacts, lấy newest.

        Args:
            version: Version để load MIR (default: v1.0.0)

        Returns:
            MIR instance

        Raises:
            MidicoderError: Nếu không tìm thấy MIR trong artifacts
        """
        # Late import để tránh circular import
        from midicoder.pipeline.mir import MIR
        artifacts_manager = ArtifactsManager()
        artifacts_manager.init()

        # Query MIR artifacts
        mir_artifacts = artifacts_manager.get_by_type("mir")

        if not mir_artifacts:
            EM.raise_error(
                ErrorCode.MIR_GRAPH_NOT_FOUND,
                version=version,
                suggestions=[
                    "Chạy 'midicoder ir build' để tạo MIR từ Contract Graph",
                    "Kiểm tra artifacts table: SELECT * FROM artifacts WHERE artifact_type='mir'"
                ]
            )

        # Lấy newest MIR (hoặc MIR cho version cụ thể)
        mir_json = None
        for artifact in mir_artifacts:
            artifact_id = artifact.get("artifact_id", "")
            if version in artifact_id or "mir" in artifact_id:
                mir_json = artifact.get("content")
                break

        if not mir_json:
            # Fallback: lấy artifact đầu tiên
            mir_json = mir_artifacts[0].get("content")

        if not mir_json:
            EM.raise_error(
                ErrorCode.MIR_GRAPH_NOT_FOUND,
                version=version,
                suggestions=["MIR content trống. Kiểm tra artifacts table."]
            )

        # Parse MIR JSON
        try:
            mir = MIR.from_json(mir_json)
        except Exception as e:
            EM.raise_error(
                ErrorCode.MIR_GRAPH_NOT_FOUND,
                error=str(e),
                suggestions=["MIR JSON format không hợp lệ. Chạy 'midicoder ir build' lại."]
            )

        return mir

    def extract_infrastructure(
        self, mir: "MIR", override_config: dict[str, Any] | None = None
    ) -> "InfrastructureConfig":
        """
        Extract infrastructure requirements từ MIR.

        Scan MIR operations và metadata để detect services cần thiết:
        - Backend: operations với op_type chứa "api", "handler", "controller", "service"
        - Frontend: operations với op_type chứa "ui", "view", "component", "page"
        - Stack: từ MIR metadata (backend_stack, frontend_stack)

        Args:
            mir: MIR instance để extract
            override_config: Override configuration (optional)

        Returns:
            InfrastructureConfig với detected requirements

        Ví dụ:
            mir = load_mir()
            config = generator.extract_infrastructure(mir)
            print(config.has_backend)  # True nếu detect backend operations
        """
        from midicoder.packs.cp_infra_iac.models import InfrastructureConfig

        # Default config
        has_backend = False
        has_frontend = False
        # Default values
        backend_stack = "fastapi"
        frontend_stack = "angular"

        # Detection keywords cho các services
        backend_keywords = ["api", "handler", "controller", "service", "route", "endpoint", "crud"]
        frontend_keywords = ["ui", "view", "component", "page", "screen", "form"]

        # Scan operations
        for operation in mir.operations:
            op_type = operation.op_type.lower()
            op_params = operation.params or {}

            # Detect backend
            if not has_backend:
                for keyword in backend_keywords:
                    if keyword in op_type:
                        has_backend = True
                        break
                # Hoặc nếu params có "entity" hoặc "model" (backend operations)
                if not has_backend and ("entity" in op_params or "model" in op_params):
                    has_backend = True

            # Detect frontend
            if not has_frontend:
                for keyword in frontend_keywords:
                    if keyword in op_type:
                        has_frontend = True
                        break

        # Read stack từ metadata (override_config ưu tiên hơn metadata)
        # Priority: override_config > metadata > default
        metadata = mir.metadata or {}

        # Override config có ưu tiên cao nhất
        if override_config:
            if "backend_stack" in override_config:
                backend_stack = override_config["backend_stack"]
            if "frontend_stack" in override_config:
                frontend_stack = override_config["frontend_stack"]
        # Sau đó là metadata
        elif metadata:
            if "backend_stack" in metadata:
                backend_stack = metadata["backend_stack"]
            if "frontend_stack" in metadata:
                frontend_stack = metadata["frontend_stack"]
        # Mặc định đã được set ở đầu function

        # Create config
        config = InfrastructureConfig(
            has_backend=has_backend,
            has_frontend=has_frontend,
            backend_stack=backend_stack,
            frontend_stack=frontend_stack
        )

        return config

    def render_template(self, config: "InfrastructureConfig") -> str:
        """
        Render Docker Compose template với Jinja2.

        Load template từ template_path và render với config variables.

        Args:
            config: InfrastructureConfig để render template

        Returns:
            Rendered Docker Compose YAML string

        Raises:
            MidicoderError: Nếu template không tìm thấy hoặc render failed

        Ví dụ:
            config = InfrastructureConfig(has_backend=True, has_frontend=True)
            compose_content = generator.render_template(config)
        """
        # Check template exists
        if not self.template_path.exists():
            EM.raise_error(
                ErrorCode.INFRA_TEMPLATE_NOT_FOUND,
                template_path=str(self.template_path),
                suggestions=[
                    "Kiểm tra template path có chính xác không",
                    "Đảm bảo file docker-compose.j2 tồn tại"
                ]
            )

        # Load template
        try:
            template_content = self.template_path.read_text(encoding="utf-8")
            template = jinja2.Template(template_content)
        except Exception as e:
            EM.raise_error(
                ErrorCode.INFRA_TEMPLATE_NOT_FOUND,
                error=str(e),
                suggestions=["Template file corrupted hoặc permission denied."]
            )

        # Render template
        try:
            render_context = {
                "has_backend": config.has_backend,
                "has_frontend": config.has_frontend,
                "backend_stack": config.backend_stack,
                "frontend_stack": config.frontend_stack,
                "backend_port": config.backend_port,
                "frontend_port": config.frontend_port,
                "postgres_password": config.postgres_password,
                "postgres_database": config.postgres_database,
                "neo4j_user": config.neo4j_user,
                "neo4j_password": config.neo4j_password,
                "jwt_secret": config.jwt_secret,
                "services": config.services
            }
            compose_content = template.render(**render_context)
        except Exception as e:
            EM.raise_error(
                ErrorCode.INFRA_TEMPLATE_RENDER_FAILED,
                error=str(e),
                suggestions=["Template syntax error hoặc missing variables."]
            )

        return compose_content

    def write_compose(self, compose_content: str, output_path: Path) -> None:
        """
        Write Docker Compose content vào file.

        Create output directory nếu không tồn tại và write compose content.

        Args:
            compose_content: Docker Compose YAML content
            output_path: Path để write docker-compose.yml

        Raises:
            MidicoderError: Nếu write failed

        Ví dụ:
            compose_content = generator.render_template(config)
            generator.write_compose(compose_content, Path(".midicoder/versions/v1.0.0/src/docker-compose.yml"))
        """
        # Create output directory
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        try:
            output_path.write_text(compose_content, encoding="utf-8")
        except Exception as e:
            EM.raise_error(
                ErrorCode.INFRA_WRITE_FAILED,
                path=str(output_path),
                error=str(e),
                suggestions=[
                    "Kiểm tra quyền ghi vào output directory",
                    "Đảm bảo đủ dung lượng đĩa",
                    "Kiểm tra file không bị lock"
                ]
            )

    def generate(
        self, mir: "MIR", output_path: Path, override_config: dict[str, Any] | None = None
    ) -> "InfrastructureConfig":
        """
        Generate Docker Compose từ MIR (full pipeline).

        Full pipeline: extract -> render -> write.

        Args:
            mir: MIR instance
            output_path: Output path cho docker-compose.yml
            override_config: Override configuration (optional)

        Returns:
            InfrastructureConfig được sử dụng

        Ví dụ:
            mir = generator.load_mir_from_sqlite()
            config = generator.generate(mir, Path(".midicoder/versions/v1.0.0/src/docker-compose.yml"))
            print(f"Generated with services: {config.services}")
        """
        # Step 1: Extract infrastructure config
        config = self.extract_infrastructure(mir, override_config)

        # Step 2: Render template
        compose_content = self.render_template(config)

        # Step 3: Write output
        self.write_compose(compose_content, output_path)

        return config