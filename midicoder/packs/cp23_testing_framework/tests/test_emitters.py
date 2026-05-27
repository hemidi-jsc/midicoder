# coding: utf-8
"""
Test cases cho CP23 stack emitters (FastAPI, NestJS, Angular, React).

Kiểm tra:
- FastAPITestEmitter.generate()
- NestJSTestEmitter.generate()
- AngularTestEmitter.generate()
- ReactTestEmitter.generate()
- Output structure và content
- Stack emitters internal methods
"""

import pytest

from midicoder.packs.cp23_testing_framework.models import (
    AssertionCheck,
    TestCase,
    TestCollection,
    TestFramework,
    TestSuite,
    TestType,
    TestAssertion,
)
from midicoder.packs.cp23_testing_framework.fastapi import FastAPITestEmitter
from midicoder.packs.cp23_testing_framework.nestjs import NestJSTestEmitter
from midicoder.packs.cp23_testing_framework.angular import AngularTestEmitter
from midicoder.packs.cp23_testing_framework.react import ReactTestEmitter


class TestFastAPITestEmitter:
    """Test FastAPITestEmitter."""

    def test_create_emitter(self):
        """Kiểm tra tạo emitter."""
        emitter = FastAPITestEmitter(stack_dir="stacks/fastapi/core")
        assert emitter is not None

    def test_generate_with_empty_collection(self):
        """Kiểm tra generate với collection rỗng."""
        emitter = FastAPITestEmitter(stack_dir="stacks/fastapi/core")
        collection = TestCollection()
        result = emitter.generate(collection)
        assert isinstance(result, list)

    def test_generate_with_suites(self):
        """Kiểm tra generate với suites."""
        emitter = FastAPITestEmitter(stack_dir="stacks/fastapi/core")
        collection = TestCollection()
        suite = TestSuite(name="unit", framework=TestFramework.PYTEST, test_type=TestType.UNIT)
        suite.add_case(TestCase(
            id="t1", type=TestType.UNIT, target="User", scenario="create",
            assertions=[TestAssertion(check=AssertionCheck.EQUAL, expected=1)],
        ))
        collection.add_suite(suite)
        result = emitter.generate(collection, entities=[{"id": "User", "fields": []}])
        assert isinstance(result, list)

    def test_get_template_name_unit_entity(self):
        """Kiểm tra _get_template_name cho unit entity."""
        emitter = FastAPITestEmitter(stack_dir="stacks/fastapi/core")
        suite = TestSuite(name="u", framework=TestFramework.PYTEST, test_type=TestType.UNIT)
        case = TestCase(id="t1", type=TestType.UNIT, target="User", scenario="s", assertions=[TestAssertion(check=AssertionCheck.EQUAL, expected=1)])
        name = emitter._get_template_name(suite, case)
        assert name == "unit_test_entity.py.jinja2"

    def test_get_template_name_unit_command(self):
        """Kiểm tra _get_template_name cho unit command."""
        emitter = FastAPITestEmitter(stack_dir="stacks/fastapi/core")
        suite = TestSuite(name="u", framework=TestFramework.PYTEST, test_type=TestType.UNIT)
        case = TestCase(id="t1", type=TestType.UNIT, target="CreateUser", scenario="s", assertions=[TestAssertion(check=AssertionCheck.EQUAL, expected=1)], tags=["command"])
        name = emitter._get_template_name(suite, case)
        assert name == "unit_test_command.py.jinja2"

    def test_get_template_name_unit_query(self):
        """Kiểm tra _get_template_name cho unit query."""
        emitter = FastAPITestEmitter(stack_dir="stacks/fastapi/core")
        suite = TestSuite(name="u", framework=TestFramework.PYTEST, test_type=TestType.UNIT)
        case = TestCase(id="t1", type=TestType.UNIT, target="ListUsers", scenario="s", assertions=[TestAssertion(check=AssertionCheck.EQUAL, expected=1)], tags=["query"])
        name = emitter._get_template_name(suite, case)
        assert name == "unit_test_query.py.jinja2"

    def test_get_template_name_integration(self):
        """Kiểm tra _get_template_name cho integration."""
        emitter = FastAPITestEmitter(stack_dir="stacks/fastapi/core")
        suite = TestSuite(name="i", framework=TestFramework.PYTEST, test_type=TestType.INTEGRATION)
        case = TestCase(id="t1", type=TestType.INTEGRATION, target="User", scenario="s", assertions=[TestAssertion(check=AssertionCheck.EQUAL, expected=1)])
        name = emitter._get_template_name(suite, case)
        assert name == "integration_test_api.py.jinja2"

    def test_get_template_name_e2e(self):
        """Kiểm tra _get_template_name cho e2e."""
        emitter = FastAPITestEmitter(stack_dir="stacks/fastapi/core")
        suite = TestSuite(name="e", framework=TestFramework.PYTEST, test_type=TestType.E2E)
        from midicoder.packs.cp23_testing_framework.models import TestStep
        case = TestCase(id="t1", type=TestType.E2E, target="User", scenario="flow", steps=[TestStep(action="navigate")], assertions=[TestAssertion(check=AssertionCheck.EQUAL, expected=1)])
        name = emitter._get_template_name(suite, case)
        assert name == "e2e_test_flow.py.jinja2"

    def test_get_file_path_unit(self):
        """Kiểm tra _get_file_path cho unit."""
        emitter = FastAPITestEmitter(stack_dir="stacks/fastapi/core")
        suite = TestSuite(name="u", framework=TestFramework.PYTEST, test_type=TestType.UNIT)
        case = TestCase(id="t1", type=TestType.UNIT, target="User", scenario="s", assertions=[TestAssertion(check=AssertionCheck.EQUAL, expected=1)])
        path = emitter._get_file_path(suite, case)
        assert path == "tests/unit/test_user.py"

    def test_get_file_path_integration(self):
        """Kiểm tra _get_file_path cho integration."""
        emitter = FastAPITestEmitter(stack_dir="stacks/fastapi/core")
        suite = TestSuite(name="i", framework=TestFramework.PYTEST, test_type=TestType.INTEGRATION)
        case = TestCase(id="t1", type=TestType.INTEGRATION, target="User", scenario="s", assertions=[TestAssertion(check=AssertionCheck.EQUAL, expected=1)])
        path = emitter._get_file_path(suite, case)
        assert path == "tests/integration/test_user_api.py"

    def test_get_file_path_e2e(self):
        """Kiểm tra _get_file_path cho e2e."""
        emitter = FastAPITestEmitter(stack_dir="stacks/fastapi/core")
        suite = TestSuite(name="e", framework=TestFramework.PYTEST, test_type=TestType.E2E)
        from midicoder.packs.cp23_testing_framework.models import TestStep
        case = TestCase(id="t1", type=TestType.E2E, target="User", scenario="crud flow", steps=[TestStep(action="navigate")], assertions=[TestAssertion(check=AssertionCheck.EQUAL, expected=1)])
        path = emitter._get_file_path(suite, case)
        assert path == "tests/e2e/test_crud_flow.py"

    def test_find_entity(self):
        """Kiểm tra _find_entity."""
        emitter = FastAPITestEmitter(stack_dir="stacks/fastapi/core")
        entities = [{"id": "User", "name": "User entity"}]
        result = emitter._find_entity("User", entities)
        assert result["id"] == "User"
        assert emitter._find_entity("Order", entities) is None

    def test_find_item(self):
        """Kiểm tra _find_item."""
        emitter = FastAPITestEmitter(stack_dir="stacks/fastapi/core")
        items = [{"id": "CreateUser"}]
        assert emitter._find_item("CreateUser", items) == items[0]
        assert emitter._find_item("DeleteUser", items) is None


