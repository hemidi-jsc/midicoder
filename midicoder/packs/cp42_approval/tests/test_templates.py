# coding: utf-8
"""
Tests cho CP42 — Approval Workflow Engine: kiểm tra pack.yml,
file_contributions, template files cho 4 stacks (FastAPI, NestJS, Angular, React),
CHANGELOG.md, và Registry integration.
"""

from __future__ import annotations

from pathlib import Path

import jinja2
import pytest

# Project root = 6 bậc parent lên từ tests/ → d:\hemidi-labs\midicoder-ce
MIDICODER_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent

FASTAPI_DIR = MIDICODER_ROOT / "midicoder" / "stacks" / "fastapi" / "core" / "cp42_approval"
NESTJS_DIR = MIDICODER_ROOT / "midicoder" / "stacks" / "nestjs" / "core" / "cp42_approval"
ANGULAR_DIR = MIDICODER_ROOT / "midicoder" / "stacks" / "angular" / "core" / "cp42_approval"
REACT_DIR = MIDICODER_ROOT / "midicoder" / "stacks" / "react" / "core" / "cp42_approval"
PACK_DIR = MIDICODER_ROOT / "midicoder" / "emitters" / "core" / "cp42_approval"


# ============================================================================
# TestPackYaml — 5 tests cho cấu hình pack.yml
# ============================================================================


