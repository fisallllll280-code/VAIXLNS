import unittest
from scripts.vx_launch_candidates import shortlist
from scripts.vx_model_catalog_gate import select_models
SHA='a'*40
class LaunchTests(unittest.TestCase):
    def test_shortlist(self):
        got=shortlist({'items':[{'canonical_id':'A','name':'Proof verification','source_refs':['docs/a.md'],'status':'PROPOSAL'}]},source_revision=SHA)
        self.assertEqual(got['shortlist'][0]['success_probability'],None)
        self.assertFalse(got['automatic_publication'])
    def test_absent_source_excluded(self):
        self.assertEqual(shortlist({'items':[{'canonical_id':'A','name':'Proof','source_refs':[]}]},source_revision=SHA)['candidate_count'],0)
    def test_revision_required(self):
        with self.assertRaises(ValueError):shortlist({'items':[]},source_revision='main')
    def test_no_fake_probability(self):
        row=shortlist({'items':[{'canonical_id':'A','name':'Finance exchange','source_refs':['docs/x']} ]},source_revision=SHA)['shortlist'][0]
        self.assertEqual(row['market_demand'],'UNKNOWN')
    def test_duplicate_ids(self):
        items=[{'canonical_id':'A','name':'Agent','source_refs':['docs/x']}]*2
        self.assertEqual(shortlist({'items':items},source_revision=SHA)['candidate_count'],1)
    def test_empty_catalog(self):
        with self.assertRaises(ValueError):shortlist([],source_revision=SHA)
    def test_zero_cost_verified_fixture(self):
        c={'models':[{'id':'local/one','provider':'local','verified_connection':True,'capabilities':['coding'],'price_input_sar':0,'price_output_sar':0,'request_fee_sar':0,'quota_verified':True}]}
        self.assertEqual(select_models(c,required_capability='coding',allow_providers={'local'})['eligible_models'],['local/one'])
    def test_unknown_price_denied(self):
        c={'models':[{'id':'p/a','provider':'p','verified_connection':True,'capabilities':['coding'],'price_input_sar':None,'price_output_sar':0,'request_fee_sar':0,'quota_verified':True}]}
        self.assertEqual(select_models(c,required_capability='coding',allow_providers={'p'})['held_models'][0]['reason'],'NONZERO_OR_UNKNOWN_COST')
    def test_paid_price_denied(self):
        c={'models':[{'id':'p/a','provider':'p','verified_connection':True,'capabilities':['coding'],'price_input_sar':'0.01','price_output_sar':0,'request_fee_sar':0,'quota_verified':True}]}
        self.assertEqual(select_models(c,required_capability='coding',allow_providers={'p'})['eligible_models'],[])
    def test_unverified_connection_denied(self):
        c={'models':[{'id':'p/a','provider':'p','verified_connection':False,'capabilities':['coding'],'price_input_sar':0,'price_output_sar':0,'request_fee_sar':0,'quota_verified':True}]}
        self.assertEqual(select_models(c,required_capability='coding',allow_providers={'p'})['held_models'][0]['reason'],'CONNECTION_NOT_VERIFIED')
    def test_unknown_provider_denied(self):
        c={'models':[{'id':'evil/a','provider':'evil'}]}
        self.assertEqual(select_models(c,required_capability='coding',allow_providers={'p'})['eligible_models'],[])
    def test_quota_unverified_denied(self):
        c={'models':[{'id':'p/a','provider':'p','verified_connection':True,'capabilities':['coding'],'price_input_sar':0,'price_output_sar':0,'request_fee_sar':0,'quota_verified':False}]}
        self.assertEqual(select_models(c,required_capability='coding',allow_providers={'p'})['held_models'][0]['reason'],'QUOTA_NOT_VERIFIED')
if __name__=='__main__':unittest.main()
