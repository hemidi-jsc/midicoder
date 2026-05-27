# coding: utf-8
"""
Kiểm tra mô-đun recipes cho CP42 — Approval Workflow Engine.

Bao gồm các tests cho:
- RecipeOutput: tạo, fields, loại IR
- basic_approval_recipe: tên, mô tả, requests, steps, không escalation/delegation
- full_workflow_recipe: tên, mô tả, 2 requests (tuần tự + song song), 5 steps,
  escalation rules, delegation, notification_config
- to_dict roundtrip
"""

from __future__ import annotations

import pytest

from midicoder.packs.cp42_approval.recipes import (
    RecipeOutput,
    basic_approval_recipe,
    full_workflow_recipe,
)


# ===========================================================================
# Test RecipeOutput
# ===========================================================================


class TestRecipeOutput:
    """Kiểm tra RecipeOutput — dataclass cơ bản."""

    def test_returns_recipe_output(self):
        """Kiểm tra recipe trả về đối tượng RecipeOutput."""
        output = basic_approval_recipe()
        assert isinstance(output, RecipeOutput)

    def test_ir_is_approval_ir(self):
        """Kiểm tra ir là đối tượng ApprovalIR."""
        output = basic_approval_recipe()
        assert type(output.ir).__name__ == "ApprovalIR"

    def test_has_name_and_description(self):
        """Kiểm tra RecipeOutput có name và description không rỗng."""
        output = basic_approval_recipe()
        assert output.name
        assert output.description


# ===========================================================================
# Test basic_approval_recipe
# ===========================================================================


class TestBasicApprovalRecipe:
    """Kiểm tra basic_approval_recipe — 1 yêu cầu tuần tự, 2 bước."""

    def test_name_is_basic_approval(self):
        """Kiểm tra tên recipe là basic_approval."""
        output = basic_approval_recipe()
        assert output.name == "basic_approval"

    def test_has_description(self):
        """Kiểm tra recipe có mô tả không rỗng."""
        output = basic_approval_recipe()
        assert output.description
        assert len(output.description) > 10

    def test_has_one_request(self):
        """Kiểm tra có đúng 1 yêu cầu phê duyệt."""
        output = basic_approval_recipe()
        assert len(output.ir.requests) == 1

    def test_request_id_is_appr_seq_001(self):
        """Kiểm tra request_id là appr_seq_001."""
        output = basic_approval_recipe()
        assert output.ir.requests[0].request_id == "appr_seq_001"

    def test_requester_id_is_user_001(self):
        """Kiểm tra initiator_id là user_001."""
        output = basic_approval_recipe()
        assert output.ir.requests[0].initiator_id == "user_001"

    def test_entity_type_is_deploy(self):
        """Kiểm tra entity_type là deploy."""
        output = basic_approval_recipe()
        assert output.ir.requests[0].entity_type == "deploy"

    def test_entity_id_is_deploy_v2_3_0(self):
        """Kiểm tra entity_id là deploy_v2.3.0."""
        output = basic_approval_recipe()
        assert output.ir.requests[0].entity_id == "deploy_v2.3.0"

    def test_approval_type_is_sequential(self):
        """Kiểm tra approval_type là SEQUENTIAL."""
        from midicoder.packs.cp42_approval.models import ApprovalType
        output = basic_approval_recipe()
        assert output.ir.requests[0].approval_type == ApprovalType.SEQUENTIAL

    def test_total_steps_is_2(self):
        """Kiểm tra total_steps là 2."""
        output = basic_approval_recipe()
        assert output.ir.requests[0].total_steps == 2

    def test_metadata_chain_type_sequential(self):
        """Kiểm tra metadata có chain_type là sequential."""
        output = basic_approval_recipe()
        assert output.ir.requests[0].metadata["chain_type"] == "sequential"

    def test_has_two_steps(self):
        """Kiểm tra có đúng 2 bước phê duyệt."""
        output = basic_approval_recipe()
        assert len(output.ir.steps) == 2

    def test_steps_are_sequential_order(self):
        """Kiểm tra các bước có step_number theo thứ tự 1, 2."""
        output = basic_approval_recipe()
        assert output.ir.steps[0].step_number == 1
        assert output.ir.steps[1].step_number == 2

    def test_step_approver_roles_manager_then_director(self):
        """Kiểm tra approver_role: manager rồi director."""
        output = basic_approval_recipe()
        assert output.ir.steps[0].approver_role == "manager"
        assert output.ir.steps[1].approver_role == "director"

    def test_no_escalation_rules(self):
        """Kiểm tra không có quy tắc nâng cấp."""
        output = basic_approval_recipe()
        assert len(output.ir.escalation_rules) == 0

    def test_no_delegations(self):
        """Kiểm tra không có ủy quyền."""
        output = basic_approval_recipe()
        assert len(output.ir.delegations) == 0

    def test_use_events_is_true(self):
        """Kiểm tra use_events là True."""
        output = basic_approval_recipe()
        assert output.ir.use_events is True

    def test_notification_config_is_empty(self):
        """Kiểm tra notification_config là dict rỗng."""
        output = basic_approval_recipe()
        assert output.ir.notification_config == {}

    def test_steps_linked_to_request(self):
        """Kiểm tra các bước đều liên kết với request_id appr_seq_001."""
        output = basic_approval_recipe()
        for step in output.ir.steps:
            assert step.request_id == "appr_seq_001"

    def test_step_ids_are_unique(self):
        """Kiểm tra các step_id là duy nhất."""
        output = basic_approval_recipe()
        ids = [s.step_id for s in output.ir.steps]
        assert len(ids) == len(set(ids))


