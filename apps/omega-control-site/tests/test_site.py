"""Structural smoke tests; not a browser end-to-end test."""
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
class Inspector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.tabs = []
    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if "id" in d:
            self.ids.add(d["id"])
        if "data-view" in d:
            self.tabs.append(d["data-view"])

class SiteStructureTest(unittest.TestCase):
    def test_navigation_and_sections(self):
        content = (ROOT / "index.html").read_text(encoding="utf-8")
        parsed = Inspector()
        parsed.feed(content)
        views = {"overview","agents","memory","repository","evidence","architecture"}
        self.assertEqual(set(parsed.tabs),views)
        self.assertTrue(views.issubset(parsed.ids))
        self.assertIn("api.github.com",content)
        self.assertIn("لا يوجد اتصال خادم خاص",content)
        self.assertNotIn("GITHUB_TOKEN",content)
    def test_responsive_layout(self):
        text = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("@media(max-width:720px)",text)

if __name__=="__main__":
    unittest.main()
