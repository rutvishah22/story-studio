import copy,unittest
from unittest.mock import patch
import server as s
from sample_narrative import SAMPLE_DRAFTS
class Writing(unittest.TestCase):
    def project(self):
        p=s.process('demo',{})['project']
        p=s.process('verify',{'project':p,'confirm_ids':s.review_summary(p)['quick_confirm_ids']})['project']
        return s.process('plan',{'project':p})['project']
    def test_configured_sample_uses_model_and_business_brief(self):
        p=self.project()
        with patch.dict(s.os.environ,{'OPENAI_API_KEY':'placeholder'}),patch.object(s,'ai',return_value={'sections':copy.deepcopy(SAMPLE_DRAFTS['Case Study'])}) as model:
            d=s.draft(p,'Case Study');self.assertEqual(d['engine'],'AI-written fictional sample')
            prompt=model.call_args.args[0]
            for rule in ['Fortune 500 C-suite','The Solution','medium-length','British English','380','select evidence','fact_ids']:
                self.assertIn(rule.casefold(),prompt.casefold())
            self.assertNotIn('Violet Lantern',prompt)
            self.assertGreater(sum(len(x['text'].split()) for x in d['sections']),350)
    def test_natural_metric_paraphrase_and_tampering(self):
        with patch.dict(s.os.environ,{'OPENAI_API_KEY':''}):
            p=self.project();d=s.draft(p,'Case Study')
            metrics=next(x for x in d['sections'] if x['name']=='Key Metrics')
            metrics['text']='Over six months, review time decreased by 24% relative to the prior six-month period.'
            d['sections'][0].update(text='How a shared workflow reduced exception review time',fact_ids=['F5'])
            self.assertNotEqual(metrics['text'],p['facts'][4]['wording'])
            self.assertFalse(any(f['check']=='Metrics' for f in s.validate(p,'Case Study',d)['findings']))
            for old,new in [('24%','42%'),('six months','three months'),('prior six-month period','last month')]:
                bad=copy.deepcopy(d);next(x for x in bad['sections'] if x['name']=='Key Metrics')['text']=metrics['text'].replace(old,new)
                self.assertEqual(s.validate(p,'Case Study',bad)['status'],'Blocked')
            bad=copy.deepcopy(d);bad['sections'][0].update(text='Review time fell by a quarter',fact_ids=[])
            self.assertEqual(s.validate(p,'Case Study',bad)['status'],'Blocked')
    def test_section_rewrite_preserves_other_sections_and_requires_revalidation(self):
        with patch.dict(s.os.environ,{'OPENAI_API_KEY':''}):
            p=self.project();p=s.process('generate',{'project':p})['project']
            p=s.process('validate',{'project':p})['project'];before=copy.deepcopy(p['drafts']['Case Study'])
        section=copy.deepcopy(SAMPLE_DRAFTS['Case Study'][5]);section['text']+='\n\nDispatcher decisions remain part of the review workflow.'
        with patch.dict(s.os.environ,{'OPENAI_API_KEY':'placeholder'}),patch.object(s,'ai',return_value={'sections':[section]+copy.deepcopy(SAMPLE_DRAFTS['Case Study'][:5])+copy.deepcopy(SAMPLE_DRAFTS['Case Study'][6:])}) as model:
            p=s.process('regenerate',{'project':p,'index':5})['project']
        after=p['drafts']['Case Study'];self.assertIsNone(after['validation']);self.assertEqual(after['revision'],before['revision']+1)
        self.assertEqual(after['sections'][:5],before['sections'][:5]);self.assertEqual(after['sections'][6:],before['sections'][6:])
        self.assertIn('Rewrite only the requested section',model.call_args.args[0])
    def test_array_response_and_refinement_failure(self):
        p=self.project()
        with patch.dict(s.os.environ,{'OPENAI_API_KEY':'placeholder'}),patch.object(s,'ai',return_value=copy.deepcopy(SAMPLE_DRAFTS['One-Pager'])):
            d=s.draft(p,'One-Pager');self.assertEqual(len(d['sections']),7)
        first=copy.deepcopy(SAMPLE_DRAFTS['Case Study']);first[5]['text']=first[5]['text'].replace('\n\n',' ')
        with patch.dict(s.os.environ,{'OPENAI_API_KEY':'placeholder'}),patch.object(s,'ai',side_effect=[{'sections':first},ValueError('Provider busy')]):
            d=s.draft(p,'Case Study');self.assertEqual(d['sections'],first);self.assertIn('retained',d['generation_note'])
    def test_unsupported_claim_warning_blocks_approval(self):
        p=self.project()
        with patch.dict(s.os.environ,{'OPENAI_API_KEY':''}): d=s.draft(p,'Case Study')
        findings=[{'level':'warning','check':'Claims','section':'Subtext','reason':'Immediate implies speed that is not supported by the evidence.'},{'level':'warning','check':'Style','section':'Title','reason':'Headline could be more concise.'}]
        with patch.dict(s.os.environ,{'OPENAI_API_KEY':'placeholder'}),patch.object(s,'ai',return_value={'findings':findings}):v=s.validate(p,'Case Study',d)
        self.assertEqual(v['status'],'Blocked');self.assertEqual(v['findings'][-1]['level'],'warning')
    def test_sample_cannot_be_approved_as_client_material(self):
        with patch.dict(s.os.environ,{'OPENAI_API_KEY':''}):
            p=self.project();p=s.process('generate',{'project':p})['project']
        p['drafts']['Case Study']['validation']={'revision':1,'status':'Passed automated checks'}
        with self.assertRaisesRegex(ValueError,'Fictional'):s.process('review',{'project':p})
if __name__=='__main__':unittest.main(verbosity=2)
