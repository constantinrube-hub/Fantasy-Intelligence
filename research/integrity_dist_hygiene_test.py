#!/usr/bin/env python3
from pathlib import Path
import hashlib, json
R=Path(__file__).resolve().parents[1];D=R/'dist';assert D.exists()
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
 return h.hexdigest()
files=[p for p in D.rglob('*') if p.is_file()]
for p in files:
 rel=p.relative_to(D);s=str(rel)
 assert p.suffix not in {'.py','.pyc','.pyo'},s
 assert not s.startswith(('research/','docs/','.github/')),s
 assert '.pre_' not in p.name and 'pre_phase' not in p.name,s
assert (D/'index.html').exists() and (D/'_headers').exists() and (D/'config/build-manifest.json').exists()
assert (R/'wrangler.toml').read_text().find('pages_build_output_dir = "dist"')>=0

def hydrate(data):
 st=data.get('storage') or {}
 if st.get('format')!='fie-current-split-v1':return data
 base=json.loads((D/st['player_base']).read_text(encoding='utf-8'))
 overlay=json.loads((D/st['scoring_overlay']).read_text(encoding='utf-8'))
 include=list(map(str,st.get('included_player_ids') or [])) if isinstance(st.get('included_player_ids'),list) else None
 exclude=set(map(str,st.get('excluded_player_ids') or []));proj=overlay.get('projections') or {};rows=[]
 base_rows=base.get('players') or []
 if include is not None:
  bm={(str(b.get('sleeper_id')) if b.get('sleeper_id') is not None else f"canonical:{b.get('canonical_player_id')}"):b for b in base_rows}; ordered=[(pid,bm.get(pid)) for pid in include]
 else:
  ordered=[((str(b.get('sleeper_id')) if b.get('sleeper_id') is not None else f"canonical:{b.get('canonical_player_id')}"),b) for b in base_rows]
 for pid,b in ordered:
  if b is None or pid in exclude:continue
  pair=proj.get(pid,[0,0]);rows.append({**b,'decision_weekly_projection':pair[0],'sleeper_weekly_projection':pair[1]})
 return {**data,'players':rows,'scoring_settings':overlay.get('scoring_settings') or {}}

# Every compacted league snapshot with starter slots must have an explicit non-empty position-model contract.
for cur in (D/'data/research/leagues').glob('*/current/milestone5_current.json') if (D/'data/research/leagues').exists() else []:
 raw=json.loads(cur.read_text(encoding='utf-8'));data=hydrate(raw)
 comp=raw.get('runtime_compaction') or {}
 assert comp.get('position_models'), f'missing position-aware runtime compaction: {cur.relative_to(D)}'
 assert int(comp.get('runtime_player_count',-1)) <= int(comp.get('original_player_count',-1)), f'invalid compaction counts: {cur.relative_to(D)}'
 assert len(data.get('players') or [])==int(comp.get('runtime_player_count',-1)), f'hydration count mismatch: {cur.relative_to(D)}'
 allowed=set(comp.get('position_models') or [])
 for row in data.get('players') or []:
  assert str(row.get('position_model') or '') in allowed, f'irrelevant position leaked into compact snapshot: {cur.relative_to(D)} {row.get("position_model")}'
 lid=cur.parents[1].name;govp=cur.parents[1]/'governance/active_release.json'
 if govp.exists():
  gov=json.loads(govp.read_text(encoding='utf-8'));line=gov.get('model_lineage') or {};paths=line.get('artifact_paths') or {};hashes=line.get('artifact_sha256') or {}
  for key in ('milestone4','milestone5','milestone6','current_snapshot'):
   ref=paths.get(key);expected=hashes.get(key);assert ref and expected,f'missing governed dist artifact hash: {lid} {key}';assert sha(D/ref)==expected,f'governed dist artifact hash mismatch: {lid} {key}'
  shared=line.get('shared_current_artifacts') or {};assert set(shared)>={'player_base','scoring_overlay'},f'missing governed shared dist artifacts: {lid}'
  for key,row in shared.items():
   assert str(row.get('path') or '').startswith('data/research/shared/current/'),f'invalid shared dist path: {lid} {key}'
   assert sha(D/row['path'])==row.get('sha256'),f'governed shared dist hash mismatch: {lid} {key}'
print(f'PASS integrity_dist_hygiene_test files={len(files)}')
