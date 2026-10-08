"""Shared publication and evidence policy; independently testable."""
import re

def client_names(project):
    return list(dict.fromkeys(f['wording'].strip() for f in project.get('facts',[]) if f.get('field')=='Company name' and f.get('wording','').strip()))

def anonymise(text,project):
    for name in sorted(client_names(project),key=len,reverse=True):
        text=re.sub(r'(?<!\w)'+re.escape(name)+r'(?!\w)','the client',text,flags=re.I)
    return text

def publication_text(text,project):
    text=re.sub(r'\bthe client\s+(implemented|deployed|built|developed|delivered)\s+(Product Genius|BPA)',r'Our team \1 \2',anonymise(text,project),flags=re.I)
    return anonymise(text.replace('\\n','\n').replace('\\t',' '),project)

def confirmation_problem(f):
    if f.get('restriction') or f.get('status') in ['restricted','missing']:return 'Restricted or missing evidence cannot be confirmed.'
    if not f.get('passage'):return 'A source passage is required.'
    if f.get('category')=='metric' and not all(f.get(k) for k in ['value','unit','period']):return 'Complete the metric value, unit and period before confirming.'
    if f.get('calculation_conflict'):return 'Resolve the conflicting calculation before confirming.'
    return ''

def publication_findings(text,project):
    findings=[]
    for name in client_names(project):
        if re.search(r'(?<!\w)'+re.escape(name)+r'(?!\w)',text,re.I):findings.append(('Anonymity',name,'Client names are never permitted in published drafts.'))
    if re.search(r'\b(?:the client|customer)\s+(?:built|developed|delivered|implemented|deployed)\s+(?:Product Genius|BPA)',text,re.I):findings.append(('Attribution',text,'Attribute delivery of Product Genius/BPA 4.0 to the delivery team, not the client.'))
    return findings


def approved_cta(project):
    evidence=' '.join(f.get('wording','') for f in project.get('facts',[]) if f.get('status')=='confirmed' and not f.get('restriction')).casefold()
    if 'product genius' in evidence and ('sku' in evidence or 'product' in evidence):
        return 'Still relying on manual searches to identify the right product?\n\nSee how BPA 4.0 Product Genius can help turn fragmented product information into evidence-backed recommendations.\n\nExplore Product Identification with BPA 4.0'
    return 'Ready to improve this workflow?\n\nExplore an approach built around your operating needs.\n\nDiscuss Your Workflow'

def scope_findings(text,project):
    findings=[]
    for fact in project.get('facts',[]):
        if fact.get('field')!='Employee count':continue
        numbers=re.findall(r'\d[\d,]*',fact.get('wording',''))
        if not numbers:continue
        amount=r'\s*[-–—]\s*'.join(re.escape(n) for n in numbers[:2]) if len(numbers)>1 else re.escape(numbers[0])
        if re.search(amount+r'\s*(?:SKUs?|products?|product requests)\b',text,re.I):findings.append(('Metric scope',text,'Employee count has been incorrectly described as product or request volume.'))
    return findings
