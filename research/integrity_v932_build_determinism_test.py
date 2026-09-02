#!/usr/bin/env python3
"""Regression for reproducible V9.3.2 build/deploy metadata."""
from __future__ import annotations
import importlib.util
import itertools
import json
from pathlib import Path
import build_app_manifest

ROOT=Path(__file__).resolve().parents[1]
release=json.loads((ROOT/'config/release.json').read_text())
first=build_app_manifest.build()
second=build_app_manifest.build()

assert first==second,'build manifest changes across identical builds'
assert first.get('generated_at')==release.get('built_at'),(
    'build manifest generated_at must use canonical release built_at, not wall-clock time'
)
src=(ROOT/'research/build_app_manifest.py').read_text()
assert 'datetime.now' not in src and 'timezone.utc' not in src,(
    'wall-clock timestamps make committed dist permanently stale after validation rebuilds'
)

# Dist current compaction must not depend on filesystem enumeration order.
dist_src=(ROOT/'tools/build_dist.py').read_text()
assert "for d in sorted(leagues.iterdir(),key=lambda p:p.name):" in dist_src
assert "for e in sorted(entries,key=lambda x:str(x.get('lid',''))):" in dist_src

spec=importlib.util.spec_from_file_location('fie_build_dist',ROOT/'tools/build_dist.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
entries=[
    {'lid':'A','rows':[{'sleeper_id':'1','position_model':'QB','marker':'x'}]},
    {'lid':'B','rows':[{'sleeper_id':'1','position_model':'QB','marker':'y'}]},
    {'lid':'C','rows':[{'sleeper_id':'2','position_model':'QB','marker':'z'}]},
]
expected=None
for perm in itertools.permutations(entries):
    groups=mod.partition_compatible(list(perm))
    membership=[[e['lid'] for e in g['entries']] for g in groups]
    if expected is None: expected=membership
    assert membership==expected,(
        f'compact current partition depends on input/filesystem order: {membership} != {expected}'
    )
assert expected==[['A','C'],['B']], expected

print('PASS V9.3.2 deterministic build manifest')
