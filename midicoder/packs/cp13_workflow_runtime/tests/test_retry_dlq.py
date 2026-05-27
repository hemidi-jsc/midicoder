"""Test CP13 — RetryPolicy, DeadLetterQueue, JobRetryTracker và StateMachine edge cases.

Module này kiểm tra:
- RetryPolicy: exponential backoff, jitter, serialization
- DeadLetterQueue: thêm/xóa message, giới hạn kích thước, serialization
- JobRetryTracker: retry lifecycle, exhaustion, reset
- StateMachine: guard failure, effect failure, error handling, metadata
"""

import pytest
from unittest import TestCase
from datetime import datetime
from uuid import uuid4

from midicoder.packs.cp13_workflow_runtime.scheduler import RetryPolicy, DeadLetterQueue, JobRetryTracker
from midicoder.packs.cp13_workflow_runtime.models import WorkflowDefinition, Transition, GuardType, EffectType, Guard, Effect
from midicoder.packs.cp13_workflow_runtime.engine.state_machine import StateMachine
from midicoder.packs.cp13_workflow_runtime.effects.base import EffectResult
from midicoder.errors import MidicoderError, ErrorCode


# ---------------------------------------------------------------------------
# TestRetryPolicy
# ---------------------------------------------------------------------------

class TestRetryPolicy(TestCase):
    """Kiểm tra RetryPolicy — exponential backoff, jitter, serialization."""

    def test_create_with_defaults(self):
        """Tạo RetryPolicy với các giá trị mặc định."""
        policy = RetryPolicy()
        self.assertEqual(policy.max_retries, 3)
        self.assertEqual(policy.base_delay_seconds, 1.0)
        self.assertEqual(policy.max_delay_seconds, 300.0)
        self.assertEqual(policy.backoff_multiplier, 2.0)
        self.assertTrue(policy.jitter)

    def test_get_delay_attempt_zero(self):
        """get_delay_attempt(0) trả về độ trễ trong khoảng [0, base_delay] khi có jitter."""
        policy = RetryPolicy()
        delay = policy.get_delay_attempt(0)
        # jitter: random.uniform(0, base_delay_seconds)
        self.assertGreaterEqual(delay, 0.0)
        self.assertLessEqual(delay, policy.base_delay_seconds)

    def test_get_delay_attempt_one(self):
        """get_delay_attempt(1) trả về độ trễ trong khoảng [0, base_delay * multiplier]."""
        policy = RetryPolicy()
        expected_max = policy.base_delay_seconds * policy.backoff_multiplier
        delay = policy.get_delay_attempt(1)
        self.assertGreaterEqual(delay, 0.0)
        self.assertLessEqual(delay, expected_max)

    def test_get_delay_attempt_two(self):
        """get_delay_attempt(2) trả về độ trễ trong khoảng [0, base_delay * multiplier^2]."""
        policy = RetryPolicy()
        expected_max = policy.base_delay_seconds * (policy.backoff_multiplier ** 2)
        delay = policy.get_delay_attempt(2)
        self.assertGreaterEqual(delay, 0.0)
        self.assertLessEqual(delay, expected_max)

    def test_get_delay_attempt_capped_at_max_delay(self):
        """get_delay_attempt(10) bị giới hạn bởi max_delay_seconds."""
        policy = RetryPolicy()
        # 1.0 * 2^10 = 1024, nhưng max_delay = 300 nên delay <= 300
        delay = policy.get_delay_attempt(10)
        self.assertGreaterEqual(delay, 0.0)
        self.assertLessEqual(delay, policy.max_delay_seconds)

    def test_get_delay_no_jitter_exact_exponential(self):
        """jitter=False cho giá trị exponential chính xác."""
        policy = RetryPolicy(jitter=False)
        # attempt=0: 1.0 * 2^0 = 1.0
        self.assertEqual(policy.get_delay_attempt(0), 1.0)
        # attempt=1: 1.0 * 2^1 = 2.0
        self.assertEqual(policy.get_delay_attempt(1), 2.0)
        # attempt=2: 1.0 * 2^2 = 4.0
        self.assertEqual(policy.get_delay_attempt(2), 4.0)
        # attempt=10: min(1.0 * 2^10, 300) = 300.0
        self.assertEqual(policy.get_delay_attempt(10), 300.0)

    def test_to_dict_from_dict_roundtrip(self):
        """to_dict() / from_dict() giữ nguyên toàn bộ thuộc tính."""
        original = RetryPolicy(
            max_retries=5,
            base_delay_seconds=2.0,
            max_delay_seconds=600.0,
            backoff_multiplier=3.0,
            jitter=False,
        )
        restored = RetryPolicy.from_dict(original.to_dict())
        self.assertEqual(restored.max_retries, original.max_retries)
        self.assertEqual(restored.base_delay_seconds, original.base_delay_seconds)
        self.assertEqual(restored.max_delay_seconds, original.max_delay_seconds)
        self.assertEqual(restored.backoff_multiplier, original.backoff_multiplier)
        self.assertEqual(restored.jitter, original.jitter)

    def test_custom_multiplier(self):
        """RetryPolicy với backoff_multiplier tùy chỉnh."""
        policy = RetryPolicy(backoff_multiplier=1.5, jitter=False)
        # attempt=0: 1.0 * 1.5^0 = 1.0
        self.assertEqual(policy.get_delay_attempt(0), 1.0)
        # attempt=1: 1.0 * 1.5^1 = 1.5
        self.assertEqual(policy.get_delay_attempt(1), 1.5)
        # attempt=2: 1.0 * 1.5^2 = 2.25
        self.assertEqual(policy.get_delay_attempt(2), 2.25)


