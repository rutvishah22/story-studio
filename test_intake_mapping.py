import unittest,base64,os
from pathlib import Path
from unittest.mock import patch
import server as s
from intake_mapper import map_intake

class Mapping(unittest.TestCase):
    def test_page_continuation_and_examples(self):
        d={'blocks':[{'kind':'table_row','text':'What We Built Example: imaginary robot | Shared queue reviews incoming records.','cells':['What We Built Example: imaginary robot','Shared queue reviews incoming records.'],'location':'Page 1'}, {'kind':'table_row','text':' | Analysts check the source and assign owners.','cells':['','Analysts check the source and assign owners.'],'location':'Page 2'}, {'kind':'table_row','text':'Client Quote | ','cells':['Client Quote',''],'location':'Page 2'}]}
        m=map_intake(d);self.assertEqual(len(m['facts']),1);f=m['facts'][0]
        self.assertIn('assign owners',f['wording']);self.assertNotIn('imaginary',f['wording']);self.assertIn('Page 2',f['location'])
    def test_plain_questions_answers_and_restrictions(self):
        texts=['Company Name: Fictional Iris Labs','Core Pain Point','Analysts compared separate reports manually.','What We Built','A shared review queue groups incoming reports.','Usage restrictions: Never publish internal codename Orion.']
        d={'blocks':[{'text':t,'kind':'paragraph','location':'Word paragraph '+str(i)} for i,t in enumerate(texts)]}
        fs=map_intake(d)['facts'];self.assertEqual([f['category'] for f in fs],['context','challenge','solution','restricted'])
        self.assertEqual(fs[0]['wording'],'Fictional Iris Labs');self.assertIn('Orion',fs[-1]['restriction'])
    @unittest.skipUnless(os.environ.get('REAL_INTAKE_TEST'),'Local client fixture not included in repository')
    def test_actual_intake_with_no_ai_or_network(self):
        source=Path(os.environ['REAL_INTAKE_TEST'])
        with patch.dict(s.os.environ,{'OPENAI_API_KEY':''}),patch.object(s,'ai',side_effect=AssertionError('No AI extraction call allowed')):
            p=s.process('upload',{'name':source.name,'data':base64.b64encode(source.read_bytes()).decode()})['project']
            self.assertEqual(len(p['facts']),22);self.assertEqual(len(p['intake']['solution']),4)
            self.assertTrue(p['intake']['client_context']);self.assertFalse(any('Vendor X' in f['wording'] for f in p['facts']))
            self.assertGreater(sum(len(f['wording'].split()) for f in p['facts'] if f['category']=='solution'),400)
            p=s.process('verify',{'project':p,'confirm_ids':s.review_summary(p)['quick_confirm_ids']})['project']
            self.assertEqual(p['plan']['evidence_gaps'],[])
            self.assertTrue(p['review_choice']['unresolved_ids'])
            p=s.process('plan',{'project':p})['project']
            for fmt in s.SECTIONS:
                p['format']=fmt
                sections=[{'name':name,'text':'[Approved CTA pending]' if name=='CTA' else 'Supported story content.','fact_ids':[] if name=='CTA' else p['plan']['selected']} for name in s.SECTIONS[fmt]]
                with patch.dict(s.os.environ,{'OPENAI_API_KEY':'placeholder'}),patch.object(s,'ai',return_value={'sections':sections}):p=s.process('generate',{'project':p})['project']
                self.assertEqual(len(p['drafts'][fmt]['sections']),len(s.SECTIONS[fmt]))

if __name__=='__main__':unittest.main()
