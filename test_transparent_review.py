import base64,copy,io,unittest,zipfile
from unittest.mock import patch
import server as s
class TransparentReview(unittest.TestCase):
    def test_continue_with_flagged_outcome_and_ambiguous_metric(self):
        p=s.process('demo',{})['project']
        for f in p['facts']:
            if 'outcome' in s.story_roles(f): f.update(needs_review=True,review_reason='Meaning requires review')
        p['facts'][4]['period']=''
        info=s.review_summary(p)
        p=s.process('verify',{'project':p,'confirm_ids':info['quick_confirm_ids']})['project']
        self.assertIn('outcome',p['plan']['evidence_gaps']);self.assertNotIn('F5',p['plan']['selected']);self.assertNotIn('F6',p['plan']['selected'])
        self.assertTrue(p['review_choice']['unresolved_ids'])
        p=s.process('plan',{'project':p})['project'];self.assertTrue(p['plan_approved'])
        for fmt in s.SECTIONS:
            p['format']=fmt
            sections=[{'name':n,'text':'[Approved CTA pending]' if n=='CTA' else '[Evidence pending: '+n+']','fact_ids':[]} for n in s.SECTIONS[fmt]]
            with patch.dict(s.os.environ,{'OPENAI_API_KEY':'placeholder'}),patch.object(s,'ai',return_value={'sections':sections}):p=s.process('generate',{'project':p})['project']
            with patch.dict(s.os.environ,{'OPENAI_API_KEY':''}):p=s.process('validate',{'project':p})['project']
            self.assertEqual(p['drafts'][fmt]['validation']['status'],'Blocked')
            p=s.process('edit',{'project':p})['project'];self.assertIsNone(p['drafts'][fmt]['validation'])
            p=s.process('save',{'project':p})['project']
    def test_offline_partial_sample_can_continue_without_resolving_metric(self):
        p=s.process('demo',{})['project'];p['facts'][4]['period']=''
        p=s.process('verify',{'project':p,'confirm_ids':s.review_summary(p)['quick_confirm_ids']})['project']
        self.assertEqual(p['facts'][0]['confirmation']['method'],'accepted_available_intake')
        p=s.process('plan',{'project':p})['project']
        with patch.dict(s.os.environ,{'OPENAI_API_KEY':''}):
            for fmt in s.SECTIONS:
                p['format']=fmt;p=s.process('generate',{'project':p})['project']
                d=p['drafts'][fmt];self.assertEqual(d['engine'],'Fictional evidence outline — no model')
                self.assertNotIn('24%',str(d));self.assertNotIn('F5',[fid for x in d['sections'] for fid in x['fact_ids']])
    def test_no_usable_facts_still_moves_to_editable_placeholder_draft(self):
        p=s.new_project();p['facts']=[s.fact(0,'restricted','Do not use this','Intake')]
        p=s.process('verify',{'project':p,'confirm_ids':[]})['project'];p=s.process('plan',{'project':p})['project']
        for fmt in s.SECTIONS:
            p['format']=fmt;p=s.process('generate',{'project':p})['project']
            self.assertEqual([x['name'] for x in p['drafts'][fmt]['sections']],s.SECTIONS[fmt]);self.assertNotIn('Do not use this',str(p['drafts'][fmt]))
            p=s.process('regenerate',{'project':p,'index':2})['project'];self.assertEqual(p['drafts'][fmt]['sections'][2]['name'],s.SECTIONS[fmt][2])
            with patch.dict(s.os.environ,{'OPENAI_API_KEY':''}):p=s.process('validate',{'project':p})['project']
            self.assertEqual(p['drafts'][fmt]['validation']['status'],'Blocked')
            with self.assertRaises(ValueError):s.process('review',{'project':p})
    def test_metric_result_counts_as_outcome_but_baseline_and_target_do_not(self):
        f=s.fact(0,'metric','Review time fell by 24% over six months.','Intake')
        self.assertIn('outcome',s.story_roles(f))
        f['metric_role']='baseline';self.assertNotIn('outcome',s.story_roles(f))
        f['metric_role']='unknown';f['wording']='Review time is expected to be reduced by 24%.';self.assertNotIn('outcome',s.story_roles(f))
    def test_extraction_accepts_semantic_category_names_with_real_passages(self):
        text='Previously the team reconciled reports manually. They introduced a shared workflow. Review time fell by 24% over six months compared with the prior six-month period.'
        buf=io.BytesIO()
        with zipfile.ZipFile(buf,'w') as z:z.writestr('word/document.xml','<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>'+text+'</w:t></w:r></w:p></w:body></w:document>')
        candidates=[{'category':'pain points','wording':'Previously the team reconciled reports manually.','passage':'Previously the team reconciled reports manually.'},{'category':'implementation','wording':'They introduced a shared workflow.','passage':'They introduced a shared workflow.'},{'category':'key metrics','story_roles':['impact'],'metric_role':'result','wording':text.split('. ')[2],'passage':text.split('. ')[2],'value':'24','unit':'%','period':'six months','comparison':'prior six-month period'}]
        with patch.dict(s.os.environ,{'OPENAI_API_KEY':'placeholder'}),patch.object(s,'ai',return_value={'facts':candidates}):p=s.process('upload',{'name':'fictional.docx','data':base64.b64encode(buf.getvalue()).decode()})['project']
        self.assertEqual([f['category'] for f in p['facts']],['challenge','solution','metric'])
        p=s.process('verify',{'project':p,'confirm_ids':s.review_summary(p)['quick_confirm_ids']})['project'];self.assertEqual(p['plan']['evidence_gaps'],[])
        self.assertIn('F3',p['plan']['selected'])
    def test_fallback_uses_verbatim_nonnumeric_source_without_invented_confirmation(self):
        p=s.new_project();p['raw']='People reconciled records manually.';p['manual_review_required']=True
        p['facts']=[s.fact(0,'context',p['raw'],'Intake')];p['facts'][0]['source_excerpt']=True
        info=s.review_summary(p);self.assertEqual(info['quick_confirm_ids'],['F1'])
        p['facts'][0]['wording']='An unsupported interpretation';self.assertEqual(s.review_summary(p)['quick_confirm_ids'],[])
if __name__=='__main__':unittest.main(verbosity=2)
