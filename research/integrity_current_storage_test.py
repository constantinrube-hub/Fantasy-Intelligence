#!/usr/bin/env python3
"""Integrity checks for deduplicated league current-snapshot storage."""
from __future__ import annotations
import hashlib,json,sys
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'research'))
from current_snapshot_storage import STORAGE_FORMAT,load_current_snapshot,read_json  # noqa:E402

paths=sorted((ROOT/'data/research/leagues').glob('*/current/milestone5_current.json'))
assert paths,'no league current snapshots found'

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for c in iter(lambda:f.read(1024*1024),b''): h.update(c)
    return h.hexdigest()

cache={};refs=set();by_sig=defaultdict(set);hydrated_bytes=0
for p in paths:
    raw=read_json(p,{}) or {};lid=p.parents[1].name
    assert (raw.get('storage') or {}).get('format')==STORAGE_FORMAT,f'legacy full current snapshot remains: {p.relative_to(ROOT)}'
    assert 'players' not in raw and 'scoring_settings' not in raw,f'duplicated payload remains in league manifest: {p.relative_to(ROOT)}'
    st=raw['storage']
    for key in ('player_base','scoring_overlay'):
        ref=ROOT/st[key]
        assert ref.exists(),f'missing shared current artifact: {st[key]}'
        refs.add(ref.resolve())
    assert str(raw.get('league_id') or '')==lid,f'league namespace mismatch: {p.relative_to(ROOT)}'
    snap=load_current_snapshot(p,root=ROOT,cache=cache)
    hydrated_bytes+=len(json.dumps(snap,separators=(',',':'),allow_nan=False).encode('utf-8'))
    expected=int((raw.get('summary') or {}).get('players') or st.get('player_count') or 0)
    assert len(snap.get('players') or [])==expected,f'hydrated player count mismatch: {lid}'
    assert snap.get('scoring_settings'),f'hydrated scoring settings missing: {lid}'
    assert str(snap.get('scoring_signature') or '')==str(raw.get('scoring_signature') or ''),f'hydrated scoring signature mismatch: {lid}'
    by_sig[str(raw.get('scoring_signature') or '')].add(st['scoring_overlay'])
    gov=read_json(p.parents[1]/'governance/active_release.json',{}) or {}
    assert (gov.get('checks') or {}).get('current_storage_integrity') is True,f'governance did not validate shared current storage: {lid}'
    line=gov.get('model_lineage') or {}
    assert (line.get('artifact_sha256') or {}).get('current_snapshot')==sha(p),f'governance current manifest hash mismatch: {lid}'
    governed=line.get('shared_current_artifacts') or {}
    for key in ('player_base','scoring_overlay'):
        row=governed.get(key) or {}
        assert row.get('path')==st[key],f'governance shared path mismatch: {lid} {key}'
        assert row.get('sha256')==sha(ROOT/st[key]),f'governance shared hash mismatch: {lid} {key}'

shared=list((ROOT/'data/research/shared/current').rglob('*.json'))
assert shared,'shared current store missing'
assert all(p.resolve() in refs for p in shared),f'unreferenced shared current artifacts exist: {[str(p.relative_to(ROOT)) for p in shared if p.resolve() not in refs][:5]}'
assert sum(len(v) for v in by_sig.values())<=len(paths)

manifest_bytes=sum(p.stat().st_size for p in paths)
shared_bytes=sum(p.stat().st_size for p in shared)
stored_bytes=manifest_bytes+shared_bytes
assert manifest_bytes<500_000,f'league manifests unexpectedly large: {manifest_bytes}'
assert hydrated_bytes>0,'unable to measure hydrated current-snapshot size'
assert stored_bytes<hydrated_bytes*.35,(
    f'shared current storage insufficiently deduplicated: stored={stored_bytes} hydrated={hydrated_bytes} '
    f'ratio={stored_bytes/hydrated_bytes:.3f}'
)
assert shared_bytes<40_000_000,f'shared current store runaway size: {shared_bytes}'

# Browser hydration is modular now. Validate the hydrator and every current
# specialist consumer directly instead of requiring a literal source-shell tag.
store_path=ROOT/'app/current-snapshot-store.js'
assert store_path.exists(),'current snapshot browser hydrator missing'
store=store_path.read_text(encoding='utf-8')
assert 'FIECurrentSnapshotStore' in store
assert "const FORMAT='fie-current-split-v1'" in store
assert 'scoring_overlay' in store and 'included_player_ids' in store

for src in ['app/kicker-intelligence.js','app/dst-intelligence.js']:
    txt=(ROOT/src).read_text(encoding='utf-8')
    assert 'FIECurrentSnapshotStore' in txt,f'{src} bypasses shared current hydrator'

print(f'PASS integrity_current_storage_test leagues={len(paths)} shared_files={len(shared)} manifest_bytes={manifest_bytes} shared_bytes={shared_bytes} hydrated_bytes={hydrated_bytes} storage_ratio={stored_bytes/hydrated_bytes:.3f}')