# ---------------------------------------------------------------------------
# TestDeadLetterQueue
# ---------------------------------------------------------------------------

class TestDeadLetterQueue(TestCase):
    """Kiểm tra DeadLetterQueue — thêm message, size, purge, serialization."""

    def test_create_with_defaults(self):
        """Tạo DeadLetterQueue với các giá trị mặc định."""
        dlq = DeadLetterQueue(queue_name="test-queue")
        self.assertEqual(dlq.queue_name, "test-queue")
        self.assertEqual(dlq.max_size, 10000)
        self.assertEqual(dlq.retention_hours, 168)
        self.assertEqual(dlq.size(), 0)

    def test_add_message(self):
        """add() thêm message vào queue."""
        dlq = DeadLetterQueue(queue_name="test-queue")
        msg = {"job_id": "job-1", "error": "timeout"}
        dlq.add(msg)
        self.assertEqual(dlq.size(), 1)

    def test_size_returns_count(self):
        """size() trả về số message đúng."""
        dlq = DeadLetterQueue(queue_name="test-queue")
        for i in range(5):
            dlq.add({"index": i})
        self.assertEqual(dlq.size(), 5)

    def test_get_all_returns_all_messages(self):
        """get_all() trả về tất cả messages."""
        dlq = DeadLetterQueue(queue_name="test-queue")
        msgs = [{"id": 1}, {"id": 2}, {"id": 3}]
        for m in msgs:
            dlq.add(m)
        all_msgs = dlq.get_all()
        self.assertEqual(len(all_msgs), 3)
        self.assertEqual(all_msgs[0]["id"], 1)
        self.assertEqual(all_msgs[2]["id"], 3)

    def test_is_full_when_at_max_size(self):
        """is_full() trả về True khi số message đạt max_size."""
        dlq = DeadLetterQueue(queue_name="tiny", max_size=3)
        self.assertFalse(dlq.is_full())
        dlq.add({"id": 1})
        dlq.add({"id": 2})
        self.assertFalse(dlq.is_full())
        dlq.add({"id": 3})
        self.assertTrue(dlq.is_full())

    def test_purge_clears_all_messages(self):
        """purge() xóa toàn bộ messages khỏi queue."""
        dlq = DeadLetterQueue(queue_name="test-queue")
        dlq.add({"id": 1})
        dlq.add({"id": 2})
        self.assertEqual(dlq.size(), 2)
        dlq.purge()
        self.assertEqual(dlq.size(), 0)
        self.assertEqual(dlq.get_all(), [])

    def test_to_dict_from_dict_roundtrip(self):
        """to_dict() / from_dict() giữ nguyên toàn bộ thuộc tính."""
        dlq = DeadLetterQueue(
            queue_name="my-dlq",
            messages=[{"job": "a"}, {"job": "b"}],
            max_size=5000,
            retention_hours=48,
        )
        restored = DeadLetterQueue.from_dict(dlq.to_dict())
        self.assertEqual(restored.queue_name, "my-dlq")
        self.assertEqual(len(restored.messages), 2)
        self.assertEqual(restored.max_size, 5000)
        self.assertEqual(restored.retention_hours, 48)

    def test_custom_max_size(self):
        """DeadLetterQueue với max_size tùy chỉnh."""
        dlq = DeadLetterQueue(queue_name="small", max_size=10)
        self.assertEqual(dlq.max_size, 10)


