#!/usr/bin/env python3
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'dist';assert D.exists()
files=[p for p in D.rglob('*') if p.is_file()]
for p in files:
 rel=p.relative_to(D);s=str(rel)
 assert p.suffix not in {'.py','.pyc','.pyo'},s
 assert not s.startswith(('research/','docs/','.github/')),s
 assert '.pre_' not in p.name and 'pre_phase' not in p.name,s
assert (D/'index.html').exists() and (D/'_headers').exists() and (D/'config/build-manifest.json').exists()
assert (R/'wrangler.toml').read_text().find('pages_build_output_dir = "dist"')>=0
# Every compacted league snapshot with starter slots must have an explicit non-empty position-model contract.
import json
for cur in (D/'data/research/leagues').glob('*/current/milestone5_current.json') if (D/'data/research/leagues').exists() else []:
 data=json.loads(cur.read_text(encoding='utf-8'))
 comp=data.get('runtime_compaction') or {}
 assert comp.get('position_models'), f'missing position-aware runtime compaction: {cur.relative_to(D)}'
 assert int(comp.get('runtime_player_count',-1)) <= int(comp.get('original_player_count',-1)), f'invalid compaction counts: {cur.relative_to(D)}'
 allowed=set(comp.get('position_models') or [])
 for row in data.get('players') or []:
  assert str(row.get('position_model') or '') in allowed, f'irrelevant position leaked into compact snapshot: {cur.relative_to(D)} {row.get("position_model")}'
print(f'PASS integrity_dist_hygiene_test files={len(files)}')
