from __future__ import annotations

from pathlib import Path

from midicoder.contract.contract_validator import _lint_guard_ref


def test_lint_guard_ref_accepts_auth_role_roles_param() -> None:
    issues = _lint_guard_ref(
        guard_id="auth.role",
        params={"roles": ["HR", "Admin"]},
        path=Path("contracts/workflows/workflows.yaml"),
        location_prefix="workflows[0].transitions[0].guards[0]",
    )
    assert not issues


def test_lint_guard_ref_accepts_auth_permission_permissions_param() -> None:
    issues = _lint_guard_ref(
        guard_id="auth.permission",
        params={"permissions": ["manage_payroll"]},
        path=Path("contracts/app/commands.yaml"),
        location_prefix="commands[0].guards[0]",
    )
    assert not issues
