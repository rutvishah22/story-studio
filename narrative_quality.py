"""Lightweight editorial checks: advisory, not a claim of human approval."""
import re

def editorial_findings(sections):
    findings=[];seen={}
    for section in sections:
        name,text=section['name'],section['text']
        if text.startswith('['):continue
        if 'the delivery team' in text.casefold():findings.append((name,'Use the established partnership voice rather than an impersonal delivery-team label.'))
        if name in ['The Solution','Solution']:
            stack=re.findall(r'\b(?:BigQuery|AlloyDB|Google ADK|Gemini Enterprise|Cloud Storage|GCS)\b',text,re.I)
            if len(set(x.casefold() for x in stack))>=3:findings.append((name,'Architecture-heavy section: explain the changed user workflow and retain only essential systems.'))
        if name in ['Subtext','Context','Client and Context','The Outcome','Why It Matters'] and re.search(r'\b(?:dramatically|revolutionary|game-changing|seamless|higher-value activities)\b',text,re.I):findings.append((name,'Replace vague selling or unsupported benefits with a specific evidenced change.'))
        for sentence in re.split(r'(?<=[.!?])\s+|\n',text):
            words=re.findall(r'\b\w+\b',sentence.casefold())
            if len(words)<12:continue
            tokens=set(words)
            for previous,prior in seen.items():
                if previous[0]!=name and len(tokens & prior)/max(1,len(tokens | prior))>.78:
                    findings.append((name,'Repeats a substantial sentence from '+previous[0]+'. Give this section its own purpose.'));break
            seen[(name,sentence)]=tokens
    return list(dict.fromkeys(findings))
