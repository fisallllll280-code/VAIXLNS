import unittest

from scripts.vaixl_language_vault import (
    build_lock_manifest,
    subject_binding,
    unlock_proof,
    verify_lock_manifest,
)


class PrivateLanguageVaultTests(unittest.TestCase):
    def test_binding_is_deterministic_without_persisting_raw_values(self):
        a = subject_binding("SYNTHETIC-ID-001", "SYNTHETIC-PHONE-001", "binding-secret")
        b = subject_binding("SYNTHETIC-ID-001", "SYNTHETIC-PHONE-001", "binding-secret")
        self.assertEqual(a, b)
        self.assertEqual(len(a), 64)

    def test_manifest_is_sanitized(self):
        binding = subject_binding("SYNTHETIC-ID-001", "SYNTHETIC-PHONE-001", "binding-secret")
        proof = unlock_proof(binding, "synthetic-unlock", "proof-secret")
        manifest = build_lock_manifest(
            ["VAIXLNS-VSL-PRIVATE", "VAIXLNS-PATTERN-PRIVATE"],
            "vault://vaixlns/private-languages",
            binding,
            proof,
        )
        rendered = str(manifest)
        self.assertNotIn("SYNTHETIC-ID-001", rendered)
        self.assertNotIn("SYNTHETIC-PHONE-001", rendered)
        self.assertNotIn("synthetic-unlock", rendered)
        self.assertFalse(manifest["privacy"]["repository_contains_raw_identity"])
        self.assertFalse(manifest["privacy"]["repository_contains_raw_phone"])
        self.assertFalse(manifest["privacy"]["repository_contains_unlock_code"])

    def test_correct_subject_and_code_verify(self):
        binding = subject_binding("SYNTHETIC-ID-002", "SYNTHETIC-PHONE-002", "binding-secret")
        proof = unlock_proof(binding, "synthetic-unlock-2", "proof-secret")
        manifest = build_lock_manifest(["VAIXLNS-PRIVATE"], "vault://vaixlns/private", binding, proof)
        self.assertTrue(verify_lock_manifest(manifest, binding, "synthetic-unlock-2", "proof-secret"))
        self.assertFalse(verify_lock_manifest(manifest, binding, "wrong-code", "proof-secret"))


if __name__ == "__main__":
    unittest.main()