# ---------------------------------------------------------------------------
# TestJobRetryTracker
# ---------------------------------------------------------------------------

class TestJobRetryTracker(TestCase):
    """Kiểm tra JobRetryTracker — retry lifecycle, exhaustion, reset."""

    def _make_tracker(self, max_retries=3):
        """Tạo JobRetryTracker với RetryPolicy mặc định."""
        policy = RetryPolicy(max_retries=max_retries, jitter=False)
        return JobRetryTracker(instance_id="inst-001", retry_policy=policy)

    def test_create_with_retry_policy(self):
        """Tạo JobRetryTracker với RetryPolicy."""
        tracker = self._make_tracker()
        self.assertEqual(tracker.instance_id, "inst-001")
        self.assertEqual(tracker.current_attempt, 0)
        self.assertEqual(tracker.last_error, "")
        self.assertIsNone(tracker.next_retry_at)
        self.assertFalse(tracker.is_exhausted)

    def test_should_retry_initially(self):
        """should_retry() trả về True khi mới tạo."""
        tracker = self._make_tracker()
        self.assertTrue(tracker.should_retry())

    def test_record_failure_increments_attempt(self):
        """record_failure() tăng current_attempt."""
        tracker = self._make_tracker()
        tracker.record_failure("error 1")
        self.assertEqual(tracker.current_attempt, 1)
        self.assertEqual(tracker.last_error, "error 1")

    def test_should_retry_false_when_exhausted(self):
        """should_retry() trả về False sau khi retry hết."""
        tracker = self._make_tracker(max_retries=2)
        tracker.record_failure("err1")
        self.assertTrue(tracker.should_retry())
        # Lần thứ 2 (>= max_retries=2) sẽ raise
        with self.assertRaises(MidicoderError):
            tracker.record_failure("err2")
        self.assertFalse(tracker.should_retry())

    def test_is_exhausted_after_max_retries(self):
        """is_exhausted thành True sau max_retries lần failure."""
        tracker = self._make_tracker(max_retries=2)
        tracker.record_failure("err1")
        self.assertFalse(tracker.is_exhausted)
        with self.assertRaises(MidicoderError):
            tracker.record_failure("err2")
        self.assertTrue(tracker.is_exhausted)

    def test_get_next_delay_returns_correct_backoff(self):
        """get_next_delay() trả về độ trễ backoff đúng."""
        policy = RetryPolicy(base_delay_seconds=1.0, backoff_multiplier=2.0, jitter=False)
        tracker = JobRetryTracker(instance_id="inst-001", retry_policy=policy)
        # attempt=0: 1.0 * 2^0 = 1.0
        self.assertEqual(tracker.get_next_delay(), 1.0)
        tracker.record_failure("err1")
        # attempt=1: 1.0 * 2^1 = 2.0
        self.assertEqual(tracker.get_next_delay(), 2.0)

    def test_reset_resets_all_state(self):
        """reset() đặt lại toàn bộ trạng thái."""
        tracker = self._make_tracker(max_retries=3)
        tracker.record_failure("err1")
        tracker.record_failure("err2")
        self.assertEqual(tracker.current_attempt, 2)
        tracker.reset()
        self.assertEqual(tracker.current_attempt, 0)
        self.assertEqual(tracker.last_error, "")
        self.assertIsNone(tracker.next_retry_at)
        self.assertFalse(tracker.is_exhausted)
        self.assertTrue(tracker.should_retry())

    def test_to_dict_returns_correct_fields(self):
        """to_dict() trả về dict với đầy đủ fields."""
        tracker = self._make_tracker()
        tracker.record_failure("err1")
        d = tracker.to_dict()
        self.assertEqual(d["instance_id"], "inst-001")
        self.assertEqual(d["current_attempt"], 1)
        self.assertEqual(d["last_error"], "err1")
        self.assertIn("retry_policy", d)
        self.assertIn("next_retry_at", d)
        self.assertIn("is_exhausted", d)
        self.assertFalse(d["is_exhausted"])

    def test_raises_cp13_job_retry_exhausted_on_exhaustion(self):
        """record_failure() raise CP13_JOB_RETRY_EXHAUSTED khi hết retry."""
        tracker = self._make_tracker(max_retries=2)
        tracker.record_failure("err1")
        with self.assertRaises(MidicoderError) as ctx:
            tracker.record_failure("err2")
        self.assertIn(ErrorCode.CP13_JOB_RETRY_EXHAUSTED.value, str(ctx.exception))

    def test_raises_after_already_exhausted(self):
        """record_failure() vẫn raise khi gọi sau khi đã exhausted."""
        tracker = self._make_tracker(max_retries=2)
        tracker.record_failure("err1")
        with self.assertRaises(MidicoderError):
            tracker.record_failure("err2")
        # exhausted rồi, gọi tiếp vẫn raise
        with self.assertRaises(MidicoderError) as ctx:
            tracker.record_failure("err3")
        self.assertIn(ErrorCode.CP13_JOB_RETRY_EXHAUSTED.value, str(ctx.exception))


