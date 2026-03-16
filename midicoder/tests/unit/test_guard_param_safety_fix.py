from __future__ import annotations

from pathlib import Path

from midicoder.contract.file_processor import _apply_auth_guard_param_safety_fixes


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.lstrip(), encoding="utf-8")


def test_guard_safety_fix_converts_role_list_to_roles_in_workflow(tmp_path: Path) -> None:
    contracts_root = tmp_path / "contracts"
    wf = contracts_root / "workflows" / "workflows.yaml"
    _write(
        wf,
        """
workflows:
  - id: PayrollWorkflow
    transitions:
      - from_state: draft
        to_state: approved
        on_command: SendPayslipEmail
        guards:
          - id: auth.role
            params:
              role:
                - HR
                - Admin
""",
    )

    notes = _apply_auth_guard_param_safety_fixes(
        contracts_root,
        "contracts/workflows/workflows.yaml",
    )
    assert notes
    text = wf.read_text(encoding="utf-8")
    assert "roles:" in text
    assert "role:" not in text
