#!/usr/bin/env python3
"""V9.3.2 structural-fingerprint regression across all current enabled leagues."""
from pathlib import Path
import json

from league_profile import (
    passive_reserve_capacity_expansion,
    research_contract,
    research_fingerprint_from_profile,
    research_roster_positions_for_live_state,
    roster_evolution_status,
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

# A Tuesday-applied declared stage may be pending after Monday Night Football.
# It remains compatible until Sleeper exposes the next official roster shape.
evolution_profile = {
    "roster_positions": ["QB", "BN"],
    "roster_evolution": {
        "season": 2026, "application_weekday": "TUESDAY", "season_complete_week": 17,
        "weekly_additions": {"1": ["BN"], "2": ["FLEX"]},
    },
}
pending = roster_evolution_status(evolution_profile, ["QB", "BN"], 2026, 1)
assert pending["recognized"] and pending["scheduled_addition_pending"]
stage_one = roster_evolution_status(evolution_profile, ["QB", "BN", "BN"], 2026, 1)
assert stage_one["recognized"] and stage_one["matched_stage"] == 1
assert not roster_evolution_status(evolution_profile, ["QB", "WR", "BN"], 2026, 1)["recognized"]
assert research_roster_positions_for_live_state(evolution_profile, ["QB", "BN", "BN"], 2026, 1)[0] == ["QB", "BN"]
assert passive_reserve_capacity_expansion(["QB", "BN"], ["QB", "BN", "BN"])

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
    research_positions, evolution = research_roster_positions_for_live_state(
        profile, pf.get('roster_positions') or [], cur.get('season'), cur.get('week'),
    )
    live_research=research_contract(
        str(lid),
        profile.get('format'),
        cur.get('scoring_settings') or profile.get('scoring_settings') or {},
        research_positions,
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
    raw_live_research = research_contract(
        str(lid), profile.get('format'),
        cur.get('scoring_settings') or profile.get('scoring_settings') or {},
        pf.get('roster_positions') or [], pf.get('settings') or {}, pf.get('total_rosters'),
        pf.get('season'), pf.get('season_type'), profile.get('research_constraints') or [],
    )
    compatibility_exception = bool(evolution.get('recognized')) or passive_reserve_capacity_expansion(
        profile.get('roster_positions'), pf.get('roster_positions'),
    )
    if compatibility_exception and live_profile_fp != profile.get('profile_fingerprint'):
        # Snapshots written before a declared roster-evolution policy carry the
        # raw live hash.  The next current refresh rewrites this metadata.
        assert cur.get('live_research_fingerprint') in {live_research_fp, sha256_json(raw_live_research)}, (
            f'{lid}: live research fingerprint metadata mismatch'
        )
        assert cur.get('profile_diff'), f'{lid}: compatible structural change missing profile_diff'
    else:
        assert cur.get('live_research_fingerprint')==live_research_fp,(
            f'{lid}: live research fingerprint metadata mismatch'
        )
    assert live_research_fp==profile_research_fp,(
        f'{lid}: genuine research-contract drift '
        f'{live_research_fp} != {profile_research_fp}'
    )
    if not (compatibility_exception and live_profile_fp != profile.get('profile_fingerprint')):
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
