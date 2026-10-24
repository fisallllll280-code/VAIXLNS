"""Dependency-free structural checks; does not replace browser testing."""
from pathlib import Path
import unittest

SITE = Path(__file__).with_name("index.html")

class OfficialSiteSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = SITE.read_text(encoding="utf-8")

    def test_accessible_language_and_mobile_viewport(self):
        for expected in ('lang="ar"', 'dir="rtl"', 'name="viewport"', 'aria-label="Main navigation"', 'focus-visible'):
            self.assertIn(expected, self.html)

    def test_all_product_names(self):
        for name in ("VX Studio", "VAIXLNS AI", "VV OS", "Ω Reality Forge", "VAIXLNS Market", "Ω Arena"):
            with self.subTest(product=name):
                self.assertIn(name, self.html)

    def test_language_switch(self):
        self.assertIn("const dict={ar:", self.html)
        self.assertIn("en:{navProducts:", self.html)
        self.assertIn("addEventListener('click'", self.html)

    def test_no_external_script_or_unapproved_release(self):
        self.assertNotIn("<script src=", self.html)
        self.assertNotIn("api_key", self.html.lower())
        self.assertIn("No Proof = No Commit", self.html)
        self.assertIn('قيد التطوير', self.html)

if __name__ == "__main__":
    unittest.main()