class TestPackYaml:
    """Nhóm kiểm tra pack.yml của CP42 Approval Workflow Engine."""

    def test_pack_yml_exists(self):
        """Kiểm tra tập tin pack.yml tồn tại tại đường dẫn đúng."""
        pack_yml = PACK_DIR / "pack.yml"
        assert pack_yml.exists(), f"pack.yml không tồn tại tại {pack_yml}"

    def test_pack_yml_has_cp42_id(self):
        """Kiểm tra pack.yml chứa định danh CP42 và cp42_approval."""
        pack_yml = PACK_DIR / "pack.yml"
        content = pack_yml.read_text(encoding="utf-8")
        assert "CP42" in content
        assert "cp42_approval" in content

    def test_pack_yml_has_capabilities(self):
        """Kiểm tra pack.yml khai báo đầy đủ khả năng phê duyệt."""
        import yaml

        pack_yml = PACK_DIR / "pack.yml"
        with open(pack_yml, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert "capabilities" in data["pack"]
        danh_sach_kha_nang = [c["id"] for c in data["pack"]["capabilities"]]
        assert "approval_chain" in danh_sach_kha_nang
        assert "approval_matrix" in danh_sach_kha_nang
        assert "delegation" in danh_sach_kha_nang
        assert "escalation" in danh_sach_kha_nang

    def test_pack_yml_has_4_stacks(self):
        """Kiểm tra pack.yml có file_contributions cho cả 4 stacks."""
        import yaml

        pack_yml = PACK_DIR / "pack.yml"
        with open(pack_yml, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        stacks_tim_thay = set()
        for contrib in data["pack"]["file_contributions"]["infrastructure"]:
            for s in contrib.get("stacks", []):
                stacks_tim_thay.add(s)
        assert "fastapi" in stacks_tim_thay
        assert "nestjs" in stacks_tim_thay
        assert "angular" in stacks_tim_thay
        assert "react" in stacks_tim_thay

    def test_pack_yml_has_file_contributions(self):
        """Kiểm tra pack.yml có section file_contributions hợp lệ."""
        import yaml

        pack_yml = PACK_DIR / "pack.yml"
        with open(pack_yml, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert "file_contributions" in data["pack"]
        assert "infrastructure" in data["pack"]["file_contributions"]


# ============================================================================
# TestFastAPITemplates — 4 tests cho 7 template files
# ============================================================================


class TestFastAPITemplates:
    """Nhóm kiểm tra FastAPI templates của CP42 Approval Workflow Engine."""

    EXPECTED = [
        "approval_models.py.jinja2",
        "approval_schemas.py.jinja2",
        "approval_service.py.jinja2",
        "approval_router.py.jinja2",
        "approval_event_handler.py.jinja2",
        "approval_escalation_worker.py.jinja2",
        "approval_delegation_service.py.jinja2",
    ]

    def test_all_templates_exist(self):
        """Kiểm tra tất cả template files FastAPI tồn tại trên đĩa."""
        for name in self.EXPECTED:
            path = FASTAPI_DIR / name
            assert path.exists(), f"Template không tồn tại: {path}"

    def test_templates_have_content(self):
        """Kiểm tra mỗi template FastAPI có nội dung, không rỗng."""
        for name in self.EXPECTED:
            path = FASTAPI_DIR / name
            content = path.read_text(encoding="utf-8")
            assert len(content) > 0, f"Template rỗng: {name}"

    def test_no_midicoder_import(self):
        """Kiểm tra templates FastAPI không import từ midicoder."""
        for name in self.EXPECTED:
            path = FASTAPI_DIR / name
            content = path.read_text(encoding="utf-8")
            assert "from midicoder" not in content, (
                f"Template {name} không được import từ midicoder"
            )

    def test_no_post_init(self):
        """Kiểm tra templates FastAPI không chứa __post_init__."""
        for name in self.EXPECTED:
            path = FASTAPI_DIR / name
            content = path.read_text(encoding="utf-8")
            assert "__post_init__" not in content, (
                f"Template {name} không được có __post_init__"
            )


# ============================================================================
# TestNestJSTemplates — 4 tests cho 7 template files
# ============================================================================


class TestNestJSTemplates:
    """Nhóm kiểm tra NestJS templates của CP42 Approval Workflow Engine."""

    EXPECTED = [
        "approval.entity.ts.jinja2",
        "approval.dto.ts.jinja2",
        "approval.service.ts.jinja2",
        "approval.controller.ts.jinja2",
        "approval.module.ts.jinja2",
        "approval.scheduler.ts.jinja2",
        "approval.gateway.ts.jinja2",
    ]

    def test_all_templates_exist(self):
        """Kiểm tra tất cả template files NestJS tồn tại trên đĩa."""
        for name in self.EXPECTED:
            path = NESTJS_DIR / name
            assert path.exists(), f"Template không tồn tại: {path}"

    def test_templates_have_content(self):
        """Kiểm tra mỗi template NestJS có nội dung, không rỗng."""
        for name in self.EXPECTED:
            path = NESTJS_DIR / name
            content = path.read_text(encoding="utf-8")
            assert len(content) > 0, f"Template rỗng: {name}"

    def test_no_midicoder_import(self):
        """Kiểm tra templates NestJS không import từ midicoder."""
        for name in self.EXPECTED:
            path = NESTJS_DIR / name
            content = path.read_text(encoding="utf-8")
            assert "from midicoder" not in content

    def test_no_post_init(self):
        """Kiểm tra templates NestJS không chứa __post_init__."""
        for name in self.EXPECTED:
            path = NESTJS_DIR / name
            content = path.read_text(encoding="utf-8")
            assert "__post_init__" not in content


# ============================================================================
# TestAngularTemplates — 4 tests cho 6 template files
# ============================================================================


class TestAngularTemplates:
    """Nhóm kiểm tra Angular templates của CP42 Approval Workflow Engine."""

    EXPECTED = [
        "approval-dashboard.component.ts.jinja2",
        "approval-details.component.ts.jinja2",
        "approval-history.component.ts.jinja2",
        "approval.service.ts.jinja2",
        "approval.store.ts.jinja2",
        "approval-types.ts.jinja2",
    ]

    def test_all_templates_exist(self):
        """Kiểm tra tất cả template files Angular tồn tại trên đĩa."""
        for name in self.EXPECTED:
            path = ANGULAR_DIR / name
            assert path.exists(), f"Template không tồn tại: {path}"

    def test_templates_have_content(self):
        """Kiểm tra mỗi template Angular có nội dung, không rỗng."""
        for name in self.EXPECTED:
            path = ANGULAR_DIR / name
            content = path.read_text(encoding="utf-8")
            assert len(content) > 0, f"Template rỗng: {name}"

    def test_no_midicoder_import(self):
        """Kiểm tra templates Angular không import từ midicoder."""
        for name in self.EXPECTED:
            path = ANGULAR_DIR / name
            content = path.read_text(encoding="utf-8")
            assert "from midicoder" not in content

    def test_no_post_init(self):
        """Kiểm tra templates Angular không chứa __post_init__."""
        for name in self.EXPECTED:
            path = ANGULAR_DIR / name
            content = path.read_text(encoding="utf-8")
            assert "__post_init__" not in content


# ============================================================================
# TestReactTemplates — 4 tests cho 6 template files
# ============================================================================


class TestReactTemplates:
    """Nhóm kiểm tra React templates của CP42 Approval Workflow Engine."""

    EXPECTED = [
        "ApprovalDashboard.tsx.jinja2",
        "ApprovalDetails.tsx.jinja2",
        "ApprovalHistory.tsx.jinja2",
        "NotificationBadge.tsx.jinja2",
        "DelegationSettings.tsx.jinja2",
        "useApprovals.ts.jinja2",
    ]

    def test_all_templates_exist(self):
        """Kiểm tra tất cả template files React tồn tại trên đĩa."""
        for name in self.EXPECTED:
            path = REACT_DIR / name
            assert path.exists(), f"Template không tồn tại: {path}"

    def test_templates_have_content(self):
        """Kiểm tra mỗi template React có nội dung, không rỗng."""
        for name in self.EXPECTED:
            path = REACT_DIR / name
            content = path.read_text(encoding="utf-8")
            assert len(content) > 0, f"Template rỗng: {name}"

    def test_no_midicoder_import(self):
        """Kiểm tra templates React không import từ midicoder."""
        for name in self.EXPECTED:
            path = REACT_DIR / name
            content = path.read_text(encoding="utf-8")
            assert "from midicoder" not in content

    def test_no_post_init(self):
        """Kiểm tra templates React không chứa __post_init__."""
        for name in self.EXPECTED:
            path = REACT_DIR / name
            content = path.read_text(encoding="utf-8")
            assert "__post_init__" not in content


# ============================================================================
# TestChangelog — 2 tests cho CHANGELOG.md
# ============================================================================


class TestChangelog:
    """Nhóm kiểm tra CHANGELOG.md của CP42 Approval Workflow Engine."""

    def test_changelog_exists(self):
        """Kiểm tra CHANGELOG.md tồn tại trong thư mục pack."""
        changelog = PACK_DIR / "CHANGELOG.md"
        assert changelog.exists()

    def test_changelog_has_version(self):
        """Kiểm tra CHANGELOG.md chứa thông tin bản phát hành 1.0.0."""
        changelog = PACK_DIR / "CHANGELOG.md"
        content = changelog.read_text(encoding="utf-8")
        assert "1.0.0" in content


# ============================================================================
# TestRegistry — 1 test cho đăng ký trong CP_ID_TO_INTERNAL
# ============================================================================


class TestRegistry:
    """Nhóm kiểm tra CP42 được đăng ký trong registry."""

    def test_cp42_in_registry(self):
        """Kiểm tra CP42 ánh xạ đúng với cp42_approval trong registry."""
        from midicoder.contracts.registry import CP_ID_TO_INTERNAL

        assert "CP42" in CP_ID_TO_INTERNAL
        assert CP_ID_TO_INTERNAL["CP42"] == "cp42_approval"


# ============================================================================
# Helper — render template với context cơ bản
# ============================================================================

STACK_DIRS = {
    "fastapi": FASTAPI_DIR,
    "nestjs": NESTJS_DIR,
    "angular": ANGULAR_DIR,
    "react": REACT_DIR,
}

ALL_TEMPLATES = {
    "fastapi": [
        "approval_models.py.jinja2",
        "approval_schemas.py.jinja2",
        "approval_service.py.jinja2",
        "approval_router.py.jinja2",
        "approval_event_handler.py.jinja2",
        "approval_escalation_worker.py.jinja2",
        "approval_delegation_service.py.jinja2",
    ],
    "nestjs": [
        "approval.entity.ts.jinja2",
        "approval.dto.ts.jinja2",
        "approval.service.ts.jinja2",
        "approval.controller.ts.jinja2",
        "approval.module.ts.jinja2",
        "approval.scheduler.ts.jinja2",
        "approval.gateway.ts.jinja2",
    ],
    "angular": [
        "approval-dashboard.component.ts.jinja2",
        "approval-details.component.ts.jinja2",
        "approval-history.component.ts.jinja2",
        "approval.service.ts.jinja2",
        "approval.store.ts.jinja2",
        "approval-types.ts.jinja2",
    ],
    "react": [
        "ApprovalDashboard.tsx.jinja2",
        "ApprovalDetails.tsx.jinja2",
        "ApprovalHistory.tsx.jinja2",
        "NotificationBadge.tsx.jinja2",
        "DelegationSettings.tsx.jinja2",
        "useApprovals.ts.jinja2",
    ],
}


def _render_template(stack: str, template_name: str) -> str:
    """Render template với context cơ bản để kiểm tra Rule V1/V2.

    Nếu render thất bại (thiếu biến context hoặc lỗi cú pháp), trả về nội dung
    thô của template để vẫn có thể kiểm tra Rule V1/V2.
    """
    template_path = STACK_DIRS[stack] / template_name
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(STACK_DIRS[stack])),
        undefined=jinja2.ChainableUndefined,
    )
    ctx = {
        "project_name": "test_project",
        "module_name": "test_module",
        "entity_name": "Approval",
        "model_name": "ApprovalModel",
        "service_name": "ApprovalService",
        "use_events": True,
        "num_requests": 10,
        "notification_config": {"emailEnabled": True, "smsEnabled": False},
    }
    try:
        template = env.get_template(template_name)
        return template.render(**ctx)
    except Exception:
        # Render thất bại: trả về nội dung thô để kiểm tra Rule V1/V2
        return template_path.read_text(encoding="utf-8")


# ============================================================================
# TestRuleV1NoMidicoderImport — kiểm tra rendered output không có `from midicoder`
# ============================================================================


class TestRuleV1NoMidicoderImport:
    """Rule V1: rendered output của template không được chứa 'from midicoder'."""

    @pytest.mark.parametrize("stack", list(ALL_TEMPLATES.keys()))
    def test_rendered_no_midicoder_import(self, stack: str):
        """Mỗi template render ra không chứa 'from midicoder'."""
        for template_name in ALL_TEMPLATES[stack]:
            output = _render_template(stack, template_name)
            assert "from midicoder" not in output, (
                f"Rule V1 vi phạm: {stack}/{template_name} chứa 'from midicoder' trong rendered output"
            )


# ============================================================================
# TestRuleV2NoPostInit — kiểm tra rendered output không có `__post_init__`
# ============================================================================


class TestRuleV2NoPostInit:
    """Rule V2: rendered output của template không được chứa '__post_init__'."""

    @pytest.mark.parametrize("stack", list(ALL_TEMPLATES.keys()))
    def test_rendered_no_post_init(self, stack: str):
        """Mỗi template render ra không chứa '__post_init__'."""
        for template_name in ALL_TEMPLATES[stack]:
            output = _render_template(stack, template_name)
            assert "__post_init__" not in output, (
                f"Rule V2 vi phạm: {stack}/{template_name} chứa '__post_init__' trong rendered output"
            )
