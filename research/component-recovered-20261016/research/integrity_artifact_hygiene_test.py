#!/usr/bin/env python3
"""Ensure active runtime/release references never resolve through quarantine/legacy roots."""
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def strings(x):
    if isinstance(x,dict):
        for v in x.values(): yield from strings(v)
    elif isinstance(x,list):
        for v in x: yield from strings(v)
    elif isinstance(x,str): yield x

# The browser runtime must use the league namespace, never the legacy root current artifact.
html=(ROOT/'index.html').read_text()
assert "return id?`data/research/leagues/${id}`:null" in html
assert "rr.path('current/milestone5_current.json')" in html

# Market manifest is the only active market discovery surface. Quarantine may exist physically,
# but no active manifest entry may point to it.
market=ROOT/'data/research/market/sleeper/manifest.json'
if market.exists():
    d=json.loads(market.read_text())
    bad=[s for s in strings(d) if 'quarantine' in s.lower()]
    assert not bad,f'active market manifest references quarantine: {bad[:3]}'

# League-specific active releases must be league scoped, have extant current snapshots, and
# contain no quarantine references.
files=list((ROOT/'data/research/leagues').glob('*/governance/active_release.json'))
assert files,'no league-specific governance files found'
for p in files:
    lid=p.parents[1].name;d=json.loads(p.read_text())
    assert str(d.get('league_id'))==lid,f'league ID mismatch in {p}'
    bad=[s for s in strings(d) if 'quarantine' in s.lower()]
    assert not bad,f'quarantine reference in {p}: {bad[:2]}'
    rel=(d.get('current_snapshot') or {}).get('path')
    if rel: assert (ROOT/rel).exists(),f'missing current snapshot referenced by {p}: {rel}'

# Legacy root governance is retained for historical provenance only and must not be a runtime URL.
legacy='data/research/governance/active_release.json'
for src in ['app/runtime-foundation.js','app/current-player-features.js','app/decision-model-v9.js','app/value-finder.js']:
    assert legacy not in (ROOT/src).read_text(),f'legacy governance runtime reference in {src}'
print('PASS integrity_artifact_hygiene_test')
