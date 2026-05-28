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

from midicoder.packs.cp_full_rbac.models import (
    Permission,
    Role,
    PolicyEffect,
    PolicyCondition,
    PolicyEvaluationResult,
    Policy,
    PolicyContext,
    PolicyDecision,
    PolicyRule,
    RBACConfig,
)
from midicoder.packs.cp_full_rbac.parser import RBACParser
from midicoder.packs.cp_full_rbac.rbac_engine import RBACEngine
from midicoder.packs.cp_full_rbac.policy_engine import PolicyEngine
from midicoder.packs.cp_full_rbac.fastapi import FastAPIRBACEmitter
from midicoder.packs.cp_full_rbac.nestjs import NestJSRBACEmitter
from midicoder.packs.cp_full_rbac.angular import AngularRBACEmitter
from midicoder.packs.cp_full_rbac.react import ReactRBACEmitter

__all__ = [
    # Models
    "Permission",
    "Role",
    "PolicyEffect",
    "PolicyCondition",
    "PolicyEvaluationResult",
    "Policy",
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
