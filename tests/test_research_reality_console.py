import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
HTML_PATH = ROOT / "web/research-reality-console/index.html"
DATA_PATH = ROOT / "web/research-reality-console/research-status.json"
DOC_PATH = ROOT / "docs/ui/VAIXLNS_RESEARCH_REALITY_CONSOLE_V1.md"


class ResearchRealityConsoleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = HTML_PATH.read_text(encoding="utf-8")
        cls.data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
        cls.docs = DOC_PATH.read_text(encoding="utf-8")

    def test_dashboard_sections_and_navigation_exist(self):
        for view in ("overview", "pipeline", "research", "assurance"):
            self.assertIn(f'id="{view}"', self.html)
            self.assertIn(f'data-view="{view}"', self.html)

    def test_active_undermind_searches_are_exactly_identified(self):
        titles = {item["title"] for item in self.data["active_searches"]}
        self.assertEqual(len(titles), 1)
        self.assertIn("Foundations of Intent-to-Reality Computing and Governed State Evolution 2026", titles)
        for item in self.data["active_searches"]:
            self.assertEqual(item["state"], "IN_PROGRESS")
            self.assertTrue(item["url"].startswith("https://app.undermind.ai/projects/"))

    def test_provider_snapshot_is_not_misrepresented_as_live(self):
        self.assertEqual(self.data["live_connection"]["state"], "NOT_CONNECTED")
        self.assertIn("not live polling", self.data["live_connection"]["explanation"])
        self.assertIn("Snapshot وليس اتصالاً حياً", self.html)
        self.assertIn("لا توجد مزامنة API مباشرة", self.html)

    def test_full_lifecycle_and_assurance_invariants_are_present(self):
        self.assertEqual(len(self.data["lifecycle"]), 17)
        self.assertEqual(len(self.data["layers"]), 9)
        self.assertTrue(self.data["assurance"]["confidence_is_not_proof"])
        self.assertTrue(self.data["assurance"]["simulation_is_not_physical_validation"])
        self.assertTrue(self.data["assurance"]["no_self_approval"])
        self.assertIn("UNKNOWN ≠ VERIFIED", self.docs)

    def test_workspace_identity_and_links_are_present(self):
        self.assertEqual(self.data["workspace"]["workspace_id"], "0d9eabfb-e9d8-49fc-aab5-a0383a9110ce")
        self.assertEqual(self.data["workspace"]["files"], 149)
        self.assertEqual(self.data["workspace"]["deep_searches"], 47)
        self.assertIn("https://app.undermind.ai/projects/", self.data["workspace"]["web_url"])

    def test_client_has_no_embedded_provider_credentials(self):
        forbidden = ("api_key", "access_token", "client_secret", "Bearer ")
        for marker in forbidden:
            self.assertNotIn(marker, self.html)
            self.assertNotIn(marker, json.dumps(self.data))

    def test_refresh_is_local_snapshot_only(self):
        self.assertIn('fetch("./research-status.json', self.html)
        self.assertIn("LOCAL SNAPSHOT", self.html)
        self.assertIn("لا ينفذ طلباً إلى مزود البحث", self.html)


if __name__ == "__main__":
    unittest.main()
