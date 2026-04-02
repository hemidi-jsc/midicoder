from __future__ import annotations

from typing import Any, ClassVar, Optional

from pydantic import BaseModel, Field

from .model_meta import ModelMeta

TEST_KIND_CATALOG = {
    "unit",
    "integration",
    "e2e",
}

TEST_FRAMEWORK_CATALOG = {
    "pytest",
    "jest",
    "selenium",
    "playwright",
    "cypress",
}

CONTRACT_TEST_STEP_TYPE_CATALOG = {
    "command",
    "query",
    "event",
}


class ContractTestStep(BaseModel):
    type: str
    ref: str
    input: dict[str, Any] = Field(default_factory=dict)
    expect: dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "forbid"}


class ContractTestCase(BaseModel):
    id: str
    kind: str
    framework: Optional[str] = None
    description: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    steps: list[ContractTestStep] = Field(default_factory=list)
    scenario: Optional[str] = None

    model_config = {"extra": "forbid"}


class TestingFile(BaseModel):
    tests: list[ContractTestCase]

    model_config = {"extra": "forbid"}

    model_meta: ClassVar[ModelMeta] = ModelMeta(
        kind="testing.contract",
        usage_en=(
            "Contract-level tests used to define happy-path, validation and "
            "integration failure scenarios for generated backend services."
        ),
    )
