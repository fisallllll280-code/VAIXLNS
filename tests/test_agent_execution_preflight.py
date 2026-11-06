import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.agent_execution_preflight import (  # noqa: E402
    REQUIRED_ARTIFACTS,
    REQUIRED_RUNTIME_SERVICES,
    _write_report,
    build_report,
)


def copy_preflight_inputs(target_root: Path) -> None:
    for relative in REQUIRED_ARTIFACTS:
        source = ROOT / relative
        destination = target_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


class AgentExecutionPreflightTests(unittest.TestCase):
    def _service_report(self, statuses):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            copy_preflight_inputs(root)
            path = root / "registry/vx-agents-fabric.integration.v1.json"
            manifest = json.loads(path.read_text(encoding="utf-8"))
            manifest["operational_status"].update(statuses)
            path.write_text(json.dumps(manifest), encoding="utf-8")
            return build_report(root, environ={})

    def test_pending_unknown_or_malformed_service_declaration_holds(self):
        for value in ("PENDING", "UNKNOWN", "FAILED", "DISCONNECTED", "", None, True, {}, []):
            for service in REQUIRED_RUNTIME_SERVICES:
                with self.subTest(value=value, service=service):
                    statuses = dict.fromkeys(REQUIRED_RUNTIME_SERVICES, "CONNECTED")
                    statuses[service] = value
                    report = self._service_report(statuses)
                    check = next(c for c in report["checks"] if c["check"] == "required_runtime_services")
                    self.assertEqual(check["status"], "HOLD")
                    self.assertIn("REQUIRED_RUNTIME_SERVICES_UNAVAILABLE:" + service, report["blockers"])

    def test_canonical_ledger_key_resolves_without_granting_execution(self):
        for state in ("CONNECTED", "ACTIVE", "ADMITTED"):
            with self.subTest(state=state):
                report = self._service_report(dict.fromkeys(REQUIRED_RUNTIME_SERVICES, state))
                check = next(c for c in report["checks"] if c["check"] == "required_runtime_services")
                self.assertEqual(check["status"], "PASS")
                self.assertEqual(report["status"], "HOLD")
                self.assertFalse(report["agent_execution_performed"])
                self.assertFalse(report["production_authorized"])
                self.assertEqual(report["live_provider_handshake"], "NOT_RUN")

    def test_misspelled_ledger_key_cannot_satisfy_canonical_binding(self):
        statuses = dict.fromkeys(REQUIRED_RUNTIME_SERVICES, "CONNECTED")
        statuses["durable_vaixlns_event_ledger"] = "NOT_CONNECTED"
        statuses["durable_vaixl_event_ledger"] = "CONNECTED"
        report = self._service_report(statuses)
        self.assertIn("REQUIRED_RUNTIME_SERVICES_UNAVAILABLE:durable_vaixlns_event_ledger", report["blockers"])

    def test_current_canonical_state_holds_without_admitted_runtime(self):
        report = build_report(ROOT, environ={})
        self.assertEqual(report["status"], "HOLD")
        self.assertFalse(report["agent_execution_performed"])
        self.assertFalse(report["canonical_mutation_performed"])
        self.assertFalse(report["production_authorized"])
        self.assertIn("RUNTIME_ROLE_BINDINGS_NOT_ADMITTED", report["blockers"])
        self.assertIn("VX_RUNTIME_PROFILES_NOT_ADMITTED", report["blockers"])
        self.assertIn("EXTERNAL_INTEGRATION_GATE_NOT_ADMITTED", report["blockers"])
        self.assertEqual(report["live_provider_handshake"], "NOT_RUN")

    def test_report_identity_is_stable_for_same_inputs(self):
        first = build_report(ROOT, environ={})
        second = build_report(ROOT, environ={})
        self.assertEqual(first["report_id"], second["report_id"])
        self.assertEqual(first["artifact_sha256"], second["artifact_sha256"])

    def test_secret_values_are_never_written_to_report(self):
        secret = "DO_NOT_EMIT_TEST_PROVIDER_SECRET_8391"
        report = build_report(ROOT, environ={
            "VX_OPENAI_COMPAT_BASE_URL": "https://private.example/" + secret,
            "VX_OPENAI_COMPAT_API_KEY": secret,
        })
        rendered = json.dumps(report, ensure_ascii=False)
        self.assertNotIn(secret, rendered)
        self.assertTrue(report["environment_summary"]["openai_compatible_api_key_present"])

    def test_broken_authority_boundary_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            copy_preflight_inputs(fixture_root)
            binding_path = fixture_root / "registry/vx-runtime-role-binding-map.v1.json"
            binding = json.loads(binding_path.read_text(encoding="utf-8"))
            binding["invariants"]["direct_agent_tool_calls_allowed"] = True
            binding_path.write_text(
                json.dumps(binding, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                encoding="utf-8",
            )

            report = build_report(fixture_root, environ={})
            self.assertEqual(report["status"], "REJECT")
            self.assertIn("RUNTIME_BINDING_MAP_INVARIANT_FAILED", report["hard_errors"])

    def test_canonical_output_target_is_protected(self):
        report = build_report(ROOT, environ={})
        with self.assertRaisesRegex(ValueError, "MUST_NOT_OVERWRITE_CANONICAL_ARTIFACT"):
            _write_report(str(ROOT / "project.genome"), report, ROOT)

    def test_preflight_only_reports_presence_not_live_connectivity(self):
        report = build_report(ROOT, environ={
            "VX_OPENAI_COMPAT_BASE_URL": "http://127.0.0.1:11434/v1",
            "VX_RESEARCH_MODEL": "local-research-model",
            "VX_FINANCE_MODEL": "local-finance-model",
            "VX_ENGINEERING_MODEL": "local-engineering-model",
            "VX_GOVERNANCE_MODEL": "local-governance-model",
            "VX_MIND_MODEL_MIND_SYS_ARCH": "review-architecture",
            "VX_MIND_MODEL_MIND_RESEARCH": "review-research",
            "VX_MIND_MODEL_MIND_FINANCE": "review-finance",
            "VX_MIND_MODEL_MIND_SECURITY": "review-security",
            "VX_MIND_MODEL_MIND_PROOF": "review-proof",
        })
        self.assertEqual(report["live_provider_handshake"], "NOT_RUN")
        self.assertFalse(report["agent_execution_performed"])
        self.assertEqual(report["status"], "HOLD")


if __name__ == "__main__":
    unittest.main()
