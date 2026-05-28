# coding: utf-8
"""
CP23: Testing Framework Generator.

Cung cấp:
- models: TestType, TestFramework, AssertionCheck, TestAssertion, TestStep,
          TestCase, TestPolicy, TestSuite, TestCollection
- parser: TestParser
- recipes: auto_generate_tests_from_mir, generate_*_tests
- fastapi: FastAPITestEmitter (pytest)
- nestjs: NestJSTestEmitter (Jest)
- angular: AngularTestEmitter (Karma/Jest)
- react: ReactTestEmitter (Jest)

Author: Midicoder Team
Version: 1.0.0
"""

from midicoder.packs.cp_full_testing_framework.models import (
    AssertionCheck,
    TestCase,
    TestCollection,
    TestFramework,
    TestPolicy,
    TestStep,
    TestSuite,
    TestType,
    TestAssertion,
)
from midicoder.packs.cp_full_testing_framework.parser import TestParser
from midicoder.packs.cp_full_testing_framework.fastapi import FastAPITestEmitter
from midicoder.packs.cp_full_testing_framework.nestjs import NestJSTestEmitter
from midicoder.packs.cp_full_testing_framework.angular import AngularTestEmitter
from midicoder.packs.cp_full_testing_framework.react import ReactTestEmitter
from midicoder.packs.cp_full_testing_framework.recipes import (
    auto_generate_tests_from_mir,
    generate_api_integration_tests,
    generate_command_unit_tests,
    generate_e2e_flow_tests,
    generate_entity_unit_tests,
    generate_query_unit_tests,
)

__all__ = [
    "AngularTestEmitter",
    "AssertionCheck",
    "auto_generate_tests_from_mir",
    "FastAPITestEmitter",
    "generate_api_integration_tests",
    "generate_command_unit_tests",
    "generate_e2e_flow_tests",
    "generate_entity_unit_tests",
    "generate_query_unit_tests",
    "NestJSTestEmitter",
    "ReactTestEmitter",
    "TestCase",
    "TestCollection",
    "TestFramework",
    "TestParser",
    "TestPolicy",
    "TestStep",
    "TestSuite",
    "TestType",
    "TestAssertion",
]
