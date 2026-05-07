"""
CP04: RBAC & Policy Engine — Core Pack.

Pack này cung cấp Role-Based Access Control + Attribute-Based Policy Engine:
- Role definitions với hierarchical inheritance
- Permission bindings (resource:action)
- ABAC policy evaluation với expression DSL
- Emitters cho 4 stacks: FastAPI, NestJS, Angular, React

Capabilities provided: authorize_role, check_policy

Author: Midicoder Team
Version: 1.0.0
"""

from midicoder.emitters.core.rbac.models import (
    PolicyContext,
    PolicyDecision,
    PolicyRule,
    RBACConfig,
)
from midicoder.emitters.core.rbac.parser import RBACParser
from midicoder.emitters.core.rbac.rbac_engine import RBACEngine
from midicoder.emitters.core.rbac.policy_engine import PolicyEngine
from midicoder.emitters.core.rbac.fastapi import FastAPIRBACEmitter
from midicoder.emitters.core.rbac.nestjs import NestJSRBACEmitter
from midicoder.emitters.core.rbac.angular import AngularRBACEmitter
from midicoder.emitters.core.rbac.react import ReactRBACEmitter

__all__ = [
    # Models
    "PolicyContext",
    "PolicyDecision",
    "PolicyRule",
    "RBACConfig",
    # Parser
    "RBACParser",
    # Engines
    "RBACEngine",
    "PolicyEngine",
    # Emitters
    "FastAPIRBACEmitter",
    "NestJSRBACEmitter",
    "AngularRBACEmitter",
    "ReactRBACEmitter",
]
