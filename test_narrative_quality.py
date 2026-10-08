import copy,unittest
from unittest.mock import patch
import server as s
from narrative_quality import editorial_findings
from sample_narrative import SAMPLE_DRAFTS

class Narrative(unittest.TestCase):
    def project(self):
        p=s.process('demo',{})['project'];p=s.process('verify',{'project':p,'confirm_ids':s.review_summary(p)['quick_confirm_ids']})['project'];return s.process('plan',{'project':p})['project']
    def test_numeric_headline_with_linked_context(self):
        p=self.project();d=copy.deepcopy(SAMPLE_DRAFTS['Case Study']);d[0].update(text='How We Reduced Review Time by 24%',fact_ids=['F5']);draft={'sections':d,'revision':1}
        with patch.dict(s.os.environ,{'OPENAI_API_KEY':''}):v=s.validate(p,'Case Study',draft)
        self.assertFalse(any(f['check']=='Metrics' for f in v['findings']))
        bad=copy.deepcopy(draft);bad['sections'][0]['text']='How We Reduced Review Time by 42%'
        with patch.dict(s.os.environ,{'OPENAI_API_KEY':''}):v=s.validate(p,'Case Study',bad)
        self.assertTrue(any(f['check']=='Metrics' and f['level']=='block' for f in v['findings']))
        for section in draft['sections']:
            if section['name'] not in ['Title','CTA']:section['text']='Supported nonnumeric prose.'
        with patch.dict(s.os.environ,{'OPENAI_API_KEY':''}):v=s.validate(p,'Case Study',draft)
        self.assertTrue(any('Headline metric lacks' in f['reason'] for f in v['findings']))
    def test_feature_dump_and_repetition_are_advisory(self):
        repeat='The shared workflow brings records together so reviewers can inspect evidence and decide the next action.'
        fs=editorial_findings([{'name':'Subtext','text':repeat},{'name':'The Outcome','text':repeat},{'name':'The Solution','text':'The delivery team uses BigQuery, AlloyDB and Google ADK.'}])
        self.assertTrue(any('Repeats' in reason for _,reason in fs));self.assertTrue(any('Architecture-heavy' in reason for _,reason in fs))
    def test_both_formats_apply_the_editorial_guide_and_section_rewrite(self):
        p=self.project()
        for fmt in s.SECTIONS:
            with patch.dict(s.os.environ,{'OPENAI_API_KEY':'placeholder'}),patch.object(s,'ai',return_value={'sections':copy.deepcopy(SAMPLE_DRAFTS[fmt])}) as model:
                d=s.draft(p,fmt);prompt=model.call_args.args[0]
            self.assertIn('business tension',prompt);self.assertIn('partnership voice',prompt);self.assertIn('Do not use every fact',prompt);self.assertIn('exact confirmed metrics',prompt)
            self.assertNotIn('NONNUMERIC',prompt);self.assertNotIn('nonnumeric Title/Headline',prompt)
            p['drafts'][fmt]=d;index=next(i for i,row in enumerate(d['sections']) if row['name'] in ['The Solution','Solution'])
            with patch.dict(s.os.environ,{'OPENAI_API_KEY':'placeholder'}),patch.object(s,'ai',return_value={'sections':[copy.deepcopy(d['sections'][index])]}) as model:s.draft(p,fmt,index)
            self.assertIn('Rewrite only the requested section',model.call_args.args[0])

if __name__=='__main__':unittest.main()
