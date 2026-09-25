#!/usr/bin/env python3
"""V9.3.2 structural-fingerprint regression across all current enabled leagues."""
from pathlib import Path
import json

from league_profile import (
    research_contract,
    research_fingerprint_from_profile,
    structural_contract,
    structural_settings,
    sha256_json,
)
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

    live_structural=structural_contract(
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
    live_profile_fp=sha256_json(live_structural)

    # Full structural drift is retained as provenance. Operational waiver
    # scheduling must not invalidate otherwise compatible historical research.
    assert cur.get('live_profile_fingerprint')==live_profile_fp,(
        f'{lid}: captured live structural fingerprint metadata mismatch'
    )
    if live_profile_fp != profile.get('profile_fingerprint'):
        assert cur.get('profile_diff'),(
            f'{lid}: structural drift exists but profile_diff is empty'
        )

    profile_research_fp=research_fingerprint_from_profile(profile)
    live_research=research_contract(
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
    live_research_fp=sha256_json(live_research)

    assert cur.get('profile_research_fingerprint')==profile_research_fp,(
        f'{lid}: stored profile research fingerprint metadata mismatch'
    )
    assert cur.get('live_research_fingerprint')==live_research_fp,(
        f'{lid}: live research fingerprint metadata mismatch'
    )
    assert live_research_fp==profile_research_fp,(
        f'{lid}: genuine research-contract drift '
        f'{live_research_fp} != {profile_research_fp}'
    )
    assert cur.get('profile_current_match') is True,(
        f'{lid}: current snapshot does not declare research-compatible profile'
    )
    checked.append(lid)

assert checked==existing_current,(
    f'structural current-profile coverage mismatch: '
    f'checked={checked} existing_current={existing_current}'
)
assert checked,'no enabled current profiles were validated'

print(
    f'PASS V9.3.2 research-compatible live-profile regression: '
    f'{len(checked)}/{len(existing_current)} current enabled profiles match'
)
