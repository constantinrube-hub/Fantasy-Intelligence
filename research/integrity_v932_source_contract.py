#!/usr/bin/env python3
"""V9.3.2 lineage source contract for the current modular V9.3.x runtime."""
from pathlib import Path
import json

R=Path(__file__).resolve().parents[1]
read=lambda p:(R/p).read_text(encoding='utf-8')

rel=json.loads(read('config/release.json'))
assert str(rel.get('release','')).startswith('9.3.'), rel
assert str(rel.get('runtime','')).startswith('9.3.'), rel

required=[
 'app/core/season-context.js','app/core/numeric.js','app/core/projection-service.js',
 'app/core/draft-state-service.js','app/core/surface-router.js',
 'app/core/special-teams-series.js','app/core/draft-value-service.js',
 'app/core/core-services.js','app/core/data-client.js','app/runtime-foundation.js',
 'app/decision-ui.js','app/value-finder.js','app/dst-intelligence.js',
 'app/kicker-intelligence.js','app/current-snapshot-store.js',
 'app/v9.3.4a3-score-performance.js','app/v9.3.4c-weekly-context.js',
 'app/v9.3.4d-starter-economics.js','app/v9.3.4e-return-scoring.js',
]
for f in required:
    assert (R/f).exists(), f'missing modular runtime file: {f}'

season=read('app/core/season-context.js')
numeric=read('app/core/numeric.js')
ui=read('app/decision-ui.js')
vf=read('app/value-finder.js')
dst=read('app/dst-intelligence.js')
kick=read('app/kicker-intelligence.js')
cur=read('research/build_current_snapshot.py')
port=read('app/portfolio-config.js')
core=read('app/core/core-services.js')
rt=read('app/runtime-foundation.js')
router=read('app/core/surface-router.js')
draftvalue=read('app/core/draft-value-service.js')
client=read('app/core/data-client.js')
store=read('app/current-snapshot-store.js')
a3=read('app/v9.3.4a3-score-performance.js')
c=read('app/v9.3.4c-weekly-context.js')
d=read('app/v9.3.4d-starter-economics.js')
e=read('app/v9.3.4e-return-scoring.js')

# Season and nullable semantics.
assert 'Number.isInteger(n)&&n>1900' in season
assert 'FIESeasonBootstrapResolver=API' in season
assert 'FIESeasonContext=API' not in season
assert 'value===null||value===undefined' in numeric
assert 'SeasonResolver' in numeric
assert 'window.FIESeasonContext=SeasonContext' in rt

# Canonical shared decision services.
assert 'FIEProjectionResolver' in ui
assert 'FIEDraftBaseValueService' in ui and 'FIEDraftBaseValueService' in vf
assert 'FIEDraftStateService' in ui and 'FIEDraftStateService' in vf
assert 'marketIndependent:true' in draftvalue
assert 'matchupSimPanel' in router

# Structural profile has one Python implementation.
assert 'structural_contract' in cur and 'live_contract = structural_contract(' in cur
assert 'profile_diff' in cur

# Portfolio custom rules live in their own module.
assert 'optionalCap' in port
assert 'managedLeagues' in port
assert 'isPlayerEligible' in port

# D/ST and kicker retain full-week special-team support.
for txt in (dst,kick):
    assert ('Weeks 1–18' in txt or 'Week 1–18' in txt)
    assert 'FIESpecialTeamsSeries' in txt
    assert 'openDrawer' in txt

# Current browser QA services.
assert 'Player</th><th>Asset Rank' in ui or "label:'Asset Rank'" in ui
assert 'Best pick' in ui and 'Alternative' in ui and 'Value play' in ui
assert 'Board → Decision' in ui
assert 'Low-data' in ui
assert 'Canonical FIE player quality excludes market price' in ui

# Current performance/correctness layers supersede old inline-shell literals.
assert 'fastAssignScores' in a3 and 'fastReplacementLevels' in a3
assert 'FIE934C' in c and 'fullSimulationRequired:false' in c
assert 'FIE934D' in d and 'computeDemand' in d and 'marginalLineupUtility' in d
assert 'FIE934E' in e and 'returnScoring' in e
for token in ['bootA3','bootC','bootD','bootE']:
    assert token in store

# Cache/runtime lineage remains V9.3 family without pinning an obsolete minor.
assert '9.3' in rt
assert 'PERSISTENT_CACHE' in client

print('PASS V9.3.2 lineage source contract on current V9.3.x modular runtime')
