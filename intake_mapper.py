"""Deterministic section/question/answer mapping. Never calls an AI provider."""
import re

GROUPS=['client_context','before_state','solution','results','client_voice','restrictions']
FIELDS=[
 ('client_context','Company name',r'company name|client name|customer name|client context'),
 ('client_context','Industry',r'industry|vertical|sector'),
 ('client_context','Employee count',r'employee count|number of employees'),
 ('client_context','Revenue or scale',r'company revenue|revenue / valuation|annual revenue'),
 ('client_context','Scope',r'project scope|business unit|business context|project contacts|key contacts'),
 ('before_state','Use case',r'use case|existing workflow|before state|current workflow|problem(?:$|:)|challenge(?:$|:)'),
 ('before_state','Pain point',r'core pain point|pain points|bottleneck'),
 ('before_state','Business impact',r'business impact'),
 ('before_state','Previous attempts',r'previous attempts'),
 ('solution','What was implemented',r'what we built|solution implemented|key capabilities|implementation details|solution(?:$|:)'),
 ('solution','Integrations',r'integrations'),
 ('solution','Deployment timeline',r'deployment timeline'),
 ('solution','Differentiation',r'why we won|differentiat'),
 ('results','Headline result',r'headline stat|headline result|results(?:$|:)'),
 ('results','Adoption',r'adoption metrics|usage metrics'),
 ('results','Measurement method',r'how measured|measurement period|calculation method'),
 ('client_voice','Client quote',r'client quote'),
 ('client_voice','Observed benefit',r'what surprised|unexpected benefit'),
 ('restrictions','Usage restrictions',r'usage restrictions|confidential|anonymisation|anonymization|publication restrictions|name or logo restrictions'),
]

def match_field(label):
    clean=re.sub(r'^\s*[\d.()â€¢-]+\s*','',label).strip()
    for group,field,pattern in FIELDS:
        if re.match(pattern,clean,re.I): return group,field
    return None

