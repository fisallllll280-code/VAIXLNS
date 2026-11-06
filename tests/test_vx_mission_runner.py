import tempfile
import unittest
from pathlib import Path

from scripts.vx_mission_runner import run_mission


class VXMissionRunnerTests(unittest.TestCase):
    def test_allowlisted_verification_mission_executes_and_emits_receipt(self):
        mission = {
            "mission_id": "VX-GATE-SELF-CHECK-001",
            "steps": [
                {"step_id": "compile", "argv": ["python", "-m", "compileall", "-q", "scripts/vx_nonregression_gate.py", "scripts/vx_mission_runner.py", "tests/test_vx_nonregression_gate.py", "tests/test_vx_mission_runner.py"], "timeout_seconds": 30},
                {"step_id": "unit-tests", "argv": ["python", "-m", "unittest", "tests.test_vx_nonregression_gate", "-v"], "timeout_seconds": 60},
            ],
        }
        report = run_mission(mission, Path.cwd())
        self.assertEqual(report["state"], "PASSED", report)
        self.assertTrue(report["execution_performed"])
        self.assertFalse(report["deployment_performed"])
        self.assertEqual(len(report["receipt_sha256"]), 64)
        self.assertTrue(all(step["state"] == "PASSED" for step in report["steps"]))

    def test_shell_command_is_rejected(self):
        report = run_mission({
            "mission_id": "BLOCK-SHELL",
            "steps": [{"step_id": "unsafe", "argv": ["python", "-c", "print('no')"]}],
        }, Path.cwd())
        self.assertEqual(report["state"], "BLOCKED")
        self.assertEqual(report["steps"][0]["error"], "COMMAND_NOT_ALLOWLISTED")
        self.assertFalse(report["execution_performed"])

    def test_path_traversal_is_rejected(self):
        report = run_mission({
            "mission_id": "BLOCK-PATH",
            "steps": [{"step_id": "compile", "argv": ["python", "-m", "compileall", "-q", "scripts/../../etc/passwd"]}],
        }, Path.cwd())
        self.assertEqual(report["state"], "BLOCKED")
        self.assertEqual(report["steps"][0]["error"], "PATH_OUTSIDE_ALLOWLIST")

    def test_duplicate_step_id_blocks_second_execution(self):
        report = run_mission({
            "mission_id": "BLOCK-DUPLICATE",
            "steps": [
                {"step_id": "same", "argv": ["python", "-m", "unittest", "tests.test_vx_nonregression_gate"]},
                {"step_id": "same", "argv": ["python", "-m", "unittest", "tests.test_vx_nonregression_gate"]},
            ],
        }, Path.cwd())
        self.assertEqual(report["state"], "BLOCKED")
        self.assertEqual(report["steps"][-1]["error"], "DUPLICATE_STEP_ID")

    def test_empty_mission_is_blocked(self):
        report = run_mission({"mission_id": "EMPTY", "steps": []}, Path.cwd())
        self.assertEqual(report["state"], "BLOCKED")
        self.assertFalse(report["execution_performed"])


if __name__ == "__main__":
    unittest.main()
