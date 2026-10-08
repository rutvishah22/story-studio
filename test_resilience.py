import base64,io,json,tempfile,threading,unittest,urllib.request,zipfile
from pathlib import Path
from unittest.mock import patch
import server as s
class Resilience(unittest.TestCase):
    def upload(self,response):
        b=io.BytesIO()
        with zipfile.ZipFile(b,'w') as z:z.writestr('word/document.xml','<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Dispatchers reconciled records manually before a shared review workflow.</w:t></w:r></w:p></w:body></w:document>')
        with tempfile.TemporaryDirectory() as folder,patch.object(s,'DATA',Path(folder)),patch.object(s,'ai',side_effect=response if isinstance(response,Exception) else None,return_value=response),patch.dict(s.os.environ,{'OPENAI_API_KEY':'test-placeholder'}):
            http=s.ThreadingHTTPServer(('127.0.0.1',0),s.Handler);t=threading.Thread(target=http.serve_forever,daemon=True);t.start()
            try:
                req=urllib.request.Request('http://127.0.0.1:'+str(http.server_port)+'/api/upload',data=json.dumps({'name':'fictional.docx','data':base64.b64encode(b.getvalue()).decode()}).encode(),headers={'Content-Type':'application/json'})
                with urllib.request.urlopen(req) as r:return json.load(r)['project']
            finally:http.shutdown();http.server_close()
    def test_unmatched_provenance_falls_back(self):
        p=self.upload({'facts':[{'category':'challenge','wording':'Invented details','passage':'Unmatched invented passage'}]})
        self.assertEqual(p['facts'],[]);self.assertEqual(p['extraction_status'],'failed');self.assertTrue(p['document']['blocks']);self.assertIn('extraction failure',p['extraction_note'])
    def test_provider_failure_retains_source(self):
        p=self.upload(ValueError('Provider busy'))
        self.assertEqual(p['facts'],[]);self.assertTrue(p['raw']);self.assertIn('Provider busy',p['extraction_note']);self.assertTrue(p['file'])
    def test_verified_passage_and_profile(self):
        p=self.upload({'facts':[{'category':'challenge','wording':'Dispatchers reconciled records manually.','passage':'Dispatchers  reconciled records manually'}]})
        self.assertEqual(p['facts'][0]['passage'],'Dispatchers reconciled records manually');self.assertEqual(p['facts'][0]['status'],'uncertain');self.assertIn('British English',s.PROFILE)
if __name__=='__main__':unittest.main(verbosity=2)
