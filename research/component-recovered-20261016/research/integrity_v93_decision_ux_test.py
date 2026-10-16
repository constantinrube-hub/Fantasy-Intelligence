#!/usr/bin/env python3
"""Current modular source integrity checks for the V9.3 Decision UX lineage."""
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
read=lambda p:(ROOT/p).read_text(encoding='utf-8')

release=json.loads(read('config/release.json'))
ui=read('app/decision-ui.js')
lc=read('app/league-context.js')
vf=read('app/value-finder.js')
dst=read('app/dst-intelligence.js')
kick=read('app/kicker-intelligence.js')
dc=read('app/core/data-client.js')
rt=read('app/runtime-foundation.js')
store=read('app/current-snapshot-store.js')
c=read('app/v9.3.4c-weekly-context.js')
d=read('app/v9.3.4d-starter-economics.js')
e=read('app/v9.3.4e-return-scoring.js')

assert str(release.get('release','')).startswith('9.3.'), release
assert str(release.get('runtime','')).startswith('9.3.'), release

# Decision UI remains modular and exposes the current high-value surfaces.
for token in [
    'function syncRelease()',
    'function renderScarcityAudit()',
    'function renderLeagueIntel()',
    'matchupSimPanel',
    'Roster Contribution',
    'Est. Available Next Pick',
    'FIEProjectionResolver',
    'FIEDraftBaseValueService',
]:
    assert token in ui, f'missing current Decision UX contract: {token}'
assert "S().activeTab==='waivers'" in ui
assert 'fieFaabStrategy' in ui

# League context is authoritative outside the old monolithic shell.
for token in ['FIELeagueContext','positionAllowed','rosterForUsername','selectPreferredRoster']:
    assert token in lc, f'missing LeagueContext contract: {token}'

# Value Finder and specialist surfaces remain league-aware.
assert 'renderValueFinderInner' in vf and 'researchError' in vf and 'Retry' in vf
assert 'FIEDraftBaseValueService' in vf and 'FIEDraftStateService' in vf
assert 'FIELeagueContext' in dst and 'FIELeagueContext' in kick
assert 'FIEDST' in dst and 'FIEKicker' in kick

# Shared data client keeps request coalescing/cache diagnostics.
for token in ['inflight','coalesced','cacheStats']:
    assert token in dc, f'missing data-client contract: {token}'

# Projections are not serialized behind public enrichment.
assert 'const proj=enrich.then' not in rt
assert 'league-season-projections' in rt and 'league-enrichment' in rt

# Current snapshot loader owns the layered A3 -> C -> D -> E boot chain.
for token in ['bootA3','bootC','bootD','bootE','v9.3.4a3-score-performance.js',
              'v9.3.4c-weekly-context.js','v9.3.4d-starter-economics.js',
              'v9.3.4e-return-scoring.js']:
    assert token in store, f'missing current runtime layer: {token}'

# C-E semantic contracts.
assert 'FIE934C' in c and 'fullSimulationRequired:false' in c
assert 'FIE934D' in d and 'universal-starter-slot-economics' in d
assert 'FIE934E' in e and 'returnScoring' in e

print('V9.3+ Decision UX modular source integrity OK')
