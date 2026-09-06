#!/usr/bin/env python3
"""Regression contract for the consolidated 15-point implementation plan."""

from pathlib import Path

R = Path(__file__).resolve().parents[1]


def read(path):
    return (R / path).read_text(encoding="utf-8")


league = read("research/league_profile.py")
runtime = read("app/runtime-foundation.js")
ui = read("app/decision-ui.js")
worker = read("app/draft-monte-carlo-worker.js")
vf = read("app/value-finder.js")
cal = read("app/core/value-calibration-guard.js")
dc = read("app/core/data-client.js")
wf = read(".github/workflows/build-fie-current.yml")
rel = read("tools/release_build.py")
sync = read("tools/sync_league_app_snapshots.py")


checks = {
    1: (
        "type_code == 3" in league
    ),

    2: (
        "const ScoringSupport=" in runtime
        and "relevantPositions" in runtime
        and "researchAllowed:weeklyExact" in runtime
    ),

    3: (
        "duplicateScarcityRemoved:true" in cal
        and "rawCanonicalBaseValue" in cal
        and "vor===null" in cal
    ),

    4: (
        "activeLeagueId:null,selectedSavedLeagueId:null"
        in runtime
        and "generation:0" in runtime
        and "AbortController" in runtime
    ),

    5: (
        "PANEL_IDS" in ui
        and "researchPanel" in ui
        and "Diagnostics" in runtime
    ),

    6: (
        "explicitForLeague" in runtime
        and "source:'explicit_override'" in runtime
        and "resolveFor" in runtime
    ),

    7: (
        "exactRosterContribution" in ui
        and "LineupOptimizer" in ui
        and "rosterUtility" in ui
    ),

    8: (
        "FIE positional rank" in ui
        and "League scoring fit" in ui
        and "<b>Bottom line:</b>" in ui
    ),

    9: (
        "tr.onclick=()=>window.openDrawer" in ui
        or "tr.onclick=()=>window.openDrawer?." in ui
    ),

    10: (
        "<b>Decision separation:</b>" in ui
        and (
            "Draft Board remains independent of selected roster" in ui
            or "Draft Board is independent of your owned roster" in ui
        )
    ),

    11: (
        "researchAllowed" in runtime
        and "weeklyExact" in runtime
        and "seasonExact" in runtime
    ),

    12: (
        "reversal_round" in runtime
        and "reversalRound" in runtime
    ),

    # The worker receives cancellation messages through
    # m.type === 'cancel', while result messages are emitted
    # with {type:'batch', ...}.
    13: (
        "type==='cancel'" in worker
        and "type:'batch'" in worker
        and "cancelled" in worker
    ),

    14: (
        "const VF_CACHE=" in vf
        and "vfBaseCacheKey" in vf
        and "vfLiveCacheKey" in vf
    ),

    15: (
        "fie-league-core-v1" in dc
        and "prefetchLeagueSnapshots" in dc
        and "build_league_app_snapshots.py" in wf
        and "sync_league_app_snapshots.py" in rel
    ),
}


failed = [
    number
    for number, passed in checks.items()
    if not passed
]

assert not failed, (
    "15-point completion regression(s): "
    f"{failed}"
)

assert (
    "value-calibration-guard.js" in sync
), (
    "dist builder must load "
    "cross-position calibration guard"
)

print(
    "PASS consolidated "
    "15-point implementation contract"
)
