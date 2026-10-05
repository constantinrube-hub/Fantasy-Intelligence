#!/usr/bin/env python3
"""Registered read-only document derivatives; no scoring, eligibility or capture writes."""
import json, shutil
from pathlib import Path
from build_waiver_ui_evidence import binding, write, read
DOCS=[('docs/FIE_UNIFIED_RESEARCH_PIPELINE.md','Research pipeline'),('docs/FEATURE_EVIDENCE_RESEARCH.md','Feature evidence'),('docs/audits/TRANCHE6B_RESEARCH_COMPLETENESS_INVENTORY.md','Completeness definitions'),('docs/audits/TRANCHE6D_M10_OFFLINE_CHALLENGER.md','M10 offline challenger'),('docs/audits/M10_SUNDAY_PAIRED_CHECKPOINT_DESIGN.md','M9 / M10 paired checkpoint'),('docs/audits/TRANCHE7A_PROSPECTIVE_M10_EVIDENCE_DESIGN.md','Prospective capture methodology')]
def abstract(text):
 return next((s.strip() for s in text.splitlines() if s.strip() and not s.lstrip().startswith(('#','|','```','-','>'))),'Open the authoritative document for its scope and qualifications.')[:450]
def build(root,dest,mode='personal'):
 root,dest=Path(root),Path(dest);base=dest/'data/ui/reports'
 if base.exists():shutil.rmtree(base)
 idx={'schema':'fie-editorial-reports-v1','reporting_only':True,'documents':[],'inventories':[]}
 w=read(dest/'data/ui/waivers/index.json')
 for d in w['documents']:
  payload=read(dest/d['url']);idx['documents'].append({**d,'id':Path(d['url']).stem,'type':'Waivers / operations','scope':'Global','period':'Methodology; not a live result','status':'Reference document','abstract':abstract(payload['text']),'source':payload['source']})
 for rel,title in DOCS:
  p=root/rel
  if not p.exists():continue
  ref=f'data/ui/reports/documents/{p.stem}.json';text=p.read_text(encoding='utf-8');source=binding(root,p)
  write(dest/ref,{'title':title,'scope':'Global research methodology','source':source,'text':text})
  idx['documents'].append({'id':p.stem,'title':title,'url':ref,'type':'Research','scope':'Global','period':'Document-defined','status':'Research reference','abstract':abstract(text),'source':source})
 if mode=='personal':
  for p in sorted((root/'data/research/portfolio').glob('*/research-completeness-inventory.json')):
   x=read(p);ref=f'data/ui/reports/inventories/{p.parent.name}.json';write(dest/ref,{'source':binding(root,p),'inventory':x});idx['inventories'].append({'season':p.parent.name,'url':ref,'source':binding(root,p)})
 write(base/'index.json',idx);return idx
if __name__=='__main__':
 root=Path(__file__).resolve().parents[1];build(root,root/'dist')
