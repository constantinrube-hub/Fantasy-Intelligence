#!/usr/bin/env python3
"""Regression for reproducible V9.3.2 build/deploy metadata."""
from __future__ import annotations
import importlib.util
import itertools
import json
import tempfile
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
assert "active_ids=sorted(" in dist_src
assert "for lid in active_ids:" in dist_src
assert "for d in sorted(leagues.iterdir(),key=lambda p:p.name):" not in dist_src
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

# Windows/mixed source line endings must be finalized before manifest hashing.
spec=importlib.util.spec_from_file_location('fie_release_build',ROOT/'tools/release_build.py')
release_builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(release_builder)
with tempfile.TemporaryDirectory() as directory:
 fixture=Path(directory)
 texts={'index.html':b'<html>\r\n</html>\n','_headers':b'/*\r\n  X-Test: yes\r\n',
        '_routes.json':b'{\r\n}\r\n','app/core/nested.js':b'// code\r\nconst x=1;\n',
        'app/style.css':b'body {}\r\n'}
 untouched={'app/icon.png':b'\x00\r\n\xff','data/research/evidence.json':b'{\r\n}\r\n',
            'config/locked-input.json':b'{\r\n}\r\n'}
 for rel,raw in {**texts,**untouched}.items():
  path=fixture/rel;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
 release_builder.normalize_deployment_code(fixture)
 for rel,raw in texts.items():assert (fixture/rel).read_bytes()==raw.replace(b'\r\n',b'\n'),rel
 for rel,raw in untouched.items():assert (fixture/rel).read_bytes()==raw,rel
 before={rel:(fixture/rel).read_bytes() for rel in texts}
 release_builder.normalize_deployment_code(fixture)
 assert before=={rel:(fixture/rel).read_bytes() for rel in texts},'normalization must be idempotent'

print('PASS V9.3.2 deterministic build manifest')
