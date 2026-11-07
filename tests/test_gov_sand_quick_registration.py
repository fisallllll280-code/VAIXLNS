from pathlib import Path
import unittest
HTML=(Path(__file__).resolve().parents[1]/"web/gov-sand-quick-registration/index.html").read_text(encoding="utf-8")
class QuickRegistrationTests(unittest.TestCase):
 def test_three_agencies(self):
  for x in ("eatizaz.mod.gov.sa","supplier.mod.gov.sa","monshaat.gov.sa"):
   self.assertIn(x,HTML)
 def test_user_must_confirm(self):
  self.assertIn('id="authority"',HTML)
  self.assertIn('el("authority").checked',HTML)
 def test_privacy_and_no_automated_submissions(self):
  for x in ("fetch(","XMLHttpRequest","localStorage","sessionStorage"):
   self.assertNotIn(x,HTML)
  self.assertIn("مسودة غير مقدمة",HTML)
 def test_export(self):
  self.assertIn("navigator.clipboard.writeText",HTML)
  self.assertIn("application-draft.txt",HTML)
if __name__=="__main__":unittest.main()
