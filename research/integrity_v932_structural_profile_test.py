#!/usr/bin/env python3
"""V9.3.2 structural-fingerprint regression across all stored managed leagues."""
from pathlib import Path
import json
from league_profile import structural_contract, structural_settings, sha256_json
from current_snapshot_storage import load_current_snapshot
R=Path(__file__).resolve().parents[1]
# Operational Sleeper progress fields must not invalidate a structural profile.
base={'type':3,'best_ball':0,'waiver_budget':1000,'daily_waivers_last_ran':100,'leg':2,'last_chopped_leg':1,'reserve_slots':5}
mut={**base,'daily_waivers_last_ran':999,'leg':9,'last_chopped_leg':8}
a=structural_contract('123456','CHOPPED',{'rec':1},['QB','RB','BN'],base,18,'2026','regular')
b=structural_contract('123456','CHOPPED',{'rec':1},['QB','RB','BN'],mut,18,'2026','regular')
assert sha256_json(a)==sha256_json(b)
assert 'leg' not in structural_settings(base) and 'daily_waivers_last_ran' not in structural_settings(base)
# Genuine scoring/roster structure changes must invalidate.
assert sha256_json(a)!=sha256_json(structural_contract('123456','CHOPPED',{'rec':.5},['QB','RB','BN'],mut,18,'2026','regular'))
assert sha256_json(a)!=sha256_json(structural_contract('123456','CHOPPED',{'rec':1},['QB','RB','WR','BN'],mut,18,'2026','regular'))
# Reproduce every stored current snapshot's already-captured live Sleeper metadata with the corrected contract.
reg=json.loads((R/'data/research/leagues/registry.json').read_text())
checked=[]
for lid,row in sorted((reg.get('leagues') or {}).items()):
    if not row.get('enabled',True): continue
    profile=json.loads((R/f'data/research/leagues/{lid}/profile.json').read_text())
    cur=load_current_snapshot(R/f'data/research/leagues/{lid}/current/milestone5_current.json',root=R)
    pf=((cur.get('scoring_provenance') or {}).get('profile_fields') or {})
    if not pf: continue
    live=structural_contract(str(lid),profile.get('format'),cur.get('scoring_settings') or profile.get('scoring_settings') or {},pf.get('roster_positions') or [],pf.get('settings') or {},pf.get('total_rosters'),pf.get('season'),pf.get('season_type'),profile.get('research_constraints') or [])
    got=sha256_json(live);exp=profile.get('profile_fingerprint')
    assert got==exp,f'{lid}: corrected captured-live fingerprint {got} != stored structural fingerprint {exp}'
    checked.append(lid)
assert len(checked)==19,f'expected 19 managed current profiles, verified {len(checked)}'
print(f'PASS V9.3.2 structural live-profile regression: {len(checked)}/19 corrected structural fingerprints match')
