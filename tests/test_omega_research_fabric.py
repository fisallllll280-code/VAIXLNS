"""Offline contract tests for the Ω research index."""
import json, tempfile, unittest
from pathlib import Path
from scripts.omega_research_fabric import db_open,index_local,local_search,record,store_evidence,remote_search,parse_results,safe_server_url,extract,inverted_abstract

class ResearchFabricTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.base=Path(self.tmp.name); self.root=self.base/"repo"; self.root.mkdir()
        (self.root/"docs").mkdir()
        (self.root/"docs"/"design.md").write_text("# VX architecture\nMUST preserve provenance and deterministic proof.\nUse incremental index and define /search endpoint.\n",encoding="utf-8")
        (self.root/"main.py").write_text("def run(): return 1\n",encoding="utf-8")
        self.dbpath=self.base/"idx.sqlite3"; self.out=self.base/"out.json"; self.db=db_open(self.dbpath)
    def tearDown(self): self.db.close(); self.tmp.cleanup()
    def test_first_index_and_local_search_extract_evidence(self):
        summary=index_local(self.root,self.db,self.dbpath,self.out); found=local_search(self.db,"provenance deterministic",10)
        self.assertEqual(summary["changed"],2); self.assertEqual(len(found),1)
        self.assertIn("VX",found[0]["system_refs"]); self.assertIn("PROOF_OR_PROVENANCE",found[0]["engineering_signals"])
        self.assertEqual(len(found[0]["sha256"]),64)
    def test_incremental_index_skips_unchanged_content(self):
        index_local(self.root,self.db,self.dbpath,self.out); second=index_local(self.root,self.db,self.dbpath,self.out)
        self.assertEqual(second["changed"],0); self.assertEqual(second["unchanged"],2)
    def test_changed_and_deleted_files_are_reconciled(self):
        index_local(self.root,self.db,self.dbpath,self.out); (self.root/"main.py").write_text("changed = True\n")
        changed=index_local(self.root,self.db,self.dbpath,self.out); self.assertEqual(changed["changed"],1)
        (self.root/"main.py").unlink(); removed=index_local(self.root,self.db,self.dbpath,self.out); self.assertEqual(removed["removed"],1)
    def test_remote_record_is_unverified_and_searchable(self):
        item=record("fixture","DOI-1","Sovereign proof fabric","https://example.org/item","deep engineering proof")
        store_evidence(self.db,[item]); found=remote_search(self.db,"sovereign proof",10)
        self.assertEqual(len(found),1); self.assertEqual(found[0]["state"],"DISCOVERED_UNVERIFIED")
    def test_crossref_parser_handles_metadata_payload(self):
        raw=json.dumps({"message":{"items":[{"DOI":"10.1/example","title":["Proof systems"],"URL":"https://doi.org/10.1/example","published-print":{"date-parts":[[2025,2]]}}]}}).encode()
        item=parse_results("crossref",raw,10)[0]
        self.assertEqual(item["title"],"Proof systems"); self.assertEqual(item["published"],"2025-2")
    def test_github_parser_handles_repo_search_payload(self):
        raw=json.dumps({"items":[{"full_name":"org/engine","html_url":"https://github.com/org/engine","stargazers_count":9}]}).encode()
        item=parse_results("github",raw,10)[0]; self.assertEqual(item["source_id"],"org/engine"); self.assertEqual(item["metadata"]["stars"],9)
    def test_openalex_abstract_positions_are_reconstructed(self):
        self.assertEqual(inverted_abstract({"proof":[1],"Deep":[0],"engineering":[2]}),"Deep proof engineering")
    def test_rejects_plain_http_non_loopback_server(self):
        with self.assertRaisesRegex(ValueError,"HTTPS"): safe_server_url("http://internal.example","/health")
    def test_rejects_server_path_traversal(self):
        with self.assertRaisesRegex(ValueError,"absolute"): safe_server_url("https://example.org","/../admin")
    def test_allows_explicit_localhost_adapter(self):
        self.assertEqual(safe_server_url("http://localhost:8123","/health"),"http://localhost:8123/health")
    def test_content_hash_covers_complete_bytes(self):
        self.assertNotEqual(extract("x.md",b"same")["sha256"],extract("x.md",b"same ")["sha256"])

if __name__=="__main__": unittest.main()
