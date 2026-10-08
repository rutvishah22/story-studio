import unittest,copy
from unittest.mock import patch
from story_policy import scope_findings,approved_cta
from intake_mapper import map_intake
import server as s
from sample_narrative import SAMPLE_DRAFTS

class Structure(unittest.TestCase):
    def test_employee_scope_cannot_become_catalogue(self):
        p={'facts':[{'field':'Employee count','wording':'400-650 (source)'}]}
        self.assertTrue(scope_findings('The catalogue spans 400–650 SKUs.',p))
        self.assertFalse(scope_findings('The client employs 400–650 employees and manages 31,000 SKUs.',p))
    def test_before_description_is_provenance_not_forced_prose(self):
        d={'blocks':[{'text':'04 RESULTS','location':'Page 1'},{'text':'METRIC','cells':['METRIC','WHAT TO ENTER','BEFORE','AFTER'],'location':'Page 1'},{'text':'Search time | time | Users spent 8 hours/week searching manuals. | 65% reduction to approximately 2.8 hours/week','cells':['Search time','time','Users spent 8 hours/week searching manuals.','65% reduction to approximately 2.8 hours/week'],'location':'Page 1'}]}
        f=map_intake(d)['facts'][0];self.assertEqual(f['comparison'],'8 hours/week');self.assertIn('searching manuals',f['baseline_description'])
        self.assertEqual(s.normalise_detail('8 h/week'),s.normalise_detail(f['comparison']))
        self.assertEqual(s.normalise_detail('monthly'),s.normalise_detail('/month'))
    def test_cta_is_approved_invitation_not_new_factual_claim(self):
        p={'facts':[{'status':'confirmed','wording':'We deployed BPA 4.0 Product Genius for SKU search.'}]}
        t=approved_cta(p);self.assertIn('Still relying on manual searches',t);self.assertIn('Explore Product Identification',t);self.assertNotIn('%',t)
        p['facts'][0]['restriction']='Excluded';self.assertNotIn('Product Genius',approved_cta(p))
    def test_field_labels_and_opening_contract_reach_both_formats(self):
        p=s.process('demo',{})['project'];p['facts'][0]['field']='Company name';p['facts'][1]['field']='Use case'
        p=s.process('verify',{'project':p,'confirm_ids':s.review_summary(p)['quick_confirm_ids']})['project'];p=s.process('plan',{'project':p})['project']
        for fmt in s.SECTIONS:
            with patch.dict(s.os.environ,{'OPENAI_API_KEY':'placeholder'}),patch.object(s,'ai',return_value={'sections':copy.deepcopy(SAMPLE_DRAFTS[fmt])}) as model:s.draft(p,fmt)
            prompt=model.call_args.args[0];self.assertIn('OPENING CONTRACT',prompt);self.assertIn('Company name',prompt);self.assertIn('employees are not SKUs',prompt);self.assertIn('baseline_description is provenance',prompt)

if __name__=='__main__':unittest.main()