def map_intake(document):
    answers=[];pending=None;group='client_context';metric_headers=False;unmapped=[]
    for block in document['blocks']:
        line=block['text'].strip();cells=block.get('cells',[])
        heading=re.match(r'^\d{1,2}\s+(CLIENT VOICE|CLIENT|PROBLEM|SOLUTION|RESULTS|RESTRICTIONS)\b',line,re.I)
        if heading:
            group={'CLIENT':'client_context','PROBLEM':'before_state','SOLUTION':'solution','RESULTS':'results','CLIENT VOICE':'client_voice','RESTRICTIONS':'restrictions'}[heading[1].upper()];pending=None;metric_headers=False;continue
        if cells and cells[0].strip().upper()=='METRIC':metric_headers=True;pending=None;continue
        if cells:
            if not cells[0].strip():
                if pending and any(cells[1:]):
                    continuation=' '.join(c for c in cells[1:] if c.strip())
                    pending['answer']+=' '+continuation;pending['source']+='\n'+line;pending['locations'].append(block['location'])
                continue
            found=match_field(cells[0])
            if found:
                answer=' '.join(c for c in cells[1:] if c.strip());field_group,field=found
            elif metric_headers and len(cells)>=4:
                field_group,field='results',cells[0]
                answer='Before: '+cells[2]+' After: '+cells[3] if cells[2].strip() or cells[3].strip() else ''
            elif len(cells)==2 and len(cells[0].split())<=12:
                field_group,field=group,cells[0];answer=cells[1];unmapped.append(field)
            else:pending=None;continue
            # Example instructions are in the label column, not evidence.
            if not answer.strip() or re.match(r'^(example[: ]|please enter|n/?a$|not provided$|[-_]+$)',answer.strip(),re.I):pending=None;continue
            pending={'group':field_group,'field':field,'answer':answer.strip(),'source':line,'locations':[block['location']]};answers.append(pending)
            if found:metric_headers=False
            continue
        # Plain Word/PDF question followed by complete answer paragraphs.
        found=match_field(line)
        if found:
            group,field=found;pending={'group':group,'field':field,'answer':'','source':line,'locations':[block['location']]};answers.append(pending)
            if ':' in line and 'Example:' not in line:
                value=line.split(':',1)[1].strip()
                if value:pending['answer']=value
            continue
        if pending and not re.match(r'^(example:|what |who |how |describe |give us |quantify |did they |page \d|\d+$)',line,re.I):
            pending['answer']+=(' ' if pending['answer'] else '')+line;pending['source']+='\n'+line;pending['locations'].append(block['location'])
    answers=[a for a in answers if a['answer'].strip()]
    facts=[]
    category={'client_context':'context','before_state':'challenge','solution':'solution','results':'outcome','client_voice':'outcome','restrictions':'restricted'}
    for index,a in enumerate(answers):
        wording=a['answer'];cat=category[a['group']];review=[];value=unit=period=qualifier=comparison=''
        # Numbers in context/scope are not automatically achieved result metrics.
        if a['group']=='results' and re.search(r'\d',wording):
            cat='metric';matches=re.findall(r'(?:([$])\s*)?([\d,]+(?:\.\d+)?)\s*(%|Ã—|hours?|hrs?|minutes?|mins?|FTEs?|users?|cycles?)?',wording,re.I)
            after=wording.split('After:',1)[-1]
            primary=re.search(r'(\$)?([\d,]+(?:\.\d+)?)\s*(%|Ã—|hours?|hrs?|minutes?|mins?|FTEs?|users?|cycles?)?',after,re.I)
            if primary:value=primary[2];unit='$' if primary[1] else primary[3] or ''
            if not unit and re.search(r'rework cycles?',after,re.I):unit='rework cycles'
            if not unit and re.search(r'tasks/day',after,re.I):unit='users'
            timeframe=re.search(r'(?:per |/)(week|month|year|day)|\b(annual|monthly|weekly|daily)\b',wording,re.I)
            if timeframe:period=timeframe[0]
            elif unit=='×':period='not applicable'
            qualifier='estimated' if re.search(r'estimat',wording,re.I) else 'approximately' if re.search(r'approxim|~',wording) else ''
            baseline=wording.split('After:')[0].replace('Before:','').strip() if 'After:' in wording else ''
            baseline_number=re.search(r'[\d,]+(?:\.\d+)?\s*(?:hours?|hrs?|minutes?|mins?|cycles?|users?)\s*(?:/(?:week|month|year|day)|per (?:week|month|year|day))?',baseline,re.I)
            comparison=baseline_number[0] if baseline_number else ''
            # Several values in a before/after result are normal, not an ambiguity.
            conflict=re.search(r'([\d,]+)\s+search hours/month.*?\(([\d,]+)\s*[×x]\s*([\d,]+)\s*hrs/week\s*[×x]\s*([\d,]+)\s*weeks',wording,re.I)
            if conflict:
                stated,users,hours,weeks=[int(v.replace(',','')) for v in conflict.groups()]
                if stated!=users*hours*weeks:review.append(f'Conflicting calculation: {users} × {hours} × {weeks} = {users*hours*weeks}, not {stated}.')
            if not period:review.append('Measurement period is not stated in this answer.')
            if not unit:review.append('Metric unit needs confirmation.')
            if re.search(r'target|potential|projected|estimated|assuming|equivalent|capacity',wording,re.I):review.append('Confirm whether this is measured, estimated or projected; capacity is not automatically realised savings.')
        if a['group'] in ['before_state','solution'] and re.search(r'\b(target|projected|assuming|potential savings)\b',wording,re.I):review.append('This answer includes a target or calculated estimate. Confirm its publication basis before using the whole claim.')
        facts.append({'calculation_conflict':any(reason.startswith('Conflicting calculation:') for reason in review),'baseline_description':wording.split('After:')[0].replace('Before:','').strip() if 'After:' in wording else '', 'category':cat,'wording':wording,'passage':a['source'],'location':'; '.join(dict.fromkeys(a['locations'])),'intake_group':a['group'],'field':a['field'],'value':value,'unit':unit,'period':period,'qualifier':qualifier,'comparison':comparison,'needs_review':bool(review),'review_reason':' '.join(review),'metric_role':('unknown' if review else 'result') if cat=='metric' else 'not_applicable','story_roles':[category[a['group']]] if cat!='metric' else ['outcome'],'restriction':wording if cat=='restricted' else ''})
    return {'facts':facts,'answers':answers,'unmapped_fields':unmapped,'engine':'Local section-and-answer mapping'}
