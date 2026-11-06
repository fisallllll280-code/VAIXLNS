import unittest
from runtime.agent_registry import AgentProfile, AgentRegistry
from runtime.health_monitor import HealthMonitor
from runtime.supervisor import Supervisor
from runtime.task_scheduler import TaskState, TaskScheduler

class SupervisorTests(unittest.TestCase):
    def setUp(self):
        self.registry = AgentRegistry()
        self.registry.register(AgentProfile("test-worker", frozenset({"test"}), lambda p: {"echo": p["value"]}))

    def test_requires_human_approval_by_default(self):
        receipt = Supervisor(self.registry).dispatch("test", {"value": 7})
        self.assertEqual(receipt["state"], TaskState.BLOCKED.value)
        self.assertIsNone(receipt["result"])

    def test_dispatch_after_approval(self):
        receipt = Supervisor(self.registry).dispatch("test", {"value": 7}, approved=True)
        self.assertEqual(receipt["state"], TaskState.SUCCEEDED.value)
        self.assertEqual(receipt["result"], {"echo": 7})

    def test_unknown_capability_fails_closed(self):
        receipt = Supervisor(self.registry).dispatch("missing", {}, approved=True)
        self.assertEqual(receipt["state"], TaskState.BLOCKED.value)

    def test_duplicate_registration_rejected(self):
        with self.assertRaises(ValueError):
            self.registry.register(AgentProfile("test-worker", frozenset({"other"}), lambda p: {}))

    def test_handler_failure_is_recorded(self):
        bad = AgentRegistry()
        bad.register(AgentProfile("bad", frozenset({"test"}), lambda p: (_ for _ in ()).throw(RuntimeError("boom"))))
        receipt = Supervisor(bad).dispatch("test", {}, approved=True)
        self.assertEqual(receipt["state"], TaskState.FAILED.value)
        self.assertIn("boom", receipt["error"])

    def test_health_scope_is_explicit(self):
        scheduler = TaskScheduler()
        result = HealthMonitor().snapshot(self.registry, scheduler)
        self.assertEqual(result["health_scope"], "local_metadata_only")

if __name__ == "__main__":
    unittest.main()
