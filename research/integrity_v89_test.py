#!/usr/bin/env python3
"""Compatibility integrity test for the V8.9 lineage on the current V9.3.x modular runtime.

The historical test asserted exact literals inside the old monolithic index.html.
Those checks became stale as V9.3.x moved runtime, scoring and league-specific
logic into dedicated modules. This test keeps the important invariants without
requiring obsolete version strings or shell implementation details.
"""
from pathlib import Path
import json
from datetime import datetime, timezone

from statistical_guardrails import promotion_gate
from fie_research import latest_completed_season
from build_current_snapshot import inferred_nfl_season

root = Path(__file__).resolve().parents[1]

def read(rel):
    p = root / rel
    assert p.exists(), f"required runtime file missing: {rel}"
    return p.read_text()

# Current release / deployment contract
release = json.loads(read('config/release.json'))
health = read('functions/api/health.js')
proxy = read('functions/api/data/[[path]].js')

assert str(release.get('release', '')).startswith('9.3.'), release
assert 'FIE_RELEASE.release' in health

# V8.9 season-aware nflverse routing remains supported.
assert 'function seasonalNflverse(dataset, season)' in proxy
assert "if (parts.length === 3)" in proxy
assert "seasonalNflverse(parts[1], parts[2])" in proxy
assert "const y = String(season);" in proxy
for dataset in ('stats-regpost', 'weekly', 'snaps', 'depth', 'team'):
    assert dataset in proxy, f'missing season-aware nflverse dataset: {dataset}'

# Current modular runtime must be present.
runtime = read('app/v9.3.3-runtime-integrity.js')
snapshot = read('app/current-snapshot-store.js')
a3 = read('app/v9.3.4a3-score-performance.js')
d = read('app/v9.3.4d-starter-economics.js')
decision_ui = read('app/decision-ui.js')
dst = read('app/dst-intelligence.js')
kicker = read('app/kicker-intelligence.js')

assert "const VERSION='9.3.4A-B'" in runtime
assert 'ensureSeasonInvariant' in runtime
assert 'activeSeason' in runtime
assert 'sameContext' in runtime
assert 'weeklyProjectionSource' in runtime
assert 'Unavailable' in runtime

# Split current-snapshot storage and ordered runtime boot chain.
assert "const FORMAT='fie-current-split-v1'" in snapshot
assert 'included_player_ids' in snapshot
assert 'scoring_overlay' in snapshot
assert 'bootA3' in snapshot
assert 'bootC' in snapshot
assert 'bootD' in snapshot
assert 'bootE' in snapshot

# A3 keeps score publication linearized and replacement-aware.
assert "const VERSION='9.3.4A3'" in a3
assert 'fastReplacementLevels' in a3
assert 'fastProjectedReplacementLevels' in a3
assert 'fastAssignScores' in a3
assert 'starter-demand' in a3

# V9.3.4D is the current universal implementation of the V8.9 starter-slot
# economics invariant. It must support fixed slots, FLEX, Superflex and IDP.
assert "const VERSION='9.3.4D'" in d
assert 'universal-starter-slot-economics' in d
assert "FLEX:['RB','WR','TE']" in d
assert "SUPER_FLEX:['QB','RB','WR','TE']" in d
assert "IDP_FLEX:['DL','LB','DB']" in d
assert 'computeDemand' in d
assert 'replacementContext' in d
assert 'starterProbability' in d
assert 'scarcityMultiplier' in d
assert 'marginalLineupUtility' in d

# D/ST and kicker remain first-class modular surfaces.
assert 'dstPanel' in decision_ui
assert 'FIEDST' in dst and 'Replacement' in dst and 'hasDST' in dst
assert 'FIEKicker' in kicker

# League-scoped research loading must remain present in special-team surfaces.
assert 'data/research/leagues/${encodeURIComponent(k)}' in dst
assert 'data/research/leagues/${encodeURIComponent(k)}' in kicker

# Historical/global current snapshot paths must not be reintroduced into the
# modular current-snapshot loader.
for legacy in (
    'data/research/milestone4.json',
    'data/research/milestone5.json',
    'data/research/milestone6.json',
):
    assert legacy not in snapshot, f'legacy global browser research path remains: {legacy}'

# Season rollover behavior remains dynamic rather than tied to 2026.
assert latest_completed_season(datetime(2027,1,10,tzinfo=timezone.utc)) == 2025
assert latest_completed_season(datetime(2027,2,10,tzinfo=timezone.utc)) == 2026
assert inferred_nfl_season(datetime(2027,1,10,tzinfo=timezone.utc)) == 2026
assert inferred_nfl_season(datetime(2027,8,10,tzinfo=timezone.utc)) == 2027

# Promotion guardrails must reject inconsistent folds and accept a strong,
# persistent improvement.
good = promotion_gate([.04,.03,.05,.02,.04], min_mean=.01, min_folds=4, require_positive_ci=True)
bad = promotion_gate([.10,-.08,.09,-.07,.01], min_mean=.01, min_folds=4, require_positive_ci=True)
assert good['robust'] is True, good
assert bad['robust'] is False, bad

print('OK: V8.9 lineage compatibility on V9.3.x modular runtime, rollover, scoring and statistical guardrails')
