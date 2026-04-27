"""
Infra Module - Infrastructure Generation.

Module này cung cấp các công cụ để generate infrastructure configuration
từ MIR (Midicoder Intermediate Representation).

Các submodules:
- docker: Docker Compose generation
- aws: AWS Terraform generation

Sử dụng:
    from midicoder.infra.docker import DockerComposeGenerator
    from midicoder.infra.aws import TerraformGenerator, AWSInfrastructureConfig
    
    # Docker Compose
    docker_gen = DockerComposeGenerator()
    docker_gen.generate(mir, output_path)
    
    # AWS Terraform
    aws_gen = TerraformGenerator()
    aws_gen.generate(mir, output_dir)

Author: Midicoder Team
Version: 1.0.0
"""

from midicoder.infra.docker import DockerComposeGenerator
from midicoder.infra.aws import AWSInfrastructureConfig, TerraformGenerator

__all__ = ["DockerComposeGenerator", "AWSInfrastructureConfig", "TerraformGenerator"]
