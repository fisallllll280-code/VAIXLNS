import unittest
from scripts.vaixl_connection_fabric import SemanticConnectionFabric

class ConnectionFabricTests(unittest.TestCase):
    def fabric(self):
        f = SemanticConnectionFabric()
        f.add_channel("SPEC-A", "SPEC", priority=100, capacity=1)
        f.add_channel("SPEC-B", "SPEC", priority=90, capacity=1)
        f.add_channel("SEC", "SECURITY", priority=110, capacity=1)
        return f

    def test_independent_purposes_flow(self):
        f = self.fabric()
        self.assertEqual(f.route({"message_id": "1", "purpose": "SPEC"}), "SPEC-A")
        self.assertEqual(f.route({"message_id": "2", "purpose": "SECURITY"}), "SEC")

    def test_same_purpose_fails_over_to_second_connection(self):
        f = self.fabric()
        f.route({"message_id": "1", "purpose": "SPEC"})
        self.assertEqual(f.route({"message_id": "2", "purpose": "SPEC"}), "SPEC-B")

    def test_blocked_channel_does_not_block_other_purpose(self):
        f = self.fabric()
        f.route({"message_id": "1", "purpose": "SPEC"})
        self.assertEqual(f.route({"message_id": "2", "purpose": "SECURITY"}), "SEC")

    def test_isolation_is_local(self):
        f = self.fabric()
        f.isolate("SPEC-A", "test")
        self.assertEqual(f.route({"message_id": "1", "purpose": "SPEC"}), "SPEC-B")
        self.assertEqual(f.channels["SPEC-A"].state, "ISOLATED")

    def test_event_hashes_are_deterministic(self):
        f = self.fabric()
        f.route({"message_id": "1", "purpose": "SPEC"})
        e = f.evidence()
        self.assertEqual(e["events"][0]["event_hash"], e["events"][0]["event_hash"])
        self.assertEqual(e["evidence_hash"], f.evidence()["evidence_hash"])

if __name__ == "__main__":
    unittest.main()
