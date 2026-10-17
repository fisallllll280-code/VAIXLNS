import unittest

from tools.validate_deep_innovation_register import EXPECTED_IDS, validate


VALID_REGISTER = """\
project.genome::v1.0.0
Ω0_GENESIS_CORE
counterevidence
UNKNOWN
INCONCLUSIVE
no merge or deployment is implied
does not itself mutate

## Recovery findings that govern this register
## Current engineering shortlist
## The full innovation portfolio recovered from the current master index
## Engineering readiness vocabulary
## Shortest safe execution sequence
## Non-negotiable preservation and safety gates

""" + "\n".join(f"| {item} | preserved source |" for item in EXPECTED_IDS)


class RegisterValidationTests(unittest.TestCase):
    def test_accepts_complete_inventory_and_gates(self):
        self.assertEqual(validate(VALID_REGISTER), [])

    def test_rejects_missing_portfolio_id(self):
        incomplete = VALID_REGISTER.replace("| I-042 | preserved source |", "")
        self.assertTrue(any("missing portfolio IDs: I-042" in e for e in validate(incomplete)))

    def test_rejects_missing_evidence_gate(self):
        text = VALID_REGISTER.replace("counterevidence", "")
        self.assertTrue(any("counterevidence" in e for e in validate(text)))

    def test_rejects_blanket_readiness_claim(self):
        text = VALID_REGISTER + "\nAll 97 innovations are verified.\n"
        self.assertTrue(any("unsafe blanket promotion claim" in e for e in validate(text)))


if __name__ == "__main__":
    unittest.main()