class TestNestJSTestEmitter:
    """Test NestJSTestEmitter."""

    def test_create_emitter(self):
        """Kiểm tra tạo emitter."""
        emitter = NestJSTestEmitter(stack_dir="stacks/nestjs/core")
        assert emitter is not None

    def test_generate_with_empty_collection(self):
        """Kiểm tra generate với collection rỗng."""
        emitter = NestJSTestEmitter(stack_dir="stacks/nestjs/core")
        collection = TestCollection()
        result = emitter.generate(collection)
        assert isinstance(result, list)

    def test_get_template_name_entity(self):
        """Kiểm tra template name cho entity."""
        emitter = NestJSTestEmitter(stack_dir="stacks/nestjs/core")
        suite = TestSuite(name="u", framework=TestFramework.JEST, test_type=TestType.UNIT)
        case = TestCase(id="t1", type=TestType.UNIT, target="User", scenario="s", assertions=[TestAssertion(check=AssertionCheck.EQUAL, expected=1)])
        assert emitter._get_template_name(suite, case) == "entity.spec.ts.jinja2"

    def test_get_template_name_command(self):
        """Kiểm tra template name cho command."""
        emitter = NestJSTestEmitter(stack_dir="stacks/nestjs/core")
        suite = TestSuite(name="u", framework=TestFramework.JEST, test_type=TestType.UNIT)
        case = TestCase(id="t1", type=TestType.UNIT, target="Cmd", scenario="s", assertions=[TestAssertion(check=AssertionCheck.EQUAL, expected=1)], tags=["command"])
        assert emitter._get_template_name(suite, case) == "command_handler.spec.ts.jinja2"

    def test_get_template_name_query(self):
        """Kiểm tra template name cho query."""
        emitter = NestJSTestEmitter(stack_dir="stacks/nestjs/core")
        suite = TestSuite(name="u", framework=TestFramework.JEST, test_type=TestType.UNIT)
        case = TestCase(id="t1", type=TestType.UNIT, target="Qry", scenario="s", assertions=[TestAssertion(check=AssertionCheck.EQUAL, expected=1)], tags=["query"])
        assert emitter._get_template_name(suite, case) == "query_handler.spec.ts.jinja2"

    def test_get_template_name_integration(self):
        """Kiểm tra template name cho integration."""
        emitter = NestJSTestEmitter(stack_dir="stacks/nestjs/core")
        suite = TestSuite(name="i", framework=TestFramework.JEST, test_type=TestType.INTEGRATION)
        case = TestCase(id="t1", type=TestType.INTEGRATION, target="User", scenario="s", assertions=[TestAssertion(check=AssertionCheck.EQUAL, expected=1)])
        assert emitter._get_template_name(suite, case) == "integration.spec.ts.jinja2"

    def test_get_template_name_e2e(self):
        """Kiểm tra template name cho e2e."""
        emitter = NestJSTestEmitter(stack_dir="stacks/nestjs/core")
        suite = TestSuite(name="e", framework=TestFramework.JEST, test_type=TestType.E2E)
        from midicoder.packs.cp23_testing_framework.models import TestStep
        case = TestCase(id="t1", type=TestType.E2E, target="User", scenario="f", steps=[TestStep(action="x")], assertions=[TestAssertion(check=AssertionCheck.EQUAL, expected=1)])
        assert emitter._get_template_name(suite, case) == "e2e_flows.spec.ts.jinja2"

    def test_get_file_paths(self):
        """Kiểm tra file paths cho NestJS."""
        emitter = NestJSTestEmitter(stack_dir="stacks/nestjs/core")
        # Unit entity
        suite = TestSuite(name="u", framework=TestFramework.JEST, test_type=TestType.UNIT)
        case = TestCase(id="t1", type=TestType.UNIT, target="User", scenario="s", assertions=[TestAssertion(check=AssertionCheck.EQUAL, expected=1)])
        assert emitter._get_file_path(suite, case) == "src/entities/user.entity.spec.ts"

        # Unit command
        case_cmd = TestCase(id="t2", type=TestType.UNIT, target="Cmd", scenario="s", assertions=[TestAssertion(check=AssertionCheck.EQUAL, expected=1)], tags=["command"])
        assert emitter._get_file_path(suite, case_cmd) == "src/commands/cmd.handler.spec.ts"

        # Integration
        suite_i = TestSuite(name="i", framework=TestFramework.JEST, test_type=TestType.INTEGRATION)
        assert emitter._get_file_path(suite_i, case) == "src/integration/user.integration.spec.ts"

    def test_find_entity_and_item(self):
        """Kiểm tra _find_entity và _find_item."""
        emitter = NestJSTestEmitter(stack_dir="stacks/nestjs/core")
        entities = [{"id": "Order"}]
        assert emitter._find_entity("Order", entities) == entities[0]
        assert emitter._find_entity("User", entities) is None
        commands = [{"id": "CreateOrder"}]
        assert emitter._find_item("CreateOrder", commands) == commands[0]


