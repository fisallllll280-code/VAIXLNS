import importlib.util
import json
import tempfile
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.request import urlopen

from va.genesis import build_system, verify_build


class VAGenesisTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def build(self, name="sample-system", intent="Create a project tracker with user roles"):
        return build_system(intent, name=name, output_dir=self.root / "out")

    def test_build_creates_four_operational_copies(self):
        result = self.build()
        self.assertEqual(
            [copy["role"] for copy in result["operational_copies"]],
            ["development", "validation", "release", "production"],
        )
        self.assertTrue((Path(result["path"]) / "system" / "app.py").is_file())

    def test_structural_verifier_passes_without_claiming_runtime(self):
        result = self.build()
        report = verify_build(result["path"])
        self.assertEqual(report["status"], "STRUCTURAL_PASS_RUNTIME_NOT_RUN")
        self.assertEqual(report["runtime_execution"], "NOT_RUN")
        self.assertFalse(report["execution_authorization"])
        self.assertEqual(report["checks_passed"], report["checks_total"])

    def test_operational_copies_have_identical_project_hashes(self):
        result = self.build()
        hashes = []
        for item in result["operational_copies"]:
            manifest = json.loads((Path(item["path"]) / "COPY_MANIFEST.json").read_text(encoding="utf-8"))
            hashes.append(manifest["project_hash"])
            self.assertFalse(manifest["execution_authorization"])
            self.assertEqual(manifest["production_admission"], "BLOCKED_UNTIL_EVIDENCE_AND_APPROVAL")
        self.assertEqual(len(set(hashes)), 1)

    def test_all_operational_copies_serve_real_http_health_and_info(self):
        result = self.build(name="runtime-smoke")
        root = Path(result["path"])
        for role in ("development", "validation", "release", "production"):
            with self.subTest(role=role):
                app_path = root / "operational-copies" / role / "app.py"
                module_spec = importlib.util.spec_from_file_location("va_generated_" + role, app_path)
                self.assertIsNotNone(module_spec)
                self.assertIsNotNone(module_spec.loader)
                module = importlib.util.module_from_spec(module_spec)
                module_spec.loader.exec_module(module)
                server = ThreadingHTTPServer(("127.0.0.1", 0), module.Handler)
                thread = Thread(target=server.serve_forever, daemon=True)
                thread.start()
                base_url = "http://127.0.0.1:%d" % server.server_address[1]
                try:
                    with urlopen(base_url + "/health", timeout=3) as response:
                        health = json.loads(response.read().decode("utf-8"))
                        self.assertEqual(response.status, 200)
                        self.assertEqual(health["status"], "ok")
                        self.assertEqual(health["system_id"], result["system_id"])
                    with urlopen(base_url + "/info", timeout=3) as response:
                        info = json.loads(response.read().decode("utf-8"))
                        self.assertEqual(response.status, 200)
                        self.assertEqual(info["name"], result["name"])
                finally:
                    server.shutdown()
                    server.server_close()
                    thread.join(timeout=3)

    def test_tampering_is_detected(self):
        result = self.build()
        app = Path(result["path"]) / "system" / "app.py"
        app.write_text(app.read_text(encoding="utf-8") + "\n# tampered\n", encoding="utf-8")
        report = verify_build(result["path"], write_report=False)
        self.assertEqual(report["status"], "STRUCTURAL_FAILURE")
        failed = {check["check"] for check in report["checks"] if not check["passed"]}
        self.assertIn("source_file_hashes", failed)

    def test_intent_is_data_not_embedded_in_executable_source(self):
        intent = 'Create a system; __import__("os").system("echo unsafe")'
        result = self.build(name="safe-prompt", intent=intent)
        app_source = (Path(result["path"]) / "system" / "app.py").read_text(encoding="utf-8")
        spec = json.loads((Path(result["path"]) / "system" / "system.json").read_text(encoding="utf-8"))
        self.assertNotIn(intent, app_source)
        self.assertEqual(spec["intent"], intent)

    def test_arabic_intent_builds_without_explicit_name(self):
        result = build_system("أنشئ نظامًا لإدارة المشاريع", output_dir=self.root / "arabic")
        self.assertTrue(result["name"].startswith("va-system-"))
        self.assertEqual(verify_build(result["path"])["status"], "STRUCTURAL_PASS_RUNTIME_NOT_RUN")

    def test_empty_intent_is_rejected(self):
        with self.assertRaises(ValueError):
            build_system("   ", output_dir=self.root / "out")

    def test_unsafe_empty_name_is_rejected(self):
        with self.assertRaises(ValueError):
            build_system("do the thing", name="🔥", output_dir=self.root / "out")

    def test_duplicate_target_is_not_overwritten(self):
        self.build()
        with self.assertRaises(FileExistsError):
            self.build()

    def test_production_copy_is_blocked_by_default(self):
        result = self.build()
        manifest = json.loads(
            (Path(result["path"]) / "operational-copies" / "production" / "COPY_MANIFEST.json")
            .read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["status"], "PROMOTION_BLOCKED")
        self.assertEqual(manifest["runtime_smoke_test"], "NOT_RUN")


if __name__ == "__main__":
    unittest.main()
