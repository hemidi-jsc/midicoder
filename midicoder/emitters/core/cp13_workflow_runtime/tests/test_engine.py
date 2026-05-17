"""Test CP13 engine — StateMachine và EventStore."""

import pytest
from unittest import TestCase
from uuid import uuid4


class TestStateMachine(TestCase):
    """Kiểm tra StateMachine engine."""

    def _make_workflow(self):
        """Tạo WorkflowDefinition đơn giản để test."""
        from midicoder.emitters.core.cp13_workflow_runtime.models import WorkflowDefinition, Transition
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

    def test_state_machine_creation(self):
        """Tạo StateMachine với WorkflowDefinition."""
        from midicoder.emitters.core.cp13_workflow_runtime.engine.state_machine import StateMachine
        wf = self._make_workflow()
        sm = StateMachine(wf)
        self.assertEqual(sm.workflow.name, "order")

    def test_create_instance(self):
        """Tạo instance mới từ StateMachine."""
        from midicoder.emitters.core.cp13_workflow_runtime.engine.state_machine import StateMachine
        wf = self._make_workflow()
        sm = StateMachine(wf)
        entity_id = uuid4()
        instance_id = sm.create_instance("order", entity_id)
        self.assertIsInstance(instance_id, type(uuid4()))
        self.assertEqual(sm.get_state(instance_id), "draft")

    def test_get_state(self):
        """Lấy trạng thái của instance."""
        from midicoder.emitters.core.cp13_workflow_runtime.engine.state_machine import StateMachine
        wf = self._make_workflow()
        sm = StateMachine(wf)
        instance_id = sm.create_instance("order", uuid4())
        state = sm.get_state(instance_id)
        self.assertEqual(state, "draft")

    def test_transition_success(self):
        """Transition thành công giữa hai states."""
        from midicoder.emitters.core.cp13_workflow_runtime.engine.state_machine import StateMachine
        wf = self._make_workflow()
        sm = StateMachine(wf)
        instance_id = sm.create_instance("order", uuid4())
        result = sm.transition(instance_id, "submit", tenant_id=uuid4())
        self.assertTrue(result.success)
        self.assertEqual(result.to_state, "submitted")

    def test_transition_updates_state(self):
        """Transition cập nhật current_state của instance."""
        from midicoder.emitters.core.cp13_workflow_runtime.engine.state_machine import StateMachine
        wf = self._make_workflow()
        sm = StateMachine(wf)
        instance_id = sm.create_instance("order", uuid4())
        sm.transition(instance_id, "submit", tenant_id=uuid4())
        state = sm.get_state(instance_id)
        self.assertEqual(state, "submitted")

    def test_get_event_log(self):
        """Lấy log events của instance."""
        from midicoder.emitters.core.cp13_workflow_runtime.engine.state_machine import StateMachine
        wf = self._make_workflow()
        sm = StateMachine(wf)
        instance_id = sm.create_instance("order", uuid4())
        sm.transition(instance_id, "submit", tenant_id=uuid4())
        log = sm.get_event_log(instance_id)
        self.assertGreater(len(log), 0)

    def test_rebuild_state(self):
        """Rebuild state từ event log."""
        from midicoder.emitters.core.cp13_workflow_runtime.engine.state_machine import StateMachine
        wf = self._make_workflow()
        sm = StateMachine(wf)
        instance_id = sm.create_instance("order", uuid4())
        sm.transition(instance_id, "submit", tenant_id=uuid4())
        sm.transition(instance_id, "approve", tenant_id=uuid4())
        state = sm.rebuild_state(instance_id)
        self.assertEqual(state, "approved")


class TestEventStore(TestCase):
    """Kiểm tra EventStore."""

    def _make_event(self, instance_id=None, workflow_name="order", event_type="transition"):
        """Tạo WorkflowEvent để test."""
        from midicoder.emitters.core.cp13_workflow_runtime.engine.event_store import WorkflowEvent
        return WorkflowEvent(
            event_type=event_type,
            instance_id=instance_id or uuid4(),
            workflow_name=workflow_name,
            data={},
        )

    def test_append_event(self):
        """Thêm event vào store."""
        from midicoder.emitters.core.cp13_workflow_runtime.engine.event_store import EventStore
        store = EventStore()
        iid = uuid4()
        evt = self._make_event(instance_id=iid)
        store.append(evt)
        events = store.get_by_instance(iid)
        self.assertEqual(len(events), 1)

    def test_get_by_instance(self):
        """Lấy events theo instance_id."""
        from midicoder.emitters.core.cp13_workflow_runtime.engine.event_store import EventStore
        store = EventStore()
        iid = uuid4()
        store.append(self._make_event(instance_id=iid, event_type="submitted"))
        store.append(self._make_event(instance_id=iid, event_type="approved"))
        store.append(self._make_event(workflow_name="other"))
        events = store.get_by_instance(iid)
        self.assertEqual(len(events), 2)

    def test_get_by_workflow(self):
        """Lấy events theo workflow_name."""
        from midicoder.emitters.core.cp13_workflow_runtime.engine.event_store import EventStore
        store = EventStore()
        store.append(self._make_event(workflow_name="order", event_type="submitted"))
        store.append(self._make_event(workflow_name="invoice", event_type="created"))
        events = store.get_by_workflow("order")
        self.assertEqual(len(events), 1)

    def test_get_by_type(self):
        """Lấy events theo event type."""
        from midicoder.emitters.core.cp13_workflow_runtime.engine.event_store import EventStore
        store = EventStore()
        store.append(self._make_event(event_type="submitted"))
        store.append(self._make_event(event_type="submitted"))
        store.append(self._make_event(event_type="approved"))
        events = store.get_by_type("submitted")
        self.assertEqual(len(events), 2)

    def test_get_count(self):
        """Đếm số events."""
        from midicoder.emitters.core.cp13_workflow_runtime.engine.event_store import EventStore
        store = EventStore()
        store.append(self._make_event())
        store.append(self._make_event())
        self.assertEqual(store.get_count(), 2)

    def test_clear(self):
        """Xoá tất cả events."""
        from midicoder.emitters.core.cp13_workflow_runtime.engine.event_store import EventStore
        store = EventStore()
        store.append(self._make_event())
        store.clear()
        self.assertEqual(store.get_count(), 0)
