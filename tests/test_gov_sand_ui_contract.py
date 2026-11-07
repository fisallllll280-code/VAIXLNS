import pathlib
import unittest
HTML=(pathlib.Path(__file__).resolve().parents[1]/"web/gov-sand-control-center/index.html").read_text(encoding="utf-8")
class TestGovSandUIContract(unittest.TestCase):
    def test_tabs(self):
        for name in ("control","finance","indexes","sand","proof"):
            self.assertIn('id="'+name+'"',HTML)
            self.assertIn('data-tab="'+name+'"',HTML)
    def test_no_network_or_storage(self):
        for key in ("fetch(", "XMLHttpRequest", "localStorage", "sessionStorage"):
            self.assertNotIn(key,HTML)
    def test_claims_explicitly_denied(self):
        self.assertIn("0 ر.س",HTML)
        self.assertIn("غير متصل",HTML)
    def test_consent(self):
        self.assertIn('id="consent"',HTML)
        self.assertIn('consent").checked',HTML)
if __name__=="__main__":unittest.main()
