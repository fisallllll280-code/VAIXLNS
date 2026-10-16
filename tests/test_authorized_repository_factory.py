import unittest
from pathlib import Path
from unittest.mock import Mock
from scripts.create_authorized_repository import provision, validate_target

MANIFEST={"owner":"example-owner","policy":{"default_visibility":"private"},"repositories":[
 {"name":"VAIXLNS-innovation-factory","role":"FACTORY","system_family":"Innovation","auto_create":True,"description":"Innovation factory"},
 {"name":"unapproved","role":"OTHER","auto_create":False}
]}

class AuthorizedRepositoryFactoryTests(unittest.TestCase):
    def test_only_manifest_target_is_allowed(self):
        self.assertEqual(validate_target("VAIXLNS-innovation-factory",MANIFEST)["role"],"FACTORY")
        with self.assertRaises(ValueError): validate_target("random-repo",MANIFEST)
        with self.assertRaises(ValueError): validate_target("unapproved",MANIFEST)
    def test_existing_repository_is_never_mutated(self):
        api=Mock(return_value={"name":"VAIXLNS-innovation-factory"})
        result=provision("VAIXLNS-innovation-factory",MANIFEST,"token",Path("."),api)
        self.assertEqual(result["status"],"EXISTS_NO_MUTATION")
        self.assertEqual(api.call_count,1)
        api.assert_called_once_with("GET","/repos/example-owner/VAIXLNS-innovation-factory","token")
    def test_missing_token_fails_before_api_call(self):
        api=Mock()
        with self.assertRaises(ValueError): provision("VAIXLNS-innovation-factory",MANIFEST,"",Path("."),api)
        api.assert_not_called()
    def test_creation_seeds_only_after_manifest_authorization(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); p=root/"registry/repository-orchestration"; p.mkdir(parents=True)
            (p/"VAIXLNS_REPOSITORY_CONTRACT.md").write_text("# Contract",encoding="utf-8")
            api=Mock(side_effect=[{"_status":404},{"html_url":"https://github.com/example-owner/VAIXLNS-innovation-factory"}, {}, {}, {}, {}])
            result=provision("VAIXLNS-innovation-factory",MANIFEST,"token",root,api)
            self.assertEqual(result["status"],"CREATED_AND_SEEDED")
            self.assertEqual(len(result["files_seeded"]),4)
            self.assertEqual(api.call_count,6)
            self.assertEqual(api.call_args_list[1].args[0],"POST")
    def test_invalid_target_is_rejected_before_api_call(self):
        api=Mock()
        with self.assertRaises(ValueError): provision("random-repo",MANIFEST,"token",Path("."),api)
        api.assert_not_called()

if __name__=="__main__": unittest.main()