class TestAngularTestEmitter:
    """Test AngularTestEmitter."""

    def test_create_emitter(self):
        """Kiểm tra tạo emitter."""
        emitter = AngularTestEmitter(stack_dir="stacks/angular/core")
        assert emitter is not None

    def test_generate_with_empty_collection(self):
        """Kiểm tra generate với collection rỗng."""
        emitter = AngularTestEmitter(stack_dir="stacks/angular/core")
        collection = TestCollection()
        result = emitter.generate(collection)
        assert isinstance(result, list)

    def test_get_template_name_component(self):
        """Kiểm tra template name cho component."""
        emitter = AngularTestEmitter(stack_dir="stacks/angular/core")
        suite = TestSuite(name="u", framework=TestFramework.KARMA, test_type=TestType.UNIT)
        case = TestCase(id="t1", type=TestType.UNIT, target="User", scenario="s", assertions=[TestAssertion(check=AssertionCheck.EQUAL, expected=1)])
        assert emitter._get_template_name(suite, case) == "component.spec.ts.jinja2"

    def test_get_template_name_service(self):
        """Kiểm tra template name cho service."""
        emitter = AngularTestEmitter(stack_dir="stacks/angular/core")
        suite = TestSuite(name="u", framework=TestFramework.KARMA, test_type=TestType.UNIT)
        case = TestCase(id="t1", type=TestType.UNIT, target="User", scenario="s", assertions=[TestAssertion(check=AssertionCheck.EQUAL, expected=1)], tags=["service"])
        assert emitter._get_template_name(suite, case) == "service.spec.ts.jinja2"

    def test_get_template_name_e2e(self):
        """Kiểm tra template name cho e2e."""
        emitter = AngularTestEmitter(stack_dir="stacks/angular/core")
        suite = TestSuite(name="e", framework=TestFramework.KARMA, test_type=TestType.E2E)
        from midicoder.packs.cp23_testing_framework.models import TestStep
        case = TestCase(id="t1", type=TestType.E2E, target="User", scenario="f", steps=[TestStep(action="x")], assertions=[TestAssertion(check=AssertionCheck.EQUAL, expected=1)])
        assert emitter._get_template_name(suite, case) == "e2e_app.spec.ts.jinja2"

    def test_get_file_paths(self):
        """Kiểm tra file paths."""
        emitter = AngularTestEmitter(stack_dir="stacks/angular/core")
        suite = TestSuite(name="u", framework=TestFramework.KARMA, test_type=TestType.UNIT)
        case = TestCase(id="t1", type=TestType.UNIT, target="User", scenario="s", assertions=[TestAssertion(check=AssertionCheck.EQUAL, expected=1)])
        assert emitter._get_file_path(suite, case) == "src/app/components/user-component.spec.ts"

        case_svc = TestCase(id="t2", type=TestType.UNIT, target="User", scenario="s", assertions=[TestAssertion(check=AssertionCheck.EQUAL, expected=1)], tags=["service"])
        assert emitter._get_file_path(suite, case_svc) == "src/app/services/user-service.spec.ts"

        suite_e = TestSuite(name="e", framework=TestFramework.KARMA, test_type=TestType.E2E)
        assert emitter._get_file_path(suite_e, case) == "e2e/src/user.e2e-spec.ts"


