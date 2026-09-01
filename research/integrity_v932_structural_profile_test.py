#!/usr/bin/env python3
"""V9.3.2 structural-fingerprint regression across all current enabled leagues."""
from pathlib import Path
import json

from league_profile import structural_contract, structural_settings, sha256_json
from current_snapshot_storage import load_current_snapshot

R=Path(__file__).resolve().parents[1]

# Operational Sleeper progress fields must not invalidate a structural profile.
base={
    'type':3,'best_ball':0,'waiver_budget':1000,
    'daily_waivers_last_ran':100,'leg':2,'last_chopped_leg':1,
    'reserve_slots':5
}
mut={
    **base,
    'daily_waivers_last_ran':999,
    'leg':9,
    'last_chopped_leg':8
}
a=structural_contract(
    '123456','CHOPPED',{'rec':1},['QB','RB','BN'],
    base,18,'2026','regular'
)
b=structural_contract(
    '123456','CHOPPED',{'rec':1},['QB','RB','BN'],
    mut,18,'2026','regular'
)
assert sha256_json(a)==sha256_json(b)
assert 'leg' not in structural_settings(base)
assert 'daily_waivers_last_ran' not in structural_settings(base)

# Genuine scoring/roster structure changes must invalidate.
assert sha256_json(a)!=sha256_json(
    structural_contract(
        '123456','CHOPPED',{'rec':.5},['QB','RB','BN'],
        mut,18,'2026','regular'
    )
)
assert sha256_json(a)!=sha256_json(
    structural_contract(
        '123456','CHOPPED',{'rec':1},['QB','RB','WR','BN'],
        mut,18,'2026','regular'
    )
)

# Validate every enabled league that currently has a current snapshot. The old
# test hard-coded 19 leagues; portfolio onboarding now makes this registry-driven.
reg=json.loads((R/'data/research/leagues/registry.json').read_text())
enabled=[
    str(lid) for lid,row in sorted((reg.get('leagues') or {}).items())
    if row.get('enabled',True)
]

checked=[]
existing_current=[]
for lid in enabled:
    profile_path=R/f'data/research/leagues/{lid}/profile.json'
    current_path=R/f'data/research/leagues/{lid}/current/milestone5_current.json'
    assert profile_path.is_file(),f'{lid}: profile.json missing'
    if not current_path.is_file():
        continue

    existing_current.append(lid)
    profile=json.loads(profile_path.read_text())
    cur=load_current_snapshot(current_path,root=R)
    pf=((cur.get('scoring_provenance') or {}).get('profile_fields') or {})
    assert pf,f'{lid}: current snapshot missing captured live profile provenance'

    live=structural_contract(
        str(lid),
        profile.get('format'),
        cur.get('scoring_settings') or profile.get('scoring_settings') or {},
        pf.get('roster_positions') or [],
        pf.get('settings') or {},
        pf.get('total_rosters'),
        pf.get('season'),
        pf.get('season_type'),
        profile.get('research_constraints') or [],
    )
    got=sha256_json(live)
    exp=profile.get('profile_fingerprint')
    assert got==exp,(
        f'{lid}: corrected captured-live fingerprint {got} '
        f'!= stored structural fingerprint {exp}'
    )
    checked.append(lid)

assert checked==existing_current,(
    f'structural current-profile coverage mismatch: '
    f'checked={checked} existing_current={existing_current}'
)
assert checked,'no enabled current profiles were validated'

print(
    f'PASS V9.3.2 structural live-profile regression: '
    f'{len(checked)}/{len(existing_current)} current enabled profiles match'
)
