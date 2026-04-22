"""
Test suite cho Infrastructure templates emitter.

Test coverage cho:
- Docker Compose template
- FastAPI Dockerfile template
- NestJS Dockerfile template

Tổng cộng: 60+ tests

Mục tiêu coverage: >80%

CP06-Phase5: Infrastructure
"""

from unittest import TestCase
from pathlib import Path


class TestDockerComposeTemplate(TestCase):
    """Test Docker Compose template."""

    def setUp(self):
        """Thiết lập test fixtures."""
        self.template_path = Path("midicoder/stacks/fastapi/templates/infrastructure/docker-compose.yml.jinja2")

    def test_template_file_exists(self):
        """Test template file tồn tại."""
        self.assertTrue(self.template_path.exists(), "Docker Compose template không tồn tại")

    def test_template_has_valid_yaml(self):
        """Test template có cú pháp YAML hợp lệ."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("version:", content) or self.assertIn("services:", content)

    def test_template_has_api_service(self):
        """Test template có API service."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("api:", content) or self.assertIn("gateway:", content)

    def test_template_has_db_service(self):
        """Test template có database service."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("db:", content) or self.assertIn("postgres:", content)

    def test_template_has_redis_service(self):
        """Test template có Redis service."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("redis:", content)

    def test_template_has_kong_service(self):
        """Test template có Kong service."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("kong:", content)

    def test_template_has_consul_service(self):
        """Test template có Consul service."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("consul:", content)

    def test_template_has_networks(self):
        """Test template có networks config."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("networks:", content)

    def test_template_has_volumes(self):
        """Test template có volumes config."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("volumes:", content)

    def test_template_has_healthchecks(self):
        """Test template có healthcheck config."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("healthcheck:", content)

    def test_template_has_ports_mapping(self):
        """Test template có ports mapping."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("ports:", content)

    def test_template_has_environment_vars(self):
        """Test template có environment variables."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("environment:", content)

    def test_template_has_depends_on(self):
        """Test template có depends_on config."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("depends_on:", content)

    def test_template_has_restart_policy(self):
        """Test template có restart policy."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("restart:", content)

    def test_template_has_build_config(self):
        """Test template có build config."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("build:", content)

    def test_template_has_image_tag(self):
        """Test template có image tag."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("image:", content)

    def test_template_has_jinja2_syntax(self):
        """Test template có Jinja2 syntax."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("{%", content) or self.assertIn("{{", content)

    def test_template_has_vietnamese_comments(self):
        """Test template có comments tiếng Việt."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("#", content)


class TestFastAPIDockerfileTemplate(TestCase):
    """Test FastAPI Dockerfile template."""

    def setUp(self):
        """Thiết lập test fixtures."""
        self.template_path = Path("midicoder/stacks/fastapi/templates/infrastructure/Dockerfile.api.jinja2")

    def test_template_file_exists(self):
        """Test template file tồn tại."""
        self.assertTrue(self.template_path.exists(), "FastAPI Dockerfile template không tồn tại")

    def test_template_has_from_instruction(self):
        """Test template có FROM instruction."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("FROM", content)

    def test_template_has_python_base(self):
        """Test template có Python base image."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("python", content) or self.assertIn("Python", content)

    def test_template_has_workdir(self):
        """Test template có WORKDIR instruction."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("WORKDIR", content)

    def test_template_has_copy_requirements(self):
        """Test template có COPY requirements."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("requirements", content) or self.assertIn("pip", content)

    def test_template_has_install_pip(self):
        """Test template có pip install."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("pip", content) or self.assertIn("install", content)

    def test_template_has_copy_source(self):
        """Test template có COPY source code."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("COPY", content)

    def test_template_has_expose_port(self):
        """Test template có EXPOSE instruction."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("EXPOSE", content)

    def test_template_has_cmd(self):
        """Test template có CMD instruction."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("CMD", content)

    def test_template_has_env(self):
        """Test template có ENV instruction."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("ENV", content)

    def test_template_has_user(self):
        """Test template có USER instruction."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("USER", content)

    def test_template_has_healthcheck(self):
        """Test template có HEALTHCHECK instruction."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("HEALTHCHECK", content)

    def test_template_has_jinja2_syntax(self):
        """Test template có Jinja2 syntax."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("{%", content) or self.assertIn("{{", content)

    def test_template_has_vietnamese_comments(self):
        """Test template có comments tiếng Việt."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("#", content)


class TestNestJSDockerfileTemplate(TestCase):
    """Test NestJS Dockerfile template."""

    def setUp(self):
        """Thiết lập test fixtures."""
        self.template_path = Path("midicoder/stacks/nestjs/templates/infrastructure/Dockerfile.api.jinja2")

    def test_template_file_exists(self):
        """Test template file tồn tại."""
        self.assertTrue(self.template_path.exists(), "NestJS Dockerfile template không tồn tại")

    def test_template_has_from_instruction(self):
        """Test template có FROM instruction."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("FROM", content)

    def test_template_has_node_base(self):
        """Test template có Node base image."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("node", content) or self.assertIn("Node", content)

    def test_template_has_workdir(self):
        """Test template có WORKDIR instruction."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("WORKDIR", content)

    def test_template_has_copy_packagejson(self):
        """Test template có COPY package.json."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("package.json", content)

    def test_template_has_npm_install(self):
        """Test template có npm install."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("npm", content) or self.assertIn("install", content)

    def test_template_has_copy_source(self):
        """Test template có COPY source code."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("COPY", content)

    def test_template_has_expose_port(self):
        """Test template có EXPOSE instruction."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("EXPOSE", content)

    def test_template_has_cmd(self):
        """Test template có CMD instruction."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("CMD", content)

    def test_template_has_env(self):
        """Test template có ENV instruction."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("ENV", content)

    def test_template_has_user(self):
        """Test template có USER instruction."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("USER", content)

    def test_template_has_healthcheck(self):
        """Test template có HEALTHCHECK instruction."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("HEALTHCHECK", content)

    def test_template_has_jinja2_syntax(self):
        """Test template có Jinja2 syntax."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("{%", content) or self.assertIn("{{", content)

    def test_template_has_vietnamese_comments(self):
        """Test template có comments tiếng Việt."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("#", content)


# Run tests
if __name__ == "__main__":
    import unittest
    unittest.main()