# ===========================================================================
# Test full_workflow_recipe
# ===========================================================================


class TestFullWorkflowRecipe:
    """Kiểm tra full_workflow_recipe — 2 yêu cầu, 5 bước, nâng cấp, ủy quyền."""

    def test_name_is_full_workflow(self):
        """Kiểm tra tên recipe là full_workflow."""
        output = full_workflow_recipe()
        assert output.name == "full_workflow"

    def test_has_description(self):
        """Kiểm tra recipe có mô tả không rỗng."""
        output = full_workflow_recipe()
        assert output.description
        assert len(output.description) > 10

    def test_has_two_requests(self):
        """Kiểm tra có đúng 2 yêu cầu phê duyệt."""
        output = full_workflow_recipe()
        assert len(output.ir.requests) == 2

    def test_first_request_is_sequential_merge(self):
        """Kiểm tra yêu cầu đầu tiên là SEQUENTIAL, entity_type merge."""
        from midicoder.packs.cp42_approval.models import ApprovalType
        output = full_workflow_recipe()
        req = output.ir.requests[0]
        assert req.request_id == "appr_full_seq_001"
        assert req.approval_type == ApprovalType.SEQUENTIAL
        assert req.entity_type == "merge"

    def test_second_request_is_parallel_release(self):
        """Kiểm tra yêu cầu thứ hai là PARALLEL, entity_type release."""
        from midicoder.packs.cp42_approval.models import ApprovalType
        output = full_workflow_recipe()
        req = output.ir.requests[1]
        assert req.request_id == "appr_full_par_001"
        assert req.approval_type == ApprovalType.PARALLEL
        assert req.entity_type == "release"

    def test_has_five_steps(self):
        """Kiểm tra có đúng 5 bước phê duyệt."""
        output = full_workflow_recipe()
        assert len(output.ir.steps) == 5

    def test_sequential_request_has_three_steps(self):
        """Kiểm tra yêu cầu tuần tự có 3 bước."""
        output = full_workflow_recipe()
        seq_steps = [s for s in output.ir.steps if s.request_id == "appr_full_seq_001"]
        assert len(seq_steps) == 3

    def test_parallel_request_has_two_steps(self):
        """Kiểm tra yêu cầu song song có 2 bước."""
        output = full_workflow_recipe()
        par_steps = [s for s in output.ir.steps if s.request_id == "appr_full_par_001"]
        assert len(par_steps) == 2

    def test_sequential_steps_roles_team_lead_manager_director(self):
        """Kiểm tra vai trò bước tuần tự: team_lead → manager → director."""
        output = full_workflow_recipe()
        seq_steps = [s for s in output.ir.steps if s.request_id == "appr_full_seq_001"]
        assert seq_steps[0].approver_role == "team_lead"
        assert seq_steps[1].approver_role == "manager"
        assert seq_steps[2].approver_role == "director"

    def test_sequential_steps_approvers(self):
        """Kiểm tra approver_id của các bước tuần tự."""
        output = full_workflow_recipe()
        seq_steps = [s for s in output.ir.steps if s.request_id == "appr_full_seq_001"]
        assert seq_steps[0].approver_id == "team_lead_001"
        assert seq_steps[1].approver_id == "manager_001"
        assert seq_steps[2].approver_id == "director_001"

    def test_parallel_steps_both_reviewers(self):
        """Kiểm tra cả 2 bước song song đều có vai trò reviewer."""
        output = full_workflow_recipe()
        par_steps = [s for s in output.ir.steps if s.request_id == "appr_full_par_001"]
        assert par_steps[0].approver_role == "reviewer"
        assert par_steps[1].approver_role == "reviewer"

    def test_parallel_steps_have_is_parallel_true(self):
        """Kiểm tra các bước song song có is_parallel=True."""
        output = full_workflow_recipe()
        par_steps = [s for s in output.ir.steps if s.request_id == "appr_full_par_001"]
        assert par_steps[0].is_parallel is True
        assert par_steps[1].is_parallel is True

    def test_has_two_escalation_rules(self):
        """Kiểm tra có đúng 2 quy tắc nâng cấp."""
        output = full_workflow_recipe()
        assert len(output.ir.escalation_rules) == 2

    def test_first_escalation_for_seq_120_minutes(self):
        """Kiểm tra quy tắc nâng cấp đầu tiên cho request tuần tự, 120 phút."""
        from midicoder.packs.cp42_approval.models import EscalationStrategy
        output = full_workflow_recipe()
        esc = output.ir.escalation_rules[0]
        assert esc.request_id == "appr_full_seq_001"
        assert esc.trigger_after_minutes == 120
        assert esc.escalation_strategy == EscalationStrategy.NEXT_LEVEL
        assert esc.target_id == "director_001"

    def test_second_escalation_for_par_240_minutes(self):
        """Kiểm tra quy tắc nâng cấp thứ hai cho request song song, 240 phút."""
        from midicoder.packs.cp42_approval.models import EscalationStrategy
        output = full_workflow_recipe()
        esc = output.ir.escalation_rules[1]
        assert esc.request_id == "appr_full_par_001"
        assert esc.trigger_after_minutes == 240
        assert esc.escalation_strategy == EscalationStrategy.NEXT_LEVEL
        assert esc.target_id == "cto_001"

    def test_has_one_delegation(self):
        """Kiểm tra có đúng 1 bản ghi ủy quyền."""
        output = full_workflow_recipe()
        assert len(output.ir.delegations) == 1

    def test_delegation_from_manager_to_senior_dev(self):
        """Kiểm tra ủy quyền từ manager_001 đến senior_dev_001."""
        from midicoder.packs.cp42_approval.models import DelegationType
        output = full_workflow_recipe()
        del_rec = output.ir.delegations[0]
        assert del_rec.delegator_id == "manager_001"
        assert del_rec.delegatee_id == "senior_dev_001"
        assert del_rec.delegation_type == DelegationType.TEMPORARY
        assert del_rec.scope == "merge"

    def test_notification_config_has_event_topics(self):
        """Kiểm tra notification_config có 4 event_topics."""
        output = full_workflow_recipe()
        nc = output.ir.notification_config
        assert "event_topics" in nc
        assert len(nc["event_topics"]) == 4
        assert "approval.requested" in nc["event_topics"]
        assert "approval.decided" in nc["event_topics"]
        assert "approval.escalated" in nc["event_topics"]
        assert "approval.delegated" in nc["event_topics"]

    def test_notification_config_has_channels(self):
        """Kiểm tra notification_config có channels."""
        output = full_workflow_recipe()
        nc = output.ir.notification_config
        assert "channels" in nc
        assert "email" in nc["channels"]
        assert "in_app" in nc["channels"]

    def test_use_events_is_true(self):
        """Kiểm tra use_events là True."""
        output = full_workflow_recipe()
        assert output.ir.use_events is True

    def test_delegation_valid_until_is_7_days(self):
        """Kiểm tra thời hạn ủy quyền khoảng 7 ngày (tolerance 1s cho floating point)."""
        from datetime import timedelta
        output = full_workflow_recipe()
        del_rec = output.ir.delegations[0]
        assert del_rec.valid_until is not None
        assert del_rec.valid_from is not None
        diff = del_rec.valid_until - del_rec.valid_from
        assert abs(diff - timedelta(days=7)) < timedelta(seconds=1)


