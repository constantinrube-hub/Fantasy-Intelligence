#!/usr/bin/env python3
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
d=json.loads((ROOT/'config/build-manifest.json').read_text());release=json.loads((ROOT/'config/release.json').read_text())
assert d.get('schema_version')==2
assert d.get('app_version')==release['release']
assert d.get('runtime_version')==release['runtime']
assert d.get('runtime_research_scope')=='league_namespaced_only'
for name,row in (d.get('files') or {}).items():
 f=ROOT/row['path'];assert f.exists(),f'missing manifest file {name}: {f}'
 got=hashlib.sha256(f.read_bytes()).hexdigest();assert got==row['sha256'],f'stale manifest hash: {row["path"]}'
print('PASS integrity_build_manifest_test')
