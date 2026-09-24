#!/usr/bin/env python3
"""Integrity checks for deduplicated league current-snapshot storage."""
from __future__ import annotations
import argparse,hashlib,json,sys
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'research'))
from current_snapshot_storage import (  # noqa:E402
    DEFAULT_REGISTRY,
    STORAGE_FORMAT,
    active_current_snapshot_paths,
    load_current_snapshot,
    read_json,
    split_manifest_shared_refs,
)

parser=argparse.ArgumentParser()
parser.add_argument(
    '--storage-only',
    action='store_true',
    help='validate split storage without governance hashes; production CI omits this flag',
)
parser.add_argument(
    '--registry',
    default=str(DEFAULT_REGISTRY),
    help='generated active registry; retired namespaces are historical-only',
)
args=parser.parse_args()

leagues_root=ROOT/'data/research/leagues'

paths=active_current_snapshot_paths(
    args.registry,
    root=ROOT,
    leagues_root=leagues_root,
)
assert paths,'no active-registry current snapshots found'

active_path_set={p.resolve() for p in paths}

all_current=sorted(
    leagues_root.glob('*/current/milestone5_current.json')
)

retired_current=[
    p for p in all_current
    if p.resolve() not in active_path_set
]

retired_refs=split_manifest_shared_refs(
    retired_current,
    root=ROOT,
)

missing_retired_refs=sorted(
    str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p)
    for p in retired_refs
    if not p.exists()
)

assert not missing_retired_refs,(
    'retired current evidence has missing shared artifacts: '
    +repr(missing_retired_refs[:5])
)

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for c in iter(lambda:f.read(1024*1024),b''): h.update(c)
    return h.hexdigest()

cache={};refs=set();by_sig=defaultdict(set);by_slice_base=defaultdict(set);hydrated_bytes=0
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

    slice_key=(
        raw.get('season'),
        raw.get('week'),
        str(raw.get('season_type') or ''),
    )
    by_slice_base[slice_key].add(st['player_base'])

    overlay=read_json(ROOT/st['scoring_overlay'],{}) or {}
    assert isinstance(overlay.get('player_overrides'),dict),f'player override map missing/invalid: {lid}'

    if not args.storage_only:
        gov=read_json(p.parents[1]/'governance/active_release.json',{}) or {}
        assert (gov.get('checks') or {}).get('current_storage_integrity') is True,f'governance did not validate shared current storage: {lid}'
        line=gov.get('model_lineage') or {}
        assert (line.get('artifact_sha256') or {}).get('current_snapshot')==sha(p),f'governance current manifest hash mismatch: {lid}'
        governed=line.get('shared_current_artifacts') or {}
        for key in ('player_base','scoring_overlay'):
            row=governed.get(key) or {}
            assert row.get('path')==st[key],f'governance shared path mismatch: {lid} {key}'
            assert row.get('sha256')==sha(ROOT/st[key]),f'governance shared hash mismatch: {lid} {key}'

all_shared=list(
    (ROOT/'data/research/shared/current').rglob('*.json')
)
assert all_shared,'shared current store missing'

owned_refs=refs|retired_refs

assert all(
    p.resolve() in owned_refs
    for p in all_shared
),f'unreferenced shared current artifacts exist: {[str(p.relative_to(ROOT)) for p in all_shared if p.resolve() not in owned_refs][:5]}'

shared=[
    p for p in all_shared
    if p.resolve() in refs
]

assert shared,'active current snapshots reference no shared current artifacts'
assert sum(len(v) for v in by_sig.values())<=len(paths)

assert all(len(v)==1 for v in by_slice_base.values()),(
    'same-time current snapshots must share one player base: '
    + repr({
        key: sorted(values)
        for key, values in by_slice_base.items()
        if len(values) != 1
    })
)

manifest_bytes=sum(p.stat().st_size for p in paths)
shared_bytes=sum(p.stat().st_size for p in shared)
stored_bytes=manifest_bytes+shared_bytes
assert manifest_bytes<500_000,f'league manifests unexpectedly large: {manifest_bytes}'
assert hydrated_bytes>0,'unable to measure hydrated current-snapshot size'
assert stored_bytes<hydrated_bytes*.35,(
    f'shared current storage insufficiently deduplicated: stored={stored_bytes} hydrated={hydrated_bytes} '
    f'ratio={stored_bytes/hydrated_bytes:.3f}'
)

# Capacity guard must scale with the managed portfolio.  The historical 19-league
# ceiling was 40 MB.  Preserve exactly that budget at 19 leagues while allowing
# 2 MB for each additional current league:
#
#   19 leagues -> 40 MB
#   22 leagues -> 46 MB
#
# This is only a secondary runaway-size guard.  The stronger efficiency invariant
# above still requires total stored current data to remain below 35% of the fully
# hydrated payload, so adding leagues cannot silently permit poor deduplication.
shared_budget_bytes=2_000_000 + 2_000_000*len(paths)
assert shared_bytes<shared_budget_bytes,(
    f'shared current store runaway size: shared={shared_bytes} '
    f'budget={shared_budget_bytes} leagues={len(paths)}'
)

# Browser hydration is modular now. Validate the hydrator and every current
# specialist consumer directly instead of requiring a literal source-shell tag.
store_path=ROOT/'app/current-snapshot-store.js'
assert store_path.exists(),'current snapshot browser hydrator missing'
store=store_path.read_text(encoding='utf-8')
assert 'FIECurrentSnapshotStore' in store
assert "const FORMAT='fie-current-split-v1'" in store
assert 'scoring_overlay' in store and 'included_player_ids' in store
assert 'player_overrides' in store

for src in ['app/kicker-intelligence.js','app/dst-intelligence.js']:
    txt=(ROOT/src).read_text(encoding='utf-8')
    assert 'FIECurrentSnapshotStore' in txt,f'{src} bypasses shared current hydrator'

print(
    f'PASS integrity_current_storage_test leagues={len(paths)} '
    f'shared_files={len(shared)} manifest_bytes={manifest_bytes} '
    f'shared_bytes={shared_bytes} shared_budget={shared_budget_bytes} '
    f'hydrated_bytes={hydrated_bytes} '
    f'storage_ratio={stored_bytes/hydrated_bytes:.3f} '
    f'retired_manifests={len(retired_current)} '
    f'retired_shared_refs={len(retired_refs)}'
)
