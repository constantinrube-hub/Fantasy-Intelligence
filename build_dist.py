#!/usr/bin/env python3
"""Build the minimal Cloudflare Pages static output.

Default mode is personal: managed league portfolio metadata is preserved. Use
--mode public to generate an empty portfolio configuration for a public site.
Full Python/research history/docs are never copied to dist.
"""
from __future__ import annotations
import argparse, json, shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DIST=ROOT/'dist'
MODEL_POS={
 'QB':{'QB'},'RB':{'RB','FB'},'WR':{'WR'},'TE':{'TE'},
 'DL':{'EDGE','IDL','DE','DT'},'LB':{'LB','ILB','OLB'},'DB':{'CB','S'},
 'K':{'K','K/P'},'P':{'P','K/P'},'DEF':{'DEF'},
 'OL':{'OL','G','OG','OT','T','C'},
}
def copy(src:Path,dst:Path): dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
def relevant_models(profile,contracts):
 slots=contracts.get('roster_slots') or {}; out=set()
 for slot in profile.get('roster_positions') or []:
  for pos in (slots.get(str(slot).upper()) or {}).get('positions') or []: out |= MODEL_POS.get(pos,{pos})
 return out
def compact_current(src:Path,dst:Path,profile,contracts):
 d=json.loads(src.read_text(encoding='utf-8')); allowed=relevant_models(profile,contracts)
 if isinstance(d.get('players'),list):
  def useful(r):
   pos_ok=(not allowed) or str(r.get('position_model') or '') in allowed
   evidence=bool(r.get('current_features')) or r.get('activation_eligible') is True or r.get('weekly_activation_eligible') is True or r.get('waiver_activation_eligible') is True
   projected=abs(float(r.get('sleeper_weekly_projection') or 0))>1e-12 or abs(float(r.get('decision_weekly_projection') or 0))>1e-12
   return pos_ok and (evidence or projected)
  d['players']=[r for r in d['players'] if useful(r)]
  d['runtime_compaction']={'position_models':sorted(allowed),'rule':'retain league-relevant rows with nonzero current projection or governed current evidence','original_player_count':len(json.loads(src.read_text(encoding='utf-8')).get('players') or []),'runtime_player_count':len(d['players'])}
 dst.parent.mkdir(parents=True,exist_ok=True);dst.write_text(json.dumps(d,separators=(',',':'))+'\n',encoding='utf-8')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=['personal','public'],default='personal');a=ap.parse_args()
 if DIST.exists(): shutil.rmtree(DIST)
 DIST.mkdir()
 copy(ROOT/'index.html',DIST/'index.html'); copy(ROOT/'_routes.json',DIST/'_routes.json'); copy(ROOT/'_headers',DIST/'_headers')
 for p in (ROOT/'app').rglob('*'):
  if p.is_file() and '.pre_' not in p.name: copy(p,DIST/p.relative_to(ROOT))
 for rel in ['config/build-manifest.json','config/model-config.json','config/release.json']:
  p=ROOT/rel
  if p.exists(): copy(p,DIST/rel)
 port=ROOT/'config/league-portfolio.json';out=DIST/'config/league-portfolio.json';out.parent.mkdir(parents=True,exist_ok=True)
 if a.mode=='personal': copy(port,out)
 else:
  base=json.loads(port.read_text(encoding='utf-8')) if port.exists() else {}; safe={k:v for k,v in base.items() if k not in {'sleeper_username','leagues'}};safe['sleeper_username']=None;safe['leagues']=[];out.write_text(json.dumps(safe,indent=2)+'\n')
 contracts=json.loads((ROOT/'config/contracts/runtime-contracts.json').read_text())
 leagues=ROOT/'data/research/leagues';
 for extra in ['registry.json','portfolio-status.json']:
  if (leagues/extra).exists(): copy(leagues/extra,DIST/'data/research/leagues'/extra)
 for d in leagues.iterdir():
  if not d.is_dir() or not (d/'profile.json').exists(): continue
  profile=json.loads((d/'profile.json').read_text())
  for name in ['profile.json','milestone1.json','milestone2.json','milestone3.json','milestone4.json','milestone5.json','milestone6.json']:
   if (d/name).exists(): copy(d/name,DIST/'data/research/leagues'/d.name/name)
  for name in ['governance/active_release.json','governance/operator_override.json']:
   if (d/name).exists(): copy(d/name,DIST/'data/research/leagues'/d.name/name)
  cur=d/'current/milestone5_current.json'
  if cur.exists(): compact_current(cur,DIST/'data/research/leagues'/d.name/'current/milestone5_current.json',profile,contracts)
 for p in (ROOT/'data/research/governance').glob('*.json') if (ROOT/'data/research/governance').exists() else []: copy(p,DIST/p.relative_to(ROOT))
 (DIST/'BUILD_MODE.txt').write_text(a.mode+'\n',encoding='utf-8')
 total=sum(p.stat().st_size for p in DIST.rglob('*') if p.is_file())
 print(f'Built {DIST} mode={a.mode} files={sum(1 for p in DIST.rglob("*") if p.is_file())} bytes={total}')
if __name__=='__main__':main()
