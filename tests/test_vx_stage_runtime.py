import unittest

from unittest.mock import patch

from scripts.vx_stage_runtime import DEFAULT_KEY, StageFederationGate, StageVX, run_stage, verify


class VXStageRuntimeTests(unittest.TestCase):
    def test_default_key_source_is_reported_when_environment_is_unset(self):
        with patch.dict("os.environ", {}, clear=True):
            evidence = run_stage()
        self.assertEqual(evidence["provenance"]["key_source"], "test-default")

    def test_environment_key_source_is_reported_when_configured(self):
        with patch.dict("os.environ", {"VX_STAGE_SIGNING_KEY": "isolated-test-key"}):
            evidence = run_stage()
        self.assertEqual(evidence["provenance"]["key_source"], "environment")

    def setUp(self):
        self.key = DEFAULT_KEY.encode("utf-8")
        self.gate = StageFederationGate(self.key)
        self.vx = StageVX(
            "VX-Code-Stage-01",
            "software-engineering",
            {"coding", "simulation", "verification"},
            {"observe", "simulate", "verify"},
        )
        self.gate.register(self.vx)
        self.vx.heartbeat("2026-10-07T00:00:00Z")

    def test_signed_request_round_trip(self):
        envelope = self.gate.signed_request(
            "R1", self.vx.instance_id, "simulation", "simulate"
        )
        self.assertTrue(verify(envelope, self.key))
        envelope["capability"] = "admin"
        self.assertFalse(verify(envelope, self.key))

    def test_authority_aware_route(self):
        route = self.gate.route("simulation", "simulate", "R2")
        self.assertEqual(route["target"], "VX-Code-Stage-01")

    def test_isolation_blocks_route(self):
        self.vx.isolate("test")
        with self.assertRaises(PermissionError):
            self.gate.route("simulation", "simulate", "R3")

    def test_recovery_restores_route(self):
        self.vx.isolate("test")
        self.vx.recover("2026-10-07T00:00:00Z")
        route = self.gate.route("verification", "verify", "R4")
        self.assertEqual(route["decision"], "ROUTE")


if __name__ == "__main__":
    unittest.main()
