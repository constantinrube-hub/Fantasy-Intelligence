#!/usr/bin/env python3
"""Read-only, scoped reporting derivatives. Never changes research eligibility."""
import hashlib,json,shutil
from pathlib import Path
DOCS=['WINDOW1D_OPTIMAL_WAIVER_CHOPPED','OFFENSIVE_WAIVER_ELIGIBILITY_DESIGN','OFFENSIVE_WAIVER_V2_EXACT_SCORING_EXTENSION_DESIGN','WORKFLOW_USABILITY_MONITORING']
def read(path): return json.loads(path.read_text(encoding='utf-8'))
def binding(root,path): return {'path':path.relative_to(root).as_posix(),'sha256':hashlib.sha256(path.read_bytes().replace(b'\r\n',b'\n')).hexdigest()}
def write(path,obj):
 path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(obj,separators=(',',':'),sort_keys=True)+'\n',encoding='utf-8',newline='\n')
def build(root,dest,mode='personal'):
 root,dest=Path(root),Path(dest);base=dest/'data/ui/waivers'
 if base.exists():shutil.rmtree(base)
 index={'schema':'fie-waiver-ui-report-v1','reporting_only':True,'leagues':{},'documents':[],'portfolio_reports':[]}
 for name in DOCS:
  p=root/'docs/audits'/f'{name}.md'
  if p.exists():
   ref=f'data/ui/waivers/documents/{name}.json';write(dest/ref,{'title':name.replace('_',' ').title(),'scope':'Overarching methodology / operations','source':binding(root,p),'text':p.read_text(encoding='utf-8')});index['documents'].append({'title':name.replace('_',' ').title(),'url':ref})
 if mode=='personal':
  bundles={}
  for p in sorted((root/'data/research/evaluation').glob('*/weeks/week-*/waivers/portfolio-latest.json')):
   report=read(p)
   index['portfolio_reports'].append({'season':report['season'],'week':report['week'],'captured_at':report.get('generated_at'),'status_counts':report.get('status_counts'),'league_count':len(report.get('leagues',[])),'league_ids':[str(x['league_id']) for x in report.get('leagues',[])],'league_statuses':{str(x['league_id']):x.get('status') for x in report.get('leagues',[])},'source':binding(root,p),'research_only':True})
   for row in report.get('leagues',[]):
    lid=str(row['league_id']);b=bundles.setdefault(lid,{'league_id':lid,'reporting_only':True,'reports':[],'history':[]})
    b['reports'].append({'season':report['season'],'week':report['week'],'captured_at':report.get('generated_at'),'capture_id':report.get('capture_id'),'source':binding(root,p),'report':row})
  for p in sorted((root/'data/research/evaluation').glob('*/waivers/history/league-*.json')):
   h=read(p);lid=str(h['portfolio_league_id']);b=bundles.setdefault(lid,{'league_id':lid,'reporting_only':True,'reports':[],'history':[]})
   # Current namespace only: prior-league roster IDs cannot impersonate current managers.
   b['history'].append({'source':binding(root,p),'captured_at':h.get('captured_at'),'source_errors':h.get('source_errors'), 'summary':h.get('summary'),'sources':h.get('sources'), 'ledger':[x for x in h.get('bid_ledger',[]) if str(x.get('source_league_id'))==lid and int(x.get('season',0))==int(h.get('target_season',0))]})
  for lid,b in sorted(bundles.items()):
   ref=f'data/ui/waivers/leagues/{lid}.json';write(dest/ref,b);index['leagues'][lid]=ref
 write(base/'index.json',index)
 return index
if __name__=='__main__':
 root=Path(__file__).resolve().parents[1];build(root,root/'dist')
