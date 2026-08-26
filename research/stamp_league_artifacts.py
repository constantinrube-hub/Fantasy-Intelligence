#!/usr/bin/env python3
"""Stamp generated research artifacts with immutable League-ID profile identity.

This is intentionally separate from M1-M6 model code: it namespaces provenance
without changing statistical calculations. It also fails if an artifact's scoring
signature disagrees with the captured profile.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def write(path: Path, obj: dict) -> None:
    tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(obj, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    tmp.replace(path)


def artifact_scoring_signature(obj: dict):
    return obj.get('scoring_signature') or (obj.get('scoring') or {}).get('signature')


def stamp(path: Path, profile: dict) -> None:
    obj=load(path)
    psig=profile.get('scoring_signature')
    asig=artifact_scoring_signature(obj)
    if psig and asig and str(psig)!=str(asig):
        raise SystemExit(f'{path}: scoring signature {asig} does not match profile {psig}')
    obj['league_id']=str(profile['league_id'])
    obj['league_format']=profile.get('format')
    obj['profile_fingerprint']=profile.get('profile_fingerprint')
    obj['profile_scoring_signature']=psig
    write(path,obj)
    print(f'Stamped {path} league={profile["league_id"]}')


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--profile', required=True)
    p.add_argument('artifacts', nargs='+')
    a=p.parse_args()
    profile=load(Path(a.profile))
    if not profile.get('league_id') or not profile.get('profile_fingerprint'):
        raise SystemExit('profile missing league_id/profile_fingerprint')
    for raw in a.artifacts:
        stamp(Path(raw), profile)

if __name__=='__main__': main()
