"""
AWS Terraform Generator — Generate Terraform từ MIR.

Module này cung cấp TerraformGenerator class để:
- Load MIR từ SQLite artifacts table
- Extract AWS infrastructure requirements từ MIR operations
- Render Terraform templates (Jinja2)
- Write Terraform files vào output directory

Theo SoT E18, AWS infrastructure bao gồm:
- API: ECS/Elastic Beanstalk
- Database: RDS/Aurora
- Cache: ElastiCache
- Graph DB: Neo4j Aura
- Storage: S3

Services chỉ được include nếu được detect trong MIR (option B).

Sử dụng:
    from midicoder.packs.cp_infra_iac.terraform import TerraformGenerator

    generator = TerraformGenerator()
    config = generator.extract_aws_infrastructure(mir)
    files = generator.render_terraform(config)
    generator.write_terraform(files, output_dir)

Author: Midicoder Team
Version: 2.0.0
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import jinja2

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# ============================================================================
# TerraformGenerator
# ============================================================================


class TerraformGenerator:
    """
    Terraform Generator từ MIR.

    Generator này:
    1. Load MIR từ SQLite artifacts
    2. Extract AWS infrastructure requirements từ operations và metadata
    3. Render Terraform templates với Jinja2
    4. Write Terraform files vào output path

    Detection rules cho services:
    - ECS/API: operations với op_type chứa "api", "handler", "controller", "service"
    - RDS: operations với op_type chứa "db", "repository", "persist", "crud"
    - ElastiCache: operations với obligation_refs chứa "cache"
    - Neo4j: operations với op_type chứa "graph", "knowledge", "relationship"
    - S3: operations với op_type chứa "storage", "upload", "download"

    Attributes:
        template_path: Path đến Terraform templates directory

    Ví dụ:
        generator = TerraformGenerator()
        config = generator.extract_aws_infrastructure(mir)
        files = generator.render_terraform(config)
        generator.write_terraform(files, output_path)
    """

    def __init__(self, template_path: str | None = None) -> None:
        """
        Initialize TerraformGenerator.

        Args:
            template_path: Custom template path (optional)
        """
        # Template path mặc định - sử dụng infrastructure/terraform
        if template_path:
            self.template_path = Path(template_path)
        else:
            self.template_path = (
                Path(__file__).parent.parent.parent / "stacks" / "infrastructure" / "terraform"
            )

    def extract_aws_infrastructure(
        self, mir: "MIR", override_config: dict[str, Any] | None = None
    ) -> "AWSInfrastructureConfig":
        """
        Extract AWS infrastructure requirements từ MIR.

        Scan MIR operations và metadata để detect services cần thiết:
        - ECS: operations với op_type chứa "api", "handler", "controller"
        - RDS: operations với op_type chứa "db", "repository", "persist"
        - ElastiCache: operations với obligation_refs chứa "cache"
        - Neo4j: operations với op_type chứa "graph", "knowledge"
        - S3: operations với op_type chứa "storage", "upload", "download"

        Args:
            mir: MIR instance để extract
            override_config: Override configuration (optional)

        Returns:
            AWSInfrastructureConfig với detected requirements

        Ví dụ:
            mir = load_mir()
            config = generator.extract_aws_infrastructure(mir)
            print(config.use_ecs)  # True nếu detect API operations
        """
        from midicoder.packs.cp_infra_iac.models import (
            AWSInfrastructureConfig,
            DEFAULT_AWS_REGION,
        )

        # Default config values
        use_ecs = True
        use_redis = True
        use_neo4j = True
        use_s3 = True

        # Detection keywords cho các services
        api_keywords = ["api", "handler", "controller", "service", "route", "endpoint"]
        db_keywords = ["db", "repository", "persist", "crud", "query"]
        cache_keywords = ["cache", "redis"]
        graph_keywords = ["graph", "knowledge", "relationship", "neo4j"]
        storage_keywords = ["storage", "upload", "download", "s3", "bucket"]

        # Flags để track detection
        detected_api = False
        detected_db = False
        detected_cache = False
        detected_graph = False
        detected_storage = False

        # Scan operations
        for operation in mir.operations:
            op_type = operation.op_type.lower()
            op_params = operation.params or {}
            obligation_refs = operation.obligation_refs or []

            # Detect API/ECS
            if not detected_api:
                for keyword in api_keywords:
                    if keyword in op_type:
                        detected_api = True
                        break
                if not detected_api and ("entity" in op_params or "method" in op_params):
                    detected_api = True

            # Detect Database
            if not detected_db:
                for keyword in db_keywords:
                    if keyword in op_type:
                        detected_db = True
                        break

            # Detect Cache
            if not detected_cache:
                for keyword in cache_keywords:
                    if keyword in op_type:
                        detected_cache = True
                        break
                if "cache" in obligation_refs:
                    detected_cache = True

            # Detect Neo4j/Graph
            if not detected_graph:
                for keyword in graph_keywords:
                    if keyword in op_type:
                        detected_graph = True
                        break

            # Detect S3/Storage
            if not detected_storage:
                for keyword in storage_keywords:
                    if keyword in op_type:
                        detected_storage = True
                        break
                if "bucket" in op_params or "key" in op_params:
                    detected_storage = True

        # Read config từ metadata (override_config ưu tiên hơn metadata)
        metadata = mir.metadata or {}

        # Build config với priority: override_config > metadata > default
        app_name = override_config.get("app_name") if override_config else None
        if not app_name:
            app_name = metadata.get("app_name", "midicoder-app")

        region = override_config.get("region") if override_config else None
        if not region:
            region = metadata.get("region", DEFAULT_AWS_REGION)

        # Create config
        config = AWSInfrastructureConfig(
            app_name=app_name,
            region=region,
            use_ecs=override_config.get("use_ecs", detected_api) if override_config else detected_api,
            use_redis=override_config.get("use_redis", detected_cache) if override_config else detected_cache,
            use_neo4j=override_config.get("use_neo4j", detected_graph) if override_config else detected_graph,
            use_s3=override_config.get("use_s3", detected_storage) if override_config else detected_storage,
        )

        return config

    def render_terraform(self, config: "AWSInfrastructureConfig") -> dict[str, str]:
        """
        Render Terraform templates với Jinja2.

        Load templates từ template_path và render với config variables.
        Returns mapping của file paths → Terraform content.

        Args:
            config: AWSInfrastructureConfig để render templates

        Returns:
            Dictionary mapping file paths to Terraform content

        Raises:
            MidicoderError: Nếu template không tìm thấy hoặc render failed

        Ví dụ:
            config = AWSInfrastructureConfig(app_name="my-app")
            files = generator.render_terraform(config)
            print(files["main.tf"])
        """
        files: dict[str, str] = {}

        # Check template directory exists
        if not self.template_path.exists():
            EM.raise_error(
                ErrorCode.INFRA_TEMPLATE_NOT_FOUND,
                template_path=str(self.template_path),
                suggestions=[
                    "Kiểm tra template path có chính xác không",
                    "Đảm bảo thư mục stacks/aws/terraform tồn tại",
                ],
            )

        # Render main.tf
        main_template = self.template_path / "main.tf.j2"
        if main_template.exists():
            try:
                template_content = main_template.read_text(encoding="utf-8")
                template = jinja2.Template(template_content)
                files["main.tf"] = template.render(config=config)
            except Exception as e:
                EM.raise_error(
                    ErrorCode.INFRA_TEMPLATE_RENDER_FAILED,
                    template=str(main_template),
                    error=str(e),
                    suggestions=["Template syntax error hoặc missing variables."],
                )

        # Render variables.tf
        variables_template = self.template_path / "variables.tf.j2"
        if variables_template.exists():
            try:
                template_content = variables_template.read_text(encoding="utf-8")
                template = jinja2.Template(template_content)
                files["variables.tf"] = template.render(config=config)
            except Exception as e:
                EM.raise_error(
                    ErrorCode.INFRA_TEMPLATE_RENDER_FAILED,
                    template=str(variables_template),
                    error=str(e),
                )

        # Render outputs.tf
        outputs_template = self.template_path / "outputs.tf.j2"
        if outputs_template.exists():
            try:
                template_content = outputs_template.read_text(encoding="utf-8")
                template = jinja2.Template(template_content)
                files["outputs.tf"] = template.render(config=config)
            except Exception as e:
                EM.raise_error(
                    ErrorCode.INFRA_TEMPLATE_RENDER_FAILED,
                    template=str(outputs_template),
                    error=str(e),
                )

        # Render module files
        modules_dir = self.template_path / "modules"
        if modules_dir.exists():
            for module_dir in modules_dir.iterdir():
                if module_dir.is_dir():
                    module_name = module_dir.name
                    module_main = module_dir / "main.tf.j2"
                    if module_main.exists():
                        try:
                            template_content = module_main.read_text(encoding="utf-8")
                            template = jinja2.Template(template_content)
                            files[f"modules/{module_name}/main.tf"] = template.render(
                                config=config
                            )
                        except Exception as e:
                            EM.raise_error(
                                ErrorCode.INFRA_TEMPLATE_RENDER_FAILED,
                                template=str(module_main),
                                error=str(e),
                            )

        return files

    def write_terraform(self, files: dict[str, str], output_dir: Path) -> None:
        """
        Write Terraform files vào output directory.

        Create output directory nếu không tồn tại và write tất cả files.

        Args:
            files: Dictionary mapping file paths to Terraform content
            output_dir: Output directory để write files

        Raises:
            MidicoderError: Nếu write failed

        Ví dụ:
            files = generator.render_terraform(config)
            generator.write_terraform(files, Path(".midicoder/versions/v1.0.0/terraform"))
        """
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)

        # Write each file
        for file_path, content in files.items():
            full_path = output_dir / file_path

            # Create parent directories
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file
            try:
                full_path.write_text(content, encoding="utf-8")
            except Exception as e:
                EM.raise_error(
                    ErrorCode.INFRA_WRITE_FAILED,
                    path=str(full_path),
                    error=str(e),
                    suggestions=[
                        "Kiểm tra quyền ghi vào output directory",
                        "Đảm bảo đủ dung lượng đĩa",
                        "Kiểm tra file không bị lock",
                    ],
                )

    def generate(
        self,
        mir: "MIR",
        output_dir: Path,
        override_config: dict[str, Any] | None = None,
    ) -> "AWSInfrastructureConfig":
        """
        Generate Terraform từ MIR (full pipeline).

        Full pipeline: extract → render → write.

        Args:
            mir: MIR instance
            output_dir: Output directory cho Terraform files
            override_config: Override configuration (optional)

        Returns:
            AWSInfrastructureConfig được sử dụng

        Ví dụ:
            mir = load_mir()
            config = generator.generate(mir, Path("terraform"))
            print(f"Generated Terraform with config: {config.app_name}")
        """
        # Step 1: Extract infrastructure config
        config = self.extract_aws_infrastructure(mir, override_config)

        # Step 2: Render templates
        files = self.render_terraform(config)

        # Step 3: Write output
        self.write_terraform(files, output_dir)

        return config