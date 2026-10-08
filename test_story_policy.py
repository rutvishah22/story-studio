import copy,unittest
from unittest.mock import patch
import server as s
from story_policy import publication_text,confirmation_problem
from intake_mapper import map_intake

class Policy(unittest.TestCase):
    def project(self):
        p=s.process('demo',{})['project'];p['demo']=False;p['facts'][0].update(field='Company name',wording='Fictional Private Labs',category='context',story_roles=['context'],metric_role='not_applicable')
        p=s.process('verify',{'project':p,'confirm_ids':s.review_summary(p)['quick_confirm_ids']})['project'];return s.process('plan',{'project':p})['project']
    def test_context_cannot_be_outcome(self):
        f=s.fact(0,'context','Private Labs','Source');f['metric_role']='result';self.assertNotIn('outcome',s.story_roles(f))
    def test_anonymity_and_attribution_boundary(self):
        p=self.project();self.assertEqual(publication_text('Fictional Private Labs deployed Product Genius.\\nNext paragraph.',p),'Our team deployed Product Genius.\nNext paragraph.')
        for fmt in s.SECTIONS:
            p['format']=fmt
            rows=[{'name':n,'text':'Fictional Private Labs deployed Product Genius.' if n!='CTA' else '[Approved CTA pending]','fact_ids':p['plan']['selected'] if n!='CTA' else []} for n in s.SECTIONS[fmt]]
            captured=[]
            def model(prompt,**kwargs):captured.append(prompt);return {'sections':copy.deepcopy(rows)}
            with patch.dict(s.os.environ,{'OPENAI_API_KEY':'placeholder'}),patch.object(s,'ai',side_effect=model):p=s.process('generate',{'project':p})['project']
            self.assertNotIn('Fictional Private Labs',captured[0]);self.assertNotIn('Fictional Private Labs',str(p['drafts'][fmt]))
            p['drafts'][fmt]['sections'][0]['text']='Fictional Private Labs deployed Product Genius.'
            with patch.dict(s.os.environ,{'OPENAI_API_KEY':''}):v=s.validate(p,fmt,p['drafts'][fmt])
            self.assertTrue(any(f['check']=='Anonymity' and f['level']=='block' for f in v['findings']))
    def test_confirmation_is_atomic_and_restrictions_stay_excluded(self):
        p=self.project();metric=p['facts'][4];metric['period']='';metric['status']='uncertain';p['facts'][1]['status']='uncertain'
        with self.assertRaises(ValueError):s.process('confirmFacts',{'project':p,'confirm_ids':['F2','F5']})
        self.assertEqual(p['facts'][1]['status'],'uncertain')
        with self.assertRaises(ValueError):s.process('confirmFacts',{'project':p,'confirm_ids':['F6']})
        p=s.process('confirmFacts',{'project':p,'confirm_ids':['F2']})['project'];self.assertEqual(p['facts'][1]['status'],'confirmed');self.assertFalse(p['plan_approved'])
    def test_normal_before_after_is_not_flagged_for_multiple_values(self):
        d={'blocks':[{'text':'04 RESULTS','location':'Page 1'},{'text':'METRIC | BEFORE | AFTER','cells':['METRIC','WHAT TO ENTER','BEFORE','AFTER'],'location':'Page 1'},{'text':'Rework | cycles | 20 cycles/month | 5 cycles/month','cells':['Error reduction','cycles','20 rework cycles/month','5 rework cycles/month'],'location':'Page 1'}]}
        f=map_intake(d)['facts'][0];self.assertFalse(f['needs_review']);self.assertEqual(f['unit'],'rework cycles')
    def test_conflicting_calculation_is_flagged(self):
        d={'blocks':[{'text':'04 RESULTS','location':'Page 1'},{'text':'METRIC','cells':['METRIC','WHAT TO ENTER','BEFORE','AFTER'],'location':'Page 1'},{'text':'Capacity | input | 400 search hours/month across 50 users (50 × 8 hrs/week × 4 weeks) | approximately 2.85× more requests','cells':['Capacity','input','400 search hours/month across 50 users (50 × 8 hrs/week × 4 weeks)','approximately 2.85× more requests'],'location':'Page 1'}]}
        f=map_intake(d)['facts'][0];self.assertTrue(f['calculation_conflict']);self.assertIn('1600',f['review_reason']);self.assertTrue(confirmation_problem(dict(f,status='uncertain')))

if __name__=='__main__':unittest.main()
