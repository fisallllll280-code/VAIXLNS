import copy
import json
import unittest
from pathlib import Path

from tools.validate_engineering_idea_fusion import load_and_validate, validate_documents

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "registry" / "federation" / "engineering_idea_fusion.v1.json"
SCHEMA_PATH = ROOT / "schemas" / "engineering-idea-fusion.v1.schema.json"


class EngineeringIdeaFusionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        cls.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    def test_checked_in_manifest_passes_source_pin_and_identity_checks(self):
        self.assertEqual(load_and_validate(ROOT), [])

    def test_supporting_artifact_links_are_revision_pinned(self):
        manifest = copy.deepcopy(self.manifest)
        manifest["supporting_artifacts"][0]["source_url"] = "https://github.com/fisallllll280-code/VX50_COMPLETE_BUILD/blob/main/docs/OMEGA_FABRIC_CONTRACT.md"
        self.assertTrue(any(x.startswith("SUPPORTING_URL_NOT_PINNED:") for x in validate_documents(manifest, self.schema)))

    def test_canonical_registry_remains_read_only(self):
        manifest = copy.deepcopy(self.manifest)
        manifest["authority"]["canonical_mutation"] = "ENABLED"
        self.assertIn(
            "CANONICAL_BOUNDARY_MISMATCH:canonical_mutation",
            validate_documents(manifest, self.schema),
        )

    def test_vlns_is_not_aliased_to_naxlns(self):
        manifest = copy.deepcopy(self.manifest)
        next(x for x in manifest["official_system_crosswalk"] if x["system_id"] == "VLNS")["repository_candidates"] = ["fisallllll280-code/NAXLNS"]
        self.assertIn("UNSUPPORTED_VLNS_NAXLNS_ALIAS", validate_documents(manifest, self.schema))

    def test_nexent_cannot_be_silently_promoted_to_nexnet(self):
        manifest = copy.deepcopy(self.manifest)
        nexnet = next(x for x in manifest["official_system_crosswalk"] if x["system_id"] == "NEXNET")
        nexnet["repository_candidates"] = ["fisallllll280-code/NEXENT"]
        self.assertIn("NEXNET_IDENTITY_CANDIDATES_REQUIRE_EVIDENCE", validate_documents(manifest, self.schema))

    def test_readme_source_link_must_be_revision_pinned(self):
        manifest = copy.deepcopy(self.manifest)
        manifest["source_repositories"][0]["source_url"] = "https://github.com/fisallllll280-code/VAIXLNS/blob/main/README.md"
        self.assertTrue(any(x.startswith("SOURCE_URL_NOT_PINNED:") for x in validate_documents(manifest, self.schema)))

    def test_recovered_formula_cannot_promote_itself_to_verified(self):
        manifest = copy.deepcopy(self.manifest)
        manifest["recovered_engineering_pipelines"][0]["state"] = "VERIFIED"
        self.assertTrue(any(x.startswith("FORMULA_STATE_MUST_NOT_PROMOTE:") for x in validate_documents(manifest, self.schema)))

    def test_duplicate_formula_identity_is_rejected(self):
        manifest = copy.deepcopy(self.manifest)
        manifest["recovered_engineering_pipelines"][1]["id"] = manifest["recovered_engineering_pipelines"][0]["id"]
        self.assertIn("DUPLICATE_FORMULA_ID", validate_documents(manifest, self.schema))

    def test_missing_source_is_rejected(self):
        manifest = copy.deepcopy(self.manifest)
        manifest["source_repositories"].pop()
        self.assertIn("SOURCE_REPOSITORY_INVENTORY_INCOMPLETE", validate_documents(manifest, self.schema))

    def test_unreviewed_state_is_not_promoted(self):
        manifest = copy.deepcopy(self.manifest)
        manifest["state"] = "VERIFIED"
        self.assertIn("FUSION_MUST_REMAIN_PROPOSAL_UNTIL_REVIEWED", validate_documents(manifest, self.schema))


if __name__ == "__main__":
    unittest.main()
