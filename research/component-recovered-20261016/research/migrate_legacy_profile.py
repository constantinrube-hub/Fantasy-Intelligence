#!/usr/bin/env python3
"""Non-destructively migrate the current single-profile FIE artifacts.

The source files are never edited. JSON destinations are stamped with the exact
League-ID profile identity so the browser/governance can prove namespace scope.
"""
from __future__ import annotations
import argparse, hashlib, json
from datetime import datetime, timezone
from pathlib import Path
from league_profile import require_league_id, write_json
from stamp_league_artifacts import artifact_scoring_signature

IDENTITY_FIELDS=('league_id','league_format','profile_fingerprint','profile_scoring_signature')

def sha_bytes(data: bytes) -> str: return hashlib.sha256(data).hexdigest()
def canonical_bytes(obj: dict) -> bytes: return (json.dumps(obj,indent=2,allow_nan=False)+'\n').encode('utf-8')

def transformed_json(src: Path, profile: dict) -> bytes:
    obj=json.loads(src.read_text(encoding='utf-8'))
    psig=profile.get('scoring_signature'); asig=artifact_scoring_signature(obj)
    # Current/governance can legitimately be stale in the legacy repo. Historical
    # milestones must match the profile; stale live artifacts remain copied but closed.
    if src.name.startswith('milestone') and 'current' not in src.parts and psig and asig and str(psig)!=str(asig):
        raise SystemExit(f'Refusing migration: {src} scoring {asig} != profile {psig}')
    obj['league_id']=str(profile['league_id'])
    obj['league_format']=profile.get('format')
    obj['profile_fingerprint']=profile.get('profile_fingerprint')
    obj['profile_scoring_signature']=psig
    return canonical_bytes(obj)

def write_expected(dst: Path, expected: bytes) -> str:
    dst.parent.mkdir(parents=True,exist_ok=True)
    if dst.exists():
        got=dst.read_bytes()
        if got!=expected: raise SystemExit(f'Refusing to overwrite different existing destination: {dst}')
    else: dst.write_bytes(expected)
    return sha_bytes(expected)

def copy_json(src: Path,dst: Path,profile: dict,copied: list[dict]):
    if not src.exists(): return
    expected=transformed_json(src,profile); h=write_expected(dst,expected)
    copied.append({'source':str(src),'destination':str(dst),'sha256':h})

def main():
    p=argparse.ArgumentParser();p.add_argument('--league-id',required=True);p.add_argument('--research-root',default='data/research');p.add_argument('--profile',required=True)
    a=p.parse_args(); lid=require_league_id(a.league_id); root=Path(a.research_root); dest=root/'leagues'/lid
    profile=json.loads(Path(a.profile).read_text(encoding='utf-8'))
    if str(profile.get('league_id'))!=lid: raise SystemExit('profile League ID mismatch')
    copied=[]
    for i in range(1,7): copy_json(root/f'milestone{i}.json',dest/f'milestone{i}.json',profile,copied)
    copy_json(root/'current'/'milestone5_current.json',dest/'current'/'milestone5_current.json',profile,copied)
    # Do not copy legacy active_release: its artifact paths/hashes are global. Phase 2
    # rebuilds a correct namespaced governance manifest immediately after migration.
    copy_json(root/'governance'/'operator_override.json',dest/'governance'/'operator_override.json',profile,copied)
    profile_dst=dest/'profile.json'; profile_bytes=(json.dumps(profile,indent=2,sort_keys=True)+'\n').encode(); write_expected(profile_dst,profile_bytes)
    manifest={'schema_version':2,'league_id':lid,'migration':'legacy_single_profile_copy','non_destructive':True,'migrated_at':datetime.now(timezone.utc).isoformat(),'copied':copied}
    write_json(dest/'migration_manifest.json',manifest)
    print(f'Migrated {len(copied)} artifacts into {dest}; legacy files were left untouched.')
if __name__=='__main__':main()
