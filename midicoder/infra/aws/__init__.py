"""
AWS Infrastructure Module - Generate AWS Terraform từ MIR.

Module này cung cấp các công cụ để generate AWS Terraform configuration
từ MIR (Midicoder Intermediate Representation).

Các components:
- terraform: Terraform generator logic
- AWSInfrastructureConfig: Data class cho AWS config
- TerraformGenerator: Class chính để generate Terraform

Sử dụng:
    from midicoder.infra.aws import TerraformGenerator, AWSInfrastructureConfig
    
    generator = TerraformGenerator()
    config = generator.extract_aws_infrastructure(mir)
    files = generator.render_terraform(config)
    generator.write_terraform(files, output_dir)

Author: Midicoder Team
Version: 1.0.0
"""

from midicoder.infra.aws.terraform import (
    AWSInfrastructureConfig,
    TerraformGenerator,
)

__all__ = ["AWSInfrastructureConfig", "TerraformGenerator"]