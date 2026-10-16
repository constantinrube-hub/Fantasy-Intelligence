#!/usr/bin/env python3
from __future__ import annotations

from reconcile_current_profile_snapshots import captured_structural_fingerprint
from league_profile import structural_contract, sha256_json

profile={
    "league_id":"123456789",
    "format":"DYNASTY_BESTBALL",
    "scoring_settings":{"rec":1.0,"pass_td":6.0},
    "profile_fingerprint":None,
}
base_settings={
    "type":2,
    "best_ball":1,
    "daily_waivers":1,
    "daily_waivers_days":9564,
    "waiver_budget":1000,
    "leg":1,
    "daily_waivers_last_ran":3,
}
pf={
    "roster_positions":["QB","RB","WR","TE","FLEX","BN"],
    "settings":base_settings,
    "total_rosters":12,
    "season":"2026",
    "season_type":"regular",
}
contract=structural_contract(
    profile["league_id"],profile["format"],profile["scoring_settings"],
    pf["roster_positions"],pf["settings"],pf["total_rosters"],
    pf["season"],pf["season_type"],[]
)
profile["profile_fingerprint"]=sha256_json(contract)

current={
    "scoring_settings":profile["scoring_settings"],
    "scoring_provenance":{"profile_fields":pf},
}
assert captured_structural_fingerprint(
    profile,current
)==profile["profile_fingerprint"]

# Operational progress drift is intentionally ignored.
operational={
    **pf,
    "settings":{
        **base_settings,
        "leg":9,
        "daily_waivers_last_ran":99,
    },
}
current_operational={
    "scoring_settings":profile["scoring_settings"],
    "scoring_provenance":{"profile_fields":operational},
}
assert captured_structural_fingerprint(
    profile,current_operational
)==profile["profile_fingerprint"]

# Genuine waiver-structure drift is not ignored.
structural={
    **pf,
    "settings":{
        **base_settings,
        "daily_waivers":0,
        "daily_waivers_days":9578,
    },
}
current_structural={
    "scoring_settings":profile["scoring_settings"],
    "scoring_provenance":{"profile_fields":structural},
}
assert captured_structural_fingerprint(
    profile,current_structural
)!=profile["profile_fingerprint"]

print("PASS current/profile reconcile fingerprint contract")
