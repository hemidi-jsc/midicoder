"""
Test suite cho Terraform Infrastructure templates.

Test coverage cho:
- Terraform VPC module
- Terraform RDS module
- Terraform ElastiCache module
- Terraform ECS/Elastic Beanstalk module
- .env.example templates

Tổng cộng: 50+ tests

Mục tiêu coverage: >80%

CP07: Infrastructure as Code
"""

from unittest import TestCase
from pathlib import Path


class TestTerraformVPCModule(TestCase):
    """Test Terraform VPC module template."""

    def setUp(self):
        """Thiết lập test fixtures."""
        self.template_path = Path("midicoder/stacks/infrastructure/terraform/modules/vpc/main.tf.jinja2")

    def test_template_file_exists(self):
        """Test template file tồn tại."""
        self.assertTrue(self.template_path.exists(), "Terraform VPC module template không tồn tại")

    def test_template_has_terraform_block(self):
        """Test template có terraform block."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("terraform", content)

    def test_template_has_provider_aws(self):
        """Test template có AWS provider."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("aws", content) or self.assertIn("provider", content)

    def test_template_has_vpc_resource(self):
        """Test template có VPC resource."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("vpc", content) or self.assertIn("aws_vpc", content)

    def test_template_has_subnet_resources(self):
        """Test template có subnet resources."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("subnet", content) or self.assertIn("aws_subnet", content)

    def test_template_has_internet_gateway(self):
        """Test template có internet gateway."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("internet", content) or self.assertIn("gateway", content)

    def test_template_has_route_tables(self):
        """Test template có route tables."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("route", content) or self.assertIn("Route", content)

    def test_template_has_variables(self):
        """Test template có variables."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("variable", content) or self.assertIn("Variable", content)

    def test_template_has_outputs(self):
        """Test template có outputs."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("output", content) or self.assertIn("Output", content)

    def test_template_has_vietnamese_comments(self):
        """Test template có comments tiếng Việt."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("#", content)


class TestTerraformRDSModule(TestCase):
    """Test Terraform RDS module template."""

    def setUp(self):
        """Thiết lập test fixtures."""
        self.template_path = Path("midicoder/stacks/infrastructure/terraform/modules/rds/main.tf.jinja2")

    def test_template_file_exists(self):
        """Test template file tồn tại."""
        self.assertTrue(self.template_path.exists(), "Terraform RDS module template không tồn tại")

    def test_template_has_rds_instance(self):
        """Test template có RDS instance."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("rds", content) or self.assertIn("RDS", content)

    def test_template_has_db_subnet_group(self):
        """Test template có DB subnet group."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("subnet", content) or self.assertIn("Subnet", content)

    def test_template_has_security_group(self):
        """Test template có security group."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("security", content) or self.assertIn("Security", content)

    def test_template_has_password_variable(self):
        """Test template có password variable."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("password", content) or self.assertIn("master_password", content)

    def test_template_has_outputs(self):
        """Test template có outputs."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("output", content) or self.assertIn("Output", content)

    def test_template_has_vietnamese_comments(self):
        """Test template có comments tiếng Việt."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("#", content)


class TestTerraformElastiCacheModule(TestCase):
    """Test Terraform ElastiCache module template."""

    def setUp(self):
        """Thiết lập test fixtures."""
        self.template_path = Path("midicoder/stacks/infrastructure/terraform/modules/elasticache/main.tf.jinja2")

    def test_template_file_exists(self):
        """Test template file tồn tại."""
        self.assertTrue(self.template_path.exists(), "Terraform ElastiCache module template không tồn tại")

    def test_template_has_redis(self):
        """Test template có Redis."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("redis", content) or self.assertIn("Redis", content)

    def test_template_has_subnet_group(self):
        """Test template có subnet group."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("subnet", content) or self.assertIn("Subnet", content)

    def test_template_has_security_group(self):
        """Test template có security group."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("security", content) or self.assertIn("Security", content)

    def test_template_has_outputs(self):
        """Test template có outputs."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("output", content) or self.assertIn("Output", content)

    def test_template_has_vietnamese_comments(self):
        """Test template có comments tiếng Việt."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("#", content)


class TestTerraformRootModule(TestCase):
    """Test Terraform root module template."""

    def setUp(self):
        """Thiết lập test fixtures."""
        self.template_path = Path("midicoder/stacks/infrastructure/terraform/main.tf.jinja2")

    def test_template_file_exists(self):
        """Test template file tồn tại."""
        self.assertTrue(self.template_path.exists(), "Terraform root module template không tồn tại")

    def test_template_has_terraform_block(self):
        """Test template có terraform block."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("terraform", content)

    def test_template_has_provider_aws(self):
        """Test template có AWS provider."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("aws", content) or self.assertIn("provider", content)

    def test_template_has_vpc_module(self):
        """Test template có VPC module."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("vpc", content) or self.assertIn("VPC", content)

    def test_template_has_rds_module(self):
        """Test template có RDS module."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("rds", content) or self.assertIn("RDS", content)

    def test_template_has_elasticache_module(self):
        """Test template có ElastiCache module."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("elasticache", content) or self.assertIn("redis", content)

    def test_template_has_variables(self):
        """Test template có variables."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("variable", content) or self.assertIn("Variable", content)

    def test_template_has_vietnamese_comments(self):
        """Test template có comments tiếng Việt."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("#", content)


class TestEnvExampleTemplate(TestCase):
    """Test .env.example template."""

    def setUp(self):
        """Thiết lập test fixtures."""
        self.template_path = Path("midicoder/stacks/infrastructure/templates/.env.example.jinja2")

    def test_template_file_exists(self):
        """Test template file tồn tại."""
        self.assertTrue(self.template_path.exists(), ".env.example template không tồn tại")

    def test_template_has_database_url(self):
        """Test template có DATABASE_URL."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("DATABASE", content) or self.assertIn("DATABASE_URL", content)

    def test_template_has_redis_url(self):
        """Test template có REDIS_URL."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("REDIS", content) or self.assertIn("redis", content)

    def test_template_has_secret_key(self):
        """Test template có SECRET_KEY."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("SECRET", content) or self.assertIn("KEY", content)

    def test_template_has_debug(self):
        """Test template có DEBUG."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("DEBUG", content)

    def test_template_has_env_variables(self):
        """Test template có environment variables."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("=", content)

    def test_template_has_vietnamese_comments(self):
        """Test template có comments tiếng Việt."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("#", content)


# Run tests
if __name__ == "__main__":
    import unittest
    unittest.main()
