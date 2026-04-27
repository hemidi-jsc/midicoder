"""
Infra Module - Infrastructure Generation.

Module này cung cấp các công cụ để generate infrastructure configuration
từ MIR (Midicoder Intermediate Representation).

Các submodules:
- docker: Docker Compose generation
- aws: AWS Terraform generation (future)

Sử dụng:
    from midicoder.infra.docker import DockerComposeGenerator
    
    generator = DockerComposeGenerator()
    generator.generate(mir, output_path)

Author: Midicoder Team
Version: 1.0.0
"""

from midicoder.infra.docker import DockerComposeGenerator

__all__ = ["DockerComposeGenerator"]