# ---------------------------------------------------------------------------
# TestStateMachineEdgeCases
# ---------------------------------------------------------------------------

class TestStateMachineEdgeCases(TestCase):
    """Kiểm tra các edge case của StateMachine — guard, effect, metadata."""

    def _make_workflow(self):
        """Tạo WorkflowDefinition đơn giản cho test."""
        transitions = [
            Transition(from_state="draft", to_state="submitted", event="submit"),
            Transition(from_state="submitted", to_state="approved", event="approve"),
            Transition(from_state="submitted", to_state="rejected", event="reject"),
        ]
        return WorkflowDefinition(
            name="order",
            states=["draft", "submitted", "approved", "rejected"],
            initial_state="draft",
            transitions=transitions,
        )

    def _make_workflow_with_guards(self):
        """Tạo workflow có guards trên transition."""
        transitions = [
            Transition(
                from_state="draft",
                to_state="submitted",
                event="submit",
                guards=[
                    Guard(type=GuardType.BUSINESS, condition="items > 0"),
                    Guard(type=GuardType.STATE, condition="status == active"),
                ],
            ),
        ]
        return WorkflowDefinition(
            name="guarded",
            states=["draft", "submitted"],
            initial_state="draft",
            transitions=transitions,
        )

    def _make_workflow_with_effects(self):
        """Tạo workflow có effects trên transition."""
        transitions = [
            Transition(
                from_state="draft",
                to_state="submitted",
                event="submit",
                effects=[
                    Effect(type=EffectType.EVENT, publish="OrderSubmitted"),
                    Effect(type=EffectType.NOTIFICATION, channel="email"),
                ],
            ),
        ]
        return WorkflowDefinition(
            name="effectful",
            states=["draft", "submitted"],
            initial_state="draft",
            transitions=transitions,
        )

    def _make_workflow_self_loop(self):
        """Tạo workflow có self-loop cho test already_in_state."""
        transitions = [
            Transition(from_state="draft", to_state="draft", event="refresh"),
        ]
        return WorkflowDefinition(
            name="self_loop",
            states=["draft"],
            initial_state="draft",
            transitions=transitions,
        )

    # --- Guard failure tests ---

    def test_transition_guard_fails(self):
        """Transition với guard_evaluator trả về False thì không chuyển state."""
        wf = self._make_workflow_with_guards()

        def always_fail_guard(guard, context):
            return False

        sm = StateMachine(wf, guard_evaluator=always_fail_guard)
        instance_id = sm.create_instance("order", uuid4())
        result = sm.transition(instance_id, "submit", tenant_id=uuid4())

        self.assertFalse(result.success)
        self.assertIsNone(result.to_state)
        self.assertEqual(sm.get_state(instance_id), "draft")  # state không đổi

    def test_multiple_guards_one_fails(self):
        """Nhiều guards, một cái fail thì transition không thực hiện."""
        wf = self._make_workflow_with_guards()

        def fail_second_guard(guard, context):
            if guard.type == GuardType.STATE:
                return False
            return True

        sm = StateMachine(wf, guard_evaluator=fail_second_guard)
        instance_id = sm.create_instance("order", uuid4())
        result = sm.transition(instance_id, "submit", tenant_id=uuid4())

        self.assertFalse(result.success)
        # Guard đầu tiên pass, guard thứ hai fail
        self.assertEqual(len(result.guards_passed), 1)
        self.assertEqual(sm.get_state(instance_id), "draft")

    # --- Effect failure tests ---

    def test_transition_effect_fails(self):
        """Effect executor trả về False thì transition vẫn thành công (best-effort)."""
        wf = self._make_workflow_with_effects()

        def always_fail_effect(effect, context):
            return False

        sm = StateMachine(wf, effect_executor=always_fail_effect)
        instance_id = sm.create_instance("order", uuid4())
        result = sm.transition(instance_id, "submit", tenant_id=uuid4())

        self.assertTrue(result.success)
        self.assertEqual(result.to_state, "submitted")
        # Không có effect nào được ghi nhận
        self.assertEqual(len(result.effects_executed), 0)

    def test_multiple_effects_one_fails(self):
        """Nhiều effects, một cái fail thì transition vẫn tiếp tục (best-effort)."""
        wf = self._make_workflow_with_effects()

        def fail_notification_effect(effect, context):
            if effect.type == EffectType.NOTIFICATION:
                return False
            return True

        sm = StateMachine(wf, effect_executor=fail_notification_effect)
        instance_id = sm.create_instance("order", uuid4())
        result = sm.transition(instance_id, "submit", tenant_id=uuid4())

        self.assertTrue(result.success)
        self.assertEqual(result.to_state, "submitted")
        # Chỉ effect đầu tiên được ghi nhận
        self.assertEqual(len(result.effects_executed), 1)

    def test_effect_executor_raises_exception_continues(self):
        """Effect executor raise exception thì transition vẫn thành công."""
        wf = self._make_workflow_with_effects()

        def raising_effect(effect, context):
            raise RuntimeError("effect failed")

        sm = StateMachine(wf, effect_executor=raising_effect)
        instance_id = sm.create_instance("order", uuid4())
        result = sm.transition(instance_id, "submit", tenant_id=uuid4())

        self.assertTrue(result.success)
        self.assertEqual(result.to_state, "submitted")

    # --- Error handling tests ---

    def test_invalid_event_raises_error(self):
        """Event name không khớp transition nào thì raise error."""
        wf = self._make_workflow()
        sm = StateMachine(wf)
        instance_id = sm.create_instance("order", uuid4())

        with self.assertRaises(MidicoderError) as ctx:
            sm.transition(instance_id, "nonexistent_event", tenant_id=uuid4())
        self.assertIn(ErrorCode.CP01_WORKFLOW_INVALID_TRANSITION.value, str(ctx.exception))

    def test_instance_not_found_raises_error(self):
        """Instance ID không tồn tại thì raise error."""
        wf = self._make_workflow()
        sm = StateMachine(wf)
        unknown_id = uuid4()

        with self.assertRaises(MidicoderError) as ctx:
            sm.transition(unknown_id, "submit", tenant_id=uuid4())
        self.assertIn(ErrorCode.CP01_WORKFLOW_NOT_FOUND.value, str(ctx.exception))

    def test_already_in_target_state_raises_error(self):
        """Instance đã ở target state thì raise CP01_WORKFLOW_ALREADY_IN_STATE."""
        wf = self._make_workflow_self_loop()
        sm = StateMachine(wf)
        instance_id = sm.create_instance("order", uuid4())

        # Self-loop: từ "draft" đến "draft", instance đang ở "draft"
        with self.assertRaises(MidicoderError) as ctx:
            sm.transition(instance_id, "refresh", tenant_id=uuid4())
        self.assertIn(ErrorCode.CP01_WORKFLOW_ALREADY_IN_STATE.value, str(ctx.exception))

    # --- Final state test ---

    def test_final_state_has_no_outgoing_transitions(self):
        """is_final_state trả về True cho state không có outgoing transitions."""
        wf = self._make_workflow()
        # "approved" và "rejected" là final states
        self.assertTrue(wf.is_final_state("approved"))
        self.assertTrue(wf.is_final_state("rejected"))
        # "draft" có transition đi ra
        self.assertFalse(wf.is_final_state("draft"))
        # "submitted" có 2 transition đi ra
        self.assertFalse(wf.is_final_state("submitted"))

    # --- Metadata test ---

    def test_transition_with_custom_metadata(self):
        """Metadata được truyền qua TransitionContext khi transition."""
        wf = self._make_workflow_with_guards()

        class ContextCapture:
            captured = None

        def capture_guard(guard, context):
            ContextCapture.captured = context
            return True

        sm = StateMachine(wf, guard_evaluator=capture_guard)
        instance_id = sm.create_instance("order", uuid4())
        custom_meta = {"order_value": 150000, "currency": "VND"}
        sm.transition(instance_id, "submit", tenant_id=uuid4(), metadata=custom_meta)

        self.assertIsNotNone(ContextCapture.captured)
        self.assertEqual(ContextCapture.captured.metadata, custom_meta)

    # --- Dry-run test ---

    def test_can_transition_dry_run_does_not_change_state(self):
        """can_transition() kiểm tra mà không thay đổi state."""
        wf = self._make_workflow()
        sm = StateMachine(wf)
        instance_id = sm.create_instance("order", uuid4())

        self.assertEqual(sm.get_state(instance_id), "draft")
        can = sm.can_transition(instance_id, "submit")
        self.assertTrue(can)
        # State vẫn là "draft" — không bị chuyển
        self.assertEqual(sm.get_state(instance_id), "draft")

    def test_can_transition_returns_false_for_invalid_event(self):
        """can_transition() trả về False cho event không hợp lệ."""
        wf = self._make_workflow()
        sm = StateMachine(wf)
        instance_id = sm.create_instance("order", uuid4())

        can = sm.can_transition(instance_id, "nonexistent")
        self.assertFalse(can)
        self.assertEqual(sm.get_state(instance_id), "draft")

    # --- EffectResult test ---

    def test_effect_result_success(self):
        """EffectResult.success() tạo kết quả thành công."""
        result = EffectResult.success(data={"key": "value"}, message="done")
        self.assertTrue(result.success)
        self.assertEqual(result.message, "done")
        self.assertEqual(result.data, {"key": "value"})
        self.assertIsNone(result.error)

    def test_effect_result_failure(self):
        """EffectResult.failure() tạo kết quả thất bại."""
        result = EffectResult.failure("something went wrong")
        self.assertFalse(result.success)
        self.assertEqual(result.error, "something went wrong")
        self.assertIsNone(result.data)