# ===========================================================================
# Test Recipe to_dict roundtrip
# ===========================================================================


class TestRecipeToDict:
    """Kiểm tra to_dict và from_dict roundtrip cho các recipe."""

    def test_basic_recipe_ir_to_dict(self):
        """Kiểm tra basic recipe chuyển sang dict có đúng cấu trúc."""
        output = basic_approval_recipe()
        d = output.ir.to_dict()
        assert "requests" in d
        assert "steps" in d
        assert "escalation_rules" in d
        assert "delegations" in d
        assert "notification_config" in d
        assert "use_events" in d
        assert len(d["requests"]) == 1
        assert len(d["steps"]) == 2
        assert len(d["escalation_rules"]) == 0
        assert len(d["delegations"]) == 0

    def test_basic_recipe_ir_from_dict_roundtrip(self):
        """Kiểm tra basic recipe roundtrip to_dict -> from_dict giữ nguyên dữ liệu."""
        from midicoder.packs.cp42_approval.parser import ApprovalIR
        output = basic_approval_recipe()
        d = output.ir.to_dict()
        restored = ApprovalIR.from_dict(d)
        assert len(restored.requests) == 1
        assert len(restored.steps) == 2
        assert restored.requests[0].request_id == "appr_seq_001"
        assert restored.steps[0].step_id == "step_seq_001"
        assert restored.use_events is True

    def test_full_recipe_ir_to_dict(self):
        """Kiểm tra full recipe chuyển sang dict có đầy đủ dữ liệu."""
        output = full_workflow_recipe()
        d = output.ir.to_dict()
        assert len(d["requests"]) == 2
        assert len(d["steps"]) == 5
        assert len(d["escalation_rules"]) == 2
        assert len(d["delegations"]) == 1
        assert d["use_events"] is True
        assert "event_topics" in d["notification_config"]

    def test_full_recipe_ir_from_dict_roundtrip(self):
        """Kiểm tra full recipe roundtrip to_dict -> from_dict giữ nguyên dữ liệu."""
        from midicoder.packs.cp42_approval.parser import ApprovalIR
        output = full_workflow_recipe()
        d = output.ir.to_dict()
        restored = ApprovalIR.from_dict(d)
        assert len(restored.requests) == 2
        assert len(restored.steps) == 5
        assert len(restored.escalation_rules) == 2
        assert len(restored.delegations) == 1
        assert restored.requests[0].request_id == "appr_full_seq_001"
        assert restored.requests[1].request_id == "appr_full_par_001"

    def test_roundtrip_preserves_request_metadata(self):
        """Kiểm tra roundtrip giữ nguyên metadata của request."""
        from midicoder.packs.cp42_approval.parser import ApprovalIR
        output = full_workflow_recipe()
        d = output.ir.to_dict()
        restored = ApprovalIR.from_dict(d)
        # Request đầu tiên: chain_type=sequential, priority=high
        assert restored.requests[0].metadata["chain_type"] == "sequential"
        assert restored.requests[0].metadata["priority"] == "high"
        # Request thứ hai: chain_type=parallel, voting_mode=majority
        assert restored.requests[1].metadata["chain_type"] == "parallel"
        assert restored.requests[1].metadata["voting_mode"] == "majority"