class TestReactTestEmitter:
    """Test ReactTestEmitter."""

    def test_create_emitter(self):
        """Kiểm tra tạo emitter."""
        emitter = ReactTestEmitter(stack_dir="stacks/react/core")
        assert emitter is not None

    def test_generate_with_empty_collection(self):
        """Kiểm tra generate với collection rỗng."""
        emitter = ReactTestEmitter(stack_dir="stacks/react/core")
        collection = TestCollection()
        result = emitter.generate(collection)
        assert isinstance(result, list)

    def test_get_template_name_component(self):
        """Kiểm tra template name cho component."""
        emitter = ReactTestEmitter(stack_dir="stacks/react/core")
        suite = TestSuite(name="u", framework=TestFramework.JEST, test_type=TestType.UNIT)
        case = TestCase(id="t1", type=TestType.UNIT, target="User", scenario="s", assertions=[TestAssertion(check=AssertionCheck.EQUAL, expected=1)])
        assert emitter._get_template_name(suite, case) == "component.test.tsx.jinja2"

    def test_get_template_name_hook(self):
        """Kiểm tra template name cho hook."""
        emitter = ReactTestEmitter(stack_dir="stacks/react/core")
        suite = TestSuite(name="u", framework=TestFramework.JEST, test_type=TestType.UNIT)
        case = TestCase(id="t1", type=TestType.UNIT, target="User", scenario="s", assertions=[TestAssertion(check=AssertionCheck.EQUAL, expected=1)], tags=["hook"])
        assert emitter._get_template_name(suite, case) == "hook.test.tsx.jinja2"

    def test_get_template_name_e2e(self):
        """Kiểm tra template name cho e2e."""
        emitter = ReactTestEmitter(stack_dir="stacks/react/core")
        suite = TestSuite(name="e", framework=TestFramework.JEST, test_type=TestType.E2E)
        from midicoder.packs.cp23_testing_framework.models import TestStep
        case = TestCase(id="t1", type=TestType.E2E, target="User", scenario="f", steps=[TestStep(action="x")], assertions=[TestAssertion(check=AssertionCheck.EQUAL, expected=1)])
        assert emitter._get_template_name(suite, case) == "e2e_app.test.tsx.jinja2"

    def test_get_file_paths(self):
        """Kiểm tra file paths."""
        emitter = ReactTestEmitter(stack_dir="stacks/react/core")
        suite = TestSuite(name="u", framework=TestFramework.JEST, test_type=TestType.UNIT)
        case = TestCase(id="t1", type=TestType.UNIT, target="User", scenario="s", assertions=[TestAssertion(check=AssertionCheck.EQUAL, expected=1)])
        assert emitter._get_file_path(suite, case) == "src/__tests__/user.test.tsx"

        case_hook = TestCase(id="t2", type=TestType.UNIT, target="User", scenario="s", assertions=[TestAssertion(check=AssertionCheck.EQUAL, expected=1)], tags=["hook"])
        assert emitter._get_file_path(suite, case_hook) == "src/__tests__/hooks/useUser.test.tsx"

        suite_e = TestSuite(name="e", framework=TestFramework.JEST, test_type=TestType.E2E)
        assert emitter._get_file_path(suite_e, case) == "src/e2e/user.e2e.test.tsx"

    def test_find_entity_and_item(self):
        """Kiểm tra _find_entity và _find_item."""
        emitter = ReactTestEmitter(stack_dir="stacks/react/core")
        entities = [{"id": "Product"}]
        assert emitter._find_entity("Product", entities) == entities[0]
        assert emitter._find_entity("User", entities) is None


