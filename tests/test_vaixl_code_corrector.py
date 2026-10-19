import unittest
from scripts.vaixl_code_corrector import correct_source

class CodeCorrectorTests(unittest.TestCase):
    def test_safe_section_alias_is_repaired(self):
        result = correct_source("SYSTEM X\nCAPABILITIES\n    READ project\n")
        self.assertTrue(result["changed"])
        self.assertIn("CAPABILITY", result["repaired_source"])
        self.assertTrue(result["replay_required"])
        self.assertTrue(result["verification_required"])

    def test_security_authority_is_never_mutated(self):
        source = "SYSTEM X\nAUTHORITY\n    PROJECT_SCOPE\nMUST_NOT\n    READ secrets\n"
        result = correct_source(source)
        self.assertFalse(result["authority_mutation"])
        self.assertFalse(result["constraint_mutation"])
        self.assertEqual(result["repaired_source"], source)

if __name__ == "__main__":
    unittest.main()
