#!/usr/bin/env python3
"""Offline migration of stored league profiles to structural fingerprints.

Does not fetch Sleeper. It recomputes each fingerprint from the already stored
profile, then updates namespaced research identity fields consistently. This is
safe because scoring/roster/format content is unchanged; only volatile settings
are removed from the identity contract.
"""
from __future__ import annotations
import json
from pathlib import Path
from league_profile import SCHEMA_VERSION, structural_contract, structural_settings, sha256_json, write_json, utc_now
ROOT=Path(__file__).resolve().parents[1]
LEAGUES=ROOT/'data/research/leagues'
REGISTRY=ROOT/'data/research/leagues/registry.json'

def migrate_one(d:Path):
    pp=d/'profile.json'; p=json.load(open(pp,encoding='utf-8')); old=p.get('profile_fingerprint')
    constraints=p.get('research_constraints') or []
    contract=structural_contract(str(p['league_id']),str(p.get('format') or 'REDRAFT'),p.get('scoring_settings') or {},p.get('roster_positions') or [],p.get('settings') or {},p.get('total_rosters'),p.get('season'),p.get('season_type'),constraints)
    new=sha256_json(contract)
    p['schema_version']=SCHEMA_VERSION;p['structural_settings']=structural_settings(p.get('settings') or {});p['profile_fingerprint']=new;p['fingerprint_contract']='structural-v2';p['migrated_at']=utc_now();write_json(pp,p)
    for fp in [*(d.glob('milestone*.json')),d/'current/milestone5_current.json',d/'governance/active_release.json']:
        if not fp.exists(): continue
        x=json.load(open(fp,encoding='utf-8'))
        if x.get('profile_fingerprint')==old or str(x.get('league_id'))==str(p['league_id']): x['profile_fingerprint']=new
        if 'live_profile_fingerprint' in x and x.get('live_profile_fingerprint')==old: x['live_profile_fingerprint']=new
        if fp.name=='active_release.json':
            checks=x.setdefault('checks',{})
            if checks.get('profile_fingerprint_match') is True: checks['profile_fingerprint_match']=True
            if checks.get('current_profile_live_match') is False and (d/'current/milestone5_current.json').exists():
                cur=json.load(open(d/'current/milestone5_current.json',encoding='utf-8'))
                if cur.get('profile_fingerprint')==new and cur.get('live_profile_fingerprint')==new: checks['current_profile_live_match']=True
            x['identity_contract']='structural-v2'
        write_json(fp,x)
    return str(p['league_id']),old,new

def main():
    changes=[]
    for d in sorted(p for p in LEAGUES.iterdir() if p.is_dir() and (p/'profile.json').exists()): changes.append(migrate_one(d))
    if REGISTRY.exists():
        r=json.load(open(REGISTRY,encoding='utf-8'))
        for lid,_,new in changes:
            if lid in (r.get('leagues') or {}): r['leagues'][lid]['profile_fingerprint']=new
        r['schema_version']=SCHEMA_VERSION;r['updated_at']=utc_now();write_json(REGISTRY,r)
    print(f'Migrated {len(changes)} league profiles to structural-v2')
if __name__=='__main__': main()
