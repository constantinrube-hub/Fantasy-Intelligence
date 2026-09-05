#!/usr/bin/env python3
"""Build the minimal Cloudflare Pages static output.

Default mode is personal: managed league portfolio metadata is preserved. Use
--mode public to generate an empty portfolio configuration for a public site.
Full Python/research history/docs are never copied to dist.

Current M5 snapshots are materialized from shared source storage, compacted with
the existing league-position relevance rule, then deduplicated again for the
browser. The deployed contract is therefore tiny league manifests + shared
runtime player bases + scoring overlays.
"""
from __future__ import annotations
import argparse, hashlib, json, shutil, sys
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DIST=ROOT/'dist'
sys.path.insert(0,str(ROOT/'research'))
from current_snapshot_storage import (  # noqa: E402
 BASE_FORMAT, OVERLAY_FORMAT, STORAGE_FORMAT, base_row, content_hash,
 load_current_snapshot, player_id, projection_is_default, projection_pair, write_json,
)
MODEL_POS={
 'QB':{'QB'},'RB':{'RB','FB'},'WR':{'WR'},'TE':{'TE'},
 'DL':{'EDGE','IDL','DE','DT'},'LB':{'LB','ILB','OLB'},'DB':{'CB','S'},
 'K':{'K','K/P'},'P':{'P','K/P'},'DEF':{'DEF'},
 'OL':{'OL','G','OG','OT','T','C'},
}
def copy(src:Path,dst:Path): dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
def sha256_file(path:Path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()
def relevant_models(profile,contracts):
 slots=contracts.get('roster_slots') or {}; out=set()
 for slot in profile.get('roster_positions') or []:
  for pos in (slots.get(str(slot).upper()) or {}).get('positions') or []: out |= MODEL_POS.get(pos,{pos})
 return out
def useful_rows(snapshot,allowed):
 rows=[]
 for r in snapshot.get('players') or []:
  pos_ok=(not allowed) or str(r.get('position_model') or '') in allowed
  evidence=bool(r.get('current_features')) or r.get('activation_eligible') is True or r.get('weekly_activation_eligible') is True or r.get('waiver_activation_eligible') is True
  projected=abs(float(r.get('sleeper_weekly_projection') or 0))>1e-12 or abs(float(r.get('decision_weekly_projection') or 0))>1e-12
  if pos_ok and (evidence or projected): rows.append(r)
 return rows
def partition_compatible(entries):
 """Partition compact league snapshots deterministically if invariant player rows conflict."""
 groups=[]
 # The greedy compatibility partition is order-sensitive. Canonicalize by league
 # ID here so identical source trees cannot emit different content-addressed
 # runtime bases merely because Path.iterdir() has a different filesystem order.
 for e in sorted(entries,key=lambda x:str(x.get('lid',''))):
  candidate={player_id(r):base_row(r) for r in e['rows']}
  placed=False
  for g in groups:
   if all(pid not in g['union'] or g['union'][pid]==row for pid,row in candidate.items()):
    g['union'].update(candidate);g['entries'].append(e);placed=True;break
  if not placed: groups.append({'union':dict(candidate),'entries':[e]})
 return groups
def emit_runtime_current(entries):
 if not entries:return
 for group in partition_compatible(entries):
  union=group['union'];ordered=sorted(union,key=lambda x:(not x.isdigit(),int(x) if x.isdigit() else x))
  base_obj={'format':BASE_FORMAT,'schema_version':1,'player_count':len(ordered),'players':[union[x] for x in ordered]}
  bh=content_hash(base_obj);base_rel=Path('data/research/shared/current')/f'runtime_player_base.{bh}.json'
  write_json(DIST/base_rel,base_obj,compact=True)

  overlays=[]
  assignment={}
  for e in group['entries']:
   sig=str(e['snapshot'].get('scoring_signature') or 'unknown');settings=e['snapshot'].get('scoring_settings') or {}
   proj={}
   for r in e['rows']:
    pair=projection_pair(r)
    if not projection_is_default(pair):proj[player_id(r)]=pair
   target=None
   for og in overlays:
    if og['sig']!=sig or og['settings']!=settings:continue
    if all(pid not in og['proj'] or og['proj'][pid]==pair for pid,pair in proj.items()):target=og;break
   if target is None:
    target={'sig':sig,'settings':settings,'proj':{},'entries':[]};overlays.append(target)
   target['proj'].update(proj);target['entries'].append(e);assignment[e['lid']]=target

  overlay_paths={}
  for og in overlays:
   obj={'format':OVERLAY_FORMAT,'schema_version':1,'scoring_signature':og['sig'],'scoring_settings':og['settings'],'projection_fields':['decision_weekly_projection','sleeper_weekly_projection'],'default_projection':[0.0,0.0],'nonzero_player_count':len(og['proj']),'projections':og['proj']}
   oh=content_hash(obj);rel=Path('data/research/shared/current/scoring')/f"{og['sig']}.{oh}.json";write_json(DIST/rel,obj,compact=True);overlay_paths[id(og)]=rel

  for e in group['entries']:
   snap=e['snapshot'];ids=[player_id(r) for r in e['rows']];manifest={k:v for k,v in snap.items() if k not in {'players','scoring_settings'}}
   manifest['storage']={'format':STORAGE_FORMAT,'player_base':base_rel.as_posix(),'scoring_overlay':overlay_paths[id(assignment[e['lid']])].as_posix(),'player_count':len(ids),'included_player_ids':ids}
   manifest['runtime_compaction']={'position_models':sorted(e['allowed']),'rule':'retain league-relevant rows with nonzero current projection or governed current evidence; shared runtime base is deduplicated across compatible leagues','original_player_count':len(snap.get('players') or []),'runtime_player_count':len(ids)}
   write_json(DIST/'data/research/leagues'/e['lid']/'current/milestone5_current.json',manifest,compact=True)

def rewrite_dist_governance(entries):
 """Bind governance hashes to the transformed dist current artifacts.

 Source governance authenticates the source manifest/shared store. Dist changes
 the current manifest and shared files during runtime compaction, so the served
 governance copy must hash the served derivatives or browser verification would
 (correctly) fail. Historical M4-M6 hashes remain unchanged because those files
 are copied byte-for-byte.
 """
 for e in entries:
  lid=e['lid'];gp=DIST/'data/research/leagues'/lid/'governance/active_release.json'
  cp=DIST/'data/research/leagues'/lid/'current/milestone5_current.json'
  if not gp.exists() or not cp.exists():continue
  g=json.loads(gp.read_text(encoding='utf-8'));cur=json.loads(cp.read_text(encoding='utf-8'));line=g.setdefault('model_lineage',{})
  paths=line.setdefault('artifact_paths',{});hashes=line.setdefault('artifact_sha256',{})
  paths['current_snapshot']=f'data/research/leagues/{lid}/current/milestone5_current.json';hashes['current_snapshot']=sha256_file(cp)
  st=cur.get('storage') or {};shared={}
  for key in ('player_base','scoring_overlay'):
   ref=str(st.get(key) or '');rp=DIST/ref
   if ref and rp.exists():shared[key]={'path':ref,'sha256':sha256_file(rp)}
  line['shared_current_artifacts']=shared
  g.setdefault('current_snapshot',{})['storage_format']=st.get('format')
  g['dist_derivation']={'current_snapshot_compacted':True,'shared_runtime_storage':True,'rule':'served governance hashes are rebound to deterministic dist derivatives; source governance remains authoritative for source artifacts'}
  write_json(gp,g,compact=True)

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
 leagues=ROOT/'data/research/leagues';current_entries=[];cache={}
 for extra in ['registry.json','portfolio-status.json']:
  if (leagues/extra).exists(): copy(leagues/extra,DIST/'data/research/leagues'/extra)
 # Directory enumeration order is filesystem-dependent; canonicalize it.
 for d in sorted(leagues.iterdir(),key=lambda p:p.name):
  if not d.is_dir() or not (d/'profile.json').exists(): continue
  profile=json.loads((d/'profile.json').read_text())
  for name in ['profile.json','milestone1.json','milestone2.json','milestone3.json','milestone4.json','milestone5.json','milestone6.json']:
   if (d/name).exists(): copy(d/name,DIST/'data/research/leagues'/d.name/name)
  for name in ['governance/active_release.json','governance/operator_override.json']:
   if (d/name).exists(): copy(d/name,DIST/'data/research/leagues'/d.name/name)
  cur=d/'current/milestone5_current.json'
  if cur.exists():
   snap=load_current_snapshot(cur,root=ROOT,cache=cache);allowed=relevant_models(profile,contracts);rows=useful_rows(snap,allowed)
   current_entries.append({'lid':d.name,'snapshot':snap,'rows':rows,'allowed':allowed})
 emit_runtime_current(current_entries)
 rewrite_dist_governance(current_entries)
 for p in (ROOT/'data/research/governance').glob('*.json') if (ROOT/'data/research/governance').exists() else []: copy(p,DIST/p.relative_to(ROOT))
 (DIST/'BUILD_MODE.txt').write_text(a.mode+'\n',encoding='utf-8')
 total=sum(p.stat().st_size for p in DIST.rglob('*') if p.is_file())
 print(f'Built {DIST} mode={a.mode} files={sum(1 for p in DIST.rglob("*") if p.is_file())} bytes={total}')
if __name__=='__main__':main()
