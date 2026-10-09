"""Tests for evidence-gated cross-system innovation integration graph."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.omega_innovation_integration import build_graph, digest


def source(items):
    return {"schema": "VAIXLNS.InnovationFederation.v1", "snapshot": "test-snapshot", "items": items}


class OmegaInnovationIntegrationTests(unittest.TestCase):
    def test_explicit_relations_resolve_without_promoting_status(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "scripts").mkdir()
            (root / "scripts" / "alpha.py").write_text("# Alpha innovation\n", encoding="utf-8")
            data = source([
                {"name": "Alpha Innovation", "family": "Index", "owner": "VAIXLNS",
                 "state": "PROPOSAL", "evidence": {"class": "SOURCE_ASSERTED", "paths": ["scripts/alpha.py"]}},
                {"name": "Beta Innovation", "family": "Search", "owner": "VX",
                 "state": "IMPLEMENTED", "derived_from": ["Alpha Innovation"]},
            ])
            graph = build_graph(data, root)
            edges = graph["edges"]
            self.assertTrue(any(e["relation"] == "DERIVED_FROM" and e["state"] == "SOURCE_DECLARED" for e in edges))
            self.assertTrue(any(e["relation"] == "EVIDENCE_PATH" and e["state"] == "PATH_EXISTS" for e in edges))
            alpha = next(n for n in graph["nodes"] if n.get("name") == "Alpha Innovation")
            self.assertEqual(alpha["source_state"], "PROPOSAL")
            self.assertEqual(graph["summary"]["innovations_promoted"], 0)
            self.assertEqual(graph["summary"]["canonical_records_mutated"], 0)

    def test_missing_paths_and_unresolved_relationships_are_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = source([{
                "name": "Orphan Capability", "family": "Unmapped", "owner": "VX",
                "state": "SOURCE-ASSERTED", "evidence": {"class": "SOURCE_ASSERTED", "paths": ["missing/file.py"]},
                "derived_from": ["Unknown Parent"], "relations": ["Unknown Partner"],
            }])
            graph = build_graph(data, root)
            types = {g["gap_type"] for g in graph["integration_gaps"]}
            self.assertIn("DECLARED_EVIDENCE_PATH_UNRESOLVED", types)
            self.assertIn("UNRESOLVED_DERIVATION_REFERENCE", types)
            self.assertIn("UNRESOLVED_RELATION_REFERENCE", types)

    def test_similar_families_create_review_candidates_not_merges(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = source([
                {"name": "Semantic Index", "family": "Canonical semantic registry engine", "owner": "VAIXLNS"},
                {"name": "Canonical Semantic Index", "family": "Semantic registry engine canonical", "owner": "VX"},
            ])
            graph = build_graph(data, root)
            self.assertTrue(any(e["relation"] in {"SIMILAR_NAME_OR_FAMILY", "POSSIBLE_DUPLICATE_NAME"} for e in graph["edges"]))
            self.assertEqual(graph["summary"]["innovations_promoted"], 0)

    def test_declared_derivation_cycle_is_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            graph = build_graph(source([
                {"name": "Alpha", "family": "One", "owner": "VAIXLNS", "derived_from": ["Beta"]},
                {"name": "Beta", "family": "Two", "owner": "VX", "derived_from": ["Alpha"]},
            ]), root)
            self.assertGreaterEqual(graph["summary"]["dependency_cycle_count"], 1)
            self.assertIn("DECLARED_DERIVATION_CYCLE", {g["gap_type"] for g in graph["integration_gaps"]})

    def test_hash_and_graph_are_deterministic(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = source([{"name": "Indexing", "family": "Knowledge", "owner": "VAIXLNS"}])
            a = build_graph(data, root)
            b = build_graph(data, root)
            self.assertEqual(a, b)
            self.assertEqual(a["graph_sha256"], digest({k: v for k, v in a.items() if k != "graph_sha256"}))

    def test_invalid_or_empty_federation_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaisesRegex(ValueError, "non-empty list"):
                build_graph({"items": []}, root)
            with self.assertRaisesRegex(ValueError, "needs name"):
                build_graph(source([{"family": "no name"}]), root)


if __name__ == "__main__":
    unittest.main()
