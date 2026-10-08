import base64,io,unittest,zipfile
from unittest.mock import patch
from xml.sax.saxutils import escape
from intake_reader import read_document
import server as s

def word():
    rows=[('Client context','Fictional Meadow Labs processes regional delivery reports.'),('Before state','Analysts manually compared depot reports in separate spreadsheets.'),('Solution','A shared queue groups reports and assigns analyst review.'),('Results','Review time fell by 24% over six months compared with the prior six-month period.'),('Example only','Example: savings of 50% (replace with your answer).')]
    xml='<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:tbl>'+''.join('<w:tr>'+''.join('<w:tc><w:p><w:r><w:t>'+escape(c)+'</w:t></w:r></w:p></w:tc>' for c in row)+'</w:tr>' for row in rows)+'</w:tbl></w:body></w:document>'
    b=io.BytesIO()
    with zipfile.ZipFile(b,'w') as z:z.writestr('word/document.xml',xml)
    return b.getvalue(),rows

class Reading(unittest.TestCase):
    def test_word_table_relationships(self):
        data,rows=word();d=read_document(data,'.docx')
        self.assertEqual(len(d['blocks']),5)
        self.assertEqual(d['blocks'][1]['cells'],list(rows[1]))
        self.assertIn('24%',d['blocks'][3]['text'])
    def test_actual_pdf_table(self):
        from reportlab.pdfgen import canvas
        b=io.BytesIO();c=canvas.Canvas(b)
        for y in [750,710,670]:c.line(50,y,550,y)
        for x in [50,200,550]:c.line(x,670,x,750)
        c.drawString(60,730,'Question');c.drawString(210,730,'Completed answer')
        c.drawString(60,690,'Solution');c.drawString(210,690,'Shared queue assigns analyst review.')
        c.save();d=read_document(b.getvalue(),'.pdf')
        rows=[x for x in d['blocks'] if x['kind']=='table_row']
        self.assertEqual(rows[1]['cells'],['Solution','Shared queue assigns analyst review.'])
    def test_failure_does_not_accept_fragments_and_retry_recovers(self):
        data,rows=word();body={'name':'fictional.docx','data':base64.b64encode(data).decode()}
        with patch.dict(s.os.environ,{'OPENAI_API_KEY':'test'}),patch.object(s,'ai',side_effect=AssertionError('Structured intake must not call AI')):p=s.process('upload',body)['project']
        self.assertEqual(len(p['facts']),4);self.assertEqual(p['extraction_status'],'complete')
        self.assertNotIn('upload_data',p)
        facts=[{'category':cat,'wording':row[1],'passage':row[1],'intake_group':group,'field':row[0]} for cat,group,row in zip(['context','challenge','solution'],['client_context','before_state','solution'],rows)]
        with patch.dict(s.os.environ,{'OPENAI_API_KEY':'test'}),patch.object(s,'ai',return_value={'facts':facts}):p=s.process('retryExtraction',{'project':p})['project']
        self.assertEqual(len(p['facts']),4);self.assertEqual(len(p['intake']['solution']),1)
        self.assertNotIn('50%',str(p['facts']))
        p=s.process('verify',{'project':p,'confirm_ids':s.review_summary(p)['quick_confirm_ids']})['project'];p=s.process('plan',{'project':p})['project']
        for fmt in s.SECTIONS:
            p['format']=fmt
            sections=[{'name':name,'text':'[Approved CTA pending]' if name=='CTA' else '[Evidence pending: '+name+']','fact_ids':[]} for name in s.SECTIONS[fmt]]
            with patch.dict(s.os.environ,{'OPENAI_API_KEY':'test'}),patch.object(s,'ai',return_value={'sections':sections}):p=s.process('generate',{'project':p})['project']
            self.assertEqual([x['name'] for x in p['drafts'][fmt]['sections']],s.SECTIONS[fmt])
    def test_no_key_retains_document_without_pseudo_facts(self):
        data,_=word()
        with patch.dict(s.os.environ,{'OPENAI_API_KEY':''}):p=s.process('upload',{'name':'fictional.docx','data':base64.b64encode(data).decode()})['project']
        self.assertEqual(len(p['facts']),4);self.assertEqual(p['extraction_status'],'complete');self.assertTrue(p['raw'])

if __name__=='__main__':unittest.main()