# ===========================================================================
# Tests cho infrastructure config generation
# ===========================================================================

class TestInfrastructureConfigGeneration:
    """Test _generate_*_config methods cho tất cả emitters."""

    def test_fastapi_generate_conftest(self):
        """Kiểm tra FastAPI _generate_conftest."""
        emitter = FastAPITestEmitter(stack_dir="stacks/fastapi/core")
        collection = TestCollection()
        result = emitter._generate_conftest(collection, entities=[{"id": "User"}])
        assert isinstance(result, list)

    def test_fastapi_generate_pytest_ini(self):
        """Kiểm tra FastAPI _generate_pytest_ini."""
        emitter = FastAPITestEmitter(stack_dir="stacks/fastapi/core")
        collection = TestCollection()
        result = emitter._generate_pytest_ini(collection)
        assert isinstance(result, list)

    def test_fastapi_generate_coverage_config(self):
        """Kiểm tra FastAPI _generate_coverage_config."""
        emitter = FastAPITestEmitter(stack_dir="stacks/fastapi/core")
        collection = TestCollection()
        result = emitter._generate_coverage_config(collection)
        assert isinstance(result, list)

    def test_nestjs_generate_jest_config(self):
        """Kiểm tra NestJS _generate_jest_config."""
        emitter = NestJSTestEmitter(stack_dir="stacks/nestjs/core")
        collection = TestCollection()
        result = emitter._generate_jest_config(collection)
        assert isinstance(result, list)

    def test_angular_generate_karma_config(self):
        """Kiểm tra Angular _generate_karma_config."""
        emitter = AngularTestEmitter(stack_dir="stacks/angular/core")
        collection = TestCollection()
        result = emitter._generate_karma_config(collection)
        assert isinstance(result, list)

    def test_react_generate_jest_config(self):
        """Kiểm tra React _generate_jest_config."""
        emitter = ReactTestEmitter(stack_dir="stacks/react/core")
        collection = TestCollection()
        result = emitter._generate_jest_config(collection)
        assert isinstance(result, list)

    def test_all_emitters_generate_full_flow(self):
        """Kiểm tra generate() end-to-end với collection có suites."""
        collection = TestCollection()
        suite = TestSuite(name="unit", framework=TestFramework.PYTEST, test_type=TestType.UNIT)
        suite.add_case(TestCase(
            id="t1", type=TestType.UNIT, target="User", scenario="create",
            assertions=[TestAssertion(check=AssertionCheck.EQUAL, expected=1)],
        ))
        collection.add_suite(suite)

        emitters = [
            FastAPITestEmitter(stack_dir="stacks/fastapi/core"),
            NestJSTestEmitter(stack_dir="stacks/nestjs/core"),
            AngularTestEmitter(stack_dir="stacks/angular/core"),
            ReactTestEmitter(stack_dir="stacks/react/core"),
        ]
        for emitter in emitters:
            result = emitter.generate(collection, entities=[{"id": "User", "fields": []}])
            assert isinstance(result, list)
