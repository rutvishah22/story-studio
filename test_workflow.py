import copy, unittest, io, base64, zipfile, urllib.request, json
from unittest.mock import patch
import server as s

def fixture():
    p=s.new_project(True);p['facts']=[s.fact(i,c,t,'Sample paragraph '+str(i)) for i,(c,t) in enumerate(s.SAMPLE)]
    for f in p['facts']:
        if f['status']!='restricted': f['status']='confirmed';f['confirmation']={'by':'Test writer','at':s.now()}
    p['facts'][4].update(value='24',unit='%',period='six months',comparison='prior six-month period');p['facts'][5]['restriction']='Violet Lantern'
    p['plan']=s.plan(p);p['plan_approved']=True
    return p
class Workflow(unittest.TestCase):
    def setUp(self):
        self.key_patch=patch.dict(s.os.environ,{"OPENAI_API_KEY":""});self.key_patch.start();self.addCleanup(self.key_patch.stop)
    def test_both_formats_and_integrity(self):
        p=fixture()
        for fmt in s.SECTIONS:
            d=s.draft(p,fmt);v=s.validate(p,fmt,d)
            self.assertEqual([x['name'] for x in d['sections']],s.SECTIONS[fmt]);self.assertEqual(v['status'],'Checks incomplete');self.assertIn('fixed format',v['reference_note'])
            metric=next(x for x in d['sections'] if '24%' in x['text']);metric['text']=metric['text'].replace('24%','42%');self.assertEqual(s.validate(p,fmt,d)['status'],'Blocked')
            d=s.draft(p,fmt);d['sections'][0]['text']+=' Violet Lantern';self.assertTrue(any(f['check']=='Restrictions' for f in s.validate(p,fmt,d)['findings']))
            d=s.draft(p,fmt);next(x for x in d['sections'] if '24%' in x['text'])['text']=s.SAMPLE[4][1].replace('six months','three months');self.assertEqual(s.validate(p,fmt,d)['status'],'Blocked')
    def test_references_and_exclusions(self):
        p=fixture();p['references']=[{'id':'R1','format':'One-Pager','approved':True,'active':True,'entities':['Otherworks'],'text':'Otherworks improved delivery by 99% during one year.'}]
        self.assertEqual(s.eligible_refs(p,'Case Study'),[])
        d=s.draft(p,'One-Pager');d['sections'][0]['text']='Otherworks improved delivery by 99% during one year.'
        self.assertTrue(any(f['check']=='Reference leakage' and f['level']=='block' for f in s.validate(p,'One-Pager',d)['findings']))
        self.assertNotIn('F6',p['plan']['selected'])
    def test_missing_story(self):
        p=fixture()
        for f in p['facts']:
            if f['category']=='solution': f['status']='uncertain'
        with self.assertRaises(ValueError):s.plan(p)
    def test_http_edit_and_upload(self):
        def post(action,p=None,**kw):
            req=urllib.request.Request('http://127.0.0.1:8768/api/'+action,data=json.dumps({'project':p,**kw}).encode(),headers={'Content-Type':'application/json'})
            with urllib.request.urlopen(req) as r:return json.load(r)['project']
        p=post('demo')
        for f in p['facts']:
            if f['status']!='restricted':f['status']='confirmed'
        p=post('verify',p);p=post('plan',p)
        for fmt in s.SECTIONS:
            p['format']=fmt;p=post('generate',p);p=post('validate',p);p=post('edit',p)
            self.assertIsNone(p['drafts'][fmt]['validation']);self.assertEqual(p['drafts'][fmt]['review'],'Pending human review')
            p=post('regenerate',p,index=0);p=post('validate',p);self.assertEqual(p['drafts'][fmt]['validation']['revision'],p['drafts'][fmt]['revision'])
        self.assertEqual(len(p['drafts']),2)
        buf=io.BytesIO()
        with zipfile.ZipFile(buf,'w') as z:z.writestr('word/document.xml','<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Fictional intake: dispatchers reconciled records manually.</w:t></w:r></w:p></w:body></w:document>')
        uploaded=post('upload',name='sample.docx',data=base64.b64encode(buf.getvalue()).decode());self.assertIn('dispatchers',uploaded['raw']);self.assertTrue(uploaded['facts'])
        from reportlab.pdfgen import canvas
        pdf=io.BytesIO();c=canvas.Canvas(pdf);c.drawString(40,700,'Fictional dispatchers used a shared delivery workflow.');c.save()
        uploaded=post('upload',name='sample.pdf',data=base64.b64encode(pdf.getvalue()).decode());self.assertIn('shared delivery',uploaded['raw']);self.assertTrue(uploaded['facts'])
        # Leave the sample workflow available in the UI, rather than the test upload.
        post('save',p)
if __name__=='__main__':unittest.main(verbosity=2)
