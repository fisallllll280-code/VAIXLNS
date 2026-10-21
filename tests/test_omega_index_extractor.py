import importlib.util,pathlib,subprocess,tempfile,unittest
p=pathlib.Path(__file__).resolve().parents[1]/"tools"/"omega_index_extractor.py"
spec=importlib.util.spec_from_file_location("extractor",p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Tests(unittest.TestCase):
 def test_pinned_repeatable_no_promotion(self):
  with tempfile.TemporaryDirectory() as d:
   r=pathlib.Path(d)/"VX";r.mkdir();subprocess.run(["git","init","-q",str(r)],check=True)
   (r/"docs/indexes").mkdir(parents=True)
   (r/"docs/indexes/catalog.md").write_text("# Innovation Catalog\n1. Alpha Tool\n2. Beta Tool\n")
   subprocess.run(["git","-C",str(r),"add","."],check=True)
   subprocess.run(["git","-C",str(r),"-c","user.email=ci@example.org","-c","user.name=CI","commit","-qm","init"],check=True)
   rows,sources=m.extract([r]);again,_=m.extract([r])
   self.assertEqual(rows,again);self.assertEqual(len(rows),3);self.assertEqual(len(sources),1)
   self.assertTrue(all(x["state"]=="RECOVERED" for x in rows))
 def test_fail_closed_unpinned(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises(ValueError):m.extract([d])
if __name__=="__main__":unittest.main()
