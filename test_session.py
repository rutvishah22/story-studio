import unittest,copy,os,json,threading,urllib.request,urllib.error
from unittest.mock import patch
import server as s
from api.index import handler
class Session(unittest.TestCase):
    def setUp(self):
        self.key_patch=patch.dict(s.os.environ,{"OPENAI_API_KEY":""});self.key_patch.start();self.addCleanup(self.key_patch.stop)
    def demo(self):return s.process('demo',{})['project']
    def test_summary_confirm_and_isolation(self):
        a=self.demo();b=self.demo();self.assertNotEqual(a['id'],b['id'])
        info=s.review_summary(a);self.assertEqual(info['exceptions'],[]);self.assertEqual(len(info['quick_confirm_ids']),12)
        a=s.process('verify',{'project':a,'confirm_ids':info['quick_confirm_ids'],'writer':'Demo writer'})['project']
        self.assertEqual(len(s.permitted(a)),12);self.assertEqual(len(s.permitted(b)),0);self.assertEqual(a['facts'][5]['status'],'restricted')
        a=s.process('plan',{'project':a})['project']
        for fmt in s.SECTIONS:
            a['format']=fmt;a=s.process('generate',{'project':a})['project'];d=a['drafts'][fmt];self.assertEqual([x['name'] for x in d['sections']],s.SECTIONS[fmt])
            d['sections'][0]['text']+=' Violet Lantern';a=s.process('validate',{'project':a})['project'];self.assertEqual(a['drafts'][fmt]['validation']['status'],'Blocked')
            a=s.process('edit',{'project':a})['project'];self.assertIsNone(a['drafts'][fmt]['validation'])
        self.assertEqual(len(a['drafts']),2)
    def test_metric_exception_and_restrictions(self):
        a=self.demo();a['facts'][4]['period']='';info=s.review_summary(a)
        self.assertEqual(info['exceptions'][0]['fact_id'],'F5');self.assertNotIn('F5',info['quick_confirm_ids']);self.assertNotIn('F6',info['quick_confirm_ids'])
        with self.assertRaises(ValueError):s.process('verify',{'project':a,'confirm_ids':['F5']})
    def test_no_disk_writes(self):
        with patch.object(s,'SESSION_ONLY',True),patch.object(s.Path,'write_text',side_effect=AssertionError('Disk write')):
            s.process('demo',{})
    def test_vercel_http_and_limits(self):
        http=s.ThreadingHTTPServer(('127.0.0.1',0),handler);threading.Thread(target=http.serve_forever,daemon=True).start();base='http://127.0.0.1:'+str(http.server_port)+'/api/index?action='
        try:
            with urllib.request.urlopen(base+'state') as r:state=json.load(r)
            self.assertIsNone(state['project']);self.assertTrue(state['session_only'])
            req=urllib.request.Request(base+'demo',data=b'{}',headers={'Content-Type':'application/json'})
            with urllib.request.urlopen(req) as r:result=json.load(r)
            self.assertTrue(result['project']['demo'])
            req=urllib.request.Request(base+'demo',data=b' '*4200001,headers={'Content-Type':'application/json'})
            with self.assertRaises(urllib.error.HTTPError) as cm:urllib.request.urlopen(req)
            self.assertEqual(cm.exception.code,413)
        finally:http.shutdown();http.server_close()
if __name__=='__main__':unittest.main(verbosity=2)
