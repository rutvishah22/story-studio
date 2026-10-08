"""Structure-preserving local readers; no network, OCR or inference calls."""
import io, re, zipfile
import xml.etree.ElementTree as ET

W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
def text(node):
    return ''.join(n.text or '' for n in node.iter(W+'t')).strip()

def read_document(data, extension):
    blocks=[]
    if extension=='.docx':
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            if sum(i.file_size for i in archive.infolist())>20000000:
                raise ValueError('The expanded Word document is too large.')
            tree=ET.fromstring(archive.read('word/document.xml'))
        body=tree.find(W+'body')
        for index,node in enumerate(body):
            location='Word block '+str(index+1)
            if node.tag==W+'p' and text(node):
                blocks.append({'kind':'paragraph','location':location,'text':text(node)})
            elif node.tag==W+'tbl':
                for row_index,row in enumerate(node.findall(W+'tr')):
                    cells=[' '.join(text(p) for p in cell.findall('.//'+W+'p') if text(p)) for cell in row.findall(W+'tc')]
                    if any(cells): blocks.append({'kind':'table_row','location':location+', row '+str(row_index+1),'cells':cells,'text':' | '.join(cells)})
    elif extension=='.pdf':
        import pdfplumber
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            if len(pdf.pages)>50: raise ValueError('Upload an intake of at most 50 pages.')
            for number,page in enumerate(pdf.pages,1):
                tables=page.find_tables()
                events=[]
                for table in tables:
                    for index,row in enumerate(table.extract()):
                        cells=[re.sub(r'\s+',' ',cell or '').strip() for cell in row]
                        if any(cells): events.append((table.bbox[1]+index*.001,{'kind':'table_row','location':f'Page {number}, table row {index+1}','cells':cells,'text':' | '.join(cells)}))
                outside=page.filter(lambda obj: not any(t.bbox[0]<=((obj.get('x0',0)+obj.get('x1',0))/2)<=t.bbox[2] and t.bbox[1]<=((obj.get('top',0)+obj.get('bottom',0))/2)<=t.bbox[3] for t in tables))
                for line in outside.extract_text_lines(layout=False):
                    value=line['text'].strip()
                    if value: events.append((line['top'],{'kind':'paragraph','location':f'Page {number}','text':value}))
                blocks.extend(block for _,block in sorted(events,key=lambda item:item[0]))
    else: raise ValueError('Upload one PDF or DOCX.')
    raw='\n'.join(block['text'] for block in blocks)
    if len(raw.strip())<30:
        raise ValueError('No readable text was recovered. Scanned/image-only PDFs need OCR; upload a text-readable PDF or Word document. No evidence has been inferred.')
    if len(raw)>120000: raise ValueError('The intake is too long. Upload only the completed intake form.')
    return {'blocks':blocks,'text':raw,'reader':'Table-aware PDF reader' if extension=='.pdf' else 'Structured Word reader','ocr':'Not performed'}
